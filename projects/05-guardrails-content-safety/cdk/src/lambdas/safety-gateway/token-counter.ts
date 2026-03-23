import { countTokens } from '@anthropic-ai/tokenizer'

const MAX_INPUT_TOKENS_ALLOWED = 10_000;

export class RequestTooLargeError extends Error {
  constructor(tokenCount: number) {
    super(`Request has ${tokenCount} tokens, which exceeds the maximum allowed of ${MAX_INPUT_TOKENS_ALLOWED}.`)
    this.name = 'RequestTooLargeError'
  }
}

export function validPromptSize(prompt: string, maxTokens = MAX_INPUT_TOKENS_ALLOWED): void {
  const tokenCount = countTokens(prompt)
  console.log(`Prompt has ${tokenCount} tokens.`)
  if (tokenCount > maxTokens) {
    throw new RequestTooLargeError(tokenCount)
  }
}
