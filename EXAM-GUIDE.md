# AWS Certified Generative AI Developer - Professional (AIP-C01) Exam Guide

## Overview

The AWS Certified Generative AI Developer - Professional (AIP-C01) exam validates a candidate's
ability to effectively integrate Foundation Models into applications and business workflows.
This certification demonstrates practical knowledge of how to implement GenAI solutions into
production environments by using AWS technologies.

### Validated Abilities

- Design and implement solutions using vector stores, RAG, knowledge bases, and other GenAI architectures
- Integrate Foundation Models into applications and business workflows
- Apply prompt engineering and management techniques
- Implement agentic AI solutions
- Optimize GenAI applications for cost, performance, and business value
- Implement security, governance, and Responsible AI practices
- Troubleshoot, monitor, and optimize GenAI applications
- Evaluate Foundation Models for quality and responsibility

## Exam Details

| Attribute | Detail |
|---|---|
| Exam Code | AIP-C01 |
| Question Types | Multiple choice (1 correct / 3 distractors), Multiple response (2+ correct / 5+ options) |
| Scored Questions | 65 |
| Unscored Questions | 10 (not identified on the exam) |
| Total Questions | 75 |
| Score Range | 100 - 1,000 (scaled) |
| Passing Score | 750 |
| Scoring Model | Compensatory (no per-section minimum; only overall score matters) |

## Target Candidate

**Experience:** 2+ years building production-grade applications on AWS or with open-source technologies,
general AI/ML or data engineering experience, and 1 year of hands-on experience implementing GenAI solutions.

### Recommended AWS Knowledge

- AWS compute, storage, and networking services
- AWS security best practices and identity management
- AWS deployment and infrastructure as code (IaC) tools
- AWS monitoring and observability services
- AWS cost optimization principles

### Out of Scope for the Target Candidate

- Model development and training
- Advanced ML techniques
- Data engineering and feature engineering

## Content Domains and Weightings

| Domain | Weight |
|---|---|
| 1. Foundation Model Integration, Data Management, and Compliance | 31% |
| 2. Implementation and Integration | 26% |
| 3. AI Safety, Security, and Governance | 20% |
| 4. Operational Efficiency and Optimization for GenAI Applications | 12% |
| 5. Testing, Validation, and Troubleshooting | 11% |

## Domain 1: Foundation Model Integration, Data Management, and Compliance (31%)

### Task 1.1: Analyze requirements and design GenAI solutions

- **1.1.1** Create comprehensive architectural designs that align with specific business needs and
  technical constraints (appropriate Foundation Models, integration patterns, deployment strategies).
- **1.1.2** Develop technical proof-of-concept implementations to validate feasibility, performance
  characteristics, and business value before full-scale deployment (e.g., Amazon Bedrock).
- **1.1.3** Create standardized technical components to ensure consistent implementation across
  multiple deployment scenarios (AWS Well-Architected Framework, WA Tool Generative AI Lens).

### Task 1.2: Select and configure Foundation Models

- **1.2.1** Assess and choose Foundation Models to ensure optimal alignment with specific business use cases and
  technical requirements (performance benchmarks, capability analysis, limitation evaluation).
- **1.2.2** Create flexible architecture patterns to enable dynamic model selection and provider
  switching without code modifications (Lambda, API Gateway, AWS AppConfig).
- **1.2.3** Design resilient AI systems to ensure continuous operation during service disruptions
  (Step Functions circuit breaker patterns, Bedrock Cross-Region Inference, cross-Region model
  deployment, graceful degradation strategies).
- **1.2.4** Implement Foundation Model customization deployment and lifecycle management (SageMaker AI for
  domain-specific fine-tuned models, parameter-efficient adaptation techniques such as LoRA and
  adapters, SageMaker Model Registry for versioning, automated deployment pipelines, rollback
  strategies, lifecycle management to retire and replace models).

### Task 1.3: Implement data validation and processing pipelines for Foundation Model consumption

- **1.3.1** Create comprehensive data validation workflows to ensure data meets quality standards
  for Foundation Model consumption (AWS Glue Data Quality, SageMaker Data Wrangler, custom Lambda functions,
  CloudWatch metrics).
- **1.3.2** Create data processing workflows to handle complex data types including text, image,
  audio, and tabular data with specialized processing requirements for Foundation Model consumption (Bedrock
  multimodal models, SageMaker Processing, AWS Transcribe, advanced multimodal pipeline
  architectures).
- **1.3.3** Format input data for Foundation Model inference according to model-specific requirements (JSON
  formatting for Bedrock API requests, structured data preparation for SageMaker AI endpoints,
  conversation formatting for dialog-based applications).
- **1.3.4** Enhance input data quality to improve Foundation Model response quality and consistency (Bedrock to
  reformat text, Amazon Comprehend to extract entities, Lambda functions to normalize data).

### Task 1.4: Design and implement vector store solutions

- **1.4.1** Create advanced vector database architectures for Foundation Model augmentation to enable efficient
  semantic retrieval (Bedrock Knowledge Bases for hierarchical organization, OpenSearch Service with
  Neural plugin, RDS with S3 document repositories, DynamoDB with vector databases for metadata and
  embeddings).
- **1.4.2** Develop comprehensive metadata frameworks to improve search precision and context
  awareness for Foundation Model interactions (S3 object metadata for document timestamps, custom attributes for
  authorship, tagging systems for domain classification).
- **1.4.3** Implement high-performance vector database architectures to optimize semantic search
  performance at scale (OpenSearch sharding strategies, multi-index approaches for specialized
  domains, hierarchical indexing techniques).
- **1.4.4** Use AWS services to create integration components to connect with resources (document
  management systems, knowledge bases, internal wikis for comprehensive data integration in GenAI
  applications).
- **1.4.5** Design and deploy data maintenance systems to ensure vector stores contain current and
  accurate information (incremental update mechanisms, real-time change detection systems, automated
  synchronization workflows, scheduled refresh pipelines).

### Task 1.5: Design retrieval mechanisms for Foundation Model augmentation

- **1.5.1** Develop effective document segmentation approaches to optimize retrieval performance
  (Bedrock chunking capabilities, Lambda functions for fixed-size chunking, custom processing for
  hierarchical chunking based on content structure).
- **1.5.2** Select and configure optimal embedding solutions to create efficient vector
  representations for semantic search (Amazon Titan embeddings, evaluating performance
  characteristics of Bedrock embedding models, Lambda functions to batch generate embeddings).
- **1.5.3** Deploy and configure vector search solutions to enable semantic search capabilities
  (OpenSearch Service with vector search, Aurora with pgvector extension, Bedrock Knowledge Bases
  with managed vector store functionality).
- **1.5.4** Create advanced search architectures to improve relevance and accuracy of retrieved
  information (OpenSearch for semantic search, hybrid search combining keywords and vectors,
  Bedrock reranker models).
- **1.5.5** Develop sophisticated query handling systems to improve retrieval effectiveness and
  result quality (Bedrock for query expansion, Lambda functions for query decomposition, Step
  Functions for query transformation).
- **1.5.6** Create consistent access mechanisms to enable seamless integration with Foundation Models (function
  calling interfaces for vector search, Model Context Protocol [MCP] clients for vector queries,
  standardized API patterns for retrieval augmentation).

### Task 1.6: Implement prompt engineering strategies and governance for Foundation Model interactions

- **1.6.1** Create effective model instruction frameworks to control Foundation Model behavior and outputs
  (Bedrock Prompt Management to enforce role definitions, Bedrock Guardrails to enforce responsible
  AI guidelines, template configurations to format responses).
- **1.6.2** Build interactive AI systems to maintain context and improve user interactions with Foundation Models
  (Step Functions for clarification workflows, Amazon Comprehend for intent recognition, DynamoDB
  for conversation history storage).
- **1.6.3** Implement comprehensive prompt management and governance systems to ensure consistency
  and oversight (Bedrock Prompt Management for parameterized templates and approval workflows, S3
  for template repositories, CloudTrail for usage tracking, CloudWatch Logs for access logging).
- **1.6.4** Develop quality assurance systems to ensure prompt effectiveness and reliability
  (Lambda functions to verify expected output, Step Functions to test edge cases, CloudWatch to
  test prompt regression).
- **1.6.5** Enhance Foundation Model performance to refine prompts iteratively and improve response quality
  beyond basic prompting (structured input components, output format specifications, chain-of-thought
  instruction patterns, feedback loops).
- **1.6.6** Design complex prompt systems to handle sophisticated tasks with Foundation Models (Bedrock Prompt
  Flows for sequential prompt chains, conditional branching based on model responses, reusable
  prompt components, integrated pre-processing and post-processing steps).

## Domain 2: Implementation and Integration (26%)

### Task 2.1: Implement agentic AI solutions and tool integrations

- **2.1.1** Develop intelligent autonomous systems with appropriate memory and state management
  capabilities (Strands Agents and AWS Agent Squad for multi-agent systems, MCP for agent-tool
  interactions).
- **2.1.2** Create advanced problem-solving systems to give Foundation Models the ability to break down and solve
  complex problems by following structured reasoning steps (Step Functions to implement ReAct
  patterns and chain-of-thought reasoning approaches).
- **2.1.3** Develop safeguarded AI workflows to ensure controlled Foundation Model behavior (Step Functions for
  stopping conditions, Lambda functions for timeout mechanisms, IAM policies for resource
  boundaries, circuit breakers to mitigate failures).
- **2.1.4** Create sophisticated model coordination systems to optimize performance across multiple
  capabilities (specialized Foundation Models for complex tasks, custom aggregation logic for model ensembles,
  model selection frameworks).
- **2.1.5** Develop collaborative AI systems to enhance Foundation Model capabilities with human expertise (Step
  Functions for review and approval processes, API Gateway for feedback collection mechanisms,
  human augmentation patterns).
- **2.1.6** Implement intelligent tool integrations to extend Foundation Model capabilities and ensure reliable
  tool operations (Strands API for custom behaviors, standardized function definitions, Lambda
  functions for error handling and parameter validation).
- **2.1.7** Develop model extension frameworks to enhance Foundation Model capabilities (Lambda functions for
  stateless MCP servers providing lightweight tool access, ECS for MCP servers providing complex
  tools, MCP client libraries for consistent access patterns).

### Task 2.2: Implement model deployment strategies

- **2.2.1** Deploy Foundation Models based on specific application needs and performance requirements (Lambda
  functions for on-demand invocation, Bedrock provisioned throughput configurations, SageMaker AI
  endpoints for hybrid solutions).
- **2.2.2** Deploy Foundation Model solutions by addressing unique challenges of LLMs that differ from
  traditional ML deployments (container-based deployment patterns optimized for memory requirements,
  GPU utilization, and token processing capacity, specialized model loading strategies).
- **2.2.3** Develop optimized Foundation Model deployment approaches to balance performance and resource
  requirements (selecting appropriate models, using smaller pre-trained models for specific tasks,
  API-based model cascading for routine queries).

### Task 2.3: Design and implement enterprise integration architectures

- **2.3.1** Create enterprise connectivity solutions to seamlessly incorporate Foundation Model capabilities into
  existing enterprise environments (API-based integrations with legacy systems, event-driven
  architectures for loose coupling, data synchronization patterns).
- **2.3.2** Develop integrated AI capabilities to enhance existing applications with GenAI
  functionality (API Gateway for microservice integrations, Lambda functions for webhook handlers,
  EventBridge for event-driven integrations).
- **2.3.3** Create secure access frameworks to ensure appropriate security controls (identity
  federation between Foundation Model services and enterprise systems, role-based access control, least privilege
  API access to Foundation Models).
- **2.3.4** Develop cross-environment AI solutions to ensure data compliance across jurisdictions
  while enabling Foundation Model access (AWS Outposts for on-premises data integration, AWS Wavelength for edge
  deployments, secure routing between cloud and on-premises resources).
- **2.3.5** Implement CI/CD pipelines and GenAI gateway architectures to implement secure and
  compliant consumption patterns (CodePipeline, CodeBuild, automated testing frameworks for
  continuous deployment and testing with security scans and rollback support, centralized
  abstraction layers, observability and control mechanisms).

### Task 2.4: Implement Foundation Model API integrations

- **2.4.1** Create flexible model interaction systems (Bedrock APIs for synchronous requests,
  language-specific AWS SDKs and SQS for asynchronous processing, API Gateway for request
  validation).
- **2.4.2** Develop real-time AI interaction systems to provide immediate feedback from Foundation Model (Bedrock
  streaming APIs for incremental response delivery, WebSockets or server-sent events for real-time
  text generation, API Gateway for chunked transfer encoding).
- **2.4.3** Create resilient Foundation Model systems to ensure reliable operations (AWS SDK for exponential
  backoff, API Gateway for rate limiting, fallback mechanisms for graceful degradation, X-Ray for
  observability across service boundaries).
- **2.4.4** Develop intelligent model routing systems to optimize model selection (application code
  for static routing configurations, Step Functions for dynamic content-based routing, intelligent
  model routing based on metrics, API Gateway with request transformations for routing logic).

### Task 2.5: Implement application integration patterns and development tools

- **2.5.1** Create Foundation Model API interfaces to address the specific requirements of GenAI workloads (API
  Gateway for streaming responses, token limit management, retry strategies for model timeouts).
- **2.5.2** Develop accessible AI interfaces to accelerate adoption and integration (AWS Amplify
  for declarative UI components, OpenAPI specifications for API-first development, Bedrock Prompt
  Flows for no-code workflow builders).
- **2.5.3** Create business system enhancements (Lambda functions for CRM enhancements, Step
  Functions for document processing systems, Amazon Q Business data sources for internal knowledge
  tools, Bedrock Data Automation for automated data processing workflows).
- **2.5.4** Enhance developer productivity to accelerate development workflows for GenAI
  applications (Amazon Q Developer for code generation and refactoring, code suggestions for API
  assistance, AI component testing, performance optimization).
- **2.5.5** Develop advanced GenAI applications to implement sophisticated AI capabilities (Strands
  Agents and AWS Agent Squad for AWS native orchestration, Step Functions for agent design patterns,
  Bedrock for prompt chaining patterns).
- **2.5.6** Improve troubleshooting efficiency for Foundation Model applications (CloudWatch Logs Insights for
  prompt/response analysis, X-Ray for Foundation Model API call tracing, Amazon Q Developer for GenAI-specific
  error pattern recognition).

## Domain 3: AI Safety, Security, and Governance (20%)

### Task 3.1: Implement input and output safety controls

- **3.1.1** Develop comprehensive content safety systems to protect against harmful user inputs to
  Foundation Models (Bedrock guardrails for content filtering, Step Functions and Lambda functions for custom
  moderation workflows, real-time validation mechanisms).
- **3.1.2** Create content safety frameworks to prevent harmful outputs (Bedrock guardrails to
  filter responses, specialized Foundation Model evaluations for content moderation and toxicity detection,
  text-to-SQL transformations to ensure deterministic results).
- **3.1.3** Develop accuracy verification systems to reduce hallucinations in Foundation Model responses (Bedrock
  Knowledge Base for grounding responses and fact-checking, confidence scoring and semantic
  similarity search for verification, JSON Schema to enforce structured outputs).
- **3.1.4** Create defense-in-depth safety systems to provide comprehensive protection against Foundation Model
  misuse (Amazon Comprehend for pre-processing filters, Bedrock for model-based guardrails, Lambda
  functions for post-processing validation, API Gateway for API response filtering).
- **3.1.5** Implement advanced threat detection to protect against adversarial inputs and security
  vulnerabilities (prompt injection and jailbreak detection mechanisms, input sanitization and
  content filters, safety classifiers, automated adversarial testing workflows).

### Task 3.2: Implement data security and privacy controls

- **3.2.1** Develop protected AI environments to ensure comprehensive security for Foundation Model deployments
  (VPC endpoints for network isolation, IAM policies for secure data access patterns, Lake
  Formation for granular data access, CloudWatch for data access monitoring).
- **3.2.2** Develop privacy-preserving systems to protect sensitive information during Foundation Model
  interactions (Amazon Comprehend and Macie for PII detection, Bedrock native data privacy
  features, Bedrock guardrails for output filtering, S3 Lifecycle configurations for data
  retention policies).
- **3.2.3** Create privacy-focused AI systems to protect user privacy while maintaining Foundation Model utility
  (data masking techniques, Amazon Comprehend PII detection, anonymization strategies, Bedrock
  guardrails).

### Task 3.3: Implement AI governance and compliance mechanisms

- **3.3.1** Develop compliance frameworks to ensure regulatory compliance for Foundation Model deployments
  (SageMaker AI for programmatic model cards, AWS Glue for data lineage tracking, metadata tagging
  for data source attribution, CloudWatch Logs for decision logs).
- **3.3.2** Implement data source tracking to maintain traceability in GenAI applications (Glue
  Data Catalog for data source registration, metadata tagging for source attribution in
  Foundation Model-generated content, CloudTrail for audit logging).
- **3.3.3** Create organizational governance systems to ensure consistent oversight of Foundation Model
  implementations (frameworks aligned with organizational policies, regulatory requirements, and
  responsible AI principles).
- **3.3.4** Implement continuous monitoring and advanced governance controls to support safety
  audits and regulatory readiness (automated detection for misuse, drift, and policy violations,
  bias drift monitoring, automated alerting and remediation workflows, token-level redaction,
  response logging, AI output policy filters).

### Task 3.4: Implement responsible AI principles

- **3.4.1** Develop transparent AI systems in Foundation Model outputs (reasoning displays for user-facing
  explanations, CloudWatch for confidence metrics and uncertainty quantification, evidence
  presentation for source attribution, Bedrock agent tracing for reasoning traces).
- **3.4.2** Apply fairness evaluations to ensure unbiased Foundation Model outputs (pre-defined fairness metrics
  in CloudWatch, Bedrock Prompt Management and Prompt Flows for systematic A/B testing, Bedrock
  with LLM-as-a-Judge for automated model evaluations).
- **3.4.3** Develop policy-compliant AI systems to ensure adherence to responsible AI practices
  (Bedrock guardrails based on policy requirements, model cards to document Foundation Model limitations, Lambda
  functions for automated compliance checks).

## Domain 4: Operational Efficiency and Optimization for GenAI Applications (12%)

### Task 4.1: Implement cost optimization and resource efficiency strategies

- **4.1.1** Develop token efficiency systems to reduce Foundation Model costs while maintaining effectiveness
  (token estimation and tracking, context window optimization, response size controls, prompt
  compression, context pruning, response limiting).
- **4.1.2** Create cost-effective model selection frameworks (cost-capability tradeoff evaluation,
  tiered Foundation Model usage based on query complexity, inference cost balancing against response quality,
  price-to-performance ratio measurement, efficient inference patterns).
- **4.1.3** Develop high-performance Foundation Model systems to maximize resource utilization and throughput
  (batching strategies, capacity planning, utilization monitoring, auto-scaling configurations,
  provisioned throughput optimization).
- **4.1.4** Create intelligent caching systems to reduce costs and improve response times (semantic
  caching, result fingerprinting, edge caching, deterministic request hashing, prompt caching).

### Task 4.2: Optimize application performance

- **4.2.1** Create responsive AI systems to address latency-cost tradeoffs and improve UX
  (pre-computation for predictable queries, latency-optimized Bedrock models for time-sensitive
  applications, parallel requests for complex workflows, response streaming, performance
  benchmarking).
- **4.2.2** Enhance retrieval performance to improve relevance and speed of retrieved information
  for Foundation Model context augmentation (index optimization, query preprocessing, hybrid search with custom
  scoring).
- **4.2.3** Implement Foundation Model throughput optimization to address throughput challenges of GenAI
  workloads (token processing optimization, batch inference strategies, concurrent model invocation
  management).
- **4.2.4** Enhance Foundation Model performance to achieve optimal results for specific GenAI use cases
  (model-specific parameter configurations, A/B testing, appropriate temperature and top-k/top-p
  selection).
- **4.2.5** Create efficient resource allocation systems for Foundation Model workloads (capacity planning for
  token processing requirements, utilization monitoring for prompt and completion patterns,
  auto-scaling configurations for GenAI traffic patterns).
- **4.2.6** Optimize Foundation Model system performance for GenAI workflows (API call profiling for
  prompt-completion patterns, vector database query optimization for retrieval augmentation, latency
  reduction techniques specific to LLM inference, efficient service communication patterns).

### Task 4.3: Implement monitoring systems for GenAI applications

- **4.3.1** Create holistic observability systems to provide complete visibility into Foundation Model
  application performance (operational metrics, performance tracing, Foundation Model interaction tracing,
  business impact metrics with custom dashboards).
- **4.3.2** Implement comprehensive GenAI monitoring systems to proactively identify issues and
  evaluate key performance indicators specific to Foundation Model implementations (CloudWatch to track token
  usage, prompt effectiveness, hallucination rates and response quality, anomaly detection for token
  burst patterns and response drift, Bedrock Model Invocation Logs for request/response analysis,
  performance benchmarks, cost anomaly detection).
- **4.3.3** Develop integrated observability solutions to provide actionable insights for Foundation Model
  applications (operational metric dashboards, business impact visualizations, compliance
  monitoring, forensic traceability and audit logging, user interaction tracking, model behavior
  pattern tracking).
- **4.3.4** Create tool performance frameworks to ensure optimal tool operation and utilization for
  Foundation Models (call pattern tracking, performance metric collection, tool calling observability and
  multi-agent coordination tracking, usage baselines for anomaly detection).
- **4.3.5** Create vector store operational management systems to ensure optimal vector store
  operation and reliability (performance monitoring for vector databases, automated index
  optimization routines, data quality validation processes).
- **4.3.6** Develop Foundation Model-specific troubleshooting frameworks to identify unique GenAI failure modes
  (golden datasets for hallucination detection, output diffing for response consistency analysis,
  reasoning path tracing for logical errors, specialized observability pipelines).

## Domain 5: Testing, Validation, and Troubleshooting (11%)

### Task 5.1: Implement evaluation systems for GenAI

- **5.1.1** Develop comprehensive assessment frameworks to evaluate quality and effectiveness of Foundation Model
  outputs beyond traditional ML evaluation (metrics for relevance, factual accuracy, consistency,
  and fluency).
- **5.1.2** Create systematic model evaluation systems to identify optimal configurations (Bedrock
  Model Evaluations, A/B testing and canary testing of Foundation Models, multi-model evaluation,
  cost-performance analysis for token efficiency, latency-to-quality ratios, and business
  outcomes).
- **5.1.3** Develop user-centered evaluation mechanisms to continuously improve Foundation Model performance
  based on user experience (feedback interfaces, rating systems for model outputs, annotation
  workflows to assess response quality).
- **5.1.4** Create systematic quality assurance processes to maintain consistent performance
  standards (continuous evaluation workflows, regression testing for model outputs, automated
  quality gates for deployments).
- **5.1.5** Develop comprehensive assessment systems to ensure thorough evaluation from multiple
  perspectives (RAG evaluation, automated quality assessment with LLM-as-a-Judge techniques, human
  feedback collection interfaces).
- **5.1.6** Implement retrieval quality testing to evaluate and optimize information retrieval
  components (relevance scoring, context matching verification, retrieval latency measurements).
- **5.1.7** Develop agent performance frameworks to ensure agents perform tasks correctly and
  efficiently (task completion rate measurements, tool usage effectiveness evaluations, Bedrock
  Agent evaluations, reasoning quality assessment in multi-step workflows).
- **5.1.8** Create comprehensive reporting systems to communicate performance metrics and insights
  to stakeholders (visualization tools, automated reporting mechanisms, model comparison
  visualizations).
- **5.1.9** Create deployment validation systems to maintain reliability during Foundation Model updates
  (synthetic user workflows, AI-specific output validation for hallucination rates and semantic
  drift, automated quality checks for response consistency).

### Task 5.2: Troubleshoot GenAI applications

- **5.2.1** Resolve content handling issues to ensure necessary information is processed completely
  in Foundation Model interactions (context window overflow diagnostics, dynamic chunking strategies, prompt
  design optimization, truncation-related error analysis).
- **5.2.2** Diagnose and resolve Foundation Model integration issues to identify and fix API integration problems
  specific to GenAI services (error logging, request validation, response analysis).
- **5.2.3** Troubleshoot prompt engineering problems to improve Foundation Model response quality and consistency
  beyond basic prompt adjustments (prompt testing frameworks, version comparison, systematic
  refinement).
- **5.2.4** Troubleshoot retrieval system issues to identify and resolve problems affecting
  information retrieval effectiveness for Foundation Model augmentation (model response relevance analysis,
  embedding quality diagnostics, drift monitoring, vectorization issue resolution, chunking and
  preprocessing remediation, vector search performance optimization).
- **5.2.5** Troubleshoot prompt maintenance issues to continuously improve Foundation Model interaction
  performance (template testing and CloudWatch Logs for prompt confusion diagnosis, X-Ray for
  prompt observability pipelines, schema validation for format inconsistencies, systematic prompt
  refinement workflows).

## Appendix A: Technologies and Concepts

The following technologies and concepts might appear on the exam (non-exhaustive, subject to change):

- Retrieval Augmented Generation (RAG)
- Vector databases and embeddings
- Prompt engineering and management
- Foundation Model integration
- Agentic AI systems
- Responsible AI practices
- Content safety and moderation
- Model evaluation and validation
- Cost optimization for AI workloads
- Performance tuning for AI applications
- Monitoring and observability for AI systems
- Security and governance for AI applications
- API design and integration patterns
- Event-driven architectures
- Serverless computing
- Container orchestration
- Infrastructure as code (IaC)
- CI/CD for AI applications
- Hybrid cloud architectures
- Enterprise system integration

## Appendix B: In-Scope AWS Services and Features

### Analytics

- Amazon Athena
- Amazon EMR
- AWS Glue
- Amazon Kinesis
- Amazon OpenSearch Service
- Amazon QuickSight
- Amazon Managed Streaming for Apache Kafka (Amazon MSK)

### Application Integration

- Amazon AppFlow
- AWS AppConfig
- Amazon EventBridge
- Amazon SNS
- Amazon SQS
- AWS Step Functions

### Compute

- AWS App Runner
- Amazon EC2
- AWS Lambda
- AWS Lambda@Edge
- AWS Outposts
- AWS Wavelength

### Containers

- Amazon ECR
- Amazon ECS
- Amazon EKS
- AWS Fargate

### Customer Engagement

- Amazon Connect

### Database

- Amazon Aurora
- Amazon DocumentDB
- Amazon DynamoDB
- Amazon DynamoDB Streams
- Amazon ElastiCache
- Amazon Neptune
- Amazon RDS

### Developer Tools

- AWS Amplify
- AWS CDK
- AWS CLI
- AWS CloudFormation
- AWS CodeArtifact
- AWS CodeBuild
- AWS CodeDeploy
- AWS CodePipeline
- AWS Tools and SDKs
- AWS X-Ray

### Machine Learning

- Amazon Augmented AI
- Amazon Bedrock
- Amazon Bedrock AgentCore
- Amazon Bedrock Knowledge Bases
- Amazon Bedrock Prompt Management
- Amazon Bedrock Prompt Flows
- Amazon Comprehend
- Amazon Kendra
- Amazon Lex
- Amazon Q Business
- Amazon Q Business Apps
- Amazon Q Developer
- Amazon Rekognition
- Amazon SageMaker AI
- Amazon SageMaker Clarify
- Amazon SageMaker Data Wrangler
- Amazon SageMaker Ground Truth
- Amazon SageMaker JumpStart
- Amazon SageMaker Model Monitor
- Amazon SageMaker Model Registry
- Amazon SageMaker Neo
- Amazon SageMaker Processing
- Amazon SageMaker Unified Studio
- Amazon Textract
- Amazon Titan
- Amazon Transcribe

### Management and Governance

- AWS Auto Scaling
- AWS Chatbot
- AWS CloudTrail
- Amazon CloudWatch
- Amazon CloudWatch Logs
- Amazon CloudWatch Synthetics
- AWS Cost Anomaly Detection
- AWS Cost Explorer
- Amazon Managed Grafana
- AWS Service Catalog
- AWS Systems Manager
- AWS Well-Architected Tool

### Migration and Transfer

- AWS DataSync
- AWS Transfer Family

### Networking and Content Delivery

- Amazon API Gateway
- AWS AppSync
- Amazon CloudFront
- Elastic Load Balancing (ELB)
- AWS Global Accelerator
- AWS PrivateLink
- Amazon Route 53
- Amazon VPC

### Security, Identity, and Compliance

- Amazon Cognito
- AWS Encryption SDK
- IAM
- IAM Access Analyzer
- IAM Identity Center
- AWS KMS
- Amazon Macie
- AWS Secrets Manager
- AWS WAF

### Storage

- Amazon EBS
- Amazon EFS
- Amazon S3
- Amazon S3 Intelligent-Tiering
- Amazon S3 Lifecycle policies
- Amazon S3 Cross-Region Replication

## Appendix C: Service Mentions on the Exam

AWS Certification uses official short names for well-known AWS services on this exam to reduce
reading load. For example, "Amazon Simple Notification Service (Amazon SNS)" appears as
"Amazon SNS". The exam's Help feature contains the full mapping of short names to full names.
Not every abbreviation is fully spelled out; some AWS services have abbreviations that are never
expanded (e.g., Amazon API Gateway, Amazon EMR).
