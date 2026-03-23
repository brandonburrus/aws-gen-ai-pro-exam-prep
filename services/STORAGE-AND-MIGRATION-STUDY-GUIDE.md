# Storage and Migration Services for GenAI

**Context: AWS Certified AI Practitioner (AIP-C01) Exam**

S3 is the most exam-relevant storage service. It is the primary data source for Bedrock Knowledge
Bases, the storage layer for training data, model artifacts, prompt templates, and evaluation
datasets. EBS and EFS appear in the context of GPU instance storage and SageMaker shared file
systems. DataSync and Transfer Family cover data migration into S3 for AI workloads.

**Exam Relevance by Task:**
- Task 1.4.1: S3 document repositories for vector architectures
- Task 1.4.2: S3 object metadata for document timestamps, custom attributes
- Task 1.6.3: S3 for template repositories (prompt management)
- Task 3.2.2: S3 Lifecycle configurations for data retention

---

## Amazon S3

### 1. Overview and Key Concepts

Amazon S3 is an object storage service with effectively unlimited capacity, 99.999999999% (11
nines) durability, and 99.99% availability for Standard storage class.

**Core primitives:**

| Concept | Description |
|---|---|
| Bucket | Top-level container. Globally unique name. Region-specific. |
| Object | A file + metadata. Identified by a key (full path including prefixes). |
| Key | The full "path" to an object, e.g. `training-data/v2/corpus.jsonl` |
| Prefix | A logical grouping using the key path before the object name. Not a real folder. |
| Version ID | Unique identifier for each version of an object when versioning is enabled. |

**Key limits:**
- Object size: 0 bytes to 5 TB. Use multipart upload for objects > 100 MB (required > 5 GB).
- Bucket limit: 100 buckets per account by default (can request increase).
- No limit on the number of objects per bucket.
- Metadata per object: 2 KB of user-defined metadata in the PUT request header.
- Object tags: up to 10 key-value pairs per object.

**Storage classes (ranked by cost, highest to lowest):**
1. S3 Standard -- frequent access, low latency
2. S3 Intelligent-Tiering -- auto-tiering based on access patterns
3. S3 Standard-IA -- infrequent access, per-GB retrieval fee
4. S3 One Zone-IA -- single AZ, lower cost, lower durability
5. S3 Glacier Instant Retrieval -- archive, millisecond retrieval
6. S3 Glacier Flexible Retrieval -- archive, minutes to hours retrieval
7. S3 Glacier Deep Archive -- lowest cost, 12-48 hour retrieval

> **Exam tip:** S3 Standard is the default. All new objects are encrypted at rest with SSE-S3 by
> default since January 5, 2023. You do not need to enable encryption -- it is always on.

---

### 2. S3 as Data Source for Bedrock Knowledge Bases

S3 is the primary data source connector for Amazon Bedrock Knowledge Bases. When you create a
Knowledge Base, you point it at an S3 bucket (or prefix within a bucket) containing your source
documents.

**How it works:**
1. You upload documents (PDF, TXT, DOCX, HTML, CSV, MD, XLS, images, audio, video) to an S3
   bucket.
2. You create a Knowledge Base and configure the S3 data source connector with the bucket URI.
3. Bedrock crawls the bucket, parses documents, chunks them, generates embeddings, and stores
   vectors in the configured vector store.
4. When you call `RetrieveAndGenerate` or `Retrieve`, Bedrock queries the vector store and
   returns relevant chunks with citations to the original S3 objects.

**Key configuration details:**
- **Inclusion prefixes**: Scope the data source to a specific S3 path prefix instead of the
  entire bucket. Use this to separate training data from evaluation data from production corpora.
- **Incremental syncs**: Bedrock tracks changes since the last sync and only processes new,
  modified, or deleted content. Call `StartIngestionJob` to trigger a sync.
- **Multimodal content**: S3 data sources support images, audio, and video files for multimodal
  Knowledge Bases.
- **Only General Purpose buckets** are supported (not Directory buckets / S3 Express One Zone).
- **Bucket must be in the same Region** as the Knowledge Base.
- **DataSync integration**: You can use AWS DataSync to continuously transfer files from
  on-premises storage to the S3 bucket on a schedule.

**S3 Vectors (new feature):** S3 can also serve as the vector store itself via S3 Vectors, an
integration that lets Bedrock store embeddings directly in S3 table buckets (Apache Iceberg
tables). This reduces cost for RAG applications by eliminating the need for a separate vector
database.

**Required IAM permissions on the Knowledge Base role:**
- `s3:GetObject` on the bucket/prefix
- `s3:ListBucket` on the bucket
- If the bucket is encrypted with KMS: `kms:Decrypt` on the KMS key

```typescript
// TypeScript SDK v3 -- Create a Bedrock Knowledge Base S3 data source
import {
  BedrockAgentClient,
  CreateDataSourceCommand,
} from "@aws-sdk/client-bedrock-agent";

const client = new BedrockAgentClient({ region: "us-east-1" });

const response = await client.send(
  new CreateDataSourceCommand({
    knowledgeBaseId: "KB_ID",
    name: "product-docs-source",
    dataSourceConfiguration: {
      type: "S3",
      s3Configuration: {
        bucketArn: "arn:aws:s3:::my-knowledge-base-docs",
        inclusionPrefixes: ["product-manuals/"],
      },
    },
  })
);
```

> **Exam tip:** If a question asks about the most cost-effective way to keep a Knowledge Base
> current with on-premises document changes, the answer is DataSync to S3 + incremental sync.

---

### 3. Object Metadata for GenAI (Timestamps, Custom Attributes, Tagging)

S3 objects have two types of metadata that are directly relevant to GenAI workloads:

#### System-Defined Metadata

Automatically maintained by S3. Key headers include:
- `Content-Type` -- MIME type (e.g., `application/pdf`)
- `Content-Length` -- size in bytes
- `Last-Modified` -- timestamp of last modification
- `ETag` -- entity tag (hash of the object)
- `x-amz-storage-class` -- current storage class
- `x-amz-server-side-encryption` -- encryption algorithm used
- `x-amz-version-id` -- version identifier (if versioning enabled)

#### User-Defined Metadata

Custom key-value pairs set at upload time. Must be prefixed with `x-amz-meta-`. Limited to 2 KB
total in the PUT request header. Cannot be modified after upload -- you must copy the object to
change metadata.

#### Object Tags

Key-value pairs (up to 10 per object) that can be added, modified, or removed after upload.
Tags are case-sensitive. Max key length: 128 Unicode chars. Max value length: 256 Unicode chars.

**GenAI use cases for metadata and tags:**

| Use Case | Mechanism |
|---|---|
| Filter Knowledge Base results by date | `.metadata.json` file with `created_date` attribute |
| Track document source/author | `.metadata.json` file with custom attributes |
| Control Lifecycle transitions | Tags + Lifecycle rules based on tag filters |
| Cost allocation for AI projects | Tags for cost tracking |
| ABAC (attribute-based access control) | Tags in IAM policy conditions |
| Data governance classification | Tags for sensitivity levels |

#### Bedrock Knowledge Base Metadata Files

This is critical for the exam. For each document in your S3 data source, you can create a
companion metadata file that Bedrock uses for filtering during retrieval.

**File naming convention:** `<document-name>.<extension>.metadata.json`

For example, for `product-manual.pdf`, the metadata file is `product-manual.pdf.metadata.json`.

**File location:** Same folder as the source document.

**File format:**
```json
{
  "metadataAttributes": {
    "company": {
      "value": {
        "type": "STRING",
        "stringValue": "Acme Corp"
      },
      "includeForEmbedding": true
    },
    "created_date": {
      "value": {
        "type": "NUMBER",
        "numberValue": 20240115
      },
      "includeForEmbedding": true
    },
    "category": {
      "value": {
        "type": "STRING",
        "stringValue": "user-guide"
      },
      "includeForEmbedding": false
    }
  }
}
```

**Key rules:**
- Max metadata file size: 10 KB
- Supported types: STRING, NUMBER, BOOLEAN
- `includeForEmbedding: true` means the attribute value is included in the text chunk before
  embedding, which influences semantic search relevance
- `includeForEmbedding: false` means the attribute is only available for explicit filtering in
  retrieval queries, not embedded

**S3 Metadata (general availability):** A newer feature that automatically captures and stores
metadata from objects as they are uploaded, making it queryable in Apache Iceberg tables stored
in S3 Tables. This supports both system-defined and custom metadata and integrates with Athena,
Redshift, and QuickSight for analytics.

```typescript
// TypeScript SDK v3 -- Upload an object with user-defined metadata and tags
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: "us-east-1" });

await s3.send(
  new PutObjectCommand({
    Bucket: "my-knowledge-base-docs",
    Key: "product-manuals/manual-v2.pdf",
    Body: fileBuffer,
    ContentType: "application/pdf",
    Metadata: {
      // These become x-amz-meta-* headers
      "document-version": "2.0",
      author: "engineering-team",
    },
    Tagging: "project=genai-chatbot&environment=production",
  })
);
```

> **Exam tip:** User-defined metadata (`x-amz-meta-*`) is immutable after upload. Tags are
> mutable. Bedrock Knowledge Base metadata uses a separate `.metadata.json` sidecar file, not
> S3 user-defined metadata or tags directly.

---

### 4. S3 Lifecycle Policies for AI Data Retention

S3 Lifecycle configurations automate the transition of objects between storage classes and their
eventual deletion. This is directly referenced in Task 3.2.2 for data retention compliance.

**Lifecycle rule actions:**
1. **Transition actions** -- move objects to a cheaper storage class after N days
2. **Expiration actions** -- delete objects after N days
3. **Noncurrent version expiration** -- delete old versions after N days (requires versioning)
4. **Abort incomplete multipart uploads** -- clean up partial uploads after N days

**Lifecycle rule filters:**
- **Prefix filter** -- apply to objects matching a key prefix
- **Tag filter** -- apply to objects matching specific tags
- **Object size filter** -- apply to objects within a size range
- **AND combination** -- combine prefix, tags, and size filters

**AI data retention patterns:**

| Data Type | Lifecycle Strategy |
|---|---|
| Raw training data | Transition to S3-IA after 90 days, Glacier after 365 days |
| Model artifacts | Keep in Standard for active deployment, S3-IA after model is retired |
| Evaluation datasets | Retain in Standard for 30 days, then S3-IA, expire after compliance period |
| Inference logs | Transition to S3-IA after 30 days, Glacier after 90 days, expire per policy |
| Prompt templates (active) | Keep in Standard (frequently accessed) |
| Knowledge Base source docs | Match retention to document refresh cadence |
| Intermediate embeddings | Expire after reprocessing or retain for audit |

**Transition waterfall constraints:**
- Cannot transition from S3 Standard-IA to S3 One Zone-IA
- Minimum 30 days before transitioning from Standard to Standard-IA or One Zone-IA
- Minimum 30 days in Standard-IA or One Zone-IA before transitioning to Glacier classes
- Minimum storage duration charges: Standard-IA (30 days), Glacier Instant (90 days), Glacier
  Flexible (90 days), Glacier Deep Archive (180 days)

```typescript
// TypeScript SDK v3 -- Set a Lifecycle configuration on a bucket
import {
  S3Client,
  PutBucketLifecycleConfigurationCommand,
} from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: "us-east-1" });

await s3.send(
  new PutBucketLifecycleConfigurationCommand({
    Bucket: "my-ai-data-bucket",
    LifecycleConfiguration: {
      Rules: [
        {
          ID: "archive-training-data",
          Status: "Enabled",
          Filter: {
            Prefix: "training-data/",
          },
          Transitions: [
            { Days: 90, StorageClass: "STANDARD_IA" },
            { Days: 365, StorageClass: "GLACIER" },
          ],
        },
        {
          ID: "expire-inference-logs",
          Status: "Enabled",
          Filter: {
            Tag: { Key: "data-type", Value: "inference-log" },
          },
          Transitions: [
            { Days: 30, StorageClass: "STANDARD_IA" },
            { Days: 90, StorageClass: "GLACIER" },
          ],
          Expiration: { Days: 730 },
        },
        {
          ID: "cleanup-multipart-uploads",
          Status: "Enabled",
          Filter: { Prefix: "" },
          AbortIncompleteMultipartUpload: { DaysAfterInitiation: 7 },
        },
      ],
    },
  })
);
```

> **Exam tip:** Lifecycle rules use the object creation date (or last modified date for
> versioned objects) as the reference point for transition timing. Objects replicated via CRR
> honor the original creation time, not the replication time.

---

### 5. S3 Intelligent-Tiering for AI Data Cost Optimization

S3 Intelligent-Tiering automatically moves objects between access tiers based on access patterns,
with no retrieval charges and no operational overhead. This is the recommended storage class for
data with unpredictable or changing access patterns.

**Access tiers (automatic):**

| Tier | Trigger | Savings |
|---|---|---|
| Frequent Access (FA) | Default tier on upload | Baseline |
| Infrequent Access (IA) | No access for 30 consecutive days | ~40% |
| Archive Instant Access (AIA) | No access for 90 consecutive days | ~68% |

**Optional archive tiers (must be enabled):**

| Tier | Trigger | Savings | Retrieval Time |
|---|---|---|---|
| Archive Access | No access for 90+ days (configurable, min 90) | ~71% | 3-5 hours |
| Deep Archive Access | No access for 180+ days (configurable, min 180) | ~95% | 12 hours |

**How it works:**
- A small monthly monitoring and automation charge per object (no minimum object size).
- Objects are automatically moved to lower-cost tiers when not accessed.
- When accessed, objects move back to Frequent Access at no additional charge.
- No retrieval fees for Frequent, Infrequent, and Archive Instant tiers.
- Objects in Archive or Deep Archive tiers require a restore before access (async).

**AI workload fit:**
- Training datasets accessed heavily during training, then rarely afterward
- Evaluation datasets used periodically during model iteration
- Knowledge Base source documents that may not be re-crawled frequently
- Historical inference logs needed for occasional auditing

**Monitoring:**
- S3 Inventory reports include the Intelligent-Tiering access tier for each object.
- S3 Event Notifications fire when objects move to Archive or Deep Archive tiers.
- HEAD requests return the `x-amz-archive-status` header for archived objects.

```typescript
// TypeScript SDK v3 -- Upload an object directly to Intelligent-Tiering
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: "us-east-1" });

await s3.send(
  new PutObjectCommand({
    Bucket: "my-ai-data-bucket",
    Key: "datasets/evaluation-set-q4.jsonl",
    Body: dataBuffer,
    StorageClass: "INTELLIGENT_TIERING",
  })
);
```

```typescript
// TypeScript SDK v3 -- Enable optional archive tiers via Intelligent-Tiering configuration
import {
  S3Client,
  PutBucketIntelligentTieringConfigurationCommand,
} from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: "us-east-1" });

await s3.send(
  new PutBucketIntelligentTieringConfigurationCommand({
    Bucket: "my-ai-data-bucket",
    Id: "archive-old-training-data",
    IntelligentTieringConfiguration: {
      Id: "archive-old-training-data",
      Status: "Enabled",
      Tierings: [
        { AccessTier: "ARCHIVE_ACCESS", Days: 90 },
        { AccessTier: "DEEP_ARCHIVE_ACCESS", Days: 180 },
      ],
      Filter: {
        Prefix: "training-data/",
      },
    },
  })
);
```

> **Exam tip:** Intelligent-Tiering is the best answer when a question describes "unpredictable
> access patterns" or "optimize costs without managing storage classes manually." It has no
> retrieval fees for the three automatic tiers. If the question mentions "known infrequent
> access," Standard-IA is cheaper (no monitoring fee).

---

### 6. S3 Cross-Region Replication (CRR) for Global AI Deployments

CRR automatically replicates objects from a source bucket to one or more destination buckets in
different AWS Regions. This supports global AI deployments, disaster recovery, and compliance.

**Requirements:**
- Versioning must be enabled on both source and destination buckets.
- Source and destination must be in different Regions (same Region = SRR).
- An IAM role must grant S3 permission to replicate objects.
- In cross-account scenarios, the destination bucket policy must allow the source role.

**Replication scope:**
- **Entire bucket** or **filtered by prefix** or **filtered by object tags**
- New objects only (by default) -- use S3 Batch Replication for existing objects.
- Metadata, tags, and ACLs are replicated.
- Encrypted objects (SSE-S3, SSE-KMS) can be replicated with proper KMS configuration.

**Replication Time Control (S3 RTC):**
- SLA: 99.99% of objects replicated within 15 minutes.
- Includes CloudWatch metrics for monitoring replication progress.
- Adds cost but guarantees compliance with replication time requirements.

**Bi-directional (two-way) replication:**
- Both buckets are source and destination.
- Enables shared datasets across Regions.
- Requires Replica Modification Sync to keep metadata changes in sync.

**AI deployment patterns with CRR:**

| Pattern | Description |
|---|---|
| Global Knowledge Base | Replicate source docs to buckets in each Region where Bedrock runs |
| DR for training data | Replicate training corpora to a backup Region |
| Multi-region inference | Replicate model artifacts and prompt templates closer to users |
| Data sovereignty | Replicate data to Regions that meet regulatory requirements |
| Latency reduction | Keep data co-located with the compute that processes it |

**Key considerations:**
- CRR does not replicate objects that existed before the replication rule was created. Use S3
  Batch Replication to backfill.
- Delete markers are replicated by default (can be disabled).
- Lifecycle actions on the source are NOT replicated. Each bucket needs its own Lifecycle rules.
- There are inter-Region data transfer charges for CRR.
- Replicating objects in Intelligent-Tiering with Batch Replication or CopyObject causes tier-up
  of the source object (it gets accessed).

```typescript
// TypeScript SDK v3 -- Configure Cross-Region Replication
import { S3Client, PutBucketReplicationCommand } from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: "us-east-1" });

await s3.send(
  new PutBucketReplicationCommand({
    Bucket: "my-source-bucket",
    ReplicationConfiguration: {
      Role: "arn:aws:iam::123456789012:role/S3ReplicationRole",
      Rules: [
        {
          ID: "replicate-knowledge-base-docs",
          Status: "Enabled",
          Filter: {
            Prefix: "knowledge-base/",
          },
          Destination: {
            Bucket: "arn:aws:s3:::my-destination-bucket-eu-west-1",
            StorageClass: "STANDARD",
            EncryptionConfiguration: {
              ReplicaKmsKeyID:
                "arn:aws:kms:eu-west-1:123456789012:key/dest-key-id",
            },
          },
          SourceSelectionCriteria: {
            SseKmsEncryptedObjects: {
              Status: "Enabled",
            },
          },
          DeleteMarkerReplication: {
            Status: "Enabled",
          },
        },
      ],
    },
  })
);
```

> **Exam tip:** If a question asks about serving a Knowledge Base to users in multiple Regions,
> the answer involves CRR to replicate source documents + a Knowledge Base in each Region.
> Multi-Region Access Points can simplify the endpoint but still require CRR underneath.

---

### 7. S3 Encryption

All S3 objects are encrypted at rest by default. There are four server-side encryption options
and one client-side option.

#### Server-Side Encryption Options

| Method | Key Management | When to Use |
|---|---|---|
| SSE-S3 (AES-256) | AWS manages keys entirely | Default. No additional cost. Good for most workloads. |
| SSE-KMS | AWS KMS manages keys (AWS managed or customer managed) | Need audit trail, key rotation control, or cross-account access control |
| DSSE-KMS | Dual-layer encryption with KMS | Compliance requiring two layers of encryption |
| SSE-C | Customer provides keys per request | You manage your own key material. Must use HTTPS. |

**SSE-S3 (default):**
- Applied automatically since January 5, 2023.
- Uses AES-256.
- No additional cost, no configuration needed.

**SSE-KMS:**
- Uses AWS KMS for key management.
- **AWS managed key** (`aws/s3`): Automatic, no per-key cost, but cannot be shared cross-account.
- **Customer managed key (CMK)**: Full control over key policy, rotation, and audit via
  CloudTrail. Required for cross-account access to encrypted objects.
- **S3 Bucket Keys**: Reduces KMS API call costs by up to 99%. Generates a bucket-level key from
  the KMS key, which then creates data keys for individual objects. Enable this when using
  SSE-KMS at scale.
- Every GET/PUT for SSE-KMS objects must use HTTPS and valid AWS credentials.
- Encryption context: defaults to bucket ARN, can be customized.

**SSE-C:**
- You provide the encryption key with each PUT/GET request via HTTPS headers.
- S3 does not store your key. If you lose it, you lose the data.
- Being deprecated for new buckets starting April 2026.

**Client-Side Encryption:**
- You encrypt data before uploading. S3 stores the ciphertext.
- You manage all key material and encryption/decryption logic.
- Use the AWS Encryption SDK or S3 Encryption Client.

**Encryption for Bedrock Knowledge Bases:**
- S3 data sources can be encrypted with SSE-S3 or SSE-KMS.
- If using SSE-KMS with a customer managed key, the Knowledge Base IAM role needs `kms:Decrypt`
  permission on that key.
- The Knowledge Base itself can have a separate KMS key for server-side encryption of its
  configuration.

```typescript
// TypeScript SDK v3 -- Upload with SSE-KMS using a customer managed key
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: "us-east-1" });

await s3.send(
  new PutObjectCommand({
    Bucket: "my-secure-bucket",
    Key: "training-data/sensitive-corpus.jsonl",
    Body: dataBuffer,
    ServerSideEncryption: "aws:kms",
    SSEKMSKeyId: "arn:aws:kms:us-east-1:123456789012:key/my-cmk-id",
    BucketKeyEnabled: true,
  })
);
```

> **Exam tip:** SSE-S3 is always on by default. Use SSE-KMS with a customer managed key when
> you need: (1) cross-account sharing of encrypted objects, (2) key rotation control, (3)
> CloudTrail audit of key usage, or (4) separation of duties between key admins and data admins.
> Enable S3 Bucket Keys to reduce KMS costs at scale.

---

### 8. S3 Event Notifications for AI Pipelines

S3 event notifications trigger downstream processing when objects are created, deleted, or
transitioned. This is the foundation of event-driven AI pipelines.

**Supported event types (key subset):**
- `s3:ObjectCreated:*` -- any object creation (PUT, POST, COPY, multipart)
- `s3:ObjectRemoved:*` -- any object deletion
- `s3:ObjectRestore:*` -- object restored from Glacier
- `s3:LifecycleExpiration:*` -- object expired by Lifecycle rule
- `s3:LifecycleTransition` -- object transitioned to another storage class
- `s3:IntelligentTiering` -- object moved to Archive or Deep Archive tier
- `s3:ObjectTagging:*` -- tags added or deleted
- `s3:Replication:*` -- replication events

**Notification destinations:**
1. **Amazon SNS** -- fan-out to multiple subscribers
2. **Amazon SQS** -- queue for decoupled processing (FIFO not supported)
3. **AWS Lambda** -- direct function invocation
4. **Amazon EventBridge** -- advanced filtering, routing, and transformation

**EventBridge integration (recommended for new designs):**
- Must be explicitly enabled on the bucket.
- Provides richer filtering (by prefix, suffix, object size, metadata).
- Supports rule-based routing to 20+ target services.
- Supports archive and replay of events.
- Supports schema discovery.

**AI pipeline patterns:**

```
S3 upload --> EventBridge --> Step Functions --> [Parse, Chunk, Embed, Index]
S3 upload --> Lambda --> StartIngestionJob (Bedrock KB sync)
S3 upload --> SQS --> SageMaker Processing Job
S3 upload --> SNS --> Lambda (thumbnail) + SQS (metadata extraction)
```

> **Exam tip:** Use EventBridge (not direct SNS/SQS/Lambda) when you need advanced filtering,
> multiple targets, or event replay. EventBridge must be explicitly enabled per bucket.
> SQS FIFO queues are NOT supported as S3 event notification destinations.

---

### 9. S3 Select for Efficient Data Retrieval

S3 Select lets you use SQL expressions to retrieve a subset of data from an S3 object without
downloading the entire object. This reduces data transfer and speeds up retrieval for large files.

**Supported formats:** CSV, JSON, Apache Parquet

**Key limits:**
- Max object size: 5 TB
- Max SQL expression: 256 KB
- Max record length: 1 MB
- Console limit: 40 MB per query (no limit via API/CLI)
- Not available for objects in Glacier storage classes
- Not available for SSE-C encrypted objects

**Use cases in GenAI:**
- Extract specific columns from large CSV training datasets
- Filter JSON inference logs by timestamp or model ID
- Sample rows from Parquet evaluation datasets
- Pre-filter data before feeding into SageMaker Processing jobs

**Note:** S3 Select is no longer available to new customers as of 2024. Existing customers can
continue using it. For new workloads, consider Amazon Athena or S3 Object Lambda as alternatives.

> **Exam tip:** If a question asks about querying data "in place" in S3 without downloading,
> the modern answer is Amazon Athena. S3 Select may still appear in legacy-oriented questions.

---

### 10. Versioning for AI Artifacts

S3 versioning preserves every version of every object in a bucket. Once enabled, it cannot be
disabled -- only suspended.

**States:**
- **Unversioned** (default) -- objects have a null version ID
- **Versioning-enabled** -- every PUT creates a new version with a unique version ID
- **Versioning-suspended** -- new PUTs get a null version ID, existing versions are preserved

**AI artifact versioning patterns:**
- **Model artifacts**: Version model weights, configuration files, and tokenizers. Roll back to a
  previous model version if the new one degrades.
- **Training datasets**: Track dataset versions. Reproduce training runs by referencing specific
  version IDs.
- **Prompt templates**: Version prompt templates for A/B testing and rollback.
- **Evaluation datasets**: Maintain versioned benchmark datasets for consistent model comparison.

**Key behaviors:**
- DELETE on a versioned object creates a delete marker (soft delete). The object is still
  recoverable by version ID.
- MFA Delete adds another layer of protection -- requires MFA to permanently delete versions or
  change versioning state. Only the root account can enable MFA Delete.
- Lifecycle rules can target noncurrent versions for expiration (clean up old versions after N
  days).

**Versioning is required for CRR and SRR.**

```typescript
// TypeScript SDK v3 -- Enable versioning on a bucket
import {
  S3Client,
  PutBucketVersioningCommand,
} from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: "us-east-1" });

await s3.send(
  new PutBucketVersioningCommand({
    Bucket: "my-ai-artifacts-bucket",
    VersioningConfiguration: {
      Status: "Enabled",
    },
  })
);
```

> **Exam tip:** Versioning cannot be disabled, only suspended. Suspending versioning does not
> delete existing versions. CRR requires versioning on both source and destination buckets.

---

### 11. Access Control

S3 provides multiple layers of access control. The exam expects you to know when to use each.

#### Bucket Policies (most common)

JSON resource-based policies attached to a bucket. Use for:
- Granting cross-account access
- Enforcing encryption requirements
- Restricting access by IP, VPC endpoint, or source ARN
- Requiring HTTPS/TLS

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RequireKMSEncryption",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::my-bucket/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}
```

#### IAM Policies

Identity-based policies attached to IAM users, roles, or groups. Use for:
- Controlling what actions a specific role (e.g., a Bedrock Knowledge Base role) can perform
- Implementing least-privilege access per service or application

#### S3 Access Points

Named network endpoints with distinct permissions policies. Use for:
- Simplifying access management for shared datasets
- Providing different access policies for different teams (data science, ML engineering, audit)
- VPC-restricted access points

#### S3 Block Public Access

Account-level and bucket-level settings that override any policy granting public access. Always
enable this for AI workloads.

#### ACLs (legacy)

S3 ACLs are legacy. AWS recommends disabling ACLs (bucket owner enforced) for all new buckets.
This makes the bucket owner the sole owner of all objects regardless of who uploaded them.

#### S3 Object Lambda

Transforms data as it is retrieved from S3. Use cases: PII redaction before returning data to
a model, format conversion, watermarking AI-generated content.

> **Exam tip:** For Bedrock Knowledge Bases, the most common access pattern is an IAM role with
> `s3:GetObject` and `s3:ListBucket` plus a bucket policy allowing that role. For cross-account
> Knowledge Bases, the bucket policy must explicitly grant the KB role from the other account.

---

### 12. Template Repositories for Prompt Management

Task 1.6.3 references S3 as a storage location for prompt templates.

**Patterns:**
- Store prompt templates as versioned JSON or YAML files in S3 with a clear prefix structure:
  `prompts/{use-case}/{version}/template.json`
- Use S3 versioning to track template changes over time.
- Use object tags to categorize templates: `model=claude-v3`, `task=summarization`,
  `status=active`.
- Use Lifecycle rules to archive deprecated templates.
- Use S3 event notifications to trigger template validation/deployment pipelines when new
  templates are uploaded.

**Bedrock Prompt Management** stores managed prompts in the service, but S3 serves as the
backing store for custom prompt management systems and for prompt templates used in custom
orchestration code.

```typescript
// TypeScript SDK v3 -- Retrieve a versioned prompt template from S3
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";

const s3 = new S3Client({ region: "us-east-1" });

const response = await s3.send(
  new GetObjectCommand({
    Bucket: "my-prompt-templates",
    Key: "prompts/summarization/v3/template.json",
    VersionId: "specific-version-id-for-reproducibility",
  })
);

const template = JSON.parse(await response.Body!.transformToString());
```

---

### S3 Key Metrics for Monitoring

| Metric | Source | What It Tells You |
|---|---|---|
| `BucketSizeBytes` | CloudWatch (daily) | Total storage size per storage class |
| `NumberOfObjects` | CloudWatch (daily) | Object count (track dataset growth) |
| `AllRequests` | S3 request metrics | Total API calls (monitor pipeline activity) |
| `4xxErrors` / `5xxErrors` | S3 request metrics | Access issues / service errors |
| `FirstByteLatency` | S3 request metrics | Time to first byte (performance) |
| `ReplicationLatency` | CRR metrics | Time for object to replicate to destination |
| `BytesPendingReplication` | CRR metrics | Replication backlog |
| S3 Storage Lens | Dashboard | Org-wide visibility into usage, cost, security posture |

---

## Amazon EBS

### 1. Block Storage for EC2/GPU Instances

Amazon Elastic Block Store provides block-level storage volumes for EC2 instances, including
GPU instances used for ML training and inference (P4d, P5, G5, Inf2, Trn1).

**Key characteristics:**
- Attached to a single EC2 instance (except io2 with multi-attach).
- Persist independently from instance lifecycle (unlike instance store).
- Exist within a single Availability Zone.
- Snapshot to S3 for backup and cross-Region copy.

**When to use EBS for AI:**
- Root volumes for SageMaker notebook instances and EC2-based training.
- High-IOPS storage for model checkpoint writing during training.
- Local cache for model weights on inference instances.
- Scratch space for data preprocessing on GPU instances.

### 2. Volume Types for AI Workloads

| Volume Type | Max IOPS | Max Throughput | Durability | AI Use Case |
|---|---|---|---|---|
| **gp3** | 16,000 | 1,000 MiB/s | 99.8-99.9% | Default for most workloads. Notebooks, general training. |
| **gp2** | 16,000 | 250 MiB/s | 99.8-99.9% | Legacy. Prefer gp3 (same price, better baseline). |
| **io2 Block Express** | 256,000 | 4,000 MiB/s | 99.999% | Large model checkpoint I/O, high-throughput training. |
| **io1** | 64,000 | 1,000 MiB/s | 99.999% | Provisioned IOPS for latency-sensitive inference. |
| **st1** | 500 | 500 MiB/s | 99.8-99.9% | Sequential reads of large training datasets. |
| **sc1** | 250 | 250 MiB/s | 99.8-99.9% | Cold storage for infrequently accessed data. |

**gp3 vs gp2:** gp3 has independently configurable IOPS (up to 16,000) and throughput (up to
1,000 MiB/s) at no additional cost above the baseline 3,000 IOPS / 125 MiB/s. gp2 ties IOPS
to volume size (3 IOPS per GiB, burst to 3,000). Always prefer gp3 for new workloads.

**io2 Block Express:** The highest-performance EBS option. Use for training jobs that write
frequent, large checkpoints and need consistent sub-millisecond latency. Supports multi-attach
for shared access from up to 16 Nitro instances in the same AZ.

### 3. Snapshots for Model Artifacts

EBS snapshots are incremental, point-in-time copies stored in S3 (managed by AWS).

**AI use cases:**
- Snapshot a volume containing a fine-tuned model before deploying to production.
- Copy snapshots cross-Region for DR.
- Create AMIs with pre-loaded model weights for faster instance launch.
- Use Amazon Data Lifecycle Manager to automate snapshot creation/retention/deletion.

**Key behaviors:**
- First snapshot captures the entire volume. Subsequent snapshots are incremental.
- Snapshots can be shared cross-account or made public.
- Snapshots can be encrypted (and copied to a different KMS key).
- Use `fast snapshot restore` to eliminate the first-access latency penalty on volumes created
  from snapshots.

> **Exam tip:** If a question asks about the fastest boot time for an inference instance with a
> large model pre-loaded, the answer is an AMI backed by an EBS snapshot with fast snapshot
> restore enabled. For the highest IOPS for training checkpoints, use io2 Block Express.

---

## Amazon EFS

### 1. Shared File System for SageMaker

Amazon Elastic File System is a fully managed, elastic NFS file system that can be mounted by
multiple EC2 instances, containers, and Lambda functions concurrently.

**Key characteristics:**
- POSIX-compliant (NFS v4.1).
- Elastic -- grows and shrinks automatically, no provisioning needed.
- Regional (Standard) or single-AZ (One Zone) deployment.
- 99.999999999% (11 nines) durability for Standard storage class.
- Supports encryption at rest (KMS) and in transit (TLS).

**SageMaker integration:**
- SageMaker training jobs can read input data from EFS using `FileSystemDataSource` with
  `FileSystemType: "EFS"` and `FileSystemAccessMode: "ro"` (read-only) or `"rw"` (read-write).
- SageMaker Studio can mount custom EFS file systems for shared notebooks and datasets across
  team members.
- EFS is ideal for datasets that are updated frequently and need to be available to multiple
  concurrent training jobs without copying.

**SageMaker data input modes comparison:**

| Mode | Source | Startup Latency | Best For |
|---|---|---|---|
| File mode | S3 | High (downloads first) | Small/medium datasets |
| Fast file mode | S3 | Low (streams on demand) | Large datasets, sequential reads |
| Pipe mode | S3 | Low (named pipes) | Legacy streaming |
| EFS / FSx | File system | None (already mounted) | Shared datasets, iterative training |

### 2. Lambda + EFS Integration for Large Models

Lambda functions can mount EFS file systems for access to files larger than the 512 MB `/tmp`
limit or the 250 MB deployment package limit.

**Use cases for GenAI:**
- Store large ML model files (ONNX, PyTorch) on EFS and load them in Lambda for inference.
- Share embedding caches across Lambda invocations.
- Store large prompt template libraries that exceed deployment package limits.

**Requirements:**
- Lambda must be in a VPC with subnets that can route NFS traffic (port 2049) to EFS mount
  targets.
- Lambda execution role needs `elasticfilesystem:ClientMount` and
  `elasticfilesystem:ClientWrite` permissions.
- Use EFS Access Points to control the POSIX user/group and root directory per function.
- Use at least two AZs for availability.

### 3. Throughput Modes for AI Workloads

| Mode | Behavior | AI Use Case |
|---|---|---|
| **Elastic** (default) | Auto-scales up to 10 GiB/s read, 3 GiB/s write | Spiky training workloads, variable model loading |
| **Provisioned** | User-specified throughput regardless of storage size | Known sustained throughput needs (e.g., continuous data ingestion) |
| **Bursting** | Throughput scales with storage size, burst credits | Small file systems with periodic high-throughput needs |

**Performance modes:**
- **General Purpose** (default): Lowest per-operation latency. Use for most AI workloads.
- **Max I/O**: Higher throughput for highly parallelized workloads. Higher latencies. Previous
  generation -- consider Elastic throughput + General Purpose instead.

**EFS storage classes:**
- Standard -- frequently accessed files
- Infrequent Access (IA) -- lower cost, per-access charge
- EFS Lifecycle Management automatically transitions files to IA after a configurable period
  (7, 14, 30, 60, 90, 180, 270, or 365 days).

> **Exam tip:** EFS Elastic throughput is the best default for ML workloads because training
> jobs create bursty I/O patterns. Use Provisioned throughput only if you consistently need
> more throughput than what Elastic provides for your file system size. EFS is the answer when
> multiple SageMaker training jobs or Lambda functions need concurrent access to the same data.

---

## AWS DataSync

### 1. Data Migration for AI Datasets

AWS DataSync is an online data transfer service that simplifies and accelerates moving data
between on-premises storage, edge locations, other clouds, and AWS storage services.

**Key features:**
- Transfers data up to 10x faster than open-source tools.
- Handles encryption, data integrity validation, network optimization automatically.
- Supports NFS, SMB, HDFS, and object storage protocols on-premises.
- Transfers to/from S3, EFS, FSx for Windows, FSx for Lustre, FSx for OpenZFS, FSx for ONTAP.
- Supports scheduled transfers (e.g., daily sync of new training data).
- Supports filtering by file name pattern, size, or modification time.
- Preserves file metadata and permissions.
- Pay-per-GB transferred.

**Architecture:**
- Deploy a DataSync agent on-premises (as a VM) near the source storage.
- Agent connects to the DataSync service over the internet or AWS Direct Connect.
- For cloud-to-cloud transfers (e.g., S3 in one Region to S3 in another), no agent is needed.

**AI data migration patterns:**

| Pattern | How |
|---|---|
| Initial dataset migration | Deploy agent on-prem, schedule full sync to S3 |
| Continuous data ingestion | Schedule recurring DataSync tasks (e.g., every 6 hours) |
| Knowledge Base population | Sync document repositories from on-prem file servers to S3 |
| Cross-Region dataset copy | S3-to-S3 transfer across Regions (agentless) |
| Hybrid training | Sync training data to S3, then use SageMaker fast file mode |

### 2. On-Premises to S3 Transfer

**Setup steps:**
1. Deploy the DataSync agent VM in your on-premises environment.
2. Activate the agent in the AWS console (connects via port 443).
3. Create a source location (NFS/SMB/HDFS path on-premises).
4. Create a destination location (S3 bucket + prefix).
5. Create a task linking source to destination with transfer options.
6. Run the task manually or on a schedule.

**Transfer options:**
- Verify data integrity (checksums).
- Preserve file metadata (timestamps, permissions, ownership).
- Filter files by include/exclude patterns.
- Configure bandwidth throttling.
- Choose handling of deleted files (preserve or delete at destination).

**Cross-account transfers:**
- The DataSync IAM role in the source account needs permissions on the destination S3 bucket.
- The destination bucket policy must grant the DataSync role from the source account.
- ACLs must be disabled on the destination bucket.

> **Exam tip:** DataSync is the answer when a question describes migrating large datasets from
> on-premises to S3 for AI training. For one-time large transfers where network bandwidth is
> limited, AWS Snow Family (Snowball) is the answer. DataSync is for ongoing/repeated transfers
> over the network.

---

## AWS Transfer Family

### 1. SFTP/FTPS for Data Ingestion

AWS Transfer Family provides fully managed file transfer endpoints using standard protocols:
SFTP, FTPS, FTP, and AS2. Files land directly in S3 or EFS.

**Key features:**
- No infrastructure to manage -- fully managed, HA, multi-AZ.
- Supports multiple identity providers: service-managed, AWS Managed Microsoft AD, custom
  (Lambda-backed for integration with LDAP, Okta, etc.).
- Files stored natively in S3 (or EFS).
- Integrates with IAM, KMS, CloudTrail, CloudWatch for security and monitoring.
- Supports managed workflows for post-upload processing (decrypt, tag, copy, invoke Lambda).

**Protocols:**

| Protocol | Port | Encryption | Notes |
|---|---|---|---|
| SFTP | 22 | SSH | Most common. Publicly accessible or VPC-hosted. |
| FTPS | 990/21 | TLS | FTP over TLS. NAT/firewall-friendly with passive mode. |
| FTP | 21 | None | Unencrypted. VPC-only (not internet-facing). |
| AS2 | 443 | S/MIME | B2B EDI exchanges. |

### 2. Integration with S3

**AI data ingestion patterns:**
- External partners upload training data, evaluation datasets, or documents via SFTP.
- Files land in an S3 bucket (scoped per user via IAM + home directory mappings).
- S3 event notifications trigger downstream processing (parsing, embedding, indexing).
- Managed workflows can automatically tag, validate, or transform uploaded files.

**User access configuration:**
- Each user gets a home directory mapped to an S3 prefix (e.g., `s3://bucket/partner-a/`).
- Logical directory mappings allow presenting a virtual directory structure while files are stored
  in different S3 paths.
- Session policies control S3 API actions per user (e.g., read-only, write-only, specific prefix).

**Endpoint types:**
- **Public** -- internet-accessible with an AWS-provided hostname or custom domain (Route 53).
- **VPC** -- accessible only within a VPC (or via VPN/Direct Connect). Supports fixed Elastic IPs
  for allowlisting.
- **VPC Internal** -- no internet access, only VPC-internal.

```typescript
// TypeScript SDK v3 -- Create a Transfer Family SFTP server backed by S3
import {
  TransferClient,
  CreateServerCommand,
} from "@aws-sdk/client-transfer";

const client = new TransferClient({ region: "us-east-1" });

const response = await client.send(
  new CreateServerCommand({
    Protocols: ["SFTP"],
    IdentityProviderType: "SERVICE_MANAGED",
    EndpointType: "PUBLIC",
    Domain: "S3",
    Tags: [{ Key: "project", Value: "genai-data-ingestion" }],
  })
);
```

> **Exam tip:** Transfer Family is the answer when a question involves external partners
> uploading data via SFTP/FTPS. DataSync is for bulk migration from on-premises storage.
> Transfer Family = protocol-based file transfer from external parties.
> DataSync = automated, high-performance bulk data movement.

---

## Cross-Cutting Exam Gotchas

| Topic | Gotcha |
|---|---|
| S3 default encryption | SSE-S3 is always on. You do not need to "enable" encryption. |
| S3 metadata immutability | User-defined metadata (`x-amz-meta-*`) cannot be changed after upload. |
| Bedrock KB metadata files | Must be `.metadata.json` sidecar files, not S3 metadata or tags. |
| Versioning | Cannot be disabled once enabled, only suspended. Required for CRR. |
| CRR existing objects | CRR only applies to new objects. Use Batch Replication for existing. |
| Lifecycle timing | Minimum 30 days before Standard-to-IA transition. Glacier min durations apply. |
| Intelligent-Tiering fees | No retrieval fee, but there is a small monthly monitoring charge per object. |
| S3 Select | Deprecated for new customers. Prefer Athena for new workloads. |
| SQS FIFO | Not supported as S3 event notification destination. |
| EBS AZ scope | EBS volumes are AZ-scoped. Cannot be shared across AZs (use EFS for that). |
| EFS throughput | Elastic throughput is the default and best for spiky ML I/O patterns. |
| DataSync vs Snowball | DataSync = network transfer. Snowball = physical device for limited bandwidth. |
| DataSync vs Transfer Family | DataSync = automated migration. Transfer Family = protocol endpoints for external parties. |
| S3 Bucket Keys | Reduce KMS costs by up to 99%. Always enable when using SSE-KMS at scale. |
| EFS + Lambda | Lambda must be in a VPC to mount EFS. Requires port 2049 (NFS) access. |
| gp3 vs gp2 | Always prefer gp3. Same cost, independently configurable IOPS and throughput. |
