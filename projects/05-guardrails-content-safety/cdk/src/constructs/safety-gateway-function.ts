import * as cdk from 'aws-cdk-lib'
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs'
import * as iam from 'aws-cdk-lib/aws-iam'
import { Construct } from 'constructs'
import * as path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/**
 * Creates the `safety-gateway` Lambda function, which serves as the
 * orchestrator for the content-safety pipeline.
 *
 * The function handles POST /invoke requests, runs pre-processing (PII
 * detection, jailbreak detection), invokes Bedrock with guardrails, and
 * applies post-processing (audit logging, output validation).
 */
export class SafetyGatewayFunction extends Construct {
  /** The underlying Node.js Lambda function. */
  public readonly function: nodejs.NodejsFunction

  constructor(scope: Construct, id: string) {
    super(scope, id)

    this.function = new nodejs.NodejsFunction(this, 'Function', {
      functionName: 'safety-gateway',
      entry: path.join(__dirname, '../lambdas/safety-gateway/handler.ts'),
      handler: 'handler',
      runtime: lambda.Runtime.NODEJS_22_X,
      timeout: cdk.Duration.seconds(30),
      bundling: {
        nodeModules: ['@anthropic-ai/tokenizer'],
      },
    })

    this.function.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'AllowComprehendDetectPiiEntities',
        effect: iam.Effect.ALLOW,
        actions: ['comprehend:DetectPiiEntities'],
        resources: ['*'],
      })
    )
  }
}
