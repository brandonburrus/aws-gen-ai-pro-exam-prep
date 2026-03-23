# Management and Governance Services for the AIP-C01 Exam

This study guide covers the Management and Governance services tested on the AWS Certified
Generative AI Developer - Professional (AIP-C01) exam. CloudWatch and CloudWatch Logs are the
most heavily tested services in this category -- they appear in nearly every task statement
across all five domains.

## Table of Contents

1. [Amazon CloudWatch](#1-amazon-cloudwatch)
2. [Amazon CloudWatch Logs](#2-amazon-cloudwatch-logs)
3. [Amazon CloudWatch Synthetics](#3-amazon-cloudwatch-synthetics)
4. [AWS CloudTrail](#4-aws-cloudtrail)
5. [AWS Auto Scaling](#5-aws-auto-scaling)
6. [Cost Tools (Cost Explorer, Cost Anomaly Detection)](#6-cost-tools)
7. [AWS Well-Architected Tool](#7-aws-well-architected-tool)
8. [Other Services](#8-other-services)

---

## 1. Amazon CloudWatch

CloudWatch is the central observability service for all AWS resources. For the exam, you need
to know CloudWatch as the primary monitoring plane for Bedrock model invocations, agents,
guardrails, and custom GenAI metrics.

### 1.1 Core Concepts

**Metrics** are time-ordered data points published to CloudWatch. Each metric belongs to a
**namespace** (e.g., `AWS/Bedrock`) and is identified by a combination of name and
**dimensions** (key-value pairs like `ModelId`).

**Statistics** are aggregations over a time period: `Sum`, `Average`, `Minimum`, `Maximum`,
`SampleCount`, and **percentiles** (p50, p90, p99). Percentile statistics are critical for
latency monitoring -- the exam tests whether you know to use p99 latency instead of average
for tail-latency SLAs.

**Periods** define the length of time associated with a specific statistic. Minimum period is
1 second (high-resolution metrics) or 60 seconds (standard). Bedrock metrics use standard
resolution.

**Alarms** watch a single metric or a metric math expression and change state based on
thresholds. States: `OK`, `ALARM`, `INSUFFICIENT_DATA`. Alarms trigger actions such as SNS
notifications, Auto Scaling policies, or EC2 actions.

**Dashboards** are customizable pages in the CloudWatch console for visualizing metrics. They
support cross-account and cross-Region aggregation.

### 1.2 Bedrock-Specific CloudWatch Metrics

These are the built-in metrics published automatically when you use Amazon Bedrock. No
additional configuration is required to start receiving them.

#### Runtime Metrics (Namespace: `AWS/Bedrock`)

| Metric | Unit | Description |
|---|---|---|
| `Invocations` | SampleCount | Number of successful requests to `Converse`, `ConverseStream`, `InvokeModel`, `InvokeModelWithResponseStream` |
| `InvocationLatency` | Milliseconds | End-to-end time from request sent to last token received |
| `InvocationClientErrors` | SampleCount | Invocations resulting in 4xx client errors |
| `InvocationServerErrors` | SampleCount | Invocations resulting in 5xx server errors |
| `InvocationThrottles` | SampleCount | Throttled invocations (do NOT count as Invocations or Errors) |
| `InputTokenCount` | SampleCount | Number of input tokens |
| `OutputTokenCount` | SampleCount | Number of output tokens |
| `OutputImageCount` | SampleCount | Number of output images (image generation models only) |
| `TimeToFirstToken` | Milliseconds | Time until first token for streaming APIs (`ConverseStream`, `InvokeModelWithResponseStream`) |
| `LegacyModelInvocations` | SampleCount | Invocations using legacy (deprecated) models |
| `EstimatedTPMQuotaUsage` | SampleCount | Estimated tokens-per-minute quota consumption |

**Dimensions for runtime metrics:**
- `ModelId` -- available on all metrics
- `ModelId` + `ImageSize` + `BucketedStepSize` -- available on `OutputImageCount`

#### Log Delivery Metrics (Namespace: `AWS/Bedrock`, Dimension: `Across all model IDs`)

| Metric | Description |
|---|---|
| `ModelInvocationLogsCloudWatchDeliverySuccess` | Successful log deliveries to CloudWatch Logs |
| `ModelInvocationLogsCloudWatchDeliveryFailure` | Failed log deliveries to CloudWatch Logs |
| `ModelInvocationLogsS3DeliverySuccess` | Successful log deliveries to S3 |
| `ModelInvocationLogsS3DeliveryFailure` | Failed log deliveries to S3 |
| `ModelInvocationLargeDataS3DeliverySuccess` | Successful large data deliveries to S3 |
| `ModelInvocationLargeDataS3DeliveryFailure` | Failed large data deliveries to S3 |

#### Guardrails Metrics (Namespace: `AWS/Bedrock/Guardrails`)

| Metric | Unit | Description |
|---|---|---|
| `Invocations` | SampleCount | Requests to `ApplyGuardrail` API |
| `InvocationLatency` | Milliseconds | Guardrail evaluation latency |
| `InvocationClientErrors` | SampleCount | Client-side errors |
| `InvocationServerErrors` | SampleCount | Server-side errors |
| `InvocationThrottles` | SampleCount | Throttled requests |
| `TextUnitCount` | SampleCount | Text units consumed by guardrail policies |
| `InvocationsIntervened` | SampleCount | Invocations where guardrails intervened (blocked/modified) |
| `FindingCounts` | SampleCount | Counts per finding type from automated reasoning checks |
| `TotalFindings` | SampleCount | Total findings per automated reasoning check request |
| `Latency` | Milliseconds | Automated reasoning policy verification latency |

**Guardrails Dimensions:**
- `Operation` (ApplyGuardrail)
- `GuardrailContentSource` (Input or Output)
- `GuardrailPolicyType` (ContentPolicy, TopicPolicy, WordPolicy, SensitiveInformationPolicy, ContextualGroundingPolicy)
- `GuardrailArn` + `GuardrailVersion`
- `FindingType` + `PolicyArn` + `PolicyVersion`

#### Agent Metrics (Namespace: `AWS/Bedrock/Agents`)

| Metric | Unit | Description |
|---|---|---|
| `InvocationCount` | SampleCount | Agent invocation requests |
| `TotalTime` | Milliseconds | Server-side processing time |
| `TTFT` | Milliseconds | Time-to-first-token (streaming agent invocations only) |
| `InvocationThrottles` | SampleCount | Throttled agent invocations |
| `InvocationServerErrors` | SampleCount | Server errors |
| `InvocationClientErrors` | SampleCount | Client errors |
| `ModelLatency` | Milliseconds | Latency of the underlying model call |
| `ModelInvocationCount` | SampleCount | Model calls made by the agent |
| `ModelInvocationThrottles` | SampleCount | Model calls throttled by Bedrock |
| `ModelInvocationClientErrors` | SampleCount | Client errors on model calls |
| `ModelInvocationServerErrors` | SampleCount | Server errors on model calls |
| `InputTokenCount` | SampleCount | Tokens input to the model |
| `OutputTokenCount` | SampleCount | Tokens output from the model |

**Agent Dimensions:**
- `Operation` (InvokeAgent, InvokeInlineAgent)
- `Operation` + `ModelId`
- `Operation` + `AgentAliasArn` + `ModelId`

> **Exam tip:** The agent IAM service role must include `cloudwatch:PutMetricData` with a
> condition restricting to the `AWS/Bedrock/Agents` namespace, or metrics will not appear in
> the dashboard.

### 1.3 Custom Metrics for GenAI

Bedrock built-in metrics cover infrastructure-level observability but not application-level
quality. For GenAI applications, you often need custom metrics:

| Custom Metric | Purpose | How to Compute |
|---|---|---|
| Hallucination rate | Track groundedness failures | Count guardrail `ContextualGroundingPolicy` interventions / total invocations |
| Response quality score | Application-specific quality | Run LLM-as-judge evaluations, publish scores as custom metrics |
| Token cost per request | Cost attribution | `(InputTokenCount * input_price) + (OutputTokenCount * output_price)` |
| Prompt confusion rate | Detect unclear prompts | Parse invocation logs for refusal patterns or low-confidence signals |
| Guardrail intervention rate | Safety monitoring | `InvocationsIntervened` / total `Invocations` per guardrail |
| RAG retrieval relevance | Knowledge base quality | Score retrieved chunks against the query, publish as metric |

Publishing custom metrics uses the `PutMetricData` API:

```typescript
import { CloudWatchClient, PutMetricDataCommand } from "@aws-sdk/client-cloudwatch";

const cw = new CloudWatchClient({ region: "us-east-1" });

await cw.send(new PutMetricDataCommand({
  Namespace: "GenAI/MyApp",
  MetricData: [
    {
      MetricName: "HallucinationRate",
      Dimensions: [
        { Name: "ModelId", Value: "anthropic.claude-sonnet-4-20250514-v1:0" },
        { Name: "Environment", Value: "production" },
      ],
      Value: 0.03, // 3% hallucination rate
      Unit: "None",
      Timestamp: new Date(),
    },
    {
      MetricName: "TokenCostUSD",
      Dimensions: [
        { Name: "ModelId", Value: "anthropic.claude-sonnet-4-20250514-v1:0" },
      ],
      Value: 0.0042,
      Unit: "None",
      Timestamp: new Date(),
    },
  ],
}));
```

> **Exam tip:** Custom metrics cost $0.30/metric/month. Use dimensions wisely -- each unique
> combination of namespace + metric name + dimensions creates a separate metric. The exam may
> test whether you understand the cost implications of high-cardinality dimensions.

### 1.4 CloudWatch Alarms for AI Thresholds

Alarms are the primary mechanism for automated response to GenAI quality issues.

**Static Threshold Alarms** -- compare a metric to a fixed value:

```typescript
import { CloudWatchClient, PutMetricAlarmCommand } from "@aws-sdk/client-cloudwatch";

const cw = new CloudWatchClient({ region: "us-east-1" });

// Alarm when throttling exceeds 10 requests in 5 minutes
await cw.send(new PutMetricAlarmCommand({
  AlarmName: "Bedrock-High-Throttling",
  Namespace: "AWS/Bedrock",
  MetricName: "InvocationThrottles",
  Dimensions: [{ Name: "ModelId", Value: "anthropic.claude-sonnet-4-20250514-v1:0" }],
  Statistic: "Sum",
  Period: 300,
  EvaluationPeriods: 1,
  Threshold: 10,
  ComparisonOperator: "GreaterThanThreshold",
  AlarmActions: ["arn:aws:sns:us-east-1:123456789012:GenAI-Alerts"],
  TreatMissingData: "notBreaching",
}));

// Alarm when p99 latency exceeds 10 seconds
await cw.send(new PutMetricAlarmCommand({
  AlarmName: "Bedrock-P99-Latency-SLA",
  Namespace: "AWS/Bedrock",
  MetricName: "InvocationLatency",
  Dimensions: [{ Name: "ModelId", Value: "anthropic.claude-sonnet-4-20250514-v1:0" }],
  ExtendedStatistic: "p99",
  Period: 300,
  EvaluationPeriods: 3,
  DatapointsToAlarm: 2,  // 2 out of 3 periods must breach
  Threshold: 10000,
  ComparisonOperator: "GreaterThanThreshold",
  AlarmActions: ["arn:aws:sns:us-east-1:123456789012:GenAI-Alerts"],
}));
```

**Composite Alarms** combine multiple alarms with AND/OR logic. Use these when a single
metric alarm would be too noisy:

```typescript
import { PutCompositeAlarmCommand } from "@aws-sdk/client-cloudwatch";

await cw.send(new PutCompositeAlarmCommand({
  AlarmName: "Bedrock-Combined-Degradation",
  AlarmRule: 'ALARM("Bedrock-High-Throttling") AND ALARM("Bedrock-P99-Latency-SLA")',
  AlarmActions: ["arn:aws:sns:us-east-1:123456789012:GenAI-Critical"],
}));
```

> **Exam tip:** Know the `TreatMissingData` options: `breaching`, `notBreaching`, `ignore`,
> `missing`. For intermittent GenAI workloads, `notBreaching` prevents false alarms when no
> invocations occur.

### 1.5 Anomaly Detection for Token Patterns

CloudWatch Anomaly Detection uses machine learning to build a model of expected metric
behavior, accounting for hourly, daily, and weekly seasonality patterns. It produces an
**anomaly detection band** -- a range of expected values.

This is particularly useful for GenAI workloads where static thresholds are hard to set:
- Token usage patterns that grow organically over time
- Latency that varies with prompt length and model load
- Invocation counts that follow business hours

**When to use anomaly detection vs. static thresholds:**
- Use anomaly detection when the metric has seasonal patterns and you cannot predict a fixed threshold
- Use static thresholds when you have a hard SLA (e.g., p99 latency must be under 10 seconds)

Anomaly detection alarms use the `ANOMALY_DETECTION_BAND` function:

```typescript
await cw.send(new PutMetricAlarmCommand({
  AlarmName: "Bedrock-Token-Anomaly",
  Namespace: "AWS/Bedrock",
  MetricName: "InputTokenCount",
  Dimensions: [{ Name: "ModelId", Value: "anthropic.claude-sonnet-4-20250514-v1:0" }],
  Statistic: "Sum",
  Period: 3600,
  EvaluationPeriods: 3,
  ThresholdMetricId: "ad1",
  ComparisonOperator: "GreaterThanUpperThreshold",
  Metrics: [
    {
      Id: "m1",
      MetricStat: {
        Metric: {
          Namespace: "AWS/Bedrock",
          MetricName: "InputTokenCount",
          Dimensions: [{ Name: "ModelId", Value: "anthropic.claude-sonnet-4-20250514-v1:0" }],
        },
        Period: 3600,
        Stat: "Sum",
      },
    },
    {
      Id: "ad1",
      Expression: "ANOMALY_DETECTION_BAND(m1, 2)",  // 2 standard deviations
    },
  ],
}));
```

CloudWatch Logs also has its own anomaly detection capability. Log anomaly detectors
continuously scan log events in a log group, establish baselines using ML and pattern
recognition, and flag significant fluctuations. This complements metric-based anomaly
detection by catching novel error patterns in invocation logs.

### 1.6 CloudWatch Dashboards for AI Observability

Bedrock provides **pre-configured dashboards** under CloudWatch > Generative AI observability
> Model Invocations. These dashboards include:

- Invocation count over time
- Invocation latency
- Token counts by model (input vs. output)
- Daily token counts by model ID
- Requests grouped by input token ranges
- Invocation throttles
- Invocation error count

You can create custom dashboards for application-level GenAI observability:

```typescript
import { CloudWatchClient, PutDashboardCommand } from "@aws-sdk/client-cloudwatch";

const cw = new CloudWatchClient({ region: "us-east-1" });

const dashboardBody = {
  widgets: [
    {
      type: "metric",
      x: 0, y: 0, width: 12, height: 6,
      properties: {
        title: "Token Usage by Model",
        metrics: [
          ["AWS/Bedrock", "InputTokenCount", "ModelId", "anthropic.claude-sonnet-4-20250514-v1:0", { stat: "Sum", label: "Input Tokens" }],
          ["AWS/Bedrock", "OutputTokenCount", "ModelId", "anthropic.claude-sonnet-4-20250514-v1:0", { stat: "Sum", label: "Output Tokens" }],
        ],
        period: 3600,
        view: "timeSeries",
        region: "us-east-1",
      },
    },
    {
      type: "metric",
      x: 12, y: 0, width: 12, height: 6,
      properties: {
        title: "Guardrail Interventions",
        metrics: [
          ["AWS/Bedrock/Guardrails", "InvocationsIntervened", "Operation", "ApplyGuardrail", { stat: "Sum" }],
          ["AWS/Bedrock/Guardrails", "Invocations", "Operation", "ApplyGuardrail", { stat: "Sum" }],
        ],
        period: 3600,
        view: "timeSeries",
      },
    },
    {
      type: "metric",
      x: 0, y: 6, width: 12, height: 6,
      properties: {
        title: "P99 Latency & Time to First Token",
        metrics: [
          ["AWS/Bedrock", "InvocationLatency", "ModelId", "anthropic.claude-sonnet-4-20250514-v1:0", { stat: "p99", label: "P99 Latency" }],
          ["AWS/Bedrock", "TimeToFirstToken", "ModelId", "anthropic.claude-sonnet-4-20250514-v1:0", { stat: "p99", label: "P99 TTFT" }],
        ],
        period: 300,
        view: "timeSeries",
      },
    },
  ],
};

await cw.send(new PutDashboardCommand({
  DashboardName: "GenAI-Observability",
  DashboardBody: JSON.stringify(dashboardBody),
}));
```

### 1.7 Metric Math for AI KPIs

Metric math lets you compute derived KPIs without publishing additional custom metrics.
Expressions use metric IDs and standard arithmetic.

Common GenAI metric math expressions:

| KPI | Expression | Purpose |
|---|---|---|
| Error rate | `(m1 + m2) / m3 * 100` where m1=ClientErrors, m2=ServerErrors, m3=Invocations | Overall error percentage |
| Tokens per invocation (avg) | `m1 / m2` where m1=Sum(InputTokenCount), m2=Sum(Invocations) | Average prompt size |
| Guardrail intervention % | `m1 / m2 * 100` where m1=InvocationsIntervened, m2=Invocations | Safety trigger rate |
| Output/Input ratio | `m1 / m2` where m1=OutputTokenCount, m2=InputTokenCount | Verbosity indicator |
| Estimated cost | `(m1 * input_price_per_token) + (m2 * output_price_per_token)` | Token-based cost approximation |

```typescript
// Example: Metric math in a GetMetricData call
import { CloudWatchClient, GetMetricDataCommand } from "@aws-sdk/client-cloudwatch";

const cw = new CloudWatchClient({ region: "us-east-1" });

const end = new Date();
const start = new Date(end.getTime() - 3600 * 1000);

const result = await cw.send(new GetMetricDataCommand({
  StartTime: start,
  EndTime: end,
  MetricDataQueries: [
    {
      Id: "invocations",
      MetricStat: {
        Metric: {
          Namespace: "AWS/Bedrock",
          MetricName: "Invocations",
          Dimensions: [{ Name: "ModelId", Value: "anthropic.claude-sonnet-4-20250514-v1:0" }],
        },
        Period: 3600,
        Stat: "Sum",
      },
      ReturnData: false,
    },
    {
      Id: "throttles",
      MetricStat: {
        Metric: {
          Namespace: "AWS/Bedrock",
          MetricName: "InvocationThrottles",
          Dimensions: [{ Name: "ModelId", Value: "anthropic.claude-sonnet-4-20250514-v1:0" }],
        },
        Period: 3600,
        Stat: "Sum",
      },
      ReturnData: false,
    },
    {
      Id: "throttle_rate",
      Expression: "throttles / (invocations + throttles) * 100",
      Label: "Throttle Rate %",
      ReturnData: true,
    },
  ],
}));
```

> **Exam tip:** `METRICS("m1")` is used when you want to apply a function across all metrics
> matching a search expression. `ANOMALY_DETECTION_BAND(m1, N)` creates an upper and lower
> band N standard deviations from the model. These are the two most likely metric math
> functions tested.

---

## 2. Amazon CloudWatch Logs

CloudWatch Logs is the centralized log ingestion and analysis service. For the exam, the
critical use case is Bedrock model invocation logging and Logs Insights queries for
prompt/response analysis.

### 2.1 Core Concepts

**Log Groups** are containers for log streams that share the same retention, monitoring, and
access control settings. Example: `/aws/bedrock/modelinvocations`.

**Log Streams** are sequences of log events from the same source. Bedrock creates a stream
named `aws/bedrock/modelinvocations` within the configured log group.

**Log Events** are individual records with a timestamp and raw message (JSON for Bedrock).

**Retention Policies** control how long logs are kept. Options range from 1 day to 10 years,
or indefinite (never expire). The default is indefinite, which can become expensive for
high-volume GenAI logging. Always set a retention policy.

**Subscription Filters** stream log data in real time to destinations:
- AWS Lambda (for real-time processing)
- Amazon Kinesis Data Streams (for analytics pipelines)
- Amazon Data Firehose (for delivery to S3, OpenSearch, etc.)

A single log group can have up to 2 subscription filters.

### 2.2 Bedrock Model Invocation Logging

Model invocation logging captures the full request and response data for every Bedrock
inference call. It is **disabled by default** and must be explicitly enabled.

**What gets logged:**
- Request metadata (timestamp, request ID, model ID, region, account)
- Input body (prompt text, up to 100 KB in CloudWatch Logs; larger payloads go to S3)
- Output body (response text, up to 100 KB)
- Token counts (input, output)
- Latency
- Error details (if applicable)

**Supported API operations:**
- `Converse` / `ConverseStream`
- `InvokeModel` / `InvokeModelWithResponseStream`

**Configuration options (modalities):**
- Text
- Image
- Embedding
- Video

Data is logged for ALL models that support the selected modalities.

**Destinations:**
- CloudWatch Logs only
- Amazon S3 only
- Both CloudWatch Logs and S3

For large data or binary image outputs, only S3 is supported. CloudWatch Logs handles JSON
payloads up to 100 KB.

**Setup via SDK:**

```typescript
import { BedrockClient, PutModelInvocationLoggingConfigurationCommand } from "@aws-sdk/client-bedrock";

const bedrock = new BedrockClient({ region: "us-east-1" });

await bedrock.send(new PutModelInvocationLoggingConfigurationCommand({
  loggingConfig: {
    cloudWatchConfig: {
      logGroupName: "/aws/bedrock/modelinvocations",
      roleArn: "arn:aws:iam::123456789012:role/BedrockLoggingRole",
      largeDataDeliveryS3Config: {
        bucketName: "my-bedrock-large-data",
        keyPrefix: "large-payloads/",
      },
    },
    textDataDeliveryEnabled: true,
    imageDataDeliveryEnabled: true,
    embeddingDataDeliveryEnabled: false,
    videoDataDeliveryEnabled: false,
  },
}));
```

**Required IAM for CloudWatch Logs destination:**
- The Bedrock service role must have `logs:CreateLogStream` and `logs:PutLogEvents` on the
  target log group.
- The trust policy must allow `bedrock.amazonaws.com` to assume the role, with
  `aws:SourceAccount` and `aws:SourceArn` conditions.

> **Exam tip:** If a question says "we need to analyze the actual prompts and responses sent
> to Bedrock," the answer is model invocation logging to CloudWatch Logs (or S3), NOT
> CloudTrail. CloudTrail logs API calls and metadata but does NOT capture prompt/response
> content.

### 2.3 CloudWatch Logs Insights Queries for GenAI

Logs Insights is the interactive query engine for CloudWatch Logs. It uses a purpose-built
query language. For the exam, know how to write queries that analyze Bedrock invocation logs.

**Common query patterns:**

```
# Find the most expensive invocations by token count
fields @timestamp, modelId, inputTokenCount, outputTokenCount
| sort outputTokenCount desc
| limit 20

# Calculate average tokens per model
fields modelId, inputTokenCount, outputTokenCount
| stats avg(inputTokenCount) as avgInput,
        avg(outputTokenCount) as avgOutput,
        count(*) as invocations
  by modelId

# Find invocations with high latency (> 5 seconds)
fields @timestamp, modelId, @message
| filter @message like /InvocationLatency/
| filter InvocationLatency > 5000
| sort InvocationLatency desc

# Search for specific content in prompts (prompt regression testing)
fields @timestamp, modelId, input.inputBodyJson
| filter input.inputBodyJson like /specific-keyword/
| limit 50

# Analyze error patterns
fields @timestamp, modelId, errorCode
| filter ispresent(errorCode)
| stats count(*) as errorCount by errorCode, modelId
| sort errorCount desc

# Token cost analysis by time window
fields @timestamp, modelId, inputTokenCount, outputTokenCount
| stats sum(inputTokenCount) as totalInput,
        sum(outputTokenCount) as totalOutput
  by bin(1h) as timeWindow
| sort timeWindow desc
```

**Logs Insights also supports an `anomaly` command** that uses ML to detect anomalous log
patterns directly within queries. This is useful for ad-hoc investigation:

```
fields @timestamp, @message
| anomaly @message
```

### 2.4 Sensitive Data Protection

CloudWatch Logs data protection policies can automatically detect and mask sensitive data
(PII, PHI, credentials) in log events. This is relevant for GenAI workloads where prompts
and responses may contain user PII.

Data protection uses managed data identifiers and can:
- Mask sensitive data in transit (audit findings reported but data masked in log output)
- Mask sensitive data at rest (data is stored in masked form)

> **Exam tip:** If a question describes a requirement to log Bedrock invocations while
> protecting PII in the logs, the answer involves CloudWatch Logs data protection policies
> (also referred to as "sensitive data protection" or "log data masking").

### 2.5 Log Retention and Cost Optimization

| Retention Period | Use Case |
|---|---|
| 1--7 days | Development/testing environments |
| 30 days | Production with short-term debugging needs |
| 90--365 days | Compliance requirements |
| Indefinite | Audit trail requirements (consider archiving to S3 instead) |

To reduce costs on high-volume GenAI logging:
1. Set explicit retention periods instead of using the default (indefinite)
2. Use subscription filters to stream to S3 via Firehose for long-term, cheaper storage
3. Enable only the modalities you need (e.g., skip image logging if you only use text)
4. Use CloudWatch Logs data protection to avoid storing raw PII

---

## 3. Amazon CloudWatch Synthetics

CloudWatch Synthetics creates **canaries** -- configurable scripts that run on a schedule to
monitor endpoints and APIs. Canaries use Lambda functions under the hood and can be written
in Node.js, Python, or Java.

### 3.1 Synthetic Canaries for AI Endpoints

Canaries monitor availability and latency of your GenAI application endpoints from an
external perspective. They simulate user interactions and detect problems before real users do.

**Key features:**
- Run as frequently as once per minute, 24/7
- Capture load time data, screenshots (for web UIs), logs, and metrics
- Publish metrics to the `CloudWatchSynthetics` namespace
- Support API canaries, heartbeat monitors, visual monitoring, and multi-check blueprints
- Can run inside a VPC to monitor private endpoints

**Blueprint types relevant to GenAI:**
- **API Canary** -- tests REST APIs (your GenAI API endpoints). Supports multiple HTTP
  methods, headers, and request bodies. Can validate response codes, latency, headers, and
  body content.
- **Heartbeat Monitor** -- loads URLs and verifies availability. Useful for monitoring a
  GenAI web application front end.
- **Multi-Check Blueprint** -- bundles up to 10 different monitoring steps in a single
  canary. Cost-effective for monitoring multiple GenAI endpoints.

### 3.2 Monitoring AI API Availability

A typical canary for a GenAI endpoint:

```typescript
// Canary script concept (runs as Lambda, uses Synthetics runtime)
// This is the logical flow -- actual canary scripts use the Synthetics
// Node.js/Python library which provides helper functions

// 1. Send a known test prompt to your GenAI API
// 2. Validate the response status code is 200
// 3. Validate the response contains expected structure
// 4. Validate latency is within acceptable bounds
// 5. Optionally validate response quality (e.g., contains expected keywords)
```

Canaries automatically create CloudWatch alarms and can integrate with X-Ray for distributed
tracing.

> **Exam tip:** Synthetics canaries are about external availability monitoring of YOUR
> endpoints (API Gateway, ALB, etc.), not direct monitoring of Bedrock itself. If a question
> asks about monitoring the availability of a customer-facing GenAI API, the answer is
> CloudWatch Synthetics. If it asks about monitoring Bedrock model performance, the answer is
> CloudWatch metrics in the `AWS/Bedrock` namespace.

---

## 4. AWS CloudTrail

CloudTrail records API calls made in your AWS account as **events**. It is the primary audit
and governance tool for Bedrock.

### 4.1 API Audit Logging for AI Services

CloudTrail is always on and captures the last 90 days of management events in the Event
History (free, no trail required). For ongoing retention, create a **trail** that delivers
log files to S3.

Every CloudTrail event includes:
- Who made the request (IAM identity, source IP, user agent)
- What API was called and with what parameters
- When the call was made
- Whether it succeeded or failed

### 4.2 Bedrock API Tracking

**Management events (logged by default):**
- `InvokeModel`, `InvokeModelWithResponseStream`
- `Converse`, `ConverseStream`
- `ListAsyncInvokes`
- All control-plane operations (CreateAgent, CreateKnowledgeBase, etc.)

**Data events (must be explicitly enabled):**
- `InvokeAgent` -- configure for resource type `AWS::Bedrock::AgentAlias`
- `InvokeInlineAgent` -- configure for `AWS::Bedrock::InlineAgent`
- `InvokeFlow` -- configure for `AWS::Bedrock::FlowAlias`
- `Retrieve`, `RetrieveAndGenerate` -- configure for `AWS::Bedrock::KnowledgeBase`
- `InvokeModelWithBidirectionalStream` -- configure for `AWS::Bedrock::Model`
- `GetAsyncInvoke`, `StartAsyncInvoke` -- configure for `AWS::Bedrock::Model` and `AWS::Bedrock::AsyncInvoke`
- `ApplyGuardrail` -- configure for `AWS::Bedrock::Guardrail`

To enable data events via CLI:

```bash
aws cloudtrail put-event-selectors --trail-name myTrail \
  --advanced-event-selectors '[
    {
      "Name": "Log Bedrock agent data events",
      "FieldSelectors": [
        { "Field": "eventCategory", "Equals": ["Data"] },
        { "Field": "resources.type", "Equals": ["AWS::Bedrock::AgentAlias"] }
      ]
    },
    {
      "Name": "Log Bedrock knowledge base data events",
      "FieldSelectors": [
        { "Field": "eventCategory", "Equals": ["Data"] },
        { "Field": "resources.type", "Equals": ["AWS::Bedrock::KnowledgeBase"] }
      ]
    }
  ]'
```

> **Exam tip:** CloudTrail logs WHO called WHAT API and WHEN. It does NOT log the content of
> prompts and responses -- that is model invocation logging (CloudWatch Logs / S3).
> This distinction is tested frequently. CloudTrail = audit trail. Invocation logging =
> content analysis.

### 4.3 Governance and Compliance Logging

CloudTrail supports:
- **Multi-region trails** -- log events from all regions into a single S3 bucket
- **Organization trails** -- log events from all accounts in an AWS Organization
- **CloudTrail Lake** -- serverless query engine for analyzing events using SQL-like syntax
- **Log file integrity validation** -- detect whether CloudTrail log files were modified
  after delivery
- **KMS encryption** -- encrypt log files at rest

**Amazon GuardDuty** monitors CloudTrail logs to detect potential security issues in Bedrock
APIs, such as unauthorized access patterns or anomalous invocation volumes.

### 4.4 CloudTrail Insights

CloudTrail Insights automatically detects unusual API activity patterns:
- Unusual volume of write management events
- Unusual volume of specific API calls
- Unusual error rates

When Insights detects anomalous activity, it generates an Insights event. This is useful for
detecting sudden spikes in Bedrock API calls that might indicate compromised credentials or
runaway automation.

> **Exam tip:** CloudTrail Insights = unusual API ACTIVITY patterns (volume, errors).
> CloudWatch Anomaly Detection = unusual METRIC patterns (latency, token counts). These serve
> different purposes and the exam will try to confuse them.

---

## 5. AWS Auto Scaling

### 5.1 Scaling AI Workloads

For Bedrock (serverless), there is no infrastructure to scale -- AWS manages capacity.
However, Auto Scaling is relevant when you build GenAI application infrastructure:

- **API Gateway + Lambda** -- Lambda concurrency scales automatically. Use reserved
  concurrency to guarantee capacity for GenAI workloads.
- **ECS/Fargate** -- Application Auto Scaling can scale tasks based on CloudWatch metrics.
- **SageMaker Endpoints** -- Application Auto Scaling adjusts the number of instances behind
  a SageMaker inference endpoint.

### 5.2 Target Tracking for AI Metrics

Target tracking policies maintain a target value for a specific metric. For GenAI:

- Scale ECS tasks to maintain average CPU at 70%
- Scale SageMaker endpoint instances to maintain `InvocationsPerInstance` at a target value
- Use custom CloudWatch metrics as scaling signals (e.g., queue depth of pending inference
  requests)

```typescript
import {
  ApplicationAutoScalingClient,
  PutScalingPolicyCommand,
} from "@aws-sdk/client-application-auto-scaling";

const aas = new ApplicationAutoScalingClient({ region: "us-east-1" });

// Target tracking for a SageMaker endpoint
await aas.send(new PutScalingPolicyCommand({
  PolicyName: "SageMaker-Invocations-Target",
  ServiceNamespace: "sagemaker",
  ResourceId: "endpoint/my-genai-endpoint/variant/AllTraffic",
  ScalableDimension: "sagemaker:variant:DesiredInstanceCount",
  PolicyType: "TargetTrackingScaling",
  TargetTrackingScalingPolicyConfiguration: {
    TargetValue: 100, // target invocations per instance
    PredefinedMetricSpecification: {
      PredefinedMetricType: "SageMakerVariantInvocationsPerInstance",
    },
    ScaleInCooldown: 600,
    ScaleOutCooldown: 60,
  },
}));
```

> **Exam tip:** Bedrock is serverless -- you do not configure Auto Scaling for it directly.
> If a question asks about scaling Bedrock, the answer involves Provisioned Throughput
> (reserved model units) or cross-region inference profiles, NOT Auto Scaling. Auto Scaling
> applies to SageMaker endpoints, ECS/Fargate tasks, and Lambda concurrency.

---

## 6. Cost Tools

### 6.1 AWS Cost Explorer

Cost Explorer provides visualization of your AWS spending over time. For GenAI workloads:

- Filter by service (Amazon Bedrock) to see total spend
- Group by usage type to see input tokens vs. output tokens vs. Provisioned Throughput
- Use the right-sizing recommendations for SageMaker instances hosting custom models
- Filter by tag to see costs for specific GenAI applications (requires cost allocation tags)

**Bedrock cost dimensions visible in Cost Explorer:**
- On-Demand token usage (input and output, by model)
- Provisioned Throughput commitment costs
- Model customization (fine-tuning) job costs
- Knowledge base storage and retrieval costs

### 6.2 Token Cost Tracking

Bedrock pricing is per-token (or per-image for image models). Cost Explorer shows aggregate
spend, but for per-request cost attribution you need to compute it from CloudWatch metrics:

```typescript
// Compute estimated cost from CloudWatch metrics
const INPUT_PRICE_PER_1K = 0.003;  // example: Claude Sonnet input
const OUTPUT_PRICE_PER_1K = 0.015; // example: Claude Sonnet output

const inputTokens = 1500;  // from InputTokenCount metric
const outputTokens = 400;  // from OutputTokenCount metric

const estimatedCost = (inputTokens / 1000) * INPUT_PRICE_PER_1K
                    + (outputTokens / 1000) * OUTPUT_PRICE_PER_1K;
// $0.0105 for this single invocation
```

Use **cost allocation tags** in AWS to attribute Bedrock costs to specific teams or projects.
Tags applied to Bedrock resources (custom models, Provisioned Throughput) propagate to Cost
Explorer.

### 6.3 AWS Cost Anomaly Detection

Cost Anomaly Detection uses ML to identify unusual spending patterns. It runs approximately
three times per day and evaluates spend data from Cost Explorer.

**Monitor types:**
- **AWS Managed Monitors** -- automatically track costs across all services, accounts, or
  cost categories. Automatically include new accounts and tag values.
- **Customer Managed Monitors** -- monitor specific accounts, services, or tag values.
  Useful for isolating GenAI workloads.

**Key features:**
- ML-based thresholds that adapt to organic growth and seasonal trends
- Root cause analysis identifying which service, account, or usage type caused the spike
- Alerts via email, SNS, or AWS Chatbot (Slack/Teams)
- Integration with EventBridge for automated remediation

**GenAI-specific cost anomaly patterns:**
- Sudden spike in token usage (new feature deployment, prompt engineering regression)
- Unexpected model invocation volume (runaway agent loops, misconfigured retry logic)
- Jump in Provisioned Throughput costs (unintended commitment)
- Knowledge base storage growth (embedding re-indexing)

The Well-Architected FSI Lens recommends tracking custom metrics like `token_in`, `token_out`,
and `embedding_ops`, then correlating them with cost anomalies on CloudWatch dashboards.

> **Exam tip:** Cost Anomaly Detection does NOT operate in real time -- there is a delay of
> several hours between spend occurring and anomaly detection. For real-time cost monitoring,
> use CloudWatch custom metrics with token counts and alarms.

---

## 7. AWS Well-Architected Tool

### 7.1 The Generative AI Lens

The Well-Architected Generative AI Lens is a structured assessment framework for evaluating
GenAI workloads against AWS best practices. It extends the six pillars of the
Well-Architected Framework with GenAI-specific considerations.

**Six pillars as applied to GenAI:**

| Pillar | GenAI Focus Areas |
|---|---|
| **Operational Excellence** | Model output quality monitoring, operational health, traceability, lifecycle automation, model customization decisions |
| **Security** | Endpoint protection, harmful output mitigation, event monitoring/audit, prompt security, model poisoning remediation |
| **Reliability** | Throughput handling, component communication, observability, graceful failure handling, artifact versioning, distributed inference |
| **Performance Efficiency** | Model performance capture and improvement, acceptable performance maintenance, computation optimization, data retrieval optimization |
| **Cost Optimization** | Cost-optimized model selection, inference cost/performance balance, prompt engineering for cost, vector store optimization, agent workflow optimization |
| **Sustainability** | Minimize compute for training/customization/hosting, model efficiency techniques, serverless architectures |

**Generative AI Lifecycle Stages:**
1. **Scoping** -- define business problem, assess GenAI relevance, set success metrics
2. **Model Selection** -- evaluate models on modality, accuracy, latency, cost, context window
3. **Model Customization** -- prompt engineering, RAG, fine-tuning, distillation
4. **Development and Integration** -- inference optimization, agent orchestration, UI
5. **Deployment** -- controlled rollout, scaling, infrastructure
6. **Continuous Improvement** -- monitoring, feedback collection, iterative refinement

### 7.2 Using the Well-Architected Tool

The Generative AI Lens is available as a custom lens in the AWS Well-Architected Tool Lens
Catalog. You can:

1. Download the lens JSON from the [AWS Well-Architected custom lens GitHub repository](https://github.com/aws-samples/sample-well-architected-custom-lens)
2. Import it into the Well-Architected Tool
3. Run workload reviews against the lens
4. Get improvement recommendations with links to implementation guidance

The tool generates a prioritized list of improvements and tracks progress over time.

> **Exam tip:** The exam references the Well-Architected Framework and Generative AI Lens
> in Task 1.1.3. Know the six pillars and how they apply to GenAI. The lens is NOT just a
> document -- it is a structured assessment tool you can import and run in the WA Tool
> console. Also know that AWS launched a separate **Responsible AI Lens** and an updated
> **Machine Learning Lens** alongside the GenAI Lens.

---

## 8. Other Services

### 8.1 AWS Chatbot

AWS Chatbot delivers AWS notifications to Slack channels and Microsoft Teams. For GenAI
workloads:

- Route CloudWatch alarm notifications to Slack/Teams for real-time team awareness
- Receive Cost Anomaly Detection alerts in chat
- Run read-only AWS CLI commands directly from chat (e.g., describe alarm state)
- Integrate with SNS topics that receive alarm actions

**GenAI relevance:** When the exam mentions "notify the development team in Slack when
Bedrock throttling exceeds a threshold," the answer involves CloudWatch Alarm -> SNS ->
AWS Chatbot -> Slack.

### 8.2 Amazon Managed Grafana

Managed Grafana is a fully managed Grafana service for operational dashboards. It natively
integrates with CloudWatch as a data source.

**When to use Managed Grafana vs. CloudWatch Dashboards:**
- Managed Grafana when you need advanced visualization, cross-data-source correlation
  (e.g., Prometheus + CloudWatch), or your team already uses Grafana
- CloudWatch Dashboards when you want zero-setup, native AWS integration, or are building
  dashboards programmatically via CloudFormation/CDK

For GenAI: Managed Grafana can pull Bedrock CloudWatch metrics and render them alongside
application metrics from other sources, giving a unified operational view.

### 8.3 AWS Service Catalog

Service Catalog lets administrators create and manage catalogs of approved AWS resources.
For GenAI:

- Publish pre-approved Bedrock configurations as Service Catalog products (e.g., a
  CloudFormation template that provisions a Bedrock agent with guardrails, logging, and
  monitoring pre-configured)
- Enforce governance by restricting developers to approved model configurations
- Version control GenAI infrastructure templates

### 8.4 AWS Systems Manager

Systems Manager provides operational management for AWS resources. GenAI-relevant features:

- **Parameter Store** -- store configuration values like model IDs, prompt templates,
  guardrail IDs, and feature flags. Supports encryption via KMS for sensitive values
  (API keys, connection strings). Use `SecureString` parameter type for secrets.
- **Session Manager** -- secure shell access to EC2 instances running custom model
  inference servers (no need for SSH keys or bastion hosts).
- **Automation** -- create runbooks for operational tasks like rotating Bedrock logging
  configurations or updating model versions across environments.
- **Patch Manager** -- keep EC2-based inference infrastructure patched.

> **Exam tip:** If a question asks where to store a model endpoint URL or a prompt template
> version identifier that Lambda functions need at runtime, the answer is typically Systems
> Manager Parameter Store (for non-secret config) or Secrets Manager (for credentials).
> Parameter Store is free for standard parameters.

---

## Quick-Reference: When to Use What

| Scenario | Service |
|---|---|
| "Monitor model invocation latency and token counts" | CloudWatch metrics (`AWS/Bedrock`) |
| "Analyze the actual prompts sent to the model" | CloudWatch Logs (model invocation logging) |
| "Query prompt patterns across thousands of invocations" | CloudWatch Logs Insights |
| "Detect unusual token usage patterns automatically" | CloudWatch Anomaly Detection |
| "Audit who called InvokeModel and when" | CloudTrail |
| "Track which IAM user created a knowledge base" | CloudTrail (management event) |
| "Log InvokeAgent calls for compliance" | CloudTrail data events (AWS::Bedrock::AgentAlias) |
| "Monitor availability of our GenAI API from outside" | CloudWatch Synthetics (canaries) |
| "Alert the team in Slack when latency breaches SLA" | CloudWatch Alarm -> SNS -> AWS Chatbot |
| "Visualize Bedrock metrics alongside Prometheus data" | Amazon Managed Grafana |
| "Detect unexpected Bedrock cost spike" | AWS Cost Anomaly Detection |
| "See Bedrock spend broken down by model" | AWS Cost Explorer |
| "Assess our GenAI workload against best practices" | Well-Architected Tool (GenAI Lens) |
| "Provide pre-approved GenAI infrastructure templates" | AWS Service Catalog |
| "Store model configuration securely" | Systems Manager Parameter Store |
| "Scale SageMaker inference endpoint instances" | Application Auto Scaling |
| "Detect unusual API call volume to Bedrock" | CloudTrail Insights |
| "Mask PII in Bedrock invocation logs" | CloudWatch Logs data protection |
| "Detect anomalous log patterns in invocation logs" | CloudWatch Logs anomaly detection |

---

## Common Exam Gotchas

1. **CloudTrail vs. Invocation Logging** -- CloudTrail captures API call metadata (who, what,
   when). Model invocation logging captures prompt/response content. The exam will present
   scenarios where one is clearly the right answer but the other sounds plausible.

2. **Bedrock metrics are automatic; invocation logging is not** -- Metrics in `AWS/Bedrock`
   flow to CloudWatch as soon as you make Bedrock API calls. Model invocation logging must be
   explicitly enabled in Bedrock settings.

3. **Throttles are not counted as Invocations or Errors** -- If you calculate error rates
   using metric math, you need to include throttles separately:
   `total_requests = Invocations + InvocationThrottles + InvocationClientErrors + InvocationServerErrors`.

4. **CloudWatch Anomaly Detection vs. CloudTrail Insights** -- Anomaly Detection is for
   metrics (latency, token counts). CloudTrail Insights is for API activity patterns (call
   volume, error rates). Different tools, different data sources.

5. **Cost Anomaly Detection has a delay** -- It runs ~3x/day. It will not catch a cost spike
   in real time. For real-time cost alerting, use CloudWatch custom metrics with alarms.

6. **Bedrock is serverless -- no Auto Scaling** -- You cannot attach Auto Scaling policies to
   Bedrock. Use Provisioned Throughput for guaranteed capacity, or cross-region inference for
   load distribution. Auto Scaling applies to SageMaker, ECS, Lambda concurrency.

7. **Three different Bedrock CloudWatch namespaces:**
   - `AWS/Bedrock` -- runtime metrics (invocations, tokens, latency)
   - `AWS/Bedrock/Guardrails` -- guardrail evaluation metrics
   - `AWS/Bedrock/Agents` -- agent invocation metrics

8. **Guardrail `InvocationsIntervened`** -- this is the metric that tells you how often
   guardrails blocked or modified content. For Task 3.4.2 (pre-defined fairness metrics),
   this metric combined with `GuardrailPolicyType` dimension gives you per-policy intervention
   rates.

9. **Well-Architected GenAI Lens is a custom lens** -- it must be downloaded and imported into
   the WA Tool. It is not a built-in lens. It covers all six pillars and all stages of the
   GenAI lifecycle.

10. **Log group size limits for CloudWatch Logs** -- Invocation log events are capped at 100 KB
    in CloudWatch Logs. Anything larger (images, long prompts/responses) must go to S3. If a
    question mentions large payloads, the answer involves S3 delivery.
