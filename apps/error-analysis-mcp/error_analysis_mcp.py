#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#     "fastmcp>=2.0",
#     "httpx>=0.28.0",
#     "python-dotenv>=1.0.0",
# ]
# requires-python = ">=3.10"
# ///

"""
Error Analysis MCP Server

Provides tools for querying Elasticsearch to analyze error patterns,
trends, and root causes from application logs.

Architecture:
- Single-file MCP server using FastMCP 2.0
- Queries Elasticsearch via HTTP REST API
- Supports ECS (Elastic Common Schema) log format
- Used by Error Analysis & Prevention Agent

Usage:
    # For Claude Desktop (stdio, no auth)
    uv run apps/error-analysis-mcp/error_analysis_mcp.py

    # For N8N / HTTP clients (streamable-http, no auth)
    uv run apps/error-analysis-mcp/error_analysis_mcp.py --transport streamable-http --port 8080

    # With authentication enabled
    export MCP_REQUIRE_AUTH=true
    export MCP_AUTH_TOKEN=your-secret-token-here
    uv run apps/error-analysis-mcp/error_analysis_mcp.py --transport streamable-http --port 8080

Configuration:
    ELASTICSEARCH_URL: Elasticsearch endpoint (default: http://localhost:9200)
    MCP_REQUIRE_AUTH: Enable authentication (true/false, default: false)
    MCP_AUTH_TOKEN: Bearer token for authentication (required if MCP_REQUIRE_AUTH=true)
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Literal
from collections import defaultdict

import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv


# Custom exception for authentication errors
class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

# Load environment variables
load_dotenv()

# Configuration
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_PATTERN = "logs-*"  # Search across all log indices

# Authentication Configuration
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")  # Bearer token for authentication
REQUIRE_AUTH = os.getenv("MCP_REQUIRE_AUTH", "false").lower() == "true"

# Initialize MCP server
mcp = FastMCP(
    name="error-analysis",
    instructions="Elasticsearch integration for error analysis and pattern detection"
)

# ============================================================================
# N8N Compatibility Middleware
# ============================================================================

@mcp.add_middleware
async def filter_n8n_metadata(request, call_next):
    """
    Strip N8N-specific metadata from tool calls.

    N8N MCP Client node (v1.118.2+) incorrectly includes protocol metadata
    (toolCallId, __fromNode) as tool parameters, causing Pydantic validation
    errors. This middleware removes known metadata fields.

    Reference: https://community.n8n.io/t/mcp-client-node-now-includes-toolcallid-in-tool-calls-bug/219307
    Linear Issue: DEV-249
    """
    if request.method == "POST" and request.url.path.endswith("/mcp"):
        try:
            body = await request.json()

            # Filter tools/call requests
            if body.get("method") == "tools/call":
                params = body.get("params", {})
                arguments = params.get("arguments", {})

                # Strip known N8N metadata fields
                n8n_metadata = ["toolCallId", "__fromNode", "__outputIndex"]
                for field in n8n_metadata:
                    arguments.pop(field, None)

                # Update request body
                params["arguments"] = arguments
                body["params"] = params

                # Reconstruct request with cleaned body
                from starlette.requests import Request
                scope = request.scope.copy()
                scope["body"] = json.dumps(body).encode()
                request = Request(scope)

        except Exception:
            # If filtering fails, pass through unchanged
            # (better to fail with original error than break middleware)
            pass

    response = await call_next(request)
    return response


# ============================================================================
# Authentication Middleware
# ============================================================================

def authenticate_request(headers: dict) -> bool:
    """
    Validate Bearer token authentication.

    Args:
        headers: Request headers dictionary

    Returns:
        True if authenticated, False otherwise

    Raises:
        AuthenticationError: If authentication fails when required
    """
    if not REQUIRE_AUTH:
        return True  # Authentication disabled

    if not MCP_AUTH_TOKEN:
        # Auth required but no token configured
        raise AuthenticationError("Server misconfigured: MCP_AUTH_TOKEN not set")

    # Get Authorization header
    auth_header = headers.get("authorization", "")

    if not auth_header:
        raise AuthenticationError("Missing Authorization header")

    # Check Bearer token format
    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("Invalid Authorization header format. Expected: Bearer <token>")

    # Extract and validate token
    provided_token = auth_header[7:]  # Remove "Bearer " prefix

    if provided_token != MCP_AUTH_TOKEN:
        raise AuthenticationError("Invalid authentication token")

    return True


@mcp.add_middleware
async def auth_middleware(request, call_next):
    """Authentication middleware for HTTP requests."""
    if REQUIRE_AUTH and request.url.path == "/mcp":
        # Extract headers from request
        headers = {key.lower(): value for key, value in request.headers.items()}
        try:
            authenticate_request(headers)
        except AuthenticationError as e:
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": str(e)
                    },
                    "id": None
                }
            )

    response = await call_next(request)
    return response


# ============================================================================
# Utility Functions
# ============================================================================

def parse_time_range(time_range: str) -> tuple[str, str]:
    """
    Parse time range string to Elasticsearch date math format.

    Examples:
        "15m" -> last 15 minutes
        "1h" -> last 1 hour
        "24h" -> last 24 hours
        "7d" -> last 7 days

    Returns:
        (gte, lte) tuple in ISO format
    """
    now = datetime.utcnow()

    # Parse time range
    if time_range.endswith('m'):
        delta = timedelta(minutes=int(time_range[:-1]))
    elif time_range.endswith('h'):
        delta = timedelta(hours=int(time_range[:-1]))
    elif time_range.endswith('d'):
        delta = timedelta(days=int(time_range[:-1]))
    else:
        # Default to 1 hour
        delta = timedelta(hours=1)

    gte = (now - delta).isoformat() + "Z"
    lte = now.isoformat() + "Z"

    return gte, lte


async def query_elasticsearch(query: dict, index: str = INDEX_PATTERN) -> dict:
    """Execute Elasticsearch query via HTTP REST API."""
    url = f"{ELASTICSEARCH_URL}/{index}/_search"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=query)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": str(e),
                "status": "failed",
                "message": f"Elasticsearch query failed: {e}"
            }


def format_error_result(hit: dict) -> dict:
    """Format Elasticsearch hit to user-friendly error object."""
    source = hit.get("_source", {})

    return {
        "timestamp": source.get("@timestamp"),
        "level": source.get("log", {}).get("level", "unknown"),
        "message": source.get("message", ""),
        "service": source.get("service", {}).get("name", "unknown"),
        "trace_id": source.get("trace", {}).get("id"),
        "host": source.get("host", {}).get("name"),
        "process_pid": source.get("process", {}).get("pid"),
        "error_type": source.get("error", {}).get("type"),
        "error_stack_trace": source.get("error", {}).get("stack_trace"),
        "index": hit.get("_index"),
        "score": hit.get("_score")
    }


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
async def search_errors(
    time_range: str = "1h",
    service: Optional[str] = None,
    log_level: Literal["error", "warn", "info", "debug", "all"] = "error",
    max_results: int = 100,
    toolCallId: Optional[str] = None  # N8N compatibility: accept but ignore toolCallId
) -> dict:
    """
    Search for errors in Elasticsearch logs.

    Args:
        time_range: Time range to search (e.g., "15m", "1h", "24h", "7d")
        service: Service name to filter by (e.g., "resume-agent", "japanese-tutor")
        log_level: Log level to filter by ("error", "warn", "info", "debug", "all")
        max_results: Maximum number of results to return (default: 100)

    Returns:
        Dictionary with:
        - total: Total number of errors found
        - errors: List of error objects
        - time_range: Queried time range
        - query_time_ms: Query execution time

    Example:
        search_errors(time_range="24h", service="resume-agent", log_level="error")
    """
    gte, lte = parse_time_range(time_range)

    # Build query
    query = {
        "size": max_results,
        "sort": [{"@timestamp": {"order": "desc"}}],
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": gte,
                                "lte": lte
                            }
                        }
                    }
                ],
                "filter": []
            }
        }
    }

    # Add service filter
    if service:
        query["query"]["bool"]["filter"].append({
            "term": {"service.name": service}
        })

    # Add log level filter
    if log_level != "all":
        query["query"]["bool"]["filter"].append({
            "term": {"log.level": log_level}
        })

    # Execute query
    result = await query_elasticsearch(query)

    if "error" in result:
        return result

    # Format results
    hits = result.get("hits", {}).get("hits", [])
    errors = [format_error_result(hit) for hit in hits]

    return {
        "total": result.get("hits", {}).get("total", {}).get("value", 0),
        "errors": errors,
        "time_range": {"gte": gte, "lte": lte},
        "query_time_ms": result.get("took", 0)
    }


@mcp.tool()
async def get_error_patterns(
    time_range: str = "24h",
    service: Optional[str] = None,
    min_occurrences: int = 2,
    max_patterns: int = 20,
    toolCallId: Optional[str] = None  # N8N compatibility: accept but ignore toolCallId
) -> dict:
    """
    Detect recurring error patterns by aggregating similar error messages.

    Groups errors by message similarity and identifies the most common patterns.
    Useful for finding systemic issues vs one-off errors.

    Args:
        time_range: Time range to analyze (e.g., "15m", "1h", "24h", "7d")
        service: Service name to filter by (optional)
        min_occurrences: Minimum number of occurrences to be considered a pattern
        max_patterns: Maximum number of patterns to return

    Returns:
        Dictionary with:
        - total_errors: Total number of errors analyzed
        - patterns: List of error patterns with occurrence counts
        - time_range: Analyzed time range

    Example:
        get_error_patterns(time_range="7d", service="resume-agent", min_occurrences=5)
    """
    gte, lte = parse_time_range(time_range)

    # Build aggregation query
    query = {
        "size": 0,  # Don't return individual hits
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": gte,
                                "lte": lte
                            }
                        }
                    },
                    {
                        "term": {"log.level": "error"}
                    }
                ],
                "filter": []
            }
        },
        "aggs": {
            "error_patterns": {
                "terms": {
                    "field": "message.keyword",
                    "size": max_patterns * 2,  # Get more for filtering
                    "min_doc_count": min_occurrences
                },
                "aggs": {
                    "sample_errors": {
                        "top_hits": {
                            "size": 1,
                            "_source": ["@timestamp", "service.name", "error.type", "trace.id"]
                        }
                    }
                }
            },
            "error_types": {
                "terms": {
                    "field": "error.type.keyword",
                    "size": 10
                }
            }
        }
    }

    # Add service filter
    if service:
        query["query"]["bool"]["filter"].append({
            "term": {"service.name": service}
        })

    # Execute query
    result = await query_elasticsearch(query)

    if "error" in result:
        return result

    # Format patterns
    patterns = []
    for bucket in result.get("aggregations", {}).get("error_patterns", {}).get("buckets", [])[:max_patterns]:
        sample = bucket.get("sample_errors", {}).get("hits", {}).get("hits", [{}])[0].get("_source", {})

        patterns.append({
            "message": bucket.get("key"),
            "occurrences": bucket.get("doc_count"),
            "error_type": sample.get("error", {}).get("type"),
            "service": sample.get("service", {}).get("name"),
            "last_seen": sample.get("@timestamp"),
            "sample_trace_id": sample.get("trace", {}).get("id")
        })

    # Format error types
    error_types = [
        {"type": bucket.get("key"), "count": bucket.get("doc_count")}
        for bucket in result.get("aggregations", {}).get("error_types", {}).get("buckets", [])
    ]

    return {
        "total_errors": result.get("hits", {}).get("total", {}).get("value", 0),
        "patterns": patterns,
        "error_types": error_types,
        "time_range": {"gte": gte, "lte": lte},
        "query_time_ms": result.get("took", 0)
    }


@mcp.tool()
async def get_error_context(
    trace_id: str,
    include_related: bool = True,
    toolCallId: Optional[str] = None  # N8N compatibility: accept but ignore toolCallId
) -> dict:
    """
    Get full context for an error using its trace ID (correlation ID).

    Retrieves the error and all related logs with the same trace ID,
    providing complete context for debugging.

    Args:
        trace_id: The trace/correlation ID to search for
        include_related: Whether to include related logs (non-error) with same trace ID

    Returns:
        Dictionary with:
        - error: The error log entry
        - related_logs: All logs with the same trace ID (if include_related=True)
        - total_related: Count of related log entries

    Example:
        get_error_context(trace_id="abc-123-def-456")
    """
    # Build query for error with trace ID
    query = {
        "size": 1,
        "sort": [{"@timestamp": {"order": "desc"}}],
        "query": {
            "bool": {
                "must": [
                    {"term": {"trace.id.keyword": trace_id}},
                    {"term": {"log.level": "error"}}
                ]
            }
        }
    }

    # Get the error
    error_result = await query_elasticsearch(query)

    if "error" in error_result:
        return error_result

    error_hits = error_result.get("hits", {}).get("hits", [])
    if not error_hits:
        return {
            "error": None,
            "message": f"No error found with trace_id: {trace_id}"
        }

    error = format_error_result(error_hits[0])

    # Get related logs if requested
    related_logs = []
    if include_related:
        related_query = {
            "size": 100,
            "sort": [{"@timestamp": {"order": "asc"}}],
            "query": {
                "bool": {
                    "must": [
                        {"term": {"trace.id.keyword": trace_id}}
                    ],
                    "must_not": [
                        {"term": {"log.level": "error"}}
                    ]
                }
            }
        }

        related_result = await query_elasticsearch(related_query)

        if "error" not in related_result:
            related_hits = related_result.get("hits", {}).get("hits", [])
            related_logs = [format_error_result(hit) for hit in related_hits]

    return {
        "error": error,
        "related_logs": related_logs,
        "total_related": len(related_logs)
    }


@mcp.tool()
async def analyze_error_trend(
    service: str,
    time_range: str = "24h",
    interval: Literal["1m", "5m", "15m", "1h", "1d"] = "1h",
    toolCallId: Optional[str] = None  # N8N compatibility: accept but ignore toolCallId
) -> dict:
    """
    Analyze error rate trends over time for a service.

    Creates a time-series histogram of error counts to identify spikes,
    patterns, and trends.

    Args:
        service: Service name to analyze (e.g., "resume-agent")
        time_range: Time range to analyze (e.g., "24h", "7d", "30d")
        interval: Histogram bucket interval ("1m", "5m", "15m", "1h", "1d")

    Returns:
        Dictionary with:
        - service: Service name
        - total_errors: Total errors in time range
        - histogram: Time-series data points
        - peak_error_time: Time with highest error count
        - trend: "increasing", "decreasing", or "stable"

    Example:
        analyze_error_trend(service="resume-agent", time_range="7d", interval="1h")
    """
    gte, lte = parse_time_range(time_range)

    # Build histogram query
    query = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": gte,
                                "lte": lte
                            }
                        }
                    },
                    {"term": {"service.name": service}},
                    {"term": {"log.level": "error"}}
                ]
            }
        },
        "aggs": {
            "errors_over_time": {
                "date_histogram": {
                    "field": "@timestamp",
                    "fixed_interval": interval,
                    "min_doc_count": 0
                }
            }
        }
    }

    # Execute query
    result = await query_elasticsearch(query)

    if "error" in result:
        return result

    # Format histogram
    buckets = result.get("aggregations", {}).get("errors_over_time", {}).get("buckets", [])
    histogram = [
        {
            "timestamp": bucket.get("key_as_string", bucket.get("key")),
            "error_count": bucket.get("doc_count")
        }
        for bucket in buckets
    ]

    # Find peak
    peak = max(histogram, key=lambda x: x["error_count"]) if histogram else None

    # Calculate trend (simple: compare first half vs second half)
    if len(histogram) >= 4:
        mid = len(histogram) // 2
        first_half_avg = sum(h["error_count"] for h in histogram[:mid]) / mid
        second_half_avg = sum(h["error_count"] for h in histogram[mid:]) / (len(histogram) - mid)

        if second_half_avg > first_half_avg * 1.2:
            trend = "increasing"
        elif second_half_avg < first_half_avg * 0.8:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    return {
        "service": service,
        "total_errors": result.get("hits", {}).get("total", {}).get("value", 0),
        "histogram": histogram,
        "peak_error_time": peak,
        "trend": trend,
        "time_range": {"gte": gte, "lte": lte},
        "interval": interval
    }


@mcp.tool()
async def compare_errors(
    trace_id_1: str,
    trace_id_2: str,
    toolCallId: Optional[str] = None  # N8N compatibility: accept but ignore toolCallId
) -> dict:
    """
    Compare two errors to find similarities and differences.

    Useful for identifying if errors are related or have common root causes.

    Args:
        trace_id_1: First error's trace ID
        trace_id_2: Second error's trace ID

    Returns:
        Dictionary with:
        - error_1: First error details
        - error_2: Second error details
        - similarities: Common attributes
        - differences: Different attributes

    Example:
        compare_errors(trace_id_1="abc-123", trace_id_2="def-456")
    """
    # Get both errors
    error1_result = await get_error_context(trace_id_1, include_related=False)
    error2_result = await get_error_context(trace_id_2, include_related=False)

    if error1_result.get("error") is None or error2_result.get("error") is None:
        return {
            "error": "One or both errors not found",
            "error_1": error1_result.get("error"),
            "error_2": error2_result.get("error")
        }

    error1 = error1_result["error"]
    error2 = error2_result["error"]

    # Find similarities and differences
    similarities = {}
    differences = {}

    keys_to_compare = ["service", "error_type", "level", "host"]

    for key in keys_to_compare:
        val1 = error1.get(key)
        val2 = error2.get(key)

        if val1 == val2 and val1 is not None:
            similarities[key] = val1
        elif val1 != val2:
            differences[key] = {"error_1": val1, "error_2": val2}

    # Compare messages (fuzzy match)
    msg1 = error1.get("message", "")
    msg2 = error2.get("message", "")

    if msg1 == msg2:
        similarities["message_match"] = "exact"
    elif any(word in msg2 for word in msg1.split()[:3]):
        similarities["message_match"] = "partial"
    else:
        similarities["message_match"] = "none"

    return {
        "error_1": error1,
        "error_2": error2,
        "similarities": similarities,
        "differences": differences,
        "likely_related": len(similarities) > len(differences)
    }


@mcp.tool()
async def health_check() -> dict:
    """
    Check Elasticsearch connection health.

    Returns:
        Dictionary with:
        - status: "healthy" or "unhealthy"
        - elasticsearch_url: Configured Elasticsearch URL
        - cluster_info: Elasticsearch cluster information
    """
    url = f"{ELASTICSEARCH_URL}/"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            cluster_info = response.json()

            return {
                "status": "healthy",
                "elasticsearch_url": ELASTICSEARCH_URL,
                "cluster_info": {
                    "name": cluster_info.get("name"),
                    "version": cluster_info.get("version", {}).get("number"),
                    "tagline": cluster_info.get("tagline")
                }
            }
        except httpx.HTTPError as e:
            return {
                "status": "unhealthy",
                "elasticsearch_url": ELASTICSEARCH_URL,
                "error": str(e)
            }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Error Analysis MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio for Claude Desktop, use streamable-http for N8N)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP server (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for HTTP server (default: 8080)"
    )

    args = parser.parse_args()

    print(f"Starting Error Analysis MCP Server")
    print(f"Transport: {args.transport}")

    if args.transport == "streamable-http":
        print(f"HTTP Server: http://{args.host}:{args.port}/mcp")

        # Show authentication status
        if REQUIRE_AUTH:
            if MCP_AUTH_TOKEN:
                print(f"Authentication: ENABLED (Bearer token required)")
            else:
                print(f"WARNING: Authentication required but MCP_AUTH_TOKEN not set!")
        else:
            print(f"Authentication: DISABLED (development mode)")

        print(f"N8N Connection URL: http://{args.host}:{args.port}/mcp")

        if REQUIRE_AUTH and MCP_AUTH_TOKEN:
            print(f"N8N Authorization Header: Bearer {MCP_AUTH_TOKEN[:8]}...{MCP_AUTH_TOKEN[-8:]}")

        mcp.run(transport=args.transport, host=args.host, port=args.port)
    else:
        print("STDIO mode for Claude Desktop")
        print("Authentication: N/A (stdio transport)")
        mcp.run(transport=args.transport)
