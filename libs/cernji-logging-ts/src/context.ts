/**
 * Correlation ID context management
 *
 * This module provides a unified API for correlation ID tracking that works
 * in both Node.js and browser environments:
 *
 * - Node.js: Uses AsyncLocalStorage for proper async context isolation
 * - Browser: Uses simple in-memory storage with best-effort context propagation
 *
 * The correct implementation is automatically selected based on the environment
 * via package.json conditional exports.
 */

// Re-export from server implementation by default (Node.js)
// Browser builds will use context.browser.ts via package.json exports
export {
  getCorrelationId,
  withCorrelationId,
  generateCorrelationId,
  correlationIdMixin,
} from './context.server.js';
