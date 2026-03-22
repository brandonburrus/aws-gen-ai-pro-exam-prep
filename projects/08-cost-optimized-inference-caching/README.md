# Project 08: Cost-Optimized Inference with Caching and Token Management

## Exam Domains

| Domain | Task | Description |
|--------|------|-------------|
| 4.1 | Implement cost optimization and resource efficiency strategies | Token estimation, caching systems, tiered model usage, provisioned throughput vs. on-demand |
| 4.2 | Optimize application performance | Latency-cost tradeoffs, pre-computation, response streaming, performance benchmarking |

## Overview

Domain 4 (Operational Efficiency) is 12% of the exam and focuses on a problem real-world GenAI practitioners face daily: Bedrock invocations are priced per token, and without controls, a single chatbot can incur unexpected costs. This project builds the full cost-optimization stack: token count estimation before invocation, a semantic cache that reuses responses for similar (not just identical) prompts, max token budget enforcement, and traffic-based routing between on-demand and provisioned throughput.

The semantic cache is the most technically interesting component. Unlike a key-value cache (which only hits on exact string matches), a semantic cache embeds the incoming prompt, searches ElastiCache for similar embeddings above a similarity threshold, and returns the cached response if a match exists. This means "What is S3?" and "Can you explain what Amazon S3 is?" resolve to the same cached answer — a significant token saving at scale. This pattern maps directly to Tasks 4.1.4 (intelligent caching systems) and 4.2 (performance optimization).

## Architecture

```
Client  POST /invoke  { "prompt": str, "max_tokens": int, "session_id": str }
    |
    v
Lambda: CostOptimizedInvoker
    |
    |-- STEP 1: Token estimation
    |       estimate_tokens(prompt) --> if > budget: return 429 with token count
    |
    |-- STEP 2: Semantic cache check
    |       embed(prompt) --> Titan Text Embeddings
    |       cache_lookup(embedding) --> ElastiCache (Redis)
    |           if hit (cosine_similarity > 0.92): return cached response + metadata
    |           if miss: continue
    |
    |-- STEP 3: Model routing
    |       if current_rps > PROVISIONED_THRESHOLD:
    |           use provisioned throughput ARN
    |       else:
    |           use on-demand model ID
    |
    |-- STEP 4: Bedrock invocation
    |       bedrock:InvokeModel (Claude 3 Haiku, on-demand or provisioned)
    |       record token usage
    |
    |-- STEP 5: Cache store
    |       store { embedding, response, prompt_hash, timestamp } in ElastiCache
    |       TTL: 1 hour
    |
    |-- STEP 6: Emit cost metrics
    |       CloudWatch: InputTokens, OutputTokens, EstimatedCostUSD, CacheHit (0|1)
    |
    v
CloudWatch Dashboard: CostOptimization
    Cost Explorer tag-based report (tag: Project=08-cost-optimization)
```

**AWS services used:**

- AWS Lambda -- the cost-optimized invoker function
- Amazon ElastiCache for Redis (Serverless or t3.micro cluster) -- semantic cache store
- Amazon Bedrock (Claude 3 Haiku) -- on-demand inference
- Amazon Bedrock Provisioned Throughput -- dedicated capacity (used in routing decision; you can simulate by toggling model IDs rather than purchasing actual provisioned throughput, which requires a minimum 1-month commitment)
- Amazon Titan Text Embeddings v2 -- generates prompt embeddings for cache lookup
- Amazon CloudWatch Metrics + Dashboard -- cost and performance metrics
- AWS Cost Explorer -- tag-based cost report for this project's resources
- Amazon API Gateway (HTTP API) -- optional HTTP entry point
- AWS IAM -- Lambda execution role

## What You Will Build

1. An ElastiCache Serverless Redis cache (or a `cache.t3.micro` cluster in a VPC) with a keyspace for storing `{ embedding_vector, response_text, original_prompt_hash, model_id, cached_at }` as Redis JSON or a serialized Python dict.
2. A Lambda function implementing the 6-step pipeline above. The semantic similarity check uses cosine similarity computed in Python (numpy or manual dot-product calculation — no external ML library needed for 1536-dimension vectors at this scale).
3. A token estimator function `estimate_tokens(text: str) -> int` using the heuristic `len(text.split()) * 1.3` (a reasonable approximation for Claude). If the estimate exceeds the caller's `max_tokens` budget, return HTTP 429 with `{ "error": "TokenBudgetExceeded", "estimated_tokens": int, "budget": int }`.
4. A routing decision function that reads a CloudWatch metric (average Lambda invocations per minute over the last 5 minutes) and selects provisioned throughput if above a configured threshold, otherwise on-demand. For the lab, simulate this by toggling the model ID based on a DynamoDB flag (no need to purchase actual provisioned throughput).
5. Custom CloudWatch metrics under namespace `GenAI/CostOptimization`:
   - `InputTokens` (count, dimension: `ModelId`)
   - `OutputTokens` (count, dimension: `ModelId`)
   - `EstimatedCostUSD` (value, dimension: `ModelId`)
   - `CacheHit` (0 or 1, dimension: `CacheType=Semantic`)
   - `CacheLatencyMs` (time for cache lookup, dimension: `CacheType=Semantic`)
6. A CloudWatch dashboard `CostOptimization` with widgets for:
   - Cache hit rate (CacheHit average over time)
   - Total estimated cost per hour (sum of EstimatedCostUSD)
   - Token usage by model (InputTokens + OutputTokens)
   - Cache lookup latency vs. Bedrock invocation latency (two lines on one chart)
7. A Cost Explorer tag report setup: tag all project resources with `Project=08-cost-optimization` and configure a Cost Explorer monthly cost report filtered on that tag.
8. A benchmark script (`benchmark.py`) that sends 50 requests — 25 unique prompts and 25 rephrased duplicates of those same prompts (semantically similar but not textually identical). Measure and print: cache hit count, total tokens consumed, total estimated cost without caching vs. with caching, average latency.

## Target Outcomes

By the end of this project you should be able to verify each of the following:

- [ ] Sending a prompt that exceeds the `max_tokens` budget returns HTTP 429 with a clear error body — no Bedrock invocation is made.
- [ ] Sending the same question twice (exact match) returns the second response from cache in under 200ms (compared to 2-5 seconds for a live Bedrock call).
- [ ] Sending a semantically similar but textually different rephrase of a cached question (e.g., "What is DynamoDB?" after caching "Explain DynamoDB to me") returns a cache hit with similarity score shown in the response metadata.
- [ ] The benchmark script shows a cache hit rate of at least 40% across the 50-request test set, demonstrating meaningful cost reduction.
- [ ] The CloudWatch dashboard shows the `CacheHit` metric split between hits and misses, and the `EstimatedCostUSD` metric is lower during the second half of the benchmark (when cached responses are served).
- [ ] You can explain why semantic caching with a similarity threshold is preferable to exact-match caching for LLM workloads, and what the risk is of setting the similarity threshold too low.

## Prerequisites

**Local tooling:**

- Node.js 22+ with npm (for Lambda handler development and AWS SDK v3)
- AWS CLI v2 with Lambda, ElastiCache, Bedrock, CloudWatch, and IAM permissions
- Python 3.11+ with `boto3`, `redis`, and `numpy` (for the benchmark script)

**AWS service enablement:**

- Amazon Bedrock model access enabled for Claude 3 Haiku and Amazon Titan Text Embeddings v2
- ElastiCache Serverless available in your region, or ElastiCache for Redis in a VPC

**Cost note:**

ElastiCache Serverless is billed per GB-hour of data stored and per ECPU consumed. For this lab (small data, low traffic) cost is negligible — typically under $0.10 for a 3-hour session. If using a provisioned `t3.micro` cluster, it costs approximately $0.017/hr.

## Step-by-Step Build Guide

1. **Create a VPC** with one private subnet group (no NAT gateway or internet gateway needed if using VPC endpoints for AWS services, or a NAT gateway if the Lambda needs to reach the Redis endpoint and AWS APIs). Create two security groups: one for Lambda (outbound port 6379 to the ElastiCache security group, outbound 443 for AWS API calls) and one for ElastiCache (inbound port 6379 from the Lambda security group).

2. **Create an ElastiCache Serverless Redis cache** (or a `cache.t3.micro` cluster) within the VPC. Note the endpoint address -- this will be a Lambda environment variable.

3. **Create a DynamoDB table** named `routing-config` (partition key `pk`, String). Seed it with `{ pk: "routing-config", use_provisioned: false }` using `aws dynamodb put-item`.

4. **Write the cost-optimized invoker Lambda handler** (`lambdas/cost-optimized-invoker/handler.ts`). Implement the six-step pipeline:
   - Step 1 (token estimation): estimate tokens via `Math.ceil(words * 1.3)`. If over budget, return HTTP 429.
   - Step 2 (semantic cache check): embed the prompt with Titan Text Embeddings v2, connect to Redis, scan keys, compute cosine similarity, return cache hit if score > 0.92.
   - Step 3 (routing): read the DynamoDB routing flag; select provisioned ARN or on-demand model ID.
   - Step 4 (Bedrock invocation): call `bedrock:InvokeModel` with the selected model ID.
   - Step 5 (cache store): serialize `{ embedding, response, model_id, cached_at }` and write to Redis with TTL 3600.
   - Step 6 (metrics): emit `InputTokens`, `OutputTokens`, `EstimatedCostUSD`, `CacheHit`, and `CacheLatencyMs` to CloudWatch under namespace `GenAI/CostOptimization`.

5. **Create the Lambda function** in the VPC private subnet with the Lambda security group. Runtime: Node.js 22.x. Set a 30-second timeout. Create an execution role granting `bedrock:InvokeModel` (for Haiku and Titan Text Embeddings), `dynamodb:GetItem` on the routing config table, `cloudwatch:PutMetricData`, and VPC networking permissions (`ec2:CreateNetworkInterface`, `ec2:DescribeNetworkInterfaces`, `ec2:DeleteNetworkInterface`).

6. **Create an HTTP API Gateway** with a `POST /invoke` route integrated to the Lambda function.

7. **Create a CloudWatch dashboard** named `CostOptimization` with widgets for: cache hit rate (`CacheHit` average over time), total estimated cost per hour (sum of `EstimatedCostUSD`), token usage by model (`InputTokens` + `OutputTokens`), and cache lookup latency vs. Bedrock invocation latency.

8. **Tag all resources** with `Project=08-cost-optimization` for Cost Explorer reporting.

9. **Deploy all resources to your AWS account** using your preferred infrastructure-as-code tool or the AWS Management Console.

10. **Write and run `scripts/benchmark.py`.** Generate 25 unique prompts on a consistent topic. Generate 25 rephrased versions. Shuffle and send all 50. Print: cache hit count, total tokens consumed, estimated cost without caching vs. with caching, and average latency. Confirm the hit rate is at least 40%.

11. **Review the CloudWatch dashboard.** Verify that `CacheHit` metrics show a rising hit rate during the second half of the benchmark, and that `EstimatedCostUSD` is lower during cache-hit periods.

## Key Exam Concepts Practiced

- Token estimation before invocation to enforce cost budgets (Task 4.1.1)
- Semantic caching with vector similarity to reduce redundant Bedrock calls (Task 4.1.4)
- Similarity threshold selection: too low causes incorrect cache hits; too high degrades hit rate (Task 4.1.4)
- On-demand vs. provisioned throughput: when each is cost-effective (Task 4.1.3)
- Custom CloudWatch metrics for cost tracking and anomaly detection (Task 4.3.2)
- AWS Cost Explorer tag-based reporting for per-project cost attribution (Task 4.1)
- ElastiCache for Redis as a low-latency cache layer in a GenAI pipeline (Task 4.1.4)
- Latency-cost tradeoff: cache lookup adds ~5ms but saves ~3000ms of Bedrock latency (Task 4.2.1)
