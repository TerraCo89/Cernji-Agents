/**
 * Performance timing utilities for logging
 */

import type { Logger } from 'pino';

/**
 * Class method decorator to log execution time
 *
 * @param level - Log level to use (default: 'info')
 *
 * @example
 * ```typescript
 * class MyService {
 *   @Timed()
 *   async expensiveOperation() {
 *     // ... code ...
 *   }
 * }
 * ```
 */
export function Timed(level: 'trace' | 'debug' | 'info' | 'warn' | 'error' = 'info') {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (this: any, ...args: any[]) {
      const startTime = performance.now();
      const logger = this.logger as Logger | undefined;

      try {
        const result = await originalMethod.apply(this, args);
        return result;
      } finally {
        const durationMs = performance.now() - startTime;

        if (logger && typeof logger[level] === 'function') {
          logger[level](
            {
              function: propertyKey,
              duration_ms: durationMs,
              duration_ns: durationMs * 1_000_000,
            },
            `Function ${propertyKey} completed`
          );
        }
      }
    };

    return descriptor;
  };
}

/**
 * Manual timing context for code blocks
 *
 * @example
 * ```typescript
 * const timer = new TimingContext(logger, 'database_query');
 * // ... code to time ...
 * timer.end(); // Logs duration
 * ```
 */
export class TimingContext {
  private startTime: number;
  private durationMs: number = 0;

  constructor(
    private logger: Logger,
    private operation: string,
    private level: 'trace' | 'debug' | 'info' | 'warn' | 'error' = 'info'
  ) {
    this.startTime = performance.now();
  }

  /**
   * End timing and log duration
   */
  end(error?: Error): void {
    this.durationMs = performance.now() - this.startTime;

    if (typeof this.logger[this.level] === 'function') {
      this.logger[this.level](
        {
          operation: this.operation,
          duration_ms: this.durationMs,
          duration_ns: this.durationMs * 1_000_000,
          error: error !== undefined,
        },
        `Operation ${this.operation} completed`
      );
    }
  }

  /**
   * Get the current duration without logging
   */
  getDuration(): number {
    return performance.now() - this.startTime;
  }
}

/**
 * Timing middleware for HTTP frameworks (Express, Hono, etc.)
 *
 * @example
 * ```typescript
 * // Express
 * app.use(timingMiddleware(logger));
 *
 * // Hono
 * app.use(timingMiddleware(logger));
 * ```
 */
export function timingMiddleware(logger: Logger) {
  return async (req: any, res: any, next: any) => {
    const startTime = performance.now();
    const path = req.path || req.url;
    const method = req.method;

    // Add timing to response finish
    const originalEnd = res.end;
    res.end = function (this: any, ...args: any[]) {
      const durationMs = performance.now() - startTime;

      logger.info(
        {
          http: {
            request: {
              method,
              path,
            },
            response: {
              status_code: res.statusCode,
            },
          },
          duration_ms: durationMs,
          duration_ns: durationMs * 1_000_000,
        },
        `${method} ${path} ${res.statusCode}`
      );

      return originalEnd.apply(this, args);
    };

    if (next) {
      return next();
    }
  };
}
