# AIP-C01 Exam Concepts: Ranked by Importance

Comprehensive concept inventory for the AWS Certified Generative AI Developer - Professional
(AIP-C01) exam. Concepts are ranked by importance using a weighted synthesis of: official exam
domain weightings, frequency of appearance across all five domain study guides, depth of coverage
in the Well-Architected Generative AI Lens, and cross-domain relevance.

**Ranking scale:**
- **CRITICAL** -- appears across multiple domains, heavily weighted, almost guaranteed on the exam.
- **HIGH** -- core to a single high-weight domain or spans two or more domains.
- **MEDIUM** -- important within its domain but narrower in scope.
- **LOW** -- supporting concept; tested indirectly or at the margins.

## Tier 1: CRITICAL Concepts

These concepts cut across multiple domains and collectively account for the vast majority of
exam questions. Master every detail.

### 1. Retrieval-Augmented Generation (RAG) Pipeline (Domains 1, 3, 4, 5)

The end-to-end pattern for grounding FM responses with external knowledge. The single most
cross-cutting concept on the exam.

**What to know:**
- Full pipeline: source data, parsing, chunking, embedding, vector store, retrieval,
  augmented prompt construction, FM invocation, post-processing.
- Bedrock Knowledge Bases as the managed RAG service (ingestion, chunking, embedding,
  indexing, retrieval, augmented generation).
- `RetrieveAndGenerate` API (end-to-end RAG) vs. `Retrieve` API (retrieval only).
- Citations and source attribution in RAG responses.
- Structured data RAG via text-to-SQL with Amazon Redshift.
- RAG evaluation metrics: context relevance, context coverage, faithfulness, citation
  precision, citation coverage.
- Troubleshooting: stale data, embedding drift, chunking misalignment, low retrieval
  relevance, context window overflow.

### 2. Amazon Bedrock Guardrails (Domains 1, 3, 4, 5)

The primary content safety, PII protection, and hallucination detection mechanism. Referenced
in every domain.

**What to know:**
- Seven policy types: content filters (6 categories), denied topics, word filters, sensitive
  information filters (PII), contextual grounding checks, automated reasoning checks, prompt
  attack detection (jailbreaks, injection, leakage).
- Content filter strength levels (NONE/LOW/MEDIUM/HIGH) and confidence classification.
- Classic vs. Standard tier (Standard: 30% better recall, 60+ languages, code element
  protection, prompt leakage detection).
- Input vs. output evaluation: input blocked prevents FM invocation (no inference charge);
  output blocked still incurs inference charge.
- Contextual grounding checks (grounding score + relevance score, OUTPUT-ONLY).
- Automated reasoning checks (formal mathematical logic, up to 99% accuracy, OUTPUT-ONLY).
- Prompt attack detection is INPUT-ONLY.
- The `ApplyGuardrail` API for decoupled guardrail evaluation without FM invocation.
- Input tagging with XML tags for InvokeModel API; `guardContent` blocks for Converse API.
- IAM enforcement via `bedrock:GuardrailIdentifier` condition key.
- Guardrail versioning (DRAFT, immutable numbered versions).
- PII detection modes: BLOCK vs. ANONYMIZE (replaces with type tags like `{NAME}`).

### 3. Amazon Bedrock APIs and Invocation Patterns (Domains 1, 2, 4, 5)

How applications interact with Foundation Models. Tested from multiple angles.

**What to know:**
- Converse API (model-agnostic, multi-turn, recommended) vs. InvokeModel API (model-specific
  JSON payloads).
- Streaming APIs: InvokeModelWithResponseStream, ConverseStream. Event types: messageStart,
  contentBlockStart, contentBlockDelta, contentBlockStop, messageStop, metadata.
- Synchronous vs. asynchronous (SQS + Lambda) vs. streaming invocation patterns.
- StartAsyncInvoke for long-running tasks (video generation, large documents).
- Bedrock Responses API (stateful, OpenAI-compatible) and Chat Completions API.
- Error handling: 429 ThrottlingException (exponential backoff with jitter), 503
  ServiceUnavailable (retry + failover), 400 ValidationError (format/token check).
- Retry configuration: AWS SDK `max_attempts`, `retry_mode` (standard/adaptive).
- Token metrics: InputTokenCount, OutputTokenCount, InvocationLatency, TimeToFirstToken,
  EstimatedTPMQuotaUsage.
- Burndown rate: 5x for Claude 3.7+ output tokens (affects quota, not billing).
- `max_tokens` parameter: deducted from quota at request start, not end.

### 4. Prompt Engineering and Management (Domains 1, 3, 4, 5)

Covers prompt design, governance, versioning, and optimization.

**What to know:**
- Prompt components: instruction, context, demonstration examples (few-shot), input text.
- System prompts for role, tone, constraints, output format.
- Techniques: zero-shot, few-shot, chain-of-thought, structured I/O, critique prompting,
  self-consistency, prompt compression, context pruning.
- Amazon Bedrock Prompt Management: create, version, test, deploy parameterized templates;
  approval workflows; prompt variants; IAM-controlled access.
- Amazon Bedrock Prompt Flows: visual no-code builder; sequential chains, conditional
  branching, reusable components, Lambda pre/post-processing nodes; immutable versions
  deployed via aliases.
- Amazon Bedrock Prompt Optimization: managed feature that auto-optimizes prompts for a
  target model.
- Prompt governance: S3 for template repos, CloudTrail for usage audit, CloudWatch Logs for
  request/response logging.
- Prompt testing: Lambda for output validation, Step Functions for edge case testing,
  CloudWatch alarms for regression detection, A/B testing.

### 5. Vector Stores and Embeddings (Domains 1, 4, 5)

The foundation of semantic search for RAG.

**What to know:**
- What vector databases store (dense numerical embeddings encoding semantic meaning).
- AWS options: OpenSearch Service/Serverless, Aurora PostgreSQL with pgvector, Neptune
  Analytics, Bedrock Knowledge Bases (managed), S3 Vectors, Pinecone, Redis Enterprise Cloud,
  MongoDB Atlas.
- Embedding models: Amazon Titan Text Embeddings V2 (256/512/1024 dimensions, binary
  embeddings), Cohere Embed (multilingual), Amazon Nova Multimodal Embeddings (text, image,
  video, audio).
- Chunking strategies: fixed-size, default Bedrock (~300 tokens), hierarchical (parent/child),
  semantic, no chunking. Hierarchical = best for precision + context.
- Search types: semantic, keyword (BM25), hybrid (semantic + keyword via Reciprocal Rank
  Fusion), reranking (post-retrieval LLM scoring).
- OpenSearch performance: HNSW algorithm, IVF, sharding, quantization (product/scalar),
  disk-based vector search, GPU-accelerated indexing, auto-optimize.
- Aurora pgvector: HNSW index (preferred for production), IVFFlat, iterative index scans.
- Metadata frameworks: S3 object metadata, custom attributes, tagging systems. Metadata
  filtering in Bedrock Knowledge Bases via filter expressions.
- Data maintenance: incremental sync, real-time change detection (DynamoDB Streams, EventBridge),
  scheduled refresh, TTL-based expiry.

### 6. Agentic AI Systems (Domains 2, 3, 4, 5)

Autonomous FM-powered systems that reason, plan, and use tools. The second-highest weight
domain is heavily focused on agents.

**What to know:**
- ReAct pattern (Reason + Act): perceive, reason, act, observe, repeat.
- Amazon Bedrock Agents: managed ReAct-based agents; action groups (Lambda), knowledge bases,
  code interpreter, memory; multi-agent (supervisor + collaborator).
- Strands Agents SDK: open-source, model-first, provider-agnostic; core = model + tools +
  system prompt; multi-agent patterns (agents-as-tools, swarms, graphs, meta agents);
  OpenTelemetry instrumentation.
- AWS Agent Squad: multi-agent coordination and fleet management.
- Amazon Bedrock AgentCore: serverless agent hosting (microVM isolation), modular services
  (Runtime, Memory, Gateway, Identity, Code Interpreter, Browser, Observability, Evaluations,
  Policy); supports any framework; up to 8-hour workloads, WebSocket streaming.
- Model Context Protocol (MCP): open standard for agent-tool interaction; Lambda for stateless
  MCP servers, ECS for complex/stateful MCP servers; MCP client libraries; AgentCore Gateway
  converts APIs to MCP-compatible tools.
- Agent safeguards: Step Functions stopping conditions, Lambda timeouts, IAM resource
  boundaries, circuit breakers, Bedrock Guardrails on agents.
- Human-in-the-loop: user confirmation, return of control (ROC), Step Functions task tokens,
  Amazon A2I, SageMaker Ground Truth.
- Agent tracing: PreProcessingTrace, OrchestrationTrace, PostProcessingTrace, FailureTrace,
  GuardrailTrace, RoutingClassifierTrace, CustomOrchestrationTrace. Enable via
  `enableTrace: TRUE`.
- Agent evaluation: AgentCore Evaluations (online + on-demand), goal attainment, tool accuracy.

### 7. Foundation Model Selection, Routing, and Lifecycle (Domains 1, 2, 4)

Choosing, routing to, and managing FMs across their lifecycle.

**What to know:**
- Four-dimension evaluation: task performance, architectural characteristics, operational
  considerations, responsible AI attributes.
- Dynamic model selection: AWS AppConfig for model ID storage; Lambda reads at runtime;
  API Gateway routes to different backends. No code changes to swap models.
- Intelligent Prompt Routing: routes within a model family (Haiku/Sonnet, 8B/70B, Lite/Pro)
  based on predicted per-prompt quality; up to 30% cost savings; default vs. configured routers.
- Cross-Region Inference: geographic profiles (data residency) vs. global profiles (max
  throughput, ~10% savings); no additional routing cost; CloudTrail logs in source region only.
- FM customization techniques: fine-tuning (SFT), continued pre-training, LoRA (parameter-
  efficient), full fine-tuning, DPO/PPO alignment, knowledge distillation (Bedrock Model
  Distillation: up to 500% faster, 75% cheaper, <2% accuracy loss).
- SageMaker Model Registry: versioning, metadata, approval workflows, CI/CD integration,
  rollback.
- Deployment modes: Bedrock on-demand (pay-per-token), Bedrock Provisioned Throughput (Model
  Units, hourly), SageMaker endpoints (full control, GPU selection), Lambda + Bedrock
  (serverless, event-driven).
- On-demand service tiers: Priority, Standard, Flex, Reserved.
- Resilience patterns: circuit breaker, graceful degradation, fallback model, cross-region
  inference.

### 8. Monitoring, Observability, and Logging (Domains 4, 5, 3)

Understanding the full observability stack for GenAI applications.

**What to know:**
- CloudWatch runtime metrics (AWS/Bedrock namespace): Invocations, InvocationLatency,
  InvocationClientErrors, InvocationServerErrors, InvocationThrottles, InputTokenCount,
  OutputTokenCount, TimeToFirstToken, EstimatedTPMQuotaUsage.
- Agent metrics (AWS/Bedrock/Agents namespace, NOT AWS/Bedrock).
- Bedrock Model Invocation Logging: disabled by default; sends to CloudWatch Logs and/or S3;
  captures full request/response; large data (>100 KB) only to S3.
- CloudTrail: management events logged by default; data events (InvokeModel, InvokeAgent,
  Retrieve) must be explicitly enabled.
- X-Ray / Application Signals: distributed tracing; segments, subsegments, traces; annotations
  (indexed, searchable) vs. metadata (not indexed); adaptive sampling.
- OpenTelemetry (ADOT SDK): recommended over X-Ray SDK; AgentCore emits OTEL-compatible
  telemetry; GenAI semantic conventions (gen_ai.request.model, gen_ai.usage.input_tokens).
- CloudWatch Logs Insights: query prompt/response patterns, filter by model ID.
- CloudWatch Anomaly Detection: ML-based expected value bands for metrics.
- Cost Anomaly Detection: ML-based, runs ~3 times daily (not real-time).
- Amazon Managed Grafana: cross-account/cross-region dashboards; requires IAM Identity Center.
- Pre-configured dashboards: Model Invocations Dashboard, AgentCore Agents Dashboard.

### 9. Security, IAM, and Network Isolation (Domains 3, 2)

Securing FM deployments end-to-end.

**What to know:**
- Bedrock does NOT support resource-based policies. All access control is identity-based.
- Key IAM actions: bedrock:InvokeModel, bedrock:InvokeModelWithResponseStream,
  bedrock:ApplyGuardrail, bedrock:CreateGuardrail.
- Condition keys: `bedrock:GuardrailIdentifier` (enforce mandatory guardrails).
- VPC endpoints (PrivateLink) for Bedrock: four endpoint types (control plane, runtime,
  agents build, agents runtime). Private DNS enables SDK code without modification.
- VPC endpoint policies for restricting access through the endpoint.
- S3 VPC gateway endpoint required for model customization in VPCs without internet access.
- Amazon Cognito for customer-facing app authentication.
- IAM Identity Center for enterprise SSO federation (SAML 2.0, OIDC).
- Least privilege: scope IAM policies to specific model ARNs and actions.
- SCPs for organizational guardrails: deny access to specific models, require guardrails,
  restrict regions.
- KMS encryption: AWS-owned keys by default; customer managed keys optional for custom
  models, agents, knowledge bases, guardrails. Key policy needs kms:CreateGrant,
  kms:DescribeKey, kms:GenerateDataKey, kms:Decrypt.
- Bedrock data privacy: does NOT use customer data to train base FMs; does NOT share data
  with providers; fine-tuning creates private copy; TLS 1.2 in transit; opt-in model
  improvement only.

### 10. Cost Optimization for GenAI (Domains 4, 1, 2)

Token efficiency, caching, model selection, and pricing mechanics.

**What to know:**
- Token efficiency: track via CloudWatch, optimize `max_tokens`, prompt compression, context
  pruning, response size controls.
- Bedrock Prompt Caching: caches model internal computation state for prompt prefixes;
  up to 90% input cost reduction, 85% latency reduction; 5-minute TTL; cache writes cost
  more, cache reads cost less; mark cache checkpoints in prompts.
- Semantic Caching (application-level): store full request-response pairs in ElastiCache
  for Valkey; vector similarity search for matching queries; bypasses LLM entirely on hit.
  Deterministic request hashing for exact-match caching.
- Edge caching with CloudFront: for static/deterministic API responses only.
- Intelligent Prompt Routing: up to 30% cost savings by routing to cheaper models.
- Model Distillation: up to 500% faster, 75% cheaper; teacher-to-student transfer.
- Batch inference: up to 50% less than on-demand; JSONL input in S3; 24-hour window.
- On-demand service tiers: Flex (cheapest, higher throttling), Standard, Priority (best
  latency), Reserved (committed capacity).
- Provisioned Throughput: Model Units, commitment terms (no-commitment, 1-month, 6-month).
- SageMaker cost tools: Inference Recommender, Savings Plans, multi-model endpoints,
  serverless inference.

## Tier 2: HIGH Importance Concepts

Core to individual domains and tested directly, but narrower in scope than Tier 1.

### 11. LLM-as-a-Judge Evaluation (Domains 5, 3, 1)

**What to know:**
- A judge model scores generator model outputs on built-in metrics (11 total): correctness,
  completeness, faithfulness, helpfulness, coherence, relevance, following instructions,
  professional style/tone, harmfulness, stereotyping, refusal.
- Score range: 0 to 1.
- Custom metrics: write judge prompts with configurable rating scales.
- RAG evaluation: retrieve-only (context relevance, context coverage) and retrieve-and-
  generate (all retrieval metrics + 10 generation metrics).
- Bring Your Own Inference (BYOI): evaluate any model hosted anywhere.
- Max 1,000 prompts per evaluation job.
- Up to 98% cost savings vs. full human evaluation.
- Supported evaluator models: Nova Pro, Claude (3.5 Sonnet, 3.7 Sonnet, 3 Haiku, 3.5 Haiku),
  Llama 3.1 70B, Mistral Large.

### 12. Data Validation and Processing Pipelines (Domain 1)

**What to know:**
- AWS Glue Data Quality (DQDL): rule-based validation (Completeness, Uniqueness, Referential
  Integrity, RowCount, ColumnValues); ML anomaly detection; runs within Glue ETL jobs.
- SageMaker Data Wrangler: visual data prep, profiling, transformation.
- Multimodal processing: Transcribe (audio to text), Rekognition (images), Bedrock Data
  Automation (documents, images, audio, video to structured output), Comprehend (entity
  extraction, PII detection).
- Input formatting: Converse API (model-agnostic, recommended), InvokeModel API
  (model-specific JSON), SageMaker endpoints (container-specific format).
- Conversation formatting: messages array with alternating user/assistant roles; store
  history in DynamoDB; retrieve and prepend on each turn.

### 13. PII Detection and Privacy Controls (Domains 3, 1)

**What to know:**
- Amazon Comprehend: DetectPiiEntities (real-time, 22+ PII types, character offsets),
  ContainsPiiEntities (labels only), async batch redaction.
- Amazon Macie: PII discovery in S3 at rest; ML + pattern matching; managed and custom data
  identifiers; findings integrate with EventBridge and Security Hub.
- Bedrock Guardrails sensitive info filters: ML-based PII detection; BLOCK vs. ANONYMIZE
  modes; 30+ PII types; custom regex; works on input and output independently.
- Data masking: static (irreversible, for non-prod) vs. dynamic (query-time, Lake Formation,
  Guardrails ANONYMIZE).
- Anonymization strategies: pseudonymization, tokenization, generalization, k-anonymity.
- S3 Lifecycle configurations for GDPR data retention/erasure compliance.

### 14. Enterprise Integration Architectures (Domain 2)

**What to know:**
- API-based integration with legacy systems via API Gateway and Lambda.
- Event-driven patterns: EventBridge, SQS (decoupling, DLQ), SNS (fan-out), DynamoDB
  Streams, Kinesis.
- Data sync: AppFlow (SaaS to AWS), DataSync (on-premises to S3), Glue ETL.
- Amazon Q Business: enterprise knowledge assistant; 40+ pre-built connectors (S3, SharePoint,
  Confluence, Salesforce, Jira); IAM Identity Center SSO; topic controls; Q Apps.
- Amazon Q Developer: AI coding assistant in IDEs; code generation, explanation, test
  generation, bug finding, security scanning, code transformation.
- GenAI Gateway pattern: centralized API Gateway + Lambda abstraction layer for rate limiting,
  cost allocation, observability, routing, security enforcement.
- Cross-environment: AWS Outposts (on-premises data residency), AWS Wavelength (5G edge,
  ultra-low latency), Direct Connect, Site-to-Site VPN, PrivateLink.

### 15. CI/CD for GenAI Applications (Domains 2, 5)

**What to know:**
- GenAI CI/CD extends traditional pipelines with prompt regression tests, FM evaluation
  quality gates, adversarial testing, and golden dataset validation.
- Pipeline stages: source, build, security scan, GenAI-specific tests, deploy (canary/
  blue-green), approval gate, production deploy with automated rollback.
- AWS services: CodePipeline (orchestration), CodeBuild (build/test/scan), CodeDeploy
  (traffic shifting), CDK/CloudFormation (IaC).
- Versioned artifacts: code version (Git), prompt version, model configuration, evaluation
  dataset version. Full snapshot for reproducibility.
- Deployment strategies: A/B testing, canary releases, shadow deployments.
- Quality gates: LLM-as-a-Judge evaluation; fail build if scores drop below threshold.

### 16. Responsible AI Principles (Domain 3)

**What to know:**
- Eight AWS Responsible AI dimensions: fairness, explainability, privacy and security, safety,
  controllability, veracity and robustness, governance, transparency.
- SageMaker Model Cards: document model purpose, intended uses, risk rating (unknown/low/
  medium/high mapping to EU AI Act), evaluation details, training details; immutable
  versioning; export to PDF.
- AWS AI Service Cards: AWS-published transparency docs for managed services; read-only.
- Model Cards vs. AI Service Cards vs. Guardrails: documentation vs. transparency vs.
  runtime enforcement.
- Extended thinking / chain-of-thought (Claude): outputs internal `thinking` blocks before
  final answer; `budget_tokens` configuration; transparency mechanism.
- Bedrock Knowledge Bases citations for source attribution.
- Agent tracing for reasoning transparency.
- SageMaker Clarify: pre-training bias metrics (CI, DPL, KL, JS) are model-agnostic;
  post-training metrics require predictions; SHAP for feature attribution.
- Bedrock Model Evaluation for bias: BOLD dataset (recommended for bias in open-ended
  generation); LLM-as-a-Judge responsible AI metrics (harmfulness, answer refusal).
- Amazon A2I for human-in-the-loop review workflows.

### 17. Hallucination Detection and Mitigation (Domains 3, 5)

**What to know:**
- Contextual grounding checks in Guardrails: grounding score (factual accuracy vs. source)
  + relevance score (relevant to query); thresholds 0 to 0.99; requires grounding source,
  query, and content to guard.
- Automated reasoning checks: formal mathematical logic; deterministic, provable verification;
  up to 99% accuracy; limited regional availability.
- RAG grounding: Knowledge Bases inject retrieved context; FM generates grounded response.
- LLM-as-a-Judge faithfulness metric.
- Golden dataset comparison in CI/CD.
- JSON Schema structured outputs to constrain response format.
- Prompt engineering: "only use information from the provided context" instructions.

### 18. Well-Architected Generative AI Lens (Domain 1, cross-cutting)

**What to know:**
- Six lifecycle phases: scoping, model selection, customization, integration, deployment,
  continuous improvement.
- Six pillars applied to GenAI: Operational Excellence, Security, Reliability, Performance
  Efficiency, Cost Optimization, Sustainability.
- Six design principles: controlled autonomy, comprehensive observability, resource
  efficiency, distributed resilience, standardized resource management, secure interaction
  boundaries.
- Key best practice IDs: GENOPS03-BP01 (prompt template management), GENSEC04-BP01
  (secure prompt catalog), GENSEC05-BP01 (least privilege for agents), GENCOST03-BP03
  (prompt caching), GENCOST05-BP01 (agent stopping conditions).
- Use the AWS WA Tool to run assessments with the GenAI Lens custom lens.

### 19. Streaming and Real-Time Interactions (Domains 2, 4)

**What to know:**
- ConverseStream / InvokeModelWithResponseStream for token-by-token delivery.
- WebSocket API Gateway for bidirectional real-time connections.
- Server-Sent Events (SSE) for unidirectional streaming over HTTP.
- Chunked transfer encoding via REST API Gateway.
- AWS Amplify AI Kit: pre-built `<AIConversation>` component; handles real-time subscriptions,
  multi-turn history, UI state management.
- Streaming does NOT change cost; same tokens billed regardless.
- Streaming improves perceived latency (TTFT metric).
- Latency-optimized inference: `performanceConfig.latency = "optimized"`; uses Trainium2;
  falls back to standard latency if quota exceeded.

### 20. Governance, Compliance, and Audit (Domain 3)

**What to know:**
- CloudTrail for API-level audit (management events by default; data events must be enabled).
- CloudWatch Logs for request/response logging.
- Glue Data Catalog for data lineage and source metadata.
- SageMaker Model Cards for regulatory documentation.
- SCPs for organizational boundaries.
- AWS Service Catalog for approved GenAI product portfolios.
- Bedrock compliance: GDPR, HIPAA eligible, SOC 1/2/3, ISO 27001, FedRAMP High, ISO/IEC
  42001:2023 (first major cloud provider for AI management certification).
- Lake Formation for granular data access (column/row/cell-level security).

## Tier 3: MEDIUM Importance Concepts

Important within their domain but narrower in scope. Expect 1-3 questions on each.

### 21. Query Handling and Retrieval Optimization (Domains 1, 4)

- Query expansion (FM generates synonyms/alternate phrasings).
- Query decomposition (split complex questions into atomic sub-queries).
- Query transformation (multi-step refinement via Step Functions).
- HyDE (Hypothetical Document Embedding): generate hypothetical answer, embed it, search
  with answer embedding.
- Hybrid search in Bedrock Knowledge Bases: requires filterable text field in vector store;
  supported for RDS, OpenSearch Serverless, MongoDB.
- Reranking: VectorSearchBedrockRerankingConfiguration; numberOfRerankedResults (1-100).
- Implicit metadata filtering: Bedrock auto-generates filters from query + metadata schema.

### 22. Model Deployment Mechanics (Domain 2)

- LLM-specific challenges: GPU VRAM requirements, sequential token generation, token
  processing capacity (TPM not RPM), model loading strategies (lazy loading, weight streaming,
  model sharding), container optimization (TGI, vLLM, Triton).
- Model cascading: simplest/cheapest model first; escalate if quality insufficient.
- Bedrock Provisioned Throughput: Model Units, commitment options, provisioned model ARN.
- SageMaker endpoint types: real-time (25 MB, 60s), serverless (4 MB, 60s, scale-to-zero),
  asynchronous (1 GB, 1 hour, scale-to-zero), batch transform (no limit).
- SageMaker auto-scaling: target-tracking (SageMakerVariantInvocationsPerInstance), step
  scaling, scheduled scaling, scale-to-zero (HasBacklogWithoutCapacity alarm).

### 23. Defense-in-Depth Safety Architecture (Domain 3)

- Layer 1: Pre-processing (Comprehend Toxicity Detection, Prompt Safety Classifier, Lambda
  input sanitization, WAF).
- Layer 2: Model-level (Bedrock Guardrails, all seven filter types).
- Layer 3: Post-processing (Lambda validation, Comprehend output checks, business logic).
- Layer 4: API-level (API Gateway rate limiting, IAM enforcement, CloudTrail, CloudWatch).
- ApplyGuardrail API enables guardrail checks at any pipeline point.

### 24. Token Efficiency and Quota Management (Domain 4)

- Token metrics in CloudWatch: InputTokenCount, OutputTokenCount, CacheReadInputTokens,
  CacheWriteInputTokens, EstimatedTPMQuotaUsage.
- Burndown rate: 5x for Claude 3.7+ output tokens (quota impact, not billing).
- `max_tokens` deducted at request start; setting too high reduces concurrency.
- Quota types: RPM, TPM, TPD (TPD = TPM x 1,440).
- Capacity tiers: Flex (cheapest, highest throttling), Standard, Priority (best latency).
- Lambda reserved concurrency as rate-limiting mechanism for downstream FM calls.

### 25. SageMaker Clarify and Model Monitor (Domains 3, 4)

- Clarify pre-training bias metrics: CI, DPL, KL, JS, LP, TVD, KS, CDD. Model-agnostic.
- Clarify post-training bias metrics: DPPL, DI, DCAcc, DCR. Require predictions.
- SHAP (SHapley Additive exPlanations) for feature attribution.
- Model Monitor four types: Data Quality (no ground truth needed), Model Quality (needs GT),
  Bias Drift (needs GT), Feature Attribution Drift (needs GT, uses NDCG < 0.90 threshold).
- Bias drift monitoring: baseline, allowed ranges, scheduled monitoring, CloudWatch alerts.

### 26. Conversation Management and Context (Domains 1, 2)

- DynamoDB for conversation history storage (session ID to message history).
- Sliding window approach for long conversations (keep last N turns + summarize older turns).
- Comprehend for intent recognition and entity extraction before FM invocation.
- Step Functions for clarification workflows when intent is ambiguous.

### 27. Step Functions as Orchestration Backbone (Domains 1, 2, 3, 5)

- Agent loops as state machines (Choose, Task, Wait, Parallel, Map states).
- Circuit breaker pattern: open after N failures, return fallback.
- ReAct implementation: each state = reasoning/acting step.
- Human-in-the-loop: wait states with task tokens.
- Evaluation workflows: quality gates in CI/CD.
- Document processing: multi-step extraction, validation, human review.
- Error handling: Catch and Retry blocks.

### 28. Prompt Attack Detection and Input Sanitization (Domain 3)

- Three attack types: jailbreaks, prompt injection, prompt leakage (Standard tier only).
- Prompt attack filter is INPUT-ONLY (inputStrength only, no outputStrength).
- Input tagging required for InvokeModel API; Converse API handles via message roles.
- Input sanitization: remove unusual Unicode, encoded content (base64, hex, ROT13, Morse),
  control characters.
- WAF for API-level input validation.
- Prompt templates with designated variable slots.
- Safety classifiers: Bedrock Guardrails, Comprehend Toxicity Detection, Comprehend Prompt
  Safety Classifier.
- Automated adversarial testing: promptfoo, Bedrock Evaluations with toxicity metrics.

### 29. Amazon Bedrock Data Automation (Domains 1, 2)

- Extracts insights from unstructured multimodal content (documents, images, audio, video).
- Returns structured output with confidence scores and visual grounding.
- InvokeDataAutomationAsync API with project ARN.
- Projects group standard and custom output configurations (LIVE and DEVELOPMENT stages).
- Use cases: invoice processing, claims, contract analysis, media metadata extraction.

### 30. FM Parameter Tuning (Domains 4, 5)

- Temperature: lower = more deterministic, higher = more creative/random.
- Top K: smaller = more predictable, larger = more diverse.
- Top P (nucleus sampling): cumulative probability cutoff.
- Use case guidelines: factual Q&A (temp 0.0-0.3), customer service (0.3-0.5), creative
  writing (0.7-1.0), code generation (0.1-0.3).
- Parameter tuning does NOT change the model; only changes inference behavior.
- Converse API inferenceConfig for standard params; additionalModelRequestFields for
  model-specific params.

### 31. Troubleshooting GenAI Applications (Domain 5)

- Context window overflow: ValidationError, truncated responses. Resolution: token counting,
  prompt compression, context pruning, dynamic chunking.
- Low retrieval relevance: hybrid search + reranking + embedding quality check.
- Outdated information: incremental sync + real-time change detection + scheduled refresh.
- Inconsistent output format: explicit format instructions + tool use/function calling for
  guaranteed JSON + JSON schema.
- Prompt confusion: simplify, add delimiters, break into chain.
- API errors: 429 (backoff + quota increase + CRIS), 400 (validate format + token limits),
  403 (check IAM + model access), 503 (retry + failover).
- Connection timeout: TCP keep-alive for VPC/NAT.

### 32. Vector Store Monitoring and Optimization (Domains 4, 5)

- OpenSearch metrics (AWS/ES or AWS/AOSS): ClusterStatus, CPUUtilization, JVMMemoryPressure,
  SearchLatency, SearchRate, KNNGraphMemoryUsage (must fit in RAM).
- Auto-optimize: specify latency/recall thresholds; OpenSearch recommends configs.
- GPU-accelerated indexing for serverless HNSW operations.
- Knowledge Base logging: APPLICATION_LOGS type; tracks documents ignored, embedding
  exceptions, indexing exceptions.
- Embedding drift detection: periodic RAG evaluation, recall monitoring, similarity score
  distribution tracking.

### 33. GenAIOps and Lifecycle Automation (Domains 2, 4)

- GenAIOps = specialized MLOps for foundation models.
- Two categories: operationalizing FM consumption (DevOps + orchestration) and
  operationalizing FM training/tuning (FMOps/LLMOps).
- IaC with CDK/CloudFormation/Terraform for all GenAI infrastructure.
- SageMaker Pipelines for automated fine-tuning to evaluation to deployment.
- SageMaker MLflow for experiment tracking and model cataloging.

## Tier 4: LOW Importance Concepts

Supporting concepts tested indirectly or at the margins. Know the basics.

### 34. Amazon Comprehend NLP Capabilities

- Entity recognition, key phrase extraction, language detection, sentiment analysis, PII
  detection, toxicity detection (7 categories), prompt safety classifier.
- No training required for built-in models.
- Used for pre-processing (intent classification, entity extraction) and post-processing
  (toxicity checks, PII redaction).

### 35. Amazon Q Business and Q Developer

- Q Business: enterprise knowledge assistant; 40+ connectors; IAM Identity Center; topic
  controls; Q Apps (no-code apps from conversations); Agentic RAG.
- Q Developer: AI coding assistant; code generation, explanation, test generation, security
  scanning, code transformation, MCP integration.
- Know when to use each: Q Business for employees (knowledge), Q Developer for developers
  (code).

### 36. Amazon Augmented AI (A2I) and SageMaker Ground Truth

- A2I: managed human review workflows; built-in task types (Textract, Rekognition);
  custom task types via StartHumanLoop; work teams (Mechanical Turk, vendor, private);
  confidence threshold triggers.
- Ground Truth: labeled data via private, vendor, or Mechanical Turk workforces.
- GenAI use: review low-confidence FM outputs, build feedback loops, validate RAG answers.

### 37. Hybrid and Edge Deployments

- AWS Outposts: on-premises AWS infrastructure; data residency/sovereignty; regulated
  industries (healthcare, finance, government).
- AWS Wavelength: 5G edge, ultra-low latency (sub-10ms); real-time voice AI, AR/VR,
  connected vehicles.
- Direct Connect, Site-to-Site VPN, PrivateLink for secure routing.

### 38. Event-Driven Architectures for GenAI

- EventBridge: route enterprise events to Lambda FM processors.
- SQS: decouple producers from FM consumers; retries, DLQs.
- SNS: fan-out for AI-generated content distribution.
- DynamoDB Streams / Kinesis: trigger FM processing on data changes.
- AppFlow: SaaS-to-AWS data sync (Salesforce, ServiceNow).

### 39. Infrastructure as Code for GenAI

- CDK, CloudFormation, Terraform for defining GenAI stacks.
- Service Catalog for approved GenAI product portfolios.
- AWS Config for resource configuration tracking.
- CodePipeline + CodeBuild for CI/CD automation.

### 40. Sustainability for GenAI

- Managed services (Bedrock, Q) minimize operational overhead.
- EC2 Inferentia/Trainium for highest compute per watt.
- Auto-scaling and serverless for resource efficiency.
- Quantization, pruning, model distillation for smaller models.
- S3 Intelligent-Tiering, Lifecycle policies for storage efficiency.
- AWS Customer Carbon Footprint Tool.

### 41. Traditional NLP Evaluation Metrics

- ROUGE: n-gram overlap (penalizes valid paraphrases).
- BLEU: precision of n-gram overlap (machine translation).
- BERTScore: semantic similarity using contextual embeddings.
- These are insufficient alone for GenAI; prefer LLM-as-a-Judge.

### 42. CloudWatch Synthetics and Deployment Validation

- Synthetic canaries for automated deployment validation tests.
- Application Signals for fine-grained metrics at resource level (Model ID, Guardrails ID,
  KB ID, Agent ID) with GenAI attributes.
- Output diffing: compare new version outputs against baseline.
- Semantic drift detection: compare embedding distributions over time.

### 43. Amazon Lex, Kendra, Rekognition, Textract, Transcribe

- Lex: conversational interfaces (chatbots, voice bots).
- Kendra: enterprise search (alternative to OpenSearch for some use cases).
- Rekognition: image/video analysis (labels, text extraction, moderation).
- Textract: document text/table/form extraction.
- Transcribe: speech-to-text conversion; toxicity detection for voice data.

### 44. Lake Formation for Data Governance

- Column-level, row-level, cell-level security.
- Data filters via CreateDataCellsFilter API.
- Integrates with Athena, Redshift Spectrum, EMR.
- SELECT permission only.

### 45. Advanced Analytics Pipeline for GenAI Logs

- Bedrock invocation logs to S3, query with Athena, visualize in QuickSight.
- Athena Federated Queries to combine Bedrock logs with other data sources.
- CloudWatch Logs Sensitive Data Protection for PII masking in logs.

## Quick Reference: Concepts by Exam Domain

### Domain 1 (31%) -- Foundation Model Integration, Data Management, Compliance

| Priority | Concepts |
|---|---|
| CRITICAL | RAG pipeline, Bedrock Guardrails, Bedrock APIs, prompt engineering, vector stores/embeddings, FM selection/lifecycle |
| HIGH | Data validation pipelines, Well-Architected GenAI Lens |
| MEDIUM | Query handling, conversation management, Bedrock Data Automation |

### Domain 2 (26%) -- Implementation and Integration

| Priority | Concepts |
|---|---|
| CRITICAL | Agentic AI, Bedrock APIs, FM selection/routing, streaming |
| HIGH | Enterprise integration, CI/CD for GenAI |
| MEDIUM | Model deployment mechanics, Step Functions orchestration |
| LOW | Q Business/Q Developer, hybrid/edge, event-driven architectures |

### Domain 3 (20%) -- AI Safety, Security, and Governance

| Priority | Concepts |
|---|---|
| CRITICAL | Bedrock Guardrails, security/IAM/network isolation |
| HIGH | PII/privacy controls, responsible AI, hallucination detection, governance/compliance |
| MEDIUM | Defense-in-depth, prompt attack detection, Clarify/Model Monitor |
| LOW | A2I, Lake Formation, Comprehend NLP |

### Domain 4 (12%) -- Operational Efficiency and Optimization

| Priority | Concepts |
|---|---|
| CRITICAL | Cost optimization, monitoring/observability |
| HIGH | Streaming/latency optimization |
| MEDIUM | Token efficiency, FM parameters, vector store monitoring, GenAIOps |
| LOW | Sustainability |

### Domain 5 (11%) -- Testing, Validation, and Troubleshooting

| Priority | Concepts |
|---|---|
| CRITICAL | Monitoring/observability |
| HIGH | LLM-as-a-Judge evaluation, CI/CD quality gates |
| MEDIUM | Troubleshooting GenAI apps, deployment validation |
| LOW | Traditional NLP metrics, CloudWatch Synthetics |

## Quick Reference: In-Scope AWS Services by Exam Frequency

### Tier A: Appears in nearly every domain (know deeply)

- Amazon Bedrock (all features: APIs, Knowledge Bases, Guardrails, Prompt Management, Prompt
  Flows, Agents, AgentCore, Model Evaluation, Data Automation, Prompt Caching, Intelligent
  Prompt Routing, Cross-Region Inference, Provisioned Throughput, Model Distillation)
- AWS Lambda
- AWS Step Functions
- Amazon CloudWatch / CloudWatch Logs
- Amazon S3
- IAM

### Tier B: Central to 2-3 domains (know well)

- Amazon OpenSearch Service
- Amazon SageMaker AI (Model Registry, Clarify, Model Monitor, Ground Truth, Data Wrangler,
  Processing, endpoints)
- Amazon API Gateway
- AWS CloudTrail
- Amazon DynamoDB
- AWS X-Ray
- Amazon Comprehend
- AWS CodePipeline / CodeBuild / CodeDeploy
- AWS AppConfig
- Amazon EventBridge

### Tier C: Important in specific contexts (know use cases)

- Amazon Aurora (pgvector)
- Amazon ElastiCache (semantic caching)
- Amazon Cognito
- AWS KMS
- Amazon Macie
- Amazon Q Business / Q Developer
- AWS Amplify
- Amazon A2I / SageMaker Ground Truth
- AWS Outposts / AWS Wavelength
- AWS PrivateLink / VPC
- Amazon Managed Grafana
- Amazon QuickSight / Athena
- AWS Glue (Data Quality, Data Catalog)
- AWS Lake Formation
- Amazon Kendra
- AWS WAF

### Tier D: Know at a high level

- Amazon ECS / EKS / Fargate / ECR (MCP server hosting, containerized models)
- Amazon SNS / SQS (async patterns)
- Amazon Connect
- Amazon Lex
- Amazon Rekognition / Textract / Transcribe
- AWS DataSync / Transfer Family / AppFlow
- Amazon Neptune
- Amazon Route 53 / CloudFront / ELB / Global Accelerator
- AWS CDK / CloudFormation
- AWS Cost Explorer / Cost Anomaly Detection
- AWS Service Catalog
- Amazon EC2 / EBS / EFS
