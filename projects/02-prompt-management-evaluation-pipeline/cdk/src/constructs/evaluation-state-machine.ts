import * as cdk from 'aws-cdk-lib'
import type * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs'
import * as sfn from 'aws-cdk-lib/aws-stepfunctions'
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks'
import { Construct } from 'constructs'

/**
 * Five open-ended AWS questions that exercise meaningfully different answers
 * across prompting styles (direct-instruction, chain-of-thought, few-shot).
 * Hardcoded at synth time and injected into the state machine via the
 * PrepareInput Pass state.
 */
const TEST_QUESTIONS = [
  'What is the difference between Amazon S3 Standard and S3 Glacier storage classes, and when should you use each?',
  'Explain how AWS Lambda cold starts work and what strategies can reduce their impact on application latency.',
  'What are the key differences between Amazon RDS and Amazon DynamoDB, and how do you decide which to use?',
  'Describe how Amazon VPC peering works and what its limitations are compared to AWS Transit Gateway.',
  'What is the shared responsibility model in AWS, and how does it affect security obligations for EC2 instances?',
]

/**
 * Shared `role` variable value injected into every prompt template invocation.
 * Defined once here so all 6 branches per question use the same persona.
 */
const TEMPLATE_ROLE = 'an AWS solutions architect with deep expertise in cloud services'

/**
 * Shared `context` variable value injected into every prompt template invocation.
 * Frames the audience and expected answer style for the judge model.
 */
const TEMPLATE_CONTEXT =
  'You are answering questions for a technical audience studying for the AWS Certified AI ' +
  'Practitioner exam. Answers should be technically precise and reference specific AWS service ' +
  'features where relevant.'

/**
 * Ordered list of template names matching the keys in the promptArns map.
 * Kept as a typed tuple so TypeScript catches typos at compile time.
 */
const TEMPLATE_NAMES = ['direct-instruction', 'chain-of-thought', 'few-shot'] as const

/**
 * Two models under evaluation. Both use US geo cross-region inference profiles
 * which route requests across us-east-1, us-east-2, and us-west-2.
 * Amazon Nova models are first-party AWS models that do not require
 * third-party Marketplace subscription acceptance.
 */
const MODELS_UNDER_TEST = [
  { id: 'us.amazon.nova-lite-v1:0', label: 'NovaLite' },
  { id: 'us.amazon.nova-pro-v1:0', label: 'NovaPro' },
] as const

/**
 * Retry configuration applied to every LambdaInvoke task that calls Bedrock
 * indirectly. Two retries with exponential backoff absorb transient throttling
 * without failing the entire execution.
 */
const LAMBDA_RETRY_ERRORS = [
  'Lambda.ServiceException',
  'Lambda.AWSLambdaException',
  'Lambda.SdkClientException',
]

/**
 * Properties required to construct the evaluation state machine.
 * All three Lambda functions and the prompt ARN map are provisioned by
 * the parent stack and passed in here to keep infrastructure definitions
 * co-located with their resource declarations.
 */
export interface EvaluationStateMachineProps {
  /** Lambda that fetches a Bedrock prompt template and invokes a model. */
  invokeTemplateFn: nodejs.NodejsFunction
  /** Lambda that scores a model output using the judge model. */
  scoreOutputFn: nodejs.NodejsFunction
  /** Lambda that aggregates all scores, publishes metrics, and writes to S3. */
  aggregateResultsFn: nodejs.NodejsFunction
  /**
   * Map of template name to versioned Bedrock Prompt Management ARN.
   * Expected keys: "direct-instruction", "chain-of-thought", "few-shot".
   */
  promptArns: Record<string, string>
}

/**
 * CDK construct that provisions the Step Functions Standard workflow driving
 * the evaluation pipeline.
 *
 * State machine flow:
 * ```
 * PrepareInput (Pass)
 *   -> EvaluateQuestions (Map, maxConcurrency 1, iterates over 5 test questions sequentially)
 *       -> InvokeAllVariants (Parallel, 6 branches: 3 templates x 2 models)
 *           -> ScoreOutputs (Map, maxConcurrency 1, scores each branch result sequentially)
 *   -> AggregateResults (LambdaInvoke, receives ScoredItem[][], flattens internally)
 * ```
 *
 * Concurrency is intentionally limited to stay within account Lambda execution
 * quotas. The outer Map processes one question at a time (maxConcurrency 1) and
 * the inner score Map also runs sequentially (maxConcurrency 1). The Parallel
 * state fires 6 invoke-template Lambdas concurrently per question, which is the
 * peak concurrency and fits comfortably within a quota of 10.
 *
 * CDK automatically grants `lambda:InvokeFunction` from the state machine's
 * execution role to each Lambda referenced in a `LambdaInvoke` task.
 */
export class EvaluationStateMachine extends Construct {
  /** The provisioned Step Functions Standard workflow. */
  public readonly stateMachine: sfn.StateMachine

  constructor(scope: Construct, id: string, props: EvaluationStateMachineProps) {
    super(scope, id)

    const { invokeTemplateFn, scoreOutputFn, aggregateResultsFn, promptArns } = props

    // PrepareInput: inject the hardcoded question array into the execution input.
    // Using resultPath '$' replaces the entire state with { questions: [...] }
    // so the outer Map can reference $.questions.
    const prepareInput = new sfn.Pass(this, 'PrepareInput', {
      result: sfn.Result.fromObject({ questions: TEST_QUESTIONS }),
      resultPath: '$',
    })

    // InvokeAllVariants: run all 6 template+model combinations in parallel.
    // Each branch receives the current question from the Map item selector
    // and outputs an InvokeTemplateResult (the raw $.Payload from Lambda).
    const invokeAllVariants = new sfn.Parallel(this, 'InvokeAllVariants')

    for (const templateName of TEMPLATE_NAMES) {
      for (const model of MODELS_UNDER_TEST) {
        const branch = new tasks.LambdaInvoke(
          this,
          `Invoke-${templateName}-${model.label}`,
          {
            lambdaFunction: invokeTemplateFn,
            payload: sfn.TaskInput.fromObject({
              prompt_arn: promptArns[templateName],
              variables: {
                role: TEMPLATE_ROLE,
                context: TEMPLATE_CONTEXT,
                // Pull the question from the Map item selector output.
                'question.$': '$.question',
              },
              model_id: model.id,
              template_name: templateName,
            }),
            // outputPath strips the Lambda envelope ({StatusCode, Payload, ...})
            // and leaves only the handler's return value as this branch's output.
            outputPath: '$.Payload',
          },
        )
        branch.addRetry({
          errors: LAMBDA_RETRY_ERRORS,
          interval: cdk.Duration.seconds(3),
          maxAttempts: 2,
          backoffRate: 2,
        })
        invokeAllVariants.branch(branch)
      }
    }

    // ScoreOutputs: score each of the 6 InvokeTemplateResult objects produced
    // by InvokeAllVariants. The Map iterates over the Parallel output array,
    // passing each element directly to score-output as the Lambda event.
    const scoreTask = new tasks.LambdaInvoke(this, 'ScoreOutput', {
      lambdaFunction: scoreOutputFn,
      // The Map item is the full InvokeTemplateResult; pass it as-is.
      outputPath: '$.Payload',
    })
    scoreTask.addRetry({
      errors: LAMBDA_RETRY_ERRORS,
      interval: cdk.Duration.seconds(3),
      maxAttempts: 2,
      backoffRate: 2,
    })

    const scoreOutputs = new sfn.Map(this, 'ScoreOutputs', {
      maxConcurrency: 1,
      // Default itemsPath is '$', which is the entire input (the 6-element array
      // from InvokeAllVariants). No itemSelector needed: each item is already
      // a complete InvokeTemplateResult that score-output expects.
      // maxConcurrency 1 ensures score-output Lambdas run sequentially to stay
      // within the account Lambda execution quota.
    })
    scoreOutputs.itemProcessor(scoreTask)

    // EvaluateQuestions: outer Map over the 5 test questions.
    // itemSelector reshapes each plain string element into { question: "..." }
    // so the Parallel branches can address it at $.question.
    // maxConcurrency 1 processes questions sequentially so the peak Lambda
    // concurrency stays at 6 (the Parallel branches) rather than 5 x 6 = 30.
    const evaluateQuestions = new sfn.Map(this, 'EvaluateQuestions', {
      maxConcurrency: 1,
      itemsPath: sfn.JsonPath.stringAt('$.questions'),
      itemSelector: {
        'question.$': '$$.Map.Item.Value',
      },
    })
    evaluateQuestions.itemProcessor(invokeAllVariants.next(scoreOutputs))

    // AggregateResults: final Lambda invocation after all 5 iterations complete.
    // Receives ScoredItem[][] (5 x 6); the handler flattens to ScoredItem[30].
    const aggregateResults = new tasks.LambdaInvoke(this, 'AggregateResults', {
      lambdaFunction: aggregateResultsFn,
      outputPath: '$.Payload',
    })

    // Wire the top-level chain.
    const definition = prepareInput.next(evaluateQuestions).next(aggregateResults)

    this.stateMachine = new sfn.StateMachine(this, 'StateMachine', {
      stateMachineName: 'PromptEvaluationPipeline',
      stateMachineType: sfn.StateMachineType.STANDARD,
      definitionBody: sfn.DefinitionBody.fromChainable(definition),
      timeout: cdk.Duration.minutes(30),
      comment:
        'Evaluates 3 Bedrock prompt templates against 2 models across 5 questions. ' +
        'Scores outputs with an LLM judge and aggregates results to S3 and CloudWatch.',
    })
  }
}
