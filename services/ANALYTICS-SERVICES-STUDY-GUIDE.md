# Analytics Services -- Comprehensive Study Guide (AIP-C01)

Amazon OpenSearch Service is the **most heavily tested analytics service** on the exam, particularly for vector search and RAG architectures. AWS Glue is the second-most important, especially for data quality and data lineage. The remaining services (Athena, EMR, Kinesis, QuickSight, MSK) appear less frequently but are still in-scope.

---

## 1. Amazon OpenSearch Service

### 1.1 Overview and Cluster Architecture

Amazon OpenSearch Service is a **fully managed** service for deploying, operating, and scaling OpenSearch clusters. It supports search, analytics, log analysis, and -- critically for this exam -- **vector search** for generative AI applications.

**Cluster architecture:**
- **Domain**: A managed OpenSearch cluster consisting of nodes
- **Data nodes**: Store data and handle search/indexing requests
- **Dedicated master nodes**: Manage cluster state (recommended for production: 3 dedicated masters)
- **UltraWarm nodes**: Cost-effective warm storage for infrequently accessed data
- **Cold storage**: Lowest-cost tier backed by S3 for rarely accessed data
- **Multi-AZ with Standby**: Production-grade availability with automatic failover

**Key sizing consideration for vector workloads:**
OpenSearch uses half of an instance's RAM for the Java heap (up to 32 GiB). By default, k-NN uses up to 50% of the remaining half. An instance with 32 GiB RAM can accommodate approximately **8 GiB of vector graphs** (32 x 0.5 x 0.5). Monitor `KNNGraphMemoryUsage` to ensure graph memory stays within this budget.

### 1.2 Vector Search Capabilities (k-NN Plugin)

Vector search converts data (text, images, audio) into high-dimensional numerical vectors (embeddings) that capture semantic meaning. OpenSearch supports the `knn_vector` field type for storing dense vectors.

**Core concepts:**
- **knn_vector field**: Stores dense vectors with configurable dimensions (up to **16,000** dimensions, 10,000 floats for provisioned domains)
- **k-NN search**: Exact nearest neighbors -- accurate but slow on large datasets
- **Approximate k-NN (ANN)**: Uses algorithms like HNSW for faster searches at scale
- **Maximum k value**: 10,000 neighbors per query

**Search engines:**
| Engine | Algorithms | Best For |
|---|---|---|
| **FAISS** (Facebook) | HNSW, IVF | Large-scale production, quantization support |
| **NMSLIB** | HNSW | High-performance HNSW search |
| **Lucene** | HNSW | Smaller datasets, integrated with OpenSearch core |

**Distance metrics:**
| Metric | Use Case |
|---|---|
| **Euclidean distance** (`l2`) | General-purpose, measures absolute distance |
| **Cosine similarity** (`cosinesimil`) | Text embeddings -- measures angle between vectors regardless of magnitude |
| **Dot product** (`innerproduct`) | Pre-normalized vectors, fastest computation |

**Creating a k-NN index:**
```json
PUT my-vector-index
{
  "settings": {
    "index.knn": true
  },
  "mappings": {
    "properties": {
      "embedding": {
        "type": "knn_vector",
        "dimension": 1536,
        "method": {
          "engine": "faiss",
          "name": "hnsw",
          "space_type": "l2",
          "parameters": {
            "m": 16,
            "ef_construction": 256
          }
        }
      },
      "text": { "type": "text" },
      "metadata": { "type": "keyword" }
    }
  }
}
```

**Querying a k-NN index:**
```json
GET my-vector-index/_search
{
  "size": 5,
  "query": {
    "knn": {
      "embedding": {
        "vector": [0.1, 0.2, ...],
        "k": 5
      }
    }
  }
}
```

**Filtered k-NN search (important for RAG):**
```json
GET my-vector-index/_search
{
  "size": 5,
  "query": {
    "knn": {
      "embedding": {
        "vector": [0.1, 0.2, ...],
        "k": 5,
        "filter": {
          "bool": {
            "must": [
              { "term": { "category": "technical" } },
              { "range": { "date": { "gte": "2024-01-01" } } }
            ]
          }
        }
      }
    }
  }
}
```

**Quantization techniques for cost optimization:**
| Technique | Compression | Memory Savings | Use Case |
|---|---|---|---|
| **Binary quantization** | 32-bit to 1-bit | Up to 32x | Coarse-grained similarity |
| **Byte quantization** | 32-bit to 8-bit | 75% | Good balance of quality and savings |
| **FP16 quantization** | 32-bit to 16-bit | 50% | Minimal quality loss |
| **Product quantization** | Variable | Up to 64x | Maximum compression |

**Disk-based vector search** (OpenSearch 2.17+):
- Keeps compressed vectors in memory, full-precision vectors on disk
- **97% reduction** in memory requirements compared to in-memory mode
- Higher latency (low hundreds of milliseconds) but dramatically lower cost
- Ideal for large-scale production workloads where cost matters more than latency

### 1.3 Neural Plugin for Semantic Search

The Neural plugin provides end-to-end semantic search by integrating ML models directly into the search pipeline. It automates embedding generation during both ingestion and query time.

**Components:**
1. **Text embedding ingest pipeline processor**: Generates embeddings during document ingestion
2. **Neural query**: Semantic search that auto-generates query embeddings
3. **Neural sparse query**: Sparse vector search using learned sparse representations

**How neural search works:**
1. Configure an ML model connector (Bedrock, SageMaker, or remote model)
2. Create an ingest pipeline with a `text_embedding` processor
3. Documents ingested through the pipeline automatically get embeddings generated
4. At query time, use the `neural` query type -- it auto-generates the query embedding

**Neural query example:**
```json
GET my-index/_search
{
  "query": {
    "neural": {
      "embedding_field": {
        "query_text": "What is machine learning?",
        "model_id": "my-bedrock-model-id",
        "k": 10
      }
    }
  }
}
```

**Neural search with images (multimodal):**
```json
{
  "neural": {
    "vector_field": {
      "query_text": "query_text",
      "query_image": "base64_encoded_image",
      "model_id": "model_id",
      "k": 100
    }
  }
}
```

**Integration with Amazon Bedrock:**
- Use CloudFormation templates to create connectors between OpenSearch and Bedrock
- The connector creates an IAM role, a Lambda function, and registers a remote model via the ML Commons plugin
- Supports Amazon Titan Embeddings, Cohere Embed, and Titan Multimodal Embeddings
- Separate templates available for VPC-based domains

### 1.4 Hybrid Search (Combining Keyword and Vector Search)

Hybrid search blends **lexical search** (BM25 keyword matching) with **semantic search** (vector similarity) for the best of both worlds. This is the recommended approach for production RAG systems.

**Why hybrid search matters:**
- Keyword search is precise for exact terms, product names, codes
- Semantic search understands intent, synonyms, context
- Combining both yields **10-20% better relevance** than either alone (per Amazon case study)

**Implementation requires a search pipeline with normalization:**

**Step 1 -- Create a search pipeline:**
```json
PUT _search/pipeline/hybrid-pipeline
{
  "description": "Hybrid search pipeline",
  "phase_results_processors": [
    {
      "normalization-processor": {
        "normalization": {
          "technique": "min_max"
        },
        "combination": {
          "technique": "arithmetic_mean",
          "parameters": {
            "weights": [0.3, 0.7]
          }
        }
      }
    }
  ]
}
```

**Step 2 -- Execute a hybrid query:**
```json
GET my-index/_search?search_pipeline=hybrid-pipeline
{
  "query": {
    "hybrid": {
      "queries": [
        {
          "match": {
            "text": "machine learning algorithms"
          }
        },
        {
          "neural": {
            "embedding_field": {
              "query_text": "machine learning algorithms",
              "model_id": "my-model-id",
              "k": 10
            }
          }
        }
      ]
    }
  }
}
```

**Normalization techniques (exam-testable):**
| Technique | How It Works | When to Use |
|---|---|---|
| **min_max** | Scales scores to [0,1] range | Default choice, works well generally |
| **l2** | L2 norm normalization | When score distributions vary widely |

**Combination techniques:**
| Technique | How It Works | When to Use |
|---|---|---|
| **arithmetic_mean** | Simple average of normalized scores | Default, balanced approach |
| **geometric_mean** | Multiplicative average | Penalizes low scores more |
| **harmonic_mean** | Harmonic average | Requires both signals to be strong |

**Weight tuning**: The `weights` array controls relative importance. `[0.3, 0.7]` means 30% keyword, 70% semantic. Tune based on your query distribution.

**Sparse vector search** (newer approach):
- Reduces corpus terms to approximately 32,000 learned tokens
- Uses mostly-zero weight vectors (sparse representation)
- Can be combined with dense vectors in hybrid queries
- Lower memory footprint than dense vectors

### 1.5 Sharding Strategies for Vector Databases

Sharding determines how data is distributed across nodes. For vector workloads, shard configuration directly impacts search latency and cost.

**Key principles:**
- Each shard independently loads k-NN graphs into memory
- More shards = more parallelism but more overhead
- Fewer shards = less overhead but potentially higher per-shard latency
- **k-NN returns k results per shard, per segment** -- always set `size` along with `k`

**Shard sizing guidelines for vector workloads:**
| Factor | Recommendation |
|---|---|
| **Shard size** | 10-50 GiB per shard (general OpenSearch guidance) |
| **Vector memory** | Monitor `KNNGraphMemoryUsage` per data node |
| **Shard count** | Number of shards = dataset size / target shard size |
| **Replicas** | At least 1 replica for availability; more for read-heavy workloads |

**Memory planning formula:**
```
Required memory per node = (num_vectors x dimensions x 4 bytes x overhead_factor) / num_shards
overhead_factor ~= 1.5 for HNSW graphs
```

**HNSW parameters that affect memory and performance:**
| Parameter | Default | Effect |
|---|---|---|
| `m` | 16 | Connections per node in graph. Higher = better recall, more memory |
| `ef_construction` | 512 | Build-time quality. Higher = better graph, slower indexing |
| `ef_search` | Set at query time | Search-time quality. Higher = better recall, slower search |

### 1.6 Multi-Index Approaches for Specialized Domains

Use multiple indexes when different document types have different embedding models, dimensions, or search requirements.

**Common patterns:**

**Pattern 1 -- Domain-specific indexes:**
```
product-descriptions-index  (dimension: 1536, Titan Embeddings)
customer-reviews-index      (dimension: 1024, Cohere Embed)
support-tickets-index       (dimension: 768, custom model)
```
Query across multiple indexes with: `GET product-*,customer-*/_search`

**Pattern 2 -- Tiered freshness indexes:**
```
recent-docs-index    (hot tier, high-performance instances)
archive-docs-index   (UltraWarm tier, cost-optimized)
```

**Pattern 3 -- Language-specific indexes:**
```
docs-en-index  (English embedding model)
docs-es-index  (Spanish embedding model)
docs-ja-index  (Japanese embedding model)
```

**When to use multi-index vs. single index:**
| Scenario | Approach |
|---|---|
| Same embedding model, same dimensions | Single index with metadata filtering |
| Different embedding models/dimensions | Separate indexes (required) |
| Different access control needs | Separate indexes |
| Need independent scaling | Separate indexes |
| Minimize operational overhead | Single index with metadata fields |

### 1.7 Hierarchical Indexing Techniques

Hierarchical indexing improves retrieval quality by organizing data at multiple levels of granularity.

**Approach 1 -- Parent-child document indexing:**
- Index both document-level summaries and chunk-level details
- First search at the document level (coarse), then at the chunk level (fine) within matching documents
- Reduces the search space and improves relevance

**Approach 2 -- Multi-resolution embeddings:**
- Generate embeddings at different granularities: paragraph, page, document
- Coarse search first identifies relevant documents, fine search retrieves exact passages
- Useful for long documents where chunk-level search alone might miss context

**Approach 3 -- Metadata-enriched hierarchical filtering:**
```json
{
  "query": {
    "knn": {
      "chunk_embedding": {
        "vector": [...],
        "k": 20,
        "filter": {
          "bool": {
            "must": [
              { "term": { "document_type": "technical_manual" } },
              { "term": { "section": "troubleshooting" } }
            ]
          }
        }
      }
    }
  }
}
```

### 1.8 Index Optimization for Performance

**Best practices for production vector search:**

1. **Force merge** completed indexes to reduce segment count (fewer segments = fewer per-segment k-NN searches)
2. **Warm up** k-NN indexes after deployment with `POST /_plugins/_knn/warmup/my-index`
3. **Use appropriate quantization** -- FP16 or byte quantization for most workloads; binary for very large scale
4. **Set `ef_search`** appropriately at query time (higher = better recall, slower)
5. **Use disk-based search** for cost-sensitive workloads (OpenSearch 2.17+)
6. **Monitor metrics**: `KNNGraphMemoryUsage`, `SearchLatency`, `Searchable Documents`
7. **Use `_msearch` API** for bulk queries to reduce per-request overhead

**Refresh interval tuning:**
- Default is 1 second for provisioned domains
- For write-heavy workloads, increase refresh interval (e.g., 30s) during bulk ingestion
- For Serverless collections, refresh interval is fixed at **60 seconds**

### 1.9 OpenSearch Serverless vs. Provisioned

| Feature | Provisioned | Serverless |
|---|---|---|
| **Scaling** | Manual (add/remove nodes) | Automatic (OCU-based) |
| **Billing** | Per-instance-hour + EBS storage | OCU-hours (compute) + S3 storage |
| **Vector engines** | FAISS, NMSLIB, Lucene | FAISS only (HNSW algorithm only) |
| **Encryption** | Optional | Always required |
| **Access control** | IAM + fine-grained access control | Data access policies |
| **Version upgrades** | Manual | Automatic |
| **Network** | VPC or public | VPC endpoints + network policies |
| **Index refresh** | Configurable (default 1s) | Fixed at 60 seconds |
| **Service name (signing)** | `es` | `aoss` |
| **Neural search latency** | Normal | Up to 15 seconds for newly created pipelines |
| **IVF algorithm** | Supported | Not supported |
| **Lucene engine** | Supported | Not supported for ANN |
| **Inline/stored scripts** | Supported | Not supported |
| **Billion-scale workloads** | Need to plan capacity | Auto-scales (contact support for >200 OCUs) |

**When to use Serverless:**
- Unpredictable or bursty workloads
- Want zero infrastructure management
- RAG applications with moderate query volume
- Development/testing environments

**When to use Provisioned:**
- Predictable, sustained workloads
- Need IVF algorithm or Lucene engine
- Need sub-second index refresh
- Need maximum control over instance types and scaling

### 1.10 Integration with Bedrock Knowledge Bases

Amazon Bedrock Knowledge Bases natively supports OpenSearch Serverless as a vector store. This is the **recommended vector database for Bedrock RAG applications**.

**How it works:**
1. Bedrock automatically creates an OpenSearch Serverless collection (vector search type)
2. Documents are chunked, embedded using your chosen model (e.g., Titan Embeddings V2), and indexed
3. At query time, Bedrock generates query embeddings and searches the OpenSearch index
4. Retrieved chunks are sent as context to the LLM for answer generation

**Configuration in Bedrock:**
```json
{
  "collectionArn": "arn:aws:aoss:us-east-1:123456789012:collection/my-collection",
  "vectorIndexName": "bedrock-knowledge-base-index",
  "fieldMapping": {
    "vectorField": "embedding",
    "textField": "text",
    "metadataField": "metadata"
  }
}
```

**Binary embeddings support:**
- Amazon Titan Text Embeddings V2 supports binary embeddings
- When combined with OpenSearch Serverless binary vector stores, reduces memory usage significantly
- Enables cost-effective RAG at scale

### 1.11 Exam Gotchas -- OpenSearch

1. **k returns per shard**: k-NN returns `k` results per shard, per segment. Always set both `k` and `size` in your query, or you may get more results than expected.
2. **Serverless limitations**: No IVF, no Lucene engine, no inline scripts, 60-second refresh interval, FAISS/HNSW only.
3. **Memory budget**: k-NN uses up to 50% of (RAM - heap). Exceeding this degrades performance.
4. **Neural search on Serverless**: Expect up to 15 seconds latency on newly created pipelines. Only remote models are supported.
5. **Signing difference**: Provisioned uses `es` service name, Serverless uses `aoss`. Must include `x-amz-content-sha256` header for Serverless.
6. **Hybrid search requires a search pipeline**: You cannot just combine match and knn in a bool query and get proper score normalization. You need the normalization processor.
7. **Dimension limits**: Up to 16,000 dimensions for Serverless, 10,000 for provisioned k-NN.
8. **UltraWarm migration**: k-NN indexes from version 2.x+ can migrate to UltraWarm/cold on domain version 2.17+.
9. **Disk-based vector search**: Available on OpenSearch 2.17+. Provides 97% memory reduction but higher latency.
10. **Bedrock integration**: Bedrock Knowledge Bases defaults to OpenSearch Serverless. The connector uses Lambda + ML Commons plugin.

### 1.12 TypeScript SDK v3 -- OpenSearch

OpenSearch uses its own client library, not the AWS SDK, for data operations. The AWS SDK is used for domain management.

**Domain management (AWS SDK):**
```typescript
import { OpenSearchClient, DescribeDomainCommand } from "@aws-sdk/client-opensearch";

const client = new OpenSearchClient({ region: "us-east-1" });

const response = await client.send(
  new DescribeDomainCommand({ DomainName: "my-vector-domain" })
);
console.log(response.DomainStatus?.EngineVersion);
```

**Serverless collection management:**
```typescript
import {
  OpenSearchServerlessClient,
  CreateCollectionCommand,
} from "@aws-sdk/client-opensearchserverless";

const client = new OpenSearchServerlessClient({ region: "us-east-1" });

const response = await client.send(
  new CreateCollectionCommand({
    name: "my-vector-collection",
    type: "VECTORSEARCH",
    description: "Vector store for RAG application",
  })
);
console.log(response.createCollectionDetail?.id);
```

**Data operations (OpenSearch client with SigV4 signing):**
```typescript
import { Client } from "@opensearch-project/opensearch";
import { AwsSigv4Signer } from "@opensearch-project/opensearch/aws";
import { defaultProvider } from "@aws-sdk/credential-provider-node";

const client = new Client({
  ...AwsSigv4Signer({
    region: "us-east-1",
    service: "aoss", // "aoss" for Serverless, "es" for provisioned
    getCredentials: () => defaultProvider()(),
  }),
  node: "https://my-collection-id.us-east-1.aoss.amazonaws.com",
});

// Index a document with vector
await client.index({
  index: "my-vector-index",
  body: {
    embedding: [0.1, 0.2, 0.3 /* ... 1536 dimensions */],
    text: "OpenSearch supports vector search for RAG applications",
    category: "technical",
  },
});

// k-NN search
const results = await client.search({
  index: "my-vector-index",
  body: {
    size: 5,
    query: {
      knn: {
        embedding: {
          vector: [0.1, 0.2, 0.3 /* ... query embedding */],
          k: 5,
        },
      },
    },
  },
});
```

---

## 2. AWS Glue

### 2.1 Glue Data Quality for Validation

AWS Glue Data Quality is a **serverless, ML-powered** capability for measuring and monitoring data quality. It is built on the open-source DeeQu framework and uses the **Data Quality Definition Language (DQDL)** to express rules.

**Why it matters for GenAI:**
- Garbage in, garbage out -- poor training data quality produces poor model outputs
- Data quality checks are essential before fine-tuning, continued pre-training, or RAG indexing
- Glue Data Quality integrates directly into ETL pipelines to validate data before downstream use

**Key capabilities:**
- **Rule recommendations**: ML-powered automatic rule suggestions based on data analysis
- **DQDL rules**: 26+ built-in rule types for comprehensive validation
- **Row-level results**: Identify which specific records failed quality checks
- **Anomaly detection**: ML-based detection of data quality drifts over time
- **Dynamic rules**: Compare current metrics against historical values using `last()` operator
- **Labels**: Attach custom metadata to rules (team ownership, criticality, regulatory)
- **Integration**: EventBridge, CloudWatch, S3 output for data quality results

**Important DQDL rule types:**

| Rule Type | What It Checks | Example |
|---|---|---|
| **Completeness** | % of non-null values | `Completeness "email" > 0.95` |
| **Uniqueness** | % of unique values | `Uniqueness "user_id" = 1.0` |
| **ColumnValues** | Value constraints | `ColumnValues "age" between 0 and 120` |
| **ColumnLength** | String length constraints | `ColumnLength "phone" = 10` |
| **ColumnExists** | Column presence | `ColumnExists "embedding_vector"` |
| **ColumnCount** | Number of columns | `ColumnCount >= 10` |
| **RowCount** | Number of rows | `RowCount > 1000` |
| **CustomSql** | Custom SQL validation | `CustomSql "SELECT COUNT(*) FROM ..." > 0` |
| **ColumnDataType** | Data type compliance | `ColumnDataType "score" = "DOUBLE"` |
| **ColumnCorrelation** | Correlation between columns | `ColumnCorrelation "x" "y" > 0.8` |
| **AggregateMatch** | Cross-dataset matching | Compares aggregates between datasets |

**DQDL ruleset example:**
```
Rules = [
  # Ensure training data quality
  Completeness "text_content" > 0.99,
  Uniqueness "document_id" = 1.0,
  ColumnValues "label" in ["positive", "negative", "neutral"],
  ColumnLength "text_content" between 10 and 50000,
  RowCount > 10000,

  # Dynamic rule -- compare to historical baseline
  RowCount > last(5).avg() * 0.9
]
```

**Integration in a Glue ETL job (visual editor):**
1. Add a data source node
2. Add an "Evaluate Data Quality" transform node
3. Define rules using the DQDL builder or text editor
4. Configure actions: publish to CloudWatch, fail job on quality failure
5. Route passing records downstream, failing records to a quarantine location

### 2.2 Glue Data Catalog for Metadata Management

The Glue Data Catalog is a **persistent, centralized metadata repository** for all data assets. It is a drop-in replacement for the Apache Hive Metastore.

**Key concepts:**
- **Databases**: Logical groupings of tables
- **Tables**: Metadata definitions (schema, location, format, partitions) -- not the actual data
- **Partitions**: Subdivision of tables for efficient querying (e.g., by date)
- **Connections**: Store parameters for connecting to data stores (JDBC, S3, etc.)
- **Schema Registry**: Manage and enforce schemas for streaming data (Kafka, Kinesis)

**For GenAI exam tasks:**
- **Data source registration** (Task 3.3.2): Register data sources in the Data Catalog so that Glue ETL, Athena, Redshift Spectrum, and EMR can discover and query them
- Use crawlers to auto-discover schemas or manually define tables via console/API/CLI
- The Data Catalog provides **schema change tracking** and **data access controls**
- Integrates with AWS Lake Formation for fine-grained access control

**Best practices:**
- Run crawlers regularly (or on schedule) to keep metadata current
- Use incremental crawls for frequently changing data sources
- Establish consistent naming conventions for databases and tables
- Use the Data Catalog as the centralized metadata layer for Athena, Redshift Spectrum, EMR, and Lake Formation

### 2.3 Data Lineage Tracking for Compliance

Data lineage traces data origins, tracks transformations, and visualizes how data flows through your organization. This is critical for AI governance and compliance.

**AWS Glue provides lineage through two mechanisms:**

**1. AWS Glue Job Lineage (built-in):**
- Glue ETL jobs automatically track source-to-target lineage
- Shows which datasets were read, what transformations were applied, where output was written
- Captured at the job run level

**2. Amazon DataZone Integration (enhanced lineage):**
- DataZone provides a graphical lineage visualization
- Captures lineage from AWS Glue catalogs and Amazon Redshift databases
- Supports column-level lineage
- Provides upstream/downstream navigation
- APIs: `GetLineageNode`, `ListLineageNodeHistory`, `PostLineageEvent`
- Glue jobs and notebooks can send lineage events directly to DataZone

**For the exam (Task 3.3.1):**
- Know that Glue tracks lineage at the job level automatically
- DataZone extends this with visual, cross-organizational lineage
- Lineage metadata should include: processing stage (raw/filtered/processed/analyzed), transformation steps, software versions, parameter settings
- Store lineage in a centralized catalog -- the Glue Data Catalog + DataZone

**Lifecycle metadata tagging pattern:**
```
raw-data/          -> stage: "raw"
filtered-data/     -> stage: "filtered", filter_params: {...}
processed-data/    -> stage: "processed", model_version: "v2.1"
analyzed-results/  -> stage: "analyzed", pipeline_run_id: "abc123"
```

### 2.4 Glue ETL for Data Processing

AWS Glue ETL is a **serverless** data processing engine based on Apache Spark. It is commonly used to prepare data for AI/ML pipelines.

**Key features for GenAI:**
- **Auto-scaling**: Automatically allocates resources based on workload
- **Flex execution**: Lower-cost execution for non-urgent jobs (uses spare capacity)
- **Streaming ETL**: Process streaming data from Kinesis Data Streams, Kafka, and MSK
- **Built-in transforms**: Clean, enrich, deduplicate, flatten, normalize data
- **Data format conversion**: Convert between JSON, CSV, Parquet, ORC, Avro, Iceberg
- **Worker types**: Standard, G.1X, G.2X, G.4X, G.8X, Z.2X (for memory-intensive jobs)
- **Bookmarking**: Track previously processed data for incremental ETL
- **DPU (Data Processing Unit)**: Unit of billing -- 1 DPU = 4 vCPUs + 16 GB memory

**Common GenAI data preparation patterns:**
1. **Training data preparation**: Clean, deduplicate, and format text data for fine-tuning
2. **RAG document processing**: Extract text from documents, chunk, and prepare for embedding
3. **Feature engineering**: Transform raw data into features for ML models
4. **Data validation pipeline**: Glue ETL + Data Quality rules before indexing into OpenSearch

### 2.5 Glue Crawlers

Crawlers automatically discover data schemas and create/update table definitions in the Data Catalog.

**How crawlers work:**
1. Connect to a data store (S3, JDBC, DynamoDB, etc.)
2. Determine data format using **classifiers** (built-in or custom)
3. Infer schema (column names, types)
4. Create or update table metadata in the Data Catalog
5. Create partitions based on folder structure (e.g., `year=2024/month=01/`)

**Supported data stores:** Amazon S3, DynamoDB, JDBC databases (RDS, Aurora, Redshift), MongoDB, and others.

**Built-in classifiers:** JSON, CSV, Parquet, ORC, Avro, XML, and more.

**Best practices:**
- Use **incremental crawling** for large, frequently updated datasets
- Define **separate include paths** for tables with different schemas in the same S3 prefix
- Schedule crawlers to run after data ingestion completes
- Each Athena table corresponds to an S3 prefix -- avoid multiple tables from the same prefix

### 2.6 Exam Gotchas -- Glue

1. **DQDL is the language for rules**: Know the name "Data Quality Definition Language" and its basic syntax.
2. **Data Quality works on both ETL jobs and Data Catalog**: Two entry points for the same capability.
3. **Dynamic rules use `last()`**: For comparing current metrics to historical baselines.
4. **Crawlers create metadata, not data**: They do not move or transform data.
5. **Data Catalog is a Hive Metastore replacement**: Compatible with Athena, EMR, Redshift Spectrum.
6. **Lineage is automatic in Glue jobs**: No extra configuration needed for basic lineage.
7. **DataZone provides enhanced lineage**: Visual, cross-org, column-level lineage beyond what Glue provides alone.
8. **Nested/list data types not supported in DQDL**: Rules cannot evaluate nested or list-type data sources.
9. **Row-level results**: Data Quality can output which specific rows failed checks, enabling quarantine patterns.
10. **Glue Streaming ETL**: Can ingest from Kinesis Data Streams, Kafka, and MSK in real time.

### 2.7 TypeScript SDK v3 -- Glue

```typescript
import {
  GlueClient,
  GetDatabaseCommand,
  GetTableCommand,
  StartJobRunCommand,
  GetDataQualityResultCommand,
  StartCrawlerCommand,
} from "@aws-sdk/client-glue";

const glue = new GlueClient({ region: "us-east-1" });

// Get a database from the Data Catalog
const db = await glue.send(
  new GetDatabaseCommand({ Name: "my_genai_database" })
);
console.log(db.Database?.Name);

// Get table metadata
const table = await glue.send(
  new GetTableCommand({
    DatabaseName: "my_genai_database",
    Name: "training_data",
  })
);
console.log(table.Table?.StorageDescriptor?.Columns);

// Start a Glue ETL job
const jobRun = await glue.send(
  new StartJobRunCommand({
    JobName: "prepare-training-data",
    Arguments: {
      "--input_path": "s3://my-bucket/raw/",
      "--output_path": "s3://my-bucket/processed/",
    },
  })
);
console.log(jobRun.JobRunId);

// Start a crawler
await glue.send(
  new StartCrawlerCommand({ Name: "my-data-crawler" })
);

// Get data quality results
const dqResult = await glue.send(
  new GetDataQualityResultCommand({ ResultId: "dq-result-abc123" })
);
console.log(dqResult.Score); // Overall data quality score
console.log(dqResult.RuleResults); // Per-rule pass/fail
```

---

## 3. Amazon Athena

### 3.1 Overview

Amazon Athena is an **interactive, serverless** query service that analyzes data in Amazon S3 using standard SQL. It is built on Presto/Trino and integrates tightly with the Glue Data Catalog.

**Relevance to GenAI:**
- Query training datasets stored in S3 without loading them into a database
- Analyze model evaluation results, data quality outputs, and experiment metadata
- Explore and profile data before using it for fine-tuning or RAG
- Query Glue Data Quality results written to S3
- Analyze logs and metrics from ML pipeline runs

### 3.2 Key Features

- **Serverless**: No infrastructure to manage, pay per query ($5 per TB scanned)
- **S3 data lake native**: Queries data directly in S3 (Parquet, ORC, JSON, CSV, Avro, Iceberg, Hudi, Delta Lake)
- **Glue Data Catalog integration**: Uses Glue tables as the metastore
- **CTAS and INSERT INTO**: Create new tables from query results for downstream processing
- **Federated query**: Query data in other sources (DynamoDB, Redshift, RDS, OpenSearch) via Lambda connectors
- **SPICE integration**: Athena results can feed into QuickSight SPICE for visualization
- **Workgroups**: Separate users/teams, enforce cost controls, configure query result locations
- **Trusted Identity Propagation**: Supports TIP for QuickSight Direct Query

### 3.3 Athena for AI Pipelines

**Common patterns:**

**1. Profiling training data:**
```sql
SELECT
  COUNT(*) as total_rows,
  COUNT(DISTINCT category) as unique_categories,
  AVG(LENGTH(text_content)) as avg_text_length,
  SUM(CASE WHEN text_content IS NULL THEN 1 ELSE 0 END) as null_count
FROM my_genai_database.training_data
WHERE partition_date = '2024-01-15'
```

**2. Analyzing data quality results:**
```sql
SELECT
  rule_name,
  result,
  evaluation_message
FROM my_genai_database.data_quality_results
WHERE result = 'FAIL'
ORDER BY rule_name
```

**3. Querying model evaluation outputs:**
```sql
SELECT
  model_id,
  AVG(accuracy) as avg_accuracy,
  AVG(f1_score) as avg_f1,
  COUNT(*) as eval_count
FROM my_genai_database.model_evaluations
GROUP BY model_id
ORDER BY avg_accuracy DESC
```

### 3.4 Exam Gotchas -- Athena

1. **Cost optimization**: Use columnar formats (Parquet, ORC) and partitioning to reduce data scanned.
2. **Not for real-time**: Athena is for interactive analytics, not sub-second queries. Use OpenSearch for search workloads.
3. **Glue Data Catalog is the metastore**: Athena does not have its own metadata store.
4. **Federated queries**: Can query OpenSearch, DynamoDB, and other sources via Lambda connectors.
5. **$5 per TB scanned**: Optimize by partitioning, using columnar formats, and compressing data.

### 3.5 TypeScript SDK v3 -- Athena

```typescript
import {
  AthenaClient,
  StartQueryExecutionCommand,
  GetQueryExecutionCommand,
  GetQueryResultsCommand,
} from "@aws-sdk/client-athena";

const athena = new AthenaClient({ region: "us-east-1" });

// Start a query
const execution = await athena.send(
  new StartQueryExecutionCommand({
    QueryString: "SELECT * FROM training_data LIMIT 10",
    QueryExecutionContext: { Database: "my_genai_database" },
    ResultConfiguration: {
      OutputLocation: "s3://my-query-results/athena/",
    },
  })
);

// Poll for completion
let status = "RUNNING";
while (status === "RUNNING" || status === "QUEUED") {
  const check = await athena.send(
    new GetQueryExecutionCommand({
      QueryExecutionId: execution.QueryExecutionId!,
    })
  );
  status = check.QueryExecution?.Status?.State!;
  if (status === "RUNNING" || status === "QUEUED") {
    await new Promise((r) => setTimeout(r, 2000));
  }
}

// Get results
const results = await athena.send(
  new GetQueryResultsCommand({
    QueryExecutionId: execution.QueryExecutionId!,
  })
);
console.log(results.ResultSet?.Rows);
```

---

## 4. Amazon EMR

### 4.1 Overview

Amazon EMR is a **managed big data platform** for processing vast amounts of data using open-source frameworks including Apache Spark, Hive, Presto, HBase, Flink, and Hudi.

**Relevance to GenAI:**
- Large-scale data processing and feature engineering for ML
- Distributed text processing and embedding generation
- Processing terabytes of training data that exceeds Glue's practical limits
- Spark MLlib for distributed ML training

### 4.2 Architecture

| Layer | Components |
|---|---|
| **Storage** | HDFS, EMRFS (S3), Local file system |
| **Resource Management** | YARN |
| **Processing** | Spark, MapReduce, Flink, Presto |
| **Applications** | Hive, Pig, Spark SQL, MLlib, Spark Streaming |

**Node types:**
- **Primary node**: Manages cluster, coordinates distributed processing
- **Core nodes**: Run tasks + store data in HDFS (if used)
- **Task nodes**: Only run tasks, no HDFS storage -- can use Spot Instances

### 4.3 EMR for AI Data Preparation

**Common patterns:**

**Spark for distributed text processing:**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import length, col

spark = SparkSession.builder.appName("DataPrep").getOrCreate()

# Read raw training data
df = spark.read.parquet("s3://my-bucket/raw-training-data/")

# Clean and filter
cleaned = (df
  .filter(length(col("text")) > 50)
  .filter(col("language") == "en")
  .dropDuplicates(["text"])
  .repartition(100)
)

# Write processed data
cleaned.write.parquet("s3://my-bucket/processed-training-data/")
```

**Key integrations:**
- **EMRFS**: Direct S3 access, data stays in S3 (no need to copy to HDFS)
- **Glue Data Catalog**: EMR can use Glue as the Hive Metastore
- **SageMaker**: SageMaker Spark connector for distributed training/inference
- **EMR Serverless**: Run Spark/Hive jobs without managing clusters

### 4.4 EMR Serverless vs. EMR on EC2

| Feature | EMR on EC2 | EMR Serverless |
|---|---|---|
| **Management** | You manage cluster lifecycle | Serverless, auto-provisions |
| **Scaling** | Manual or managed scaling | Automatic |
| **Billing** | Per-instance-hour | Per-resource-second |
| **Best for** | Long-running, complex workloads | Short-lived, intermittent jobs |
| **Frameworks** | Spark, Hive, Presto, HBase, Flink, etc. | Spark, Hive |
| **Customization** | Full control over AMIs, bootstrap actions | Limited |

### 4.5 Exam Gotchas -- EMR

1. **EMR vs. Glue**: Both do Spark ETL. Use Glue for simpler, serverless ETL with Data Catalog integration. Use EMR for complex, large-scale processing with multiple frameworks.
2. **EMR Serverless**: Good for intermittent Spark/Hive workloads without cluster management.
3. **Anti-pattern**: Do not use EMR for small datasets that can be processed in memory on a single system.
4. **EMRFS**: Always prefer EMRFS (S3) over HDFS for storage in cloud-native architectures.
5. **Glue Data Catalog integration**: EMR can use Glue as the Hive Metastore for unified metadata.

### 4.6 TypeScript SDK v3 -- EMR

```typescript
import { EMRClient, RunJobFlowCommand } from "@aws-sdk/client-emr";

const emr = new EMRClient({ region: "us-east-1" });

const cluster = await emr.send(
  new RunJobFlowCommand({
    Name: "data-prep-cluster",
    ReleaseLabel: "emr-7.0.0",
    Instances: {
      MasterInstanceType: "m5.xlarge",
      SlaveInstanceType: "m5.2xlarge",
      InstanceCount: 5,
      KeepJobFlowAliveWhenNoSteps: false,
    },
    Applications: [{ Name: "Spark" }],
    Steps: [
      {
        Name: "Process Training Data",
        ActionOnFailure: "TERMINATE_CLUSTER",
        HadoopJarStep: {
          Jar: "command-runner.jar",
          Args: [
            "spark-submit",
            "--deploy-mode", "cluster",
            "s3://my-bucket/scripts/process_data.py",
          ],
        },
      },
    ],
    JobFlowRole: "EMR_EC2_DefaultRole",
    ServiceRole: "EMR_DefaultRole",
    LogUri: "s3://my-bucket/emr-logs/",
  })
);
console.log(cluster.JobFlowId);
```

---

## 5. Amazon Kinesis

### 5.1 Overview

Amazon Kinesis is a platform for collecting, processing, and analyzing **real-time streaming data**. It consists of several services.

**Relevance to GenAI:**
- Stream real-time data for continuous model inference
- Ingest user interactions for real-time recommendation systems
- Feed streaming data into ML pipelines for anomaly detection
- Process real-time events for RAG applications that need fresh data

### 5.2 Kinesis Data Streams vs. Data Firehose

| Feature | Kinesis Data Streams | Amazon Data Firehose |
|---|---|---|
| **Purpose** | Real-time data streaming with custom consumers | Managed ETL delivery to destinations |
| **Latency** | ~200ms (real-time) | Near real-time (60-900 second buffering) |
| **Scaling** | Manual (provisioned) or auto (on-demand) | Automatic |
| **Consumers** | Custom applications, Lambda, KCL | Built-in delivery to S3, Redshift, OpenSearch, Splunk, HTTP |
| **Data retention** | 1-365 days | No retention (deliver and done) |
| **Ordering** | Per-shard ordering via partition key | No ordering guarantee |
| **Replay** | Yes (within retention period) | No |
| **Transforms** | Custom consumer logic | Lambda transforms, format conversion (Parquet/ORC) |
| **Pricing** | Per-shard-hour or on-demand | Per-GB delivered |

### 5.3 Key Concepts

**Kinesis Data Streams:**
- **Shard**: Unit of capacity. Each shard provides 1 MB/s write, 2 MB/s read
- **Partition key**: Determines which shard a record goes to
- **Sequence number**: Unique per-record identifier within a shard
- **On-demand mode**: Automatically scales shards (default throughput: 4 MB/s write, 8 MB/s read)
- **Enhanced fan-out**: Dedicated 2 MB/s per-consumer throughput (no shared read capacity)

**Amazon Data Firehose:**
- **Delivery stream**: The core entity -- source to destination pipeline
- **Buffering**: Configurable by size (1-128 MB) and interval (60-900 seconds)
- **Dynamic partitioning**: Partition output data in S3 by key values
- **Format conversion**: Convert JSON to Parquet/ORC using Glue Data Catalog schemas
- **Destinations**: S3, Redshift, OpenSearch Service, Splunk, Datadog, MongoDB, HTTP endpoints

### 5.4 Streaming Data for AI Patterns

**Pattern 1 -- Real-time feature ingestion:**
```
User events -> Kinesis Data Streams -> Lambda -> DynamoDB (feature store) -> Model inference
```

**Pattern 2 -- Streaming into OpenSearch for RAG:**
```
Data source -> Kinesis Data Firehose -> S3 -> Glue ETL -> OpenSearch index
```

**Pattern 3 -- Real-time anomaly detection:**
```
IoT sensors -> Kinesis Data Streams -> Managed Service for Apache Flink -> Bedrock inference -> Alert
```

**Pattern 4 -- Glue Streaming ETL:**
```
Kinesis Data Streams -> Glue Streaming ETL -> S3 (Iceberg tables) -> Athena analysis
```

### 5.5 Exam Gotchas -- Kinesis

1. **Data Streams vs. Firehose**: Streams for custom processing with replay. Firehose for managed delivery to destinations.
2. **Firehose can deliver to OpenSearch Service**: Built-in destination, no custom code needed.
3. **On-demand vs. provisioned**: On-demand auto-scales shards; provisioned requires manual shard management.
4. **Data retention**: Streams retains data 1-365 days. Firehose does not retain (deliver-only).
5. **Enhanced fan-out**: Needed when multiple consumers need dedicated throughput from the same stream.
6. **Kinesis Data Firehose was renamed**: Now called "Amazon Data Firehose" -- exam may use either name.
7. **Lambda integration**: Both Streams and Firehose support Lambda for processing/transformation.

### 5.6 TypeScript SDK v3 -- Kinesis

```typescript
import {
  KinesisClient,
  PutRecordCommand,
  GetRecordsCommand,
  GetShardIteratorCommand,
} from "@aws-sdk/client-kinesis";

const kinesis = new KinesisClient({ region: "us-east-1" });

// Publish a record to Kinesis Data Streams
await kinesis.send(
  new PutRecordCommand({
    StreamName: "user-interactions",
    Data: Buffer.from(
      JSON.stringify({
        userId: "user-123",
        action: "search",
        query: "machine learning tutorials",
        timestamp: new Date().toISOString(),
      })
    ),
    PartitionKey: "user-123",
  })
);

// Firehose example
import {
  FirehoseClient,
  PutRecordCommand as FirehosePutRecordCommand,
} from "@aws-sdk/client-firehose";

const firehose = new FirehoseClient({ region: "us-east-1" });

await firehose.send(
  new FirehosePutRecordCommand({
    DeliveryStreamName: "events-to-s3",
    Record: {
      Data: Buffer.from(
        JSON.stringify({ event: "page_view", page: "/products" }) + "\n"
      ),
    },
  })
);
```

---

## 6. Amazon QuickSight

### 6.1 Overview

Amazon QuickSight is a **serverless, cloud-native BI service** that delivers interactive dashboards, pixel-perfect reports, natural language queries, and embedded analytics.

**Relevance to GenAI:**
- Visualize AI/ML metrics, model performance, and data quality results
- Use **Amazon Q in QuickSight** for natural language data exploration
- Embed AI-powered analytics into applications
- Create dashboards for monitoring RAG pipeline health

### 6.2 Amazon Q in QuickSight (Natural Language Queries)

Amazon Q in QuickSight is the **generative BI** capability that lets users interact with data using natural language.

**Capabilities:**
- **Multi-visual Q&A**: Ask questions in natural language, get rich visual answers (charts, tables, KPIs)
- **Dashboard authoring**: Build dashboards using natural language prompts
- **Executive summaries**: AI-generated summaries of dashboard insights
- **Data stories**: Generate narrative documents with visuals from natural language prompts
- **Scenario analysis**: Agentic capability for complex business problem analysis
- **Unstructured insights**: Combine insights from documents and structured databases

**How it works:**
1. User asks a natural language question in the Q interface
2. Amazon Q interprets the question, identifies relevant fields
3. If needed, invokes LLMs on Amazon Bedrock for interpretation
4. Queries the underlying dataset and generates visual answers
5. Results displayed as multi-visual answers (bar charts, KPIs, tables, trend lines)

**Topics**: Define a "Topic" in QuickSight to configure which datasets and fields are available for Q&A. Topics map business terms to data columns.

### 6.3 Key Concepts

- **SPICE**: Super-fast Parallel In-memory Calculation Engine. In-memory optimized data store for fast querying. Supports up to 2 billion rows per dataset.
- **Datasets**: Connect to data sources (Athena, Redshift, S3, RDS, etc.)
- **Analyses**: Where you build visuals
- **Dashboards**: Published, read-only versions of analyses
- **Embedded analytics**: Embed dashboards, Q&A, and authoring into applications via SDK

### 6.4 Exam Gotchas -- QuickSight

1. **Amazon Q in QuickSight**: The generative BI capability. Powered by Bedrock LLMs under the hood.
2. **SPICE**: In-memory engine, not always required (can use direct query mode for real-time data).
3. **Serverless scaling**: Auto-scales to tens of thousands of users.
4. **Pricing**: Per-session pricing for readers (pay only when they view dashboards).
5. **Data sources**: Connects to Athena, Redshift, S3, RDS, OpenSearch, and many more.
6. **Embedding SDK**: JavaScript SDK for embedding dashboards and Q&A into applications.
7. **Not a data processing tool**: QuickSight is for visualization and exploration, not ETL or transformation.

### 6.5 TypeScript SDK v3 -- QuickSight

```typescript
import {
  QuickSightClient,
  GenerateEmbedUrlForRegisteredUserCommand,
  ListDashboardsCommand,
  DescribeDataSetCommand,
} from "@aws-sdk/client-quicksight";

const qs = new QuickSightClient({ region: "us-east-1" });
const accountId = "123456789012";

// List dashboards
const dashboards = await qs.send(
  new ListDashboardsCommand({ AwsAccountId: accountId })
);
console.log(dashboards.DashboardSummaryList);

// Generate embedding URL for a registered user
const embedUrl = await qs.send(
  new GenerateEmbedUrlForRegisteredUserCommand({
    AwsAccountId: accountId,
    UserArn:
      "arn:aws:quicksight:us-east-1:123456789012:user/default/my-user",
    ExperienceConfiguration: {
      QuickSightConsole: {
        InitialPath: "/start",
      },
    },
    SessionLifetimeInMinutes: 600,
  })
);
console.log(embedUrl.EmbedUrl);
```

---

## 7. Amazon Managed Streaming for Apache Kafka (MSK)

### 7.1 Overview

Amazon MSK is a **fully managed Apache Kafka** service for building real-time streaming data pipelines and applications. It manages infrastructure provisioning, cluster operations, patching, and security.

**Relevance to GenAI:**
- Event-driven architectures for AI applications
- Real-time data ingestion pipelines for continuously updating knowledge bases
- Change data capture (CDC) for keeping RAG indexes current
- High-throughput data streaming for ML feature pipelines

### 7.2 Key Concepts

**Cluster types:**
| Type | Description |
|---|---|
| **MSK Provisioned** | You choose broker types and count. Two broker types: Express (fully managed, faster) and Standard. |
| **MSK Serverless** | Auto-scaling, pay-per-use. No broker management. |

**Core components:**
- **Topics**: Logical channels for organizing messages
- **Partitions**: Horizontal scaling within a topic
- **Producers**: Applications that publish messages
- **Consumers**: Applications that read messages
- **Consumer groups**: Coordinate message consumption across multiple consumers
- **MSK Connect**: Managed Kafka Connect for source/sink connectors (e.g., Debezium for CDC)
- **MSK Replicator**: Cross-region data replication

### 7.3 MSK for AI Architectures

**Pattern 1 -- CDC pipeline for RAG freshness:**
```
Database -> MSK Connect (Debezium) -> MSK topic -> Glue Streaming ETL -> OpenSearch index
```

**Pattern 2 -- Event-driven inference:**
```
Application events -> MSK topic -> Lambda (event source mapping) -> Bedrock inference -> Response topic
```

**Pattern 3 -- Real-time feature pipeline:**
```
Clickstream -> MSK topic -> Managed Flink -> Feature Store -> Real-time ML inference
```

**MSK + Lambda integration:**
- Lambda can consume from MSK topics via event source mapping
- Automatic partition assignment, offset tracking, and batch processing
- Supports event filtering to reduce Lambda invocations
- Supports cross-account event processing

### 7.4 MSK vs. Kinesis Data Streams

| Feature | Amazon MSK | Kinesis Data Streams |
|---|---|---|
| **Protocol** | Apache Kafka (open source) | AWS proprietary |
| **Ecosystem** | Kafka ecosystem (Connect, Streams, KSQL) | AWS ecosystem (Lambda, Firehose, Flink) |
| **Ordering** | Per-partition | Per-shard |
| **Message size** | Up to 10 MB (configurable) | Up to 1 MB |
| **Retention** | Unlimited (with tiered storage) | 1-365 days |
| **Client libraries** | Any Kafka client | AWS SDK, KCL, KPL |
| **Best for** | Existing Kafka workloads, complex event processing | AWS-native, simpler setup |
| **Pricing** | Per-broker-hour (provisioned) or per-GB (serverless) | Per-shard-hour or on-demand |

### 7.5 Exam Gotchas -- MSK

1. **MSK vs. Kinesis**: Choose MSK when you have existing Kafka expertise/code or need the Kafka ecosystem (Connect, Streams). Choose Kinesis for simpler, AWS-native streaming.
2. **MSK Serverless**: Auto-scales, no broker management -- good for variable workloads.
3. **MSK Connect**: Managed Kafka Connect for connecting to external data sources/sinks without managing infrastructure.
4. **Glue Streaming ETL**: Can read from MSK topics directly for real-time processing.
5. **Lambda integration**: Lambda can consume directly from MSK topics with event source mapping.
6. **CDC with Debezium**: Common exam pattern for keeping RAG knowledge bases current with database changes.

### 7.6 TypeScript SDK v3 -- MSK

```typescript
import {
  KafkaClient,
  ListClustersV2Command,
  GetBootstrapBrokersCommand,
} from "@aws-sdk/client-kafka";

const msk = new KafkaClient({ region: "us-east-1" });

// List MSK clusters
const clusters = await msk.send(new ListClustersV2Command({}));
console.log(clusters.ClusterInfoList);

// Get bootstrap brokers for client connection
const brokers = await msk.send(
  new GetBootstrapBrokersCommand({
    ClusterArn:
      "arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster/abc-123",
  })
);
console.log(brokers.BootstrapBrokerStringSaslIam); // IAM auth endpoint
```

For actual Kafka produce/consume operations, use a Kafka client library (e.g., `kafkajs`) rather than the AWS SDK:

```typescript
import { Kafka } from "kafkajs";

const kafka = new Kafka({
  clientId: "my-genai-app",
  brokers: ["broker1:9098", "broker2:9098"],
  ssl: true,
  sasl: {
    mechanism: "aws",
    authorizationIdentity: "123456789012",
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
    sessionToken: process.env.AWS_SESSION_TOKEN,
  },
});

const producer = kafka.producer();
await producer.connect();
await producer.send({
  topic: "document-updates",
  messages: [
    {
      key: "doc-456",
      value: JSON.stringify({
        action: "updated",
        documentId: "doc-456",
        content: "Updated document content for RAG indexing",
      }),
    },
  ],
});
```

---

## 8. Service Selection Quick Reference

Use this table when an exam question describes a scenario and you need to choose the right service.

| Scenario | Service |
|---|---|
| Vector database for RAG with Bedrock | **OpenSearch Serverless** (vector search collection) |
| Semantic search + keyword search combined | **OpenSearch Service** (hybrid search) |
| Validate data quality before fine-tuning | **AWS Glue Data Quality** (DQDL rules) |
| Register data sources in a metadata catalog | **AWS Glue Data Catalog** |
| Track data lineage for AI governance | **AWS Glue** (job lineage) + **Amazon DataZone** (visual lineage) |
| Query S3 data with SQL for exploration | **Amazon Athena** |
| Process terabytes of training data with Spark | **Amazon EMR** or **Glue ETL** |
| Real-time streaming into OpenSearch | **Amazon Data Firehose** (built-in OpenSearch destination) |
| Custom real-time stream processing with replay | **Kinesis Data Streams** |
| Natural language BI queries for business users | **Amazon Q in QuickSight** |
| Event-driven AI with Kafka ecosystem | **Amazon MSK** |
| CDC pipeline for keeping RAG index current | **MSK Connect** (Debezium) -> MSK -> Glue/Lambda -> OpenSearch |
| Managed delivery of streaming data to S3/Redshift | **Amazon Data Firehose** |
| Visualize model evaluation metrics | **Amazon QuickSight** |
| Large-scale batch embedding generation | **OpenSearch Ingestion** (ML batch inference) or **EMR** |
| Cost-optimized vector search at scale | **OpenSearch** disk-based vector search or quantization |

---

## 9. Key Metrics to Monitor

| Service | Key Metrics |
|---|---|
| **OpenSearch** | `KNNGraphMemoryUsage`, `SearchLatency`, `IndexingLatency`, `SearchableDocuments`, `CPUUtilization`, `JVMMemoryPressure` |
| **OpenSearch Serverless** | `SearchOCU`, `IndexingOCU`, `SearchRequestLatency`, `SearchRequestErrors` |
| **Glue** | `glue.driver.aggregate.bytesRead`, `glue.driver.aggregate.numCompletedTasks`, DPU utilization, job duration |
| **Glue Data Quality** | Data quality score, per-rule pass/fail counts, anomaly detection alerts |
| **Athena** | `TotalExecutionTime`, `DataScannedInBytes`, `QueryQueueTime` |
| **EMR** | `AppsRunning`, `AppsCompleted`, `HDFSUtilization`, `MemoryAvailableMB`, `YARNMemoryAvailablePercentage` |
| **Kinesis Data Streams** | `IncomingRecords`, `IncomingBytes`, `GetRecords.IteratorAgeMilliseconds`, `ReadProvisionedThroughputExceeded` |
| **Data Firehose** | `DeliveryToS3.Success`, `IncomingBytes`, `DeliveryToS3.DataFreshness` |
| **QuickSight** | SPICE usage, concurrent user sessions, dataset refresh status |
| **MSK** | `BytesInPerSec`, `BytesOutPerSec`, `UnderReplicatedPartitions`, `OfflinePartitionsCount`, consumer lag |
