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

- AWS CLI v2 with VPC, Lambda, Cognito, API Gateway, Bedrock, CloudTrail, CloudWatch, S3, KMS, and IAM permissions
- Python 3.11+ with `boto3`
- AWS CDK CLI recommended (this project involves 10+ interconnected resources where IaC pays off significantly)

**AWS service enablement:**

- Amazon Bedrock model access enabled for your target model in your region
- Bedrock Model Invocation Logs available in your region (generally available in all Bedrock regions)

**Cost note:**

VPC Interface Endpoints are billed per AZ per hour ($0.01/hr each). For a 2-3 hour lab, two endpoints across two AZs costs approximately $0.08. Delete endpoints after the lab.

## Step-by-Step Build Guide

1. **Create the VPC.** Use CDK or CloudFormation: one VPC, two private subnets (no NAT Gateway, no internet gateway). One security group for Lambda: ingress none, egress TCP 443 to `0.0.0.0/0` (will be further restricted by route table — no internet route exists).

2. **Create VPC Interface Endpoints** for `bedrock-runtime` and `bedrock`. Attach to both private subnets. Enable private DNS. Create endpoint policies that allow only `bedrock:InvokeModel` on the specific model ARN(s) you plan to use.

3. **Create the Lambda execution role.** Attach a policy allowing `bedrock:InvokeModel` on specific model ARNs with a condition `"StringEquals": { "aws:SourceVpc": "<vpc-id>" }`. Also allow `logs:CreateLogGroup`, `logs:PutLogEvents`, `ec2:CreateNetworkInterface`, `ec2:DescribeNetworkInterfaces`, `ec2:DeleteNetworkInterface` (required for VPC Lambda).

4. **Write and deploy the Lambda** (`invoke_handler.py`). Accept `{ "prompt": str }`. Call `bedrock:InvokeModel`. Emit two custom CloudWatch metrics: `InputTokens` and `OutputTokens`. Emit an `EstimatedCostUSD` metric (tokens × per-token price). Deploy into the private subnets with the Lambda security group.

5. **Create the Cognito User Pool.** Enable email as username. Create an app client with `ALLOW_USER_PASSWORD_AUTH`. Create one test user (force password change disabled for lab convenience). Note the User Pool ID and App Client ID.

6. **Create the REST API Gateway** with a Cognito authorizer referencing your User Pool. Create resource `/invoke`, method `POST`, integration type Lambda proxy. Deploy to stage `prod`.

7. **Enable Bedrock Model Invocation Logging** in the Bedrock console (under Settings → Model invocation logging). Select destination: S3 bucket + CloudWatch Logs group. Create an S3 bucket `bedrock-invocation-logs-<account-id>` with SSE-S3 (or KMS). Create the CloudWatch Logs group `/aws/bedrock/invocations`.

8. **Create a CloudTrail trail** logging to a separate S3 bucket. Enable data events for Bedrock: event source `bedrock.amazonaws.com`, action `InvokeModel`.

9. **Write the token script** (`get_token.py`) that calls Cognito's `initiate_auth` with credentials and prints the `AccessToken`. Use this token in the `Authorization: Bearer <token>` header for test requests.

10. **Build the CloudWatch dashboard** `GenAI-Governance`. Add metric widgets for Lambda custom metrics (`InputTokens`, `OutputTokens`, `EstimatedCostUSD`) and API Gateway metrics (4xx count, 5xx count, latency). Add a log insights widget querying `/aws/bedrock/invocations` for invocation count.

11. **Run test invocations** (5-10 requests via the API Gateway URL with the bearer token). Verify all logs and dashboard populate.

12. **Validate network isolation.** From within the Lambda (add a test code path), attempt a call to `https://example.com`. It should timeout, confirming no internet route.

## Key Exam Concepts Practiced

- VPC Interface Endpoints (PrivateLink) for Bedrock as a network isolation control (Task 3.2.1)
- VPC endpoint policies for restricting which models can be invoked from within the VPC (Task 3.2.1, 3.3.3)
- Cognito User Pool + JWT authorizer on API Gateway for authentication (Task 2.3.3)
- IAM least-privilege with `aws:SourceVpc` condition to enforce network-bound access (Task 3.2.1)
- Bedrock Model Invocation Logs for full prompt/response audit trail (Task 3.3.1, 3.3.2)
- CloudTrail for API-level audit logging of Bedrock calls (Task 3.3.2)
- CloudWatch dashboard for token usage, invocation counts, error rates, and cost (Task 4.3.2, 4.3.3)
- The difference between data privacy (VPC + endpoint policy) and data logging (invocation logs + CloudTrail) as complementary controls (Task 3.2.1 vs. 3.3.2)
