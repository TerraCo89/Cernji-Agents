---
description: List all portfolio examples with optional filtering
allowed-tools: mcp__resume-agent__data_list_portfolio_examples, mcp__resume-agent__data_get_portfolio_example, AskUserQuestion
argument-hint: [--tech=TECHNOLOGY] [--company=COMPANY] [--limit=N]
---

# List Portfolio Examples

View all examples in your portfolio library with optional filtering by technology or company.

## Arguments

Parse `$ARGUMENTS` for optional filters:
- `--tech=X` or `-t X` - Filter by technology (e.g., `--tech=RAG`)
- `--company=X` or `-c X` - Filter by company (e.g., `--company="D&D Worldwide Logistics"`)
- `--limit=N` or `-l N` - Limit results (e.g., `--limit=10`)

If no arguments, show all examples.

## Process

### Step 1: Parse Arguments

Extract filters from `$ARGUMENTS`:
```python
technology_filter = None
company_filter = None
limit = None

# Parse patterns like:
# "--tech=RAG --limit=5"
# "-t RAG -c Aryza"
# "tech:RAG limit:10"
```

### Step 2: Fetch Examples

Call MCP tool:
```
results = mcp__resume-agent__data_list_portfolio_examples(
  limit=limit,
  technology_filter=technology_filter,
  company_filter=company_filter
)
```

### Step 3: Display Results

**If no examples found:**
```
No portfolio examples found.

Add your first example with:
  /career:add-portfolio
```

**If examples exist:**

Format as table:
```
PORTFOLIO LIBRARY ({count} examples)

ID  | Title                                | Company              | Technologies           | Updated
----|--------------------------------------|----------------------|------------------------|------------
1   | RAG Pipeline - Customer Matching     | D&D Worldwide        | RAG, Redis, Supabase   | 2025-01-15
2   | Qdrant MCP - Agent Memory           | Aryza                | Qdrant, Vector DBs     | 2025-01-14
3   | Multi-Stage Email Processing         | D&D Worldwide        | FastAPI, OpenAI        | 2025-01-13
...

Commands:
  View details: /career:search-portfolio "keyword"
  Add new: /career:add-portfolio
  Filter by tech: /career:list-portfolio --tech=RAG
  Filter by company: /career:list-portfolio --company=Aryza
```

### Step 4: Interactive Options

If more than 5 examples, ask user:

**Use AskUserQuestion:**
```
What would you like to do?
Options:
1. View details for specific example (enter ID)
2. Filter by technology
3. Filter by company
4. Show all (no filters)
5. Nothing, just browsing
```

**If user selects "View details":**
1. Ask for ID number
2. Use `mcp__resume-agent__data_get_portfolio_example(example_id)`
3. Display full example:
   ```
   ===== PORTFOLIO EXAMPLE #{id} =====

   Title: {title}
   Company: {company}
   Project: {project}

   Description:
   {description}

   Technologies:
   {technologies_list}

   File Paths:
   {file_paths}

   Source Repository:
   {source_repo}

   Content:
   {content}

   Created: {created_at}
   Updated: {updated_at}
   ```

**If user selects "Filter by technology":**
1. Show unique technologies from all examples
2. Ask user to select
3. Re-run command with filter

**If user selects "Filter by company":**
1. Show unique companies from all examples
2. Ask user to select
3. Re-run command with filter

### Step 5: Summary Statistics

At the end, show:
```
LIBRARY STATISTICS

Total Examples: {total_count}
Companies: {unique_companies}
Technologies: {unique_technologies_count}

Top Technologies:
- RAG: {count} examples
- Vector Databases: {count} examples
- FastAPI: {count} examples
...

Most Recent:
{most_recent_3_titles}
```

## Example Usage

### List All
```
User: /career:list-portfolio
```

### Filter by Technology
```
User: /career:list-portfolio --tech=RAG
User: /career:list-portfolio -t "Vector Databases"
```

### Filter by Company
```
User: /career:list-portfolio --company="D&D Worldwide Logistics"
User: /career:list-portfolio -c Aryza
```

### Combined Filters
```
User: /career:list-portfolio --tech=RAG --limit=5
User: /career:list-portfolio -t FastAPI -c "D&D Worldwide" -l 3
```

## Output Format

Keep output concise and scannable:
- Use tables for list view
- Use IDs for easy reference
- Show most important metadata
- Provide commands for next actions
- Truncate long content with "..." and offer to show full details

## Error Handling

- **Empty library**: Provide helpful message with command to add first example
- **No matches**: Show what filters were applied, suggest alternatives
- **Invalid filter values**: List available companies/technologies
