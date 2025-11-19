/**
 * Cernji-Logging TypeScript Usage Example
 *
 * This file demonstrates how to use Cernji-Logging in a TypeScript application.
 * Copy relevant sections to your application.
 */

import {
  getLogger,
  withCorrelationId,
  setCorrelationId,
  getCorrelationId,
  generateCorrelationId,
  Timed,
  TimingContext,
  timingMiddleware,
} from '@cernji/logging';

// ============================================
// Basic Logger Setup
// ============================================

// Get a logger for your module
// The logger name appears in logs as 'event.module'
const logger = getLogger('my-service');


// ============================================
// Basic Logging Examples
// ============================================

function basicLoggingExample() {
  // Info level with structured data
  logger.info({ version: '1.0.0', config: 'loaded' }, 'Application started');

  // Debug level (only appears if LOG_LEVEL=debug)
  logger.debug({ variable: 'value' }, 'Detailed diagnostic info');

  // Warning level
  logger.warn({ condition: 'rate_limit' }, 'Unusual condition detected');

  // Error level with exception info
  try {
    throw new Error('Example error');
  } catch (error) {
    logger.error({ error }, 'Operation failed');
  }
}


// ============================================
// Correlation ID Examples
// ============================================

async function correlationIdExample() {
  // Generate a new correlation ID
  const correlationId = generateCorrelationId();

  // Use async wrapper (recommended)
  await withCorrelationId(correlationId, async () => {
    logger.info('Processing request');  // Will include trace.id
    await someAsyncOperation();
    logger.info('Request completed');   // Will include same trace.id
  });

  // Alternative: Set globally (use carefully in async code)
  setCorrelationId(correlationId);
  logger.info('This also has trace.id');

  // Get current correlation ID
  const currentId = getCorrelationId();
  logger.info({ trace_id: currentId }, 'Current correlation ID');
}


// ============================================
// Express/HTTP Server Examples
// ============================================

// Express middleware example
import express from 'express';

const app = express();

// Add timing middleware (measures request duration)
app.use(timingMiddleware(logger));

// Add correlation ID middleware
app.use(async (req, res, next) => {
  const correlationId = (req.headers['x-correlation-id'] as string) || generateCorrelationId();

  // Set response header for client
  res.setHeader('X-Correlation-ID', correlationId);

  await withCorrelationId(correlationId, async () => {
    next();
  });
});

// Example endpoint
app.post('/api/users', async (req, res) => {
  logger.info({ method: req.method, path: req.path }, 'HTTP request received');

  try {
    const result = await processRequest(req.body);
    logger.info({ status: 200 }, 'HTTP request completed');
    res.json(result);
  } catch (error) {
    logger.error({ error }, 'HTTP request failed');
    res.status(500).json({ error: 'Internal server error' });
  }
});


// ============================================
// Service-to-Service Communication
// ============================================

async function callExternalService() {
  // Get current correlation ID
  const correlationId = getCorrelationId();

  // Build headers with correlation ID
  const headers: Record<string, string> = {};
  if (correlationId) {
    headers['X-Correlation-ID'] = correlationId;
  }

  logger.info({ service: 'api.example.com' }, 'Calling external service');

  const response = await fetch('https://api.example.com/data', {
    headers,
  });

  logger.info({ status: response.status }, 'External service response');
  return response;
}


// ============================================
// Performance Timing Examples
// ============================================

class DatabaseService {
  private logger = getLogger('database-service');

  // Method decorator for automatic timing (default: info level)
  @Timed()
  async queryUsers() {
    await new Promise(resolve => setTimeout(resolve, 100)); // Simulate query
    return [{ id: 1, name: 'John' }];
  }

  // Method decorator with custom log level
  @Timed('debug')
  async internalOperation() {
    await new Promise(resolve => setTimeout(resolve, 50));
    return 'result';
  }

  // Manual timing using TimingContext
  async complexQuery() {
    const timer = new TimingContext(this.logger, 'complex_query');

    try {
      // Simulate complex query
      await new Promise(resolve => setTimeout(resolve, 200));
      return 'result';
    } finally {
      timer.end(); // Logs duration
    }
  }
}


// ============================================
// Class-Based Service Example
// ============================================

class UserService {
  private logger = getLogger('user-service');

  @Timed()
  async createUser(userData: { email: string; name: string }) {
    const correlationId = generateCorrelationId();

    await withCorrelationId(correlationId, async () => {
      this.logger.info({ email: userData.email }, 'Creating user');

      try {
        // Simulate user creation
        await new Promise(resolve => setTimeout(resolve, 100));
        const userId = 'user_123';

        this.logger.info(
          { user_id: userId, email: userData.email },
          'User created successfully'
        );

        return userId;
      } catch (error) {
        this.logger.error(
          { error, email: userData.email },
          'User creation failed'
        );
        throw error;
      }
    });
  }

  async getUser(userId: string) {
    const timer = new TimingContext(this.logger, 'get_user');

    try {
      this.logger.debug({ user_id: userId }, 'Fetching user');

      // Simulate database query
      await new Promise(resolve => setTimeout(resolve, 50));

      return { id: userId, name: 'John Doe' };
    } finally {
      timer.end();
    }
  }
}


// ============================================
// Migration Example
// ============================================

function migrationBefore() {
  /** OLD CODE: Using console.log */
  const userId = 'user_123';
  console.log(`[UserService] Processing user ${userId}`);
  console.log(`[UserService] User ${userId} processed successfully`);
}

function migrationAfter() {
  /** NEW CODE: Using Cernji-Logging */
  const logger = getLogger('user-service');
  const userId = 'user_123';
  logger.info({ user_id: userId }, 'Processing user');
  logger.info({ user_id: userId }, 'User processed successfully');
}


// ============================================
// Complete Application Example
// ============================================

async function main() {
  // 1. Basic logging
  logger.info({ version: '1.0.0' }, 'Application starting');

  // 2. Generate correlation ID for this session
  const sessionId = generateCorrelationId();

  await withCorrelationId(sessionId, async () => {
    // 3. Use service with timing decorators
    const dbService = new DatabaseService();
    const users = await dbService.queryUsers();

    // 4. Use user service
    const userService = new UserService();
    const userId = await userService.createUser({
      email: 'user@example.com',
      name: 'John Doe',
    });

    // 5. Call external service (propagates correlation ID)
    // await callExternalService();

    logger.info({ user_id: userId }, 'Application session complete');
  });
}


// ============================================
// Fastify Server Example
// ============================================

import Fastify from 'fastify';

const fastify = Fastify();

// Correlation ID hook
fastify.addHook('onRequest', async (request, reply) => {
  const correlationId = (request.headers['x-correlation-id'] as string) || generateCorrelationId();

  reply.header('X-Correlation-ID', correlationId);

  // Store for use in handlers
  (request as any).correlationId = correlationId;
});

// Example route
fastify.post('/api/users', async (request, reply) => {
  const correlationId = (request as any).correlationId;

  await withCorrelationId(correlationId, async () => {
    logger.info(
      { method: request.method, url: request.url },
      'HTTP request received'
    );

    try {
      const result = await processRequest(request.body);
      logger.info({ status: 200 }, 'HTTP request completed');
      return result;
    } catch (error) {
      logger.error({ error }, 'HTTP request failed');
      reply.status(500).send({ error: 'Internal server error' });
    }
  });
});


// ============================================
// Helper Functions
// ============================================

async function someAsyncOperation() {
  await new Promise(resolve => setTimeout(resolve, 10));
}

async function processRequest(data: any) {
  await new Promise(resolve => setTimeout(resolve, 50));
  return { status: 'success' };
}


// ============================================
// Export examples for import
// ============================================

export {
  basicLoggingExample,
  correlationIdExample,
  callExternalService,
  DatabaseService,
  UserService,
  main,
};


// Run main if executed directly
if (require.main === module) {
  main().catch((error) => {
    logger.error({ error }, 'Application error');
    process.exit(1);
  });
}
