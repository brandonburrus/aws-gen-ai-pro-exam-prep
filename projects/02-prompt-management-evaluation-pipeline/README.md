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

- Node.js 22+ with `bun` package manager (`npm install -g bun`)
- AWS CDK CLI (`npm install -g aws-cdk`)
- AWS CLI v2 configured with Bedrock, Step Functions, Lambda, CloudWatch, S3, and IAM permissions

**AWS service enablement:**

- Amazon Bedrock model access enabled for Claude 3 Haiku and Claude 3 Sonnet in your target region
- Bedrock Prompt Management available in your region (us-east-1 recommended)

**Sample data:**

- 5 test questions on a domain of your choice (e.g., AWS services, a public FAQ topic). Questions should be open-ended enough that answer quality is meaningfully different across prompting styles.

## Step-by-Step Build Guide

1. **Initialize the CDK project.** Copy `projects/cdk-template/` into `cdk/`. Update `package.json` `name` to `prompt-evaluation-pipeline`. Run `bun install`.

2. **Create the Bedrock Prompt templates.** Use the Bedrock console or `bedrock-agent:CreatePrompt` to create three parameterized templates (direct instruction, chain-of-thought, few-shot) each with variables `{{role}}`, `{{context}}`, and `{{question}}`. Publish v1 of each with `bedrock-agent:CreatePromptVersion`. Note the versioned ARNs — these are referenced as environment variables in the Lambda functions.

3. **Write Lambda handler `src/lambdas/invoke-template/handler.ts`.** Accept `{ prompt_arn, prompt_version, variables, model_id }`. Fetch the template with `bedrock-agent:GetPrompt`, substitute variables, call `bedrock:InvokeModel`, and return `{ output, input_tokens, output_tokens }`.

4. **Write Lambda handler `src/lambdas/score-output/handler.ts`.** Accept `{ question, output }`. Build a judge prompt instructing the model to return `{ relevance: 1-5, consistency: 1-5, reasoning: string }`. Call `bedrock:InvokeModel` with Claude 3 Haiku. Parse and return the JSON scores.

5. **Write Lambda handler `src/lambdas/aggregate-results/handler.ts`.** Accept the full array of scored results. Compute averages grouped by `template_name` and `model_id`. Publish metrics to CloudWatch under namespace `GenAI/PromptEvaluation`. Write the full results object to S3.

6. **Define the `EvaluationStack`** in `src/stacks/evaluation-stack.ts`. Provision: an S3 bucket for evaluation results, three `NodejsFunction` constructs (one per handler) with appropriate IAM grants (`bedrock:InvokeModel`, `bedrock-agent:GetPrompt`, `cloudwatch:PutMetricData`, `s3:PutObject`), a Step Functions `StateMachine` (Standard workflow) using the L2 `stepfunctions` and `stepfunctions-tasks` CDK modules. Structure the state machine as: `PrepareInput` (Pass) → `EvaluateQuestions` (Map, max concurrency 5) → inside each iteration a `Parallel` state with six `LambdaInvoke` tasks (three templates × two models) → `ScoreOutputs` (Map, six judge invocations) → `AggregateResults` (`LambdaInvoke`). Grant the state machine `lambda:InvokeFunction` on all three Lambda functions.

7. **Define the CloudWatch dashboard** via `aws-cloudwatch.Dashboard` in the stack. Add two `GraphWidget` instances: average relevance by template (`TemplateName` dimension) and average consistency by model (`ModelId` dimension).

8. **Run `bun run synth`** to validate the CloudFormation template output.

9. **Run `bun run deploy`** to provision all resources. Set the three prompt ARNs and the S3 bucket name as Lambda environment variables post-deploy (or inject them as CDK `CfnParameter` values or SSM parameters).

10. **Execute the state machine** from the Step Functions console or via `aws stepfunctions start-execution`. Monitor the execution map. Fix any IAM or payload shape issues.

11. **Review results** in S3 and the CloudWatch dashboard. Document your findings in a `findings.md` file in this project folder.

## Key Exam Concepts Practiced

- Bedrock Prompt Management: parameterized templates, versioning, variable substitution (Task 1.6.1, 1.6.3)
- Prompt governance: immutable versioned ARNs, approval workflow pattern (Task 1.6.3)
- Step Functions as an orchestration layer for multi-model evaluation (Task 1.6.4, 5.1.2)
- LLM-as-a-Judge evaluation technique for relevance and consistency scoring (Task 5.1.5)
- Custom CloudWatch metrics and dashboards for GenAI observability (Task 4.3.2)
- Chain-of-thought and few-shot prompting strategies (Task 1.6.5)
- Cost comparison between Haiku (fast/cheap) and Sonnet (capable/expensive) for the same workload (Task 4.1.2)
