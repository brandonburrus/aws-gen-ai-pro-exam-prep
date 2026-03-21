# Project 02: Prompt Management and Evaluation Pipeline

## Exam Domains

| Domain | Task | Description |
|--------|------|-------------|
| 1.6 | Implement prompt engineering strategies and governance | Parameterized templates, prompt management systems, quality assurance, approval workflows |
| 5.1 | Implement evaluation systems for GenAI | Systematic quality assurance, regression testing, automated scoring, LLM-as-a-Judge |

## Overview

Prompt management is a frequently tested governance topic on the AIP-C01 exam. Ad-hoc prompt strings embedded in application code are unversioned, untestable, and impossible to audit — a pattern the exam consistently penalizes. This project replaces that anti-pattern with a production-grade approach: prompts live in Amazon Bedrock Prompt Management as versioned, parameterized templates with named variables, and a Step Functions workflow drives systematic evaluation across multiple templates and models.

The evaluation pipeline is the other pillar of this project. Rather than eyeballing outputs manually, you will build an automated scoring workflow: Step Functions invokes a set of prompt variants, collects the raw outputs, feeds each output plus the original question to a second "judge" model that scores relevance and consistency on a 1-5 scale, and publishes all scores as custom CloudWatch metrics. This directly practices Task 5.1 (LLM-as-a-Judge evaluation) alongside Task 1.6 (prompt governance).

By the end of the session you will have a reusable prompt evaluation harness and a concrete understanding of how Bedrock Prompt Management fits into a governed GenAI architecture.

## Architecture

```
Bedrock Prompt Management
    |-- Template A (concise role, structured output)
    |-- Template B (verbose role, chain-of-thought)
    |-- Template C (few-shot examples)
    |
    v
Step Functions (EvaluationStateMachine)
    |-- Map state: iterate over test questions
    |       |-- Lambda: render each template with question variable
    |       |-- Bedrock InvokeModel: Claude 3 Haiku (fast/cheap)
    |       |-- Bedrock InvokeModel: Claude 3 Sonnet (capable)
    |       |-- Lambda: judge each output with a scoring prompt
    |       |-- CloudWatch PutMetricData: relevance + consistency scores
    |-- Lambda: aggregate results, write summary to S3
    |
    v
CloudWatch Metrics / Dashboard
    S3 (evaluation-results.json)
```

**AWS services used:**

- Amazon Bedrock Prompt Management -- stores versioned, parameterized prompt templates
- AWS Step Functions (Standard workflow) -- orchestrates the evaluation loop
- AWS Lambda -- renders templates, calls Bedrock, scores outputs, aggregates results
- Amazon Bedrock (Claude 3 Haiku, Claude 3 Sonnet) -- generates responses and acts as judge
- Amazon CloudWatch -- receives custom metrics and hosts the evaluation dashboard
- Amazon S3 -- stores raw evaluation results JSON
- AWS IAM -- execution roles for Step Functions and Lambda
- Amazon CloudWatch Logs -- captures execution traces

## What You Will Build

1. Three parameterized prompt templates in Bedrock Prompt Management, each with at least three variables: `{{role}}`, `{{context}}`, and `{{question}}`. Each template takes a different prompting approach (concise instruction, chain-of-thought, few-shot).
2. A published version (v1) of each template so the Step Functions workflow can reference immutable ARNs.
3. A Step Functions Standard workflow with a Map state that iterates over a hardcoded array of 5 test questions, invoking each template + model combination (3 templates × 2 models = 6 invocations per question).
4. A Lambda-based scoring function that calls a third Bedrock model (Claude 3 Haiku) with a judge prompt, receives a JSON score `{ "relevance": 1-5, "consistency": 1-5, "reasoning": "..." }`, and returns it to Step Functions.
5. A Lambda aggregation function that receives all scores, computes per-template and per-model averages, and writes a `evaluation-results.json` summary to S3.
6. Custom CloudWatch metrics under namespace `GenAI/PromptEvaluation` for `Relevance` and `Consistency`, dimensioned by `TemplateName` and `ModelId`.
7. A CloudWatch dashboard with two widgets: a line chart of average relevance by template and a line chart of average consistency by model.

## Target Outcomes

By the end of this project you should be able to verify each of the following:

- [ ] All three prompt templates exist in Bedrock Prompt Management with at least one published version each; you can retrieve a template by ARN and inspect its variables.
- [ ] The Step Functions execution completes successfully for all 5 test questions without any Lambda errors; the execution history shows all 30 Bedrock invocations.
- [ ] `evaluation-results.json` in S3 contains scores for every template + model + question combination.
- [ ] CloudWatch metrics appear in the `GenAI/PromptEvaluation` namespace with the correct dimensions; the dashboard displays data.
- [ ] You can identify which template scored highest for relevance and explain one structural reason why (e.g., chain-of-thought instruction keeps the model on topic).
- [ ] You can explain the difference between a prompt template version and a prompt template draft in Bedrock Prompt Management, and why version pinning matters in a production pipeline.

## Prerequisites

**Local tooling:**

- AWS CLI v2 configured with Bedrock, Step Functions, Lambda, CloudWatch, S3, and IAM permissions
- Python 3.11+ with `boto3`
- AWS SAM CLI or CDK CLI (optional but recommended for Lambda deployment)

**AWS service enablement:**

- Amazon Bedrock model access enabled for Claude 3 Haiku and Claude 3 Sonnet in your target region
- Bedrock Prompt Management available in your region (us-east-1 recommended)

**Sample data:**

- 5 test questions on a domain of your choice (e.g., AWS services, a public FAQ topic). Questions should be open-ended enough that answer quality is meaningfully different across prompting styles.

## Step-by-Step Build Guide

1. **Design your three prompt templates.** Each should have the same three input variables (`role`, `context`, `question`) so they are directly comparable. Template A: direct instruction only. Template B: chain-of-thought (`Think step by step before answering`). Template C: two few-shot examples followed by the live question.

2. **Create the templates in Bedrock Prompt Management** using the console or `bedrock-agent:CreatePrompt`. Set the default model to Claude 3 Haiku. Publish v1 of each template with `bedrock-agent:CreatePromptVersion`.

3. **Write the Lambda render + invoke function** (`invoke_template.py`). Accept `{ "prompt_arn": str, "prompt_version": str, "variables": {...}, "model_id": str }`. Call `bedrock-agent:GetPrompt` to fetch the template, substitute variables, then call `bedrock:InvokeModel`. Return `{ "output": str, "input_tokens": int, "output_tokens": int }`.

4. **Write the Lambda judge function** (`score_output.py`). Accept `{ "question": str, "output": str }`. Build a judge prompt asking the model to rate the output on relevance (does it answer the question?) and consistency (is it internally consistent?) and return JSON. Call `bedrock:InvokeModel` with Claude 3 Haiku. Parse and return the JSON scores.

5. **Write the Lambda aggregation function** (`aggregate_results.py`). Accept the full array of scored results. Compute averages grouped by `template_name` and `model_id`. Publish CloudWatch metrics via `put_metric_data`. Write the full results object to S3.

6. **Define the Step Functions state machine** (Amazon States Language or CDK). Structure: `PrepareInput` (Pass state with questions array) → `EvaluateQuestions` (Map state, max concurrency 5) → inside each iteration: `InvokeTemplateA-Haiku`, `InvokeTemplateA-Sonnet`, ... (6 parallel Lambda invocations via Parallel state) → `ScoreOutputs` (Map state, 6 judge invocations) → `AggregateResults` (Lambda). Use `ResultPath` carefully to avoid state bloat.

7. **Deploy all Lambda functions** with appropriate IAM roles. The invoke function needs `bedrock:InvokeModel` and `bedrock-agent:GetPrompt`. The judge function needs `bedrock:InvokeModel`. The aggregation function needs `cloudwatch:PutMetricData` and `s3:PutObject`.

8. **Deploy the state machine** and grant it `lambda:InvokeFunction` on all three functions.

9. **Execute the state machine** and monitor the execution in the Step Functions console. Fix any IAM or payload issues.

10. **Create the CloudWatch dashboard** with widgets for Relevance and Consistency metrics by template and model.

11. **Review results** in S3 and the dashboard. Document your findings in a `findings.md` file in this project folder.

## Key Exam Concepts Practiced

- Bedrock Prompt Management: parameterized templates, versioning, variable substitution (Task 1.6.1, 1.6.3)
- Prompt governance: immutable versioned ARNs, approval workflow pattern (Task 1.6.3)
- Step Functions as an orchestration layer for multi-model evaluation (Task 1.6.4, 5.1.2)
- LLM-as-a-Judge evaluation technique for relevance and consistency scoring (Task 5.1.5)
- Custom CloudWatch metrics and dashboards for GenAI observability (Task 4.3.2)
- Chain-of-thought and few-shot prompting strategies (Task 1.6.5)
- Cost comparison between Haiku (fast/cheap) and Sonnet (capable/expensive) for the same workload (Task 4.1.2)
