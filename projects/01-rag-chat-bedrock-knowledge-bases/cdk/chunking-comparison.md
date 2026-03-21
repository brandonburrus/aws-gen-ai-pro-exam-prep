# Chunking Strategy Comparison

Generated: 2026-03-21T20:00:28.475Z

Endpoint: `https://2yeayr0hni.execute-api.us-east-1.amazonaws.com/chat`

---

## Question 1

> What are the differences between fine-tuning, prompt engineering, and retrieval-augmented generation as techniques for customizing foundation model responses?

### Hierarchical Chunking

Answer: Fine-tuning, prompt engineering, and retrieval-augmented generation (RAG) are three techniques for customizing foundation model responses:

- Fine-tuning involves training a pre-trained foundation model on a specific dataset to improve its performance on a particular task. This requires labeled data and can be resource-intensive. 

- Prompt engineering involves crafting specific prompts or instructions to guide the model's responses. This is a lightweight technique that can achieve good results with well-designed prompts.

- Retrieval-augmented generation combines a retrieval system that retrieves relevant information from an external knowledge base with a generative model. The retrieved information is then used to augment the model's response. This technique allows the model to access external knowledge that it was not trained on.

In summary, fine-tuning requires labeled data and training, prompt engineering relies on crafting effective prompts, and RAG combines retrieval of external knowledge with generation. Each technique has its own trade-offs in terms of resources, complexity, and performance. The choice of technique depends on the specific requirements and constraints of the application.

### Fixed-Size Chunking

Here are the differences between fine-tuning, prompt engineering, and retrieval-augmented generation:

Fine-tuning :
- Involves training a pre-trained model on a specific dataset to improve its performance on a particular task.
- Requires labeled data and can be resource-intensive.
- Best suited for tasks requiring improved performance, domain-specific language, or when labeled data is available.

Prompt engineering :
- Involves crafting well-designed prompts to guide the model's behavior and outputs.
- Can achieve desired results with minimal effort.
- Best suited as the first approach when customizing foundation model responses.

Retrieval-augmented generation (RAG) :
- Involves retrieving relevant information from external knowledge sources and augmenting the model's prompt with this information.
- Best suited when the model needs access to external knowledge sources.
- Can improve the model's performance on tasks requiring external information.

In summary, fine-tuning is best suited for tasks requiring improved performance, prompt engineering is best suited as the first approach, and RAG is best suited when the model needs access to external knowledge sources.

---

## Question 2

> Which AWS services are used to build a machine learning pipeline, and what role does each service play in the data preparation, training, and deployment stages?

### Hierarchical Chunking

Answer:

**Data Preparation Stage:**

1. **Amazon S3:** Stores raw data and intermediate data during the pipeline execution.
2. **AWS Lambda:** Validates and processes data files, such as checking file encoding, size, and format.
3. **Amazon Comprehend:** Extracts named entities and performs sentiment analysis on text and transcripts.
4. **Amazon Transcribe:** Converts audio files to text.
5. **Amazon Rekognition:** Detects labels on images for metadata enrichment.
6. **AWS Glue Data Quality:** Validates tabular metadata against defined rules (optional).

**Training Stage:**

1. **Amazon SageMaker:** Provides a managed service for building, training, and deploying machine learning models.
2. **Amazon SageMaker Processing:** Runs batch data transformation and validation jobs.
3. **Amazon SageMaker Data Wrangler:** Performs visual data preparation, profiling, and feature engineering.
4. **Amazon SageMaker Model Registry:** Catalogs, versions, approves, and deploys customized foundation models.
5. **Amazon SageMaker Pipelines:** Automates MLOps workflows for fine-tuning, evaluation, and deployment.

**Deployment Stage:**

1. **Amazon SageMaker:** Hosts and manages the trained models.
2. **Amazon API Gateway:** Provides a secure entry point for invoking the trained models.
3. **AWS Step Functions:** Orchestrates multi-step workflows, including circuit breakers, clarification flows, query transformation, and prompt testing.
4. **AWS AppConfig:** Stores and dynamically retrieves model IDs and feature flags without code deployment.

### Fixed-Size Chunking

Here are the AWS services used to build a machine learning pipeline and their roles in the data preparation, training, and deployment stages:

1. **Amazon S3**: This service is used as the input file store and output store. It integrates with EventBridge for triggering the pipeline.
2. **AWS Lambda**: This service is used for validation, processing, payload building, and model invocation.
3. **Amazon SageMaker**: This service is used for data preparation, training, and deployment of machine learning models.
4. **Amazon EventBridge**: This service is used to trigger the pipeline when new files are received in the S3 bucket.
5. **AWS Step Functions**: This service is used for full pipeline orchestration with parallel states and error handling.
6. **Amazon CloudWatch Logs**: This service is used for logging the execution of Step Functions and Lambda functions.
7. **AWS IAM**: This service is used to manage least-privilege roles for Lambda and Step Functions.

These services work together to create a robust machine learning pipeline that can handle data preparation, training, and deployment of machine learning models.

---

## Question 3

> How does Amazon Bedrock evaluate foundation model performance using built-in evaluation jobs, and what metrics does it report?

### Hierarchical Chunking

Answer: Amazon Bedrock provides three evaluation methods to evaluate foundation model performance:

1. Programmatic evaluation: This uses predefined NLP metrics like accuracy, robustness, and toxicity against curated datasets. It provides a quick baseline comparison of model performance.

2. Human evaluation: This allows you to bring your own dataset and define custom metrics. You can use your own team or AWS-managed workers to evaluate the model outputs.

3. LLM-as-a-Judge evaluation: This uses a judge model (e.g. Anthropic's Claude) to score the generator model's output using curated or custom metrics. It provides scalable human-like quality at up to 98% cost savings compared to full human evaluation.

The built-in metrics reported by LLM-as-a-Judge evaluation include:

- Correctness: Is the response accurate?
- Completeness: Does the response answer all aspects of the question?
- Faithfulness: Does the response contain only information found in the provided context?
- Helpfulness: Is the response useful, coherent, and does it anticipate implicit needs?
- Coherence: Is the response logically consistent without gaps or contradictions?
- Relevance: Is the response relevant to the prompt?
- Following instructions: Does the response follow exact directions from the prompt?
- Professional style and tone: Is the style appropriate for a professional setting?
- Harmfulness: Does the response contain harmful content?
- Stereotyping: Does the response contain stereotypes (positive or negative)?
- Refusal: Does the response decline to answer or reject the request?

All metric scores range from 0 to 1, with closer to 1 indicating more of that characteristic. Custom metrics are also supported.

### Fixed-Size Chunking

Amazon Bedrock evaluates foundation model performance using built-in evaluation jobs, which include the following methods:

1. **Programmatic (automatic) evaluation**: This method uses predefined NLP metrics such as accuracy, robustness, and toxicity against curated datasets to provide a quick baseline comparison.
2. **Human evaluation**: This method allows you to bring your own dataset, define custom metrics, and use your team or AWS-managed workers to evaluate subjective quality, brand voice, style, and nuance.
3. **LLM-as-a-Judge**: This method uses a judge model (e.g., Amazon Nova Pro, Anthropic Claude, Meta Llama 3.1 70B Instruct, Mistral Large) to score the generator model's output using curated or custom metrics. Bedrock LLM-as-a-Judge built-in metrics include correctness, completeness, faithfulness, helpfulness, coherence, relevance, and following instructions.

The built-in metrics reported by Amazon Bedrock include:

- **Correctness**: Is the response accurate? Considers ground truth if provided.
- **Completeness**: Does the response answer all aspects of the question?.
- **Faithfulness**: Does the response contain only information found in the provided context?.
- **Helpfulness**: Is the response useful, coherent, and does it anticipate implicit needs?.
- **Coherence**: Is the response logically consistent without gaps or contradictions?.
- **Relevance**: Is the response relevant to the prompt?.
- **Following instructions**: Does the response follow exact directions from the prompt?.
- **Professional style and tone**: Is the style appropriate for a professional setting?.
- **Harmfulness**: Does the response contain harmful content?.
- **Stereotyping**: Does the response contain stereotypes (positive or negative)?.
- **Refusal**: Does the response decline to answer or reject the request?.

All metric scores range from 0 to 1, with closer to 1 indicating more of that characteristic. Custom metrics are also supported, allowing you to evaluate against specific brand voice, categorical rubrics, or domain-specific criteria.

---

## Question 4

> What are the responsible AI practices recommended by AWS, including fairness, toxicity detection, and the use of human review with Amazon Augmented AI?

### Hierarchical Chunking

Answer: AWS recommends several responsible AI practices, including:

1. **Fairness**: AWS recommends implementing robust testing frameworks to detect potential bias and regularly auditing outcomes across different segments. This includes specifying balanced, neutral perspectives in instructions, instructing the model to consider multiple demographic groups, and using Chain-of-Thought to make reasoning explicit and auditable.

2. **Toxicity Detection**: AWS recommends implementing content filters, word filters, and sensitive information filters to detect and block toxic content. This includes setting strength levels per category, defining denied topics, and blocking/masking personally identifiable information (PII).

3. **Human Review with Amazon Augmented AI (A2I)**: AWS recommends integrating human review into ML workflows using Amazon A2I. This includes using built-in task types, custom task types, and work teams to review low-confidence outputs, audit responses for quality and bias, build feedback loops, and validate RAG answers against sources.

4. **Transparency**: AWS recommends clearly communicating when and how AI is being used, documenting model limitations, and tracking decisions across the pipeline. This includes using SageMaker Model Cards, AI Service Cards, and Prompt Flows tracing to provide transparency and enable stakeholders to make informed choices about their engagement with an AI system.

5. **Safety**: AWS recommends implementing comprehensive safety frameworks, including content filtering, output validation, and clear escalation paths. This includes using Bedrock guardrails based on policy requirements, model cards to document Foundation Model limitations, and Lambda functions for automated compliance checks.

6. **Explainability**: AWS recommends implementing interpretability techniques and translating complex model decisions into understandable explanations. This includes using SageMaker Clarify SHAP values, extended thinking, and agent tracing to explain individual predictions and show reasoning behind FM decisions.

7. **Privacy and Security**: AWS recommends implementing sophisticated data governance frameworks, including encryption, access controls, and data minimization practices. This includes using SageMaker Model Cards, AI Service Cards, and Lambda functions for automated compliance checks to appropriately obtain, use, and protect data and models.

8. **Controllability**: AWS recommends implementing robust monitoring systems that track performance metrics, user feedback, and system outputs. This includes using CloudWatch, SageMaker Model Monitor, and GuardrailTrace to monitor model performance and detect guardrail-blocked content.

### Fixed-Size Chunking

Here are the responsible AI practices recommended by AWS:

1. **Fairness**: AWS recommends implementing robust testing frameworks to detect potential bias and regularly auditing outcomes across different segments to ensure fairness.
2. **Toxicity Detection**: AWS provides tools and services to detect and mitigate toxicity in AI systems. For example, Amazon Comprehend can be used to detect toxic content in text data.
3. **Human Review with Amazon Augmented AI (A2I)**: AWS recommends integrating human review into ML workflows using Amazon A2I. This can be done by setting up conditions for review, such as when the confidence threshold is below a specified value, and using work teams like Mechanical Turk, vendor-managed, or private workforce for human review.

These practices help ensure that AI systems are fair, safe, and reliable, and that they are used responsibly and ethically.

---

## Question 5

> Explain how Amazon Bedrock Guardrails work to filter harmful content and enforce topic boundaries in generative AI applications.

### Hierarchical Chunking

Answer: Amazon Bedrock Guardrails work by implementing a combination of multiple policies that evaluate both user inputs and model responses to filter harmful content and enforce topic boundaries in generative AI applications. Here's how they work:

1. Guardrails are configured with various filter policies, including content filters, denied topics, word filters, sensitive information filters, contextual grounding checks, and automated reasoning checks.

2. Content filters detect harmful content across categories like hate, insults, sexual content, violence, misconduct, and prompt attacks.

3. Denied topics allow users to block specific undesirable topics, up to 30 per guardrail.

4. Word filters enable exact-match blocking of custom words/phrases and built-in profanity lists.

5. Sensitive information filters detect and block personally identifiable information (PII) using machine learning and custom regex patterns.

6. Contextual grounding checks detect hallucinations based on grounding source and query relevance.

7. Automated reasoning checks validate responses against logical rules using formal mathematical reasoning.

8. Input evaluation happens in parallel across all configured policies for low latency.

9. If the input is blocked, the foundation model is never invoked.

10. If the output is blocked, the response is replaced with blocked messaging or masked.

11. Guardrails integrate natively with Bedrock Agents, Knowledge Bases, and Prompt Flows.

In summary, Amazon Bedrock Guardrails provide a comprehensive set of policies and filters to detect and block harmful content, enforce topic boundaries, and ensure safe and responsible use of generative AI applications.

### Fixed-Size Chunking

Amazon Bedrock Guardrails work by implementing a multi-layered approach to filter harmful content and enforce topic boundaries in generative AI applications. Here's how it works:

1. **Content Filter Sensitivity Levels**: Guardrails allow you to set sensitivity levels for content filters, which can range from low to high, depending on the level of risk you want to mitigate.
2. **Denied Topics**: You can define specific topics that are not allowed in the generated content. For example, you can block topics like "requests to roleplay as a different AI system", "requests involving violence", or "competitor product comparisons".
3. **Word Filters**: Guardrails provide word filters that can block profanity and hate speech. You can set the strength of the word filters to high, medium, or low, depending on your requirements.
4. **Sensitive Information Filters**: Guardrails can also filter out sensitive information, such as personally identifiable information (PII), from the generated content.
5. **Automated Reasoning Checks**: Guardrails include automated reasoning checks to ensure that the generated content is contextually grounded and relevant to the input prompt.

By implementing these filters and checks, Amazon Bedrock Guardrails can help ensure that the generated content is safe, relevant, and free from harmful or inappropriate content.
