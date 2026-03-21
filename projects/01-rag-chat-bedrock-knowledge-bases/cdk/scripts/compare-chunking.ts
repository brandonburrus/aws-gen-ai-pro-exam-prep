/**
 * compare-chunking.ts
 *
 * Sends 5 AWS Certified AI Practitioner (AIF-C01) exam-focused questions to the
 * deployed chat API using both chunking strategies (hierarchical and fixed-size),
 * then writes a side-by-side comparison to `chunking-comparison.md`.
 *
 * Usage:
 *   bun run scripts/compare-chunking.ts
 *
 * Prerequisites:
 *   - The SandboxChatStack CloudFormation stack is deployed
 *   - AWS credentials are configured in the current environment
 *   - PDFs have been uploaded to the S3 bucket and both data sources have been synced
 */

import { join } from 'node:path'

const STACK_NAME = 'Sandbox-ChatStack'
const REGION = 'us-east-1'
const OUTPUT_KEY = 'ChatApiEndpoint'

const QUESTIONS = [
  'What are the differences between fine-tuning, prompt engineering, and retrieval-augmented generation as techniques for customizing foundation model responses?',
  'Which AWS services are used to build a machine learning pipeline, and what role does each service play in the data preparation, training, and deployment stages?',
  'How does Amazon Bedrock evaluate foundation model performance using built-in evaluation jobs, and what metrics does it report?',
  'What are the responsible AI practices recommended by AWS, including fairness, toxicity detection, and the use of human review with Amazon Augmented AI?',
  'Explain how Amazon Bedrock Guardrails work to filter harmful content and enforce topic boundaries in generative AI applications.',
]

type Strategy = 'hierarchical' | 'fixed'

/** Raw success shape returned by the POST /chat Lambda handler. */
interface ChatSuccessBody {
  answer: string
  strategy: Strategy
  knowledgeBaseId: string
}

/** Raw error shape returned by the POST /chat Lambda handler. */
interface ChatErrorBody {
  error: string
  details?: string
}

/** Normalised result returned by {@link askQuestion}. */
type QuestionResult = { answer: string } | { error: string }

/** Per-question collected output written to the markdown report. */
interface ComparisonEntry {
  question: string
  hierarchical: string
  fixed: string
}

/**
 * Resolves the `ChatApiEndpoint` CloudFormation output value from the deployed
 * stack by shelling out to the AWS CLI.
 *
 * Exits the process if the endpoint cannot be resolved (stack not deployed,
 * credentials not configured, etc.).
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
 * Posts a single question to the chat API with the specified chunking strategy
 * and returns the generated answer or an error description.
 */
async function askQuestion(
  endpoint: string,
  question: string,
  strategy: Strategy,
): Promise<QuestionResult> {
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, strategy }),
    })

    const json = (await response.json()) as ChatSuccessBody | ChatErrorBody

    if (response.ok && 'answer' in json) {
      return { answer: json.answer }
    }

    const errBody = json as ChatErrorBody
    const message = errBody.details ? `${errBody.error}: ${errBody.details}` : errBody.error
    return { error: message }
  } catch (err) {
    return { error: (err as Error).message }
  }
}

/**
 * Formats a {@link QuestionResult} as a plain string suitable for embedding in
 * the markdown report. Errors are prefixed so they stand out during review.
 */
function formatResult(result: QuestionResult): string {
  if ('error' in result) {
    return `**Error:** ${result.error}`
  }
  return result.answer
}

/**
 * Builds the full markdown content for the comparison report from the collected
 * results.
 */
function buildMarkdown(entries: ComparisonEntry[], endpoint: string): string {
  const timestamp = new Date().toISOString()

  const sections = entries
    .map((entry, i) => {
      return [
        `## Question ${i + 1}`,
        '',
        `> ${entry.question}`,
        '',
        '### Hierarchical Chunking',
        '',
        entry.hierarchical,
        '',
        '### Fixed-Size Chunking',
        '',
        entry.fixed,
      ].join('\n')
    })
    .join('\n\n---\n\n')

  return [
    '# Chunking Strategy Comparison',
    '',
    `Generated: ${timestamp}`,
    '',
    `Endpoint: \`${endpoint}\``,
    '',
    '---',
    '',
    sections,
    '',
  ].join('\n')
}

async function main() {
  console.log(`Resolving endpoint from CloudFormation stack "${STACK_NAME}"...`)
  const endpoint = await resolveEndpoint()
  console.log(`Endpoint: ${endpoint}`)
  console.log('')

  const entries: ComparisonEntry[] = []

  for (let i = 0; i < QUESTIONS.length; i++) {
    const question = QUESTIONS[i]
    process.stdout.write(`[${i + 1}/${QUESTIONS.length}] Asking both strategies...`)

    const [hierarchicalResult, fixedResult] = await Promise.all([
      askQuestion(endpoint, question, 'hierarchical'),
      askQuestion(endpoint, question, 'fixed'),
    ])

    entries.push({
      question,
      hierarchical: formatResult(hierarchicalResult),
      fixed: formatResult(fixedResult),
    })

    process.stdout.write(' done\n')
  }

  const markdown = buildMarkdown(entries, endpoint)
  const outputPath = join(import.meta.dir, '..', 'chunking-comparison.md')
  await Bun.write(outputPath, markdown)

  console.log('')
  console.log(`Wrote chunking-comparison.md with ${entries.length} comparisons.`)
}

main()
