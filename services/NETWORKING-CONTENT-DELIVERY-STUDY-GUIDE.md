# Networking and Content Delivery -- Comprehensive Study Guide (AIP-C01)

Amazon API Gateway is the **most heavily tested** networking service on the AWS Certified Generative AI Developer - Professional exam. It appears in nearly every domain -- from dynamic model selection (Task 1.2.2) to streaming responses (Task 2.4.2) to rate limiting (Task 2.4.3) to API response filtering (Task 3.1.4). VPC endpoints and PrivateLink are tested for network isolation of AI workloads (Task 3.2.1).

---

## 1. Amazon API Gateway (Heavily Tested)

API Gateway is the central "AI gateway" pattern on the exam. It sits between client applications and AI backends (Lambda + Bedrock), providing authorization, throttling, caching, request validation, and streaming.

### 1.1 REST API vs HTTP API vs WebSocket API

| Feature | REST API | HTTP API | WebSocket API |
|---|---|---|---|
| **Protocol** | RESTful (HTTP 1.1) | RESTful (HTTP 1.1/2) | WebSocket (persistent) |
| **Latency/Cost** | Higher latency, higher cost | ~40% lower cost, lower latency | Connection-based pricing |
| **Endpoint Types** | Edge-optimized, Regional, Private | Regional only | Regional only |
| **API Keys / Usage Plans** | Yes | No | Yes |
| **Per-client throttling** | Yes | No | No |
| **Request Validation** | Yes (JSON Schema) | No | No |
| **Request Body Transform** | Yes (VTL mapping templates) | No | Yes (VTL) |
| **Response Caching** | Yes | No | No |
| **AWS WAF** | Yes | No | No |
| **Private Endpoints** | Yes (via VPC endpoint) | No | No |
| **Lambda Authorizer** | Yes | Yes | Yes (on $connect) |
| **Cognito Authorizer** | Yes (native) | Yes (via JWT authorizer) | No (use Lambda auth) |
| **JWT Authorizer** | No (use Lambda auth) | Yes (native) | No |
| **Response Streaming** | Yes (STREAM mode) | No | Bidirectional by nature |
| **Canary Deployments** | Yes | No | No |
| **Max Payload** | 10 MB (buffered) / unlimited (streamed) | 10 MB | 128 KB (32 KB frame) |

#### When to Use Each for AI Workloads

**REST API -- The Default for AI Gateways:**
- You need **request validation** (validate prompt JSON schemas before hitting Lambda/Bedrock)
- You need **usage plans and API keys** (per-tenant AI usage tracking)
- You need **per-client throttling** (different rate limits per AI consumer)
- You need **response caching** (cache identical prompt responses)
- You need **response streaming** (stream Bedrock responses back to clients via `STREAM` mode)
- You need **WAF protection** (block prompt injection at the edge)
- You need **VTL mapping templates** (transform requests for model routing)
- You need a **private API** (internal-only AI services)

**HTTP API -- Simple, Low-Cost AI Proxy:**
- You need a **simple proxy** to Lambda with minimal features
- You want the **lowest cost** and **lowest latency**
- You use **JWT/OIDC** for authorization (native JWT authorizer)
- You do NOT need caching, request validation, or usage plans

**WebSocket API -- Real-Time AI Streaming:**
- You need **bidirectional communication** (chat interfaces)
- You need to **push partial responses** from server to client (token-by-token streaming)
- You need **long-lived connections** for real-time AI interactions
- You are building a **chat application** with streaming LLM output

#### Exam Gotcha: REST API Streaming vs WebSocket API

The exam tests whether you know that REST APIs now support response streaming via `STREAM` transfer mode. For many AI use cases, REST API streaming is simpler than WebSocket because you get all REST API features (caching, throttling, WAF) plus streaming. Use WebSocket only when you need true bidirectional communication (the client sends multiple messages during a session, such as a multi-turn chat over a persistent connection).

### 1.2 Response Streaming (Exam-Critical)

Response streaming is a core exam topic for AI/GenAI use cases. Bedrock's `InvokeModelWithResponseStream` and `ConverseStream` APIs produce streaming output -- API Gateway must relay it to clients.

#### REST API Response Streaming (STREAM Mode)

Set the integration's `responseTransferMode` to `STREAM`:

- Works with `HTTP_PROXY` and `AWS_PROXY` (Lambda proxy) integration types only
- Lambda functions must be [streaming-enabled](https://docs.aws.amazon.com/lambda/latest/dg/configuration-response-streaming.html) (response streaming Lambda)
- Streams can last **up to 15 minutes**
- **Idle timeouts**: Regional/Private = 5 minutes; Edge-optimized = 30 seconds
- First 10 MB has no bandwidth restriction; beyond 10 MB restricted to 2 MB/s
- **NOT compatible with**: endpoint caching, content encoding, VTL response transformation
- Reduces **time-to-first-byte (TTFB)** dramatically for GenAI applications
- Can exceed the 10 MB response payload limit
- Can exceed the 29-second timeout limit (streams up to 15 minutes)

```typescript
// TypeScript SDK v3: Create REST API with streaming integration
import {
  APIGatewayClient,
  PutIntegrationCommand,
} from "@aws-sdk/client-api-gateway";

const client = new APIGatewayClient({});

const command = new PutIntegrationCommand({
  restApiId: "abc123",
  resourceId: "xyz789",
  httpMethod: "POST",
  type: "AWS_PROXY",
  integrationHttpMethod: "POST",
  uri: `arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/${lambdaArn}/invocations`,
  // Key setting for streaming
  // Note: responseTransferMode is set via update_integration patchOperations
});

// Then update to enable streaming
import { UpdateIntegrationCommand } from "@aws-sdk/client-api-gateway";

const updateCommand = new UpdateIntegrationCommand({
  restApiId: "abc123",
  resourceId: "xyz789",
  httpMethod: "POST",
  patchOperations: [
    {
      op: "replace",
      path: "/responseTransferMode",
      value: "STREAM",
    },
  ],
});
```

#### WebSocket API for AI Streaming

WebSocket APIs use `$connect`, `$disconnect`, and `$default` routes plus custom routes:

```typescript
// TypeScript SDK v3: Create WebSocket API
import {
  ApiGatewayV2Client,
  CreateApiCommand,
  CreateRouteCommand,
  CreateIntegrationCommand,
} from "@aws-sdk/client-apigatewayv2";

const client = new ApiGatewayV2Client({});

const api = await client.send(
  new CreateApiCommand({
    Name: "ai-chat-websocket",
    ProtocolType: "WEBSOCKET",
    RouteSelectionExpression: "$request.body.action",
  })
);

// Create Lambda integration for message handling
const integration = await client.send(
  new CreateIntegrationCommand({
    ApiId: api.ApiId,
    IntegrationType: "AWS_PROXY",
    IntegrationUri: `arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/${lambdaArn}/invocations`,
  })
);

// Create custom route for sending prompts
await client.send(
  new CreateRouteCommand({
    ApiId: api.ApiId,
    RouteKey: "sendPrompt",
    Target: `integrations/${integration.IntegrationId}`,
  })
);
```

Backend Lambda pushes streamed tokens to connected clients using the `@connections` API:

```typescript
// Lambda handler: stream Bedrock response tokens back via WebSocket
import {
  ApiGatewayManagementApiClient,
  PostToConnectionCommand,
} from "@aws-sdk/client-apigatewaymanagementapi";
import {
  BedrockRuntimeClient,
  InvokeModelWithResponseStreamCommand,
} from "@aws-sdk/client-bedrock-runtime";

export async function handler(event: any) {
  const { connectionId, domainName, stage } = event.requestContext;
  const body = JSON.parse(event.body);

  const apigw = new ApiGatewayManagementApiClient({
    endpoint: `https://${domainName}/${stage}`,
  });
  const bedrock = new BedrockRuntimeClient({});

  const response = await bedrock.send(
    new InvokeModelWithResponseStreamCommand({
      modelId: "anthropic.claude-3-sonnet-20240229-v1:0",
      contentType: "application/json",
      body: JSON.stringify({
        anthropic_version: "bedrock-2023-05-31",
        messages: [{ role: "user", content: body.prompt }],
        max_tokens: 1024,
      }),
    })
  );

  // Stream each chunk to the WebSocket client
  if (response.body) {
    for await (const event of response.body) {
      if (event.chunk?.bytes) {
        const chunk = JSON.parse(
          new TextDecoder().decode(event.chunk.bytes)
        );
        if (chunk.type === "content_block_delta") {
          await apigw.send(
            new PostToConnectionCommand({
              ConnectionId: connectionId,
              Data: JSON.stringify({
                type: "token",
                text: chunk.delta?.text,
              }),
            })
          );
        }
      }
    }
  }

  return { statusCode: 200 };
}
```

#### Chunked Transfer Encoding and SSE

**Chunked Transfer Encoding** (`Transfer-Encoding: chunked`) is how HTTP/1.1 streaming works:
- The server does not know the total response size upfront
- Data is sent in chunks, each prefixed with its size
- API Gateway REST API STREAM mode uses chunked transfer encoding under the hood
- The client reads chunks as they arrive (no need to wait for full response)

**Server-Sent Events (SSE)** are a pattern built on top of chunked responses:
- Content-Type: `text/event-stream`
- One-directional: server pushes events to the client
- Simpler than WebSocket when you only need server-to-client streaming
- Use REST API STREAM mode with SSE formatting in your Lambda response

### 1.3 Rate Limiting and Throttling (Exam-Critical)

API Gateway uses the **token bucket algorithm** for throttling. This is a core exam topic because AI APIs are expensive and you must protect against abuse.

#### Four Levels of Throttling (Applied in Order)

| Level | Scope | Configurable? |
|---|---|---|
| 1. Per-client per-method | Usage plan + API key (most specific) | Yes |
| 2. Per-method per-stage | Stage settings or usage plan | Yes |
| 3. Per-account per-Region | All APIs in the account | Yes (request increase) |
| 4. AWS Regional limit | Hard ceiling across all accounts | No |

**Default account-level limits**: 10,000 RPS steady-state, 5,000 burst (varies by Region). Can request an increase.

**Token bucket algorithm**:
- Tokens are added at the **steady-state rate** (RPS)
- Bucket holds up to **burst** tokens
- Each request consumes one token
- When bucket is empty: `429 Too Many Requests`

#### Throttling for AI APIs

```typescript
// TypeScript SDK v3: Create a usage plan with throttling for AI API
import {
  APIGatewayClient,
  CreateUsagePlanCommand,
} from "@aws-sdk/client-api-gateway";

const client = new APIGatewayClient({});

const usagePlan = await client.send(
  new CreateUsagePlanCommand({
    name: "ai-standard-tier",
    description: "Standard tier for AI API consumers",
    throttle: {
      rateLimit: 50, // 50 requests per second steady state
      burstLimit: 100, // burst up to 100
    },
    quota: {
      limit: 10000, // 10,000 requests per month
      period: "MONTH",
    },
    apiStages: [
      {
        apiId: "abc123",
        stage: "prod",
        throttle: {
          // Method-level overrides
          "/inference/POST": {
            rateLimit: 10, // Tighter limit on expensive inference
            burstLimit: 20,
          },
        },
      },
    ],
  })
);
```

#### Exam Gotcha: Throttling Limits Are Best-Effort

Usage plan throttling and quotas are applied on a **best-effort basis** -- they are targets, not hard ceilings. Clients may occasionally exceed quotas. For hard enforcement, combine with:
- **AWS WAF** rate-based rules (for IP-based rate limiting)
- **Lambda authorizer** logic (for custom enforcement)
- **Bedrock Guardrails** (for content-based limits)

### 1.4 Request Validation and Transformation

#### Request Validation (REST API Only)

API Gateway can validate requests **before** they reach your backend, reducing unnecessary Lambda invocations and Bedrock calls:

- Validates **required request parameters** in URI, query string, and headers
- Validates **request body** against a JSON Schema model
- Returns `400 Bad Request` if validation fails (never reaches backend)
- Defined via **request validators** attached to API methods

```typescript
// TypeScript SDK v3: Create a model and request validator
import {
  APIGatewayClient,
  CreateModelCommand,
  CreateRequestValidatorCommand,
  UpdateMethodCommand,
} from "@aws-sdk/client-api-gateway";

const client = new APIGatewayClient({});

// Define a JSON Schema model for AI inference requests
const model = await client.send(
  new CreateModelCommand({
    restApiId: "abc123",
    name: "InferenceRequest",
    contentType: "application/json",
    schema: JSON.stringify({
      $schema: "http://json-schema.org/draft-04/schema#",
      type: "object",
      required: ["modelId", "prompt"],
      properties: {
        modelId: {
          type: "string",
          enum: [
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "amazon.titan-text-lite-v1",
          ],
        },
        prompt: {
          type: "string",
          minLength: 1,
          maxLength: 100000,
        },
        maxTokens: {
          type: "integer",
          minimum: 1,
          maximum: 4096,
        },
        temperature: {
          type: "number",
          minimum: 0,
          maximum: 1,
        },
      },
    }),
  })
);

// Create a request validator
const validator = await client.send(
  new CreateRequestValidatorCommand({
    restApiId: "abc123",
    name: "ValidateBodyAndParams",
    validateRequestBody: true,
    validateRequestParameters: true,
  })
);
```

#### Request/Response Mapping Templates (VTL)

Mapping templates use **Apache Velocity Template Language (VTL)** to transform requests and responses. This is how API Gateway can route to different Bedrock models based on request content (Task 1.2.2: Dynamic model selection).

```velocity
## Request mapping template: Route to different models based on request
#set($inputRoot = $input.path('$'))
#set($modelId = $inputRoot.modelId)

## Dynamic model routing based on task complexity
#if($inputRoot.taskType == "simple")
  #set($modelId = "amazon.titan-text-lite-v1")
#elseif($inputRoot.taskType == "complex")
  #set($modelId = "anthropic.claude-3-sonnet-20240229-v1:0")
#end

{
  "modelId": "$modelId",
  "prompt": "$util.escapeJavaScript($inputRoot.prompt)",
  "maxTokens": $inputRoot.maxTokens
}
```

```velocity
## Response mapping template: Filter AI response before returning to client
## (Task 3.1.4: API response filtering)
#set($inputRoot = $input.path('$'))
{
  "response": "$util.escapeJavaScript($inputRoot.output.text)",
  "usage": {
    "inputTokens": $inputRoot.usage.inputTokens,
    "outputTokens": $inputRoot.usage.outputTokens
  }
  ## Intentionally omit internal metadata, model internals, etc.
}
```

#### Exam Gotcha: VTL Not Available with Streaming

When `responseTransferMode` is `STREAM`, VTL response mapping templates are **not supported**. You must perform any response transformation inside the Lambda function or in the client. This means you cannot use API Gateway to filter streaming AI responses -- you must do it in your Lambda handler.

### 1.5 Integration with Lambda for AI Backends

API Gateway + Lambda is the standard pattern for the AI gateway:

```
Client --> API Gateway --> Lambda --> Amazon Bedrock
                |                        |
                |-- Auth (Cognito/JWT) --|
                |-- Throttling          --|
                |-- Caching             --|
                |-- Validation          --|
```

**Lambda Proxy Integration** (most common): API Gateway passes the entire request to Lambda as-is. Lambda returns the full response including status code and headers.

**Lambda Non-Proxy Integration**: API Gateway transforms the request/response using VTL mapping templates. Useful for model routing without changing Lambda code.

### 1.6 Usage Plans and API Keys

Usage plans are REST API only and provide per-tenant AI usage management:

| Concept | Purpose |
|---|---|
| **API Key** | Alphanumeric string identifying a client/tenant |
| **Usage Plan** | Defines throttle limits + quota for associated API keys |
| **Throttle** | Rate (RPS) and burst limits per client |
| **Quota** | Total requests allowed per day/week/month |

**AI use case**: Give each customer an API key. Associate it with a usage plan that limits them to, say, 1,000 Bedrock inference calls per month. Premium customers get a higher-tier usage plan.

#### Exam Gotcha: API Keys Are Not for Authentication

API keys are for **identification and usage tracking**, not for authentication or authorization. For authentication, use:
- **IAM authorization** (for AWS service-to-service)
- **Cognito user pools** (for end-user auth)
- **Lambda authorizers** (for custom auth logic)
- **JWT authorizers** (HTTP API only)

### 1.7 Custom Authorizers with Cognito

**Cognito User Pool Authorizer (REST API)**:
- Native integration, no Lambda needed
- API Gateway validates the JWT token from Cognito
- Returns `401 Unauthorized` if token is invalid/expired
- Can access user claims in mapping templates via `$context.authorizer.claims`

**Lambda Authorizer**:
- Custom authorization logic in a Lambda function
- Can validate tokens from any identity provider
- Returns an IAM policy document (allow/deny)
- Two types: **TOKEN** (header-based) and **REQUEST** (parameter-based)
- Cached for up to 3600 seconds (reduces Lambda invocations)

```typescript
// TypeScript SDK v3: Create a Cognito authorizer
import {
  APIGatewayClient,
  CreateAuthorizerCommand,
} from "@aws-sdk/client-api-gateway";

const client = new APIGatewayClient({});

const authorizer = await client.send(
  new CreateAuthorizerCommand({
    restApiId: "abc123",
    name: "CognitoAuth",
    type: "COGNITO_USER_POOLS",
    providerARNs: [
      "arn:aws:cognito-idp:us-east-1:123456789012:userpool/us-east-1_AbCdEf",
    ],
    identitySource: "method.request.header.Authorization",
  })
);
```

### 1.8 Timeout Considerations (Exam-Critical)

| Timeout | Default | Maximum | Notes |
|---|---|---|---|
| **REST API integration timeout** | 29 seconds | 29 seconds (can request increase for Regional/Private) | June 2024: can request increase beyond 29s for Regional/Private REST APIs |
| **HTTP API integration timeout** | 30 seconds | 30 seconds | Cannot be changed |
| **WebSocket API** | N/A | Idle: 10 minutes, Connection: 2 hours | Connection-based, not request-based |
| **Lambda function timeout** | 3 seconds | 15 minutes | Independent of API Gateway timeout |
| **REST API Streaming** | N/A | 15 minutes | Streaming bypasses the 29-second limit |
| **REST API idle timeout (streaming, Regional)** | 5 minutes | 5 minutes | Connection drops if no data for 5 min |
| **REST API idle timeout (streaming, Edge)** | 30 seconds | 30 seconds | Much shorter for edge-optimized |

#### Exam Gotcha: API Gateway Timeout vs Lambda Timeout

This is one of the most commonly tested gotchas:

1. **Default**: API Gateway REST API times out at **29 seconds**. Even if your Lambda has a 15-minute timeout, the client gets a `504 Gateway Timeout` after 29 seconds.
2. **Streaming solves this**: With `STREAM` mode, the REST API can stream for up to **15 minutes**, bypassing the 29-second limit entirely.
3. **Async pattern**: For non-streaming long-running jobs, use asynchronous invocation: API Gateway accepts the request, Lambda processes asynchronously, client polls for results via a separate endpoint (or gets notified via WebSocket/SNS).
4. **Timeout increase**: Since June 2024, you can request an integration timeout increase beyond 29 seconds for Regional and Private REST APIs. This is specifically called out as beneficial for "Generative AI use cases with Large Language Models."

### 1.9 Caching for AI Responses

API Gateway REST API caching stores integration responses to reduce backend calls:

| Setting | Value |
|---|---|
| **Cache capacity** | 0.5 GB to 237 GB |
| **Default TTL** | 300 seconds (5 minutes) |
| **Max TTL** | 3600 seconds (1 hour) |
| **Scope** | Per-stage; can override per-method |
| **Cache key** | Integration request parameters (query strings, headers) |
| **Invalidation** | `Cache-Control: max-age=0` header (requires authorization) |

**AI use case**: Cache responses for common/repeated prompts. If many users ask the same question (e.g., "What are your return policies?"), caching avoids redundant Bedrock calls and dramatically reduces cost and latency.

#### Exam Gotcha: Caching Incompatible with Streaming

When response streaming is enabled (`STREAM` mode), endpoint caching is **not supported**. You must choose between caching and streaming. For GenAI chatbots, streaming is usually more important. For FAQ-style AI, caching may be more valuable.

### 1.10 Key CloudWatch Metrics

| Metric | What It Tells You |
|---|---|
| `Count` | Total API requests |
| `4XXError` | Client errors (validation failures, auth failures, throttling) |
| `5XXError` | Server errors (Lambda failures, integration timeouts) |
| `Latency` | End-to-end time (API Gateway received request to returned response) |
| `IntegrationLatency` | Time from API Gateway sending to backend to receiving response |
| `CacheHitCount` | Requests served from cache |
| `CacheMissCount` | Requests forwarded to integration |

**AI-specific monitoring**: Watch `IntegrationLatency` closely -- Bedrock inference times vary by model and prompt length. Watch `5XXError` for Lambda timeouts caused by slow model responses.

---

## 2. AWS AppSync

### 2.1 GraphQL for AI Applications

AWS AppSync is a managed **GraphQL** service. It can serve as an alternative AI gateway to API Gateway, particularly when you need:
- **A single endpoint** that fetches data from multiple sources (DynamoDB, Lambda, HTTP, Bedrock)
- **Flexible queries** where the client specifies exactly which fields to return (avoids over-fetching)
- **Real-time subscriptions** for live AI output

#### AppSync + Bedrock Direct Integration

AppSync has a **native data source for Amazon Bedrock**. You can invoke Bedrock models directly from AppSync resolvers without Lambda:

```javascript
// AppSync JS resolver: Invoke Bedrock Converse API directly
import { converse } from "@aws-appsync/utils/ai";

export function request(ctx) {
  return converse({
    modelId: "anthropic.claude-3-5-haiku-20241022-v1:0",
    messages: [
      {
        role: "user",
        content: [{ text: ctx.args.prompt }],
      },
    ],
    system: [{ text: "You are a helpful assistant." }],
  });
}

export function response(ctx) {
  return ctx.result.output.message.content[0].text;
}
```

**Limitations of AppSync Bedrock integration**:
- Synchronous only -- invocations must complete within **10 seconds**
- **No streaming APIs** (cannot call `InvokeModelWithResponseStream` or `ConverseStream`)
- Same-region invocations only
- For longer invocations: use a **Lambda data source** + subscriptions for async pattern

### 2.2 Real-Time Subscriptions for AI

AppSync subscriptions use **WebSockets** to push updates to connected clients. This is the pattern for handling long-running Bedrock invocations:

1. Client sends a GraphQL mutation to start an AI inference job
2. Mutation triggers a Lambda function that calls Bedrock asynchronously
3. Lambda streams tokens back by publishing to AppSync subscription via mutations
4. Client receives real-time updates via WebSocket subscription

```graphql
type Mutation {
  startInference(prompt: String!): InferenceJob
  publishToken(jobId: ID!, token: String!): Token
}

type Subscription {
  onToken(jobId: ID!): Token
    @aws_subscribe(mutations: ["publishToken"])
}

type Token {
  jobId: ID!
  token: String!
}

type InferenceJob {
  jobId: ID!
  status: String!
}
```

### 2.3 Resolvers with Lambda/DynamoDB

AppSync resolvers map GraphQL operations to data sources:

| Resolver Type | Runtime | Use Case |
|---|---|---|
| **JS resolvers** (APPSYNC_JS) | JavaScript | Preferred for new development |
| **VTL resolvers** | Velocity Template Language | Legacy, still supported |
| **Direct Lambda resolvers** | Lambda function | Complex logic, external API calls |
| **Pipeline resolvers** | Chain of functions | Multi-step operations (auth -> validate -> invoke) |

**AI pattern with Pipeline Resolver**:
1. Function 1: Validate and sanitize the prompt (guard against injection)
2. Function 2: Check DynamoDB for cached response
3. Function 3: If no cache hit, invoke Bedrock via Lambda
4. Function 4: Store result in DynamoDB for future cache hits

### 2.4 When to Use AppSync vs API Gateway for AI

| Criterion | AppSync | API Gateway |
|---|---|---|
| **Query flexibility** | Client picks exact fields (GraphQL) | Fixed response shape (REST) |
| **Real-time** | Native WebSocket subscriptions | WebSocket API (separate) |
| **Bedrock direct** | Yes (10s limit) | No (needs Lambda) |
| **Streaming** | Via subscriptions (async pattern) | REST STREAM mode or WebSocket API |
| **Caching** | Server-side + client-side | Server-side (REST API) |
| **Rate limiting** | No native usage plans | Yes (REST API) |
| **WAF** | Yes | Yes (REST API only) |
| **Multiple data sources** | Single query, multiple sources | One integration per method |

---

## 3. Amazon CloudFront

### 3.1 CDN for AI Application Frontends

CloudFront is a global **Content Delivery Network** with 600+ Points of Presence (PoPs). For AI applications, it serves:
- **Static assets** for AI chat UIs (HTML, CSS, JS, images)
- **API acceleration** (CloudFront in front of API Gateway for global reach)
- **Edge compute** (Lambda@Edge / CloudFront Functions for preprocessing)

### 3.2 Edge Caching Strategies for AI

| Strategy | How It Works | AI Use Case |
|---|---|---|
| **Static asset caching** | Cache JS/CSS/images at edge | AI chatbot frontend (React/Angular app) |
| **API response caching** | Cache API Gateway responses at edge | Repeated FAQ-style AI queries |
| **Origin Shield** | Additional caching layer between edge and origin | Reduce Bedrock calls from global audience |
| **Cache behaviors** | Different caching rules per URL path | Cache `/static/*` aggressively, no-cache on `/api/chat` |

**Cache Key Best Practices for AI**:
- Include relevant query parameters in cache key (e.g., `modelId`, `prompt`)
- Exclude auth headers from cache key (they vary per user but shouldn't affect response)
- Use short TTLs for AI responses that may change (model updates)
- Use longer TTLs for static content and embeddings

### 3.3 Lambda@Edge and CloudFront Functions for AI

| Feature | CloudFront Functions | Lambda@Edge |
|---|---|---|
| **Runtime** | JavaScript (lightweight) | Node.js or Python |
| **Execution** | Edge location (PoP) | Regional Edge Cache |
| **Max duration** | 1 ms | 5s (viewer) / 30s (origin) |
| **Max memory** | 2 MB | 128-10,240 MB |
| **Network access** | No | Yes |
| **Triggers** | Viewer request/response | Viewer + Origin request/response |

**AI Preprocessing Use Cases**:

- **Lambda@Edge (Origin Request)**: Inspect request headers, route to different AI backends based on user location, device type, or A/B test group
- **Lambda@Edge (Origin Response)**: Add security headers, mask PII in AI responses before caching
- **CloudFront Functions (Viewer Request)**: Normalize request URLs, add/remove query parameters, simple auth token validation
- **Lambda@Edge for edge inference**: Run lightweight inference at CloudFront edge locations for ultra-low latency personalization

```typescript
// Lambda@Edge: Route AI requests based on user location
// Triggered on Origin Request
export async function handler(event: any) {
  const request = event.Records[0].cf.request;
  const country = request.headers["cloudfront-viewer-country"]?.[0]?.value;

  // Route to region-specific AI endpoint
  if (country === "JP" || country === "KR") {
    request.origin = {
      custom: {
        domainName: "api-apac.example.com",
        port: 443,
        protocol: "https",
        path: "/v1/inference",
      },
    };
    request.headers["host"] = [
      { key: "host", value: "api-apac.example.com" },
    ];
  }

  return request;
}
```

---

## 4. Amazon VPC

### 4.1 VPC Endpoints for Bedrock (Exam-Critical)

**Interface VPC endpoints** (powered by AWS PrivateLink) create private connections from your VPC to Bedrock without traversing the public internet.

#### Bedrock VPC Endpoint Service Names

| Endpoint | Service Name | Purpose |
|---|---|---|
| **Bedrock Control Plane** | `com.amazonaws.{region}.bedrock` | Manage models, fine-tuning jobs |
| **Bedrock Runtime** | `com.amazonaws.{region}.bedrock-runtime` | InvokeModel, Converse (inference) |
| **Bedrock Agents** | `com.amazonaws.{region}.bedrock-agent` | Build-time agent operations |
| **Bedrock Agents Runtime** | `com.amazonaws.{region}.bedrock-agent-runtime` | InvokeAgent, RetrieveAndGenerate |

#### Creating VPC Endpoints for Bedrock

```typescript
// TypeScript SDK v3: Create interface VPC endpoint for Bedrock Runtime
import { EC2Client, CreateVpcEndpointCommand } from "@aws-sdk/client-ec2";

const ec2 = new EC2Client({});

const endpoint = await ec2.send(
  new CreateVpcEndpointCommand({
    VpcId: "vpc-12345",
    VpcEndpointType: "Interface",
    ServiceName: "com.amazonaws.us-east-1.bedrock-runtime",
    SubnetIds: ["subnet-aaa", "subnet-bbb"], // Private subnets in 2+ AZs
    SecurityGroupIds: ["sg-endpoint"],
    PrivateDnsEnabled: true, // Use default DNS name (bedrock-runtime.us-east-1.amazonaws.com)
  })
);
```

#### VPC Endpoint Policies

Restrict which Bedrock actions can be called through the endpoint:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Principal": "*",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet*",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-text*"
      ]
    }
  ]
}
```

### 4.2 Network Isolation for AI Workloads

The standard secure AI architecture:

```
Internet --> CloudFront --> API Gateway --> Lambda (private subnet)
                                              |
                                    VPC Endpoint (PrivateLink)
                                              |
                                        Amazon Bedrock
```

Key design decisions:
- Lambda in **private subnets** with no internet access (unless via NAT Gateway)
- VPC endpoints for Bedrock, S3, DynamoDB, and other AWS services
- **No public IPs** on any compute resources
- All traffic stays on the AWS backbone network

### 4.3 Security Groups and NACLs

**Security Group for VPC Endpoint**:
- Inbound: Allow HTTPS (port 443) from Lambda security group
- Outbound: All traffic (stateful, return traffic auto-allowed)

**Security Group for Lambda**:
- Outbound: Allow HTTPS (port 443) to VPC endpoint security group
- Inbound: None required (Lambda initiates connections)

**NACLs** (Network Access Control Lists):
- Stateless (must allow both inbound and outbound)
- Applied at subnet level
- Allow ephemeral ports (1024-65535) for return traffic
- Generally, keep NACLs permissive and use security groups for fine-grained control

```typescript
// TypeScript SDK v3: Create security group for Bedrock VPC endpoint
import {
  EC2Client,
  CreateSecurityGroupCommand,
  AuthorizeSecurityGroupIngressCommand,
} from "@aws-sdk/client-ec2";

const ec2 = new EC2Client({});

const sg = await ec2.send(
  new CreateSecurityGroupCommand({
    GroupName: "bedrock-vpce-sg",
    Description: "Security group for Bedrock VPC endpoint",
    VpcId: "vpc-12345",
  })
);

await ec2.send(
  new AuthorizeSecurityGroupIngressCommand({
    GroupId: sg.GroupId,
    IpPermissions: [
      {
        IpProtocol: "tcp",
        FromPort: 443,
        ToPort: 443,
        UserIdGroupPairs: [
          { GroupId: "sg-lambda-12345" }, // Allow from Lambda SG
        ],
      },
    ],
  })
);
```

### 4.4 Private Subnets for AI Services

| Component | Subnet Type | Why |
|---|---|---|
| Lambda (AI inference) | Private | No direct internet access; use VPC endpoints |
| VPC Endpoints | Private | Interface endpoints create ENIs in private subnets |
| NAT Gateway | Public | Only if Lambda needs internet access (e.g., external APIs) |
| ALB/NLB | Public or Private | Public for internet-facing, Private for internal |

---

## 5. AWS PrivateLink

### 5.1 Private Connectivity to AI Services

AWS PrivateLink provides **private connectivity** between VPCs, AWS services, and on-premises networks without exposing traffic to the public internet.

**For AI workloads, PrivateLink is used for**:
- Connecting to **Bedrock** (via interface VPC endpoints)
- Connecting to **SageMaker** endpoints
- Connecting to **S3** (for training data, model artifacts)
- Exposing your **own AI services** to other accounts/VPCs

#### Interface Endpoints vs Gateway Endpoints

| Type | Powered By | Services | DNS | Cost |
|---|---|---|---|---|
| **Interface Endpoint** | PrivateLink (ENI in subnet) | Most AWS services, including Bedrock | Private DNS optional | Per-hour + per-GB |
| **Gateway Endpoint** | Route table entry | S3 and DynamoDB only | Prefix list in route table | Free |

#### Exam Gotcha: Bedrock Uses Interface Endpoints, Not Gateway

Bedrock requires **interface VPC endpoints** (PrivateLink). S3 and DynamoDB can use **gateway endpoints** (free). If the exam asks about private Bedrock access, the answer is always interface VPC endpoint / PrivateLink.

### 5.2 VPC Endpoint Services (Exposing Your AI)

You can create your own PrivateLink-powered service to expose your AI inference endpoint to other VPCs/accounts:

```
Consumer VPC --> Interface Endpoint --> NLB --> Your AI Service (EC2/ECS/EKS)
                  (PrivateLink)
```

Requirements:
- Your service must be behind a **Network Load Balancer (NLB)** or **Gateway Load Balancer (GWLB)**
- Consumer creates an interface endpoint in their VPC pointing to your service
- Traffic never traverses the public internet
- Useful for multi-account AI platform architectures

---

## 6. Elastic Load Balancing (ELB)

### 6.1 ALB vs NLB for AI Workloads

| Feature | Application Load Balancer (ALB) | Network Load Balancer (NLB) |
|---|---|---|
| **OSI Layer** | Layer 7 (HTTP/HTTPS) | Layer 4 (TCP/UDP/TLS) |
| **Routing** | Path, host, header, query string, method | Port-based |
| **WebSocket** | Yes | Yes (TCP passthrough) |
| **gRPC** | Yes | No |
| **SSL termination** | Yes | Yes (TLS) |
| **Static IP** | No (use Global Accelerator) | Yes |
| **PrivateLink** | No (cannot be endpoint service) | Yes (can be endpoint service target) |
| **Lambda targets** | Yes | No |
| **Latency** | ~ms (application-level processing) | ~us (ultra-low, network-level) |
| **AI Use Case** | API routing, path-based model routing, WebSocket for chat | Extreme throughput, PrivateLink service, SageMaker endpoints |

#### When to Use Each for AI

**ALB**:
- Route `/v1/chat` to one target group (chat model), `/v1/embed` to another (embedding model)
- Content-based routing for multi-model architectures
- WebSocket support for real-time AI chat
- Lambda as a target (serverless inference)
- Health checks on HTTP endpoints

**NLB**:
- Required when creating **PrivateLink endpoint services** (ALB cannot back endpoint services)
- Ultra-low latency for high-throughput inference pipelines
- Static IPs for firewall allowlisting
- TCP-level load balancing for custom protocols
- Front-end for EKS/ECS inference containers

### 6.2 Target Groups for AI Microservices

```typescript
// TypeScript SDK v3: Create ALB target group for AI inference service
import {
  ElasticLoadBalancingV2Client,
  CreateTargetGroupCommand,
} from "@aws-sdk/client-elastic-load-balancing-v2";

const elbv2 = new ElasticLoadBalancingV2Client({});

const targetGroup = await elbv2.send(
  new CreateTargetGroupCommand({
    Name: "ai-inference-targets",
    Protocol: "HTTP",
    Port: 8080,
    VpcId: "vpc-12345",
    TargetType: "ip", // Use 'ip' for ECS Fargate, 'instance' for EC2
    HealthCheckProtocol: "HTTP",
    HealthCheckPath: "/health",
    HealthCheckIntervalSeconds: 30,
    HealthyThresholdCount: 2,
    UnhealthyThresholdCount: 3,
    Matcher: { HttpCode: "200" },
  })
);
```

### 6.3 Health Checks for AI Endpoints

AI inference endpoints may have variable response times. Tune health checks accordingly:

| Setting | Recommendation for AI |
|---|---|
| **Interval** | 30 seconds (default) -- not too frequent to avoid load |
| **Timeout** | 10-30 seconds (inference can be slow) |
| **Healthy threshold** | 2 (quick recovery) |
| **Unhealthy threshold** | 3-5 (avoid flapping during slow inference) |
| **Health check path** | `/health` (lightweight endpoint, NOT an inference endpoint) |

**Never use an inference endpoint as a health check path** -- it's expensive (invokes Bedrock) and slow.

---

## 7. AWS Global Accelerator

### 7.1 Global AI Application Performance

AWS Global Accelerator uses **Anycast IP addresses** to route traffic to the nearest AWS edge location, then over the AWS global backbone to your application endpoints.

| Feature | Global Accelerator | CloudFront |
|---|---|---|
| **Protocol** | TCP and UDP | HTTP/HTTPS |
| **IP addresses** | 2 static Anycast IPv4 | Dynamic (DNS-based) |
| **Caching** | No | Yes |
| **Use case** | Non-HTTP protocols, static IP requirement | HTTP content delivery, caching |
| **AI use case** | Multi-region AI inference with failover | CDN for AI app frontends + API caching |
| **DDoS protection** | AWS Shield Standard (built-in) | AWS Shield Standard (built-in) |
| **Health checks** | Yes (endpoint-level) | Yes (origin-level) |

**When to use for AI**:
- **Multi-region AI deployment**: Run inference in us-east-1 and eu-west-1, Global Accelerator routes users to the closest healthy region
- **Static IP requirement**: Clients that cannot use DNS (IoT devices, on-premises systems) need fixed IPs to reach your AI API
- **Automatic failover**: If Bedrock in one region is degraded, traffic automatically shifts to the next closest healthy region
- **Traffic dials**: Gradually shift traffic between regions during model deployments

```typescript
// TypeScript SDK v3: Create Global Accelerator for multi-region AI API
import {
  GlobalAcceleratorClient,
  CreateAcceleratorCommand,
  CreateListenerCommand,
  CreateEndpointGroupCommand,
} from "@aws-sdk/client-global-accelerator";

const client = new GlobalAcceleratorClient({ region: "us-west-2" });

const accelerator = await client.send(
  new CreateAcceleratorCommand({
    Name: "ai-inference-global",
    IpAddressType: "IPV4",
    Enabled: true,
  })
);

const listener = await client.send(
  new CreateListenerCommand({
    AcceleratorArn: accelerator.Accelerator?.AcceleratorArn,
    PortRanges: [{ FromPort: 443, ToPort: 443 }],
    Protocol: "TCP",
  })
);

// Primary region endpoint group
await client.send(
  new CreateEndpointGroupCommand({
    ListenerArn: listener.Listener?.ListenerArn,
    EndpointGroupRegion: "us-east-1",
    EndpointConfigurations: [
      {
        EndpointId: "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/ai-api/abc123",
        Weight: 100,
      },
    ],
    TrafficDialPercentage: 100,
    HealthCheckIntervalSeconds: 30,
  })
);
```

---

## 8. Amazon Route 53

### 8.1 DNS for AI Applications

Route 53 is a highly available DNS web service. For AI applications, it provides:
- **Domain registration** and DNS management
- **Routing policies** to direct traffic to the right AI endpoint
- **Health checks** for AI service availability
- **DNS failover** for multi-region AI architectures

### 8.2 Routing Policies (Exam-Referenced)

Latency-based routing is explicitly referenced in the exam appendix.

| Policy | How It Works | AI Use Case |
|---|---|---|
| **Simple** | Single resource, no health check | Single-region AI API |
| **Weighted** | Percentage-based traffic split | A/B test AI models (80/20 split) |
| **Latency** | Route to lowest-latency region | Multi-region Bedrock deployment; user gets fastest region |
| **Failover** | Primary/secondary with health check | DR for AI services |
| **Geolocation** | Route based on user location | Data sovereignty (EU users to EU Bedrock) |
| **Geoproximity** | Route based on geographic distance + bias | Fine-grained geographic AI routing |
| **Multivalue Answer** | Return multiple healthy IPs | Simple load distribution |
| **IP-based** | Route based on client IP range | Enterprise-specific AI endpoints |

#### Latency-Based Routing for AI (Exam-Critical)

```typescript
// TypeScript SDK v3: Create latency-based routing records
import {
  Route53Client,
  ChangeResourceRecordSetsCommand,
} from "@aws-sdk/client-route-53";

const route53 = new Route53Client({});

await route53.send(
  new ChangeResourceRecordSetsCommand({
    HostedZoneId: "Z1234567890",
    ChangeBatch: {
      Changes: [
        {
          Action: "CREATE",
          ResourceRecordSet: {
            Name: "ai-api.example.com",
            Type: "A",
            SetIdentifier: "us-east-1-ai",
            Region: "us-east-1",
            AliasTarget: {
              HostedZoneId: "Z35SXDOTRQ7X7K", // ALB hosted zone ID
              DNSName: "ai-alb-us-east-1.elb.amazonaws.com",
              EvaluateTargetHealth: true,
            },
          },
        },
        {
          Action: "CREATE",
          ResourceRecordSet: {
            Name: "ai-api.example.com",
            Type: "A",
            SetIdentifier: "eu-west-1-ai",
            Region: "eu-west-1",
            AliasTarget: {
              HostedZoneId: "Z32O12XQLNTSW2", // ALB hosted zone ID
              DNSName: "ai-alb-eu-west-1.elb.amazonaws.com",
              EvaluateTargetHealth: true,
            },
          },
        },
      ],
    },
  })
);
```

### 8.3 Health Checks and Failover

Route 53 health checks monitor AI endpoint availability:

| Health Check Type | What It Monitors |
|---|---|
| **Endpoint** | HTTP/HTTPS/TCP connectivity to a specific URL |
| **Calculated** | Combines multiple health checks (AND/OR logic) |
| **CloudWatch alarm** | Monitors a CloudWatch alarm state |

**AI failover pattern**:
1. Deploy AI inference in 2+ regions
2. Create health checks for each region's API endpoint
3. Use **failover routing** (primary: us-east-1, secondary: eu-west-1) or **latency routing** with health checks enabled
4. If the primary region's health check fails (e.g., Bedrock latency spikes, Lambda errors), Route 53 automatically routes to the secondary

#### Exam Gotcha: DNS Propagation Delay

Route 53 failover is DNS-based, so clients may cache the old IP for up to the **TTL** duration. For faster failover:
- Use **short TTLs** (60 seconds) on health-checked records
- Combine with **Global Accelerator** for instant failover (no DNS caching issue)
- Client-side retry logic with exponential backoff

---

## 9. Exam Cheat Sheet -- Key Facts

### API Gateway Numbers to Memorize

| Limit | Value |
|---|---|
| REST API integration timeout (default) | 29 seconds |
| REST API streaming duration | Up to 15 minutes |
| REST API streaming idle timeout (Regional) | 5 minutes |
| REST API streaming idle timeout (Edge) | 30 seconds |
| REST API payload (buffered) | 10 MB |
| REST API payload (streamed) | Exceeds 10 MB |
| HTTP API timeout | 30 seconds |
| WebSocket message payload | 128 KB |
| WebSocket frame size | 32 KB |
| WebSocket idle timeout | 10 minutes |
| WebSocket connection duration | 2 hours |
| Lambda authorizer cache TTL (max) | 3600 seconds |
| Default account throttle (RPS) | 10,000 |
| Default account burst | 5,000 |
| API Gateway cache TTL (max) | 3600 seconds |
| API Gateway cache size | 0.5 GB to 237 GB |

### Decision Matrix: Which Networking Service?

| Scenario | Service |
|---|---|
| AI API with usage plans, rate limiting, caching, and streaming | **API Gateway REST API** |
| Simple, low-cost AI proxy with JWT auth | **API Gateway HTTP API** |
| Real-time bidirectional AI chat | **API Gateway WebSocket API** |
| GraphQL with multiple data sources + real-time subscriptions | **AWS AppSync** |
| CDN for AI app frontend + API acceleration | **Amazon CloudFront** |
| Private access to Bedrock from VPC | **VPC Interface Endpoint (PrivateLink)** |
| Free private access to S3/DynamoDB from VPC | **VPC Gateway Endpoint** |
| Multi-region AI with automatic failover (DNS-based) | **Route 53 latency or failover routing** |
| Multi-region AI with instant failover (static IPs) | **AWS Global Accelerator** |
| Layer 7 routing to multiple AI models | **ALB with path-based routing** |
| PrivateLink endpoint service for AI | **NLB** (required for endpoint services) |
| Ultra-low latency inference load balancing | **NLB** |

### Exam Gotchas Summary

1. **API Gateway REST vs HTTP**: REST API has caching, WAF, usage plans, request validation, VTL templates, streaming. HTTP API has none of these but is cheaper.
2. **29-second timeout**: REST API default. Streaming bypasses it. Can request increase for Regional/Private.
3. **Streaming disables caching and VTL**: You cannot cache or transform streamed responses in API Gateway.
4. **API keys are not auth**: They are for identification and usage tracking only.
5. **Throttling is best-effort**: Not a hard ceiling. Combine with WAF for enforcement.
6. **AppSync Bedrock limit**: 10-second synchronous limit, no streaming APIs.
7. **Bedrock uses Interface endpoints**: Not Gateway endpoints. Gateway endpoints are S3 and DynamoDB only.
8. **NLB for PrivateLink**: You need NLB (not ALB) to create a VPC endpoint service.
9. **Route 53 TTL and failover**: DNS-based failover is subject to TTL caching. Use short TTLs or Global Accelerator for faster failover.
10. **Lambda@Edge vs CloudFront Functions**: Lambda@Edge can make network calls and run up to 30s. CloudFront Functions are sub-millisecond but no network access.
