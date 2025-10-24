# Research Topic Decomposition Patterns

This document provides detailed examples of how to decompose different types of programming research topics into specific investigation avenues.

## Pattern 1: Error Message Investigation

**Goal:** Understand the root cause of an error and find solutions.

### Example 1: "TypeError: Cannot read property 'map' of undefined"

**Decomposition Strategy:** Start with immediate causes, then expand to related issues and alternatives.

**Research Avenues (6):**

1. **Root Cause Analysis**
   - What conditions cause `undefined` to be passed to `.map()`?
   - Common async/timing issues leading to this error
   - React/Vue component lifecycle issues

2. **Debugging Techniques**
   - How to trace where `undefined` originates
   - Browser DevTools strategies
   - Adding defensive checks and validation

3. **Known Framework Issues**
   - React: data not yet loaded from API
   - Vue: reactive data initialization
   - Next.js: SSR vs client rendering

4. **Preventive Patterns**
   - Optional chaining (`?.`)
   - Default values and fallbacks
   - TypeScript for type safety

5. **Testing Approaches**
   - Unit tests to catch undefined data
   - Integration tests for data flow
   - Mocking strategies

6. **Alternative Data Handling**
   - Loading states
   - Error boundaries
   - Suspense patterns

### Example 2: "ModuleNotFoundError: No module named 'X'"

**Decomposition Strategy:** Installation, environment, and configuration issues.

**Research Avenues (5):**

1. **Installation Issues**
   - Package not installed in active environment
   - Pip vs conda conflicts
   - Requirements.txt problems

2. **Python Environment Problems**
   - Virtual environment not activated
   - Wrong Python interpreter
   - PATH configuration

3. **Import Path Issues**
   - Module location and PYTHONPATH
   - Relative vs absolute imports
   - Package structure problems

4. **Version Conflicts**
   - Python version incompatibility
   - Dependency version conflicts
   - Breaking changes in library

5. **IDE Configuration**
   - VSCode Python interpreter selection
   - PyCharm project structure
   - Linter configuration

## Pattern 2: Library/Tool Comparison

**Goal:** Compare multiple options to help user choose the best tool for their needs.

### Example 1: "Compare state management libraries for React"

**Decomposition Strategy:** Cover major options + evaluation criteria.

**Research Avenues (8):**

1. **Redux Approach**
   - Core concepts and boilerplate
   - Redux Toolkit modern approach
   - Ecosystem (DevTools, middleware)
   - Production examples

2. **Zustand Approach**
   - Minimal API and simplicity
   - Performance characteristics
   - TypeScript integration
   - Use cases

3. **Jotai Approach**
   - Atomic state model
   - React Suspense integration
   - Bottom-up architecture

4. **MobX Approach**
   - Observable patterns
   - Object-oriented state
   - Automatic reactivity

5. **Context API + Hooks**
   - Built-in React solution
   - Performance considerations
   - When it's sufficient

6. **Performance Benchmarks**
   - Bundle size comparison
   - Re-render optimization
   - Memory usage

7. **Developer Experience**
   - Learning curve
   - Debugging tools
   - TypeScript support

8. **Production Readiness**
   - Community size
   - Maintenance status
   - Migration stories

### Example 2: "Compare Python web frameworks"

**Decomposition Strategy:** Major frameworks + specialized considerations.

**Research Avenues (7):**

1. **Flask (Micro-framework)**
   - Minimal setup
   - Extension ecosystem
   - Best for small-medium projects

2. **FastAPI (Modern, async)**
   - Type hints and validation
   - Automatic API docs
   - Performance benchmarks

3. **Django (Full-featured)**
   - Batteries included
   - ORM and admin panel
   - Best for complex apps

4. **Pyramid (Flexible)**
   - Configuration flexibility
   - Scaling capabilities

5. **Performance Comparison**
   - Request throughput
   - Async support
   - Benchmarks

6. **Ecosystem and Deployment**
   - Available libraries
   - Hosting options
   - Containerization

7. **Learning Resources**
   - Documentation quality
   - Tutorial availability
   - Community support

## Pattern 3: Implementation Best Practices

**Goal:** Find recommended patterns and anti-patterns for specific tasks.

### Example 1: "Best practices for API authentication"

**Decomposition Strategy:** Different auth methods + cross-cutting concerns.

**Research Avenues (8):**

1. **JWT Token Approach**
   - Token structure
   - Refresh token patterns
   - Security considerations

2. **OAuth 2.0 Integration**
   - Authorization flows
   - Provider integration (Google, GitHub)
   - Token management

3. **API Key Authentication**
   - Key generation and rotation
   - Rate limiting by key
   - When to use

4. **Session-Based Auth**
   - Cookie management
   - Server-side sessions
   - Stateful vs stateless

5. **Security Best Practices**
   - HTTPS requirements
   - Token storage (localStorage vs cookies)
   - XSS and CSRF protection

6. **Multi-Factor Authentication**
   - TOTP implementation
   - SMS/email codes
   - Backup codes

7. **Rate Limiting and Throttling**
   - Per-user limits
   - IP-based limits
   - Distributed systems

8. **Error Handling**
   - 401 vs 403 responses
   - Token expiration handling
   - Graceful degradation

### Example 2: "Database connection pooling best practices"

**Decomposition Strategy:** Different databases + configuration patterns.

**Research Avenues (6):**

1. **PostgreSQL Connection Pooling**
   - PgBouncer setup
   - Connection pool sizing
   - Production configuration

2. **MySQL/MariaDB Pooling**
   - Built-in pooling
   - ProxySQL
   - Configuration tuning

3. **MongoDB Connection Management**
   - Driver-level pooling
   - Connection limits
   - Replica sets

4. **Application-Level Pooling**
   - Language-specific libraries (Python, Node.js, Java)
   - Pool size calculation
   - Health checks

5. **Monitoring and Troubleshooting**
   - Connection leak detection
   - Pool exhaustion debugging
   - Metrics to track

6. **Cloud Database Pooling**
   - AWS RDS Proxy
   - Azure Database connection limits
   - GCP Cloud SQL

## Pattern 4: GitHub Code Examples

**Goal:** Find real-world working examples of specific technologies or patterns.

### Example 1: "Find examples of WebSocket implementation in Go"

**Decomposition Strategy:** Different libraries + use cases.

**Research Avenues (5):**

1. **gorilla/websocket Examples**
   - Chat application patterns
   - Production repositories
   - Best practices

2. **nhooyr.io/websocket Examples**
   - Modern API usage
   - Performance optimizations
   - Real-time features

3. **Broadcasting Patterns**
   - Pub/sub implementations
   - Redis integration
   - Horizontal scaling

4. **Authentication and Security**
   - Token-based auth over WebSocket
   - Origin validation
   - Rate limiting

5. **Testing WebSocket Connections**
   - Unit test patterns
   - Integration testing
   - Load testing

### Example 2: "Find microservices architecture examples in Python"

**Decomposition Strategy:** Different frameworks + architectural patterns.

**Research Avenues (7):**

1. **FastAPI Microservices**
   - Service-to-service communication
   - API gateway patterns
   - Production examples

2. **Flask Microservices**
   - Service organization
   - Inter-service auth
   - Repository examples

3. **gRPC Implementation**
   - Protocol buffer definitions
   - Python gRPC services
   - Production repositories

4. **Message Queue Integration**
   - Celery task distribution
   - RabbitMQ patterns
   - Event-driven architecture

5. **Service Discovery**
   - Consul integration
   - Kubernetes service mesh
   - DNS-based discovery

6. **Monitoring and Logging**
   - Distributed tracing (Jaeger)
   - Centralized logging (ELK)
   - Prometheus metrics

7. **Deployment Patterns**
   - Docker Compose setups
   - Kubernetes manifests
   - CI/CD pipelines

## Pattern 5: Documentation Deep Dive

**Goal:** Thoroughly understand a specific library or framework feature.

### Example 1: "Research React Server Components"

**Decomposition Strategy:** Core concepts + practical implementation + ecosystem.

**Research Avenues (6):**

1. **Core Concepts**
   - Official documentation
   - Server vs Client components
   - Rendering model

2. **Practical Implementation**
   - Next.js App Router examples
   - Data fetching patterns
   - Component composition

3. **Migration Guide**
   - Moving from Client components
   - Gradual adoption strategies
   - Common pitfalls

4. **Performance Benefits**
   - Bundle size reduction
   - Streaming SSR
   - Benchmarks

5. **Limitations and Trade-offs**
   - Cannot use hooks
   - Context limitations
   - Browser API restrictions

6. **Community Examples**
   - Open source projects
   - Blog posts and tutorials
   - GitHub repositories

## Decomposition Guidelines

### Determine Number of Avenues

**3-5 avenues** for:
- Specific error with clear causes
- Comparing 2-3 well-defined options
- Focused implementation question

**5-8 avenues** for:
- Moderate complexity errors with multiple potential causes
- Comparing several libraries/frameworks
- Best practices with multiple approaches

**8-10 avenues** for:
- Complex architectural decisions
- Multi-faceted problems (security + performance + scalability)
- Comprehensive technology research

### Avenue Quality Checklist

Each avenue should be:
- **Specific**: Not "Authentication" but "JWT Token Approach"
- **Actionable**: Results in concrete code examples
- **Distinct**: No overlap with other avenues
- **Valuable**: Provides unique insights or solutions

### Balance Breadth and Depth

**Good balance:**
- 5 avenues investigating different solutions deeply
- Each provides working code + sources

**Too broad:**
- 10 avenues with surface-level information
- No working examples

**Too narrow:**
- 3 avenues all investigating slight variations of same approach
- Missing alternative solutions

## Quick Reference: Avenue Templates

### Error Investigation Avenue
```
Research [specific cause] for error: [error message]

Focus on:
- Root cause explanation
- Debugging steps
- Working fix with code
- Prevention strategies

Sources: Official docs, issue trackers, Stack Overflow
```

### Library Comparison Avenue
```
Research [Library Name] for [use case]

Focus on:
- Core features and API
- Working example
- Pros/cons vs alternatives
- Production readiness

Sources: Official docs, GitHub repos, production case studies
```

### Best Practice Avenue
```
Research [specific pattern] for [task]

Focus on:
- Recommended approach
- Working implementation
- Security/performance considerations
- Anti-patterns to avoid

Sources: Official docs, engineering blogs, open source examples
```

### GitHub Example Avenue
```
Find [technology] examples demonstrating [specific feature]

Focus on:
- Well-maintained repositories
- Production-quality code
- Recent commits (not abandoned)
- Stars and community adoption

Sources: GitHub search, Awesome lists, trending repos
```
