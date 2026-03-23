# Security, Identity, and Compliance -- Comprehensive Study Guide (AIP-C01)

Security services are foundational to the AWS Certified Generative AI Developer - Professional exam. IAM is the single most critical security topic, appearing in tasks across domains 2 and 3. This guide covers IAM (including Access Analyzer and Identity Center), Amazon Cognito, AWS KMS, AWS Secrets Manager, Amazon Macie, AWS WAF, and the AWS Encryption SDK.

---

## 1. IAM (Identity and Access Management)

IAM is the backbone of AWS security and is **heavily tested** on the exam. You must understand how IAM policies control access to Bedrock foundation models, how service roles enable AI agents, and how to implement least privilege for AI workloads.

### 1.1 IAM Policies for Amazon Bedrock Access

Amazon Bedrock uses **identity-based policies only** -- it does not support resource-based policies. All access control is done through policies attached to IAM users, groups, or roles.

#### Key Bedrock IAM Features

| IAM Feature | Bedrock Support |
|---|---|
| Identity-based policies | Yes |
| Resource-based policies | **No** |
| Policy actions | Yes |
| Policy resources (ARN-level) | Yes |
| Policy condition keys | Yes |
| ABAC (tags in policies) | Yes |
| Temporary credentials | Yes |
| Service roles | Yes |
| Service-linked roles | **No** |

#### Bedrock Resource ARN Format

```
arn:aws:bedrock:<region>::foundation-model/<model-id>
arn:aws:bedrock:<region>:<account-id>:agent/<agent-id>
arn:aws:bedrock:<region>:<account-id>:knowledge-base/<kb-id>
arn:aws:bedrock:<region>:<account-id>:guardrail/<guardrail-id>
arn:aws:bedrock:<region>:<account-id>:custom-model/<model-name>
arn:aws:bedrock:<region>:<account-id>:inference-profile/<profile-id>
arn:aws:bedrock:<region>:<account-id>:flow/<flow-id>
```

> **Exam Gotcha**: Foundation model ARNs have **no account ID** (they use `::` with an empty account field) because they are AWS-owned. Custom models, agents, knowledge bases, and guardrails use your account ID.

#### Restricting Access to Specific Models

You can restrict which foundation models a principal can invoke by specifying model ARNs in the `Resource` element:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSpecificModels",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet*",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2*"
      ]
    }
  ]
}
```

#### Denying Access to Specific Models

For organizations that want to allow most models but block specific ones:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenySpecificModels",
      "Effect": "Deny",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/meta.llama*"
      ]
    }
  ]
}
```

#### AWS Managed Policies for Bedrock

| Policy | Purpose |
|---|---|
| `AmazonBedrockFullAccess` | Full admin access to all Bedrock resources. Includes EC2, IAM, KMS, and SageMaker permissions. |
| `AmazonBedrockReadOnly` | Read-only access to all Bedrock resources. |
| `AmazonBedrockLimitedAccess` | Basic Bedrock API access, KMS key management, networking, and Marketplace subscriptions. Use when SCPs handle model-level governance. |
| `AmazonBedrockMarketplaceAccess` | Manage and use Bedrock Marketplace model endpoints with SageMaker integration. |

> **Exam Gotcha**: `AmazonBedrockFullAccess` grants permissions beyond just Bedrock -- it includes EC2 (for VPC config), IAM (for service roles), KMS (for encryption), and SageMaker (for custom models). In a least-privilege scenario, create a custom policy instead.

### 1.2 Bedrock Condition Keys

Condition keys let you add fine-grained restrictions to IAM policies beyond just actions and resources.

| Condition Key | Description | Type |
|---|---|---|
| `bedrock:GuardrailIdentifier` | Enforce a specific guardrail ARN (or ARN:version) on model invocations | ARN |
| `bedrock:InferenceProfileArn` | Restrict to a specific inference profile | ARN |
| `bedrock:PromptRouterArn` | Restrict to a specific prompt router | ARN |
| `bedrock:BearerTokenType` | Filter by SHORT_TERM or LONG_TERM bearer tokens | String |
| `bedrock:ServiceTier` | Restrict by service tier | String |
| `bedrock:ThirdPartyKnowledgeBaseCredentialsSecretArn` | Restrict third-party KB credentials | ARN |
| `bedrock:InlineAgentName` | Restrict InvokeInlineAgent API by agent name | String |
| `aws:RequestTag/${TagKey}` | Filter on tags in the create request | String |
| `aws:ResourceTag/${TagKey}` | Filter on tags attached to the resource | String |

#### Enforcing Guardrails via IAM Policy

This is a **new and exam-relevant** feature. You can force all model invocations to use a specific guardrail:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EnforceGuardrail",
      "Effect": "Deny",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "bedrock:GuardrailIdentifier": "arn:aws:bedrock:us-east-1:123456789012:guardrail/abc123"
        }
      }
    }
  ]
}
```

If the guardrail in the IAM policy does not match the guardrail specified in the API call, the request is rejected.

#### Controlling Marketplace Models with Product ID Condition Keys

Third-party models from providers like Anthropic, Cohere, and Stability are offered through AWS Marketplace and have product IDs. You can use the `aws-marketplace:ProductId` condition key to control access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOnlySpecificMarketplaceModels",
      "Effect": "Allow",
      "Action": "aws-marketplace:Subscribe",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws-marketplace:ProductId": [
            "prod-abc123",
            "prod-def456"
          ]
        }
      }
    }
  ]
}
```

> **Exam Gotcha**: Models from Amazon, DeepSeek, Mistral AI, Meta, Qwen, and OpenAI are **not sold through AWS Marketplace** and have no product keys. To restrict them, deny the `bedrock:InvokeModel` action with their model IDs in the `Resource` field instead.

### 1.3 Service Roles for AI Services

Amazon Bedrock Agents, Knowledge Bases, and model customization jobs all require IAM service roles. These roles allow the Bedrock service to act on your behalf.

#### Bedrock Agent Service Role

The trust policy must allow the `bedrock.amazonaws.com` service principal to assume the role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "123456789012"
        },
        "ArnLike": {
          "AWS:SourceArn": "arn:aws:bedrock:us-east-1:123456789012:agent/*"
        }
      }
    }
  ]
}
```

The `aws:SourceAccount` and `AWS:SourceArn` conditions prevent the confused deputy problem. After creating agents, narrow the `SourceArn` from `agent/*` to the specific agent ID.

#### Permissions the Agent Service Role Needs

| Permission | Purpose |
|---|---|
| `bedrock:InvokeModel` on foundation model ARNs | Run inference with the agent's FM |
| `s3:GetObject` on schema bucket | Access OpenAPI schemas for action groups |
| `bedrock:Retrieve` on knowledge base ARNs | Query attached knowledge bases |
| `bedrock:ApplyGuardrail` (optional) | Apply guardrails to agent responses |
| `lambda:InvokeFunction` | **Not on the service role** -- use a resource-based policy on the Lambda instead |

> **Exam Gotcha**: Lambda permissions for agent action groups are granted via a **resource-based policy on the Lambda function**, not via the agent's service role. The resource-based policy allows `bedrock.amazonaws.com` to invoke the function.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBedrockToInvokeLambda",
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:my-agent-action",
      "Condition": {
        "ArnLike": {
          "AWS:SourceArn": "arn:aws:bedrock:us-east-1:123456789012:agent/AGENT_ID"
        }
      }
    }
  ]
}
```

#### Bedrock Does Not Use Service-Linked Roles

Bedrock does **not** create service-linked roles. You must create and manage service roles yourself (or let the console create them). This is different from services like SageMaker or RDS.

### 1.4 Cross-Account Access for Foundation Models

Since Bedrock does not support resource-based policies, cross-account access requires **IAM role assumption**:

1. **Account B** (the one with the model access) creates an IAM role with Bedrock permissions
2. The trust policy on that role allows **Account A** to assume it
3. **Account A** uses `sts:AssumeRole` to get temporary credentials
4. Account A uses those credentials to call Bedrock APIs in Account B

For cross-account Bedrock Agents or Knowledge Bases, each resource must be in an account with the appropriate model access. Cross-Region inference profiles can span regions within the same account but not across accounts.

### 1.5 Least Privilege for AI API Access

The exam tests your ability to apply least privilege to AI workloads. Key principles:

1. **Scope model access**: Only allow the specific model IDs the application needs
2. **Scope actions**: Only grant `bedrock:InvokeModel` (not `bedrock:*`) for inference workloads
3. **Use condition keys**: Enforce guardrails, restrict inference profiles, require tags
4. **Separate roles**: Use different IAM roles for different tasks (model invocation vs. model customization vs. agent management)
5. **Time-bound credentials**: Use temporary credentials via STS, not long-term access keys
6. **Regularly review**: Use IAM Access Analyzer to find unused permissions

#### Example: Minimal Invoke-Only Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeClaudeOnly",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet*"
    }
  ]
}
```

#### Bedrock API Key Security

Bedrock supports API keys (bearer tokens) as an alternative authentication mechanism. Key points:

- **Short-term keys**: Generated locally, last up to 12 hours or the IAM session duration (whichever is shorter). Cannot be listed or retrieved via API.
- **Long-term keys**: Managed via IAM console, can have configurable expiration (1 day to indefinite). Tracked via CloudTrail.
- **Best practice**: Always prefer STS temporary credentials. If API keys are necessary, use short-term keys. Store long-term keys in Secrets Manager.

Control API key usage with condition keys:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PreventLongTermAPIKeys",
      "Effect": "Deny",
      "Action": "bedrock:CallWithBearerToken",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "bedrock:BearerTokenType": "LONG_TERM"
        }
      }
    }
  ]
}
```

### 1.6 Service Control Policies (SCPs) for AI Governance

SCPs are used at the AWS Organizations level to set **permission guardrails** across all accounts. They do not grant permissions -- they only restrict what is allowed.

#### Key SCP Concepts for the Exam

- SCPs affect all IAM users and roles in member accounts (not the management account)
- SCPs apply to the root user in member accounts
- SCPs do NOT affect service-linked roles
- For a permission to be allowed, every level in the OU hierarchy must allow it
- Deny always wins over Allow

#### SCP to Restrict Bedrock Models Org-Wide

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyNonApprovedModels",
      "Effect": "Deny",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "NotResource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet*",
        "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2*"
      ]
    }
  ]
}
```

#### SCP to Block Cross-Region Inference

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyCrossRegionInference",
      "Effect": "Deny",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*:*:inference-profile/*"
    }
  ]
}
```

#### SCP to Prevent AI Data Opt-In

AWS lets you opt out of AI services using your content to improve their models. Use an SCP to enforce this org-wide:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyAIOptIn",
      "Effect": "Deny",
      "Action": [
        "organizations:DisableAWSServiceAccess"
      ],
      "Resource": "*"
    }
  ]
}
```

> **Exam Gotcha**: SCPs set maximum permissions. Even if an IAM policy allows `bedrock:InvokeModel` on all models, an SCP denying specific models takes precedence. The exam may test whether you choose IAM policies (account-level) vs SCPs (org-level) for different governance scenarios.

### 1.7 IAM Access Analyzer for AI Permissions

IAM Access Analyzer helps you achieve least privilege by finding **unused access**, **external access**, and **overly permissive policies**.

#### Three Types of Analyzers

| Analyzer Type | What It Finds | Scope |
|---|---|---|
| **External access** | Resources shared with principals outside your zone of trust | Account or Organization |
| **Internal access** | Access paths between IAM principals and resources within your org | Account or Organization |
| **Unused access** | Unused roles, access keys, passwords, and service/action-level permissions | Account or Organization |

#### How It Applies to AI Workloads

1. **Find unused Bedrock permissions**: If a role has `bedrock:*` but only uses `bedrock:InvokeModel`, the unused access analyzer flags the excess permissions
2. **Policy validation**: Validates IAM policies against 100+ checks before deployment. Integrates into CI/CD pipelines.
3. **Policy generation**: Generates least-privilege policies based on CloudTrail access activity. Start broad, then refine based on actual usage.
4. **Custom policy checks**: Validate policies against your org's security standards (e.g., "no policy should allow `bedrock:*`")

#### Key Exam Facts

- External access findings are **free**
- Unused and internal access findings are **charged** per IAM role/user analyzed per month
- Unused access tracking period is configurable: 1 to 365 days
- You can exclude specific accounts, roles, or users from analysis
- Integrates with **Security Hub** and **EventBridge** for automated responses
- Uses **automated reasoning** (provable security), not sampling or heuristics

### 1.8 TypeScript SDK v3 Examples for IAM

#### Assuming a Role for Bedrock Access

```typescript
import { STSClient, AssumeRoleCommand } from "@aws-sdk/client-sts";
import {
  BedrockRuntimeClient,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";

const stsClient = new STSClient({ region: "us-east-1" });

const assumeRoleResponse = await stsClient.send(
  new AssumeRoleCommand({
    RoleArn: "arn:aws:iam::123456789012:role/bedrock-invoke-role",
    RoleSessionName: "bedrock-session",
    DurationSeconds: 3600,
  })
);

const bedrockClient = new BedrockRuntimeClient({
  region: "us-east-1",
  credentials: {
    accessKeyId: assumeRoleResponse.Credentials!.AccessKeyId!,
    secretAccessKey: assumeRoleResponse.Credentials!.SecretAccessKey!,
    sessionToken: assumeRoleResponse.Credentials!.SessionToken!,
  },
});
```

---

## 2. IAM Identity Center

IAM Identity Center (formerly AWS SSO) provides **centralized access management** across multiple AWS accounts and applications using single sign-on.

### 2.1 Core Concepts

| Concept | Description |
|---|---|
| **Identity source** | Where user identities are managed: Identity Center directory, Active Directory, or external IdP (Okta, Entra ID, Ping) |
| **Permission sets** | Templates defining a collection of IAM policies. Assigned to users/groups for specific accounts. |
| **AWS access portal** | Web portal where users sign in once and access all assigned accounts and applications |
| **Delegated administrator** | A member account designated to manage Identity Center (recommended over using the management account) |

### 2.2 SSO for AI Applications

IAM Identity Center is relevant to the exam when:

- **Multi-account AI workloads**: Different accounts for dev, staging, and production AI environments. Identity Center provides SSO across all of them.
- **Team-based access**: Data scientists, ML engineers, and app developers get different permission sets
- **Federated access to Bedrock console**: Users sign in with corporate credentials via SAML/OIDC federation to access the Bedrock console

### 2.3 Permission Sets for AI Teams

Permission sets define what a user can do when they sign into a specific account. They support:

- **AWS managed policies** (e.g., `AmazonBedrockFullAccess`, `AmazonBedrockReadOnly`)
- **Customer managed policies** (policies you create in each target account)
- **Inline policies** (embedded directly in the permission set)
- **Permissions boundaries** (maximum permission limits)

#### Example Permission Sets for AI Teams

| Team | Permission Set | Policies |
|---|---|---|
| AI Developers | `BedrockDeveloper` | `AmazonBedrockFullAccess`, `AmazonS3ReadOnlyAccess` |
| Data Scientists | `BedrockDataScience` | Custom policy with `bedrock:InvokeModel`, `bedrock:CreateModelCustomizationJob`, `s3:GetObject` |
| AI Operations | `BedrockOps` | Custom policy with `bedrock:Get*`, `bedrock:List*`, `cloudwatch:GetMetricData` |
| Security/Audit | `BedrockAudit` | `AmazonBedrockReadOnly`, `SecurityAudit` managed policy |

> **Exam Gotcha**: Permission sets create **IAM roles** in each assigned account. When a user signs in via the access portal, they assume one of these roles. The session duration is configurable (1-12 hours). Users should choose the least-privileged permission set when multiple are available.

### 2.4 Key Exam Facts

- Identity Center requires **AWS Organizations**
- Creates a service-linked role (`AWSServiceRoleForSSO`) in each account
- Supports **SCIM** for automatic user/group provisioning from external IdPs
- Can be combined with SCPs to restrict what permission sets can do
- Session duration is separate from the permission set session duration
- You can limit identity store access from member accounts using SCPs

---

## 3. Amazon Cognito

Amazon Cognito provides **authentication, authorization, and user management** for web and mobile applications. It is the primary service for adding user sign-in to AI-powered applications.

### 3.1 User Pools vs Identity Pools

These are the two core components, and the exam tests your understanding of when to use each.

| Feature | User Pools | Identity Pools |
|---|---|---|
| **Primary purpose** | Authentication (who are you?) | Authorization (what can you access?) |
| **Output** | JSON Web Tokens (JWTs): ID token, access token, refresh token | Temporary AWS credentials (access key, secret key, session token) |
| **Use case** | Sign-up, sign-in, token management for your app | Granting users direct access to AWS services (S3, DynamoDB, etc.) |
| **Supports** | Username/password, social login, SAML, OIDC, MFA, passwordless | AWS credentials via IAM roles, ABAC, guest access |
| **Federation** | Acts as the identity provider itself | Consumes tokens from user pools, social IdPs, SAML, OIDC |

#### The Combined Flow (Most Common Pattern)

1. User signs in to **User Pool** (via managed login, SDK, or hosted UI)
2. User Pool returns **JWTs** (ID token + access token + refresh token)
3. App sends the ID token to an **Identity Pool**
4. Identity Pool validates the token, maps the user to an **IAM role**
5. Identity Pool returns **temporary AWS credentials**
6. App uses credentials to access AWS services directly

> **Exam Gotcha**: User pools issue **JWTs** for API authorization. Identity pools issue **AWS credentials** for direct AWS service access. You need user pools for signing users into your AI app. You need identity pools only if the client needs to call AWS services directly (e.g., uploading files to S3 from a mobile app).

### 3.2 Token Management

| Token | Lifetime | Purpose |
|---|---|---|
| **ID token** | 5 min - 1 day (default 30 min) | Contains user identity claims (`sub`, `email`, `cognito:groups`). Used by API Gateway Cognito authorizers. |
| **Access token** | 5 min - 1 day (default 30 min) | Contains scopes and authorized actions. Used for resource server authorization. |
| **Refresh token** | 1 hour - 3650 days (default 30 days) | Used to get new ID and access tokens without re-authenticating. |

Key points:
- ID and access tokens are **JWTs** that can be verified locally (check signature, issuer, expiration, audience)
- Refresh tokens are **opaque** -- they must be sent to Cognito to get new tokens
- **Token customization**: Use a pre-token-generation Lambda trigger to add custom claims to tokens
- **Token revocation**: Supported for refresh tokens. Revoking a refresh token invalidates all access and ID tokens issued from it.

### 3.3 Integration with API Gateway for AI Endpoints

This is a high-probability exam topic: securing your AI application's API with Cognito.

#### Cognito Authorizer on REST API (Most Common Pattern)

1. Create a Cognito User Pool
2. Create a `COGNITO_USER_POOLS` authorizer in API Gateway
3. Enable it on API methods
4. Client gets an ID token from Cognito and passes it in the `Authorization` header
5. API Gateway validates the token and forwards the request to Lambda/Bedrock

```
Client --> [ID Token] --> API Gateway (Cognito Authorizer) --> Lambda --> Bedrock
```

#### JWT Authorizer on HTTP API

For HTTP APIs (v2), use a JWT authorizer instead:

1. Configure the JWT authorizer with the Cognito User Pool issuer URL and audience (client ID)
2. Client passes an access token or ID token in the `Authorization` header
3. API Gateway validates the JWT signature, issuer, audience, and expiration
4. Optionally require specific scopes for route-level authorization

#### Cognito + Amazon Verified Permissions

For **fine-grained authorization** (RBAC/ABAC) beyond what scopes provide:

1. Cognito issues tokens with group/attribute claims
2. Application calls Amazon Verified Permissions with the token
3. Verified Permissions evaluates Cedar policies against token claims
4. Returns Allow or Deny decision

> **Exam Gotcha**: API Gateway Cognito authorizers validate the **ID token**. JWT authorizers validate either ID or access tokens. For scope-based authorization (e.g., "this API requires the `ai:invoke` scope"), use the **access token** with a JWT authorizer.

### 3.4 Empowering AI Agents with User Context

A key pattern for the exam: AI agents that act on behalf of users.

1. User signs in to the app, receives tokens from Cognito
2. The AI agent (represented as a Cognito app client) performs an **OAuth 2.0 client credentials grant**
3. The agent passes the user's access token as context using the `aws_client_metadata` parameter
4. A **pre-token-generation Lambda trigger** customizes the agent's access token to include the user's claims
5. The agent uses its customized token to call downstream services on behalf of the user
6. Downstream services verify the token and authorize based on both agent and user claims

### 3.5 TypeScript SDK v3 Examples

#### Authenticating a User

```typescript
import {
  CognitoIdentityProviderClient,
  InitiateAuthCommand,
} from "@aws-sdk/client-cognito-identity-provider";

const cognitoClient = new CognitoIdentityProviderClient({
  region: "us-east-1",
});

const authResponse = await cognitoClient.send(
  new InitiateAuthCommand({
    AuthFlow: "USER_PASSWORD_AUTH",
    ClientId: "your-app-client-id",
    AuthParameters: {
      USERNAME: "user@example.com",
      PASSWORD: "securePassword123!",
    },
  })
);

const idToken = authResponse.AuthenticationResult?.IdToken;
const accessToken = authResponse.AuthenticationResult?.AccessToken;
const refreshToken = authResponse.AuthenticationResult?.RefreshToken;
```

#### Getting AWS Credentials from Identity Pool

```typescript
import { CognitoIdentityClient } from "@aws-sdk/client-cognito-identity";
import { fromCognitoIdentityPool } from "@aws-sdk/credential-providers";

const credentials = fromCognitoIdentityPool({
  clientConfig: { region: "us-east-1" },
  identityPoolId: "us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  logins: {
    "cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX": idToken!,
  },
});

// Use these credentials with any AWS SDK client
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
const s3Client = new S3Client({ region: "us-east-1", credentials });
```

### 3.6 Key Exam Facts

- Cognito scales to **millions of users** and **100+ billion authentications per month**
- User pool sign-in method (email, phone, username) **cannot be changed** after creation
- Custom attributes **cannot be removed** after being added
- Cognito does **not** provide built-in backup or export -- you must implement your own
- MFA options: SMS, TOTP (authenticator app), email OTP
- Advanced security features: adaptive authentication, compromised credentials detection
- Cognito supports **passwordless** authentication (passkeys, email/SMS OTP)
- After 5 failed sign-in attempts, lockout durations increase up to ~15 minutes

---

## 4. AWS KMS (Key Management Service)

KMS provides centralized key management for encrypting data in AI workloads. The exam tests your understanding of key types, key policies, and how KMS integrates with Bedrock and other AI data stores.

### 4.1 Key Types

| Key Type | Managed By | Rotation | Use Case |
|---|---|---|---|
| **AWS owned keys** | AWS (invisible to you) | AWS-managed | Default encryption for many services. Free. No visibility or control. |
| **AWS managed keys** | AWS (visible in KMS) | Every year (automatic) | Default option when you enable encryption. Format: `aws/<service>`. Limited policy control. |
| **Customer managed keys (CMKs)** | You | Configurable (annual automatic + on-demand) | Full control over key policy, rotation, grants, and auditing. Costs $1/month/key + API charges. |

> **Exam Gotcha**: When the exam asks about "customer managed KMS key" vs "AWS managed key", the differentiator is **control**. Customer managed keys let you define key policies, enable/disable keys, grant cross-account access, and audit usage via CloudTrail. AWS managed keys are simpler but less flexible.

### 4.2 Encryption for AI Data

#### Bedrock Encryption

| Resource | Default Encryption | Customer Managed Key Support |
|---|---|---|
| Model customization (training data, output) | AWS owned key | Yes -- specify during job creation |
| Agents | AWS owned key | Yes -- specify during agent creation |
| Knowledge Bases | AWS owned key | Yes -- for the KB metadata. Vector store encryption is separate. |
| Guardrails | AWS owned key | Yes -- specify during creation |
| Model invocation logging | AWS owned key | Yes -- for CloudWatch Logs and S3 output |
| Provisioned Throughput | AWS owned key | Yes |

#### Common AI Data Stores

| Data Store | Encryption at Rest | KMS Integration |
|---|---|---|
| **S3** (training data, RAG documents) | SSE-S3 (default), SSE-KMS, SSE-C, or client-side | Full CMK support. Bucket keys reduce KMS costs. |
| **OpenSearch Serverless** (vector store) | Always encrypted | CMK support for collection encryption |
| **Amazon Aurora** (metadata, structured data) | Encrypted by default | CMK support at cluster creation |
| **DynamoDB** (session state, metadata) | Encrypted by default | AWS owned, AWS managed, or CMK |
| **Amazon RDS/Aurora** (structured data) | Optional, immutable after creation | CMK support |

### 4.3 Key Policies for AI Services

When Bedrock (or other AI services) need to use your CMK, the key policy must grant the service permission. This is done via **grants** or direct key policy statements.

#### Key Policy Allowing Bedrock to Use a CMK

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowBedrockServiceRole",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/bedrock-agent-role"
      },
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:DescribeKey",
        "kms:CreateGrant"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "bedrock.us-east-1.amazonaws.com"
        }
      }
    }
  ]
}
```

The `kms:ViaService` condition key ensures the key can only be used when the request comes through the Bedrock service.

#### The Lambda Execution Role for Secrets Rotation Needs KMS Permissions

If a secret encrypted with a CMK is being rotated:

```json
{
  "Effect": "Allow",
  "Action": [
    "kms:Decrypt",
    "kms:GenerateDataKey"
  ],
  "Resource": "arn:aws:kms:us-east-1:123456789012:key/key-id"
}
```

### 4.4 Envelope Encryption

This is how KMS protects large amounts of data:

1. KMS generates a **data key** (plaintext + encrypted copy)
2. You use the plaintext data key to encrypt your data locally
3. You discard the plaintext data key
4. You store the **encrypted data key** alongside the encrypted data
5. To decrypt: send the encrypted data key to KMS, get plaintext key back, decrypt data

This is the same pattern used by the AWS Encryption SDK and by services like S3 (SSE-KMS).

> **Exam Gotcha**: KMS can only directly encrypt/decrypt data up to **4 KB**. For anything larger, you must use envelope encryption (generate a data key, encrypt locally). The AWS Encryption SDK automates this.

### 4.5 TypeScript SDK v3 Examples

#### Encrypting Data with a KMS Key

```typescript
import { KMSClient, GenerateDataKeyCommand, DecryptCommand } from "@aws-sdk/client-kms";
import { createCipheriv, createDecipheriv, randomBytes } from "crypto";

const kmsClient = new KMSClient({ region: "us-east-1" });

// Generate a data key for envelope encryption
const dataKeyResponse = await kmsClient.send(
  new GenerateDataKeyCommand({
    KeyId: "arn:aws:kms:us-east-1:123456789012:key/my-key-id",
    KeySpec: "AES_256",
  })
);

const plaintextKey = dataKeyResponse.Plaintext!; // Use to encrypt data
const encryptedKey = dataKeyResponse.CiphertextBlob!; // Store alongside encrypted data

// Encrypt your data with the plaintext key
const iv = randomBytes(16);
const cipher = createCipheriv("aes-256-gcm", plaintextKey, iv);
const encrypted = Buffer.concat([cipher.update("sensitive AI data"), cipher.final()]);
const authTag = cipher.getAuthTag();

// Store: encryptedKey + iv + authTag + encrypted data
// Discard: plaintextKey (don't persist it)
```

### 4.6 Key Exam Facts

- KMS keys are **regional** -- a key in us-east-1 cannot be used in eu-west-1 unless you use multi-region keys
- **Multi-region keys**: Replicated keys with the same key material across regions. Useful for cross-region inference or disaster recovery.
- **S3 Bucket Keys**: Reduce KMS API calls (and costs) by generating a bucket-level key that is reused for objects. Reduces costs by up to 99%.
- Key deletion has a **waiting period** of 7-30 days (default 30). Keys cannot be recovered after deletion.
- **Automatic key rotation**: Customer managed symmetric keys only. Rotates every year by default (configurable). Old key material is retained for decryption.
- All KMS API calls are logged in **CloudTrail** -- this is how you audit who decrypted what

---

## 5. AWS Secrets Manager

Secrets Manager securely stores and rotates credentials, API keys, and other sensitive configuration needed by AI applications.

### 5.1 API Key Management for AI Services

AI applications often need to manage:
- Third-party AI API keys (OpenAI, Anthropic direct, etc.)
- Database credentials for RAG data sources
- OAuth client secrets for external integrations
- Encryption keys for client-side encryption

Secrets Manager provides:
- **Encryption at rest** using KMS (AWS managed key by default, CMK optional)
- **Fine-grained IAM access control** per secret
- **Versioning** with staging labels (AWSCURRENT, AWSPREVIOUS, AWSPENDING)
- **Cross-region replication** for disaster recovery
- **Automatic rotation** via Lambda functions

### 5.2 Rotation

Secrets Manager rotation is powered by Lambda functions that execute a four-step workflow:

| Step | Lambda Handler | What Happens |
|---|---|---|
| 1. `createSecret` | Creates a new secret version with `AWSPENDING` label | Generates new credentials |
| 2. `setSecret` | Updates the external service with new credentials | Changes password on the database/service |
| 3. `testSecret` | Validates the new credentials work | Attempts a connection with new credentials |
| 4. `finishSecret` | Moves `AWSCURRENT` to new version, old becomes `AWSPREVIOUS` | Completes the rotation |

#### Rotation Strategies

| Strategy | Description | When to Use |
|---|---|---|
| **Single user** | Updates the password for a single user | Simple applications with one set of credentials |
| **Alternating users** | Creates two users and alternates between them | Zero-downtime rotation. Requires a superuser secret to create the alternate user. |

#### Lambda Execution Role for Rotation

The Lambda function needs:
- `secretsmanager:DescribeSecret`, `secretsmanager:GetSecretValue`, `secretsmanager:PutSecretValue`, `secretsmanager:UpdateSecretVersionStage`
- `kms:Decrypt`, `kms:GenerateDataKey` (if using CMK)
- Database/service-specific permissions (e.g., `rds:DescribeDBInstances` for RDS)

#### Network Access

- If the Lambda function runs in a VPC, it needs either a **NAT gateway** or a **Secrets Manager VPC endpoint** to reach the Secrets Manager API
- The Lambda security group must allow outbound access to the database/service

### 5.3 Integration with Lambda

Two approaches for retrieving secrets in Lambda functions:

| Approach | Description | Best For |
|---|---|---|
| **AWS Parameters and Secrets Lambda Extension** | Runtime-agnostic HTTP interface. Caches secrets for 300 seconds by default. Added as a Lambda layer. | Any runtime. Simple setup. |
| **Powertools for AWS Lambda** | Code-integrated utility. Supports multiple providers (Secrets Manager, Parameter Store, AppConfig). Built-in transformations and type safety. | Python, TypeScript, Java, .NET. |

Both are better than calling the Secrets Manager API directly because they cache secrets locally, reducing API calls and latency.

### 5.4 TypeScript SDK v3 Examples

#### Retrieving a Secret

```typescript
import {
  SecretsManagerClient,
  GetSecretValueCommand,
} from "@aws-sdk/client-secrets-manager";

const smClient = new SecretsManagerClient({ region: "us-east-1" });

const secret = await smClient.send(
  new GetSecretValueCommand({
    SecretId: "my-ai-api-key",
    VersionStage: "AWSCURRENT",
  })
);

const apiKey = secret.SecretString;
```

#### Creating a Secret with Rotation

```typescript
import {
  SecretsManagerClient,
  CreateSecretCommand,
  RotateSecretCommand,
} from "@aws-sdk/client-secrets-manager";

const smClient = new SecretsManagerClient({ region: "us-east-1" });

await smClient.send(
  new CreateSecretCommand({
    Name: "prod/ai-service/api-key",
    SecretString: JSON.stringify({ apiKey: "sk-xxx" }),
    KmsKeyId: "arn:aws:kms:us-east-1:123456789012:key/my-key-id",
    Tags: [{ Key: "Environment", Value: "production" }],
  })
);

await smClient.send(
  new RotateSecretCommand({
    SecretId: "prod/ai-service/api-key",
    RotationLambdaARN: "arn:aws:lambda:us-east-1:123456789012:function:rotate-api-key",
    RotationRules: {
      AutomaticallyAfterDays: 30,
    },
  })
);
```

### 5.5 Key Exam Facts

- Secrets are encrypted at rest with KMS (default: `aws/secretsmanager` managed key)
- Pricing: $0.40/secret/month + $0.05 per 10,000 API calls
- Secrets can store up to **65,536 bytes**
- Secrets Manager supports **resource-based policies** (unlike Bedrock)
- Cross-region replication is automatic for replica secrets
- Secrets Manager is different from Systems Manager Parameter Store:
  - **Secrets Manager**: Built-in rotation, higher cost, designed for credentials
  - **Parameter Store**: No built-in rotation (requires custom Lambda), lower cost (free tier), designed for configuration

---

## 6. Amazon Macie

Amazon Macie discovers and protects **sensitive data in S3** using machine learning and pattern matching. It is tested in the context of securing AI training data and ensuring PII is not inadvertently used.

### 6.1 PII Detection in S3

Macie provides two methods for finding sensitive data:

| Method | Description | When to Use |
|---|---|---|
| **Automated sensitive data discovery** | Continuously samples and analyzes representative objects across your S3 estate. Daily evaluation. Breadth-first approach. | Ongoing monitoring of all S3 buckets |
| **Sensitive data discovery jobs** | Targeted, deeper analysis of specific buckets/prefixes. One-time or scheduled. | Pre-processing AI training data, compliance audits |

#### What Macie Detects

Macie uses **managed data identifiers** (built-in) and **custom data identifiers** (user-defined regex):

| Category | Examples |
|---|---|
| **Credentials** | AWS secret access keys, SSH private keys, PGP keys, HTTP auth headers |
| **Financial** | Credit card numbers, expiration dates, bank account numbers, magnetic stripe data |
| **Personal (PII)** | SSNs, passport numbers, driver's license numbers, names, addresses, phone numbers |
| **Health (PHI)** | Health insurance IDs, DEA numbers, National Provider Identifiers, HCPCS codes |

Custom data identifiers use **regular expressions** to find organization-specific sensitive data (employee IDs, internal project codes, etc.).

#### Allow Lists

Allow lists tell Macie to **ignore** specific patterns or text. Use them for:
- Known test credit card numbers
- Public phone numbers (company switchboard)
- Internal identifiers that match PII patterns but are not sensitive

### 6.2 Sensitive Data Discovery for AI Training Data

Before using data to fine-tune or pre-train a model, scan it with Macie:

1. Create a **sensitive data discovery job** targeting the S3 bucket with training data
2. Configure it to use the relevant managed data identifiers (PII, PHI, credentials)
3. Add custom data identifiers for organization-specific sensitive data
4. Review findings to identify objects containing sensitive data
5. Remediate: remove, redact, or exclude flagged objects from the training dataset

Macie produces:
- **Sensitive data findings**: Detailed reports per-object, including data type, count, and location within the file
- **Discovery results**: Records of each analysis, stored for 90 days (configure S3 export for long-term retention)
- **Sensitivity scores**: Per-bucket scores (0-100) based on the amount and type of sensitive data found

### 6.3 Macie vs Amazon Comprehend PII Detection

This is an exam topic -- understanding when to use each:

| Feature | Amazon Macie | Amazon Comprehend |
|---|---|---|
| **Primary purpose** | S3 data security posture | NLP text analysis |
| **Input** | S3 objects (files, documents) | Text strings (API input) |
| **Detection method** | ML + pattern matching on files | NLP models on text |
| **Scope** | Entire S3 estate | Individual text documents/strings |
| **PII capabilities** | Discover PII in stored data | Detect and redact PII in text at runtime |
| **Output** | Security findings + sensitivity scores | Entity list with confidence scores + redacted text |
| **Use case** | "Scan my training data for PII before fine-tuning" | "Redact PII from user prompts before sending to Bedrock" |
| **Integration** | S3, Security Hub, EventBridge | Bedrock Guardrails (PII filter), Lambda |
| **Cost model** | Per GB scanned + per bucket monitored | Per unit of text analyzed |

> **Exam Gotcha**: Use **Macie** for discovering PII in S3 data stores (bulk, at-rest scanning). Use **Comprehend** (or Bedrock Guardrails PII filters) for detecting/redacting PII in real-time text processing (in-transit). They serve different purposes and are not interchangeable.

### 6.4 Key Exam Facts

- Macie is **optimized for S3** only. For other data stores, move data to S3 first.
- Macie can analyze **encrypted** objects if it has access to the decryption key
- 30-day free trial includes automated discovery (up to 150 GB) and bucket inventory
- Macie creates a service-linked role for accessing S3
- Stores discovery results for **90 days** -- configure S3 export for longer retention
- Security Hub controls: `Macie.1` (is Macie enabled?) and `Macie.2` (is automated discovery enabled?)
- Multi-account support: administrator account manages Macie across organization accounts
- Macie findings provide **exact location data**: line numbers, page numbers, cell references, JSON paths (up to 15 occurrences per finding, 1,000 per discovery result)

---

## 7. AWS WAF (Web Application Firewall)

AWS WAF protects web applications and APIs from common web exploits. For the exam, focus on protecting AI API endpoints from abuse, rate limiting expensive inference calls, and managing AI bot traffic.

### 7.1 Protecting AI API Endpoints

WAF integrates with **API Gateway**, **CloudFront**, **ALB**, and **AppSync** -- the common front doors for AI applications.

#### Architecture

```
Client --> CloudFront (WAF) --> API Gateway --> Lambda --> Bedrock
Client --> API Gateway (WAF) --> Lambda --> Bedrock
Client --> ALB (WAF) --> ECS/EKS --> Bedrock
```

WAF is the **first line of defense**, evaluated before other access control features (Cognito authorizers, IAM, etc.).

#### Web ACL Rule Types

| Rule Type | Description |
|---|---|
| **AWS Managed Rules** | Pre-built rule groups from AWS. Include Core Rule Set, Known Bad Inputs, SQL injection, Bot Control. |
| **Rate-based rules** | Block/count requests that exceed a threshold per time window. Key for AI API protection. |
| **IP-based rules** | Allow/block specific IP addresses or CIDR ranges |
| **Geo-match rules** | Allow/block based on country of origin |
| **Custom rules** | Match on headers, body, query strings, URI path, HTTP method, etc. |

### 7.2 Rate Limiting for AI APIs

AI inference is **expensive** -- rate limiting prevents abuse and controls costs.

#### Rate-Based Rules

- Minimum threshold: **100 requests per 5-minute window** (changed from the previous 2,000)
- Aggregation keys: IP address, forwarded IP, HTTP method, query string, custom header, label namespace, or combination
- Action when threshold exceeded: Block, Count, CAPTCHA, or Challenge
- Mitigation lag: 30-50 seconds after the threshold is exceeded

#### Example: Rate Limit AI Inference by API Key

```json
{
  "Name": "RateLimitAIInference",
  "Priority": 1,
  "Statement": {
    "RateBasedStatement": {
      "Limit": 100,
      "AggregateKeyType": "CUSTOM_KEYS",
      "CustomKeys": [
        {
          "Header": {
            "Name": "x-api-key",
            "TextTransformations": [
              {
                "Priority": 0,
                "Type": "NONE"
              }
            ]
          }
        }
      ]
    }
  },
  "Action": {
    "Block": {}
  },
  "VisibilityConfig": {
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "RateLimitAIInference"
  }
}
```

#### Rate-Based Rules vs Bot Control

| Feature | Rate-Based Rules | Bot Control (Targeted) |
|---|---|---|
| Cost | Included in standard WAF fees | Additional subscription fee |
| Threshold | Configurable (min 100) | Dynamic, based on historical patterns |
| Mitigation speed | 30-50 seconds | Less than 10 seconds |
| IP tracking limit | 10,000 IPs | 50,000 IPs + tokens |
| Best for | Known rate limits for API endpoints | Unknown traffic patterns, bot detection |

### 7.3 Custom Rules for AI-Specific Threats

#### Managing AI Bot Scrapers

AI bots (crawlers from AI companies scraping content for training data) are a growing concern:

1. **robots.txt**: Basic protection, but bots can ignore it
2. **Bot Control (Common)**: Identify and label AI bots. Set action to Count initially to analyze traffic.
3. **Custom rules**: Block specific User-Agent strings (e.g., `GPTBot`, `ClaudeBot`, `Bytespider`)
4. **Challenge/CAPTCHA**: Force suspected bots to prove they are human
5. **Honeypot**: Create hidden endpoints that only bots would find

#### Protecting Against Prompt Injection via WAF

While WAF cannot understand prompt injection semantically, you can:
- Block requests with suspicious patterns in the body (regex matching)
- Rate-limit large request bodies (prompt injection often involves large payloads)
- Use custom rules to block known prompt injection signatures
- Combine with Bedrock Guardrails for defense-in-depth

### 7.4 AWS Solutions Construct: WAF + API Gateway

The `aws-wafwebacl-apigateway` Solutions Construct deploys a WAF web ACL with seven AWS managed rule groups pre-configured and associates it with an API Gateway REST API. Available in CDK (TypeScript, Python, Java).

### 7.5 Key Exam Facts

- WAF operates at **Layer 7** (application layer)
- Web ACLs are **regional** (except for CloudFront, which requires us-east-1)
- Rule evaluation order is by **priority number** (lower = evaluated first)
- A single web ACL can have up to **5,000 WCUs** (Web ACL Capacity Units)
- WAF logs can be sent to **CloudWatch Logs**, **S3**, or **Kinesis Data Firehose**
- WAF supports **labels** -- rules can add labels to requests, and downstream rules can match on those labels
- WAF precedes all other API Gateway access controls (Cognito, IAM, Lambda authorizers)
- Shield Advanced provides DDoS protection at layers 3, 4, and 7 and includes WAF at no additional cost

---

## 8. AWS Encryption SDK

The AWS Encryption SDK is a **client-side encryption library** that implements envelope encryption. It is relevant to the exam for encrypting sensitive AI data before storing or transmitting it.

### 8.1 Core Concepts

| Concept | Description |
|---|---|
| **Envelope encryption** | Encrypt data with a data key, then encrypt the data key with a wrapping key |
| **Data key** | Unique per message. Generated by the SDK. Used to encrypt your data. Never stored in plaintext. |
| **Wrapping key** | Protects data keys. Can be a KMS key, raw AES key, or raw RSA key. |
| **Keyring** | Specifies which wrapping keys to use. KMS keyring is the most common. |
| **Encryption context** | Key-value pairs that provide AAD (Additional Authenticated Data). Bound cryptographically to the ciphertext. Required for decryption. |
| **Encrypted message** | Portable format containing encrypted data + encrypted data keys + metadata |
| **Key commitment** | Guarantees ciphertext can only be decrypted to a single plaintext (prevents key confusion attacks) |

### 8.2 How It Works

#### Encryption Flow

1. You specify a **keyring** with one or more wrapping keys (e.g., KMS key ARN)
2. SDK generates a unique **data key**
3. Each wrapping key in the keyring encrypts a copy of the data key
4. SDK uses the plaintext data key to encrypt your data (AES-256-GCM)
5. SDK destroys the plaintext data key from memory
6. SDK returns an **encrypted message** containing: encrypted data + all encrypted data key copies + algorithm info + encryption context

#### Decryption Flow

1. SDK parses the encrypted message
2. SDK passes the encrypted data keys to the keyring
3. Keyring uses a wrapping key to decrypt one of the data keys
4. SDK verifies key commitment (ensures the correct key)
5. SDK uses the decrypted data key to decrypt the data
6. SDK destroys the data key from memory and returns the plaintext

### 8.3 Multiple Wrapping Keys

A key feature: you can encrypt a data key under **multiple wrapping keys**. Use cases:

- **Multi-region**: Encrypt under KMS keys in us-east-1 and eu-west-1 so either region can decrypt
- **Multi-party**: Encrypt under keys owned by different teams or organizations
- **Key rotation**: Encrypt under both old and new keys during transition
- Any single wrapping key can decrypt independently

### 8.4 Encryption Context (AAD)

The encryption context is **not encrypted** but is **cryptographically bound** to the ciphertext. If you encrypt with context `{"purpose": "training-data"}`, you must provide the same context to decrypt.

Best practices:
- Always use an encryption context
- Include meaningful metadata: purpose, owner, classification level
- It appears in CloudTrail logs when KMS keys are used, aiding auditing

### 8.5 Commitment Policy

Controls whether the SDK uses key commitment:

| Policy | Encrypt | Decrypt |
|---|---|---|
| `ForbidEncryptAllowDecrypt` | No commitment | Allows with or without commitment |
| `RequireEncryptAllowDecrypt` | Requires commitment | Allows with or without commitment |
| `RequireEncryptRequireDecrypt` (default) | Requires commitment | Requires commitment |

> **Exam Gotcha**: Use the default `RequireEncryptRequireDecrypt` unless you need backward compatibility with older ciphertext that lacks key commitment.

### 8.6 Language Support

The SDK is available in: **JavaScript/Node.js**, Python, Java, C, .NET, Rust, Go. All implementations are interoperable -- data encrypted in one language can be decrypted in another (assuming the same wrapping keys).

### 8.7 TypeScript/JavaScript Example

```typescript
import {
  buildClient,
  CommitmentPolicy,
  KmsKeyringNode,
} from "@aws-crypto/client-node";

const { encrypt, decrypt } = buildClient(
  CommitmentPolicy.REQUIRE_ENCRYPT_REQUIRE_DECRYPT
);

const keyring = new KmsKeyringNode({
  generatorKeyId:
    "arn:aws:kms:us-east-1:123456789012:key/my-key-id",
  keyIds: [
    "arn:aws:kms:eu-west-1:123456789012:key/my-eu-key-id",
  ],
});

const encryptionContext = {
  purpose: "ai-training-data",
  dataset: "customer-reviews-v3",
};

// Encrypt
const { result: ciphertext } = await encrypt(keyring, Buffer.from("sensitive training data"), {
  encryptionContext,
});

// Decrypt
const { plaintext, messageHeader } = await decrypt(keyring, ciphertext);

// Verify encryption context matches
for (const [key, value] of Object.entries(encryptionContext)) {
  if (messageHeader.encryptionContext[key] !== value) {
    throw new Error("Encryption context mismatch");
  }
}

console.log(plaintext.toString()); // "sensitive training data"
```

### 8.8 AWS Encryption SDK vs Other Options

| Feature | AWS Encryption SDK | S3 SSE-KMS | S3 Client-Side (S3 Encryption Client) |
|---|---|---|---|
| Where encryption happens | Client-side | Server-side (S3) | Client-side |
| Works with non-S3 data | Yes (any data) | No (S3 only) | No (S3 only) |
| Envelope encryption | Yes | Yes | Yes |
| Portable encrypted format | Yes | No | No |
| Supports non-KMS keys | Yes (raw AES, RSA) | No | Yes |
| Key commitment | Yes | N/A | No |

> **Exam Gotcha**: Use the **AWS Encryption SDK** when you need client-side encryption of data that may be stored anywhere (S3, DynamoDB, local files, transmitted over networks). Use **S3 SSE-KMS** when server-side encryption on S3 is sufficient. Use the **S3 Encryption Client** only if you specifically need client-side encryption for S3 objects.

### 8.9 Key Exam Facts

- The Encryption SDK does **not require** any AWS service -- it can use raw AES/RSA keys. But it integrates best with KMS.
- The SDK is **open source**
- Default algorithm: AES-256-GCM with HKDF, ECDSA signing, and key commitment
- Data key caching can improve performance for high-throughput workloads but requires careful security configuration (max age, max bytes, max messages)
- The encrypted message format is **portable** across all language implementations
- Digital signatures (ECDSA) add integrity but **increase decryption cost** significantly

---

## 9. Cross-Cutting Exam Themes

### 9.1 Defense in Depth for AI Applications

The exam expects you to know how these services work together:

```
Layer 1: Edge Protection         --> AWS WAF + Shield (DDoS, bot control, rate limiting)
Layer 2: Identity Verification   --> Cognito (user auth) + Identity Center (admin SSO)
Layer 3: API Authorization       --> API Gateway + Cognito Authorizer / IAM Auth
Layer 4: Service Authorization   --> IAM policies (least privilege for Bedrock access)
Layer 5: Org Governance          --> SCPs (model restrictions, region restrictions)
Layer 6: Data Protection (rest)  --> KMS (encryption), Macie (PII detection)
Layer 7: Data Protection (transit) --> TLS everywhere, Encryption SDK (client-side)
Layer 8: Secrets Management      --> Secrets Manager (API keys, credentials, rotation)
Layer 9: Monitoring              --> CloudTrail, Access Analyzer, Security Hub
```

### 9.2 Common Exam Scenarios

| Scenario | Answer |
|---|---|
| "How do you restrict which FM a developer can invoke?" | IAM policy with specific model ARNs in `Resource` |
| "How do you enforce model restrictions across all accounts?" | SCP with `Deny` on non-approved model ARNs |
| "How do you ensure all model calls use a guardrail?" | IAM condition key `bedrock:GuardrailIdentifier` |
| "How do you add user auth to an AI chatbot API?" | Cognito User Pool + API Gateway authorizer |
| "How do you scan training data for PII?" | Amazon Macie sensitive data discovery job |
| "How do you redact PII from prompts in real-time?" | Bedrock Guardrails PII filter (or Comprehend) |
| "How do you protect an AI API from abuse?" | WAF rate-based rules on API Gateway |
| "How do you encrypt training data with your own key?" | KMS customer managed key with S3 SSE-KMS or Encryption SDK |
| "How do you securely store third-party AI API keys?" | Secrets Manager with rotation |
| "How do you find unused Bedrock permissions?" | IAM Access Analyzer unused access analyzer |
| "How do you give AI agents temporary access to AWS?" | Cognito Identity Pool with IAM role mapping |
| "How do you encrypt data client-side before upload?" | AWS Encryption SDK with KMS keyring |
| "How do you rotate database credentials used by a RAG pipeline?" | Secrets Manager with Lambda rotation function |
| "How do you manage SSO for AI dev teams across accounts?" | IAM Identity Center with permission sets |

### 9.3 Key Metrics and Limits

| Service | Metric/Limit |
|---|---|
| KMS | 4 KB direct encryption limit; symmetric key: 5,500-30,000 requests/sec (varies by region) |
| Secrets Manager | 65,536 byte max secret size; 40,000 API calls/sec per region |
| WAF | 5,000 WCU per web ACL; rate-based rule min threshold: 100/5 min |
| Cognito User Pools | 70 custom attributes max; 5 failed logins before lockout |
| Cognito Identity Pools | 60 identity providers per pool |
| Macie | 10,000 S3 buckets evaluated per account; 90-day finding retention |
| IAM | 5,120 characters max for inline policy; 6,144 characters max for managed policy |
| SCPs | 5,120 characters max; 5 SCPs per OU |
| Access Analyzer | 1-365 day tracking period for unused access |
