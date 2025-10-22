# Agent Skills API Reference

Complete API documentation for managing agent skills and their versions.

## Table of Contents
- [Skills Management](#skills-management)
- [Skill Versions Management](#skill-versions-management)
- [Response Schemas](#response-schemas)

---

## Skills Management

### Create Skill

**Endpoint:** `POST /v1/skills`

**Description:** Creates a new agent skill.

**Request Body:**
```json
{
  "name": "string",           // Required - The name of the skill
  "description": "string",    // Required - A description of what the skill does
  "parameters": {             // Optional - The parameters the skill accepts
    "type": "object",
    "properties": {
      "param_name": {
        "type": "string",
        "description": "Parameter description"
      }
    },
    "required": ["param_name"]
  }
}
```

**Response (200):**
```json
{
  "id": "skill-abc123xyz",
  "name": "get_weather",
  "description": "Get the current weather for a location.",
  "created_at": "2023-10-27T10:00:00Z"
}
```

**Example:**
```python
from anthropic import Anthropic

client = Anthropic(api_key="YOUR_API_KEY")

skill = client.beta.skills.create(
    display_title="Financial Analyzer",
    files=files_from_dir("path/to/skill")
)
```

---

### List Skills

**Endpoint:** `GET /v1/skills`

**Query Parameters:**
- `source` (optional) - Filter by source: "anthropic" or "custom"

**Description:** Lists all available skills in the workspace.

**Response (200):**
```json
{
  "data": [
    {
      "id": "skill-abc123xyz",
      "display_title": "calculator",
      "latest_version": "1.0.0",
      "source": "custom",
      "created_at": "2023-10-27T10:00:00Z",
      "updated_at": "2023-10-27T10:00:00Z"
    }
  ]
}
```

**Example:**
```python
# List all Anthropic-managed skills
skills = client.beta.skills.list(
    source="anthropic",
    betas=["skills-2025-10-02"]
)

for skill in skills.data:
    print(f"{skill.id}: {skill.display_title}")
```

---

### Get Skill

**Endpoint:** `GET /v1/skills/{skill_id}`

**Path Parameters:**
- `skill_id` (string, required) - The ID of the skill to retrieve

**Response (200):**
```json
{
  "id": "skill-abc123xyz",
  "name": "calculator",
  "description": "Performs mathematical calculations.",
  "latest_version": "2.0.0",
  "created_at": "2023-10-27T10:00:00Z"
}
```

---

### Delete Skill

**Endpoint:** `DELETE /v1/skills/{skill_id}`

**Path Parameters:**
- `skill_id` (string, required) - The ID of the skill to delete

**Response (200):**
```json
{
  "id": "skill-abc123xyz",
  "deleted": true
}
```

**Warning:** Deleting a skill is permanent and cannot be undone. All versions of the skill will also be deleted.

---

## Skill Versions Management

### Create Skill Version

**Endpoint:** `POST /v1/skills/{skill_id}/versions`

**Path Parameters:**
- `skill_id` (string, required) - The ID of the skill to create a version for

**Request Body:**
```json
{
  "version_number": "1.0.0",        // Required - Version number (semver)
  "code": "string",                 // Required - The code for the skill version
  "implementation": "string"        // Required - Implementation details
}
```

**Response (200):**
```json
{
  "id": "skill-version-abc123xyz",
  "skill_id": "skill-abc123xyz",
  "version": "1.0.0",
  "created_at": "2023-10-27T10:00:00Z"
}
```

**Example:**
```python
version = client.beta.skills.versions.create(
    skill_id="skill-abc123",
    files=files_from_dir("path/to/updated/skill")
)

print(f"Created version: {version.version}")
```

---

### List Skill Versions

**Endpoint:** `GET /v1/skills/{skill_id}/versions`

**Path Parameters:**
- `skill_id` (string, required) - The ID of the skill

**Response (200):**
```json
{
  "data": [
    {
      "id": "skill-version-abc123xyz",
      "skill_id": "skill-abc123xyz",
      "version": "1.0.0",
      "created_at": "2023-10-27T10:00:00Z"
    },
    {
      "id": "skill-version-def456xyz",
      "skill_id": "skill-abc123xyz",
      "version": "2.0.0",
      "created_at": "2023-10-28T10:00:00Z"
    }
  ]
}
```

---

### Get Skill Version

**Endpoint:** `GET /v1/skills/{skill_id}/versions/{version_id}`

**Path Parameters:**
- `skill_id` (string, required) - The ID of the skill
- `version_id` (string, required) - The ID of the skill version

**Response (200):**
```json
{
  "id": "skill-version-abc123xyz",
  "skill_id": "skill-abc123xyz",
  "version": "1.0.0",
  "code": "// Function code here",
  "created_at": "2023-10-27T10:00:00Z"
}
```

---

### Delete Skill Version

**Endpoint:** `DELETE /v1/skills/{skill_id}/versions/{version_id}`

**Path Parameters:**
- `skill_id` (string, required) - The ID of the skill
- `version_id` (string, required) - The ID of the skill version to delete

**Response (200/204):**
```json
{
  "id": "skill-version-abc123xyz",
  "deleted": true
}
```

---

## Using Skills in Messages API

To use skills in a message request, include them in the `container` parameter:

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {
                "type": "anthropic",      # or "custom"
                "skill_id": "pptx",       # Skill ID
                "version": "latest"       # or specific version
            }
        ]
    },
    messages=[{
        "role": "user",
        "content": "Create a presentation about renewable energy"
    }],
    tools=[{
        "type": "code_execution_20250825",
        "name": "code_execution"
    }]
)
```

---

## Pre-built Skills

Anthropic provides four pre-built skills accessible via the API:

| Skill ID | Description | Capabilities |
|----------|-------------|--------------|
| `pptx` | PowerPoint | Create and edit presentations |
| `xlsx` | Excel | Create spreadsheets, formulas, formatting |
| `docx` | Word | Create and format documents |
| `pdf` | PDF | Generate formatted PDF documents |

**Example:**
```python
# Use PowerPoint skill
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{
            "type": "anthropic",
            "skill_id": "pptx",
            "version": "latest"
        }]
    },
    messages=[{
        "role": "user",
        "content": "Create a 5-slide presentation on AI trends"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

---

## Response Schemas

### Skill Object
```typescript
{
  id: string;              // Unique identifier
  name?: string;           // Skill name (deprecated, use display_title)
  display_title: string;   // Human-readable skill name
  description?: string;    // Skill description
  latest_version: string;  // Latest version number
  source: "anthropic" | "custom";  // Skill source
  created_at: string;      // ISO 8601 timestamp
  updated_at: string;      // ISO 8601 timestamp
}
```

### Skill Version Object
```typescript
{
  id: string;              // Unique identifier
  skill_id: string;        // Parent skill ID
  version: string;         // Version number (semver)
  created_at: string;      // ISO 8601 timestamp
}
```

---

## Error Responses

All endpoints may return standard HTTP error codes:

- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid API key
- `404 Not Found` - Skill or version not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

**Error Response Format:**
```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "Detailed error message"
  }
}
```

---

## Rate Limits

Skills API endpoints are subject to standard Anthropic API rate limits. Check the response headers for rate limit information:

- `X-RateLimit-Limit` - Request limit per time window
- `X-RateLimit-Remaining` - Remaining requests
- `X-RateLimit-Reset` - Time when limit resets (Unix timestamp)

---

## Beta Headers

Skills functionality requires beta headers:

```python
client = Anthropic(
    api_key=API_KEY,
    default_headers={"anthropic-beta": "skills-2025-10-02"}
)
```

When using skills in messages, include additional betas:
```python
betas=[
    "code-execution-2025-08-25",
    "files-api-2025-04-14",
    "skills-2025-10-02"
]
```
