import * as path from 'node:path'
import { fileURLToPath } from 'node:url'
import * as cdk from 'aws-cdk-lib'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as lambda from 'aws-cdk-lib/aws-lambda'
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs'
import * as s3 from 'aws-cdk-lib/aws-s3'
import type { Construct } from 'constructs'
import { BedrockPromptTemplates } from '../constructs/bedrock-prompt-templates.ts'
import { EvaluationDashboard } from '../constructs/evaluation-dashboard.ts'
import { EvaluationStateMachine } from '../constructs/evaluation-state-machine.ts'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/**
 * Bedrock model IDs for the two models under evaluation.
 * Amazon Nova models are first-party AWS models and do not require
 * third-party Marketplace subscription acceptance, which was the root cause
 * of the access-denied errors encountered with the Anthropic Claude models.
 *
 * NOVA_PRO_INFERENCE_PROFILE_ID is used as the judge model for score-output.
 * Both model IDs are also referenced inside EvaluationStateMachine.
 */
const NOVA_PRO_INFERENCE_PROFILE_ID = 'us.amazon.nova-pro-v1:0'

/**
 * Bare foundation model IDs for both Nova models (no region prefix).
 * Used to construct per-region foundation model ARNs for the two-statement
 * cross-region IAM policy required by geographic cross-region inference.
 */
const NOVA_LITE_FM_ID = 'amazon.nova-lite-v1:0'
const NOVA_PRO_FM_ID = 'amazon.nova-pro-v1:0'

/**
 * Destination regions the US geo cross-region inference profiles can route to
 * when called from us-east-1. IAM must explicitly grant bedrock:InvokeModel on
 * the foundation model ARN in each of these regions — a wildcard in the region
 * field is not evaluated correctly for cross-region routing authorization.
 *
 * Source: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html
 * US Anthropic Claude Haiku 4.5 / Sonnet 4.5: us-east-1 -> us-east-1, us-east-2, us-west-2
 */
const US_INFERENCE_DESTINATION_REGIONS = ['us-east-1', 'us-east-2', 'us-west-2']

/**
 * Primary stack for Project 02: Prompt Management and Evaluation Pipeline.
 *
 * Provisions:
 * - Three versioned Bedrock Prompt Management templates
 * - An S3 bucket for evaluation results
 * - Three Lambda functions (invoke-template, score-output, aggregate-results)
 *   with least-privilege IAM policies
 * - A Step Functions Standard workflow orchestrating the full evaluation loop
 */
export class PromptPipeline extends cdk.Stack {
  /** Results bucket exposed for downstream references (e.g. Step Functions pass state). */
  public readonly resultsBucket: s3.Bucket
  /** Lambda that renders a Bedrock prompt template and invokes a model. */
  public readonly invokeTemplateFn: nodejs.NodejsFunction
  /** Lambda that scores a model output using a judge model. */
  public readonly scoreOutputFn: nodejs.NodejsFunction
  /** Lambda that aggregates all scores, emits CloudWatch metrics, and writes to S3. */
  public readonly aggregateResultsFn: nodejs.NodejsFunction
  /** Step Functions Standard workflow that drives the evaluation pipeline. */
  public readonly evaluationStateMachine: EvaluationStateMachine
  /** CloudWatch Dashboard showing Relevance and Consistency metrics. */
  public readonly evaluationDashboard: EvaluationDashboard

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    const promptTemplates = new BedrockPromptTemplates(this, 'PromptTemplates')

    // S3 bucket for evaluation results.
    this.resultsBucket = new s3.Bucket(this, 'EvaluationResultsBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      // DESTROY + autoDeleteObjects is appropriate for a sandbox/learning project.
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    })

    // invoke-template Lambda: fetches a Bedrock Prompt Management template by
    // versioned ARN, substitutes variables, and calls the Converse API with the
    // specified model.
    this.invokeTemplateFn = new nodejs.NodejsFunction(this, 'InvokeTemplateFn', {
      entry: path.join(__dirname, '../lambdas/invoke-template/handler.ts'),
      handler: 'handler',
      runtime: lambda.Runtime.NODEJS_22_X,
      timeout: cdk.Duration.seconds(60),
      memorySize: 256,
      environment: {
        PROMPT_ARN_DIRECT_INSTRUCTION: promptTemplates.promptArns['direct-instruction'],
        PROMPT_ARN_CHAIN_OF_THOUGHT: promptTemplates.promptArns['chain-of-thought'],
        PROMPT_ARN_FEW_SHOT: promptTemplates.promptArns['few-shot'],
      },
    })

    // Allow GetPrompt on all prompts in this account/region.
    // The exact prompt IDs are only known after deploy, so we use a wildcard
    // on the prompt resource type which is the narrowest practical scope.
    this.invokeTemplateFn.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'BedrockGetPrompt',
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:GetPrompt'],
        resources: [`arn:aws:bedrock:us-east-1:${this.account}:prompt/*`],
      }),
    )

    // Statement 1: allow invoking the two US Nova geo cross-region inference profiles.
    // These are account-scoped resources in the source region (us-east-1).
    this.invokeTemplateFn.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'BedrockInvokeInferenceProfile',
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:InvokeModel'],
        resources: [
          `arn:aws:bedrock:us-east-1:${this.account}:inference-profile/us.${NOVA_LITE_FM_ID}`,
          `arn:aws:bedrock:us-east-1:${this.account}:inference-profile/us.${NOVA_PRO_FM_ID}`,
        ],
      }),
    )

    // Statement 2: allow invoking the foundation model in every destination region
    // the US inference profiles can route to from us-east-1 (us-east-1, us-east-2,
    // us-west-2). A wildcard in the region field is not correctly evaluated for
    // cross-region routing; each destination region must be listed explicitly.
    this.invokeTemplateFn.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'BedrockInvokeFoundationModel',
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:InvokeModel'],
        resources: US_INFERENCE_DESTINATION_REGIONS.flatMap(region => [
          `arn:aws:bedrock:${region}::foundation-model/${NOVA_LITE_FM_ID}`,
          `arn:aws:bedrock:${region}::foundation-model/${NOVA_PRO_FM_ID}`,
        ]),
      }),
    )

    // score-output Lambda: receives the invoke-template result and scores the
    // model output using Nova Pro as the judge model via the Bedrock Converse API.
    this.scoreOutputFn = new nodejs.NodejsFunction(this, 'ScoreOutputFn', {
      entry: path.join(__dirname, '../lambdas/score-output/handler.ts'),
      handler: 'handler',
      runtime: lambda.Runtime.NODEJS_22_X,
      timeout: cdk.Duration.seconds(60),
      memorySize: 256,
      environment: {
        JUDGE_MODEL_ID: NOVA_PRO_INFERENCE_PROFILE_ID,
      },
    })

    // Statement 1: allow invoking the Nova Pro US geo cross-region inference profile.
    this.scoreOutputFn.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'BedrockInvokeJudgeInferenceProfile',
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:InvokeModel'],
        resources: [
          `arn:aws:bedrock:us-east-1:${this.account}:inference-profile/us.${NOVA_PRO_FM_ID}`,
        ],
      }),
    )

    // Statement 2: allow invoking the Nova Pro foundation model in every destination
    // region the US inference profile routes to from us-east-1.
    this.scoreOutputFn.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'BedrockInvokeJudgeFoundationModel',
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:InvokeModel'],
        resources: US_INFERENCE_DESTINATION_REGIONS.map(
          region => `arn:aws:bedrock:${region}::foundation-model/${NOVA_PRO_FM_ID}`,
        ),
      }),
    )

    // aggregate-results Lambda: receives the full array of scored items,
    // computes per-template and per-model averages, publishes CloudWatch
    // metrics, and writes the full results JSON to S3.
    this.aggregateResultsFn = new nodejs.NodejsFunction(this, 'AggregateResultsFn', {
      entry: path.join(__dirname, '../lambdas/aggregate-results/handler.ts'),
      handler: 'handler',
      runtime: lambda.Runtime.NODEJS_22_X,
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        RESULTS_BUCKET_NAME: this.resultsBucket.bucketName,
      },
    })

    // S3 write access using the CDK L2 grant helper (grants PutObject and
    // the minimal set of supporting actions on the bucket and its objects).
    this.resultsBucket.grantWrite(this.aggregateResultsFn)

    // PutMetricData is not resource-constrainable in IAM — the namespace is
    // not an ARN-addressable resource — so we must use a wildcard resource.
    this.aggregateResultsFn.addToRolePolicy(
      new iam.PolicyStatement({
        sid: 'CloudWatchPutMetricData',
        effect: iam.Effect.ALLOW,
        actions: ['cloudwatch:PutMetricData'],
        resources: ['*'],
      }),
    )

    // Expose the prompt ARNs and bucket name as CloudFormation outputs so
    // they are visible in the console after deploy.
    new cdk.CfnOutput(this, 'ResultsBucketName', {
      value: this.resultsBucket.bucketName,
      description: 'S3 bucket where evaluation-results.json is written',
    })

    new cdk.CfnOutput(this, 'DirectInstructionPromptArn', {
      value: promptTemplates.promptArns['direct-instruction'],
      description: 'Versioned ARN of the direct-instruction Bedrock prompt template',
    })

    new cdk.CfnOutput(this, 'ChainOfThoughtPromptArn', {
      value: promptTemplates.promptArns['chain-of-thought'],
      description: 'Versioned ARN of the chain-of-thought Bedrock prompt template',
    })

    new cdk.CfnOutput(this, 'FewShotPromptArn', {
      value: promptTemplates.promptArns['few-shot'],
      description: 'Versioned ARN of the few-shot Bedrock prompt template',
    })

    // Step Functions state machine: orchestrates the full evaluation loop.
    // CDK automatically grants lambda:InvokeFunction from the state machine's
    // execution role to each Lambda referenced in a LambdaInvoke task.
    this.evaluationStateMachine = new EvaluationStateMachine(this, 'EvaluationStateMachine', {
      invokeTemplateFn: this.invokeTemplateFn,
      scoreOutputFn: this.scoreOutputFn,
      aggregateResultsFn: this.aggregateResultsFn,
      promptArns: promptTemplates.promptArns,
    })

    new cdk.CfnOutput(this, 'StateMachineArn', {
      value: this.evaluationStateMachine.stateMachine.stateMachineArn,
      description: 'ARN of the PromptEvaluationPipeline state machine',
    })

    this.evaluationDashboard = new EvaluationDashboard(this, 'EvaluationDashboard')

    new cdk.CfnOutput(this, 'DashboardName', {
      value: this.evaluationDashboard.dashboard.dashboardName,
      description: 'CloudWatch Dashboard for Relevance and Consistency evaluation metrics',
    })
  }
}
