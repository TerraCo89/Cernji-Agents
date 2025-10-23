# Portfolio Finder - Example Search Output

This document shows example output from the portfolio-finder skill.

## Example 1: Backend Engineer Job Search

**Input:**
- Job: Senior Backend Engineer at Cookpad
- Required technologies: Python, PostgreSQL, AWS, Docker, Microservices, REST APIs
- Search across 47 repositories (filtered to 8 relevant private repos)

**Output:**

```
Code Portfolio Analysis
Job Target: Cookpad - Senior Backend Engineer

Executive Summary
Found 8 relevant repositories demonstrating 6 key technologies.
Strongest examples in: Python, PostgreSQL, Docker, AWS
Gaps to address: Microservices architecture (only prototype examples found)

Detailed Findings

Technology: Python
- Best Example: ddwl-platform - Enterprise logistics platform backend
  - Link: https://github.com/kcernjav/ddwl-platform (PRIVATE)
  - Why it's strong: Production system handling 10K+ daily shipments, comprehensive FastAPI implementation, 85% test coverage
  - Key files: backend/services/matching.py (RAG pipeline), backend/api/routes.py (REST endpoints)
- Additional Examples: career-assistant (FastAPI + MCP server), data-pipeline-tools (ETL scripts)

Technology: PostgreSQL
- Best Example: ddwl-platform - Complex schema with GIS extensions
  - Link: https://github.com/kcernjav/ddwl-platform (PRIVATE)
  - Why it's strong: Advanced SQL (CTEs, window functions), PostGIS for location queries, optimized indexes
  - Key files: backend/migrations/, backend/repositories/shipment_repository.py
- Additional Examples: career-assistant (SQLite with full-text search - transferable skills)

Technology: Docker
- Best Example: ddwl-platform - Multi-stage builds, docker-compose orchestration
  - Link: https://github.com/kcernjav/ddwl-platform (PRIVATE)
  - Why it's strong: Production Dockerfiles with security best practices, docker-compose for local dev + testing
  - Key files: backend/Dockerfile, docker-compose.yml, .github/workflows/docker.yml
- Additional Examples: career-assistant (single container), personal-blog (Nginx + Node)

Technology: AWS
- Best Example: ddwl-platform - Multi-service AWS deployment
  - Link: https://github.com/kcernjav/ddwl-platform (PRIVATE)
  - Why it's strong: ECS Fargate deployment, RDS PostgreSQL, S3 for file storage, CloudWatch monitoring
  - Key files: infrastructure/aws/, .github/workflows/deploy.yml
- Additional Examples: No other repos with AWS (note: used AWS at previous jobs but code is proprietary)

Technology: REST APIs
- Best Example: ddwl-platform - FastAPI with OpenAPI documentation
  - Link: https://github.com/kcernjav/ddwl-platform (PRIVATE)
  - Why it's strong: 20+ endpoints, Pydantic validation, versioned API (v1/v2), comprehensive error handling
  - Key files: backend/api/routes.py, backend/schemas/
- Additional Examples: career-assistant (MCP server - similar patterns), personal-blog (Express.js)

Technology: Microservices (Gap Identified)
- Prototype Example: microservices-demo - Learning project (2022)
  - Link: https://github.com/kcernjav/microservices-demo (PRIVATE)
  - Why it's limited: Only 2 services, not production-ready, no inter-service communication patterns
  - Key files: services/user-service/, services/order-service/
- Note: This is a skill gap for the Cookpad role. ddwl-platform is a modular monolith, not true microservices.

Strategic Recommendations

For Resume:
1. Lead with "ddwl-platform" project:
   - "Designed and implemented FastAPI backend serving 10,000+ daily shipments"
   - "Architected PostgreSQL schema with PostGIS extensions for location-based matching"
   - "Deployed to AWS ECS Fargate with RDS, S3, and CloudWatch integration"
   - Technologies: Python, FastAPI, PostgreSQL, PostGIS, Docker, AWS (ECS, RDS, S3)

2. Include "career-assistant" as second project:
   - "Built MCP server with FastAPI exposing AI-powered career tools to Claude Desktop"
   - "Implemented RAG pipeline with sentence-transformers and SQLite vector search"
   - Technologies: Python, FastAPI, SQLite, Docker, RAG, Claude AI SDK

3. Mention AWS experience from previous roles (even if code not available):
   - "Extensive AWS experience from previous roles (proprietary code)"

For Cover Letter:
Highlight the ddwl-platform RAG pipeline as your strongest proof point:
- Technical challenge: Matching shipments to carriers using semantic search
- Solution: Built RAG pipeline with embeddings + Redis cache
- Outcome: 40% reduction in matching latency, improved match quality
- Link: Request temporary repo access during interview process

This demonstrates:
- Backend architecture skills (exact match to Cookpad's needs)
- Production system experience (not just prototypes)
- Performance optimization mindset (latency reduction)

For Interview Preparation:
Top repos to be ready to discuss in depth:

1. ddwl-platform (PRIMARY EXAMPLE)
   - Architecture decisions: Why FastAPI over Django? (async performance)
   - Database design: PostGIS for geospatial queries, indexing strategy
   - AWS deployment: ECS Fargate vs EC2 trade-offs, RDS setup
   - Challenges: Scaling to 10K daily shipments, optimizing matching algorithm
   - Future improvements: What you'd do differently, scalability roadmap

2. career-assistant (SECONDARY EXAMPLE)
   - Demonstrates: Modern Python patterns, AI integration, MCP protocol
   - Interesting for: RAG implementation, vector search, agent orchestration
   - Trade-offs: SQLite vs PostgreSQL for vector search (sufficient for use case)

3. Prepare to discuss microservices gap honestly:
   - Acknowledge: Limited production microservices experience
   - Transferable skills: Modular architecture in ddwl-platform, API design, inter-service patterns
   - Learning plan: Willing to study Cookpad's architecture, read relevant books/courses

Repository Access
All examples are in private repositories. To share with interviewers:

Option 1: Temporary access (recommended)
- Add interviewer's GitHub username as collaborator
- Remove access after interview process

Option 2: Code samples
- Prepare sanitized code snippets (remove proprietary data)
- Create a public gist with key files
- Walk through during technical interview

Option 3: Make repository public (use caution)
- Only if no proprietary information
- Career-assistant is safe to make public (no client data)
- ddwl-platform contains business logic - keep private
```

---

## Example 2: Full-Stack Role with Frontend Focus

**Input:**
- Job: Full-Stack Engineer (React, TypeScript, Node.js)
- Technologies: React, TypeScript, Next.js, Node.js, PostgreSQL
- Search across 35 repositories (filtered to 6 relevant repos)

**Output:**

```
Code Portfolio Analysis
Job Target: Full-Stack Engineer Role

Executive Summary
Found 6 relevant repositories demonstrating 5 key technologies.
Strongest examples in: React, TypeScript, Next.js
Moderate examples in: Node.js, PostgreSQL
Gaps to address: None - all required technologies covered

Detailed Findings

Technology: React + TypeScript
- Best Example: client-dashboard - Real-time observability dashboard
  - Link: https://github.com/kcernjav/cernji-agents/tree/master/apps/client (PUBLIC)
  - Why it's strong: Vue 3 with Composition API (similar patterns to React hooks), TypeScript throughout, TailwindCSS
  - Key files: apps/client/src/components/EventTable.vue, apps/client/src/composables/
- Note: This is Vue, not React, but demonstrates modern frontend skills (component composition, reactive state, TypeScript)

Technology: Next.js
- Best Example: personal-website - Portfolio site with SSR
  - Link: https://github.com/kcernjav/personal-website (PRIVATE)
  - Why it's strong: Next.js 14, App Router, Server Components, API routes, Vercel deployment
  - Key files: app/page.tsx, app/api/contact/route.ts
- Additional Examples: blog-platform (Next.js 13 with MDX)

Technology: Node.js
- Best Example: observability-server - Event tracking backend
  - Link: https://github.com/kcernjav/cernji-agents/tree/master/apps/observability-server (PUBLIC)
  - Why it's strong: Bun runtime (Node.js compatible), WebSocket server, SQLite WAL mode, TypeScript
  - Key files: apps/observability-server/src/index.ts
- Additional Examples: blog-platform (Express.js API)

Technology: PostgreSQL
- Best Example: ddwl-platform - See backend engineer example above
  - Link: https://github.com/kcernjav/ddwl-platform (PRIVATE)
  - Why it's strong: Advanced SQL, PostGIS, migrations, query optimization

Strategic Recommendations

For Resume:
1. personal-website (Next.js project)
2. client-dashboard (Vue/TypeScript - explain transferable React skills)
3. observability-server (Node.js backend)

For Cover Letter:
Acknowledge Vue vs React difference upfront:
- "While my recent frontend work uses Vue 3 Composition API, the patterns directly transfer to React hooks"
- Demonstrate: Show how ref() = useState(), computed() = useMemo(), watchEffect() = useEffect()
- Commitment: "Excited to deepen React expertise in a production environment"

For Interview Preparation:
- Be ready to discuss Vue → React migration (syntax differences, not conceptual)
- Prepare Next.js examples (App Router, Server Components)
- Discuss observability-server WebSocket implementation
```

---

## Example 3: No Relevant Repositories Found

**Input:**
- Job: DevOps Engineer (Kubernetes, Terraform, Jenkins, Ansible)
- Search across 28 repositories (filtered to 3 possibly relevant repos)

**Output:**

```
Code Portfolio Analysis
Job Target: DevOps Engineer Role

Executive Summary
Searched 28 repositories but found limited examples of required DevOps technologies.

Technologies found:
- Docker: 5 repositories (good coverage)
- GitHub Actions: 3 repositories (basic CI/CD)

Technologies NOT found:
- Kubernetes: No production examples
- Terraform: No infrastructure-as-code repositories
- Jenkins: No Jenkins pipelines
- Ansible: No configuration management examples

Detailed Findings

Technology: Docker
- Best Example: ddwl-platform - Production Dockerfiles
  - Link: https://github.com/kcernjav/ddwl-platform (PRIVATE)
  - Why it's strong: Multi-stage builds, docker-compose, security best practices
  - Key files: backend/Dockerfile, docker-compose.yml

Technology: GitHub Actions (CI/CD)
- Best Example: ddwl-platform - Automated deployment pipeline
  - Link: https://github.com/kcernjav/ddwl-platform (PRIVATE)
  - Why it's strong: Build, test, and deploy workflow to AWS ECS
  - Key files: .github/workflows/deploy.yml

Strategic Recommendations

For Resume:
Given the significant skill gaps, this role may not be the best fit based on public portfolio alone.

However, if you have DevOps experience from work projects:
1. List Docker and CI/CD skills from GitHub portfolio
2. Mention Kubernetes/Terraform/Ansible from professional work (even if code is proprietary)
3. Be explicit about skill levels: "Proficient" vs "Familiar" vs "Learning"

For Cover Letter:
Be honest about the skill gap:
- "While my GitHub portfolio focuses on application development, I have hands-on Kubernetes experience from [previous role/company]"
- "I'm passionate about infrastructure-as-code and have been studying Terraform [mention any courses/certifications]"
- Emphasize: Willingness to learn, Docker expertise as foundation, understanding of DevOps principles

For Interview Preparation:
1. Prepare to discuss Docker expertise in depth (this is your strongest proof point)
2. Create a demo project if possible:
   - Simple Kubernetes deployment (minikube + kubectl)
   - Terraform module (provision AWS resources)
   - Share as public repo to demonstrate learning
3. Be ready to discuss DevOps concepts even without code examples:
   - CI/CD pipelines, infrastructure-as-code principles, GitOps workflow

Repository Access
Docker examples are visible in public repositories (Cernji-Agents).

Recommendation:
Consider creating public demo projects for missing technologies before applying:
- kubernetes-demo: Simple multi-service deployment with Helm charts
- terraform-aws-modules: Reusable IaC modules for common AWS resources
- This shows initiative and learning ability (valued in DevOps roles)
```

---

## Example 4: Technology-Specific Search (No Job Context)

**Input:**
- User query: "Find examples of my Python and PostgreSQL work"
- No specific job posting
- Technologies: Python, PostgreSQL

**Output:**

```
Portfolio Search Results
Technologies: Python, PostgreSQL

Found 8 repositories with Python, 3 repositories with PostgreSQL.

Technology: Python

Best Examples:
1. ddwl-platform - Enterprise logistics platform
   - Link: https://github.com/kcernjav/ddwl-platform (PRIVATE)
   - Complexity: High (production system, 10K+ daily users)
   - Notable features: FastAPI, Pydantic, async/await, RAG pipeline, 85% test coverage
   - Key files: backend/services/matching.py, backend/api/routes.py

2. career-assistant - AI-powered career tools
   - Link: https://github.com/kcernjav/cernji-agents (PUBLIC)
   - Complexity: Medium (MCP server, AI integration)
   - Notable features: FastAPI, Claude AI SDK, vector search, agent orchestration
   - Key files: apps/resume-agent/resume_agent.py

3. data-pipeline-tools - ETL scripts
   - Link: https://github.com/kcernjav/data-tools (PRIVATE)
   - Complexity: Medium (production ETL, error handling)
   - Notable features: Pandas, SQLAlchemy, scheduled jobs
   - Key files: pipelines/extract.py, pipelines/transform.py

Other repositories with Python: ml-experiments, web-scraper, api-client, automation-scripts, jupyter-notebooks

Technology: PostgreSQL

Best Examples:
1. ddwl-platform - Advanced SQL with PostGIS
   - Link: https://github.com/kcernjav/ddwl-platform (PRIVATE)
   - Complexity: High (complex schema, geospatial queries, optimizations)
   - Notable features: PostGIS, CTEs, window functions, migrations, query optimization
   - Key files: backend/migrations/, backend/repositories/shipment_repository.py

2. blog-platform - Standard relational schema
   - Link: https://github.com/kcernjav/blog-platform (PRIVATE)
   - Complexity: Medium (users, posts, comments, tags)
   - Notable features: Alembic migrations, SQLAlchemy ORM
   - Key files: backend/models.py, migrations/

3. data-pipeline-tools - Data warehouse
   - Link: https://github.com/kcernjav/data-tools (PRIVATE)
   - Complexity: Medium (ETL destination, aggregations)
   - Notable features: Bulk inserts, scheduled aggregations
   - Key files: pipelines/load.py, sql/aggregations.sql

Summary:
Your strongest Python work is in ddwl-platform and career-assistant.
Your strongest PostgreSQL work is in ddwl-platform (advanced SQL + PostGIS).

If applying for a Python/PostgreSQL role, lead with ddwl-platform as it demonstrates both technologies at a production level.
```
