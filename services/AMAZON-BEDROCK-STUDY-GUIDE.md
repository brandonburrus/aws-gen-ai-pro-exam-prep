# Amazon Bedrock -- Comprehensive Study Guide (AIP-C01)

Amazon Bedrock is the **most heavily tested service** on the AWS Certified Generative AI Developer - Professional exam. It appears across virtually every domain and task statement. This guide covers the core Bedrock service itself; Knowledge Bases, Agents, and Flows are covered separately.

---

## 1. Service Overview

Amazon Bedrock is a **fully managed service** that provides secure API access to high-performing foundation models (FMs) from multiple AI providers. It lets you build and scale generative AI applications without managing infrastructure.

### What Bedrock Does

- Provides a **single unified API** to access 100+ FMs from 17+ providers
- Supports text generation, image generation, embeddings, video generation, speech-to-speech, and multimodal understanding
- Enables model customization (fine-tuning, continued pre-training) with your own data
- Offers content safety controls through Guardrails
- Provides model evaluation capabilities (automatic, human, LLM-as-a-judge)
- Supports document and media processing through Data Automation
- Handles scaling, security, and compliance as a fully managed service

### When to Use Bedrock

- You need access to **multiple FM providers** through a single API
- You want a **serverless, fully managed** inference experience (no infrastructure to manage)
- You need **enterprise security**: data never leaves your account, never used to train base models
- You need **content safety controls** (Guardrails) built into the inference pipeline
- You want to **switch between models** without rewriting application code (Converse API)
- You require **compliance**: SOC, ISO, HIPAA-eligible, FedRAMP High, GDPR

### When NOT to Use Bedrock

- You need to **train a model from scratch** -- use SageMaker AI instead
- You need to host a **custom open-weight model** with full control over infrastructure -- use SageMaker AI endpoints
- You need models **not available on Bedrock** -- check Bedrock Marketplace first, then SageMaker
- You need **real-time fine-tuning** during inference -- Bedrock fine-tuning is an offline batch process

---

## 2. Foundation Models Available

### Model Providers and Key Families

| Provider | Key Models | Primary Use Cases |
|---|---|---|
| **Amazon** | Nova Micro, Nova Lite, Nova Pro, Nova Premier, Nova Canvas, Nova Reel, Nova Sonic, Titan Embeddings V2, Titan Image Generator | Text, multimodal, image gen, video gen, speech-to-speech, embeddings |
| **Anthropic** | Claude Opus 4.6, Claude Sonnet 4.6, Claude Haiku 4.5, Claude Opus 4.5 | Complex reasoning, coding, analysis, agentic workflows |
| **Meta** | Llama 4 Maverick, Llama 4 Scout, Llama 3.3 70B, Llama 3.1 (8B/70B/405B) | Open-weight text generation, multilingual |
| **Mistral AI** | Mistral Large 3, Devstral 2, Ministral, Pixtral Large | Code, multilingual, vision |
| **Cohere** | Command R/R+, Embed v4, Rerank 3.5 | RAG, search, embeddings, reranking |
| **AI21 Labs** | Jamba 1.5 Large/Mini | Long-context text generation |
| **Stability AI** | Stable Image (various) | Image generation and manipulation |
| **DeepSeek** | DeepSeek-R1, DeepSeek-V3.1, DeepSeek-V3.2 | Reasoning, code |
| **OpenAI** | GPT-OSS 20B/120B, GPT-OSS Safeguard | Text generation, safety |
| **Google** | Gemma 3 (4B/12B/27B) | Lightweight inference |
| **Qwen** | Qwen3 235B, Qwen3 32B, Qwen3 Coder | Code, multilingual |
| **Writer** | Palmyra X4, Palmyra X5 | Enterprise text |
| **TwelveLabs** | Marengo Embed | Video embeddings |
| **Others** | MiniMax, Moonshot (Kimi), NVIDIA Nemotron | Various |

### Model Selection Considerations (Exam-Critical)

- **Claude Opus 4.6**: Most capable model for complex tasks, highest cost
- **Claude Sonnet 4.6**: Best balance of capability and cost for most production workloads
- **Claude Haiku 4.5**: Fastest, cheapest Claude model for high-volume, latency-sensitive tasks
- **Nova Micro**: Text-only, lowest latency and cost for simple text tasks
- **Nova Lite**: Multimodal (text + image + video), low cost
- **Nova Pro**: Best balance for multimodal tasks within Amazon's family
- **Nova Premier**: Complex reasoning, agentic workflows, model distillation teacher
- **Titan Embeddings V2**: Cost-effective embeddings for RAG
- **Cohere Embed v4**: Multimodal embeddings with leading retrieval quality

---

## 3. Key APIs

Amazon Bedrock provides **four main API families** for inference. Knowing when to use each is heavily tested.

### API Family Comparison

| API | Endpoint | Best For | Key Feature |
|---|---|---|---|
| **Responses API** | `bedrock-mantle.{region}.amazonaws.com` | Stateful conversations, agentic apps | Built-in tool use, multimodal, stateful -- **recommended for new apps** |
| **Chat Completions** | `bedrock-mantle.{region}.amazonaws.com` | Stateless multi-turn chat | OpenAI-compatible, lightweight |
| **Converse / ConverseStream** | `bedrock-runtime.{region}.amazonaws.com` | Multi-turn chat, model portability | Unified interface across all Bedrock models |
| **InvokeModel / InvokeModelWithResponseStream** | `bedrock-runtime.{region}.amazonaws.com` | Single transactions, embeddings, image gen | Direct model access, full control over request/response format |

### Converse API (Exam Priority: HIGH)

The Converse API provides a **consistent, model-agnostic interface** for conversational inference. Write code once, switch models by changing the `modelId`.

**Key characteristics:**
- Unified request/response format across all models that support messages
- Supports `Converse` (synchronous) and `ConverseStream` (streaming)
- Permission: `bedrock:InvokeModel` for Converse, `bedrock:InvokeModelWithResponseStream` for ConverseStream
- Supports: text, images, documents, video, tool use, guardrails, prompt caching
- Automatically applies model-specific prompt templates (e.g., for Mistral, Meta)
- Returns standardized `usage` (inputTokens, outputTokens) and `metrics` (latencyMs)

**Request structure:**
```
modelId (required) -- model ID, inference profile ID, or provisioned model ARN
messages[] -- array of {role, content[]} objects
  role: "user" | "assistant"
  content[]: text | image | document | video | toolUse | toolResult | cachePoint
system[] -- system prompt content blocks
inferenceConfig -- temperature, maxTokens, topP, stopSequences
toolConfig -- tool definitions for function calling
guardrailConfig -- guardrail ID, version, and trace settings
additionalModelRequestFields -- model-specific parameters (e.g., top_k for Claude)
requestMetadata -- custom metadata for invocation logs
serviceTier -- "standard" | "priority" | "flex"
```

**Response structure:**
- `output.message` -- the generated message with role and content
- `stopReason` -- "end_turn", "tool_use", "max_tokens", "stop_sequence", "guardrail_intervened"
- `usage` -- { inputTokens, outputTokens, totalTokens }
- `metrics` -- { latencyMs }
- `trace` -- guardrail assessment details (if trace enabled)

### InvokeModel API (Exam Priority: HIGH)

Direct, model-specific API for single-turn inference.

**Key characteristics:**
- Request body is **model-specific JSON** -- different format for Claude vs. Llama vs. Titan
- Returns raw model response in the format specified by `contentType`
- Best for: embeddings, image generation, single-turn text, or when you need model-specific features
- Permission: `bedrock:InvokeModel`
- Does NOT support documents or video directly (Converse API restriction applies)

**When to use InvokeModel vs. Converse:**

| Scenario | Use |
|---|---|
| Multi-turn conversation | Converse |
| Need to switch models easily | Converse |
| Generating embeddings | InvokeModel |
| Image generation | InvokeModel |
| Need model-specific parameters not in Converse | InvokeModel |
| Consistent interface across models | Converse |
| Legacy integration with model-specific format | InvokeModel |

### Streaming APIs

- **ConverseStream**: Streaming version of Converse. Returns events: `messageStart`, `contentBlockStart`, `contentBlockDelta`, `contentBlockStop`, `messageStop`, `metadata`
- **InvokeModelWithResponseStream**: Streaming version of InvokeModel. Returns raw chunks.
- The **AWS CLI does NOT support streaming operations** -- must use SDK
- Check `responseStreamingSupported` field from `GetFoundationModel` to confirm model support

### Async and Batch APIs

- **StartAsyncInvoke**: For long-running operations like video generation. Returns an `invocationArn` immediately; results stored in S3. Permission: `bedrock:InvokeModel`
- **Batch Inference**: Process thousands of prompts asynchronously. Input/output via S3. Supports both InvokeModel and Converse format. NOT supported for provisioned models.
- **InvokeModelWithBidirectionalStream**: Full-duplex streaming for real-time speech-to-speech (Nova Sonic)

---

## 4. Sub-services and Features

### 4.1 Bedrock Guardrails

Configurable safeguards that work with **any** FM (Bedrock-hosted, self-hosted, or third-party via `ApplyGuardrail` API).

**Six safeguard policies:**

| Policy | What It Does | Action Options |
|---|---|---|
| **Content Filters** | Detects harmful text/image content across categories: Hate, Insults, Sexual, Violence, Misconduct, Prompt Attacks | Block, Detect (no action) |
| **Denied Topics** | Blocks specific topics you define | Block |
| **Word Filters** | Exact-match blocking of custom words/phrases and profanity | Block |
| **Sensitive Information Filters** | Detects PII (names, SSNs, emails, etc.) | Block or Mask (anonymize with tags) |
| **Contextual Grounding Checks** | Detects hallucinations by checking if responses are grounded in source material | Block, Detect |
| **Automated Reasoning Checks** | Validates responses against logical rules and policies using formal mathematical techniques | Block, Detect |

**Tiers:**
- **Classic Tier**: Basic content filters and denied topics
- **Standard Tier**: Enhanced contextual understanding, typo detection, 60+ language support, code domain protection, distinguishes jailbreaks from prompt injection. Requires opt-in to cross-Region inference.

**Key exam points:**
- Guardrails can be applied in **synchronous** or **asynchronous** streaming mode
- In **synchronous** streaming mode: buffers chunks, applies policies before sending (more latency, better accuracy)
- In **asynchronous** streaming mode: sends chunks immediately, applies policies in background (no latency impact, but may initially pass inappropriate content). Does NOT support masking.
- `ApplyGuardrail` API: Apply guardrails **independently** without invoking a model -- use for self-hosted or third-party models
- Blocked content appears as plain text in model invocation logs (can be disabled)
- Guardrails support **cross-Region inference** for guardrail policy evaluation
- Image content filtering supported (max 8000x8000 px, 4 MB, 20 images per request)

### 4.2 Bedrock Data Automation (BDA)

Automates transformation of **unstructured multimodal data** (documents, images, video, audio) into structured formats using generative AI.

**Key capabilities:**
- Document processing: parse, classify, extract structured data from PDFs, forms, invoices
- Media analysis: video summaries, unsafe content detection, text extraction, brand classification
- Supports documents up to 3,000 pages
- Provides **confidence scores** and **bounding box** data for extracted fields
- **Blueprints**: Define custom extraction schemas (what fields to extract)
- **Projects**: Group standard and custom output configurations; support LIVE and DEVELOPMENT stages

**APIs:**
- `InvokeDataAutomationAsync` -- asynchronous processing, returns invocation ARN
- `InvokeDataAutomation` -- synchronous processing for documents and images
- `CreateBlueprint`, `CreateDataAutomationProject` -- configuration

**Integration with RAG:** BDA can be used as a parser for Knowledge Bases to convert unstructured docs into RAG-ready chunks.

### 4.3 Bedrock Model Evaluation

Evaluate and compare FMs for your specific use cases.

**Three evaluation methods:**

| Method | Description | Use Case |
|---|---|---|
| **Automatic (Programmatic)** | Uses predefined metrics (accuracy, robustness, toxicity) with built-in or custom datasets | Quick, objective model comparison |
| **Human Evaluation** | Human raters assess model outputs using custom metrics (relevance, style, brand voice) | Subjective quality assessment |
| **LLM-as-a-Judge** | Uses a second LLM to evaluate model responses with metrics like correctness, completeness, harmfulness | Human-like quality at lower cost |

**Key exam points:**
- Can evaluate **any model** on Bedrock: serverless, Marketplace, customized, distilled, imported, prompt routers
- "Bring your own inference responses": Evaluate models hosted anywhere (not just Bedrock)
- RAG evaluation: Evaluate retrieval quality and generation quality of Knowledge Bases
- **Compare feature**: View results of multiple evaluation jobs side-by-side
- Supported use cases: text generation, classification, Q&A, summarization

### 4.4 Model Invocation Logging

Collects invocation logs, model input data, and model output data for all invocations in an account/Region.

**Configuration:**
- **Disabled by default** -- must be explicitly enabled
- Destinations: **CloudWatch Logs** and/or **Amazon S3**
- S3 is required for large data (images, embeddings, video) and binary outputs
- Can selectively enable: text, image, embedding, video data delivery
- Logs stored until logging configuration is deleted

**APIs:**
- `PutModelInvocationLoggingConfiguration`
- `GetModelInvocationLoggingConfiguration`
- `DeleteModelInvocationLoggingConfiguration`

**Exam tip:** S3 bucket must be in the **same Region** as the logging configuration. If using SSE-KMS, add a KMS encryption policy to the bucket.

### 4.5 Cross-Region Inference (CRIS)

Automatically routes inference requests to other AWS Regions with available capacity for higher throughput.

**Two types:**

| Type | Data Boundary | Throughput | Cost |
|---|---|---|---|
| **Geographic CRIS** | Stays within geographic boundary (e.g., US, EU) | Higher than single-region | Standard pricing |
| **Global CRIS** | Any supported commercial AWS Region worldwide | Highest available | ~10% cost savings |

**Key exam points:**
- **No additional cost** for using cross-Region inference (geographic); ~10% savings for global
- All data transmitted **stays on AWS network**, encrypted in transit between Regions
- CloudTrail logs **only in the source Region** (simplifies monitoring)
- Can route to Regions **not manually enabled** in your account
- Identified by inference profile IDs: geographic profiles use region prefix, global profiles use `global.` prefix
- Supported for: on-demand inference, batch inference, agents, model evaluation, prompt management, prompt flows
- **IAM requirements**: Three-part policy for global CRIS (regional inference profile, regional FM, global FM)
- **SCP considerations**: Must update `aws:RequestedRegion` conditions to allow `"unspecified"` for global CRIS
- Prioritizes source Region when capacity is available (minimizes latency)

**Quota management:**
- Quotas measured in Tokens Per Minute (TPM) and Requests Per Minute (RPM)
- **Burndown rate**: Output tokens consume **5x** more quota than input tokens
- Request quota increases through Service Quotas console in the **source** Region

### 4.6 Provisioned Throughput

Purchase dedicated throughput capacity for a model to guarantee consistent performance.

**Two purchasing methods:**
- **By Model Units (MUs)**: Request MUs through AWS Support, then purchase via console or `CreateProvisionedModelThroughput` API
- **By Tokens**: Purchase tokens-per-minute capacity directly

**Key characteristics:**
- Returns a `provisionedModelArn` to use as `modelId` in inference calls
- Can be used with InvokeModel, InvokeModelWithResponseStream, Converse, ConverseStream
- Can be associated with agent aliases
- Commitment terms available (1-month, 6-month) for discounts, or no-commitment
- Custom models **require** Provisioned Throughput for inference
- **Batch inference is NOT supported** for provisioned models
- Can change associated model only for custom model Provisioned Throughputs

**When to use:**
- Predictable, high-volume production workloads
- Need guaranteed throughput that won't be throttled
- Running custom (fine-tuned) models -- they require it

### 4.7 Service Tiers

On-demand inference offers four tiers to balance cost and performance:

| Tier | Pricing | Latency | Best For |
|---|---|---|---|
| **Reserved** | Fixed monthly per 1K TPM | Guaranteed, 99.5% uptime SLA | Mission-critical, predictable workloads; 1-month or 3-month reservations |
| **Priority** | Standard + premium | Up to 25% better OTPS latency | Customer-facing apps, real-time interaction |
| **Standard** | Base rate | Consistent | General-purpose AI tasks |
| **Flex** | Discounted | Higher latency tolerated | Non-urgent: evaluations, summarizations, agentic workflows |

Set the tier **per API call** using the `serviceTier` parameter.

### 4.8 Model Customization

Customize FMs with your own data to improve domain-specific performance.

**Two methods:**

| Method | Data Type | Purpose | Supported Models |
|---|---|---|---|
| **Fine-tuning** | Labeled input-output pairs (JSONL from S3) | Teach model specific task behavior | Claude 3 Haiku, Llama, Nova, Titan, Cohere, Mistral |
| **Continued Pre-training** | Unlabeled domain text | Expand model knowledge for a domain/industry | Amazon Titan, Nova |

**Additional methods via SageMaker AI recipes for Nova:**
- Supervised Fine-Tuning (PEFT, FFT)
- Alignment (DPO, PPO)
- Knowledge Distillation
- Reinforcement Fine-Tuning (RFT)

**Key exam points:**
- Both create a **private copy** of the FM accessible only to your account
- Data transferred securely through **VPC** 
- Custom models **require Provisioned Throughput** for inference
- Training and validation data stored in **S3**
- Encrypted with **AWS KMS** (customer-managed keys supported)
- **EventBridge** integration for job status change notifications
- Use **canaries** in training data + prompt logging to detect training data leakage

### 4.9 Bedrock Marketplace

Access and deploy additional models from third-party providers not available as serverless Bedrock models.

**How it works:**
- Subscribe to a model in the Bedrock Marketplace catalog
- Deploy to a **SageMaker AI endpoint** (specify instance type and count)
- Register the endpoint with Bedrock
- Invoke using standard Converse or InvokeModel APIs
- Deployment takes approximately 10-15 minutes

**Key points:**
- Endpoints hosted by SageMaker AI but accessed through Bedrock APIs
- Supports `Converse` and `InvokeModel` operations
- Do NOT modify endpoints directly in SageMaker (may cause failures) -- use Bedrock Marketplace console/API
- If endpoint fails due to SageMaker modifications, deregister and reregister

### 4.10 Intelligent Prompt Routing

Dynamically routes prompts to different models within a model family based on complexity.

- Routes simple prompts to smaller/cheaper models, complex prompts to larger models
- Can reduce costs by up to **30%** without compromising accuracy
- Uses a prompt router that you configure

### 4.11 Model Distillation

Creates smaller, faster, more cost-effective models from larger teacher models.

- Up to **500% faster** and **75% less expensive** than original models
- Less than **2%** accuracy loss
- Useful for RAG and other specific use cases where you can trade minimal accuracy for significant speed/cost gains
- Nova Premier serves as a teacher model for distillation

### 4.12 Prompt Caching

Caches frequently used prompt prefixes to reduce latency and cost.

**Key characteristics:**
- Reduces inference latency by up to **85%**
- Reduces input token costs by up to **90%**
- Supported in Converse, ConverseStream, InvokeModel, InvokeModelWithResponseStream
- Uses **cache checkpoints** to define what to cache
- Cache has a **TTL**: most models support 5-minute TTL; some support extended 1-hour TTL
- TTL resets with each cache hit; cache expires after TTL window with no hits
- Cached tokens charged at a reduced rate
- For Claude models: automatic cache management with a single breakpoint (checks ~20 content blocks back)

**Best use cases:**
- Chat with document (static document, varying questions)
- Coding assistants (static codebase context)
- Agentic workflows (repeated tool/system prompts)
- Few-shot learning (reused examples)

**Supported models:** Claude (Opus, Sonnet, Haiku 4.5+), Amazon Nova (Micro, Lite, Pro, Premier, Nova 2 Lite)

---

## 5. Key CloudWatch Metrics

### Runtime Metrics (AWS/Bedrock namespace)

| Metric | Description | Exam Relevance |
|---|---|---|
| `Invocations` | Count of successful invocations | Usage tracking |
| `InvocationLatency` | Time from request to complete response (ms) | Performance monitoring |
| `TimeToFirstToken` | Time from request to first token in streaming (ms) | Streaming performance; set alarms for latency SLAs |
| `InputTokenCount` | Number of input tokens processed | Cost attribution |
| `OutputTokenCount` | Number of output tokens generated | Cost attribution |
| `OutputImageCount` | Number of images generated | Cost tracking for image models |
| `InvocationClientErrors` | 4xx errors | Application debugging |
| `InvocationServerErrors` | 5xx errors | Service health monitoring |
| `InvocationThrottles` | Throttled requests | Capacity planning; trigger for CRIS or Provisioned Throughput |
| `EstimatedTPMQuotaUsage` | Estimated TPM quota consumed (includes burndown) | Proactive capacity management; request increases before throttling |

### Logging Delivery Metrics

| Metric | Description |
|---|---|
| `ModelInvocationLogsCloudWatchDeliverySuccess` | Successful log deliveries to CloudWatch |
| `ModelInvocationLogsCloudWatchDeliveryFailure` | Failed log deliveries to CloudWatch |
| `ModelInvocationLogsS3DeliverySuccess` | Successful log deliveries to S3 |
| `ModelInvocationLogsS3DeliveryFailure` | Failed log deliveries to S3 |

### Pre-built CloudWatch Dashboards

CloudWatch provides pre-configured Model Invocations dashboards:
- Invocation count, latency, token counts by model
- Daily token counts by model ID
- Requests grouped by input tokens
- Invocation throttles and error counts

---

## 6. TypeScript AWS SDK v3 Usage

### InvokeModel (Synchronous)

```typescript
import {
  BedrockRuntimeClient,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

// InvokeModel -- request body is model-specific
const response = await client.send(
  new InvokeModelCommand({
    modelId: "anthropic.claude-sonnet-4-20250514",
    contentType: "application/json",
    accept: "application/json",
    body: JSON.stringify({
      anthropic_version: "bedrock-2023-05-31",
      max_tokens: 1024,
      messages: [
        {
          role: "user",
          content: "Explain quantum computing in one paragraph.",
        },
      ],
    }),
  })
);

const responseBody = JSON.parse(new TextDecoder().decode(response.body));
console.log(responseBody.content[0].text);
```

### Converse API (Synchronous)

```typescript
import {
  BedrockRuntimeClient,
  ConverseCommand,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

// Converse API -- unified format across all models
const response = await client.send(
  new ConverseCommand({
    modelId: "anthropic.claude-sonnet-4-20250514",
    messages: [
      {
        role: "user",
        content: [{ text: "Explain quantum computing in one paragraph." }],
      },
    ],
    system: [{ text: "You are a physics professor. Be concise." }],
    inferenceConfig: {
      maxTokens: 1024,
      temperature: 0.7,
      topP: 0.9,
    },
  })
);

console.log(response.output?.message?.content?.[0]?.text);
console.log("Input tokens:", response.usage?.inputTokens);
console.log("Output tokens:", response.usage?.outputTokens);
console.log("Latency (ms):", response.metrics?.latencyMs);
console.log("Stop reason:", response.stopReason);
```

### ConverseStream (Streaming)

```typescript
import {
  BedrockRuntimeClient,
  ConverseStreamCommand,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

const response = await client.send(
  new ConverseStreamCommand({
    modelId: "anthropic.claude-sonnet-4-20250514",
    messages: [
      {
        role: "user",
        content: [{ text: "Write a short story about a robot." }],
      },
    ],
    inferenceConfig: {
      maxTokens: 2048,
      temperature: 0.8,
    },
  })
);

// Process the stream of events
if (response.stream) {
  for await (const event of response.stream) {
    if (event.contentBlockDelta?.delta?.text) {
      process.stdout.write(event.contentBlockDelta.delta.text);
    }
    if (event.messageStop) {
      console.log("\nStop reason:", event.messageStop.stopReason);
    }
    if (event.metadata) {
      console.log("Usage:", event.metadata.usage);
      console.log("Latency:", event.metadata.metrics?.latencyMs, "ms");
    }
  }
}
```

### InvokeModelWithResponseStream (Streaming)

```typescript
import {
  BedrockRuntimeClient,
  InvokeModelWithResponseStreamCommand,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

const response = await client.send(
  new InvokeModelWithResponseStreamCommand({
    modelId: "anthropic.claude-sonnet-4-20250514",
    contentType: "application/json",
    accept: "application/json",
    body: JSON.stringify({
      anthropic_version: "bedrock-2023-05-31",
      max_tokens: 2048,
      messages: [
        { role: "user", content: "Write a haiku about cloud computing." },
      ],
    }),
  })
);

if (response.body) {
  for await (const event of response.body) {
    if (event.chunk?.bytes) {
      const chunk = JSON.parse(new TextDecoder().decode(event.chunk.bytes));
      if (chunk.type === "content_block_delta") {
        process.stdout.write(chunk.delta?.text ?? "");
      }
    }
  }
}
```

### Converse with Tool Use

```typescript
import {
  BedrockRuntimeClient,
  ConverseCommand,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

const toolConfig = {
  tools: [
    {
      toolSpec: {
        name: "get_weather",
        description: "Get current weather for a city",
        inputSchema: {
          json: {
            type: "object",
            properties: {
              city: { type: "string", description: "City name" },
            },
            required: ["city"],
          },
        },
      },
    },
  ],
};

const response = await client.send(
  new ConverseCommand({
    modelId: "anthropic.claude-sonnet-4-20250514",
    messages: [
      {
        role: "user",
        content: [{ text: "What's the weather in Seattle?" }],
      },
    ],
    toolConfig,
  })
);

// If stopReason is "tool_use", the model wants to call a tool
if (response.stopReason === "tool_use") {
  const toolUseBlock = response.output?.message?.content?.find(
    (block) => "toolUse" in block
  );
  console.log("Tool call:", toolUseBlock?.toolUse?.name);
  console.log("Tool input:", toolUseBlock?.toolUse?.input);
}
```

### Converse with Guardrails

```typescript
const response = await client.send(
  new ConverseCommand({
    modelId: "anthropic.claude-sonnet-4-20250514",
    messages: [
      {
        role: "user",
        content: [{ text: "Tell me something harmful." }],
      },
    ],
    guardrailConfig: {
      guardrailIdentifier: "my-guardrail-id",
      guardrailVersion: "1",
      trace: "enabled", // returns guardrail assessment in response trace
    },
  })
);

if (response.stopReason === "guardrail_intervened") {
  console.log("Guardrail blocked the response");
  console.log("Trace:", JSON.stringify(response.trace, null, 2));
}
```

### Using Cross-Region Inference

```typescript
// Use the inference profile ID instead of a regional model ID
const response = await client.send(
  new ConverseCommand({
    // Geographic CRIS profile (US)
    modelId: "us.anthropic.claude-sonnet-4-20250514-v1:0",
    // Or Global CRIS profile:
    // modelId: "global.anthropic.claude-sonnet-4-20250514-v1:0",
    messages: [
      {
        role: "user",
        content: [{ text: "Hello, world!" }],
      },
    ],
  })
);
```

---

## 7. Integration Patterns

### Lambda + Bedrock

The most common pattern. Lambda function invokes Bedrock models.

```
API Gateway --> Lambda --> Bedrock Runtime (Converse/InvokeModel)
```

- Lambda IAM role needs `bedrock:InvokeModel` permission
- For streaming: use Lambda response streaming with function URL or API Gateway WebSocket
- Consider Lambda timeout (max 15 minutes) for long model responses

### API Gateway + Lambda + Bedrock

- REST API: Standard request/response, good for Converse API
- WebSocket API: Required for real-time streaming to clients
- HTTP API: Lower latency, lower cost alternative to REST API

### Step Functions + Bedrock

- **Direct Bedrock integration**: Step Functions can invoke Bedrock models directly without Lambda
- Use for orchestrating multi-step AI workflows
- Combine with other AWS services (S3, DynamoDB, SQS)
- Supports the Bedrock `InvokeModel` and `Converse` API actions natively

### EventBridge + Bedrock

- Receive notifications for model customization job status changes
- Trigger workflows when invocation logging detects anomalies
- React to Bedrock Data Automation job completions

### S3 + Bedrock

- Store training data for model customization
- Store batch inference input/output
- Store model invocation logs (large data)
- Store async invocation results (video generation, embeddings)
- Store Data Automation results

### CloudWatch + Bedrock

- Monitor runtime metrics (invocations, latency, tokens, throttles)
- Set alarms on `InvocationThrottles` to trigger scaling actions
- Use CloudWatch Logs Insights to query invocation logs
- Create dashboards for operational visibility

### CloudTrail + Bedrock

- Logs all Bedrock API calls for auditing
- Cross-Region inference requests logged in the **source Region** only
- Track who invoked which models, when, and from where

---

## 8. Cost Optimization

### Pricing Models

| Model | Description | Best For |
|---|---|---|
| **On-Demand** | Pay per input/output token, no commitment | Variable or unpredictable workloads |
| **Provisioned Throughput** | Purchase dedicated capacity (Model Units or Tokens) | Predictable high-volume workloads, custom models |
| **Batch Inference** | ~50% cost reduction vs. on-demand | Non-time-sensitive bulk processing |
| **Service Tiers** | Flex (~discount), Standard, Priority (~premium), Reserved | Match tier to urgency |

### Token Cost Optimization Strategies

1. **Optimize prompt length**: Keep prompts concise; remove unnecessary context
2. **Control response length**: Set `maxTokens` appropriately; use stop sequences
3. **Prompt caching**: Cache static prompt prefixes for up to 90% cost reduction on cached tokens
4. **Model selection**: Use the smallest model that meets quality requirements
   - Route simple tasks to Nova Micro or Haiku
   - Route complex tasks to Sonnet or Opus
5. **Intelligent Prompt Routing**: Auto-route to optimal model based on complexity (up to 30% savings)
6. **Model Distillation**: Create smaller specialized models (up to 75% cheaper)
7. **Batch inference**: Use for non-urgent workloads (50% savings)
8. **Cross-Region Inference (Global)**: ~10% savings on token pricing
9. **Flex tier**: Discount pricing for latency-tolerant workloads
10. **Request-response caching**: Cache full responses externally (ElastiCache, DynamoDB) for identical queries

### Quota Management

- Monitor `EstimatedTPMQuotaUsage` in CloudWatch
- Set alarms at **70-80%** quota utilization
- Output token burndown rate is **5:1** (output tokens consume 5x more quota than input)
- Request quota increases **proactively** through Service Quotas console

---

## 9. Security

### Data Protection

- **Data isolation**: Bedrock never shares your data with model providers or uses it to train base models
- **Encryption in transit**: TLS 1.2 for all inter-network data, SSL for API/console requests
- **Encryption at rest**: All resources encrypted using AWS KMS
- **Customer-managed keys**: Supported for model customization jobs, agents, knowledge bases, evaluations
- **No data storage**: Bedrock does NOT store text, images, or documents provided as inference content

### Network Security

- **VPC endpoints**: Use AWS PrivateLink for private connections between VPC and Bedrock
- **VPC-protected features**: Model customization jobs, batch inference, Knowledge Bases
- **S3 gateway endpoints**: Use for private access to S3 during model customization
- **VPC Flow Logs**: Monitor network traffic for security analysis

### Identity and Access Management

- **IAM permissions**:
  - `bedrock:InvokeModel` -- for Converse, InvokeModel, StartAsyncInvoke
  - `bedrock:InvokeModelWithResponseStream` -- for ConverseStream, InvokeModelWithResponseStream
  - Deny both actions to fully block inference access to a resource
- **Service roles**: Required for model customization, evaluation, and Knowledge Bases
- **Least privilege**: Use SCPs to restrict access to specific models/Regions
- **Cross-account**: S3 cross-account access supported for custom model import

### Compliance

- SOC 1/2/3, ISO 27001, CSA STAR Level 2
- HIPAA-eligible
- FedRAMP High authorized
- GDPR compliant
- Comprehensive CloudTrail audit logging

### Abuse Detection

Built-in automated abuse detection mechanisms identify and respond to potential misuse.

### Prompt Injection Security

- Content filters detect prompt attacks (jailbreaks, prompt injection)
- Standard Tier Guardrails distinguish between jailbreaks and prompt injection
- **Prompt leakage** detection available in Standard Tier
- Defense-in-depth approach recommended: combine model controls + guardrails + application-level validation

---

## 10. Structured Outputs

A capability for guaranteeing **schema-compliant JSON responses** through constrained decoding.

- Ensures valid, type-safe JSON matching a specified JSON Schema
- Two approaches: **JSON Schema output format** (controls response format) and **strict tool use** (validates tool parameters)
- Eliminates parsing failures, missing fields, type mismatches
- Works with: Cross-Region inference, batch inference, streaming
- Supported providers: Anthropic, DeepSeek, Google, MiniMax, Mistral AI, Moonshot AI, NVIDIA, OpenAI, Qwen

---

## 11. Exam Gotchas and Traps

### API Selection Traps

| Trap | Correct Answer |
|---|---|
| "Which API provides a consistent interface across all Bedrock models?" | **Converse API** (not InvokeModel) |
| "Which API should you use for generating embeddings?" | **InvokeModel** (Converse does not support embeddings) |
| "Which API should you use for image generation?" | **InvokeModel** (or StartAsyncInvoke for video) |
| "Which API is recommended for new applications?" | **Responses API** (for modern apps) or **Converse API** (for native Bedrock apps needing model portability) |
| "How do you stream responses from Bedrock?" | **ConverseStream** or **InvokeModelWithResponseStream** -- NOT the AWS CLI (CLI does not support streaming) |
| "What permission does ConverseStream require?" | `bedrock:InvokeModelWithResponseStream` (NOT `bedrock:InvokeModel`) |

### Cross-Region Inference Traps

| Trap | Correct Answer |
|---|---|
| "Is there extra cost for geographic CRIS?" | **No** -- same pricing as on-demand |
| "Is there extra cost for global CRIS?" | **No additional surcharge** -- actually ~10% cheaper |
| "Where are CloudTrail logs recorded for CRIS?" | **Source Region only** |
| "Can CRIS route to disabled Regions?" | **Yes** -- even Regions not manually enabled |
| "What must you update in SCPs for global CRIS?" | Allow `aws:RequestedRegion: "unspecified"` |

### Provisioned Throughput Traps

| Trap | Correct Answer |
|---|---|
| "Can you use batch inference with provisioned models?" | **No** |
| "Do custom (fine-tuned) models require Provisioned Throughput?" | **Yes** -- custom models require Provisioned Throughput for inference |
| "What do you pass as modelId for provisioned throughput?" | The **provisionedModelArn** (not the base model ID) |

### Guardrails Traps

| Trap | Correct Answer |
|---|---|
| "Can Guardrails work with non-Bedrock models?" | **Yes** -- use `ApplyGuardrail` API |
| "Does async streaming guardrail mode support masking?" | **No** -- only synchronous mode supports masking |
| "What happens in Detect mode?" | Guardrail detects but takes **no action** -- content passes through; useful for testing |

### General Traps

| Trap | Correct Answer |
|---|---|
| "Does Bedrock store your inference data?" | **No** -- data is used only to generate the response |
| "Is model invocation logging enabled by default?" | **No** -- disabled by default, must be explicitly enabled |
| "What is the output token burndown rate for quotas?" | **5:1** -- output tokens consume 5x more quota |
| "Where must the S3 bucket for invocation logging be?" | **Same Region** as the logging configuration |
| "Can you change the model for a base model Provisioned Throughput?" | **No** -- only for custom model Provisioned Throughputs |

---

## 12. Quick Reference Decision Framework

```
Need to invoke a model?
  |
  +-- New app / OpenAI migration? --> Responses API or Chat Completions
  |
  +-- Need model-agnostic interface? --> Converse API
  |
  +-- Need embeddings or image gen? --> InvokeModel
  |
  +-- Need real-time streaming? --> ConverseStream or InvokeModelWithResponseStream
  |
  +-- Need async (video gen)? --> StartAsyncInvoke
  |
  +-- Need bulk processing? --> Batch Inference
  |
  +-- Need speech-to-speech? --> InvokeModelWithBidirectionalStream (Nova Sonic)

Need higher throughput?
  |
  +-- Data residency requirements? --> Geographic Cross-Region Inference
  |
  +-- Maximum throughput + cost savings? --> Global Cross-Region Inference
  |
  +-- Guaranteed capacity for production? --> Provisioned Throughput or Reserved Tier
  |
  +-- Running a custom model? --> Provisioned Throughput (required)

Need content safety?
  |
  +-- Using Bedrock models? --> Guardrails via guardrailConfig parameter
  |
  +-- Using external models? --> ApplyGuardrail API
  |
  +-- Need hallucination detection? --> Contextual Grounding Checks
  |
  +-- Need factual accuracy? --> Automated Reasoning Checks
  |
  +-- Need PII protection? --> Sensitive Information Filters (Block or Mask)

Need to reduce costs?
  |
  +-- Repeated prompt prefixes? --> Prompt Caching (up to 90% savings)
  |
  +-- Variable complexity? --> Intelligent Prompt Routing (up to 30% savings)
  |
  +-- Non-urgent workload? --> Batch Inference (50% savings) or Flex tier
  |
  +-- Can use a smaller model? --> Model Distillation (up to 75% savings)
  |
  +-- Global workload? --> Global CRIS (~10% savings)
```

---

## 13. Key Terminology Quick Reference

| Term | Definition |
|---|---|
| **Foundation Model (FM)** | Large AI model trained on vast amounts of diverse data |
| **Base Model** | Pre-packaged FM from a provider, available in Bedrock |
| **Inference** | Process of a model generating output from input |
| **Token** | Sequence of characters that a model treats as a single unit |
| **Inference Profile** | Defines an FM and the Regions to which requests can be routed |
| **Provisioned Throughput** | Dedicated capacity purchased for consistent model performance |
| **Model Customization** | Adjusting model parameters using training data (fine-tuning or continued pre-training) |
| **Hyperparameters** | Settings that control the training process during customization |
| **Inference Parameters** | Settings that influence response generation (temperature, maxTokens, topP) |
| **RAG** | Retrieval Augmented Generation -- querying data sources to augment prompts |
| **Blueprint** | Custom extraction schema for Bedrock Data Automation |
| **Cache Checkpoint** | Point in a prompt that defines what gets cached for prompt caching |
| **Burndown Rate** | Ratio at which output tokens consume quota (5:1 for Bedrock) |
