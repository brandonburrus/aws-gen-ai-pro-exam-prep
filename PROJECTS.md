# Hands-On Projects for AIP-C01 Exam Preparation

12 focused projects (2-3 hours each) ordered by exam domain weight, collectively covering all 5 content domains and all 20 tasks.

## Project 1: RAG Chat Application with Bedrock Knowledge Bases

**Domains:** 1.4, 1.5

Ingest a set of PDF documents into a Bedrock Knowledge Base backed by OpenSearch Serverless. Build a Lambda-powered chat API that retrieves relevant chunks and augments prompts with context. Experiment with chunking strategies (fixed-size vs. hierarchical) and observe how they affect answer quality.

## Project 2: Prompt Management and Evaluation Pipeline

**Domains:** 1.6, 5.1

Create parameterized prompt templates in Bedrock Prompt Management with variables for role, context, and output format. Build a Step Functions workflow that runs the same query across multiple templates and models, logs results to CloudWatch, and scores outputs for relevance and consistency.

## Project 3: Multi-Model Router with Fallback

**Domains:** 1.2, 2.4

Build an API Gateway + Lambda system that routes requests to different Bedrock models based on query complexity (simple queries to a smaller/cheaper model, complex ones to a larger model). Implement exponential backoff, a circuit breaker pattern with Step Functions, and cross-region fallback when a model is unavailable.

## Project 4: Agentic Tool-Use Chatbot with Strands Agents

**Domains:** 2.1

Build an agent using Strands Agents SDK that can call external tools -- a weather API, a calculator, and a DynamoDB lookup. Define tool schemas with function calling, implement parameter validation and error handling in Lambda, and add conversation memory with DynamoDB.

## Project 5: Guardrails and Content Safety Layer

**Domains:** 3.1, 3.2

Configure Bedrock Guardrails with denied topics, word filters, and PII redaction. Build a Lambda function that wraps Bedrock invocations with pre-processing (Amazon Comprehend for PII detection and intent classification) and post-processing (output validation against JSON Schema). Test with adversarial prompts including injection attempts and jailbreaks.

## Project 6: Secure GenAI API with Governance Controls

**Domains:** 3.2, 3.3, 4.3

Deploy a Bedrock-backed API inside a VPC with PrivateLink endpoints, Cognito authentication, and IAM least-privilege policies. Enable CloudTrail logging for all Bedrock API calls, configure Bedrock Model Invocation Logs to S3, and build a CloudWatch dashboard tracking invocation counts, token usage, and error rates.

## Project 7: Streaming Chat UI with Amplify

**Domains:** 2.4, 2.5

Build a web frontend with AWS Amplify that calls Bedrock's streaming API through API Gateway with WebSocket support. Display tokens as they arrive in real time. Add a feedback thumbs-up/thumbs-down mechanism that writes ratings to DynamoDB for later evaluation.

## Project 8: Cost-Optimized Inference with Caching and Token Management

**Domains:** 4.1, 4.2

Build a Lambda function that estimates token counts before invocation, implements semantic caching with ElastiCache (hash similar prompts to reuse responses), enforces max token limits, and routes between on-demand and provisioned throughput based on traffic. Log cost metrics to CloudWatch and build a Cost Explorer dashboard.

## Project 9: RAG Evaluation and Troubleshooting Harness

**Domains:** 5.1, 5.2

Create a golden dataset of question-answer pairs with source documents. Build a Step Functions pipeline that runs each question through your RAG system, compares answers against ground truth using an LLM-as-a-Judge evaluation (a second Bedrock model scores relevance, faithfulness, and completeness), and generates a report. Add embedding drift detection by comparing vector similarity distributions over time.

## Project 10: CI/CD Pipeline for GenAI Application

**Domains:** 2.3, 5.1

Use CDK to define infrastructure for a complete GenAI stack (Lambda, API Gateway, Bedrock, OpenSearch). Build a CodePipeline that runs prompt regression tests in CodeBuild (comparing outputs against baseline responses for semantic drift), validates guardrail configurations, and deploys with automated rollback on quality gate failure.

## Project 11: Multimodal Data Pipeline with Validation

**Domains:** 1.1, 1.3

Build a Step Functions pipeline that ingests text, image, and audio files from S3, validates them with Glue Data Quality rules and custom Lambda checks, processes audio through Transcribe, extracts entities with Comprehend, formats everything into Bedrock-compatible JSON payloads, and invokes the model. Design the architecture using the Well-Architected GenAI Lens checklist and document your decisions.

## Project 12: Foundation Model Deployment with Responsible AI Evaluation

**Domains:** 2.2, 3.4

Deploy a fine-tuned model to a SageMaker AI endpoint in a container optimized for GPU/memory, then set up an on-demand Bedrock model as a cascade fallback for overflow traffic. Build an evaluation pipeline that uses a second model as an LLM-as-a-Judge to score both deployments for fairness across demographic prompt variations, logs confidence metrics to CloudWatch, generates a SageMaker model card documenting limitations, and enables Bedrock agent tracing to surface reasoning paths.
