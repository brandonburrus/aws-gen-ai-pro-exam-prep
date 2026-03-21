import * as cdk from 'aws-cdk-lib'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs'
import { Construct } from 'constructs'
import * as path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export interface AskPdfQuestionFunctionProps {
  /** Knowledge base ID for the hierarchical-chunking knowledge base. */
  hierarchicalKnowledgeBaseId: string
  /** Knowledge base ID for the fixed-chunking knowledge base. */
  fixedKnowledgeBaseId: string
  /**
   * ARN of the knowledge base used to grant `bedrock:Retrieve` permission.
   * This is the ARN for the hierarchical knowledge base.
   */
  hierarchicalKnowledgeBaseArn: string
  /**
   * ARN of the knowledge base used to grant `bedrock:Retrieve` permission.
   * This is the ARN for the fixed-chunking knowledge base.
   */
  fixedKnowledgeBaseArn: string
  /**
   * ARN of the Bedrock foundation model used for generation.
   * Both `bedrock:InvokeModel` and `bedrock:RetrieveAndGenerate` will be
   * granted for this model.
   */
  modelArn: string
}

/**
 * Creates the `ask-pdf-question` Lambda function, which accepts a `question`
 * and a `strategy` ("hierarchical" or "fixed"), calls the Bedrock
 * `RetrieveAndGenerate` API against the corresponding knowledge base, and
 * returns the generated answer with citations.
 *
 * IAM permissions granted to the function's execution role:
 * - `bedrock:RetrieveAndGenerate` (not resource-constrainable, scoped to `*`)
 * - `bedrock:Retrieve` on both knowledge base ARNs
 * - `bedrock:InvokeModel` on the generation model ARN
 */
export class AskPdfQuestionFunction extends Construct {
  /** The underlying Node.js Lambda function. */
  public readonly function: nodejs.NodejsFunction

  constructor(scope: Construct, id: string, props: AskPdfQuestionFunctionProps) {
    super(scope, id)

    const {
      hierarchicalKnowledgeBaseId,
      fixedKnowledgeBaseId,
      hierarchicalKnowledgeBaseArn,
      fixedKnowledgeBaseArn,
      modelArn,
    } = props

    this.function = new nodejs.NodejsFunction(this, 'Function', {
      functionName: 'ask-pdf-question',
      entry: path.join(__dirname, '../lambdas/ask-pdf-question/handler.ts'),
      handler: 'handler',
      runtime: lambda.Runtime.NODEJS_22_X,
      timeout: cdk.Duration.seconds(30),
      environment: {
        HIERARCHICAL_KB_ID: hierarchicalKnowledgeBaseId,
        FIXED_KB_ID: fixedKnowledgeBaseId,
        MODEL_ARN: modelArn,
      },
    })

    this.function.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'BedrockRetrieveAndGenerate',
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:RetrieveAndGenerate'],
        // RetrieveAndGenerate does not support resource-level restrictions.
        resources: ['*'],
      }),
    )

    this.function.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'BedrockRetrieveKnowledgeBases',
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:Retrieve'],
        resources: [hierarchicalKnowledgeBaseArn, fixedKnowledgeBaseArn],
      }),
    )

    this.function.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'BedrockInvokeGenerationModel',
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:InvokeModel'],
        resources: [modelArn],
      }),
    )
  }
}
