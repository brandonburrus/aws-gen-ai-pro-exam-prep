# Prompt Management and Evaluation Pipeline: Findings

## Overview

This document reports the results of running the automated evaluation pipeline built in Project 02.
The pipeline evaluated three Bedrock prompt templates (direct-instruction, chain-of-thought, and
few-shot) against two Amazon Nova models (Nova Lite and Nova Pro) across five AWS knowledge
questions, producing 30 scored responses in total.

Scoring was performed by an LLM-as-a-Judge (Nova Pro) on two dimensions: relevance (does the
answer address the question?) and consistency (is the answer internally coherent?). Both dimensions
use a 1 to 5 integer scale.

---

## Evaluation Setup

| Dimension            | Value                                      |
| -------------------- | ------------------------------------------ |
| Templates evaluated  | direct-instruction, chain-of-thought, few-shot |
| Models under test    | `us.amazon.nova-lite-v1:0`, `us.amazon.nova-pro-v1:0` |
| Judge model          | `us.amazon.nova-pro-v1:0`                  |
| Questions            | 5 AWS knowledge questions                  |
| Total evaluations    | 30 (3 templates x 2 models x 5 questions)  |
| Scoring dimensions   | Relevance (1-5), Consistency (1-5)         |

### Questions

1. What is the difference between Amazon S3 Standard and S3 Glacier storage classes, and when should you use each?
2. Explain how AWS Lambda cold starts work and what strategies can reduce their impact on application latency.
3. What are the key differences between Amazon RDS and Amazon DynamoDB, and how do you decide which to use?
4. Describe how Amazon VPC peering works and what its limitations are compared to AWS Transit Gateway.
5. What is the shared responsibility model in AWS, and how does it affect security obligations for EC2 instances?

---

## Score Results

### By Template

| Template            | Avg Relevance | Avg Consistency | Items |
| ------------------- | ------------- | --------------- | ----- |
| direct-instruction  | 5.0           | 5.0             | 10    |
| chain-of-thought    | 5.0           | 5.0             | 10    |
| few-shot            | 5.0           | 5.0             | 10    |

### By Model

| Model                    | Avg Relevance | Avg Consistency | Items |
| ------------------------ | ------------- | --------------- | ----- |
| `us.amazon.nova-lite-v1:0` | 5.0           | 5.0             | 15    |
| `us.amazon.nova-pro-v1:0`  | 5.0           | 5.0             | 15    |

All 30 evaluations received the maximum score of 5 on both dimensions. The judge found every
response directly addressed its question and was internally coherent with no contradictions.

---

## Output Verbosity by Template

While scores were uniform, the templates produced meaningfully different output lengths.

| Template            | Avg Output Tokens (Nova Lite) | Avg Output Tokens (Nova Pro) |
| ------------------- | ----------------------------- | ---------------------------- |
| direct-instruction  | ~133                          | ~116                         |
| chain-of-thought    | ~632                          | ~802                         |
| few-shot            | ~597                          | ~736                         |

Direct-instruction responses were concise and targeted. Chain-of-thought and few-shot responses
were 4 to 6 times longer, structured with markdown headings, numbered lists, and subsections.
This verbosity had no measurable effect on either relevance or consistency scores.

---

## Token Usage and Cost Profile

| Stage                    | Input Tokens | Output Tokens |
| ------------------------ | ------------ | ------------- |
| Model invocations (x30)  | 7,184        | 16,068        |
| Judge invocations (x30)  | 21,852       | 1,801         |
| **Total**                | **29,036**   | **17,869**    |

The judge consumed roughly three times more input tokens than the models under test because each
judge call includes the full model answer in its context window. For long outputs (chain-of-thought
and few-shot), judge input tokens per call ranged from 842 to 1,157 tokens compared to 279 to 474
for direct-instruction outputs.

---

## Findings

### Finding 1: Prompt structure did not affect answer quality on factual AWS topics

All three templates produced maximum scores on every question. For well-scoped, factual questions
where the correct answer is knowable and bounded, structured prompting (chain-of-thought, few-shot)
does not improve relevance or consistency over a plain direct-instruction prompt.

This does not mean chain-of-thought and few-shot templates are without value. On tasks requiring
multi-step reasoning, ambiguous interpretation, or novel problem solving, those templates are
expected to show a measurable advantage. The five questions used here did not require that kind of
reasoning.

### Finding 2: Nova Lite matched Nova Pro in answer quality at lower cost

Nova Lite produced scores identical to Nova Pro across all 15 paired comparisons. For an exam
preparation use case where answers to known questions are being evaluated, the smaller model is
fully adequate and would reduce invocation cost by the Nova Lite to Nova Pro pricing ratio.

Nova Pro produced slightly longer answers (averaging ~100 additional tokens per response on
chain-of-thought and few-shot templates), suggesting it is more verbose by default, but that
verbosity did not translate to a quality advantage under this judge's rubric.

### Finding 3: Direct-instruction is the most cost-efficient template by a significant margin

Direct-instruction outputs averaged 84 to 162 tokens depending on model, versus 514 to 962 tokens
for chain-of-thought and few-shot. Since judge input tokens scale with answer length, using
direct-instruction reduces total pipeline cost by approximately 60 to 70 percent per evaluation
run compared to the structured templates, with no quality penalty on these question types.

### Finding 4: The judge scoring ceiling suggests rubric or question set limitations

Every response received 5/5 on both dimensions. A ceiling result like this can mean one of three
things: the models genuinely produced perfect answers, the questions were too easy to discriminate
between response quality levels, or the judge's rubric was insufficiently granular to detect
meaningful differences.

The most likely explanation is a combination of the second and third. The five questions are
standard AWS certification topics with well-established correct answers. Both Nova models have
clearly been trained on this material. The judge rubric rewards relevance and consistency but does
not evaluate technical depth, accuracy of specific claims, presence of common misconceptions, or
completeness of coverage. A rubric that scored factual precision, mention of key subtleties (such
as S3 Glacier retrieval tier pricing, or the n*(n-1)/2 peering connection growth problem), and
conciseness would likely surface meaningful differences between templates and models.

### Finding 5: The pipeline infrastructure is sound and suitable for more discriminating evaluations

The Step Functions workflow, LLM-as-a-Judge scoring loop, S3 result storage, and CloudWatch metric
emission all functioned correctly end to end. The architecture supports straightforward extension:
adding questions, templates, or models requires only changes to the state machine input payload and
the prompt definitions in Bedrock Prompt Management. No infrastructure changes are needed to scale
the evaluation surface.

---

## Recommendations

**For question design:** Use questions that have gradations of correct answers rather than binary
correct/incorrect responses. Scenario-based questions (for example, "A company needs sub-10ms
read latency on user session data at unpredictable traffic spikes. Which AWS database service and
configuration would you recommend and why?") will expose differences between templates and models
that factual recall questions cannot.

**For the judge rubric:** Add scoring dimensions for technical accuracy, completeness, and
conciseness alongside the existing relevance and consistency dimensions. Consider a rubric that
explicitly penalizes over-length responses that pad correct answers with unnecessary structure,
which would disadvantage few-shot and chain-of-thought on simpler questions.

**For model selection:** Based on these results, Nova Lite is sufficient for answer generation on
factual AWS topics. Reserve Nova Pro for judge duties, where reasoning quality over longer contexts
matters more.

**For template selection:** Direct-instruction is the default choice for factual question sets.
Reserve chain-of-thought for questions that require the model to reason through trade-offs or
derive an answer from first principles. Reserve few-shot for questions where output format
consistency is important and example outputs need to demonstrate the expected structure.
