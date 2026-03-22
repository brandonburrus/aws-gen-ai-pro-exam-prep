import * as fs from 'node:fs'
import * as path from 'node:path'
import * as bedrock from '@aws-cdk/aws-bedrock-alpha'
import { Construct } from 'constructs'

/**
 * Shape of the inferenceConfiguration.text block inside each prompt JSON file.
 */
interface PromptInferenceConfig {
  maxTokens: number
  temperature: number
  topP: number
}

/**
 * Minimal typed representation of the prompt JSON files stored in prompts/.
 * Only the fields consumed at synth time are declared here.
 */
interface PromptFileSchema {
  name: string
  description: string
  defaultVariant: string
  variants: Array<{
    name: string
    templateConfiguration: {
      text: {
        text: string
        inputVariables: Array<{ name: string }>
      }
    }
    inferenceConfiguration: {
      text: PromptInferenceConfig
    }
  }>
}

/**
 * Typed result returned by loadPromptConfig for each template.
 */
interface PromptConfig {
  name: string
  description: string
  promptText: string
  promptVariables: string[]
  inferenceConfig: PromptInferenceConfig
}

/**
 * Properties for BedrockPromptTemplates.
 * Currently all configuration is read from the prompts/ JSON files.
 * Declared as a named type alias to allow future extensibility without a
 * breaking change at the call site.
 */
export type BedrockPromptTemplatesProps = Record<string, never>

/**
 * CDK construct that provisions all three parameterized prompt templates
 * (direct-instruction, chain-of-thought, few-shot) in Amazon Bedrock Prompt
 * Management, and publishes an immutable v1 version of each.
 *
 * Prompt definitions are read from the sibling prompts/ directory at CDK
 * synth time, so the JSON files remain the single source of truth.  Any
 * change to a JSON file will automatically produce a new PromptVersion on
 * the next deploy via the hash-based versioning mechanism built into the
 * alpha construct library.
 *
 * Exposed properties (promptArns map and individual version constructs) are
 * intended to be passed as environment variables into the evaluation Lambda
 * functions defined in the parent stack.
 */
export class BedrockPromptTemplates extends Construct {
  /** The direct-instruction Prompt resource. */
  public readonly directInstructionPrompt: bedrock.Prompt
  /** The chain-of-thought Prompt resource. */
  public readonly chainOfThoughtPrompt: bedrock.Prompt
  /** The few-shot Prompt resource. */
  public readonly fewShotPrompt: bedrock.Prompt

  /** Immutable v1 snapshot of the direct-instruction prompt. */
  public readonly directInstructionVersion: bedrock.PromptVersion
  /** Immutable v1 snapshot of the chain-of-thought prompt. */
  public readonly chainOfThoughtVersion: bedrock.PromptVersion
  /** Immutable v1 snapshot of the few-shot prompt. */
  public readonly fewShotVersion: bedrock.PromptVersion

  /**
   * Convenience map of template name to versioned prompt ARN.
   * Keys match the `name` field in each JSON file.
   * Values are token strings resolved at deploy time.
   */
  public readonly promptArns: Record<string, string>

  constructor(scope: Construct, id: string, _props: BedrockPromptTemplatesProps = {}) {
    super(scope, id)

    const directConfig = this.loadPromptConfig('direct-instruction.json')
    const cotConfig = this.loadPromptConfig('chain-of-thought.json')
    const fewShotConfig = this.loadPromptConfig('few-shot.json')

    this.directInstructionPrompt = this.makePrompt('DirectInstruction', directConfig)
    this.chainOfThoughtPrompt = this.makePrompt('ChainOfThought', cotConfig)
    this.fewShotPrompt = this.makePrompt('FewShot', fewShotConfig)

    this.directInstructionVersion = this.directInstructionPrompt.createVersion(
      'Initial v1 snapshot',
    )
    this.chainOfThoughtVersion = this.chainOfThoughtPrompt.createVersion('Initial v1 snapshot')
    this.fewShotVersion = this.fewShotPrompt.createVersion('Initial v1 snapshot')

    this.promptArns = {
      [directConfig.name]: this.directInstructionVersion.versionArn,
      [cotConfig.name]: this.chainOfThoughtVersion.versionArn,
      [fewShotConfig.name]: this.fewShotVersion.versionArn,
    }
  }

  /**
   * Reads and validates a prompt JSON file from the prompts/ directory that
   * sits two levels above this construct's source file (i.e. at
   * projects/02-prompt-management-evaluation-pipeline/prompts/).
   *
   * @param filename - Basename of the JSON file, e.g. "direct-instruction.json".
   * @returns Typed PromptConfig extracted from the file.
   */
  private loadPromptConfig(filename: string): PromptConfig {
    const promptsDir = path.resolve(__dirname, '..', '..', '..', 'prompts')
    const filePath = path.join(promptsDir, filename)
    const raw = fs.readFileSync(filePath, 'utf-8')
    const parsed = JSON.parse(raw) as PromptFileSchema

    const variant = parsed.variants[0]
    return {
      name: parsed.name,
      description: parsed.description,
      promptText: variant.templateConfiguration.text.text,
      promptVariables: variant.templateConfiguration.text.inputVariables.map(v => v.name),
      inferenceConfig: variant.inferenceConfiguration.text,
    }
  }

  /**
   * Creates a Bedrock Prompt with a single TEXT variant using Claude Haiku 4.5
   * and the inference parameters read from the prompt JSON file.
   *
   * @param constructId - CDK logical ID used to scope child constructs.
   * @param config - Parsed prompt configuration from the JSON file.
   * @returns The created Prompt construct.
   */
  private makePrompt(constructId: string, config: PromptConfig): bedrock.Prompt {
    const variant = bedrock.PromptVariant.text({
      variantName: 'default',
      model: bedrock.BedrockFoundationModel.AMAZON_NOVA_LITE_V1,
      promptVariables: config.promptVariables,
      promptText: config.promptText,
      inferenceConfiguration: bedrock.PromptInferenceConfiguration.text({
        maxTokens: config.inferenceConfig.maxTokens,
        temperature: config.inferenceConfig.temperature,
        topP: config.inferenceConfig.topP,
      }),
    })

    return new bedrock.Prompt(this, constructId, {
      promptName: config.name,
      description: config.description,
      defaultVariant: variant,
      variants: [variant],
    })
  }
}
