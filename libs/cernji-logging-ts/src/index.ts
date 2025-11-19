/**
 * Cernji Logging - Standardized structured logging for Cernji Agents
 */

import pino, { type Logger, type LoggerOptions, type DestinationStream } from 'pino';
import { ecsFormat } from '@elastic/ecs-pino-format';
import { getConfig } from './config.js';
import { correlationIdMixin } from './context.js';
import { createWriteStream } from 'fs';
import { mkdirSync } from 'fs';
import { dirname } from 'path';

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

  // Create destination stream for file logging (avoiding pino transports which break in Next.js)
  let destination: DestinationStream | undefined;

  if (config.filePath) {
    try {
      // Create directory if it doesn't exist
      const dir = dirname(config.filePath);
      mkdirSync(dir, { recursive: true });

      // Create write stream to file
      destination = createWriteStream(config.filePath, { flags: 'a' });
    } catch (error) {
      console.error(`Failed to create log file at ${config.filePath}:`, error);
      // Fall back to stdout
      destination = undefined;
    }
  }

  // Create logger with custom destination stream or stdout
  const logger = destination ? pino(pinoOptions, destination) : pino(pinoOptions);

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
