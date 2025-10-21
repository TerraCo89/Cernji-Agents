#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "pyyaml>=6.0",
#   "sqlmodel>=0.0.22",
#   "python-dotenv>=1.0.0",
# ]
# requires-python = ">=3.10"
# ///

"""
Test SQLite Backend

Quick test to verify the SQLite backend is working correctly.
Tests read and write operations directly through repositories.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from sqlmodel import Field, Session, SQLModel, create_engine, select

# Load environment
load_dotenv()

# Configuration
DB_PATH = Path("./data/resume_agent.db")
USER_ID = os.getenv("USER_ID", "default")


# ============================================================================
# SQLMODEL SCHEMAS (Same as resume_agent.py)
# ============================================================================

class DBPersonalInfo(SQLModel, table=True):
    """Personal info database table"""
    __tablename__ = "personal_info"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, default="default")
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    title: Optional[str] = None
    about_me: Optional[str] = None
    professional_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DBEmployment(SQLModel, table=True):
    """Employment history database table"""
    __tablename__ = "employment_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, default="default")
    company: str = Field(index=True)
    position: Optional[str] = None
    title: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    description: str
    technologies_json: Optional[str] = None
    achievements_json: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_read_personal_info(engine):
    """Test reading personal info from SQLite"""
    print("\n" + "=" * 70)
    print("TEST 1: Reading Personal Info from SQLite")
    print("=" * 70)

    with Session(engine) as session:
        personal_info = session.exec(
            select(DBPersonalInfo).where(DBPersonalInfo.user_id == USER_ID)
        ).first()

        if personal_info:
            print(f"[PASS] Read personal info successfully")
            print(f"   Name: {personal_info.name}")
            print(f"   Email: {personal_info.email}")
            print(f"   Title: {personal_info.title}")
            print(f"   LinkedIn: {personal_info.linkedin}")
            return True
        else:
            print(f"[FAIL] Personal info not found")
            return False


def test_read_employment_history(engine):
    """Test reading employment history from SQLite"""
    print("\n" + "=" * 70)
    print("TEST 2: Reading Employment History from SQLite")
    print("=" * 70)

    with Session(engine) as session:
        employment_list = session.exec(
            select(DBEmployment)
            .where(DBEmployment.user_id == USER_ID)
            .order_by(DBEmployment.start_date.desc())
        ).all()

        if employment_list:
            print(f"[PASS] Read {len(employment_list)} employment entries")

            # Show first job
            first_job = employment_list[0]
            print(f"\n   Latest job:")
            print(f"   - Company: {first_job.company}")
            print(f"   - Title: {first_job.title or first_job.position}")
            print(f"   - Start: {first_job.start_date}")

            # Count technologies and achievements
            techs = json.loads(first_job.technologies_json) if first_job.technologies_json else []
            achievements = json.loads(first_job.achievements_json) if first_job.achievements_json else []

            print(f"   - Technologies: {len(techs)}")
            print(f"   - Achievements: {len(achievements)}")

            if techs:
                print(f"   - Top 5 technologies: {', '.join(techs[:5])}")

            return True
        else:
            print(f"[FAIL] No employment entries found")
            return False


def test_add_achievement(engine):
    """Test adding achievement to SQLite"""
    print("\n" + "=" * 70)
    print("TEST 3: Adding Achievement to SQLite")
    print("=" * 70)

    with Session(engine) as session:
        # Get first employment entry
        employment = session.exec(
            select(DBEmployment)
            .where(DBEmployment.user_id == USER_ID)
            .order_by(DBEmployment.start_date.desc())
        ).first()

        if not employment:
            print(f"[FAIL] No employment entry to add achievement to")
            return False

        # Add test achievement
        achievements = json.loads(employment.achievements_json) if employment.achievements_json else []

        test_achievement = {
            "description": "Successfully tested SQLite backend integration",
            "metric": "100%"
        }

        achievements.append(test_achievement)
        employment.achievements_json = json.dumps(achievements)
        employment.updated_at = datetime.utcnow()

        session.commit()

        print(f"[PASS] Added achievement to {employment.company}")
        print(f"   Achievement: {test_achievement['description']}")
        print(f"   Metric: {test_achievement['metric']}")
        print(f"   Total achievements: {len(achievements)}")

        return True


def test_verify_achievement(engine):
    """Verify achievement persisted to SQLite"""
    print("\n" + "=" * 70)
    print("TEST 4: Verifying Achievement Persisted")
    print("=" * 70)

    with Session(engine) as session:
        # Get first employment entry
        employment = session.exec(
            select(DBEmployment)
            .where(DBEmployment.user_id == USER_ID)
            .order_by(DBEmployment.start_date.desc())
        ).first()

        if not employment:
            print(f"[FAIL] No employment entry found")
            return False

        achievements = json.loads(employment.achievements_json) if employment.achievements_json else []

        # Look for our test achievement
        test_ach = None
        for ach in achievements:
            if "SQLite backend integration" in ach["description"]:
                test_ach = ach
                break

        if test_ach:
            print(f"[PASS] Achievement persisted in database")
            print(f"   Company: {employment.company}")
            print(f"   Achievement: {test_ach['description']}")
            print(f"   Metric: {test_ach.get('metric', 'N/A')}")
            return True
        else:
            print(f"[FAIL] Achievement not found in database")
            return False


def test_add_technology(engine):
    """Test adding technology to SQLite"""
    print("\n" + "=" * 70)
    print("TEST 5: Adding Technology to SQLite")
    print("=" * 70)

    with Session(engine) as session:
        # Get first employment entry
        employment = session.exec(
            select(DBEmployment)
            .where(DBEmployment.user_id == USER_ID)
            .order_by(DBEmployment.start_date.desc())
        ).first()

        if not employment:
            print(f"[FAIL] No employment entry to add technology to")
            return False

        # Add test technologies
        techs = json.loads(employment.technologies_json) if employment.technologies_json else []

        new_techs = ["SQLite", "SQLModel", "UV Scripts"]
        added_techs = []

        for tech in new_techs:
            if tech not in techs:
                techs.append(tech)
                added_techs.append(tech)

        if added_techs:
            employment.technologies_json = json.dumps(techs)
            employment.updated_at = datetime.utcnow()
            session.commit()

            print(f"[PASS] Added technologies to {employment.company}")
            print(f"   Added: {', '.join(added_techs)}")
            print(f"   Total technologies: {len(techs)}")
            return True
        else:
            print(f"[PASS] All technologies already present (no duplicates added)")
            return True


def test_query_by_company(engine):
    """Test querying employment by company"""
    print("\n" + "=" * 70)
    print("TEST 6: Query by Company (Database Feature)")
    print("=" * 70)

    with Session(engine) as session:
        # Get all companies
        all_employment = session.exec(
            select(DBEmployment).where(DBEmployment.user_id == USER_ID)
        ).all()

        if not all_employment:
            print(f"[FAIL] No employment entries found")
            return False

        # Pick first company and query specifically for it
        first_company = all_employment[0].company

        company_jobs = session.exec(
            select(DBEmployment)
            .where(DBEmployment.user_id == USER_ID)
            .where(DBEmployment.company == first_company)
        ).all()

        print(f"[PASS] Query by company works")
        print(f"   Company: {first_company}")
        print(f"   Jobs found: {len(company_jobs)}")

        return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("SQLite Backend Test Suite")
    print("=" * 70)
    print(f"Database: {DB_PATH}")
    print(f"User ID: {USER_ID}")

    # Create engine
    if not DB_PATH.exists():
        print(f"\n[ERROR] Database not found: {DB_PATH}")
        print("Run migration first: uv run scripts/migrate_to_sqlite.py")
        return 1

    engine = create_engine(f"sqlite:///{DB_PATH}")

    # Run tests
    tests = [
        ("Read Personal Info", lambda: test_read_personal_info(engine)),
        ("Read Employment History", lambda: test_read_employment_history(engine)),
        ("Add Achievement", lambda: test_add_achievement(engine)),
        ("Verify Achievement Persisted", lambda: test_verify_achievement(engine)),
        ("Add Technology", lambda: test_add_technology(engine)),
        ("Query by Company", lambda: test_query_by_company(engine)),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[EXCEPTION] in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed! SQLite backend is working correctly.")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
