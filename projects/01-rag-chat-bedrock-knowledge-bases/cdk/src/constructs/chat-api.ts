import * as apigwv2 from 'aws-cdk-lib/aws-apigatewayv2'
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations'
import type * as lambda from 'aws-cdk-lib/aws-lambda'
import { Construct } from 'constructs'

export interface ChatApiProps {
  /** The Lambda function that handles POST /chat requests. */
  chatHandler: lambda.IFunction
}

/**
 * An HTTP API (API Gateway v2) with a single `POST /chat` route backed by a
 * Lambda proxy integration.
 *
 * The API is publicly accessible with no authorization. The `$default` stage
 * is created automatically by `HttpApi`.
 */
export class ChatApi extends Construct {
  /** The underlying HTTP API resource. */
  public readonly api: apigwv2.HttpApi

  /**
   * The fully-qualified HTTPS endpoint for the `/chat` route.
   * Example: `https://<id>.execute-api.us-east-1.amazonaws.com/chat`
   */
  public readonly chatEndpoint: string

  constructor(scope: Construct, id: string, props: ChatApiProps) {
    super(scope, id)

    this.api = new apigwv2.HttpApi(this, 'HttpApi', {
      apiName: 'aip-c01-chat-api',
    })

    this.api.addRoutes({
      path: '/chat',
      methods: [apigwv2.HttpMethod.POST],
      integration: new HttpLambdaIntegration('ChatIntegration', props.chatHandler),
    })

    this.chatEndpoint = `${this.api.apiEndpoint}/chat`
  }
}
