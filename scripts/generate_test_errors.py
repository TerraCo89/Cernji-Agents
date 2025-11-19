#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#     "httpx>=0.28.0",
# ]
# requires-python = ">=3.10"
# ///

"""
Generate realistic test errors for ELK stack testing.

This script creates various error patterns in Elasticsearch to test
the automatic error analysis system.
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import random

ELASTICSEARCH_URL = "http://localhost:9200"
SERVICE_NAME = "resume-agent"

# Error patterns to simulate
ERROR_PATTERNS = [
    {
        "type": "ModuleNotFoundError",
        "message": "ModuleNotFoundError: No module named 'fastmcp'",
        "category": "configuration",
        "count": 8
    },
    {
        "type": "TypeError",
        "message": "TypeError: 'NoneType' object has no attribute 'invoke'",
        "category": "documentation",
        "count": 5
    },
    {
        "type": "ConnectionError",
        "message": "ConnectionError: Failed to connect to Elasticsearch at localhost:9200",
        "category": "configuration",
        "count": 3
    },
    {
        "type": "AttributeError",
        "message": "AttributeError: 'dict' object has no attribute 'get_error_context'",
        "category": "documentation",
        "count": 6
    },
    {
        "type": "TimeoutError",
        "message": "TimeoutError: Agent execution timed out after 30 seconds",
        "category": "agent_scope",
        "count": 2
    }
]


async def create_error_log(error_pattern: dict, index: int, base_time: datetime) -> dict:
    """Create a single error log entry in ECS format."""
    # Vary timestamp slightly for each error
    timestamp = base_time - timedelta(minutes=random.randint(1, 10))

    return {
        "@timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "log": {
            "level": "error",
            "file": {
                "path": "/app/resume_agent.py"
            }
        },
        "message": error_pattern["message"],
        "service": {
            "name": SERVICE_NAME,
            "type": "python"
        },
        "error": {
            "type": error_pattern["type"],
            "stack_trace": f"  File \"/app/resume_agent.py\", line {100 + index}\n    {error_pattern['message']}"
        },
        "trace": {
            "id": f"trace-{SERVICE_NAME}-{random.randint(1000, 9999)}"
        },
        "host": {
            "name": "test-host"
        },
        "process": {
            "pid": random.randint(10000, 99999)
        },
        "ecs": {
            "version": "8.11.0"
        }
    }


async def index_error_logs():
    """Index all test error logs into Elasticsearch."""
    base_time = datetime.now()
    index_name = f"logs-{SERVICE_NAME}-{base_time.strftime('%Y.%m.%d')}"

    print(f"Generating test errors for index: {index_name}")
    print(f"Service: {SERVICE_NAME}")
    print(f"Base time: {base_time.isoformat()}")
    print()

    total_errors = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for pattern in ERROR_PATTERNS:
            print(f"Generating {pattern['count']} × {pattern['type']} errors...")

            for i in range(pattern['count']):
                error_log = await create_error_log(pattern, i, base_time)

                # Index the document
                try:
                    response = await client.post(
                        f"{ELASTICSEARCH_URL}/{index_name}/_doc",
                        json=error_log
                    )
                    response.raise_for_status()
                    total_errors += 1

                except httpx.HTTPError as e:
                    print(f"Error indexing document: {e}")
                    return False

            print(f"  [OK] Created {pattern['count']} {pattern['type']} errors")

    print()
    print(f"[SUCCESS] Created {total_errors} test errors in Elasticsearch")
    print(f"Index: {index_name}")
    print()
    print("Error pattern summary:")
    for pattern in ERROR_PATTERNS:
        print(f"  - {pattern['type']}: {pattern['count']} errors ({pattern['category']})")

    return True


async def verify_indexing():
    """Verify errors were indexed successfully."""
    print("\nVerifying errors are indexed...")

    # Wait a moment for Elasticsearch to refresh
    await asyncio.sleep(2)

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{ELASTICSEARCH_URL}/logs-{SERVICE_NAME}-*/_search",
                json={
                    "size": 0,
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"log.level": "error"}},
                                {"term": {"service.name": SERVICE_NAME}}
                            ]
                        }
                    },
                    "aggs": {
                        "error_types": {
                            "terms": {
                                "field": "error.type.keyword",
                                "size": 10
                            }
                        }
                    }
                }
            )
            response.raise_for_status()
            result = response.json()

            total = result.get("hits", {}).get("total", {}).get("value", 0)
            print(f"[OK] Found {total} total errors in Elasticsearch")

            error_types = result.get("aggregations", {}).get("error_types", {}).get("buckets", [])
            if error_types:
                print("\nError types found:")
                for bucket in error_types:
                    print(f"  - {bucket['key']}: {bucket['doc_count']} occurrences")

            return True

        except httpx.HTTPError as e:
            print(f"[ERROR] Error verifying indexing: {e}")
            return False


async def main():
    print("=" * 60)
    print("Test Error Generator for Error Analysis System")
    print("=" * 60)
    print()

    # Generate and index errors
    success = await index_error_logs()

    if not success:
        print("\n[FAILED] Failed to generate test errors")
        return

    # Verify indexing
    await verify_indexing()

    print()
    print("=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print()
    print("1. Wait ~5 seconds for Elasticsearch to fully index the errors")
    print()
    print("2. Send webhook to trigger automatic analysis:")
    print('   curl -X POST "http://localhost:4000/alerts/trigger" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"alert_id":"test-with-real-errors","alert_name":"High Error Rate","service":"resume-agent","error_count":24,"severity":"high","time_range":"15m"}\'')
    print()
    print("3. Watch observability server logs for analysis results!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
