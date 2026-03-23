# Database Services -- Comprehensive Study Guide (AIP-C01)

Database services appear across multiple exam domains. Aurora (pgvector) and DynamoDB are the most heavily tested -- Aurora for vector search in RAG architectures, DynamoDB for conversation history and metadata storage. ElastiCache appears in caching/optimization questions, Neptune in knowledge graph scenarios, and DocumentDB as a vector-capable alternative.

---

## Exam Relevance Map

| Service | Exam Task | Context |
|---|---|---|
| **Aurora (pgvector)** | 1.4.1, 1.5.3 | Vector store for RAG, Bedrock Knowledge Bases integration |
| **DynamoDB** | 1.4.1, 1.6.2 | Conversation history, metadata for GenAI apps |
| **DynamoDB Streams** | 1.4.1 | Change detection, event-driven GenAI pipelines |
| **ElastiCache** | 4.1.4 | Semantic caching, response caching for AI |
| **Neptune** | 1.4.1 | Knowledge graphs, GraphRAG |
| **DocumentDB** | 1.4.1 | MongoDB-compatible vector search |
| **RDS (PostgreSQL)** | 1.4.1 | pgvector (non-Aurora alternative) |

---

## 1. Amazon Aurora (pgvector Focus)

### 1.1 Overview

Amazon Aurora is a **fully managed relational database engine** compatible with MySQL and PostgreSQL. For the exam, focus on **Aurora PostgreSQL-Compatible Edition** because it supports the **pgvector** extension for vector similarity search.

Key Aurora characteristics:
- Up to **5x throughput** of standard PostgreSQL
- **Storage auto-scales** from 10 GB to 128 TB
- Up to **15 read replicas** with sub-10ms replica lag
- **Multi-AZ** with automatic failover (under 30 seconds)
- **Aurora Serverless v2** scales compute capacity automatically
- **Aurora Optimized Reads** improves query performance for vector workloads by using local NVMe storage

### 1.2 pgvector Extension for Vector Search

pgvector is an **open-source PostgreSQL extension** that adds vector data types and similarity search operations. It allows you to store embeddings directly alongside your relational data.

**Core capabilities:**
- Store vectors as a native `vector` data type
- Exact and approximate nearest neighbor (ANN) search
- Distance metrics: **L2 (Euclidean)**, **cosine distance**, **inner product**
- Maximum dimensions: **16,000** (as of pgvector 0.8.0)
- Filter with standard SQL `WHERE` clauses during vector search

**Enabling pgvector:**
```sql
-- Enable the extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a table with a vector column (1536 dims for Titan Embeddings V2)
CREATE TABLE documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  metadata JSONB,
  embedding vector(1536)
);

-- Insert a vector
INSERT INTO documents (content, metadata, embedding)
VALUES (
  'Aurora supports vector search via pgvector',
  '{"source": "docs", "topic": "databases"}',
  '[0.1, 0.2, 0.3, ...]'::vector
);
```

**Similarity search queries:**
```sql
-- Cosine similarity search (most common for text embeddings)
SELECT id, content, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM documents
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;

-- L2 (Euclidean) distance
SELECT * FROM documents
ORDER BY embedding <-> '[0.1, 0.2, ...]'::vector
LIMIT 10;

-- Inner product (use <#> operator)
SELECT * FROM documents
ORDER BY embedding <#> '[0.1, 0.2, ...]'::vector
LIMIT 10;

-- Filtered vector search (pgvector 0.8.0 iterative scans prevent overfiltering)
SELECT * FROM documents
WHERE metadata->>'topic' = 'databases'
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

**Distance operator reference:**

| Operator | Metric | Best For |
|---|---|---|
| `<->` | L2 (Euclidean) distance | Absolute distance comparisons |
| `<=>` | Cosine distance | Text embeddings (most common) |
| `<#>` | Negative inner product | When vectors are normalized |

### 1.3 Vector Indexing: IVFFlat vs HNSW

Without an index, pgvector performs **exact nearest neighbor** search (scans every row). For production workloads, you need an approximate nearest neighbor (ANN) index.

**IVFFlat (Inverted File with Flat Compression):**
```sql
-- Create an IVFFlat index
-- lists = number of clusters (start with rows / 1000, min 100)
CREATE INDEX ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Tune probes at query time (higher = better recall, slower)
SET ivfflat.probes = 10;
```

- Divides vectors into **clusters (lists)** using k-means
- At query time, searches only the **nearest clusters** (controlled by `probes`)
- **Faster to build** than HNSW
- **Must have data loaded before creating** the index (k-means needs data to cluster)
- Lower recall than HNSW at the same speed
- Best when: dataset is relatively static, cost of index rebuild is acceptable

**HNSW (Hierarchical Navigable Small World):**
```sql
-- Create an HNSW index
-- m = connections per layer (default 16), ef_construction = build quality (default 64)
CREATE INDEX ON documents
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Tune ef_search at query time (higher = better recall, slower)
SET hnsw.ef_search = 40;
```

- Builds a **multi-layered graph** structure
- **Better recall** than IVFFlat at the same query speed
- **Can be built on an empty table** (incrementally adds vectors)
- **More expensive to build** and uses more memory
- pgvector 0.7.0+: **parallel HNSW index builds** (up to 30x faster)
- Best when: you need highest recall, data changes frequently

**Index comparison (exam-critical):**

| Property | IVFFlat | HNSW |
|---|---|---|
| Build speed | Faster | Slower (but parallel since 0.7.0) |
| Query recall | Good | Better |
| Memory usage | Lower | Higher |
| Empty table support | No (needs data first) | Yes |
| Incremental updates | Requires rebuild | Supports incremental |
| Tuning knobs | `lists`, `probes` | `m`, `ef_construction`, `ef_search` |

### 1.4 pgvector 0.8.0 Improvements (Latest)

- **Iterative index scans**: Solves the overfiltering problem when combining vector search with SQL `WHERE` clauses. Continues scanning instead of stopping prematurely when filters are strict.
- **Three scan modes**: `off`, `strict_order` (maintains exact ordering), `relaxed_order` (best performance, recommended for production)
- **Improved query planner**: Better decisions about when to use indexes vs sequential scan
- **HNSW performance**: Faster index builds and search

### 1.5 Quantization (Cost/Performance Optimization)

pgvector 0.7.0+ supports quantization to reduce memory and storage:

| Technique | Storage Savings | Recall Impact | Use Case |
|---|---|---|---|
| **Scalar (halfvec)** | 50% | Minimal | Recommended starting point |
| **Binary** | ~97% | Significant (use re-ranking) | Very large datasets, cost-sensitive |

```sql
-- Scalar quantization: cast to halfvec
CREATE INDEX ON documents
USING hnsw ((embedding::halfvec(1536)) halfvec_cosine_ops);

-- Query with scalar quantization
SELECT * FROM documents
ORDER BY embedding::halfvec(1536) <=> '[0.1, ...]'::halfvec(1536)
LIMIT 10;
```

### 1.6 When to Use Aurora vs OpenSearch for Vectors

| Factor | Aurora (pgvector) | OpenSearch Service |
|---|---|---|
| Best for | Existing PostgreSQL workloads, combined SQL + vector queries | Dedicated vector search at scale, full-text + vector hybrid search |
| Scale | Millions of vectors | Billions of vectors (GPU-accelerated indexing) |
| Query type | SQL + vector in same query | k-NN, hybrid (BM25 + vector), aggregations |
| Managed RAG | Bedrock Knowledge Bases supported | Bedrock Knowledge Bases supported (Serverless) |
| Latency | Single-digit ms for moderate scale | Single-digit ms, optimized for large scale |
| Additional features | Full SQL, joins, transactions, ACID | Full-text search, dashboards, log analytics |
| Cost model | Instance-based or Serverless v2 | Instance-based or Serverless (OCU-based) |

**Exam tip**: Choose Aurora when the application already uses PostgreSQL and needs both relational queries AND vector search. Choose OpenSearch when vector search is the primary workload or when you need billions of vectors with GPU acceleration.

### 1.7 Integration with Bedrock Knowledge Bases

Aurora PostgreSQL with pgvector is a **supported vector store** for Amazon Bedrock Knowledge Bases. The managed service handles:
- Chunking documents from S3 data sources
- Generating embeddings using a Bedrock embedding model
- Storing embeddings and metadata in Aurora with pgvector
- Retrieval via the Bedrock Retrieve API
- Metadata filtering for multi-tenant isolation

**Required Aurora schema for Bedrock Knowledge Bases:**
```sql
-- Bedrock Knowledge Bases expects this schema structure
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE bedrock_integration.bedrock_kb (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  embedding vector(1536),  -- dimension must match your embedding model
  chunks TEXT,
  metadata JSON
);

CREATE INDEX ON bedrock_integration.bedrock_kb
USING hnsw (embedding vector_cosine_ops);
```

### 1.8 Performance Tuning for Vector Workloads

- **Aurora Optimized Reads**: Uses local NVMe-based storage to cache data, improving vector query performance for datasets larger than memory
- **Read replicas**: Offload vector search queries to up to 15 read replicas
- **Instance sizing**: Vector workloads are memory-intensive; choose memory-optimized instances (r6g, r7g)
- **Shared memory**: Increase `shared_buffers` and `effective_cache_size` for vector index caching
- **Maintenance**: Run `VACUUM` and `ANALYZE` after bulk vector loads
- **Connection pooling**: Use RDS Proxy or PgBouncer for high-concurrency GenAI workloads

### 1.9 TypeScript SDK v3 Example

```typescript
import { RDSDataClient, ExecuteStatementCommand } from "@aws-sdk/client-rds-data";

const client = new RDSDataClient({ region: "us-east-1" });

// Vector similarity search via Aurora Data API (Serverless v2)
async function searchSimilarDocuments(
  queryEmbedding: number[],
  limit: number = 10
) {
  const embeddingStr = `[${queryEmbedding.join(",")}]`;

  const command = new ExecuteStatementCommand({
    resourceArn: "arn:aws:rds:us-east-1:123456789012:cluster:my-aurora-cluster",
    secretArn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret",
    database: "mydb",
    sql: `
      SELECT id, content, metadata,
             1 - (embedding <=> :embedding::vector) AS similarity
      FROM documents
      ORDER BY embedding <=> :embedding::vector
      LIMIT :limit
    `,
    parameters: [
      { name: "embedding", value: { stringValue: embeddingStr } },
      { name: "limit", value: { longValue: limit } },
    ],
  });

  const response = await client.send(command);
  return response.records;
}
```

### 1.10 Key Metrics

| Metric | Source | What It Tells You |
|---|---|---|
| `CPUUtilization` | CloudWatch | Sustained >70% means you need to scale up or add read replicas |
| `FreeableMemory` | CloudWatch | Low values impact vector index caching |
| `DatabaseConnections` | CloudWatch | High connection count needs RDS Proxy |
| `ReadIOPS` / `WriteIOPS` | CloudWatch | Measures storage I/O pressure |
| `AuroraReplicaLag` | CloudWatch | Monitors read replica freshness |
| `ServerlessDatabaseCapacity` | CloudWatch | ACU usage for Serverless v2 |

---

## 2. Amazon DynamoDB

### 2.1 Overview and Key Concepts

Amazon DynamoDB is a **fully managed, serverless NoSQL database** that delivers single-digit millisecond performance at any scale. It is the default choice for storing conversation history and metadata in GenAI applications.

**Core concepts (exam-critical):**

| Concept | Description |
|---|---|
| **Table** | Collection of items. No fixed schema beyond the primary key. |
| **Item** | A single record, max **400 KB** |
| **Partition Key (PK)** | Required. Determines which partition stores the item. Must have **high cardinality**. |
| **Sort Key (SK)** | Optional. Enables range queries within a partition. Combined with PK to form the primary key. |
| **Global Secondary Index (GSI)** | Alternate PK + optional SK. Can query across all partitions. Eventually consistent. Separate throughput. Max **20 per table**. |
| **Local Secondary Index (LSI)** | Same PK, different SK. Must be created at table creation time. Shares throughput with base table. Max **5 per table**. Strongly consistent reads supported. |

**Single-table design**: DynamoDB best practice is to store multiple entity types in a single table, using composite sort keys to differentiate them. This is the pattern used for chatbot data models.

### 2.2 Conversation History Storage Patterns

This is the most exam-relevant DynamoDB pattern for GenAI. The recommended data model uses **vertical partitioning** to store conversation metadata and messages as separate items under the same partition key.

**Schema design:**

```
Partition Key (PK): UserID
Sort Key (SK):      CONV#<ConversationID>          -- metadata item
                    CHAT#<ConversationID>#MSG#<ULID> -- message item
```

**Metadata item:**
```json
{
  "PK": "user-123",
  "SK": "CONV#conv-abc",
  "created_at": 1700000000,
  "expires_at": 1707776000,
  "title": "Help with my order",
  "model_id": "anthropic.claude-sonnet-4-20250514"
}
```

**Message item:**
```json
{
  "PK": "user-123",
  "SK": "CHAT#conv-abc#MSG#01HQ3ZZKBKACTAV9WEVGEMMVRY",
  "created_at": 1700000001,
  "expires_at": 1707776001,
  "sender": "user",
  "message": "What is the status of my order #12345?"
}
```

**Why this design works:**

- Uses **ULID** (Universally Unique Lexicographically Sortable Identifier) for message IDs, providing automatic chronological ordering
- **Vertical partitioning** avoids the 400 KB item size limit -- each message is its own item (1 WCU per small message write vs. potentially hundreds of WCU if messages were stored as a list in a single item)
- `SK` prefix pattern (`CONV#` vs `CHAT#`) enables efficient access patterns: query `begins_with('CONV#')` for listing conversations, `begins_with('CHAT#<convId>#MSG')` for getting messages
- **TTL** on `expires_at` provides automatic cleanup (e.g., 90 days)

**Access patterns:**

| Pattern | Operation | Key Condition |
|---|---|---|
| List user conversations | `Query` | `PK = userId AND begins_with(SK, 'CONV#')` |
| Get messages for conversation | `Query` | `PK = userId AND begins_with(SK, 'CHAT#<convId>#MSG')` |
| Create conversation | `PutItem` | `PK = userId, SK = 'CONV#<convId>'` |
| Add message | `PutItem` | `PK = userId, SK = 'CHAT#<convId>#MSG#<ulid>'` |
| Delete conversation | `BatchWriteItem` | Delete metadata item + all message items |

**Anti-pattern (exam gotcha)**: Storing all messages as a list attribute in a single item. This fails because:
1. Items have a 400 KB size limit
2. Every write (even a 2-byte "hi") costs WCU proportional to the full item size
3. No way to query individual messages efficiently

### 2.3 Metadata Storage for GenAI Applications

DynamoDB is commonly used to store metadata alongside vector databases:

- **Document metadata**: Source, title, date, author, permissions for documents stored in S3 whose embeddings are in a vector store
- **User preferences**: Model preferences, conversation settings, prompt templates
- **Session state**: Active session tracking, model parameters per session
- **Prompt/response logging**: Audit trail of prompts and completions

**Example: metadata sidecar for a vector store**

```
PK: DOC#<documentId>
SK: META

Attributes:
  source_s3_uri: "s3://my-bucket/docs/report.pdf"
  chunk_count: 42
  embedding_model: "amazon.titan-embed-text-v2:0"
  indexed_at: 1700000000
  permissions: ["role-admin", "role-analyst"]
```

The vector store holds the embeddings and chunk text; DynamoDB holds the rich metadata that supports filtering, access control, and auditing.

### 2.4 DynamoDB Streams for Change Detection

DynamoDB Streams captures a **time-ordered sequence of item-level modifications** for up to **24 hours**. Each stream record contains information about a single data modification.

**Stream view types:**

| View Type | Content | Use Case |
|---|---|---|
| `KEYS_ONLY` | Only the key attributes | Lightweight event notification |
| `NEW_IMAGE` | Entire item after modification | Sync to downstream systems |
| `OLD_IMAGE` | Entire item before modification | Audit, rollback |
| `NEW_AND_OLD_IMAGES` | Both before and after | Diff detection, full audit trail |

**Key characteristics:**
- Stream records appear **exactly once** in the stream
- Records appear in the **same sequence** as actual modifications to the item
- Data retention: **24 hours**
- Maximum **2 simultaneous consumers per shard** (use EventBridge for more)
- Encrypted at rest
- No performance impact on the source table
- Separate endpoint from the DynamoDB data plane

**GenAI use cases for DynamoDB Streams:**

1. **Trigger re-embedding**: When a document's metadata changes, trigger a Lambda that regenerates embeddings in the vector store
2. **Sync to search index**: Stream changes to OpenSearch via Lambda for full-text search
3. **Real-time analytics**: Stream conversation data to Kinesis Data Streams for analytics
4. **Audit trail**: Capture all modifications to prompts, model configs, or guardrail settings
5. **Cache invalidation**: When source data changes, invalidate cached LLM responses

**DynamoDB Streams vs Kinesis Data Streams for DynamoDB:**

| Feature | DynamoDB Streams | Kinesis Data Streams |
|---|---|---|
| Retention | 24 hours | Up to 365 days |
| Consumers per shard | 2 | Unlimited (with enhanced fan-out) |
| Integration | Lambda triggers, KCL | Lambda, Firehose, Flink, Spark |
| Cost | Included with DynamoDB | Separate Kinesis pricing + CDC units |
| Ordering | Per-item ordering guaranteed | Per-shard ordering |

**Exam tip**: If the question mentions needing more than 2 consumers or retention beyond 24 hours, the answer is Kinesis Data Streams for DynamoDB (or EventBridge integration).

### 2.5 TTL for Data Lifecycle

Time to Live (TTL) enables **automatic, cost-free deletion** of expired items. The TTL attribute must store a **Unix epoch timestamp in seconds**.

**How TTL works:**
- DynamoDB scans for expired items in the background
- Items are typically deleted within **a few minutes to 48 hours** after expiration (not instant)
- Deleted items appear in DynamoDB Streams as **service deletions** (distinguishable from user deletions)
- TTL deletes are **free** -- they do not consume write capacity
- Expired items are removed from GSIs and LSIs
- With Global Tables, TTL deletes **replicate to all regions**

**GenAI use cases:**
- Auto-expire conversation history after 90 days
- Clean up temporary session data
- Remove cached prompt/response pairs after staleness threshold
- Comply with data retention policies (GDPR, etc.)

```typescript
// Setting TTL when creating a conversation
const ttlEpoch = Math.floor(Date.now() / 1000) + (90 * 24 * 60 * 60); // 90 days

const params = {
  TableName: "ChatApp",
  Item: {
    PK: { S: "user-123" },
    SK: { S: "CONV#conv-abc" },
    created_at: { N: String(Math.floor(Date.now() / 1000)) },
    expires_at: { N: String(ttlEpoch) },  // TTL attribute
    title: { S: "New conversation" },
  },
};
```

### 2.6 On-Demand vs Provisioned Capacity

| Mode | Best For | Pricing | Scaling |
|---|---|---|---|
| **On-demand** | Unpredictable traffic, new apps, spiky GenAI workloads | Per-request pricing | Instant, automatic |
| **Provisioned** | Predictable, steady-state workloads | Per-hour capacity units | Auto Scaling available but not instant |

**On-demand capacity:**
- Pay per read/write request
- Scales instantly to accommodate traffic spikes
- No capacity planning needed
- More expensive per-request than provisioned at steady state
- Best for: new GenAI apps with unknown traffic patterns, chatbots with spiky usage

**Provisioned capacity:**
- Specify Read Capacity Units (RCU) and Write Capacity Units (WCU)
- 1 RCU = 1 strongly consistent read/second for items up to 4 KB
- 1 WCU = 1 write/second for items up to 1 KB
- Auto Scaling adjusts within min/max bounds (but has a ramp-up delay)
- Can use **Reserved Capacity** for up to 77% savings
- Best for: production chatbots with predictable, high-throughput traffic

**Exam tip**: For GenAI applications that are new or have unpredictable traffic, the answer is almost always on-demand mode. For cost optimization of mature, predictable workloads, switch to provisioned with auto scaling.

### 2.7 TypeScript SDK v3 Examples

```typescript
import {
  DynamoDBClient,
  PutItemCommand,
  QueryCommand,
} from "@aws-sdk/client-dynamodb";
import { unmarshall, marshall } from "@aws-sdk/util-dynamodb";

const client = new DynamoDBClient({ region: "us-east-1" });

// Store a conversation message
async function putMessage(
  userId: string,
  conversationId: string,
  message: string,
  sender: "user" | "bot"
) {
  // Use a ULID-style sortable ID (timestamp-based for ordering)
  const messageId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const ttl = Math.floor(Date.now() / 1000) + 90 * 24 * 60 * 60;

  const command = new PutItemCommand({
    TableName: "ChatApp",
    Item: marshall({
      PK: userId,
      SK: `CHAT#${conversationId}#MSG#${messageId}`,
      message,
      sender,
      created_at: Math.floor(Date.now() / 1000),
      expires_at: ttl,
    }),
  });

  await client.send(command);
}

// Get messages for a conversation (ordered by sort key = chronological)
async function getConversationMessages(
  userId: string,
  conversationId: string
) {
  const command = new QueryCommand({
    TableName: "ChatApp",
    KeyConditionExpression: "PK = :pk AND begins_with(SK, :skPrefix)",
    ExpressionAttributeValues: marshall({
      ":pk": userId,
      ":skPrefix": `CHAT#${conversationId}#MSG`,
    }),
  });

  const response = await client.send(command);
  return (response.Items ?? []).map((item) => unmarshall(item));
}

// List all conversations for a user
async function listConversations(userId: string) {
  const command = new QueryCommand({
    TableName: "ChatApp",
    KeyConditionExpression: "PK = :pk AND begins_with(SK, :skPrefix)",
    ExpressionAttributeValues: marshall({
      ":pk": userId,
      ":skPrefix": "CONV#",
    }),
  });

  const response = await client.send(command);
  return (response.Items ?? []).map((item) => unmarshall(item));
}
```

### 2.8 DynamoDB Streams with Lambda (TypeScript)

```typescript
import { DynamoDBStreamHandler } from "aws-lambda";
import { unmarshall } from "@aws-sdk/util-dynamodb";
import { AttributeValue } from "@aws-sdk/client-dynamodb";

// Lambda function triggered by DynamoDB Stream
export const handler: DynamoDBStreamHandler = async (event) => {
  for (const record of event.Records) {
    const eventName = record.eventName; // INSERT | MODIFY | REMOVE

    if (eventName === "INSERT" && record.dynamodb?.NewImage) {
      const newItem = unmarshall(
        record.dynamodb.NewImage as Record<string, AttributeValue>
      );

      // Trigger re-embedding when new document metadata is added
      if (newItem.SK?.startsWith("DOC#")) {
        await triggerReembedding(newItem);
      }
    }

    if (eventName === "REMOVE") {
      // Handle TTL deletions vs user deletions
      const isServiceDeletion =
        record.userIdentity?.type === "Service" &&
        record.userIdentity?.principalId === "dynamodb.amazonaws.com";

      if (isServiceDeletion) {
        console.log("Item expired via TTL");
      }
    }
  }
};
```

### 2.9 Key Metrics

| Metric | Source | What It Tells You |
|---|---|---|
| `ConsumedReadCapacityUnits` | CloudWatch | Actual read throughput consumption |
| `ConsumedWriteCapacityUnits` | CloudWatch | Actual write throughput consumption |
| `ThrottledRequests` | CloudWatch | Capacity exceeded -- scale up or switch to on-demand |
| `SuccessfulRequestLatency` | CloudWatch | P50/P99 latency for operations |
| `SystemErrors` | CloudWatch | Internal DynamoDB errors (rare, retryable) |
| `AccountMaxReads/Writes` | CloudWatch | Approaching account-level limits |
| `TimeToLiveDeletedItemCount` | CloudWatch | Tracks TTL deletion volume |
| `IteratorAge` (Streams) | CloudWatch | Age of oldest unprocessed stream record -- indicates consumer lag |

---

## 3. Amazon ElastiCache

### 3.1 Overview: Redis OSS vs Memcached vs Valkey

ElastiCache is a **fully managed in-memory data store** service. For the exam, focus on **ElastiCache for Valkey** (the successor to Redis OSS) because it supports vector search, which enables semantic caching.

| Feature | Valkey (Redis OSS successor) | Memcached |
|---|---|---|
| Data structures | Strings, hashes, lists, sets, sorted sets, streams, JSON, **vectors** | Simple key-value only |
| Persistence | Optional (AOF, RDB snapshots) | None |
| Replication | Yes (primary + replicas) | None |
| Clustering | Yes (sharding) | Yes (sharding) |
| Pub/Sub | Yes | No |
| Lua scripting | Yes | No |
| Vector search | Yes (HNSW, FLAT) | No |
| Transactions | Yes (MULTI/EXEC) | No |
| TTL | Per-key | Per-key |

**Exam tip**: If the question involves caching for GenAI, the answer is always ElastiCache for Valkey (not Memcached) because of vector search support.

### 3.2 Semantic Caching Patterns for AI

Semantic caching is the most important ElastiCache concept for this exam. Unlike traditional caches that require exact string matches, a semantic cache uses **vector similarity** to match semantically equivalent queries.

**How semantic caching works:**

1. User sends query to the GenAI application
2. Application generates an **embedding** of the query (e.g., using Amazon Titan Text Embeddings)
3. Application searches ElastiCache for **similar embeddings** (vector similarity search)
4. **Cache hit** (similarity above threshold): Return the cached response directly -- no LLM call needed
5. **Cache miss**: Call the LLM, get the response, then cache both the query embedding and response in ElastiCache for future reuse

**Performance impact (from AWS benchmarks):**
- Up to **86% reduction** in LLM inference cost
- Up to **88% improvement** in average end-to-end latency
- 95%+ recall rate for vector search in ElastiCache
- Microsecond read latency for cache hits

**Architecture:**
```
User Query
    |
    v
Generate Query Embedding (Bedrock Titan Embeddings)
    |
    v
Vector Search in ElastiCache ──── Cache Hit? ──── Yes ──> Return Cached Response
    |                                                      (microseconds)
    No (Cache Miss)
    |
    v
Call LLM (Bedrock) ──> Get Response ──> Cache query embedding + response in ElastiCache
    |
    v
Return Response to User
```

**Key configuration decisions:**

| Parameter | Description | Typical Value |
|---|---|---|
| **Similarity threshold** | Minimum similarity score to consider a cache hit | 0.90 - 0.98 (tune per use case) |
| **TTL** | How long cached responses remain valid | Hours to days (depends on data freshness needs) |
| **Distance metric** | Cosine, Euclidean, or inner product | Cosine (most common for text) |
| **Index type** | HNSW or FLAT | HNSW for large caches, FLAT for small |

**Similarity threshold tuning (exam-critical):**
- **Too high** (e.g., 0.99): Very few cache hits, minimal cost savings
- **Too low** (e.g., 0.80): More cache hits but risk returning incorrect/stale responses
- **Best practice**: Start at 0.95, monitor quality, adjust based on user feedback

### 3.3 Response Caching Strategies

Beyond semantic caching, ElastiCache supports multiple caching strategies for GenAI:

**1. Exact match caching:**
- Cache the exact prompt+response pair
- Simplest, zero risk of returning wrong answers
- Low hit rate (queries must be identical)

**2. Semantic caching (covered above):**
- Cache based on vector similarity
- Higher hit rate, some risk of semantic mismatch
- Best for: FAQ-style queries, customer support, IT helpdesks

**3. Conversational memory:**
- Store recent conversation context in ElastiCache for fast retrieval
- Agents and chatbots retrieve past interactions from ElastiCache instead of DynamoDB for hot data
- Integration with frameworks: Mem0, LangGraph, LangChain use ElastiCache as a memory backend

**4. Tool output caching (for agents):**
- Cache the results of tool calls (API lookups, database queries) that agents make
- Agentic AI applications break tasks into steps that may repeatedly look up similar information
- Cache tool outputs to avoid redundant calls

### 3.4 Cache Invalidation Patterns

| Strategy | How It Works | Best For |
|---|---|---|
| **TTL-based** | Entries automatically expire after a set time | Most GenAI caching (set TTL based on data freshness needs) |
| **Proactive invalidation** | Application explicitly deletes cache entries when source data changes | When you know exactly when data changes |
| **Proactive update** | Preload cache with known hot queries on deployment | Predictable query patterns |
| **Eviction policies** | LRU, LFU, or volatile-ttl when memory is full | Automatic memory management |

**Exam tip**: For GenAI caching, TTL-based invalidation is the most common answer. Set TTL to match how frequently your knowledge base updates.

### 3.5 ElastiCache Serverless

ElastiCache Serverless for Valkey automatically scales capacity based on demand. Relevant for GenAI workloads because:
- No capacity planning needed
- Scales from zero to billions of vectors
- Pay for what you use (ElastiCache Processing Units)
- Up to 30% discount with Database Savings Plans

### 3.6 TypeScript Example: Semantic Cache

```typescript
// Pseudocode illustrating semantic cache flow with ElastiCache for Valkey
// (Uses the ioredis client for Valkey compatibility)

import Redis from "ioredis";
import {
  BedrockRuntimeClient,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";

const redis = new Redis({
  host: "my-elasticache-cluster.xxxxx.cache.amazonaws.com",
  port: 6379,
  tls: {},
});

const bedrock = new BedrockRuntimeClient({ region: "us-east-1" });

const SIMILARITY_THRESHOLD = 0.95;
const CACHE_TTL_SECONDS = 3600; // 1 hour

// Generate embedding using Titan Embeddings V2
async function getEmbedding(text: string): Promise<number[]> {
  const command = new InvokeModelCommand({
    modelId: "amazon.titan-embed-text-v2:0",
    contentType: "application/json",
    body: JSON.stringify({ inputText: text }),
  });
  const response = await bedrock.send(command);
  const result = JSON.parse(new TextDecoder().decode(response.body));
  return result.embedding;
}

// Search semantic cache, fall back to LLM on miss
async function queryWithSemanticCache(userQuery: string): Promise<string> {
  const queryEmbedding = await getEmbedding(userQuery);

  // Search ElastiCache vector index for similar queries
  // FT.SEARCH is the Valkey vector search command
  const searchResults = await redis.call(
    "FT.SEARCH",
    "semantic_cache_idx",
    `*=>[KNN 1 @embedding $query_vec AS score]`,
    "PARAMS", "2", "query_vec", Buffer.from(new Float32Array(queryEmbedding).buffer),
    "SORTBY", "score",
    "RETURN", "2", "response", "score",
    "DIALECT", "2"
  ) as any[];

  // Check if we got a hit above our similarity threshold
  if (searchResults && searchResults[0] > 0) {
    const score = parseFloat(searchResults[2]?.[3]); // cosine similarity
    if (score >= SIMILARITY_THRESHOLD) {
      const cachedResponse = searchResults[2]?.[1];
      console.log(`Cache hit (similarity: ${score})`);
      return cachedResponse;
    }
  }

  // Cache miss: call the LLM
  console.log("Cache miss, calling LLM");
  const llmResponse = await callLLM(userQuery);

  // Store in cache for future use
  const cacheKey = `cache:${Date.now()}`;
  await redis.call(
    "HSET", cacheKey,
    "query", userQuery,
    "response", llmResponse,
    "embedding", Buffer.from(new Float32Array(queryEmbedding).buffer)
  );
  await redis.expire(cacheKey, CACHE_TTL_SECONDS);

  return llmResponse;
}
```

### 3.7 Key Metrics

| Metric | Source | What It Tells You |
|---|---|---|
| `CacheHitRate` | CloudWatch | Percentage of successful cache lookups |
| `EngineCPUUtilization` | CloudWatch | CPU used by Valkey engine (vector search is CPU-intensive) |
| `DatabaseMemoryUsagePercentage` | CloudWatch | Memory consumption (vectors use significant memory) |
| `CurrConnections` | CloudWatch | Active connections to cache |
| `Evictions` | CloudWatch | Items evicted due to memory pressure (may need scaling) |
| `ReplicationLag` | CloudWatch | Replica freshness |
| `NetworkBytesIn/Out` | CloudWatch | Network throughput |

---

## 4. Amazon Neptune

### 4.1 Graph Database Overview

Amazon Neptune is a **fully managed graph database** that supports two graph models:
- **Property Graph** with Apache TinkerPop Gremlin query language
- **RDF (Resource Description Framework)** with SPARQL query language

**Neptune Analytics** is a separate, memory-optimized engine for graph analytics with built-in vector search.

Key characteristics:
- Up to 15 read replicas
- Multi-AZ with automatic failover
- Continuous backup to S3
- Encryption at rest and in transit
- Supports up to **billions of relationships** with millisecond query latency

### 4.2 Knowledge Graphs for GenAI (GraphRAG)

This is Neptune's primary exam relevance. **GraphRAG** combines knowledge graphs with RAG to provide more accurate, comprehensive, and explainable AI responses.

**Why knowledge graphs improve GenAI:**

| Traditional RAG | GraphRAG |
|---|---|
| Retrieves isolated document chunks | Retrieves interconnected entities and relationships |
| Struggles with multi-hop reasoning | Supports multi-hop reasoning by traversing the graph |
| Context fragmentation across chunks | Maintains entity relationships across documents |
| Limited cross-document reasoning | Connects related information across multiple documents |

**How GraphRAG works:**
1. **Document ingestion**: Extract entities, relationships, and structural elements from unstructured text
2. **Graph construction**: Build a knowledge graph of entities and their relationships
3. **Embedding storage**: Store vector embeddings of graph nodes and edges
4. **Retrieval**: Vector search finds relevant nodes, then graph traversal expands context by following relationships
5. **Generation**: LLM generates response using the enriched, relationship-aware context

**Amazon Bedrock Knowledge Bases GraphRAG:**
- Fully managed: automatically creates and maintains graphs and embeddings
- Uses **Neptune Analytics** as the graph store
- Uses **OpenSearch Serverless** as the vector store
- Claude 3 Haiku for contextual enrichment during graph construction
- Supports only S3 as data source
- Max 1,000 files per data source (can request increase to 10,000)

**AWS GraphRAG Toolkit (self-managed):**
- Open-source Python toolkit
- Supports Neptune Database or Neptune Analytics as graph store
- Supports Neptune Analytics or OpenSearch Serverless as vector store
- Supports Bring Your Own Knowledge Graph (BYOKG) -- connect existing graphs to LLMs
- More flexible but requires managing the pipeline yourself

### 4.3 Use Cases for Neptune in GenAI

| Use Case | Why Neptune |
|---|---|
| **Fraud detection** | Traverse transaction relationships to identify fraud rings |
| **Drug discovery** | Map molecular interactions and protein relationships |
| **Recommendation engines** | Traverse user-item-feature relationships |
| **IT operations** | Map infrastructure dependencies, impact analysis |
| **Compliance/regulatory** | Track entity relationships for KYC, AML |
| **Enterprise search** | Connect information across departments and documents |

### 4.4 When to Use Neptune vs Other Databases

- **Choose Neptune** when: You need to model and query complex relationships between entities, your queries involve traversing paths/connections, or you need GraphRAG
- **Choose DynamoDB** when: You need simple key-value or document access with single-digit ms latency
- **Choose Aurora** when: You need relational data modeling with SQL queries and vector search
- **Choose OpenSearch** when: You need full-text search combined with vector search at scale

### 4.5 TypeScript SDK v3 Example

```typescript
// Neptune is typically accessed via HTTP endpoints with Gremlin or SPARQL
// For Neptune Analytics (used with Bedrock Knowledge Bases GraphRAG):

import {
  NeptuneGraphClient,
  ExecuteQueryCommand,
} from "@aws-sdk/client-neptune-graph";

const client = new NeptuneGraphClient({ region: "us-east-1" });

// Query a Neptune Analytics graph
async function queryKnowledgeGraph(graphId: string, query: string) {
  const command = new ExecuteQueryCommand({
    graphIdentifier: graphId,
    queryString: query,
    language: "OPEN_CYPHER", // or GREMLIN
  });

  const response = await client.send(command);
  return response.payload;
}

// Example: Find entities related to a topic within 2 hops
const results = await queryKnowledgeGraph(
  "g-abc123",
  `
  MATCH (e:Entity {name: 'Amazon Bedrock'})-[r*1..2]-(related)
  RETURN e.name, type(r), related.name
  LIMIT 20
  `
);
```

### 4.6 Key Metrics

| Metric | Source | What It Tells You |
|---|---|---|
| `GremlinRequestsPerSec` | CloudWatch | Query throughput |
| `GremlinErrors` | CloudWatch | Query failures |
| `CPUUtilization` | CloudWatch | Graph traversal is CPU-intensive |
| `VolumeBytesUsed` | CloudWatch | Graph storage consumption |
| `MainRequestQueuePendingRequests` | CloudWatch | Query queue depth |

---

## 5. Amazon DocumentDB

### 5.1 Overview

Amazon DocumentDB is a **fully managed, MongoDB-compatible document database**. It supports the MongoDB API, making it a drop-in replacement for applications using MongoDB drivers.

Key characteristics:
- **MongoDB API compatibility** (works with existing MongoDB drivers and tools)
- Storage auto-scales up to 128 TB
- Up to 15 read replicas
- Continuous backup to S3
- Flexible JSON document model with schema-less design

### 5.2 Vector Search Capabilities

DocumentDB supports vector search starting with version 5.0+:

- **Indexing methods**: HNSW and IVFFlat (same as pgvector)
- **Max dimensions**: 2,000 (indexed), 16,000 (stored without index)
- **Distance metrics**: Euclidean, cosine, dot product
- **Query operators**: `$search` (classic) and `$vectorSearch` (v8.0+, aggregation pipeline)

**Creating a vector index:**
```javascript
// HNSW index
db.runCommand({
  createIndexes: "documents",
  indexes: [{
    key: { embedding: "cosmosSearch" },
    cosmosSearchOptions: {
      kind: "vector-hnsw",
      m: 16,
      efConstruction: 64,
      similarity: "COS",
      dimensions: 1536
    },
    name: "embedding_hnsw_index"
  }]
});

// IVFFlat index
db.runCommand({
  createIndexes: "documents",
  indexes: [{
    key: { embedding: "cosmosSearch" },
    cosmosSearchOptions: {
      kind: "vector-ivf",
      numLists: 100,
      similarity: "COS",
      dimensions: 1536
    },
    name: "embedding_ivf_index"
  }]
});
```

**Querying vectors (v8.0+ $vectorSearch):**
```javascript
db.documents.aggregate([
  {
    $vectorSearch: {
      index: "embedding_hnsw_index",
      path: "embedding",
      queryVector: [0.1, 0.2, 0.3, ...],
      limit: 10,
      numCandidates: 100
    }
  }
]);
```

### 5.3 When to Use DocumentDB vs DynamoDB

| Factor | DocumentDB | DynamoDB |
|---|---|---|
| Data model | Rich JSON documents, flexible schema | Key-value with optional document support |
| Query flexibility | MongoDB query language, aggregation pipeline, ad-hoc queries | Key-based access, limited query patterns without GSIs |
| Vector search | Native support (HNSW, IVFFlat) | No native vector support |
| Scale | Vertical + read replicas | Horizontal, virtually unlimited |
| Latency | Single-digit ms | Single-digit ms |
| Schema evolution | Excellent (schema-less documents) | Good (schema-less but key design is rigid) |
| Best for GenAI | Document-heavy RAG with vector search, existing MongoDB apps | Conversation history, metadata, session state |
| Pricing | Instance-based | Per-request or provisioned capacity |

**Exam tip**: If a question mentions MongoDB compatibility or an existing MongoDB application, DocumentDB is the answer. If it asks about conversation history or metadata at scale, the answer is DynamoDB.

### 5.4 TypeScript Example

```typescript
import { MongoClient } from "mongodb";

const uri = "mongodb://username:password@docdb-cluster.cluster-xxxxx.us-east-1.docdb.amazonaws.com:27017/?tls=true&tlsCAFile=global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false";

const client = new MongoClient(uri);

async function vectorSearch(queryEmbedding: number[], limit: number = 10) {
  const db = client.db("genai_app");
  const collection = db.collection("documents");

  // DocumentDB 8.0+ $vectorSearch
  const results = await collection.aggregate([
    {
      $vectorSearch: {
        index: "embedding_hnsw_index",
        path: "embedding",
        queryVector: queryEmbedding,
        limit: limit,
        numCandidates: limit * 10,
      },
    },
    {
      $project: {
        content: 1,
        metadata: 1,
        score: { $meta: "vectorSearchScore" },
      },
    },
  ]).toArray();

  return results;
}
```

---

## 6. Amazon RDS (PostgreSQL with pgvector)

### 6.1 Overview

Amazon RDS for PostgreSQL supports the **pgvector** extension, providing the same vector search capabilities as Aurora PostgreSQL but on the standard RDS platform.

### 6.2 RDS PostgreSQL vs Aurora PostgreSQL for Vectors

| Factor | RDS PostgreSQL + pgvector | Aurora PostgreSQL + pgvector |
|---|---|---|
| Performance | Standard PostgreSQL performance | Up to 5x PostgreSQL throughput |
| Storage | Manual provisioning (gp3, io1/io2) | Auto-scaling (10 GB to 128 TB) |
| Read replicas | Up to 15 (async replication) | Up to 15 (sub-10ms lag via shared storage) |
| Failover | 60-120 seconds | Under 30 seconds |
| Serverless | No | Aurora Serverless v2 |
| Optimized Reads | No | Yes (NVMe-based local caching) |
| Bedrock KB integration | Yes (as RDS for PostgreSQL data store) | Yes (preferred option) |
| Cost | Lower per-instance cost | Higher per-instance, but better price/performance at scale |
| Best for | Dev/test, small-scale vector workloads, cost-sensitive | Production vector workloads, high-throughput RAG |

**Exam tip**: If a question asks about vector search with PostgreSQL and does not specify a budget constraint, Aurora is the default answer. RDS is the answer when cost is the primary concern or the workload is small-scale.

### 6.3 TypeScript SDK v3 Example (RDS Data API)

```typescript
import { RDSClient, ExecuteStatementCommand } from "@aws-sdk/client-rds-data";

const client = new RDSClient({ region: "us-east-1" });

// Same API as Aurora when using Data API
async function vectorSearchRDS(queryEmbedding: number[]) {
  const command = new ExecuteStatementCommand({
    resourceArn: "arn:aws:rds:us-east-1:123456789012:db:my-rds-instance",
    secretArn: "arn:aws:secretsmanager:us-east-1:123456789012:secret:my-secret",
    database: "mydb",
    sql: `
      SELECT id, content, 1 - (embedding <=> :embedding::vector) AS similarity
      FROM documents
      ORDER BY embedding <=> :embedding::vector
      LIMIT 10
    `,
    parameters: [
      { name: "embedding", value: { stringValue: `[${queryEmbedding.join(",")}]` } },
    ],
  });

  return (await client.send(command)).records;
}
```

---

## 7. Database Selection Decision Guide for GenAI

### When the Exam Asks "Which Database?"

```
Need vector search for RAG?
├── Already using PostgreSQL? ──> Aurora PostgreSQL + pgvector
├── Already using MongoDB? ──> DocumentDB
├── Need full-text + vector hybrid search? ──> OpenSearch Service
├── Need graph-based relationships (GraphRAG)? ──> Neptune Analytics
├── Need lowest latency vector search (caching)? ──> ElastiCache for Valkey
└── Need billions of vectors, GPU acceleration? ──> OpenSearch Service

Need conversation history storage?
└── Always ──> DynamoDB (single-table, vertical partitioning)

Need metadata for GenAI apps?
└── Always ──> DynamoDB (key-value access pattern)

Need semantic caching for LLM responses?
└── Always ──> ElastiCache for Valkey

Need knowledge graph?
├── Fully managed with Bedrock KB? ──> Neptune Analytics (GraphRAG)
└── Self-managed? ──> Neptune Database + GraphRAG Toolkit

Need change detection from data store?
├── From DynamoDB? ──> DynamoDB Streams or Kinesis Data Streams
└── From relational DB? ──> Aurora CDC or RDS event notifications
```

### Vector Database Comparison Matrix

| Feature | Aurora (pgvector) | OpenSearch | DocumentDB | ElastiCache (Valkey) | Neptune Analytics |
|---|---|---|---|---|---|
| Max dimensions | 16,000 | 16,000 | 2,000 (indexed) | Configurable | Configurable |
| Index types | HNSW, IVFFlat | HNSW | HNSW, IVFFlat | HNSW, FLAT | HNSW |
| Bedrock KB support | Yes | Yes (Serverless) | No | No | Yes (GraphRAG) |
| Hybrid search | SQL + vector | BM25 + vector | MongoDB query + vector | Filter + vector | Graph traversal + vector |
| Quantization | halfvec, binary | Yes | No | No | No |
| Serverless option | Aurora Serverless v2 | OpenSearch Serverless | No | ElastiCache Serverless | Yes (Analytics) |
| Primary use case | SQL + vector | Dedicated vector search | MongoDB apps + vector | Semantic caching | GraphRAG |

---

## 8. Exam Gotchas and Traps

1. **DynamoDB item size limit is 400 KB**. Never store unbounded lists (like all messages) in a single item. Use vertical partitioning with composite sort keys.

2. **DynamoDB Streams retention is 24 hours**. If you need longer retention or more than 2 consumers, use Kinesis Data Streams for DynamoDB.

3. **IVFFlat requires data before index creation** (needs data to cluster). HNSW can be built on an empty table. If the question says "frequently changing data" or "incremental updates", HNSW is the answer.

4. **pgvector cosine distance operator is `<=>`**, not `<->` (which is L2/Euclidean). For text embeddings, cosine is almost always the right choice.

5. **DocumentDB max indexed vector dimensions is 2,000** (vs 16,000 for pgvector and OpenSearch). If the question mentions high-dimensional vectors (>2,000), DocumentDB is not the answer.

6. **ElastiCache semantic caching uses vector similarity, not exact match**. The similarity threshold must be tuned -- too low risks returning wrong answers, too high misses cache opportunities.

7. **TTL deletions in DynamoDB are not instant** (can take up to 48 hours). If the exam asks about immediate deletion, use `DeleteItem`, not TTL.

8. **DynamoDB on-demand mode** is the default recommendation for new/unpredictable GenAI workloads. Provisioned mode is for cost optimization of mature, predictable workloads.

9. **Aurora Serverless v2** is the answer when the question mentions variable or unpredictable vector search workloads that need to scale to zero.

10. **Neptune Analytics** (not Neptune Database) is what integrates with Bedrock Knowledge Bases for GraphRAG.

11. **GraphRAG is not a replacement for standard RAG** -- it complements it for queries that need multi-hop reasoning across relationships. Standard RAG with vector search is still appropriate for most document Q&A.

12. **ElastiCache for Valkey** (not Redis OSS, not Memcached) is the current recommended choice. AWS has migrated from Redis OSS to Valkey. Exam questions may reference either name.

13. **DynamoDB Streams vs EventBridge**: DynamoDB now integrates directly with EventBridge for more than 2 consumers and advanced filtering/routing. If the question mentions complex event routing, the answer is EventBridge.

14. **Aurora Optimized Reads** specifically helps vector workloads that are larger than memory by using local NVMe storage for caching. This is an Aurora-specific advantage over RDS.

15. **Bedrock Knowledge Bases schema for Aurora**: The vector store must be set up with the correct schema (id, embedding, chunks, metadata columns) before connecting to Bedrock. This is a manual prerequisite, not automatic.
