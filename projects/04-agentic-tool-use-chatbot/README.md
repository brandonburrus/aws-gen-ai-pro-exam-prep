# Project 04: Agentic Tool-Use Chatbot with Strands Agents

## Exam Domains

| Domain | Task | Description |
|--------|------|-------------|
| 2.1 | Implement agentic AI solutions and tool integrations | Autonomous systems with memory and state, tool integrations, error handling, parameter validation, MCP patterns |

## Overview

Agentic AI — where a Foundation Model autonomously decides which tools to invoke, in what order, and with what parameters — is one of the highest-weight topics in Domain 2. This project builds a functional multi-tool chatbot using the Strands Agents SDK, AWS's open-source framework for building agents on Bedrock. The agent can call three external tools: a weather lookup, a calculator, and a DynamoDB-backed product catalog lookup.

The project emphasizes the engineering details that separate a toy demo from a production-ready agent: tool schemas with strict JSON Schema validation, Lambda functions that validate incoming parameters before executing, structured error responses that allow the model to self-correct, and a conversation memory store in DynamoDB so context is preserved across turns. These implementation details map directly to Tasks 2.1.1, 2.1.6, and 2.1.7 in the exam guide.

## Architecture

```
Client  POST /chat  { session_id, message }
    |
    v
API Gateway (HTTP API)
    |
    v
Lambda: AgentOrchestrator
    |
    v
Strands Agents SDK (in-process)
    |-- Bedrock: Claude 3 Sonnet (reasoning + tool selection)
    |-- DynamoDB: ConversationHistory (session_id → message list)
    |
    |-- Tool: get_weather(city: str) --> HTTP call to Open-Meteo (free, no key)
    |-- Tool: calculate(expression: str) --> safe eval via Python AST
    |-- Tool: lookup_product(product_id: str) --> DynamoDB: ProductCatalog
    |
    v
Lambda: ToolExecutor (optional separation for parameter validation)
    |-- JSON Schema validation on all tool inputs
    |-- Structured error responses: { "error": str, "hint": str }

DynamoDB Tables:
    ConversationHistory  (PK: session_id, SK: timestamp)
    ProductCatalog       (PK: product_id, attrs: name, price, stock)
```

**AWS services used:**

- Amazon API Gateway (HTTP API) -- chat endpoint
- AWS Lambda -- agent orchestrator and tool executor
- Amazon Bedrock (Claude 3 Sonnet) -- the reasoning model driving the agent
- Strands Agents SDK -- agent loop, tool registration, and Bedrock integration
- Amazon DynamoDB -- conversation history store and product catalog
- AWS IAM -- least-privilege roles; agent Lambda cannot exceed defined tool permissions
- Amazon CloudWatch Logs -- captures agent reasoning traces and tool call logs

## What You Will Build

1. A DynamoDB `ProductCatalog` table pre-loaded with 10 sample products (id, name, price, stock_count, category).
2. A DynamoDB `ConversationHistory` table storing turn-by-turn message history keyed by `session_id`.
3. Three tool implementations registered with the Strands SDK:
   - `get_weather(city: str) -> dict` -- calls the Open-Meteo geocoding and forecast API (free, no API key required), returns current temperature and conditions.
   - `calculate(expression: str) -> dict` -- safely evaluates a mathematical expression using Python's `ast` module (no `eval`), returns result or a structured error for invalid expressions.
   - `lookup_product(product_id: str) -> dict` -- queries DynamoDB `ProductCatalog`, returns product details or a structured not-found error.
4. JSON Schema definitions for each tool's input parameters, with `required` fields and type constraints, registered as Strands tool schemas.
5. Parameter validation in each tool that returns `{ "error": "InvalidParameter", "field": "...", "hint": "..." }` for bad inputs, allowing the model to self-correct on the next reasoning step.
6. The agent orchestrator Lambda that loads conversation history from DynamoDB, appends the new user message, runs the Strands agent loop, persists the assistant response, and returns the final answer.
7. An HTTP API Gateway `POST /chat` route accepting `{ "session_id": str, "message": str }`.
8. A test script that runs a multi-turn conversation: asks about weather, does a calculation, looks up a product, then asks a follow-up that requires combining information from two prior tool calls.

## Target Outcomes

By the end of this project you should be able to verify each of the following:

- [ ] A single chat request that requires multiple tool calls (e.g., "What's the weather in Seattle and how much would it cost to buy 3 units of product P001?") returns a correct, synthesized answer without any manual orchestration.
- [ ] Sending an invalid expression to the calculator (e.g., `"2 + import os"`) returns a graceful error message to the user, not a Lambda exception, because the tool validation layer caught it and returned a structured error that the model used to compose a safe response.
- [ ] Looking up a non-existent product ID returns a helpful message (e.g., "I couldn't find product XYZ in the catalog") rather than an unhandled DynamoDB exception.
- [ ] A second chat message in the same session (same `session_id`) correctly references context from the first turn, demonstrating that conversation history is being loaded and passed to the agent.
- [ ] CloudWatch Logs for the orchestrator Lambda show the agent's reasoning steps (which tool was selected, what parameters were passed, what the tool returned) for each invocation.
- [ ] You can explain the difference between Strands Agents and Amazon Bedrock Agents, and identify one scenario where you would choose each.

## Prerequisites

**Local tooling:**

- AWS CLI v2 with Lambda, DynamoDB, API Gateway, Bedrock, and IAM permissions
- Python 3.11+ with `boto3` and the Strands Agents SDK (`pip install strands-agents strands-agents-tools`)
- AWS SAM CLI recommended for packaging Lambda with dependencies

**AWS service enablement:**

- Amazon Bedrock model access enabled for Claude 3 Sonnet in your target region

**External dependencies:**

- Open-Meteo API (free, no key, no registration required): `https://api.open-meteo.com`

## Step-by-Step Build Guide

1. **Create the DynamoDB tables.**
   - `ProductCatalog`: PK `product_id` (String). Insert 10 items with fields `name`, `price` (Number), `stock_count` (Number), `category`.
   - `ConversationHistory`: PK `session_id` (String), SK `timestamp` (String, ISO8601). TTL attribute `expires_at` (set to 24h from creation).

2. **Set up the Python project.** Create a `requirements.txt` with `strands-agents`, `boto3`, and `requests`. This will be packaged as a Lambda layer or zip.

3. **Implement `tool_weather.py`.** Define a function `get_weather(city: str) -> dict`. Call Open-Meteo geocoding API to convert city to lat/lon, then call the forecast API for current temperature and weather code. Return `{ "city": str, "temperature_c": float, "condition": str }` or `{ "error": "CityNotFound", "hint": "Try a more specific city name" }`.

4. **Implement `tool_calculator.py`.** Define `calculate(expression: str) -> dict`. Parse with `ast.parse(expression, mode='eval')`. Walk the AST and reject any node type outside `[Num, BinOp, UnaryOp, Add, Sub, Mult, Div, Pow, Mod]`. Evaluate with `eval(compile(tree, '', 'eval'))`. Return `{ "result": float }` or `{ "error": "InvalidExpression", "hint": "Only arithmetic operations are supported" }`.

5. **Implement `tool_product.py`.** Define `lookup_product(product_id: str) -> dict`. Call DynamoDB `get_item`. Return the item as a dict or `{ "error": "ProductNotFound", "product_id": product_id, "hint": "Check the product ID and try again" }`.

6. **Register tools with Strands.** Use the `@tool` decorator (or `Tool` class) from the Strands SDK to define each function with its JSON Schema. Example schema for `get_weather`: `{ "type": "object", "properties": { "city": { "type": "string", "description": "City name to look up" } }, "required": ["city"] }`.

7. **Implement `orchestrator.py` (Lambda handler).** On each invocation: load conversation history from DynamoDB (scan by `session_id`, sort by `timestamp`) → build messages list → instantiate Strands `Agent` with the three registered tools and `model="anthropic.claude-3-sonnet-20240229-v1:0"` → call `agent(user_message)` → persist assistant response to `ConversationHistory` → return response.

8. **Deploy the Lambda function.** Package with all dependencies. Set timeout to 60 seconds (agent loops with tool calls can take 20-40s). Attach an execution role with: `bedrock:InvokeModel`, `dynamodb:GetItem` on `ProductCatalog`, `dynamodb:PutItem` + `dynamodb:Query` on `ConversationHistory`.

9. **Deploy API Gateway** (HTTP API, `POST /chat` → Lambda integration).

10. **Load test data** into `ProductCatalog` using `batch_write_item`.

11. **Write and run the multi-turn test script.** Session 1: "What is the weather in Paris?" → "Calculate 22 * 3.5" → "Look up product P003" → "If I buy enough P003 to cover the price in Euros equal to the temperature in Paris, how many units is that?". Verify that the final answer requires memory of turn 1 and turn 3.

12. **Review CloudWatch Logs** for the reasoning trace. Confirm tool call parameters and responses are logged for each turn.

## Key Exam Concepts Practiced

- Strands Agents SDK for building tool-use agents on Bedrock (Tasks 2.1.1, 2.1.6)
- Tool schema definition with JSON Schema and parameter validation (Task 2.1.6)
- Structured error responses enabling model self-correction within the agent loop (Task 2.1.3)
- Conversation memory with DynamoDB for stateful multi-turn interactions (Task 2.1.1)
- IAM resource boundaries limiting what tools the agent can access (Task 2.1.3)
- Lambda timeout as a stopping condition for runaway agent loops (Task 2.1.3)
- MCP (Model Context Protocol) as the emerging standard for tool interfaces -- Strands implements this pattern (Task 2.1.7)
- Difference between Strands Agents (code-first, in-process) and Bedrock Agents (managed service) (Task 2.1.1)
