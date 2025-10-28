"""
Quick test script for the Cookpad job posting scraper.

This script tests the improved Japan Dev scraper on the specific Cookpad
Conversational AI Engineer job posting.

Usage:
    uv run python test_cookpad_scraper.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for direct import
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import browser automation module directly (avoid __init__.py with old imports)
from resume_agent.tools.browser_automation import scrape_japan_dev_job


async def test_cookpad_job():
    """Test scraping the Cookpad Conversational AI Engineer posting."""

    url = "https://japan-dev.com/jobs/cookpad/cookpad-conversational-ai-engineermoment-076di1"

    print("=" * 80)
    print("Testing Japan Dev Scraper on Cookpad Job")
    print("=" * 80)
    print(f"URL: {url}")
    print("\nStarting scrape... (this may take 30-60 seconds)\n")

    try:
        job_data = await scrape_japan_dev_job(url)

        print("\n" + "=" * 80)
        print("FINAL EXTRACTED JOB DATA")
        print("=" * 80)
        print(f"Job Title: {job_data.get('job_title', 'NOT FOUND')}")
        print(f"Company: {job_data.get('company_name', 'NOT FOUND')}")
        print(f"Location: {job_data.get('location', 'NOT FOUND')}")
        print(f"Employment Type: {job_data.get('employment_type', 'NOT FOUND')}")
        print(f"\n🎯 SALARY: {job_data.get('salary_range', 'NOT FOUND')}")
        print(f"\nApplication: {job_data.get('application_url', 'NOT FOUND')}")
        print(f"Posted: {job_data.get('posted_date', 'NOT FOUND')}")

        if job_data.get('requirements'):
            print(f"\nRequirements ({len(job_data['requirements'])} found):")
            for i, req in enumerate(job_data['requirements'][:5], 1):
                print(f"  {i}. {req}")
            if len(job_data['requirements']) > 5:
                print(f"  ... and {len(job_data['requirements']) - 5} more")

        print("\n" + "=" * 80)

        # Validate salary was found
        if job_data.get('salary_range'):
            print("✅ SUCCESS: Salary information was extracted!")
        else:
            print("❌ FAILURE: Salary information was NOT extracted")
            print("Check the DEBUG output above to see what the LLM extracted")

        return job_data

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_cookpad_job())
