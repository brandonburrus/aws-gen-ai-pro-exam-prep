# Domain 3: AI Safety, Security, and Governance

**Exam Weight: 20% — the third-largest domain on the exam**

This domain covers four task areas: implementing input/output safety controls, data security and
privacy controls, AI governance and compliance mechanisms, and responsible AI principles. Bedrock
Guardrails is the single most important service across all four tasks.

## Task 3.1 — Implement Input and Output Safety Controls

### Key Concepts

**Content Safety Systems for Harmful Inputs (Skill 3.1.1)**

Amazon Bedrock Guardrails is the primary content safety mechanism on the exam. A guardrail is a
combination of multiple policies that evaluate both user inputs and model responses.

Core architectural facts:

- An account can have multiple guardrails, each configured differently per use case.
- A guardrail requires at least one filter policy and blocked messaging for both prompts and
  responses (`blockedInputMessaging` and `blockedOutputsMessaging`).
- Guardrails work with any text or image Foundation Model on Bedrock, plus external/self-hosted
  models via the `ApplyGuardrail` API.
- Guardrails integrate natively with Bedrock Agents, Knowledge Bases, and Prompt Flows.
- Input evaluation happens in parallel across all configured policies for low latency.
- If the input is blocked, the Foundation Model is never invoked (no inference charge, only the
  guardrail evaluation charge).
- If the output is blocked, you are charged for both guardrail evaluation and model inference.

Seven guardrail policies:

| # | Policy | What It Does | Applies To |
|---|---|---|---|
| 1 | Content Filters | Detects harmful content across 6 categories: Hate, Insults, Sexual, Violence, Misconduct, Prompt Attack | Input + Output |
| 2 | Denied Topics | Blocks user-defined undesirable topics (up to 30 per guardrail) | Input + Output |
| 3 | Word Filters | Exact-match blocking of custom words/phrases and built-in profanity list | Input + Output |
| 4 | Sensitive Information Filters | Detects/blocks/masks PII using ML-based detection + custom regex | Input + Output |
| 5 | Contextual Grounding Checks | Detects hallucinations based on grounding source and query relevance | Output only |
| 6 | Automated Reasoning Checks | Validates responses against logical rules using formal mathematical reasoning | Output only |
| 7 | Prompt Attacks (sub-category of Content Filters) | Detects jailbreaks, prompt injection, prompt leakage | Input only |

Content filter strength levels (configured independently per category for input and output):

| Filter Strength | Blocks Content Classified At | Allows Content Classified At |
|---|---|---|
| NONE | Nothing | NONE, LOW, MEDIUM, HIGH |
| LOW | HIGH confidence only | NONE, LOW, MEDIUM |
| MEDIUM | HIGH + MEDIUM | NONE, LOW |
| HIGH | HIGH + MEDIUM + LOW | NONE only |

Content is classified with a confidence level (NONE/LOW/MEDIUM/HIGH). The filter strength
determines the threshold for blocking. A higher strength means more aggressive filtering.

Safeguard tiers:

- **Classic Tier** — Original behavior. Supports English/French/Spanish. Optimized for lower latency.
- **Standard Tier** — 30% better recall for content filters, 32% better recall for denied topics.
  Supports 60+ languages. Includes typo detection. Distinguishes between jailbreaks and prompt
  injection. Extends protection to code elements (comments, variable names, function names, string
  literals). Requires cross-Region inference opt-in.

Denied topics configuration:

- Up to 30 denied topics per guardrail.
- Each has a name (max 100 chars), a definition (max 200 chars), and optional sample phrases
  (up to 5 phrases, max 100 chars each).
- Can independently enable/disable for input and output with separate actions (BLOCK or NONE).
- Best practice: use crisp definitions, not instructions. Do not use negative definitions. Do not
  use denied topics for entity or word capture (use word filters or PII filters instead).

Word filters:

- Custom words/phrases for exact-match blocking (up to 10,000 items, up to 3 words each).
- Built-in profanity managed word list (toggle on/off).
- Can upload from .txt/.csv or S3 object.

Guardrail versioning:

- Creating a guardrail produces a working DRAFT.
- Create numbered, immutable versions via `CreateGuardrailVersion`.
- Versions do not have their own ARN. IAM policies on a guardrail apply to all its versions.
- Specify `guardrailVersion` as `"DRAFT"` or a numeric string (e.g., `"1"`, `"2"`).

The `ApplyGuardrail` API evaluates content against a guardrail without invoking any Foundation
Model:

```
POST /guardrail/{guardrailIdentifier}/version/{guardrailVersion}/apply
```

- `source`: `"INPUT"` for user content or `"OUTPUT"` for model output.
- Returns `action` (`GUARDRAIL_INTERVENED` or `NONE`), `outputs`, and detailed `assessments`.
- Use cases: pre-retrieval validation in RAG, evaluate non-Bedrock model outputs, insert guardrail
  checks at any point in custom application flow.

Input tagging for selective evaluation — when using `InvokeModel` / `InvokeModelWithResponseStream`,
you must wrap user content with XML tags to enable prompt attack detection:

```xml
<amazon-bedrock-guardrails-guardContent_xyz>
  user input here
</amazon-bedrock-guardrails-guardContent_xyz>
```

The tag suffix is specified in `guardrailConfig.tagSuffix`. Without tags, prompt attacks in user
input will not be filtered. The Converse API uses `guardContent` blocks with qualifiers instead.

Step Functions and Lambda extend guardrails with custom moderation workflows: pre-check with
Comprehend, invoke model with guardrails, post-process with Lambda, with branching logic, retries,
and human review escalation.

IAM enforcement: use the `bedrock:GuardrailIdentifier` condition key in IAM policies to mandate
specific guardrails for all inference calls, preventing bypass.

> **Exam tip:** If a question asks how to prevent Foundation Model invocation without content
> safety checks, the answer involves IAM policies with `bedrock:GuardrailIdentifier` condition keys
> combined with explicit deny statements.

**Content Safety Frameworks for Harmful Outputs (Skill 3.1.2)**

Input vs. output evaluation differences:

- Input blocked: Foundation Model never invoked. Returns `blockedInputMessaging`.
- Output blocked: Foundation Model already generated the response. Response replaced with
  `blockedOutputsMessaging` or masked.
- Prompt Attack filter is INPUT-ONLY — it has only `inputStrength`, no `outputStrength`.
- All other content filter categories (Hate, Insults, Sexual, Violence, Misconduct) can have
  different strengths for input vs. output.
- Contextual Grounding and Automated Reasoning checks are OUTPUT-ONLY.

Bedrock Model Evaluations for content moderation:

- **Automatic evaluations** — predefined metrics: accuracy, robustness, toxicity. Use curated or
  custom datasets.
- **LLM-as-a-Judge** — a second Foundation Model evaluates the first model's responses on
  correctness, completeness, harmfulness, answer refusal. Up to 98% cost savings vs. human
  evaluation.
- **Human evaluations** — custom metrics (relevance, style, safety) via internal employees or
  AWS-managed workers.
- **RAG evaluations** — context relevance, answer correctness, faithfulness for Knowledge Bases.

Text-to-SQL for deterministic results — Bedrock Knowledge Bases supports structured data stores
with natural language to SQL conversion:

- Connects to Amazon Redshift as the query engine.
- Converts natural language questions into SQL queries deterministically.
- Three APIs: `RetrieveAndGenerate` (query + retrieve + generate), `Retrieve` (query + retrieve),
  `GenerateQuery` (natural language to SQL only).
- Provides deterministic retrieval from structured data, reducing hallucination risk.

**Accuracy Verification to Reduce Hallucinations (Skill 3.1.3)**

Bedrock Knowledge Bases provide RAG-based grounding:

- User query is embedded, semantic search retrieves relevant documents, retrieved context is
  injected into the Foundation Model prompt, Foundation Model generates a grounded response.
- Citations are automatically included in responses for verification.
- Supported vector stores: OpenSearch Serverless, Aurora PostgreSQL, Pinecone, Redis Enterprise
  Cloud, MongoDB Atlas, Neptune Analytics.

Contextual Grounding Checks in Guardrails — the primary hallucination detection mechanism:

Two check types:
1. **Grounding Check** — Is the response factually accurate based on the source? New information
   not in the source is considered ungrounded.
2. **Relevance Check** — Is the response relevant to the user's query? A factually correct response
   to the wrong question is irrelevant.

Configuration:
- Each check produces a score from 0 to 1 (higher = more grounded/relevant).
- Configure thresholds between 0 and 0.99.
- If the score falls below the threshold, the response is flagged as a hallucination.
- Action can be BLOCK or NONE (detect only).
- Character limits: grounding source max 100,000 chars, query max 1,000 chars, response max
  5,000 chars.

Three required components:
1. **Grounding source** — reference/source material (retrieved documents).
2. **Query** — the user's question.
3. **Content to guard** — the model's response.

How to provide these depends on the API:
- Invoke APIs: use XML tags (`<amazon-bedrock-guardrails-groundingSource_xyz>` and
  `<amazon-bedrock-guardrails-query_xyz>`).
- Converse APIs: use `guardContent` blocks with qualifiers `["grounding_source"]` and `["query"]`.
- ApplyGuardrail API: provide content blocks with `guard_content` qualifier.

Grounding check scenario examples (exam-relevant):

| Source | Query | Response | Grounding | Relevance |
|---|---|---|---|---|
| "Tokyo is capital of Japan" | "Capital of Japan?" | "Capital of Japan is Tokyo" | Grounded | Relevant |
| "Tokyo is capital of Japan" | "Capital of Japan?" | "Capital of Japan is London" | NOT grounded | Relevant |
| "London is capital of UK. Tokyo is capital of Japan." | "Capital of Japan?" | "Capital of UK is London" | Grounded | NOT relevant |
| Same source | "Capital of Japan?" | "It is raining outside" | NOT grounded | NOT relevant |

Structured outputs (JSON Schema) via Converse API:

- Constrains model responses to follow a user-defined JSON schema, eliminating parsing errors.
- Specify schema in `outputConfig.textFormat` (Converse API).
- First-time schema compilation can take up to a few minutes. Compiled grammars cached 24 hours.
- Helps reduce hallucinations by constraining output format for downstream processing.

Automated Reasoning Checks:

- Uses formal logic (mathematical proofs) to verify response accuracy.
- Identifies correct responses with up to 99% accuracy.
- Provides provable explanations for why information is accurate or inaccurate.
- Operates in detect mode; the application decides how to act on findings.

> **Exam tip:** For "reduce hallucinations" questions: Bedrock Knowledge Bases (RAG grounding) +
> Contextual Grounding Checks in Guardrails is the primary answer. JSON Schema structured outputs
> is the answer for "ensure deterministic output format." Automated Reasoning is the answer for
> "verify logical/policy compliance with provable explanations."

**Defense-in-Depth Safety Systems (Skill 3.1.4)**

AWS recommends a multi-layered approach. Each layer addresses different threat vectors:

**Layer 1 — Pre-Processing (Application Level):**
- Amazon Comprehend Trust and Safety: Toxicity Detection (`DetectToxicContent` API, 7 categories:
  sexual harassment, hate speech, threat, abuse, profanity, insult, graphic), Prompt Safety
  Classifier (safe/unsafe binary classification).
- Application-level input sanitization in Lambda: remove unusual Unicode, encoded content
  (base64, hex, ROT13, Morse code), control characters.
- AWS WAF for API-level input validation, rate limiting, IP filtering.

**Layer 2 — Model Level (Bedrock Guardrails):**
- All seven filter types: content filters, denied topics, word filters, sensitive information
  filters, prompt attack detection, contextual grounding, automated reasoning.

**Layer 3 — Post-Processing:**
- Lambda functions for custom validation, filtering, or transformation of model responses.
- Additional Comprehend toxicity checks on output.
- Business logic validation.

**Layer 4 — API Level:**
- API Gateway for rate limiting, throttling, authentication, authorization.
- IAM policies to enforce mandatory guardrails.
- CloudTrail for audit logging.
- CloudWatch for monitoring and anomaly detection.

The `ApplyGuardrail` API enables guardrail evaluation decoupled from model invocation. Insert at
any point: before retrieval in RAG, after retrieval but before generation, after generation from
non-Bedrock models, or between agent steps.

**Advanced Threat Detection (Skill 3.1.5)**

Three types of prompt attacks detected by Bedrock Guardrails:

1. **Jailbreaks** — bypass native safety capabilities (e.g., "Do Anything Now" prompts).
2. **Prompt Injection** — override developer instructions (e.g., "Ignore everything earlier").
3. **Prompt Leakage** (Standard tier only) — extract system prompts or confidential configuration.

Prompt Attack filter configuration:
- Part of `contentPolicyConfig` with type `PROMPT_ATTACK`.
- Has only `inputStrength` — no `outputStrength`. Prompt attacks are INPUT-ONLY detection.
- Action can be BLOCK or NONE (detect only).

Input tagging is critical for prompt attack detection when using `InvokeModel` /
`InvokeModelWithResponseStream`. Without tags, prompt attacks will not be filtered. The Converse
API handles this via message roles.

Input sanitization strategies (defense-in-depth):
1. Application-level: remove unnecessary Unicode, unusual patterns, encoded content.
2. AWS WAF: block known attack patterns at the API gateway level.
3. Prompt templates: structure prompts with designated slots for user variables.
4. System prompts: constrain model behavior with clear boundaries.
5. Format breakers: convert text through multiple formats to strip hidden malicious content.

Safety classifiers available:
- Bedrock Guardrails content filters (ML-based, 6 categories).
- Comprehend Toxicity Detection (7-category classifier).
- Comprehend Prompt Safety Classifier (binary safe/unsafe).
- Custom classifiers via SageMaker or fine-tuned Foundation Models deployed as Lambda functions.

Automated adversarial testing:
- Use tools like `promptfoo` to test prompt injection, jailbreaking, adversarial inputs.
- Test categories: role confusion, context manipulation, privilege escalation, multi-turn attacks,
  context poisoning, cross-agent prompt propagation.
- Include both benign scenarios and malicious attack vectors in test suites.
- Use Bedrock Evaluations with toxicity metrics and LLM-as-a-Judge with harmfulness metrics.

Monitoring:
- All blocked content appears as plain text in Model Invocation Logs (disable if unwanted).
- CloudWatch metrics: monitor `GuardrailPolicyType` for masking/blocking events.
- Guardrail tracing: enable via `trace` field (`"enabled"`, `"disabled"`, `"enabled_full"`).

> **Exam tip:** For "protect against prompt injection" questions, the answer is Bedrock Guardrails
> Prompt Attack content filter (Standard tier for best detection). For "defense in depth," describe
> the four-layer architecture: Comprehend pre-processing, Guardrails at model level, Lambda
> post-processing, API Gateway at the API level.

## Task 3.2 — Implement Data Security and Privacy Controls

### Key Concepts

**Protected AI Environments (Skill 3.2.1)**

VPC endpoints for network isolation:

- AWS PrivateLink creates a private connection between your VPC and Bedrock. Traffic never
  traverses the public internet.
- Creates an endpoint network interface (ENI) in each subnet you enable.
- No internet gateway, NAT device, VPN, or Direct Connect required.

Bedrock VPC endpoint service names:

| Category | Service Name |
|---|---|
| Control Plane APIs | `com.amazonaws.region.bedrock` |
| Runtime APIs (InvokeModel, Converse) | `com.amazonaws.region.bedrock-runtime` |
| Agents Build-time APIs | `com.amazonaws.region.bedrock-agent` |
| Agents Runtime APIs | `com.amazonaws.region.bedrock-agent-runtime` |

Private DNS: when enabled, API requests use the default Regional DNS name
(e.g., `bedrock-runtime.us-east-1.amazonaws.com`). Existing SDK code works without modification.

VPC endpoint policies: attach a resource-based IAM policy to restrict which principals, actions,
and resources are accessible through the endpoint. Default policy allows full access.

When using a VPC with no internet access for model customization, create an S3 VPC gateway
endpoint so jobs can access training/validation data.

IAM policies for Bedrock:

| Feature | Supported? |
|---|---|
| Identity-based policies | Yes |
| Resource-based policies | No |
| Policy condition keys | Yes |
| ABAC (tags in policies) | Yes |
| Temporary credentials | Yes |
| Service roles | Yes |
| Service-linked roles | No |

Key IAM actions: `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`,
`bedrock:CreateModelCustomizationJob`, `bedrock:CreateModelInvocationJob`,
`bedrock:CreateGuardrail`, `bedrock:ApplyGuardrail`.

AWS managed policies: `AmazonBedrockFullAccess` (full access), `AmazonBedrockReadOnly` (read-only).

AWS Lake Formation for granular data access — three levels:

- **Column-level** — restrict which columns users can see (e.g., hide PII columns).
- **Row-level** — restrict rows based on column values using PartiQL `WHERE` clause syntax.
- **Cell-level** — combines row + column filtering for maximum granularity.

Implementation uses data filters created via `CreateDataCellsFilter` API. Filters apply only to the
`SELECT` Lake Formation permission. Integrates with Athena, Redshift Spectrum, and EMR.

CloudWatch for data access monitoring:

- Model Invocation Logging: disabled by default, must be explicitly enabled.
- Collects invocation logs, model input data, and model output data.
- Destinations: CloudWatch Logs, S3, or both.
- APIs: `PutModelInvocationLoggingConfiguration`, `GetModelInvocationLoggingConfiguration`,
  `DeleteModelInvocationLoggingConfiguration`.
- CloudWatch Logs: JSON events with metadata + I/O up to 100 KB. Larger data goes to S3.
- Runtime metrics (automatic): `Invocations`, `InvocationLatency`, `InputTokenCount`,
  `OutputTokenCount`, `TimeToFirstToken`, `InvocationThrottles`.

> **Exam tip:** Bedrock does NOT support resource-based policies. All access control uses
> identity-based policies. For "network isolation" questions, the answer is VPC interface endpoints
> powered by AWS PrivateLink. For "granular data access in a data lake," the answer is Lake
> Formation with data filters.

**Privacy-Preserving Systems (Skill 3.2.2)**

Amazon Comprehend PII Detection:

- `DetectPiiEntities` — real-time, locates PII with type, confidence score, and character offsets.
  Up to 100 KB per document. English and Spanish.
- `ContainsPiiEntities` — returns labels and scores of PII types found (no position info).
- Async batch jobs for PII detection and redaction. Redaction replaces PII with asterisks.
- 22 universal PII types: ADDRESS, AGE, AWS_ACCESS_KEY, AWS_SECRET_KEY,
  CREDIT_DEBIT_CVV/EXPIRY/NUMBER, DATE_TIME, DRIVER_ID, EMAIL, IBAN, IP_ADDRESS, LICENSE_PLATE,
  MAC_ADDRESS, NAME, PASSWORD, PHONE, PIN, SWIFT_CODE, URL, USERNAME, VIN.
- 14 country-specific types for Canada, India, UK, and US (SSN, passport, health numbers, etc.).

Amazon Macie for PII Detection in S3:

- Uses ML and pattern matching to discover sensitive data in S3.
- Two discovery methods: automated sensitive data discovery (daily, breadth-first) and targeted
  sensitive data discovery jobs.
- Managed data identifiers: built-in criteria for financial, personal, and credential data.
- Custom data identifiers: user-defined regex (up to 512 chars), optional keywords, proximity
  rules, custom severity settings.
- Allow lists for exceptions.
- Findings integrated with EventBridge and Security Hub.

Bedrock native data privacy features:

- Bedrock never shares your data with model providers.
- Bedrock does not use customer data to train base Foundation Models.
- Fine-tuning creates a private copy of the model. Training data is not stored after job completion.
- Model improvement is opt-in only.
- Encryption in transit: TLS 1.2. Encryption at rest: AWS-owned keys by default, customer managed
  KMS keys optional.
- Compliance: GDPR, HIPAA eligible, SOC 1/2/3, ISO 27001, CSA STAR Level 2, FedRAMP High.

Bedrock Guardrails sensitive information filters:

- ML-based, context-dependent PII detection (not just regex).
- Two handling modes: BLOCK (entire request/response blocked) or ANONYMIZE/MASK (PII replaced with
  type identifier tags like `{NAME}`, `{EMAIL}`, `{US_SOCIAL_SECURITY_NUMBER}`).
- 30+ PII entity types across categories: General, Finance, IT, USA, Canada, UK.
- Custom regex patterns supported (does NOT support regex lookaround).
- Each PII type can individually be set to BLOCK or ANONYMIZE.
- Works on both input and output, independently configurable.
- Standard tier extends PII detection to code elements (comments, variable names, string literals,
  hardcoded credentials).

S3 Lifecycle configurations for data retention:

- Automate data lifecycle for privacy compliance (GDPR right to erasure, data minimization).
- Transition actions (move to cheaper storage classes) and expiration actions (delete objects).
- Up to 1,000 rules per bucket. Filter by prefix, tags, or size.

KMS encryption for Bedrock:

- AWS-owned keys by default (no charge, no management).
- Customer managed keys optional for: custom models, agents, knowledge base data source ingestion,
  vector stores in OpenSearch, evaluation jobs, flows, guardrails.
- When using customer managed keys, Bedrock creates KMS grants (primary for long-lived resources,
  secondary for async operations).
- Key policy needs: `kms:CreateGrant`, `kms:DescribeKey`, `kms:GenerateDataKey`, `kms:Decrypt`.
- Use `kms:ViaService` condition to restrict key access to Bedrock only.

> **Exam tip:** For "detect PII in real-time text" the answer is Amazon Comprehend. For "discover
> PII in S3 at rest" the answer is Amazon Macie. For "filter PII in Foundation Model prompts and
> responses" the answer is Bedrock Guardrails sensitive information filters. Know the difference
> between BLOCK (stops content) and ANONYMIZE (replaces PII with tags).

**Privacy-Focused AI Systems (Skill 3.2.3)**

Data masking techniques:

- **Static masking** — applied to data at rest before use. Original data permanently replaced.
  Irreversible. Used for creating non-production datasets from production data.
- **Dynamic masking** — applied at query time based on user permissions. Original data preserved.
  Lake Formation cell/row/column security and Bedrock Guardrails ANONYMIZE mode are forms of
  dynamic masking.

Anonymization strategies:

| Strategy | Description | Reversible? |
|---|---|---|
| Pseudonymization | Replace identifiers with artificial IDs. Mapping table allows re-identification. | Yes (with mapping) |
| Tokenization | Replace sensitive data with format-preserving tokens. Token vault maintains mapping. | Yes (with vault) |
| Generalization | Reduce data precision (exact age to age range, address to city). | No |
| k-Anonymity | Ensure each record is indistinguishable from at least k-1 others. | No |

Bedrock data privacy guarantees summary:

1. Bedrock does NOT use inputs/outputs to train base Foundation Models.
2. Data is not shared with model providers (Anthropic, Meta, AI21, etc.).
3. Fine-tuning creates a private copy; training data not stored after completion.
4. All data encrypted in transit (TLS 1.2) and at rest (AWS-owned or CMK).
5. Private VPC connectivity via AWS PrivateLink.
6. Model improvement is opt-in only.
7. Fine-tuned models can replay training data — filter confidential data before training.

Service selection matrix:

| Need | Service |
|---|---|
| PII detection in text (real-time) | Amazon Comprehend `DetectPiiEntities` |
| PII detection in S3 at rest | Amazon Macie |
| PII filtering in AI prompts/responses | Bedrock Guardrails sensitive information filters |
| Network isolation for Bedrock | VPC interface endpoints (PrivateLink) |
| Fine-grained data lake access | AWS Lake Formation data filters |
| Encryption key management | AWS KMS (customer managed keys) |
| Model invocation auditing | CloudWatch Logs + S3 + CloudTrail |
| Data lifecycle/retention | S3 Lifecycle configuration |

## Task 3.3 — Implement AI Governance and Compliance Mechanisms

### Key Concepts

**Compliance Frameworks (Skill 3.3.1)**

SageMaker AI Model Cards — centralized documentation for capturing critical details about ML models
for governance and reporting:

Key content sections (JSON schema):

| Section | Fields | Purpose |
|---|---|---|
| `model_overview` | `model_description`, `model_creator`, `model_artifact` (max 15), `algorithm_type`, `problem_type` | High-level identification |
| `intended_uses` | `purpose_of_model`, `intended_uses`, `factors_affecting_model_efficiency`, `risk_rating` | Document appropriate/inappropriate uses |
| `business_details` | `business_problem`, `business_stakeholders`, `line_of_business` | Business context |
| `training_details` | `objective_function`, `training_observations`, `training_job_details` (ARN, datasets, metrics) | Reproducibility and audit trail |
| `evaluation_details` | `name` (required), datasets (max 10), `metric_groups` | Performance evidence |

Risk ratings: `unknown`, `low`, `medium`, `high`. Maps directly to EU AI Act risk classification.

Versioning: any edit (other than approval status update) creates a new immutable version, ensuring
a complete audit trail.

Export: model cards can be exported to PDF via `CreateModelCardExportJob`.

Integration: Model Cards integrate with SageMaker Model Registry. Can auto-populate evaluation
metrics from Clarify and Model Monitor reports stored in S3. Supports cross-account access.

Key APIs: `CreateModelCard`, `DescribeModelCard`, `ListModelCards`, `ListModelCardVersions`,
`UpdateModelCard`, `DeleteModelCard`, `CreateModelCardExportJob`.

AWS Glue for data lineage:

- Glue Data Catalog: centralized metadata repository for data location, schema, and runtime metrics.
  Organized into databases and tables.
- Crawlers automatically scan data sources, infer schemas, and populate the catalog.
- Data lineage records track transformations and operations performed on data.
- Column statistics (min/max, null counts, distinct values) without additional pipelines.
- Integrates with Lake Formation for fine-grained access control.

CloudWatch Logs for decision logs:

- Bedrock model invocation logs sent to CloudWatch Logs as JSON events.
- Each event contains invocation metadata plus I/O (up to 100 KB). Larger payloads go to S3.
- Use CloudWatch Logs Insights for querying. Create custom metric filters for alerting.

> **Exam tip:** SageMaker Model Cards is the answer for "document Foundation Model limitations,
> intended uses, and risk ratings for regulatory compliance." Glue Data Catalog is the answer for
> "track data lineage and source metadata."

**Data Source Tracking for Traceability (Skill 3.3.2)**

Glue Data Catalog for data source registration:

- Structure: databases, tables, crawlers, connections, schema registry.
- Crawlers use classifiers (built-in or custom) to recognize data formats and infer schemas.
- Supports S3, RDS, Redshift, DynamoDB, Kafka, MongoDB, JDBC-compatible sources.

Metadata tagging for source attribution:

- Bedrock Knowledge Bases: create `.metadata.json` files alongside S3 source documents with
  key-value attribute pairs for metadata filtering during queries.
- S3 object tagging: up to 10 tags per object (keys up to 128 chars, values up to 256 chars).
- AWS Organizations Tag Policies enforce consistent tagging across accounts.

CloudTrail for audit logging:

- Bedrock management events logged by default (InvokeModel, Converse, all control plane ops).
- Bedrock data events must be explicitly configured via advanced event selectors.

Data events by resource type:

| Resource Type | Events Logged |
|---|---|
| `AWS::Bedrock::AgentAlias` | `InvokeAgent` |
| `AWS::Bedrock::Model` | `InvokeModelWithBidirectionalStream`, `GetAsyncInvoke`, `StartAsyncInvoke` |
| `AWS::Bedrock::KnowledgeBase` | `Retrieve`, `RetrieveAndGenerate` |
| `AWS::Bedrock::FlowAlias` | `InvokeFlow` |
| `AWS::Bedrock::Guardrail` | Guardrail data events |
| `AWS::Bedrock::Prompt` | `RenderPrompt` |

Each CloudTrail event includes: identity info (who), IP address, timestamp, request parameters,
response elements, error codes.

Bedrock Knowledge Bases citation/attribution:

- `RetrieveAndGenerate` returns citations linking generated text to source documents.
- Each citation contains: `location` (position in source), `source` (identifier/URL),
  `sourceContent` (referenced content), `title`.
- In the console, citations appear as footnotes expandable to source text and S3 links.
- Guardrails applied to `RetrieveAndGenerate` evaluate user input and generated response only —
  they do NOT evaluate the retrieved references.

> **Exam tip:** For "audit trail of all Bedrock API calls" the answer is CloudTrail. For "track
> who invoked which model and when" the answer is CloudTrail management events. For "log full
> prompt/response content" the answer is Bedrock Model Invocation Logging (CloudWatch Logs + S3).
> For "cite sources in generated answers" the answer is Bedrock Knowledge Bases citations via
> `RetrieveAndGenerate`.

**Organizational Governance Systems (Skill 3.3.3)**

Regulatory requirements and AWS support:

| Framework | GenAI Relevance | AWS Support |
|---|---|---|
| GDPR | Right to explanation, data minimization, consent | Bedrock PII filters, regional data residency, encryption, VPC endpoints |
| HIPAA | PHI protection, BAA required | Bedrock is HIPAA-eligible, sensitive info filters, invocation logging |
| SOC 2 | Audit controls, monitoring, access management | CloudTrail, CloudWatch, IAM, encryption |
| EU AI Act | Risk classification, transparency, human oversight | Model Cards risk ratings, Guardrails, model evaluation, A2I |
| ISO/IEC 42001:2023 | AI management system certification | AWS was first major cloud provider to achieve this certification for Bedrock, Q Business, Textract, Transcribe |
| FedRAMP High | Federal government security | Bedrock has FedRAMP High authorization |

AWS AI Service Cards:

- Published by AWS for their own managed AI services (Rekognition, Nova models, Titan,
  Comprehend, Transcribe, etc.).
- Content: intended use cases, limitations, responsible AI design choices, performance expectations,
  fairness/bias testing methodology, deployment best practices.
- Distinction: AI Service Cards are AWS-published and read-only. SageMaker Model Cards are
  customer-created for custom models and fully customizable.

AWS Service Catalog for approved GenAI products:

- Administrators create portfolios of approved products (CloudFormation or Terraform templates).
- End users can only launch products from portfolios they have access to.
- Apply launch constraints (deployment configurations) and template constraints (parameter values).
- Use TagOptions to enforce tagging on provisioned resources.
- AWS Organizations integration for cross-account portfolio sharing.

Service Control Policies (SCPs) for organizational guardrails:

- JSON policies attached to OUs or accounts that set maximum permission boundaries.
- GenAI governance examples: deny access to specific Bedrock models, deny `bedrock:InvokeModel`
  without a guardrail, restrict Bedrock to specific Regions, block model customization in
  certain accounts.
- SCPs are deny-only filters — they cannot grant permissions, only restrict.
- Combine IAM policies with `bedrock:GuardrailIdentifier` condition key to require guardrails on
  every invocation at the organizational level.

**Continuous Monitoring and Governance Controls (Skill 3.3.4)**

Bias drift monitoring with SageMaker Clarify:

1. Create a baseline: run a baselining job against training data.
2. Define allowed ranges for bias metrics (e.g., DPPL between -0.1 and 0.1).
3. Schedule monitoring via `create_monitoring_schedule()` on a `ModelBiasModelMonitor` instance.
4. Clarify computes bias metrics on live data during each monitoring window.
5. Uses Normal Bootstrap Interval method for statistical significance (avoids false alarms).
6. If the confidence interval does not overlap the allowed range, an alert fires via CloudWatch.

Bias metrics supported: DPPL (Difference in Positive Proportions in Predicted Labels), DI (Disparate
Impact), DCAcc (Difference in Conditional Acceptance), DCR (Difference in Conditional Rejection).

SageMaker Model Monitor — four monitoring types:

| Type | What It Monitors | Requires Ground Truth? |
|---|---|---|
| Data Quality | Statistical properties of input features (drift) | No |
| Model Quality | Prediction accuracy | Yes |
| Bias Drift | Fairness metrics over time | Yes |
| Feature Attribution Drift | SHAP value changes (NDCG score) | Yes |

Feature Attribution Drift measures changes in feature importance using SHAP values. Uses NDCG
(Normalized Discounted Cumulative Gain) to compare feature attribution rankings. Default alert
threshold: NDCG < 0.90.

Automated alerting and remediation:

- CloudWatch Alarms on Bedrock runtime metrics (token counts, latency, errors, throttles).
- EventBridge Rules for Bedrock job state changes — trigger Lambda, Step Functions, or SNS.
- Remediation pattern: CloudWatch Alarm -> SNS -> Lambda -> (disable endpoint, retrain, notify).
- CloudWatch anomaly detection creates dynamic baselines for GenAI metrics.

Bedrock Model Invocation Logging:

- Disabled by default. Enable via console or `PutModelInvocationLoggingConfiguration`.
- Logs `Converse`, `ConverseStream`, `InvokeModel`, `InvokeModelWithResponseStream`.
- Choose which modalities to log: Text, Image, Embedding, Video.
- CloudWatch Logs: JSON events up to 100 KB. S3: gzipped JSON files for larger data.
- S3 bucket must be in same Region, ACLs disabled, bucket policy granting `s3:PutObject` to
  `bedrock.amazonaws.com`.
- Large data (>100 KB) or binary image outputs can ONLY go to S3, not CloudWatch Logs.

Token-level redaction:

- Bedrock Guardrails ANONYMIZE action replaces PII with tags (`{NAME}`, `{SSN}`).
- BLOCK removes content entirely and returns blocked messaging.
- All blocked content from guardrails appears as plain text in Model Invocation Logs.
  Disable logging or use S3 with KMS encryption if this is a security concern.

Monitoring integration pattern:

```
Bedrock Invocation Logs -> S3 -> Glue Catalog -> Athena -> QuickSight
                       -> CloudWatch Logs -> Logs Insights -> Dashboards
                       -> Metric Filters -> Alarms -> SNS -> Lambda
```

> **Exam tip:** Data Quality monitoring does NOT need Ground Truth labels. Bias Drift and Model
> Quality monitoring DO require Ground Truth labels. For "blocked content appears in logs" —
> remember that guardrail-blocked content shows as plain text in invocation logs. Large payloads
> (>100 KB) can only go to S3.

## Task 3.4 — Implement Responsible AI Principles

### Key Concepts

**Transparent AI Systems (Skill 3.4.1)**

Bedrock Agent tracing — the primary transparency mechanism for agent decision-making:

Seven trace types:

| Trace Type | Purpose |
|---|---|
| PreProcessingTrace | Agent contextualizes and categorizes user input; determines if valid |
| OrchestrationTrace | Agent interprets input, invokes action groups, queries knowledge bases (the "reasoning") |
| PostProcessingTrace | Agent shapes orchestration output into user-facing response |
| CustomOrchestrationTrace | Details about custom orchestration steps |
| RoutingClassifierTrace | Routing classifier input/output for multi-agent collaboration |
| FailureTrace | Records the reason a step failed; only type WITHOUT a `ModelInvocationInput` object |
| GuardrailTrace | Actions taken by an attached Guardrail |

How to enable:
- Console: choose "Show trace" in the agent test window.
- API: set `enableTrace` to `TRUE` in `InvokeAgent`. Disabled by default.

TSTALIASID: the test alias used with the DRAFT version for API-based testing. Must call
`PrepareAgent` first to package the agent with latest working draft changes.

Each trace (except FailureTrace) contains a `ModelInvocationInput` object showing: the type
(PRE_PROCESSING, ORCHESTRATION, ROUTING_CLASSIFIER, etc.), the actual prompt sent to the
Foundation Model, the model used, inference configuration, and whether the prompt was DEFAULT or
OVERRIDDEN.

Bedrock Prompt Flows tracing:

- Set `enableTrace` to `true` in `InvokeFlow`.
- Trace event types: FlowTraceNodeInputEvent, FlowTraceNodeOutputEvent,
  FlowTraceConditionNodeResultEvent, FlowTraceNodeActionEvent, FlowTraceDependencyEvent.

Extended thinking / Chain-of-thought (Claude on Bedrock):

- Outputs internal `thinking` content blocks showing step-by-step reasoning before the final
  `text` answer. Direct transparency mechanism for user-facing explanations.
- Supported models: Claude Opus 4.5, Opus 4, Sonnet 4, Sonnet 4.5, Haiku 4.5, Claude 3.7 Sonnet.
- Set `budget_tokens` in thinking configuration (minimum 1,024 tokens).
- Response includes `thinking` blocks followed by `text` blocks.
- Streaming required when `max_tokens` > 21,333.
- Adaptive thinking (Claude Opus 4.6, Sonnet 4.6): set `thinking.type` to `"adaptive"` instead of
  fixed budget. Claude dynamically decides when and how much to think.
- NOT compatible with `temperature`, `top_p`, `top_k`, response pre-fill, or forced tool use.

Evidence presentation / source attribution:

- Bedrock Knowledge Bases `RetrieveAndGenerate` returns `citations` with each response.
- Each citation contains: `generatedResponsePart` (segment of response), `retrievedReferences`
  (source S3 URI, content excerpt, metadata).
- The `Retrieve` API returns raw source chunks for custom attribution handling.

> **Exam tip:** For "show reasoning behind agent decisions" the answer is agent tracing with
> `enableTrace: TRUE`. Know that FailureTrace is the only trace type without ModelInvocationInput.
> TSTALIASID is the test alias. For "provide source attribution in generated answers" the answer is
> Knowledge Bases citations. For "show Foundation Model reasoning to users" the answer is extended
> thinking (Claude).

**Fairness Evaluations (Skill 3.4.2)**

SageMaker Clarify for bias detection:

Pre-training bias metrics (model-agnostic, computed on raw data):

| Metric | What It Measures |
|---|---|
| Class Imbalance (CI) | Imbalance in number of members between facet groups. Range: [-1, +1] |
| Difference in Proportions of Labels (DPL) | Imbalance of positive outcomes between facets. Range: [-1, +1] |
| Kullback-Leibler Divergence (KL) | How much outcome distributions of facets diverge |
| Jensen-Shannon Divergence (JS) | Symmetric measure of divergence between outcome distributions |
| Lp-norm (LP) | Distance between outcome distributions |
| Total Variation Distance (TVD) | Half the L1-norm distance between outcome distributions |
| Kolmogorov-Smirnov (KS) | Maximum divergence between outcomes in facet labels |
| Conditional Demographic Disparity (CDD) | Disproportionately fewer positive outcomes, conditioned on a group variable (addresses Simpson's Paradox) |

Post-training bias metrics require model predictions and detect legal concepts like disparate impact.

Key terminology: facet = attribute column assessed for bias; facet value = specific values that
might be favored/disfavored; positive label = favorable outcome.

SHAP (SHapley Additive exPlanations): computes feature attributions to explain which features
contributed most to a prediction.

Production monitoring: SageMaker Model Monitor + Clarify detects bias drift and feature attribution
drift over time.

Bedrock Model Evaluation for bias:

Built-in datasets for fairness evaluation:

| Task | Dataset | Metric |
|---|---|---|
| Robustness (bias) | BOLD (Bias in Open-ended Language Generation) | Word Error Rate |
| Toxicity | RealToxicityPrompts | Toxicity score |
| Accuracy | TREX | Real World Knowledge score |
| Summarization | Gigaword | BERTScore |
| Q&A | BoolQ, NaturalQuestions, TriviaQA | NLP-F1 |

BOLD is the recommended dataset for measuring bias in open-ended generation tasks. All built-in
datasets are downsampled to 100 prompts each. Custom datasets support up to 1,000 prompts per job.

LLM-as-a-Judge (GA in Bedrock Model Evaluation):

- Quality metrics: correctness, completeness, professional style and tone, coherence.
- Responsible AI metrics: harmfulness, answer refusal.
- Supports Bring Your Own Inference Responses (BYOI) — evaluate any model hosted anywhere.
- Custom metrics via custom judge prompts.
- Can evaluate RAG systems for correctness, completeness, faithfulness, and responsible AI metrics.

Bedrock Prompt Management for A/B testing:

- Create multiple prompt variants — alternative configurations of the same prompt.
- Compare versions side-by-side (differences highlighted).
- Test different versions against the same inputs to measure output quality and bias.
- Create immutable versions for production deployment.

Designing prompts to reduce bias:

- Specify balanced, neutral perspectives in instructions.
- Instruct the model to consider multiple demographic groups.
- Use Chain-of-Thought to make reasoning explicit and auditable.
- Test prompts across demographic groups and compare outputs systematically.
- Use Prompt Management's variant comparison feature for A/B testing.

> **Exam tip:** BOLD is the built-in bias evaluation dataset. SageMaker Clarify pre-training
> metrics are model-agnostic (data only); post-training metrics require predictions. LLM-as-a-Judge
> responsible AI metrics are harmfulness and answer refusal. Know the difference between pre-training
> and post-training bias metrics.

**Policy-Compliant AI Systems (Skill 3.4.3)**

Mapping organizational policies to Bedrock Guardrails:

| Policy Type | Guardrail Filter |
|---|---|
| Content policies | Content filters (set strength levels per category) |
| Prohibited topics | Denied topics (natural language definitions) |
| Language standards | Word filters (profanity + custom lists) |
| Privacy policies | Sensitive information filters (PII types to block/mask) |
| Accuracy requirements | Contextual grounding checks |
| Compliance rules | Automated reasoning checks |

SageMaker Model Cards for documenting limitations:

- Risk rating field (`unknown`, `low`, `medium`, `high`) maps to EU AI Act risk classification.
- Intended uses section records appropriate and inappropriate use cases.
- Evaluation details section records performance metrics with datasets.
- Immutable versioning provides evidence for auditors.
- Can be exported to PDF for stakeholder communication.

Model Cards vs. AI Service Cards:

| Aspect | SageMaker Model Cards | AWS AI Service Cards |
|---|---|---|
| Created by | You (for your models) | AWS (for their services) |
| Purpose | Internal governance/documentation | External transparency to customers |
| Customizable | Yes, full JSON schema | No, read-only AWS documentation |
| Integrated with | SageMaker Model Registry | Published at docs.aws.amazon.com |
| Versioned | Yes, immutable versions | Updated by AWS |

Lambda functions for automated compliance checks:

- Pre-process inputs before sending to models (validation, sanitization).
- Post-process outputs before returning to users (compliance scanning).
- Call `ApplyGuardrail` API within Lambda for custom pipeline guardrail checks.
- Log compliance events to CloudWatch/CloudTrail.
- Trigger alerts via SNS/EventBridge on violations.

### Cross-Cutting Responsible AI Topics

AWS Responsible AI dimensions (eight pillars from the Well-Architected Generative AI Lens):

1. **Fairness** — not discriminating; considering impacts on different stakeholder groups.
2. **Explainability** — understanding and evaluating system outputs.
3. **Privacy and Security** — appropriately obtaining, using, and protecting data and models.
4. **Safety** — reducing harmful output and misuse; operating within defined scope.
5. **Controllability** — mechanisms to monitor and steer AI system behavior.
6. **Veracity and Robustness** — correct outputs even with unexpected/adversarial inputs.
7. **Governance** — best practices in the AI supply chain.
8. **Transparency** — enabling stakeholders to make informed choices about AI engagement.

Human in the loop — Amazon Augmented AI (A2I):

- Integrates human review into ML workflows.
- Built-in task types: Textract key-value extraction, Rekognition image moderation.
- Custom task types: any ML workflow via `StartHumanLoop` in the A2I Runtime API.
- Work teams: Mechanical Turk, vendor-managed, or private workforce.
- Conditions for review: confidence threshold below a specified value triggers human review.
- Results stored in S3; notifications via CloudWatch Events.
- GenAI integration: review low-confidence Foundation Model outputs, audit responses for quality
  and bias, build feedback loops, validate RAG answers against sources.

Relationship between Guardrails, Model Cards, and AI Service Cards:

| Tool | Scope | Type | When Used |
|---|---|---|---|
| Bedrock Guardrails | Runtime enforcement | Active controls | Applied at inference time to filter/block content |
| SageMaker Model Cards | Your models | Documentation | Throughout model lifecycle for governance |
| AWS AI Service Cards | AWS services | Transparency docs | Before/during service adoption for due diligence |

Together they address: transparency (AI Service Cards + Model Cards), safety and controllability
(Guardrails), and governance (all three).

Transparency requirements mapped to AWS services:

| Requirement | AWS Service/Feature |
|---|---|
| Show reasoning behind FM decisions | Extended thinking (Claude), Agent tracing |
| Cite sources in generated answers | Bedrock Knowledge Bases citations |
| Document model limitations | SageMaker Model Cards, AI Service Cards |
| Track decisions across pipeline | Prompt Flows tracing, Agent tracing |
| Monitor model performance | CloudWatch, SageMaker Model Monitor |
| Detect guardrail-blocked content | GuardrailTrace, invocation logs |
| Explain individual predictions | SageMaker Clarify SHAP values |
| Invisible watermarking | Amazon Titan Image Generator watermarks |

Bedrock data privacy commitments:

- Does NOT use customer data to train Foundation Models.
- Does NOT store or log prompts/completions (unless you enable invocation logging).
- Model providers have NO access to customer data.
- Mantle inference engine implements Zero Operator Access (ZOA) design.
- Encrypted in transit (TLS 1.2) and at rest (AWS-owned or customer managed KMS keys).

> **Exam tip:** Know the eight Responsible AI dimensions. For "human review of low-confidence
> outputs" the answer is Amazon A2I. For "document model limitations for regulatory compliance"
> the answer is SageMaker Model Cards. For "understand AWS service limitations before adoption"
> the answer is AWS AI Service Cards.

## Domain 3 Quick-Reference: Service-to-Task Mapping

| Service | Primary Task(s) | Key Feature for This Domain |
|---|---|---|
| Amazon Bedrock Guardrails | 3.1, 3.2, 3.3, 3.4 | Content filters, denied topics, PII filters, grounding checks, prompt attack detection |
| Amazon Comprehend | 3.1, 3.2 | Toxicity detection, PII detection/redaction, prompt safety classifier |
| Amazon Macie | 3.2 | PII discovery in S3 |
| AWS Lake Formation | 3.2 | Column/row/cell-level data access control |
| AWS KMS | 3.2 | Customer managed encryption keys for Bedrock resources |
| AWS PrivateLink / VPC Endpoints | 3.2 | Network isolation for Bedrock |
| AWS CloudTrail | 3.3 | Audit logging of all Bedrock API calls |
| CloudWatch / CloudWatch Logs | 3.1, 3.3, 3.4 | Model invocation logging, runtime metrics, alarms, dashboards |
| SageMaker Model Cards | 3.3, 3.4 | Model documentation, risk ratings, regulatory compliance |
| SageMaker Clarify | 3.3, 3.4 | Bias detection (pre/post-training), SHAP explanations, bias drift monitoring |
| SageMaker Model Monitor | 3.3 | Data quality, model quality, bias drift, feature attribution drift monitoring |
| AWS Glue Data Catalog | 3.3 | Data source registration, lineage tracking, metadata management |
| Bedrock Knowledge Bases | 3.1, 3.3, 3.4 | RAG grounding, citations/attribution, text-to-SQL |
| Bedrock Model Evaluation | 3.1, 3.4 | Toxicity evaluation, bias evaluation (BOLD), LLM-as-a-Judge |
| Amazon A2I | 3.4 | Human-in-the-loop review workflows |
| AWS Service Catalog | 3.3 | Approved GenAI product portfolios with governance controls |
| SCPs (Organizations) | 3.3 | Maximum permission boundaries for Bedrock across accounts |
| API Gateway / WAF | 3.1 | Rate limiting, input validation, API-level security |
| AWS AI Service Cards | 3.3, 3.4 | AWS-published transparency docs for managed AI services |
