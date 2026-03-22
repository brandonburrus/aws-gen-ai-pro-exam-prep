# Project 11: Multimodal Data Pipeline with Validation

## Exam Domains

| Domain | Task | Description |
|--------|------|-------------|
| 1.1 | Analyze requirements and design GenAI solutions | Architectural designs aligned with business needs, Well-Architected Framework GenAI Lens, technical proof-of-concept |
| 1.3 | Implement data validation and processing pipelines for FM consumption | Data validation workflows, multimodal processing (text/image/audio), data formatting for Bedrock API, entity extraction, quality standards |

## Overview

Foundation Models increasingly accept multimodal inputs — text, images, and audio in a single request. But ingesting raw files from multiple sources and preparing them for a multimodal model involves a complex chain of validation, transformation, and formatting steps. This project builds that pipeline as a Step Functions workflow that ingests all three data types from S3, validates them with AWS Glue Data Quality rules and custom Lambda checks, transcribes audio with Amazon Transcribe, extracts entities with Amazon Comprehend, and formats everything into a Bedrock-compatible JSON payload before invoking the model.

The architecture exercise is what sets this project apart from the others. After building the pipeline, you will document it using the Well-Architected Generative AI Lens checklist, answering the lens's evaluation questions for each of its focus areas (data, model, application, security, operations). This reinforces Task 1.1.3 and gives you first-hand experience with the type of architectural review the exam asks about.

## Architecture

```
S3 Trigger (EventBridge + S3 Event Notification)
    |-- s3://bucket/incoming/text/*.txt
    |-- s3://bucket/incoming/images/*.jpg
    |-- s3://bucket/incoming/audio/*.mp3
    |
    v
Step Functions: MultimodalIngestionPipeline (Standard)
    |
    |-- Stage 1: Parallel validation
    |       |-- Lambda: ValidateTextFile
    |       |       --> check encoding (UTF-8), size < 100KB, non-empty
    |       |-- Lambda: ValidateImage
    |       |       --> check MIME type, dimensions > 100x100, size < 5MB
    |       |-- Lambda: ValidateAudio
    |       |       --> check duration < 30 min, format in [mp3, wav, flac]
    |       |-- (optional) Glue Data Quality job on tabular metadata CSV
    |
    |-- Stage 2: Parallel processing
    |       |-- Lambda: ProcessText
    |       |       --> Comprehend: DetectEntities, DetectSentiment
    |       |       --> extract named entities (PERSON, ORG, LOCATION, DATE)
    |       |-- Lambda: ProcessImage (pass-through; Bedrock handles multimodal images)
    |       |       --> Rekognition: DetectLabels (for metadata enrichment)
    |       |-- Lambda: ProcessAudio
    |               --> Transcribe: StartTranscriptionJob
    |               --> poll until complete (or use EventBridge Transcribe events)
    |               --> fetch transcript JSON from S3
    |               --> Comprehend: DetectEntities on transcript
    |
    |-- Stage 3: Format payload
    |       Lambda: BuildBedrockPayload
    |           --> assemble messages array per Bedrock multi-modal schema:
    |               [
    |                 { role: "user", content: [
    |                   { type: "text", text: "<text + entities>" },
    |                   { type: "image", source: { type: "base64", ... } },
    |                   { type: "text", text: "<audio transcript + entities>" }
    |                 ]}
    |               ]
    |
    |-- Stage 4: Invoke model
            Lambda: InvokeMultimodal
                --> bedrock:InvokeModel (Claude 3 Sonnet with vision)
                --> write response + pipeline metadata to S3 output/

Glue Data Quality (optional parallel path):
    --> validate tabular metadata CSV against defined rules
    --> fail pipeline if DQ score < 0.8
```

**AWS services used:**

- AWS Step Functions (Standard workflow) -- full pipeline orchestration with parallel states and error handling
- AWS Lambda -- validation, processing, payload building, and model invocation
- Amazon S3 -- input file store and output store; EventBridge integration for trigger
- Amazon Transcribe -- audio-to-text transcription
- Amazon Comprehend -- named entity recognition and sentiment analysis on text and transcripts
- Amazon Rekognition -- image label detection for metadata enrichment
- Amazon Bedrock (Claude 3 Sonnet with vision) -- multimodal inference
- AWS Glue Data Quality -- optional tabular metadata validation
- Amazon EventBridge -- S3 event notifications triggering the pipeline
- Amazon CloudWatch Logs -- Step Functions execution logs, Lambda logs
- AWS IAM -- least-privilege roles per Lambda and for Step Functions
- AWS Well-Architected Tool -- architecture review (optional but recommended)

## What You Will Build

1. An S3 bucket with prefixes `incoming/text/`, `incoming/images/`, and `incoming/audio/`, and an EventBridge rule that triggers the Step Functions pipeline when all three prefix types receive a new file (or on manual trigger for simplicity in the lab).
2. Six Lambda functions: `ValidateText`, `ValidateImage`, `ValidateAudio`, `ProcessText`, `ProcessImage`, `ProcessAudio`.
3. A `BuildBedrockPayload` Lambda that merges all processing outputs into a Bedrock-compatible `messages` array for a multimodal request.
4. An `InvokeMultimodal` Lambda that calls `bedrock:InvokeModel` with the assembled payload and writes the output to `s3://bucket/output/<pipeline_run_id>/result.json`.
5. A Step Functions Standard workflow with Parallel states for validation and processing, proper Catch/Retry blocks on each state, and a `Fail` state that writes an error record to S3 if any validation step fails.
6. Sample test data: one text file (a short article), one JPEG image (any public domain photo), and one MP3 audio file (a short public domain speech or a text-to-speech generated clip).
7. A Well-Architected Generative AI Lens review document (`wa-review.md`) answering at least one evaluation question per lens pillar (data quality, model selection, application design, security, operations). Base your answers on the architecture you actually built.
8. A `test_pipeline.py` script that uploads the three test files to S3 and starts the Step Functions execution, then polls until completion and prints the model's response from the output file.

## Target Outcomes

By the end of this project you should be able to verify each of the following:

- [ ] Uploading a valid text file, image, and audio clip and starting the pipeline produces a successful Step Functions execution with all parallel branches completing.
- [ ] The model's response in `output/<run_id>/result.json` references content from all three input modalities (text entities, image labels, and transcribed speech content), demonstrating that the multimodal payload was assembled correctly.
- [ ] Uploading an oversized image (> 5MB) causes the `ValidateImage` Lambda to return a validation error, the pipeline transitions to the `Fail` state, and an error record is written to S3 — the model invocation Lambda is never called.
- [ ] The audio transcript produced by Amazon Transcribe is present in the `ProcessAudio` Lambda output and is readable.
- [ ] The `wa-review.md` document contains substantive answers to at least 5 Well-Architected Lens questions, not just template placeholders.
- [ ] You can explain why each data type requires its own validation logic (text: encoding, audio: duration/format, image: dimensions/size) rather than a single generic validator.

## Prerequisites

**Local tooling:**

- Node.js 22+ with npm (for Lambda handler development and AWS SDK v3)
- AWS CLI v2 with Lambda, Step Functions, S3, Transcribe, Comprehend, Rekognition, Bedrock, Glue, EventBridge, and IAM permissions
- Python 3.11+ with `boto3` (for Lambda handler source and the pipeline test script)

**AWS service enablement:**

- Amazon Bedrock model access for Claude 3 Sonnet (with vision capability) in your region
- Amazon Transcribe, Comprehend, and Rekognition available in your region (all generally available)

**Sample data:**

- Text: a 2-3 paragraph article (plain text, UTF-8)
- Image: a JPEG under 5MB (any public domain photo; ensure it has visible subjects for Rekognition to label)
- Audio: an MP3 under 30 minutes. Free options: LibriVox public domain audiobook clips, or generate a short clip with Amazon Polly

**Well-Architected Generative AI Lens:**

The Lens whitepaper is available at `WELL-ARCHITECTED-AI-LENS.md` in this repository. Review the evaluation questions before building to guide architectural decisions.

## Step-by-Step Build Guide

1. **Create an S3 bucket** with versioning enabled and prefixes `incoming/text/`, `incoming/images/`, `incoming/audio/`, and `output/`.

2. **Create an EventBridge rule** that triggers on S3 `Object Created` events matching the `incoming/` prefix. Target the Step Functions state machine (created in a later step). Alternatively, use a manual trigger for simplicity during the lab.

3. **Write the ValidateText Lambda handler** (`lambdas/validate-text/handler.ts`). Read the file from S3. Check size < 100KB and UTF-8 decodable. Return `{ valid: boolean, errors: string[] }`.

4. **Write the ValidateImage Lambda handler** (`lambdas/validate-image/handler.ts`). Read the file from S3. Check magic bytes for JPEG/PNG, verify file size < 5MB. Return `{ valid: boolean, errors: string[] }`.

5. **Write the ValidateAudio Lambda handler** (`lambdas/validate-audio/handler.ts`). Check file extension against `[mp3, wav, flac]` and size < 50MB. Return `{ valid: boolean, errors: string[] }`.

6. **Write the processing Lambda handlers.** `ProcessText` (`lambdas/process-text/handler.ts`): call `comprehend:DetectEntities` and `comprehend:DetectSentiment`, return entities and sentiment. `ProcessImage` (`lambdas/process-image/handler.ts`): call `rekognition:DetectLabels`, return top 10 labels. `ProcessAudio` (`lambdas/process-audio/handler.ts`): start a Transcribe job, poll until complete (or use a Step Functions Wait + poll pattern), fetch the transcript from the Transcribe output S3 URI, run Comprehend entity detection on the transcript.

7. **Write the BuildBedrockPayload Lambda handler** (`lambdas/build-bedrock-payload/handler.ts`). Merge all processing outputs. Assemble the `messages` array with mixed `text` and `image` content types per the Bedrock multimodal schema. Fetch the image from S3 and base64-encode it. Return the complete payload.

8. **Write the InvokeMultimodal Lambda handler** (`lambdas/invoke-multimodal/handler.ts`). Call `bedrock:InvokeModel` with Claude 3 Sonnet and the assembled payload. Write the response and full pipeline metadata to `s3://bucket/output/<run_id>/result.json`.

9. **Create eight Lambda functions** (one per handler above). Runtime: Node.js 22.x. Create execution roles granting the minimum required permissions per function:
   - Validation functions: `s3:GetObject` on the incoming prefixes
   - `ProcessText`: `comprehend:DetectEntities`, `comprehend:DetectSentiment`
   - `ProcessImage`: `rekognition:DetectLabels`
   - `ProcessAudio`: `transcribe:StartTranscriptionJob`, `transcribe:GetTranscriptionJob`, `s3:GetObject` (for transcript output), `comprehend:DetectEntities`
   - `BuildBedrockPayload`: `s3:GetObject` on the incoming prefixes
   - `InvokeMultimodal`: `bedrock:InvokeModel`, `s3:PutObject` on the output prefix

10. **Create a Step Functions Standard workflow** (`MultimodalIngestionPipeline`) with `LogLevel.ALL` for CloudWatch Logs. Structure:
    - `ValidateAll`: Parallel state with three branches (ValidateText, ValidateImage, ValidateAudio). Each branch has a Catch block that transitions to a `HandleValidationError` state.
    - `ProcessAll`: Parallel state with three branches (ProcessText, ProcessImage, ProcessAudio).
    - `BuildPayload`: Lambda invocation.
    - `InvokeModel`: Lambda invocation with Retry on `ThrottlingException` (3 attempts, 2s backoff).
    - `HandleValidationError`: writes an error record to S3, then transitions to a Fail state.
    Grant the state machine execution role `lambda:InvokeFunction` on all eight Lambda functions.

11. **Deploy all resources to your AWS account** using your preferred infrastructure-as-code tool or the AWS Management Console. Upload the three sample test files to `incoming/text/`, `incoming/images/`, and `incoming/audio/` to trigger the pipeline automatically, or start the state machine manually via `scripts/test_pipeline.py`.

12. **Build the Well-Architected review document** (`wa-review.md`). For each pillar in the Well-Architected Generative AI Lens, pick one evaluation question and write a 2-3 sentence answer reflecting the architecture you built. The document must contain substantive answers to at least 5 questions.

## Key Exam Concepts Practiced

- Multimodal data processing pipeline: text, image, and audio each require distinct AWS services (Task 1.3.2)
- Data validation as a pre-ingestion quality gate: checking format, size, and encoding before processing (Task 1.3.1)
- Amazon Transcribe for audio-to-text transformation in a GenAI pipeline (Task 1.3.2)
- Amazon Comprehend for entity extraction to enrich model input context (Task 1.3.4)
- Bedrock multimodal payload format: the `messages` array with mixed `text` and `image` content types (Task 1.3.3)
- Step Functions Parallel state for concurrent validation and processing branches (Task 1.3.1)
- Well-Architected Generative AI Lens as a design review framework (Task 1.1.3)
- Error handling in data pipelines: validation failure → Fail state, no silent data corruption (Task 1.3.1)
- Amazon Rekognition as a metadata enrichment service (not directly in Bedrock's vision; supplements multimodal context) (Task 1.3.4)
