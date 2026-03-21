# Domain 2: Implementation and Integration — Study Guide

**Exam Weight: 26%**
**Source: AWS Certified Generative AI Developer - Professional (AIP-C01)**

This domain covers the practical implementation of GenAI solutions on AWS, including agentic
systems, model deployment, enterprise integrations, API patterns, and developer tooling. It
carries the second-highest exam weight and requires deep familiarity with how AWS services
wire together in production GenAI architectures.

---

## Task 2.1: Implement Agentic AI Solutions and Tool Integrations

### What is Agentic AI?

An AI agent is an autonomous system that uses a foundation model (FM) as its reasoning engine,
coordinates with external tools and APIs, maintains state, and executes multi-step workflows to
accomplish a goal. Agentic AI unifies:

- Multi-agent system architecture (distributed AI, actor model)
- The cognitive loop: perceive → reason → act
- The generative power of LLMs
- Cloud-native and serverless compute flexibility

### Core AWS Frameworks for Agents

**Amazon Bedrock Agents**
- Fully managed service for building goal-driven, tool-using agents
- Uses the ReAct (Reason + Act) framework internally: the agent breaks user input into logical
  steps, selects tools (action groups), executes them, and synthesizes a response
- Supports multi-agent collaboration (supervisor + collaborator agents)
- Integrates with Knowledge Bases for RAG, Lambda action groups, code interpreter, and memory

**Strands Agents (Open Source SDK)**
- Open-sourced by AWS in May 2025; provider-independent and model-agnostic
- Model-first design philosophy: the LLM drives orchestration decisions, not rigid state machines
- Core agent = Model + Tools + System Prompt
- Supports multiple model providers: Amazon Bedrock, Anthropic, Ollama, Meta, OpenAI, Cohere
- Four multi-agent coordination patterns:
  - **Agents-as-Tools**: an agent wraps another agent as a callable tool, creating hierarchical delegation
  - **Swarms**: self-organizing peer agents that hand off tasks to each other autonomously
  - **Graphs**: directed workflows with conditional routing and deterministic execution paths
  - **Meta Agents**: a single agent with tools that dynamically create and orchestrate other agents
- Built-in OpenTelemetry (OTEL) instrumentation for observability
- Deploy via Lambda (serverless), ECS/EKS (containers), or Amazon Bedrock AgentCore Runtime

**AWS Agent Squad**
- AWS-native orchestration for multi-agent systems
- Works alongside Strands Agents for coordinating agent ensembles
- Used in Task 2.5.5 for advanced GenAI orchestration

**Amazon Bedrock AgentCore**
- Platform for building, deploying, and managing agents securely at scale using any framework/model
- Modular services: Runtime, Memory, Gateway, Identity, Code Interpreter, Browser, Observability,
  Evaluations, Policy
- AgentCore Runtime: serverless hosting for agents; framework-agnostic (supports LangGraph, Strands,
  CrewAI, custom); each session runs in a dedicated microVM for isolation
- Supports long-running workloads (up to 8 hours), bidirectional streaming (WebSocket), and
  100 MB payloads
- AgentCore Gateway: converts APIs and services into MCP-compatible tools
- Consumption-based pricing with no upfront commitments

### Model Context Protocol (MCP)

MCP is an open standard from Anthropic that enables LLMs to interact with external tools,
environments, and memory in a standardized way.

- Defines how agents discover and call tools (MCP servers)
- Enterprise-ready features (March 2025): OAuth 2.1 security, expanded resource types,
  Streamable HTTP transport
- AWS joined the MCP steering committee in May 2025
- **MCP Server hosting options:**
  - AWS Lambda: stateless MCP servers for lightweight, low-latency tool access (skill 2.1.7)
  - Amazon ECS: MCP servers for complex, long-running, or stateful tools (skill 2.1.7)
- **MCP Client libraries**: provide consistent, standardized access patterns for agents to
  call MCP servers
- Amazon Q Developer, Cursor, and other AI coding assistants integrated MCP for standardized
  development workflows

### ReAct Pattern and Chain-of-Thought Reasoning

ReAct (Reason + Act) is the core agent reasoning loop:

1. Receive user request
2. Reason about what action to take (chain-of-thought)
3. Select and invoke a tool
4. Observe the result
5. Repeat until the goal is achieved

**AWS Implementation:**
- AWS Step Functions implements ReAct patterns as state machines
- Each state in Step Functions can represent a reasoning/acting step
- Lambda functions handle individual tool calls within the workflow
- Amazon Bedrock's custom orchestration Lambda gives full control over the ReAct loop

### Safeguarded AI Workflows (Guardrails on Agent Behavior)

Controlling agent behavior in production requires multiple safety mechanisms:

| Control | AWS Service | Purpose |
|---|---|---|
| Stopping conditions | Step Functions | Halt workflow after max iterations or time |
| Timeout mechanisms | Lambda | Force-stop long-running tool calls |
| Resource boundaries | IAM policies | Prevent agents from accessing unauthorized resources |
| Circuit breakers | Step Functions / custom | Stop cascading failures from tool errors |
| Content safety | Bedrock Guardrails | Block harmful inputs/outputs at model layer |

**Circuit Breaker Pattern**: When a tool fails repeatedly, a circuit breaker "opens" and
stops calling the failing service, returning a fallback response instead of allowing cascading
failures.

### Model Coordination and Ensembles

- **Specialized FMs for subtasks**: Route different parts of a complex task to the FM best
  suited for that step (e.g., a coding model for code generation, a summarization model for
  document synthesis)
- **Custom aggregation logic for ensembles**: Multiple models independently process the same
  input; outputs are aggregated (e.g., majority vote, weighted average)
- **Model selection frameworks**: Dynamically pick the right FM based on task type, expected
  token count, latency requirements, or cost budget

### Human-in-the-Loop (HITL)

Amazon Bedrock Agents offers two HITL patterns:

- **User Confirmation**: Agent presents an action for binary (yes/no) approval before executing
- **Return of Control (ROC)**: Agent prepares the action but hands control back to the application;
  the user can review and modify parameters before the application executes

**AWS Services for HITL orchestration:**
- AWS Step Functions: orchestrate review and approval workflows with wait states and task tokens
- API Gateway: collect user feedback via webhooks or REST endpoints
- Amazon Augmented AI (A2I): managed human review workflows for ML predictions (confidence
  thresholds trigger human review automatically for built-in task types)
- Amazon SageMaker Ground Truth: labeled data via private, vendor, or Mechanical Turk workforces

### Tool Integrations

- **Strands API**: define custom tool behaviors with standardized function signatures; tools
  are Python functions decorated with `@tool`
- **Standardized function definitions**: JSON schema descriptions of tool inputs/outputs that
  the FM uses to decide when and how to call each tool
- **Lambda for tool hosting**: handles error catching, parameter validation, and response
  formatting before returning results to the agent loop

---

## Task 2.2: Implement Model Deployment Strategies

### Deployment Options Comparison

| Deployment Mode | Service | Best For | Key Characteristics |
|---|---|---|---|
| On-demand (serverless) | Amazon Bedrock | Variable/unpredictable traffic | Pay-per-token; no pre-provisioning |
| Provisioned Throughput | Amazon Bedrock | Consistent/high-volume traffic | Fixed hourly cost; guaranteed Model Units (MUs) |
| Custom endpoint | SageMaker AI | Fine-tuned or custom models | Full control; GPU/CPU instance selection |
| Serverless invocation | Lambda → Bedrock | Event-driven, low-frequency | No idle costs; cold-start considerations |
| Hybrid | Bedrock + SageMaker | Complex routing needs | Mix on-demand + provisioned |

### Amazon Bedrock Provisioned Throughput

- Purchase **Model Units (MUs)** that guarantee a fixed throughput level (input + output tokens
  per minute)
- Commitment options: no-commitment (hourly), 1-month, 6-month (increasing discounts)
- Supports base models and custom (fine-tuned) models
- Required for: consistent low-latency applications, high-throughput batch processing,
  production SLAs that require guaranteed capacity
- Use the provisioned model ARN as the `modelId` in InvokeModel / Converse API calls

### LLM-Specific Deployment Challenges

LLMs differ from traditional ML models in several critical ways:

- **Memory requirements**: LLMs require large amounts of GPU VRAM; container images must be
  sized accordingly
- **GPU utilization patterns**: token generation is inherently sequential (autoregressive);
  batching strategies must account for variable-length sequences
- **Token processing capacity**: measured in tokens per minute (TPM), not requests per minute (RPM)
- **Model loading strategies**: lazy loading, weight streaming, model sharding across multiple
  GPUs
- **Container-based deployment patterns**: containers must be optimized for GPU drivers, CUDA
  versions, and model-specific inference servers (TGI, vLLM, Triton)

### Optimized Deployment Approaches

- **Right-sizing**: match model size to task complexity; avoid using a 100B-parameter model
  for simple classification tasks
- **Smaller pre-trained models**: distilled or smaller models (e.g., Haiku vs. Opus, Nova Micro
  vs. Nova Pro) for routine queries that do not require maximum capability
- **API-based model cascading**: attempt the simplest/cheapest model first; escalate to a more
  capable model only if quality is insufficient
- **Cross-Region Inference (CRIS)**: Amazon Bedrock automatically routes to other regions within
  a geography (US, EU, APAC) for higher throughput and resilience during regional capacity
  constraints

---

## Task 2.3: Design and Implement Enterprise Integration Architectures

### Enterprise Connectivity Patterns

**API-based integrations with legacy systems:**
- REST or SOAP adapters via API Gateway or Lambda functions
- Transform legacy data formats to JSON before sending to Bedrock APIs
- Use SQS as a buffer to handle throughput mismatches between legacy systems and Bedrock limits

**Event-driven architectures (loose coupling):**
- Amazon EventBridge: route events from enterprise applications to Lambda functions that invoke FMs
- Amazon SQS: decouple producers from FM consumers; enables retries and dead-letter queues (DLQs)
- Amazon SNS: fan-out pattern for broadcasting AI-generated content to multiple downstream consumers
- DynamoDB Streams / Kinesis: trigger FM processing in response to real-time data changes

**Data synchronization patterns:**
- AWS AppFlow: managed data sync between SaaS apps (Salesforce, ServiceNow) and AWS
- AWS DataSync: sync on-premises or cross-cloud file data to S3 for FM consumption
- AWS Glue: ETL pipelines to prepare and synchronize structured data for knowledge bases

### Enhancing Existing Applications with GenAI

- **API Gateway + Lambda**: add a GenAI endpoint to an existing microservice architecture
  without modifying the core application
- **Lambda webhook handlers**: receive events from third-party systems (Slack, Jira, Salesforce)
  and trigger FM processing
- **EventBridge event-driven integrations**: applications emit events; EventBridge rules route
  them to FM-powered processors asynchronously

**Amazon Q Business** for internal knowledge tools:
- Pre-built connectors to 40+ data sources (S3, SharePoint, Salesforce, Confluence, Jira)
- Built-in semantic search across enterprise data
- Fine-grained access control via IAM Identity Center
- Amazon Q Apps: lightweight purpose-built apps employees create from Q Business conversations

### Secure Access Frameworks

- **Identity federation**: federate enterprise identity providers (Okta, Azure AD) with AWS IAM
  Identity Center; use SAML 2.0 or OIDC for single sign-on to FM services
- **Role-based access control (RBAC)**: separate IAM roles for read-only RAG access vs.
  full model invocation vs. fine-tuning operations
- **Least privilege API access**: scope IAM policies to specific Bedrock model ARNs, specific
  actions (bedrock:InvokeModel, bedrock:Retrieve), and specific resources
- **VPC endpoints (PrivateLink)**: keep FM API traffic on the AWS network; prevents data from
  traversing the public internet
- **Amazon Cognito**: user pool authentication for customer-facing GenAI applications

### Cross-Environment AI Solutions (Hybrid and Edge)

**AWS Outposts:**
- Brings AWS infrastructure (compute, storage, networking) into on-premises data centers
- Use case: organizations with strict data residency or sovereignty requirements who must keep
  sensitive data on-premises while still using FM APIs
- Supports EC2, ECS, EKS, Lambda, and RDS on-premises with the same AWS APIs
- Ideal for regulated industries (healthcare, financial services, government)

**AWS Wavelength:**
- AWS infrastructure embedded inside telecom provider 5G networks
- Enables ultra-low latency GenAI inference at the mobile network edge (sub-10ms)
- Use cases: real-time voice AI, AR/VR with AI assistance, connected vehicle AI

**Secure routing patterns:**
- AWS Direct Connect: dedicated network link from on-premises to AWS (bypasses public internet)
- Site-to-Site VPN: encrypted tunnel for secure cloud-to-on-premises communication
- AWS PrivateLink: private connectivity between VPCs and AWS services without public IPs

### CI/CD Pipelines for GenAI

A GenAI-specific CI/CD pipeline must handle both code changes AND model/prompt changes.

**Standard pipeline stages with GenAI additions:**

1. **Source**: CodeCommit, GitHub, or CodeStar Connections
2. **Build**: CodeBuild compiles code, runs linting, unit tests
3. **Security scan**: CodeBuild with SAST tools; scan for prompt injection vulnerabilities,
   hardcoded credentials, and IAM over-permissions
4. **GenAI-specific tests**: automated prompt regression tests; validate FM responses against
   golden datasets; check hallucination rates
5. **Deploy (dev/staging)**: CodeDeploy or CDK deploy with canary/blue-green strategies
6. **Approval gate**: manual or automated approval based on GenAI evaluation metrics
7. **Deploy (prod)**: rollback support; automated rollback triggered by CloudWatch alarms

**AWS Services:**
- CodePipeline: orchestrates the end-to-end pipeline
- CodeBuild: executes build, test, and scan stages
- CodeDeploy: manages deployment strategies (blue/green, canary, rolling)
- AWS CDK: infrastructure as code for pipeline and GenAI resources
- CloudFormation: deploy and version infrastructure stacks

**GenAI Gateway Architecture:**
- A centralized abstraction layer that sits between applications and FM APIs
- Provides: rate limiting, cost allocation, observability, request logging, model routing,
  security policy enforcement, and A/B testing
- Implemented using: API Gateway (entry point) → Lambda (business logic / routing) → Bedrock
- Enables model swapping without changing downstream application code

---

## Task 2.4: Implement Foundation Model API Integrations

### Bedrock API Families

| API Family | Use Case | Endpoint |
|---|---|---|
| Invoke API | Single transactions; large payloads; direct model access | bedrock-runtime |
| Converse API | Multi-turn chat; unified interface across all models | bedrock-runtime |
| Responses API | Stateful conversations; built-in tool use; OpenAI-compatible | bedrock-mantle |
| Chat Completions | OpenAI migration; stateless multi-turn | bedrock-mantle |
| StartAsyncInvoke | Long-running batch inference; video/image generation | bedrock-runtime |

**Key distinction:** The Converse API provides a normalized request/response format that
works across all Bedrock-supported models — you can switch models without changing application
code. The InvokeModel API requires model-specific JSON payloads.

### Synchronous vs. Asynchronous Patterns

**Synchronous (InvokeModel / Converse):**
- Application sends request and blocks until the full response is returned
- Suitable for: interactive chatbots, low-latency queries
- Risk: timeouts for long-running generation tasks

**Streaming (InvokeModelWithResponseStream / ConverseStream):**
- Response is returned as a sequence of events (token chunks) as the model generates them
- Reduces perceived latency significantly; user sees text appear progressively
- Implementation options:
  - **API Gateway WebSocket API**: bidirectional real-time connection (persistent)
  - **Server-Sent Events (SSE)**: unidirectional server-to-client streaming over HTTP
  - **API Gateway chunked transfer encoding**: for REST-based streaming responses
- Bedrock streaming event types: messageStart, contentBlockStart, contentBlockDelta,
  contentBlockStop, messageStop, metadata

**Asynchronous (SQS + Lambda):**
- Application sends request to SQS; Lambda polls the queue and calls Bedrock; result stored
  in DynamoDB or S3; application polls or subscribes for results
- Suitable for: batch processing, long-running tasks, fire-and-forget workflows
- Provides built-in retry, DLQ support, and decoupling

**StartAsyncInvoke:**
- Submit model invocation and receive an `invocationArn` immediately
- Poll for results or receive notification when complete
- Used for: video generation (Nova Reel), large document processing, image generation

### Resilient FM Systems

**Throttling and Error Handling:**

Amazon Bedrock returns two primary error types that require resilience handling:

- **429 ThrottlingException**: account quota exceeded (RPM or TPM limits)
  - Mitigation: exponential backoff with jitter, request rate limiting, quota increase requests
- **503 ServiceUnavailableException**: temporary service unavailability
  - Mitigation: exponential backoff, circuit breaker pattern, cross-region failover

**Exponential Backoff with Jitter (AWS SDK built-in):**
- On each retry, wait `min(cap, base * 2^attempt) + random(0, jitter)`
- Jitter prevents "thundering herd" problems where all retries hit simultaneously
- AWS SDKs include built-in retry logic; configure `max_attempts` and `retry_mode`

**Circuit Breaker Pattern:**
- Monitor failure rates for FM API calls
- When failures exceed a threshold, "open" the circuit: stop calling the failing endpoint
  and return a fallback response immediately
- After a cool-down period, allow a single test request; if it succeeds, "close" the circuit

**Graceful Degradation:**
- If primary model is unavailable, fall back to a simpler/smaller model
- If all FM APIs are unavailable, return a cached response or a static fallback message
- Use Amazon Bedrock Cross-Region Inference for automatic regional failover

**AWS X-Ray for Observability:**
- Distributed tracing across Lambda → API Gateway → Bedrock invocations
- Identifies latency hotspots and error rates across service boundaries
- Bedrock supports X-Ray active tracing on Lambda functions invoking it

### Intelligent Model Routing

Organizations often need to route requests to different models based on context:

**Static Routing:**
- Configuration-based rules in application code or AWS AppConfig
- Example: route all SQL generation requests to model A; route all creative writing to model B
- Simple, predictable, low overhead

**Dynamic Content-Based Routing:**
- Step Functions state machine evaluates request properties to select the target model
- Lambda function classifies input (using a lightweight classifier model or rule engine)
- API Gateway request transformations apply routing headers based on request parameters

**Intelligent Prompt Routing (Amazon Bedrock feature):**
- Routes requests within a model family (e.g., Haiku vs. Sonnet) based on predicted response
  quality for each specific prompt
- Uses advanced prompt matching and model understanding to predict which model will perform best
- Can reduce costs by up to 30% without sacrificing accuracy
- Supports: Anthropic Claude family, Meta Llama family, Amazon Nova family
- Each request is fully traceable for debugging
- Default prompt routers: pre-configured by Bedrock; ready to use out of the box
- Configured prompt routers: user-defined routing criteria and fallback model

**Metric-Based Routing:**
- CloudWatch metrics drive routing decisions (e.g., route to cheaper model when cost budget
  is exceeded for the hour)

---

## Task 2.5: Implement Application Integration Patterns and Development Tools

### GenAI-Specific API Gateway Patterns

API Gateway requires special configuration for GenAI workloads:

- **Streaming responses**: configure integration response timeout to 29 seconds maximum;
  use WebSocket APIs for truly real-time streaming; use chunked transfer encoding for
  HTTP streaming
- **Token limit management**: validate request payload sizes at the API Gateway level;
  return 413 errors before the request reaches Lambda/Bedrock for oversized requests
- **Retry strategies**: implement retry logic in the client or use SQS for automatic retries;
  do not retry at the API Gateway level for non-idempotent FM calls
- **Request validation**: API Gateway request validators enforce required parameters and
  JSON schema compliance before forwarding to Lambda

### Accessible AI Interfaces

**AWS Amplify AI Kit:**
- Frontend SDK for building AI-powered web/mobile apps in TypeScript
- Pre-built `<AIConversation>` component: handles real-time subscriptions, multi-turn chat
  history, UI state management
- `conversation` API: maintains persistent conversation history tied to user accounts
- Connects to Amazon Bedrock models via Amplify backend
- Supports React, Next.js, Vue, Angular, React Native, Flutter, Swift, Android

**OpenAPI Specifications for API-First Development:**
- Define GenAI API contracts in OpenAPI 3.0 before implementation
- API Gateway imports OpenAPI specs to auto-generate REST APIs
- Enables SDK generation for client teams; establishes clear interface boundaries
- Supports versioning strategies for prompt/model changes

**Amazon Bedrock Prompt Flows (No-Code Builder):**
- Visual drag-and-drop builder in the AWS Console and Bedrock Studio
- Connect prompts, FMs, Lambda functions, knowledge bases, and other nodes visually
- Supports: conditional branching, loops, parallel execution, code hooks
- Version flows for rollback and A/B testing
- Deploy flows via aliases that point to immutable versions
- Use cases: multi-step document processing, sequential prompt chains, automated workflows

### Business System Enhancements

**CRM Enhancements (Lambda):**
- Lambda functions triggered by CRM events (Salesforce webhooks) invoke Bedrock to
  generate personalized responses, summaries, or recommendations
- Results written back to CRM via API calls within the Lambda function

**Document Processing (Step Functions):**
- Step Functions orchestrate multi-step document workflows:
  1. S3 upload → EventBridge trigger → Step Functions execution
  2. Textract / Bedrock Data Automation extracts structured data
  3. Confidence score evaluation: high-confidence → store; low-confidence → A2I human review
  4. Validated data stored in downstream systems

**Amazon Bedrock Data Automation:**
- Extracts insights from unstructured multimodal content (documents, images, audio, video)
- Returns structured output with confidence scores and visual grounding
- Use: invoice processing, claims processing, contract analysis, media metadata extraction
- Invoke via `InvokeDataAutomationAsync` API with a project ARN
- Projects group standard and custom output configurations; support LIVE and DEVELOPMENT stages

**Amazon Q Business for Internal Knowledge Tools:**
- Data sources: S3, SharePoint, Confluence, Salesforce, Jira, ServiceNow (40+ connectors)
- Built-in semantic retrieval (Agentic RAG), conversation history, access controls
- Topic controls: restrict responses to specific domains; block sensitive topics
- Amazon Q Apps: no-code apps built from Q Business conversations; automate repetitive tasks

### Developer Productivity

**Amazon Q Developer:**
- AI-powered assistant for developers embedded in IDEs (VS Code, JetBrains, CLI)
- Capabilities:
  - Code generation and completion (inline suggestions)
  - Code explanation and documentation
  - Unit test generation
  - Bug finding and fixing
  - Code transformation (e.g., Java version upgrades)
  - Security vulnerability scanning
  - API call suggestions for AWS services
  - GenAI-specific error pattern recognition (skill 2.5.6)
- Integrated MCP support for standardized tool access in development workflows
- CloudWatch Logs Insights queries: Q Developer can help write and explain complex queries
  for analyzing FM prompt/response logs

### Advanced GenAI Application Patterns

**Prompt Chaining (Amazon Bedrock):**
- The output of one FM call becomes the input to the next
- Enables complex, multi-step reasoning that exceeds a single context window
- Implemented via: Step Functions (orchestration), Lambda (glue code), Bedrock Prompt Flows

**Agent Design Patterns (Step Functions):**
- Step Functions orchestrates agent loops as state machines
- States: Choose (routing), Task (tool call), Wait (human review), Parallel (multi-model), Map (batch)
- Error handling with Catch and Retry blocks

**Strands and AWS Agent Squad for Orchestration:**
- Strands: model-driven, framework-level orchestration; agents define their own tool use sequences
- AWS Agent Squad: higher-level multi-agent coordination; manage agent pools and delegation
- Combined: Strands for individual agent logic; Agent Squad for fleet-level coordination

### Troubleshooting GenAI Applications

**Key Tools:**

| Problem | Tool | Approach |
|---|---|---|
| Poor response quality | CloudWatch Logs Insights | Query stored prompt/response pairs; identify failure patterns |
| Latency issues | AWS X-Ray | Trace end-to-end; identify which service boundary adds the most latency |
| Error pattern recognition | Amazon Q Developer | Ask Q Developer to analyze error logs and suggest fixes |
| Prompt regressions | Bedrock Prompt Management | Version prompts; compare A/B test results |
| Tool call failures | CloudWatch + X-Ray | Trace Lambda invocations from agent action groups |

**CloudWatch Logs Insights queries for GenAI:**
- Filter by model ID to analyze per-model performance
- Parse JSON log fields for inputTokenCount, outputTokenCount, latency
- Identify high-latency invocations with `stats avg(latency) by modelId`

**Bedrock Model Invocation Logs:**
- Enable on the Bedrock console; logs all request/response data to CloudWatch and/or S3
- Critical for: debugging hallucinations, auditing prompt content, cost allocation by use case

---

## Key Services Quick Reference for Domain 2

### Agentic AI

| Service | Role |
|---|---|
| Amazon Bedrock Agents | Managed ReAct-based agent platform |
| Amazon Bedrock AgentCore | Deploy/host agents at scale; modular services |
| Strands Agents (SDK) | Open-source model-driven agent framework |
| AWS Agent Squad | Multi-agent coordination and fleet management |
| MCP (protocol) | Standardized agent-tool communication |
| AWS Step Functions | Orchestrate agent loops and multi-step workflows |
| AWS Lambda | Host tools, MCP servers (stateless), action groups |
| Amazon ECS | Host MCP servers (complex/stateful tools) |
| Amazon Augmented AI | Human review workflows for agent decisions |

### Model Deployment

| Service | Role |
|---|---|
| Amazon Bedrock (on-demand) | Serverless, pay-per-token FM inference |
| Amazon Bedrock Provisioned Throughput | Guaranteed capacity via Model Units |
| Amazon SageMaker AI endpoints | Custom model hosting; full infrastructure control |
| Amazon Bedrock Cross-Region Inference | Automatic regional failover and load balancing |

### Enterprise Integration

| Service | Role |
|---|---|
| Amazon API Gateway | Entry point for GenAI APIs; request validation; routing |
| AWS Lambda | Glue code; webhook handlers; tool execution |
| Amazon EventBridge | Event-driven routing from enterprise apps to GenAI |
| Amazon SQS | Async decoupling; retry and DLQ for FM calls |
| Amazon SNS | Fan-out distribution of AI-generated content |
| AWS AppFlow | SaaS-to-AWS data synchronization |
| AWS Outposts | On-premises data residency with AWS APIs |
| AWS Wavelength | 5G edge deployments for ultra-low latency |
| AWS PrivateLink / VPC Endpoints | Private FM API access without internet exposure |
| AWS CodePipeline / CodeBuild | CI/CD for GenAI applications |
| Amazon Q Business | Enterprise knowledge assistant with 40+ connectors |

### API and Application Patterns

| Service | Role |
|---|---|
| Amazon Bedrock Converse API | Unified multi-model chat interface |
| Amazon Bedrock Invoke API | Direct model access with full payload control |
| Amazon Bedrock Prompt Flows | Visual no-code workflow builder for FM pipelines |
| Amazon Bedrock Data Automation | Structured extraction from multimodal content |
| AWS Amplify AI Kit | Frontend components for AI-powered apps |
| Amazon Q Developer | AI coding assistant; error analysis; code generation |
| AWS X-Ray | Distributed tracing for GenAI API call chains |
| Amazon CloudWatch Logs Insights | Query and analyze FM prompt/response logs |

---

## Common Exam Scenarios and Correct Answers

**Q: A chatbot must stream responses token-by-token to the user. What is the correct approach?**
Use Amazon Bedrock's ConverseStream or InvokeModelWithResponseStream API. Front it with API
Gateway using a WebSocket API for bidirectional real-time communication, or use server-sent
events (SSE) for one-way streaming.

**Q: An FM API call is failing intermittently with 429 errors. How should the application handle this?**
Implement exponential backoff with jitter using the AWS SDK retry configuration. Consider
purchasing Provisioned Throughput if the workload is consistent, or use Amazon Bedrock
Intelligent Prompt Routing to shift load to smaller models during peak periods.

**Q: A company needs to run GenAI inference on data that cannot leave their on-premises data center. What architecture should they use?**
AWS Outposts brings AWS infrastructure (including EC2 for self-hosted model inference, or
EKS/ECS for containerized models) on-premises. For managed FM access, use Direct Connect to
reach Bedrock APIs over a private network, combined with VPC endpoints and IAM policies that
restrict access to specific data.

**Q: An organization wants to route simple queries to a cheap model and complex queries to a powerful model. What is the best approach?**
Use Amazon Bedrock Intelligent Prompt Routing (for within-family routing with up to 30% cost
savings) or implement a custom Step Functions state machine that classifies the query and routes
to the appropriate model endpoint.

**Q: A developer wants to add a GenAI chat interface to an existing React web application quickly. What is the fastest approach?**
Use the AWS Amplify AI Kit with the pre-built `<AIConversation>` component. It handles
real-time subscriptions, conversation history, and UI state management out of the box with
minimal configuration.

**Q: An enterprise needs to build a CI/CD pipeline for a GenAI application that includes prompt testing and security scanning. Which services are involved?**
CodePipeline (orchestration), CodeBuild (build, test, security scan), CodeDeploy or CDK
(deployment), CloudWatch alarms (rollback triggers), and automated prompt regression tests
against golden datasets as a quality gate stage.

**Q: An agent must stop after 10 tool calls to prevent runaway execution. How is this implemented?**
Use Step Functions with a counter in the state machine context. Each iteration increments the
counter; a Choice state checks if the counter exceeds 10 and routes to a termination state
if so. Lambda functions can implement timeout mechanisms for individual tool calls.

**Q: An application needs to call three specialized agents in parallel and merge their results. What architecture achieves this?**
AWS Step Functions Parallel state: fan out to three Lambda functions (each calling a specialized
Bedrock agent), then aggregate results in a subsequent state using custom aggregation logic.
This matches the model coordination / ensemble pattern from skill 2.1.4.

**Q: A company wants to give their employees a chat interface over internal SharePoint, Confluence, and Salesforce data. What is the fastest path?**
Amazon Q Business with pre-built connectors for SharePoint, Confluence, and Salesforce.
Configure IAM Identity Center for SSO. Use Amazon Q Apps for task-specific automations.

---

## Important Notes and Exam Tips

- **Strands Agents** is the preferred AWS-native open-source agent SDK as of 2025. Expect
  questions about its model-first approach, MCP integration, and deployment on Lambda/ECS/AgentCore.

- **MCP = Model Context Protocol**: Always used for standardizing agent-tool communication.
  Lambda hosts stateless MCP servers; ECS hosts complex/long-running MCP servers.

- **Bedrock Converse API** is the preferred unified API for multi-turn conversations. It
  normalizes request/response format across all Bedrock models.

- **Provisioned Throughput** = guaranteed capacity via Model Units (MUs). Required for
  predictable high-volume workloads. Billed hourly even if not used.

- **Intelligent Prompt Routing** routes within a model family (e.g., Haiku ↔ Sonnet) based
  on predicted per-prompt quality; can reduce cost up to 30%.

- **Step Functions** is the orchestration backbone for agentic workflows, CI/CD gates,
  document processing, and human-in-the-loop patterns.

- **AWS Outposts** = on-premises data residency. **AWS Wavelength** = 5G/telecom edge.
  Know when to use each based on the data sovereignty vs. latency constraint.

- **Bedrock Data Automation** processes multimodal content (documents, images, audio, video)
  into structured output with confidence scores. Pairs with SageMaker A2I for human review
  of low-confidence extractions.

- **Amazon Q Business** targets enterprise employees (internal knowledge assistant).
  **Amazon Q Developer** targets software developers (code generation, debugging). Know which
  is correct for each scenario.

- **GenAI Gateway pattern**: centralized API Gateway + Lambda layer that provides rate limiting,
  routing, observability, and security policy enforcement across all FM API calls.

- **Exponential backoff with jitter** is the correct answer for handling 429 and 503 errors
  from Bedrock. AWS SDKs have built-in retry logic — configure `max_attempts` and `retry_mode`.

- **ReAct pattern** = the agent reasoning loop. Bedrock Agents uses ReAct internally; Step
  Functions implements custom ReAct loops for non-managed agents.

- **Human-in-the-Loop**: Step Functions task tokens enable pause-and-wait-for-human patterns;
  Amazon A2I provides built-in UI and workforce management for review tasks.

- For **streaming real-time responses**, the answer is almost always ConverseStream/InvokeModelWithResponseStream + WebSocket API Gateway or SSE.

- **Bedrock Prompt Flows** = visual no-code workflow builder for chaining prompts and AWS
  services. Versions are immutable snapshots; deploy via aliases.
