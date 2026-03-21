import * as cdk from 'aws-cdk-lib'
import * as opensearchserverless from 'aws-cdk-lib/aws-opensearchserverless'
import { Construct } from 'constructs'

export interface OpenSearchVectorCollectionProps {
  /** Name of the OpenSearch Serverless collection. Must be lowercase, 3-32 chars. */
  collectionName: string
  /** Optional description for the collection. */
  description?: string
  /**
   * Additional IAM principal ARNs to include in the data access policy alongside
   * the account root principal. Use this to grant collection/index access to
   * service roles (e.g. a Bedrock Knowledge Base service role).
   */
  additionalAccessPrincipals?: string[]
}

export class OpenSearchVectorCollection extends Construct {
  /** The underlying CfnCollection resource. */
  public readonly collection: opensearchserverless.CfnCollection
  /** The collection API endpoint (e.g. https://xxx.us-east-1.aoss.amazonaws.com). */
  public readonly collectionEndpoint: string
  /** The collection ARN. */
  public readonly collectionArn: string
  /** The OpenSearch dashboard endpoint URL. */
  public readonly dashboardEndpoint: string

  constructor(scope: Construct, id: string, props: OpenSearchVectorCollectionProps) {
    super(scope, id)

    const { collectionName, description, additionalAccessPrincipals = [] } = props

    const encryptionPolicy = new opensearchserverless.CfnSecurityPolicy(this, 'EncryptionPolicy', {
      name: `${collectionName}-enc`,
      type: 'encryption',
      policy: JSON.stringify({
        Rules: [{ ResourceType: 'collection', Resource: [`collection/${collectionName}`] }],
        AWSOwnedKey: true,
      }),
    })

    const networkPolicy = new opensearchserverless.CfnSecurityPolicy(this, 'NetworkPolicy', {
      name: `${collectionName}-net`,
      type: 'network',
      policy: JSON.stringify([
        {
          AllowFromPublic: true,
          Rules: [
            { ResourceType: 'collection', Resource: [`collection/${collectionName}`] },
            { ResourceType: 'dashboard', Resource: [`collection/${collectionName}`] },
          ],
        },
      ]),
    })

    this.collection = new opensearchserverless.CfnCollection(this, 'Collection', {
      name: collectionName,
      type: 'VECTORSEARCH',
      description: description ?? 'Vector search collection for RAG knowledge base',
    })

    this.collection.addDependency(encryptionPolicy)
    this.collection.addDependency(networkPolicy)

    new opensearchserverless.CfnAccessPolicy(this, 'DataAccessPolicy', {
      name: `${collectionName}-access`,
      type: 'data',
      policy: JSON.stringify([
        {
          Rules: [
            {
              ResourceType: 'index',
              Resource: [`index/${collectionName}/*`],
              Permission: ['aoss:*'],
            },
            {
              ResourceType: 'collection',
              Resource: [`collection/${collectionName}`],
              Permission: ['aoss:*'],
            },
          ],
          Principal: [
            `arn:aws:iam::${cdk.Aws.ACCOUNT_ID}:root`,
            ...additionalAccessPrincipals,
          ],
        },
      ]),
    })

    this.collectionEndpoint = this.collection.attrCollectionEndpoint
    this.collectionArn = this.collection.attrArn
    this.dashboardEndpoint = this.collection.attrDashboardEndpoint
  }
}
