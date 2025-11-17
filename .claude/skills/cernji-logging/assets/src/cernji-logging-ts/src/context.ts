/**
 * Correlation ID context management using AsyncLocalStorage
 */

import { AsyncLocalStorage } from 'async_hooks';
import { randomUUID } from 'crypto';

// AsyncLocalStorage to store correlation ID
const correlationIdStorage = new AsyncLocalStorage<string>();

/**
 * Get the current correlation ID from context
 */
export function getCorrelationId(): string | undefined {
  return correlationIdStorage.getStore();
}

/**
 * Set correlation ID and execute a function within that context
 *
 * @param correlationId - The correlation ID to set (generates new UUID if null)
 * @param fn - Async function to execute with the correlation ID in context
 * @returns The result of the function
 *
 * @example
 * ```typescript
 * await withCorrelationId('req-12345', async () => {
 *   logger.info('Processing request'); // Includes trace.id
 * });
 * ```
 */
export async function withCorrelationId<T>(
  correlationId: string | null,
  fn: () => Promise<T>
): Promise<T> {
  const id = correlationId || generateCorrelationId();
  return correlationIdStorage.run(id, fn);
}

/**
 * Generate a new correlation ID
 */
export function generateCorrelationId(): string {
  return randomUUID();
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
