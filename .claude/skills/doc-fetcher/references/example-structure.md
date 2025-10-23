# Documentation Directory Structure Examples

This reference shows the expected directory structure for fetched documentation in `ai_docs/`.

## Single Library - Simple Fetch

When fetching a library for the first time with no topic specified:

```
ai_docs/
└── ai-ml/
    └── langgraph/
        ├── README.md              # Main documentation (default fetch)
        └── .meta.json            # Metadata about fetches
```

**`.meta.json` contents:**
```json
{
  "library_name": "LangGraph",
  "context7_id": "/langchain-ai/langgraph",
  "category": "ai-ml",
  "last_updated": "2025-10-23T14:30:00Z",
  "version": "latest",
  "fetches": [
    {
      "topic": "general",
      "file": "README.md",
      "tokens": 5000,
      "fetched_at": "2025-10-23T14:30:00Z"
    }
  ]
}
```

## Multiple Topics

When fetching specific topics for a library:

```
ai_docs/
└── frameworks/
    └── nextjs/
        ├── README.md              # General overview
        ├── routing.md             # Routing documentation
        ├── api-routes.md          # API routes documentation
        ├── server-components.md   # Server components documentation
        └── .meta.json            # Metadata tracking all fetches
```

**`.meta.json` with multiple topics:**
```json
{
  "library_name": "Next.js",
  "context7_id": "/vercel/next.js",
  "category": "frameworks",
  "last_updated": "2025-10-23T15:45:00Z",
  "version": "latest",
  "fetches": [
    {
      "topic": "general",
      "file": "README.md",
      "tokens": 5000,
      "fetched_at": "2025-10-23T14:00:00Z"
    },
    {
      "topic": "routing",
      "file": "routing.md",
      "tokens": 3500,
      "fetched_at": "2025-10-23T15:30:00Z"
    },
    {
      "topic": "api routes",
      "file": "api-routes.md",
      "tokens": 2800,
      "fetched_at": "2025-10-23T15:35:00Z"
    },
    {
      "topic": "server components",
      "file": "server-components.md",
      "tokens": 4200,
      "fetched_at": "2025-10-23T15:45:00Z"
    }
  ]
}
```

## Specific Version

When fetching a specific version:

```
ai_docs/
└── frameworks/
    └── nextjs/
        ├── v14/
        │   ├── README.md
        │   ├── routing.md
        │   └── .meta.json        # Version-specific metadata
        ├── v15/
        │   ├── README.md
        │   └── .meta.json
        └── README.md             # Latest version (default)
```

**Version-specific `.meta.json`:**
```json
{
  "library_name": "Next.js",
  "context7_id": "/vercel/next.js/v14.3.0-canary.87",
  "category": "frameworks",
  "last_updated": "2025-10-23T16:00:00Z",
  "version": "v14.3.0-canary.87",
  "fetches": [
    {
      "topic": "general",
      "file": "README.md",
      "tokens": 5000,
      "fetched_at": "2025-10-23T16:00:00Z"
    }
  ]
}
```

## Full Multi-Library Example

Realistic `ai_docs/` directory after multiple fetches:

```
ai_docs/
├── ai-ml/
│   ├── langchain/
│   │   ├── README.md
│   │   ├── chains.md
│   │   ├── agents.md
│   │   └── .meta.json
│   ├── langgraph/
│   │   ├── README.md
│   │   ├── state-graphs.md
│   │   └── .meta.json
│   └── openai/
│       ├── README.md
│       ├── chat-completions.md
│       └── .meta.json
├── frameworks/
│   ├── nextjs/
│   │   ├── README.md
│   │   ├── routing.md
│   │   ├── api-routes.md
│   │   └── .meta.json
│   └── react/
│       ├── README.md
│       ├── hooks.md
│       └── .meta.json
├── databases/
│   ├── mongodb/
│   │   ├── README.md
│   │   └── .meta.json
│   └── prisma/
│       ├── README.md
│       ├── migrations.md
│       └── .meta.json
└── frontend/
    └── tailwindcss/
        ├── README.md
        ├── utilities.md
        └── .meta.json
```

## File Naming Conventions

### Topic to Filename Mapping

| Topic Input | Filename |
|-------------|----------|
| "general" or none | README.md |
| "routing" | routing.md |
| "API routes" | api-routes.md |
| "Server Components" | server-components.md |
| "state graphs" | state-graphs.md |
| "Chat Completions API" | chat-completions-api.md |

**Rules:**
1. Lowercase all words
2. Replace spaces with hyphens
3. Remove special characters except hyphens
4. Use `.md` extension
5. General/default documentation always goes to `README.md`

## Directory Path Construction

**Formula:**
```
ai_docs/{category}/{normalized-library-name}/[{version}/]{topic-filename}
```

**Examples:**

1. **Basic:** `ai_docs/ai-ml/langgraph/README.md`
   - Category: ai-ml
   - Library: langgraph
   - Version: none (latest)
   - Topic: general (README.md)

2. **With topic:** `ai_docs/frameworks/nextjs/routing.md`
   - Category: frameworks
   - Library: nextjs
   - Version: none (latest)
   - Topic: routing

3. **With version:** `ai_docs/frameworks/nextjs/v14/app-router.md`
   - Category: frameworks
   - Library: nextjs
   - Version: v14
   - Topic: app router

## Metadata Usage

The `.meta.json` file serves multiple purposes:

1. **Track fetch history** - Avoid re-fetching unchanged documentation
2. **Version management** - Know which version of docs you have
3. **Topic index** - Quick reference to all available topics
4. **Refresh logic** - Determine when to refresh based on `last_updated`
5. **Context7 mapping** - Remember the Context7 ID for future fetches

## Refresh Behavior

### Refreshing Existing Documentation

When refreshing (user requests update or re-fetch):

1. **Load existing `.meta.json`**
2. **Check if topic exists:**
   - If yes: Overwrite existing file, update metadata entry
   - If no: Create new file, add metadata entry
3. **Update `last_updated` timestamp**
4. **Save updated `.meta.json`**

### Adding New Topics

When adding a new topic to existing library:

1. **Load existing `.meta.json`**
2. **Fetch new topic documentation**
3. **Create new topic file** (e.g., `hooks.md`)
4. **Append to `fetches` array** in metadata
5. **Update `last_updated` timestamp**
6. **Save updated `.meta.json`**

## Migration from Existing Structure

If `ai_docs/` already has documentation without this structure:

### Example: Existing `ai_docs/langgraph/README.md`

**Current structure:**
```
ai_docs/
└── langgraph/
    └── README.md
```

**Migration process:**
1. Detect library category (langgraph -> ai-ml)
2. Create new directory: `ai_docs/ai-ml/langgraph/`
3. Move existing file: `README.md` -> `ai_docs/ai-ml/langgraph/README.md`
4. Create `.meta.json` with default metadata
5. Inform user: "Migrated langgraph docs to ai_docs/ai-ml/langgraph/"

**After migration:**
```
ai_docs/
└── ai-ml/
    └── langgraph/
        ├── README.md
        └── .meta.json
```
