# Domain 5: Testing, Validation, and Troubleshooting

**Exam Weight: 11% — the smallest domain on the exam**

This domain covers two task areas: implementing evaluation systems for GenAI (Task 5.1 with nine
skills) and troubleshooting GenAI applications (Task 5.2 with five skills). Despite its lower
weight, this domain is uniquely cross-cutting — it requires fluency with services and concepts
from every other domain.

## Task 5.1 — Implement Evaluation Systems for GenAI

### Key Concepts

**Comprehensive Assessment Frameworks (Skill 5.1.1)**

Traditional ML evaluation metrics (accuracy, precision, recall, F1) do not capture the quality
dimensions of generative outputs. FM evaluation requires metrics across four categories:

| Category | Metrics |
|---|---|
| Quality | Correctness, completeness, helpfulness, logical coherence, relevance, following instructions |
| Faithfulness | Grounding to source material, hallucination detection, citation accuracy |
| Style | Professional tone, fluency, formatting appropriateness |
| Responsible AI | Harmfulness, stereotyping, refusal behavior |

Traditional NLP overlap metrics are still relevant as baselines but insufficient alone:

| Metric | What It Measures | Limitation for GenAI |
|---|---|---|
| ROUGE | N-gram overlap between generated and reference text | Penalizes valid paraphrases |
| BLEU | Precision of n-gram overlap (machine translation) | Same — punishes diverse but correct outputs |
| BERTScore | Semantic similarity using contextual embeddings | Better than lexical metrics but does not catch factual errors |

For GenAI, prefer **LLM-as-a-Judge** or **human evaluation** over lexical metrics, because
generative models produce valid responses that differ significantly in wording from reference
answers.

> **Exam tip:** If a question asks about evaluating FM outputs "beyond traditional ML evaluation,"
> the answer involves LLM-as-a-Judge metrics (correctness, completeness, faithfulness) rather
> than ROUGE/BLEU scores.

**Systematic Model Evaluation with Bedrock (Skill 5.1.2)**

Amazon Bedrock provides three evaluation methods:

| Method | How It Works | Best For |
|---|---|---|
| Programmatic (automatic) | Predefined NLP metrics (accuracy, robustness, toxicity) against curated datasets | Quick baseline comparisons |
| Human evaluation | Bring your own dataset; define custom metrics; use your team or AWS-managed workers | Subjective quality (brand voice, style, nuance) |
| LLM-as-a-Judge | A judge model (e.g., Claude, Nova Pro) scores the generator model's output using curated or custom metrics | Scalable human-like quality at up to 98% cost savings vs. full human eval |

**Bedrock LLM-as-a-Judge built-in metrics:**

| Metric ID | What It Scores |
|---|---|
| `Builtin.Correctness` | Is the response accurate? Considers ground truth if provided |
| `Builtin.Completeness` | Does the response answer all aspects of the question? |
| `Builtin.Faithfulness` | Does the response contain only information found in the provided context? |
| `Builtin.Helpfulness` | Is the response useful, coherent, and does it anticipate implicit needs? |
| `Builtin.Coherence` | Is the response logically consistent without gaps or contradictions? |
| `Builtin.Relevance` | Is the response relevant to the prompt? |
| `Builtin.FollowingInstructions` | Does the response follow exact directions from the prompt? |
| `Builtin.ProfessionalStyleAndTone` | Is the style appropriate for a professional setting? |
| `Builtin.Harmfulness` | Does the response contain harmful content? |
| `Builtin.Stereotyping` | Does the response contain stereotypes (positive or negative)? |
| `Builtin.Refusal` | Does the response decline to answer or reject the request? |

All metric scores range **0 to 1** (closer to 1 = more of that characteristic).

**Custom metrics** are also supported: you write a judge prompt, define a rating scale, and use
built-in variables to inject data at runtime. Custom metrics enable evaluation against specific
brand voice, categorical rubrics, or domain-specific criteria.

**Supported evaluator models:** Amazon Nova Pro, Anthropic Claude (3.5 Sonnet v1/v2, 3.7 Sonnet,
3 Haiku, 3.5 Haiku), Meta Llama 3.1 70B Instruct, Mistral Large. Cross-Region inference
profiles are supported for all evaluator models.

**Multi-model evaluation and comparison:** Bedrock supports running evaluation jobs across
multiple generator models and comparing results side-by-side. Use this to evaluate
cost-performance tradeoffs:

- **Token efficiency** — compare input/output token counts per response across models.
- **Latency-to-quality ratios** — measure response quality vs. time-to-first-token.
- **Business outcomes** — tie evaluation metrics to downstream KPIs (conversion rate,
  support ticket resolution).

**A/B testing and canary testing:**

| Strategy | Description | Implementation |
|---|---|---|
| A/B testing | Route a percentage of traffic to a new model/prompt variant; compare metrics | AppConfig feature flags, Bedrock Prompt Flows, or application-level routing |
| Canary testing | Deploy a new version to a small fraction of traffic (e.g., 5%); gradually increase if stable | Step Functions, CodeDeploy traffic shifting, or application routing logic |
| Shadow deployment | Run input through both old and new versions; compare outputs without exposing the new version to users | Parallel Lambda invocations; compare results offline |

**Max prompts per evaluation job:** 1,000.

> **Exam tip:** Questions asking "how to identify the optimal model configuration" point to
> Bedrock Model Evaluations with LLM-as-a-Judge, combined with A/B testing or canary releases
> for online validation.

**User-Centered Evaluation Mechanisms (Skill 5.1.3)**

Continuous improvement requires feedback from real users:

| Feedback Type | Examples | Collection Method |
|---|---|---|
| Explicit | Thumbs up/down, star ratings, free-text comments | API Gateway for feedback endpoints; store in DynamoDB |
| Implicit | Copy response, rephrase query, abandon conversation, time on response | Application event logging; CloudWatch custom metrics |
| Annotation workflows | Subject-matter experts label responses for quality, accuracy, relevance | SageMaker Ground Truth, Amazon Augmented AI (A2I), or custom annotation UIs |

**Feedback loop pattern:**
1. Collect feedback signals from users.
2. Aggregate and analyze in CloudWatch or a data warehouse.
3. Triage failures — convert user-reported failures into new test cases.
4. Add new cases to the versioned evaluation dataset.
5. Re-evaluate the system; iterate on prompts, models, or retrieval settings.

This creates a **virtuous cycle** where production usage directly hardens the automated test
suite.

> **Exam tip:** Questions about "continuously improving FM performance based on user experience"
> point to feedback collection interfaces (thumbs up/down), annotation workflows
> (SageMaker Ground Truth / A2I), and feeding failures back into the evaluation dataset.

**Systematic Quality Assurance Processes (Skill 5.1.4)**

GenAI QA requires a multi-layered testing framework:

| Layer | Test Type | What It Validates |
|---|---|---|
| Foundational | Unit tests | Individual deterministic components (data transformation, API clients) — mock FM calls |
| Foundational | Integration tests | Component interactions — data pipeline integrity, tool/API integration, auth flows |
| Foundational | End-to-end tests | Full workflow from user input through response — verify workflow completion and structural correctness, not exact output |
| Quality Assessment | Offline evaluation | LLM-as-a-Judge scoring against versioned evaluation datasets; integrated into CI/CD as quality gates |
| Quality Assessment | Online evaluation | A/B testing and canary releases with real traffic |
| Quality Assessment | Human-in-the-loop | Expert review, feedback collection, annotation workflows |

**Continuous evaluation workflows:**
- Integrate offline evaluation into CI/CD pipelines (CodePipeline/CodeBuild).
- Pipeline fails the build if quality scores drop below predefined thresholds.
- This automatically prevents regressions.

**Regression testing for model outputs:**
- Maintain a **golden dataset** of known-good prompt/response pairs.
- After any change (prompt update, model swap, retrieval config change), re-run the golden
  dataset through the evaluation pipeline.
- Compare scores against baselines; flag any degradation.

**Automated quality gates for deployments:**
- Step Functions orchestrate: build -> unit test -> evaluation -> security scan -> deploy.
- Evaluation stage runs the versioned dataset through LLM-as-a-Judge.
- Only deploy if all quality thresholds pass.

**Key unit testing practice for GenAI:** Mock and stub FM API calls. Unit tests must remain fast
and isolated — they test the deterministic code around the FM, not the FM itself. Test edge cases
for input preprocessing and output parsing logic.

**Key end-to-end testing practice for GenAI:** Do not assert on exact output text. Instead,
verify that the workflow completes, the response is structurally correct (e.g., valid JSON),
and the content is semantically relevant. Handle variable response times with appropriate
timeouts.

> **Exam tip:** "Maintain consistent performance standards" and "quality gates" both point to
> CI/CD-integrated evaluation pipelines that fail builds when LLM-as-a-Judge scores fall below
> thresholds.

**Comprehensive Assessment — RAG Evaluation and LLM-as-a-Judge (Skill 5.1.5)**

**RAG Evaluation in Amazon Bedrock** supports two job types:

| Job Type | What Is Evaluated | Metrics |
|---|---|---|
| Retrieve only | Quality of retrieved chunks from the knowledge base | Context relevance, context coverage (requires ground truth) |
| Retrieve and generate | Retrieved chunks + generated response quality | All retrieval metrics + correctness, completeness, faithfulness, helpfulness, coherence, citation precision, citation coverage, harmfulness, stereotyping, refusal |

**RAG retrieval metrics explained:**

| Metric | Description |
|---|---|
| Context relevance | Are retrieved chunks contextually relevant to the query? (Precision-oriented) |
| Context coverage | Do retrieved chunks cover all information in the ground truth? (Recall-oriented; requires ground truth) |

**RAG generation metrics (in addition to standard LLM-as-a-Judge metrics):**

| Metric | Description |
|---|---|
| Citation precision | How many cited passages are cited correctly? |
| Citation coverage | How well is the response supported by cited passages? (Approximately citation recall) |
| Faithfulness | Does the response avoid hallucination relative to retrieved text? |

**Best practice:** Always use both citation precision and citation coverage together for a
complete view of citation quality.

**Bring Your Own Inference (BYOI):** Bedrock RAG evaluation supports evaluating custom RAG
pipelines — bring your own input-output pairs and retrieved contexts directly, bypassing the
Bedrock Knowledge Base call.

**Bedrock Guardrails integration:** You can incorporate Guardrails directly into RAG evaluation
jobs for more comprehensive testing of safety controls.

**Hallucination detection approaches:**

| Approach | AWS Implementation |
|---|---|
| Contextual grounding checks | Bedrock Guardrails — verify response is grounded in source material and relevant to query |
| Automated Reasoning checks | Bedrock Guardrails — mathematical logic and formal verification; up to 99% verification accuracy |
| Faithfulness scoring | LLM-as-a-Judge `Builtin.Faithfulness` metric |
| Golden dataset comparison | Compare FM responses against known-correct answers; flag deviations |

**Contextual grounding checks** in Bedrock Guardrails use two paradigms:
- **Grounding** — ensures factual accuracy against the source material.
- **Relevance** — ensures the response is relevant to the user query.
Each chunk is independently evaluated; if any chunk passes, the whole response is considered
grounded/relevant. Configurable thresholds control filtering sensitivity.

> **Exam tip:** "Ensure thorough evaluation from multiple perspectives" means combining RAG
> evaluation (retrieval + generation metrics), LLM-as-a-Judge (automated quality), and human
> feedback collection in a single evaluation strategy.

**Retrieval Quality Testing (Skill 5.1.6)**

Evaluate retrieval components independently from generation:

| Dimension | How to Test | Tools |
|---|---|---|
| Relevance scoring | Measure how well retrieved chunks answer the query | Bedrock RAG evaluation (retrieve-only), RAGAS context_relevancy metric |
| Context matching verification | Verify retrieved content matches expected ground truth | Context coverage metric (requires ground truth annotations) |
| Retrieval latency | Measure time from query to retrieved results | CloudWatch custom metrics on Knowledge Base API calls; Application Signals |
| Embedding quality | Compare embedding similarity scores for known-similar and known-dissimilar pairs | Custom benchmark scripts; MTEB leaderboard for model selection |

**RAGAS framework metrics** (open-source, works with Bedrock):
- Context precision, context recall, faithfulness, answer relevancy, answer correctness.

**Testing retrieval configuration changes:** Use Bedrock RAG evaluation's compare feature to
evaluate different Knowledge Base configurations side-by-side (different chunking strategies,
embedding models, vector stores, retrieval settings).

**Agent Performance Frameworks (Skill 5.1.7)**

**Amazon Bedrock AgentCore Evaluations** provides automated assessment of agent performance:

| Evaluation Type | Description |
|---|---|
| Online evaluation | Continuously monitors agent quality using live production traffic; configurable session sampling and percentage-based filtering |
| On-demand evaluation | Targeted assessment of specific agent interactions; useful for testing, investigation, and historical analysis |

**Built-in agent evaluation metrics:**
- **Goal attainment** — did the agent accomplish the user's stated goal?
- **Tool accuracy** — did the agent select the correct tool and extract the right parameters?
- **Custom evaluators** — define domain-specific metrics for agent behavior.

**Agent trace analysis** — Bedrock provides detailed traces for debugging agent behavior:

| Trace Type | What It Shows |
|---|---|
| PreProcessingTrace | Input/output of the pre-processing step (intent classification) |
| OrchestrationTrace | Reasoning steps, tool selection, knowledge base queries |
| PostProcessingTrace | Response formatting and finalization |
| FailureTrace | Reason a step failed |
| GuardrailTrace | Actions taken by Guardrails |
| RoutingClassifierTrace | How the agent classified the request for routing |

**Key agent evaluation dimensions:**
- **Task completion rate** — percentage of user requests fully resolved.
- **Tool usage effectiveness** — correct tool selected, correct parameters extracted, correct
  execution.
- **Reasoning quality** — logical consistency of multi-step reasoning chains.
- **Latency** — end-to-end response time for agent workflows.

AgentCore Evaluations integrates with Strands Agents, LangGraph, and OpenTelemetry/
OpenInference. Traces are stored in CloudWatch Transaction Search and can be evaluated
using the `Evaluate` API.

**Limits:** Up to 1,000 evaluation configurations per region; up to 100 active at a time;
up to 1 million input/output tokens per minute for large regions.

> **Exam tip:** Agent evaluation questions map to Bedrock AgentCore Evaluations for automated
> assessment, and Bedrock agent traces for debugging reasoning paths and tool usage.

**Comprehensive Reporting Systems (Skill 5.1.8)**

Communicate evaluation results to stakeholders:

| Tool | Use Case |
|---|---|
| Bedrock evaluation report card | Console-based visualization of metric histograms and scores per evaluation job |
| Bedrock evaluation compare | Side-by-side comparison of multiple evaluation jobs (different models, configs) |
| Amazon QuickSight | Custom dashboards for business stakeholders; connect to evaluation data in S3 |
| CloudWatch dashboards | Operational dashboards for token usage, latency, error rates, model invocation metrics |
| Amazon Managed Grafana | Advanced visualization with CloudWatch, Prometheus, or custom data sources |
| Automated reports | Step Functions + Lambda to generate periodic evaluation summaries; deliver via SNS/SES |

**Bedrock evaluation report card details:** The console displays a metrics summary card with
histogram charts showing the distribution of scores across all prompts. Each metric includes
an average score (0-1) and a breakdown graph plotting how many responses fall within each
score range.

**Deployment Validation Systems (Skill 5.1.9)**

Ensure reliability during FM updates (model changes, prompt changes, config changes):

| Validation Technique | Description | Implementation |
|---|---|---|
| Synthetic user workflows | Automated test scenarios that simulate real user interactions | CloudWatch Synthetics canaries; Step Functions orchestrated test flows |
| Hallucination rate monitoring | Track faithfulness scores over time; alert on degradation | Bedrock evaluation jobs + CloudWatch alarms on faithfulness metric |
| Semantic drift detection | Compare embedding distributions of responses over time; detect when outputs shift meaning | Custom Lambda comparing response embeddings against baseline vectors |
| Output diffing | Compare new version outputs against baseline for same inputs | Lambda-based diff pipeline; flag significant deviations |
| Response consistency checks | Verify the same prompt produces consistent outputs across multiple invocations | Run golden dataset multiple times; measure variance in LLM-as-a-Judge scores |
| Canary releases | Route small traffic percentage to new version; monitor before full rollout | CodeDeploy traffic shifting; application-level routing |

**GenAIOps CI/CD pipeline for deployment validation:**
1. **Trigger** — commit to main branch or promotion of a new prompt version.
2. **Build** — package application into container images.
3. **Unit test** — test deterministic components (data processing, API clients).
4. **Evaluation** — run versioned dataset through LLM-as-a-Judge; fail if scores below threshold.
5. **Security scan** — automated adversarial testing (prompt injection, PII exposure).
6. **Deploy** — deploy to staging; run canary release or A/B test.

**Versioned artifacts for GenAIOps:** Every deployment is a snapshot of the entire stack — code
version (Git commit), prompt version, model configuration, and evaluation dataset version. This
ensures reproducibility and auditability.

> **Exam tip:** "Maintain reliability during FM updates" = synthetic user workflows + automated
> quality checks (LLM-as-a-Judge in CI/CD) + canary releases + hallucination/drift monitoring.

## Task 5.2 — Troubleshoot GenAI Applications

### Key Concepts

**Content Handling Issues (Skill 5.2.1)**

Context window overflow is one of the most common GenAI failure modes:

| Problem | Symptoms | Resolution |
|---|---|---|
| Context window overflow | `ValidationError`, truncated responses, missing information in output | Reduce input size: prompt compression, context pruning, smaller chunks |
| Token limit exceeded | API error (400) indicating input exceeds model's max token count | Count tokens before sending; use tiktoken or model-specific tokenizer; truncate or split |
| Truncated retrieval context | RAG responses miss important details; incomplete answers | Reduce number of retrieved chunks; use hierarchical chunking (child for precision, parent for context); increase chunk overlap |
| Long conversation history | Multi-turn conversations exceed context window mid-session | Implement sliding window (keep last N turns); summarize older turns; store full history in DynamoDB but send only recent + summary |

**Dynamic chunking strategies for troubleshooting:**
- If responses are incomplete or miss key details, increase chunk size or overlap.
- If responses contain irrelevant information, decrease chunk size for more precise retrieval.
- Switch from fixed-size to semantic or hierarchical chunking if content boundaries are poorly
  aligned with chunk boundaries.

**Prompt design optimization for content handling:**
- Move critical instructions to the beginning of the prompt (models attend more to the start).
- Use explicit delimiters (`<context>`, `<instructions>`) to help the model parse long inputs.
- Compress retrieved context: summarize or extract key sentences before injecting into prompt.
- Set `max_tokens` for the response to reserve space within the context window for input.

> **Exam tip:** Context window overflow questions often have "ValidationError" or "truncated
> response" in the scenario. The answer involves token counting, prompt compression, context
> pruning, or dynamic chunking.

**FM Integration Issues (Skill 5.2.2)**

Common Bedrock API errors and their resolutions:

| Error | HTTP Code | Cause | Resolution |
|---|---|---|---|
| `AccessDeniedException` | 403 | Missing IAM permissions | Verify IAM policy grants `bedrock:InvokeModel` or `bedrock-runtime:*` for the target model |
| `ThrottlingException` | 429 | Exceeded account quotas (tokens/min, requests/min) | Implement exponential backoff with jitter; request quota increase; use Provisioned Throughput or Cross-Region inference |
| `ValidationError` | 400 | Malformed request body, invalid parameters, token limit exceeded | Validate request format against model-specific schema; check parameter ranges; count tokens |
| `ServiceUnavailable` | 503 | Temporary service issue | Exponential backoff with jitter; switch to different Region (Cross-Region inference); use Provisioned Throughput |
| `InternalFailure` | 500 | Server error | Retry with exponential backoff; contact AWS Support if persistent |
| `ResourceNotFound` | 404 | Invalid model ID, endpoint name, or resource identifier | Verify model ID; use `ListFoundationModels` to confirm available models; check model access is enabled |
| `ModelTimeoutException` | — | Model invocation exceeded time limit | Retry with backoff; consider streaming API; reduce input size; use a smaller/faster model |
| Connection timeout/reset | — | Idle connections through NAT Gateway, VPC endpoint, or NLB | Enable TCP keep-alive to prevent idle connection drops |

**Retry and resilience patterns:**

| Pattern | Implementation |
|---|---|
| Exponential backoff with jitter | AWS SDK retry config: `max_attempts`, `mode: standard/adaptive`; custom decorator for additional control |
| Circuit breaker | Step Functions state machine: open circuit after N consecutive failures; route to fallback |
| Fallback model | AppConfig stores primary and fallback model IDs; Lambda switches on 5xx/throttle errors |
| Cross-Region inference | Bedrock inference profiles (Geographic or Global) for automatic regional routing |

**Error logging and request validation:**
- Enable **Bedrock Model Invocation Logging** to CloudWatch Logs and/or S3.
- Log full prompt/response payloads for debugging (text, image, video, embedding data delivery
  configurable independently).
- Use **CloudWatch Logs Insights** to query prompt/response patterns for specific error
  scenarios.
- Use **AWS X-Ray** (Application Signals) to trace end-to-end request flow across Lambda,
  API Gateway, Bedrock, and other services.

**Bedrock runtime metrics available in CloudWatch:**

| Metric | Description |
|---|---|
| `Invocations` | Total model invocations |
| `InvocationLatency` | Time from request to response |
| `InvocationClientErrors` | 4xx errors |
| `InvocationServerErrors` | 5xx errors |
| `InvocationThrottles` | Throttled requests |
| `InputTokenCount` | Tokens in the input |
| `OutputTokenCount` | Tokens in the output |
| `TimeToFirstToken` | Latency to first streaming token |
| `EstimatedTPMQuotaUsage` | Estimated tokens-per-minute quota utilization |

> **Exam tip:** API integration troubleshooting questions typically involve `ThrottlingException`
> (answer: exponential backoff + quota increase + Cross-Region inference), `ValidationError`
> (answer: validate request format + check token limits), or connectivity issues (answer: TCP
> keep-alive + VPC endpoint configuration).

**Prompt Engineering Problems (Skill 5.2.3)**

When FM responses are low-quality, inconsistent, or off-target:

| Problem | Diagnosis | Resolution |
|---|---|---|
| Inconsistent output format | Model sometimes returns JSON, sometimes plain text | Add explicit format instructions; use tool use / function calling for guaranteed JSON; add JSON schema in the prompt |
| Hallucinations | Model generates plausible but incorrect facts | Add "only use information from the provided context" instruction; enable Bedrock Guardrails contextual grounding; use RAG for factual grounding |
| Ignoring instructions | Model doesn't follow specific directions | Move instructions to the beginning of the system prompt; use explicit delimiters; reduce prompt complexity; test with fewer constraints |
| Low relevance | Model responds generically instead of specifically | Add more context; provide few-shot examples; use chain-of-thought prompting |
| Prompt confusion | Model misinterprets ambiguous instructions | Simplify language; break complex prompts into sequential chain; use Bedrock Prompt Flows for multi-step orchestration |
| Regression after changes | Quality drops after a prompt update | Compare outputs from old and new prompt versions using LLM-as-a-Judge; roll back and iterate |

**Prompt testing frameworks:**
- **Bedrock Prompt Management** — version prompts; compare outputs across versions.
- **Bedrock Prompt builder** — console UI for iterative prompt testing.
- **Evaluation datasets** — maintain a golden dataset of prompt/expected-response pairs.
- **CloudWatch alarms** — monitor regression metrics after prompt changes (failure rate,
  unexpected output rate).

**Systematic refinement workflow:**
1. Identify the failure pattern (hallucination, format error, irrelevance).
2. Create test cases that reproduce the failure.
3. Iterate on the prompt (add constraints, examples, delimiters).
4. Run the full evaluation dataset to confirm the fix doesn't regress other cases.
5. Version the new prompt in Bedrock Prompt Management.
6. Deploy via CI/CD with automated quality gate.

> **Exam tip:** "Improve FM response quality and consistency beyond basic prompt adjustments"
> points to prompt testing frameworks, version comparison with LLM-as-a-Judge, and systematic
> refinement workflows — not just rewriting the prompt.

**Retrieval System Issues (Skill 5.2.4)**

Troubleshooting RAG pipeline problems:

| Problem | Diagnosis | Resolution |
|---|---|---|
| Low retrieval relevance | Retrieved chunks don't answer the query | Check embedding model quality; try hybrid search (semantic + keyword); add reranking; adjust `topK` and similarity threshold |
| Embedding quality degradation | Retrieval quality drops over time | Monitor embedding drift; re-embed with updated model; verify chunking consistency |
| Stale data in vector store | Responses contain outdated information | Verify sync job status; implement incremental sync; add EventBridge triggers for real-time updates |
| Vectorization errors | Documents fail to embed or produce zero vectors | Check document format compatibility; validate preprocessing pipeline; review embedding model token limits vs. chunk size |
| Chunking misalignment | Important information split across chunks | Switch to semantic or hierarchical chunking; increase overlap tokens; test different chunk sizes |
| Slow vector search | High retrieval latency | Optimize OpenSearch sharding and index configuration; use approximate nearest-neighbor (HNSW); enable disk-based vector search for cost savings; consider quantization |
| Missing metadata filters | Retrieval returns results from wrong domain/context | Add metadata to documents during ingestion; use metadata filter expressions in `Retrieve`/`RetrieveAndGenerate` API calls |
| Poor reranking results | Reranker doesn't improve relevance | Verify reranker model is appropriate for the domain; check that enough candidates are passed to the reranker (increase initial `topK`) |

**Embedding quality diagnostics:**
- Compare retrieval results for known queries against expected documents.
- Use the MTEB leaderboard to benchmark embedding models for your domain.
- Test multiple vector dimensions (Titan V2: 256/512/1024) — start compact, increase if
  needed.
- Verify the embedding model's max token input >= your chunk size.

**Drift monitoring for retrieval systems:**
- Track retrieval relevance scores over time in CloudWatch.
- Set alarms when average context relevance drops below a threshold.
- Schedule periodic re-evaluation using Bedrock RAG evaluation jobs.
- Monitor vector store index health (OpenSearch cluster metrics, index size, shard balance).

**Vector search performance optimization:**
- **OpenSearch HNSW tuning:** Increase `m` (connections per node) for better recall at the cost
  of memory; increase `ef_search` for better query accuracy at the cost of latency.
- **Quantization:** Use scalar or product quantization to reduce RAM; trades slight accuracy
  for significant cost reduction.
- **Disk-based vector search:** Keep compressed vectors in memory for candidate selection;
  retrieve full-precision from disk for final scoring.
- **OpenSearch auto-optimize:** Automatically evaluates configuration tradeoffs between search
  quality, speed, and cost.

> **Exam tip:** Retrieval troubleshooting questions often describe symptoms like "irrelevant
> results" (answer: hybrid search + reranking + embedding quality check) or "outdated
> information" (answer: incremental sync + real-time change detection + scheduled refresh).

**Prompt Maintenance Issues (Skill 5.2.5)**

Ongoing prompt management and debugging:

| Problem | Diagnosis Tool | Resolution |
|---|---|---|
| Prompt confusion | CloudWatch Logs — analyze prompt/response pairs to identify where the model misinterprets instructions | Simplify prompt structure; add explicit section delimiters; split into prompt chain |
| Format inconsistencies | Schema validation — validate FM output against expected JSON schema | Add strict output format instructions; use tool use for structured output; add Lambda post-processing validation |
| Observability gaps | X-Ray prompt observability pipeline — trace the full request lifecycle to identify where quality degrades | Instrument with X-Ray/Application Signals; add OpenTelemetry GenAI attributes; enable Bedrock model invocation logging |
| Template variable errors | Template testing — verify all variables are correctly populated before sending to the FM | Unit test template rendering; validate variable substitution in CI/CD |
| Cross-model inconsistencies | Same prompt produces different quality across models | Create model-specific prompt variants; use Bedrock Prompt Management to manage variants per model |

**Observability pipeline for prompts:**
- **CloudWatch Logs Insights** — query patterns: search for specific prompt templates, filter
  by error responses, analyze token usage per prompt variant.
- **X-Ray / Application Signals** — end-to-end tracing with GenAI-specific attributes:
  `gen_ai.request.model`, `gen_ai.request.max_tokens`, `gen_ai.request.temperature`,
  `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.response.finish_reasons`.
- **Bedrock Model Invocation Logging** — capture full prompt/response payloads to CloudWatch
  Logs and S3; configure text, image, video, and embedding data delivery independently.
- **CloudWatch GenAI Observability dashboards** — pre-configured views for invocation count,
  latency, token counts by model, error counts, and throttling events.

**Systematic prompt refinement workflow:**
1. Enable model invocation logging to capture all prompt/response data.
2. Use CloudWatch Logs Insights to identify failure patterns.
3. Create targeted test cases for each failure pattern.
4. Iterate on the prompt in Bedrock Prompt builder (console).
5. Version the improved prompt in Bedrock Prompt Management.
6. Run the evaluation dataset to verify the fix; confirm no regressions.
7. Deploy through CI/CD pipeline with automated quality gate.

> **Exam tip:** Prompt maintenance questions mention CloudWatch Logs (for prompt/response analysis),
> X-Ray (for tracing), and schema validation (for format consistency). The correct answer always
> includes both diagnosis tools and a systematic refinement process.

## Important Services Reference for Domain 5

### Amazon Bedrock Evaluations

| Feature | Description |
|---|---|
| Model Evaluation (LLM-as-a-Judge) | Judge model scores generator outputs on 11 built-in metrics; supports custom metrics |
| Model Evaluation (Programmatic) | Predefined NLP metrics (accuracy, robustness, toxicity) |
| Model Evaluation (Human) | Bring your own dataset; define custom metrics; use your team or AWS workers |
| RAG Evaluation (Retrieve only) | Evaluate retrieval quality: context relevance, context coverage |
| RAG Evaluation (Retrieve and generate) | Evaluate both retrieval and generation: all retrieval metrics + 10 generation metrics |
| BYOI (Bring Your Own Inference) | Evaluate custom RAG pipelines by providing your own input-output pairs and contexts |
| Compare feature | Side-by-side comparison of multiple evaluation jobs |
| Custom metrics | Write custom judge prompts with configurable rating scales and dynamic content injection |
| Max prompts per job | 1,000 |

### Amazon Bedrock AgentCore Evaluations

| Feature | Description |
|---|---|
| Online evaluation | Continuous monitoring of live agent traffic; configurable sampling and filtering |
| On-demand evaluation | Targeted assessment of specific traces/spans; useful for debugging and investigation |
| Built-in evaluators | Goal attainment, tool accuracy |
| Custom evaluators | Define domain-specific agent metrics |
| Framework support | Strands Agents, LangGraph, OpenTelemetry/OpenInference |
| Limits | 1,000 eval configs/region; 100 active; 1M tokens/min |

### Amazon Bedrock Guardrails (Evaluation-Related)

| Feature | Role in Testing |
|---|---|
| Contextual grounding checks | Detect and filter hallucinated responses using grounding + relevance scores |
| Automated Reasoning checks | Mathematical/formal verification of factual accuracy; up to 99% accuracy |
| Content filters | Test for harmful, stereotyped, or inappropriate content |
| Integration with RAG evaluation | Incorporate Guardrails into evaluation jobs for comprehensive safety testing |

### Observability Services

| Service | Domain 5 Use Case |
|---|---|
| CloudWatch Metrics | Bedrock runtime metrics: invocations, latency, token counts, errors, throttles |
| CloudWatch Logs | Store and query prompt/response payloads via Logs Insights |
| CloudWatch GenAI Observability | Pre-configured dashboards for model invocations and AgentCore agents |
| CloudWatch Synthetics | Synthetic canaries for automated deployment validation tests |
| CloudWatch Application Signals | Fine-grained metrics at resource level (Model ID, Guardrails ID, KB ID, Agent ID) with GenAI attributes |
| AWS X-Ray | End-to-end request tracing across Lambda, API Gateway, Bedrock |
| Amazon Q Developer | GenAI-specific error pattern recognition for troubleshooting |
| Bedrock Model Invocation Logging | Full prompt/response logging to CloudWatch Logs and S3; configurable per modality |
| Bedrock Agent Traces | Step-by-step reasoning process traces (PreProcessing, Orchestration, PostProcessing, Failure, Guardrail) |

### Supporting Services

| Service | Domain 5 Use Case |
|---|---|
| AWS Step Functions | Orchestrate evaluation workflows, quality gates, canary release logic, circuit breakers |
| AWS Lambda | Custom validation, output schema checks, evaluation scripts, synthetic test drivers |
| Amazon SageMaker Ground Truth | Managed annotation workflows for human evaluation of FM outputs |
| Amazon Augmented AI (A2I) | Human review workflows for FM outputs requiring expert validation |
| AWS CodePipeline / CodeBuild | CI/CD pipelines with integrated evaluation quality gates |
| AWS CodeDeploy | Canary and linear traffic shifting for deployment validation |
| AWS AppConfig | Feature flags for A/B testing and dynamic model/prompt variant routing |
| Amazon DynamoDB | Store feedback data, evaluation results, conversation history for analysis |
| Amazon S3 | Central storage for evaluation datasets, model invocation logs, evaluation reports |
| Amazon QuickSight | Business-facing dashboards for evaluation metrics and trends |

## Exam Patterns and Common Distractors

### Pattern: "How do you evaluate FM output quality beyond traditional ML metrics?"
**Answer:** LLM-as-a-Judge with Bedrock Model Evaluations — use built-in metrics (correctness,
completeness, faithfulness, helpfulness) rather than ROUGE/BLEU. Combine with human evaluation
for subjective quality.

### Pattern: "How do you evaluate a RAG system's retrieval quality?"
**Answer:** Bedrock RAG evaluation (retrieve-only job) with context relevance and context
coverage metrics. Context coverage requires ground truth annotations. For generation quality,
use retrieve-and-generate job with faithfulness and citation precision/coverage metrics.

### Pattern: "How do you detect and prevent hallucinations?"
**Answer:** Bedrock Guardrails contextual grounding checks (grounding + relevance scores),
Automated Reasoning checks (formal verification, up to 99% accuracy), LLM-as-a-Judge
faithfulness metric, and golden dataset comparisons in CI/CD.

### Pattern: "How do you ensure a model update doesn't degrade quality?"
**Answer:** Deployment validation pipeline: run versioned evaluation dataset through
LLM-as-a-Judge as a CI/CD quality gate; fail the build if scores drop below threshold.
Use canary releases to validate with live traffic. Monitor hallucination rates and semantic
drift with CloudWatch alarms.

### Pattern: "How do you troubleshoot ThrottlingException from Bedrock?"
**Answer:** Implement exponential backoff with jitter (AWS SDK retry config). Request quota
increase. Use Cross-Region inference profiles. Consider Provisioned Throughput for high-volume
workloads.

### Pattern: "How do you troubleshoot low-quality RAG responses?"
**Answer:** Diagnose: check retrieval quality separately from generation quality (use
retrieve-only evaluation). Fix retrieval: try hybrid search (semantic + keyword), add
reranking, adjust chunk size/overlap, verify embedding model quality. Fix generation:
improve prompt, add grounding instructions, enable contextual grounding checks.

### Pattern: "How do you debug agent behavior?"
**Answer:** Enable Bedrock agent trace to view step-by-step reasoning (OrchestrationTrace),
tool selection, and knowledge base queries. Use AgentCore Evaluations for automated assessment
of goal attainment and tool accuracy. Use CloudWatch Transaction Search to investigate
specific sessions.

### Pattern: "How do you observe and trace GenAI application performance?"
**Answer:** Enable Bedrock Model Invocation Logging to CloudWatch Logs/S3. Use CloudWatch GenAI
Observability dashboards for metrics. Use X-Ray / Application Signals for end-to-end tracing
with OpenTelemetry GenAI attributes. Use CloudWatch Logs Insights for prompt/response analysis.

### Pattern: "How do you continuously improve prompts in production?"
**Answer:** Systematic prompt refinement: enable model invocation logging -> analyze failures
with CloudWatch Logs Insights -> create test cases -> iterate in Prompt builder -> version in
Prompt Management -> validate with evaluation dataset in CI/CD -> deploy. Collect user
feedback to feed failures back into the evaluation dataset.

### Pattern: "Context window overflow — how do you resolve it?"
**Answer:** Token counting before invocation. Prompt compression (remove redundant context).
Context pruning (recent turns only + summary of older turns). Dynamic chunking (reduce chunk
size or number of retrieved chunks). Set `max_tokens` to reserve space for the response.

## Quick-Reference: GenAI Evaluation Framework

```
Evaluation Dataset (versioned, expanded with real-world failures)
    |
    v
Offline Evaluation (CI/CD quality gate)
    |-- LLM-as-a-Judge (Bedrock Model Evaluation)
    |       |-- Quality: correctness, completeness, helpfulness, coherence
    |       |-- Faithfulness: grounding, hallucination detection
    |       |-- Responsible AI: harmfulness, stereotyping, refusal
    |       |-- Custom: brand voice, domain-specific rubrics
    |
    |-- RAG Evaluation (Bedrock Knowledge Base Evaluation)
    |       |-- Retrieval: context relevance, context coverage
    |       |-- Generation: faithfulness, citation precision, citation coverage
    |
    |-- Agent Evaluation (AgentCore Evaluations)
            |-- Goal attainment, tool accuracy, custom evaluators
    |
    v
Online Evaluation (live traffic)
    |-- A/B testing (AppConfig feature flags)
    |-- Canary releases (5% traffic -> monitor -> scale)
    |-- Shadow deployment (parallel comparison)
    |
    v
Human-in-the-Loop Evaluation
    |-- Explicit feedback (thumbs up/down, ratings)
    |-- Implicit feedback (copy, rephrase, abandon)
    |-- Expert annotation (SageMaker Ground Truth / A2I)
    |
    v
Feedback Loop (failures -> new test cases -> evaluation dataset)
```

## Quick-Reference: Troubleshooting Decision Tree

```
FM Response Issue
    |
    |-- Is it an API error?
    |       |-- 429 ThrottlingException -> Exponential backoff + Cross-Region inference
    |       |-- 400 ValidationError -> Check request format + token limits
    |       |-- 403 AccessDenied -> Check IAM permissions + model access
    |       |-- 503 ServiceUnavailable -> Retry + failover region
    |       |-- Connection timeout -> TCP keep-alive for VPC/NAT
    |
    |-- Is the response incomplete?
    |       |-- Context window overflow -> Token counting + prompt compression
    |       |-- Truncated retrieval -> Adjust chunking + increase overlap
    |       |-- Long conversation -> Sliding window + conversation summarization
    |
    |-- Is the response inaccurate (hallucination)?
    |       |-- Enable Guardrails contextual grounding checks
    |       |-- Add RAG grounding ("use only provided context")
    |       |-- Evaluate faithfulness with LLM-as-a-Judge
    |       |-- Check retrieval quality (retrieve-only evaluation)
    |
    |-- Is the response irrelevant?
    |       |-- Check retrieval: hybrid search + reranking
    |       |-- Improve prompt: add few-shot examples + chain-of-thought
    |       |-- Check embedding model quality (MTEB benchmark)
    |
    |-- Is the format inconsistent?
            |-- Add explicit format instructions + JSON schema
            |-- Use tool use / function calling for structured output
            |-- Add Lambda post-processing validation
```

## Domain 5 Key Numbers

| Item | Value |
|---|---|
| Domain weight | 11% |
| Bedrock evaluation max prompts per job | 1,000 |
| LLM-as-a-Judge metric score range | 0 to 1 |
| Automated Reasoning verification accuracy | Up to 99% |
| LLM-as-a-Judge cost savings vs. human evaluation | Up to 98% |
| AgentCore Evaluations max configs per region | 1,000 |
| AgentCore Evaluations max active configs | 100 |
| AgentCore Evaluations max tokens/min | 1,000,000 |
| Bedrock built-in LLM-as-a-Judge metrics | 11 |
| RAG retrieval-only metrics | 2 (context relevance, context coverage) |
| RAG retrieve-and-generate metrics | 10 (quality + responsible AI + citations) |
