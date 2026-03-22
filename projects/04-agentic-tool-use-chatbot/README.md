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

- Node.js 22+ with `bun` package manager (`npm install -g bun`)
- AWS CDK CLI (`npm install -g aws-cdk`)
- AWS CLI v2 with Lambda, DynamoDB, API Gateway, Bedrock, and IAM permissions
- Python 3.11+ with the Strands Agents SDK (`pip install strands-agents strands-agents-tools`) for Lambda handler development

**AWS service enablement:**

- Amazon Bedrock model access enabled for Claude 3 Sonnet in your target region

**External dependencies:**

- Open-Meteo API (free, no key, no registration required): `https://api.open-meteo.com`

## Step-by-Step Build Guide

1. **Initialize the CDK project.** Copy `projects/cdk-template/` into `cdk/`. Update `package.json` `name` to `agentic-tool-use-chatbot`. Run `bun install`.

2. **Implement the tool handlers as Python Lambda source** under `src/lambdas/agent-orchestrator/`. Create `tool_weather.py`, `tool_calculator.py`, and `tool_product.py` in that directory. `tool_weather.py`: call the Open-Meteo geocoding and forecast API, return `{ city, temperature_c, condition }` or a structured error. `tool_calculator.py`: parse with `ast.parse`, walk the AST to reject non-arithmetic nodes, return `{ result }` or a structured error. `tool_product.py`: call DynamoDB `get_item`, return product fields or a structured not-found error. Register all three with the Strands `@tool` decorator with JSON Schema definitions for each input.

3. **Implement `handler.py` (Lambda orchestrator).** Load conversation history from DynamoDB by querying on `session_id` sorted by `timestamp`. Append the new user message. Instantiate a Strands `Agent` with the three registered tools and the Claude 3 Sonnet model ID. Call `agent(user_message)`. Persist the assistant response to `ConversationHistory`. Return the final answer.

4. **Define the `AgentStack`** in `src/stacks/agent-stack.ts`. Provision:
   - `Table` for `ProductCatalog` (partition key `product_id`, String).
   - `Table` for `ConversationHistory` (partition key `session_id`, sort key `timestamp`, String; TTL attribute `expires_at`).
   - A Python Lambda via `aws_lambda.Function` with `Runtime.PYTHON_3_12`, the handler zip (or a `DockerImageFunction` / Layer containing `strands-agents` and `requests`), and a 60-second timeout. Grant `bedrock:InvokeModel`, `dynamodb:GetItem` on `ProductCatalog`, `dynamodb:PutItem` + `dynamodb:Query` on `ConversationHistory`.
   - `HttpApi` with a `POST /chat` route integrated to the Lambda via `HttpLambdaIntegration`.

5. **Package the Lambda.** Create a `requirements.txt` in the handler directory listing `strands-agents`, `boto3`, and `requests`. Use a CDK `BundlingOptions` command that runs `pip install -r requirements.txt -t /asset-output && cp -r . /asset-output` so that all dependencies are included in the deployment zip.

6. **Run `bun run synth`** to validate the CloudFormation template.

7. **Run `bun run deploy`** to provision all resources.

8. **Load test data** into `ProductCatalog` using `aws dynamodb batch-write-item` with 10 sample product items (fields: `product_id`, `name`, `price`, `stock_count`, `category`).

9. **Write and run the multi-turn test script** (`scripts/test_conversation.py`). Session 1: "What is the weather in Paris?" → "Calculate 22 * 3.5" → "Look up product P003" → "If I buy enough P003 to cover the price in Euros equal to the temperature in Paris, how many units is that?". Verify that the final answer requires memory of turn 1 and turn 3.

10. **Review CloudWatch Logs** for the orchestrator Lambda. Confirm tool call parameters and responses are logged for each turn, and that the conversation history grows correctly across requests.

## Key Exam Concepts Practiced

- Strands Agents SDK for building tool-use agents on Bedrock (Tasks 2.1.1, 2.1.6)
- Tool schema definition with JSON Schema and parameter validation (Task 2.1.6)
- Structured error responses enabling model self-correction within the agent loop (Task 2.1.3)
- Conversation memory with DynamoDB for stateful multi-turn interactions (Task 2.1.1)
- IAM resource boundaries limiting what tools the agent can access (Task 2.1.3)
- Lambda timeout as a stopping condition for runaway agent loops (Task 2.1.3)
- MCP (Model Context Protocol) as the emerging standard for tool interfaces -- Strands implements this pattern (Task 2.1.7)
- Difference between Strands Agents (code-first, in-process) and Bedrock Agents (managed service) (Task 2.1.1)
