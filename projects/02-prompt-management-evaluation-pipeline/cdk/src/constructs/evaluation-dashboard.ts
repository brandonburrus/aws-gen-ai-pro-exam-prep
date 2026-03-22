import * as cdk from 'aws-cdk-lib'
import * as cw from 'aws-cdk-lib/aws-cloudwatch'
import { Construct } from 'constructs'

/**
 * Template names that correspond to the three Bedrock Prompt Management
 * variants under evaluation. These values match the `template_name` values
 * injected by the Step Functions state machine and emitted as CloudWatch
 * metric dimensions by the aggregate-results Lambda.
 */
const TEMPLATE_NAMES = ['direct-instruction', 'chain-of-thought', 'few-shot'] as const

/**
 * Model IDs for the two models under evaluation. These are the global
 * cross-region inference profile IDs emitted as the `ModelId` dimension by
 * the aggregate-results Lambda.
 */
const MODEL_IDS = [
  'global.anthropic.claude-haiku-4-5-20251001-v1:0',
  'global.anthropic.claude-sonnet-4-5-20250929-v1:0',
] as const

/** CloudWatch metric namespace shared by all GenAI evaluation metrics. */
const METRIC_NAMESPACE = 'GenAI/PromptEvaluation'

/**
 * Props for {@link EvaluationDashboard}.
 * Currently all metric definitions are derived from the known namespace,
 * dimension names, and model/template constants declared in this module.
 */
export type EvaluationDashboardProps = Record<string, never>

/**
 * CloudWatch Dashboard construct for the Prompt Evaluation Pipeline.
 *
 * Renders two widgets:
 * - Average Relevance score per prompt template (TemplateName dimension)
 * - Average Consistency score per model (ModelId dimension)
 *
 * Metrics are emitted by the aggregate-results Lambda via PutMetricData
 * into the `GenAI/PromptEvaluation` namespace.
 */
export class EvaluationDashboard extends Construct {
  /** The underlying CloudWatch Dashboard resource. */
  public readonly dashboard: cw.Dashboard

  constructor(scope: Construct, id: string, _props: EvaluationDashboardProps = {}) {
    super(scope, id)

    const relevanceMetrics = TEMPLATE_NAMES.map(
      templateName =>
        new cw.Metric({
          namespace: METRIC_NAMESPACE,
          metricName: 'Relevance',
          dimensionsMap: { TemplateName: templateName },
          statistic: cw.Stats.AVERAGE,
          period: cdk.Duration.minutes(5),
          label: templateName,
        }),
    )

    const consistencyMetrics = MODEL_IDS.map(
      modelId =>
        new cw.Metric({
          namespace: METRIC_NAMESPACE,
          metricName: 'Consistency',
          dimensionsMap: { ModelId: modelId },
          statistic: cw.Stats.AVERAGE,
          period: cdk.Duration.minutes(5),
          label: modelId,
        }),
    )

    const relevanceWidget = new cw.GraphWidget({
      title: 'Average Relevance by Template',
      width: 12,
      height: 6,
      left: relevanceMetrics,
      leftYAxis: { min: 0, max: 10, label: 'Score (0-10)' },
    })

    const consistencyWidget = new cw.GraphWidget({
      title: 'Average Consistency by Model',
      width: 12,
      height: 6,
      left: consistencyMetrics,
      leftYAxis: { min: 0, max: 10, label: 'Score (0-10)' },
    })

    this.dashboard = new cw.Dashboard(this, 'Dashboard', {
      dashboardName: 'PromptEvaluationPipeline',
      widgets: [[relevanceWidget, consistencyWidget]],
    })
  }
}
