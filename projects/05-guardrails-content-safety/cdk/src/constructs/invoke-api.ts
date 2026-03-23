import * as apigwv2 from 'aws-cdk-lib/aws-apigatewayv2'
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations'
import type * as lambda from 'aws-cdk-lib/aws-lambda'
import { Construct } from 'constructs'

export interface InvokeApiProps {
  /** The Lambda function that handles POST /invoke requests. */
  handler: lambda.IFunction
}

/**
 * An HTTP API (API Gateway v2) with a single `POST /invoke` route backed by a
 * Lambda proxy integration.
 *
 * The API is publicly accessible with no authorization. The `$default` stage
 * is created automatically by `HttpApi`.
 */
export class InvokeApi extends Construct {
  /** The underlying HTTP API resource. */
  public readonly api: apigwv2.HttpApi

  /**
   * The fully-qualified HTTPS endpoint for the `/invoke` route.
   * Example: `https://<id>.execute-api.us-east-1.amazonaws.com/invoke`
   */
  public readonly invokeEndpoint: string

  constructor(scope: Construct, id: string, props: InvokeApiProps) {
    super(scope, id)

    this.api = new apigwv2.HttpApi(this, 'HttpApi', {
      apiName: 'guardrail-safety-api',
    })

    this.api.addRoutes({
      path: '/invoke',
      methods: [apigwv2.HttpMethod.POST],
      integration: new HttpLambdaIntegration('InvokeIntegration', props.handler),
    })

    this.invokeEndpoint = `${this.api.apiEndpoint}/invoke`
  }
}
