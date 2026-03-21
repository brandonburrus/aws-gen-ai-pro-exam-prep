import * as cdk from 'aws-cdk-lib'
import { Sandbox } from './stages/sandbox.ts'

const app = new cdk.App()

new Sandbox(app, 'Sandbox')

app.synth()
