# AWS Well-Architected Framework: Generative AI Lens

> Study guide synthesized from the official AWS Well-Architected Generative AI Lens
> (Publication date: November 19, 2025). Mapped to the AIP-C01 exam domains for
> targeted study. Source: https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html

## Exam Relevance

The Well-Architected Generative AI Lens is explicitly referenced in the AIP-C01 exam guide
under Task 1.1.3: "Create standardized technical components to ensure consistent implementation
across multiple deployment scenarios (AWS Well-Architected Framework, WA Tool Generative AI Lens)."

Understanding this lens is relevant across all five exam domains:

| Exam Domain | Relevant Pillars |
|---|---|
| D1: Foundation Model Integration, Data Management, and Compliance (31%) | Operational Excellence, Performance Efficiency, Reliability |
| D2: Implementation and Integration (26%) | Operational Excellence, Reliability, Performance Efficiency |
| D3: AI Safety, Security, and Governance (20%) | Security, Operational Excellence |
| D4: Operational Efficiency and Optimization (12%) | Cost Optimization, Performance Efficiency, Sustainability |
| D5: Testing, Validation, and Troubleshooting (11%) | Operational Excellence, Performance Efficiency, Reliability |

## Overview

The AWS Well-Architected Generative AI Lens extends the Well-Architected Framework to address the
unique considerations of generative AI. It covers the entire generative AI lifecycle -- scoping,
model selection, customization, development, deployment, and continuous improvement -- evaluated
against the six Well-Architected pillars: Operational Excellence, Security, Reliability,
Performance Efficiency, Cost Optimization, and Sustainability.

**Scope:** Best practices for generative AI applications using foundation models on Amazon Bedrock,
customer-managed models on Amazon SageMaker AI, and business applications with Amazon Q. Traditional
ML workloads (non-generative) are covered by the separate Machine Learning Lens.

**Intended audience:** Architects, builders, security experts, MLOps engineers, and decision-makers
involved in designing, developing, and operating generative AI applications on AWS.

**Availability:** The lens is available as a custom lens JSON file for import into the
AWS Well-Architected Tool from the public AWS Well-Architected custom lens GitHub repository.

## Design Principles

Six design principles apply across all generative AI workloads:

1. **Design for controlled autonomy:** Implement comprehensive guardrails and boundaries that
   govern how AI systems operate, scale, and interact. Establish clear operational requirements,
   security controls, and failure conditions to keep AI systems within safe, efficient, and
   cost-effective parameters while maintaining reliability.

2. **Implement comprehensive observability:** Monitor and measure specific aspects of your
   generative AI system, from security and performance to cost and environmental impact. Collect
   metrics across every layer -- user feedback, model behavior, resource utilization, and security
   events -- to maintain operational excellence while optimizing system behavior.

3. **Optimize resource efficiency:** Select and configure AI components based on empirical
   requirements rather than assumptions. Right-size models, optimize data operations, and
   implement dynamic scaling to balance performance needs with cost and sustainability goals.

4. **Establish distributed resilience:** Design systems that remain operational despite component
   or regional failures. Implement redundancy, automated recovery mechanisms, and geographic
   distribution of resources for consistent service delivery.

5. **Standardize resource management:** Maintain centralized catalogs and controls for critical
   components like prompts, models, and access permissions. Implement structured management
   systems for security, version control, and cost optimization.

6. **Secure interaction boundaries:** Protect and control data flows and system interfaces.
   Implement least-privilege access, secure communications, input/output sanitization, and
   comprehensive monitoring for system security and integrity.

## Key Definitions

| Term | Definition |
|---|---|
| Agent | An AI system that can perform tasks autonomously and interact with its environment to achieve specific goals |
| Chunking | Breaking up large data files into small, discrete chunks to fit data into a context window |
| Continuous pre-training | Continuously updating a pre-trained model with new data to improve performance and adapt to evolving domains |
| Embedding | Transforms chunks of data into vectors that represent semantic meaning |
| Fine-tuning | Adapting a pre-trained model to a specific task or domain by training on a smaller, task-specific dataset |
| Foundation model | Large language model pre-trained on vast amounts of data, serving as a foundation for downstream tasks |
| GenAIOps / LLMOps | Operational practices for managing the lifecycle of LLMs, including model selection, data prep, deployment, monitoring, and governance |
| Hallucination | When a generative AI model produces outputs that are inconsistent, factually incorrect, or unrelated to the input prompt |
| Indexing | Process of inserting embedded chunks into a vector data store |
| Model card | Document providing key information about an ML model including intended use, training data, performance, and limitations |
| Model customization | Modifying a foundation model using various techniques to control its behavior |
| Model distillation | Creating a smaller, more efficient model that mimics a larger model's behavior |
| Model gateway | An interaction layer offering secure access to the model hub through standardized APIs |
| Model hub | Central repository providing access to enterprise foundation models from first-party, third-party, and open-source providers |
| Model orchestration | Encapsulation of multistep workflows characteristic of generative AI workflows |
| Prompt catalog | Centralized repository for storing, managing, and versioning prompts |
| Provisioned throughput | Amazon Bedrock feature providing higher throughput at fixed cost for predictable workloads |
| Quantization | Reducing precision of model parameters to decrease memory footprint and computational requirements |
| RAG (Retrieval-Augmented Generation) | Augmenting an LLM's output with relevant information retrieved from a document corpus to ground responses and reduce hallucination |
| Tokenization | Breaking input text into smaller units (tokens) as a preprocessing step |
| Vector store | Specialized data store for efficient storage and retrieval of high-dimensional vector embeddings |

## Responsible AI

AWS defines Responsible AI along eight dimensions that are assessed and updated over time:

1. **Fairness:** Considering impacts on different groups of stakeholders. Implement robust testing
   frameworks to detect potential bias and regularly audit outcomes across different segments.

2. **Explainability:** Understanding and evaluating system outputs. Implement interpretability
   techniques and translate complex model decisions into understandable explanations.

3. **Privacy and security:** Appropriately obtaining, using, and protecting data and models.
   Implement sophisticated data governance frameworks including encryption, access controls,
   and data minimization practices.

4. **Safety:** Reducing harmful system output and misuse. Implement comprehensive safety
   frameworks including content filtering, output validation, and clear escalation paths.

5. **Controllability:** Having mechanisms to monitor and steer AI system behavior. Implement
   robust monitoring systems that track performance metrics, user feedback, and system outputs.

6. **Veracity and robustness:** Achieving correct system outputs, even with unexpected or
   adversarial inputs. Implement comprehensive testing frameworks and automated reasoning
   to capture and correct hallucinations.

7. **Governance:** Incorporating best practices into the AI supply chain, including providers
   and deployers. Establish AI governance committees with technical, business, and risk perspectives.

8. **Transparency:** Enabling stakeholders to make informed choices about their engagement
   with an AI system. Clearly communicate when and how AI is being used.

## Generative AI Lifecycle

The generative AI lifecycle consists of six key phases, each evaluated against all six
Well-Architected pillars:

### Phase 1: Scoping

Prioritize understanding the business problem. Define goals, requirements, and use cases.
Key considerations:

- Determine if generative AI is the right approach for the problem
- Assess risks and costs of investment
- Identify model requirements (off-the-shelf vs. custom, single vs. orchestrated models)
- Establish success metrics for model performance evaluation
- Determine technical and organizational feasibility
- Develop a comprehensive risk profile (technology and business risks)
- Create security scoping matrices for different use cases
- Assess data availability and quality for model customization

### Phase 2: Model Selection

Evaluate models based on requirements and use cases. Key factors:

- Modality, size, accuracy, training data, pricing, context window, inference latency
- Compatibility with existing infrastructure
- Data usage policies by hosting providers
- Instance type evaluation for SageMaker AI hosting
- Vector database selection and availability for RAG workloads
- Hosting options: batch inference, real-time inference, or combined inference profiles
- Model routing solutions and model catalogs for flexibility

### Phase 3: Model Customization

Align the model with application goals through iterative refinement:

- **Prompt engineering:** Craft prompts to guide desired outputs; implement template management
- **RAG:** Augment with retrieval from external knowledge bases
- **Fine-tuning:** Train on domain-specific data for improved performance
- **Continuous pre-training:** Update with new domain data
- **Model distillation:** Create smaller efficient models from larger teacher models
- **Human feedback alignment:** Refine behavior based on human input

### Phase 4: Development and Integration

Integrate the model into applications and systems:

- Implement conversational interfaces, prompt catalogs, agents, and knowledge bases
- Connect to databases, data pipelines, and enterprise applications
- Implement guardrails to reduce risks like hallucination
- Optimize for real-time inference performance
- Build APIs for model interaction
- Design user-friendly interfaces
- Validate with automated testing
- Establish monitoring systems

### Phase 5: Deployment

Roll out the solution in a controlled manner:

- Implement CI/CD pipelines using CodePipeline, CodeBuild
- Use IaC tools (AWS CDK, CloudFormation, Terraform) for resource management
- Maintain version control and automated pipelines
- Validate security and privacy requirements
- Enable quick rollbacks through documentation and versioning

### Phase 6: Continuous Improvement

Ongoing monitoring and refinement:

- Track key metrics (accuracy, toxicity, coherence)
- Gather user feedback on quality and usefulness
- Update training data based on feedback
- Experiment with new techniques, algorithms, and architectures
- Regularly reassess and update AI strategy

## Data Architecture

Three primary use cases for data in generative AI, each with distinct architectural requirements:

**Pre-training data:** Petabyte-scale diverse datasets requiring highly scalable infrastructure.
Challenges include data quality across diverse sources, efficient storage/retrieval, and
computational resources for processing. Must address data versioning, privacy protection, and
sustainable long-term practices.

**Fine-tuning / customization data:** Smaller, focused datasets adapted to specific tasks/domains.
Requires flexible architectures for varying data sizes. Challenges include data selection/curation,
quality/relevance, and bias reduction. Must support rapid iteration and careful versioning.

**RAG data:** Dynamic retrieval from external knowledge bases combined with model inference.
Demands low-latency retrieval systems and seamless integration. Must address efficient indexing
of large knowledge bases, real-time retrieval, and up-to-date information.

**Strategic imperatives:**
- Data quality as the foundation (automated validation, cleansing, continuous monitoring)
- Unified data architecture (break down silos, integrate structured and unstructured data)
- Privacy-first approach (differential privacy, federated learning, synthetic data generation)

## Agentic AI

AI agents are autonomous entities capable of perceiving their environment, reasoning, and taking
actions to achieve defined goals. The core of an agentic system is usually an LLM augmented
with retrieval, tools, and memory. Agency exists on a spectrum -- only increase agency when
task complexity requires it.

**Three common agentic patterns:**

1. **LLM-augmented workflows:** Largely deterministic code paths with certain steps augmented
   by LLMs for decision-making. Low degree of agency. Example: document classification and
   routing system using tool calls.

2. **Autonomous agents:** Built around an LLM with retrieval, tools, and memory orchestrated
   in a ReACT (reason and act) loop. The agent is given tools and instructions, then loops
   until given a stop reason. Tools connected via MCP protocol. System prompt defines goal,
   role, and reasoning guidelines.

3. **Hybrid (Plan and Solve):** Combines workflows and autonomous agents with high agency.
   An LLM creates a plan and task breakdown, a queue of tasks is resolved by ReACT agents,
   then another LLM decides if the result is sufficient or needs more tasks. Scales with
   queues, auto-scaling, and asynchronous execution.

## Pillar 1: Operational Excellence

Operational excellence for generative AI focuses on achieving consistent model output quality,
monitoring operational health, maintaining traceability, automating lifecycle management, and
determining when to customize models.

**Principles:**
- Implement comprehensive observability across all layers (application, service, foundation model)
- Automate operational management using IaC and automated lifecycle processes
- Establish operational controls (prompt template management, rate limits, workflow tracing)

### GENOPS01: Model Output Quality

**How do you achieve and verify consistent model output quality?**

#### BP01: Periodically Evaluate Functional Performance (Risk: High)

Implement periodic evaluations using stratified sampling and custom metrics to maintain
performance and reliability. Regularly assess against ground truth data and specific
evaluation criteria.

**Key implementation details:**
- Run ground truth data periodically, applying sampling techniques for monitoring
- Employ stratified sampling (divide data into relevant categories, randomly sample each)
- Periodically update ground truth datasets as inputs and usage evolve
- Address data drift where actual usage diverges from initial ground truth

**AWS services and tools:**
- Amazon Bedrock model evaluation feature (built-in)
- Amazon SageMaker AI (manual evaluations via Studio, automatic evaluations via fmeval library)
- Open-source libraries: fmeval, ragas
- Amazon Bedrock model invocation logging for metadata, requests, and responses
- Amazon CloudWatch for metrics
- AWS Step Functions for workflow automation

**Organization considerations:** AI policy should define minimum performance levels and
validation cadence. Identify a single-threaded workload owner for performance evaluations.
Run evaluations when new candidate models are available or after model customization.

#### BP02: Collect and Monitor User Feedback (Risk: High)

Supplement model evaluation with direct user feedback. Implement continuous feedback loops
(thumbs up/down, ratings) to detect issues early and inform prompt engineering.

**AWS services and tools:**
- Amazon Q Business: analytics dashboard (usage trends, conversations, query trends, feedback),
  PutFeedback API, conversation logging (S3, CloudWatch Logs, or Amazon Data Firehose)
- Amazon Bedrock: S3 for feedback storage, Lambda for processing, EventBridge for triggers
- Amazon DynamoDB for scalable, low-latency feedback storage
- Amazon QuickSight for feedback visualization dashboards
- AWS Step Functions for feedback processing pipelines
- A/B testing for validating improvements

### GENOPS02: Operational Health

**How do you monitor and manage operational health?**

#### BP01: Monitor All Application Layers (Risk: High)

Implement comprehensive monitoring and logging across all layers:

- **Application layer:** Software abstraction above the foundation model
- **Service layer:** Gateway that negotiates prompts and brokers responses (may interact with
  prompt catalog, vector store, or guardrails)
- **Foundation model layer:** Responds back through the service layer; complex workloads may
  navigate knowledge graphs, run prompt flows, or initiate agents

**AWS services and tools:**
- Amazon Bedrock, Amazon Q Business, Amazon OpenSearch Service Serverless (managed monitoring
  integrated with CloudWatch and CloudTrail)
- Amazon SageMaker AI Inference Endpoints (logs to CloudWatch)
- SageMaker AI HyperPod (EKS): one-click observability with Amazon Managed Grafana, NVIDIA
  DCGM metrics, EFA metrics, CloudWatch Container Insights
- AWS X-Ray or Amazon Bedrock Agent tracing for service layer
- Amazon Data Firehose for log ingestion, Amazon Athena for ad-hoc log querying
- Amazon GuardDuty for threat detection

#### BP02: Monitor Foundation Model Metrics (Risk: High)

Set up continuous monitoring and alerting for foundation models covering performance,
security, and cost-efficiency.

**Key metrics to track:**

| Service | Metrics |
|---|---|
| Amazon Bedrock | Invocation counts, latency, InputTokenCount, OutputTokenCount, InvocationThrottles, error rates |
| Amazon SageMaker AI | Invocation counts, latency, error rates, GPU and memory utilization |
| SageMaker AI HyperPod | NVIDIA DCGM (GPU health), EFA (network), system metrics (CPU, memory, disk) |

**Implementation pattern:**
1. Enable model invocation logging (S3 or CloudWatch Logs)
2. Set up CloudWatch dashboards with anomaly detection
3. Create alarms for critical thresholds (elevated latency, high error rates/throttling)
4. Implement EventBridge rules to capture events and trigger SNS/Lambda responses
5. Develop incident response playbooks
6. Establish regular review process

#### BP03: Mitigate Risk of System Overload (Risk: High)

Two primary approaches:

1. **Scale inference serving architecture:** Use Amazon SageMaker AI Inference Components to
   host and scale models independent of underlying infrastructure. Models are treated as primary
   elements, scaling hardware based on CPU/GPU resources and inference load.

2. **Rate limit and throttle managed inference:** Control request processing rates. Amazon
   Bedrock has default quotas for API request rates, token usage, and concurrent invocations.
   Increase throughput via cross-Region inference or provisioned model throughput.

**Implementation patterns:**
- Amazon API Gateway for rate limiting
- Exponential backoff with jitter (AWS SDK built-in retry mechanisms)
- AWS Step Functions for complex retry workflows with circuit breaker patterns
- SageMaker AI HyperPod: Kubernetes resource quotas, horizontal pod autoscaling,
  HyperPod Task Governance with intelligent throttling
- Continuous monitoring and regular load testing

### GENOPS03: Traceability and Auditability

**How do you maintain traceability for models, prompts, and assets?**

#### BP01: Implement Prompt Template Management (Risk: High)

Maintain a versioned prompt template management system for consistent, optimized performance.

**Amazon Bedrock Prompt Management capabilities:**
- Create, edit, version, and share prompts across teams
- Components: prompts, variables, variants, visual builder interface
- Integration into applications by specifying prompts during model inference

**Amazon Bedrock Flows capabilities:**
- Create and manage advanced workflows without writing code
- Visual builder linking foundation models, prompts, agents, knowledge bases
- Supports versioning, rollback, and A/B testing

**Key practices:**
- Version prompts including hyperparameters or ranges
- Test and compare prompt variants
- Capture baseline metrics and validate for deviations
- Establish cross-team collaboration and guidelines

#### BP02: Enable Tracing for Agents and RAG Workflows (Risk: High)

Implement comprehensive tracing for visibility into agent decision-making.

**Amazon Bedrock Agent trace components:**
- **PreProcessingTrace:** How the agent contextualizes and categorizes user input
- **OrchestrationTrace:** How the agent interprets input, invokes action groups, queries
  knowledge bases
- **PostProcessingTrace:** How the agent handles final output
- **FailureTrace:** Reasons for step failures
- **GuardrailTrace:** Actions taken by guardrails

**Amazon AgentCore:**
- Supports agent tracing by default
- Captures and visualizes traces and spans for each workflow step
- Supports OpenTelemetry for integration with CloudWatch, Datadog, LangSmith, Langfuse

**Multi-agent optimization:**
- Use supervisor with routing mode to route information directly to appropriate collaborator
  agents, reducing unnecessary data transfers and latency

### GENOPS04: Lifecycle Management

**How do you automate lifecycle management?**

#### BP01: Automate with Infrastructure as Code (Risk: High)

Use IaC tools for consistent, version-controlled, automated infrastructure deployment.

**Tools:** AWS CDK, AWS CloudFormation, or Terraform for defining and managing infrastructure
resources (Amazon Bedrock, API Gateway, Lambda, data pipelines).

**Key practices:**
- Store IaC templates in Git version control
- Implement CI/CD pipelines using AWS CodePipeline
- Use same templates with different parameters for dev/test/production
- AWS Config for resource configuration tracking
- Service Catalog for standardized resource provisioning
- Regular security audits of IaC templates

#### BP02: Implement GenAIOps (Risk: High)

GenAIOps is a specialized subset of MLOps focusing on operationalizing foundation models.

**Two categories:**

1. **Operationalizing foundation model consumption:** Applications follow traditional DevOps
   patterns but with complex orchestration (RAG, agents). Involves vector database selection,
   indexing pipelines, and retrieval strategies.

2. **Operationalizing foundation model training/tuning (FMOps/LLMOps):** Model selection,
   continuous tuning/training, experiment tracking, central model registry, prompt
   management/evaluation, and deployment.

**AWS services:**
- Amazon SageMaker AI Pipelines (serverless workflow orchestration for MLOps/LLMOps)
- SageMaker AI MLflow or self-managed MLflow for experiment tracking and model cataloging
- Amazon Bedrock for managed RAG (Knowledge Bases), Agents, fine-tuning, continued pre-training
- AWS CodePipeline, CodeBuild, CodeDeploy for CI/CD integration

### GENOPS05: Model Customization

**How do you determine when to customize models?**

#### BP01: Learn When to Customize Models (Risk: High)

Start with the least resource-intensive option and progressively move to more advanced methods:

| Approach | When to Use | Effort |
|---|---|---|
| Prompt engineering | First approach -- well-crafted prompts can often achieve desired results | Low |
| RAG | When the model needs access to external knowledge sources | Medium |
| Fine-tuning | Specific task requiring improved performance, labeled data available, domain-specific language needed | High |
| Continuous pre-training | Domain adaptation with more data than fine-tuning requires | Higher |
| Custom foundation model | No pre-trained models meet requirements, vast proprietary data, need complete control | Highest |

**AWS services:**
- Amazon Bedrock: built-in evaluation tools, managed RAG, agents, fine-tuning, continued pre-training
- Amazon SageMaker AI with HyperPod: distributed training with data and model parallelism
- Amazon OpenSearch Service for vector databases in RAG workflows
- SageMaker AI Model Monitor for ongoing effectiveness tracking

## Pillar 2: Security

Security for generative AI focuses on protecting endpoints, mitigating harmful outputs,
monitoring/auditing events, securing prompts, controlling excessive agency, and preventing
data poisoning.

**Principles:**
- Implement comprehensive access controls with least privilege across all components
- Secure data and communication flows (private networks, input sanitization, governed data access)
- Monitor and enforce security boundaries across control and data planes
- Control AI system behaviors with guardrails and boundaries

### GENSEC01: Endpoint Security

**How do you manage access to generative AI endpoints?**

#### BP01: Grant Least Privilege Access to Foundation Model Endpoints (Risk: High)

Establish identity-based security for generative AI workloads.

**Key implementation details:**
- Use IAM to limit access to foundation model endpoints to specific IAM roles
- Grant roles least privilege access with session durations and permissions boundaries
- Control model access at the organization layer through service control policies (SCPs),
  resource control policies, session policies, and permission boundaries
- Block or restrict unapproved models by accounts, Regions, or organization

**For SageMaker AI HyperPod:** Two primary roles -- cluster admin users (create, configure,
manage clusters) and data scientist users (run ML workloads, submit jobs). Each role should
have only necessary permissions.

**For Amazon Q Developer:** Subscription model -- confirm user needs and subscription level
matches required access.

#### BP02: Implement Private Network Communication (Risk: High)

Reduce the attack surface by keeping communication off the public internet.

**Key implementation details:**
- AWS PrivateLink for private communication between VPCs and AWS generative AI services
  (Amazon Bedrock, Amazon Q family)
- SageMaker AI inference endpoints deployed in VPC can be made private via PrivateLink
- SageMaker AI HyperPod: deploy clusters within private VPC with appropriate subnets and
  security groups (both EKS and Slurm)
- Extend private network access to supporting infrastructure (vector stores, external tools
  for agents)

#### BP03: Least Privilege Access to Data Stores (Risk: High)

Treat generative AI systems like privileged users when granting data access.

**Key implementation details:**
- Deploy data stores in VPC with strong access controls and zero-trust principles
- Use temporary, least privilege credentials for application access
- Implement guardrails in Amazon Bedrock and SageMaker AI for granular control
- Apply data obfuscation and anonymization for model training data
- Use metadata filtering in vector stores and knowledge bases for granular access control
- Amazon Bedrock Knowledge Bases for data access abstraction
- Sanitize data before ingestion -- remove prohibited material before the model accesses it
- Test with curated prompts to confirm models cannot access sensitive information

#### BP04: Implement Access Monitoring (Risk: High)

Monitor access to generative AI services and foundation models for unauthorized use.

**Key implementation details:**
- AWS CloudTrail for service-level API access monitoring
- Amazon Bedrock model invocation logging (metadata, requests, responses)
- Amazon Q Developer: user activity capture in settings
- Amazon Q Business: log delivery to S3, CloudWatch Logs, or Amazon Data Firehose
- SageMaker AI HyperPod: CloudWatch Logs, CloudWatch Alarms, AWS Security Hub
- Log both application name and end-user for each request
- Agentic workloads require additional logging for each agent called
- Implement guardrails to mask/remove sensitive data before invocations

### GENSEC02: Response Validation

**How do you stop applications from generating harmful, biased, or incorrect responses?**

#### BP01: Implement Guardrails to Mitigate Harmful or Incorrect Responses (Risk: High)

**Guardrail techniques (layered approach):**

| Technique | Description |
|---|---|
| Prompt engineering | Chain-of-thought, logic-of-thought, few-shot prompting to encourage reasoning |
| RAG architectures | Ground responses with factual information from knowledge bases |
| Amazon Bedrock Guardrails | Filter on content, topic, or sensitive information; define fallback behavior |
| Amazon Q Business admin controls | Block certain phrases and topics |
| Human review | Greatest confidence for the most critical responses |
| Model-as-a-judge | Foundation models classify responses and take action |
| Agent flows | Route response review to appropriate process |

**Amazon Bedrock Guardrails configuration options:**
- Content filter sensitivity levels
- Denied topics
- Word filters (allowlists and blocklists)
- Sensitive information filters for PII
- Automated reasoning checks for contextual grounding and response relevance

**Amazon Bedrock Guardrails SDK** is available for custom self-hosted generative AI workloads.

### GENSEC03: Event Monitoring

**How do you monitor and audit events?**

#### BP01: Control Plane and Data Access Monitoring (Risk: High)

Implement comprehensive monitoring across six dimensions:

1. **Performance monitoring:** Response times, latency, throughput, resource utilization, token
   usage, batch processing efficiency, model loading/unloading times
2. **Quality and accuracy monitoring:** Completion rates, response quality scores, content safety,
   hallucination rates, prompt effectiveness
3. **Security monitoring:** Auth attempts, prompt injection exploits, access patterns, rate
   limiting/quota usage, data leakage
4. **Cost monitoring:** Token usage/costs, resource utilization costs, API call volumes,
   storage/transfer costs, model deployment/training costs
5. **Audit trail implementation:** Detailed request/response logs, user interaction logs,
   model version changes, configuration modifications
6. **Compliance monitoring:** Data retention compliance, PII handling, regulatory requirements,
   consent management, geographic data restrictions

### GENSEC04: Prompt Security

**How do you secure system and user prompts?**

#### BP01: Implement a Secure Prompt Catalog (Risk: Medium)

Use Amazon Bedrock Prompt Management for centralized, identity-protected prompt storage.

**Key practices:**
- Secure prompt catalog access with IAM policy documents
- Develop roles with least privilege access to prompt actions (CreatePromptVersion, GetPrompt)
- Enforce separation of duties between prompt engineering and agent workflow testing
- Use automated prompt optimization before cataloging
- Extend CI/CD workflows to incorporate prompt engineering
- Use Amazon Bedrock Flows for testing prompts in orchestrated manner

#### BP02: Sanitize and Validate User Inputs (Risk: High)

Protect against prompt injection and improper content.

**Defense techniques:**
- Add abstraction layer between user prompt and foundation model
- Create context boundaries in prompt templates (explicit instructions to maintain safety constraints)
- Search for suspicious keywords
- Scan user-influenced prompts with a guardrails solution
- Use a separate LLM-as-a-judge to confirm prompt safety
- Set character and token size limits on prompts
- Set rate limits on requests
- Amazon Bedrock Guardrails with allowlists and blocklists
- Continually refine guardrails based on testing results

### GENSEC05: Excessive Agency

**How do you avoid excessive agency for models?**

#### BP01: Least Privilege Access for Agentic Workflows (Risk: High)

Excessive agency is an OWASP Top 10 security threat for LLMs, introduced through agentic
architectures.

**Key implementation details:**
- Develop permissions boundaries on foundation model requests and agentic workflows
- Amazon Bedrock Agents have execution roles; Bedrock Flows have service roles -- both
  need least privilege access
- Create separate developer roles (prompt engineer vs. security engineer)
- Define permission boundaries setting maximum permissions for roles
- Share permission boundaries across models in multi-model/multi-agent scenarios
- Implement user confirmation for agent actions to mitigate excessive agency
- Consider Amazon Verified Permissions for fine-grained authorization

### GENSEC06: Data Poisoning

**How do you detect and remediate data poisoning risks?**

#### BP01: Implement Data Purification Filters (Risk: High)

Data poisoning occurs during pre-training, domain adaptation, and fine-tuning when inappropriate
data is introduced into training. Best handled at the data layer before training begins.

**Techniques:**
- Amazon Transcribe Toxicity Detection for voice data
- Amazon Bedrock Guardrails API (ApplyGuardrail) for text data filtering
- fmeval or SageMaker AI Studio model evaluation for post-training assessment
- Isolate model training environment, infrastructure, and data
- SageMaker AI HyperPod (EKS): containerized data validation services in Kubernetes jobs
- SageMaker AI HyperPod (Slurm): data purification scripts as prerequisite batch jobs
- Log and monitor the filtering process to catch anomalies

## Pillar 3: Reliability

Reliability focuses on managing throughput requirements, maintaining reliable communication,
implementing recovery actions, versioning artifacts, distributing inference, and ensuring
fault-tolerant distributed computation.

**Principles:**
- Design for distributed resilience across multiple Regions and Availability Zones
- Implement robust error management with automated recovery
- Standardize resource management through centralized catalogs
- Architect for intelligent scalability based on actual utilization patterns

### GENREL01: Throughput Management

**How do you determine throughput quotas for foundation models?**

#### BP01: Scale and Balance Foundation Model Throughput (Risk: Medium)

Collect utilization data and implement dynamic scaling to match capacity with demand.

**Key implementation details:**
- Implement request buffering using message queue services to smooth irregular traffic
- Use token bucket algorithms for rate limiting
- Amazon Bedrock Provisioned Throughput for dedicated infrastructure with stable throughput
- Amazon Bedrock cross-Region inference profiles for distributing requests
- SageMaker AI Inference Endpoints with EC2 Auto Scaling groups behind load balancers
- Monitor Provisioned Throughput capacity in Amazon CloudWatch
- Implement retry mechanisms with exponential backoff
- Proactively engage AWS support to increase service quotas

### GENREL02: Network Reliability

**How do you maintain reliable communication among architecture components?**

#### BP01: Implement Redundant Network Connections (Risk: Medium)

Create multiple network paths between critical components.

**Key implementation details:**
- Multi-AZ deployments across at least two Availability Zones
- AWS PrivateLink for secure private communications
- Deploy vector databases (OpenSearch Service Serverless) across multiple AZs with VPC Endpoints
- Extend multi-AZ to agentic workflows (Lambda functions in multi-AZ)
- Multi-Region: VPC peering, AWS Transit Gateway, or Amazon VPC Lattice for cross-Region
  connectivity
- Amazon CloudFront with latency-based routing
- Amazon Route 53 with latency-based routing within VPC
- Combine with Amazon Bedrock cross-Region inference capabilities
- Regular failover drills and failure simulations

### GENREL03: Remediation and Recovery

**How do you implement remediation for loops, retries, and failures?**

#### BP01: Manage Prompt Flows and Recover from Failure (Risk: Medium)

Leverage conditions, loops, and logical structures for reliable prompt flows.

**Key implementation details:**
- Create abstraction layers between users and models for retries, error handling, graceful failures
- Implement logic checks to verify prompts contain expected information
- Verify model responses meet expectations before returning to users
- For external data sources: verify relevant data exists; define fallback actions
- For agentic workflows: classify responses as actionable or inactionable; handle errors
  (error codes, empty responses) with appropriate agent prompts
- Amazon Bedrock Flows with iterator and condition nodes for flow logic

**Error classification system:**
- Categorize failure types with severity levels
- Create response templates for each category
- Implement circuit breaker patterns
- Track recovery success rates

#### BP02: Implement Timeout Mechanisms on Agentic Workflows (Risk: High)

Control long-running unexpected workflows.

**Key implementation details:**
- Set runtime timeouts on external infrastructure (Lambda functions, API endpoints)
- Account for edge cases (cold starts) when setting timeout values
- Connect agentic workflows to event systems (EventBridge) for asynchronous management
- Implement dead letter queues for timed-out processes
- Ensure error handling is transparent to users while maintaining system security
- Monitor timeout frequency and alert on repeated timeouts

### GENREL04: Prompt and Model Management

**How do you maintain versions for prompts, model parameters, and foundation models?**

#### BP01: Implement a Prompt Catalog (Risk: Medium)

Centralized versioned storage for prompts.

**Key practices:**
- Release prompts to live version only after passing appropriate testing
- Enable rollback to previous versions for unexpected/undesirable behavior
- Maintain versioned hyperparameter ranges (temperature, top_p, top_k) paired with prompt versions
- Maintain test results for prompts against several model versions
- Define prompt metadata schema (version, author, purpose)
- Establish naming conventions, tagging, and access control
- Implement approval workflows and audit trails
- Codify governance in AI usage/policy document

**AWS services:** Amazon Bedrock Prompt Management

#### BP02: Implement a Model Catalog (Risk: Low)

Centralized versioned storage for models.

**Key practices:**
- Maintain first-party, third-party, and custom models in centralized catalog
- Record and track model access, versions, and model card information
- Implement model cards (capabilities, limitations, training data, intended use, ethical considerations)
- Establish approval workflows, deployment procedures, deprecation policies
- Maintain performance benchmarks

**AWS services:** Amazon Bedrock API, Amazon Bedrock Marketplace, Amazon Bedrock model catalog

### GENREL05: Distributed Availability

**How do you distribute inference workloads across Regions?**

#### BP01: Load-Balance Inference Requests Across Regions (Risk: Medium)

Use multi-Region deployment for highly available inference.

**Key implementation details:**
- Amazon Bedrock cross-Region inference profiles for routing to nearest available endpoint
- SageMaker AI Inference Endpoints with multi-AZ deployment and auto-scaling
- Health checks and automated failover
- Monitor latency, error rates, and throughput across Regions

#### BP02: Replicate Embedding Data Across Regions (Risk: Medium)

Ensure data availability across all Regions of availability.

**Key implementation details:**
- Amazon S3 cross-Region replication for embedding data
- Amazon OpenSearch Service cross-cluster replication
- AWS Glue data pipelines for synchronization
- Consider data sovereignty requirements and regulatory restrictions
- Amazon S3 Intelligent Tiering for cost-effective storage
- Monitor for replication issues and compliance violations

#### BP03: Verify Agent Capabilities Across Regions (Risk: Medium)

Ensure supporting infrastructure is available wherever agents operate.

**Key implementation details:**
- Deploy APIs across multiple Regions behind CloudFront with latency-based routing
- Amazon Route 53 with latency-based routing for VPC traffic
- Configure model access in all required Regions
- Verify agents can access required resources in all Regions

### GENREL06: Distributed Compute Tasks

**How do you design high-performance distributed computation for successful completion?**

#### BP01: Design for Fault-Tolerance (Risk: High)

Model pre-training, fine-tuning, and distillation require orchestrating dozens to hundreds
of machines running for days, weeks, or months.

**Key implementation details:**
- Amazon SageMaker AI HyperPod: managed infrastructure with automatic fault detection and recovery
  - EKS-based: application-level checkpointing, shared persistent volumes, Kubernetes health checks
  - Slurm-based: auto-resume for zero-touch resiliency, multi-head node support
  - Both: built-in GPU health monitoring (DCGM), EFA health checks, automatic node replacement
- Amazon Bedrock: managed fine-tuning, continued pre-training, model distillation
- AWS Batch: distributed tasks with automatic scaling, retry logic, resource optimization
- Amazon FSx for Lustre for rapid access to large data volumes
- Amazon S3 for checkpoint storage
- CloudWatch for alerts, EventBridge for automated remediation

## Pillar 4: Performance Efficiency

Performance efficiency focuses on establishing evaluation processes, maintaining model
performance, optimizing compute resources, and improving data retrieval performance.

**Principles:**
- Measure and validate performance systematically with comprehensive testing frameworks
- Optimize model and vector operations based on empirical performance requirements
- Leverage managed services for operational efficiency

**Key performance metrics:**
- Inference latency (time to generate a response)
- Throughput (concurrent requests without degradation)
- Response quality (accuracy, relevance, coherence against ground truth)
- Resource utilization (CPU, memory, GPU efficiency)
- Availability (system responsiveness percentage)

### GENPERF01: Performance Evaluation

**How do you capture and improve model performance?**

#### BP01: Define a Ground Truth Dataset (Risk: Medium)

Ground truth data (golden dataset) facilitates model testing for use-case-specific scenarios.

**Key implementation details:**
- Curate sample prompts and expected responses (dozens to thousands depending on complexity)
- Group prompts by variations of the same ask
- Treat as a living artifact that changes with use cases
- For agent workflows: capture ideal prompt flows tracing through various systems
- Golden datasets also useful for fine-tuning and model distillation

**AWS services:** Amazon SageMaker Ground Truth, Amazon S3 (hierarchical storage), AWS Glue
Crawler (data dictionary), Amazon Athena (segment querying), Amazon SageMaker JumpStart

#### BP02: Collect Performance Metrics (Risk: Medium)

Foundation model performance on specific tasks is measured differently depending on the desired
outcome. Inaccurate or toxic responses may be considered under-performing.

**Key implementation details:**
- Traditional metrics (latency, throughput) plus response quality dimensions
- Report metrics, telemetry, and logs to Amazon CloudWatch
- Use OpenLLMetry trace frameworks for detailed tracing
- Benchmark with golden datasets and external benchmarking datasets
- Consult model cards for strengths and weaknesses
- Track experiments with Amazon SageMaker AI with MLflow
- Establish performance thresholds and configure CloudWatch alarms

### GENPERF02: Maintaining Model Performance

**How do you verify acceptable performance levels?**

#### BP01: Load Test Model Endpoints (Risk: Medium)

Determine baseline performance under average and extreme throughput.

**Key implementation details:**
- Develop test suites simulating heaviest expected load against ground truth data
- Amazon Bedrock: review published metrics; benchmark with golden datasets; consider
  provisioned throughput or cross-Region inference for throughput limitations
- Amazon SageMaker AI: test with respect to instance type/size; use quantization, LoRA;
  LMI deep learning containers (request batching, vLLM support)
- Performance optimization: prompt caching (Bedrock), streaming responses, batch inference

#### BP02: Optimize Inference Parameters (Risk: Low)

Configure hyperparameters to improve response quality.

**Key parameters:**
- **Temperature:** Controls randomness (lower = more deterministic, higher = more creative)
- **Top-p (nucleus sampling):** Cumulative probability cutoff for token selection
- **Top-k:** Number of top tokens considered for selection

**Optimization approach:**
- Test highest and lowest values, compare to golden data
- Use Newtonian approach (halving increments) to find ideal values
- LLM-as-a-judge pattern for evaluating performance at scale
- Document recommended hyperparameter ranges by task in AI policy

#### BP03: Select and Customize the Appropriate Model (Risk: Medium)

Choose the right model family and size for your use case.

**Key implementation details:**
- Amazon Bedrock Evaluations / fmeval for testing against evaluation datasets
- Amazon Bedrock Prompt Routing for dynamic routing within a model family when testing is
  inconclusive
- Model customization progression: fine-tuning (small labeled data), continuous pre-training
  (more data, domain adaptation), model distillation (synthetic data from teacher to student)
- Track dominant model family per workload in AI usage document

### GENPERF03: High-Performance Compute Optimization

**How do you optimize computational resources?**

#### BP01: Use Managed Solutions Where Appropriate (Risk: Medium)

**Hosting options (increasing control, increasing operational burden):**

| Option | When to Use |
|---|---|
| Amazon Bedrock | Fully managed; select from models via API; Custom Model Import for own models |
| Amazon SageMaker AI endpoints | More flexibility; managed endpoints with inference-time customization (LoRA) |
| Amazon EC2 | Maximum control; full infrastructure management |

**Training:** Amazon SageMaker AI HyperPod provides managed infrastructure reducing training
time by up to 32% for large clusters. Supports both EKS and Slurm orchestration. HyperPod
recipes provide pre-configured training stacks for NVIDIA H100, A100, and AWS Trainium.

**Observability:** Amazon Managed Grafana and Prometheus for unified monitoring.

### GENPERF04: Vector Store Optimization

**How do you improve data retrieval performance?**

#### BP01: Test Vector Embeddings for Latency and Relevance (Risk: Medium)

Effective chunking and embedding strategies have the greatest effect on performance.

**Chunking strategies:** Fixed-size, hierarchical, or semantic. Amazon Bedrock allows custom
chunking via AWS Lambda functions.

**Search algorithms (Approximate Nearest Neighbor):**

| Algorithm | Strength |
|---|---|
| LSH (Locality-Sensitive Hashing) | Fast indexing |
| HNSW (Hierarchical Navigable Small World) | High accuracy |
| IVF (Inverted File Index) | Balance of speed and accuracy |
| PQ (Product Quantization) | Compact storage |

**Key practices:**
- Organize indices hierarchically (top-level for general, lower-level for detail)
- Implement query expansion using AI-generated context
- Shift from fuzzy matching toward semantic similarity
- Leverage hybrid search approaches (keyword + vector)
- Monitor embedding generation, index construction, query processing, result retrieval
- Maintain data quality through regular assessments and version control

#### BP02: Optimize Vector Sizes (Risk: Low)

Embedding models may support different vector sizes with performance trade-offs.

**Key guidance:**
- Start with compact encoding, increase if warranted
- Higher latency tolerance: larger vectors may offer more accuracy
- Low-latency needs: smaller vectors for faster retrieval
- A well-tuned model with smaller dimensions (256) can outperform a generic model with
  larger dimensions (1024+)
- Check HuggingFace MTEB Leaderboard for benchmarks
- Consider self-hosting open-source embedding models via SageMaker if needed

## Pillar 5: Cost Optimization

Cost optimization focuses on model selection, pricing model selection, cost-aware prompting,
vector store optimization, and agent workflow optimization.

**Principles:**
- Optimize model and inference selection based on actual performance requirements
- Control resource consumption parameters (prompt lengths, response sizes, vector dimensions)
- Design workflow boundaries with clear limits and exit conditions

### GENCOST01: Model Selection

**How do you select the appropriate model to optimize costs?**

#### BP01: Right-Size Model Selection (Risk: Medium)

Foundation model costs vary greatly across providers, families/sizes, and hosting paradigms.

**Cost dimensions:**
- Managed models (Amazon Bedrock): charged by tokens (input/output)
- Self-hosted models (EC2/SageMaker): charged by infrastructure uptime plus storage/network

**Strategy:**
- Start with a smaller model, gradually increase until acceptable performance
- Right-size as an ongoing activity (newer models may be smaller and more cost-effective)
- Decompose workloads and route to different-sized models based on complexity
- Amazon Bedrock Prompt Routing for dynamic routing within a model family
- Use batch inference for non-real-time needs
- Deploy multiple models to single multi-model endpoints where appropriate

### GENCOST02: Pricing Model

**How do you select a cost-effective pricing model?**

#### BP01: Balance Cost and Performance of Inference Paradigms (Risk: Medium)

**Key guidance:**
- Amazon Bedrock Provisioned Throughput: prefer longer commitment terms for better unit costs;
  validate with shorter commitments first
- Compare hosting on SageMaker AI vs. Amazon Bedrock Custom Model Import
- Deploy to the most cost-effective option where performance trade-offs are negligible

#### BP02: Optimize Resource Consumption for Hosting (Risk: Medium)

**Key guidance:**
- Right-size inference endpoints to smallest instance meeting performance goals
- Shut down during off-hours for predictable workloads
- Purchase EC2 Reserved Instances or Savings Plans
- Use SageMaker AI Inference Recommender for instance type evaluation
- SageMaker AI HyperPod Task Governance for dynamic resource allocation based on priority
- HyperPod Flexible Training Plans: set timeline/budget constraints for cost-optimized execution
- Advanced techniques: quantization, LoRA adaptation
- SageMaker AI HyperPod usage reporting for granular GPU/CPU visibility at team/task levels

### GENCOST03: Cost-Aware Prompting

**How do you engineer prompts to optimize cost?**

#### BP01: Optimize Prompt Token Length (Risk: Medium)

Shorter prompts require less compute for inference.

**Key techniques:**
- Rigorous testing to shorten prompts without performance loss
- Use a separate LLM to shorten prompts (Amazon Bedrock Prompt Optimization)
- Zero-shot prompting for common tasks
- Chain-of-thought for reasoning tasks
- Least-to-most for complex problem decomposition

#### BP02: Control Model Response Length (Risk: Medium)

Control response sizes to reduce costs.

**Key techniques:**
- Set response length hyperparameters (max tokens)
- Add prompt instructions encouraging succinctness
- For deterministic scenarios: instruct model to return keys (True/False) instead of
  full-text responses, reducing tokens and increasing determinism

#### BP03: Implement Prompt Caching (Risk: Medium)

Cache frequently used prompt portions to reduce inference costs and latency.

**Amazon Bedrock prompt caching details:**
- Cached tokens charged at reduced rate
- Tokens written to cache may be charged at higher rate
- Uncached tokens at standard rate
- Model-specific minimum/maximum token counts (e.g., Claude 3.7 Sonnet requires minimum
  1,024 tokens per checkpoint)
- Five-minute TTL that resets with each hit

**Best for:** Workloads with long, repeated contexts (e.g., chatbot where users upload
documents and ask questions -- cache the document content).

#### BP04: Annotate User Input for Cost-Aware Content Filtering (Risk: Medium)

Use input tags to selectively apply content filtering only to user-provided content,
avoiding unnecessary processing of system prompts and trusted content.

**Pattern:** XML-style tags with unique random suffix per request to reduce prompt injection:
```
<amazon-bedrock-guardrails-guardContent_xyz>
[Content to be filtered]
</amazon-bedrock-guardrails-guardContent_xyz>
```

**Tag:** User queries, current conversation turns, new/unverified content.
**Leave untagged:** System prompts, verified search results, historical context, trusted content.

### GENCOST04: Vector Store Costs

**How do you optimize vector stores for cost?**

#### BP01: Reduce Vector Length on Embedded Tokens (Risk: Medium)

Smaller vector sizes reduce embedding costs and database computation.

**Key guidance:**
- Use smallest vector length supported that meets quality requirements
- Smaller vectors = fewer tokens = reduced embedding cost
- Consider compressed vector types where supported
- May need to modify chunk size or introduce overlapping chunks
- Performance trade-off: test retrieval quality with smaller vectors

### GENCOST05: Agent Workflow Costs

**How do you optimize agent workflows for cost?**

#### BP01: Create Stopping Conditions (Risk: High)

Agentic workflows can run indefinitely, incurring unbounded costs.

**Key implementation details:**
- Estimate maximum time needed for agent completion (model response + tool execution + network latency)
- Implement timeout mechanisms (Amazon Bedrock Agent timeout, application layer)
- Set timeouts on external tools (Lambda functions, API endpoints)
- Set token limits on model responses
- Evaluate asynchronous workflows for ability to interrupt/halt long-running events
- Ensure prompts handle timeout responses gracefully

## Pillar 6: Sustainability

Sustainability focuses on minimizing computational resources for training, customization,
hosting, data processing, and storage while leveraging model efficiency techniques and
serverless architectures.

**Principles:**
- Identify if generative AI is the right solution (simpler approaches may suffice)
- Design for environmental efficiency (right-sized models, optimized data operations)
- Implement dynamic resource optimization (auto-scaling, serverless architectures)

### GENSUS01: Energy-Efficient Infrastructure

**How do you minimize computational resources for training, customizing, and hosting?**

#### BP01: Implement Auto Scaling and Serverless Architectures (Risk: Medium)

Provision and consume resources only when needed.

**Key implementation details:**
- Amazon Bedrock and Amazon Q are fully managed (AWS handles infrastructure and scaling)
- SageMaker AI Inference Recommender for automated load testing and optimal instance selection
- Amazon EC2 Inferentia instances for highest compute power per watt
- SageMaker AI HyperPod for managed infrastructure with built-in scaling
- Scale self-hosted models to zero when not in use
- Configure idle timeout for SageMaker notebooks
- AWS Customer Carbon Footprint Tool for tracking environmental impact

#### BP02: Use Efficient Model Customization Services (Risk: Medium)

Maximize efficiency through distributed training and parameter-efficient fine-tuning.

**Key techniques:**
- Amazon Bedrock managed fine-tuning and continued pre-training
- SageMaker AI HyperPod with AWS Trainium instances for reduced energy consumption
- Parameter-Efficient Fine Tuning (PEFT) like LoRA to reduce parameters needing updates
- Managed spot training using spare EC2 capacity (with checkpointing)
- SageMaker AI Debugger for detecting/stopping problematic training jobs early

### GENSUS02: Sustainable Data Processing and Storage

**How do you optimize data processing and storage to minimize energy consumption?**

#### BP01: Optimize Data Processing and Storage (Risk: Medium)

**Key implementation details:**
- Amazon S3 Intelligent-Tiering for automatic cost-effective storage class transitions
- S3 Lifecycle policies for data transitions and deletion
- Columnar formats (Apache Parquet) with compression to reduce data transfer and processing
- Amazon Athena for serverless queries directly on S3
- AWS Glue for serverless ETL (runs only when needed)
- AWS Lambda for event-driven serverless computing
- Amazon EMR with auto-scaling for large batch processing
- SageMaker AI HyperPod: differentiated training SLAs (production gets consistent resources,
  development gets longer completion windows, flexible training plans with cost-efficient capacity blocks)
- Monitor with AWS Cost Explorer, Trusted Advisor, CloudWatch metrics

### GENSUS03: Energy-Efficient Models

**How do you maintain model efficiency and resource optimization?**

#### BP01: Leverage Smaller Models and Optimized Inference Techniques (Risk: Medium)

Implement model optimization to reduce resource consumption while meeting performance goals.

**Key techniques:**

| Technique | Description |
|---|---|
| Quantization | Reducing precision of model weights/activations; decreases model size, speeds up inference |
| Pruning | Removing redundant/unnecessary parameters for more compact models |
| Efficient architectures | Fine-tune smaller models for specific use cases instead of using large general-purpose models |
| Model distillation (Amazon Bedrock) | Train smaller model to mimic a larger model; similar performance with fewer resources |
| SageMaker AI inference optimization | Apply quantization, speculative decoding, LoRA; evaluate for latency, throughput, price |

## Quick Reference: All Best Practices by Risk Level

### High Risk (must implement)

| ID | Best Practice | Pillar |
|---|---|---|
| GENOPS01-BP01 | Periodically evaluate functional performance | Operational Excellence |
| GENOPS01-BP02 | Collect and monitor user feedback | Operational Excellence |
| GENOPS02-BP01 | Monitor all application layers | Operational Excellence |
| GENOPS02-BP02 | Monitor foundation model metrics | Operational Excellence |
| GENOPS02-BP03 | Mitigate risk of system overload | Operational Excellence |
| GENOPS03-BP01 | Implement prompt template management | Operational Excellence |
| GENOPS03-BP02 | Enable tracing for agents and RAG workflows | Operational Excellence |
| GENOPS04-BP01 | Automate with IaC | Operational Excellence |
| GENOPS04-BP02 | Implement GenAIOps | Operational Excellence |
| GENOPS05-BP01 | Learn when to customize models | Operational Excellence |
| GENSEC01-BP01 | Grant least privilege access to endpoints | Security |
| GENSEC01-BP02 | Implement private network communication | Security |
| GENSEC01-BP03 | Least privilege access to data stores | Security |
| GENSEC01-BP04 | Implement access monitoring | Security |
| GENSEC02-BP01 | Implement guardrails for harmful/incorrect responses | Security |
| GENSEC03-BP01 | Control plane and data access monitoring | Security |
| GENSEC04-BP02 | Sanitize and validate user inputs | Security |
| GENSEC05-BP01 | Least privilege access for agentic workflows | Security |
| GENSEC06-BP01 | Implement data purification filters | Security |
| GENREL03-BP02 | Implement timeout mechanisms on agentic workflows | Reliability |
| GENREL06-BP01 | Design for fault-tolerance in distributed compute | Reliability |
| GENCOST05-BP01 | Create stopping conditions for agent workflows | Cost Optimization |

### Medium Risk (should implement)

| ID | Best Practice | Pillar |
|---|---|---|
| GENSEC04-BP01 | Implement a secure prompt catalog | Security |
| GENREL01-BP01 | Scale and balance foundation model throughput | Reliability |
| GENREL02-BP01 | Implement redundant network connections | Reliability |
| GENREL03-BP01 | Manage prompt flows and recover from failure | Reliability |
| GENREL04-BP01 | Implement a prompt catalog | Reliability |
| GENREL05-BP01 | Load-balance inference across Regions | Reliability |
| GENREL05-BP02 | Replicate embedding data across Regions | Reliability |
| GENREL05-BP03 | Verify agent capabilities across Regions | Reliability |
| GENPERF01-BP01 | Define a ground truth dataset | Performance Efficiency |
| GENPERF01-BP02 | Collect performance metrics | Performance Efficiency |
| GENPERF02-BP01 | Load test model endpoints | Performance Efficiency |
| GENPERF02-BP03 | Select and customize appropriate model | Performance Efficiency |
| GENPERF03-BP01 | Use managed solutions where appropriate | Performance Efficiency |
| GENPERF04-BP01 | Test vector embeddings for latency and relevance | Performance Efficiency |
| GENCOST01-BP01 | Right-size model selection | Cost Optimization |
| GENCOST02-BP01 | Balance cost and performance of inference | Cost Optimization |
| GENCOST02-BP02 | Optimize resource consumption for hosting | Cost Optimization |
| GENCOST03-BP01 | Optimize prompt token length | Cost Optimization |
| GENCOST03-BP02 | Control model response length | Cost Optimization |
| GENCOST03-BP03 | Implement prompt caching | Cost Optimization |
| GENCOST03-BP04 | Annotate user input for cost-aware filtering | Cost Optimization |
| GENCOST04-BP01 | Reduce vector length on embedded tokens | Cost Optimization |
| GENSUS01-BP01 | Implement auto scaling and serverless architectures | Sustainability |
| GENSUS01-BP02 | Use efficient model customization services | Sustainability |
| GENSUS02-BP01 | Optimize data processing and storage | Sustainability |
| GENSUS03-BP01 | Leverage smaller models and optimized inference | Sustainability |

### Low Risk (consider implementing)

| ID | Best Practice | Pillar |
|---|---|---|
| GENREL04-BP02 | Implement a model catalog | Reliability |
| GENPERF02-BP02 | Optimize inference parameters | Performance Efficiency |
| GENPERF04-BP02 | Optimize vector sizes | Performance Efficiency |

## AWS Services Cross-Reference

The following table maps key AWS services to the Well-Architected GenAI Lens pillars
where they are most heavily referenced:

| AWS Service | OE | SEC | REL | PERF | COST | SUS |
|---|---|---|---|---|---|---|
| Amazon Bedrock | X | X | X | X | X | X |
| Amazon Bedrock Guardrails | X | X | | | X | |
| Amazon Bedrock Prompt Management | X | X | X | | X | |
| Amazon Bedrock Flows | X | | X | | | |
| Amazon Bedrock Knowledge Bases | | X | | | | |
| Amazon Bedrock Agents | | X | X | | X | |
| Amazon AgentCore | X | | | | | |
| Amazon SageMaker AI | X | X | X | X | X | X |
| SageMaker AI HyperPod | X | X | X | X | X | X |
| SageMaker AI Model Monitor | X | | | X | | |
| SageMaker AI MLflow | X | | | X | | |
| Amazon Q Business | X | X | | | | |
| Amazon Q Developer | | X | | | | |
| Amazon CloudWatch | X | X | X | X | | X |
| AWS CloudTrail | X | X | | | | |
| Amazon EventBridge | X | | X | | | |
| AWS Step Functions | X | | | | | |
| AWS Lambda | X | | X | X | | X |
| Amazon API Gateway | X | | | | | |
| AWS IAM | | X | | | | |
| AWS PrivateLink | | X | X | | | |
| Amazon OpenSearch Service | | X | X | X | X | |
| Amazon S3 | X | X | X | X | | X |
| AWS CDK / CloudFormation | X | | | | | |
| AWS CodePipeline / CodeBuild | X | | | | | |
| Amazon Route 53 | | | X | | | |
| Amazon CloudFront | | | X | | | |
| Amazon DynamoDB | X | | | | | |
| Amazon Athena | X | | | X | | X |
| AWS Glue | | | X | X | | X |
| Amazon Data Firehose | X | X | | | | |
| QuickSight | X | X | | | | |
| EC2 Inferentia / Trainium | | | | X | | X |
| Amazon FSx for Lustre | | | X | | | |
| Amazon Verified Permissions | | X | | | | |
| AWS Batch | | | X | | | X |
| SageMaker AI Inference Recommender | | | | | X | X |
