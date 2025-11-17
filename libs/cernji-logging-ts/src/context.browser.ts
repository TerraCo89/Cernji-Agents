/**
 * Browser-compatible correlation ID context management
 *
 * Note: Browser environments don't have AsyncLocalStorage, so correlation ID
 * tracking is simplified. IDs can be generated but not automatically propagated
 * across async boundaries like in Node.js.
 */

// In-memory storage for browser (single-threaded, no async context isolation)
let currentCorrelationId: string | undefined;

/**
 * Get the current correlation ID from context
 *
 * Note: In browser environments, this returns the last set correlation ID.
 * Unlike Node.js, it doesn't automatically propagate across async boundaries.
 */
export function getCorrelationId(): string | undefined {
  return currentCorrelationId;
}

/**
 * Set correlation ID and execute a function within that context
 *
 * @param correlationId - The correlation ID to set (generates new UUID if null)
 * @param fn - Async function to execute with the correlation ID in context
 * @returns The result of the function
 *
 * Note: In browser environments, this sets a global correlation ID for the
 * duration of the function execution, but doesn't provide the same isolation
 * guarantees as Node.js AsyncLocalStorage.
 *
 * @example
 * ```typescript
 * await withCorrelationId('req-12345', async () => {
 *   logger.info('Processing request'); // May include trace.id
 * });
 * ```
 */
export async function withCorrelationId<T>(
  correlationId: string | null,
  fn: () => Promise<T>
): Promise<T> {
  const id = correlationId || generateCorrelationId();
  const previousId = currentCorrelationId;

  try {
    currentCorrelationId = id;
    return await fn();
  } finally {
    currentCorrelationId = previousId;
  }
}

/**
 * Generate a new correlation ID
 *
 * Uses crypto.randomUUID() which is available in modern browsers
 */
export function generateCorrelationId(): string {
  // Use Web Crypto API (available in modern browsers)
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  // Fallback for older browsers
  return `${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
}

/**
 * Mixin function to inject correlation ID into log objects
 * Used by Pino to automatically add trace.id to all log records
 */
export function correlationIdMixin() {
  const correlationId = getCorrelationId();
  if (correlationId) {
    return {
      trace: {
        id: correlationId,
      },
    };
  }
  return {};
}
