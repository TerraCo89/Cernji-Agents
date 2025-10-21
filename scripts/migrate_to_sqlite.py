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
Migration Script: YAML Files → SQLite Database

This standalone UV script migrates your existing YAML resume and career history
files to a SQLite database for better performance and query capabilities.

Usage:
    uv run scripts/migrate_to_sqlite.py

What it does:
    1. Reads master-resume.yaml and career-history.yaml
    2. Creates SQLite database (default: ./data/resume_agent.db)
    3. Creates tables (personal_info, employment_history)
    4. Migrates all data to database
    5. Preserves original YAML files (safe to rollback)

After migration:
    - Update .env: STORAGE_BACKEND=sqlite
    - Restart MCP server: uv run resume_agent.py
    - Original YAML files remain untouched (can rollback anytime)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine, select, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MASTER_RESUME = PROJECT_ROOT / "resumes" / "kris-cernjavic-resume.yaml"
CAREER_HISTORY = PROJECT_ROOT / "resumes" / "career-history.yaml"
DB_PATH = PROJECT_ROOT / "data" / "resume_agent.db"


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
    technologies_json: Optional[str] = None  # JSON array
    achievements_json: Optional[str] = None  # JSON array
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# MIGRATION FUNCTIONS
# ============================================================================

def migrate_to_sqlite(
    master_resume_path: Path = MASTER_RESUME,
    career_history_path: Path = CAREER_HISTORY,
    db_path: Path = DB_PATH,
    user_id: str = "default"
):
    """
    Migrate YAML files to SQLite database.

    Args:
        master_resume_path: Path to master resume YAML
        career_history_path: Path to career history YAML
        db_path: Path to SQLite database file
        user_id: User ID to assign data to
    """
    logger.info("=" * 70)
    logger.info("Resume Agent: YAML → SQLite Migration")
    logger.info("=" * 70)

    # Create database directory
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if database already exists
    if db_path.exists():
        logger.warning(f"Database already exists: {db_path}")
        response = input("Overwrite existing database? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            logger.info("Migration cancelled")
            return
        db_path.unlink()
        logger.info("Removed existing database")

    # Create database engine
    engine = create_engine(f"sqlite:///{db_path}")
    logger.info(f"Creating database: {db_path}")

    # Create tables
    SQLModel.metadata.create_all(engine)
    logger.info("✓ Created database tables")

    # Migrate career history (more complete than master resume)
    logger.info("\n" + "=" * 70)
    logger.info("Migrating Career History")
    logger.info("=" * 70)

    if not career_history_path.exists():
        logger.error(f"Career history not found: {career_history_path}")
        logger.info("Using master resume instead...")
        career_history_path = master_resume_path

    with open(career_history_path, 'r', encoding='utf-8') as f:
        career_data = yaml.safe_load(f)

    with Session(engine) as session:
        # Personal info
        pi_data = career_data.get("personal_info", {})
        personal_info = DBPersonalInfo(
            user_id=user_id,
            name=pi_data.get("name", ""),
            phone=pi_data.get("phone"),
            email=pi_data.get("email"),
            linkedin=pi_data.get("linkedin"),
            title=pi_data.get("title"),
            about_me=career_data.get("about_me"),
            professional_summary=career_data.get("professional_summary")
        )
        session.add(personal_info)
        session.commit()

        logger.info(f"✓ Migrated personal info: {personal_info.name}")

        # Employment history
        employment_count = 0
        for emp_data in career_data.get("employment_history", []):
            employment = DBEmployment(
                user_id=user_id,
                company=emp_data["company"],
                title=emp_data.get("title"),
                position=emp_data.get("position"),
                employment_type=emp_data.get("employment_type"),
                start_date=emp_data["start_date"],
                end_date=emp_data.get("end_date"),
                description=emp_data["description"],
                technologies_json=json.dumps(emp_data.get("technologies", [])),
                achievements_json=json.dumps(emp_data.get("achievements")) if emp_data.get("achievements") else None
            )
            session.add(employment)
            employment_count += 1

            # Log progress
            techs = emp_data.get("technologies", [])
            achievements = emp_data.get("achievements", [])
            logger.info(f"✓ {emp_data['company']}: {len(techs)} technologies, {len(achievements) if achievements else 0} achievements")

        session.commit()
        logger.info(f"\n✓ Migrated {employment_count} employment entries")

    # Verify migration
    logger.info("\n" + "=" * 70)
    logger.info("Verifying Migration")
    logger.info("=" * 70)

    with Session(engine) as session:
        # Check personal info
        pi = session.exec(select(DBPersonalInfo).where(DBPersonalInfo.user_id == user_id)).first()
        if pi:
            logger.info(f"✓ Personal info: {pi.name}")
        else:
            logger.error("✗ Personal info not found")

        # Check employment
        emp_count = session.exec(select(DBEmployment).where(DBEmployment.user_id == user_id)).all()
        logger.info(f"✓ Employment history: {len(emp_count)} entries")

    # Success message
    logger.info("\n" + "=" * 70)
    logger.info("✅ Migration Complete!")
    logger.info("=" * 70)
    logger.info(f"Database: {db_path}")
    logger.info(f"Size: {db_path.stat().st_size / 1024:.2f} KB")
    logger.info("\nNext steps:")
    logger.info("1. Update .env file: STORAGE_BACKEND=sqlite")
    logger.info("2. Restart MCP server: uv run resume_agent.py")
    logger.info("\nOriginal YAML files are preserved for backup/rollback.")


if __name__ == "__main__":
    import sys

    # Allow override of user_id via command line
    user_id = sys.argv[1] if len(sys.argv) > 1 else "default"

    try:
        migrate_to_sqlite(user_id=user_id)
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
