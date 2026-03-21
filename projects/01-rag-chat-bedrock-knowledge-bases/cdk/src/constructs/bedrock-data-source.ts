import * as bedrock from 'aws-cdk-lib/aws-bedrock'
import { Construct } from 'constructs'

/**
 * Hierarchical chunking splits documents into two layers: parent chunks used
 * for context and smaller child chunks used for retrieval. At query time
 * Bedrock retrieves child chunks then substitutes the parent for broader context.
 */
export interface HierarchicalChunkingConfig {
  strategy: 'HIERARCHICAL'
  /** Maximum tokens per parent (first-layer) chunk. */
  parentMaxTokens: number
  /** Maximum tokens per child (second-layer) chunk. */
  childMaxTokens: number
  /** Number of tokens to overlap between adjacent chunks at each layer. */
  overlapTokens: number
}

/**
 * Fixed-size chunking splits documents into chunks of a uniform token count
 * with a configurable percentage of overlap between adjacent chunks.
 */
export interface FixedSizeChunkingConfig {
  strategy: 'FIXED_SIZE'
  /** Maximum number of tokens per chunk. */
  maxTokens: number
  /** Percentage of overlap between adjacent chunks (1-99). */
  overlapPercentage: number
}

/** Union of all supported chunking strategy configurations. */
export type ChunkingConfig = HierarchicalChunkingConfig | FixedSizeChunkingConfig

export interface BedrockDataSourceProps {
  /** ID of the Bedrock Knowledge Base this data source belongs to. */
  knowledgeBaseId: string
  /** Display name for this data source. */
  dataSourceName: string
  /** ARN of the S3 bucket to use as the data source. */
  bucketArn: string
  /**
   * S3 key prefixes to include during ingestion.
   * Only objects whose keys begin with one of these prefixes will be indexed.
   * Defaults to all objects in the bucket if omitted.
   */
  inclusionPrefixes?: string[]
  /** Chunking strategy and its parameters. */
  chunkingConfig: ChunkingConfig
}

/**
 * Creates an Amazon Bedrock data source that reads PDF documents from an S3
 * bucket and ingests them into a knowledge base using the specified chunking
 * strategy.
 *
 * Supported chunking strategies:
 * - HIERARCHICAL: two-layer chunking (parent + child) with token overlap
 * - FIXED_SIZE: uniform chunk size with overlap percentage
 */
export class BedrockDataSource extends Construct {
  /** The underlying CfnDataSource resource. */
  public readonly dataSource: bedrock.CfnDataSource
  /** The auto-assigned data source ID. */
  public readonly dataSourceId: string

  constructor(scope: Construct, id: string, props: BedrockDataSourceProps) {
    super(scope, id)

    const { knowledgeBaseId, dataSourceName, bucketArn, inclusionPrefixes, chunkingConfig } = props

    const chunkingConfiguration = buildChunkingConfiguration(chunkingConfig)

    this.dataSource = new bedrock.CfnDataSource(this, 'DataSource', {
      knowledgeBaseId,
      name: dataSourceName,
      dataSourceConfiguration: {
        type: 'S3',
        s3Configuration: {
          bucketArn,
          ...(inclusionPrefixes && inclusionPrefixes.length > 0
            ? { inclusionPrefixes }
            : {}),
        },
      },
      vectorIngestionConfiguration: {
        chunkingConfiguration,
      },
    })

    this.dataSourceId = this.dataSource.attrDataSourceId
  }
}

/**
 * Maps a {@link ChunkingConfig} discriminated union to the CloudFormation
 * `ChunkingConfiguration` property shape expected by `CfnDataSource`.
 */
function buildChunkingConfiguration(
  config: ChunkingConfig,
): bedrock.CfnDataSource.ChunkingConfigurationProperty {
  if (config.strategy === 'HIERARCHICAL') {
    return {
      chunkingStrategy: 'HIERARCHICAL',
      hierarchicalChunkingConfiguration: {
        levelConfigurations: [
          { maxTokens: config.parentMaxTokens },
          { maxTokens: config.childMaxTokens },
        ],
        overlapTokens: config.overlapTokens,
      },
    }
  }

  return {
    chunkingStrategy: 'FIXED_SIZE',
    fixedSizeChunkingConfiguration: {
      maxTokens: config.maxTokens,
      overlapPercentage: config.overlapPercentage,
    },
  }
}
