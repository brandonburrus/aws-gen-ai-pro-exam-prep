import * as cdk from 'aws-cdk-lib'
import * as bedrock from 'aws-cdk-lib/aws-bedrock'
import * as iam from 'aws-cdk-lib/aws-iam'
import { Construct } from 'constructs'

/**
 * Model ID for Amazon Titan Text Embeddings V2.
 * Outputs 1024-dimensional vectors by default.
 */
const TITAN_EMBED_V2_MODEL_ID = 'amazon.titan-embed-text-v2:0'

export interface BedrockKnowledgeBaseProps {
  /** Display name of the knowledge base. */
  knowledgeBaseName: string
  /** ARN of the OpenSearch Serverless collection to use as the vector store. */
  collectionArn: string
  /** ARN of the S3 bucket containing the source documents. */
  bucketArn: string
  /**
   * Name of the OpenSearch vector index.
   * Must already exist before the knowledge base is created.
   */
  vectorIndexName: string
}

/**
 * Creates an Amazon Bedrock Knowledge Base backed by an OpenSearch Serverless
 * vector store, along with the IAM service role that Bedrock needs to access
 * the collection and the S3 data bucket.
 *
 * The embedding model is Amazon Titan Text Embeddings V2 (1024 dimensions).
 *
 * Field mapping:
 * - vectorField: bedrock-knowledge-base-default-vector
 * - textField:   AMAZON_BEDROCK_TEXT_CHUNK
 * - metadataField: AMAZON_BEDROCK_METADATA
 */
export class BedrockKnowledgeBase extends Construct {
  /** The underlying CfnKnowledgeBase resource. */
  public readonly knowledgeBase: bedrock.CfnKnowledgeBase
  /** The auto-assigned knowledge base ID (e.g. ABCDEF1234). */
  public readonly knowledgeBaseId: string
  /** The full knowledge base ARN. */
  public readonly knowledgeBaseArn: string
  /** The IAM service role assumed by Bedrock when operating this knowledge base. */
  public readonly role: iam.Role

  constructor(scope: Construct, id: string, props: BedrockKnowledgeBaseProps) {
    super(scope, id)

    const { knowledgeBaseName, collectionArn, bucketArn, vectorIndexName } = props

    const embeddingModelArn = `arn:aws:bedrock:${cdk.Aws.REGION}::foundation-model/${TITAN_EMBED_V2_MODEL_ID}`

    this.role = new iam.Role(this, 'ServiceRole', {
      roleName: `AmazonBedrockExecutionRoleForKnowledgeBase-${knowledgeBaseName}`,
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com', {
        conditions: {
          StringEquals: {
            'aws:SourceAccount': cdk.Aws.ACCOUNT_ID,
          },
          ArnLike: {
            'AWS:SourceArn': `arn:aws:bedrock:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:knowledge-base/*`,
          },
        },
      }),
      inlinePolicies: {
        BedrockEmbeddingModel: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              sid: 'BedrockInvokeModelStatement',
              effect: iam.Effect.ALLOW,
              actions: ['bedrock:InvokeModel'],
              resources: [embeddingModelArn],
            }),
          ],
        }),
        S3DataSource: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              sid: 'S3ListBucketStatement',
              effect: iam.Effect.ALLOW,
              actions: ['s3:ListBucket'],
              resources: [bucketArn],
              conditions: {
                StringEquals: { 'aws:ResourceAccount': cdk.Aws.ACCOUNT_ID },
              },
            }),
            new iam.PolicyStatement({
              sid: 'S3GetObjectStatement',
              effect: iam.Effect.ALLOW,
              actions: ['s3:GetObject'],
              resources: [`${bucketArn}/*`],
              conditions: {
                StringEquals: { 'aws:ResourceAccount': cdk.Aws.ACCOUNT_ID },
              },
            }),
          ],
        }),
        OpenSearchServerless: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              sid: 'OpenSearchServerlessAPIAccessAllStatement',
              effect: iam.Effect.ALLOW,
              actions: ['aoss:APIAccessAll'],
              resources: [collectionArn],
            }),
          ],
        }),
      },
    })

    this.knowledgeBase = new bedrock.CfnKnowledgeBase(this, 'KnowledgeBase', {
      name: knowledgeBaseName,
      roleArn: this.role.roleArn,
      knowledgeBaseConfiguration: {
        type: 'VECTOR',
        vectorKnowledgeBaseConfiguration: {
          embeddingModelArn,
        },
      },
      storageConfiguration: {
        type: 'OPENSEARCH_SERVERLESS',
        opensearchServerlessConfiguration: {
          collectionArn,
          vectorIndexName,
          fieldMapping: {
            vectorField: 'bedrock-knowledge-base-default-vector',
            textField: 'AMAZON_BEDROCK_TEXT_CHUNK',
            metadataField: 'AMAZON_BEDROCK_METADATA',
          },
        },
      },
    })

    this.knowledgeBaseId = this.knowledgeBase.attrKnowledgeBaseId
    this.knowledgeBaseArn = this.knowledgeBase.attrKnowledgeBaseArn
  }
}
