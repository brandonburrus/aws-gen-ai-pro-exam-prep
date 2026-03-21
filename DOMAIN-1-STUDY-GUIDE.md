# Domain 1: Foundation Model Integration, Data Management, and Compliance

**Exam Weight: 31% — the largest domain on the exam**

This domain covers six task areas: designing GenAI solutions, selecting and configuring Foundation
Models (FMs), building data pipelines, implementing vector stores, designing retrieval mechanisms,
and implementing prompt engineering with governance.

---

## Task 1.1 — Analyze Requirements and Design GenAI Solutions

### Key Concepts

**Architectural Design Alignment (Skill 1.1.1)**

When designing a GenAI solution, match every architectural choice to a stated business need or
technical constraint:

- Choose FMs based on task type (text generation, summarization, classification, code generation,
  multimodal), latency SLA, and cost envelope.
- Select integration patterns: synchronous API calls for real-time responses; asynchronous via SQS
  for batch or bursty workloads; streaming for progressive UI rendering.
- Choose deployment strategies: on-demand (pay-per-token) vs. Provisioned Throughput
  (predictable high-volume) vs. self-hosted on SageMaker (data residency, custom models).

**Proof-of-Concept with Amazon Bedrock (Skill 1.1.2)**

Amazon Bedrock is the primary PoC vehicle on the exam. Key PoC steps:
1. Use the Bedrock console Playground to run ad-hoc prompts against multiple models.
2. Use Bedrock Model Evaluation to compare models on accuracy, robustness, and toxicity using
   your own dataset before committing to a model.
3. Measure token costs, latency, and quality metrics. Establish baselines before full deployment.

**Standardized Components via Well-Architected (Skill 1.1.3)**

The **AWS Well-Architected Generative AI Lens** extends the six Well-Architected pillars to GenAI:

| Pillar | GenAI Focus |
|---|---|
| Operational Excellence | Prompt template management, versioning, MLOps pipelines |
| Security | IAM least privilege, VPC isolation, Guardrails, PII protection |
| Reliability | Cross-Region inference, circuit breakers, graceful degradation |
| Performance Efficiency | Model selection, caching, batching, provisioned throughput |
| Cost Optimization | Token efficiency, tiered routing, right-sized models |
| Sustainability | Efficient inference, smaller models where appropriate |

The Generative AI Lens covers six lifecycle phases: **scoping, model selection, customization,
integration, deployment, and iteration**. Use the **AWS WA Tool** (accessible from the console)
to run assessments against the Generative AI Lens catalog.

> **Exam tip:** If a question asks how to ensure "consistent implementation across multiple
> deployment scenarios," the answer involves the Well-Architected Framework and/or the WA Tool
> Generative AI Lens.

---

## Task 1.2 — Select and Configure Foundation Models

### Key Concepts

**FM Evaluation Framework (Skill 1.2.1)**

Evaluate FMs across four dimensions:

1. **Task Performance** — task-specific accuracy, few-shot learning, instruction-following
   fidelity, output consistency, domain knowledge, reasoning capability.
2. **Architectural Characteristics** — parameter count, context window size, modality (text,
   image, video, audio, embedding), tokenization methodology.
3. **Operational Considerations** — throughput/latency profiles, cost-per-token, scalability,
   customization options, ease of integration, security.
4. **Responsible AI Attributes** — hallucination propensity, bias measurements, safety guardrail
   effectiveness, explainability, legal implications.

For **agentic AI** use cases, also evaluate: planning/reasoning capability, tool and API
integration quality, agent-to-agent communication, and multi-agent collaboration.

**Bedrock Model Evaluation** supports:
- **Automatic evaluations** — predefined metrics (accuracy, robustness, toxicity) against
  curated datasets.
- **Human evaluations** — bring your own dataset, define custom metrics (relevance, brand
  alignment, style).
- **LLM-as-a-Judge** — use a judge model (e.g., Claude, Nova Pro) to score generator model
  outputs on correctness, completeness, harmfulness, and refusal.

**Dynamic Model Selection (Skill 1.2.2)**

Pattern: decouple model identity from application code so you can swap providers without code
changes.

- **AWS AppConfig** — store the current model ID (e.g., `anthropic.claude-3-5-sonnet-20241022-v2:0`)
  as a configuration value; Lambda reads it at runtime. Changing the model is a config update,
  not a code deployment.
- **Amazon API Gateway** — front-end the model invocation; route requests to different backend
  Lambda functions or Bedrock endpoints via request transformation.
- **AWS Lambda** — stateless handler that reads the model identifier from AppConfig and calls
  `bedrock-runtime:InvokeModel`.

**Resilient AI Systems (Skill 1.2.3)**

Patterns for continuity during service disruptions:

| Pattern | Implementation |
|---|---|
| Cross-Region Inference (Geographic) | Keeps data within a geographic boundary; higher throughput than single-region; best for data residency requirements |
| Cross-Region Inference (Global) | Routes to any supported commercial region worldwide; ~10% cost savings; highest throughput; best without geographic restrictions |
| Circuit Breaker | Step Functions state machine: if model invocation fails N times, open the circuit and return a cached/fallback response |
| Graceful Degradation | Fallback to a smaller, cheaper model or a deterministic rule-based response when the primary FM is unavailable |
| Fallback Model | Configure alternate model IDs in AppConfig; Lambda switches to fallback on 5xx or throttle errors |

Cross-Region inference key facts:
- No additional cost for cross-region routing.
- All data stays encrypted on the AWS network during transit.
- CloudTrail logs are recorded in the **source region only**.
- Geographic profiles maintain data residency; Global profiles do not constrain geography.

**FM Customization Lifecycle (Skill 1.2.4)**

| Technique | When to Use | AWS Service |
|---|---|---|
| Fine-tuning (SFT) | Labeled examples available; adapt behavior/style | Amazon Bedrock or SageMaker AI |
| Continued Pre-training | Large unlabeled domain corpus; expand knowledge | Bedrock or SageMaker AI |
| LoRA (Low-Rank Adaptation) | Parameter-efficient; fast; lower compute cost | SageMaker AI adapter inference components |
| Full Fine-tuning (FFT) | Large dataset; maximum adaptation; higher compute | SageMaker AI |
| DPO / PPO (Alignment) | Steer model outputs toward preferences | SageMaker AI (Nova customization) |
| Knowledge Distillation | Transfer from large teacher to small student model | Bedrock Model Distillation |

**SageMaker Model Registry** — centralized catalog for model versioning:
- Register each trained model as a new version under a Model Group.
- Associate metadata: training metrics, dataset pointers, approval status.
- Control deployment through approval workflows (pending/approved/rejected).
- Integrate with CI/CD pipelines (CodePipeline + CodeBuild) for automated promotion.
- Rollback by re-pointing the endpoint to a previous approved model version.

> **Exam tip:** LoRA is the correct answer for "parameter-efficient adaptation" questions.
> SageMaker Model Registry is the correct answer for "versioning and lifecycle management of
> customized models."

---

## Task 1.3 — Implement Data Validation and Processing Pipelines

### Key Concepts

**Data Validation Workflows (Skill 1.3.1)**

| Service | Role in Validation |
|---|---|
| AWS Glue Data Quality | Rule-based validation (DQDL — Data Quality Definition Language), ML anomaly detection, serverless, integrates with Glue ETL jobs and the Glue Data Catalog |
| SageMaker Data Wrangler | Visual data preparation, profiling, transformation; generates code for SageMaker Pipelines |
| AWS Lambda | Custom validation logic (field format checks, business rule enforcement) before data enters the FM pipeline |
| Amazon CloudWatch | Publish custom metrics for data quality scores; trigger alarms on validation failure rates |

AWS Glue Data Quality (DQDL) key rules types: `Completeness`, `Uniqueness`, `Referential
Integrity`, `RowCount`, `ColumnValues`. Records that fail rules can be written to a separate
rejected S3 path for remediation.

**Multimodal Data Processing (Skill 1.3.2)**

FMs consume multiple data types. Appropriate processing per modality:

| Modality | Processing Service |
|---|---|
| Text | AWS Glue ETL, Lambda, SageMaker Processing |
| Audio | Amazon Transcribe → text → embed or ingest |
| Images | Amazon Rekognition (labels/text extraction), Bedrock Nova multimodal embeddings |
| Video | Bedrock Data Automation, Amazon Rekognition Video, Nova multimodal embeddings |
| Tabular | SageMaker Data Wrangler, Glue ETL, Bedrock structured data KB (Redshift / Glue Data Catalog) |

**Bedrock multimodal models** (e.g., Anthropic Claude, Amazon Nova) can natively consume
images and text in a single API request. For video and audio, you typically convert to text
(Transcribe) or use Bedrock Data Automation before passing to the FM.

**Input Formatting (Skill 1.3.3)**

Every model has its own prompt format. Know the key patterns:

- **Bedrock Converse API** — model-agnostic abstraction; automatically handles model-specific
  formatting; recommended for new integrations.
- **Bedrock InvokeModel API** — model-specific JSON body (e.g., `anthropic_version`,
  `messages`, `max_tokens` for Claude; `inputText`, `textGenerationConfig` for Titan).
- **SageMaker Endpoints** — send the request body in the format expected by the model container.
- **Conversation formatting** — for multi-turn dialogs, maintain a `messages` array with
  alternating `user` and `assistant` roles. Store history in DynamoDB; retrieve and prepend on
  each invocation.

**Input Quality Enhancement (Skill 1.3.4)**

| Enhancement | Service |
|---|---|
| Text reformatting / normalization | Bedrock (prompt the FM to clean/normalize), Lambda |
| Entity extraction | Amazon Comprehend (entities, key phrases, PII, sentiment) |
| Data normalization | Lambda (regex, format standardization), Glue |
| Noise removal / deduplication | SageMaker Processing, Glue ETL |

Amazon Comprehend provides pre-built NLP models for entity recognition, key phrase extraction,
language detection, sentiment analysis, and PII detection — no training required.

---

## Task 1.4 — Design and Implement Vector Store Solutions

### Key Concepts

**Vector Database Architectures (Skill 1.4.1)**

A vector database stores dense numerical representations (embeddings) that encode semantic
meaning. Similarity search finds semantically related content even without keyword overlap.

| AWS Vector Store Option | Best For |
|---|---|
| Amazon OpenSearch Service (Serverless or managed) | Full-text + vector hybrid search, large scale, real-time updates, Neural plugin for Bedrock integration |
| Amazon Aurora PostgreSQL with pgvector | Existing relational workloads that need vector capability; SQL-compatible; transactional consistency |
| Amazon Neptune Analytics | Graph + vector hybrid; knowledge graphs with vector search |
| Amazon DynamoDB + external vector store | Metadata and scalar lookups in DynamoDB; embeddings in a dedicated vector DB |
| Amazon Bedrock Knowledge Bases | Fully managed; abstracts ingestion, vectorization, and retrieval; quickest time-to-value |
| Pinecone / Redis Enterprise Cloud / MongoDB Atlas | Third-party options supported by Bedrock Knowledge Bases |

**Amazon Bedrock Knowledge Bases** supports these vector stores:
OpenSearch Serverless, Aurora PostgreSQL, Neptune Analytics, Pinecone, Redis Enterprise Cloud,
MongoDB Atlas, and Amazon S3 Vectors (cost-optimized, durable, sub-second queries).

**Metadata Frameworks (Skill 1.4.2)**

Attach metadata to vector documents to enable filtered retrieval:

- **S3 object metadata** — document timestamps, version, source URL stored as S3 metadata tags.
- **Custom attributes** — author, department, classification level, domain.
- **Tagging systems** — domain taxonomy for filtering by topic (e.g., `domain: legal`).

Metadata filtering in Bedrock Knowledge Bases: pass filter expressions in the
`RetrieveAndGenerate` or `Retrieve` API calls to scope results (e.g., `{"equals": {"key":
"domain", "value": "legal"}}`).

**High-Performance Vector Architecture (Skill 1.4.3)**

OpenSearch Service performance levers:

- **Sharding** — distribute index across multiple nodes; increase shard count for large indexes.
- **HNSW (Hierarchical Navigable Small World)** — approximate nearest-neighbor algorithm; tunable
  `m` (connections per node) and `ef_construction` (build-time quality) parameters.
- **IVF (Inverted File Index)** — alternative ANN algorithm; good for very large indexes with
  faster build times.
- **Multi-index approach** — separate indexes per domain or content type; reduces search space
  and improves relevance.
- **Quantization (product quantization, scalar quantization)** — compress vectors to reduce RAM
  usage; trades slight accuracy loss for cost savings.
- **Disk-based vector search** — keep compressed vectors in memory for candidate selection;
  retrieve full-precision vectors from disk for final scoring.
- **GPU-accelerated indexing** — serverless GPU attachment for billion-scale index builds.

**Data Maintenance for Vector Stores (Skill 1.4.5)**

Vector stores must reflect current source data:

| Mechanism | Description |
|---|---|
| Incremental sync | Re-index only changed/new documents (Bedrock KB sync job detects additions and deletions) |
| Real-time change detection | DynamoDB Streams → Lambda → re-embed and upsert into vector store |
| EventBridge rules | Trigger re-indexing on S3 object creation/update events |
| Scheduled refresh | CloudWatch Events / EventBridge Scheduler → Step Functions pipeline → full or partial re-sync |
| TTL-based expiry | Remove stale embeddings using vector store TTL features or scheduled Lambda cleanup |

---

## Task 1.5 — Design Retrieval Mechanisms for FM Augmentation

### Key Concepts

**Chunking Strategies (Skill 1.5.1)**

Chunking splits documents into pieces that fit within embedding model token limits and maximize
retrieval precision.

| Strategy | How It Works | Best For |
|---|---|---|
| Fixed-size chunking | Divide by token count with configurable overlap | Simple text; uniform structure |
| Default Bedrock chunking | ~300 tokens; preserves sentence boundaries | General-purpose |
| Hierarchical chunking | Parent chunks + child chunks; retrieve child, return parent for context | Long documents where context matters |
| Semantic chunking | NLP-based; split at topic/semantic boundaries; configurable breakpoint percentile | High-quality retrieval; nuanced content |
| No chunking | Each document is one chunk | Short documents (PDFs, emails) |

Hierarchical chunking detail: child chunks are retrieved for precision; parent chunks (larger
context window) are returned to the FM for broader context. Configurable parent/child sizes and
overlap tokens.

> **Exam tip:** Hierarchical chunking is the best answer for "improve context quality while
> maintaining retrieval precision."

**Embedding Models (Skill 1.5.2)**

An embedding model converts text (or multimodal content) into a dense vector. Key properties:

- **Dimensionality** — higher dimensions capture more semantic nuance but cost more storage/compute.
- **Domain fit** — a model trained on legal text will produce better embeddings for legal queries.
- **Max token input** — must be >= your chunk size.

AWS embedding options:

| Model | Key Characteristics |
|---|---|
| Amazon Titan Text Embeddings V2 | Supports binary vector embeddings; variable dimensions (256/512/1024); available in all Bedrock Knowledge Bases regions |
| Cohere Embed | High-quality multilingual; binary embeddings supported; optimized for retrieval |
| Amazon Nova Multimodal Embeddings | Cross-modal retrieval (text, image, video, audio) in a unified vector space |

**Binary vector embeddings** (Titan V2, Cohere Embed): represent each dimension as 0 or 1.
Benefits: lower storage cost, faster similarity computation. Tradeoff: slightly less precise
than float32. Currently supported with OpenSearch Serverless as the vector store.

**Batch embedding generation**: use Lambda to call `bedrock:InvokeModel` for the embedding
model in batches to reduce API calls and cost.

**Vector Search Solutions (Skill 1.5.3)**

| Solution | Notes |
|---|---|
| OpenSearch Service with vector search | k-NN and Approximate k-NN (HNSW/IVF); supports `knn_vector` field; scalable to billions of vectors |
| Aurora PostgreSQL + pgvector | SQL-based vector operations (`<->` cosine distance operator); transactional; good for hybrid relational + vector queries |
| Bedrock Knowledge Bases | Fully managed; handles ingestion, chunking, embedding, indexing, retrieval |

**Advanced Search Architectures (Skill 1.5.4)**

| Search Type | Description | When to Use |
|---|---|---|
| Semantic search | Embed query → vector similarity search | When keyword matching fails; synonyms, paraphrasing |
| Keyword search (BM25/lexical) | Exact term matching, TF-IDF scoring | Exact product codes, names, IDs |
| Hybrid search | Combine semantic + keyword scores (Reciprocal Rank Fusion or custom scoring) | Most production RAG systems; best overall relevance |
| Reranking | Post-retrieval model scores candidates by relevance to original query | When top-K results need reordering for quality |

**Bedrock reranker models**: after initial retrieval, send retrieved chunks + original query to
a reranker model in Bedrock. The reranker scores and re-orders results before passing context
to the FM. This is a two-stage retrieval pattern.

OpenSearch hybrid search combines lexical (BM25) and semantic (k-NN) scores. Conditional
scoring logic, parallel query processing, and post-filtering are supported.

**Query Handling Systems (Skill 1.5.5)**

Advanced techniques to improve what gets retrieved:

| Technique | Implementation |
|---|---|
| Query expansion | Bedrock: prompt an FM to generate synonyms/alternate phrasings; re-run search with expanded terms |
| Query decomposition | Lambda: split a complex multi-part question into atomic sub-queries; retrieve for each; merge results |
| Query transformation | Step Functions: orchestrate multi-step query refinement (expand → search → evaluate → refine) |
| HyDE (Hypothetical Document Embedding) | Generate a hypothetical answer, embed it, search with the answer embedding instead of the question embedding |

**Access Mechanisms (Skill 1.5.6)**

Standardize how FMs and agents access vector search:

- **Function calling / tool use** — define a `search_knowledge_base` tool in the FM's tool
  specification; the FM calls it autonomously when it needs retrieved context.
- **Model Context Protocol (MCP)** — open protocol for agent-tool integration; MCP clients
  provide standardized access to vector stores, APIs, databases; lightweight Lambda MCP servers
  for simple tools, ECS for complex ones.
- **Standardized API patterns** — wrap vector search behind a consistent internal API
  (API Gateway + Lambda); consumers never interact with the vector store directly.

---

## Task 1.6 — Implement Prompt Engineering Strategies and Governance

### Key Concepts

**Model Instruction Frameworks (Skill 1.6.1)**

Prompts have four components:
1. **Instruction** — what the model must do.
2. **Context** — background information, retrieved documents, system persona.
3. **Demonstration examples (few-shot)** — input/output examples that calibrate behavior.
4. **Input text** — the actual user query or data to process.

**System prompts** establish the model's role, tone, constraints, and output format. Enforce
these via:
- **Bedrock Prompt Management** — store role definitions as versioned, reusable prompt templates.
- **Bedrock Guardrails** — enforce Responsible AI policies (denied topics, content filters,
  PII redaction) independently of the prompt.
- **Template configurations** — use variables (`{{user_input}}`, `{{context}}`) for reusable
  parameterized prompts.

**Interactive AI Systems / Conversation Management (Skill 1.6.2)**

Managing multi-turn context:

| Service | Role |
|---|---|
| Amazon DynamoDB | Store conversation history (session ID → message history); retrieve and prepend on each turn |
| Amazon Comprehend | Detect user intent, extract entities, classify domain before invoking the FM |
| Step Functions | Implement clarification workflows: ask follow-up questions when intent is ambiguous; route to correct handler based on intent |

**Prompt Management and Governance (Skill 1.6.3)**

**Amazon Bedrock Prompt Management**:
- Create, version, test, and deploy parameterized prompt templates.
- Support approval workflows before a new prompt version goes to production.
- Share prompts across teams with IAM-controlled access.
- Use the Prompt builder console UI for iterative testing.

Governance supporting services:

| Service | Governance Role |
|---|---|
| Amazon S3 | Central repository for prompt template files and version history |
| AWS CloudTrail | Audit log of all Bedrock API calls (who invoked which prompt, which model, when) |
| Amazon CloudWatch Logs | Log every prompt/response pair for debugging and compliance review |
| AWS IAM | Control who can create, modify, or deploy prompt versions |

**Quality Assurance for Prompts (Skill 1.6.4)**

- **Lambda functions** — verify that model output matches expected format (JSON schema
  validation, regex checks).
- **Step Functions** — orchestrate test suites that exercise edge cases; assert on outputs.
- **CloudWatch alarms** — monitor regression metrics (e.g., failure rate, unexpected output rate)
  over time; alert on degradation after a prompt change.
- **A/B testing** — route a percentage of traffic to a new prompt variant via Bedrock Prompt
  Flows or AppConfig feature flags; compare metrics.

**Advanced Prompt Engineering Techniques (Skill 1.6.5)**

| Technique | Description |
|---|---|
| Zero-shot | No examples; relies on instruction clarity alone |
| Few-shot (in-context learning) | Provide 2-5 input/output examples in the prompt |
| Chain-of-thought (CoT) | Instruct the model to reason step-by-step before answering; improves accuracy on complex reasoning |
| Structured input/output | Define exact input structure and JSON output schema; use tool use for guaranteed JSON |
| Critique prompting | Ask the model to evaluate and improve its own initial response |
| Self-consistency | Generate multiple responses with different random seeds; vote on the majority answer |
| Prompt compression | Remove redundant context to reduce token usage and cost |
| Context pruning | Trim conversation history to the most recent/relevant turns |
| Feedback loops | Collect user ratings; use low-rated examples as negative training data or prompt refinement signals |

**Complex Prompt Systems (Skill 1.6.6)**

**Amazon Bedrock Prompt Flows** — visual no-code/low-code builder for multi-step prompt
orchestration:
- **Sequential prompt chains** — output of prompt A becomes input to prompt B.
- **Conditional branching** — route to different prompt nodes based on model output
  classification.
- **Reusable prompt components** — reference Bedrock Prompt Management templates as nodes
  in a flow.
- **Pre/post processing** — add Lambda nodes before or after FM invocations for data
  transformation or validation.

Use cases for prompt flows: document processing pipelines, intent classification → response
generation chains, multi-step summarization, automated compliance checks before returning
responses.

---

## Important Services Reference for Domain 1

### Amazon Bedrock

| Feature | Description |
|---|---|
| InvokeModel API | Synchronous model invocation; model-specific request body |
| Converse API | Model-agnostic conversation abstraction; handles system prompts, tool use, and multi-turn history |
| Streaming APIs | InvokeModelWithResponseStream; returns tokens incrementally for better UX |
| Cross-Region Inference | Geographic (data residency) or Global (max throughput) inference profile routing |
| Provisioned Throughput | Reserved capacity for predictable high-volume workloads; eliminates throttling |
| Knowledge Bases | Fully managed RAG: ingestion, chunking, embedding, vector store, retrieval, augmented generation |
| Prompt Management | Versioned, parameterized prompt templates with approval workflows |
| Prompt Flows | Visual multi-step prompt orchestration with conditional branching |
| Guardrails | Input/output content filtering, PII protection, denied topics, contextual grounding, automated reasoning checks |
| Model Evaluation | Automatic (LLM-as-a-Judge) and human evaluation; supports RAG evaluation |
| Bedrock Data Automation | Converts multimodal content (video, audio, images, documents) to structured text for ingestion |

### Amazon OpenSearch Service

- Supports `knn_vector` field type for dense vector storage (up to 16,000 dimensions).
- HNSW (Hierarchical Navigable Small World) and IVF algorithms for approximate nearest-neighbor.
- Distance metrics: cosine similarity, Euclidean distance, dot product.
- Hybrid search: combines BM25 (lexical) + k-NN (semantic) with Reciprocal Rank Fusion.
- Neural search plugin integrates with Bedrock embedding models for pipeline-based indexing.
- Serverless or managed cluster deployment.
- Sharding and replication for horizontal scalability.

### Amazon SageMaker AI

| Feature | Role in Domain 1 |
|---|---|
| SageMaker Processing | Run batch data transformation and validation jobs |
| SageMaker Data Wrangler | Visual data preparation, profiling, and feature engineering |
| SageMaker Model Registry | Catalog, version, approve, and deploy customized FM models |
| SageMaker Pipelines | Automated MLOps workflows for fine-tuning → evaluation → deployment |
| Adapter Inference Components | Deploy LoRA adapters alongside base models for parameter-efficient serving |

### AWS Glue

- **Glue Data Quality (DQDL)** — rule-based data validation; ML anomaly detection; runs within
  Glue ETL jobs; integrates with EventBridge for alerts.
- **Glue Data Catalog** — metadata repository for data lineage and source attribution.
- **Glue ETL** — serverless Spark for large-scale data transformation before FM ingestion.

### Supporting Services

| Service | Domain 1 Use Case |
|---|---|
| AWS Step Functions | Orchestrate multi-step workflows: circuit breakers, clarification flows, query transformation, prompt testing |
| AWS AppConfig | Store and dynamically retrieve model IDs and feature flags without code deployment |
| Amazon Comprehend | Entity extraction, intent detection, PII identification, sentiment analysis |
| Amazon Transcribe | Audio-to-text conversion for multimodal data pipelines |
| AWS Lambda | Custom validation, data normalization, batch embedding generation, query decomposition |
| Amazon DynamoDB | Conversation history storage; metadata storage alongside vector stores |
| AWS CloudTrail | Audit logging for all Bedrock API calls |
| Amazon CloudWatch | Metrics, alarms, logs for prompt regression testing and data quality monitoring |

---

## Exam Patterns and Common Distractors

### Pattern: "How do you switch models without code changes?"
**Answer:** AWS AppConfig to store the model ID; Lambda reads it at runtime. API Gateway can
also route to different model endpoints via request transformations.

### Pattern: "How do you ensure continuous operation when a Bedrock model is unavailable?"
**Answer:** Cross-Region inference profiles (geographic or global) for regional failover, plus
Step Functions circuit breaker for service-level failures, plus graceful degradation to a
fallback model.

### Pattern: "Which chunking strategy improves both precision and context quality?"
**Answer:** Hierarchical chunking. Child chunks for precision retrieval; parent chunks returned
to the FM for broader context.

### Pattern: "How do you validate data quality before FM ingestion?"
**Answer:** AWS Glue Data Quality with DQDL rules, supplemented by custom Lambda functions
for business logic validation, and CloudWatch metrics for ongoing monitoring.

### Pattern: "How do you improve RAG retrieval relevance beyond basic semantic search?"
**Answer:** Hybrid search (semantic + keyword with RRF scoring) in OpenSearch, combined with
Bedrock reranker models for post-retrieval reordering.

### Pattern: "How do you govern and audit prompt usage?"
**Answer:** Bedrock Prompt Management for versioning and approval workflows; S3 for template
repositories; CloudTrail for API-level audit; CloudWatch Logs for request/response logging.

### Pattern: "What is the parameter-efficient customization technique?"
**Answer:** LoRA (Low-Rank Adaptation). It adds small trainable adapter layers to the base
model; much cheaper than full fine-tuning.

### Pattern: "How do you handle multi-modal data in a RAG pipeline?"
**Answer:** Amazon Transcribe for audio, Rekognition/Nova multimodal embeddings for images and
video, Bedrock Data Automation for document and multimedia parsing, then ingest into Bedrock
Knowledge Bases with a multimodal embedding model (Amazon Nova Multimodal Embeddings).

### Pattern: "What is the correct approach to store and retrieve conversation history?"
**Answer:** DynamoDB keyed by session ID; retrieve history and prepend to the `messages` array
on each Converse API call.

---

## Quick-Reference: AWS Well-Architected Generative AI Lens

**Six lifecycle phases the lens covers:**
1. Scoping — define business problem, success metrics, use case fit for GenAI.
2. Model Selection — evaluate FMs using the four-dimension framework.
3. Customization — fine-tuning, continued pretraining, LoRA adapters.
4. Integration — RAG, APIs, enterprise system connectivity.
5. Deployment — on-demand, provisioned throughput, SageMaker endpoints.
6. Iteration — continuous evaluation, drift monitoring, prompt optimization.

**Best practice IDs to know:**
- `GENOPS03-BP01` — Implement prompt template management (Bedrock Prompt Management + Flows).
- `GENSEC04-BP01` — Implement a secure prompt catalog (versioned, IAM-controlled).

---

## Quick-Reference: Retrieval-Augmented Generation (RAG) Pipeline

```
Source Data (S3, Confluence, SharePoint, Salesforce, Web)
    |
    v
Parsing (Bedrock Data Automation / Foundation Model parser / default)
    |
    v
Chunking (Fixed-size / Hierarchical / Semantic / No chunking)
    |
    v
Embedding (Titan Text V2 / Cohere Embed / Nova Multimodal Embeddings)
    |
    v
Vector Store (OpenSearch Serverless / Aurora pgvector / Neptune / Pinecone / S3 Vectors)
    |
    v
Retrieval (Semantic / Hybrid / Reranking)
    |
    v
Augmented Prompt (System prompt + retrieved chunks + user query)
    |
    v
Foundation Model (Bedrock InvokeModel / Converse API)
    |
    v
Response (optionally post-processed by Guardrails / Lambda)
```

**Bedrock Knowledge Bases APIs:**
- `RetrieveAndGenerate` — end-to-end RAG: retrieves context and generates a response.
- `Retrieve` — retrieval only; returns ranked chunks; you construct the FM call yourself.

---

## Domain 1 Key Numbers

| Item | Value |
|---|---|
| Domain weight | 31% |
| Bedrock default chunk size | ~300 tokens |
| OpenSearch max vector dimensions | 16,000 |
| Titan Text Embeddings V2 dimensions | 256, 512, or 1024 (configurable) |
| Cross-region inference cost savings (Global) | ~10% vs. geographic profiles |
| LLM-as-a-Judge response accuracy (Automated Reasoning) | Up to 99% for factual validation |
| Bedrock Model Evaluation max prompts per job | 1,000 |
