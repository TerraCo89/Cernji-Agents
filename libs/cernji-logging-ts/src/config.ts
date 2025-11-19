/**
 * Configuration management for Cernji Logging
 */

export type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';
export type LogFormat = 'json' | 'pretty';
export type Environment = 'dev' | 'development' | 'staging' | 'production' | 'prod';

export interface LogConfig {
  level: LogLevel;
  format: LogFormat;
  filePath: string | undefined;
  serviceName: string;
  serviceVersion: string | undefined;
  environment: Environment;
}

export function getConfig(): LogConfig {
  return {
    level: (process.env.LOG_LEVEL?.toLowerCase() || 'info') as LogLevel,
    format: (process.env.LOG_FORMAT?.toLowerCase() || 'json') as LogFormat,
    filePath: process.env.LOG_FILE,
    serviceName: process.env.SERVICE_NAME || 'unknown-service',
    serviceVersion: process.env.SERVICE_VERSION,
    environment: (process.env.ENVIRONMENT?.toLowerCase() || 'dev') as Environment,
  };
}
