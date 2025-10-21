<!--
Sync Impact Report:
Version: 1.0.0 (Initial Ratification)
Modified Principles: N/A (Initial creation)
Added Sections:
  - Core Principles (I-VIII)
  - Multi-App Architecture Standards
  - Development Workflow
  - Governance
Removed Sections: N/A
Templates Requiring Updates:
  ✅ plan-template.md - Updated with constitution check gates
  ✅ spec-template.md - Aligned requirements sections
  ✅ tasks-template.md - Added observability and testing task categories
Follow-up TODOs: None
-->

# Cernji-Agents Constitution

## Core Principles

### I. Multi-App Isolation

Each application in the `apps/` directory MUST be self-contained and independently deployable.

**Rules:**
- Each app has its own dependencies, configuration, and `.claude/` directory
- Apps MUST NOT import code from other apps
- Shared data lives in root-level directories (`data/`, `resumes/`, `job-applications/`)
- Each app MUST provide a complete README.md with setup instructions
- Each app SHOULD provide a CLAUDE.md with agent-specific guidance

**Rationale:**
Isolation enables parallel development, independent testing, and flexible deployment. Apps can evolve at different rates without breaking each other.

### II. Data Access Layer (DAL)

All data operations MUST go through a centralized data access layer with schema validation.

**Rules:**
- Data-agnostic agents: Agents receive data and return content (no direct file I/O)
- Pydantic schemas: All data MUST be validated before read/write operations
- Single source of truth: The data-access-agent owns all file operations
- Type safety: No unvalidated data may be persisted or retrieved
- Future-proof: File storage MUST be swappable for database without agent changes

**Rationale:**
Centralized data access ensures consistency, enables testing, prevents data corruption, and makes storage layer migrations trivial.

### III. Test-First Development (NON-NEGOTIABLE)

Tests MUST be written before implementation for all new features.

**Rules:**
- Red-Green-Refactor cycle strictly enforced
- Tests written → User approved → Tests FAIL → Then implement
- Contract tests required for all external interfaces (MCP tools, REST endpoints, WebSocket)
- Integration tests required for multi-component workflows
- Unit tests SHOULD cover edge cases and error conditions
- All tests MUST pass before merge

**Rationale:**
Test-first ensures features are testable by design, provides living documentation, and catches regressions early.

### IV. Observability by Default

All applications MUST support event-driven observability through standardized hooks.

**Rules:**
- Hook events: PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, SessionEnd
- Structured logging with JSON payloads
- Every app MUST specify a `source_app` identifier for event tracking
- AI-generated summaries (`--summarize` flag) SHOULD be enabled for complex operations
- Event payloads MUST be serializable (no circular references)
- WebSocket broadcasting for real-time monitoring

**Rationale:**
Observability enables debugging multi-agent systems, performance analysis, and understanding agent behavior in production.

### V. User Experience Consistency

All user-facing interfaces MUST follow consistent patterns across applications.

**Rules:**
- Slash commands: Namespaced by app (e.g., `/career:apply`, `/translate:lesson`)
- Error messages: Human-readable with actionable next steps
- Progress feedback: Long-running operations MUST provide status updates
- Input validation: Clear error messages for invalid inputs
- Documentation: Every command/tool MUST have usage examples
- Idempotency: Commands SHOULD be safe to retry (fetch-job pattern)

**Rationale:**
Consistency reduces cognitive load, improves adoption, and creates a professional user experience.

### VI. Performance Standards

Applications MUST meet minimum performance thresholds.

**Rules:**
- MCP tool calls: <2 seconds for data reads, <5 seconds for writes
- REST API endpoints: <200ms p95 latency for GET, <500ms for POST
- WebSocket: <100ms message broadcast latency
- Database queries: Proper indexing for all query patterns
- File operations: Batch operations where possible (avoid N+1)
- Memory: Applications MUST NOT leak memory (monitor in long-running processes)

**Rationale:**
Performance directly impacts user satisfaction and system scalability. Standards ensure a responsive experience.

### VII. Type Safety & Validation

All data crossing application boundaries MUST be validated with schemas.

**Rules:**
- Pydantic models in Python applications
- TypeScript interfaces with runtime validation in JavaScript/TypeScript applications
- No `any` types in TypeScript (use `unknown` and validate)
- JSON payloads MUST have corresponding schema definitions
- Validation errors MUST include field-level details
- Schema changes REQUIRE version bumps (see Versioning)

**Rationale:**
Type safety prevents runtime errors, improves maintainability, and enables confident refactoring.

### VIII. Simplicity & YAGNI

Start simple. Complexity MUST be justified against constitutional gates.

**Rules:**
- Build the simplest thing that works
- New abstractions require justification in plan.md Complexity Tracking
- Prefer composition over inheritance
- Avoid premature optimization
- Each component SHOULD do one thing well
- When in doubt, choose the simpler approach

**Rationale:**
Unnecessary complexity increases maintenance burden, slows development, and introduces bugs.

## Multi-App Architecture Standards

### Application Structure

Each application in `apps/` MUST follow this structure:

```
apps/{app-name}/
├── .claude/
│   ├── agents/       # App-specific agents (if applicable)
│   └── commands/     # App-specific slash commands (if applicable)
├── src/              # Source code (language-specific layout)
├── tests/            # Test suite (if applicable)
├── README.md         # Setup, usage, and API documentation
├── CLAUDE.md         # Agent-specific development guidance (optional)
├── .env.example      # Environment template (if needed)
└── package.json      # Dependencies (or pyproject.toml, etc.)
```

### Root-Level Organization

Root directories serve shared purposes:

- **`data/`**: Shared databases (SQLite files)
- **`resumes/`**: Resume-specific data (YAML, PDF)
- **`job-applications/`**: Generated application artifacts
- **`ai_docs/`**: AI-generated documentation
- **`app_docs/`**: Application workflow documentation
- **`specs/`**: Feature specifications
- **`.claude/hooks/`**: Root-level observability hooks
- **`scripts/`**: System management scripts (start-system, stop-system)

### Technology Choices

Applications MAY use different tech stacks based on requirements:

- **Python apps**: UV + FastMCP + Pydantic (resume-agent pattern)
- **TypeScript apps**: Bun + SQLite + WebSocket (observability-server pattern)
- **Web clients**: Vue 3 + Vite + TailwindCSS (client pattern)
- Database: SQLite for all apps (simplicity, single file, fast)

### Inter-App Communication

Apps MUST NOT directly call each other. Integration patterns:

- **Shared data**: Read/write to root-level `data/` directories
- **Event-driven**: Publish events to observability-server
- **MCP tools**: Expose functionality via MCP server protocol
- **REST APIs**: Expose HTTP endpoints for external access

## Development Workflow

### Feature Development Process

1. **Specification** (`/speckit.specify`):
   - Create feature spec in `specs/{###-feature-name}/spec.md`
   - Define user stories with priorities (P1, P2, P3)
   - Write acceptance scenarios (Given/When/Then)
   - Identify unclear requirements with `NEEDS CLARIFICATION`

2. **Planning** (`/speckit.plan`):
   - Technical research (Phase 0)
   - Data model design (Phase 1)
   - Contract definitions (Phase 1)
   - Constitution check (GATE: must pass before implementation)

3. **Task Generation** (`/speckit.tasks`):
   - Dependency-ordered task list
   - Organized by user story for independent delivery
   - Test tasks FIRST (if tests required)

4. **Implementation** (`/speckit.implement`):
   - Execute tasks in dependency order
   - Run tests (Red-Green-Refactor)
   - Commit after each logical group

5. **Validation** (`/speckit.analyze`):
   - Cross-artifact consistency check
   - Quality analysis
   - Documentation verification

### Constitution Check Gates

Before Phase 0 research, verify:

- ✅ Does this feature belong in an existing app or require a new one?
- ✅ If new app: Is the complexity justified? (3 apps → 4 apps)
- ✅ Can this be achieved without adding new dependencies?
- ✅ Does this follow the Data Access Layer pattern?
- ✅ Are performance requirements defined?
- ✅ Is observability integration planned?

Re-check after Phase 1 design:

- ✅ Are all data schemas defined with Pydantic/TypeScript types?
- ✅ Are contract tests planned for all interfaces?
- ✅ Is the implementation the simplest approach?
- ✅ Are all dependencies justified in Complexity Tracking?

### Testing Standards

**Test Hierarchy:**

1. **Contract Tests** (REQUIRED for interfaces):
   - MCP tool signatures
   - REST API endpoints
   - WebSocket message formats
   - Database schemas

2. **Integration Tests** (REQUIRED for workflows):
   - Multi-component interactions
   - End-to-end user journeys
   - Error handling paths

3. **Unit Tests** (SHOULD HAVE for logic):
   - Business logic
   - Data transformations
   - Edge cases

**Test Organization:**

```
tests/
├── contract/      # Interface contract tests
├── integration/   # Multi-component tests
└── unit/          # Isolated logic tests
```

### Code Review Checklist

Before merge, verify:

- [ ] All tests pass (including new tests for feature)
- [ ] Constitution compliance verified
- [ ] Data schemas updated (if data changes)
- [ ] Documentation updated (README, CLAUDE.md)
- [ ] Performance benchmarks met (if applicable)
- [ ] Observability hooks integrated (for new operations)
- [ ] No new dependencies added without justification
- [ ] Complexity tracking updated (if gates violated)

## Governance

### Amendment Process

Constitution amendments require:

1. Proposal with rationale
2. Impact analysis on existing features
3. Template propagation plan (plan.md, spec.md, tasks.md)
4. Version bump following semantic versioning
5. Documentation update in affected CLAUDE.md files

### Versioning Policy

Constitution version follows MAJOR.MINOR.PATCH:

- **MAJOR**: Backward incompatible governance changes (e.g., removing a principle)
- **MINOR**: New principles or materially expanded guidance
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance Review

All pull requests MUST verify compliance with:

1. Core Principles (I-VIII)
2. Multi-App Architecture Standards
3. Testing Standards
4. Performance Standards

Violations MUST be:

- Explicitly justified in plan.md Complexity Tracking
- Approved by project maintainer
- Documented in feature specification

### Living Document

This constitution is a living document:

- Updated as project evolves
- Refined based on learnings
- Amended when principles no longer serve the project

**Use `.specify/memory/constitution.md` as the source of truth for all development decisions.**

---

**Version**: 1.0.0 | **Ratified**: 2025-10-21 | **Last Amended**: 2025-10-21
