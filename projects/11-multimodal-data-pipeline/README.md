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

- AWS CLI v2 with Lambda, Step Functions, S3, Transcribe, Comprehend, Rekognition, Bedrock, Glue, EventBridge, and IAM permissions
- Python 3.11+ with `boto3`
- AWS SAM CLI recommended for multi-Lambda packaging

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

1. **Create the S3 bucket** with `incoming/text/`, `incoming/images/`, `incoming/audio/`, and `output/` prefixes. Enable versioning.

2. **Write and deploy the validation Lambdas.** Each reads the file from S3 and returns `{ "valid": bool, "errors": list }`. `ValidateText`: check size < 100KB and UTF-8 decodable. `ValidateImage`: use `imghdr` or check magic bytes for JPEG/PNG, check that file size < 5MB. `ValidateAudio`: check file extension and size < 50MB (actual duration check requires a library; for the lab, size is a sufficient proxy).

3. **Write and deploy the processing Lambdas.**
   - `ProcessText`: call `comprehend.detect_entities` and `comprehend.detect_sentiment`. Return entities list and sentiment.
   - `ProcessImage`: call `rekognition.detect_labels`. Return top 10 labels.
   - `ProcessAudio`: start an Amazon Transcribe job (`transcribe.start_transcription_job`), poll until status is COMPLETED (or use Step Functions Wait + Lambda poll pattern), fetch transcript from the Transcribe output S3 URI, run Comprehend entity detection on the transcript text.

4. **Write `build_bedrock_payload.py` (Lambda).** Accept the merged outputs from all three processing Lambdas. Build the messages array: `[{ "role": "user", "content": [ { "type": "text", "text": f"Text document:\n{text_content}\nEntities: {entities}" }, { "type": "image", "source": { "type": "base64", "media_type": "image/jpeg", "data": "<base64>" } }, { "type": "text", "text": f"Audio transcript:\n{transcript}\nEntities: {audio_entities}" } ] }]`. Fetch the image from S3, base64-encode it.

5. **Write `invoke_multimodal.py` (Lambda).** Accept the messages payload. Call `bedrock:InvokeModel` with Claude 3 Sonnet. Write the response + full pipeline metadata to `s3://bucket/output/<run_id>/result.json`.

6. **Define the Step Functions workflow.** Use Amazon States Language or CDK:
   - State `ValidateAll`: Parallel, three branches (one per data type), each is a Lambda task with Catch → `HandleValidationError`.
   - State `ProcessAll`: Parallel, three branches.
   - State `BuildPayload`: Lambda task.
   - State `InvokeModel`: Lambda task.
   - State `HandleValidationError`: Lambda writes error record to S3, then transitions to `Fail`.

7. **Configure Retry and Catch.** Add `Retry` on `ProcessAudio` (Transcribe jobs take 10-60 seconds; use a Step Functions Wait state or Lambda polling loop). Add `Catch` on the model invocation for `ThrottlingException`.

8. **Write `test_pipeline.py`.** Upload test files to S3. Start execution with `sfn.start_execution(...)`. Poll `sfn.describe_execution(...)` until status is SUCCEEDED or FAILED. Print the result from S3.

9. **Build the `wa-review.md` document.** Open `WELL-ARCHITECTED-AI-LENS.md`. For each pillar, pick one evaluation question and write a 2-3 sentence answer reflecting the architecture you built.

10. **Run the pipeline end-to-end.** Fix any IAM, payload format, or Transcribe polling issues.

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
