# Project 09: RAG Evaluation and Troubleshooting Harness

## Exam Domains

| Domain | Task | Description |
|--------|------|-------------|
| 5.1 | Implement evaluation systems for GenAI | RAG evaluation, LLM-as-a-Judge, automated quality assessment, golden datasets, retrieval quality testing |
| 5.2 | Troubleshoot GenAI applications | Retrieval system issues, embedding quality diagnostics, drift monitoring, chunking remediation |

## Overview

Building a RAG system is one thing; knowing whether it is working well is another. The AIP-C01 exam tests your ability to design systematic evaluation pipelines that quantify RAG quality across three independent dimensions: relevance (did the retrieved chunks relate to the question?), faithfulness (is the answer grounded in the retrieved context?), and completeness (did the answer fully address the question?). This project builds that evaluation harness end to end.

The project adds a second, forward-looking concern: embedding drift. As your document corpus grows and changes over time, the distribution of embedding vectors in your vector store can shift in ways that degrade retrieval quality without obvious error signals. You will implement a drift detector that periodically computes the average pairwise cosine similarity within your vector store and emits it as a CloudWatch metric — a decrease over time signals that embeddings are becoming less coherent and retrieval quality may be degrading.

This project builds on the Bedrock Knowledge Base created in Project 01 but can also be run standalone against any RAG endpoint.

## Architecture

```
S3: golden-dataset/
    |-- questions.json   [ { id, question, ground_truth_answer, source_doc_id } ]
    |-- source_docs/     (same PDFs from Project 01)

Step Functions: RAGEvaluationPipeline (Standard)
    |
    |-- Map state: for each question in golden dataset
    |       |-- Lambda: RAGQuery
    |       |   --> RetrieveAndGenerate (Bedrock Knowledge Base)
    |       |   --> returns { answer, retrieved_chunks, retrieval_latency_ms }
    |       |
    |       |-- Lambda: JudgeEvaluation
    |           --> Bedrock: Claude 3 Sonnet (judge model)
    |           --> prompt: score relevance, faithfulness, completeness 1-5 + reasoning
    |           --> returns { relevance: int, faithfulness: int, completeness: int, reasoning: str }
    |
    |-- Lambda: GenerateReport
        |-- Compute per-metric averages
        |-- Flag questions with any score <= 2 as "needs attention"
        |-- Write report to S3: evaluation-reports/YYYY-MM-DD-HH.json
        |-- Emit CloudWatch metrics: AvgRelevance, AvgFaithfulness, AvgCompleteness
        |-- Publish SNS alert if any average drops below threshold (3.5)

Step Functions: DriftDetectionPipeline (scheduled, EventBridge rule every 6 hours)
    |-- Lambda: SampleEmbeddings
    |       --> Bedrock Knowledge Base: retrieve random sample of 50 embeddings
    |       --> compute average pairwise cosine similarity
    |       --> emit CloudWatch metric: EmbeddingCohesion
    |-- Lambda: DetectDrift
            --> compare current EmbeddingCohesion vs. 7-day moving average
            --> if delta > 10%: publish SNS alert "Embedding drift detected"

CloudWatch Dashboard: RAGEvaluation
SNS Topic: evaluation-alerts
```

**AWS services used:**

- Amazon S3 -- golden dataset storage and evaluation report storage
- AWS Step Functions (Standard workflow) -- evaluation pipeline orchestration
- AWS Lambda -- RAG query executor, judge evaluator, report generator, drift detector
- Amazon Bedrock Knowledge Bases (`bedrock-agent-runtime:RetrieveAndGenerate`) -- the RAG system under test
- Amazon Bedrock (Claude 3 Sonnet as judge) -- LLM-as-a-Judge scoring
- Amazon CloudWatch Metrics + Dashboard -- evaluation scores over time, embedding drift
- Amazon SNS -- alert notifications when scores drop below threshold
- Amazon EventBridge (Scheduler) -- triggers drift detection pipeline every 6 hours
- AWS IAM -- least-privilege roles

## What You Will Build

1. A golden dataset of 10 question-answer pairs in `questions.json`, where each answer is directly verifiable from the source documents used in Project 01 (or any documents you ingest). Include `source_doc_id` to enable retrieval attribution checks.
2. A Step Functions Standard workflow `RAGEvaluationPipeline` that iterates over the golden dataset and produces a full evaluation report.
3. A Lambda `RAGQuery` function that calls `RetrieveAndGenerate`, captures the retrieved chunk text and source citations, measures latency, and returns all of it to Step Functions.
4. A Lambda `JudgeEvaluation` function with a carefully crafted judge prompt that instructs Claude 3 Sonnet to score a given (question, retrieved_context, answer, ground_truth) tuple on three dimensions: relevance (are the retrieved chunks related to the question?), faithfulness (is the answer supported by the retrieved context?), and completeness (does the answer fully address the question?). The judge must return valid JSON.
5. A Lambda `GenerateReport` that aggregates all scores, writes a JSON report to S3, emits three custom CloudWatch metrics, and publishes an SNS alert if any metric average falls below 3.5.
6. A drift detection Lambda that samples the vector store by running 50 random single-word queries and computing average cosine similarity between the returned embedding vectors. Emits `EmbeddingCohesion` to CloudWatch.
7. A CloudWatch dashboard `RAGEvaluation` with time-series charts for all four metrics (AvgRelevance, AvgFaithfulness, AvgCompleteness, EmbeddingCohesion) and a CloudWatch Logs Insights widget showing the most recent "needs attention" questions.
8. An EventBridge Scheduler rule that triggers the drift detection pipeline every 6 hours.
9. A `run_evaluation.py` script that starts the Step Functions execution and tails the CloudWatch Logs output until completion.

## Target Outcomes

By the end of this project you should be able to verify each of the following:

- [ ] Running the evaluation pipeline to completion produces an evaluation report in S3 with scores for all 10 golden dataset questions.
- [ ] The CloudWatch dashboard shows non-zero values for AvgRelevance, AvgFaithfulness, and AvgCompleteness.
- [ ] At least one golden dataset question receives a faithfulness score of 5 (the answer is fully supported by the retrieved context) and you can explain which chunk provided the supporting evidence.
- [ ] At least one golden dataset question receives a score of 3 or lower on at least one dimension, and you can articulate why (e.g., the retrieved chunk did not contain enough context for a complete answer).
- [ ] The drift detection Lambda runs and emits the `EmbeddingCohesion` metric to CloudWatch.
- [ ] You can explain the difference between relevance, faithfulness, and completeness as evaluation dimensions, and give an example of an answer that scores high on faithfulness but low on completeness.

## Prerequisites

**Local tooling:**

- Node.js 22+ with npm (for Lambda handler development and AWS SDK v3)
- AWS CLI v2 with Step Functions, Lambda, Bedrock, S3, CloudWatch, SNS, EventBridge, and IAM permissions
- Python 3.11+ with `boto3` and `numpy` (for Lambda handler source)
- A working Bedrock Knowledge Base (from Project 01 or newly created with any document set)

**AWS service enablement:**

- Amazon Bedrock model access enabled for Claude 3 Sonnet (judge model) and the embedding model used in your knowledge base
- Bedrock Knowledge Bases available in your region

**Sample golden dataset design tip:**

Write the golden dataset by reading the source documents yourself. Include: 3 questions with direct single-sentence answers in the docs, 3 questions requiring synthesis across multiple paragraphs, 2 questions that test a document boundary (the answer spans two chunks), and 2 "trick" questions where the answer is not in the documents (expected: low faithfulness score).

## Step-by-Step Build Guide

1. **Create the golden dataset.** Write `golden-dataset/questions.json` with 10 question-answer pairs (format: `[{ id, question, ground_truth_answer, source_doc_id }]`). Include: 3 questions with direct single-sentence answers, 3 requiring synthesis across multiple paragraphs, 2 testing a document boundary (answer spans two chunks), and 2 "trick" questions where the answer is not in the documents.

2. **Write the RAGQuery Lambda handler** (`lambdas/rag-query/handler.ts`). Call `bedrock-agent-runtime:RetrieveAndGenerate` with the knowledge base ID and the question. Capture the retrieved chunk text, source citations, and measure end-to-end latency. Return `{ answer, retrieved_chunks, citations, latency_ms }`.

3. **Write the JudgeEvaluation Lambda handler** (`lambdas/judge-evaluation/handler.ts`). Build a judge prompt with the system prompt establishing the judge role and scoring criteria. The user message contains the question, retrieved context (all chunks concatenated), the generated answer, and the ground truth. Call `bedrock:InvokeModel` with Claude 3 Sonnet. Parse and return `{ relevance: number, faithfulness: number, completeness: number, reasoning: { relevance: string, faithfulness: string, completeness: string } }`. Instruct the judge to base faithfulness only on the retrieved context, not on its own knowledge.

4. **Write the GenerateReport Lambda handler** (`lambdas/generate-report/handler.ts`). Compute per-metric averages, flag questions with any score <= 2 as "needs attention", write the full report to S3 at `evaluation-reports/YYYY-MM-DD-HH.json`, emit three custom CloudWatch metrics (`AvgRelevance`, `AvgFaithfulness`, `AvgCompleteness`) under a custom namespace, and publish an SNS alert if any metric average falls below 3.5.

5. **Write the DriftDetector Lambda handler** (`lambdas/drift-detector/handler.ts`). Run 50 random single-word queries against the Knowledge Base via `bedrock-agent-runtime:Retrieve`. Collect the returned embedding vectors, compute average pairwise cosine similarity, and emit `EmbeddingCohesion` as a CloudWatch metric.

6. **Create an S3 bucket** for golden dataset storage and evaluation reports. Upload `questions.json` under the `golden-dataset/` prefix.

7. **Create four Lambda functions** (one per handler). Runtime: Node.js 22.x. Create execution roles:
   - `RAGQuery`: `bedrock:RetrieveAndGenerate`, `bedrock:Retrieve` on the knowledge base ARN
   - `JudgeEvaluation`: `bedrock:InvokeModel` on the Claude 3 Sonnet model ARN
   - `GenerateReport`: `s3:PutObject` on the reports bucket, `cloudwatch:PutMetricData`, `sns:Publish` on the alerts topic
   - `DriftDetector`: `bedrock:Retrieve` on the knowledge base ARN, `cloudwatch:PutMetricData`

8. **Create a Step Functions Standard workflow** (`RAGEvaluationPipeline`). Structure: `LoadDataset` (Lambda reads `questions.json` from S3) -> `EvaluateQuestions` (Map state, max concurrency 3) -> inside each iteration: `QueryRAG` (invoke RAGQuery) -> `Judge` (invoke JudgeEvaluation) -> after Map completes: `GenerateReport` (invoke GenerateReport Lambda). Grant the state machine execution role `lambda:InvokeFunction` on all relevant Lambda functions and `s3:GetObject` on the golden dataset bucket.

9. **Create an SNS topic** for evaluation alerts. Subscribe your email address and confirm the subscription.

10. **Create an EventBridge Scheduler rule** that triggers the DriftDetector Lambda on a schedule of every 6 hours.

11. **Create a CloudWatch dashboard** named `RAGEvaluation` with time-series charts for `AvgRelevance`, `AvgFaithfulness`, `AvgCompleteness`, and `EmbeddingCohesion`, plus a CloudWatch Logs Insights widget showing the most recent "needs attention" questions.

12. **Deploy all resources to your AWS account** using your preferred infrastructure-as-code tool or the AWS Management Console.

13. **Run the evaluation pipeline** via `scripts/run_evaluation.py` or `aws stepfunctions start-execution`. Monitor execution in the Step Functions console. Verify the S3 report and CloudWatch metrics populate.

14. **Review the CloudWatch dashboard.** Identify at least one golden dataset question with a faithfulness score of 5 (explain which chunk provided support) and at least one with a score of 3 or lower (explain the failure mode).

## Key Exam Concepts Practiced

- LLM-as-a-Judge evaluation: relevance, faithfulness, and completeness as independent dimensions (Task 5.1.5)
- Golden dataset design principles: direct answers, multi-chunk synthesis, out-of-corpus questions (Task 5.1.1)
- Step Functions orchestration of automated evaluation pipelines (Task 5.1.4)
- Embedding drift detection as a retrieval health signal (Task 5.2.4)
- CloudWatch custom metrics and alerting for evaluation quality monitoring (Task 4.3.2)
- Retrieval attribution: using citation metadata to verify faithfulness (Task 5.1.6)
- EventBridge Scheduler for scheduled automated quality checks (Task 5.1.4)
- Troubleshooting low scores: is it a chunking problem, an embedding problem, or a generation problem? (Task 5.2.4)
