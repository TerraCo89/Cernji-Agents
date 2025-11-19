#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#     "httpx>=0.28.0",
#     "python-dotenv>=1.0.0",
# ]
# requires-python = ">=3.10"
# ///

"""
Trigger Error Analysis Agent from Kibana Alert

Called by observability server when high-severity error alerts are received.
Automatically analyzes error patterns, creates Linear issues, and updates knowledge base.

Usage:
    echo '{"alert_data": {...}}' | uv run trigger_error_analysis.py
    OR
    uv run trigger_error_analysis.py --alert-json '{"alert_data": {...}}'

Environment Variables:
    ELASTICSEARCH_URL: Elasticsearch endpoint (default: http://localhost:9200)
    LINEAR_API_KEY: Linear API key for creating issues
    QDRANT_URL: Qdrant vector store URL (default: http://localhost:6333)
"""

import os
import sys
import json
import argparse
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
OBSERVABILITY_SERVER_URL = os.getenv("OBSERVABILITY_SERVER_URL", "http://localhost:4000")
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY", "")
LINEAR_API_URL = "https://api.linear.app/graphql"
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = "resume-agent-chunks"  # Same collection as resume-agent uses


# ============================================================================
# Error Analysis Functions
# ============================================================================

async def search_errors_from_alert(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query Elasticsearch for errors related to the alert.

    Uses the same query pattern as the error-analysis MCP server.
    """
    service = alert_data.get("service", "unknown")
    time_range = alert_data.get("time_range", "15m")

    # Parse time range (simplified)
    if time_range.endswith('m'):
        gte = f"now-{time_range}"
    elif time_range.endswith('h'):
        gte = f"now-{time_range}"
    else:
        gte = "now-1h"

    query = {
        "size": 50,
        "sort": [{"@timestamp": {"order": "desc"}}],
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": gte,
                                "lte": "now"
                            }
                        }
                    },
                    {"term": {"log.level": "error"}}
                ],
                "filter": []
            }
        }
    }

    # Add service filter if specified
    if service and service != "unknown":
        query["query"]["bool"]["filter"].append({
            "term": {"service.name": service}
        })

    # Execute query
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{ELASTICSEARCH_URL}/logs-*/_search",
                json=query
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error querying Elasticsearch: {e}", file=sys.stderr)
            return {"error": str(e)}


async def get_error_patterns(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get error patterns for the service from the alert.
    """
    service = alert_data.get("service", "unknown")
    time_range = alert_data.get("time_range", "1h")

    if time_range.endswith('m'):
        gte = f"now-{time_range}"
    else:
        gte = "now-1h"

    query = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": gte,
                                "lte": "now"
                            }
                        }
                    },
                    {"term": {"log.level": "error"}}
                ],
                "filter": []
            }
        },
        "aggs": {
            "error_patterns": {
                "terms": {
                    "field": "message.keyword",
                    "size": 10,
                    "min_doc_count": 2
                },
                "aggs": {
                    "sample_errors": {
                        "top_hits": {
                            "size": 1,
                            "_source": ["@timestamp", "service.name", "error.type", "trace.id"]
                        }
                    }
                }
            }
        }
    }

    # Add service filter
    if service and service != "unknown":
        query["query"]["bool"]["filter"].append({
            "term": {"service.name": service}
        })

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{ELASTICSEARCH_URL}/logs-*/_search",
                json=query
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error querying Elasticsearch patterns: {e}", file=sys.stderr)
            return {"error": str(e)}


def classify_root_cause(error_message: str, error_type: Optional[str]) -> str:
    """
    Simple root cause classification based on error patterns.

    Categories:
    - configuration: Missing dependencies, env vars, etc.
    - documentation: API usage errors, missing examples
    - agent_scope: Complex state management errors
    - unknown: Cannot classify automatically
    """
    error_lower = error_message.lower()
    error_type_lower = (error_type or "").lower()

    # Configuration/Dependency issues
    if any(pattern in error_lower for pattern in [
        "modulenotfounderror",
        "importerror",
        "cannot find module",
        "connection refused",
        "enoent",
        "no such file",
        "environment variable"
    ]):
        return "configuration"

    # Documentation/API usage issues
    if any(pattern in error_lower for pattern in [
        "typeerror",
        "attributeerror",
        "nonetype",
        "unexpected argument",
        "missing argument",
        "invalid",
        "unsupported"
    ]):
        return "documentation"

    # Agent scope/complexity issues
    if any(pattern in error_lower for pattern in [
        "state",
        "deadlock",
        "timeout",
        "recursion",
        "maximum",
        "context"
    ]):
        return "agent_scope"

    return "unknown"


def generate_linear_issue_description(alert_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """
    Generate Linear issue description from alert and analysis data.
    """
    service = alert_data.get("service", "unknown")
    error_count = alert_data.get("error_count", 0)
    severity = alert_data.get("severity", "unknown")

    patterns = analysis.get("patterns", [])
    root_cause = analysis.get("root_cause", "unknown")

    description = f"""## Problem

**Alert triggered**: High error rate detected in `{service}`
**Error count**: {error_count} errors
**Severity**: {severity}
**Time**: {alert_data.get('timestamp', 'unknown')}

## Error Patterns Detected

"""

    if patterns:
        for i, pattern in enumerate(patterns[:5], 1):
            description += f"{i}. **{pattern.get('message', 'Unknown error')}** ({pattern.get('count', 0)} occurrences)\n"
            if pattern.get('error_type'):
                description += f"   - Type: `{pattern['error_type']}`\n"
            if pattern.get('sample_trace_id'):
                description += f"   - Sample trace ID: `{pattern['sample_trace_id']}`\n"
            description += "\n"
    else:
        description += "*No specific patterns identified - requires manual investigation*\n\n"

    description += f"""## Root Cause Classification

**Category**: {root_cause}

"""

    # Add category-specific recommendations
    if root_cause == "configuration":
        description += """**Recommended Actions**:
- [ ] Verify all dependencies are declared in `pyproject.toml` or `package.json`
- [ ] Check environment variables in `.env.example`
- [ ] Verify service dependencies (Docker, databases) are running
- [ ] Review startup validation scripts

"""
    elif root_cause == "documentation":
        description += """**Recommended Actions**:
- [ ] Search for working examples in codebase
- [ ] Add code examples to `ai_docs/` or `library-docs/`
- [ ] Update API documentation with correct usage
- [ ] Create skill for reusable pattern

"""
    elif root_cause == "agent_scope":
        description += """**Recommended Actions**:
- [ ] Analyze agent graph complexity (count nodes/edges)
- [ ] Consider splitting into specialized sub-agents
- [ ] Review state management patterns
- [ ] Simplify conditional logic

"""
    else:
        description += """**Recommended Actions**:
- [ ] Manual investigation required
- [ ] Check full error context in ELK stack
- [ ] Review related logs with trace IDs
- [ ] Consult knowledge base for similar errors

"""

    description += f"""## Investigation Resources

- **ELK Query**: `service.name:{service} AND log.level:error`
- **Time Range**: {alert_data.get('time_range', '15m')}
- **Alert ID**: {alert_data.get('alert_id', 'N/A')}

## Acceptance Criteria

- [ ] Root cause identified and documented
- [ ] Fix implemented and tested
- [ ] Knowledge base updated with solution
- [ ] No recurrence for 7 days after deployment

---

🤖 Auto-generated by Error Analysis Agent
"""

    return description


async def send_analysis_event(event_data: Dict[str, Any]) -> None:
    """
    Send error analysis event to observability server for tracking.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{OBSERVABILITY_SERVER_URL}/events",
                json=event_data
            )
            response.raise_for_status()
            print(f"Analysis event sent to observability server: {event_data.get('session_id')}", file=sys.stderr)
        except httpx.HTTPError as e:
            print(f"Warning: Could not send event to observability server: {e}", file=sys.stderr)


async def create_linear_issue(issue_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create a Linear issue using GraphQL API.

    Args:
        issue_data: Dictionary with title, description, team, labels, priority

    Returns:
        Created issue data or None if failed
    """
    if not LINEAR_API_KEY:
        print("Warning: LINEAR_API_KEY not set, skipping Linear issue creation", file=sys.stderr)
        return None

    # GraphQL mutation to create issue
    mutation = """
    mutation IssueCreate($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue {
          id
          identifier
          title
          url
        }
      }
    }
    """

    # Prepare input
    input_data = {
        "title": issue_data["title"],
        "description": issue_data["description"],
        "teamId": issue_data.get("team_id"),  # Will need to look up if only name provided
        "priority": issue_data.get("priority", 3),  # Default to Normal
    }

    # Add label IDs if provided
    if issue_data.get("label_ids"):
        input_data["labelIds"] = issue_data["label_ids"]

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                LINEAR_API_URL,
                json={
                    "query": mutation,
                    "variables": {"input": input_data}
                },
                headers={
                    "Authorization": LINEAR_API_KEY,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            result = response.json()

            if result.get("data", {}).get("issueCreate", {}).get("success"):
                issue = result["data"]["issueCreate"]["issue"]
                print(f"Linear issue created: {issue['identifier']} - {issue['url']}", file=sys.stderr)
                return issue
            else:
                error = result.get("errors", [{"message": "Unknown error"}])[0]["message"]
                print(f"Failed to create Linear issue: {error}", file=sys.stderr)
                return None

        except httpx.HTTPError as e:
            print(f"Error creating Linear issue: {e}", file=sys.stderr)
            return None


async def get_linear_team_id(team_name: str = "DEV") -> Optional[str]:
    """
    Get Linear team ID by name.

    Args:
        team_name: Team name (e.g., "DEV")

    Returns:
        Team ID or None if not found
    """
    if not LINEAR_API_KEY:
        return None

    query = """
    query Teams {
      teams {
        nodes {
          id
          name
          key
        }
      }
    }
    """

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                LINEAR_API_URL,
                json={"query": query},
                headers={
                    "Authorization": LINEAR_API_KEY,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            result = response.json()

            teams = result.get("data", {}).get("teams", {}).get("nodes", [])
            for team in teams:
                if team["name"] == team_name or team["key"] == team_name:
                    return team["id"]

            print(f"Warning: Team '{team_name}' not found in Linear", file=sys.stderr)
            return None

        except httpx.HTTPError as e:
            print(f"Error fetching Linear teams: {e}", file=sys.stderr)
            return None


async def store_in_knowledge_base(error_data: Dict[str, Any]) -> bool:
    """
    Store error analysis in Qdrant knowledge base for future reference.

    Args:
        error_data: Dictionary with error details and solution

    Returns:
        True if successful, False otherwise
    """
    try:
        # Import sentence-transformers here (only if needed)
        from sentence_transformers import SentenceTransformer

        # Initialize embedding model (same as resume-agent uses)
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        # Create knowledge base entry
        text = f"""
Error Analysis Entry

Error Type: {error_data.get('error_type', 'Unknown')}
Service: {error_data.get('service', 'Unknown')}
Message: {error_data.get('message', 'No message')}

Root Cause: {error_data.get('root_cause', 'Unknown')}
Occurrences: {error_data.get('occurrences', 0)}

Solution:
{error_data.get('solution', 'No solution documented yet')}

Prevention:
{error_data.get('prevention', 'See Linear issue for prevention strategy')}

Linear Issue: {error_data.get('linear_issue_url', 'N/A')}
Last Updated: {datetime.utcnow().isoformat()}Z
""".strip()

        # Generate embedding
        embedding = model.encode(text).tolist()

        # Store in Qdrant
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points",
                json={
                    "points": [
                        {
                            "id": f"error-{error_data.get('alert_id', 'unknown')}",
                            "vector": embedding,
                            "payload": {
                                "type": "error_analysis",
                                "error_type": error_data.get('error_type'),
                                "service": error_data.get('service'),
                                "root_cause": error_data.get('root_cause'),
                                "occurrences": error_data.get('occurrences', 0),
                                "linear_issue_url": error_data.get('linear_issue_url'),
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "text": text
                            }
                        }
                    ]
                }
            )
            response.raise_for_status()
            print(f"Stored error analysis in knowledge base (Qdrant)", file=sys.stderr)
            return True

    except ImportError:
        print("Warning: sentence-transformers not installed, skipping knowledge base storage", file=sys.stderr)
        return False
    except httpx.HTTPError as e:
        print(f"Warning: Could not store in knowledge base: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Warning: Error storing in knowledge base: {e}", file=sys.stderr)
        return False


# ============================================================================
# Main Analysis Workflow
# ============================================================================

async def analyze_alert(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main error analysis workflow.

    Returns:
        Dictionary with analysis results and actions taken.
    """
    print(f"Starting error analysis for alert: {alert_data.get('alert_name', 'unnamed')}", file=sys.stderr)

    # Step 1: Query Elasticsearch for errors
    print("Querying Elasticsearch for error patterns...", file=sys.stderr)
    errors_result = await search_errors_from_alert(alert_data)
    patterns_result = await get_error_patterns(alert_data)

    if "error" in errors_result or "error" in patterns_result:
        return {
            "success": False,
            "error": "Failed to query Elasticsearch",
            "alert_id": alert_data.get("alert_id")
        }

    # Step 2: Analyze patterns
    total_errors = errors_result.get("hits", {}).get("total", {}).get("value", 0)
    pattern_buckets = patterns_result.get("aggregations", {}).get("error_patterns", {}).get("buckets", [])

    patterns = []
    for bucket in pattern_buckets:
        sample = bucket.get("sample_errors", {}).get("hits", {}).get("hits", [{}])[0].get("_source", {})
        patterns.append({
            "message": bucket.get("key"),
            "count": bucket.get("doc_count"),
            "error_type": sample.get("error", {}).get("type"),
            "sample_trace_id": sample.get("trace", {}).get("id")
        })

    # Step 3: Classify root cause
    root_cause = "unknown"
    if patterns:
        # Classify based on most common pattern
        top_pattern = patterns[0]
        root_cause = classify_root_cause(
            top_pattern.get("message", ""),
            top_pattern.get("error_type")
        )

    # Step 4: Generate analysis report
    analysis = {
        "total_errors": total_errors,
        "patterns": patterns,
        "root_cause": root_cause,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    print(f"Analysis complete: {total_errors} errors, {len(patterns)} patterns, root cause: {root_cause}", file=sys.stderr)

    # Step 5: Send analysis event to observability server
    await send_analysis_event({
        "source_app": "error-analysis-agent",
        "session_id": alert_data.get("alert_id", f"analysis-{datetime.utcnow().timestamp()}"),
        "hook_event_type": "ErrorAnalysisComplete",
        "payload": {
            "alert_id": alert_data.get("alert_id"),
            "service": alert_data.get("service"),
            "total_errors": total_errors,
            "pattern_count": len(patterns),
            "root_cause": root_cause,
            "analysis": analysis
        }
    })

    # Step 6: Create Linear issue automatically (Phase 3)
    linear_issue = None
    linear_issue_url = None

    if LINEAR_API_KEY:
        print("Creating Linear issue automatically...", file=sys.stderr)

        # Get team ID
        team_id = await get_linear_team_id("DEV")

        if team_id:
            linear_issue_data = {
                "title": f"[{root_cause.upper()}] {alert_data.get('service', 'Unknown')}: {alert_data.get('alert_name', 'Error spike detected')}",
                "description": generate_linear_issue_description(alert_data, analysis),
                "team_id": team_id,
                "priority": 2 if alert_data.get("severity") == "high" else 3,
                # Note: Would need to look up label IDs for automatic labeling
                # For now, just create the issue without labels (can add manually)
            }

            linear_issue = await create_linear_issue(linear_issue_data)
            if linear_issue:
                linear_issue_url = linear_issue.get("url")
    else:
        print("Skipping Linear issue creation (LINEAR_API_KEY not set)", file=sys.stderr)

    # Step 7: Store in knowledge base (Phase 3)
    if linear_issue_url and patterns:
        # Store the top pattern with solution
        top_pattern = patterns[0] if patterns else None
        if top_pattern:
            await store_in_knowledge_base({
                "alert_id": alert_data.get("alert_id"),
                "error_type": top_pattern.get("error_type"),
                "service": alert_data.get("service"),
                "message": top_pattern.get("message"),
                "root_cause": root_cause,
                "occurrences": top_pattern.get("count", 0),
                "solution": f"See Linear issue for investigation and resolution",
                "prevention": f"Refer to Linear issue {linear_issue.get('identifier')} for prevention strategy",
                "linear_issue_url": linear_issue_url
            })

    # Return results
    actions_taken = []
    if linear_issue:
        actions_taken.append(f"Created Linear issue: {linear_issue.get('identifier')}")
    if patterns:
        actions_taken.append("Stored error pattern in knowledge base")

    return {
        "success": True,
        "alert_id": alert_data.get("alert_id"),
        "analysis": analysis,
        "linear_issue": linear_issue,
        "linear_issue_url": linear_issue_url,
        "actions_taken": actions_taken if actions_taken else [
            "Analysis complete (LINEAR_API_KEY not set for automatic issue creation)"
        ]
    }


# ============================================================================
# CLI
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description="Trigger error analysis from Kibana alert"
    )
    parser.add_argument(
        "--alert-json",
        type=str,
        help="Alert data as JSON string"
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)"
    )

    args = parser.parse_args()

    # Get alert data from argument or stdin
    if args.alert_json:
        try:
            alert_data = json.loads(args.alert_json)
        except json.JSONDecodeError as e:
            print(f"Error parsing alert JSON: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        try:
            alert_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"Error parsing alert JSON from stdin: {e}", file=sys.stderr)
            sys.exit(1)

    # Run analysis
    try:
        result = await analyze_alert(alert_data)

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            print(f"\nError Analysis Results:")
            print(f"  Success: {result.get('success')}")
            print(f"  Alert ID: {result.get('alert_id')}")
            if result.get('success'):
                print(f"  Total Errors: {result['analysis']['total_errors']}")
                print(f"  Patterns Found: {len(result['analysis']['patterns'])}")
                print(f"  Root Cause: {result['analysis']['root_cause']}")
                print(f"\nLinear Issue:")
                print(f"  Title: {result['linear_issue_data']['title']}")
                print(f"  Labels: {', '.join(result['linear_issue_data']['labels'])}")
            else:
                print(f"  Error: {result.get('error')}")

        sys.exit(0 if result.get("success") else 1)

    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
