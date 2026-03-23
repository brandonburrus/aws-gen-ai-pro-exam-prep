# Amazon SageMaker AI Ecosystem -- Comprehensive Study Guide (AIP-C01)

The Amazon SageMaker AI ecosystem spans model training, deployment, monitoring, governance, and data preparation. While Bedrock is the primary "fully managed GenAI" service on the exam, SageMaker appears whenever you need **full control** over models, training infrastructure, custom deployment, or MLOps workflows. This guide covers every in-scope SageMaker sub-service for the AIP-C01 exam.

---

## 1. SageMaker AI Core -- Inference and Deployment

SageMaker AI provides four inference options for deploying models behind endpoints. Knowing which to pick is a common exam scenario.

### Inference Options Comparison

| Option | Payload Limit | Processing Time Limit | Scaling to Zero | Persistent Endpoint | Best For |
|---|---|---|---|---|---|
| **Real-Time Inference** | 25 MB | 60s (8 min streaming) | No | Yes | Low-latency, high-throughput production workloads |
| **Serverless Inference** | 4 MB | 60s | Yes | Yes (cold-startable) | Intermittent/unpredictable traffic with tolerance for cold starts |
| **Batch Transform** | 100 MB per record | Days (3600s timeout per request) | N/A (job-based) | No | Offline predictions on large datasets |
| **Async Inference** | 1 GB | 1 hour | Yes | Yes | Large payloads, long processing times, near-real-time |

### Real-Time Inference Key Concepts

- **Endpoint Configuration**: Defines instance type, instance count, and model data location
- **Production Variants**: Multiple variants behind one endpoint for A/B testing and canary deployments
- **Model Artifacts**: Must be compressed as `.tar.gz` and stored in S3
- **ContentType / Accept**: MIME types must match what the model container expects
- **Auto-Scaling**: Based on `InvocationsPerInstance` or custom CloudWatch metrics

### Advanced Endpoint Architectures

| Architecture | Description | Use Case |
|---|---|---|
| **Multi-Model Endpoints (MME)** | Thousands of models behind one endpoint, sharing a container | Cost optimization when models use the same framework |
| **Multi-Container Endpoints (MCE)** | Multiple containers with different frameworks on one endpoint | Models requiring different frameworks |
| **Serial Inference Pipelines** | Chain of containers for pre/post-processing + inference | Preprocessing + model inference + postprocessing |
| **Inference Components** | Fine-grained resource allocation per model on shared infrastructure | Hosting multiple FMs with different resource requirements |

### Deployment Strategies

- **Blue/Green**: Create new endpoint, test, switch traffic. SageMaker supports this natively via endpoint updates.
- **Canary**: Route a small percentage of traffic to a new variant, monitor, then shift all traffic.
- **Shadow Testing**: New model receives a copy of production traffic for comparison but does not serve responses to users. Use CloudWatch to compare `ModelLatency`, error rates, etc.

### When to Use / When NOT to Use SageMaker Endpoints

**Use when:**
- You need to host a custom or open-weight model (Llama, Mistral, etc.) with full infrastructure control
- You need multi-model endpoints for cost optimization
- You need GPU-level tuning, custom containers, or specialized inference frameworks
- You need serial inference pipelines with pre/post-processing

**Do NOT use when:**
- A model is available on Bedrock and you want serverless, zero-ops inference -- use Bedrock
- You just need a one-off prediction on a batch dataset -- consider Bedrock Batch Inference first

---

## 2. SageMaker JumpStart -- Foundation Models

SageMaker JumpStart is a model hub within SageMaker that provides access to **hundreds of pre-trained foundation models** for one-click deployment and fine-tuning.

### What JumpStart Provides

- **Pre-trained FMs**: Llama 2/3, Mistral, Falcon, Bloom, Stable Diffusion, FLAN-T5, GPT-J, Code Llama, and more
- **One-click deployment**: Deploy FMs to SageMaker endpoints directly from Studio
- **Fine-tuning support**: Domain adaptation and instruction-based fine-tuning from Studio or the Python SDK
- **Solution templates**: End-to-end ML solutions for common use cases
- **Pre-optimized containers**: Inference containers with the right dependencies pre-configured

### JumpStart Fine-Tuning Approaches

| Approach | Description | Data Format |
|---|---|---|
| **Domain Adaptation** | Adapt a model to a specific domain using unlabeled text | CSV, JSON, or TXT (single file, uses `Text` column) |
| **Instruction-Based** | Fine-tune using prompt-completion pairs | JSON Lines (`.jsonl`) with `prompt` and `completion` fields |

### Key JumpStart Hyperparameters for Fine-Tuning

- `epoch`: Number of training passes
- `learning_rate`: Step size for weight updates
- `per_device_train_batch_size`: Training batch size per device
- `lora_r`: LoRA rank (dimension of the low-rank matrices)
- `lora_alpha`: LoRA scaling factor
- `lora_dropout`: Dropout for LoRA layers
- `int8_quantization`: Enable 8-bit quantization to reduce memory
- `enable_fsdp`: Enable Fully Sharded Data Parallel for distributed training
- `instruction_tuned`: Boolean to toggle instruction-based fine-tuning

### JumpStart vs Bedrock for Model Access

| Dimension | SageMaker JumpStart | Amazon Bedrock |
|---|---|---|
| **Infrastructure** | You manage endpoint instances | Fully managed, serverless |
| **Model Weights** | You have access to model artifacts | No access to weights |
| **Customization** | Full fine-tuning, LoRA, PEFT, continued pre-training | Fine-tuning and continued pre-training (limited methods) |
| **Cost Model** | Pay for instance hours (even when idle) | Pay per token/API call |
| **Open-Weight Models** | Full catalog of open-weight models | Subset available via Bedrock and Bedrock Marketplace |
| **Control** | Full control over inference infrastructure | Zero infrastructure management |

### When to Use JumpStart

- You need an **open-weight FM** that is not on Bedrock
- You need **LoRA or full fine-tuning** with custom hyperparameter control
- You want to deploy a model on **specific GPU instance types** (e.g., `ml.g5.xlarge`, `ml.p4d.24xlarge`)
- You need **model weights in S3** for custom pipelines

### When NOT to Use JumpStart

- The model is available on Bedrock and you want zero-ops -- use Bedrock
- You need to build a model from scratch -- use SageMaker Training Jobs

---

## 3. SageMaker Model Registry

The Model Registry is a **central catalog** for managing model versions, approval workflows, and deployment lineage.

### Core Concepts

- **Model Group**: A collection of model versions that solve the same problem (e.g., "fraud-detection-model")
- **Model Package (Version)**: A specific trained model version within a group, containing:
  - Model artifacts S3 location
  - Container image URI
  - Inference specification
  - Metadata and tags
- **Model Card**: Documentation attached to each model version (see Section 12)

### Lifecycle Stages and Approval Workflow

Model Registry now supports **custom lifecycle stages** such as:
- `Development` -> `Testing` -> `Production`

Each stage has an **approval status**:
- `PendingApproval`
- `Approved`
- `Rejected`

Only personas with the right IAM permissions can update stage status, creating an audit trail.

### Key Features

| Feature | Description |
|---|---|
| **Version Tracking** | Each registered model gets an incremental version number |
| **Approval Workflows** | Status tracking (Pending -> Approved -> Rejected) with IAM-based access control |
| **Model Lineage** | Track which training job, dataset, and pipeline created each model |
| **Cross-Account Support** | Share model groups across AWS accounts |
| **EventBridge Integration** | Lifecycle events trigger EventBridge rules for CI/CD automation |
| **Collections** | Group related Model Groups together for organization |
| **Model Cards** | Each model version links to its corresponding Model Card |

### Deployment Pipeline Integration

```
Training Job -> Register in Model Registry -> Approval -> Deploy to Endpoint
                                                |
                                                v
                                        EventBridge Rule -> Lambda -> Update Endpoint
```

SageMaker Pipelines can automatically register trained models in the Registry, then EventBridge rules can trigger deployment when approval status changes to `Approved`.

### Exam-Critical: Model Registry vs Model Cards

| Model Registry | Model Cards |
|---|---|
| Stores **metadata** about models (artifacts location, container image, version) | Stores **documentation** about models (intended use, risk rating, training details) |
| Used for **MLOps** (versioning, approval, deployment) | Used for **governance and compliance** (audit, risk assessment) |
| Each model version in the Registry links to its Model Card | Each Model Card is immutable once associated with a model |

---

## 4. SageMaker Clarify -- Bias, Explainability, and FM Evaluation

SageMaker Clarify provides bias detection, model explainability, and foundation model evaluation capabilities.

### Three Primary Functions

#### 1. Pre-Training Bias Detection
Detect bias in your **training data** before model training begins:
- **Class Imbalance (CI)**: Measures whether one group is underrepresented
- **Difference in Proportions of Labels (DPL)**: Compares label distributions across groups
- **Conditional Demographic Disparity (CDD)**: Checks for bias conditioned on other features

#### 2. Post-Training Bias Detection and Explainability
After training, analyze the **model's predictions**:
- **Feature Attribution**: SHAP (Shapley Additive Explanations) values show which features contribute most to predictions
- **Partial Dependence Plots (PDP)**: Show how a feature affects predictions while marginalizing other features
- **Post-training bias metrics**: Disparate Impact, Difference in Conditional Acceptance, Treatment Equality

#### 3. Foundation Model Evaluation (FMEval)
Evaluate LLMs and foundation models across quality and responsibility dimensions:

**Automatic Evaluation Dimensions:**
- **Accuracy**: Correctness of generated responses
- **Semantic Robustness**: Consistency under input perturbations
- **Factual Knowledge**: Ability to recall facts
- **Prompt Stereotyping**: Detection of stereotypical associations
- **Toxicity**: Presence of harmful or offensive content

**Human Evaluation:**
- Compare up to 2 models concurrently
- Custom evaluation criteria (helpfulness, tone, brand voice)
- Use your own workforce or AWS-managed evaluation teams

**Supported Evaluation Tasks:**
- Open-ended generation
- Text summarization
- Question answering
- Text classification
- Custom tasks

### How Clarify Runs

Clarify uses **SageMaker Processing Jobs** under the hood:
1. Takes input data and configuration
2. Optionally obtains model predictions
3. Computes bias metrics and feature attributions
4. Generates analysis results (JSON + visual report)

### Integration Points

- **SageMaker Experiments**: Tracks feature attribution scores alongside training metrics
- **SageMaker Model Monitor**: Monitors deployed models for bias drift and feature attribution drift in production
- **SageMaker Pipelines**: Integrate Clarify steps into automated ML pipelines

### When to Use Clarify

- **Pre-training**: Assess training data for demographic bias
- **Post-training**: Explain model predictions with SHAP values
- **Production monitoring**: Detect bias drift and feature attribution drift (via Model Monitor)
- **FM evaluation**: Compare foundation models before selecting one for production
- **Compliance**: Generate bias reports for auditors and regulators

### When NOT to Use Clarify

- You need real-time inference explanations for every request -- Clarify is batch-oriented (though it supports near-real-time for some use cases)
- You only need Bedrock model evaluation -- use Bedrock's built-in evaluation features instead

---

## 5. SageMaker Ground Truth -- Data Labeling

Ground Truth is a **managed data labeling** service that combines human workers with machine learning to create high-quality training datasets.

### Workforce Options

| Workforce | Description | Use Case |
|---|---|---|
| **Amazon Mechanical Turk** | Public crowdsourced workforce | High-volume, general labeling (non-sensitive data) |
| **Private Workforce** | Your own employees | Sensitive data, domain expertise |
| **Vendor Companies** | Third-party labeling providers via AWS Marketplace | Specialized labeling at scale |
| **AWS-Managed (Ground Truth Plus)** | AWS expert workforce, fully managed | Turnkey service with quality management |

### Built-In Task Types

- Image classification, object detection, semantic segmentation
- Video object detection and tracking, video clip classification
- Text classification, named entity recognition
- 3D point cloud object detection and tracking

### Active Learning (Automated Data Labeling)

Ground Truth supports **active learning** to reduce labeling costs:
1. A random sample is sent to human labelers
2. A model is trained on the labeled data
3. The model automatically labels high-confidence items
4. Low-confidence items are routed back to human labelers

Active learning is available for: image classification, semantic segmentation, object detection, and text classification. Requires **thousands of data objects** to be effective.

### Ground Truth Plus for GenAI

Ground Truth Plus generates datasets for **foundation model customization**:
- **Demonstration Data**: Human annotators create prompt-response pairs (for supervised fine-tuning / SFT)
- **Preference Data**: Human annotators rank model outputs (for Reinforcement Learning from Human Feedback / RLHF)
- Supports LLMs, text-to-image, and text-to-video models
- Includes red teaming capabilities to discover model vulnerabilities

### Quality Assurance

- **Annotation Consolidation**: Multiple workers label the same item; a consolidation algorithm produces a single high-fidelity label
- **Approval Workflows**: Review and change annotations
- **Machine Validation**: Automated checks on annotation quality
- **Consensus**: Algorithms route reviews to multiple individuals

### When to Use Ground Truth

- You need labeled data for training custom models
- You need human-generated demonstration data or preference data for SFT/RLHF
- You need active learning to reduce labeling costs on large datasets
- You need red teaming for foundation model safety evaluation

### When NOT to Use Ground Truth

- You have pre-labeled data that only needs formatting -- use Data Wrangler
- You need synthetic data generation for training -- consider Bedrock for synthetic data generation

---

## 6. SageMaker Data Wrangler -- Data Preparation

Data Wrangler is a **visual data preparation** tool for importing, transforming, and analyzing data for ML.

### Key Capabilities

| Capability | Details |
|---|---|
| **Data Import** | Amazon S3, Athena, Redshift, Snowflake, Databricks, 40+ third-party sources |
| **300+ Built-In Transforms** | Encoding, normalization, imputation, column manipulation, custom PySpark/SQL |
| **Data Quality Reports** | Detect missing values, outliers, target leakage, and anomalies |
| **Quick Model** | Estimate a dataset's predictive power without training a full model |
| **Bias Detection** | Integrated with Clarify to check for bias during preparation |
| **Natural Language Interface** | Describe transforms in plain English |
| **Export Options** | S3, SageMaker Pipelines, Feature Store, Python scripts |

### Data Wrangler Flow

A **data flow** defines a series of ML data preparation steps:
1. Import data from a source
2. Apply transformations (visual or code-based)
3. Analyze and visualize data
4. Export to a destination

Data flows can be exported as:
- SageMaker Processing jobs (for automated execution)
- SageMaker Pipelines steps (for CI/CD integration)
- Python scripts (for manual execution)
- Feature Store ingestion jobs

### Data Quality and Insights Report

The report includes:
- **Summary**: Missing values, invalid values, feature types, outlier counts, severity warnings
- **Target Column**: Distribution analysis
- **Quick Model**: Estimated model performance (R2, accuracy, AUC, etc.)
- **Feature Summary**: Features ranked by predictive power
- **Samples**: Anomalous and duplicate sample detection

### Exam Relevance (Task 1.3.1)

The exam specifically calls out Data Wrangler for **data validation**. Know that it:
- Generates data quality reports that flag issues before training
- Integrates directly with SageMaker Pipelines for automated data validation
- Can detect bias in data via Clarify integration

### When to Use / When NOT to Use

**Use when:** Visual/low-code data prep, data quality assessment, exploratory analysis, preparing tabular/image/text data for ML

**Do NOT use when:** Large-scale ETL jobs (use AWS Glue), real-time data streaming (use Kinesis), simple S3 data format conversion

---

## 7. SageMaker Processing -- Data Processing Jobs

SageMaker Processing provides **fully managed infrastructure** for running data preprocessing, postprocessing, feature engineering, and model evaluation scripts.

### How Processing Jobs Work

```
S3 Input -> Processing Container -> S3 Output
            (/opt/ml/processing/)
```

1. You specify input data (S3, Athena, or Redshift)
2. SageMaker provisions compute (CPU or GPU instances)
3. Your script runs inside a container
4. Output is written to S3

### Key Characteristics

- Input data is downloaded to `/opt/ml/processing/input/`
- Output data is uploaded from `/opt/ml/processing/output/`
- Supports **scikit-learn, Spark, and custom containers**
- Monitored via CloudWatch logs and metrics (CPU, GPU, memory, disk)
- Infrastructure is fully managed and terminated after the job completes

### Common Use Cases

| Use Case | Description |
|---|---|
| **Data Preprocessing** | Clean, normalize, feature-engineer raw data before training |
| **Feature Engineering** | Create new features from existing data |
| **Model Evaluation** | Run evaluation scripts on a held-out test set |
| **Bias Analysis** | Clarify uses Processing jobs under the hood |
| **Data Validation** | Validate data schemas and distributions |
| **Post-Processing** | Transform model outputs (e.g., calibrate probabilities) |

### Exam Relevance (Task 1.3.2)

The exam specifically calls out SageMaker Processing for **data processing**. Distinguish it from:
- **Data Wrangler**: Visual, low-code data preparation
- **Processing Jobs**: Code-first, script-based data processing on managed infrastructure
- **AWS Glue**: Serverless ETL for data integration and cataloging

---

## 8. SageMaker Model Monitor -- Production Monitoring

Model Monitor **automatically monitors deployed models** in production and alerts when quality issues arise.

### Four Monitoring Dimensions

| Monitor Type | What It Detects | Baseline Source |
|---|---|---|
| **Data Quality** | Drift in input data distributions (schema violations, missing values, statistical changes) | Training dataset statistics |
| **Model Quality** | Degradation in prediction accuracy (accuracy, precision, recall, RMSE) | Ground truth labels (requires labeling) |
| **Bias Drift** | Changes in fairness metrics over time | Pre-deployment Clarify bias analysis |
| **Feature Attribution Drift** | Changes in SHAP feature importance rankings | Pre-deployment Clarify SHAP analysis |

### How Model Monitor Works

1. **Enable Data Capture**: Log inputs and outputs of endpoints/batch transforms to S3
2. **Create Baseline**: Generate statistics and constraints from your training dataset
3. **Schedule Monitoring**: Set up periodic monitoring jobs (hourly, daily, etc.)
4. **Detect Violations**: Monitor compares live data against baseline; violations generate reports
5. **Alert**: CloudWatch alarms trigger notifications or automated retraining

### Key Details

- Data Capture happens **asynchronously** and does not impact endpoint performance
- Supports **real-time endpoints** and **batch transform jobs** (not multi-model endpoints)
- Works on **tabular data** natively; for NLP/CV, use custom containers (BYOC)
- Keep disk utilization **below 75%** to ensure data capture continues
- Integrates with **SageMaker Model Dashboard** for a centralized monitoring view

### Feature Attribution Drift Deep Dive

Uses **Normalized Discounted Cumulative Gain (NDCG)** to compare feature importance rankings:
- Compares SHAP-based feature rankings from training data vs. live data
- NDCG score below **0.90** triggers an alert
- Available via Clarify integration with Model Monitor

### When to Use Model Monitor

- You have a deployed SageMaker endpoint and need to detect data drift
- You need to monitor prediction quality over time
- You need to track bias drift for compliance
- You want automated alerts when model performance degrades

### When NOT to Use

- You are using Bedrock endpoints -- Bedrock has its own monitoring via CloudWatch
- You need monitoring for multi-model endpoints (not supported)

---

## 9. SageMaker Neo -- Model Compilation and Edge Optimization

SageMaker Neo **compiles trained models** for optimized inference on cloud instances or edge devices.

### How Neo Works

1. **Compiler**: Converts framework-specific operations into a framework-agnostic intermediate representation (IR), optimizes it, and generates binary code for the target platform
2. **Runtime**: A lightweight runtime for each target platform that loads and serves the compiled model

### Supported Frameworks

DarkNet, Keras, MXNet, PyTorch, TensorFlow, TensorFlow-Lite, ONNX, XGBoost

### Supported Targets

- **Cloud**: SageMaker hosting instances (including Inferentia/Inf1)
- **Edge**: ARM, Intel, NVIDIA processors on Android, Linux, Windows

### Key Benefits

- Up to **25x faster inference** with no loss in accuracy
- Less than **1/10th the runtime footprint** (critical for edge)
- Supports FP32, INT8, and FP16 quantization
- Compiled models can be deployed to SageMaker endpoints or edge devices

### When to Use Neo

- You need to **optimize inference latency** on specific hardware
- You are deploying models to **edge devices** (IoT, cameras, robots)
- You want to use **AWS Inferentia** (Inf1/Inf2) instances for cost-effective inference
- You need to **reduce model size** through compilation and quantization

### When NOT to Use Neo

- You are using Bedrock (fully managed, no compilation needed)
- Your model framework is not supported by Neo
- You need dynamic model architectures that change at inference time

### Exam Note

Neo is lower-weight on the AIP-C01 exam compared to Bedrock and JumpStart, but it may appear in questions about **cost optimization** and **edge deployment**.

---

## 10. SageMaker Unified Studio

SageMaker Unified Studio is a **single development environment** that brings together AWS data, analytics, AI, and ML services.

### What Unified Studio Provides

- **Unified interface** for data exploration, SQL analytics, data processing, ML model development, and GenAI app development
- **Integrates tools from**: Amazon EMR, AWS Glue, Amazon Athena, Amazon Redshift, Amazon MWAA, Amazon Bedrock, and Amazon SageMaker AI
- **Project-based collaboration**: Users work in projects to share data, code, and resources
- **Built-in AI assistance**: Amazon Q Developer for code generation, SQL writing, and troubleshooting
- **Governance**: Amazon SageMaker Catalog for data discovery and access control

### Key Capabilities

| Capability | Tools |
|---|---|
| **SQL Analytics** | Amazon Athena, Amazon Redshift query engines |
| **Data Processing** | Apache Spark, Trino via AWS Glue / Amazon EMR |
| **ML Development** | SageMaker AI notebooks, training, deployment |
| **GenAI Development** | Bedrock models, Knowledge Bases, Agents, Guardrails, Flows |
| **Visualization** | Amazon QuickSight integration |
| **Data Governance** | SageMaker Catalog, data quality monitoring, lineage tracking |

### Bedrock in Unified Studio

Selected Amazon Bedrock capabilities are available directly in Unified Studio:
- Foundation model access (including Claude, Nova, Llama, DeepSeek-R1)
- Knowledge Bases, Guardrails, Agents, and Flows
- Bedrock IDE for building GenAI applications

### Inference Endpoints in Unified Studio

You can create and manage SageMaker inference endpoints directly in Unified Studio:
- Configure instance type, instance count, and auto-scaling
- Deploy models without managing underlying infrastructure
- Search and monitor endpoints

### Exam Relevance

Unified Studio questions will likely focus on:
- Understanding that it is a **single pane of glass** for data + analytics + AI
- It integrates **both Bedrock and SageMaker AI** capabilities
- It uses **project-based access control** and **SSO/IAM authentication**

---

## 11. Model Customization for GenAI

Model customization is critical for the exam. The key is knowing **which technique to use when**.

### Customization Techniques Spectrum

```
No Customization (Prompt Engineering)
        |
        v
Retrieval-Augmented Generation (RAG)
        |
        v
Parameter-Efficient Fine-Tuning (PEFT / LoRA)
        |
        v
Full Fine-Tuning (FFT)
        |
        v
Continued Pre-Training
        |
        v
Training from Scratch
```

### Technique Comparison

| Technique | What It Does | Data Required | Compute Cost | When to Use |
|---|---|---|---|---|
| **Prompt Engineering** | Crafts prompts to guide model behavior | None | Zero (inference-time only) | Start here; often sufficient |
| **RAG** | Retrieves context from external knowledge at inference time | Knowledge base documents | Low (retrieval + inference) | Need up-to-date factual knowledge without changing model weights |
| **LoRA / PEFT** | Adds small adapter layers; freezes base model weights | 100s-1000s of labeled examples | Low-Medium | Domain adaptation, task specialization with limited data/budget |
| **Full Fine-Tuning** | Updates all model parameters | 1000s-10000s+ of labeled examples | High (full GPU training) | Extensive customization with large datasets |
| **Continued Pre-Training** | Extends model knowledge with unlabeled domain text | Large corpus of domain text (unlabeled) | Very High | New domain vocabulary, industry jargon, proprietary knowledge |
| **Training from Scratch** | Build a model with random weight initialization | Massive dataset (billions of tokens) | Extremely High | Proprietary architecture, unique requirements |

### LoRA (Low-Rank Adaptation) Deep Dive

LoRA is the **most exam-relevant PEFT technique**:

- **How it works**: Adds small, trainable low-rank matrices to existing model layers (typically attention layers). Only these adapter weights are updated during training.
- **Key hyperparameters**:
  - `lora_r`: Rank of the decomposition (typically 4-64). Higher rank = more parameters = more capacity but more compute.
  - `lora_alpha`: Scaling factor, often set to 2x `lora_r`
  - `lora_dropout`: Dropout applied to LoRA layers for regularization
- **Benefits**:
  - 70%+ reduction in training compute vs full fine-tuning
  - 50%+ reduction in training cost
  - Base model weights remain frozen (can swap adapters at inference time)
  - Multiple LoRA adapters can be loaded on a single base model
- **SageMaker Support**: SageMaker supports deploying LoRA adapters as **adapter inference components** on endpoints, allowing multiple task-specific adapters on a shared base model

### Alignment Techniques

| Technique | Description | Data Format |
|---|---|---|
| **SFT (Supervised Fine-Tuning)** | Train on prompt-completion pairs | `{"prompt": "...", "completion": "..."}` |
| **DPO (Direct Preference Optimization)** | Learn from preferred vs. rejected response pairs | `{"prompt": "...", "chosen": "...", "rejected": "..."}` |
| **PPO (Proximal Policy Optimization)** | Reinforcement learning to optimize for reward | Reward model + prompts |
| **RLHF** | Human feedback guides model alignment | Human preference rankings |

### Continued Pre-Training

- Uses **self-supervised learning** on large quantities of unlabeled proprietary data
- Expands the model's foundational knowledge (domain vocabulary, specialized terms)
- Typically followed by SFT and alignment (DPO or PPO)
- Available on both **Bedrock** (for supported models) and **SageMaker AI**

### Knowledge Distillation

- Transfers knowledge from a **larger teacher model** to a **smaller student model**
- Useful when you lack adequate training data but have access to a more powerful model
- Produces a smaller, faster, more cost-efficient model
- Available in SageMaker AI (e.g., Amazon Nova customization)

### Where to Do Customization

| Platform | Techniques | Trade-offs |
|---|---|---|
| **Amazon Bedrock** | Fine-tuning (SFT), continued pre-training, distillation (limited models) | Quickest time-to-value, fully managed, limited model/technique selection |
| **SageMaker Training Jobs** | SFT, PEFT/LoRA, FFT, DPO, PPO, continued pre-training, distillation | Balanced ease-of-use and flexibility, managed infrastructure |
| **SageMaker HyperPod** | All techniques including large-scale distributed training | Maximum control and scale, requires cluster management |

---

## 12. Model Cards -- Governance and Compliance

Model Cards are a **documentation framework** for machine learning models, designed for governance, compliance, and responsible AI.

### What Model Cards Contain

| Section | Description |
|---|---|
| **Model Overview** | Model name, type, version, source algorithm, framework |
| **Intended Uses** | Scenarios where the model is appropriate and inappropriate, assumptions, general purpose |
| **Risk Rating** | Unknown, Low, Medium, or High -- impacts production deployment decisions |
| **Business Details** | Business problem, expected users, business impact |
| **Training Details** | Training data, hyperparameters, training metrics, objective function |
| **Evaluation Details** | Evaluation metrics in JSON format (bar charts, matrices, linear graphs) |
| **Additional Information** | Custom properties, free-form documentation |

### Key Properties

- **Immutable**: Once a Model Card is associated with a model version, it cannot be modified (except approval status). Edits create new versions.
- **Versioned**: Each edit creates a new Model Card version for an immutable audit trail
- **Linked to Model Registry**: Each model version in the Registry has a 1:1 link to its Model Card
- **Exportable**: Model Cards can be exported to PDF for sharing with stakeholders and regulators
- **Auto-populated**: When using the SageMaker Python SDK, some fields are auto-populated from training job metadata

### Risk Ratings and Compliance

Model Cards support **risk ratings** that help organizations comply with internal policies and external regulations:
- Models with `High` risk may require additional review before production deployment
- Risk ratings are visible in the Model Dashboard
- Organizations can enforce policies that prevent deploying `High` risk models without explicit approval

### Exam-Critical Points

- Model Cards address **Task 3.3.1** (model cards for compliance)
- They are NOT the same as Model Registry -- Cards document the "why" and "how", Registry tracks the "what" and "where"
- No native integration with Model Monitor, but you can manually upload Model Monitor metrics to a Model Card
- Model Cards can be created for models not trained in SageMaker, but no information is auto-populated

---

## 13. Exam Gotchas -- SageMaker vs Bedrock Decision Points

This is one of the most common exam trap areas. The exam tests whether you know when to use SageMaker vs Bedrock.

### Decision Framework

```
Do you need to train or build a model from scratch?
  YES -> SageMaker AI
  NO  -> Continue

Is the model available on Bedrock?
  YES -> Do you need full control over infrastructure?
    YES -> SageMaker AI (JumpStart or custom endpoint)
    NO  -> Bedrock
  NO  -> SageMaker AI (JumpStart or custom endpoint)

Do you need fine-tuning?
  Need LoRA with custom hyperparameter control -> SageMaker AI
  Need simple SFT or continued pre-training -> Bedrock (if model supports it) or SageMaker AI
  Need DPO, PPO, RLHF -> SageMaker AI

Do you need model evaluation?
  Compare Bedrock-hosted models -> Bedrock Evaluation
  Evaluate with custom metrics/benchmarks -> SageMaker Clarify FMEval
  Need human evaluation -> Either (both support it)

Do you need production monitoring?
  SageMaker endpoint -> Model Monitor
  Bedrock endpoint -> CloudWatch metrics + Bedrock-specific monitoring

Do you need data labeling for RLHF?
  -> Ground Truth Plus
```

### Common Exam Traps

| Scenario | Correct Answer | Why |
|---|---|---|
| "Deploy a foundation model with zero infrastructure management" | **Bedrock** | Serverless, no endpoint management |
| "Fine-tune Llama 3 with LoRA and custom hyperparameters" | **SageMaker AI** (JumpStart) | Bedrock has limited fine-tuning control |
| "Detect bias in training data before model training" | **SageMaker Clarify** | Pre-training bias detection |
| "Evaluate multiple LLMs for accuracy and toxicity" | **SageMaker Clarify FMEval** or **Bedrock Evaluation** | Both work, but SageMaker Clarify gives more customization |
| "Monitor a deployed model for data drift" | **SageMaker Model Monitor** | Designed for production monitoring of SageMaker endpoints |
| "Label data for RLHF fine-tuning" | **Ground Truth Plus** | Generates preference data for RLHF |
| "Prepare and clean tabular data with no code" | **Data Wrangler** | Visual data preparation tool |
| "Run a preprocessing script on managed infrastructure" | **SageMaker Processing** | Script-based processing on managed compute |
| "Track model versions and approval status" | **Model Registry** | Central model version catalog |
| "Document model risk rating and intended use" | **Model Cards** | Governance and compliance documentation |
| "Deploy model to edge devices" | **SageMaker Neo** + Edge Manager | Compile and deploy to edge |
| "Host 1000+ models behind one endpoint" | **Multi-Model Endpoints** | Cost-effective multi-model serving |

---

## 14. When to Use / When NOT to Use -- Decision Matrix

| Sub-Service | Use When | Do NOT Use When |
|---|---|---|
| **SageMaker Endpoints** | Custom models, specific GPU requirements, multi-model hosting | Model available on Bedrock and you want serverless |
| **JumpStart** | Open-weight FMs, custom fine-tuning, need model artifacts | Model on Bedrock meets your needs with less ops |
| **Model Registry** | Tracking model versions, approval workflows, CI/CD pipelines | One-off model experiments (use MLflow/Experiments) |
| **Clarify** | Bias detection, SHAP explainability, FM evaluation | Real-time per-request explanations at scale |
| **Ground Truth** | Labeled training data, RLHF preference data, active learning | Data already labeled, synthetic data generation |
| **Data Wrangler** | Visual data prep, data quality reports, exploratory analysis | Large-scale ETL (use Glue), real-time streaming |
| **Processing** | Script-based preprocessing/postprocessing on managed compute | Visual data preparation (use Data Wrangler) |
| **Model Monitor** | Production drift detection, bias monitoring, model quality | Bedrock endpoints (not compatible) |
| **Neo** | Edge deployment, inference optimization, specific hardware targets | Bedrock models, unsupported frameworks |
| **Unified Studio** | Unified data + analytics + AI experience, team collaboration | Single-purpose tasks where Studio/Console suffices |
| **Model Cards** | Governance, compliance documentation, risk assessment | Just tracking model artifacts (use Model Registry) |

---

## 15. Key CloudWatch Metrics

### Endpoint Instance Metrics (`/aws/sagemaker/Endpoints` namespace)

| Metric | Description | Exam Relevance |
|---|---|---|
| `CPUUtilization` | Sum of each CPU core's utilization (0%-400% for 4 CPUs) | Capacity planning |
| `GPUUtilization` | Percentage of GPU units used (0%-400% for 4 GPUs) | GPU sizing and cost optimization |
| `GPUMemoryUtilization` | GPU memory used (0%-400% for 4 GPUs) | Detect OOM risks |
| `MemoryUtilization` | Container memory usage (0%-100%) | Detect memory pressure |
| `DiskUtilization` | Disk space used (0%-100%) | Keep below 75% for data capture |
| `CPUUtilizationNormalized` | Normalized CPU usage (0%-100%) | Inference components only |
| `GPUUtilizationNormalized` | Normalized GPU usage (0%-100%) | Inference components only |

### Endpoint Invocation Metrics (`AWS/SageMaker` namespace)

| Metric | Description | Exam Relevance |
|---|---|---|
| `Invocations` | Number of InvokeEndpoint requests | Traffic volume |
| `InvocationsPerInstance` | Invocations normalized by active instances | **Auto-scaling target metric** |
| `ModelLatency` | Time the model container takes to respond (microseconds) | Performance monitoring |
| `OverheadLatency` | Time SageMaker adds for overhead (microseconds) | Distinguish model vs infra latency |
| `Invocation4XXErrors` | Client error count | Request validation issues |
| `Invocation5XXErrors` | Server error count | Model or infra failures |
| `ModelSetupTime` | Time to set up the model (serverless) | Cold start measurement |

### Training Job Metrics (`/aws/sagemaker/TrainingJobs`)

| Metric | Description |
|---|---|
| `CPUUtilization` | CPU usage during training |
| `GPUUtilization` | GPU usage during training |
| `GPUMemoryUtilization` | GPU memory during training |
| `DiskUtilization` | Disk usage during training |

### Auto-Scaling Key Metrics

- **Primary scaling metric**: `InvocationsPerInstance` -- scales based on request load per instance
- **Alternative**: `ModelLatency` -- scale when latency exceeds threshold
- For serverless endpoints: `ServerlessConcurrentExecutionsUtilization`
- Async inference endpoints can **scale to zero** when queue is empty

### Multi-Model Endpoint Specific Metrics

| Metric | Description |
|---|---|
| `ModelLoadingWaitTime` | Time waiting for model to load |
| `ModelUnloadingTime` | Time to unload a model |
| `ModelDownloadingTime` | Time to download model from S3 |
| `ModelLoadingTime` | Time to load model into memory |
| `ModelCacheHit` | Whether the model was already in memory (1 = cache hit) |

---

## 16. TypeScript SDK v3 Usage

### SageMaker Runtime -- Invoke Endpoint

```typescript
import {
  SageMakerRuntimeClient,
  InvokeEndpointCommand,
} from "@aws-sdk/client-sagemaker-runtime";

const client = new SageMakerRuntimeClient({ region: "us-east-1" });

const response = await client.send(
  new InvokeEndpointCommand({
    EndpointName: "my-llm-endpoint",
    ContentType: "application/json",
    Accept: "application/json",
    Body: JSON.stringify({
      inputs: "What is machine learning?",
      parameters: {
        max_new_tokens: 256,
        temperature: 0.7,
        top_p: 0.9,
      },
    }),
  })
);

const result = JSON.parse(new TextDecoder().decode(response.Body));
console.log(result);
```

### SageMaker Runtime -- Invoke Endpoint with Streaming

```typescript
import {
  SageMakerRuntimeClient,
  InvokeEndpointWithResponseStreamCommand,
} from "@aws-sdk/client-sagemaker-runtime";

const client = new SageMakerRuntimeClient({ region: "us-east-1" });

const response = await client.send(
  new InvokeEndpointWithResponseStreamCommand({
    EndpointName: "my-llm-endpoint",
    ContentType: "application/json",
    Body: JSON.stringify({
      inputs: "Explain quantum computing",
      parameters: { max_new_tokens: 512 },
      stream: true,
    }),
  })
);

if (response.Body) {
  for await (const event of response.Body) {
    if (event.PayloadPart?.Bytes) {
      const chunk = new TextDecoder().decode(event.PayloadPart.Bytes);
      process.stdout.write(chunk);
    }
  }
}
```

### Model Registry -- List and Describe Model Packages

```typescript
import {
  SageMakerClient,
  ListModelPackagesCommand,
  DescribeModelPackageCommand,
} from "@aws-sdk/client-sagemaker";

const client = new SageMakerClient({ region: "us-east-1" });

// List model versions in a group
const listResponse = await client.send(
  new ListModelPackagesCommand({
    ModelPackageGroupName: "my-model-group",
    ModelApprovalStatus: "Approved",
    SortBy: "CreationTime",
    SortOrder: "Descending",
    MaxResults: 10,
  })
);

for (const pkg of listResponse.ModelPackageSummaryList ?? []) {
  console.log(`Version: ${pkg.ModelPackageVersion}, Status: ${pkg.ModelApprovalStatus}`);

  // Describe a specific model version
  const detail = await client.send(
    new DescribeModelPackageCommand({
      ModelPackageName: pkg.ModelPackageArn,
    })
  );
  console.log(`Container: ${detail.InferenceSpecification?.Containers?.[0]?.Image}`);
}
```

### Model Registry -- Update Approval Status

```typescript
import {
  SageMakerClient,
  UpdateModelPackageCommand,
} from "@aws-sdk/client-sagemaker";

const client = new SageMakerClient({ region: "us-east-1" });

await client.send(
  new UpdateModelPackageCommand({
    ModelPackageArn: "arn:aws:sagemaker:us-east-1:123456789012:model-package/my-group/1",
    ModelApprovalStatus: "Approved",
    ApprovalDescription: "Passed evaluation metrics thresholds",
  })
);
```

### Create a Processing Job

```typescript
import {
  SageMakerClient,
  CreateProcessingJobCommand,
} from "@aws-sdk/client-sagemaker";

const client = new SageMakerClient({ region: "us-east-1" });

await client.send(
  new CreateProcessingJobCommand({
    ProcessingJobName: "data-preprocessing-job",
    RoleArn: "arn:aws:iam::123456789012:role/SageMakerProcessingRole",
    ProcessingResources: {
      ClusterConfig: {
        InstanceCount: 1,
        InstanceType: "ml.m5.xlarge",
        VolumeSizeInGB: 30,
      },
    },
    AppSpecification: {
      ImageUri: "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3",
      ContainerEntrypoint: ["python3", "/opt/ml/processing/input/code/preprocess.py"],
    },
    ProcessingInputs: [
      {
        InputName: "input-data",
        S3Input: {
          S3Uri: "s3://my-bucket/raw-data/",
          LocalPath: "/opt/ml/processing/input/data",
          S3DataType: "S3Prefix",
          S3InputMode: "File",
        },
      },
      {
        InputName: "code",
        S3Input: {
          S3Uri: "s3://my-bucket/scripts/preprocess.py",
          LocalPath: "/opt/ml/processing/input/code",
          S3DataType: "S3Prefix",
          S3InputMode: "File",
        },
      },
    ],
    ProcessingOutputConfig: {
      Outputs: [
        {
          OutputName: "processed-data",
          S3Output: {
            S3Uri: "s3://my-bucket/processed-data/",
            LocalPath: "/opt/ml/processing/output",
            S3UploadMode: "EndOfJob",
          },
        },
      ],
    },
  })
);
```

---

## 17. Cost Considerations

### Instance Types for GenAI Workloads

| Instance Family | Accelerator | Best For | Key Characteristic |
|---|---|---|---|
| **ml.p5.48xlarge** | 8x NVIDIA H100 | Large-scale FM training | Highest GPU performance |
| **ml.p4d.24xlarge** | 8x NVIDIA A100 | FM training and inference | High memory (40GB/80GB per GPU) |
| **ml.g5.xlarge-48xlarge** | NVIDIA A10G | Inference and fine-tuning | Cost-effective GPU inference |
| **ml.g4dn.xlarge-16xlarge** | NVIDIA T4 | Budget inference | Lower cost, suitable for smaller models |
| **ml.inf2.xlarge-48xlarge** | AWS Inferentia2 | High-throughput inference | Best cost-per-inference for supported models |
| **ml.inf1.xlarge-24xlarge** | AWS Inferentia | Cost-effective inference | Lower cost, first-gen Inferentia |
| **ml.trn1.2xlarge-32xlarge** | AWS Trainium | Cost-effective FM training | Up to 50% savings vs GPU for training |
| **ml.m5.xlarge-24xlarge** | CPU only | Processing, small model inference | No GPU, general purpose |

### Cost Optimization Strategies

| Strategy | Savings | How It Works |
|---|---|---|
| **Managed Spot Training** | Up to 90% | Use Spot Instances for training; SageMaker handles interruptions. Requires checkpointing for long jobs. Set `EnableManagedSpotTraining=True` and `MaxWaitTimeInSeconds > MaxRuntimeInSeconds` |
| **SageMaker Savings Plans** | Up to 64% | Commit to consistent usage ($/hour) for 1 or 3 years |
| **AWS Inferentia/Trainium** | 30-50% | Purpose-built ML chips vs NVIDIA GPUs |
| **Serverless Inference** | Variable | Pay only when invoked; scales to zero. Max 6 GB memory |
| **Async Inference** | Variable | Scale to zero when queue is empty; process when capacity is available |
| **Multi-Model Endpoints** | Variable | Share one endpoint across thousands of models |
| **Inference Components** | Variable | Fine-grained resource allocation on shared infrastructure |
| **Right-sizing** | Variable | Use Inference Recommender to find the optimal instance type |
| **Neo Compilation** | Variable | Compile models for target hardware to reduce latency and compute |

### Cost Comparison: SageMaker vs Bedrock

| Factor | SageMaker Endpoints | Bedrock |
|---|---|---|
| **Billing Model** | Per-instance-hour (pay while endpoint is running) | Per-token (pay per API call) or Provisioned Throughput |
| **Idle Cost** | Yes (unless serverless/async with scale-to-zero) | No (on-demand pricing) |
| **Scaling** | Manual or auto-scaling configuration | Automatic |
| **Right for** | Sustained high-throughput, custom models | Variable traffic, rapid prototyping, multi-model |

### Exam Tip: Spot Training Checkpointing

For managed spot training, you **must implement checkpointing** for training jobs longer than 1 hour. Without checkpointing:
- If the Spot Instance is interrupted, training restarts from the beginning
- Built-in algorithms that don't support checkpointing are limited to `MaxWaitTimeInSeconds = 3600`
- Use `CheckpointConfig` to specify an S3 location for saving checkpoints

---

## Quick Reference Card

| Need | Use This |
|---|---|
| Deploy a custom/open-weight FM | SageMaker JumpStart + Endpoints |
| Serverless FM inference | Amazon Bedrock |
| Fine-tune with LoRA | SageMaker JumpStart or Training Jobs |
| Track model versions | Model Registry |
| Document model risk/compliance | Model Cards |
| Detect training data bias | SageMaker Clarify (pre-training) |
| Explain predictions with SHAP | SageMaker Clarify (post-training) |
| Evaluate LLM quality/toxicity | SageMaker Clarify FMEval |
| Label data for SFT/RLHF | Ground Truth / Ground Truth Plus |
| Visual data preparation | Data Wrangler |
| Script-based data processing | SageMaker Processing |
| Monitor production data drift | Model Monitor |
| Compile model for edge | SageMaker Neo |
| Unified data + AI workspace | SageMaker Unified Studio |
| Cost-effective training | Spot Training + Trainium |
| Cost-effective inference | Inferentia + Serverless/Async endpoints |
