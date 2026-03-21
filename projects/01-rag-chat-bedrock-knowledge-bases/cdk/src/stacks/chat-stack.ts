import * as cdk from 'aws-cdk-lib'
import type { Construct } from 'constructs'
import * as s3 from 'aws-cdk-lib/aws-s3'
import { OpenSearchVectorCollection } from '../constructs/opensearch-vector-collection'
import { OpenSearchVectorIndex } from '../constructs/opensearch-vector-index'
import { BedrockKnowledgeBase } from '../constructs/bedrock-knowledge-base'
import { BedrockDataSource } from '../constructs/bedrock-data-source'
import { AskPdfQuestionFunction } from '../constructs/ask-pdf-question-function'
import { ChatApi } from '../constructs/chat-api'

export class ChatStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    const bucket = new s3.Bucket(this, 'pdfs-bucket', {
      bucketName: 'aip-c01-bedrock-pdfs-bucket',
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    })

    // Pre-compute both KB service role ARNs from their deterministic names so we
    // can include them in the OpenSearch data access policy before either KB
    // construct is instantiated. This works because the stack targets a concrete
    // account + region (no pseudo-parameter tokens in this.account).
    const kbRoleArn = `arn:aws:iam::${this.account}:role/AmazonBedrockExecutionRoleForKnowledgeBase-aip-c01-pdf-kb`
    const fixedKbRoleArn = `arn:aws:iam::${this.account}:role/AmazonBedrockExecutionRoleForKnowledgeBase-aip-c01-pdf-fixed-kb`

    const vectorCollection = new OpenSearchVectorCollection(this, 'VectorCollection', {
      collectionName: 'aip-c01-rag-vectors',
      additionalAccessPrincipals: [kbRoleArn, fixedKbRoleArn],
    })

    // Hierarchical KB index
    const vectorIndex = new OpenSearchVectorIndex(this, 'VectorIndex', {
      collectionEndpoint: vectorCollection.collectionEndpoint,
      indexName: 'bedrock-kb-pdf-index',
    })

    // Fixed-chunking KB index — separate index in the same collection
    const fixedVectorIndex = new OpenSearchVectorIndex(this, 'FixedVectorIndex', {
      collectionEndpoint: vectorCollection.collectionEndpoint,
      indexName: 'bedrock-kb-pdf-fixed-index',
    })

    const knowledgeBase = new BedrockKnowledgeBase(this, 'KnowledgeBase', {
      knowledgeBaseName: 'aip-c01-pdf-kb',
      collectionArn: vectorCollection.collectionArn,
      bucketArn: bucket.bucketArn,
      vectorIndexName: vectorIndex.index.indexName,
    })

    // The knowledge base must not be created until the vector index exists,
    // since Bedrock validates that the named index is present in the collection.
    knowledgeBase.knowledgeBase.addDependency(vectorIndex.index)

    const dataSource = new BedrockDataSource(this, 'DataSource', {
      knowledgeBaseId: knowledgeBase.knowledgeBaseId,
      dataSourceName: 'aip-c01-pdf-kb-s3-source',
      bucketArn: bucket.bucketArn,
      inclusionPrefixes: ['docs/'],
      chunkingConfig: {
        strategy: 'HIERARCHICAL',
        parentMaxTokens: 1500,
        childMaxTokens: 300,
        overlapTokens: 60,
      },
    })

    const fixedKnowledgeBase = new BedrockKnowledgeBase(this, 'FixedKnowledgeBase', {
      knowledgeBaseName: 'aip-c01-pdf-fixed-kb',
      collectionArn: vectorCollection.collectionArn,
      bucketArn: bucket.bucketArn,
      vectorIndexName: fixedVectorIndex.index.indexName,
    })

    // Same dependency rule: the fixed KB must not be created before its index exists.
    fixedKnowledgeBase.knowledgeBase.addDependency(fixedVectorIndex.index)

    const fixedDataSource = new BedrockDataSource(this, 'FixedDataSource', {
      knowledgeBaseId: fixedKnowledgeBase.knowledgeBaseId,
      dataSourceName: 'aip-c01-pdf-fixed-kb-s3-source',
      bucketArn: bucket.bucketArn,
      inclusionPrefixes: ['docs/'],
      chunkingConfig: {
        strategy: 'FIXED_SIZE',
        maxTokens: 300,
        overlapPercentage: 10,
      },
    })

    /**
     * Amazon Nova Lite -- active, cost-effective text model with no Anthropic
     * use-case form requirement. Replaces Claude 3 Haiku which is now Legacy.
     */
    const generationModelArn =
      `arn:aws:bedrock:${this.region}::foundation-model/amazon.nova-lite-v1:0`

    const askPdfQuestionFunction = new AskPdfQuestionFunction(this, 'AskPdfQuestionFunction', {
      hierarchicalKnowledgeBaseId: knowledgeBase.knowledgeBaseId,
      fixedKnowledgeBaseId: fixedKnowledgeBase.knowledgeBaseId,
      hierarchicalKnowledgeBaseArn: knowledgeBase.knowledgeBaseArn,
      fixedKnowledgeBaseArn: fixedKnowledgeBase.knowledgeBaseArn,
      modelArn: generationModelArn,
    })

    const chatApi = new ChatApi(this, 'ChatApi', {
      chatHandler: askPdfQuestionFunction.function,
    })

    new cdk.CfnOutput(this, 'BucketName', { value: bucket.bucketName })
    new cdk.CfnOutput(this, 'CollectionEndpoint', { value: vectorCollection.collectionEndpoint })
    new cdk.CfnOutput(this, 'CollectionArn', { value: vectorCollection.collectionArn })
    new cdk.CfnOutput(this, 'DashboardEndpoint', { value: vectorCollection.dashboardEndpoint })
    new cdk.CfnOutput(this, 'KnowledgeBaseId', { value: knowledgeBase.knowledgeBaseId })
    new cdk.CfnOutput(this, 'KnowledgeBaseArn', { value: knowledgeBase.knowledgeBaseArn })
    new cdk.CfnOutput(this, 'DataSourceId', { value: dataSource.dataSourceId })
    new cdk.CfnOutput(this, 'FixedKnowledgeBaseId', { value: fixedKnowledgeBase.knowledgeBaseId })
    new cdk.CfnOutput(this, 'FixedKnowledgeBaseArn', { value: fixedKnowledgeBase.knowledgeBaseArn })
    new cdk.CfnOutput(this, 'FixedDataSourceId', { value: fixedDataSource.dataSourceId })
    new cdk.CfnOutput(this, 'AskPdfQuestionFunctionName', { value: 'ask-pdf-question' })
    new cdk.CfnOutput(this, 'ChatApiEndpoint', { value: chatApi.chatEndpoint })
  }
}
