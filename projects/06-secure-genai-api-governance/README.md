# Project 06: Secure GenAI API with Governance Controls

## Exam Domains

| Domain | Task | Description |
|--------|------|-------------|
| 3.2 | Implement data security and privacy controls | VPC endpoints for network isolation, IAM policies for secure data access, CloudWatch for data access monitoring |
| 3.3 | Implement AI governance and compliance mechanisms | Compliance frameworks, data lineage tracking, audit logging, continuous monitoring |
| 4.3 | Implement monitoring systems for GenAI applications | Holistic observability, token usage tracking, custom dashboards, Bedrock Model Invocation Logs |

## Overview

Security and governance controls are 20% of the exam and are frequently tested through scenario-based questions: "A company requires that all Bedrock API calls stay within the corporate network boundary — which services do you configure?" or "An auditor needs a complete record of every prompt sent to the model — what do you enable?" This project answers both questions by building a Bedrock-backed API that runs entirely inside a VPC, authenticates callers via Cognito, enforces IAM least-privilege, and produces a full audit trail.

The monitoring and governance portion is the second pillar. You will enable Bedrock Model Invocation Logs to ship request/response pairs to S3 and CloudWatch, configure CloudTrail for API-level audit logs, and build a CloudWatch dashboard that gives stakeholders visibility into invocation counts, token usage, error rates, and cost proxies — all without leaving the AWS console. This project maps to the intersection of Domain 3 (security) and Domain 4 (operational efficiency), which together represent 32% of the exam.

## Architecture

```
Internet
    |
    v
Amazon Cognito User Pool (authentication)
    |-- App Client (no client secret for this lab)
    |-- JWT access token returned to caller
    |
    v  Bearer token
Amazon API Gateway (REST API, Cognito Authorizer)
    |-- Resource: POST /invoke
    |-- Method: Lambda integration (VPC-linked Lambda via VPC endpoint... 
    |           actually: API GW is public but invokes Lambda in VPC)
    |
    v
AWS Lambda (in VPC, private subnets)
    |-- Security group: outbound 443 only to VPC endpoints
    |-- No internet gateway route
    |
    v  (via VPC Interface Endpoint)
Amazon Bedrock (bedrock-runtime VPC endpoint)
    |-- bedrock:InvokeModel
    |-- Model Invocation Logs --> CloudWatch Logs + S3
    |
CloudTrail (management events: all Bedrock API calls)
Amazon CloudWatch Dashboard: GenAI-Governance

IAM Roles:
    LambdaExecutionRole: bedrock:InvokeModel on specific model ARNs only
    CallerPolicy: execute-api:Invoke on specific resource ARNs only
```

**AWS services used:**

- Amazon VPC -- private subnets, route tables, security groups for Lambda
- AWS PrivateLink (VPC Interface Endpoints) -- `com.amazonaws.<region>.bedrock-runtime` and `com.amazonaws.<region>.bedrock`
- Amazon Cognito User Pool -- user authentication and JWT issuance
- Amazon API Gateway (REST API) -- public entry point with Cognito JWT authorizer
- AWS Lambda -- Bedrock invocation handler, running in private VPC subnets
- Amazon Bedrock -- model invocation (Claude 3 Sonnet or Haiku)
- Bedrock Model Invocation Logs -- complete prompt/response capture to S3 and CloudWatch Logs
- AWS CloudTrail -- API-level audit log for all Bedrock control-plane and data-plane calls
- Amazon S3 -- invocation log storage, CloudTrail log storage
- Amazon CloudWatch Logs -- Lambda logs, Bedrock invocation logs
- Amazon CloudWatch Metrics + Dashboard -- token usage, invocation counts, error rates
- AWS IAM -- least-privilege execution and caller policies
- AWS KMS -- optional: encrypt S3 buckets for invocation logs

## What You Will Build

1. A VPC with two private subnets in different AZs and no internet gateway. A security group for Lambda that allows only outbound HTTPS (port 443).
2. Two VPC Interface Endpoints: `bedrock-runtime` and `bedrock`, each with endpoint policies restricting access to specific model ARNs.
3. A Cognito User Pool with one test user and an app client. A script that exchanges username/password for a JWT access token using the `ALLOW_USER_PASSWORD_AUTH` flow.
4. A REST API Gateway with a Cognito JWT authorizer on `POST /invoke`. Only requests with a valid Cognito JWT in the `Authorization` header are forwarded to Lambda.
5. A Lambda function in the private subnets that calls `bedrock:InvokeModel`. The execution role uses a condition `aws:SourceVpc` to ensure the call only succeeds when originating from the VPC.
6. Bedrock Model Invocation Logging enabled at the account level, shipping logs to an S3 bucket (with SSE-KMS) and a CloudWatch Logs group `/aws/bedrock/invocations`.
7. A CloudTrail trail logging all Bedrock API calls (both management and data events) to a separate S3 bucket.
8. A CloudWatch dashboard `GenAI-Governance` with four widgets:
   - Total invocations per hour (metric filter on invocation logs)
   - Input + output token counts per invocation (custom metric from Lambda)
   - Error rate (4xx + 5xx from API Gateway)
   - Estimated cost per hour (token count × published per-token price, computed in Lambda and emitted as a custom metric)

## Target Outcomes

By the end of this project you should be able to verify each of the following:

- [ ] Calling `POST /invoke` without an `Authorization` header returns HTTP 401. Calling with a valid Cognito JWT returns a successful model response.
- [ ] Invoking the Lambda function directly (not via API Gateway) with a Bedrock call still works, confirming the VPC endpoint routes traffic privately. The Lambda has no internet access — attempting an outbound HTTP call to an external URL times out.
- [ ] The Bedrock VPC endpoint policy blocks calls to any model ARN not explicitly listed. Attempting to invoke a disallowed model from within the Lambda returns an access denied error.
- [ ] Every Bedrock `InvokeModel` call appears in the CloudWatch Logs group `/aws/bedrock/invocations` with the full request and response within 2 minutes.
- [ ] CloudTrail shows `bedrock:InvokeModel` events with the caller identity (Lambda execution role ARN) and source VPC endpoint ID.
- [ ] The CloudWatch dashboard populates within 5 minutes of making 5 test invocations, showing token counts and invocation counts.
- [ ] You can explain why using a VPC endpoint policy (restricting which models can be called) is a governance control, not just a network control.

## Prerequisites

**Local tooling:**

- Node.js 22+ with npm (for Lambda handler development and AWS SDK v3)
- AWS CLI v2 with VPC, Lambda, Cognito, API Gateway, Bedrock, CloudTrail, CloudWatch, S3, KMS, and IAM permissions

**AWS service enablement:**

- Amazon Bedrock model access enabled for your target model in your region
- Bedrock Model Invocation Logs available in your region (generally available in all Bedrock regions)

**Cost note:**

VPC Interface Endpoints are billed per AZ per hour ($0.01/hr each). For a 2-3 hour lab, two endpoints across two AZs costs approximately $0.08. Delete endpoints after the lab.

## Step-by-Step Build Guide

1. **Create a VPC with two private subnets** in different Availability Zones. Do not attach an internet gateway or NAT gateway. Create a security group for Lambda that allows only outbound HTTPS (port 443) traffic.

2. **Create VPC Interface Endpoints** for `com.amazonaws.<region>.bedrock-runtime` and `com.amazonaws.<region>.bedrock`. Enable private DNS on both. Attach an endpoint policy to each that restricts `bedrock:InvokeModel` to only the specific model ARN(s) you plan to use.

3. **Write the Lambda invoke handler** (`lambdas/invoke-handler/handler.ts`). The handler calls `bedrock:InvokeModel`, then emits custom CloudWatch metrics: `InputTokens`, `OutputTokens`, and `EstimatedCostUSD` (computed from token counts and published per-token pricing). Use the `@aws-sdk/client-bedrock-runtime` and `@aws-sdk/client-cloudwatch` packages.

4. **Create the Lambda function** in the private subnets with the Lambda security group. Runtime: Node.js 22.x. Set a 30-second timeout. Create an execution role with: `bedrock:InvokeModel` on specific model ARNs (add a `StringEquals` condition for `aws:SourceVpc` matching your VPC ID), the standard VPC networking permissions (`ec2:CreateNetworkInterface`, `ec2:DescribeNetworkInterfaces`, `ec2:DeleteNetworkInterface`), `cloudwatch:PutMetricData`, and CloudWatch Logs permissions.

5. **Create a Cognito User Pool** with email sign-in enabled. Create an app client with `ALLOW_USER_PASSWORD_AUTH` flow (no client secret for this lab). Create a test user via `aws cognito-idp admin-create-user`.

6. **Create a REST API Gateway** with a Cognito User Pools authorizer on the `POST /invoke` resource. Integrate the method with the Lambda function. Deploy to a `prod` stage.

7. **Enable Bedrock Model Invocation Logging.** Configure account-level logging (via the Bedrock console or `bedrock:PutModelInvocationLoggingConfiguration` API) to ship logs to an S3 bucket and a CloudWatch Logs group `/aws/bedrock/invocations`. Create the S3 bucket with server-side encryption enabled.

8. **Create a CloudTrail trail.** Log all Bedrock API calls (management and data events) to a separate S3 bucket. Enable Bedrock as a data event source so that `InvokeModel` calls are recorded.

9. **Create a CloudWatch dashboard** named `GenAI-Governance` with four widgets: total invocations per hour (metric filter on invocation logs), input + output token counts per invocation (custom metrics from Lambda), error rate (4xx + 5xx from API Gateway), and estimated cost per hour.

10. **Deploy all resources to your AWS account** using your preferred infrastructure-as-code tool or the AWS Management Console.

11. **Write a token retrieval script** (`scripts/get_token.ts`) that calls Cognito `initiateAuth` and prints the `AccessToken`.

12. **Run 5-10 test invocations** via `curl -H "Authorization: Bearer <token>" -X POST <api-url>/prod/invoke`. Verify all CloudWatch metrics and the dashboard populate within 5 minutes.

13. **Validate network isolation.** Temporarily add a code path in the Lambda that calls `https://example.com`. Confirm it times out, verifying no internet route exists from within the VPC.

## Key Exam Concepts Practiced

- VPC Interface Endpoints (PrivateLink) for Bedrock as a network isolation control (Task 3.2.1)
- VPC endpoint policies for restricting which models can be invoked from within the VPC (Task 3.2.1, 3.3.3)
- Cognito User Pool + JWT authorizer on API Gateway for authentication (Task 2.3.3)
- IAM least-privilege with `aws:SourceVpc` condition to enforce network-bound access (Task 3.2.1)
- Bedrock Model Invocation Logs for full prompt/response audit trail (Task 3.3.1, 3.3.2)
- CloudTrail for API-level audit logging of Bedrock calls (Task 3.3.2)
- CloudWatch dashboard for token usage, invocation counts, error rates, and cost (Task 4.3.2, 4.3.3)
- The difference between data privacy (VPC + endpoint policy) and data logging (invocation logs + CloudTrail) as complementary controls (Task 3.2.1 vs. 3.3.2)
