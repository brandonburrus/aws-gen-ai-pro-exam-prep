# Container Services for GenAI -- Study Guide

**Exam: AWS Certified Generative AI Developer - Professional (AIP-C01)**

This guide covers container services relevant to the AIP-C01 exam: Amazon ECS, Amazon EKS,
AWS Fargate, and Amazon ECR. Containers appear in the exam primarily under:

- **Task 2.1.7**: ECS for hosting MCP servers that provide complex tools to AI agents
- **Task 2.2.2**: Container-based deployment for LLMs (memory requirements, GPU utilization, token processing)
- **Task 2.2.3**: Container optimization for Foundation Model deployment
- General knowledge: hosting custom models, AI microservices, and inference endpoints

---

## 1. Amazon ECS (Elastic Container Service)

### Overview

Amazon ECS is a fully managed container orchestration service that runs Docker containers at
scale. It eliminates the need to install and operate your own container orchestration software.

**Core Concepts:**

| Concept | Description |
|---|---|
| **Cluster** | Logical grouping of tasks or services. Can span multiple AZs. |
| **Task Definition** | JSON blueprint for your application: container images, CPU/memory, ports, volumes, IAM roles, network mode. Versioned with revision numbers. |
| **Task** | A running instantiation of a task definition. Can be a standalone task or part of a service. |
| **Service** | Maintains a desired count of tasks, handles rolling deployments, integrates with load balancers, and supports auto scaling. |
| **Capacity Provider** | Determines the infrastructure (Fargate, Fargate Spot, EC2 Auto Scaling groups) that tasks run on. |

**Launch Types:**

- **Fargate**: Serverless -- AWS manages the underlying compute. You specify CPU and memory at the task level.
- **EC2**: You manage EC2 instances registered to the cluster. Required for GPU workloads.
- **External (ECS Anywhere)**: Register on-premises or other servers to an ECS cluster.

**Network Modes:**

- `awsvpc` (required for Fargate): Each task gets its own ENI with a private IP. Best isolation.
- `bridge`: Default Docker bridge networking on EC2. Tasks share the host network stack via port mappings.
- `host`: Task uses the host's network directly. No port mapping overhead.
- `none`: No external network connectivity.

### GPU Support for AI Inference

ECS supports GPU workloads through EC2 instances with NVIDIA GPUs. This is the primary way
to run self-managed AI inference on containers in AWS.

**GPU-Optimized AMI:**
- Amazon provides an ECS GPU-optimized AMI (Amazon Linux 2023) with pre-installed NVIDIA kernel
  drivers, NVIDIA Fabric Manager, NVIDIA Container Toolkit, and Docker GPU runtime.
- Supports GPU architectures: Ampere, Turing, Volta, Maxwell, Hopper, and Ada Lovelace.
- No additional configuration required -- works out of the box.

**Supported GPU Instance Types:**

| Instance Family | GPU | Use Case |
|---|---|---|
| **p3** (V100) | 1-8 GPUs, 16-128 GiB GPU mem | Training and inference |
| **p4d** (A100) | 8 GPUs, 320 GiB GPU mem | Large model training |
| **p5** (H100) | 8 GPUs, 640 GiB GPU mem | Frontier model training |
| **g4dn** (T4) | 1-4 GPUs, 16-64 GiB GPU mem | Cost-effective inference |
| **g5** (A10G) | 1-8 GPUs, 24-192 GiB GPU mem | Inference and fine-tuning |
| **g6/g6e** (L40S) | 1-8 GPUs, 24-384 GiB GPU mem | LLM inference, best price/performance |

**Specifying GPUs in a Task Definition:**

```json
{
  "containerDefinitions": [
    {
      "name": "inference-container",
      "image": "my-model-server:latest",
      "resourceRequirements": [
        {
          "type": "GPU",
          "value": "1"
        }
      ],
      "memory": 16384,
      "cpu": 4096
    }
  ],
  "requiresCompatibilities": ["EC2"],
  "family": "ai-inference-task"
}
```

**Key Considerations for GPU Tasks:**
- GPUs are **not supported on Fargate** -- you must use the EC2 launch type.
- GPUs are **not supported on Windows** containers.
- Set `ECS_ENABLE_GPU_SUPPORT` to `true` in the container agent configuration.
- Use placement constraints to target specific GPU instance types:
  `attribute:ecs.instance-type == g6e.xlarge`
- The ECS container agent pins physical GPUs to containers. The total GPU count across all
  containers in a task cannot exceed the instance's available GPUs.
- Container images must include the necessary GPU libraries (CUDA, cuDNN). Use NVIDIA base
  images like `nvidia/cuda` or framework images like `pytorch/pytorch:latest-cuda`.
- NVIDIA GPU Time-slicing is supported on Bottlerocket, allowing multiple tasks to share a
  single GPU concurrently.

### MCP Server Hosting on ECS (Task 2.1.7)

The exam calls out ECS specifically for hosting MCP (Model Context Protocol) servers that
provide complex tools to AI agents.

**Why ECS for MCP Servers:**
- MCP servers that provide complex, long-running, or stateful tools need persistent
  containers (not Lambda's 15-minute timeout).
- ECS provides reliable service orchestration, health checks, and auto-recovery.
- Service Connect enables service-to-service communication between MCP servers and agents.
- Supports WebSocket/Streamable HTTP transport for the MCP protocol.

**Amazon ECS MCP Server (AWS-managed):**
- AWS provides a fully managed, remote MCP server for ECS operations (preview as of late 2025).
- Provides tools for containerizing apps (`containerize_app`), deploying to ECS
  (`create_ecs_infrastructure`), troubleshooting (`ecs_troubleshooting_tool`), and managing
  resources (`ecs_resource_management`).
- Uses CloudFormation for infrastructure provisioning.
- Works with Amazon Q Developer, Kiro CLI, Cursor, and any MCP-compatible AI assistant.

**Deploying Your Own MCP Server on ECS:**

```
MCP Client (Agent) --> ALB --> ECS Service --> MCP Server Container
                                   |
                                   +--> ECR (image source)
                                   +--> CloudWatch (logs/metrics)
```

1. Build MCP server as a Docker image and push to ECR.
2. Create ECS task definition with appropriate CPU/memory.
3. Deploy as an ECS service behind an ALB.
4. Secure with OAuth 2.0 authentication, WAF, and security groups.
5. Use Service Connect for inter-service discovery if running multiple MCP servers.

**Guidance for Deploying MCP Servers on AWS** (AWS Solutions):
- Containerized architecture with OAuth 2.0 authentication.
- Content delivery network (CloudFront) and WAF for security layers.
- Container orchestration for high availability.
- Centralized logging for monitoring server behavior.

### Auto Scaling for AI Workloads

ECS provides two levels of auto scaling, both important for AI inference:

**1. Service Auto Scaling (Task-Level)**
Adjusts the number of running tasks in a service using Application Auto Scaling.

| Policy Type | How It Works | AI Use Case |
|---|---|---|
| **Target Tracking** | Keeps a metric at a target value (e.g., CPU at 70%) | Steady-state inference load |
| **Step Scaling** | Scales by specific increments at alarm thresholds | Bursty inference with known patterns |
| **Scheduled Scaling** | Scales at specific times | Predictable daily inference peaks |

Built-in metrics for target tracking:
- `ECSServiceAverageCPUUtilization`
- `ECSServiceAverageMemoryUtilization`
- `ALBRequestCountPerTarget`

For AI inference, custom metrics like queue depth, tokens-per-second, or GPU utilization
(via Container Insights) are often more meaningful than CPU/memory alone.

**2. Cluster Auto Scaling (Instance-Level)**
Adjusts the number of EC2 instances in the cluster using capacity providers.

- Set a `targetCapacity` percentage (e.g., 100% means instances are fully utilized before
  adding more).
- ECS publishes `CapacityProviderReservation` to CloudWatch and manages a target tracking
  scaling policy on the Auto Scaling group.
- For GPU workloads, cluster auto scaling ensures GPU instances are provisioned when tasks
  need them.

**Best Practice for AI Workloads:**
- Use `binpack` placement strategy to maximize GPU utilization per instance before scaling out.
- Maintain headroom (over-provision slightly) because scaling GPU instances takes longer than
  scaling standard instances.
- Use step scaling over target tracking when you need faster reaction to inference queue
  backlogs.

### Service Connect for AI Microservices

Service Connect provides built-in service discovery and service mesh capabilities for
ECS services, eliminating the need for manual DNS configuration or external service meshes.

**How It Works:**
- Creates a managed Envoy proxy sidecar in each task.
- Services discover each other via short DNS names within a Cloud Map namespace.
- Round-robin load balancing with passive health checks, outlier detection, and retries.

**Key Concepts:**
- **Namespace**: A logical grouping (Cloud Map) where services discover each other. Can span
  clusters within the same Region.
- **Client Service**: Consumes endpoints in the namespace (needs the namespace to discover others).
- **Client-Server Service**: Both provides and consumes endpoints.
- **Port Name**: Named port mapping in the task definition used for endpoint configuration.

**AI Architecture Pattern -- MCP Server Mesh:**

```
Agent Service (client)
    |-- connects to --> Inference MCP Server (client-server)
    |-- connects to --> RAG MCP Server (client-server)
    |-- connects to --> Code Execution MCP Server (client-server)
```

All services share a namespace. The agent discovers MCP servers by short name (e.g.,
`inference-server:8080`). Service Connect handles load balancing across task replicas.

**Resource Overhead:**
- Add 256 CPU units and at least 64 MiB memory for the Service Connect proxy container.
- If a service receives > 500 requests/second, add 512 CPU units for the proxy.
- If the namespace has > 100 services or > 2000 tasks, add 128 MiB memory for the proxy.

**Limitations:**
- Does not support Windows containers.
- Only interconnects ECS services within the same namespace (external consumers need an ALB
  or other mechanism).
- Does not support HTTP 1.0.

---

## 2. Amazon EKS (Elastic Kubernetes Service)

### Kubernetes for AI Workloads

Amazon EKS is a managed Kubernetes service. It runs the Kubernetes control plane across
multiple AZs and integrates with AWS services for networking, security, and observability.

**When EKS matters for the exam:**
- Organizations with existing Kubernetes expertise or multi-cloud strategies.
- Complex AI/ML pipelines that need Kubernetes-native tooling (KubeFlow, Ray, Argo Workflows).
- GPU scheduling with fine-grained control (DRA, device plugins, node affinity).
- Distributed training across many GPU nodes using Elastic Fabric Adapter (EFA).

### GPU Node Groups

**EKS-Optimized Accelerated AMIs:**
- Pre-built AMIs with NVIDIA drivers and the NVIDIA Kubernetes device plugin.
- `eksctl` automatically detects GPU instance types and installs the device plugin.

**GPU Resource Scheduling:**
- Kubernetes uses the `nvidia.com/gpu` resource type in pod specs.
- The NVIDIA device plugin advertises GPU resources to the Kubernetes scheduler.
- Pods request GPUs via `resources.limits`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: inference-pod
spec:
  containers:
    - name: model-server
      image: my-inference-server:latest
      resources:
        limits:
          nvidia.com/gpu: 1
          memory: "16Gi"
          cpu: "4"
```

**Capacity Blocks for ML:**
- Reserve GPU instances for a specific future time window.
- Useful for short-duration ML training or batch inference jobs.
- Supported for both managed node groups and self-managed nodes.
- Launch template requires `InstanceMarketOptions.MarketType = capacity-block`.

**Elastic Fabric Adapter (EFA) for Distributed Training:**
- EFA provides low-latency, high-throughput networking between GPU instances.
- Required for large-scale distributed training with NCCL (NVIDIA Collective Communications Library).
- Supported on p3dn, p4d, p5 instance types.
- Requires VPC CNI version 1.18.5+ for EFA-only interfaces.

**Dynamic Resource Allocation (DRA):**
- Kubernetes-native mechanism for fine-grained GPU allocation.
- Supports NVIDIA IMEX (Internode Memory Exchange) for cross-node GPU communication.
- Relevant for P6e-GB200 UltraServers with NVLink domains.

### EKS vs ECS Decision (Exam Perspective)

| Factor | Choose ECS | Choose EKS |
|---|---|---|
| **Team expertise** | AWS-native, no Kubernetes knowledge | Existing Kubernetes skills |
| **Simplicity** | Simpler task definitions and services | More complex but more flexible |
| **GPU scheduling** | Good enough for single-node GPU tasks | Better for multi-node distributed training |
| **ML tooling** | Basic container orchestration | KubeFlow, Ray, Argo, Spark on K8s |
| **Multi-cloud** | AWS-only | Portable across clouds |
| **MCP servers** | Preferred (exam calls out ECS) | Works but not specifically called out |
| **Managed overhead** | Lower (no etcd, API server concerns) | Control plane managed, but more K8s concepts |

---

## 3. AWS Fargate

### Serverless Containers for AI

Fargate is a serverless compute engine for ECS and EKS. AWS manages all underlying infrastructure.
You define CPU and memory at the task (ECS) or pod (EKS) level.

**Task CPU and Memory Combinations:**

| vCPU | Memory Range | Notes |
|---|---|---|
| 0.25 | 0.5 GB - 2 GB | Lightweight sidecars |
| 0.5 | 1 - 4 GB | Small services |
| 1 | 2 - 8 GB | General purpose |
| 2 | 4 - 16 GB | Medium workloads |
| 4 | 8 - 30 GB | Larger workloads |
| 8 | 16 - 60 GB | CPU-intensive inference (Linux, platform 1.4.0+) |
| 16 | 32 - 120 GB | Largest Fargate tasks (Linux, platform 1.4.0+) |

**Key Characteristics:**
- Always uses `awsvpc` network mode (each task gets its own ENI).
- Pricing is per-second (1-minute minimum for Linux, 5-minute minimum for Windows).
- Ephemeral storage: 20 GB default, configurable up to 200 GB.
- Supports EBS volumes, EFS volumes, and bind mounts.
- Supports Seekable OCI (SOCI) for lazy loading -- containers start faster by downloading
  the image in the background while the application initializes.

### Fargate Limitations for AI/ML (Exam-Critical)

| Limitation | Impact on AI Workloads |
|---|---|
| **No GPU support** | Cannot run GPU-accelerated inference or training |
| **Max 16 vCPU / 120 GB memory** | Insufficient for large Foundation Models that need hundreds of GBs |
| **No `privileged` mode** | Cannot access host-level GPU drivers or specialized hardware |
| **No `ipcMode` shared** | Cannot use shared memory for inter-process communication (limits some ML frameworks) |
| **Limited Linux capabilities** | Only `CAP_SYS_PTRACE` can be added |
| **No placement constraints** | Cannot target specific instance types or hardware |

### When to Use Fargate vs EC2 Launch Type

| Use Case | Fargate | EC2 Launch Type |
|---|---|---|
| MCP servers (CPU-only tools) | Good fit -- scales to zero, simple | Viable but over-provisioned |
| Text preprocessing/embedding | Good fit if within resource limits | Better for high-throughput batch |
| GPU inference (LLMs) | Not supported | Required |
| Small model inference (CPU) | Good fit (e.g., sklearn, small transformers) | Unnecessary overhead |
| Batch AI processing | Fargate Spot (up to 70% discount) | EC2 Spot for GPU workloads |
| Real-time API serving | Good for moderate load | Better for high-throughput with GPU |

**Fargate Spot:**
- Up to 70% discount for interrupt-tolerant tasks.
- Fargate may reclaim capacity with a 30-second warning (SIGTERM).
- Good for: batch preprocessing, non-critical inference, data pipelines.
- Not suitable for: real-time user-facing inference, stateful MCP servers.

---

## 4. Amazon ECR (Elastic Container Registry)

### Container Image Management

Amazon ECR is a managed Docker container registry for storing, managing, and deploying
container images. It supports both private and public repositories.

**Core Features:**

| Feature | Description |
|---|---|
| **Private Registry** | One per account per Region. Stores Docker and OCI images. |
| **IAM Integration** | Fine-grained access control via IAM policies and repository policies. |
| **Encryption** | Images encrypted at rest using AWS KMS (default AWS-managed key or customer-managed CMK). |
| **Tag Immutability** | Prevents image tags from being overwritten. Recommended for production. |
| **Pull-Through Cache** | Cache images from public registries (Docker Hub, GitHub, etc.) in your private registry. |
| **Managed Signing** | Automatic cryptographic signatures when images are pushed. |

**Image Lifecycle for AI/ML:**
- ML model serving images are often large (5-20+ GB with CUDA, PyTorch, model weights).
- Use multi-stage Docker builds to minimize image size.
- Use ECR lifecycle policies to automatically clean up old images.
- Use SOCI (Seekable OCI) indexes for faster container startup on Fargate.

### Image Scanning

ECR provides two scanning modes:

**Basic Scanning:**
- Uses AWS-native technology with the CVE database.
- Scans for operating system package vulnerabilities.
- Two frequencies: scan on push or manual scan.
- One scan per image per 24 hours, max 100,000 images per registry per day.
- Findings sent to EventBridge.

**Enhanced Scanning (Amazon Inspector):**
- Integrates with Amazon Inspector for automated, continuous scanning.
- Scans both OS package vulnerabilities AND programming language package vulnerabilities
  (Python, Node.js, Java, etc.).
- Two frequencies: scan on push or continuous (re-scans when new CVEs are published).
- Maps vulnerabilities to running containers in ECS and EKS.

**Security Hub Controls for ECR:**

| Control | Requirement |
|---|---|
| ECR.1 | Image scanning configured |
| ECR.2 | Tag immutability enabled |
| ECR.3 | At least one lifecycle policy |
| ECR.4 | Public repos tagged |
| ECR.5 | Encrypted with customer-managed KMS key |

### Cross-Region and Cross-Account Replication

ECR supports private image replication across Regions and accounts:

- **Cross-Region replication**: Replicate images to other AWS Regions for multi-Region
  deployments. Reduces pull latency for globally distributed inference services.
- **Cross-Account replication**: Share images with other AWS accounts. The destination account
  must configure a registry permissions policy granting `ecr:ReplicateImage` and
  `ecr:CreateRepository`.
- Up to 25 unique destinations across all rules, max 10 rules, max 100 filters per rule.
- Replication occurs once per image push/restore. Most images replicate in under 30 minutes.
- Repository policies, IAM policies, and lifecycle policies are NOT replicated (use repository
  creation templates to replicate settings like tag immutability and encryption).
- Replication does not propagate deletes or archive actions.

### Lifecycle Policies

Lifecycle policies automate cleanup of unused images:

```json
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep only last 10 tagged images",
      "selection": {
        "tagStatus": "tagged",
        "tagPatternList": ["v*"],
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    },
    {
      "rulePriority": 2,
      "description": "Expire untagged images older than 7 days",
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 7
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
```

**Archive Storage:**
- Images can be transitioned to archive storage (cheaper) instead of expired.
- Minimum storage duration of 90 days for archived images.
- Archived images cannot be scanned; must be restored first.

---

## 5. Container Deployment Patterns for GenAI

### Pattern 1: Custom Model Serving Container

Deploy a custom inference server (vLLM, TGI, Triton) on ECS with GPU instances.

```
Client Request
    |
    v
ALB (Application Load Balancer)
    |
    v
ECS Service (g6e instances, EC2 launch type)
    |-- Task: vLLM server container (GPU pinned)
    |-- Task: vLLM server container (GPU pinned)
    |
    v
ECR (model + inference server image)
S3 (model weights, loaded at startup or via EFS)
```

**Task Definition Considerations:**
- Use `resourceRequirements` with `type: GPU` to request GPUs.
- Set memory to accommodate the model weights + runtime overhead. A 7B parameter model
  in FP16 needs approximately 14 GB GPU memory; a 70B model needs approximately 140 GB.
- Use placement constraints to target appropriate GPU instances.
- Mount EFS or use S3 for model weight storage (avoids baking weights into the image).
- Set health checks with longer intervals for model loading time.

### Pattern 2: MCP Server Deployment

Deploy MCP servers on ECS for AI agents to use as tools.

```
AI Agent (Bedrock Agent / Strands Agent)
    |
    v (MCP protocol over Streamable HTTP)
    |
ECS Service (Fargate or EC2)
    |-- MCP Server: Database Query Tool
    |-- MCP Server: Web Search Tool
    |-- MCP Server: Code Execution Tool
    |
Service Connect Namespace (short-name discovery)
```

**Fargate for CPU-Only MCP Servers:**
- Most MCP servers (database tools, API integrations, search) are CPU-bound.
- Fargate simplifies operations -- no instance management.
- Scale to zero with Fargate Spot for cost optimization on non-critical tools.

**EC2 for GPU-Enhanced MCP Servers:**
- Some MCP servers may need GPUs (e.g., local embedding generation, image processing tools).
- Use EC2 launch type with GPU instances.

### Pattern 3: AI Microservices Architecture

Decompose an AI application into independently scalable container services.

```
API Gateway
    |
    v
[Orchestrator Service] (ECS/Fargate)
    |
    +---> [Embedding Service] (ECS/Fargate, scales independently)
    +---> [Vector Search Service] (ECS/Fargate)
    +---> [Inference Service] (ECS/EC2 with GPU)
    +---> [Post-Processing Service] (ECS/Fargate)
    |
    All connected via Service Connect namespace
```

**Benefits:**
- Each service scales based on its own bottleneck (GPU utilization for inference,
  CPU for preprocessing, memory for vector search).
- Independent deployment and versioning.
- Fault isolation -- a failure in one service does not cascade.

### Pattern 4: Sidecar Patterns for AI

**Inference Sidecar:**
A lightweight model runs as a sidecar container alongside the main application for low-latency
local inference (e.g., content classification, PII detection).

```json
{
  "containerDefinitions": [
    {
      "name": "main-app",
      "image": "my-app:latest",
      "essential": true,
      "portMappings": [{ "containerPort": 8080 }]
    },
    {
      "name": "pii-detector",
      "image": "my-pii-model:latest",
      "essential": false,
      "portMappings": [{ "containerPort": 9090 }]
    }
  ]
}
```

The main application calls `localhost:9090` for PII detection with no network hop.

**Observability Sidecar:**
AWS Distro for OpenTelemetry (ADOT) collector runs as a sidecar to collect traces, metrics,
and logs from AI inference containers.

**Service Connect Proxy:**
Automatically injected by ECS when using Service Connect. Handles service discovery, load
balancing, retries, and metrics collection.

---

## 6. Exam Gotchas

### ECS vs EKS vs Lambda for AI Workloads

| Scenario | Best Choice | Why |
|---|---|---|
| Simple MCP server (stateless, fast) | **Lambda** | 15-min max, scales to zero, cheapest for sporadic use |
| Complex MCP server (stateful, long-running) | **ECS** | Persistent containers, Service Connect, exam specifically calls this out |
| GPU inference (single node) | **ECS on EC2** | Simpler GPU task definitions, managed scaling |
| Distributed training (multi-node GPU) | **EKS** | Kubernetes-native GPU scheduling, EFA, DRA |
| Existing Kubernetes platform | **EKS** | Organizational consistency |
| Batch preprocessing (no GPU) | **Fargate** or **Lambda** | Serverless, pay per use |

### Common Exam Traps

1. **"Fargate for GPU inference"** -- Wrong. Fargate does not support GPUs. If a question
   mentions GPU requirements, the answer must include EC2 launch type or EKS with GPU nodes.

2. **"ECS vs SageMaker for model hosting"** -- SageMaker endpoints are managed and provide
   built-in model optimization, A/B testing, and auto scaling out of the box. ECS gives you
   full control but requires you to manage the inference server, scaling, and health checks.
   Choose ECS when you need custom inference logic, non-standard model formats, or tight
   integration with other containerized services.

3. **"Fargate for large models"** -- Fargate maxes out at 16 vCPU and 120 GB memory with no
   GPU. Most LLMs above 7B parameters in FP16 need GPU memory, not just system RAM. Even
   CPU-only inference of large models would exceed Fargate's resource limits.

4. **"ECR replication copies everything"** -- Only images pushed or restored AFTER replication
   is configured get replicated. Pre-existing images are not retroactively replicated. Deletes
   and lifecycle policy expirations are also not replicated.

5. **"Service Connect replaces ALB"** -- Service Connect only handles service-to-service
   communication within a namespace. External traffic still needs an ALB or NLB.

6. **"ECS auto scaling is instant"** -- Scaling GPU instances takes several minutes. Over-provision
   (maintain headroom) and use step scaling with aggressive thresholds for latency-sensitive
   AI workloads.

---

## 7. When to Use Each -- Decision Matrix

```
Need GPU? ──Yes──> Need multi-node training? ──Yes──> Amazon EKS (GPU node groups + EFA)
    │                        │
    │                        No
    │                        │
    │                        v
    │               Amazon ECS on EC2 (GPU tasks)
    │
    No
    │
    v
Need persistent containers? ──Yes──> Memory > 120 GB? ──Yes──> ECS on EC2
    │                                       │
    │                                       No
    │                                       │
    │                                       v
    │                                  AWS Fargate
    No
    │
    v
Short-lived / event-driven? ──Yes──> AWS Lambda
    │
    No
    │
    v
AWS Fargate (default serverless container choice)
```

**Quick Reference Table:**

| Workload | Service | Launch Type | Why |
|---|---|---|---|
| LLM inference (7B+ params) | ECS | EC2 (GPU) | GPU required for practical latency |
| Small model inference (CPU) | ECS | Fargate | Serverless, cost-effective |
| MCP server (complex tools) | ECS | Fargate or EC2 | Exam calls out ECS specifically |
| Distributed training | EKS | EC2 (GPU + EFA) | Multi-node GPU coordination |
| Data preprocessing pipeline | ECS | Fargate / Fargate Spot | No GPU needed, cost-sensitive |
| Real-time embedding service | ECS | Fargate (if CPU) or EC2 (if GPU) | Depends on model size |
| Batch inference | ECS or AWS Batch | Fargate Spot or EC2 Spot | Cost optimization |
| Container image storage | ECR | N/A | Managed registry, integrates with ECS/EKS |

---

## 8. TypeScript SDK v3 Usage

### Register a Task Definition (GPU Inference)

```typescript
import {
  ECSClient,
  RegisterTaskDefinitionCommand,
} from "@aws-sdk/client-ecs";

const ecs = new ECSClient({ region: "us-east-1" });

const command = new RegisterTaskDefinitionCommand({
  family: "gpu-inference-task",
  requiresCompatibilities: ["EC2"],
  networkMode: "awsvpc",
  cpu: "4096",
  memory: "16384",
  taskRoleArn: "arn:aws:iam::123456789012:role/ecsTaskRole",
  executionRoleArn: "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  containerDefinitions: [
    {
      name: "inference-server",
      image: "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-model:latest",
      essential: true,
      resourceRequirements: [
        { type: "GPU", value: "1" },
      ],
      portMappings: [
        { containerPort: 8080, protocol: "tcp" },
      ],
      logConfiguration: {
        logDriver: "awslogs",
        options: {
          "awslogs-group": "/ecs/gpu-inference",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "inference",
        },
      },
      environment: [
        { name: "MODEL_ID", value: "my-fine-tuned-model" },
        { name: "NVIDIA_VISIBLE_DEVICES", value: "all" },
      ],
    },
  ],
});

const response = await ecs.send(command);
console.log("Task definition ARN:", response.taskDefinition?.taskDefinitionArn);
```

### Create an ECS Service with Auto Scaling

```typescript
import { ECSClient, CreateServiceCommand } from "@aws-sdk/client-ecs";

const ecs = new ECSClient({ region: "us-east-1" });

const createService = new CreateServiceCommand({
  cluster: "ai-inference-cluster",
  serviceName: "inference-service",
  taskDefinition: "gpu-inference-task",
  desiredCount: 2,
  launchType: "EC2",
  networkConfiguration: {
    awsvpcConfiguration: {
      subnets: ["subnet-abc123", "subnet-def456"],
      securityGroups: ["sg-inference"],
      assignPublicIp: "DISABLED",
    },
  },
  loadBalancers: [
    {
      targetGroupArn: "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/inference-tg/abc123",
      containerName: "inference-server",
      containerPort: 8080,
    },
  ],
  placementConstraints: [
    {
      type: "memberOf",
      expression: "attribute:ecs.instance-type =~ g6e.*",
    },
  ],
  serviceConnectConfiguration: {
    enabled: true,
    namespace: "ai-services",
    services: [
      {
        portName: "inference-port",
        discoveryName: "inference-server",
        clientAliases: [
          { port: 8080, dnsName: "inference-server" },
        ],
      },
    ],
  },
});

const serviceResponse = await ecs.send(createService);
```

### Register Auto Scaling Target

```typescript
import {
  ApplicationAutoScalingClient,
  RegisterScalableTargetCommand,
  PutScalingPolicyCommand,
} from "@aws-sdk/client-application-auto-scaling";

const autoScaling = new ApplicationAutoScalingClient({ region: "us-east-1" });

await autoScaling.send(new RegisterScalableTargetCommand({
  ServiceNamespace: "ecs",
  ResourceId: "service/ai-inference-cluster/inference-service",
  ScalableDimension: "ecs:service:DesiredCount",
  MinCapacity: 1,
  MaxCapacity: 10,
}));

await autoScaling.send(new PutScalingPolicyCommand({
  ServiceNamespace: "ecs",
  ResourceId: "service/ai-inference-cluster/inference-service",
  ScalableDimension: "ecs:service:DesiredCount",
  PolicyName: "cpu-target-tracking",
  PolicyType: "TargetTrackingScaling",
  TargetTrackingScalingPolicyConfiguration: {
    TargetValue: 70.0,
    PredefinedMetricSpecification: {
      PredefinedMetricType: "ECSServiceAverageCPUUtilization",
    },
    ScaleInCooldown: 300,
    ScaleOutCooldown: 60,
  },
}));
```

### Push Image to ECR

```typescript
import {
  ECRClient,
  GetAuthorizationTokenCommand,
  CreateRepositoryCommand,
  DescribeRepositoriesCommand,
} from "@aws-sdk/client-ecr";

const ecr = new ECRClient({ region: "us-east-1" });

// Create repository with scanning and immutability
await ecr.send(new CreateRepositoryCommand({
  repositoryName: "my-inference-server",
  imageScanningConfiguration: { scanOnPush: true },
  imageTagMutability: "IMMUTABLE",
  encryptionConfiguration: {
    encryptionType: "KMS",
    kmsKey: "arn:aws:kms:us-east-1:123456789012:key/my-key-id",
  },
}));

// Get auth token for Docker login
const authResponse = await ecr.send(new GetAuthorizationTokenCommand({}));
const token = authResponse.authorizationData?.[0]?.authorizationToken;
// Decode and use with `docker login`
```

---

## 9. Key Metrics -- CloudWatch

### Built-in ECS Metrics (AWS/ECS namespace)

| Metric | Dimensions | Description |
|---|---|---|
| `CPUUtilization` | ClusterName, ServiceName | Percentage of CPU units used by tasks vs reserved |
| `MemoryUtilization` | ClusterName, ServiceName | Percentage of memory used by tasks vs reserved |
| `CPUReservation` | ClusterName | Percentage of CPU reserved by tasks vs total registered (EC2 only) |
| `MemoryReservation` | ClusterName | Percentage of memory reserved by tasks vs total registered (EC2 only) |
| `GPUReservation` | ClusterName | Percentage of GPUs reserved by tasks vs total available (EC2 only) |
| `EBSFilesystemUtilization` | ClusterName, ServiceName | EBS storage used vs allocated |

### Container Insights Metrics (ECS/ContainerInsights namespace)

Requires enabling Container Insights on the cluster. Additional cost but provides per-task
and per-container visibility.

| Metric | Description |
|---|---|
| `CpuUtilized` / `CpuReserved` | Absolute CPU units used/reserved |
| `MemoryUtilized` / `MemoryReserved` | Absolute memory bytes used/reserved |
| `NetworkRxBytes` / `NetworkTxBytes` | Network I/O per task |
| `StorageReadBytes` / `StorageWriteBytes` | Storage I/O per task |
| `RunningTaskCount` / `PendingTaskCount` | Task status counts |
| `DesiredTaskCount` | Target task count for the service |
| `ContainerInstanceCount` | Number of EC2 instances in the cluster |

### Service Connect Metrics

When Service Connect is enabled, additional metrics are published:

| Metric | Description |
|---|---|
| `ActiveConnectionCount` | Current active connections to the service |
| `NewConnectionCount` | New connections per period |
| `RequestCount` / `GrpcRequestCount` | Total HTTP/gRPC requests |
| `HTTPCode_Target_2XX/4XX/5XX_Count` | Response code distribution |
| `TargetResponseTime` | Latency from the proxy to the service |
| `RequestCountPerTarget` | Requests per individual task |

### Cluster Auto Scaling Metric

| Metric | Namespace | Description |
|---|---|---|
| `CapacityProviderReservation` | AWS/ECS/ManagedScaling | Percent of container instances in use for a capacity provider. Drives the auto scaling policy. |

### AI-Relevant Custom Metrics

For GPU inference workloads, publish custom metrics via CloudWatch agent or Container Insights:

| Custom Metric | What It Measures | Scaling Signal |
|---|---|---|
| GPU Utilization (%) | How busy the GPU compute cores are | Scale out if consistently > 80% |
| GPU Memory Utilization (%) | VRAM usage | Indicates model size vs instance capacity |
| Inference Latency (p50/p95/p99) | End-to-end inference time | Scale out if p99 exceeds SLA |
| Tokens Per Second | Throughput of LLM inference | Core performance metric |
| Queue Depth | Pending inference requests | Leading indicator for scale-out |
| Batch Size | Requests batched per inference call | Tuning metric for throughput vs latency |

---

## Summary -- Key Facts for Exam Day

1. **GPU inference requires EC2 launch type** (ECS) or GPU node groups (EKS). Fargate has no GPU support.
2. **ECS is specifically called out for MCP servers** providing complex tools to AI agents (Task 2.1.7).
3. **Fargate maxes out at 16 vCPU / 120 GB memory** -- insufficient for large Foundation Models.
4. **Service Connect** provides service mesh capabilities without external tools -- uses Cloud Map
   namespaces for short-name discovery between AI microservices.
5. **ECR Enhanced Scanning** (via Inspector) scans both OS and language package vulnerabilities.
   Basic scanning only covers OS packages.
6. **ECR replication** is push-only (not retroactive), does not replicate deletes, and does not
   replicate policies.
7. **ECS GPU task definitions** use `resourceRequirements` with `type: GPU` and a `value` string.
8. **Cluster auto scaling** uses `CapacityProviderReservation` metric with target tracking.
   Use `binpack` strategy to maximize GPU utilization per instance.
9. **Fargate Spot** offers up to 70% savings for interrupt-tolerant AI batch workloads.
10. **SOCI (Seekable OCI)** enables lazy loading of large container images on Fargate, reducing
    cold start time for AI containers with large images.
