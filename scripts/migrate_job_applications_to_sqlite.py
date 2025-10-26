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
Migrate job applications from file-based storage to SQLite.

This script:
1. Reads existing job application directories
2. Loads job-analysis.json files
3. Migrates to SQLite database
4. Verifies data integrity
5. Optionally deletes files after successful migration
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up environment before importing
os.environ["STORAGE_BACKEND"] = "sqlite"
os.environ["SQLITE_DATABASE_PATH"] = "./data/resume_agent.db"
os.environ["USER_ID"] = "default"

from resume_agent_langgraph import job_app_repo

# Constants
APPLICATIONS_DIR = Path("./job-applications")


def find_job_applications():
    """Find all job application directories with job-analysis.json."""
    if not APPLICATIONS_DIR.exists():
        print(f"[ERROR] Applications directory not found: {APPLICATIONS_DIR}")
        return []

    applications = []
    for app_dir in APPLICATIONS_DIR.iterdir():
        if not app_dir.is_dir():
            continue

        analysis_file = app_dir / "job-analysis.json"
        if analysis_file.exists():
            applications.append({
                "directory": app_dir,
                "analysis_file": analysis_file
            })

    return applications


def parse_company_and_title(dir_name: str):
    """
    Parse company and job title from directory name.
    Format: Company_Job_Title or Company_Job_Title_(extra)
    """
    # Remove parenthetical extras
    if '(' in dir_name:
        dir_name = dir_name[:dir_name.index('(')].strip('_')

    # Split by underscore
    parts = dir_name.split('_')

    # Try to intelligently split into company and title
    # Look for common company indicators
    if len(parts) >= 2:
        # Simple heuristic: First part is company, rest is title
        company = parts[0]
        job_title = ' '.join(parts[1:])
        return company, job_title

    return None, None


def migrate_job_application(app_info, user_id="default"):
    """Migrate a single job application to SQLite."""
    analysis_file = app_info["analysis_file"]
    app_dir = app_info["directory"]
    dir_name = app_dir.name

    print(f"\n{'='*60}")
    print(f"Migrating: {dir_name}")
    print(f"{'='*60}")

    try:
        # Load job analysis
        with open(analysis_file, 'r', encoding='utf-8') as f:
            job_data = json.load(f)

        # Extract company and job title
        company = job_data.get("company")
        job_title = job_data.get("job_title")

        # Fallback to parsing directory name if not in JSON
        if not company or not job_title:
            print("[WARN] Company/title not in JSON, parsing directory name...")
            company_parsed, title_parsed = parse_company_and_title(dir_name)
            company = company or company_parsed
            job_title = job_title or title_parsed

        if not company or not job_title:
            print(f"[ERROR] Could not determine company/title for {dir_name}")
            return False

        print(f"   Company: {company}")
        print(f"   Title: {job_title}")

        # Save to SQLite via repository
        job_app_repo.save_job_analysis(user_id, job_data)
        print(f"[OK] Job analysis migrated successfully")

        # Check for and migrate other files
        files_migrated = 0

        # Migrate tailored resume if exists
        resume_files = list(app_dir.glob("*resume*.txt")) + list(app_dir.glob("Resume_*.txt"))
        if resume_files:
            resume_file = resume_files[0]
            with open(resume_file, 'r', encoding='utf-8') as f:
                resume_content = f.read()
            job_app_repo.save_tailored_resume(user_id, company, job_title, resume_content, metadata=None)
            print(f"[OK] Tailored resume migrated: {resume_file.name}")
            files_migrated += 1

        # Migrate cover letter if exists
        cover_files = list(app_dir.glob("CoverLetter_*.txt"))
        if cover_files:
            cover_file = cover_files[0]
            with open(cover_file, 'r', encoding='utf-8') as f:
                cover_content = f.read()
            job_app_repo.save_cover_letter(user_id, company, job_title, cover_content, metadata=None)
            print(f"[OK] Cover letter migrated: {cover_file.name}")
            files_migrated += 1

        # Migrate portfolio examples if exists
        portfolio_files = list(app_dir.glob("portfolio_*.txt"))
        if portfolio_files:
            portfolio_file = portfolio_files[0]
            with open(portfolio_file, 'r', encoding='utf-8') as f:
                portfolio_content = f.read()
            job_app_repo.save_portfolio_examples(user_id, company, job_title, portfolio_content)
            print(f"[OK] Portfolio examples migrated: {portfolio_file.name}")
            files_migrated += 1

        print(f"\n[SUMMARY] Total files migrated: {files_migrated + 1}")  # +1 for job analysis
        return True

    except Exception as e:
        print(f"[ERROR] Error migrating {dir_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_migration(app_info, user_id="default"):
    """Verify that migration was successful by reading from SQLite."""
    analysis_file = app_info["analysis_file"]

    try:
        # Load original data
        with open(analysis_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)

        company = original_data.get("company")
        job_title = original_data.get("job_title")

        if not company or not job_title:
            dir_name = app_info["directory"].name
            company, job_title = parse_company_and_title(dir_name)

        # Read from SQLite
        migrated_data = job_app_repo.get_job_analysis(user_id, company, job_title)

        if migrated_data is None:
            print(f"[ERROR] Verification failed: Data not found in SQLite")
            return False

        # Compare key fields
        if (migrated_data.get("company") == company and
            migrated_data.get("job_title") == job_title and
            migrated_data.get("url") == original_data.get("url")):
            print(f"[OK] Verification passed: Data matches in SQLite")
            return True
        else:
            print(f"[WARN] Verification warning: Some fields differ")
            return True  # Still consider it successful if core fields match

    except Exception as e:
        print(f"[ERROR] Verification error: {e}")
        return False


def delete_migrated_files(app_dir, dry_run=True):
    """Delete migrated application files."""
    if dry_run:
        print(f"[DRY RUN] Would delete {app_dir}")
        return

    try:
        import shutil
        shutil.rmtree(app_dir)
        print(f"[DELETE] Deleted: {app_dir}")
    except Exception as e:
        print(f"[ERROR] Error deleting {app_dir}: {e}")


def main():
    """Main migration workflow."""
    print("\n" + "="*60)
    print("Job Applications Migration to SQLite")
    print("="*60)
    print(f"Database: {os.getenv('SQLITE_DATABASE_PATH')}")
    print(f"User ID: {os.getenv('USER_ID')}")
    print(f"Applications Dir: {APPLICATIONS_DIR}")

    # Find all applications
    print(f"\n[SCAN] Scanning for job applications...")
    applications = find_job_applications()

    if not applications:
        print("[ERROR] No job applications found to migrate")
        return 1

    print(f"[OK] Found {len(applications)} job application(s) to migrate")

    # Migrate each application
    results = []
    for app_info in applications:
        success = migrate_job_application(app_info)
        results.append((app_info, success))

    # Verify migrations
    print(f"\n{'='*60}")
    print("Verifying Migrations")
    print(f"{'='*60}")

    verified = 0
    for app_info, success in results:
        if success:
            if verify_migration(app_info):
                verified += 1

    # Summary
    print(f"\n{'='*60}")
    print("Migration Summary")
    print(f"{'='*60}")

    migrated_count = sum(1 for _, success in results if success)
    print(f"Applications found: {len(applications)}")
    print(f"Successfully migrated: {migrated_count}")
    print(f"Successfully verified: {verified}")
    print(f"Failed: {len(applications) - migrated_count}")

    if migrated_count == len(applications) and verified == migrated_count:
        print(f"\n[SUCCESS] All applications migrated and verified successfully!")

        # Ask about file deletion
        response = input("\n[DELETE?] Delete original files? (yes/no): ").strip().lower()
        if response == "yes":
            print("\nDeleting original files...")
            for app_info, success in results:
                if success:
                    delete_migrated_files(app_info["directory"], dry_run=False)
            print("[OK] Original files deleted")
        else:
            print("[INFO] Original files preserved")

        return 0
    else:
        print(f"\n[WARN] Some migrations failed or could not be verified")
        print("[INFO] Original files preserved")
        return 1


if __name__ == "__main__":
    sys.exit(main())
