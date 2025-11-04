#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Architecture Validation Script (DEV-53)

Validates that all databases follow the app-specific architecture pattern:
- apps/{app-name}/data/{app-name}.db

Detects:
- Orphaned databases at root level (data/*.db except events.db)
- MCP configs pointing to wrong paths
- Apps without initialized databases
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Set console encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout.reconfigure(encoding='utf-8')

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg: str):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")

def print_error(msg: str):
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}")

def print_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")

def find_orphaned_databases(project_root: Path) -> List[Path]:
    """
    Find orphaned database files at root level.

    Exceptions:
    - data/events.db (shared observability database)
    - data/*_backup_*.db (backup files)
    """
    data_dir = project_root / "data"
    if not data_dir.exists():
        return []

    orphaned = []
    for db_file in data_dir.glob("*.db"):
        # Skip allowed shared databases
        if db_file.name == "events.db":
            continue
        # Skip backup files
        if "_backup_" in db_file.name:
            continue

        orphaned.append(db_file)

    return orphaned

def validate_app_databases(project_root: Path) -> Dict[str, Dict]:
    """
    Validate that each app has its database in the correct location.

    Expected patterns:
    - apps/resume-agent/data/resume_agent.db
    - apps/japanese-tutor/src/data/japanese_agent.db
    - apps/resume-agent-langgraph/data/resume_agent.db

    Returns:
        Dict mapping app names to validation results
    """
    apps_dir = project_root / "apps"
    results = {}

    # Define expected database locations for each app
    expected_databases = {
        "resume-agent": "data/resume_agent.db",
        "japanese-tutor": "src/data/japanese_agent.db",
        "resume-agent-langgraph": "data/resume_agent.db",
    }

    for app_name, db_path in expected_databases.items():
        app_dir = apps_dir / app_name
        if not app_dir.exists():
            results[app_name] = {
                "status": "app_not_found",
                "message": f"App directory not found: {app_dir}"
            }
            continue

        db_file = app_dir / db_path
        results[app_name] = {
            "status": "ok" if db_file.exists() else "missing",
            "path": db_file,
            "exists": db_file.exists(),
            "message": f"Database {'found' if db_file.exists() else 'missing'} at {db_file.relative_to(project_root)}"
        }

    return results

def validate_mcp_configs(project_root: Path) -> List[Dict]:
    """
    Validate MCP configuration files point to correct database paths.

    Checks:
    - .mcp.json (root level)
    - apps/*/. mcp.json (app level)

    Returns:
        List of issues found in MCP configurations
    """
    issues = []

    # Check root .mcp.json
    root_mcp = project_root / ".mcp.json"
    if root_mcp.exists():
        try:
            with open(root_mcp) as f:
                config = json.load(f)

            # Check sqlite-resume server
            if "mcpServers" in config and "sqlite-resume" in config["mcpServers"]:
                args = config["mcpServers"]["sqlite-resume"].get("args", [])
                for arg in args:
                    if "resume_agent.db" in arg:
                        expected = "apps\\resume-agent\\data\\resume_agent.db"
                        if arg != expected and "resume_agent.db" in arg:
                            issues.append({
                                "file": str(root_mcp.relative_to(project_root)),
                                "server": "sqlite-resume",
                                "current": arg,
                                "expected": expected,
                                "message": "MCP config points to incorrect database path"
                            })
                        break

            # Check sqlite-japanese server
            if "mcpServers" in config and "sqlite-japanese" in config["mcpServers"]:
                args = config["mcpServers"]["sqlite-japanese"].get("args", [])
                for arg in args:
                    if "japanese_agent.db" in arg:
                        expected = "apps\\japanese-tutor\\src\\data\\japanese_agent.db"
                        if arg != expected and "japanese_agent.db" in arg:
                            issues.append({
                                "file": str(root_mcp.relative_to(project_root)),
                                "server": "sqlite-japanese",
                                "current": arg,
                                "expected": expected,
                                "message": "MCP config points to incorrect database path"
                            })
                        break

        except json.JSONDecodeError as e:
            issues.append({
                "file": str(root_mcp.relative_to(project_root)),
                "message": f"Invalid JSON: {e}"
            })

    return issues

def main():
    """Run all database architecture validations."""
    project_root = Path(__file__).resolve().parent.parent

    print(f"\n{Colors.BOLD}Database Architecture Validation (DEV-53){Colors.RESET}\n")
    print(f"Project root: {project_root}\n")

    all_passed = True

    # 1. Check for orphaned databases
    print(f"{Colors.BOLD}1. Checking for orphaned databases at root level...{Colors.RESET}")
    orphaned = find_orphaned_databases(project_root)
    if orphaned:
        all_passed = False
        print_error(f"Found {len(orphaned)} orphaned database(s):")
        for db in orphaned:
            print(f"   - {db.relative_to(project_root)}")
        print(f"\n   {Colors.YELLOW}Action:{Colors.RESET} Delete these files or move to app-specific locations\n")
    else:
        print_success("No orphaned databases found\n")

    # 2. Validate app-specific databases
    print(f"{Colors.BOLD}2. Validating app-specific database locations...{Colors.RESET}")
    app_results = validate_app_databases(project_root)
    for app_name, result in app_results.items():
        if result["status"] == "ok":
            print_success(f"{app_name}: {result['message']}")
        elif result["status"] == "missing":
            all_passed = False
            print_error(f"{app_name}: {result['message']}")
        elif result["status"] == "app_not_found":
            print_warning(f"{app_name}: {result['message']}")
    print()

    # 3. Validate MCP configurations
    print(f"{Colors.BOLD}3. Validating MCP configurations...{Colors.RESET}")
    mcp_issues = validate_mcp_configs(project_root)
    if mcp_issues:
        all_passed = False
        print_error(f"Found {len(mcp_issues)} MCP configuration issue(s):")
        for issue in mcp_issues:
            print(f"   File: {issue['file']}")
            if "server" in issue:
                print(f"   Server: {issue['server']}")
                print(f"   Current:  {issue['current']}")
                print(f"   Expected: {issue['expected']}")
            print(f"   {issue['message']}\n")
    else:
        print_success("MCP configurations are correct\n")

    # Summary
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    if all_passed:
        print_success(f"{Colors.BOLD}All validations passed!{Colors.RESET}")
        print_info("Database architecture follows DEV-53 standards.")
        return 0
    else:
        print_error(f"{Colors.BOLD}Validation failed!{Colors.RESET}")
        print_info("Please fix the issues above and re-run this script.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
