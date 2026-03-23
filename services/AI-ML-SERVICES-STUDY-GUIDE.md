# AI/ML Individual Services -- Comprehensive Study Guide (AIP-C01)

This guide covers the AWS AI/ML services that appear on the Certified Generative AI Developer - Professional exam **outside of** Amazon Bedrock and SageMaker (which have their own dedicated guides). These services are the specialized, purpose-built AI tools that integrate with and complement generative AI workflows.

---

## Table of Contents

1. [Amazon Comprehend](#1-amazon-comprehend)
2. [Amazon Kendra](#2-amazon-kendra)
3. [Amazon Q Business and Q Apps](#3-amazon-q-business-and-q-apps)
4. [Amazon Q Developer](#4-amazon-q-developer)
5. [Amazon Titan Foundation Models](#5-amazon-titan-foundation-models)
6. [Amazon Lex](#6-amazon-lex)
7. [Amazon Transcribe](#7-amazon-transcribe)
8. [Amazon Textract](#8-amazon-textract)
9. [Amazon Rekognition](#9-amazon-rekognition)
10. [Amazon Augmented AI (A2I)](#10-amazon-augmented-ai-a2i)
11. [Service Comparison Decision Guide](#11-service-comparison-decision-guide)

---

## 1. Amazon Comprehend

### Service Overview

Amazon Comprehend is a **fully managed NLP service** that uses machine learning to extract insights from text. It requires no ML expertise and works through simple API calls.

**Core Capabilities:**
- **Entity Recognition** -- identifies people, places, organizations, dates, quantities
- **Sentiment Analysis** -- positive, negative, neutral, mixed (document-level and targeted)
- **PII Detection and Redaction** -- locates or redacts 22 universal + 14 country-specific PII types
- **Key Phrase Extraction** -- identifies important phrases
- **Language Detection** -- identifies dominant language (100+ languages)
- **Custom Classification** -- build custom text classifiers without ML expertise
- **Custom Entity Recognition** -- train models to find domain-specific entities
- **Toxicity Detection** -- detects toxic content in text
- **Topic Modeling** -- discovers topics across document collections (async batch only)
- **Syntax Analysis** -- tokenization and Parts of Speech (PoS) labeling
- **Events Extraction** -- extracts structured event data (who-what-when-where)

### GenAI Exam Relevance

| Exam Task | How Comprehend Applies |
|---|---|
| **Task 3.2.2, 3.2.3** | PII detection and redaction in data pipelines |
| **Task 1.3.4** | Entity extraction for pre-processing unstructured data |
| **Task 1.6.2** | Intent recognition / text classification |
| **Task 3.1.4** | Pre-processing filters before sending data to FMs |

### Key Features for the Exam

**PII Detection (High Priority):**
- Two operations: `DetectPiiEntities` (locate with offsets) and `ContainsPiiEntities` (label only)
- Supports **English and Spanish** only for PII
- Real-time (synchronous, single document up to 100KB) and batch (asynchronous, S3-based)
- Can **redact** PII in batch mode -- returns copy with PII replaced
- S3 Object Lambda Access Points can filter PII from S3 documents on-the-fly
- 22 universal PII types: NAME, ADDRESS, EMAIL, PHONE, CREDIT_DEBIT_NUMBER, SSN, etc.
- 14 country-specific types: US SSN, UK NHS number, CA Social Insurance Number, Indian Aadhaar, etc.
- Confidence threshold tuning: higher threshold = better precision, lower = better recall

**Custom Models:**
- Custom Classification: train with labeled documents, auto-splits training/test
- Custom Entity Recognition: train with annotations or entity lists
- Both use Flywheels for ongoing model management and retraining

**Real-time vs Async:**
- Real-time endpoints for custom models require provisioning (cost while running)
- Async jobs for batch processing through S3

### When to Use / When NOT to Use

**Use Comprehend when:**
- You need standalone PII detection/redaction as a **pre-processing step** before data reaches an FM
- You need entity extraction, sentiment analysis, or classification on text **outside** of a Bedrock pipeline
- You need PII detection on text that is **not** being sent to a foundation model (e.g., data lake governance)
- You need **batch PII redaction** across large document sets in S3
- You need S3 Object Lambda PII filtering for data access control
- You need custom text classification or custom entity recognition

**Do NOT use Comprehend when:**
- You need PII filtering **inline** during Bedrock model invocation -- use **Bedrock Guardrails** instead
- You need content moderation / toxicity filtering during FM inference -- use **Bedrock Guardrails**
- You need NLP on images or PDFs directly -- use **Textract** first to extract text, then Comprehend

### Comprehend PII vs Bedrock Guardrails PII (Critical Exam Topic)

| Feature | Comprehend PII | Bedrock Guardrails PII |
|---|---|---|
| **When to use** | Standalone text processing, data pipelines, S3 data governance | Inline with FM invocation (input/output filtering) |
| **Integration** | Standalone API calls or S3 Object Lambda | Built into Bedrock Invoke/Converse pipeline |
| **Languages** | English and Spanish only | Varies by configuration |
| **Action** | Locate (offsets) or Redact (batch) | Block or Mask |
| **Custom patterns** | No custom PII types (fixed taxonomy) | Custom regex patterns supported |
| **Batch support** | Yes (async S3 jobs) | No (real-time only) |
| **Use in Bedrock** | As a pre/post-processing step outside Bedrock | Natively integrated into inference calls |

**Exam tip:** If the question says "prevent PII from reaching the foundation model" or "filter PII in prompts and responses," the answer is **Bedrock Guardrails**. If the question says "detect PII in documents before ingestion" or "redact PII across an S3 data lake," the answer is **Comprehend**.

### Integration with Bedrock/GenAI

- Pre-process text with Comprehend PII detection **before** sending to Bedrock
- Extract entities from documents to enrich metadata for RAG knowledge bases
- Use sentiment analysis to route customer interactions (positive -> upsell, negative -> escalation)
- Custom classification to categorize documents before routing to specialized FM prompts
- Comprehend results can feed into A2I human review workflows

### Exam Gotchas

- Comprehend PII detection supports **only English and Spanish** -- not all languages
- `DetectPiiEntities` returns offsets (where PII is); `ContainsPiiEntities` returns labels only (what types exist)
- PII redaction is **batch only** (async) -- you cannot redact in real-time with a single API call
- Custom models require **real-time endpoints** to be provisioned for synchronous inference (cost implication)
- Topic Modeling is **async batch only** -- no real-time topic detection
- Comprehend does NOT support custom PII entity types; if you need custom patterns, use Bedrock Guardrails regex

### TypeScript SDK v3 Usage

```typescript
import {
  ComprehendClient,
  DetectPiiEntitiesCommand,
  DetectSentimentCommand,
  DetectEntitiesCommand,
  ContainsPiiEntitiesCommand,
} from "@aws-sdk/client-comprehend";

const client = new ComprehendClient({ region: "us-east-1" });

// Detect PII entities with offsets
const piiResponse = await client.send(
  new DetectPiiEntitiesCommand({
    Text: "John Smith lives at 123 Main St. SSN: 123-45-6789",
    LanguageCode: "en",
  })
);
// Returns: Entities[] with Type, Score, BeginOffset, EndOffset

// Check if document contains PII (labels only, no offsets)
const containsPii = await client.send(
  new ContainsPiiEntitiesCommand({
    Text: "Call me at 555-0123",
    LanguageCode: "en",
  })
);
// Returns: Labels[] with Name and Score

// Sentiment analysis
const sentiment = await client.send(
  new DetectSentimentCommand({
    Text: "I love this product!",
    LanguageCode: "en",
  })
);
// Returns: Sentiment (POSITIVE|NEGATIVE|NEUTRAL|MIXED), SentimentScore

// Entity extraction
const entities = await client.send(
  new DetectEntitiesCommand({
    Text: "Amazon was founded by Jeff Bezos in Seattle",
    LanguageCode: "en",
  })
);
// Returns: Entities[] with Type (PERSON, ORGANIZATION, LOCATION, etc.)
```

### Key Metrics

- `SuccessfulRequestCount`, `ThrottledCount` -- API health
- Custom model metrics: Precision, Recall, F1 during training
- PII detection confidence scores per entity (tunable threshold)

---

## 2. Amazon Kendra

### Service Overview

Amazon Kendra is a **fully managed intelligent search service** that uses NLP and deep learning for semantic, contextual search. It goes beyond keyword matching to understand the meaning and context of queries.

**Core Capabilities:**
- Semantic search with natural language understanding
- 43+ pre-built data source connectors (S3, SharePoint, Confluence, Salesforce, etc.)
- Retrieval API optimized for RAG use cases
- Access control list (ACL) filtering for user-level document permissions
- Custom document enrichment during ingestion
- Relevance tuning and boosting
- Factoid, descriptive, and keyword query support

### GenAI Exam Relevance

| Exam Task | How Kendra Applies |
|---|---|
| **Task 2.5.3** | Internal knowledge tools, enterprise search |
| **RAG Retriever** | Serves as the retrieval layer for RAG architectures |

### Key Features for the Exam

**Index Types (Critical):**

| Feature | GenAI Enterprise Edition | Enterprise Edition | Developer Edition |
|---|---|---|---|
| **Purpose** | Highest accuracy for RAG / Retrieve API | Production semantic search | Testing only |
| **Accuracy** | Highest (advanced semantic models) | High | Same as Enterprise |
| **Retrieve API** | Full support, optimized | Full support | Full support |
| **Query API** | Full support | Full support | Full support |
| **Production use** | Yes | Yes | No |
| **Regions** | US East, US West, Ireland, Sydney | All Kendra regions | All Kendra regions |

**Retrieve API vs Query API:**
- **Retrieve API**: Returns up to 100 passages of up to 200 tokens each. Optimized for RAG. No query suggestions, spell check, or faceting. Use this for feeding passages to an LLM.
- **Query API**: Returns excerpts up to 100 tokens, supports advanced query syntax, spell correction, faceting, query suggestions, incremental learning. Use this for traditional search UX.

**Data Source Connectors:**
- 43+ connectors: S3, SharePoint, Confluence, Salesforce, ServiceNow, Jira, Google Drive, Slack, etc.
- v2.0 connectors required for GenAI Enterprise Edition
- Automatic crawling, syncing, and incremental updates

**Custom Document Enrichment:**
- Pre-extraction: modify documents/metadata before indexing
- Post-extraction: enrich with Lambda functions after text extraction
- Inline: basic attribute manipulation during ingestion

### When to Use / When NOT to Use

**Use Kendra when:**
- You need **enterprise search** with ACL-based access control
- You need a **retriever for RAG** with 43+ data source connectors out of the box
- You need **user-level document permissions** (RBAC with ACLs from source systems)
- You already have data in enterprise systems (SharePoint, Confluence, Salesforce, etc.)
- You need **relevance tuning** and search analytics
- You want to use Kendra GenAI Index with **Bedrock Knowledge Bases** as a retriever

**Do NOT use Kendra when:**
- You only need a **vector database** -- use OpenSearch Serverless, Aurora pgvector, etc.
- Your documents are already in S3 and you just need basic chunking + embeddings -- **Bedrock Knowledge Bases** with a vector store is simpler
- You need sub-millisecond latency for vector search -- use a dedicated vector DB
- Budget is very constrained -- Kendra has a higher starting cost than vector-DB-only solutions

### Kendra vs Bedrock Knowledge Bases (Critical Exam Topic)

| Feature | Amazon Kendra | Bedrock Knowledge Bases |
|---|---|---|
| **Primary purpose** | Enterprise intelligent search + RAG retriever | Managed RAG pipeline for Bedrock FMs |
| **Data sources** | 43+ native connectors with ACL support | S3, web crawlers, Confluence, SharePoint, Salesforce (growing) |
| **Access control** | Full ACL/RBAC from source systems | Metadata filtering (no native ACL from sources) |
| **Vector storage** | Built-in (no separate vector DB needed) | Requires a vector store (OpenSearch Serverless, Aurora pgvector, Pinecone, etc.) |
| **Search capabilities** | Semantic + keyword + faceting + spell check | Semantic retrieval only |
| **Can be used together** | Yes -- Kendra GenAI Index as retriever for Bedrock KB | Yes |
| **Standalone search UI** | Yes (Kendra search experience) | No (designed for FM consumption) |
| **Cost model** | Index-based (capacity units) | Per-query + vector DB costs |

**Exam tip:** If the question emphasizes **enterprise data source connectors with access control**, the answer is Kendra. If the question emphasizes a **managed RAG pipeline tightly integrated with Bedrock Agents/FMs**, the answer is Bedrock Knowledge Bases. They can also be used **together** -- Kendra GenAI Index as the retriever backing a Bedrock Knowledge Base.

### Integration with Bedrock/GenAI

- **Kendra GenAI Index + Bedrock Knowledge Bases**: Use Kendra as the retriever for Bedrock KB, combining Kendra's 43+ connectors and ACLs with Bedrock's RAG orchestration
- **Kendra + Amazon Q Business**: Q Business can use Kendra as its retriever backend
- **Kendra + Lex**: AMAZON.KendraSearchIntent routes Lex bot queries to Kendra for FAQ-style answers
- **Kendra Retrieve API -> LLM**: Fetch passages from Kendra, inject into FM prompt for custom RAG

### Exam Gotchas

- GenAI Enterprise Edition only available in limited regions (US East, US West, Ireland, Sydney)
- GenAI Enterprise Edition only supports **English** language content
- GenAI Edition only supports **v2.0 data source connectors**
- Retrieve API does NOT support query suggestions, spell check, or faceting
- Kendra is not just a vector database -- it has its own built-in retrieval engine
- Kendra does NOT require you to choose an embedding model or manage vectors -- it handles this internally

### TypeScript SDK v3 Usage

```typescript
import {
  KendraClient,
  RetrieveCommand,
  QueryCommand,
} from "@aws-sdk/client-kendra";

const client = new KendraClient({ region: "us-east-1" });

// Retrieve API for RAG (returns passages, optimized for LLM consumption)
const retrieveResponse = await client.send(
  new RetrieveCommand({
    IndexId: "your-index-id",
    QueryText: "What is our company's vacation policy?",
    PageSize: 10, // up to 100
  })
);
// Returns: ResultItems[] with DocumentId, Content (up to 200 tokens), DocumentTitle, DocumentURI

// Query API for traditional search (returns excerpts with highlights)
const queryResponse = await client.send(
  new QueryCommand({
    IndexId: "your-index-id",
    QueryText: "vacation policy",
    PageSize: 10,
    AttributeFilter: {
      EqualsTo: {
        Key: "_category",
        Value: { StringValue: "HR" },
      },
    },
  })
);
// Returns: ResultItems[] with excerpts, highlights, facets, spell corrections
```

### Key Metrics

- CloudWatch: `IndexQueryCount`, `IndexQueryLatency`, `DocumentsIndexed`, `DocumentsDeleted`
- Search Analytics dashboard (built-in): query volumes, click-through rates, zero-result queries

---

## 3. Amazon Q Business and Q Apps

### Service Overview

Amazon Q Business is a **fully managed, generative AI-powered enterprise assistant** that connects to your organization's data and systems. It provides conversational Q&A, content generation, summarization, and action execution, all with permissions-aware responses.

Amazon Q Apps is a feature within Q Business that lets end users create **lightweight, purpose-built AI applications** from conversations or prompts.

**Core Capabilities:**
- Conversational Q&A grounded in enterprise data with source citations
- 40+ pre-built data source connectors
- Built-in RAG pipeline (no need to manage vector stores, embeddings, or chunking)
- Plugins for taking actions in third-party systems (Jira, Salesforce, etc.)
- Admin controls: topic filters, guardrails, PII detection
- IAM Identity Center integration for user authentication
- Amazon Q Apps for user-created lightweight automation
- Agentic RAG with query decomposition and iterative retrieval

### GenAI Exam Relevance

| Exam Task | How Q Business Applies |
|---|---|
| **Task 2.5.3** | Internal knowledge tools for enterprise |
| **RAG** | Fully managed RAG solution without infrastructure management |

### Key Features for the Exam

**Architecture:**
- Uses foundation models hosted on Amazon Bedrock (no model selection needed -- managed)
- Built-in indexing pipeline with vector database (native index) or can use Kendra as retriever
- Document enrichment with Lambda functions for custom pre-processing
- Supports uploading documents directly in conversations (temporary, session-scoped)

**Data Source Connectors (40+):**
- Amazon S3, SharePoint, Confluence, Salesforce, Jira, Google Drive, Slack, ServiceNow, Microsoft Exchange, Smartsheet, and more
- Can use Amazon AppFlow to pull from unsupported sources into S3

**Plugins:**
- Read and write actions to third-party systems
- Custom plugins via OpenAPI schemas with OAuth/Cognito authentication
- Built-in plugins for Jira, Salesforce, etc.

**Amazon Q Apps:**
- Created by end users (Pro license required) from conversations or prompts
- Input/output cards, plugin cards, custom labels
- Published to company app library; admin-verified apps get priority placement
- Automate repetitive tasks: content generation, ticket creation, document processing
- Q Apps respect the same data governance and permissions as Q Business

**Security:**
- SAML 2.0 identity provider integration
- Permissions-aware: responses filtered by user's access level
- Admin controls: blocked topics, content restrictions, response scope

**Agentic RAG (new capability):**
- Query decomposition: breaks complex queries into sub-queries
- Iterative retrieval: re-plans if initial results are insufficient
- Transparent response events showing processing steps
- Multi-turn conversational context

### When to Use / When NOT to Use

**Use Q Business when:**
- You need an **out-of-the-box enterprise AI assistant** without building RAG infrastructure
- You have data across **multiple enterprise systems** (SharePoint, Confluence, Jira, etc.)
- You need **permissions-aware** responses that respect user access controls
- You want end users to **create their own lightweight AI apps** (Q Apps)
- You want **zero ML infrastructure management** -- fully managed end-to-end
- You need **plugin-based actions** (create Jira tickets, query Salesforce, etc.)

**Do NOT use Q Business when:**
- You need **fine-grained control** over the FM, prompt engineering, or RAG pipeline -- build custom with Bedrock
- You need to use a **specific model** (Q Business manages model selection)
- You need **customer-facing** chatbots -- Q Business is for internal enterprise use
- You need **custom UI/UX** beyond what Q Business web experience provides
- You need to integrate with models **outside of Bedrock**

### Q Business vs Custom RAG (Critical Exam Topic)

| Feature | Amazon Q Business | Custom RAG (Bedrock KB + FM) |
|---|---|---|
| **Setup complexity** | Low -- managed end-to-end | Medium-High -- configure KB, vector store, FM, prompts |
| **Model choice** | Managed (no selection) | Full choice of any Bedrock FM |
| **Data sources** | 40+ native connectors | S3, web crawlers, select connectors |
| **Permissions** | Full ACL from source systems | Metadata filtering only |
| **Customization** | Limited (admin controls, plugins) | Full (prompts, chains, agents, guardrails) |
| **UI** | Built-in web experience | Build your own |
| **Actions** | Plugins (Jira, Salesforce, custom) | Bedrock Agents with Lambda |
| **Pricing** | Per-user subscription ($3-20/user/month) | Pay-per-use (API calls + infrastructure) |
| **Target audience** | Enterprise employees (internal) | Any (internal or customer-facing) |

**Exam tip:** Q Business is the answer when the question describes an **enterprise** needing to quickly deploy an AI assistant across internal teams with existing enterprise data sources. Custom Bedrock RAG is the answer when the question requires **customization, specific model selection, or customer-facing** applications.

### Integration with Bedrock/GenAI

- Q Business uses Bedrock FMs internally (managed)
- Can use Kendra as an alternative retriever backend
- Q Apps extend Q Business with user-created automation
- Integrates with Slack and Microsoft Teams for chat deployment
- Custom plugins connect to any API via OpenAPI schemas

### Exam Gotchas

- Q Business is for **internal enterprise** use, not customer-facing chatbots
- You **cannot select** which FM Q Business uses -- it is managed
- Q Apps require a **Pro license** (not Lite)
- Q Apps created by Lite users were **deleted** after August 30, 2024
- Uploaded documents in Q Business conversations are **session-scoped** only (not permanently indexed)
- Q Business is NOT the same as Q Developer -- different products, different purposes

### TypeScript SDK v3 Usage

```typescript
import {
  QBusinessClient,
  ChatSyncCommand,
  ListApplicationsCommand,
} from "@aws-sdk/client-qbusiness";

const client = new QBusinessClient({ region: "us-east-1" });

// Chat with Q Business application
const chatResponse = await client.send(
  new ChatSyncCommand({
    applicationId: "your-app-id",
    userMessage: "What is our company's remote work policy?",
  })
);
// Returns: systemMessage (answer), sourceAttributions (citations)

// List Q Business applications
const apps = await client.send(new ListApplicationsCommand({}));
```

---

## 4. Amazon Q Developer

### Service Overview

Amazon Q Developer is an **AI-powered developer assistant** that integrates into IDEs, the AWS console, and CI/CD workflows. It is the evolution of Amazon CodeWhisperer.

**Core Capabilities:**
- **Code generation**: inline code completion, full function generation
- **Code explanation**: explain selected code blocks
- **Code refactoring**: restructure code for clarity, performance
- **Code transformation**: automated language upgrades (e.g., Java 8 -> 17)
- **Test generation**: unit test scaffolding
- **Bug fixing**: diagnose and suggest fixes
- **Security scanning**: detect vulnerabilities in generated code
- **AWS console assistance**: answer questions about AWS services and diagnose errors
- **CLI assistance**: natural language to bash/CLI translation

### GenAI Exam Relevance

| Exam Task | How Q Developer Applies |
|---|---|
| **Task 2.5.4** | Code generation and refactoring capabilities |
| **Task 2.5.6** | Error pattern recognition and debugging |

### Key Features for the Exam

**Code Generation:**
- Inline suggestions as you type (auto-completion)
- Full function generation from comments/docstrings
- Context-aware: uses open files, imports, project structure
- Supports 15+ languages: Python, Java, JavaScript, TypeScript, C#, Go, etc.
- Reference tracker shows if suggestions match public code

**Agentic Coding:**
- Multi-step development: plans, generates code, runs tests, iterates
- Reads/modifies files, executes commands
- Toggle on/off in IDE

**Code Transformation:**
- Automated Java upgrades (8 -> 17)
- .NET Framework to cross-platform .NET
- Language and OS-level conversions

**Security Scanning:**
- Detects vulnerabilities in generated and existing code
- AI-powered remediation suggestions
- Integrated into IDE workflow

**Customization:**
- Code customization: train on your codebase for organization-specific suggestions
- Supports multiple languages for customization
- Usage limits apply for customization creation

**IDE Support:**
- VS Code, JetBrains IDEs, Visual Studio, Eclipse
- AWS Console (chat and error diagnosis)
- CLI (bash translation)
- Slack and Microsoft Teams integration

### When to Use / When NOT to Use

**Use Q Developer when:**
- Developers need **AI-assisted coding** in their IDE
- You need **automated code transformation** (language upgrades)
- You need **security vulnerability scanning** in generated code
- You want **AWS-specific expertise** in your development workflow
- You need to **debug AWS service errors** in the console

**Do NOT use Q Developer when:**
- You need to build an **AI-powered application** for end users -- use Bedrock
- You need **enterprise knowledge search** -- use Q Business
- You need to **train custom ML models** -- use SageMaker

### Integration with Bedrock/GenAI

- Q Developer uses Bedrock FMs internally for code generation
- Can assist in writing Bedrock API code, CDK/CloudFormation templates
- Helps debug Bedrock application errors
- Not directly programmable -- it is a developer tool, not an API service

### Exam Gotchas

- Q Developer is **NOT** the same as Q Business -- different audiences, different capabilities
- Q Developer was formerly called **CodeWhisperer** (exam may reference the rename)
- Q Developer does **not** use your code to train models without explicit consent
- Code customization has **usage limits** on creation/activation
- Q Developer is a **developer productivity tool**, not a service you call via API in your application
- Free tier includes code suggestions; Pro tier adds security scanning, customization

### Key Metrics

- Developer productivity: lines of code accepted, suggestion acceptance rate
- Security scanning: vulnerabilities detected, remediation rate
- Transformation: upgrade success rate, manual intervention required

---

## 5. Amazon Titan Foundation Models

### Service Overview

Amazon Titan is a **family of foundation models built by Amazon**, available exclusively through Amazon Bedrock. The family includes text generation, embedding, multimodal embedding, and image generation models.

**Model Family:**

| Model | Model ID | Purpose | Key Specs |
|---|---|---|---|
| **Titan Text Embeddings V2** | `amazon.titan-embed-text-v2:0` | Text-to-vector embeddings for RAG, search, classification | 8,192 tokens / 50K chars, output: 1024/512/256 dims |
| **Titan Multimodal Embeddings G1** | `amazon.titan-embed-image-v1` | Text+image-to-vector embeddings | 128 text tokens, output: 1024/384/256 dims |
| **Titan Image Generator G1 v2** | `amazon.titan-image-generator-v2:0` | Text-to-image, editing, conditioning | 512 char prompt, English only |
| **Titan Text Premier** | (legacy) | Enterprise text generation | 32K token context |
| **Titan Text Express** | (legacy) | Balanced cost/performance text | 8K token context |
| **Titan Text Lite** | (legacy) | Cost-effective text generation | 4K token context |

> **Note:** Amazon Nova models (Nova Micro, Lite, Pro, Premier, Canvas, Reel, Sonic) are Amazon's newer model family and are gradually superseding Titan Text models for text generation. For the exam, focus on **Titan Embeddings** and **Titan Image Generator** as they remain the primary Amazon embedding and image models.

### GenAI Exam Relevance

| Exam Task | How Titan Applies |
|---|---|
| **Task 1.5.2** | Embedding models for vector representations |
| **RAG** | Titan Embeddings V2 is a key embedding model for knowledge bases |

### Key Features for the Exam

**Titan Text Embeddings V2 (High Priority):**
- **Dimensions**: 1,024 (default), 512, or 256 -- configurable per request
- **Max input**: 8,192 tokens or 50,000 characters
- **Languages**: Optimized for English; 100+ languages supported (multilingual queries within a single language work well; cross-language queries are sub-optimal)
- **Use cases**: RAG, document search, reranking, semantic similarity, clustering, classification
- **Normalization**: Supported (useful for cosine similarity)
- **Fine-tuning**: Not supported
- **No inference parameters**: Does not accept `maxTokenCount`, `topP`, etc.
- **Delivery modes**: Latency-optimized (real-time) and throughput-optimized (batch)
- **Best practice**: Segment long documents into logical chunks (paragraphs/sections) for retrieval

**Titan Multimodal Embeddings G1:**
- **Dimensions**: 1,024 (default), 384, or 256
- **Input**: Text (up to 128 tokens) AND/OR images (PNG, JPEG, up to 25MB)
- **Use cases**: Multimodal search, recommendation, personalization
- **Fine-tuning**: Supported (image-text pairs, JSONL format, 1K-500K training samples)
- Generates a single embedding vector from text, image, or both

**Titan Image Generator v2:**
- Text-to-image generation with photorealistic output
- Image editing, inpainting, outpainting
- Image conditioning (use reference image for structure)
- Background removal
- Subject consistency (via fine-tuning)
- Color palette control
- **Watermark detection**: Built-in invisible watermarking for provenance
- **IP indemnity**: AWS provides intellectual property indemnity for Titan Image Generator outputs
- **Safety filters**: Blocks harmful/inappropriate content generation
- English prompts only, max 512 characters

### When to Use / When NOT to Use

**Use Titan Embeddings V2 when:**
- Building RAG with Bedrock Knowledge Bases (default embedding model option)
- You need **configurable dimensions** (256/512/1024) to balance accuracy vs storage/latency
- You need an embedding model with **multilingual support**
- You need **normalization** for cosine similarity comparisons

**Do NOT use Titan Embeddings when:**
- You need embeddings for **code** specifically -- consider Cohere Embed v4
- You need **multimodal embeddings** with high text token count -- Titan Multimodal only supports 128 tokens
- You need to **fine-tune** the embedding model -- Titan Text Embeddings V2 does not support fine-tuning

**Use Titan Image Generator when:**
- You need image generation with **IP indemnity coverage** from AWS
- You need built-in **watermarking** for content provenance
- You need image **editing, conditioning, or background removal**

### Integration with Bedrock/GenAI

- **Bedrock Knowledge Bases**: Titan Embeddings V2 is a primary embedding model option
- **Bedrock Batch Inference**: Use throughput-optimized mode for bulk embedding generation
- **Custom RAG**: Generate embeddings via Bedrock InvokeModel, store in your vector database
- **Titan Image Generator**: Called through Bedrock InvokeModel for image generation tasks

### Exam Gotchas

- Titan Embeddings V2 dimensions are **1024, 512, 256** (NOT 1536 -- that is Titan V1)
- Titan V1 outputs **1,536** dimensions; V2 outputs **1,024** default
- Titan Multimodal Embeddings max text input is only **128 tokens** (very short vs V2's 8,192)
- Titan Embeddings V2 does **NOT** support fine-tuning
- Titan Multimodal Embeddings G1 **does** support fine-tuning
- Cross-language queries with Titan Embeddings V2 produce **sub-optimal results**
- Titan Text generation models (Premier, Express, Lite) are being superseded by Amazon Nova -- but may still appear on exam
- Amazon provides **IP indemnity** for Titan Image Generator outputs (differentiator from third-party models)

### TypeScript SDK v3 Usage

```typescript
import {
  BedrockRuntimeClient,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";

const client = new BedrockRuntimeClient({ region: "us-east-1" });

// Generate text embeddings with Titan Embeddings V2
const embeddingResponse = await client.send(
  new InvokeModelCommand({
    modelId: "amazon.titan-embed-text-v2:0",
    contentType: "application/json",
    accept: "application/json",
    body: JSON.stringify({
      inputText: "What is machine learning?",
      dimensions: 512, // 256, 512, or 1024 (default)
      normalize: true, // for cosine similarity
    }),
  })
);

const embeddingResult = JSON.parse(
  new TextDecoder().decode(embeddingResponse.body)
);
// embeddingResult.embedding -> number[] of length 512

// Generate multimodal embeddings (text + image)
const multimodalResponse = await client.send(
  new InvokeModelCommand({
    modelId: "amazon.titan-embed-image-v1",
    contentType: "application/json",
    accept: "application/json",
    body: JSON.stringify({
      inputText: "a sunset over the ocean",
      // inputImage: base64EncodedImage, // optional
      embeddingConfig: { outputEmbeddingLength: 384 }, // 256, 384, or 1024
    }),
  })
);

// Generate an image with Titan Image Generator v2
const imageResponse = await client.send(
  new InvokeModelCommand({
    modelId: "amazon.titan-image-generator-v2:0",
    contentType: "application/json",
    accept: "application/json",
    body: JSON.stringify({
      textToImageParams: {
        text: "A futuristic city skyline at sunset, photorealistic",
      },
      imageGenerationConfig: {
        numberOfImages: 1,
        height: 1024,
        width: 1024,
      },
    }),
  })
);
```

### Key Metrics

- Bedrock CloudWatch: `InvocationLatency`, `InvocationCount`, `InvocationErrors` (per model)
- Embedding quality: measured by downstream task performance (retrieval accuracy, classification F1)

---

## 6. Amazon Lex

### Service Overview

Amazon Lex is a **fully managed service for building conversational interfaces** (chatbots) using voice and text. It uses the same technology as Amazon Alexa.

**Core Capabilities:**
- Automatic Speech Recognition (ASR) for voice input
- Natural Language Understanding (NLU) for intent recognition
- Multi-turn dialog management
- Slot filling (extracting parameters from user input)
- Integration with Lambda for fulfillment logic
- Generative AI features: Conversational FAQ (QnAIntent), Assisted Slot Resolution, Descriptive Bot Builder

### GenAI Exam Relevance

| Exam Task | How Lex Applies |
|---|---|
| **Conversational interfaces** | Building chatbot front-ends for GenAI applications |
| **Integration** | Routes to Kendra, Bedrock Agents, or Lambda for fulfillment |

### Key Features for the Exam

**Core Concepts:**
- **Bot**: The conversational application
- **Intent**: An action the user wants to perform (e.g., OrderPizza, BookHotel)
- **Utterance**: What the user says to trigger an intent ("I want to order a pizza")
- **Slot**: A parameter needed to fulfill an intent (pizza size, topping)
- **Slot Type**: The data type of a slot (built-in: AMAZON.Number, AMAZON.City; custom: PizzaSize)
- **Fulfillment**: Lambda function or return-to-client to process the intent

**GenAI Features (V2):**
- **AMAZON.QnAIntent**: Conversational FAQ -- routes questions to Kendra or Bedrock Knowledge Base for answers. No sample utterances needed.
- **AMAZON.BedrockAgentIntent**: Routes to Bedrock Agents and Knowledge Bases for advanced conversational AI
- **Assisted NLU**: Uses LLMs to improve intent classification and slot resolution while staying within configured intents/slots
- **Assisted Slot Resolution**: LLM-enhanced slot value extraction
- **Descriptive Bot Builder**: Create intents from natural language descriptions
- **Utterance Generation**: Auto-generate sample utterances from intent descriptions
- **QnA with Bedrock Guardrails**: Apply guardrails to QnAIntent responses

**Bot Architecture:**
- **Versions**: Immutable snapshots of bot configuration
- **Aliases**: Pointers to versions (e.g., "prod" -> version 5, "staging" -> version 6)
- **Network of Bots**: Combine multiple bots, route to appropriate bot based on input
- **Visual Conversation Builder**: Drag-and-drop conversation flow design
- **Conditional Branching**: Control conversation paths based on conditions

### When to Use / When NOT to Use

**Use Lex when:**
- You need a **structured chatbot** with defined intents, slots, and dialog flows
- You need **voice support** (ASR) for telephony or Alexa-like interfaces
- You need integration with **Amazon Connect** contact centers
- You need a conversational **front-end** that routes to Kendra, Bedrock, or Lambda
- You need **multi-language** chatbot support

**Do NOT use Lex when:**
- You need a **free-form conversational AI** without structured intents -- use Bedrock Agents directly
- You need an **enterprise knowledge assistant** -- use Q Business
- You only need **text-based** chat without voice -- Bedrock Agents/Converse API may be simpler
- Your bot needs to handle **unbounded** topics without predefined intents -- Bedrock is more flexible

### Integration with Bedrock/GenAI

- **AMAZON.QnAIntent + Kendra**: Lex routes FAQ-style questions to Kendra for retrieval
- **AMAZON.QnAIntent + Bedrock KB**: Routes to Bedrock Knowledge Base for RAG answers
- **AMAZON.BedrockAgentIntent**: Routes to Bedrock Agents for complex multi-step tasks
- **Lambda fulfillment**: Intent triggers Lambda which calls Bedrock for generation
- **Amazon Connect**: Lex provides the NLU layer for Connect contact center voice bots
- **Assisted NLU**: Uses Bedrock LLMs to improve intent recognition accuracy

### Exam Gotchas

- Lex V2 is the current version -- V1 is legacy
- **AMAZON.QnAIntent** does NOT require sample utterances (it catches unmatched queries)
- Lex is for **structured** conversations with defined intents; Bedrock Agents handle **unstructured** tasks
- Custom vocabulary max **500 phrases** per language
- Lex bots have **versions** (immutable) and **aliases** (mutable pointers)
- Lex integrates with **Polly** for text-to-speech output (voice responses)
- 8 kHz telephony audio is supported (important for contact center use)

### TypeScript SDK v3 Usage

```typescript
import {
  LexRuntimeV2Client,
  RecognizeTextCommand,
} from "@aws-sdk/client-lex-runtime-v2";

const client = new LexRuntimeV2Client({ region: "us-east-1" });

const response = await client.send(
  new RecognizeTextCommand({
    botId: "your-bot-id",
    botAliasId: "your-alias-id",
    localeId: "en_US",
    sessionId: "user-session-123",
    text: "I want to book a hotel in Seattle",
  })
);
// Returns: messages[], sessionState (intent, slots, dialogAction)
// sessionState.intent.name -> "BookHotel"
// sessionState.intent.slots -> { city: "Seattle", ... }
```

### Key Metrics

- CloudWatch: `MissedUtteranceCount`, `RuntimeSuccessCount`, `RuntimeThrottledCount`
- Analytics dashboard: intent success/failure rates, slot resolution rates, conversation drop-off
- Test Workbench: measure bot performance with test sets

---

## 7. Amazon Transcribe

### Service Overview

Amazon Transcribe is a **fully managed speech-to-text service** using Automatic Speech Recognition (ASR). It converts audio into text with high accuracy, supporting both batch and real-time streaming.

**Core Capabilities:**
- Batch transcription (from S3 audio/video files)
- Real-time streaming transcription (WebSocket, HTTP/2, SDK)
- Speaker diarization (identify who said what)
- Custom vocabulary and custom language models
- Automatic language identification
- PII redaction in transcripts
- Vocabulary filtering (mask profanity/custom words)
- Punctuation, number normalization, true casing
- Call Analytics (call center specific)
- Medical transcription (specialized medical vocabulary)

### GenAI Exam Relevance

| Exam Task | How Transcribe Applies |
|---|---|
| **Task 1.3.2** | Audio processing for multimodal GenAI pipelines |
| **Pre-processing** | Convert audio/video to text for FM consumption |

### Key Features for the Exam

**Transcription Modes:**
- **Batch**: Upload audio to S3, get transcript back. Supports all audio/video formats.
- **Streaming**: Real-time via WebSocket or HTTP/2. Supports FLAC, OPUS (in Ogg), PCM. Up to 4 hours. Returns partial results that stabilize.

**Accuracy Enhancement:**
- **Custom Vocabulary**: Up to 100 entries of domain-specific terms (medical, legal, technical)
- **Custom Language Models**: Train on your text corpus for domain-specific language patterns
- **Vocabulary Filtering**: Mask or remove specific words from output

**Privacy and Safety:**
- **Automatic Content Redaction**: Redact PII from transcripts (SSN, credit card, etc.)
- **Vocabulary Filtering**: Remove profanity or custom terms
- **Toxic Audio Content Detection**: Identify toxic speech

**Streaming Features:**
- Partial results with `IsPartial` flag (progresses to complete segments)
- Partial-result stabilization (reduces word changes, slight accuracy trade-off)
- Word-level confidence scores and timestamps
- Speaker diarization in streaming

**Call Analytics (Transcribe Call Analytics):**
- Call summarization
- Sentiment analysis per speaker turn
- Issue detection
- Action item extraction
- Non-talk time detection

**Medical Transcription:**
- Specialized medical vocabulary
- Dictation and conversational modes
- Medical specialties support
- HIPAA eligible

### When to Use / When NOT to Use

**Use Transcribe when:**
- You need to convert **audio/video to text** as a pre-processing step for GenAI
- You need **real-time speech-to-text** for live captioning or voice interfaces
- You need to **transcribe call center audio** with analytics
- You need **PII redaction** in audio transcripts
- You need **speaker identification** (diarization)

**Do NOT use Transcribe when:**
- You need **text-to-speech** -- use Amazon Polly
- You need **real-time conversational speech-to-speech** -- use Amazon Nova Sonic via Bedrock
- Audio is already text -- skip directly to NLP services

### Integration with Bedrock/GenAI

- **Audio -> Text -> FM pipeline**: Transcribe converts audio to text, then feed to Bedrock for analysis, summarization, or Q&A
- **Transcribe + Comprehend**: Transcribe audio, then run Comprehend for entity extraction, sentiment, PII detection
- **Transcribe + Lex**: Real-time voice-to-text for Lex chatbot input (Lex has built-in ASR, but Transcribe offers more control)
- **Call Analytics + Bedrock**: Transcribe call audio with analytics, then use Bedrock to generate call summaries, action items

### Exam Gotchas

- Streaming supports limited audio formats: **FLAC, OPUS (Ogg), PCM** only (not MP3 in streaming)
- Batch supports **all common formats** (MP3, WAV, FLAC, etc.)
- Streaming has a **4-hour** maximum duration
- Partial-result stabilization trades **accuracy for latency**
- Custom vocabulary is different from Custom Language Models (vocabulary = specific terms, CLM = language patterns)
- Transcribe Call Analytics is a **separate feature** from standard transcription
- Medical transcription is US English only (`en-US`)
- Transcribe processes **audio** -- for document text extraction, use Textract

### TypeScript SDK v3 Usage

```typescript
import {
  TranscribeClient,
  StartTranscriptionJobCommand,
  GetTranscriptionJobCommand,
} from "@aws-sdk/client-transcribe";

const client = new TranscribeClient({ region: "us-east-1" });

// Start a batch transcription job
await client.send(
  new StartTranscriptionJobCommand({
    TranscriptionJobName: "my-job-001",
    LanguageCode: "en-US",
    Media: {
      MediaFileUri: "s3://my-bucket/audio/meeting.mp3",
    },
    OutputBucketName: "my-bucket",
    OutputKey: "transcripts/meeting.json",
    Settings: {
      ShowSpeakerLabels: true,
      MaxSpeakerLabels: 4,
    },
    ContentRedaction: {
      RedactionType: "PII",
      RedactionOutput: "redacted", // or "redacted_and_unredacted"
      PiiEntityTypes: ["NAME", "ADDRESS", "CREDIT_DEBIT_NUMBER"],
    },
  })
);

// Check job status
const job = await client.send(
  new GetTranscriptionJobCommand({
    TranscriptionJobName: "my-job-001",
  })
);
// job.TranscriptionJob.TranscriptionJobStatus -> "IN_PROGRESS" | "COMPLETED" | "FAILED"
```

### Key Metrics

- CloudWatch: `TotalRequestCount`, `SuccessfulRequestCount`, `ThrottledCount`
- Per-job: word confidence scores, speaker labels, timestamps

---

## 8. Amazon Textract

### Service Overview

Amazon Textract is a **fully managed document analysis service** that extracts text, forms, tables, and structured data from documents using deep learning. It goes beyond basic OCR.

**Core Capabilities:**
- **DetectDocumentText**: Raw OCR text extraction (lines and words)
- **AnalyzeDocument**: Extract text + forms (key-value pairs) + tables + signatures + queries + layout
- **AnalyzeExpense**: Extract structured data from invoices and receipts
- **AnalyzeID**: Extract data from identity documents (driver's licenses, passports)
- **AnalyzeLending**: Specialized mortgage document processing
- Custom Adapters: Train custom models for domain-specific document types

### GenAI Exam Relevance

| Exam Task | How Textract Applies |
|---|---|
| **Document processing** | Extract text from documents before sending to FMs |
| **Data pre-processing** | Structure unstructured documents for RAG pipelines |

### Key Features for the Exam

**APIs and Features:**

| API | Purpose | Key Features |
|---|---|---|
| `DetectDocumentText` | Basic OCR | Lines, words, confidence scores, bounding boxes |
| `AnalyzeDocument` | Structured extraction | Forms (key-value), Tables, Queries, Signatures, Layout |
| `AnalyzeExpense` | Invoice/receipt | Vendor name, line items, totals, tax amounts |
| `AnalyzeID` | Identity documents | Name, DOB, address, document number, expiration |
| `AnalyzeLending` | Mortgage packages | Classify and extract from mortgage document types |

**Processing Modes:**
- **Synchronous**: Single-page documents (JPEG, PNG, PDF, TIFF). Near real-time.
- **Asynchronous**: Multi-page documents (PDF, TIFF up to thousands of pages). Uses `StartDocumentTextDetection`/`StartDocumentAnalysis` -> poll with `GetDocumentTextDetection`/`GetDocumentAnalysis`.

**AnalyzeDocument Features (FeatureTypes):**
- `FORMS`: Extracts key-value pairs (e.g., "Name: John Smith")
- `TABLES`: Extracts table structure with rows, columns, cells, headers, merged cells
- `QUERIES`: Ask specific questions and get targeted answers (e.g., "What is the patient name?")
- `SIGNATURES`: Detects signature locations
- `LAYOUT`: Identifies document structure (paragraphs, headers, footers, lists, figures, page numbers)

**Custom Adapters:**
- Train on annotated sample documents for domain-specific extraction
- Provide `AdapterId` and `AdapterVersion` when calling AnalyzeDocument

**Document Formats:**
- Synchronous: JPEG, PNG, PDF (single-page), TIFF (single-page)
- Asynchronous: PDF (multi-page), TIFF (multi-page)
- Max 10MB file size

### When to Use / When NOT to Use

**Use Textract when:**
- You need to **extract text from scanned documents or images** (OCR + structure)
- You need **form field extraction** (key-value pairs)
- You need **table extraction** from documents
- You need to process **invoices, receipts, IDs, or mortgage documents**
- You need to **convert documents to text** before sending to an FM for analysis

**Do NOT use Textract when:**
- Your documents are already **digital text** (plain text, HTML, etc.) -- no extraction needed
- You need **NLP analysis** on extracted text -- use Comprehend after Textract
- You need **speech-to-text** -- use Transcribe
- You need real-time **handwriting recognition from a stylus** -- Textract works on document images

### Integration with Bedrock/GenAI

- **Textract -> Bedrock**: Extract text from documents, then send to FM for summarization, Q&A, analysis
- **Textract -> Comprehend**: Extract text, then detect PII, entities, or sentiment
- **Textract + A2I**: Route low-confidence Textract extractions to human reviewers
- **Document processing pipeline**: S3 -> Textract -> Lambda (post-processing) -> Bedrock Knowledge Base
- **Bedrock Data Automation** may use Textract-like capabilities under the hood for document processing

### Exam Gotchas

- Textract is for **documents/images** -- NOT for audio (use Transcribe) or live text (use Comprehend)
- `DetectDocumentText` is just OCR; `AnalyzeDocument` adds structure (forms, tables, queries)
- Queries feature lets you ask **specific questions** about the document -- very useful for targeted extraction
- Synchronous APIs are **single-page only**; multi-page requires async
- Textract returns **Block objects** with hierarchical relationships (PAGE -> LINE -> WORD, TABLE -> CELL)
- AnalyzeExpense is specifically for **invoices and receipts** -- do not use AnalyzeDocument for these
- AnalyzeID is for **government-issued identity documents** only
- HIPAA eligible, PCI DSS compliant

### TypeScript SDK v3 Usage

```typescript
import {
  TextractClient,
  AnalyzeDocumentCommand,
  DetectDocumentTextCommand,
  AnalyzeExpenseCommand,
} from "@aws-sdk/client-textract";

const client = new TextractClient({ region: "us-east-1" });

// Analyze document for forms and tables (S3-based)
const analysisResponse = await client.send(
  new AnalyzeDocumentCommand({
    Document: {
      S3Object: {
        Bucket: "my-bucket",
        Name: "documents/tax-form.pdf",
      },
    },
    FeatureTypes: ["FORMS", "TABLES", "QUERIES", "SIGNATURES"],
    QueriesConfig: {
      Queries: [
        { Text: "What is the total amount?" },
        { Text: "What is the customer name?" },
      ],
    },
  })
);
// Returns: Blocks[] with BlockType (PAGE, LINE, WORD, TABLE, CELL, KEY_VALUE_SET, QUERY, QUERY_RESULT)

// Simple OCR text detection
const textResponse = await client.send(
  new DetectDocumentTextCommand({
    Document: {
      S3Object: {
        Bucket: "my-bucket",
        Name: "documents/letter.png",
      },
    },
  })
);
// Returns: Blocks[] with LINE and WORD blocks, each with Text and Confidence

// Analyze invoice/receipt
const expenseResponse = await client.send(
  new AnalyzeExpenseCommand({
    Document: {
      S3Object: {
        Bucket: "my-bucket",
        Name: "receipts/receipt-001.jpg",
      },
    },
  })
);
// Returns: ExpenseDocuments[] with SummaryFields and LineItemGroups
```

### Key Metrics

- CloudWatch: `SuccessfulRequestCount`, `ThrottledCount`, `ServerErrorCount`
- Per-extraction: confidence scores per block/field
- Response time varies by document complexity and page count

---

## 9. Amazon Rekognition

### Service Overview

Amazon Rekognition is a **fully managed image and video analysis service** that uses deep learning for computer vision tasks. No ML expertise required.

**Core Capabilities:**
- **Label Detection**: Objects, scenes, concepts, activities, dominant colors
- **Content Moderation**: Explicit/inappropriate content detection
- **Facial Analysis**: Face detection, attributes (emotion, age range, landmarks)
- **Face Comparison**: Compare faces between images
- **Face Search**: Match faces against a stored collection
- **Face Liveness**: Verify live person (anti-spoofing)
- **Celebrity Recognition**: Identify celebrities
- **Text Detection**: Extract text from images/videos (OCR for visual media)
- **Personal Protective Equipment (PPE) Detection**: Detect masks, helmets, vests
- **Custom Labels**: Train custom object detection models
- **Custom Moderation**: Train custom content moderation adapters
- **Video Analysis**: Asynchronous analysis of stored videos, real-time streaming

### GenAI Exam Relevance

| Exam Task | How Rekognition Applies |
|---|---|
| **Content moderation** | Pre-filter images/video before GenAI processing |
| **Multimodal preprocessing** | Extract labels/text from images for FM context |

### Key Features for the Exam

**Image vs Video Operations:**
- **Image operations**: Synchronous. Input from S3 or Base64 bytes. Returns immediately.
- **Video operations (stored)**: Asynchronous. Start -> Get pattern. Videos in S3.
- **Video operations (streaming)**: Real-time via Kinesis Video Streams.

**Content Moderation:**
- Detects explicit adult content, violence, and other inappropriate material
- **Custom Moderation adapters**: Train on your annotated images to enhance accuracy for your domain
- Returns labels with confidence scores
- Integrates with **A2I** for human review of flagged content
- **Bulk analysis**: `StartMediaAnalysisJob` for processing large image collections

**Face Liveness:**
- Verifies a live person is present (prevents photo/video spoofing)
- Uses `CreateFaceLivenessSession`, `StartFaceLivenessSession`, `GetFaceLivenessSessionResults`
- Important for identity verification workflows

**Custom Labels:**
- Train custom object/scene detection models with your images
- Useful for business-specific visual inspection (e.g., product defects)
- Charges for training hours and inference hours

### When to Use / When NOT to Use

**Use Rekognition when:**
- You need **image/video content moderation** (filter before or alongside GenAI)
- You need **facial analysis, comparison, or liveness detection**
- You need to **detect objects, scenes, or text in images/video**
- You need **real-time video stream analysis** (Kinesis Video Streams)
- You need to **moderate user-uploaded images** before processing with an FM

**Do NOT use Rekognition when:**
- You need to **generate images** -- use Bedrock (Titan Image Generator, Stability AI, Nova Canvas)
- You need **document text extraction** with forms/tables -- use Textract
- You need **text analysis** (sentiment, entities) -- use Comprehend
- You need multimodal **understanding** (describe what's in an image) -- use a multimodal FM via Bedrock (Claude, Nova)

### Integration with Bedrock/GenAI

- **Content moderation pipeline**: User uploads image -> Rekognition moderates -> if safe, send to FM for analysis
- **Rekognition + A2I**: Low-confidence moderation results routed to human reviewers
- **Label extraction -> FM context**: Detect labels/objects in images, include as text context for FM prompts
- **Video analysis -> summarization**: Extract scenes/events from video, feed to FM for narrative summarization

### Exam Gotchas

- Rekognition is for **analysis**, not generation -- it does not create images
- `DetectModerationLabels` is for content moderation; `DetectLabels` is for general object/scene detection
- Face **collections** store face vectors (not images) for search operations
- Video analysis is **asynchronous** (Start/Get pattern) -- not real-time for stored videos
- Streaming video analysis uses **Kinesis Video Streams** (real-time)
- Custom Labels and Custom Moderation have **training costs** (per-hour)
- Rekognition is a **HIPAA Eligible Service**
- Text detection in images (`DetectText`) is basic OCR -- for forms/tables, use Textract

### TypeScript SDK v3 Usage

```typescript
import {
  RekognitionClient,
  DetectLabelsCommand,
  DetectModerationLabelsCommand,
  DetectTextCommand,
} from "@aws-sdk/client-rekognition";

const client = new RekognitionClient({ region: "us-east-1" });

// Detect labels (objects, scenes) in an image
const labels = await client.send(
  new DetectLabelsCommand({
    Image: {
      S3Object: { Bucket: "my-bucket", Name: "images/photo.jpg" },
    },
    MaxLabels: 20,
    MinConfidence: 75,
  })
);
// Returns: Labels[] with Name, Confidence, Instances (bounding boxes), Parents

// Content moderation
const moderation = await client.send(
  new DetectModerationLabelsCommand({
    Image: {
      S3Object: { Bucket: "my-bucket", Name: "uploads/user-image.jpg" },
    },
    MinConfidence: 60,
  })
);
// Returns: ModerationLabels[] with Name, Confidence, ParentName

// Detect text in images
const textInImage = await client.send(
  new DetectTextCommand({
    Image: {
      S3Object: { Bucket: "my-bucket", Name: "images/sign.jpg" },
    },
  })
);
// Returns: TextDetections[] with DetectedText, Type (LINE|WORD), Confidence, Geometry
```

### Key Metrics

- CloudWatch: `SuccessfulRequestCount`, `ThrottledCount`, per-API metrics
- Per-response: confidence scores for labels, moderation labels, faces
- Custom Labels: training loss, F1 score, precision, recall

---

## 10. Amazon Augmented AI (A2I)

### Service Overview

Amazon Augmented AI (A2I) is a service that enables **human-in-the-loop review workflows** for machine learning predictions. It provides the infrastructure to build, manage, and monitor human review processes without building custom review tools.

**Core Capabilities:**
- Built-in integration with Textract and Rekognition
- Custom task types for any ML workflow
- Configurable confidence thresholds for triggering human review
- Workforce management (private, Mechanical Turk, third-party vendors)
- Worker task templates (customizable UI)
- Results stored in S3
- EventBridge notifications on completion

### GenAI Exam Relevance

| Exam Task | How A2I Applies |
|---|---|
| **Task 2.1.5** | Human review workflows for ML/AI outputs |
| **Quality assurance** | Human oversight of FM-generated content |

### Key Features for the Exam

**Three Components:**
1. **Worker Task Template**: HTML template defining the review UI presented to human reviewers
2. **Flow Definition**: Specifies conditions for review, workforce, task template, and output location
3. **Human Loop**: An individual review task created when conditions are met

**Built-in Task Types:**
- **Amazon Textract**: Review key-value pair extractions from documents. Confidence thresholds trigger review automatically.
- **Amazon Rekognition**: Review content moderation results. Confidence thresholds or random sampling trigger review.
- Both built-in types support automatic **Human Loop Activation Conditions** (confidence thresholds).

**Custom Task Types:**
- For any ML model or workflow (including GenAI/Bedrock outputs)
- You call `StartHumanLoop` explicitly from your application code
- **No automatic activation conditions** -- your application decides when to trigger review
- Supports review of Comprehend, Transcribe, Translate, SageMaker, or any custom output

**Workforce Options:**
- **Private workforce**: Your organization's employees (via Cognito or OIDC)
- **Amazon Mechanical Turk**: Public crowd workers (not for confidential data)
- **Third-party vendors**: AWS Marketplace review vendors

**Human Loop Activation:**

| Task Type | Activation | Configuration |
|---|---|---|
| Textract (built-in) | Automatic based on confidence thresholds | Set in Flow Definition |
| Rekognition (built-in) | Automatic based on confidence thresholds OR random sampling | Set in Flow Definition |
| Custom | Manual -- your code calls `StartHumanLoop` | In your application logic |

### When to Use / When NOT to Use

**Use A2I when:**
- You need **human review of low-confidence ML predictions**
- You need human verification of **Textract document extractions** or **Rekognition content moderation**
- You need **human-in-the-loop** for GenAI output quality assurance
- You need a **managed review infrastructure** without building custom review tools
- You need **audit trails** for human review decisions (output in S3)

**Do NOT use A2I when:**
- You need **real-time human approval** in a latency-sensitive pipeline (A2I is async)
- You need **automated content moderation** without humans -- use Rekognition or Bedrock Guardrails alone
- You need **model retraining** -- A2I captures review results, but retraining is a separate process
- You need a full **annotation/labeling platform** -- use SageMaker Ground Truth

### Integration with Bedrock/GenAI

- **GenAI output review**: Application calls Bedrock FM -> evaluate output confidence/quality -> if uncertain, call `StartHumanLoop` to route for human review
- **Textract + A2I**: Low-confidence document extractions routed to human reviewers before entering RAG pipeline
- **Rekognition + A2I**: Content moderation with human review for borderline cases
- **Comprehend + A2I**: Route uncertain entity extractions or PII detections for human verification
- **Feedback loop**: A2I review results can be used to improve prompts, fine-tune models, or update guardrails

**Common GenAI Pattern:**
```
User prompt -> Bedrock FM -> Generate response
                                |
                          Evaluate quality/confidence
                                |
                    High confidence -> Return to user
                    Low confidence  -> A2I Human Loop -> Reviewer corrects -> Return to user
```

### Exam Gotchas

- A2I is **asynchronous** -- human review takes time; not suitable for real-time approval flows
- Built-in task types (Textract, Rekognition) have **automatic activation conditions** (confidence thresholds)
- Custom task types do **NOT** have automatic activation -- your code must call `StartHumanLoop`
- A2I is part of the **SageMaker** service family (console access through SageMaker)
- Worker task templates are **HTML-based** -- customizable review UIs
- Results are stored in **S3** as JSON
- A2I sends **EventBridge** events on human loop completion
- Multiple reviewers can be used to increase confidence (consensus)
- A2I is NOT a replacement for Bedrock Guardrails -- Guardrails are automated; A2I involves humans

### TypeScript SDK v3 Usage

```typescript
import {
  SageMakerA2IRuntimeClient,
  StartHumanLoopCommand,
  DescribeHumanLoopCommand,
  ListHumanLoopsCommand,
} from "@aws-sdk/client-sagemaker-a2i-runtime";

const client = new SageMakerA2IRuntimeClient({ region: "us-east-1" });

// Start a human review loop (custom task type)
const humanLoop = await client.send(
  new StartHumanLoopCommand({
    HumanLoopName: "review-document-extraction-001",
    FlowDefinitionArn:
      "arn:aws:sagemaker:us-east-1:123456789:flow-definition/my-review-flow",
    HumanLoopInput: {
      InputContent: JSON.stringify({
        extractedText: "Patient Name: J0hn Sm1th", // possibly incorrect OCR
        confidence: 0.62,
        sourceDocument: "s3://my-bucket/docs/form.pdf",
      }),
    },
  })
);
// Returns: HumanLoopArn

// Check status of a human loop
const status = await client.send(
  new DescribeHumanLoopCommand({
    HumanLoopName: "review-document-extraction-001",
  })
);
// status.HumanLoopStatus -> "InProgress" | "Completed" | "Stopped" | "Failed"
// status.HumanLoopOutput?.OutputS3Uri -> S3 path with reviewer's corrections

// List human loops for a flow definition
const loops = await client.send(
  new ListHumanLoopsCommand({
    FlowDefinitionArn:
      "arn:aws:sagemaker:us-east-1:123456789:flow-definition/my-review-flow",
  })
);
```

### Key Metrics

- CloudWatch Events via EventBridge: human loop status changes
- S3 output: reviewer decisions, timestamps, worker IDs
- Metrics to track: review latency, agreement rate between reviewers, override rate vs model predictions

---

## 11. Service Comparison Decision Guide

### "Which service do I use?" Quick Reference

| Scenario | Service |
|---|---|
| Detect/redact PII in text before ingestion to a data lake | **Comprehend** |
| Filter PII in prompts/responses during Bedrock inference | **Bedrock Guardrails** |
| Enterprise search with 40+ data source connectors and ACLs | **Kendra** |
| Managed RAG pipeline integrated with Bedrock Agents | **Bedrock Knowledge Bases** |
| Out-of-the-box enterprise AI assistant for employees | **Q Business** |
| Custom GenAI application with model selection and prompt control | **Bedrock (custom RAG)** |
| AI-assisted code generation in IDE | **Q Developer** |
| Text-to-vector embeddings for RAG | **Titan Embeddings V2** (or Cohere Embed) |
| Structured chatbot with intents, slots, and voice | **Lex** |
| Free-form conversational AI agent | **Bedrock Agents** |
| Speech to text (audio transcription) | **Transcribe** |
| Text to speech | **Polly** (not covered here) |
| Document OCR with forms and tables | **Textract** |
| Image/video content moderation | **Rekognition** |
| Image generation | **Bedrock** (Titan Image, Nova Canvas, Stability) |
| Human review of ML/AI predictions | **A2I** |
| Extract entities from text | **Comprehend** |
| Detect objects/labels in images | **Rekognition** |
| Detect text in images | **Rekognition** (basic) or **Textract** (structured) |

### Common Multi-Service Pipelines

**Document Processing for RAG:**
```
S3 (documents) -> Textract (extract text/structure) -> Comprehend (PII redaction)
  -> Titan Embeddings V2 (vectorize) -> OpenSearch/Aurora (store)
  -> Bedrock KB (retrieve + generate)
```

**Voice-Enabled GenAI Assistant:**
```
User speaks -> Transcribe (speech-to-text) -> Lex (intent recognition)
  -> Bedrock Agent (fulfillment) -> Polly (text-to-speech) -> User hears response
```

**Content Moderation Pipeline:**
```
User uploads image -> Rekognition (content moderation)
  -> If uncertain: A2I (human review)
  -> If safe: Bedrock FM (analyze/describe image)
  -> Bedrock Guardrails (filter response)
```

**Enterprise Knowledge Assistant:**
```
Q Business (conversational UI) -> Kendra GenAI Index (retrieval)
  -> Bedrock FM (generation, managed by Q Business)
  -> User gets permissions-aware answer with citations
```

**Call Center Intelligence:**
```
Call audio -> Transcribe Call Analytics (transcribe + sentiment + summarization)
  -> Comprehend (entity extraction, PII detection)
  -> Bedrock FM (generate follow-up recommendations)
  -> A2I (human review for sensitive cases)
```

### Embedding Model Comparison (Exam-Relevant)

| Model | Dimensions | Max Input | Languages | Fine-tuning | Key Differentiator |
|---|---|---|---|---|---|
| **Titan Text Embeddings V2** | 1024/512/256 | 8,192 tokens | 100+ (English optimized) | No | Configurable dimensions, normalization |
| **Titan Text Embeddings V1** | 1,536 | 8,192 tokens | 25+ | No | Legacy, higher dimension |
| **Titan Multimodal Embeddings** | 1024/384/256 | 128 text tokens | English | Yes | Text + image joint embedding |
| **Cohere Embed v4** | 1024 | 512 tokens | 100+ | No | Multimodal (text+image), strong multilingual |
| **Cohere Embed Multilingual** | 1024 | 512 tokens | 100+ | No | Strong cross-language search |

### Cost Considerations

| Service | Pricing Model | Free Tier |
|---|---|---|
| **Comprehend** | Per API request + input size | 50K units/month (12 months) |
| **Kendra** | Index capacity units (hourly) | 750 hours Developer Edition (30 days) |
| **Q Business** | Per-user subscription ($3-20/month) | None |
| **Q Developer** | Free tier + Pro tier ($19/user/month) | Free tier available |
| **Titan Embeddings** | Per 1K input tokens via Bedrock | Bedrock free tier varies |
| **Lex** | Per text/speech request | 10K text, 5K speech/month (12 months) |
| **Transcribe** | Per second of audio | 60 minutes/month (12 months) |
| **Textract** | Per page processed | 1K pages/month (3 months) |
| **Rekognition** | Per image/minute of video | 1K images/month (12 months) |
| **A2I** | Per human review task + workforce costs | None |
