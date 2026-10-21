/** Stable error codes used across the core, providers and adapters. */
export const ErrorCodes = Object.freeze({
  UNSUPPORTED: 'UNSUPPORTED',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  NO_MICROPHONE: 'NO_MICROPHONE',
  NO_SPEECH: 'NO_SPEECH',
  NETWORK: 'NETWORK',
  RECOGNITION_FAILED: 'RECOGNITION_FAILED',
  NO_MATCH: 'NO_MATCH',
  ACTION_FAILED: 'ACTION_FAILED',
});

/** Default user-facing English messages. Safe to speak aloud. */
export const DEFAULT_MESSAGES = Object.freeze({
  [ErrorCodes.UNSUPPORTED]:
    "Voice recognition isn't supported in this browser. You can type a command instead.",
  [ErrorCodes.PERMISSION_DENIED]:
    'Microphone access is blocked. Please allow it in your browser settings.',
  [ErrorCodes.NO_MICROPHONE]: "I couldn't find a microphone.",
  [ErrorCodes.NO_SPEECH]: "I didn't hear anything. Please try again.",
  [ErrorCodes.NETWORK]: 'Speech recognition needs an internet connection.',
  [ErrorCodes.RECOGNITION_FAILED]: 'Speech recognition failed. Please try again.',
  [ErrorCodes.NO_MATCH]: "Sorry, I didn't understand that.",
  [ErrorCodes.ACTION_FAILED]: 'Something went wrong while doing that.',
});

export class VoiceError extends Error {
  /**
   * @param {string} code one of ErrorCodes
   * @param {string} [message] user-facing message (defaults per code)
   */
  constructor(code, message) {
    super(message || DEFAULT_MESSAGES[code] || 'Something went wrong.');
    this.name = 'VoiceError';
    this.code = code;
  }
}
