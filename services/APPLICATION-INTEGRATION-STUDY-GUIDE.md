# Application Integration Services -- Comprehensive Study Guide (AIP-C01)

Application integration services orchestrate, decouple, and connect the components of generative AI applications. **AWS Step Functions is one of the most heavily tested services** on the exam, referenced in nearly every task statement across both domains. EventBridge, SQS, SNS, AppFlow, and AppConfig appear in targeted scenarios.

---

## 1. AWS Step Functions (Heavily Tested)

### 1.1 Overview

AWS Step Functions is a **serverless workflow orchestration service** that coordinates distributed applications and microservices using visual state machines. For GenAI, it is the primary mechanism for building deterministic, auditable AI workflows.

**Core Exam Relevance:**
- Task 1.2.3: Circuit breaker patterns for resilient AI systems
- Task 1.5.5: Query transformation workflows
- Task 1.6.2: Clarification workflows
- Task 1.6.6: Sequential prompt chains
- Task 2.1.1: Agent orchestration
- Task 2.1.2: ReAct patterns, chain-of-thought reasoning
- Task 2.1.3: Stopping conditions for AI workflows
- Task 2.1.5: Human review/approval processes
- Task 2.4.4: Dynamic content-based routing
- Task 2.5.3: Document processing systems
- Task 2.5.5: Agent design patterns

### 1.2 Standard vs Express Workflows

| Feature | Standard | Express |
|---|---|---|
| **Max duration** | 1 year | 5 minutes |
| **Execution model** | Exactly-once | At-least-once (async), At-most-once (sync) |
| **Pricing** | Per state transition | Per execution + duration + memory |
| **Integration patterns** | Request Response, Run a Job (.sync), Wait for Callback (.waitForTaskToken) | Request Response only |
| **Execution history** | 90-day retention in console | CloudWatch Logs only |
| **Max executions/sec** | ~2,000 | ~100,000 |
| **Use case** | Long-running AI workflows, human approval, agent loops | High-volume event processing, real-time inference pipelines |

**When to use which for GenAI:**
- **Standard**: Prompt chaining with human-in-the-loop, agent orchestration with ReAct loops, circuit breaker patterns, any workflow needing `.waitForTaskToken` or `.sync`
- **Express**: High-throughput document classification, real-time inference routing, short AI pipelines under 5 minutes

**Exam Gotcha**: Express Workflows do NOT support `.sync` or `.waitForTaskToken` integration patterns. If a question involves waiting for human approval or waiting for a Bedrock model customization job to complete, the answer is Standard Workflow.

**Exam Gotcha**: You can nest Express Workflows inside Standard Workflows to optimize cost for high-throughput sub-steps within a longer orchestration.

### 1.3 Bedrock Integration (Optimized Integration)

Step Functions has an **optimized integration** with Amazon Bedrock, meaning you can invoke Bedrock directly from a Task state without needing a Lambda function intermediary.

**Supported Bedrock APIs:**

| API | Integration Patterns | Use Case |
|---|---|---|
| `InvokeModel` | Request Response, Run a Job (.sync), Wait for Callback (.waitForTaskToken) | Inference on any FM |
| `CreateModelCustomizationJob` | Request Response | Start fine-tuning job |
| `CreateModelCustomizationJob.sync` | Run a Job (.sync) | Wait for fine-tuning to complete |

**Key InvokeModel features specific to Step Functions:**
- **`Body`**: Inline model input payload (up to 256 KiB)
- **`Input.S3Uri`**: Read input from S3 (for payloads > 256 KiB)
- **`Output.S3Uri`**: Write output to S3 (for large responses)
- You can specify `Body` OR `Input`, but not both

**Task state definition for Bedrock InvokeModel:**

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::bedrock:invokeModel",
  "Arguments": {
    "ModelId": "anthropic.claude-sonnet-4-20250514",
    "Body": {
      "anthropic_version": "bedrock-2023-05-31",
      "max_tokens": 1024,
      "messages": [
        {
          "role": "user",
          "content": "{% $states.input.userPrompt %}"
        }
      ]
    },
    "ContentType": "application/json",
    "Accept": "application/json"
  },
  "Output": {
    "result": "{% $states.result.Body.content[0].text %}"
  },
  "Next": "NextState"
}
```

**TypeScript SDK v3 -- Starting a Step Functions execution that invokes Bedrock:**

```typescript
import { SFNClient, StartExecutionCommand } from "@aws-sdk/client-sfn";

const sfnClient = new SFNClient({ region: "us-east-1" });

const response = await sfnClient.send(
  new StartExecutionCommand({
    stateMachineArn: "arn:aws:states:us-east-1:123456789012:stateMachine:BedrockPromptChain",
    input: JSON.stringify({
      userPrompt: "Summarize the key benefits of serverless architecture",
      modelId: "anthropic.claude-sonnet-4-20250514",
    }),
  })
);
```

**IAM policy for Step Functions to call Bedrock InvokeModel:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-20250514"
      ]
    }
  ]
}
```

**Exam Gotcha**: Scope IAM policies to specific model ARNs. Do not use wildcards in production. The exam tests whether you know to restrict `bedrock:InvokeModel` to specific foundation model or provisioned model ARNs.

### 1.4 Circuit Breaker Pattern for FM Resilience

The circuit breaker pattern prevents cascading failures when a foundation model endpoint is unavailable, throttled, or experiencing high latency. This is **directly tested** in Task 1.2.3.

**How it works with Step Functions + DynamoDB:**

1. **Caller** starts a Step Functions Express Workflow with the callee service name
2. **Get Circuit Status** step reads from a DynamoDB `CircuitStatus` table
3. If an unexpired record exists for the callee, the circuit is **OPEN** -- return immediate failure
4. If no record exists (or record expired), the circuit is **CLOSED** -- proceed with the call
5. If the call **fails** after retries with exponential backoff, insert a record with `ExpiryTimeStamp` into DynamoDB
6. DynamoDB **TTL** automatically cleans expired records, eventually closing the circuit

**State machine logic (Amazon States Language):**

```json
{
  "Is Circuit Closed": {
    "Type": "Choice",
    "Choices": [
      {
        "Variable": "$.CircuitStatus",
        "StringEquals": "OPEN",
        "Next": "Circuit Open"
      },
      {
        "Variable": "$.CircuitStatus",
        "StringEquals": "",
        "Next": "Execute Model Call"
      }
    ]
  },
  "Circuit Open": {
    "Type": "Fail",
    "Error": "CircuitBreakerOpen",
    "Cause": "The circuit is open. The callee service is degraded."
  },
  "Execute Model Call": {
    "Type": "Task",
    "Resource": "arn:aws:states:::bedrock:invokeModel",
    "Arguments": {
      "ModelId": "{% $states.input.modelId %}",
      "Body": {
        "prompt": "{% $states.input.prompt %}"
      }
    },
    "Retry": [
      {
        "ErrorEquals": ["States.TaskFailed"],
        "IntervalSeconds": 2,
        "MaxAttempts": 3,
        "BackoffRate": 2,
        "JitterStrategy": "FULL"
      }
    ],
    "Catch": [
      {
        "ErrorEquals": ["States.ALL"],
        "Next": "Open Circuit"
      }
    ],
    "Next": "Success"
  }
}
```

**GenAI-specific circuit breaker scenarios:**
- FM endpoint returns `ThrottlingException` repeatedly -- trip the circuit, fall back to a lighter model
- Bedrock returns `ModelTimeoutException` -- trip the circuit, return cached response
- Model customization job fails -- trip the circuit, continue using base model

**Exam Gotcha**: The circuit breaker uses DynamoDB TTL for automatic circuit closure. Express Workflows are recommended for the circuit breaker itself because they are cheaper for high-throughput calls. The parent orchestration workflow should be Standard if it needs human approval or long-running coordination.

### 1.5 ReAct Pattern Implementation

The **ReAct (Reasoning + Acting)** pattern is a fundamental agentic AI design tested in Task 2.1.2. Step Functions can implement this as a deterministic loop.

**Pattern:** Thought -> Action -> Observation -> Repeat until done

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Reasoning  │────>│  Tool/Action │────>│  Observation    │
│  (Bedrock)  │     │  (Lambda)    │     │  (Parse Result) │
└─────────────┘     └──────────────┘     └─────────────────┘
       ^                                          │
       │              ┌───────────┐               │
       └──────────────│ Continue? │<──────────────┘
                      └───────────┘
                        │ Done
                        v
                  ┌───────────┐
                  │  Output   │
                  └───────────┘
```

**Step Functions implementation approach:**
1. **Reasoning State** (Task): Call Bedrock with the current context, ask it to decide the next action
2. **Choice State**: Evaluate the model's decision -- does it want to use a tool, or is it done?
3. **Action State** (Task): Execute the selected tool via Lambda or direct SDK integration
4. **Observation State** (Pass): Append the tool result to the conversation context
5. **Loop back** to Reasoning State

**Stopping conditions (Task 2.1.3):**
- `TimeoutSeconds` on the overall state machine execution
- `MaxAttempts` limit on the reasoning loop (use a counter variable with a Choice state)
- `HeartbeatSeconds` on individual Task states to detect hung tasks
- Choice state checking iteration count against a configured maximum

**Exam Gotcha**: The exam distinguishes between Step Functions ReAct (deterministic, auditable, developer-defined loop structure) and Bedrock Agents ReAct (AI-native, model decides the flow). Use Step Functions when you need full control and auditability. Use Bedrock Agents when you need semantic flexibility.

### 1.6 Human-in-the-Loop Patterns

Human review and approval (Task 2.1.5) use the **Wait for Callback with Task Token** pattern. This is only available in Standard Workflows.

**How it works:**
1. Task state sends a message containing a **task token** to SQS, SNS, or Lambda
2. Step Functions **pauses** the execution (up to 1 year)
3. An external process (human reviewer via web app, email link, etc.) processes the request
4. The external process calls `SendTaskSuccess` or `SendTaskFailure` with the task token
5. Step Functions **resumes** the execution

**Task state with callback token:**

```json
{
  "Wait for Human Review": {
    "Type": "Task",
    "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
    "Parameters": {
      "QueueUrl": "https://sqs.us-east-1.amazonaws.com/123456789012/human-review-queue",
      "MessageBody": {
        "taskToken.$": "$$.Task.Token",
        "generatedContent.$": "$.modelOutput",
        "reviewType": "content-safety"
      }
    },
    "HeartbeatSeconds": 3600,
    "TimeoutSeconds": 86400,
    "Next": "Process Approved Content"
  }
}
```

**TypeScript SDK v3 -- Sending task success from a reviewer application:**

```typescript
import { SFNClient, SendTaskSuccessCommand } from "@aws-sdk/client-sfn";

const sfnClient = new SFNClient({ region: "us-east-1" });

await sfnClient.send(
  new SendTaskSuccessCommand({
    taskToken: event.taskToken,
    output: JSON.stringify({
      approved: true,
      reviewerNotes: "Content meets safety guidelines",
    }),
  })
);
```

**GenAI use cases for human-in-the-loop:**
- Content safety review before publishing AI-generated content
- Fact-checking AI summaries before sending to customers
- Approval of AI-generated code changes before deployment
- Review of AI-extracted data from documents before database updates
- Movie idea pitch workflow: AI generates ideas, human selects favorites, AI refines

**Exam Gotcha**: The task token is accessed via `$$.Task.Token` (the Context Object, using `$$`), not from the input. `HeartbeatSeconds` sends periodic keep-alive signals; if no heartbeat is received within the interval, the task fails with `States.HeartbeatTimeout`. This is different from `TimeoutSeconds` which is the total allowed wait time.

### 1.7 Chain-of-Thought Reasoning Workflows

Chain-of-thought (CoT) decomposes complex reasoning into sequential steps, each building on the previous output. Step Functions implements this as a linear sequence of Bedrock InvokeModel calls.

**Pattern: Sequential Prompt Chain**

```json
{
  "Comment": "Chain-of-thought: Analyze, Plan, Execute, Verify",
  "StartAt": "Step 1 - Analyze Problem",
  "States": {
    "Step 1 - Analyze Problem": {
      "Type": "Task",
      "Resource": "arn:aws:states:::bedrock:invokeModel",
      "Arguments": {
        "ModelId": "anthropic.claude-sonnet-4-20250514",
        "Body": {
          "messages": [{"role": "user", "content": "Analyze this problem: {% $states.input.problem %}"}],
          "max_tokens": 1024
        }
      },
      "Output": {
        "analysis": "{% $states.result.Body.content[0].text %}",
        "originalProblem": "{% $states.input.problem %}"
      },
      "Next": "Step 2 - Generate Plan"
    },
    "Step 2 - Generate Plan": {
      "Type": "Task",
      "Resource": "arn:aws:states:::bedrock:invokeModel",
      "Arguments": {
        "ModelId": "anthropic.claude-sonnet-4-20250514",
        "Body": {
          "messages": [{"role": "user", "content": "Based on this analysis: {% $states.input.analysis %}\nGenerate a solution plan."}],
          "max_tokens": 1024
        }
      },
      "Output": {
        "plan": "{% $states.result.Body.content[0].text %}",
        "analysis": "{% $states.input.analysis %}"
      },
      "Next": "Step 3 - Execute Plan"
    },
    "Step 3 - Execute Plan": {
      "Type": "Task",
      "Resource": "arn:aws:states:::bedrock:invokeModel",
      "Arguments": {
        "ModelId": "anthropic.claude-sonnet-4-20250514",
        "Body": {
          "messages": [{"role": "user", "content": "Execute this plan: {% $states.input.plan %}"}],
          "max_tokens": 2048
        }
      },
      "Next": "Step 4 - Verify Result"
    },
    "Step 4 - Verify Result": {
      "Type": "Task",
      "Resource": "arn:aws:states:::bedrock:invokeModel",
      "Arguments": {
        "ModelId": "anthropic.claude-sonnet-4-20250514",
        "Body": {
          "messages": [{"role": "user", "content": "Verify and critique: {% $states.input.result %}"}],
          "max_tokens": 1024
        }
      },
      "End": true
    }
  }
}
```

### 1.8 Prompt Chaining with Step Functions

The AWS Bedrock Serverless Prompt Chaining reference architecture demonstrates six patterns:

| Pattern | Description | Step Functions Feature |
|---|---|---|
| **Sequential chain** | Write a novel analysis (prompt 1 output feeds prompt 2) | Linear state sequence |
| **Iterative processing** | Generate a short story (process a list of AI-generated items) | Map state |
| **Parallel prompts** | Create a vacation itinerary (parallelize distinct prompts) | Parallel state |
| **Backtracking** | Pitch movie ideas (go back to a previous step) | Choice state with loop |
| **Human input** | Movie producer approval (pause for human decision) | `.waitForTaskToken` |
| **Multi-agent chain** | Find trending GitHub repos (chain multiple AI agents with APIs) | Sequential tasks with Lambda |

**Parallel prompt execution:**

```json
{
  "Generate Multiple Perspectives": {
    "Type": "Parallel",
    "Branches": [
      {
        "StartAt": "Optimistic Analysis",
        "States": {
          "Optimistic Analysis": {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeModel",
            "Arguments": {
              "ModelId": "anthropic.claude-sonnet-4-20250514",
              "Body": {
                "messages": [{"role": "user", "content": "Give an optimistic analysis of: {% $states.input.topic %}"}]
              }
            },
            "End": true
          }
        }
      },
      {
        "StartAt": "Critical Analysis",
        "States": {
          "Critical Analysis": {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeModel",
            "Arguments": {
              "ModelId": "anthropic.claude-sonnet-4-20250514",
              "Body": {
                "messages": [{"role": "user", "content": "Give a critical analysis of: {% $states.input.topic %}"}]
              }
            },
            "End": true
          }
        }
      }
    ],
    "Next": "Synthesize Perspectives"
  }
}
```

**Exam Gotcha**: Step Functions prompt chaining uses the **optimized Bedrock integration** (no Lambda needed). This is different from Bedrock Prompt Flows (which uses a visual flow builder within the Bedrock console). The exam may ask you to choose between them: use Step Functions for complex orchestration with error handling, human approval, and conditional branching; use Prompt Flows for simpler linear/branching flows managed entirely within Bedrock.

### 1.9 Dynamic Model Routing

Task 2.4.4 tests dynamic content-based routing. Step Functions can route requests to different models based on input characteristics.

```json
{
  "Route by Complexity": {
    "Type": "Choice",
    "Choices": [
      {
        "Variable": "$.complexity",
        "StringEquals": "simple",
        "Next": "Invoke Haiku"
      },
      {
        "Variable": "$.complexity",
        "StringEquals": "complex",
        "Next": "Invoke Sonnet"
      },
      {
        "Variable": "$.inputTokenCount",
        "NumericGreaterThan": 100000,
        "Next": "Invoke Long Context Model"
      }
    ],
    "Default": "Invoke Sonnet"
  }
}
```

**Dynamic routing strategies for GenAI:**
- **Cost-based**: Route simple queries to cheaper models (Haiku/Nova Micro), complex to capable models (Sonnet/Nova Pro)
- **Latency-based**: Route real-time chat to fast models, batch processing to powerful models
- **Content-based**: Route code questions to code-specialized models, creative writing to general models
- **Fallback**: If primary model throttles, fall back to secondary model (combine with circuit breaker)
- **A/B testing**: Route percentage of traffic to different models for evaluation

### 1.10 Error Handling (Catch, Retry with Backoff)

Step Functions provides sophisticated error handling that is critical for resilient AI systems.

**Retry fields:**

| Field | Default | Description |
|---|---|---|
| `ErrorEquals` | Required | Array of error names to match |
| `IntervalSeconds` | 1 | Seconds before first retry |
| `MaxAttempts` | 3 | Maximum number of retries |
| `BackoffRate` | 2.0 | Multiplier for interval between retries |
| `MaxDelaySeconds` | None | Cap on the exponential backoff delay |
| `JitterStrategy` | `NONE` | `FULL` randomizes delays to prevent thundering herd |

**Built-in error names relevant to GenAI workloads:**

| Error Name | Description |
|---|---|
| `States.ALL` | Wildcard for any error (except `States.DataLimitExceeded` and `States.Runtime`) |
| `States.TaskFailed` | Wildcard for task failures (except `States.Timeout`) |
| `States.Timeout` | Task exceeded `TimeoutSeconds` or missed `HeartbeatSeconds` |
| `States.HeartbeatTimeout` | Task failed to send heartbeat within `HeartbeatSeconds` |
| `States.DataLimitExceeded` | Payload exceeded 256 KiB (terminal, cannot be caught by `States.ALL`) |
| `States.Runtime` | Runtime processing error (terminal, cannot be caught by `States.ALL`) |

**Retry pattern for Bedrock throttling:**

```json
{
  "Invoke Model": {
    "Type": "Task",
    "Resource": "arn:aws:states:::bedrock:invokeModel",
    "Arguments": {
      "ModelId": "anthropic.claude-sonnet-4-20250514",
      "Body": { "messages": [{"role": "user", "content": "{% $states.input.prompt %}"}] }
    },
    "Retry": [
      {
        "ErrorEquals": ["Bedrock.ThrottlingException"],
        "IntervalSeconds": 3,
        "MaxAttempts": 5,
        "BackoffRate": 2,
        "JitterStrategy": "FULL",
        "MaxDelaySeconds": 30
      },
      {
        "ErrorEquals": ["States.Timeout"],
        "IntervalSeconds": 5,
        "MaxAttempts": 2,
        "BackoffRate": 1
      },
      {
        "ErrorEquals": ["States.ALL"],
        "IntervalSeconds": 1,
        "MaxAttempts": 2,
        "BackoffRate": 2
      }
    ],
    "Catch": [
      {
        "ErrorEquals": ["Bedrock.ThrottlingException"],
        "Next": "Fallback to Secondary Model"
      },
      {
        "ErrorEquals": ["States.ALL"],
        "Next": "Handle Error"
      }
    ],
    "TimeoutSeconds": 120,
    "Next": "Process Response"
  }
}
```

**Exam Gotcha**: Retriers are evaluated **in order**. Put specific errors first, `States.ALL` last. `States.ALL` does NOT catch `States.DataLimitExceeded` or `States.Runtime` -- these are terminal errors. Retries count as state transitions and affect billing for Standard Workflows.

**Exam Gotcha**: `JitterStrategy: "FULL"` randomizes the retry interval between 0 and the calculated backoff delay. This prevents the thundering herd problem when multiple concurrent executions all retry at the same interval.

### 1.11 Stopping Conditions and Timeout Mechanisms

Task 2.1.3 specifically tests stopping conditions for AI workflows.

**Available mechanisms:**

| Mechanism | Scope | Behavior |
|---|---|---|
| `TimeoutSeconds` (state level) | Individual task | Task fails with `States.Timeout` if it exceeds this duration |
| `TimeoutSeconds` (top level) | Entire state machine | Entire execution fails if total duration exceeds this |
| `HeartbeatSeconds` | Task with callback | Task fails with `States.HeartbeatTimeout` if no heartbeat received |
| `MaxAttempts` (in Retry) | Retry loop | Stop retrying after N attempts |
| Counter + Choice state | Reasoning loop | Manual iteration limit for ReAct/CoT patterns |

**Iteration limit pattern for ReAct loops:**

```json
{
  "Check Iteration Limit": {
    "Type": "Choice",
    "Choices": [
      {
        "Variable": "$.iterationCount",
        "NumericGreaterThanEquals": 10,
        "Next": "Force Final Answer"
      }
    ],
    "Default": "Continue Reasoning"
  },
  "Continue Reasoning": {
    "Type": "Task",
    "Resource": "arn:aws:states:::bedrock:invokeModel",
    "Arguments": {
      "ModelId": "anthropic.claude-sonnet-4-20250514",
      "Body": {
        "messages": [{"role": "user", "content": "{% $states.input.context %}"}]
      }
    },
    "Next": "Increment Counter"
  },
  "Increment Counter": {
    "Type": "Pass",
    "Arguments": {
      "iterationCount": "{% $states.input.iterationCount + 1 %}",
      "context": "{% $states.input.context %}"
    },
    "Next": "Check Iteration Limit"
  }
}
```

### 1.12 Document Processing Workflows

Task 2.5.3 tests document processing systems. Step Functions orchestrates multi-step document pipelines.

**Typical document processing workflow:**
1. **Event trigger**: S3 upload triggers EventBridge rule, which starts Step Functions
2. **Document classification**: Bedrock classifies document type (invoice, contract, report)
3. **Text extraction**: Amazon Textract extracts text and tables (`.sync` pattern to wait for completion)
4. **Entity extraction**: Bedrock or Comprehend extracts named entities
5. **Summarization**: Bedrock generates a summary
6. **Quality check**: Parallel state runs multiple validation checks
7. **Storage**: Write results to OpenSearch for search, DynamoDB for metadata

**Distributed Map for bulk processing:**

```json
{
  "Process Document Batch": {
    "Type": "Map",
    "ItemProcessor": {
      "ProcessorConfig": {
        "Mode": "DISTRIBUTED",
        "ExecutionType": "EXPRESS"
      },
      "StartAt": "Process Single Document",
      "States": {
        "Process Single Document": {
          "Type": "Task",
          "Resource": "arn:aws:states:::bedrock:invokeModel",
          "Arguments": {
            "ModelId": "anthropic.claude-sonnet-4-20250514",
            "Body": {
              "messages": [{"role": "user", "content": "Extract key data from: {% $states.input.documentText %}"}]
            }
          },
          "End": true
        }
      }
    },
    "ItemReader": {
      "Resource": "arn:aws:states:::s3:getObject",
      "Parameters": {
        "Bucket": "my-documents-bucket",
        "Key": "manifest.json"
      }
    },
    "MaxConcurrency": 100,
    "ToleratedFailurePercentage": 5,
    "Next": "Aggregate Results"
  }
}
```

**Exam Gotcha**: Distributed Map state can launch up to 10,000 parallel child executions (Express Workflows) for bulk document processing. `ToleratedFailurePercentage` allows the overall workflow to succeed even if some documents fail.

### 1.13 Key Metrics for Step Functions

| Metric | Description | Alarm Threshold Guidance |
|---|---|---|
| `ExecutionsFailed` | Number of failed executions | > 0 for critical workflows |
| `ExecutionsTimedOut` | Executions that hit timeout | Monitor for AI workload latency |
| `ExecutionThrottled` | Executions throttled by quotas | Indicates capacity issues |
| `ExecutionTime` | Duration of execution | Monitor P99 for SLA compliance |
| `LambdaFunctionsFailed` | Lambda failures within workflow | Correlate with Bedrock throttling |

---

## 2. Amazon EventBridge

### 2.1 Event-Driven AI Architectures

Amazon EventBridge is a **serverless event bus** that routes events from sources to targets based on rules. It is the backbone of event-driven AI architectures (Task 2.3.2).

**Core concepts:**
- **Event bus**: A pipeline that receives events (default bus, custom bus, partner bus)
- **Rules**: Pattern-match on events and route to targets
- **Targets**: What gets invoked when a rule matches (Lambda, Step Functions, SQS, SNS, etc.)
- **Event patterns**: JSON-based filters that match event structure
- **Schema registry**: Automatically discovers and stores event schemas

### 2.2 Event Patterns for GenAI Applications

**S3 upload triggers AI processing:**

```json
{
  "source": ["aws.s3"],
  "detail-type": ["Object Created"],
  "detail": {
    "bucket": {
      "name": ["documents-for-processing"]
    },
    "object": {
      "key": [{ "suffix": ".pdf" }]
    }
  }
}
```

**Bedrock model customization job completion:**

```json
{
  "source": ["aws.bedrock"],
  "detail-type": ["Bedrock Model Customization Job State Change"],
  "detail": {
    "status": ["Completed", "Failed"]
  }
}
```

**SageMaker training job completion (for custom models):**

```json
{
  "source": ["aws.sagemaker"],
  "detail-type": ["SageMaker Training Job State Change"],
  "detail": {
    "TrainingJobStatus": ["Completed", "Failed"]
  }
}
```

### 2.3 Integration with Bedrock, Lambda, Step Functions

**Common GenAI event-driven patterns:**

| Trigger | EventBridge Rule | Target | Use Case |
|---|---|---|---|
| S3 document upload | Match `Object Created` | Step Functions | Document processing pipeline |
| Bedrock job complete | Match status change | Lambda | Post-processing fine-tuned model |
| CloudWatch alarm | Match alarm state | SNS + Lambda | Model performance degradation alert |
| Custom app event | Match custom detail-type | Step Functions | User request triggers AI workflow |
| Scheduled rule | Cron/rate expression | Lambda | Periodic knowledge base refresh |

**TypeScript SDK v3 -- Creating an EventBridge rule for S3 -> Step Functions:**

```typescript
import {
  EventBridgeClient,
  PutRuleCommand,
  PutTargetsCommand,
} from "@aws-sdk/client-eventbridge";

const ebClient = new EventBridgeClient({ region: "us-east-1" });

await ebClient.send(
  new PutRuleCommand({
    Name: "DocumentUploadRule",
    EventPattern: JSON.stringify({
      source: ["aws.s3"],
      "detail-type": ["Object Created"],
      detail: {
        bucket: { name: ["ai-documents"] },
        object: { key: [{ suffix: ".pdf" }] },
      },
    }),
    State: "ENABLED",
  })
);

await ebClient.send(
  new PutTargetsCommand({
    Rule: "DocumentUploadRule",
    Targets: [
      {
        Id: "StepFunctionsTarget",
        Arn: "arn:aws:states:us-east-1:123456789012:stateMachine:DocProcessing",
        RoleArn: "arn:aws:iam::123456789012:role/EventBridgeStepFunctionsRole",
      },
    ],
  })
);
```

### 2.4 Exam Gotchas for EventBridge

- EventBridge rules match on **event patterns** (content-based filtering), not message attributes like SNS
- EventBridge can have up to **5 targets per rule** (use multiple rules for more)
- EventBridge **guarantees at-least-once delivery** to targets
- EventBridge has a **built-in archive and replay** feature for reprocessing events
- Step Functions is an **optimized integration** target for EventBridge (can pass the full event as input)
- For cross-account event routing, use **cross-account event bus** patterns

---

## 3. Amazon SQS

### 3.1 Async Inference Patterns

Amazon SQS decouples AI request producers from consumers, enabling asynchronous processing (Task 2.4.1).

**Standard Queue vs FIFO Queue for AI Workloads:**

| Feature | Standard | FIFO |
|---|---|---|
| **Throughput** | Nearly unlimited | 300 msg/s (3,000 with batching, higher with high throughput mode) |
| **Ordering** | Best-effort | Strict ordering within message group |
| **Delivery** | At-least-once (possible duplicates) | Exactly-once processing |
| **Use case** | High-volume inference, document processing | Ordered conversation turns, sequential processing |
| **AI example** | Batch image generation requests | Chat messages that must be processed in order |

**Async inference pattern with SQS:**

```
Producer -> SQS Queue -> Lambda (consumer) -> Bedrock InvokeModel -> Result Store (DynamoDB/S3)
                |
                v
          Dead Letter Queue (failed requests)
```

**TypeScript SDK v3 -- Sending AI inference request to SQS:**

```typescript
import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";

const sqsClient = new SQSClient({ region: "us-east-1" });

await sqsClient.send(
  new SendMessageCommand({
    QueueUrl: "https://sqs.us-east-1.amazonaws.com/123456789012/ai-inference-queue",
    MessageBody: JSON.stringify({
      requestId: "req-12345",
      prompt: "Generate a product description for...",
      modelId: "anthropic.claude-sonnet-4-20250514",
      callbackUrl: "https://api.example.com/results",
    }),
    MessageAttributes: {
      Priority: {
        DataType: "String",
        StringValue: "high",
      },
    },
  })
);
```

### 3.2 Dead Letter Queues for Failed AI Requests

DLQs capture messages that fail processing after a configured number of attempts.

**Configuration:**
- Set `maxReceiveCount` in the **redrive policy** (e.g., 3 attempts before DLQ)
- DLQ retention period should be **longer** than the source queue retention
- Use CloudWatch alarm on `ApproximateNumberOfMessagesVisible` in the DLQ to alert on failures

**Redrive policy setup:**

```typescript
import { SQSClient, SetQueueAttributesCommand } from "@aws-sdk/client-sqs";

const sqsClient = new SQSClient({ region: "us-east-1" });

await sqsClient.send(
  new SetQueueAttributesCommand({
    QueueUrl: "https://sqs.us-east-1.amazonaws.com/123456789012/ai-inference-queue",
    Attributes: {
      RedrivePolicy: JSON.stringify({
        deadLetterTargetArn:
          "arn:aws:sqs:us-east-1:123456789012:ai-inference-dlq",
        maxReceiveCount: "3",
      }),
    },
  })
);
```

**GenAI-specific DLQ scenarios:**
- Bedrock throttling exhausts retries -- message goes to DLQ for later reprocessing
- Malformed prompt causes repeated model errors -- DLQ captures for investigation
- Payload too large for model context window -- DLQ captures for chunking/retry with different approach

**Exam Gotcha**: DLQ for FIFO queues must also be FIFO. DLQ for Standard queues must be Standard. Using a DLQ with a FIFO queue can break message ordering, so only use when order is not critical for failed messages.

### 3.3 SQS with Step Functions

SQS has an **optimized integration** with Step Functions supporting both Request Response and Wait for Callback patterns.

- **Request Response**: `arn:aws:states:::sqs:sendMessage` -- sends a message and continues
- **Wait for Callback**: `arn:aws:states:::sqs:sendMessage.waitForTaskToken` -- sends message with task token, pauses until callback

### 3.4 Key Metrics for SQS

| Metric | Description | Alarm Guidance |
|---|---|---|
| `ApproximateNumberOfMessagesVisible` | Messages available for processing | High count = consumers can't keep up |
| `ApproximateAgeOfOldestMessage` | Age of oldest message | High age = processing backlog |
| `NumberOfMessagesSent` | Messages sent to queue | Baseline for throughput monitoring |
| `ApproximateNumberOfMessagesNotVisible` | Messages being processed (in-flight) | Monitor against SQS limits |
| DLQ `ApproximateNumberOfMessagesVisible` | Failed messages | > 0 triggers investigation |

---

## 4. Amazon SNS

### 4.1 Notification Patterns for AI Workflows

Amazon SNS is a **pub/sub messaging service** for fan-out notifications and decoupled communication.

**GenAI notification patterns:**
- **Model completion notification**: SNS topic receives completion event, fans out to multiple subscribers (email, Slack webhook via Lambda, dashboard update)
- **Error alerting**: CloudWatch alarms publish to SNS for AI pipeline failures
- **Human review notification**: Step Functions sends task token + content to SNS, subscriber (reviewer) receives email/SMS

### 4.2 Fan-Out Patterns

**SNS + SQS fan-out for parallel AI processing:**

```
                           ┌── SQS Queue A ── Lambda (Summarization)
                           │
SNS Topic ── Subscription ─┼── SQS Queue B ── Lambda (Translation)
                           │
                           └── SQS Queue C ── Lambda (Sentiment Analysis)
```

Each SQS queue subscribes to the same SNS topic. When a document is published to the topic, all three queues receive a copy and process it independently.

**Message filtering for targeted processing:**

```typescript
import { SNSClient, SubscribeCommand } from "@aws-sdk/client-sns";

const snsClient = new SNSClient({ region: "us-east-1" });

await snsClient.send(
  new SubscribeCommand({
    TopicArn: "arn:aws:sns:us-east-1:123456789012:ai-results",
    Protocol: "sqs",
    Endpoint: "arn:aws:sqs:us-east-1:123456789012:high-priority-results",
    Attributes: {
      FilterPolicy: JSON.stringify({
        priority: ["high"],
        resultType: ["summary", "analysis"],
      }),
    },
  })
);
```

### 4.3 SNS with Step Functions

SNS has an **optimized integration** with Step Functions:
- **Request Response**: `arn:aws:states:::sns:publish` -- publish and continue
- **Wait for Callback**: `arn:aws:states:::sns:publish.waitForTaskToken` -- publish with task token, pause

**Exam Gotcha**: SNS does NOT support `.sync` (Run a Job) pattern -- only Request Response and Wait for Callback. This makes sense because publishing a notification is not a "job" that completes.

### 4.4 Key Metrics for SNS

| Metric | Description |
|---|---|
| `NumberOfMessagesPublished` | Messages published to topic |
| `NumberOfNotificationsDelivered` | Successful deliveries |
| `NumberOfNotificationsFailed` | Failed deliveries |
| `PublishSize` | Size of published messages |

---

## 5. Amazon AppFlow

### 5.1 Data Integration for Knowledge Bases

Amazon AppFlow is a **fully managed data integration service** that securely transfers data between SaaS applications and AWS services. In the GenAI context, it is primarily used to ingest data into S3 for Knowledge Base indexing.

**How it fits in GenAI architectures:**

```
SaaS Source (Salesforce, Slack, etc.) → AppFlow → S3 Bucket → Bedrock Knowledge Base
```

### 5.2 Connector Types

**Supported sources (80+ connectors):** Salesforce, Google Analytics, Google BigQuery, Slack, ServiceNow, Zendesk, Jira Cloud, HubSpot, Marketo, SAP OData, Microsoft Dynamics 365, Microsoft SharePoint Online, GitHub, Snowflake, Datadog, and many more.

**Supported destinations:** Amazon S3, Amazon Redshift, Amazon Lookout for Metrics, Amazon RDS for PostgreSQL, Salesforce, Snowflake, Upsolver, Zendesk, and others.

**Custom connectors:** Build your own using the AppFlow Custom Connector SDK (Python/Java) for unsupported SaaS applications.

**Flow trigger types:**

| Type | Description | GenAI Use Case |
|---|---|---|
| **On demand** | Manual trigger | One-time data backfill for knowledge base |
| **Scheduled** | Cron-based trigger | Periodic refresh of knowledge base data |
| **Event-driven** | Triggered by source events | Real-time sync (Salesforce CDC) |

**Data transformations within AppFlow:**
- Field mapping and renaming
- Data masking and truncation
- Field validation (required, type checking)
- Filtering by field value
- Merging fields

**TypeScript SDK v3 -- Creating an AppFlow flow:**

```typescript
import { AppflowClient, CreateFlowCommand } from "@aws-sdk/client-appflow";

const appflowClient = new AppflowClient({ region: "us-east-1" });

await appflowClient.send(
  new CreateFlowCommand({
    flowName: "salesforce-to-knowledge-base",
    triggerConfig: {
      triggerType: "Scheduled",
      triggerProperties: {
        Scheduled: {
          scheduleExpression: "rate(1 day)",
          dataPullMode: "Incremental",
        },
      },
    },
    sourceFlowConfig: {
      connectorType: "Salesforce",
      connectorProfileName: "my-salesforce-profile",
      sourceConnectorProperties: {
        Salesforce: { object: "Knowledge__kav" },
      },
    },
    destinationFlowConfigList: [
      {
        connectorType: "S3",
        destinationConnectorProperties: {
          S3: {
            bucketName: "my-knowledge-base-bucket",
            bucketPrefix: "salesforce-articles",
            s3OutputFormatConfig: {
              fileType: "JSON",
            },
          },
        },
      },
    ],
    tasks: [
      {
        sourceFields: ["Title", "Summary", "ArticleBody"],
        taskType: "Map_all",
        connectorOperator: { Salesforce: "NO_OP" },
      },
    ],
  })
);
```

### 5.3 Exam Gotchas for AppFlow

- AppFlow transfers data **into AWS** from SaaS (and vice versa) -- it is NOT a general ETL tool (that is AWS Glue)
- AppFlow supports **incremental data pull** for scheduled flows, transferring only changed records
- AppFlow encrypts data in transit and supports **AWS PrivateLink** for private connectivity
- For GenAI, AppFlow is the answer when the question asks about getting **SaaS data into S3** for knowledge base ingestion
- AppFlow does NOT directly integrate with Bedrock -- it writes to S3, then Knowledge Base indexes from S3

---

## 6. AWS AppConfig

### 6.1 Feature Flags for Model Selection

AWS AppConfig (part of AWS Systems Manager) enables **dynamic configuration changes** without code deployments. For GenAI, it is specifically tested for dynamic model selection (Task 1.2.2).

**Core concepts:**
- **Application**: Organizational namespace
- **Environment**: Logical deployment target (dev, staging, prod)
- **Configuration profile**: Contains the configuration data (feature flags or freeform)
- **Deployment strategy**: Controls how configuration changes roll out
- **Hosted configuration store**: AWS-managed storage for config data

### 6.2 Dynamic Configuration Without Code Changes

**Feature flag for model selection:**

```json
{
  "version": "1",
  "flags": {
    "primaryModel": {
      "name": "Primary Model Selection",
      "description": "Controls which FM is used for primary inference",
      "attributes": {
        "modelId": {
          "constraints": {
            "type": "string",
            "enum": [
              "anthropic.claude-sonnet-4-20250514",
              "anthropic.claude-haiku-4-20250514",
              "amazon.nova-pro-v1:0",
              "amazon.nova-micro-v1:0"
            ]
          }
        },
        "maxTokens": {
          "constraints": {
            "type": "number",
            "minimum": 100,
            "maximum": 4096
          }
        },
        "temperature": {
          "constraints": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
          }
        }
      }
    },
    "fallbackModel": {
      "name": "Fallback Model",
      "description": "Model to use when primary is unavailable"
    },
    "guardrailsEnabled": {
      "name": "Guardrails Enabled",
      "description": "Toggle Bedrock Guardrails on/off"
    }
  },
  "values": {
    "primaryModel": {
      "enabled": true,
      "modelId": "anthropic.claude-sonnet-4-20250514",
      "maxTokens": 1024,
      "temperature": 0.7
    },
    "fallbackModel": {
      "enabled": true,
      "modelId": "amazon.nova-micro-v1:0"
    },
    "guardrailsEnabled": {
      "enabled": true
    }
  }
}
```

**TypeScript SDK v3 -- Retrieving AppConfig configuration at runtime:**

```typescript
import {
  AppConfigDataClient,
  StartConfigurationSessionCommand,
  GetLatestConfigurationCommand,
} from "@aws-sdk/client-appconfigdata";

const appConfigClient = new AppConfigDataClient({ region: "us-east-1" });

// Start a configuration session (do this once per environment)
const session = await appConfigClient.send(
  new StartConfigurationSessionCommand({
    ApplicationIdentifier: "my-genai-app",
    EnvironmentIdentifier: "production",
    ConfigurationProfileIdentifier: "model-selection",
    RequiredMinimumPollIntervalInSeconds: 60,
  })
);

// Periodically poll for latest configuration
const config = await appConfigClient.send(
  new GetLatestConfigurationCommand({
    ConfigurationToken: session.InitialConfigurationToken,
  })
);

const modelConfig = JSON.parse(
  new TextDecoder().decode(config.Configuration)
);

// Use in your Bedrock call
const modelId = modelConfig.primaryModel.modelId;
const maxTokens = modelConfig.primaryModel.maxTokens;
```

### 6.3 Deployment Strategies

AppConfig supports controlled rollouts to minimize risk of bad configuration changes.

**Predefined strategies:**

| Strategy | Growth | Duration | Bake Time | Use Case |
|---|---|---|---|---|
| `AppConfig.AllAtOnce` | 100% | 0 min | 10 min | Instant rollout for non-critical changes |
| `AppConfig.Linear50PercentEvery30Seconds` | 50% | 1 min | 1 min | Quick rollout with minimal bake |
| `AppConfig.Linear20PercentEvery6Minutes` | 20% | 30 min | 30 min | Gradual rollout for important changes |
| `AppConfig.Canary10Percent20Minutes` | 10% then 100% | 20 min | 10 min | Canary deployment for risky changes |

**Custom deployment strategy:**

| Field | Description |
|---|---|
| `GrowthType` | `LINEAR` (even distribution) or `EXPONENTIAL` (percentage-based growth) |
| `GrowthFactor` | Percentage of targets to include in each step |
| `DeploymentDurationInMinutes` | Total time for deployment |
| `FinalBakeTimeInMinutes` | Monitoring period after 100% deployment |
| `ReplicateTo` | Where to replicate (currently only `NONE` or `SSM_DOCUMENT`) |

**Automatic rollback:** Configure CloudWatch alarms as monitors. If an alarm triggers during deployment, AppConfig automatically rolls back the configuration change.

**GenAI scenarios for AppConfig:**
- **A/B model testing**: Deploy a new model ID to 10% of traffic (canary), monitor quality metrics, then expand
- **Prompt template updates**: Update system prompts without redeploying application code
- **Guardrail tuning**: Adjust guardrail thresholds dynamically based on observed false positive rates
- **Feature toggles**: Enable/disable RAG, streaming, or specific model capabilities per environment
- **Cost management**: Switch to cheaper models during low-priority hours without deployment

### 6.4 Exam Gotchas for AppConfig

- AppConfig is NOT the same as AWS Config (which audits resource compliance)
- AppConfig supports **validation** via JSON Schema or Lambda validators before deployment
- Configuration polling uses a session-based model: `StartConfigurationSession` then `GetLatestConfiguration` in a loop
- The `GetLatestConfiguration` call returns an empty body if nothing changed since the last poll (this is normal, not an error)
- AppConfig integrates with **CloudWatch alarms** for automatic rollback during bad deployments
- For the exam, AppConfig is the answer when asked about **changing model parameters or model selection at runtime without code changes**

---

## 7. Cross-Service Integration Patterns for GenAI

### 7.1 End-to-End Document Processing Pipeline

```
S3 Upload → EventBridge Rule → Step Functions (Standard) →
  ├── Textract (OCR, .sync) →
  ├── Bedrock (Classify Document) →
  ├── Bedrock (Extract Entities) →
  ├── Bedrock (Summarize) →
  ├── Choice (Confidence Check) →
  │     ├── High Confidence → Store Results (DynamoDB)
  │     └── Low Confidence → SQS (Human Review Queue) → .waitForTaskToken
  └── SNS (Notify Completion)
```

### 7.2 Resilient Multi-Model Inference

```
API Gateway → Lambda →
  ├── AppConfig (Get Model Config) →
  ├── Step Functions (Express) →
  │     ├── Circuit Breaker Check (DynamoDB) →
  │     ├── Primary Model (Bedrock InvokeModel) →
  │     │     ├── Retry with backoff + jitter
  │     │     └── Catch → Fallback Model (Bedrock InvokeModel)
  │     └── Response
  └── CloudWatch Metrics
```

### 7.3 Event-Driven Knowledge Base Refresh

```
AppFlow (Scheduled, Salesforce → S3) →
  EventBridge (S3 Object Created) →
    Step Functions →
      ├── Bedrock (StartIngestionJob.sync) →
      ├── Wait for Indexing Complete →
      └── SNS (Notify Team)
```

---

## 8. Quick-Reference Comparison Table

| Service | Primary GenAI Role | Exam Weight | Key Integration Pattern |
|---|---|---|---|
| **Step Functions** | Workflow orchestration, prompt chaining, agent loops, human approval | Very High | Optimized Bedrock integration, `.waitForTaskToken`, Retry/Catch |
| **EventBridge** | Event routing, triggering AI pipelines | Medium | Event patterns, rule-based routing to Step Functions |
| **SQS** | Async decoupling, buffering AI requests | Medium | DLQ for failed inference, `.waitForTaskToken` with Step Functions |
| **SNS** | Notifications, fan-out | Low-Medium | Fan-out to multiple AI processors, human review notifications |
| **AppFlow** | SaaS data ingestion for Knowledge Bases | Low | Scheduled/event flows from SaaS to S3 |
| **AppConfig** | Runtime model/config changes | Low-Medium | Feature flags for model selection, deployment strategies |

---

## 9. Exam Strategy Tips

1. **Step Functions is almost always the answer** when the question involves orchestrating multiple AI steps, error handling, human approval, or deterministic workflows. If you see "audit trail", "exactly-once", or "visual workflow", it is Step Functions.

2. **Step Functions vs Bedrock Agents**: Step Functions for deterministic, developer-defined flows with full auditability. Bedrock Agents for autonomous, LLM-driven orchestration with semantic flexibility. The exam will present scenarios where one is clearly better than the other.

3. **Step Functions vs Bedrock Prompt Flows**: Step Functions for complex flows needing error handling, human-in-the-loop, conditional branching, and integration with non-Bedrock services. Prompt Flows for simpler prompt chains managed entirely within Bedrock.

4. **Circuit breaker pattern**: If the question mentions "resilient AI systems", "prevent cascading failures", or "handle model unavailability gracefully", the answer involves Step Functions + DynamoDB circuit breaker.

5. **`.waitForTaskToken`**: If the question mentions human review, external approval, or pausing for an async callback, this is the pattern. Only available in Standard Workflows.

6. **AppConfig vs environment variables**: If the question asks about changing model parameters "without redeploying" or "without code changes", AppConfig is the answer (not Lambda environment variables, which require a deployment).

7. **SQS DLQ**: If the question asks about handling failed AI inference requests for later reprocessing, SQS with a dead-letter queue is the answer.

8. **AppFlow**: If the question mentions ingesting data from Salesforce, ServiceNow, or other SaaS into S3 for a knowledge base, AppFlow is the answer.

9. **EventBridge**: If the question mentions reacting to S3 uploads, model training completion events, or building event-driven AI architectures, EventBridge is the answer. It is the "glue" that starts AI pipelines based on events.

10. **Error handling order**: Retriers are evaluated in order (specific errors first, `States.ALL` last). `States.ALL` does NOT catch `States.DataLimitExceeded` or `States.Runtime`. Use `JitterStrategy: "FULL"` for concurrent retry scenarios.
