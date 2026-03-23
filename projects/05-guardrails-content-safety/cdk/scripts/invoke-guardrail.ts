/**
 * invoke-guardrail.ts
 *
 * Sends a single prompt to the deployed POST /invoke endpoint and prints the
 * response. The prompt is taken from the command-line arguments.
 *
 * Usage:
 *   bun run scripts/invoke-guardrail.ts "What is Amazon Bedrock?"
 *
 * Prerequisites:
 *   - The Sandbox-GuardrailSafety CloudFormation stack is deployed
 *   - AWS credentials are configured in the current environment
 */

const STACK_NAME = 'Sandbox-GuardrailSafety'
const REGION = 'us-east-1'
const OUTPUT_KEY = 'InvokeApiEndpoint'

/** Shape of a successful response from POST /invoke. */
interface InvokeSuccessBody {
  output: string
  pii_redacted: boolean
  guardrail_action: string
}

/** Shape of an error response from POST /invoke. */
interface InvokeErrorBody {
  error: string
  details?: string
}

/**
 * Resolves the `InvokeApiEndpoint` CloudFormation output value from the
 * deployed stack by shelling out to the AWS CLI.
 *
 * Exits the process if the endpoint cannot be resolved.
 */
async function resolveEndpoint(): Promise<string> {
  const proc = Bun.spawn(
    [
      'aws',
      'cloudformation',
      'describe-stacks',
      '--stack-name',
      STACK_NAME,
      '--region',
      REGION,
      '--query',
      `Stacks[0].Outputs[?OutputKey=='${OUTPUT_KEY}'].OutputValue`,
      '--output',
      'text',
    ],
    { stdout: 'pipe', stderr: 'pipe' },
  )

  const [stdout, stderr, exitCode] = await Promise.all([
    new Response(proc.stdout).text(),
    new Response(proc.stderr).text(),
    proc.exited,
  ])

  if (exitCode !== 0) {
    console.error(`Failed to describe stack "${STACK_NAME}":`)
    console.error(stderr.trim())
    process.exit(1)
  }

  const endpoint = stdout.trim()
  if (!endpoint || endpoint === 'None') {
    console.error(
      `Could not resolve "${OUTPUT_KEY}" from stack "${STACK_NAME}". Is the stack deployed?`,
    )
    process.exit(1)
  }

  return endpoint
}

async function main() {
  const prompt = process.argv.slice(2).join(' ').trim()

  if (!prompt) {
    console.error('Usage: bun run scripts/invoke-guardrail.ts "<prompt>"')
    process.exit(1)
  }

  const sessionId = `cli-${Date.now()}`

  console.log(`Resolving endpoint from CloudFormation stack "${STACK_NAME}"...`)
  const endpoint = await resolveEndpoint()
  console.log(`Endpoint: ${endpoint}`)
  console.log('')
  console.log(`Prompt:     ${prompt}`)
  console.log(`Session ID: ${sessionId}`)
  console.log('')

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, session_id: sessionId }),
  })

  const json = (await response.json()) as InvokeSuccessBody | InvokeErrorBody

  if (!response.ok || 'error' in json) {
    const body = json as InvokeErrorBody
    console.error(`HTTP ${response.status} - ${body.error}${body.details ? `: ${body.details}` : ''}`)
    process.exit(1)
  }

  const body = json as InvokeSuccessBody
  console.log(`Output:          ${body.output}`)
  console.log(`PII redacted:    ${body.pii_redacted}`)
  console.log(`Guardrail action: ${body.guardrail_action}`)
}

main()
