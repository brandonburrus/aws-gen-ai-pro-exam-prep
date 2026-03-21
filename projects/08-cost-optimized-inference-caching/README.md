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

- AWS CLI v2 with Lambda, ElastiCache, Bedrock, CloudWatch, and IAM permissions
- Python 3.11+ with `boto3`, `redis` (`pip install redis`), `numpy`
- AWS SAM CLI or CDK CLI recommended (Lambda needs VPC config to reach ElastiCache)

**AWS service enablement:**

- Amazon Bedrock model access enabled for Claude 3 Haiku and Amazon Titan Text Embeddings v2
- ElastiCache Serverless available in your region, or ElastiCache for Redis in a VPC

**Cost note:**

ElastiCache Serverless is billed per GB-hour of data stored and per ECPU consumed. For this lab (small data, low traffic) cost is negligible — typically under $0.10 for a 3-hour session. If using a provisioned `t3.micro` cluster, it costs approximately $0.017/hr.

## Step-by-Step Build Guide

1. **Create the ElastiCache Serverless cache** (or a `t3.micro` Redis cluster in a VPC). Note the endpoint. If using a VPC-based cluster, ensure your Lambda security group can reach the ElastiCache security group on port 6379.

2. **Design the cache key and value schema.** Key: `semantic_cache:<embedding_hash>` where `embedding_hash` is the first 16 hex chars of the SHA256 of the embedding vector (for fast O(1) exact-match lookups before doing cosine similarity). Value: JSON string `{ "embedding": [...], "response": str, "model_id": str, "cached_at": str }`. Use Redis `SCAN` to iterate all keys for similarity search (acceptable for small caches; at scale use a vector store instead).

3. **Implement `embedding.py`.** Function `get_embedding(text: str) -> list[float]`: calls `bedrock:InvokeModel` with Titan Text Embeddings v2. Returns the 1536-dimension float array. Cache the embedding locally in the Lambda execution context (module-level dict) to avoid re-embedding the same text within a warm invocation window.

4. **Implement `semantic_cache.py`.** Functions:
   - `cosine_similarity(a: list, b: list) -> float`: dot product / (|a| * |b|).
   - `cache_lookup(embedding: list, threshold: float = 0.92) -> dict | None`: connect to Redis, scan all keys, load each value, compute cosine similarity, return the best match above threshold.
   - `cache_store(embedding: list, response: str, model_id: str)`: serialize and store in Redis with TTL 3600.

5. **Implement `token_estimator.py`.** Function `estimate_tokens(text: str) -> int`: use `ceil(len(text.split()) * 1.3)`. Function `check_budget(prompt: str, max_tokens: int) -> bool`.

6. **Implement `routing.py`.** Function `select_model() -> str`: read a DynamoDB item `{ pk: "routing-config", use_provisioned: bool }`. If `use_provisioned=true`, return the provisioned throughput ARN (or a second model ID to simulate). Otherwise return the on-demand model ID.

7. **Implement `cost_optimized_invoker.py` (Lambda handler).** Wire together all steps in sequence. After each Bedrock response, parse the usage block to get actual token counts (not estimates). Emit CloudWatch metrics via `put_metric_data`. Return `{ "response": str, "cache_hit": bool, "similarity_score": float | null, "input_tokens": int, "output_tokens": int, "estimated_cost_usd": float }`.

8. **Deploy the Lambda** with the VPC configuration (if using VPC-based ElastiCache) and correct IAM role.

9. **Create the CloudWatch dashboard.** Add all metric widgets described above.

10. **Tag all resources** with `Project=08-cost-optimization` using AWS CLI tag commands or CDK resource tags.

11. **Write and run `benchmark.py`.** Generate 25 unique prompts on a consistent topic. Generate 25 rephrased versions. Shuffle them randomly. Send all 50. Collect and print results.

## Key Exam Concepts Practiced

- Token estimation before invocation to enforce cost budgets (Task 4.1.1)
- Semantic caching with vector similarity to reduce redundant Bedrock calls (Task 4.1.4)
- Similarity threshold selection: too low causes incorrect cache hits; too high degrades hit rate (Task 4.1.4)
- On-demand vs. provisioned throughput: when each is cost-effective (Task 4.1.3)
- Custom CloudWatch metrics for cost tracking and anomaly detection (Task 4.3.2)
- AWS Cost Explorer tag-based reporting for per-project cost attribution (Task 4.1)
- ElastiCache for Redis as a low-latency cache layer in a GenAI pipeline (Task 4.1.4)
- Latency-cost tradeoff: cache lookup adds ~5ms but saves ~3000ms of Bedrock latency (Task 4.2.1)
