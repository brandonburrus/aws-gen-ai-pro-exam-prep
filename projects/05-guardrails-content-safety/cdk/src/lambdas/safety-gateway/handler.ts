import type { APIGatewayProxyEventV2, APIGatewayProxyResultV2 } from 'aws-lambda'
import { validPromptSize } from './token-counter'
import { redactPII } from './pii-redactor'
import { BedrockRuntimeClient, ConverseCommand } from '@aws-sdk/client-bedrock-runtime'

const MODEL_ID = process.env.MODEL_ID ?? 'us.anthropic.claude-haiku-4-5-20251001-v1:0'

const bedrock = new BedrockRuntimeClient({
  region: process.env.AWS_REGION ?? 'us-east-1',
})

/** The JSON body expected on POST /invoke requests. */
interface InvokeRequestBody {
  prompt: string
  session_id: string
}

/** Shape of the successful response body. */
interface InvokeSuccessBody {
  output: string
  pii_redacted: boolean
  guardrail_action: string
}

/** Shape of the error response body. */
interface InvokeErrorBody {
  error: string
  details?: string
}

function respond(
  statusCode: number,
  body: InvokeSuccessBody | InvokeErrorBody,
): APIGatewayProxyResultV2 {
  return {
    statusCode,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

/**
 * Parses and validates the request body. Returns the typed body on success or
 * a descriptive error string on failure.
 */
function parseBody(raw: string | undefined | null): InvokeRequestBody | string {
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

  const { prompt, session_id } = parsed as Record<string, unknown>

  if (typeof prompt !== 'string' || prompt.trim() === '') {
    return '`prompt` must be a non-empty string'
  }
  if (typeof session_id !== 'string' || session_id.trim() === '') {
    return '`session_id` must be a non-empty string'
  }

  return { prompt: prompt.trim(), session_id: session_id.trim() }
}

/**
 * Lambda handler for the POST /invoke endpoint.
 */
export async function handler(event: APIGatewayProxyEventV2): Promise<APIGatewayProxyResultV2> {
  const bodyOrError = parseBody(event.body)
  if (typeof bodyOrError === 'string') {
    return respond(400, {
      error: 'Validation failed',
      details: bodyOrError,
    })
  }

  try {
    validPromptSize(bodyOrError.prompt)
  } catch {
    return respond(413, {
      error: 'Request too large',
      details: 'Prompt exceeds maximum token limit',
    })
  }

  const {
    redactedText: redactedPrompt,
    didRedact,
  } = await redactPII(bodyOrError.prompt)

  const response = await bedrock.send(
    new ConverseCommand({
      modelId: MODEL_ID,
      messages: [
        {
          role: 'user',
          content: [
            { text: redactedPrompt }
          ]
        }
      ],
      guardrailConfig: {
        guardrailIdentifier: process.env.GUARDRAIL_ID ?? 'content-safety-guardrail',
        guardrailVersion: process.env.GUARDRAIL_VERSION ?? '1',
      },
    })
  )

  const bedrockResponse = response.output?.message?.content?.[0]?.text
  // stopReason is set to 'guardrail_intervened' when the guardrail blocks content;
  // otherwise it's 'end_turn' or another normal completion reason.
  const guardrailAction = response.stopReason === 'guardrail_intervened' ? 'INTERVENED' : 'NONE'

  return respond(200, {
    output: bedrockResponse ?? '<no response>',
    pii_redacted: didRedact,
    guardrail_action: guardrailAction,
  })
}
