# Project 07: Streaming Chat UI with Amplify

## Exam Domains

| Domain | Task | Description |
|--------|------|-------------|
| 2.4 | Implement Foundation Model API integrations | Real-time AI interaction systems, Bedrock streaming APIs, WebSocket or server-sent events, chunked transfer encoding |
| 2.5 | Implement application integration patterns and development tools | FM API interfaces with token limit management, AWS Amplify for declarative UI components, feedback interfaces |

## Overview

Streaming is a first-class topic on the AIP-C01 exam because it is fundamental to user experience in chat applications — nobody wants to stare at a spinner for 15 seconds waiting for a 500-token response to arrive all at once. This project builds a complete streaming chat application: a React frontend hosted on AWS Amplify that displays tokens in real time as the model generates them, delivered over a WebSocket connection managed by API Gateway.

The second feature — a feedback mechanism — practices Task 5.1.3 (user-centered evaluation). Users can rate any model response with a thumbs-up or thumbs-down, and those ratings are written to DynamoDB alongside the full conversation context. This creates a dataset for later human-feedback-based evaluation, which is a pattern the exam tests in the context of continuous model improvement loops.

## Architecture

```
React App (AWS Amplify Hosting)
    |
    |-- WebSocket connection
    v
API Gateway WebSocket API
    |-- $connect route    --> Lambda: ConnectionManager (write to DynamoDB)
    |-- $disconnect route --> Lambda: ConnectionManager (delete from DynamoDB)
    |-- sendMessage route --> Lambda: StreamingInvoker
    |
    v
Lambda: StreamingInvoker
    |-- bedrock:InvokeModelWithResponseStream (Claude 3 Haiku)
    |-- Stream chunks via: execute-api:ManageConnections (PostToConnection)
    |-- Each chunk: { type: "chunk", text: "..." }
    |-- Final message: { type: "done", input_tokens: int, output_tokens: int }
    |
    v  (on thumbs-up / thumbs-down)
API Gateway HTTP API  POST /feedback
    |
    v
Lambda: FeedbackHandler
    |-- DynamoDB: ChatFeedback table
    |       PK: session_id, SK: message_id
    |       attrs: rating (UP|DOWN), prompt, response, timestamp, model_id
    |
DynamoDB: WebSocketConnections  (PK: connection_id, TTL: 2h)
```

**AWS services used:**

- AWS Amplify Hosting -- serves the React frontend from a Git repository or manual deploy
- Amazon API Gateway (WebSocket API) -- bidirectional WebSocket connection management and message routing
- Amazon API Gateway (HTTP API) -- REST endpoint for feedback submission
- AWS Lambda -- WebSocket connection manager, streaming invoker, feedback handler
- Amazon Bedrock (`bedrock:InvokeModelWithResponseStream`) -- streaming token generation
- Amazon DynamoDB -- WebSocket connection registry, chat feedback store
- AWS IAM -- Lambda execution roles with `execute-api:ManageConnections`
- Amazon CloudWatch Logs -- Lambda and API Gateway access logs

## What You Will Build

1. A Lambda `ConnectionManager` that handles `$connect` (writes `connection_id` to DynamoDB with a 2-hour TTL) and `$disconnect` (deletes the record).
2. A Lambda `StreamingInvoker` that:
   - Receives `{ action: "sendMessage", data: { session_id, message } }` from the WebSocket route.
   - Calls `bedrock:InvokeModelWithResponseStream` using the Bedrock runtime streaming API.
   - Iterates over the response stream and calls `execute-api:ManageConnections` (PostToConnection) for each token chunk.
   - Sends a final `{ type: "done" }` message when the stream ends.
3. A Lambda `FeedbackHandler` that accepts `POST /feedback` with body `{ session_id, message_id, rating, prompt, response }` and writes to the DynamoDB `ChatFeedback` table.
4. A React chat UI (created with Create React App or Vite) that:
   - Opens a WebSocket connection to API Gateway on load.
   - Displays a chat thread with user messages and streaming assistant responses.
   - Appends tokens to the current assistant message bubble as they arrive.
   - Shows a thumbs-up / thumbs-down button under each completed assistant message.
   - Sends feedback to the HTTP feedback endpoint on button click.
5. The React app deployed to Amplify Hosting via `amplify publish` or a manual zip upload.
6. A `feedback-viewer.py` script that queries the `ChatFeedback` DynamoDB table and prints a summary: total ratings, up/down split, and the 3 lowest-rated prompts with their responses.

## Target Outcomes

By the end of this project you should be able to verify each of the following:

- [ ] Opening the Amplify-hosted URL in a browser shows the chat interface. Sending a message causes tokens to appear incrementally in the assistant bubble (visually streaming, not appearing all at once after a delay).
- [ ] The WebSocket connection ID appears in the DynamoDB `WebSocketConnections` table while the browser tab is open and disappears within 30 seconds of closing the tab.
- [ ] Clicking thumbs-up or thumbs-down on a response writes a record to the DynamoDB `ChatFeedback` table with the correct `rating`, `prompt`, and `response` fields.
- [ ] The `feedback-viewer.py` script outputs the up/down ratio and lowest-rated responses correctly.
- [ ] You can explain why `InvokeModelWithResponseStream` is used instead of `InvokeModel`, and what the tradeoff is in terms of Lambda billing (streaming holds the connection open longer — duration billing implications).
- [ ] You can explain the role of `execute-api:ManageConnections` and why the Lambda execution role needs it scoped to the specific API Gateway stage ARN.

## Prerequisites

**Local tooling:**

- Node.js 22+ with `bun` package manager (`npm install -g bun`)
- AWS CDK CLI (`npm install -g aws-cdk`)
- AWS CLI v2 with Lambda, API Gateway, DynamoDB, Amplify, Bedrock, and IAM permissions
- AWS Amplify CLI (`npm install -g @aws-amplify/cli`) for frontend hosting

**AWS service enablement:**

- Amazon Bedrock model access enabled for Claude 3 Haiku (recommended for faster streaming in the UI)
- AWS Amplify Hosting available in your region

**Local development tip:**

Before deploying to Amplify, you can run the React app locally against a deployed backend (real API Gateway WebSocket URL) to iterate on the UI faster.

## Step-by-Step Build Guide

1. **Initialize the CDK project.** Copy `projects/cdk-template/` into `cdk/`. Update `package.json` `name` to `streaming-chat-ui`. Run `bun install`.

2. **Define the `StreamingStack`** in `src/stacks/streaming-stack.ts`. Provision the following constructs:
   - `Table` for `WebSocketConnections` (partition key `connection_id`, String; TTL attribute `expires_at`).
   - `Table` for `ChatFeedback` (partition key `session_id`, sort key `message_id`, String; attributes `rating`, `prompt`, `response`, `timestamp`, `model_id`).
   - `WebSocketApi` with route selection expression `$request.body.action`. Add `$connect`, `$disconnect`, and `sendMessage` routes, each integrated to their respective Lambda via `WebSocketLambdaIntegration`.
   - `NodejsFunction` for `ConnectionManager` (`src/lambdas/connection-manager/handler.ts`). Grant `dynamodb:PutItem` + `dynamodb:DeleteItem` on the connections table.
   - `NodejsFunction` for `StreamingInvoker` (`src/lambdas/streaming-invoker/handler.ts`). Grant `bedrock:InvokeModelWithResponseStream` and `execute-api:ManageConnections` on the WebSocket stage ARN (`arn:aws:execute-api:<region>:<account>:<api-id>/<stage>/*`).
   - `NodejsFunction` for `FeedbackHandler` (`src/lambdas/feedback-handler/handler.ts`). Grant `dynamodb:PutItem` on the feedback table.
   - `HttpApi` with `POST /feedback` integrated to the feedback handler Lambda.

3. **Write `src/lambdas/connection-manager/handler.ts`.** On `$connect`: extract `connectionId` from `requestContext`, write to `WebSocketConnections` with `expires_at = now + 7200`. On `$disconnect`: delete the item.

4. **Write `src/lambdas/streaming-invoker/handler.ts`.** Parse the WebSocket event body for `session_id` and `message`. Build the Bedrock request for Claude 3 Haiku. Call `bedrock-runtime:InvokeModelWithResponseStream`. Iterate the `ResponseStream`: for each `chunk` event, extract `delta.text` and call `apigatewaymanagementapi:PostToConnection` with `{ type: "chunk", text: deltaText }`. After the loop, send `{ type: "done", input_tokens, output_tokens }`.

5. **Write `src/lambdas/feedback-handler/handler.ts`.** Accept `POST /feedback` with body `{ session_id, message_id, rating, prompt, response }`. Write to the `ChatFeedback` DynamoDB table.

6. **Run `bun run synth`** to validate the CloudFormation template.

7. **Run `bun run deploy`** to provision all resources. Note the WebSocket API URL and HTTP API URL from the stack outputs.

8. **Build the React app.** Create a Vite project in `frontend/`. Key components:
   - `useWebSocket` hook: manages connection lifecycle, appends incoming chunk payloads to the current streaming message buffer.
   - `ChatMessage` component: renders a message bubble; if `isStreaming=true`, appends new chunks via state updates.
   - `FeedbackButtons` component: renders thumbs-up/down, calls `POST /feedback` on click.
   - Store `VITE_WS_URL` and `VITE_API_URL` as environment variables in `.env.local` set to the stack outputs.

9. **Test locally.** Run `bun run dev` from the `frontend/` directory with the deployed URLs. Send several messages and verify streaming behavior before deploying to Amplify.

10. **Deploy to Amplify Hosting.** Run `bun run build` in `frontend/`, then drag-drop the `dist/` folder in the Amplify console under "Deploy without Git". Alternatively, connect a GitHub repo and use Amplify's build pipeline with a `amplify.yml` specifying `bun run build`.

11. **Write `scripts/feedback-viewer.ts`.** Scan the `ChatFeedback` table, group by `rating`, print up/down ratio, and list the 3 lowest-rated responses sorted by timestamp. Run with `bun run scripts/feedback-viewer.ts`.

## Key Exam Concepts Practiced

- Bedrock streaming API (`InvokeModelWithResponseStream`) and the WebSocket delivery pattern (Task 2.4.2)
- API Gateway WebSocket API route selection and connection lifecycle management (Task 2.4.1)
- `execute-api:ManageConnections` permission and its scoping to stage ARNs (Task 2.4.1)
- AWS Amplify Hosting for rapid frontend deployment (Task 2.5.2)
- Feedback collection mechanisms and rating storage for LLM evaluation (Task 5.1.3)
- Lambda duration billing implications of streaming vs. synchronous Bedrock calls (Task 4.1.1)
- Token limit management and why Haiku is preferred for interactive streaming over Sonnet (Task 4.2.1)
- CloudWatch Logs for real-time debugging of WebSocket event routing (Task 2.5.6)
