/**
 * Adapted from Disler's Multi-Agent Observability reference implementation
 * Source: https://github.com/disler/claude-code-hooks-multi-agent-observability
 */
import { initDatabase, insertEvent, getFilterOptions, getRecentEvents, updateEventHITLResponse } from './db';
import type { HookEvent, HumanInTheLoopResponse } from './types';
import { 
  createTheme, 
  updateThemeById, 
  getThemeById, 
  searchThemes, 
  deleteThemeById, 
  exportThemeById, 
  importTheme,
  getThemeStats 
} from './theme';

// Initialize database
initDatabase();

// Store WebSocket clients
const wsClients = new Set<any>();

// Alert throttling: Track recent alerts to prevent spam
const recentAlerts = new Map<string, number>(); // key: service_name, value: last_trigger_timestamp
const THROTTLE_WINDOW_MS = 5 * 60 * 1000; // 5 minutes

// Polling configuration
const ELASTICSEARCH_URL = process.env.ELASTICSEARCH_URL || 'http://localhost:9200';
const POLLING_INTERVAL_MS = parseInt(process.env.POLLING_INTERVAL_MS || '60000'); // 1 minute default
const ERROR_THRESHOLD = parseInt(process.env.ERROR_THRESHOLD || '10'); // Trigger if > 10 errors
const POLLING_TIME_WINDOW = process.env.POLLING_TIME_WINDOW || '5m'; // Look back 5 minutes

// Services to monitor (can be configured via env var)
const MONITORED_SERVICES = (process.env.MONITORED_SERVICES || 'resume-agent,agent-chat-ui,japanese-tutor').split(',');

// Function to trigger error analysis
async function triggerErrorAnalysis(alert: any, eventId: number): Promise<void> {
  const service = alert.service || 'unknown';
  const now = Date.now();

  // Check if we've recently triggered analysis for this service
  const lastTrigger = recentAlerts.get(service);
  if (lastTrigger && (now - lastTrigger) < THROTTLE_WINDOW_MS) {
    console.log(`[Error Analysis] Throttled analysis for ${service} (triggered ${Math.round((now - lastTrigger) / 1000)}s ago)`);
    return;
  }

  // Update throttle tracking
  recentAlerts.set(service, now);

  // Prepare alert data for analysis script
  const alertData = {
    alert_id: alert.alert_id || `alert-${eventId}`,
    alert_name: alert.alert_name,
    service: service,
    error_count: alert.error_count || 0,
    severity: alert.severity || 'unknown',
    timestamp: alert.timestamp || new Date().toISOString(),
    time_range: alert.time_range || '15m',
    query_context: alert.query_context
  };

  try {
    // Call the Python analysis script
    // Get the project root (two levels up from src/)
    const projectRoot = new URL('../../..', import.meta.url).pathname.slice(1); // Remove leading slash on Windows
    const scriptPath = `${projectRoot}/apps/observability-server/scripts/trigger_error_analysis.py`;

    const proc = Bun.spawn([
      'uv',
      'run',
      scriptPath,
      '--alert-json',
      JSON.stringify(alertData),
      '--output',
      'json'
    ], {
      cwd: projectRoot,
      stdout: 'pipe',
      stderr: 'pipe'
    });

    // Read output
    const output = await new Response(proc.stdout).text();
    const errorOutput = await new Response(proc.stderr).text();

    const exitCode = await proc.exited;

    if (exitCode === 0) {
      try {
        const result = JSON.parse(output);
        console.log(`[Error Analysis] Analysis complete for ${service}:`, {
          total_errors: result.analysis?.total_errors,
          patterns: result.analysis?.patterns?.length,
          root_cause: result.analysis?.root_cause
        });

        // Phase 3: Log Linear issue if created automatically
        if (result.linear_issue) {
          console.log(`[Error Analysis] ✓ Linear issue created automatically:`, {
            identifier: result.linear_issue.identifier,
            url: result.linear_issue_url
          });
        } else if (result.linear_issue_data) {
          // Fallback: Phase 2 behavior (manual creation)
          console.log(`[Error Analysis] Linear issue data ready (LINEAR_API_KEY not set):`, {
            title: result.linear_issue_data.title,
            labels: result.linear_issue_data.labels
          });
        }

        // Log actions taken
        if (result.actions_taken && result.actions_taken.length > 0) {
          console.log(`[Error Analysis] Actions taken:`, result.actions_taken);
        }
      } catch (parseError) {
        console.error('[Error Analysis] Error parsing analysis result:', parseError);
      }
    } else {
      console.error(`[Error Analysis] Analysis script failed with exit code ${exitCode}`);
      if (errorOutput) {
        console.error('[Error Analysis] Error output:', errorOutput);
      }
    }
  } catch (error) {
    console.error('[Error Analysis] Error spawning analysis script:', error);
  }
}

// Polling service to check Elasticsearch for high error rates
async function checkErrorRates(): Promise<void> {
  for (const service of MONITORED_SERVICES) {
    try {
      // Query Elasticsearch for error count in the last time window
      const response = await fetch(`${ELASTICSEARCH_URL}/logs-${service}-*/_count`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: {
            bool: {
              must: [
                {
                  range: {
                    '@timestamp': {
                      gte: `now-${POLLING_TIME_WINDOW}`,
                      lte: 'now'
                    }
                  }
                },
                { term: { 'log.level': 'error' } },
                { term: { 'service.name': service } }
              ]
            }
          }
        })
      });

      if (!response.ok) {
        console.error(`[Polling] Error querying ${service}:`, response.statusText);
        continue;
      }

      const result = await response.json();
      const errorCount = result.count || 0;

      // Check if error count exceeds threshold
      if (errorCount > ERROR_THRESHOLD) {
        console.log(`[Polling] High error rate detected for ${service}: ${errorCount} errors in ${POLLING_TIME_WINDOW}`);

        // Create alert data and trigger analysis
        const alertData = {
          alert_id: `polling-${service}-${Date.now()}`,
          alert_name: `High Error Rate Detected (Polling)`,
          service: service,
          error_count: errorCount,
          severity: 'high',
          timestamp: new Date().toISOString(),
          time_range: POLLING_TIME_WINDOW,
          source: 'polling'
        };

        // Store alert as event
        const event: HookEvent = {
          source_app: 'polling-service',
          session_id: alertData.alert_id,
          hook_event_type: 'PollingAlert',
          payload: alertData
        };

        const savedEvent = insertEvent(event);

        // Broadcast to WebSocket clients
        const message = JSON.stringify({
          type: 'polling_alert',
          data: savedEvent
        });
        wsClients.forEach(client => {
          try {
            client.send(message);
          } catch (err) {
            wsClients.delete(client);
          }
        });

        // Trigger error analysis
        triggerErrorAnalysis(alertData, savedEvent.id).catch(err => {
          console.error('[Polling] Error triggering analysis:', err);
        });
      } else {
        console.log(`[Polling] ${service}: ${errorCount} errors (threshold: ${ERROR_THRESHOLD}) - OK`);
      }

    } catch (error) {
      console.error(`[Polling] Error checking ${service}:`, error);
    }
  }
}

// Start polling service
let pollingInterval: Timer;
function startPollingService(): void {
  console.log(`[Polling] Starting error monitoring service`);
  console.log(`[Polling] Interval: ${POLLING_INTERVAL_MS}ms (${POLLING_INTERVAL_MS / 1000}s)`);
  console.log(`[Polling] Time window: ${POLLING_TIME_WINDOW}`);
  console.log(`[Polling] Error threshold: ${ERROR_THRESHOLD}`);
  console.log(`[Polling] Monitored services: ${MONITORED_SERVICES.join(', ')}`);

  // Run first check immediately
  checkErrorRates();

  // Then poll at regular intervals
  pollingInterval = setInterval(checkErrorRates, POLLING_INTERVAL_MS);
}

// Stop polling service
function stopPollingService(): void {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    console.log('[Polling] Stopped error monitoring service');
  }
}

// Helper function to send response to agent via WebSocket
async function sendResponseToAgent(
  wsUrl: string,
  response: HumanInTheLoopResponse
): Promise<void> {
  console.log(`[HITL] Connecting to agent WebSocket: ${wsUrl}`);

  return new Promise((resolve, reject) => {
    let ws: WebSocket | null = null;
    let isResolved = false;

    const cleanup = () => {
      if (ws) {
        try {
          ws.close();
        } catch (e) {
          // Ignore close errors
        }
      }
    };

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (isResolved) return;
        console.log('[HITL] WebSocket connection opened, sending response...');

        try {
          ws!.send(JSON.stringify(response));
          console.log('[HITL] Response sent successfully');

          // Wait longer to ensure message fully transmits before closing
          setTimeout(() => {
            cleanup();
            if (!isResolved) {
              isResolved = true;
              resolve();
            }
          }, 500);
        } catch (error) {
          console.error('[HITL] Error sending message:', error);
          cleanup();
          if (!isResolved) {
            isResolved = true;
            reject(error);
          }
        }
      };

      ws.onerror = (error) => {
        console.error('[HITL] WebSocket error:', error);
        cleanup();
        if (!isResolved) {
          isResolved = true;
          reject(error);
        }
      };

      ws.onclose = () => {
        console.log('[HITL] WebSocket connection closed');
      };

      // Timeout after 5 seconds
      setTimeout(() => {
        if (!isResolved) {
          console.error('[HITL] Timeout sending response to agent');
          cleanup();
          isResolved = true;
          reject(new Error('Timeout sending response to agent'));
        }
      }, 5000);

    } catch (error) {
      console.error('[HITL] Error creating WebSocket:', error);
      cleanup();
      if (!isResolved) {
        isResolved = true;
        reject(error);
      }
    }
  });
}

// Create Bun server with HTTP and WebSocket support
const server = Bun.serve({
  port: 4000,
  
  async fetch(req: Request) {
    const url = new URL(req.url);
    
    // Handle CORS
    const headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };
    
    // Handle preflight
    if (req.method === 'OPTIONS') {
      return new Response(null, { headers });
    }
    
    // POST /events - Receive new events
    if (url.pathname === '/events' && req.method === 'POST') {
      try {
        const event: HookEvent = await req.json();
        
        // Validate required fields
        if (!event.source_app || !event.session_id || !event.hook_event_type || !event.payload) {
          return new Response(JSON.stringify({ error: 'Missing required fields' }), {
            status: 400,
            headers: { ...headers, 'Content-Type': 'application/json' }
          });
        }
        
        // Insert event into database
        const savedEvent = insertEvent(event);
        
        // Broadcast to all WebSocket clients
        const message = JSON.stringify({ type: 'event', data: savedEvent });
        wsClients.forEach(client => {
          try {
            client.send(message);
          } catch (err) {
            // Client disconnected, remove from set
            wsClients.delete(client);
          }
        });
        
        return new Response(JSON.stringify(savedEvent), {
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error processing event:', error);
        return new Response(JSON.stringify({ error: 'Invalid request' }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }
    
    // GET /events/filter-options - Get available filter options
    if (url.pathname === '/events/filter-options' && req.method === 'GET') {
      const options = getFilterOptions();
      return new Response(JSON.stringify(options), {
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }
    
    // GET /events/recent - Get recent events
    if (url.pathname === '/events/recent' && req.method === 'GET') {
      const limit = parseInt(url.searchParams.get('limit') || '100');
      const events = getRecentEvents(limit);
      return new Response(JSON.stringify(events), {
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }

    // POST /events/:id/respond - Respond to HITL request
    if (url.pathname.match(/^\/events\/\d+\/respond$/) && req.method === 'POST') {
      const id = parseInt(url.pathname.split('/')[2]);

      try {
        const response: HumanInTheLoopResponse = await req.json();
        response.respondedAt = Date.now();

        // Update event in database
        const updatedEvent = updateEventHITLResponse(id, response);

        if (!updatedEvent) {
          return new Response(JSON.stringify({ error: 'Event not found' }), {
            status: 404,
            headers: { ...headers, 'Content-Type': 'application/json' }
          });
        }

        // Send response to agent via WebSocket
        if (updatedEvent.humanInTheLoop?.responseWebSocketUrl) {
          try {
            await sendResponseToAgent(
              updatedEvent.humanInTheLoop.responseWebSocketUrl,
              response
            );
          } catch (error) {
            console.error('Failed to send response to agent:', error);
            // Don't fail the request if we can't reach the agent
          }
        }

        // Broadcast updated event to all connected clients
        const message = JSON.stringify({ type: 'event', data: updatedEvent });
        wsClients.forEach(client => {
          try {
            client.send(message);
          } catch (err) {
            wsClients.delete(client);
          }
        });

        return new Response(JSON.stringify(updatedEvent), {
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error processing HITL response:', error);
        return new Response(JSON.stringify({ error: 'Invalid request' }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }

    // POST /alerts/trigger - Receive webhooks from Kibana alerting
    if (url.pathname === '/alerts/trigger' && req.method === 'POST') {
      try {
        const alert = await req.json();

        console.log('[Kibana Alert] Received alert:', alert.alert_name || 'unnamed');

        // Store alert as an event
        const event: HookEvent = {
          source_app: 'kibana',
          session_id: alert.correlation_id || alert.alert_id || `alert-${Date.now()}`,
          hook_event_type: 'KibanaAlert',
          payload: {
            alert_id: alert.alert_id,
            alert_name: alert.alert_name,
            service: alert.service,
            error_count: alert.error_count,
            severity: alert.severity || 'unknown',
            timestamp: alert.timestamp,
            query_context: alert.query_context,
            ...alert
          }
        };

        const savedEvent = insertEvent(event);

        // Broadcast to WebSocket clients
        const message = JSON.stringify({
          type: 'alert',
          data: savedEvent
        });
        wsClients.forEach(client => {
          try {
            client.send(message);
          } catch (err) {
            wsClients.delete(client);
          }
        });

        // Trigger error analysis agent for high-severity alerts
        const shouldTriggerAnalysis =
          alert.severity === 'high' ||
          alert.error_count > 10 ||
          alert.alert_name?.includes('Critical');

        if (shouldTriggerAnalysis) {
          console.log(`[Kibana Alert] Triggering error analysis for alert: ${alert.alert_name}`);

          // Trigger analysis asynchronously (don't block response)
          triggerErrorAnalysis(alert, savedEvent.id).catch(err => {
            console.error('[Kibana Alert] Error triggering analysis:', err);
          });
        } else {
          console.log(`[Kibana Alert] Alert stored with ID: ${savedEvent.id} (analysis not triggered)`);
        }

        return new Response(JSON.stringify({
          success: true,
          event_id: savedEvent.id,
          message: 'Alert received and stored'
        }), {
          status: 200,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('[Kibana Alert] Error processing alert:', error);
        return new Response(JSON.stringify({
          success: false,
          error: 'Failed to process alert'
        }), {
          status: 500,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }

    // Theme API endpoints
    
    // POST /api/themes - Create a new theme
    if (url.pathname === '/api/themes' && req.method === 'POST') {
      try {
        const themeData = await req.json();
        const result = await createTheme(themeData);
        
        const status = result.success ? 201 : 400;
        return new Response(JSON.stringify(result), {
          status,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error creating theme:', error);
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Invalid request body' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }
    
    // GET /api/themes - Search themes
    if (url.pathname === '/api/themes' && req.method === 'GET') {
      const query = {
        query: url.searchParams.get('query') || undefined,
        isPublic: url.searchParams.get('isPublic') ? url.searchParams.get('isPublic') === 'true' : undefined,
        authorId: url.searchParams.get('authorId') || undefined,
        sortBy: url.searchParams.get('sortBy') as any || undefined,
        sortOrder: url.searchParams.get('sortOrder') as any || undefined,
        limit: url.searchParams.get('limit') ? parseInt(url.searchParams.get('limit')!) : undefined,
        offset: url.searchParams.get('offset') ? parseInt(url.searchParams.get('offset')!) : undefined,
      };
      
      const result = await searchThemes(query);
      return new Response(JSON.stringify(result), {
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }
    
    // GET /api/themes/:id - Get a specific theme
    if (url.pathname.startsWith('/api/themes/') && req.method === 'GET') {
      const id = url.pathname.split('/')[3];
      if (!id) {
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Theme ID is required' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
      
      const result = await getThemeById(id);
      const status = result.success ? 200 : 404;
      return new Response(JSON.stringify(result), {
        status,
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }
    
    // PUT /api/themes/:id - Update a theme
    if (url.pathname.startsWith('/api/themes/') && req.method === 'PUT') {
      const id = url.pathname.split('/')[3];
      if (!id) {
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Theme ID is required' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
      
      try {
        const updates = await req.json();
        const result = await updateThemeById(id, updates);
        
        const status = result.success ? 200 : 400;
        return new Response(JSON.stringify(result), {
          status,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error updating theme:', error);
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Invalid request body' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }
    
    // DELETE /api/themes/:id - Delete a theme
    if (url.pathname.startsWith('/api/themes/') && req.method === 'DELETE') {
      const id = url.pathname.split('/')[3];
      if (!id) {
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Theme ID is required' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
      
      const authorId = url.searchParams.get('authorId');
      const result = await deleteThemeById(id, authorId || undefined);
      
      const status = result.success ? 200 : (result.error?.includes('not found') ? 404 : 403);
      return new Response(JSON.stringify(result), {
        status,
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }
    
    // GET /api/themes/:id/export - Export a theme
    if (url.pathname.match(/^\/api\/themes\/[^\/]+\/export$/) && req.method === 'GET') {
      const id = url.pathname.split('/')[3];
      
      const result = await exportThemeById(id);
      if (!result.success) {
        const status = result.error?.includes('not found') ? 404 : 400;
        return new Response(JSON.stringify(result), {
          status,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
      
      return new Response(JSON.stringify(result.data), {
        headers: { 
          ...headers, 
          'Content-Type': 'application/json',
          'Content-Disposition': `attachment; filename="${result.data.theme.name}.json"`
        }
      });
    }
    
    // POST /api/themes/import - Import a theme
    if (url.pathname === '/api/themes/import' && req.method === 'POST') {
      try {
        const importData = await req.json();
        const authorId = url.searchParams.get('authorId');
        
        const result = await importTheme(importData, authorId || undefined);
        
        const status = result.success ? 201 : 400;
        return new Response(JSON.stringify(result), {
          status,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      } catch (error) {
        console.error('Error importing theme:', error);
        return new Response(JSON.stringify({ 
          success: false, 
          error: 'Invalid import data' 
        }), {
          status: 400,
          headers: { ...headers, 'Content-Type': 'application/json' }
        });
      }
    }
    
    // GET /api/themes/stats - Get theme statistics
    if (url.pathname === '/api/themes/stats' && req.method === 'GET') {
      const result = await getThemeStats();
      return new Response(JSON.stringify(result), {
        headers: { ...headers, 'Content-Type': 'application/json' }
      });
    }
    
    // WebSocket upgrade
    if (url.pathname === '/stream') {
      const success = server.upgrade(req);
      if (success) {
        return undefined;
      }
    }
    
    // Default response
    return new Response('Multi-Agent Observability Server', {
      headers: { ...headers, 'Content-Type': 'text/plain' }
    });
  },
  
  websocket: {
    open(ws) {
      console.log('WebSocket client connected');
      wsClients.add(ws);
      
      // Send recent events on connection
      const events = getRecentEvents(50);
      ws.send(JSON.stringify({ type: 'initial', data: events }));
    },
    
    message(ws, message) {
      // Handle any client messages if needed
      console.log('Received message:', message);
    },
    
    close(ws) {
      console.log('WebSocket client disconnected');
      wsClients.delete(ws);
    },
    
    error(ws, error) {
      console.error('WebSocket error:', error);
      wsClients.delete(ws);
    }
  }
});

console.log(`🚀 Server running on http://localhost:${server.port}`);
console.log(`📊 WebSocket endpoint: ws://localhost:${server.port}/stream`);
console.log(`📮 POST events to: http://localhost:${server.port}/events`);
console.log('');

// Start the polling service for automatic error detection
startPollingService();

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\nShutting down...');
  stopPollingService();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\nShutting down...');
  stopPollingService();
  process.exit(0);
});