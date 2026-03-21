import * as opensearchserverless from 'aws-cdk-lib/aws-opensearchserverless'
import { Construct } from 'constructs'

export interface OpenSearchVectorIndexProps {
  /** The collection API endpoint (attrCollectionEndpoint) from an OpenSearchVectorCollection. */
  collectionEndpoint: string
  /**
   * Name of the index to create.
   * Must match the pattern: ^(?![_-])[a-z][a-z0-9_-]*$
   */
  indexName: string
}

/**
 * Creates an OpenSearch Serverless vector index configured for use with
 * an Amazon Bedrock Knowledge Base.
 *
 * The index is configured with:
 * - k-NN enabled (faiss engine, hnsw algorithm, l2 space type)
 * - bedrock-knowledge-base-default-vector: knn_vector field, 1536 dimensions
 * - AMAZON_BEDROCK_TEXT_CHUNK: indexed text field
 * - AMAZON_BEDROCK_METADATA: stored (non-indexed) text field
 */
export class OpenSearchVectorIndex extends Construct {
  /** The underlying CfnIndex resource. */
  public readonly index: opensearchserverless.CfnIndex

  constructor(scope: Construct, id: string, props: OpenSearchVectorIndexProps) {
    super(scope, id)

    this.index = new opensearchserverless.CfnIndex(this, 'Index', {
      collectionEndpoint: props.collectionEndpoint,
      indexName: props.indexName,
      settings: {
        index: {
          knn: true,
        },
      },
      mappings: {
        properties: {
          'bedrock-knowledge-base-default-vector': {
            type: 'knn_vector',
            dimension: 1024,
            method: {
              engine: 'faiss',
              name: 'hnsw',
              spaceType: 'l2',
            },
          },
          AMAZON_BEDROCK_TEXT_CHUNK: {
            type: 'text',
            index: true,
          },
          AMAZON_BEDROCK_METADATA: {
            type: 'text',
            index: false,
          },
        },
      },
    })
  }
}
