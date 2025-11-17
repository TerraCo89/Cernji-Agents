/**
 * Cernji Logging - Browser-compatible logging
 *
 * Provides a console-based logger with a Pino-compatible API for browser environments.
 */

import { getConfig } from './config.js';
import { correlationIdMixin } from './context.browser.js';

export { getCorrelationId, withCorrelationId, generateCorrelationId } from './context.browser.js';
export { Timed, TimingContext } from './timing.js';
export type { LogConfig, LogLevel, LogFormat, Environment } from './config.js';

// Browser-compatible Logger type (subset of Pino Logger)
export interface Logger {
  trace(obj: object, msg?: string): void;
  trace(msg: string): void;
  debug(obj: object, msg?: string): void;
  debug(msg: string): void;
  info(obj: object, msg?: string): void;
  info(msg: string): void;
  warn(obj: object, msg?: string): void;
  warn(msg: string): void;
  error(obj: object, msg?: string): void;
  error(msg: string): void;
  fatal(obj: object, msg?: string): void;
  fatal(msg: string): void;
  child(bindings: object): Logger;
}

/**
 * Create a console-based logger that mimics Pino's API
 */
function createConsoleLogger(
  name?: string,
  bindings: object = {}
): Logger {
  const config = getConfig();
  const logLevels = ['trace', 'debug', 'info', 'warn', 'error', 'fatal'];
  const currentLevelIndex = logLevels.indexOf(config.level);

  function shouldLog(level: string): boolean {
    const levelIndex = logLevels.indexOf(level);
    return levelIndex >= currentLevelIndex;
  }

  function formatMessage(level: string, obj: object | string, msg?: string): void {
    if (!shouldLog(level)) return;

    const timestamp = new Date().toISOString();
    const correlation = correlationIdMixin();
    const context = {
      '@timestamp': timestamp,
      'log.level': level,
      service: {
        name: config.serviceName,
        version: config.serviceVersion,
        environment: config.environment,
      },
      ...correlation,
      ...bindings,
      ...(name ? { name } : {}),
    };

    // Handle both (obj, msg) and (msg) signatures
    if (typeof obj === 'string') {
      const message = obj;
      const logData = { ...context, message };
      consoleLog(level, logData);
    } else {
      const message = msg || '';
      const logData = { ...context, ...obj, message };
      consoleLog(level, logData);
    }
  }

  function consoleLog(level: string, data: object): void {
    const message = (data as any).message || '';
    const prefix = `[${(data as any)['@timestamp']}] ${level.toUpperCase()}`;

    // Use appropriate console method
    switch (level) {
      case 'trace':
      case 'debug':
        console.debug(prefix, message, data);
        break;
      case 'info':
        console.info(prefix, message, data);
        break;
      case 'warn':
        console.warn(prefix, message, data);
        break;
      case 'error':
      case 'fatal':
        console.error(prefix, message, data);
        break;
      default:
        console.log(prefix, message, data);
    }
  }

  return {
    trace(obj: any, msg?: string) {
      formatMessage('trace', obj, msg);
    },
    debug(obj: any, msg?: string) {
      formatMessage('debug', obj, msg);
    },
    info(obj: any, msg?: string) {
      formatMessage('info', obj, msg);
    },
    warn(obj: any, msg?: string) {
      formatMessage('warn', obj, msg);
    },
    error(obj: any, msg?: string) {
      formatMessage('error', obj, msg);
    },
    fatal(obj: any, msg?: string) {
      formatMessage('fatal', obj, msg);
    },
    child(childBindings: object): Logger {
      return createConsoleLogger(name, { ...bindings, ...childBindings });
    },
  };
}

/**
 * Get a configured logger instance
 *
 * @param name - Optional logger name (typically module name)
 * @returns A configured logger instance
 *
 * @example
 * ```typescript
 * const logger = getLogger('my-component');
 * logger.info({ userId: 123 }, 'User logged in');
 * ```
 */
export function getLogger(name?: string): Logger {
  return createConsoleLogger(name);
}

/**
 * Configure and get a logger instance
 * @deprecated Use getLogger instead
 */
export const configureLogging = getLogger;

// Browser-specific: timingMiddleware not supported (returns no-op)
export function timingMiddleware() {
  return (_req: any, _res: any, next: any) => next();
}
