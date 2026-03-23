/**
 * test-guardrail.ts
 *
 * Smoke-tests the deployed POST /invoke endpoint by running three test cases:
 * a happy-path request, a missing-prompt request, and an empty-body request.
 *
 * Usage:
 *   bun run scripts/test-guardrail.ts
 *
 * Prerequisites:
 *   - The Sandbox-GuardrailSafety CloudFormation stack is deployed
 *   - AWS credentials are configured in the current environment
 */

const STACK_NAME = 'Sandbox-GuardrailSafety'
const REGION = 'us-east-1'
const OUTPUT_KEY = 'InvokeApiEndpoint'

/** The JSON body expected on POST /invoke requests. */
interface InvokeRequestBody {
  prompt?: string
  session_id?: string
}

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

/** A single test case definition. */
interface TestCase {
  name: string
  body: InvokeRequestBody
  expectedStatus: number
}

/** The outcome of running a single test case. */
interface TestResult {
  name: string
  passed: boolean
  expectedStatus: number
  actualStatus: number
  responseBody: InvokeSuccessBody | InvokeErrorBody | unknown
}

const TEST_CASES: TestCase[] = [
  {
    name: 'happy path -- valid prompt and session_id',
    body: { prompt: 'What is Amazon Bedrock?', session_id: 'test-1' },
    expectedStatus: 200,
  },
  {
    name: 'missing prompt field',
    body: { session_id: 'test-2' },
    expectedStatus: 400,
  },
  {
    name: 'empty body',
    body: {},
    expectedStatus: 400,
  },
]

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

/**
 * Posts the given body to the invoke endpoint and returns the HTTP status code
 * and parsed response body.
 */
async function post(
  endpoint: string,
  body: InvokeRequestBody,
): Promise<{ status: number; json: unknown }> {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const json = await response.json()
  return { status: response.status, json }
}

/**
 * Runs a single test case against the endpoint. Returns the result indicating
 * whether the actual status code matched the expected one.
 */
async function runTest(endpoint: string, testCase: TestCase): Promise<TestResult> {
  const { status, json } = await post(endpoint, testCase.body)
  const passed = status === testCase.expectedStatus
  return {
    name: testCase.name,
    passed,
    expectedStatus: testCase.expectedStatus,
    actualStatus: status,
    responseBody: json,
  }
}

/** Prints a single test result to stdout in a readable format. */
function printResult(result: TestResult): void {
  const label = result.passed ? 'PASS' : 'FAIL'
  const statusInfo = result.passed
    ? `${result.actualStatus}`
    : `expected ${result.expectedStatus}, got ${result.actualStatus}`
  console.log(`  [${label}] ${result.name} (${statusInfo})`)
  if (!result.passed) {
    console.log(`         response: ${JSON.stringify(result.responseBody)}`)
  }
}

async function main() {
  console.log(`Resolving endpoint from CloudFormation stack "${STACK_NAME}"...`)
  const endpoint = await resolveEndpoint()
  console.log(`Endpoint: ${endpoint}`)
  console.log('')
  console.log(`Running ${TEST_CASES.length} test cases...`)
  console.log('')

  const results: TestResult[] = []

  for (const testCase of TEST_CASES) {
    const result = await runTest(endpoint, testCase)
    printResult(result)
    results.push(result)
  }

  const passed = results.filter(r => r.passed).length
  const failed = results.length - passed

  console.log('')
  console.log(`Results: ${passed} passed, ${failed} failed`)

  if (failed > 0) {
    process.exit(1)
  }
}

main()
