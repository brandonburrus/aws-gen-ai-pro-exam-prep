# Bedrock Prompt Management, Prompt Flows, and Agentic AI Study Guide

## AIP-C01 Exam Coverage

| Topic | Domain | Task | Weight |
|-------|--------|------|--------|
| Prompt Management | Domain 1 | Task 1.6 | Part of 30% |
| Prompt Flows | Domain 1 / Domain 2 | Task 1.6 / Task 2.5 | Part of 30% / 26% |
| Agentic AI (AgentCore, Strands, Agent Squad) | Domain 2 | Task 2.1 | Part of 26% |
| Tool Use / Function Calling | Domain 2 | Task 2.1 | Part of 26% |

---

## 1. Amazon Bedrock Prompt Management

### What It Is

A managed service for creating, saving, versioning, testing, and reusing prompt templates across different workflows. It eliminates ad-hoc prompt engineering by centralizing prompt governance.

### Core Concepts

| Term | Definition |
|------|------------|
| **Prompt** | An input provided to a model to guide response generation |
| **Variable** | A placeholder (e.g., `{{genre}}`) filled at runtime or during testing |
| **Prompt Variant** | An alternative configuration of the same prompt -- different model, different inference params, or different wording |
| **Prompt Builder** | Visual console tool for creating, editing, and testing prompts |
| **Draft Version** | The mutable working copy, created when you first save a prompt |
| **Version** | An immutable snapshot of a prompt at a point in time, used for deployment |

### Parameterized Prompt Templates

Variables use double-brace syntax in prompt text. At invocation time, variable values are supplied either:
- Directly in the `Converse` API via the `promptVariables` field
- Through a Prompt node's inputs in a Bedrock Flow
- During testing in the Prompt Builder

```
Create a {{genre}} playlist with {{count}} songs.
```

Each prompt can have **up to 3 variants** for side-by-side comparison. Variants can differ in:
- The prompt text itself
- The model selected (e.g., Claude Sonnet vs. Amazon Titan)
- Inference parameters (temperature, topP, maxTokens, stopSequences)
- System prompt content
- Tool configuration (for function-calling models)

### Versioning and Lifecycle

```
Draft (mutable) --> Version 1 (immutable snapshot) --> Version 2 --> ...
```

**Workflow:**
1. Create a prompt (creates a DRAFT)
2. Iterate on the draft -- modify text, model, parameters
3. When satisfied, **create a version** (immutable snapshot)
4. Deploy the version by referencing its ARN in your application
5. To update, modify the DRAFT and create a new version

**Version Comparison:** The console lets you diff two versions side-by-side, showing JSON differences with `+` (added) and `-` (removed) markers. You can also run both versions against test inputs to compare outputs.

### Integration with Other Services

| Integration Point | How It Works |
|-------------------|--------------|
| **Converse API** | Pass the prompt version ARN as `modelId` plus `promptVariables` |
| **InvokeModel API** | Reference prompt version ARN directly |
| **Bedrock Flows** | Add a **Prompt node** referencing the prompt ARN |
| **Bedrock Agents** | Use prompts in agent orchestration templates |

**API Example (CreatePrompt):**
```python
import boto3

client = boto3.client("bedrock-agent")

response = client.create_prompt(
    name="playlist-generator",
    description="Generates playlists by genre",
    defaultVariant="variant-one",
    variants=[
        {
            "name": "variant-one",
            "templateType": "TEXT",
            "templateConfiguration": {
                "text": {
                    "text": "Create a {{genre}} playlist with {{count}} songs.",
                    "inputVariables": [
                        {"name": "genre"},
                        {"name": "count"}
                    ]
                }
            },
            "modelId": "anthropic.claude-sonnet-4-20250514-v1:0",
            "inferenceConfiguration": {
                "text": {
                    "temperature": 0.7,
                    "maxTokens": 500
                }
            }
        }
    ]
)

prompt_id = response["id"]

# Create immutable version
version_response = client.create_prompt_version(promptIdentifier=prompt_id)
```

### Governance and Auditing

- All Prompt Management API calls are logged in **AWS CloudTrail** (CreatePrompt, CreatePromptVersion, DeletePrompt, etc.)
- Prompts can be shared across teams via ARNs and IAM policies
- Version immutability provides an audit trail of what was deployed when
- **Prompt Optimization** feature can automatically rewrite prompts for better accuracy

### Exam Tips for Prompt Management

- A **Draft** is the only mutable version; all numbered versions are **immutable**
- You invoke a prompt version via Converse API by passing its **ARN** as the `modelId`
- Up to **3 variants** can be compared side-by-side
- Variables use `{{variableName}}` syntax
- Structured prompts can include system instructions, tools configuration, and conversational history (for models supporting Converse API)

---

## 2. Amazon Bedrock Prompt Flows

### What It Is

A visual workflow builder for creating end-to-end generative AI pipelines by connecting nodes (prompts, models, Lambda functions, knowledge bases, agents, S3, conditions, loops). Flows link foundation models, AWS services, and custom logic without writing orchestration code.

### Core Architecture

```
Create Flow --> Design nodes + connections --> Prepare (working draft)
  --> Test --> Create Version (immutable) --> Create Alias --> Deploy
```

**Key Concepts:**
- **Flow**: A series of interconnected nodes; initiated via `InvokeFlow`
- **Node**: A step in the flow with inputs, outputs, and configuration
- **Connection**: Links output of one node to input of another (data connection or conditional connection)
- **Expression**: Extracts relevant parts from a node's whole input (e.g., `$.data.name`)
- **Working Draft**: Mutable version for iterative testing
- **Version**: Immutable snapshot of a flow
- **Alias**: A pointer to a version, used in production `InvokeFlow` calls

### Node Types

#### Logic Nodes (Control Flow)

| Node Type | Purpose | Key Details |
|-----------|---------|-------------|
| **Flow Input** | Entry point; one per flow | Takes `content` from `InvokeFlow` request |
| **Flow Output** | Returns results; multiple allowed | One per branch/path |
| **Condition** | Routes data based on conditions | Up to 5 conditions; evaluated in order; includes default path |
| **Iterator** | Processes array items one at a time | Splits array into individual items |
| **Collector** | Gathers iterated results back into array | Pairs with Iterator |
| **DoWhile Loop** | Repeats nodes until condition met | `maxIterations` default=10; no nested loops; up to 5 exit conditions |

#### Data Processing Nodes

| Node Type | Purpose | Key Details |
|-----------|---------|-------------|
| **Prompt** | Invokes an FM with a prompt | Can reference Prompt Management or define inline; supports guardrails |
| **Agent** | Calls a Bedrock Agent | Supports multi-turn within a flow; inputs: prompt, session/prompt attributes |
| **Knowledge Base** | Queries a knowledge base | With `modelId`: returns generated text; without: returns raw retrieval results |
| **Lambda Function** | Runs custom code | Input event has `messageVersion`, `flow`, `node`, `input` fields |
| **Inline Code** | Python code within the flow | No external dependencies; last expression is the return value; 128KB memory |
| **S3 Storage** | Stores data to S3 | Input: content + objectKey; Output: s3Uri |
| **S3 Retrieval** | Reads data from S3 | Input: objectKey; Output: file content (must be UTF-8) |
| **Lex** | Calls a Lex bot | Single-turn only; returns `predictedIntent` |

### Condition Expressions

Condition nodes use relational and logical operators:

**Relational:** `==`, `!=`, `>`, `>=`, `<`, `<=`
**Logical:** `and`, `or`, `not`

```
(retailPrice > 10) and (type == "produce")
```

Conditions are evaluated **in order** -- if multiple match, the first one wins. A **default** path handles unmatched cases.

### Sequential Chains and Conditional Branching

**Sequential chain example:**
```
Input --> Prompt (classify) --> Condition (check category)
                                  |-- "technical" --> KB query --> Prompt (answer) --> Output
                                  |-- "billing"   --> Lambda (lookup account) --> Output
                                  |-- default     --> Prompt (general response) --> Output
```

**DoWhile loop example (iterative refinement):**
```
Input --> [Loop Start] --> Prompt (generate) --> Inline Code (evaluate quality)
              ^                                          |
              |_________ quality < threshold ____________|
                                                         |
                                         quality >= threshold --> Output
```

### Pre/Post-Processing Steps

- **Pre-processing**: Use Lambda or Inline Code nodes before Prompt nodes to clean, transform, or validate input
- **Post-processing**: Use Lambda or Inline Code nodes after Prompt nodes to parse, format, or validate output
- **Guardrails**: Can be attached to Prompt nodes and Knowledge Base nodes (RetrieveAndGenerate only)

### Error Handling

- Flow execution stops at the first node failure
- Lambda functions must return responses in the expected format (with `messageVersion`)
- Inline code nodes execute in a sandboxed Python environment with no external packages
- DoWhile loops have mandatory `maxIterations` to prevent infinite loops
- Use condition nodes to handle error paths explicitly

### Deployment

1. **Prepare** the flow (applies latest changes to working draft)
2. **Test** with sample inputs in the console or via API
3. **Create a version** (immutable snapshot)
4. **Create an alias** pointing to the version
5. Invoke via `InvokeFlow` against the alias

```python
response = bedrock_agent_runtime.invoke_flow(
    flowIdentifier="FLOW_ID",
    flowAliasIdentifier="ALIAS_ID",
    inputs=[{
        "content": {"document": {"genre": "jazz", "count": 10}},
        "nodeName": "FlowInput",
        "nodeOutputName": "document"
    }]
)
```

### Async Flow Executions

Flows can run asynchronously for long-running tasks, returning a flow execution ID that you can poll for status.

### Exam Tips for Flows

- Every flow has exactly **one Input node** but can have **multiple Output nodes**
- Condition nodes evaluate conditions **in order** (first match wins)
- DoWhile loops: **no nested loops**, max 5 exit conditions, `maxIterations` prevents runaway
- Iterator/Collector pairs handle array processing
- Lambda nodes receive a specific event structure with `messageVersion` field
- Inline Code nodes: Python only, no external packages, last expression = return value
- Guardrails can only be applied to Prompt nodes and KB nodes (with RetrieveAndGenerate)
- **Flows vs. Agents**: Flows are deterministic pipelines; Agents are autonomous with reasoning loops

---

## 3. Amazon Bedrock AgentCore

### What It Is

An agentic platform for building, deploying, and operating AI agents securely at scale. It is **framework-agnostic** (works with Strands, LangGraph, CrewAI, LlamaIndex, Google ADK, OpenAI Agents SDK) and **model-agnostic** (any FM in or outside Bedrock).

### Core Services

| Service | Purpose |
|---------|---------|
| **Runtime** | Serverless hosting for agents/tools; isolated microVMs per session; supports real-time (<10min) and async (up to 8 hours); MCP and A2A protocol support |
| **Memory** | Short-term (within session) and long-term (across sessions) memory; strategies include SessionSummarizer, PreferenceLearner, FactExtractor |
| **Gateway** | Converts APIs, Lambda functions, and services into MCP-compatible tools; tool discovery; integrates with API Gateway, Salesforce, Jira, Slack |
| **Identity** | Agent identity and access management; works with Cognito, Okta, Azure Entra ID, Auth0; OAuth 2.0 support |
| **Code Interpreter** | Sandboxed code execution (Python, JavaScript, TypeScript) |
| **Browser** | Serverless browser runtime for agents to interact with web apps (Playwright, BrowserUse) |
| **Observability** | Tracing, debugging, monitoring; OpenTelemetry (OTEL)-compatible; integrates with CloudWatch |
| **Evaluations** | Automated agent quality assessment on sessions, traces, and spans |
| **Policy** | Deterministic control over agent boundaries; Cedar policy language; integrates with Gateway to intercept tool calls |

### Runtime Architecture

```
User Request --> AgentCore Runtime --> Dedicated microVM (session isolation)
                                          |
                                          +--> Agent code (any framework)
                                          +--> Tools (MCP/A2A)
                                          +--> Memory (short + long term)
                                          +--> Identity (auth)
```

Key properties:
- Each session runs in a **dedicated microVM** with isolated compute, memory, and network
- Supports **bidirectional streaming** for real-time interactions
- Can process payloads up to **100MB**
- **Consumption-based pricing** -- pay only for what you use
- Supports deploying MCP servers, A2A servers, and AGUI servers

### Memory Service

**Short-term memory:**
- Captures turn-by-turn interactions within a single session
- Maintains immediate context so users don't repeat information

**Long-term memory:**
- Automatically extracts key insights across sessions
- Built-in strategies:
  - **SessionSummarizer**: Summarizes conversation sessions
  - **PreferenceLearner**: Learns user preferences
  - **FactExtractor**: Extracts and retains facts
- Supports **message batching** to reduce API calls in high-throughput scenarios

```python
from bedrock_agentcore.memory import MemoryClient
from strands import Agent

memory_client = MemoryClient()
session_manager = memory_client.create_session_manager(
    memory_id="my-memory-store",
    session_id="user-123-session"
)

agent = Agent(
    model="bedrock/anthropic.claude-sonnet-4-20250514-v1:0",
    session_manager=session_manager
)
```

### MCP Server Hosting

AgentCore Runtime can host MCP servers in two modes:

| Mode | Transport | Use Case |
|------|-----------|----------|
| **Stateless** | Streamable HTTP | Simple request/response tools; scales easily |
| **Stateful** | Streamable HTTP with Mcp-Session-Id | Multi-turn conversations, elicitation, sampling, progress notifications |

MCP servers must:
- Use `streamable-http` transport
- Listen on host `0.0.0.0`, port `8000`
- Use ARM64 containers
- Expose `/mcp` endpoint for JSON-RPC messages

### AgentCore Gateway

Converts existing APIs into MCP-compatible tools without rewriting code:

| Input Type | How It Works |
|------------|--------------|
| **OpenAPI spec** | Parses spec, creates MCP tools for each endpoint |
| **Lambda functions** | Wraps functions as MCP tools |
| **API Gateway** | Directly connects REST APIs as a Gateway target |
| **Existing MCP servers** | Proxies through for governance and discovery |

Supports **natural language tool discovery** -- agents can search for tools using queries rather than knowing exact tool names.

### Exam Tips for AgentCore

- AgentCore is **framework-agnostic** and **model-agnostic** -- this is a key differentiator
- Runtime uses **microVMs** for session isolation (not containers, not Lambda)
- Memory has two types: **short-term** (within session) and **long-term** (across sessions)
- Gateway converts APIs to **MCP-compatible tools**
- Policy uses **Cedar** language for fine-grained control
- Supports both **MCP** (Model Context Protocol) and **A2A** (Agent-to-Agent) protocols

---

## 4. Strands Agents SDK

### What It Is

An open-source, model-driven Python SDK for building AI agents. Developed initially for Amazon Q Developer. Uses a "model-driven" approach where the LLM handles reasoning and planning, reducing the need for explicit orchestration code.

### Core Architecture

An agent in Strands has three components:

```python
from strands import Agent
from strands.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: 72F, sunny"

agent = Agent(
    model="bedrock/anthropic.claude-sonnet-4-20250514-v1:0",  # Model
    tools=[get_weather],                                        # Tools
    system_prompt="You are a helpful weather assistant."         # Prompt
)

result = agent("What's the weather in Seattle?")
```

| Component | Role |
|-----------|------|
| **Model** | LLM that handles reasoning, planning, tool selection |
| **Tools** | Functions the agent can call; defined via `@tool` decorator or MCP servers |
| **Prompt** | System instructions that guide agent behavior |

### The Agent Loop

```
User input --> LLM (with tools description)
                |
                +--> Natural language response (done)
                +--> Tool call request
                        |
                        v
                     Execute tool --> Return result to LLM --> (repeat loop)
```

The LLM autonomously decides:
- Which tools to use
- What order to use them
- When to ask for clarification
- When to stop

### Custom Tools

```python
from strands.tools import tool

@tool
def search_database(query: str, limit: int = 10) -> dict:
    """Search the product database.
    
    Args:
        query: Search query string
        limit: Maximum results to return
    """
    # Implementation here
    return {"results": [...]}
```

Tools can also be loaded from MCP servers:
```python
from strands.tools.mcp import MCPClient

mcp_client = MCPClient(server_url="http://my-mcp-server:8000/mcp")
agent = Agent(
    model="bedrock/anthropic.claude-sonnet-4-20250514-v1:0",
    tools=[mcp_client]
)
```

### Multi-Agent Orchestration (Strands 1.0)

Strands 1.0 provides four multi-agent primitives:

#### 1. Agents-as-Tools
Agents wrapped as callable tools for hierarchical delegation:
```python
research_agent = Agent(
    system_prompt="You research topics thoroughly.",
    tools=[web_search]
)

writer_agent = Agent(
    system_prompt="You write engaging content.",
    tools=[research_agent.as_tool()]  # Research agent is a tool
)
```

#### 2. Handoffs
Transfer control between agents, preserving conversation context:
```python
from strands.multiagent import handoff

support_agent = Agent(system_prompt="Handle general support")
billing_agent = Agent(system_prompt="Handle billing questions")

# support_agent can hand off to billing_agent when needed
```

#### 3. Swarms
Self-organizing teams of agents collaborating on complex tasks:
```python
from strands.multiagent import Swarm

swarm = Swarm(
    agents=[analyst_agent, researcher_agent, writer_agent],
    task="Analyze market trends and produce a report"
)
```

#### 4. Graphs
Explicit workflows with conditional routing:
```python
from strands.multiagent import GraphBuilder

graph = GraphBuilder()
graph.add_node("research", research_agent)
graph.add_node("analyze", analysis_agent)
graph.add_node("write", writer_agent)
graph.add_edge("research", "analyze")
graph.add_edge("analyze", "write")
```

### Memory and State

- **Durable session management**: Automatic persistence and restoration of conversations
- **Native async support**: True concurrent execution and real-time streaming
- Integration with **AgentCore Memory** for managed short/long-term memory

### Observability

- Built-in **OpenTelemetry** instrumentation
- Traces every tool call, LLM invocation, and agent decision
- Integrates with AWS X-Ray, CloudWatch, and third-party tools (Langfuse)
- Metrics: latency, token usage, tool call counts, error rates

### Deployment Options

| Method | Service | Use Case |
|--------|---------|----------|
| Serverless | AWS Lambda | Low-latency, event-driven |
| Containers | ECS/Fargate/EKS | Long-running, complex agents |
| Managed | AgentCore Runtime | Production-grade with session isolation |
| Local | Direct execution | Development and testing |

### Exam Tips for Strands

- **Model-driven** approach: the LLM decides what to do, not explicit code
- Three components: **Model + Tools + Prompt**
- `@tool` decorator is how you define custom tools
- Four multi-agent primitives: **Agents-as-Tools, Handoffs, Swarms, Graphs**
- Supports **MCP** servers as tool sources
- Open-source (Apache 2.0), not an AWS-only service
- Built-in **OpenTelemetry** for observability

---

## 5. AWS Agent Squad (Multi-Agent Orchestrator)

### What It Is

An open-source framework (formerly "Multi-Agent Orchestrator") for building multi-agent systems where specialized agents collaborate to solve complex tasks. Available in Python and TypeScript.

### Architecture

```
User Request --> Classifier (intent routing)
                    |
                    +--> Agent A (billing specialist)
                    +--> Agent B (technical support)
                    +--> Agent C (general knowledge)
                    |
                Response aggregation --> User
```

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Classifier** | Routes requests to the most appropriate agent based on intent |
| **Agent** | A specialized unit that handles a specific domain |
| **Orchestrator** | Coordinates agents, manages context, handles routing |
| **Storage** | Manages conversation history and context across agents |

### Key Differentiators from Bedrock Multi-Agent Collaboration

| Feature | Agent Squad | Bedrock Multi-Agent Collaboration |
|---------|------------|-----------------------------------|
| Deployment | Self-managed (open source) | Fully managed by Bedrock |
| Flexibility | Complete control over behavior | Managed with configuration |
| Agents | Independent microservices | Bedrock Agent sub-agents |
| Routing | Custom classifier logic | Supervisor agent with routing |
| Integration | Any LLM provider | Amazon Bedrock models |

### Bedrock Native Multi-Agent Collaboration

Amazon Bedrock also has a **built-in multi-agent collaboration** feature:

| Mode | Behavior |
|------|----------|
| **Supervisor** | Supervisor agent breaks down tasks and delegates to sub-agents |
| **Supervisor with Routing** | Simple queries routed directly; complex queries delegated |

Features:
- **Inline agent support**: Create temporary agents on-the-fly
- **CloudFormation/CDK support**: Infrastructure as code
- **Enhanced tracing**: Full visibility into delegation and execution
- **Payload referencing**: Pass large payloads between agents
- Limits configurable for collaborator count and step count

### Exam Tips for Agent Squad / Multi-Agent

- **Agent Squad** = open-source, self-managed, any provider
- **Bedrock Multi-Agent Collaboration** = managed, supervisor pattern, Bedrock-native
- Supervisor mode: supervisor breaks down tasks
- Supervisor with routing: simple queries bypass supervisor
- Know when to use which: open-source flexibility vs. managed simplicity

---

## 6. Model Context Protocol (MCP)

### What It Is

An open standard protocol enabling seamless communication between LLMs and external data sources, tools, and services. Think of it as a "USB-C for AI" -- a universal connector.

### Architecture

```
AI Application (MCP Client)  <--MCP Protocol-->  MCP Server (tools/data)
         |                                              |
    Strands Agent                              Lambda Function
    LangGraph Agent                            ECS Container
    Bedrock Agent                              API Gateway
                                               Third-party service
```

### Three Primitives

| Primitive | What It Provides | Example |
|-----------|-----------------|---------|
| **Tools** | Functions models can call | `search_database`, `send_email` |
| **Resources** | Data to include in context | Files, database records, API responses |
| **Prompts** | Templates for model interaction | Structured queries, report formats |

### MCP Solves the M x N Problem

Without MCP: M agents x N tools = M*N custom integrations
With MCP: M agents + N tools = M+N standardized connections

### Transport Types

| Transport | Mode | Use Case |
|-----------|------|----------|
| **stdio** | Local | Development, local tools |
| **SSE (Server-Sent Events)** | Local/Remote | Streaming responses |
| **Streamable HTTP** | Remote | Production deployment (required by AgentCore) |

### MCP on AWS

#### Lambda-Based MCP Servers (Stateless)
- Simple request/response tools
- Scales automatically
- No session state between calls
- Good for: database queries, API calls, data transformations

#### ECS-Based MCP Servers (Stateful/Complex)
- Long-running tools, complex workflows
- Maintains state across calls
- Good for: multi-step processes, browser automation, file operations

#### AgentCore Gateway
- **Converts existing APIs to MCP** without code changes
- Supports OpenAPI specs, Lambda functions, and API Gateway as input
- Built-in authentication (IAM, OAuth, API keys)
- Natural language tool discovery
- Policy integration for governance

### MCP Protocol Details (AgentCore)

| Operation | Purpose |
|-----------|---------|
| `tools/list` | Discover available tools |
| `tools/call` | Invoke a specific tool with arguments |

**Stateful MCP** (supported by AgentCore Runtime):
- Uses `Mcp-Session-Id` header for session tracking
- **Elicitation**: Server can request user input mid-operation
- **Sampling**: Server can request LLM-generated content
- **Progress notifications**: Real-time updates during long operations

### Exam Tips for MCP

- MCP is an **open standard**, not AWS-proprietary
- Three primitives: **Tools, Resources, Prompts**
- AgentCore requires **streamable-http** transport (not stdio)
- Gateway converts **existing APIs to MCP** without rewriting
- MCP versions supported by AgentCore: `2025-06-18` and `2025-03-26`
- Know the difference between stateless (Lambda) and stateful (ECS/AgentCore) MCP servers

---

## 7. Tool Use / Function Calling

### How It Works (Converse API)

The Bedrock Converse API provides a unified interface for tool use across all supported models:

```
1. User sends message + tool definitions to model
2. Model decides if it needs a tool (stopReason = "tool_use")
3. Model returns tool name + parameters (toolUse block)
4. Developer executes the tool
5. Developer sends tool result back (toolResult block)
6. Model generates final response incorporating tool results
```

### Tool Definition (ToolSpec)

```python
tool_config = {
    "tools": [
        {
            "toolSpec": {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City name"
                            },
                            "units": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "Temperature units"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        }
    ]
}
```

### Client-Side vs. Server-Side Tool Calling

| Mode | Who Executes the Tool | API |
|------|----------------------|-----|
| **Client-side** | Your application code | Converse, InvokeModel, Responses API, Chat Completions API |
| **Server-side** | Amazon Bedrock | Converse API with AgentCore Gateway integration |

### The Tool Use Loop (Converse API)

```python
import boto3, json

bedrock = boto3.client("bedrock-runtime")

messages = [{"role": "user", "content": [{"text": "What's the weather in Seattle?"}]}]

# Step 1: Send message with tool config
response = bedrock.converse(
    modelId="anthropic.claude-sonnet-4-20250514-v1:0",
    messages=messages,
    toolConfig=tool_config
)

# Step 2: Check if tool use is requested
if response["stopReason"] == "tool_use":
    tool_use_block = response["output"]["message"]["content"]
    messages.append(response["output"]["message"])
    
    for block in tool_use_block:
        if "toolUse" in block:
            tool = block["toolUse"]
            # Step 3: Execute the tool
            result = get_weather(tool["input"]["location"])
            
            # Step 4: Send tool result back
            messages.append({
                "role": "user",
                "content": [{
                    "toolResult": {
                        "toolUseId": tool["toolUseId"],
                        "content": [{"json": result}],
                        "status": "success"  # or "error"
                    }
                }]
            })
    
    # Step 5: Get final response
    final_response = bedrock.converse(
        modelId="anthropic.claude-sonnet-4-20250514-v1:0",
        messages=messages,
        toolConfig=tool_config
    )
```

### Error Handling for Tool Calls

```python
tool_result = {
    "toolUseId": tool["toolUseId"],
    "content": [{"text": "Station WXYZ not found in database"}],
    "status": "error"  # Tells the model the tool failed
}
```

The `status` field (`"success"` or `"error"`) is supported by **Amazon Nova** and **Anthropic Claude 3/4** models. The model can then decide to retry, try a different approach, or report the error to the user.

### ToolChoice Configuration

| Value | Behavior |
|-------|----------|
| `auto` | Model decides whether to use tools (default) |
| `any` | Model must use at least one tool |
| `tool` | Model must use a specific named tool |

### Structured Outputs with Tool Use

Tool use can enforce structured JSON output -- define a tool whose input schema matches your desired output format. The model will always return data conforming to that schema.

### Exam Tips for Tool Use

- `stopReason == "tool_use"` means the model wants to call a tool
- The developer executes the tool, not the model (client-side)
- `toolUseId` must be passed back in `toolResult` to link request/response
- `status` field in toolResult: `"success"` or `"error"`
- Tool definitions use **JSON Schema** format
- The Converse API is the **recommended** API for tool use (model-agnostic)
- Models can request **multiple tool calls** in a single response

---

## 8. Agentic Design Patterns

### ReAct (Reasoning + Acting)

The core pattern used by Bedrock Agents. Alternates between reasoning about the situation and taking action:

```
Thought: I need to find the user's order status. I should call the order lookup API.
Action: call get_order_status(order_id="12345")
Observation: Order 12345 is "shipped", tracking: UPS1234
Thought: I have the information. I can now respond to the user.
Answer: Your order 12345 has been shipped. Tracking number: UPS1234
```

In Bedrock Agents, this manifests as:
- **Rationale**: The agent's reasoning (Thought)
- **InvocationInput**: The action to take (Action)
- **Observation**: The result from the action

### Chain-of-Thought Reasoning

Technique where the model explicitly articulates its reasoning steps. In Bedrock:
- Foundation models like Claude support CoT natively
- Agent orchestration templates can include CoT instructions
- Enhances transparency and debuggability

### Human-in-the-Loop

Several implementation patterns:

| Pattern | Service | Use Case |
|---------|---------|----------|
| **Return of Control** | Bedrock Agents | Agent pauses and returns parameters to the application for human approval before executing |
| **Step Functions** | AWS Step Functions | Workflow pauses at a review/approval step; human approves via callback |
| **Elicitation** | MCP (stateful) | MCP server requests additional input from the user mid-operation |
| **Handoffs** | Strands Agents | Agent transfers control to a human when it encounters unknown tasks |

**Return of Control (Bedrock Agents):**
```python
# Configure action group with RETURN_CONTROL
action_group = {
    "actionGroupExecutor": {
        "customControl": "RETURN_CONTROL"  # Instead of Lambda ARN
    }
}

# Agent returns invocationInputs in the InvokeAgent response
# Developer inspects, approves, executes, and returns results via
# sessionState.returnControlInvocationResults
```

### Circuit Breakers and Stopping Conditions

- **Bedrock Agents**: Built-in orchestration limits (max steps per invocation)
- **Bedrock Flows**: `maxIterations` on DoWhile loops (default 10)
- **Strands Agents**: Configurable maximum tool calls and iterations
- **Step Functions**: Timeouts on each state and the overall execution
- **General pattern**: Set maximum iterations, time limits, and budget constraints

### Multi-Model Coordination

| Pattern | Description | When to Use |
|---------|-------------|-------------|
| **Supervisor** | One coordinator agent delegates to specialists | Clear hierarchy, well-defined sub-tasks |
| **Swarm** | Peer agents collaborate without a leader | Diverse perspectives, creative tasks |
| **Pipeline** | Sequential hand-off between specialized agents | Clear stage-wise processing |
| **Router** | Classifier routes to the best agent | Intent-based routing |

### Bedrock Agent Orchestration Stages

```
Pre-Processing --> Orchestration (loop) --> Post-Processing
     |                    |                      |
  Validate input    Reason + Act            Format output
  Categorize        Call tools              (off by default)
                    Query KBs
                    Generate response
```

Each stage has a customizable **prompt template** and optional **Lambda parser**.

### Exam Tips for Agentic Patterns

- **ReAct** = Bedrock Agents' native pattern (Thought/Action/Observation)
- **Return of Control** = how Bedrock Agents implement human-in-the-loop without Lambda
- Pre-processing and post-processing are **optional** agent stages
- The orchestration loop continues until the agent has a final answer or hits a limit
- **Trace** reveals the full reasoning chain: rationale, invocation inputs, observations
- Know the four prompt templates: pre-processing, orchestration, KB response generation, post-processing

---

## 9. Exam Gotchas

### Bedrock Agents vs. Prompt Flows vs. Step Functions

| Feature | Bedrock Agents | Prompt Flows | Step Functions |
|---------|---------------|--------------|----------------|
| **Orchestration** | Autonomous (LLM decides) | Deterministic (you define) | Deterministic (you define) |
| **Reasoning** | Yes (ReAct loop) | No | No |
| **Tool calling** | Yes (action groups) | Via Lambda/Agent nodes | Via Lambda/any service |
| **Conditional logic** | LLM decides path | Condition nodes | Choice states |
| **Human approval** | Return of Control | N/A (build with Lambda) | Callback pattern |
| **Visual builder** | Console UI | Visual flow builder | Workflow Studio |
| **Versioning** | Agent aliases | Flow versions + aliases | Version ARNs |
| **Use case** | Open-ended tasks requiring reasoning | Repeatable AI pipelines | Any workflow orchestration |

### Common Traps

1. **"Which service for a deterministic AI pipeline?"** -- Prompt Flows (not Agents)
2. **"Which service for open-ended tasks requiring reasoning?"** -- Bedrock Agents (not Flows)
3. **"Which service for general workflow with human approval?"** -- Step Functions
4. **"How to make an agent pause for approval?"** -- Return of Control (not Step Functions)
5. **"Framework-agnostic agent hosting?"** -- AgentCore Runtime (not Bedrock Agents)
6. **"Convert existing APIs to agent-compatible tools?"** -- AgentCore Gateway (not manual MCP)
7. **"Open-source agent SDK by AWS?"** -- Strands Agents (not Bedrock Agents SDK)
8. **"Multi-agent with full control?"** -- Agent Squad or Strands Graphs
9. **"Multi-agent fully managed?"** -- Bedrock Multi-Agent Collaboration
10. **"Immutable prompt for production?"** -- Create a Version (not use the Draft)

### Prompt Management Traps

- Draft is **mutable**; versions are **immutable**
- You **cannot** modify a version after creation
- To invoke a prompt version via Converse API, use the version **ARN** as `modelId`
- Prompt Optimization rewrites prompts automatically -- know this exists

### Flow Traps

- Iterator produces **individual items** + **arraySize**; Collector produces **array** + **arraySize**
- Inline code: **Python only**, no external packages, last expression = output
- Lex node: **single-turn only**
- Knowledge base node without modelId: returns **raw retrieval results** (array), not generated text

---

## 10. When to Use Each: Decision Matrix

```
Need autonomous reasoning?
  YES --> Bedrock Agents or Strands Agents
  NO  --> Is it a repeatable AI pipeline?
            YES --> Bedrock Prompt Flows
            NO  --> Is it a general workflow with non-AI steps?
                      YES --> AWS Step Functions
                      NO  --> Direct API call (Converse API)
```

### Detailed Decision Matrix

| Scenario | Best Choice | Why |
|----------|-------------|-----|
| Repeatable prompt chain with conditions | **Prompt Flows** | Deterministic, visual, versioned |
| Open-ended task requiring multi-step reasoning | **Bedrock Agents** | ReAct loop, tool calling, KB queries |
| Self-managed agent with any LLM provider | **Strands Agents** | Open-source, model-agnostic |
| Production agent hosting with isolation | **AgentCore Runtime** | microVMs, session isolation, managed |
| Convert REST APIs to agent tools | **AgentCore Gateway** | No code changes, MCP-compatible |
| Multi-agent with AWS-managed coordination | **Bedrock Multi-Agent Collaboration** | Supervisor pattern, built-in |
| Multi-agent with full customization | **Strands Graphs or Agent Squad** | Custom routing and orchestration |
| Workflow with human approval gates | **Step Functions** | Callback pattern, state machine |
| Agent that pauses for user confirmation | **Bedrock Agents (Return of Control)** | Native agent capability |
| Reusable prompt across multiple apps | **Prompt Management** | Versioned, shareable, testable |
| Agent memory across sessions | **AgentCore Memory** | Managed short + long term |
| Policy enforcement on agent tool use | **AgentCore Policy** | Cedar language, real-time |

---

## 11. TypeScript SDK v3 Usage

### Bedrock Converse API with Tool Use

```typescript
import {
  BedrockRuntimeClient,
  ConverseCommand,
  type Message,
  type ToolConfiguration,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

const toolConfig: ToolConfiguration = {
  tools: [
    {
      toolSpec: {
        name: "get_weather",
        description: "Get current weather for a location",
        inputSchema: {
          json: {
            type: "object",
            properties: {
              location: { type: "string", description: "City name" },
            },
            required: ["location"],
          },
        },
      },
    },
  ],
};

async function chat(userMessage: string): Promise<string> {
  const messages: Message[] = [
    { role: "user", content: [{ text: userMessage }] },
  ];

  // Initial request
  const response = await client.send(
    new ConverseCommand({
      modelId: "anthropic.claude-sonnet-4-20250514-v1:0",
      messages,
      toolConfig,
    })
  );

  // Handle tool use
  if (response.stopReason === "tool_use") {
    const assistantMessage = response.output!.message!;
    messages.push(assistantMessage);

    for (const block of assistantMessage.content!) {
      if (block.toolUse) {
        const toolInput = block.toolUse.input as { location: string };
        const weatherResult = await getWeather(toolInput.location);

        messages.push({
          role: "user",
          content: [
            {
              toolResult: {
                toolUseId: block.toolUse.toolUseId!,
                content: [{ json: weatherResult }],
                status: "success",
              },
            },
          ],
        });
      }
    }

    // Send tool results back
    const finalResponse = await client.send(
      new ConverseCommand({
        modelId: "anthropic.claude-sonnet-4-20250514-v1:0",
        messages,
        toolConfig,
      })
    );

    return finalResponse.output!.message!.content![0].text!;
  }

  return response.output!.message!.content![0].text!;
}
```

### Invoking a Prompt from Prompt Management

```typescript
import {
  BedrockRuntimeClient,
  ConverseCommand,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

const response = await client.send(
  new ConverseCommand({
    modelId: "arn:aws:bedrock:us-east-1:123456789012:prompt/PROMPT_ID:1",
    messages: [{ role: "user", content: [{ text: "placeholder" }] }],
    promptVariables: {
      genre: { text: "jazz" },
      count: { text: "10" },
    },
  })
);
```

### Invoking a Bedrock Flow

```typescript
import {
  BedrockAgentRuntimeClient,
  InvokeFlowCommand,
} from "@aws-sdk/client-bedrock-agent-runtime";

const client = new BedrockAgentRuntimeClient({ region: "us-east-1" });

const response = await client.send(
  new InvokeFlowCommand({
    flowIdentifier: "FLOW_ID",
    flowAliasIdentifier: "ALIAS_ID",
    inputs: [
      {
        content: { document: "What is generative AI?" },
        nodeName: "FlowInputNode",
        nodeOutputName: "document",
      },
    ],
  })
);

// Process streaming response
for await (const event of response.responseStream!) {
  if (event.flowOutputEvent) {
    console.log(event.flowOutputEvent.content?.document);
  }
}
```

### Invoking a Bedrock Agent

```typescript
import {
  BedrockAgentRuntimeClient,
  InvokeAgentCommand,
} from "@aws-sdk/client-bedrock-agent-runtime";

const client = new BedrockAgentRuntimeClient({ region: "us-east-1" });

const response = await client.send(
  new InvokeAgentCommand({
    agentId: "AGENT_ID",
    agentAliasId: "ALIAS_ID",
    sessionId: "unique-session-id",
    inputText: "What is the status of order 12345?",
    enableTrace: true,
  })
);

for await (const event of response.completion!) {
  if (event.chunk) {
    const text = new TextDecoder().decode(event.chunk.bytes);
    process.stdout.write(text);
  }
  if (event.trace) {
    console.log("Trace:", JSON.stringify(event.trace, null, 2));
  }
}
```

---

## 12. Key Metrics and Monitoring

### Bedrock Agent Tracing

Enable tracing by setting `enableTrace: true` in `InvokeAgent`. The trace includes:

| Trace Type | What It Captures |
|------------|-----------------|
| **PreProcessingTrace** | Input validation and categorization |
| **OrchestrationTrace** | Reasoning (rationale), tool invocations, observations |
| **PostProcessingTrace** | Response formatting (if enabled) |
| **FailureTrace** | Error details when a step fails |
| **GuardrailTrace** | Guardrail assessment results |
| **RoutingClassifierTrace** | Multi-agent routing decisions |

**OrchestrationTrace** contains:
- `rationale`: The agent's reasoning text (the "Thought" in ReAct)
- `invocationInput`: Which action group/KB the agent chose
- `observation`: Results from the action/query
- `modelInvocationInput`: Full prompt sent to the FM
- `modelInvocationOutput`: FM's raw response

### AgentCore Observability

- **OpenTelemetry (OTEL)** compatible traces, metrics, and logs
- Integrates with **Amazon CloudWatch** for dashboards and alarms
- Supports **AWS X-Ray** for distributed tracing
- Visualizes agent execution paths step-by-step
- Enables debugging of performance bottlenecks

### Strands Agents Observability

```python
# Built-in OpenTelemetry instrumentation
from strands import Agent

agent = Agent(
    model="bedrock/anthropic.claude-sonnet-4-20250514-v1:0",
    tools=[my_tool],
    trace_attributes={"environment": "production"}
)
```

Key metrics tracked:
- **Agent loop iterations**: How many reasoning cycles
- **Tool call count and latency**: Per-tool performance
- **Token usage**: Input/output tokens per invocation
- **Error rates**: Tool failures, model errors
- **End-to-end latency**: Total time from request to response

### CloudWatch Metrics for Bedrock

| Metric | Description |
|--------|-------------|
| `Invocations` | Number of model invocations |
| `InvocationLatency` | Time per invocation |
| `InputTokenCount` / `OutputTokenCount` | Token consumption |
| `InvocationClientErrors` / `InvocationServerErrors` | Error counts |
| `InvocationThrottles` | Rate limiting events |

### CloudTrail Integration

All API calls across Prompt Management, Flows, Agents, and AgentCore are logged in CloudTrail:
- `CreatePrompt`, `CreatePromptVersion`, `DeletePrompt`
- `CreateFlow`, `CreateFlowVersion`, `InvokeFlow`
- `CreateAgent`, `InvokeAgent`, `UpdateAgent`
- AgentCore Runtime, Memory, Gateway operations

---

## Quick Reference Card

### Service Endpoints to Remember

| Service | Client | Build-Time | Runtime |
|---------|--------|------------|---------|
| Prompt Management | `bedrock-agent` | `CreatePrompt`, `CreatePromptVersion` | Invoke via `Converse` with prompt ARN |
| Flows | `bedrock-agent` / `bedrock-agent-runtime` | `CreateFlow`, `CreateFlowVersion` | `InvokeFlow` |
| Agents | `bedrock-agent` / `bedrock-agent-runtime` | `CreateAgent`, `PrepareAgent` | `InvokeAgent` |
| AgentCore | `bedrock-agentcore` / Python SDK | Console / CLI / SDK | Runtime SDK |

### Key ARN Patterns

```
Prompt:      arn:aws:bedrock:{region}:{account}:prompt/{prompt-id}
Prompt Ver:  arn:aws:bedrock:{region}:{account}:prompt/{prompt-id}:{version}
Flow:        arn:aws:bedrock:{region}:{account}:flow/{flow-id}
Agent:       arn:aws:bedrock:{region}:{account}:agent/{agent-id}
Agent Alias: arn:aws:bedrock:{region}:{account}:agent-alias/{agent-id}/{alias-id}
```

### Must-Know Limits

| Resource | Limit |
|----------|-------|
| Prompt variants per prompt | 3 |
| Condition node conditions | Up to 5 |
| DoWhile loop max iterations | Configurable (default 10) |
| Condition expression max length | 64 characters |
| Flow Input nodes per flow | Exactly 1 |
| Flow Output nodes per flow | Multiple allowed |
| AgentCore Runtime async workload duration | Up to 8 hours |
| AgentCore Runtime payload size | Up to 100MB |
| MCP server port (AgentCore) | 8000 |
| MCP server host (AgentCore) | 0.0.0.0 |
