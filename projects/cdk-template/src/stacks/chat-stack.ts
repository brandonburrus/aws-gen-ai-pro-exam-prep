import * as cdk from 'aws-cdk-lib'
import type { Construct } from 'constructs'
import * as s3 from 'aws-cdk-lib/aws-s3'

export class ChatStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    const bucket = new s3.Bucket(this, 'Bucket', {
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    })

    new cdk.CfnOutput(this, 'BucketName', { value: bucket.bucketName })
  }
}
