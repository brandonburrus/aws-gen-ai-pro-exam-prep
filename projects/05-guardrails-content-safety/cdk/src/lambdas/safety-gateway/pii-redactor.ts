import { ComprehendClient, DetectPiiEntitiesCommand } from '@aws-sdk/client-comprehend';

const MIN_PII_REDACTION_CONFIDENCE = 0.5;

const comprehend = new ComprehendClient({
  region: process.env.AWS_REGION ?? 'us-east-1',
});

export interface PiiRedactionResult {
  redactedText: string;
  didRedact: boolean;
}

export async function redactPII(
  text: string,
  confidenceRedactionThreshold: number = MIN_PII_REDACTION_CONFIDENCE
): Promise<PiiRedactionResult> {
  const piiDetection = await comprehend.send(
    new DetectPiiEntitiesCommand({
      Text: text,
      LanguageCode: 'en',
    }),
  );

  let redactedText = text;
  if (piiDetection.Entities) {
    for (const entity of piiDetection.Entities) {
      if (
        (entity.Score ?? 0) >= confidenceRedactionThreshold
          && entity.BeginOffset !== undefined
          && entity.EndOffset !== undefined
      ) {
        // NOTE: Naive replacement algorithm that may produce incorrect results
        redactedText =
          redactedText.slice(0, entity.BeginOffset) +
          `[REDACTED_${(entity.Type ?? 'INFO').toUpperCase()}]` +
          redactedText.slice(entity.EndOffset);
      }
    }
  }

  const redactionResult: PiiRedactionResult = {
    redactedText,
    didRedact: !!piiDetection.Entities && piiDetection.Entities.length > 0,
  }
  console.log('PII Redaction Result:', {
    result: redactionResult,
    piiEntities: piiDetection.Entities,
  });

  return redactionResult;
}
