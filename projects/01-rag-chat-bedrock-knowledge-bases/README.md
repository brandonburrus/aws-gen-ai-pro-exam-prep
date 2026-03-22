# Project 01: RAG Chat Application with Bedrock Knowledge Bases

## Exam Domains

| Domain | Task | Description |
|--------|------|-------------|
| 1.4 | Design and implement vector store solutions | Build vector DB architectures for FM augmentation using Bedrock Knowledge Bases and OpenSearch Serverless |
| 1.5 | Design retrieval mechanisms for FM augmentation | Implement chunking strategies, embedding selection, semantic search, and query handling |

## Overview

Retrieval-Augmented Generation (RAG) is one of the most heavily tested architectural patterns on the AIP-C01 exam. This project builds a complete, working RAG pipeline: PDF documents are ingested into an Amazon Bedrock Knowledge Base backed by an OpenSearch Serverless vector index, and a Lambda-powered HTTP API accepts user questions, retrieves relevant document chunks, and returns answers grounded in the source material.

The second half of the project focuses on a core exam concept — chunking strategy tradeoffs. You will ingest the same document corpus twice using different chunking configurations (fixed-size vs. hierarchical), query both knowledge bases with the same set of questions, and observe how chunk boundaries affect the relevance and completeness of retrieved context. This hands-on comparison directly reinforces Task 1.5.1 (document segmentation) and Task 1.4.3 (high-performance vector architectures).

By the end of the session you will have a fully operational RAG API and a documented comparison of chunking strategies with concrete examples showing how each approach affects answer quality.

## Architecture

```
S3 (source PDFs)
    |
    v
Bedrock Knowledge Base (sync job)
    |-- Amazon Titan Embeddings (embedding model)
    |-- OpenSearch Serverless (vector index)
    |
    v
API Gateway (HTTP API)
    |
    v
Lambda (chat handler)
    |-- RetrieveAndGenerate API  -->  Bedrock Knowledge Base
    |-- Claude 3 Sonnet (generation model)
    |
    v
HTTP response (answer + source citations)
```

**AWS services used:**

- Amazon S3 -- stores source PDF documents
- Amazon Bedrock Knowledge Bases -- manages ingestion, chunking, embedding, and sync
- Amazon OpenSearch Serverless -- hosts the vector index (collection + index)
- Amazon Titan Text Embeddings v2 -- converts chunks to vector representations
- Amazon Bedrock (Claude 3 Sonnet or Haiku) -- generates answers from retrieved context
- AWS Lambda -- implements the chat request handler
- Amazon API Gateway (HTTP API) -- exposes the chat endpoint
- AWS IAM -- least-privilege execution roles for Lambda and Bedrock
- Amazon CloudWatch Logs -- captures Lambda invocation logs

## What You Will Build

1. An S3 bucket loaded with 3-5 sample PDF documents (AWS whitepapers or public documentation work well).
2. Two Bedrock Knowledge Bases pointing at the same S3 bucket, one configured with fixed-size chunking (300 tokens, 20% overlap) and one with hierarchical chunking.
3. An OpenSearch Serverless collection and vector index for each knowledge base.
4. A Lambda function that accepts a `{ "question": "..." }` JSON body, calls `bedrock-agent-runtime:RetrieveAndGenerate` against a specified knowledge base, and returns the model answer plus source chunk citations.
5. An HTTP API Gateway route `POST /chat` wired to the Lambda function.
6. A local test script (Python or shell) that fires the same 5 test questions at both knowledge base endpoints and writes the responses side-by-side to a Markdown comparison file.
7. A short written summary (added to the comparison file) noting which chunking strategy produced better results for each question type and why.

## Target Outcomes

By the end of this project you should be able to verify each of the following:

- [ ] Uploading a new PDF to the S3 bucket and triggering a knowledge base sync job completes without errors.
- [ ] `POST /chat` with a question about content in the uploaded PDFs returns a coherent answer with at least one source citation referencing the correct document.
- [ ] The same question directed at both knowledge bases returns answers; you can explain why the chunk boundaries visible in the citations differ between fixed-size and hierarchical strategies.
- [ ] Lambda logs in CloudWatch show the retrieved chunk count, the model used, and total latency for each request.
- [ ] You can describe the role of Amazon Titan Embeddings in the pipeline and explain what would change if you swapped it for a different embedding model.
- [ ] You can articulate one scenario where hierarchical chunking outperforms fixed-size chunking and one where it does not.

## Prerequisites

**Local tooling:**

- Node.js 22+ with `bun` package manager (`npm install -g bun`)
- AWS CDK CLI (`npm install -g aws-cdk`)
- AWS CLI v2 configured with a profile that has permissions for Bedrock, S3, Lambda, API Gateway, OpenSearch Serverless, and IAM
- Python 3.11+ with `boto3` installed (for the chunking comparison test script)

**AWS service enablement:**

- Amazon Bedrock model access enabled for Amazon Nova Lite and Amazon Titan Text Embeddings v2 in your target region (us-east-1 or us-west-2 recommended)
- OpenSearch Serverless available in your region

**Sample data:**

- 3-5 PDF documents totalling at least 50 pages. AWS whitepapers (e.g., the Well-Architected Framework PDF, the Bedrock User Guide chapters) are ideal because the answers are verifiable.

## Step-by-Step Build Guide

1. **Initialize the CDK project.** Copy `projects/cdk-template/` into `cdk/`. Update `package.json` `name` to `rag-chat-kb`. Run `bun install` to fetch all CDK and esbuild dependencies.

2. **Define the `OpenSearchVectorCollection` construct** in `src/constructs/opensearch-vector-collection.ts`. The construct provisions a `CfnCollection` of type `VECTORSEARCH`, an encryption policy, a network policy allowing public access, and a data access policy granting both the deploying role and the Knowledge Base execution roles full index access.

3. **Define the `OpenSearchVectorIndex` construct** in `src/constructs/opensearch-vector-index.ts`. Use a custom `AwsCustomResource` backed by a Lambda function that calls the OpenSearch REST API to create the kNN index. Fields: `bedrock-knowledge-base-default-vector` (knn_vector, 1536 dimensions), `AMAZON_BEDROCK_TEXT_CHUNK` (text), `AMAZON_BEDROCK_METADATA` (text).

4. **Define the `BedrockKnowledgeBase` construct** in `src/constructs/bedrock-knowledge-base.ts`. Provisions a `CfnKnowledgeBase` with an `OPENSEARCH_SERVERLESS` storage configuration pointing at the collection ARN and vector index name. Attaches a `CfnServiceLinkedRoleForBedrockKnowledgeBase` or creates a custom execution role with permissions for `aoss:APIAccessAll` and `bedrock:InvokeModel`.

5. **Define the `BedrockDataSource` construct** in `src/constructs/bedrock-data-source.ts`. Provisions a `CfnDataSource` scoped to the given Knowledge Base ID. Accept a `chunkingConfig` prop that toggles between `FIXED_SIZE` (300 tokens, 10% overlap) and `HIERARCHICAL` (parent 1500 tokens, child 300 tokens, 60-token overlap) strategies.

6. **Define the `AskPdfQuestionFunction` construct** in `src/constructs/ask-pdf-question-function.ts`. Uses `NodejsFunction` with `src/lambdas/ask-pdf-question/handler.ts` as the entry. The handler accepts `{ question: string, kb_id: string }`, calls `bedrock-agent-runtime:RetrieveAndGenerate`, and returns `{ answer: string, citations: [...] }`. Grant the function `bedrock:RetrieveAndGenerate` and `bedrock:Retrieve` on both Knowledge Base ARNs.

7. **Define the `ChatApi` construct** in `src/constructs/chat-api.ts`. Provisions an `HttpApi` with a `POST /chat` route integrated to the Lambda function via `HttpLambdaIntegration`.

8. **Wire everything together in `ChatStack`** (`src/stacks/chat-stack.ts`). Create the S3 bucket (versioned, `DESTROY` removal policy). Instantiate two `OpenSearchVectorIndex` resources (one per chunking strategy) and two `BedrockKnowledgeBase` + `BedrockDataSource` pairs. Add `addDependency` from each Knowledge Base to its vector index. Instantiate `AskPdfQuestionFunction` and `ChatApi`. Emit `CfnOutput` values for the bucket name, both Knowledge Base IDs, and the API endpoint.

9. **Run `bun run synth`** to validate the CloudFormation template. Resolve any IAM policy or custom resource errors before deploying.

10. **Run `bun run deploy`** to provision all resources. After deployment, upload your PDF documents to the S3 bucket under the `docs/` prefix, then trigger a sync job on each Knowledge Base via the Bedrock console or `aws bedrock-agent start-ingestion-job`.

11. **Write the test script** (`cdk/scripts/compare-chunking.ts`). Define 5 questions. For each, call the deployed `POST /chat` endpoint twice — once with the hierarchical Knowledge Base ID and once with the fixed-size Knowledge Base ID. Write results side-by-side to `chunking-comparison.md`.

12. **Run `bun run cdk/scripts/compare-chunking.ts`**, review the output, and add a written analysis section to `chunking-comparison.md` noting which chunking strategy produced better results for each question type and why.

## Key Exam Concepts Practiced

- Bedrock Knowledge Bases ingestion pipeline and sync job lifecycle
- Fixed-size vs. hierarchical chunking tradeoffs and when each applies (Task 1.5.1)
- Amazon Titan Embeddings as the embedding model powering vector search (Task 1.5.2)
- OpenSearch Serverless as a managed vector store — collection types, index configuration, access policies (Tasks 1.4.1, 1.4.3)
- `RetrieveAndGenerate` vs. `Retrieve` API call patterns (Task 1.5.3)
- Source citations and grounding as hallucination-reduction techniques (Task 3.1.3)
- IAM least-privilege roles for Bedrock + Lambda integrations (Task 3.2.1)
- CloudWatch Logs for observing retrieval latency and chunk counts (Task 4.3.2)
