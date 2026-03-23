# Amazon Bedrock Knowledge Bases -- Comprehensive Study Guide (AIP-C01)

Amazon Bedrock Knowledge Bases is the **fully managed RAG (Retrieval Augmented Generation) service** on the exam. It appears heavily in Domain 1 (31% of the exam), particularly around vector stores, chunking strategies, retrieval mechanisms, and grounding to reduce hallucinations.

**Exam relevance:** Tasks 1.4 (vector stores), 1.5 (retrieval mechanisms), 3.1.3 (grounding to reduce hallucinations)

---

## 1. Service Overview

### What It Is

Amazon Bedrock Knowledge Bases is a fully managed capability that implements the **entire RAG workflow** -- ingestion, vectorization, storage, retrieval, and response generation -- without requiring custom integrations or data flow management.

### How RAG Works with Knowledge Bases

```
┌─────────────────── INGESTION TIME ───────────────────┐
│                                                       │
│  Data Source (S3, Confluence, etc.)                   │
│       │                                               │
│       ▼                                               │
│  Parse Documents (default / FM / BDA parser)          │
│       │                                               │
│       ▼                                               │
│  Chunk Documents (fixed / hierarchical / semantic)    │
│       │                                               │
│       ▼                                               │
│  Generate Embeddings (Titan V2, Cohere, etc.)         │
│       │                                               │
│       ▼                                               │
│  Store in Vector Database (OpenSearch, Aurora, etc.)   │
│                                                       │
└───────────────────────────────────────────────────────┘

┌─────────────────── QUERY TIME ───────────────────────┐
│                                                       │
│  User Query                                           │
│       │                                               │
│       ▼                                               │
│  Convert Query to Embedding (same embedding model)    │
│       │                                               │
│       ▼                                               │
│  Search Vector Store (semantic / hybrid)              │
│       │                                               │
│       ▼                                               │
│  (Optional) Rerank Results                            │
│       │                                               │
│       ▼                                               │
│  Augment Prompt with Retrieved Chunks                 │
│       │                                               │
│       ▼                                               │
│  Generate Response with FM (Claude, Nova, etc.)       │
│       │                                               │
│       ▼                                               │
│  Return Response with Citations                       │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### Two Core APIs

| API | Purpose | Returns |
|---|---|---|
| **Retrieve** | Fetches the most relevant source chunks from the vector store | Array of chunks with metadata and scores |
| **RetrieveAndGenerate** | Retrieve + InvokeModel in one call -- retrieves chunks, augments the prompt, generates a natural language response | Generated text with citations to source documents |

There is also **RetrieveAndGenerateStream** for streaming responses, and **GenerateQuery** for structured data stores (Natural Language to SQL).

---

## 2. Data Sources

### Supported Connectors

| Data Source | Metadata Fields | Inclusion/Exclusion Filters | Incremental Sync | Multimodal Support |
|---|---|---|---|---|
| **Amazon S3** | Yes (via `.metadata.json` sidecar files) | Inclusion prefixes | Yes | Yes (images, audio, video) |
| **Confluence** | Auto-detected (title, body, dates) | Yes | Yes | No |
| **Microsoft SharePoint** | Auto-detected | Yes | Yes | No |
| **Salesforce** | Auto-detected | Yes | Yes | No |
| **Web Crawler** | Auto-detected | URL filters, domain scope, depth/speed limits | Yes | No |
| **Custom** | User-defined per document | N/A (you control ingestion) | N/A (direct API ingestion) | Yes |
| **Amazon Redshift** | Structured data (NL-to-SQL) | N/A | N/A | No |

### Key Data Source Behaviors

- **Incremental sync**: On subsequent syncs, only new, modified, and deleted content is processed. This uses the data source's native change-tracking mechanism.
- **S3 metadata files**: Must be named `<filename>.metadata.json` and stored alongside the source document. This is how you add filterable metadata attributes for S3 sources.
- **Custom data sources**: Use the `KnowledgeBaseDocuments` API to directly ingest, update, or delete individual documents without a full sync. Supports streaming data ingestion.
- **You cannot change the parsing strategy or chunking strategy after connecting a data source.** You must create a new data source to use different settings.
- Each data source connector stores authentication credentials in **AWS Secrets Manager**.

### Sync Process

1. Bedrock fetches documents from the data source
2. Documents are parsed using the configured parser
3. Content is chunked according to the chunking strategy
4. Chunks are converted to embeddings using the configured embedding model
5. Embeddings are stored in the vector database with associated text and metadata

---

## 3. Chunking Strategies

Chunking determines how source documents are split into smaller pieces for embedding and retrieval. **You cannot change the chunking strategy after connecting a data source.**

### Strategy Comparison

| Strategy | How It Works | When to Use | Key Parameters |
|---|---|---|---|
| **Default** | Splits into ~300-token chunks, preserving sentence boundaries | Quick start; general-purpose | None (automatic) |
| **Fixed-size** | Splits into chunks of a configured token count with configurable overlap | Predictable chunk sizes; uniform documents | `maxTokens`, `overlapPercentage` |
| **Hierarchical** | Two-level structure: large parent chunks containing smaller child chunks | Need precise retrieval AND broad context; retrieves child chunks but returns parent chunks | `parentMaxTokens`, `childMaxTokens`, `overlapTokens` |
| **Semantic** | Uses NLP to group semantically similar sentences together | Documents with diverse topics; want chunks to be coherent units of meaning | `maxTokens`, `bufferSize`, `breakpointPercentileThreshold` |
| **None** | Treats each file as a single chunk | Pre-processed documents; small files | None |

### Detailed Parameter Reference

#### Fixed-Size Chunking
- **maxTokens**: Maximum number of tokens per chunk
- **overlapPercentage**: Percentage of overlap between consecutive chunks (ensures context continuity at chunk boundaries)

#### Hierarchical Chunking
- **Parent chunk size**: Maximum tokens for the larger (parent) chunks
- **Child chunk size**: Maximum tokens for the smaller (child) chunks derived from parents
- **overlapTokens**: Absolute number of overlapping tokens between consecutive chunks at each level
- At retrieval time, child chunks are found first, then **replaced with their parent chunks** to give the model broader context
- The returned number of results may be fewer than requested because multiple child chunks can share the same parent

#### Semantic Chunking
- **maxTokens**: Maximum tokens per chunk (sentence boundaries honored)
- **bufferSize**: Number of surrounding sentences to consider when computing embeddings for boundary detection. Buffer size of 1 = current + previous + next sentence (3 total)
- **breakpointPercentileThreshold**: Percentile of sentence dissimilarity at which to split. Higher threshold = fewer, larger chunks; lower threshold = more, smaller chunks
- **Additional cost**: Semantic chunking uses a foundation model to compute sentence embeddings for boundary detection

#### No Chunking
- Each document becomes a single chunk
- Documents must be pre-processed into individual files
- **Cannot view page numbers in citations** and cannot filter by `x-amz-bedrock-kb-document-page-number`

### Multimodal Content Chunking

For audio, video, and images, chunking works differently:

- **Nova Multimodal Embeddings**: Chunking happens at the embedding model level. Audio/video chunk duration is configurable (1-30 seconds, default 5 seconds). Text chunking strategies do NOT apply to multimodal files.
- **Bedrock Data Automation (BDA) parser**: Converts multimedia to text first (transcripts, scene summaries), then applies standard text chunking.

### Custom Transformation (Lambda)

You can use a **Lambda function** during ingestion to post-process chunks. This allows:
- Custom chunking logic
- Custom chunk-level metadata assignment
- Can be applied after one of Bedrock's built-in chunking options

Configuration requires a `CustomTransformationConfiguration` with the Lambda ARN and an S3 location for intermediate storage.

---

## 4. Embedding Models

### Supported Embedding Models for Knowledge Bases

| Model | Model ID | Dimensions | Vector Types | Max Tokens | Key Feature |
|---|---|---|---|---|---|
| **Amazon Titan Embeddings G1 - Text** | `amazon.titan-embed-text-v1` | 1536 (fixed) | Floating-point | 8192 | Legacy; widest availability |
| **Amazon Titan Text Embeddings V2** | `amazon.titan-embed-text-v2:0` | 256, 512, **1024** (configurable) | Floating-point, Binary | 8192 | Flexible dimensions; binary support; normalization; most regions |
| **Cohere Embed English** | `cohere.embed-english-v3` | 1024 | Floating-point, Binary | 512 | English-optimized |
| **Cohere Embed Multilingual** | `cohere.embed-multilingual-v3` | 1024 | Floating-point, Binary | 512 | 100+ languages |
| **Amazon Titan Multimodal Embeddings G1** | `amazon.titan-embed-image-v1` | 1024 | Floating-point | N/A | Text + image embeddings |
| **Amazon Nova Multimodal Embeddings** | N/A | 1024 | Floating-point | N/A | Text, image, audio, video in unified vector space |
| **Cohere Embed v3 (Multimodal)** | N/A | 1024 | Floating-point, Binary | N/A | Multimodal embeddings |

### Key Exam Points for Embedding Models

- **Titan V2 is the default/recommended choice** for most use cases: configurable dimensions, binary vector support, widest region availability
- **Binary vectors** use 1 bit per dimension instead of 32 bits (floating-point). They reduce storage cost significantly but are less precise. Only supported with **Amazon OpenSearch Serverless** and **Amazon OpenSearch Managed Clusters**.
- **Lower dimensions** (e.g., 256) = faster search, less storage, slightly less accuracy. Higher dimensions = more accurate, more storage, slower.
- **Cohere Embed Multilingual** is the choice when you need **multilingual support** (100+ languages)
- **You cannot change the embedding model after creating the knowledge base.** Changing models requires creating a new knowledge base.
- The same embedding model used during ingestion MUST be used during query time.

---

## 5. Vector Stores

### Supported Vector Databases

| Vector Store | Type | Quick Create | Hybrid Search | Binary Vectors | Key Strengths |
|---|---|---|---|---|---|
| **Amazon OpenSearch Serverless** | AWS-managed serverless | Yes (default) | Yes | Yes | Default choice; full-text search + vector search; auto-scaling; richest filter support (`startsWith`, `stringContains`, `listContains`) |
| **Amazon OpenSearch Service Managed Clusters** | AWS-managed (provisioned) | No | Yes | Yes (v2.16+) | Fine-grained configuration; performance tuning; existing OpenSearch investments |
| **Amazon Aurora PostgreSQL (pgvector)** | AWS-managed relational | Yes (quick create) | Yes | No | SQL + vector capabilities; familiar PostgreSQL; good for existing Aurora users |
| **Amazon S3 Vectors** | AWS-managed object storage | Yes | No | No | Lowest cost; subsecond query performance; ideal for cost-sensitive large KBs |
| **Amazon Neptune Analytics** | AWS-managed graph | Yes | No | No | GraphRAG; entity relationships; multi-hop reasoning; cross-document correlation |
| **Pinecone** | Third-party SaaS | No | No | No | Pure vector search performance; managed SaaS |
| **Redis Enterprise Cloud** | Third-party SaaS | No | No | No | Ultra-low latency; real-time use cases |
| **MongoDB Atlas** | Third-party SaaS | No | Yes | No | Document database + vector search; existing MongoDB investments |

### Vector Store Selection Decision Framework

```
Need lowest cost for large KBs?
  → Amazon S3 Vectors

Need hybrid search (keyword + semantic)?
  → OpenSearch Serverless (default) or Aurora PostgreSQL or MongoDB Atlas

Need binary vector support?
  → OpenSearch Serverless or OpenSearch Managed Clusters

Need graph-based relationships / cross-document reasoning?
  → Neptune Analytics (GraphRAG)

Need ultra-low latency?
  → Redis Enterprise Cloud

Already using PostgreSQL?
  → Aurora PostgreSQL with pgvector

Already using MongoDB?
  → MongoDB Atlas

Default / general purpose?
  → OpenSearch Serverless (auto-created by Bedrock)
```

### Vector Store Configuration

When setting up a vector store (not quick-create), you must create:
1. A **vector field** for storing embeddings (dimensions must match your embedding model)
2. A **text field** for storing raw text chunks (e.g., `AMAZON_BEDROCK_TEXT_CHUNK`)
3. A **metadata field** for Bedrock-managed metadata (e.g., `AMAZON_BEDROCK_METADATA`)

For OpenSearch Serverless:
- Use the **faiss** engine (not nmslib) -- nmslib is NOT supported
- Use **Euclidean** distance metric for floating-point embeddings
- Use **Hamming** distance metric for binary embeddings

---

## 6. Search and Retrieval

### Search Types

| Search Type | How It Works | When to Use |
|---|---|---|
| **Semantic** | Converts query to embedding, searches vector index for nearest neighbors | Default behavior; works with all vector stores |
| **Hybrid** | Combines vector embedding search AND raw text keyword search | Better recall; handles exact-match terms (names, IDs, codes) that semantic search may miss |
| **Default** | Bedrock chooses the best strategy for your vector store configuration | Let Bedrock decide |

**Hybrid search is only supported with**: Amazon OpenSearch Serverless, Amazon Aurora PostgreSQL (RDS), and MongoDB Atlas (requires a filterable text field).

### Metadata Filtering

Metadata filtering narrows search results by applying conditions on document metadata attributes BEFORE vector similarity search.

#### Filter Operators

| Operator | API Name | Supported Types |
|---|---|---|
| Equals | `equals` | string, number, boolean |
| Not Equals | `notEquals` | string, number, boolean |
| Greater Than | `greaterThan` | number |
| Greater Than or Equals | `greaterThanOrEquals` | number |
| Less Than | `lessThan` | number |
| Less Than or Equals | `lessThanOrEquals` | number |
| In | `in` | string list |
| Not In | `notIn` | string list |
| Starts With | `startsWith` | string (OpenSearch Serverless only) |
| String Contains | `stringContains` | string (OpenSearch Serverless only) |
| List Contains | `listContains` | string (OpenSearch Serverless only) |

#### Logical Operators

- **`andAll`**: All filters must match (up to 5 per group)
- **`orAll`**: At least one filter must match (up to 5 per group)
- You can nest up to 5 filter groups within a top-level logical operator (one level of nesting)

#### Implicit Metadata Filtering

A feature that **automatically generates and applies filters** based on the user query and a metadata schema. The system analyzes the query, identifies relevant metadata constraints, and applies them without the developer writing explicit filter logic. Currently only supported with **Anthropic Claude 3.5 Sonnet**.

### Reranking

Reranking uses a foundation model to **re-score and reorder** initial vector search results for better relevance.

- Uses models like **Cohere Rerank 3.5** or Amazon Bedrock foundation models
- Applied AFTER the initial vector search
- Can specify **numberOfRerankedResults** (1-100) to limit how many results the reranker processes
- Can configure **metadata fields** to include or exclude during reranking (`selectionMode`: ALL or SELECTIVE)
- Reranking results **override** the default ranking from the vector store
- Only applicable to **textual data**
- Reduces cost and latency by returning fewer but more relevant results

### Query Decomposition

A technique that breaks **complex, multi-part queries** into smaller, more manageable sub-queries. Each sub-query is processed independently against the knowledge base, and the results are combined to generate a comprehensive response.

Example: "What is the difference between Lambda and Fargate for running containers, and which is cheaper?" gets broken into separate sub-queries about Lambda capabilities, Fargate capabilities, and their pricing.

---

## 7. Grounding and Hallucination Reduction

### How Knowledge Bases Provide Grounding

RAG is fundamentally a **grounding mechanism**. Instead of relying solely on the model's training data (which may be outdated or incorrect), Knowledge Bases ground the model's response in your actual data:

1. **Contextual grounding**: Retrieved chunks provide factual context that the model uses to generate responses
2. **Citation tracking**: Every response includes citations linking back to the specific source chunks used
3. **Source attribution**: Users can verify claims by tracing back to original documents
4. **Reduced hallucination**: The model is constrained to generate responses based on retrieved content rather than fabricating information

### Citations in Responses

The `RetrieveAndGenerate` response includes a `citations` array. Each citation contains:
- **generatedResponsePart**: The specific segment of the generated text that is based on a source
- **retrievedReferences**: The actual source chunks with their content, location (S3 URI, page number), and metadata

### Combining with Guardrails

You can apply **Bedrock Guardrails** to knowledge base queries for additional safety:
- **Contextual grounding checks**: Detect and filter hallucinations by checking if the response is grounded in the retrieved source material AND relevant to the user query
- **Grounding threshold**: Configurable threshold for how closely the response must match source material
- **Relevance threshold**: Configurable threshold for how relevant the response must be to the query
- Content filters, denied topics, PII detection all apply

---

## 8. Query Decomposition

### How It Works

When a user asks a complex question that spans multiple topics or requires information from different parts of the knowledge base:

1. The orchestration model analyzes the query
2. It breaks the query into focused sub-queries
3. Each sub-query is independently searched against the knowledge base
4. Retrieved results from all sub-queries are combined
5. The generation model synthesizes a comprehensive answer from all retrieved context

### Configuration

- Enabled through the **orchestrationConfiguration** in `RetrieveAndGenerate` requests
- You can customize the **orchestration prompt** that controls how queries are decomposed
- Prompt placeholders and XML tags are used to structure the decomposition instructions

---

## 9. Parsing Options

### Available Parsers

| Parser | What It Does | When to Use |
|---|---|---|
| **Default parser** | Extracts text from supported file formats (PDF, DOCX, TXT, HTML, CSV, etc.) | Standard text documents |
| **Foundation model parser** | Uses Claude or Nova vision models to parse complex documents including tables, charts, images | Documents with rich visual content (PDFs with tables, diagrams) |
| **Bedrock Data Automation (BDA) parser** | Converts multimodal content (audio, video) to text representations | Audio/video content; preview feature |

- Foundation model parsing incurs **additional model inference charges**
- You can provide a **custom parsing prompt** when using a foundation model parser
- BDA parser is currently available in **US West (Oregon)** only (preview)

---

## 10. TypeScript AWS SDK v3 Usage

### Creating a Knowledge Base

```typescript
import {
  BedrockAgentClient,
  CreateKnowledgeBaseCommand,
  CreateDataSourceCommand,
  StartIngestionJobCommand,
} from "@aws-sdk/client-bedrock-agent";

const client = new BedrockAgentClient({ region: "us-east-1" });

// Step 1: Create the Knowledge Base
const createKbResponse = await client.send(
  new CreateKnowledgeBaseCommand({
    name: "my-knowledge-base",
    roleArn: "arn:aws:iam::123456789012:role/BedrockKBRole",
    knowledgeBaseConfiguration: {
      type: "VECTOR",
      vectorKnowledgeBaseConfiguration: {
        embeddingModelArn:
          "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
        embeddingModelConfiguration: {
          bedrockEmbeddingModelConfiguration: {
            dimensions: 1024, // 256, 512, or 1024 for Titan V2
          },
        },
      },
    },
    storageConfiguration: {
      type: "OPENSEARCH_SERVERLESS",
      opensearchServerlessConfiguration: {
        collectionArn: "arn:aws:aoss:us-east-1:123456789012:collection/abc123",
        vectorIndexName: "bedrock-kb-index",
        fieldMapping: {
          vectorField: "bedrock-knowledge-base-default-vector",
          textField: "AMAZON_BEDROCK_TEXT_CHUNK",
          metadataField: "AMAZON_BEDROCK_METADATA",
        },
      },
    },
  })
);

const knowledgeBaseId = createKbResponse.knowledgeBase!.knowledgeBaseId!;

// Step 2: Create a Data Source (S3)
const createDsResponse = await client.send(
  new CreateDataSourceCommand({
    knowledgeBaseId,
    name: "my-s3-data-source",
    dataSourceConfiguration: {
      type: "S3",
      s3Configuration: {
        bucketArn: "arn:aws:s3:::my-kb-documents-bucket",
      },
    },
    vectorIngestionConfiguration: {
      chunkingConfiguration: {
        chunkingStrategy: "HIERARCHICAL",
        hierarchicalChunkingConfiguration: {
          levelConfigurations: [
            { maxTokens: 1500 }, // parent chunk size
            { maxTokens: 300 },  // child chunk size
          ],
          overlapTokens: 60,
        },
      },
    },
  })
);

const dataSourceId = createDsResponse.dataSource!.dataSourceId!;

// Step 3: Start Ingestion (Sync)
await client.send(
  new StartIngestionJobCommand({
    knowledgeBaseId,
    dataSourceId,
  })
);
```

### Querying with RetrieveAndGenerate

```typescript
import {
  BedrockAgentRuntimeClient,
  RetrieveAndGenerateCommand,
} from "@aws-sdk/client-bedrock-agent-runtime";

const runtimeClient = new BedrockAgentRuntimeClient({ region: "us-east-1" });

const response = await runtimeClient.send(
  new RetrieveAndGenerateCommand({
    input: { text: "What are the key features of our product?" },
    retrieveAndGenerateConfiguration: {
      type: "KNOWLEDGE_BASE",
      knowledgeBaseConfiguration: {
        knowledgeBaseId: "ABCDEF1234",
        modelArn:
          "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        retrievalConfiguration: {
          vectorSearchConfiguration: {
            numberOfResults: 10,
            overrideSearchType: "HYBRID",
          },
        },
        generationConfiguration: {
          inferenceConfig: {
            textInferenceConfig: {
              temperature: 0.0,
              maxTokens: 2048,
            },
          },
        },
      },
    },
  })
);

// The generated response
console.log(response.output?.text);

// Citations linking response segments to source documents
for (const citation of response.citations ?? []) {
  console.log("Generated text segment:", citation.generatedResponsePart?.textResponsePart?.text);
  for (const ref of citation.retrievedReferences ?? []) {
    console.log("  Source:", ref.location?.s3Location?.uri);
    console.log("  Content:", ref.content?.text);
  }
}
```

### Querying with Retrieve (Chunks Only)

```typescript
import {
  BedrockAgentRuntimeClient,
  RetrieveCommand,
} from "@aws-sdk/client-bedrock-agent-runtime";

const runtimeClient = new BedrockAgentRuntimeClient({ region: "us-east-1" });

const response = await runtimeClient.send(
  new RetrieveCommand({
    knowledgeBaseId: "ABCDEF1234",
    retrievalQuery: { text: "deployment best practices" },
    retrievalConfiguration: {
      vectorSearchConfiguration: {
        numberOfResults: 20,
        overrideSearchType: "HYBRID",
      },
    },
  })
);

for (const result of response.retrievalResults ?? []) {
  console.log("Score:", result.score);
  console.log("Content:", result.content?.text);
  console.log("Source:", result.location?.s3Location?.uri);
  console.log("Metadata:", result.metadata);
}
```

### Metadata Filtering

```typescript
const response = await runtimeClient.send(
  new RetrieveCommand({
    knowledgeBaseId: "ABCDEF1234",
    retrievalQuery: { text: "security policies" },
    retrievalConfiguration: {
      vectorSearchConfiguration: {
        numberOfResults: 10,
        filter: {
          andAll: [
            {
              equals: { key: "department", value: "engineering" },
            },
            {
              greaterThan: { key: "year", value: 2023 },
            },
          ],
        },
      },
    },
  })
);
```

### Reranking Configuration

```typescript
const response = await runtimeClient.send(
  new RetrieveCommand({
    knowledgeBaseId: "ABCDEF1234",
    retrievalQuery: { text: "How do I configure auto-scaling?" },
    retrievalConfiguration: {
      vectorSearchConfiguration: {
        numberOfResults: 50, // retrieve more initial results
        rerankingConfiguration: {
          type: "BEDROCK_RERANKING_MODEL",
          bedrockRerankingConfiguration: {
            numberOfRerankedResults: 10, // return top 10 after reranking
            modelConfiguration: {
              modelArn:
                "arn:aws:bedrock:us-east-1::foundation-model/cohere.rerank-v3-5:0",
            },
          },
        },
      },
    },
  })
);
```

---

## 11. Integration Patterns

### With Bedrock Agents

The most common integration pattern. Associate a knowledge base with an agent so the agent can automatically query it when relevant:

1. Create the knowledge base independently
2. Associate it with the agent via `AssociateAgentKnowledgeBase`
3. Provide the agent with **instructions** on when/how to use the knowledge base
4. The agent autonomously decides when to invoke the knowledge base based on user queries
5. Modify query configurations at runtime using `sessionState` in `InvokeAgent`

### With Custom Applications

Use the `Retrieve` API for maximum control:
1. Call `Retrieve` to get relevant chunks
2. Build your own prompt template incorporating the chunks
3. Call `InvokeModel` or `Converse` with the augmented prompt
4. Handle citations and post-processing in your application

This pattern gives you control over prompt engineering, chunk selection, and response formatting.

### With Lambda Functions

Two integration points:

**Ingestion-time Lambda** (Custom Transformation):
- Post-process chunks during data ingestion
- Add custom metadata to chunks
- Implement custom chunking logic
- Invoked by Bedrock during the sync process

**Query-time Lambda** (Application Layer):
- Lambda function calls `Retrieve` or `RetrieveAndGenerate` API
- Typically behind API Gateway or invoked by an agent
- Handles business logic, authentication, session management

### With Amazon Kendra GenAI Index

You can use an **Amazon Kendra GenAI index** as the retrieval backend for a Bedrock Knowledge Base. This lets you:
- Reuse existing Kendra-indexed content across multiple applications
- Leverage Kendra's high-accuracy retrieval with Bedrock's generation capabilities
- Avoid re-ingesting and re-indexing data

---

## 12. Monitoring and Logging

### CloudWatch Logs

Knowledge bases support **APPLICATION_LOGS** for data ingestion monitoring:
- Track file processing status during ingestion jobs
- Log destinations: CloudWatch Logs, Amazon S3, or Amazon Data Firehose
- Useful queries include: files ignored during ingestion, vector embedding exceptions, deletion exceptions

Enable via console or CloudWatch API (`PutDeliverySource` / `PutDeliveryDestination` / `CreateDelivery`).

### Key Debugging Queries (CloudWatch Logs Insights)

```
# All documents ignored during ingestion
fields @timestamp, @message
| filter @message like /IGNORED/

# All embedding/indexing exceptions
fields @timestamp, @message
| filter @message like /EXCEPTION/

# All exceptions during a specific ingestion job
fields @timestamp, @message
| filter ingestionJobId = "your-job-id" and @message like /EXCEPTION/
```

### CloudWatch Metrics

Bedrock publishes runtime metrics under the `AWS/Bedrock` namespace:
- **Invocations**: Count of API calls
- **InvocationLatency**: End-to-end latency
- **InvocationClientErrors** / **InvocationServerErrors**: Error rates
- **InputTokenCount** / **OutputTokenCount**: Token usage
- **InvocationThrottles**: Throttle events

Agent-specific metrics (when KB is used via agents):
- Agent invocation counts, latency, TTFT, token counts, error rates

---

## 13. Cost Considerations

### Cost Components

| Component | Pricing Model | Notes |
|---|---|---|
| **Embedding generation** | Per-token (on-demand) or per-hour (provisioned throughput) | Charged during ingestion AND re-ingestion on sync |
| **Vector store storage** | Varies by store (OpenSearch Serverless OCUs, Aurora ACUs, S3 storage, Pinecone pods, etc.) | OpenSearch Serverless has a minimum of 2 OCUs; S3 Vectors is cheapest |
| **Retrieval (query-time)** | Embedding model cost (to embed query) + vector store query cost | Each query embeds the query text |
| **Response generation** | Per-token for the generation FM (input + output tokens) | Includes retrieved chunks in the input context |
| **Reranking** | Per-query ($2.00 per 1,000 queries for Cohere Rerank 3.5) | Query = up to 100 document chunks |
| **Semantic chunking** | Per-token (uses an FM for boundary detection) | Additional cost compared to fixed-size chunking |
| **FM-based parsing** | Per-token for the parser model | Only if you use a foundation model parser |
| **Data source connectors** | No additional charge for the connector itself | But you pay for the compute/storage of the source |

### Cost Optimization Strategies

- **Use Titan V2 with lower dimensions** (256 or 512) to reduce vector storage costs with minimal accuracy loss
- **Use binary vectors** (with OpenSearch Serverless) for significant storage reduction
- **Use Amazon S3 Vectors** as the vector store for the lowest storage cost
- **Use fixed-size chunking** instead of semantic chunking to avoid the FM cost during ingestion
- **Manage sync frequency** carefully -- every sync re-embeds changed documents
- **Use `Retrieve` instead of `RetrieveAndGenerate`** when you want to control the generation model and prompt (potentially use a cheaper model)
- **Use reranking** to retrieve fewer but more relevant results, reducing the tokens sent to the generation model

---

## 14. Exam Gotchas and Common Traps

### Chunking Strategy Traps

1. **"Cannot change chunking strategy after connecting a data source"** -- if you need to change, create a new data source
2. **Semantic chunking costs extra** -- it uses a foundation model for boundary detection during ingestion
3. **No chunking = no page number citations** -- you lose `x-amz-bedrock-kb-document-page-number` metadata
4. **Hierarchical chunking returns fewer results than requested** -- because child chunks are replaced by parents, and multiple children may share a parent
5. **Hierarchical chunking is not recommended with S3 vector bucket** -- metadata size limitations with high token counts

### Vector Store Traps

1. **OpenSearch Serverless must use `faiss` engine** -- `nmslib` is NOT supported for filtering
2. **Binary vectors only work with OpenSearch** (Serverless or Managed Clusters) -- not Aurora, not Pinecone, not others
3. **Hybrid search requires specific vector stores** -- only OpenSearch Serverless, Aurora PostgreSQL, and MongoDB Atlas (must have filterable text field)
4. **`startsWith` and `stringContains` filters are OpenSearch Serverless only** -- other vector stores do not support these

### Embedding Model Traps

1. **Cannot change the embedding model after creating a knowledge base** -- must create a new KB
2. **Same embedding model at ingestion and query time** -- mismatched models produce garbage results
3. **Titan V1 is fixed at 1536 dimensions** -- cannot reduce; Titan V2 is configurable (256, 512, 1024)
4. **Cohere Embed has 512 max tokens** -- shorter context window than Titan (8192)

### Retrieval and Configuration Traps

1. **Implicit metadata filtering only works with Claude 3.5 Sonnet** -- not other models
2. **Reranking only applies to textual data** -- not images, audio, or video
3. **Maximum 100 results per query** (numberOfResults min 1, max 100)
4. **RetrieveAndGenerate has a session concept** -- sessionId is auto-generated and required for multi-turn context
5. **Filter nesting is limited to one level** -- you can combine up to 5 filter groups, and each group can have up to 5 filters

### Data Source Traps

1. **Cannot change parsing strategy after connecting a data source**
2. **Cannot add S3 multimodal storage location after creating a knowledge base** -- must create a new KB
3. **Confluence, SharePoint, Salesforce connectors do not support multimodal** -- only S3 and custom sources do
4. **Web crawler is/was in preview** -- exam may ask about limitations

---

## 15. When to Use / When NOT to Use

### Use Knowledge Bases When

- You need to **ground FM responses in your private data** (the core RAG use case)
- You want a **fully managed** RAG pipeline without building custom ingestion/retrieval
- You need **citations and source attribution** in generated responses
- You have **unstructured documents** (PDFs, docs, web pages) that need to be searchable
- You need **incremental sync** to keep the knowledge base current
- You're building with **Bedrock Agents** and need to give them access to domain knowledge
- You need **structured data querying** via Natural Language to SQL

### Do NOT Use Knowledge Bases When

- Your data is **rapidly changing in real-time** and you need sub-second freshness -- use custom pipeline with streaming
- You need **full control over the embedding pipeline** (custom models, custom preprocessing) -- build your own RAG with SageMaker + OpenSearch
- Your data is **already in a well-indexed search engine** (e.g., Kendra) -- use Kendra GenAI Index integration or Kendra directly
- You need **cross-account or cross-region vector store access** -- limited to same-account configurations
- You need to use an **embedding model not supported by Knowledge Bases** -- build custom RAG
- Your documents are **extremely large** and you need fine-grained control over how they're split -- consider custom chunking with Lambda or pre-processing

### Knowledge Bases vs. Other RAG Approaches

| Approach | When to Choose |
|---|---|
| **Bedrock Knowledge Bases** | Fully managed RAG; fastest to deploy; built-in sync, chunking, retrieval, generation, citations |
| **Amazon Kendra** | Enterprise search with fine-grained access control; 40+ native connectors; when search accuracy is the primary goal |
| **Kendra GenAI Index + KB** | Combine Kendra's retrieval accuracy with Bedrock's generation capabilities |
| **Custom RAG (SageMaker + OpenSearch)** | Full control over every pipeline stage; custom embedding models; custom retrieval logic |
| **Long-context window models** | Small datasets that fit in context; no need for persistent vector storage |
| **Fine-tuning** | When the knowledge needs to be baked into model weights rather than retrieved at query time |

---

## 16. Quick Reference Card

### API Clients (SDK v3)

| Client | Package | Purpose |
|---|---|---|
| `BedrockAgentClient` | `@aws-sdk/client-bedrock-agent` | Build-time: create/update/delete KB, data sources, start sync |
| `BedrockAgentRuntimeClient` | `@aws-sdk/client-bedrock-agent-runtime` | Runtime: Retrieve, RetrieveAndGenerate, RetrieveAndGenerateStream |

### Critical Numbers

| Limit | Value |
|---|---|
| Max results per query | 100 |
| Default results per query | 5 |
| Max filter groups | 5 |
| Max filters per group | 5 |
| Max filter nesting depth | 1 level |
| Default chunk size (default chunking) | ~300 tokens |
| Titan V2 dimension options | 256, 512, 1024 |
| Titan V1 fixed dimensions | 1536 |
| Cohere Embed dimensions | 1024 |
| Cohere Embed max input tokens | 512 |
| Titan Embed max input tokens | 8192 |
| Max reranking results | 100 |

### IAM Permissions for Knowledge Base Service Role

The Bedrock KB service role needs:
- `bedrock:InvokeModel` on the embedding model ARN
- `s3:GetObject` and `s3:ListBucket` on the data source bucket
- Vector store access (e.g., `aoss:APIAccessAll` for OpenSearch Serverless)
- `secretsmanager:GetSecretValue` for third-party data source credentials
