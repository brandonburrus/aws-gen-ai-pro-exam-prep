import * as cdk from 'aws-cdk-lib'
import type { Construct } from 'constructs'
import { GuardrailSafety } from '../stacks/guardrail-safety.ts'

export class Sandbox extends cdk.Stage {
  constructor(scope: Construct, id: string, props?: cdk.StageProps) {
    super(scope, id, {
      ...props,
      env: {
        account: '045064753163',
        region: 'us-east-1',
      },
    })

    new GuardrailSafety(this, 'GuardrailSafety')
  }
}
