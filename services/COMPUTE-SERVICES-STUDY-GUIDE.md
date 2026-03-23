# Compute Services for Generative AI -- Study Guide

**Exam: AWS Certified Generative AI Developer - Professional (AIP-C01)**

Lambda is the single most referenced service on this exam. It appears in 14+ task
statements across all three domains -- from data processing to agentic orchestration
to guardrail enforcement. EC2 GPU instances, App Runner, Outposts, and Wavelength
appear in targeted scenarios around inference hardware, containers, data sovereignty,
and edge deployment.

---

## 1. AWS Lambda (Primary Focus)

### 1.1 Overview and Key Limits

Lambda runs code without provisioning servers. For the exam, know these hard limits cold:

| Resource | Limit | Notes |
|---|---|---|
| **Timeout** | 900 seconds (15 min) | Default is 3 seconds. Bedrock calls need 30-120s. |
| **Memory** | 128 MB - 10,240 MB | CPU scales proportionally with memory. |
| **Ephemeral storage (/tmp)** | 512 MB - 10,240 MB | Useful for temp files during data processing. |
| **Sync invocation payload** | 6 MB request / 6 MB response | Key limit for Bedrock responses. |
| **Async invocation payload** | 256 KB | For event-driven patterns. |
| **Streaming response payload** | 200 MB | Via function URLs or InvokeWithResponseStream. |
| **Deployment package (.zip)** | 50 MB zipped / 250 MB unzipped | Container images up to 10 GB. |
| **Layers** | 5 per function | Combined unzipped size counts toward 250 MB. |
| **Concurrency (account default)** | 1,000 per Region | Can be increased. |
| **Concurrency scaling rate** | 1,000 new environments per 10 sec | Per-function burst rate. |
| **Environment variables** | 4 KB total | Use SSM/Secrets Manager for larger config. |

**Exam Gotcha**: The default timeout of 3 seconds will cause Bedrock InvokeModel calls
to fail. Always set timeout to at least 30-60 seconds for FM invocations. For agentic
workflows with multiple tool calls, consider 300-900 seconds.

**Exam Gotcha**: The 6 MB synchronous response limit is bypassed by response streaming
(200 MB). If a question mentions "large model responses" or "streaming tokens", response
streaming is the answer.

**Key CloudWatch Metrics**:
- `Invocations` -- total invocation count
- `Duration` -- execution time (p50, p99)
- `Errors` -- function errors
- `Throttles` -- invocations rejected due to concurrency limits
- `ConcurrentExecutions` -- current in-flight executions
- `IteratorAge` -- lag for stream-based event sources (Kinesis, DynamoDB)

---

### 1.2 Lambda for GenAI: Invoking Bedrock

Lambda is the primary compute for on-demand FM invocation (Task 2.2.1). There are two
API patterns to know:

**Pattern 1: InvokeModel (model-specific payloads)**

```typescript
import {
  BedrockRuntimeClient,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

export const handler = async (event: { prompt: string }) => {
  const payload = {
    anthropic_version: "bedrock-2023-05-31",
    max_tokens: 1024,
    messages: [
      { role: "user", content: [{ type: "text", text: event.prompt }] },
    ],
  };

  const response = await client.send(
    new InvokeModelCommand({
      modelId: "anthropic.claude-sonnet-4-20250514",
      contentType: "application/json",
      body: JSON.stringify(payload),
    })
  );

  const body = JSON.parse(new TextDecoder().decode(response.body));
  return { statusCode: 200, body: body.content[0].text };
};
```

**Pattern 2: Converse API (model-agnostic, preferred)**

The Converse API provides a unified interface across all Bedrock models. This is the
recommended approach for dynamic model selection (Task 1.2.2) because you swap the
`modelId` without changing the request schema.

```typescript
import {
  BedrockRuntimeClient,
  ConverseCommand,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

export const handler = async (event: { prompt: string; modelId: string }) => {
  const response = await client.send(
    new ConverseCommand({
      modelId: event.modelId,
      messages: [
        {
          role: "user",
          content: [{ text: event.prompt }],
        },
      ],
      inferenceConfig: {
        maxTokens: 1024,
        temperature: 0.7,
      },
    })
  );

  const text = response.output?.message?.content?.[0]?.text;
  return { statusCode: 200, body: text };
};
```

**Exam Gotcha**: The Converse API is the correct answer when a question asks about
"model-agnostic invocation", "switching between models", or "consistent API across
providers". InvokeModel is correct when the question involves model-specific features
or a specific payload format.

---

### 1.3 Lambda Layers for ML Libraries

Lambda Layers let you package shared code and dependencies separately from function code.
Each function can use up to 5 layers, and the total unzipped size (function + layers)
must not exceed 250 MB.

**GenAI-relevant use cases**:
- **Powertools for AWS Lambda** -- available as a managed layer
- **Common SDKs** -- shared Bedrock client configuration
- **Data processing libraries** -- tokenizers, text-processing utilities
- **Validation schemas** -- shared Zod/JSON schemas for input validation

**Layer packaging (Python example for ML libraries)**:
```bash
mkdir -p python
pip install tiktoken numpy -t python/
zip -r ml-layer.zip python/
aws lambda publish-layer-version \
  --layer-name ml-utilities \
  --zip-file fileb://ml-layer.zip \
  --compatible-runtimes python3.12
```

**Exam Gotcha**: Lambda Layers do NOT increase the 250 MB deployment limit -- they share
it. For large ML frameworks, use container images (up to 10 GB). Layers also cannot be
used with Lambda@Edge.

---

### 1.4 Lambda Streaming Responses

Response streaming is critical for GenAI workloads because FM responses are generated
token-by-token. Streaming reduces Time to First Byte (TTFB) and supports payloads up
to 200 MB (vs 6 MB buffered).

**Three ways to stream Lambda responses**:
1. **Lambda Function URLs** with `InvokeMode: RESPONSE_STREAM`
2. **InvokeWithResponseStream** API via AWS SDK
3. **API Gateway proxy integration** (uses InvokeWithResponseStream under the hood)

**Bandwidth limits**:
- First 6 MB: uncapped bandwidth
- Remainder: 2 MBps maximum

**Native runtime support**: Node.js managed runtimes only. For Python and other
languages, use a custom runtime or Lambda Web Adapter.

**VPC restriction**: Lambda function URLs do NOT support response streaming within a
VPC. Use `InvokeWithResponseStream` via SDK with a VPC endpoint instead.

```typescript
// Streaming handler using awslambda.streamifyResponse()
import { pipeline } from "node:stream/promises";
import { Readable } from "node:stream";

export const handler = awslambda.streamifyResponse(
  async (event, responseStream, _context) => {
    // Write tokens as they arrive from Bedrock
    responseStream.write("Starting generation...\n");

    // Simulate streaming FM output
    for (const chunk of ["Hello", " world", " from", " Lambda!"]) {
      responseStream.write(chunk);
      await new Promise((r) => setTimeout(r, 100));
    }

    responseStream.end();
  }
);
```

**Streaming Bedrock responses through Lambda** (real-world pattern):

```typescript
import {
  BedrockRuntimeClient,
  ConverseStreamCommand,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

export const handler = awslambda.streamifyResponse(
  async (event, responseStream, _context) => {
    const parsed = JSON.parse(event.body || "{}");

    const response = await client.send(
      new ConverseStreamCommand({
        modelId: "anthropic.claude-sonnet-4-20250514",
        messages: [{ role: "user", content: [{ text: parsed.prompt }] }],
        inferenceConfig: { maxTokens: 2048 },
      })
    );

    if (response.stream) {
      for await (const event of response.stream) {
        if (event.contentBlockDelta?.delta?.text) {
          responseStream.write(event.contentBlockDelta.delta.text);
        }
      }
    }

    responseStream.end();
  }
);
```

**Exam Gotcha**: Streaming responses are still billed for the full function duration,
even if the client disconnects. The function is NOT interrupted when the caller drops
the connection.

---

### 1.5 Lambda as MCP Server (Task 2.1.7)

The Model Context Protocol (MCP) defines a standard interface for AI models to access
tools. Lambda is ideal for **stateless MCP servers** because:

- Each invocation is independent (no server to maintain)
- Auto-scales with demand
- IAM provides fine-grained access control per tool
- Pay only when tools are invoked

**Architecture pattern**:
```
Agent (Bedrock/Strands) --> API Gateway / Function URL --> Lambda (MCP Server)
                                                            |
                                                            +--> DynamoDB
                                                            +--> S3
                                                            +--> External APIs
```

Lambda functions implementing MCP tools receive a standardized request (tool name +
parameters) and return structured results. Powertools for AWS Lambda provides a
`BedrockAgentFunctionResolver` for handling Bedrock Agent action group invocations,
which follows the same tool-calling pattern.

```typescript
// Lambda as a tool endpoint for an agent
export const handler = async (event: {
  tool: string;
  parameters: Record<string, string>;
}) => {
  switch (event.tool) {
    case "lookup_customer":
      return await lookupCustomer(event.parameters.customerId);
    case "check_inventory":
      return await checkInventory(event.parameters.productId);
    default:
      return { error: `Unknown tool: ${event.tool}` };
  }
};
```

**Exam Gotcha**: MCP servers on Lambda are *stateless*. If the tool requires maintaining
conversation state or long-lived connections (e.g., SSE/WebSocket), use ECS/Fargate or
App Runner instead. Lambda is the answer for stateless, on-demand tool execution.

---

### 1.6 Lambda for Data Processing

Lambda appears in nearly every data-processing task statement on the exam.

**Fixed-size chunking (Task 1.5.1)**:
```typescript
export function chunkText(text: string, chunkSize: number, overlap: number): string[] {
  const chunks: string[] = [];
  let start = 0;

  while (start < text.length) {
    const end = Math.min(start + chunkSize, text.length);
    chunks.push(text.slice(start, end));
    start += chunkSize - overlap;
  }

  return chunks;
}

export const handler = async (event: { text: string }) => {
  const chunks = chunkText(event.text, 1000, 200);
  return { chunks, count: chunks.length };
};
```

**Batch embedding generation (Task 1.5.2)**:
```typescript
import {
  BedrockRuntimeClient,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

async function generateEmbedding(text: string): Promise<number[]> {
  const response = await client.send(
    new InvokeModelCommand({
      modelId: "amazon.titan-embed-text-v2:0",
      contentType: "application/json",
      body: JSON.stringify({
        inputText: text,
        dimensions: 1024,
        normalize: true,
      }),
    })
  );

  const body = JSON.parse(new TextDecoder().decode(response.body));
  return body.embedding;
}

export const handler = async (event: { chunks: string[] }) => {
  // Process chunks in parallel with concurrency control
  const batchSize = 5;
  const embeddings: number[][] = [];

  for (let i = 0; i < event.chunks.length; i += batchSize) {
    const batch = event.chunks.slice(i, i + batchSize);
    const results = await Promise.all(batch.map(generateEmbedding));
    embeddings.push(...results);
  }

  return { embeddings, count: embeddings.length };
};
```

**Custom data validation (Task 1.3.1)**:
```typescript
import { z } from "zod";

const TrainingDataSchema = z.object({
  prompt: z.string().min(1).max(10000),
  completion: z.string().min(1).max(10000),
  category: z.enum(["general", "code", "math", "creative"]),
});

export const handler = async (event: { records: unknown[] }) => {
  const valid: z.infer<typeof TrainingDataSchema>[] = [];
  const invalid: { index: number; errors: string[] }[] = [];

  event.records.forEach((record, index) => {
    const result = TrainingDataSchema.safeParse(record);
    if (result.success) {
      valid.push(result.data);
    } else {
      invalid.push({
        index,
        errors: result.error.errors.map((e) => e.message),
      });
    }
  });

  return { valid, invalid, validCount: valid.length, invalidCount: invalid.length };
};
```

**Data normalization (Task 1.3.4)** -- Lambda functions clean, lowercase, strip HTML,
remove PII, and standardize formats before data enters the training or RAG pipeline.

---

### 1.7 Lambda for Guardrails: Pre/Post-Processing

**Prompt verification (Task 1.6.4)** -- validate and sanitize user prompts before
they reach the FM:

```typescript
export const handler = async (event: { prompt: string; userId: string }) => {
  // Check prompt length
  if (event.prompt.length > 10000) {
    return { allowed: false, reason: "Prompt exceeds maximum length" };
  }

  // Check for injection patterns
  const injectionPatterns = [
    /ignore previous instructions/i,
    /you are now/i,
    /system:\s/i,
  ];

  for (const pattern of injectionPatterns) {
    if (pattern.test(event.prompt)) {
      return { allowed: false, reason: "Potential prompt injection detected" };
    }
  }

  return { allowed: true, sanitizedPrompt: event.prompt.trim() };
};
```

**Post-processing validation (Task 3.1.4)** -- validate FM outputs before returning
to the user:

```typescript
export const handler = async (event: { response: string; context: string }) => {
  // Check for hallucinated content
  const containsPII = /\b\d{3}-\d{2}-\d{4}\b/.test(event.response); // SSN pattern
  const containsEmail = /\b[\w.-]+@[\w.-]+\.\w+\b/.test(event.response);

  const issues: string[] = [];
  if (containsPII) issues.push("Response contains potential PII (SSN pattern)");
  if (containsEmail) issues.push("Response contains email addresses");

  if (issues.length > 0) {
    return {
      approved: false,
      issues,
      redactedResponse: event.response
        .replace(/\b\d{3}-\d{2}-\d{4}\b/g, "[REDACTED-SSN]")
        .replace(/\b[\w.-]+@[\w.-]+\.\w+\b/g, "[REDACTED-EMAIL]"),
    };
  }

  return { approved: true, response: event.response };
};
```

**Automated compliance checks (Task 3.4.3)** -- Lambda triggered by EventBridge or
Step Functions to audit model outputs, log to CloudWatch, and flag violations.

---

### 1.8 Timeout and Concurrency for AI Workloads

**Timeout strategy by workload type**:

| Workload | Recommended Timeout | Rationale |
|---|---|---|
| Simple FM invocation | 30-60s | Single Converse call |
| RAG (retrieve + generate) | 60-120s | KB lookup + FM call |
| Agentic workflow | 120-300s | Multiple tool calls + FM reasoning |
| Batch embedding | 300-900s | Processing many chunks |
| Data processing pipeline | 300-900s | Large document chunking |

**Concurrency controls**:

| Control | Purpose | Use Case |
|---|---|---|
| **Reserved concurrency** | Guarantees AND caps concurrency for a function | Protect downstream Bedrock throttle limits |
| **Provisioned concurrency** | Pre-initializes execution environments | Eliminate cold starts for latency-sensitive APIs |
| **Account concurrency limit** | Total concurrent executions across all functions | Default 1,000; request increase for production |

**Reserved concurrency** is the exam favorite. Setting reserved concurrency on your
Bedrock-invoking Lambda function prevents it from consuming all account concurrency AND
protects Bedrock's tokens-per-minute quota from being overwhelmed.

**Exam Gotcha**: Setting reserved concurrency to 0 effectively disables a function.
Lambda sends events to the configured DLQ or on-failure destination instead.

**Exam Gotcha**: Provisioned concurrency and SnapStart cannot be used together.

---

### 1.9 Lambda SnapStart

SnapStart reduces cold start latency by snapshotting the initialized execution
environment and restoring it on invocation. Instead of running initialization code on
every cold start, Lambda restores from a cached snapshot.

**Supported runtimes**: Java 11+, Python 3.12+, .NET 8+

**How it works**:
1. You publish a new function version
2. Lambda runs initialization code and takes an encrypted snapshot
3. Snapshots are stored in S3, divided into 512 KB chunks
4. On invocation, Lambda restores from snapshot instead of re-initializing
5. Tiered caching (L1 on worker nodes, L2 in distributed cache) speeds retrieval

**When to use SnapStart vs Provisioned Concurrency**:

| Dimension | SnapStart | Provisioned Concurrency |
|---|---|---|
| Cost | Lower (no pre-warmed environments) | Higher (always-on charge) |
| Latency | Sub-second cold starts | No cold starts at all |
| Best for | Moderate latency sensitivity | Strict latency requirements (< 100ms) |
| Runtimes | Java, Python, .NET | All runtimes |
| Compatibility | No EFS, no ephemeral > 512 MB | Full feature support |

**Exam Gotcha**: SnapStart requires you to handle uniqueness, network connections, and
ephemeral data carefully. Connections established during init are NOT guaranteed to be
valid after snapshot restore -- re-establish them in the handler.

---

### 1.10 Powertools for AWS Lambda

Powertools is a developer toolkit available for TypeScript, Python, Java, and .NET.
Available as individual npm packages or as a Lambda Layer.

**Core features for the exam**:

| Feature | Package | Purpose |
|---|---|---|
| **Logger** | `@aws-lambda-powertools/logger` | Structured JSON logging with correlation IDs |
| **Tracer** | `@aws-lambda-powertools/tracer` | X-Ray tracing with automatic segment capture |
| **Metrics** | `@aws-lambda-powertools/metrics` | CloudWatch EMF custom metrics |
| **Parameters** | `@aws-lambda-powertools/parameters` | SSM, Secrets Manager, AppConfig retrieval with caching |
| **Idempotency** | `@aws-lambda-powertools/idempotency` | Prevent duplicate executions (DynamoDB-backed) |
| **Batch** | `@aws-lambda-powertools/batch` | Handle SQS/Kinesis/DynamoDB partial failures |
| **Parser** | `@aws-lambda-powertools/parser` | Zod-based input validation |
| **Event Handler** | `@aws-lambda-powertools/event-handler` | Bedrock Agent function resolver |

```typescript
import { Logger } from "@aws-lambda-powertools/logger";
import { Tracer } from "@aws-lambda-powertools/tracer";
import { Metrics, MetricUnit } from "@aws-lambda-powertools/metrics";

const logger = new Logger({ serviceName: "genai-api" });
const tracer = new Tracer({ serviceName: "genai-api" });
const metrics = new Metrics({ namespace: "GenAI", serviceName: "genai-api" });

export const handler = async (event: unknown) => {
  logger.info("Processing request", { event });

  const segment = tracer.getSegment();
  const subsegment = segment?.addNewSubsegment("BedrockInvocation");

  try {
    // ... invoke Bedrock ...
    metrics.addMetric("ModelInvocations", MetricUnit.Count, 1);
    metrics.addMetric("InputTokens", MetricUnit.Count, 150);
    return { statusCode: 200, body: "Success" };
  } catch (error) {
    metrics.addMetric("ModelErrors", MetricUnit.Count, 1);
    logger.error("Bedrock invocation failed", { error });
    throw error;
  } finally {
    subsegment?.close();
    metrics.publishStoredMetrics();
  }
};
```

**Bedrock Agent Function Resolver** (Powertools TypeScript):

```typescript
import { BedrockAgentFunctionResolver } from "@aws-lambda-powertools/event-handler/bedrock-agent";

const resolver = new BedrockAgentFunctionResolver();

resolver.tool("lookup_customer", async (params) => {
  const customer = await getCustomer(params.customerId);
  return { name: customer.name, plan: customer.plan };
});

resolver.tool("get_order_status", async (params) => {
  const order = await getOrder(params.orderId);
  return { status: order.status, eta: order.eta };
});

export const handler = resolver.resolve();
```

**Exam Gotcha**: Idempotency is critical for GenAI workflows. FM invocations are
expensive -- Powertools idempotency uses DynamoDB to cache responses and prevent
duplicate invocations when retries occur.

---

### 1.11 Error Handling Patterns

**Synchronous invocation**: Caller receives the error directly. No automatic retry.
The caller (API Gateway, SDK client) must implement retry logic.

**Asynchronous invocation**: Lambda retries twice by default (3 total attempts) with
increasing backoff. Configurable via:
- `MaximumRetryAttempts` (0-2)
- `MaximumEventAgeInSeconds` (60-21600, i.e., up to 6 hours)

**Failed event destinations**:
- SQS queue (most common for DLQ pattern)
- SNS topic
- S3 bucket (failure records only)
- Another Lambda function
- EventBridge

**Dead Letter Queues (DLQ)**: Older mechanism; captures discarded events. Use on-failure
destinations instead for new designs (richer metadata, more destination options).

**Error handling for Bedrock calls**:

```typescript
import {
  ThrottlingException,
  ModelTimeoutException,
  ServiceQuotaExceededException,
} from "@aws-sdk/client-bedrock-runtime";

async function invokeWithRetry(
  fn: () => Promise<unknown>,
  maxRetries = 3
): Promise<unknown> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (
        error instanceof ThrottlingException ||
        error instanceof ServiceQuotaExceededException
      ) {
        // Exponential backoff with jitter
        const delay = Math.min(1000 * 2 ** attempt + Math.random() * 1000, 30000);
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }
      if (error instanceof ModelTimeoutException) {
        // Model overloaded; retry with backoff
        if (attempt < maxRetries) continue;
      }
      throw error; // Non-retryable error
    }
  }
  throw new Error("Max retries exceeded");
}
```

**Exam Gotcha**: For event-source mappings (SQS, Kinesis, DynamoDB Streams), Lambda
retries the entire batch. Use `bisectBatchOnFunctionError` to isolate the bad record,
and `maxRetryAttempts` + `maxRecordAge` to prevent poison pills from blocking the stream.

---

## 2. Amazon EC2 for GenAI

### 2.1 GPU Instance Families

| Family | Chip | Primary Use | Key Feature |
|---|---|---|---|
| **P6/P6e** | NVIDIA Blackwell/Blackwell Ultra | Training + Inference at trillion-param scale | Up to 72 GPUs, 3200 Gbps EFA |
| **P5/P5e** | NVIDIA H100/H200 | Training + Inference (100B+ params) | Up to 8 GPUs, 3200 Gbps EFA, UltraClusters |
| **P4d/P4de** | NVIDIA A100 | Training + Inference | 8 GPUs, 400 Gbps EFA |
| **G6e** | NVIDIA L40S | Inference + Spatial computing | Up to 8 GPUs |
| **G5** | NVIDIA A10G | Inference + Graphics | Up to 8 GPUs, 3x perf over G4dn |
| **G4dn** | NVIDIA T4 | Cost-effective inference | Up to 8 GPUs |
| **Trn2** | AWS Trainium2 | Training + Inference (GenAI) | AWS custom silicon, best price-performance |
| **Trn1/Trn1n** | AWS Trainium | Training | Up to 16 chips, 50% cost savings vs comparable |
| **Inf2** | AWS Inferentia2 | Inference | Optimized for LLM inference |
| **Inf1** | AWS Inferentia | Inference | Previous gen, cost-effective |

**AWS Custom Silicon**:
- **Trainium** (Trn1, Trn2): Designed for training. Use AWS Neuron SDK.
- **Inferentia** (Inf1, Inf2): Designed for inference. Use AWS Neuron SDK.
- These are the cost-optimized choices when the question mentions "lowest cost training"
  or "cost-effective inference" on AWS custom hardware.

### 2.2 When to Use EC2 vs Lambda vs SageMaker

| Criteria | Lambda | EC2 GPU | SageMaker Endpoints |
|---|---|---|---|
| **Invocation pattern** | Event-driven, on-demand | Always-on, persistent | Managed real-time/batch |
| **Max execution time** | 15 minutes | Unlimited | Unlimited |
| **GPU access** | No | Yes (P, G, Trn, Inf) | Yes (managed) |
| **Model hosting** | Invoke via Bedrock API | Self-managed | Managed (auto-scaling, A/B) |
| **Scaling** | Automatic (ms) | ASG (minutes) | Auto-scaling (minutes) |
| **Cost model** | Per-invocation | Per-hour | Per-hour + per-inference |
| **Best for** | Bedrock API calls, data processing, tool execution | Custom model hosting, fine-tuning, large batch jobs | Production model endpoints with ML ops |

**Exam decision tree**:
- "Invoke a foundation model" --> Lambda + Bedrock
- "Host a custom model with GPU" --> EC2 or SageMaker
- "Cost-effective training" --> Trn1/Trn2 instances
- "Managed inference endpoint" --> SageMaker
- "Self-managed, full control" --> EC2

### 2.3 Auto Scaling for AI Workloads

EC2 Auto Scaling Groups with GPU instances use target tracking policies. Key metric:
- **Custom CloudWatch metric** for GPU utilization (reported via CloudWatch agent or
  NVIDIA DCGM exporter)
- `CPUUtilization` alone is insufficient for GPU workloads

**Step Scaling example**: Scale out when average GPU utilization > 70% for 3 minutes;
scale in when < 30% for 10 minutes.

**Exam Gotcha**: EC2 GPU instances are expensive. Always use Spot Instances for
fault-tolerant training jobs (up to 90% savings). Use On-Demand or Reserved for
inference endpoints requiring availability.

**Key CloudWatch Metrics**:
- `CPUUtilization`, `NetworkIn`, `NetworkOut` (standard)
- Custom GPU metrics via CloudWatch agent (GPU utilization, GPU memory)
- `StatusCheckFailed` for instance health

---

## 3. AWS App Runner

### 3.1 Container Deployment for AI Services

App Runner is a fully managed container service for web applications and APIs. It
connects to source code (GitHub) or container images (ECR) and handles build, deploy,
scaling, and TLS automatically.

**Key characteristics**:
- Automatic scaling based on concurrent requests
- Built-in HTTPS, load balancing, health checks
- No infrastructure to manage (no VPC required by default, but VPC connector available)
- Deploys from ECR images or source code
- Min instances can be set to 0 (scale to zero) or higher (provisioned instances)

**Auto Scaling configuration**:
- `MaxConcurrency`: max concurrent requests per instance (default: 100)
- `MaxSize`: max number of instances (default: 25)
- `MinSize`: min instances (default: 1; set to 0 for scale-to-zero)

### 3.2 When to Use App Runner vs Lambda vs ECS

| Criteria | Lambda | App Runner | ECS/Fargate |
|---|---|---|---|
| **Execution time** | 15 min max | Unlimited | Unlimited |
| **Container support** | Container images (no Dockerfile) | Full Dockerfile, ECR | Full container orchestration |
| **Scaling** | Per-invocation | Per-request concurrency | Task-based ASG |
| **Complexity** | Lowest | Low | Medium-High |
| **GPU support** | No | No | Yes (EC2 launch type) |
| **State** | Stateless | Stateless (between requests) | Stateful possible |
| **Best for** | Short tasks, event-driven | Web APIs, containerized AI services | Complex microservices, GPU workloads |

**Exam decision tree**:
- "Simple containerized API, no infrastructure management" --> App Runner
- "Need GPU containers" --> ECS on EC2 with GPU instances
- "Event-driven, short-lived" --> Lambda
- "Full orchestration control" --> ECS/EKS

**Exam Gotcha**: App Runner does NOT support GPU instances. If the question mentions
GPU inference in a container, the answer is ECS on EC2 (not Fargate, which also lacks GPU).

**Key CloudWatch Metrics**:
- `RequestCount` -- total HTTP requests
- `2xxStatusCode`, `4xxStatusCode`, `5xxStatusCode` -- response codes
- `RequestLatency` -- response time
- `ActiveInstances` -- currently running instances
- `ConcurrencyUtilization` -- percentage of max concurrency used

---

## 4. AWS Lambda@Edge

### 4.1 Edge Processing for AI Applications

Lambda@Edge extends Lambda to CloudFront edge locations worldwide. Functions run in
response to CloudFront events: viewer request, viewer response, origin request, origin
response.

**Key limits (different from standard Lambda)**:

| Resource | Viewer Events | Origin Events |
|---|---|---|
| **Timeout** | 5 seconds | 30 seconds |
| **Memory** | 128 MB | 128 MB (configurable up to limits) |
| **Package size** | 1 MB | 50 MB |
| **Ephemeral storage** | 512 MB (fixed) | 512 MB (fixed) |

**Restrictions**:
- Must be deployed in **us-east-1** (automatically replicated globally)
- No VPC access
- No environment variables (except reserved Lambda vars)
- No Lambda Layers
- No provisioned concurrency
- No container images
- No arm64 architecture
- No X-Ray tracing

### 4.2 GenAI Use Cases at the Edge

- **Request routing**: Route AI requests to the nearest Region based on latency
- **Content transformation**: Modify HTML/JSON responses at the edge (e.g., inject
  AI-generated summaries, translate content headers)
- **A/B testing**: Route a percentage of users to different model versions
- **Authentication**: Validate JWT tokens before requests reach the origin
- **Prompt caching**: Check CloudFront cache for repeated identical prompts

**Lambda@Edge vs CloudFront Functions**:

| Dimension | Lambda@Edge | CloudFront Functions |
|---|---|---|
| Runtime | Node.js, Python | JavaScript only |
| Execution time | Up to 30s (origin) | < 1ms |
| Scale | Thousands/sec | Millions/sec |
| Network access | Yes | No |
| Use case | Complex logic, API calls | Header manipulation, redirects, URL rewrites |

**Exam Gotcha**: Lambda@Edge is NOT suitable for invoking Bedrock models (too slow for
viewer events at 5s, and no direct Bedrock access from edge). Use it for lightweight
pre/post-processing, routing, and auth. For actual FM inference at the edge, consider
Wavelength or Outposts.

---

## 5. AWS Outposts

### 5.1 On-Premises AI Deployment (Task 2.3.4)

AWS Outposts brings AWS infrastructure to on-premises data centers. Two form factors:
- **Outposts Rack**: Full 42U rack with EC2, EBS, S3, ECS, EKS, RDS, etc.
- **Outposts Server**: 1U/2U server for edge locations with limited space

**Architecture**: Outposts are fully managed by AWS. They connect back to a parent AWS
Region for control plane operations, but data processing happens locally.

**GenAI on Outposts**:
- Deploy Small Language Models (SLMs) locally using EC2 GPU instances on Outposts
- Use Llama.cpp or similar lightweight inference engines
- AWS IoT Greengrass for managing ML components on Outposts Servers
- Anomaly detection, virtual assistants, and time-series forecasting at the edge

### 5.2 Data Sovereignty and Compliance Use Cases

Outposts is the correct answer when the question mentions:
- **Data residency requirements**: data must not leave a specific geographic location
- **Data sovereignty**: regulatory requirement for data to remain on-premises
- **Low latency to on-premises systems**: factory floor, hospital, trading floor
- **Local data processing**: data too sensitive or too large to send to the cloud
- **Hybrid cloud**: consistent API experience across on-premises and cloud

**Exam Gotcha**: Outposts requires a network connection back to the parent Region for
management. It is NOT an air-gapped solution. For fully disconnected environments, the
exam scope does not cover AWS Snow Family, but know that Outposts needs connectivity.

**Key CloudWatch Metrics**:
- `ConnectedStatus` -- connection to parent Region
- Standard EC2 metrics for instances on Outposts
- S3 on Outposts metrics for local storage

---

## 6. AWS Wavelength

### 6.1 Ultra-Low Latency AI at the Edge (Task 2.3.4)

AWS Wavelength embeds AWS compute and storage within telecom providers' 5G networks.
Wavelength Zones are extensions of a parent AWS Region but physically located inside
carrier data centers.

**How it works**:
1. Opt in to a Wavelength Zone
2. Extend your VPC with a subnet in the Wavelength Zone
3. Create a **carrier gateway** (like an internet gateway, but for the carrier network)
4. Deploy EC2 instances, EKS pods, or containers in the Wavelength subnet
5. Traffic from 5G devices reaches your app without leaving the telecom network

**Supported services in Wavelength Zones**:
- Amazon EC2 (including Auto Scaling)
- Amazon ECS/EKS
- Amazon EBS
- Amazon VPC
- Application Load Balancer
- CloudWatch, CloudTrail, CloudFormation, Systems Manager

**MTU considerations**:
- 9001 bytes between instances in the same Wavelength Zone
- 1500 bytes between carrier gateway and Wavelength Zone
- 1300 bytes between Wavelength Zone and Region (private IP)

### 6.2 5G Integration Patterns

**Use cases on the exam**:
- **Real-time inference**: Computer vision, AR/VR, autonomous vehicles
- **Interactive AI**: Voice assistants, real-time translation at the device edge
- **IoT + AI**: Smart factory sensors processed at the 5G edge
- **Gaming**: AI-driven NPCs with ultra-low latency

**Architecture pattern**:
```
5G Device --> Carrier Network --> Wavelength Zone (EC2/EKS)
                                      |
                                      v
                                 Parent Region (Bedrock, S3, DynamoDB)
```

**Wavelength vs Local Zones vs Outposts**:

| Dimension | Wavelength | Local Zones | Outposts |
|---|---|---|---|
| **Location** | Inside carrier 5G network | AWS-managed metro facility | Customer data center |
| **Latency target** | Single-digit ms (5G) | Single-digit ms (metro) | Sub-ms (on-premises) |
| **Network** | Carrier gateway | Internet gateway | Local gateway |
| **Management** | AWS-managed | AWS-managed | AWS-managed on-prem |
| **Exam trigger** | "5G", "mobile edge", "carrier" | "metro", "city", "end users" | "on-premises", "data center", "sovereignty" |

**Exam Gotcha**: Wavelength is always the answer when the question mentions "5G",
"mobile devices at the edge", "carrier network", or "telecom provider". If the
question says "on-premises" or "data center", the answer is Outposts. If it says
"metro area" without 5G context, consider Local Zones.

**Key CloudWatch Metrics**:
- Standard EC2 metrics for instances in Wavelength Zones
- VPC Flow Logs for network traffic analysis
- Custom application metrics via CloudWatch agent

---

## Quick Reference: Service Selection Matrix

| Scenario | Service |
|---|---|
| Invoke Bedrock FM on-demand | **Lambda** |
| Stream FM tokens to client | **Lambda** (response streaming) |
| Process/chunk documents for RAG | **Lambda** |
| Generate embeddings in batch | **Lambda** (or Step Functions + Lambda) |
| Validate prompts before FM call | **Lambda** |
| Post-process FM output (PII, compliance) | **Lambda** |
| Stateless MCP tool server | **Lambda** |
| Handle webhook from external system | **Lambda** |
| Dynamic model selection | **Lambda** + Converse API |
| Host custom model with GPU | **EC2** (P5, G5, Inf2, Trn1) |
| Cost-effective model training | **EC2 Trn1/Trn2** (Trainium) |
| Cost-effective inference | **EC2 Inf2** (Inferentia2) |
| Simple containerized AI API | **App Runner** |
| Containerized AI with GPU | **ECS on EC2** (not App Runner) |
| Route AI requests at edge | **Lambda@Edge** |
| AI on-premises (data sovereignty) | **Outposts** |
| AI at 5G edge (mobile devices) | **Wavelength** |

---

## Exam Tips Summary

1. **Lambda timeout**: Default 3s will fail on Bedrock calls. Set 30-120s minimum.
2. **6 MB vs 200 MB**: Buffered responses = 6 MB. Streaming = 200 MB. Streaming is
   for GenAI.
3. **Converse API**: Model-agnostic. Use it for dynamic model selection questions.
4. **Reserved concurrency**: Protects account concurrency AND Bedrock rate limits.
5. **SnapStart vs Provisioned Concurrency**: SnapStart is cheaper but sub-second, not
   zero cold start. PC eliminates cold starts entirely.
6. **Layers**: Do NOT increase the 250 MB limit. For large ML packages, use container
   images (10 GB).
7. **Lambda@Edge limits**: 5s viewer / 30s origin timeout, 1 MB package for viewer
   events. Cannot invoke Bedrock.
8. **App Runner has no GPU**. GPU containers = ECS on EC2.
9. **Outposts**: "on-premises" + "data sovereignty" + "local data processing".
10. **Wavelength**: "5G" + "carrier" + "mobile edge" + "ultra-low latency".
11. **Trainium for training, Inferentia for inference** -- both are AWS custom silicon,
    both use the Neuron SDK.
12. **Powertools idempotency**: Prevents duplicate FM invocations during retries. Uses
    DynamoDB for persistence.
13. **Async error handling**: 2 retries (default), configurable. Use on-failure
    destinations (SQS/SNS/S3/EventBridge) over DLQs for new designs.
14. **Streaming billing**: You pay for full duration even if the client disconnects.
15. **VPC + streaming**: Function URLs do not support streaming in VPC. Use
    `InvokeWithResponseStream` via SDK with VPC endpoints.
