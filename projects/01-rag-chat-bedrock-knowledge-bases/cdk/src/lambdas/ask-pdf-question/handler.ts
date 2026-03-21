import {
  BedrockAgentRuntimeClient,
  RetrieveAndGenerateCommand,
  type Citation,
} from '@aws-sdk/client-bedrock-agent-runtime'
import type { APIGatewayProxyEventV2, APIGatewayProxyResultV2 } from 'aws-lambda'

/** Supported chunking strategy names that callers pass as `strategy`. */
type Strategy = 'hierarchical' | 'fixed'

/** The JSON body expected in POST /chat requests. */
interface ChatRequestBody {
  question: string
  strategy: Strategy
}

/** A single citation returned alongside the generated answer. */
interface CitationResult {
  /** The verbatim text span in the generated answer that this citation supports. */
  generatedText: string
  /** Source references retrieved from the knowledge base for this span. */
  sources: Array<{
    /** Relevant chunk text retrieved from the knowledge base. */
    text: string
    /** S3 URI of the source document, if available. */
    sourceUri: string | undefined
  }>
}

/** Shape of the successful response body. */
interface ChatSuccessBody {
  answer: string
  citations: CitationResult[]
  strategy: Strategy
  knowledgeBaseId: string
}

/** Shape of the error response body. */
interface ChatErrorBody {
  error: string
  details?: string
}

const client = new BedrockAgentRuntimeClient({ region: process.env.AWS_REGION ?? 'us-east-1' })

/** Returns an API Gateway v2 proxy response with JSON body and CORS headers. */
function respond(statusCode: number, body: ChatSuccessBody | ChatErrorBody): APIGatewayProxyResultV2 {
  return {
    statusCode,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

/**
 * Resolves the Bedrock Knowledge Base ID from environment variables based on
 * the requested chunking strategy.
 */
function resolveKnowledgeBaseId(strategy: Strategy): string {
  const envKey = strategy === 'hierarchical' ? 'HIERARCHICAL_KB_ID' : 'FIXED_KB_ID'
  const kbId = process.env[envKey]
  if (!kbId) {
    throw new Error(`Environment variable ${envKey} is not set`)
  }
  return kbId
}

/**
 * Maps a single Bedrock citation object to the leaner {@link CitationResult}
 * shape returned to callers.
 */
function mapCitation(citation: Citation): CitationResult {
  const generatedText = citation.generatedResponsePart?.textResponsePart?.text ?? ''
  const sources = (citation.retrievedReferences ?? []).map(ref => ({
    text: ref.content?.text ?? '',
    sourceUri: ref.location?.s3Location?.uri,
  }))
  return { generatedText, sources }
}

/**
 * Parses and validates the request body. Returns the typed body on success or
 * a descriptive error string on failure.
 */
function parseBody(raw: string | undefined): ChatRequestBody | string {
  if (!raw) {
    return 'Request body is empty'
  }

  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    return 'Request body is not valid JSON'
  }

  if (typeof parsed !== 'object' || parsed === null) {
    return 'Request body must be a JSON object'
  }

  const { question, strategy } = parsed as Record<string, unknown>

  if (typeof question !== 'string' || question.trim() === '') {
    return '`question` must be a non-empty string'
  }
  if (strategy !== 'hierarchical' && strategy !== 'fixed') {
    return '`strategy` must be "hierarchical" or "fixed"'
  }

  return { question: question.trim(), strategy: strategy as Strategy }
}

/**
 * Lambda handler for the POST /chat endpoint.
 *
 * Expects a JSON body of the shape:
 * ```json
 * { "question": "...", "strategy": "hierarchical" | "fixed" }
 * ```
 *
 * Calls the Bedrock `RetrieveAndGenerate` API against the knowledge base
 * selected by `strategy` and returns the generated answer with citations.
 */
export async function handler(event: APIGatewayProxyEventV2): Promise<APIGatewayProxyResultV2> {
  const bodyOrError = parseBody(event.body)
  if (typeof bodyOrError === 'string') {
    return respond(400, { error: 'Validation failed', details: bodyOrError })
  }

  const { question, strategy } = bodyOrError

  let knowledgeBaseId: string
  try {
    knowledgeBaseId = resolveKnowledgeBaseId(strategy)
  } catch (err) {
    return respond(500, { error: 'Configuration error', details: (err as Error).message })
  }

  const modelArn = process.env.MODEL_ARN
  if (!modelArn) {
    return respond(500, { error: 'Configuration error', details: 'MODEL_ARN is not set' })
  }

  try {
    const command = new RetrieveAndGenerateCommand({
      input: { text: question },
      retrieveAndGenerateConfiguration: {
        type: 'KNOWLEDGE_BASE',
        knowledgeBaseConfiguration: {
          knowledgeBaseId,
          modelArn,
        },
      },
    })

    const response = await client.send(command)

    return respond(200, {
      answer: response.output?.text ?? '',
      citations: (response.citations ?? []).map(mapCitation),
      strategy,
      knowledgeBaseId,
    })
  } catch (err) {
    const error = err as Error
    return respond(502, { error: 'Bedrock API error', details: error.message })
  }
}
