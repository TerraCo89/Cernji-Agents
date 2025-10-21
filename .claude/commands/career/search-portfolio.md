---
description: Search portfolio library for specific technologies or keywords
allowed-tools: mcp__resume-agent__data_search_portfolio_examples, mcp__resume-agent__data_get_portfolio_example, AskUserQuestion
argument-hint: [query] [--tech=TECH1,TECH2]
---

# Search Portfolio Library

Full-text search across your portfolio library. Searches titles, descriptions, content, companies, and projects.

## Arguments

Parse `$ARGUMENTS` for:
- Main query (required): Free-text search term(s)
- `--tech=X,Y` (optional): Filter by specific technologies

Examples:
- `vector database`
- `RAG --tech=Redis,Supabase`
- `"semantic search" --tech=Python`

## Process

### Step 1: Parse Arguments

Extract query and technology filters:
```python
# Parse patterns:
# "vector database"
# "RAG --tech=Redis"
# "semantic search --tech=Python,FastAPI"

query = main_search_term
technologies = [] if no --tech flag else comma_separated_list
```

**If no arguments provided:**
Ask user:
```
What would you like to search for?
Examples:
- "vector database"
- "RAG pipeline"
- "agent orchestration"
- "email processing"

Search:
```

### Step 2: Execute Search

Call MCP tool:
```
results = mcp__resume-agent__data_search_portfolio_examples(
  query=query,
  technologies=technologies if provided else None
)
```

### Step 3: Display Results

**If no results:**
```
No portfolio examples found for "{query}"{tech_filter_msg}

Suggestions:
- Try broader search terms
- Remove technology filters
- List all examples: /career:list-portfolio
- Add new example: /career:add-portfolio
```

**If results found:**

Format with relevance context:
```
SEARCH RESULTS: "{query}" ({count} matches)

ID  | Title                              | Company           | Technologies         | Match Preview
----|-----------------------------------|-------------------|----------------------|---------------------------
1   | RAG Pipeline - Customer Matching  | D&D Worldwide     | RAG, Redis, Supabase | ...implemented semantic
    |                                   |                   |                      | similarity search using...
----|-----------------------------------|-------------------|----------------------|---------------------------
2   | Cache-First Retrieval Strategy    | D&D Worldwide     | Redis, FastAPI       | ...vector store in Supabase
    |                                   |                   |                      | for storing company SOPs...
----|-----------------------------------|-------------------|----------------------|---------------------------
3   | Qdrant MCP - Agent Memory         | Aryza             | Qdrant, Vector DBs   | ...used extensively to share
    |                                   |                   |                      | memory between Claude...

Commands:
  View full example: Enter ID number
  Refine search: /career:search-portfolio "new query"
  List all: /career:list-portfolio
```

### Step 4: Interactive Selection

**Use AskUserQuestion:**
```
What would you like to do?
Options:
1. View full details for an example (enter ID)
2. Copy example content for application
3. Refine search
4. Done
```

**If "View full details":**
1. Ask for ID
2. Use `mcp__resume-agent__data_get_portfolio_example(example_id)`
3. Display complete example with highlighted search terms:
   ```
   ===== PORTFOLIO EXAMPLE #{id} =====

   Title: {title}
   Company: {company} | Project: {project}

   Description:
   {description}

   Technologies: {technologies}

   File Paths:
   {file_paths with :line_numbers}

   Source Repository:
   {repo_url}

   CONTENT:
   {content with search terms highlighted if possible}

   ---
   Created: {created_at} | Updated: {updated_at}
   ---

   This example demonstrates: {key_technologies}
   ```

**If "Copy example content":**
1. Ask for ID
2. Get full content
3. Format for easy copying:
   ```
   PORTFOLIO EXAMPLE: {title}

   Company: {company}
   Technologies: {technologies}

   {content}

   Source: {repo_url}
   Files: {file_paths}

   [Ready to paste into job application]
   ```

**If "Refine search":**
1. Ask for new query
2. Optionally suggest related terms based on results
3. Re-execute search

### Step 5: Smart Suggestions

After showing results, provide contextual suggestions:

**If searching for technologies:**
```
Related examples you might be interested in:
- Also tagged with: {related_technologies}
- From same company: {count} more examples
- Similar projects: {similar_projects}
```

**If search returned many results:**
```
TIP: Narrow your search by:
- Adding technology filter: /career:search-portfolio "{query}" --tech=Python
- Searching specific company examples
- Using more specific terms
```

**If search returned few results:**
```
TIP: Broaden your search by:
- Using general terms (e.g., "AI" instead of "RAG pipeline")
- Removing technology filters
- Searching by company: /career:list-portfolio --company="{company}"
```

## Search Features

The search looks for matches in:
1. **Title** (highest priority)
2. **Description**
3. **Content** (full text)
4. **Company name**
5. **Project name**
6. **Technologies** (exact or partial match)

Results are ordered by:
- Most recently updated first
- Relevance (if multiple fields match)

## Example Usage

### Basic Search
```
User: /career:search-portfolio "vector database"
User: /career:search-portfolio RAG
User: /career:search-portfolio "semantic search"
```

### Technology-Filtered Search
```
User: /career:search-portfolio "pipeline" --tech=FastAPI
User: /career:search-portfolio "AI" --tech=Python,OpenAI
User: /career:search-portfolio "memory" --tech=Qdrant
```

### Multi-Word Search
```
User: /career:search-portfolio "email processing automation"
User: /career:search-portfolio "multi-agent orchestration"
```

## Output Format

- **Concise preview**: Show 50-100 char snippet with "..."
- **Highlight context**: Show where search term appears
- **Easy navigation**: Use IDs for quick access
- **Action-oriented**: Provide next-step commands
- **Scannable**: Use tables and clear formatting

## Error Handling

- **Empty query**: Prompt for search term
- **No results**: Suggest alternatives, broader terms
- **Invalid technology filter**: List available technologies
- **Very broad search** (100+ results): Suggest filtering options
