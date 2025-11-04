---
name: work-linear-issue
description: Work on a specific Linear issue from start to finish using systematic task delegation
---

# /work-linear-issue - Complete Linear Issue Implementation

## Purpose
Fetch a Linear issue by ID and implement it systematically using sub-agents, following the proven process below.

## Usage
```
/work-linear-issue <ISSUE_ID>
```

Example:
```
/work-linear-issue DDWL-123
```

## Execution Flow

### Phase 1: Issue Understanding

#### 1.1 Fetch Issue Details
Use the Linear MCP tools to retrieve complete issue information:
```
mcp__linear__get_issue(id: ISSUE_ID)
```

Extract and analyze:
- **Title**: What feature/fix is needed
- **Description**: Detailed requirements (often in Markdown)
- **Labels**: Technology tags (backend, frontend, database, etc.)
- **Status**: Current state
- **Priority**: Urgency level
- **Project**: Related project context
- **Parent/Sub-issues**: Hierarchical dependencies
- **Comments**: Additional context from team discussion
- **Attachments**: Screenshots, diagrams, reference docs
- **Git Branch Name**: Auto-generated branch for this work

#### 1.2 Parse Requirements
Analyze the description for:
- **Acceptance Criteria**: What defines "done"
- **Technical Specs**: API schemas, UI mockups, database changes
- **Related Work**: Links to other issues, PRs, or documentation
- **Testing Requirements**: Expected test coverage
- **Documentation Needs**: What needs updating

#### 1.3 Check Dependencies
- Review parent issue (if sub-issue)
- Check related issues linked in description
- Identify blocking dependencies
- Note any prerequisite work

### Phase 2: Context Gathering (Use Sub-Agents)

#### IMPORTANT
- Update the task status to In Progress.
- Create a branch for the ticket: eg. feature\DEV-123

After understanding the issue, use the **Task tool with subagent_type=Explore** to delegate code exploration. Launch these explorations **in parallel** (single message with multiple Task calls):

#### 2.1 Feature Area Discovery
Launch an Explore agent based on issue labels and description:

```
Prompt for agent:
Find all files related to [FEATURE_FROM_ISSUE]. Look for:
1. Direct matches in file names and imports
2. Files mentioned in the issue description
3. Related API endpoints, models, and schemas
4. Existing test files for this feature area
5. Configuration files that might need updates
Thoroughness: medium
```

#### 2.2 API & Schema Discovery
Launch an Explore agent to find related backend/database structures:

```
Prompt for agent:
Find API endpoints and schemas related to [FEATURE_FROM_ISSUE]. Search for:
1. FastAPI router definitions matching this feature area
2. SQLModel table definitions in models/
3. Pydantic schemas in schemas/
4. Repository and service layer implementations
5. MCP tools if this involves AI integration
Thoroughness: medium
```

#### 2.3 Pattern & Scaffold Discovery
Launch an Explore agent to find implementation patterns:

```
Prompt for agent:
Find implementation patterns for [FEATURE_FROM_ISSUE]. Look for:
1. Similar features already implemented
2. Relevant scaffold templates in docs/developer/scaffold-templates.md
3. Testing patterns for similar features
4. Error handling patterns in app/core/errors/
Thoroughness: quick
```

#### 2.4 Frontend Discovery (if applicable)
If issue has "frontend" label, launch additional agent:

```
Prompt for agent:
Find frontend files related to [FEATURE_FROM_ISSUE]. Look for:
1. React components in frontend/src/components/
2. Routes in frontend/src/routes/
3. Stores in frontend/src/stores/
4. Hooks in frontend/src/hooks/
5. API client usage patterns
Thoroughness: medium
```

### Phase 3: Planning

After sub-agents return with findings, create a comprehensive plan using the TodoWrite tool:

#### 3.1 Break Down Requirements
Map issue acceptance criteria to specific tasks:
- Each acceptance criterion becomes one or more todos
- Group related work (e.g., "Backend API" group, "Frontend UI" group)
- Identify test requirements for each piece

#### 3.2 Map to Implementation
For each requirement, identify:
- **Files to create/modify** (from Phase 2 discoveries)
- **Patterns to follow** (from scaffold templates)
- **APIs to integrate** (from context gathering)
- **Tests to write** (unit, integration, E2E)

#### 3.3 Create Todo List
Write specific, testable tasks:

**Format**:
- ✅ Content: "Create [specific file/function] implementing [requirement]"
- 📝 ActiveForm: "Creating [specific file/function]"

**Task Grouping**:
1. **Setup Tasks**: Branch creation, dependency updates
2. **Backend Tasks**: APIs, services, repositories, models
3. **Frontend Tasks**: Components, routes, hooks, stores
4. **Database Tasks**: Migrations, RLS policies
5. **Integration Tasks**: MCP tools, external APIs
6. **Testing Tasks**: Unit, integration, E2E tests
7. **Documentation Tasks**: README updates, API docs
8. **Validation Tasks**: Run tests, check build, verify requirements

### Phase 4: Implementation (Delegate to Sub-Agents)

**CRITICAL**: The orchestrator should NOT implement code directly. Delegate to specialized sub-agents.

#### 4.1 Git Branch Setup
If git branch name is provided by Linear:
```bash
git checkout -b BRANCH_NAME
```

#### 4.2 Atomic Task Delegation
For each todo item, delegate to the appropriate specialist:

**Agent Selection Based on Work Type**:

| Work Type | Sub-Agent | Example Task |
|-----------|-----------|--------------|
| FastAPI endpoints, services | `ddwl-fastapi-developer` | "Create POST /api/customers/match endpoint" |
| React components | `ddwl-react-chakraui-developer` | "Create CustomerMatchingForm component" |
| Database migrations | `ddwl-supabase-coordinator` | "Add customer_matches table migration" |
| MCP tools | `ddwl-mcp-tool-builder` | "Create customer matching MCP tool" |
| Unit/integration tests | `ddwl-test-engineer` | "Write tests for customer matching service" |
| Test execution | `ddwl-test-runner` | "Run pytest suite and fix failures" |
| Frontend debugging | `frontend-error-detective` | "Fix TypeScript errors in CustomerForm" |
| Quote processing | `quote-processor` | "Generate quote from RFQ email" |
| Rate management | `rate-manager` | "Update co-loader rates for APAC routes" |

#### 4.3 Delegation Example

```
User Issue: "Implement customer fuzzy matching API"

Orchestrator Todo List:
1. ⏳ Create customer matching service layer
2. ⏳ Create POST /api/customers/match endpoint
3. ⏳ Add unit tests for matching service
4. ⏳ Add integration test for API endpoint
5. ⏳ Update API documentation

Step 1: Mark todo #1 in_progress
Step 2: Delegate to ddwl-fastapi-developer:

Task(
  subagent_type="ddwl-fastapi-developer",
  description="Create customer matching service",
  prompt="""
  Create customer matching service layer:

  File: apps/backend/app/services/customer_matching_service.py

  Requirements from Linear Issue DDWL-123:
  - Fuzzy match company names using RapidFuzz
  - Match by email domain
  - Return confidence score (0-100)
  - Support batch matching

  Implementation Details:
  - Follow service pattern from apps/backend/app/services/quote_service.py:25-150
  - Use CustomerRepository from apps/backend/app/repositories/customer_repository.py
  - Implement BusinessRuleError for no matches (app/core/errors/)

  Reference discoveries:
  - Customer model: apps/backend/app/models/customer.py:15
  - Similar matching logic: apps/backend/app/services/email_parsing_service.py:89-120

  DO NOT create the API endpoint - that's a separate task.
  """
)

Step 3: Review result → Success!
Step 4: Mark todo #1 completed
[Continue with remaining todos...]
```

#### 4.4 Delegation Best Practices

**DO**:
- ✅ Reference Linear issue number in commit messages
- ✅ Provide file paths from Phase 2 discoveries
- ✅ Include acceptance criteria from issue description
- ✅ Reference similar patterns found in codebase
- ✅ Specify what NOT to do (avoid scope creep)
- ✅ Launch independent tasks in parallel

**DON'T**:
- ❌ Implement code yourself in the orchestrator
- ❌ Give vague instructions without context
- ❌ Mark todos complete before verifying work
- ❌ Skip test creation
- ❌ Forget to update documentation

### Phase 5: Testing & Validation

#### 5.1 Run Test Suite
Delegate to `ddwl-test-runner`:
```
Task(
  subagent_type="ddwl-test-runner",
  description="Run tests for Linear issue DDWL-123",
  prompt="""
  Run test suite for customer matching feature:

  Commands:
  export TESTING=true POSTGRES_DB=app_test
  uv run pytest apps/backend/app/tests/unit/test_customer_matching_service.py -v
  uv run pytest apps/backend/app/tests/integration/test_customer_matching_api.py -v

  If tests fail, analyze and fix automatically.
  Report final test results.
  """
)
```

#### 5.2 Verify Acceptance Criteria
Check each criterion from the Linear issue:
- ✅ Feature works as described
- ✅ Tests pass
- ✅ No regressions introduced
- ✅ Documentation updated
- ✅ Code follows project patterns

#### 5.3 Update Linear Issue
After successful implementation:
- Add comment summarizing changes
- Update status to "In Review" or "Ready for Testing"
- Link PR if created

### Phase 6: Pull Request Creation (Optional)

If user requests PR creation, use `/pr` command or delegate:
```bash
# Ensure all changes are committed
git add .
git commit -m "feat(customer-matching): implement fuzzy matching API

Implements DDWL-123
- Add customer matching service with RapidFuzz
- Create POST /api/customers/match endpoint
- Add comprehensive test suite
- Update API documentation

Refs: DDWL-123"

git push -u origin BRANCH_NAME

# Create PR
gh pr create --title "feat: Customer fuzzy matching API (DDWL-123)" \
  --body "Implements Linear issue DDWL-123..."
```

## Important Guidelines

### Linear Integration
- Always fetch latest issue state at start
- Include issue ID in all commits: `feat(scope): description\n\nRefs: DDWL-123`
- Update issue status as work progresses
- Add comments to issue documenting key decisions

### Sub-Agent Usage
- **Always use Task tool with subagent_type=Explore** for code discovery
- Launch multiple agents **in parallel** when possible
- Specify thoroughness: "quick", "medium", or "very thorough"

### Test Safety
For DDWL Platform, **ALWAYS** use test database:
```bash
export TESTING=true POSTGRES_DB=app_test
```

### Code References
Format: `file_path:line_number`
Example: "Matching logic in `apps/backend/app/services/customer_matching.py:145`"

## Example Workflow

```
User: /work-linear-issue DDWL-456

You: 🚀 Let me fetch Linear issue DDWL-456 and implement it systematically!

[Fetches issue via mcp__linear__get_issue]

Issue Details:
Title: "Add email-based customer matching"
Labels: backend, enhancement
Priority: High
Status: Todo

Requirements:
✅ Match customers by email domain
✅ Return top 3 matches with confidence scores
✅ Add caching for frequent lookups

[Launches 3 Explore agents in parallel]
- File discovery agent
- API/schema discovery agent
- Pattern discovery agent

[Waits for agents, creates todo list]

Todo List:
1. ⏳ Create email domain extraction utility
2. ⏳ Add email matching to CustomerMatchingService
3. ⏳ Add caching layer with Redis
4. ⏳ Create unit tests
5. ⏳ Create integration tests
6. ⏳ Update API documentation

[Begins implementation by delegating to specialists]
[Marks todos as completed after verification]
[Runs tests and validates]
[Updates Linear issue with summary]

✅ Issue DDWL-456 complete! All acceptance criteria met.
```

## Output Style

- Be enthusiastic and supportive 🚀
- Reference the Linear issue number frequently
- Provide educational insights about patterns discovered
- Explain why specific approaches are chosen
- Keep user informed via todo updates
- Celebrate milestones (tests passing, features complete)

Now, let's implement your Linear issue! Please provide:
**Linear Issue ID** (e.g., `DDWL-123`)
