import * as cdk from 'aws-cdk-lib'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as s3 from 'aws-cdk-lib/aws-s3'
import type { Construct } from 'constructs'
import { SafetyGatewayFunction } from '../constructs/safety-gateway-function.ts'
import { InvokeApi } from '../constructs/invoke-api.ts'
import { ContentSafetyGuardrail } from '../constructs/content-safety-guardrail.ts'

const MODEL_ID = 'us.anthropic.claude-haiku-4-5-20251001-v1:0'

export class GuardrailSafety extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    const bedrockAuditBucket = new s3.Bucket(this, 'BedrockAuditBucket', {
      bucketName: `bedrock-audit-logs-${this.account}-${this.region}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    })

    const guardrail = new ContentSafetyGuardrail(this, 'ContentSafetyGuardrail')
    const safetyGateway = new SafetyGatewayFunction(this, 'SafetyGatewayFunction')

    safetyGateway.function.addEnvironment('MODEL_ID', MODEL_ID)
    safetyGateway.function.addEnvironment('GUARDRAIL_ID', guardrail.guardrailId)
    safetyGateway.function.addEnvironment('GUARDRAIL_VERSION', guardrail.guardrailVersion)

    // Cross-region inference profiles (us.* prefix) route requests to any
    // region in the geo (us-east-1, us-east-2, us-west-2). Bedrock makes two
    // IAM checks per invocation:
    //   1. The inference-profile ARN — always in the stack's deploy region.
    //   2. The underlying foundation-model ARN — in whichever region Bedrock
    //      routes to, with the geo prefix stripped from the model ID.
    // The foundation-model resource uses a wildcard region so the policy
    // remains valid regardless of which region handles the actual inference.
    safetyGateway.function.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'AllowBedrockInvokeModel',
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:InvokeModel'],
        resources: [
          'arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5*',
          `arn:aws:bedrock:${this.region}:${this.account}:inference-profile/${MODEL_ID}`,
        ],
      }),
    )

    safetyGateway.function.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'AllowBedrockApplyGuardrail',
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:ApplyGuardrail'],
        resources: [guardrail.guardrailArn],
      }),
    )

    const invokeApi = new InvokeApi(this, 'InvokeApi', {
      handler: safetyGateway.function,
    })

    new cdk.CfnOutput(this, 'InvokeApiEndpoint', {
      value: invokeApi.invokeEndpoint,
      description: 'URL for the POST /invoke endpoint',
    })
  }
}
