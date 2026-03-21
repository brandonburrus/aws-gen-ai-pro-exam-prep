import * as cdk from 'aws-cdk-lib'
import type { Construct } from 'constructs'
import { ChatStack } from '../stacks/chat-stack'

export class Sandbox extends cdk.Stage {
  constructor(scope: Construct, id: string, props?: cdk.StageProps) {
    super(scope, id, {
      ...props,
      env: {
        account: '045064753163',
        region: 'us-east-1',
      },
    })

    new ChatStack(this, 'ChatStack')
  }
}
