# Project 03: Multi-Model Router with Fallback

## Exam Domains

| Domain | Task | Description |
|--------|------|-------------|
| 1.2 | Select and configure Foundation Models | Dynamic model selection, resilient AI systems, circuit breaker patterns, cross-region fallback |
| 2.4 | Implement Foundation Model API integrations | Resilient FM systems, exponential backoff, rate limiting, intelligent model routing |

## Overview

Production GenAI systems rarely rely on a single model invoked unconditionally. The AIP-C01 exam tests your ability to design routing logic that matches request characteristics to the most appropriate — and most cost-effective — model, then handle failures gracefully. This project builds exactly that: an API Gateway and Lambda layer that classifies incoming requests by complexity and routes them to a smaller, cheaper model for simple queries and a larger, more capable model for complex ones, with a full fault-tolerance stack underneath.

The resilience portion of the project is where the most exam-relevant learning happens. You will implement exponential backoff in the SDK retry configuration, model a circuit breaker state machine in Step Functions (closed → open → half-open), and configure Bedrock Cross-Region Inference so that when a model is rate-limited or unavailable in the primary region, requests automatically fall over to a secondary region. Together these patterns cover Tasks 1.2.3 and 2.4.3 in detail.

## Architecture

```
Client
    |
    v
API Gateway (HTTP API)  POST /invoke
    |
    v
Lambda: Router
    |-- Classifier: estimate complexity score (token count heuristic + keyword signals)
    |-- Simple query (score < threshold)  --> Bedrock: Claude 3 Haiku (primary region)
    |-- Complex query (score >= threshold) --> Bedrock: Claude 3 Sonnet (primary region)
    |
    | (on ThrottlingException or ModelNotReadyException)
    v
Step Functions: CircuitBreaker
    |-- State: CLOSED  (normal operation, route to primary)
    |-- State: OPEN    (recent failures > threshold, reject fast)
    |-- State: HALF_OPEN (probe request to check recovery)
    |
    | (OPEN state or primary region unavailable)
    v
Bedrock Cross-Region Inference (secondary region fallback)

CloudWatch Alarms --> SNS --> Lambda: CircuitBreakerStateManager
```

**AWS services used:**

- Amazon API Gateway (HTTP API) -- entry point for inference requests
- AWS Lambda (router + circuit breaker state manager) -- request classification, routing, fallback logic
- Amazon Bedrock (`bedrock:InvokeModel`) -- Claude 3 Haiku and Claude 3 Sonnet in primary region
- Amazon Bedrock Cross-Region Inference -- automatic fallback to secondary region inference profile
- AWS Step Functions (Express workflow) -- models circuit breaker state transitions
- Amazon DynamoDB -- stores circuit breaker state (CLOSED/OPEN/HALF_OPEN) and failure counts
- Amazon CloudWatch -- monitors error rates and triggers circuit breaker alarms
- Amazon SNS -- notifies the circuit breaker state manager on alarm state change
- AWS X-Ray -- traces requests across Lambda and Bedrock invocations
- AWS IAM -- least-privilege roles per component

## What You Will Build

1. A Lambda router function that scores request complexity using a simple heuristic (input token estimate + presence of multi-step reasoning keywords) and selects the appropriate model ID.
2. A DynamoDB table with a single item representing circuit breaker state: `{ state: CLOSED|OPEN|HALF_OPEN, failure_count: int, last_failure_ts: str, open_until_ts: str }`.
3. A Step Functions Express workflow (`CircuitBreakerCheck`) that the router invokes synchronously before each Bedrock call. The workflow reads DynamoDB state and either allows the call, rejects fast (OPEN), or runs a probe (HALF_OPEN).
4. A Lambda circuit breaker state manager triggered by a CloudWatch Alarm (Bedrock error rate > 20% over 2 minutes). This function transitions the state machine: CLOSED → OPEN.
5. A Cross-Region Inference profile in Bedrock configured to fall back from us-east-1 to us-west-2 for both model IDs.
6. Exponential backoff configured via the AWS SDK retry config in the router Lambda (max 3 retries, base delay 1s, exponential factor 2).
7. X-Ray active tracing on the Lambda function and API Gateway stage.
8. A CloudWatch dashboard showing: requests by model, error rate by model, circuit breaker state transitions, and p99 latency.
9. A test script that sends 20 requests — 10 simple and 10 complex — and prints the model used, latency, and token counts for each.

## Target Outcomes

By the end of this project you should be able to verify each of the following:

- [ ] Simple test queries (e.g., "What is an S3 bucket?") are consistently routed to Claude 3 Haiku; complex multi-step queries (e.g., "Compare the tradeoffs between Aurora Serverless and provisioned Aurora for a high-read OLTP workload, then recommend one with justification") are routed to Claude 3 Sonnet.
- [ ] The DynamoDB circuit breaker record updates correctly: simulating repeated Bedrock errors (by temporarily revoking model access or injecting errors) causes the state to transition to OPEN within the alarm evaluation window.
- [ ] While the circuit breaker is OPEN, the router returns a 503 with a `{ "error": "circuit open", "retry_after": <ts> }` body without making any Bedrock calls.
- [ ] Cross-region fallback can be demonstrated by invoking the Cross-Region Inference profile ARN directly and confirming the response comes from the secondary region (check the `x-amzn-bedrock-invocation-region` response header or CloudWatch logs).
- [ ] X-Ray traces in the console show the full call graph: API Gateway → Lambda → Step Functions → DynamoDB → Bedrock.
- [ ] You can explain the difference between Cross-Region Inference and manually duplicating Lambda + Bedrock in two regions.

## Prerequisites

**Local tooling:**

- Node.js 22+ with `bun` package manager (`npm install -g bun`)
- AWS CDK CLI (`npm install -g aws-cdk`)
- AWS CLI v2 with Bedrock, Lambda, API Gateway, Step Functions, DynamoDB, CloudWatch, SNS, and IAM permissions

**AWS service enablement:**

- Amazon Bedrock model access enabled for Claude 3 Haiku and Claude 3 Sonnet in both us-east-1 and us-west-2
- Bedrock Cross-Region Inference available in your primary region
- AWS X-Ray enabled (no additional activation required; tracing is configured per resource)

## Step-by-Step Build Guide

1. **Initialize the CDK project.** Copy `projects/cdk-template/` into `cdk/`. Update `package.json` `name` to `multi-model-router`. Run `bun install`.

2. **Write Lambda handler `src/lambdas/router/handler.ts`.** Implement `classifyComplexity(prompt: string): number` using estimated token count, reasoning keyword presence, and question count. Score >= 0.5 selects Claude 3 Sonnet; below that selects Claude 3 Haiku. Before each Bedrock call, invoke the `CircuitBreakerCheck` Step Functions Express workflow synchronously. On `ThrottlingException` after retries, fall back to the Cross-Region Inference profile ARN.

3. **Write Lambda handler `src/lambdas/circuit-breaker-state-manager/handler.ts`.** Triggered by SNS. On ALARM, read DynamoDB state and transition CLOSED → OPEN (set `open_until_ts = now + 60s`). On OK, transition OPEN → HALF_OPEN after expiry, then CLOSED after a clean probe window.

4. **Define the `RouterStack`** in `src/stacks/router-stack.ts`. Provision the following constructs:
   - `Table` for `circuit-breaker-state` (partition key `circuit_id`, String). Seed the initial item via a CDK custom resource or post-deploy script.
   - `StateMachine` (Express workflow) for `CircuitBreakerCheck`. States: `GetState` (DynamoDB `GetItem` task) → `CheckState` (Choice: OPEN → `RejectFast` Pass, HALF_OPEN → `ProbeAllowed` Pass, CLOSED → `Allowed` Pass). Grant `sfn:StartSyncExecution` to the router Lambda.
   - Router `NodejsFunction` with X-Ray active tracing, SDK retry config (3 retries, exponential backoff) set via `AWS_NODEJS_CONNECTION_REUSE_ENABLED` and Bedrock client config. Grant `bedrock:InvokeModel`, `dynamodb:GetItem`, `sfn:StartSyncExecution`.
   - Circuit breaker `NodejsFunction` for state management, subscribed to the SNS topic. Grant `dynamodb:GetItem`, `dynamodb:PutItem`.
   - `HttpApi` with `POST /invoke` route integrated to the router Lambda.
   - `Alarm` on Bedrock `InvocationClientErrors` metric (threshold > 20% over 2 evaluation periods). Alarm and OK actions publish to an `Topic`.
   - `Topic` with `LambdaSubscription` to the circuit breaker state manager Lambda.
   - `Dashboard` with widgets for requests by model, error rate, circuit state, and p99 latency.

5. **Configure Cross-Region Inference profiles** in the Bedrock console for both Claude 3 Haiku and Sonnet. Note the inference profile ARNs and set them as Lambda environment variables in the CDK stack.

6. **Run `bun run synth`** to validate the CloudFormation output.

7. **Run `bun run deploy`** to provision all resources. Seed the DynamoDB circuit breaker item (`circuit_id = "bedrock-primary"`, `state = "CLOSED"`, `failure_count = 0`) via `aws dynamodb put-item` after deploy.

8. **Enable X-Ray** on the API Gateway stage via the CDK `HttpStage` `throttle` and `detailedMetricsEnabled` props, and confirm active tracing is set on both Lambda functions.

9. **Run the test script** that sends 20 requests (10 simple, 10 complex). Verify routing behavior and that model selection, latency, and token counts are logged correctly.

10. **Simulate failures** by temporarily attaching a deny policy on `bedrock:InvokeModel`. Observe the CloudWatch alarm trigger the circuit breaker transition to OPEN, verify 503 fast-fail responses, then remove the deny policy and watch recovery through HALF_OPEN back to CLOSED.

11. **Review the X-Ray service map** in the console to confirm the full call graph: API Gateway → Lambda → Step Functions → DynamoDB → Bedrock.

## Key Exam Concepts Practiced

- Dynamic model selection based on request characteristics (Tasks 1.2.1, 1.2.2, 2.4.4)
- Circuit breaker pattern with Step Functions for fault-tolerant AI systems (Task 1.2.3)
- Bedrock Cross-Region Inference for regional failover without re-architecting (Task 1.2.3)
- Exponential backoff via SDK retry configuration (Task 2.4.3)
- Graceful degradation strategies (fast-fail with actionable error vs. silent hang) (Task 2.4.3)
- Cost optimization through tiered model routing — Haiku for simple, Sonnet for complex (Task 4.1.2)
- X-Ray distributed tracing across Lambda, Step Functions, and Bedrock (Task 2.5.6, 4.3.1)
- CloudWatch Alarms as operational triggers for automated remediation (Task 4.3.2)
