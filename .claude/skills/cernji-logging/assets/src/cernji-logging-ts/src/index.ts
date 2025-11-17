/**
 * Cernji Logging - Standardized structured logging for Cernji Agents
 */

import pino, { type Logger, type LoggerOptions } from 'pino';
import { ecsFormat } from '@elastic/ecs-pino-format';
import { getConfig, type LogConfig } from './config.js';
import { correlationIdMixin } from './context.js';

export { getCorrelationId, withCorrelationId, generateCorrelationId } from './context.js';
export { Timed, TimingContext, timingMiddleware } from './timing.js';
export type { LogConfig, LogLevel, LogFormat, Environment } from './config.js';
export type { Logger };

/**
 * Get a configured Pino logger instance
 *
 * @param name - Optional logger name (typically module name)
 * @param options - Optional Pino logger options to override defaults
 * @returns A configured Pino logger
 *
 * @example
 * ```typescript
 * const logger = getLogger('my-service');
 * logger.info({ userId: 123 }, 'User logged in');
 * ```
 */
export function getLogger(name?: string, options?: LoggerOptions): Logger {
  const config = getConfig();

  const ecsOptions = ecsFormat({
    serviceName: config.serviceName,
    serviceVersion: config.serviceVersion,
    serviceEnvironment: config.environment,
  });

  const pinoOptions: LoggerOptions = {
    ...ecsOptions,
    level: config.level,
    mixin: correlationIdMixin,
    ...options,
  };

  // Use pretty printer for development
  if (config.format === 'pretty' || config.environment === 'dev') {
    pinoOptions.transport = {
      target: 'pino-pretty',
      options: {
        colorize: true,
        translateTime: 'yyyy-mm-dd HH:MM:ss',
        ignore: 'pid,hostname',
      },
    };
  }

  // Log to file if configured
  if (config.filePath) {
    pinoOptions.transport = {
      target: 'pino/file',
      options: {
        destination: config.filePath,
        mkdir: true,
      },
    };
  }

  const logger = pino(pinoOptions);

  // Add name as child logger if provided
  if (name) {
    return logger.child({ name });
  }

  return logger;
}

/**
 * Configure and get a logger instance
 * @deprecated Use getLogger instead
 */
export const configureLogging = getLogger;
