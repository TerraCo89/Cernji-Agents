#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "fastmcp>=2.0",
#   "pyyaml>=6.0",
#   "httpx>=0.28.0",
#   "sqlmodel>=0.0.22",
#   "python-dotenv>=1.0.0",
# ]
# requires-python = ">=3.10"
# ///

"""
Test job application MCP tools (file-based).

These tools remain file-based by design as job applications are
write-once artifacts that work well as files.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up environment
os.environ["STORAGE_BACKEND"] = "sqlite"
os.environ["SQLITE_DATABASE_PATH"] = "./data/resume_agent.db"
os.environ["USER_ID"] = "default"

from resume_agent_langgraph import (
    data_list_applications,
    data_read_job_analysis,
    data_get_application_path,
)


def test_list_applications():
    """Test listing job applications."""
    print("\n" + "="*60)
    print("TEST: List Applications")
    print("="*60)

    result = data_list_applications(limit=5)

    if result["status"] == "success":
        apps = result["applications"]
        print(f"✅ Found {len(apps)} applications")

        for i, app in enumerate(apps, 1):
            print(f"\n   {i}. {app['company']} - {app['role']}")
            print(f"      Files: {', '.join([k for k, v in app['files'].items() if v])}")

        return True, apps
    else:
        print(f"❌ Error: {result.get('error')}")
        return False, []


def test_read_job_analysis(company, job_title):
    """Test reading job analysis."""
    print("\n" + "="*60)
    print("TEST: Read Job Analysis")
    print("="*60)
    print(f"   Company: {company}")
    print(f"   Role: {job_title}")

    result = data_read_job_analysis(company, job_title)

    if result["status"] == "success":
        data = result["data"]
        print(f"✅ Job analysis loaded")
        print(f"   URL: {data.get('url', 'N/A')[:60]}...")
        print(f"   Location: {data.get('location', 'N/A')}")
        print(f"   Keywords: {len(data.get('keywords', []))}")
        print(f"   Required qualifications: {len(data.get('required_qualifications', []))}")
        return True
    else:
        print(f"❌ Error: {result.get('error')}")
        return False


def test_get_application_path(company, job_title):
    """Test getting application path."""
    print("\n" + "="*60)
    print("TEST: Get Application Path")
    print("="*60)
    print(f"   Company: {company}")
    print(f"   Role: {job_title}")

    result = data_get_application_path(company, job_title)

    if result["status"] == "success":
        print(f"✅ Path retrieved")
        print(f"   Directory: {result['directory']}")
        print(f"   Exists: {result['exists']}")
        return True
    else:
        print(f"❌ Error: {result.get('error')}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Job Application Tools Tests (File-Based)")
    print("="*60)

    tests_passed = []

    # Test 1: List applications
    passed, apps = test_list_applications()
    tests_passed.append(("List Applications", passed))

    # Test 2 & 3: If we have applications, test reading them
    if apps:
        first_app = apps[0]
        company = first_app["company"]
        job_title = first_app["role"]

        passed = test_read_job_analysis(company, job_title)
        tests_passed.append(("Read Job Analysis", passed))

        passed = test_get_application_path(company, job_title)
        tests_passed.append(("Get Application Path", passed))
    else:
        print("\n⚠️  No applications found, skipping read tests")

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for name, passed in tests_passed:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, p in tests_passed if p)
    total_count = len(tests_passed)

    print(f"\nPassed: {passed_count}/{total_count}")

    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())