# AIP-C01 Exam Gotchas

A comprehensive collection of tricky, counterintuitive, and commonly confused facts organized by domain and task. These are the details that exam questions exploit to create plausible-but-wrong answer choices.

## How to Use This Document

Each gotcha follows this format:

> **The misleading assumption** -- why it is wrong and what the correct answer is.

Gotchas are grouped by domain and task. Many gotchas span multiple tasks; they appear under the most relevant one with cross-references where needed.

---

## Domain 1: Design and Implement Generative AI Solutions (31%)

### Task 1.1: Design and Implement Solutions Using Foundation Models

> **"Bedrock supports resource-based policies for model access control."** -- Bedrock does NOT support resource-based policies. All access control is done through identity-based IAM policies. Cross-account access requires IAM role assumption via STS, not resource policy sharing.

> **"Foundation model ARNs include your AWS account ID."** -- Foundation model ARNs use an empty account field (`arn:aws:bedrock:us-east-1::foundation-model/...`) because they are AWS-owned. Only custom models, agents, knowledge bases, and guardrails use your account ID.

> **"The Converse API is always the right choice for Bedrock inference."** -- Converse is the recommended model-agnostic API for multi-turn chat, but you must use InvokeModel for embeddings and image generation. Converse does not support these use cases.

> **"ConverseStream uses the bedrock:InvokeModel permission."** -- ConverseStream requires `bedrock:InvokeModelWithResponseStream`, which is a separate IAM action. Denying both actions is required to fully block inference access.

> **"You can stream Bedrock responses using the AWS CLI."** -- The AWS CLI does NOT support streaming operations. You must use an SDK (Python boto3, TypeScript SDK v3, etc.) for ConverseStream and InvokeModelWithResponseStream.

> **"Streaming changes the cost of Bedrock inference."** -- Streaming does NOT change cost. You pay the same per-token price whether you use synchronous or streaming APIs.

> **"The Responses API and Converse API are the same thing."** -- They are different. The Responses API (on the `bedrock-mantle` endpoint) is the newest, supports stateful conversations and built-in tool use, and is recommended for new applications. The Converse API (on `bedrock-runtime`) is the model-agnostic unified interface for native Bedrock integration. Know when to pick each.

> **"Custom (fine-tuned) models can be invoked on-demand like base models."** -- Custom models created through Bedrock fine-tuning or continued pre-training REQUIRE Provisioned Throughput for inference. You cannot invoke them on-demand.

> **"Batch inference works with Provisioned Throughput."** -- Batch inference is NOT supported for provisioned models. Use on-demand capacity for batch jobs.

> **"SageMaker and Bedrock are interchangeable for deploying foundation models."** -- Use Bedrock when you want serverless, zero-ops inference. Use SageMaker when you need full control over infrastructure, LoRA with custom hyperparameters, DPO/PPO alignment, or models not available on Bedrock.

> **"Bedrock Marketplace models run on Bedrock infrastructure."** -- Marketplace models are deployed to SageMaker AI endpoints and accessed through Bedrock APIs. Do NOT modify these endpoints directly in SageMaker or they may break. Use the Bedrock Marketplace console/API instead.

### Task 1.2: Design Resilient Architectures

> **"Cross-Region Inference (CRIS) costs extra."** -- Geographic CRIS has no additional cost (same pricing as on-demand). Global CRIS actually provides approximately 10% cost savings.

> **"CRIS can only route to Regions you have manually enabled."** -- CRIS can route to Regions NOT manually enabled in your account.

> **"CloudTrail logs CRIS requests in every Region the request touches."** -- CloudTrail logs CRIS requests ONLY in the source Region.

> **"SCPs with aws:RequestedRegion conditions work fine with Global CRIS."** -- You must update `aws:RequestedRegion` conditions to allow `"unspecified"` for Global CRIS. Otherwise, requests will be denied.

> **"Global CRIS needs a three-part IAM policy."** -- Correct, but this is a gotcha because people forget. You need permissions for: (1) the regional inference profile, (2) the regional foundation model, AND (3) the global foundation model.

> **"The circuit breaker pattern for foundation models requires Lambda."** -- Step Functions has an optimized (direct) integration with Bedrock InvokeModel. You can implement a circuit breaker using Step Functions + DynamoDB TTL without Lambda.

> **"Express Workflows support .waitForTaskToken."** -- Express Workflows do NOT support `.sync` or `.waitForTaskToken` integration patterns. If you need human approval or long-running job completion, you must use Standard Workflows.

### Task 1.3: Design Data Pipelines for Foundation Models

> **"Data Wrangler and AWS Glue serve the same purpose."** -- Data Wrangler is a visual, low-code data preparation tool (data quality reports, exploratory analysis). AWS Glue is a serverless ETL service for large-scale data integration. Use Data Wrangler for ML data prep; use Glue for ETL.

> **"SageMaker Processing and Data Wrangler are redundant."** -- Processing Jobs are code-first, script-based data processing on managed compute. Data Wrangler is visual/low-code. Processing Jobs are what runs under the hood for Clarify analysis.

> **"You can change the parsing or chunking strategy after connecting a data source."** -- You CANNOT change the parsing strategy or chunking strategy after connecting a data source to a Knowledge Base. You must create a new data source.

> **"Semantic chunking is free."** -- Semantic chunking uses a foundation model to compute sentence embeddings for boundary detection, which incurs additional model inference charges compared to fixed-size chunking.

### Task 1.4: Design and Implement Vector Stores

> **"Any vector store supports hybrid search."** -- Hybrid search (keyword + semantic) is only supported by Amazon OpenSearch Serverless, Amazon Aurora PostgreSQL (pgvector), and MongoDB Atlas. It requires a filterable text field.

> **"Binary vectors work with any Bedrock-supported vector store."** -- Binary vectors are only supported with Amazon OpenSearch Serverless and Amazon OpenSearch Managed Clusters. Not Aurora, not Pinecone, not S3 Vectors, not Neptune.

> **"OpenSearch Serverless for Bedrock Knowledge Bases can use the nmslib engine."** -- OpenSearch Serverless with Bedrock Knowledge Bases must use the faiss engine. nmslib is NOT supported for filtering.

> **"You can change the embedding model after creating a Knowledge Base."** -- You CANNOT change the embedding model after creation. You must create a new Knowledge Base. The same embedding model used at ingestion MUST be used at query time.

> **"Titan Embeddings V1 supports configurable dimensions."** -- Titan V1 is fixed at 1536 dimensions. Titan Embeddings V2 supports configurable dimensions (256, 512, 1024).

> **"Cohere Embed and Titan Embeddings have the same max token input."** -- Cohere Embed has a 512 max token input, while Titan Embeddings supports up to 8192 tokens. This matters for chunking strategy.

> **"startsWith and stringContains metadata filters work on all vector stores."** -- `startsWith`, `stringContains`, and `listContains` filters are OpenSearch Serverless ONLY.

> **"Hierarchical chunking returns exactly the number of results you request."** -- Hierarchical chunking may return FEWER results than requested because child chunks are replaced by their parent chunks, and multiple children can share the same parent.

> **"No chunking preserves page number citations."** -- When using no chunking (each file = one chunk), you CANNOT view page numbers in citations and cannot filter by `x-amz-bedrock-kb-document-page-number`.

### Task 1.5: Design and Implement Retrieval Mechanisms

> **"Reranking works on all content types."** -- Reranking only applies to textual data. It does not work on images, audio, or video.

> **"Implicit metadata filtering works with any foundation model."** -- Implicit metadata filtering (auto-generating filters from user queries) only works with Anthropic Claude 3.5 Sonnet.

> **"A higher numberOfResults always improves RAG quality."** -- The maximum is 100 results per query. More results increase input token costs. Use reranking to retrieve more initially but return fewer, more relevant results to the generation model.

> **"Query decomposition is always on."** -- Query decomposition must be explicitly enabled through the `orchestrationConfiguration` in RetrieveAndGenerate requests.

> **"The Retrieve API and RetrieveAndGenerate API return the same thing."** -- Retrieve returns raw chunks with metadata and scores. RetrieveAndGenerate retrieves chunks AND generates a natural language response with citations in a single call.

### Task 1.6: Design and Implement Prompt Engineering Strategies

> **"Prompt Management drafts are immutable."** -- Drafts are the ONLY mutable version. All numbered versions are immutable snapshots. To update, modify the draft and create a new version.

> **"You can have unlimited prompt variants."** -- Each prompt supports up to 3 variants for side-by-side comparison.

> **"You invoke a prompt version by passing the prompt ID."** -- You invoke a prompt version via the Converse API by passing its full ARN (including version number) as the `modelId` parameter.

> **"Prompt caching works on all models."** -- Prompt caching is supported on specific models: Claude (Opus, Sonnet, Haiku 4.5+) and Amazon Nova (Micro, Lite, Pro, Premier, Nova 2 Lite). Check model support.

> **"Prompt cache lives forever."** -- Cache has a TTL (most models: 5 minutes; some support extended 1-hour TTL). The TTL resets with each cache hit but expires after the TTL window with no hits.

> **"Prompt caching reduces output token costs."** -- Prompt caching reduces INPUT token costs (up to 90%) and inference latency (up to 85%). Output token pricing is unchanged.

---

## Domain 2: Develop Generative AI Applications (26%)

### Task 2.1: Design and Implement Agentic AI Solutions

> **"Bedrock Agents and Prompt Flows serve the same purpose."** -- Agents are AUTONOMOUS with a ReAct reasoning loop (the model decides what to do). Flows are DETERMINISTIC pipelines (you define the path). Choose Agents for open-ended tasks requiring reasoning; choose Flows for repeatable AI pipelines.

> **"Lambda permissions for agent action groups go on the agent's service role."** -- Lambda permissions for agent action groups are granted via a RESOURCE-BASED POLICY on the Lambda function (allowing `bedrock.amazonaws.com` to invoke it), NOT via the agent's IAM service role.

> **"Bedrock Agents use service-linked roles."** -- Bedrock does NOT create service-linked roles. You must create and manage service roles yourself (or let the console create them).

> **"Return of Control uses Lambda."** -- Return of Control is the mechanism where the agent PAUSES and returns parameters to your application for human approval. It works WITHOUT Lambda. Your application inspects the returned parameters, executes the action, and returns results via `sessionState.returnControlInvocationResults`.

> **"AgentCore Runtime uses Lambda or containers for isolation."** -- AgentCore Runtime uses dedicated microVMs for session isolation, not containers and not Lambda.

> **"Strands Agents is an AWS-proprietary service."** -- Strands Agents SDK is open-source (Apache 2.0). It works with any foundation model, not just Bedrock models.

> **"Agent Squad and Bedrock Multi-Agent Collaboration are the same."** -- Agent Squad (formerly Multi-Agent Orchestrator) is open-source and self-managed. Bedrock Multi-Agent Collaboration is fully managed with supervisor/routing patterns. Choose based on whether you need flexibility or simplicity.

> **"AgentCore Gateway requires rewriting your APIs."** -- AgentCore Gateway converts existing APIs (OpenAPI specs, Lambda functions, API Gateway endpoints) into MCP-compatible tools WITHOUT code changes.

> **"MCP servers on AgentCore can use any transport."** -- AgentCore requires streamable-http transport. MCP servers must listen on host `0.0.0.0`, port `8000`, and use ARM64 containers.

> **"Bedrock Flows support nested DoWhile loops."** -- DoWhile loops do NOT support nesting. Each loop allows up to 5 exit conditions and a configurable `maxIterations` (default 10).

> **"Every Flow can have multiple Input nodes."** -- Every flow has exactly ONE Input node but can have MULTIPLE Output nodes.

> **"Inline Code nodes in Flows support any Python package."** -- Inline Code nodes run in a sandboxed Python environment with NO external packages. The last expression is the return value. Memory limit is 128KB.

### Task 2.2: Deploy Foundation Models

> **"SageMaker endpoints and Bedrock have the same billing model."** -- SageMaker charges per-instance-hour (you pay while the endpoint is running, even idle). Bedrock on-demand charges per-token. This distinction drives cost optimization decisions.

> **"SageMaker Serverless Inference scales to zero with no trade-offs."** -- Serverless Inference does scale to zero, but it has cold starts. Max memory is 6 GB. Payload limit is 4 MB (vs 25 MB for real-time). Timeout is 60 seconds.

> **"SageMaker Async Inference cannot scale to zero."** -- Async Inference CAN scale to zero when the queue is empty. It supports payloads up to 1 GB and processing times up to 1 hour.

> **"Shadow testing sends responses from the new model to users."** -- Shadow testing sends a COPY of production traffic to the new model for comparison, but the new model's responses are NOT served to users. You compare metrics in CloudWatch.

### Task 2.3: Design and Implement Enterprise Integration

> **"Cognito User Pools and Identity Pools serve the same purpose."** -- User Pools handle authentication (who are you?) and return JWTs. Identity Pools handle authorization (what AWS resources can you access?) and return temporary AWS credentials. You need both for a full auth flow.

> **"API Gateway Cognito authorizers validate access tokens."** -- Cognito authorizers on REST APIs validate the ID token. JWT authorizers on HTTP APIs can validate either ID or access tokens. For scope-based authorization, use the access token with a JWT authorizer.

> **"Cognito User Pool sign-in methods can be changed after creation."** -- The sign-in method (email, phone, username) CANNOT be changed after User Pool creation.

> **"WAF runs after Cognito and IAM authorization."** -- WAF is evaluated FIRST, before all other API Gateway access controls (Cognito authorizers, IAM, Lambda authorizers).

> **"WAF rate-based rules take effect immediately."** -- There is a 30-50 second mitigation lag after the threshold is exceeded. Bot Control (Targeted) is faster at less than 10 seconds but costs extra.

### Task 2.4: Design and Implement Foundation Model API Integration

> **"max_tokens controls what you pay for."** -- `max_tokens` is deducted from your quota at request START, not end. You pay for actual tokens generated, but quota is reserved upfront. This means setting max_tokens too high wastes quota even if the model generates fewer tokens.

> **"Output tokens consume the same quota as input tokens."** -- The burndown rate for output tokens is 5:1. Each output token consumes 5x more quota than an input token. This applies to Bedrock quota management, not billing.

> **"Service tiers are configured at the account or model level."** -- Service tiers (Standard, Priority, Flex, Reserved) are set PER API CALL using the `serviceTier` parameter. Different calls to the same model can use different tiers.

> **"Structured Outputs requires post-processing."** -- Bedrock Structured Outputs uses constrained decoding to GUARANTEE schema-compliant JSON responses. No post-processing or retry logic needed.

> **"Step Functions needs Lambda to call Bedrock."** -- Step Functions has an optimized direct integration with Bedrock InvokeModel. No Lambda function is needed as an intermediary.

### Task 2.5: Design and Implement Application Integration

> **"Knowledge Base nodes in Flows always return generated text."** -- A Knowledge Base node WITHOUT a `modelId` returns raw retrieval results (array of chunks). WITH a `modelId`, it returns generated text. This distinction matters for flow design.

> **"Guardrails can be applied to any Flow node type."** -- Guardrails can only be applied to Prompt nodes and Knowledge Base nodes (and only when the KB node uses RetrieveAndGenerate).

> **"Condition nodes evaluate all matching conditions."** -- Condition nodes evaluate conditions IN ORDER. The first match wins. A default path handles unmatched cases.

---

## Domain 3: Secure Generative AI Solutions (20%)

### Task 3.1: Design and Implement Input/Output Safety Controls

> **"The Prompt Attack filter works on both input and output."** -- The Prompt Attack filter (detecting jailbreaks and prompt injection) is INPUT-ONLY. It does not apply to model outputs.

> **"Contextual Grounding checks work on both input and output."** -- Contextual Grounding checks are OUTPUT-ONLY. They detect hallucinations by checking if responses are grounded in source material.

> **"Guardrails only work with Bedrock-hosted models."** -- Guardrails can be applied to ANY model (Bedrock-hosted, self-hosted, or third-party) using the `ApplyGuardrail` API.

> **"Async streaming guardrail mode supports PII masking."** -- Async streaming mode does NOT support masking. Only synchronous guardrail mode supports masking. Async mode sends chunks immediately (no latency impact) but may initially pass inappropriate content.

> **"Standard Tier and Classic Tier Guardrails have the same capabilities."** -- Standard Tier adds: enhanced contextual understanding, typo detection, 60+ language support, code domain protection, and the ability to distinguish jailbreaks from prompt injection. Standard Tier requires opt-in to cross-Region inference.

> **"Guardrails Detect mode blocks harmful content."** -- Detect mode detects but takes NO action. Content passes through to the user. This is useful for testing and monitoring before enabling blocking.

> **"Automated Reasoning Checks use machine learning."** -- Automated Reasoning Checks use formal mathematical techniques (not ML) to validate responses against logical rules and policies. This is provably correct verification.

### Task 3.2: Implement Data Security for Generative AI Solutions

> **"Bedrock stores your inference data."** -- Bedrock does NOT store text, images, or documents provided as inference content. Data is used only to generate the response and is not retained.

> **"Model invocation logging is enabled by default."** -- Model invocation logging is DISABLED by default. You must explicitly enable it via the `PutModelInvocationLoggingConfiguration` API.

> **"Model invocation logs can go to any S3 bucket."** -- The S3 bucket for invocation logging must be in the SAME Region as the logging configuration. If using SSE-KMS, the bucket needs a KMS encryption policy.

> **"CloudTrail automatically logs Bedrock data events."** -- CloudTrail management events are automatic, but DATA events (which include model invocation details) must be explicitly enabled. This is a common exam trap.

> **"KMS can directly encrypt large AI training datasets."** -- KMS can only directly encrypt data up to 4 KB. For larger data, you must use envelope encryption (generate a data key with GenerateDataKey, encrypt locally). The AWS Encryption SDK automates this.

> **"Use Macie and Comprehend interchangeably for PII detection."** -- Use Macie for discovering PII in S3 data stores (bulk, at-rest scanning of training data). Use Comprehend (or Bedrock Guardrails PII filters) for detecting/redacting PII in real-time text processing (in-transit).

> **"Secrets Manager and Parameter Store are interchangeable."** -- Secrets Manager has built-in rotation, higher cost, and is designed for credentials. Parameter Store has no built-in rotation (requires custom Lambda), lower cost, and is designed for configuration values.

> **"Bedrock uses service-linked roles."** -- Bedrock does NOT use service-linked roles. You must create and manage service roles yourself. The confused deputy problem is mitigated with `aws:SourceAccount` and `AWS:SourceArn` conditions in the trust policy.

### Task 3.3: Implement Governance for Generative AI Solutions

> **"Model Registry and Model Cards serve the same purpose."** -- Model Registry tracks the "what" and "where" (versioning, approval workflows, deployment lineage). Model Cards document the "why" and "how" (intended use, risk rating, training details, compliance documentation).

> **"SageMaker Model Monitor works with Bedrock endpoints."** -- Model Monitor is for SageMaker endpoints ONLY. For Bedrock, use CloudWatch metrics and model invocation logging.

> **"SCPs grant permissions."** -- SCPs only RESTRICT permissions. They set the maximum permissions boundary. Even if an IAM policy allows an action, an SCP deny takes precedence. SCPs do not affect the management account.

> **"AmazonBedrockFullAccess is a minimal permission policy."** -- AmazonBedrockFullAccess includes permissions for EC2 (VPC config), IAM (service roles), KMS (encryption), and SageMaker (custom models). In a least-privilege scenario, create a custom policy.

> **"You can enforce guardrails only in application code."** -- You can enforce guardrails via IAM policy using the `bedrock:GuardrailIdentifier` condition key. If the guardrail in the policy does not match the one in the API call, the request is denied.

> **"Models from all providers on Bedrock can be restricted using Marketplace product IDs."** -- Models from Amazon, DeepSeek, Mistral AI, Meta, Qwen, and OpenAI are NOT sold through AWS Marketplace and have no product keys. Restrict them by denying `bedrock:InvokeModel` with their model IDs in the Resource field.

### Task 3.4: Implement Responsible AI Practices

> **"SageMaker Clarify is only for traditional ML bias detection."** -- Clarify also provides foundation model evaluation (FMEval) capabilities including accuracy, semantic robustness, factual knowledge, prompt stereotyping, and toxicity detection.

> **"Bedrock Model Evaluation and SageMaker Clarify FMEval are redundant."** -- Both evaluate foundation models, but they serve different scenarios. Bedrock Evaluation is for comparing Bedrock-hosted models with built-in and custom metrics. Clarify FMEval provides more customizable evaluation with support for models hosted anywhere.

> **"Ground Truth is only for image labeling."** -- Ground Truth Plus generates demonstration data (prompt-response pairs for SFT) and preference data (ranked outputs for RLHF). It also supports red teaming for foundation model safety evaluation.

---

## Domain 4: Optimize Generative AI Solutions (12%)

### Task 4.1: Optimize Cost

> **"Intelligent Prompt Routing and Model Distillation are the same."** -- Prompt Routing dynamically routes prompts to different models based on complexity at inference time (up to 30% savings). Distillation creates a NEW smaller model from a larger teacher model offline (up to 75% cheaper, up to 500% faster).

> **"Prompt caching reduces both input and output token costs."** -- Prompt caching reduces input token costs (up to 90%) and latency (up to 85%). Output token costs are unaffected.

> **"Batch inference works with any Bedrock model configuration."** -- Batch inference is NOT supported for provisioned models. It provides approximately 50% cost reduction vs on-demand for supported configurations.

> **"SageMaker Managed Spot Training is risk-free."** -- You MUST implement checkpointing for training jobs longer than 1 hour. Without checkpointing, if the Spot Instance is interrupted, training restarts from the beginning.

> **"AWS Inferentia and Trainium are the same thing."** -- Inferentia is for inference (cost-effective model serving). Trainium is for training (up to 50% savings vs GPU). They are different chip families for different workloads.

> **"Cost Anomaly Detection alerts in real-time."** -- Cost Anomaly Detection runs approximately 3x daily, not in real-time. There is inherent lag between spend and detection.

> **"S3 Vectors is a compromise choice for Knowledge Base vector stores."** -- S3 Vectors is the LOWEST COST vector store option with subsecond query performance. It is ideal for cost-sensitive, large-scale Knowledge Bases. The trade-off is no hybrid search and no binary vector support.

> **"OpenSearch Serverless is cheap for small workloads."** -- OpenSearch Serverless has a minimum of 2 OCUs (OpenSearch Compute Units), which means a baseline cost even for minimal usage. For cost-sensitive small workloads, consider S3 Vectors or Aurora PostgreSQL.

### Task 4.2: Optimize Performance

> **"Lower embedding dimensions always hurt retrieval quality."** -- Lower dimensions (e.g., Titan V2 at 256) reduce storage and speed up search with only marginal accuracy loss. This is a valid optimization for cost and latency when perfect accuracy is not required.

> **"Disk-based vector search in OpenSearch is unsuitable for production."** -- Disk-based vector search (OpenSearch 2.17+) provides a 97% reduction in memory requirements at the cost of higher latency (low hundreds of milliseconds). This is suitable for large-scale production where cost matters more than sub-millisecond latency.

> **"HNSW parameters do not affect ingestion performance."** -- Higher `ef_construction` values improve search quality but significantly slow down ingestion. Higher `m` values increase memory usage and slow both ingestion and search. Tune these based on your quality vs. performance trade-off.

> **"You should always use the highest-capability model."** -- Use the smallest model that meets quality requirements. Route simple tasks to Nova Micro or Haiku, complex tasks to Sonnet or Opus. Intelligent Prompt Routing automates this.

> **"Provisioned Throughput is the only way to handle traffic spikes."** -- Cross-Region Inference (geographic or global) is a simpler, cheaper way to handle capacity constraints. Provisioned Throughput guarantees dedicated capacity but at a commitment cost.

### Task 4.3: Monitor and Troubleshoot

> **"Agent metrics are in the AWS/Bedrock namespace."** -- Agent metrics use the `AWS/Bedrock/Agents` namespace, NOT `AWS/Bedrock`. Guardrails metrics use `AWS/Bedrock/Guardrails`. This namespace distinction is frequently tested.

> **"InvocationThrottles count as Invocations."** -- Throttled invocations do NOT count as Invocations and do NOT count as errors. They are a separate metric. This matters for calculating success rates and error rates.

> **"Average latency is the right metric for SLAs."** -- Use p99 or p95 latency (percentile statistics) for latency SLAs, not average. Average hides tail latency issues.

> **"SageMaker DiskUtilization above 75% is just a warning."** -- Keep disk utilization below 75% to ensure data capture continues on SageMaker endpoints. Above this threshold, data capture may silently stop.

> **"Custom CloudWatch metrics are free."** -- Custom metrics cost $0.30/metric/month. Each unique combination of namespace + metric name + dimensions creates a separate metric. High-cardinality dimensions (e.g., per-user metrics) can become expensive.

> **"The agent service role does not need CloudWatch permissions."** -- The agent IAM service role must include `cloudwatch:PutMetricData` with a condition restricting to the `AWS/Bedrock/Agents` namespace, or agent metrics will not appear.

> **"Feature Attribution Drift uses simple thresholds."** -- SageMaker Model Monitor uses NDCG (Normalized Discounted Cumulative Gain) to compare SHAP-based feature importance rankings. An NDCG score below 0.90 triggers an alert.

---

## Domain 5: Evaluate Generative AI Solutions (11%)

### Task 5.1: Design and Implement Evaluation Systems

> **"LLM-as-a-Judge and human evaluation produce the same quality."** -- LLM-as-a-Judge provides human-LIKE quality at lower cost and faster speed, but it is not a perfect substitute for human evaluation. Use human evaluation for subjective quality (brand voice, cultural sensitivity) and LLM-as-a-Judge for scalable quality assessment.

> **"Bedrock Model Evaluation only works with Bedrock models."** -- Bedrock Evaluation supports "bring your own inference responses" for evaluating models hosted anywhere, not just on Bedrock.

> **"RAG evaluation is separate from model evaluation."** -- Bedrock Evaluation includes RAG evaluation capabilities: evaluate both retrieval quality (are the right chunks retrieved?) and generation quality (is the response accurate given the chunks?).

> **"Automatic evaluation is always sufficient."** -- Automatic evaluation uses predefined metrics (accuracy, robustness, toxicity). For subjective qualities like helpfulness, tone, brand voice, and cultural sensitivity, you need human evaluation or LLM-as-a-Judge with custom criteria.

### Task 5.2: Troubleshoot Generative AI Solutions

> **"A model returning 'I don't know' is always a model problem."** -- This is often a RAG retrieval problem, not a model problem. Check: Are the right chunks being retrieved? Is the chunking strategy appropriate? Is the embedding model matching? Are metadata filters too restrictive?

> **"High latency always means the model is slow."** -- Distinguish between model latency and overhead latency. On SageMaker, `ModelLatency` is the container processing time while `OverheadLatency` is SageMaker infrastructure time. On Bedrock, check `InvocationThrottles` as throttling causes retries that look like high latency.

> **"stopReason 'max_tokens' means the response is complete."** -- A stopReason of `max_tokens` means the response was TRUNCATED because it hit the maximum token limit. The response is incomplete. Increase `maxTokens` or use more concise prompts.

> **"Guardrail trace data appears automatically."** -- You must set `trace: "enabled"` in the `guardrailConfig` to get guardrail assessment details in the response. Without this, you only know the guardrail intervened but not why.

> **"Agent trace data shows the final answer only."** -- Setting `enableTrace: true` on `InvokeAgent` returns the full reasoning chain: PreProcessingTrace (input validation), OrchestrationTrace (rationale + actions + observations), PostProcessingTrace (formatting), FailureTrace (errors), and GuardrailTrace.

> **"Bedrock Data Automation and Knowledge Bases are unrelated."** -- Bedrock Data Automation (BDA) can be used as a parser for Knowledge Bases to convert unstructured multimodal content (audio, video, complex documents) into RAG-ready chunks.

---

## Cross-Cutting Gotchas

These gotchas span multiple domains and are high-probability exam topics.

### Quota and Throttling

> **"Quota is measured only in Requests Per Minute."** -- Bedrock quotas are measured in both Tokens Per Minute (TPM) AND Requests Per Minute (RPM). You can be throttled on either dimension.

> **"Output token burndown rate is 1:1."** -- The burndown rate is 5:1 for Claude 3.7+ and other recent models. One output token consumes 5x more quota than one input token. This is a quota concern, not a billing concern.

> **"Request quota increases through the console in any Region."** -- For Cross-Region Inference, request quota increases through Service Quotas console in the SOURCE Region.

> **"Setting max_tokens high has no downside."** -- `max_tokens` is reserved from your quota at request START. If your quota is 100K TPM and you set max_tokens to 50K, you can only run 2 concurrent requests regardless of how many tokens are actually generated.

### Encryption and Data Protection

> **"All Bedrock resources use customer managed keys by default."** -- Bedrock resources use AWS owned keys by default. You must explicitly specify a customer managed KMS key during resource creation for full control over key policies, rotation, and auditing.

> **"KMS keys work across Regions by default."** -- KMS keys are REGIONAL. A key in us-east-1 cannot be used in eu-west-1 unless you use multi-region keys.

> **"S3 Bucket Keys are a separate encryption mechanism."** -- S3 Bucket Keys reduce KMS API calls (up to 99% cost reduction) by generating a bucket-level key. They work WITH SSE-KMS, not instead of it.

### Networking

> **"VPC endpoints are optional for Bedrock."** -- VPC endpoints (AWS PrivateLink) are required for private connectivity to Bedrock from within a VPC. Without them, traffic goes over the internet (even within AWS). Model customization, batch inference, and Knowledge Bases support VPC-protected operation.

### CloudTrail

> **"CloudTrail captures Bedrock model input/output by default."** -- CloudTrail captures management events (API calls) by default. Data events (including model invocation content) must be explicitly enabled and configured. Use model invocation logging for input/output capture, not CloudTrail.

### Identity and Access

> **"Permission sets in IAM Identity Center are IAM policies."** -- Permission sets are TEMPLATES that create IAM roles in each assigned account. When a user signs in via the access portal, they assume one of these roles. Session duration is configurable (1-12 hours).

> **"IAM Access Analyzer findings are all free."** -- External access findings are free. Unused access and internal access findings are charged per IAM role/user analyzed per month.

---

## Quick-Reference: Commonly Confused Service Pairs

| Scenario | Use This | NOT This |
|---|---|---|
| Fully managed serverless inference | Amazon Bedrock | SageMaker Endpoints |
| Full infrastructure control for models | SageMaker Endpoints | Amazon Bedrock |
| Autonomous AI reasoning | Bedrock Agents | Prompt Flows |
| Deterministic AI pipeline | Prompt Flows | Bedrock Agents |
| General workflow orchestration | Step Functions | Prompt Flows |
| Human-in-the-loop for agents | Return of Control | Step Functions |
| Framework-agnostic agent hosting | AgentCore Runtime | Bedrock Agents |
| Convert APIs to agent tools | AgentCore Gateway | Manual MCP server |
| Open-source agent SDK | Strands Agents | Bedrock Agents SDK |
| Multi-agent (fully managed) | Bedrock Multi-Agent Collaboration | Agent Squad |
| Multi-agent (full control) | Agent Squad / Strands Graphs | Bedrock Multi-Agent Collaboration |
| PII in S3 (at rest) | Amazon Macie | Amazon Comprehend |
| PII in text (in transit) | Bedrock Guardrails / Comprehend | Amazon Macie |
| Data labeling for RLHF | Ground Truth Plus | SageMaker Processing |
| Bias in training data | SageMaker Clarify (pre-training) | Bedrock Guardrails |
| Model governance documentation | Model Cards | Model Registry |
| Model version tracking | Model Registry | Model Cards |
| Credential rotation | Secrets Manager | Parameter Store |
| Configuration values | Parameter Store | Secrets Manager |
| Large-scale ETL | AWS Glue | Data Wrangler |
| Visual data preparation for ML | Data Wrangler | AWS Glue |

---

## Quick-Reference: Key Numbers

| Item | Value |
|---|---|
| Output token burndown rate (quota) | 5:1 |
| Max results per KB query | 100 |
| Default results per KB query | 5 |
| Max filter groups (KB) | 5 |
| Max filters per group (KB) | 5 |
| Titan V2 dimension options | 256, 512, 1024 |
| Titan V1 fixed dimensions | 1536 |
| Cohere Embed max input tokens | 512 |
| Titan Embed max input tokens | 8192 |
| Prompt variants per prompt | 3 |
| DoWhile max iterations (default) | 10 |
| Flow Input nodes per flow | Exactly 1 |
| AgentCore Runtime async max duration | 8 hours |
| AgentCore payload max size | 100 MB |
| MCP server port (AgentCore) | 8000 |
| KMS max direct encryption | 4 KB |
| Cognito ID/access token lifetime | 5 min - 1 day |
| Cognito refresh token lifetime | 1 hour - 3650 days |
| WAF rate-based minimum threshold | 100 requests / 5 min |
| WAF rate-based mitigation lag | 30-50 seconds |
| Secrets Manager max secret size | 65,536 bytes |
| SageMaker endpoint disk utilization ceiling | 75% |
| NDCG drift alert threshold | 0.90 |
| Prompt cache TTL (most models) | 5 minutes |
| Step Functions Express max duration | 5 minutes |
| Step Functions Standard max duration | 1 year |
| Batch inference cost reduction vs on-demand | ~50% |
| Prompt caching input token cost reduction | Up to 90% |
| Prompt caching latency reduction | Up to 85% |
| Model Distillation cost reduction | Up to 75% |
| Intelligent Prompt Routing cost reduction | Up to 30% |
| Global CRIS cost savings | ~10% |
