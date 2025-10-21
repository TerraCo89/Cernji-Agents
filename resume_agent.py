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
Resume Agent MCP Server

A Model Context Protocol server that exposes your career application slash commands
to any MCP client (Claude Desktop, ChatGPT, Cursor, etc.).

This server uses the SUBPROCESS approach - it spawns the `claude` CLI directly,
which means it uses your MAX subscription instead of requiring ANTHROPIC_API_KEY.
This saves thousands in API costs during development.

How it works:
- MCP tools wrap your .claude/commands/career/*.md slash commands
- When called, it spawns: `claude -- /career:analyze-job https://...`
- Claude CLI uses your MAX subscription authentication
- Output is captured and returned to the MCP client

Available via MCP:
- analyze_job(job_url) → /career:analyze-job
- tailor_resume(job_url) → /career:tailor-resume
- apply_to_job(job_url) → /career:apply

Single-file deployment using UV (Astral) + FastMCP.

Usage:
    uv run resume_agent.py

For HTTP server (production):
    uv run resume_agent.py --transport streamable-http --port 8080
"""

import asyncio
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from sqlmodel import Session, SQLModel, create_engine, select, Field as SQLField, Relationship

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(
    name="resume-agent",
    version="0.1.0"
)

# Project paths
PROJECT_ROOT = Path(__file__).parent
COMMANDS_DIR = PROJECT_ROOT / ".claude" / "commands"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
RESUMES_DIR = PROJECT_ROOT / "resumes"
APPLICATIONS_DIR = PROJECT_ROOT / "job-applications"
MASTER_RESUME = RESUMES_DIR / "kris-cernjavic-resume.yaml"
CAREER_HISTORY = RESUMES_DIR / "career-history.yaml"

# Ensure directories exist
APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# PYDANTIC SCHEMAS (Data Models)
# ============================================================================

class PersonalInfo(BaseModel):
    """Personal contact information"""
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    title: Optional[str] = None


class Technology(BaseModel):
    """Technology or skill"""
    name: str


class Achievement(BaseModel):
    """Achievement with optional metrics"""
    description: str
    metric: Optional[str] = None


class Employment(BaseModel):
    """Employment history entry"""
    company: str
    position: Optional[str] = None
    title: Optional[str] = None  # Some use 'position', some use 'title'
    employment_type: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    description: str
    technologies: List[str] = Field(default_factory=list)
    achievements: Optional[List[Achievement]] = None


class MasterResume(BaseModel):
    """Master resume data structure"""
    personal_info: PersonalInfo
    about_me: Optional[str] = None
    professional_summary: Optional[str] = None
    employment_history: List[Employment] = Field(default_factory=list)


class CareerHistory(BaseModel):
    """Extended career history with additional details"""
    personal_info: PersonalInfo
    professional_summary: Optional[str] = None
    employment_history: List[Employment] = Field(default_factory=list)


class JobAnalysis(BaseModel):
    """Structured job posting data"""
    url: str
    fetched_at: str  # ISO timestamp
    company: str
    job_title: str
    location: str
    salary_range: Optional[str] = None
    required_qualifications: List[str] = Field(default_factory=list)
    preferred_qualifications: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    candidate_profile: str
    raw_description: str


class TailoredResume(BaseModel):
    """Tailored resume content and metadata"""
    company: str
    job_title: str
    content: str
    created_at: str  # ISO timestamp
    keywords_used: List[str] = Field(default_factory=list)
    changes_from_master: List[str] = Field(default_factory=list)


class CoverLetter(BaseModel):
    """Cover letter content and metadata"""
    company: str
    job_title: str
    content: str
    created_at: str  # ISO timestamp
    talking_points: List[str] = Field(default_factory=list)


class PortfolioExamples(BaseModel):
    """Portfolio code examples"""
    company: str
    job_title: str
    examples: List[dict] = Field(default_factory=list)  # List of {repo, description, link}
    created_at: str  # ISO timestamp


class ApplicationMetadata(BaseModel):
    """Metadata about a job application"""
    directory: str
    company: str
    role: str
    files: dict  # {resume: bool, cover_letter: bool, analysis: bool}
    modified: float  # Unix timestamp


# ============================================================================
# SQLMODEL SCHEMAS (Database Tables - Optional)
# ============================================================================
# These schemas are used when STORAGE_BACKEND=sqlite in .env
# When STORAGE_BACKEND=file (default), the file-based system is used instead

class DBPersonalInfo(SQLModel, table=True):
    """Personal info database table"""
    __tablename__ = "personal_info"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: str = SQLField(index=True, default="default")
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    title: Optional[str] = None
    about_me: Optional[str] = None
    professional_summary: Optional[str] = None
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DBEmployment(SQLModel, table=True):
    """Employment history database table"""
    __tablename__ = "employment_history"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: str = SQLField(index=True, default="default")
    company: str = SQLField(index=True)
    position: Optional[str] = None
    title: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    description: str
    technologies_json: Optional[str] = None  # JSON array
    achievements_json: Optional[str] = None  # JSON array
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DBJobApplication(SQLModel, table=True):
    """Job application database table"""
    __tablename__ = "job_applications"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: str = SQLField(index=True, default="default")
    url: str
    company: str = SQLField(index=True)
    job_title: str = SQLField(index=True)
    location: str
    salary_range: Optional[str] = None
    candidate_profile: str
    raw_description: str
    fetched_at: str  # ISO timestamp
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DBJobQualification(SQLModel, table=True):
    """Job qualification (required or preferred)"""
    __tablename__ = "job_qualifications"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    job_id: int = SQLField(foreign_key="job_applications.id", index=True)
    qualification_type: str = SQLField(index=True)  # 'required' or 'preferred'
    description: str


class DBJobResponsibility(SQLModel, table=True):
    """Job responsibility"""
    __tablename__ = "job_responsibilities"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    job_id: int = SQLField(foreign_key="job_applications.id", index=True)
    description: str


class DBJobKeyword(SQLModel, table=True):
    """ATS keyword from job posting"""
    __tablename__ = "job_keywords"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    job_id: int = SQLField(foreign_key="job_applications.id", index=True)
    keyword: str = SQLField(index=True)


class DBTailoredResume(SQLModel, table=True):
    """Tailored resume for specific job"""
    __tablename__ = "tailored_resumes"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    job_id: int = SQLField(foreign_key="job_applications.id", unique=True, index=True)
    content: str  # Full resume text
    keywords_used_json: Optional[str] = None  # JSON array
    changes_from_master_json: Optional[str] = None  # JSON array
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DBCoverLetter(SQLModel, table=True):
    """Cover letter for specific job"""
    __tablename__ = "cover_letters"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    job_id: int = SQLField(foreign_key="job_applications.id", unique=True, index=True)
    content: str  # Full cover letter text
    talking_points_json: Optional[str] = None  # JSON array
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


class DBPortfolioExamples(SQLModel, table=True):
    """Portfolio code examples for job"""
    __tablename__ = "portfolio_examples"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    job_id: int = SQLField(foreign_key="job_applications.id", unique=True, index=True)
    content: str  # Full portfolio analysis text
    examples_json: Optional[str] = None  # JSON array of examples
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class DBPortfolioLibrary(SQLModel, table=True):
    """Job-agnostic portfolio library for code examples"""
    __tablename__ = "portfolio_library"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: str = SQLField(index=True, default="default")
    title: str = SQLField(index=True)  # "RAG Pipeline - Customer Matching"
    company: Optional[str] = SQLField(index=True, default=None)  # "D&D Worldwide Logistics"
    project: Optional[str] = None  # "DDWL Platform"
    description: Optional[str] = None  # What it demonstrates
    content: str  # Code examples, explanations, file content
    technologies_json: Optional[str] = None  # JSON array: ["RAG", "Redis", "Supabase"]
    file_paths_json: Optional[str] = None  # JSON array: ["backend/services/matching.py:536"]
    source_repo: Optional[str] = None  # GitHub URL
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)


# ============================================================================
# REPOSITORY INTERFACES
# ============================================================================

class ResumeRepository(ABC):
    """Abstract repository for resume operations"""

    @abstractmethod
    def get_master_resume(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get master resume for user"""
        pass

    @abstractmethod
    def save_master_resume(self, user_id: str, resume_data: Dict[str, Any]) -> None:
        """Save master resume for user"""
        pass


class CareerHistoryRepository(ABC):
    """Abstract repository for career history operations"""

    @abstractmethod
    def get_career_history(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get career history for user"""
        pass

    @abstractmethod
    def save_career_history(self, user_id: str, history_data: Dict[str, Any]) -> None:
        """Save career history for user"""
        pass

    @abstractmethod
    def add_achievement(self, user_id: str, company: str, achievement: Dict[str, Any]) -> None:
        """Add achievement to employment history"""
        pass

    @abstractmethod
    def add_technology(self, user_id: str, company: str, technologies: List[str]) -> None:
        """Add technologies to employment history"""
        pass


class JobApplicationRepository(ABC):
    """Abstract repository for job application operations"""

    @abstractmethod
    def get_job_analysis(self, user_id: str, company: str, job_title: str) -> Optional[Dict[str, Any]]:
        """Get job analysis for application"""
        pass

    @abstractmethod
    def save_job_analysis(self, user_id: str, job_data: Dict[str, Any]) -> None:
        """Save job analysis"""
        pass

    @abstractmethod
    def get_tailored_resume(self, user_id: str, company: str, job_title: str) -> Optional[str]:
        """Get tailored resume content"""
        pass

    @abstractmethod
    def save_tailored_resume(
        self, user_id: str, company: str, job_title: str,
        content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save tailored resume"""
        pass

    @abstractmethod
    def get_cover_letter(self, user_id: str, company: str, job_title: str) -> Optional[str]:
        """Get cover letter content"""
        pass

    @abstractmethod
    def save_cover_letter(
        self, user_id: str, company: str, job_title: str,
        content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save cover letter"""
        pass

    @abstractmethod
    def save_portfolio_examples(
        self, user_id: str, company: str, job_title: str, content: str
    ) -> None:
        """Save portfolio examples"""
        pass

    @abstractmethod
    def list_applications(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent job applications"""
        pass

    @abstractmethod
    def get_application_path(
        self, user_id: str, company: str, job_title: str, ensure_exists: bool = False
    ) -> Dict[str, Any]:
        """Get application directory/identifier"""
        pass


class PortfolioLibraryRepository(ABC):
    """Abstract repository for portfolio library operations"""

    @abstractmethod
    def add_example(
        self, user_id: str, title: str, content: str,
        company: Optional[str] = None, project: Optional[str] = None,
        description: Optional[str] = None, technologies: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None, source_repo: Optional[str] = None
    ) -> int:
        """Add new portfolio example, returns ID"""
        pass

    @abstractmethod
    def list_examples(
        self, user_id: str, limit: Optional[int] = None,
        technology_filter: Optional[str] = None, company_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List portfolio examples with optional filters"""
        pass

    @abstractmethod
    def search_examples(
        self, user_id: str, query: str, technologies: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search portfolio examples by keyword/technology"""
        pass

    @abstractmethod
    def get_example(self, user_id: str, example_id: int) -> Optional[Dict[str, Any]]:
        """Get specific portfolio example by ID"""
        pass

    @abstractmethod
    def update_example(
        self, user_id: str, example_id: int,
        title: Optional[str] = None, content: Optional[str] = None,
        company: Optional[str] = None, project: Optional[str] = None,
        description: Optional[str] = None, technologies: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None, source_repo: Optional[str] = None
    ) -> None:
        """Update existing portfolio example"""
        pass

    @abstractmethod
    def delete_example(self, user_id: str, example_id: int) -> None:
        """Delete portfolio example"""
        pass


# ============================================================================
# SQLITE BACKEND IMPLEMENTATION
# ============================================================================

class SQLiteResumeRepository(ResumeRepository):
    """SQLite implementation of resume repository"""

    def __init__(self, db_path: str, user_id: str):
        self.db_path = db_path
        self.user_id = user_id
        self.engine = create_engine(f"sqlite:///{db_path}")
        # Create tables if they don't exist
        SQLModel.metadata.create_all(self.engine)

    def get_master_resume(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get master resume from database"""
        with Session(self.engine) as session:
            # Get personal info
            personal_info = session.exec(
                select(DBPersonalInfo).where(DBPersonalInfo.user_id == user_id)
            ).first()

            if not personal_info:
                return None

            # Get employment history
            employment_list = session.exec(
                select(DBEmployment)
                .where(DBEmployment.user_id == user_id)
                .order_by(DBEmployment.start_date.desc())
            ).all()

            # Build resume data
            return {
                "personal_info": {
                    "name": personal_info.name,
                    "phone": personal_info.phone,
                    "email": personal_info.email,
                    "linkedin": personal_info.linkedin,
                    "title": personal_info.title
                },
                "about_me": personal_info.about_me,
                "professional_summary": personal_info.professional_summary,
                "employment_history": [
                    {
                        "company": emp.company,
                        "position": emp.position or emp.title,
                        "employment_type": emp.employment_type,
                        "start_date": emp.start_date,
                        "end_date": emp.end_date,
                        "description": emp.description,
                        "technologies": json.loads(emp.technologies_json) if emp.technologies_json else []
                    }
                    for emp in employment_list
                ]
            }

    def save_master_resume(self, user_id: str, resume_data: Dict[str, Any]) -> None:
        """Save master resume to database"""
        with Session(self.engine) as session:
            # Update or create personal info
            personal_info = session.exec(
                select(DBPersonalInfo).where(DBPersonalInfo.user_id == user_id)
            ).first()

            pi_data = resume_data.get("personal_info", {})
            if personal_info:
                personal_info.name = pi_data.get("name", personal_info.name)
                personal_info.phone = pi_data.get("phone")
                personal_info.email = pi_data.get("email")
                personal_info.linkedin = pi_data.get("linkedin")
                personal_info.title = pi_data.get("title")
                personal_info.about_me = resume_data.get("about_me")
                personal_info.professional_summary = resume_data.get("professional_summary")
                personal_info.updated_at = datetime.utcnow()
            else:
                personal_info = DBPersonalInfo(
                    user_id=user_id,
                    name=pi_data.get("name", ""),
                    phone=pi_data.get("phone"),
                    email=pi_data.get("email"),
                    linkedin=pi_data.get("linkedin"),
                    title=pi_data.get("title"),
                    about_me=resume_data.get("about_me"),
                    professional_summary=resume_data.get("professional_summary")
                )
                session.add(personal_info)

            # Delete existing employment history and recreate
            for emp in session.exec(select(DBEmployment).where(DBEmployment.user_id == user_id)).all():
                session.delete(emp)

            # Add employment history
            for emp_data in resume_data.get("employment_history", []):
                employment = DBEmployment(
                    user_id=user_id,
                    company=emp_data["company"],
                    title=emp_data.get("title"),
                    position=emp_data.get("position"),
                    employment_type=emp_data.get("employment_type"),
                    start_date=emp_data["start_date"],
                    end_date=emp_data.get("end_date"),
                    description=emp_data["description"],
                    technologies_json=json.dumps(emp_data.get("technologies", []))
                )
                session.add(employment)

            session.commit()


class SQLiteCareerHistoryRepository(CareerHistoryRepository):
    """SQLite implementation of career history repository"""

    def __init__(self, db_path: str, user_id: str):
        self.db_path = db_path
        self.user_id = user_id
        self.engine = create_engine(f"sqlite:///{db_path}")

    def get_career_history(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get career history from database (includes achievements)"""
        with Session(self.engine) as session:
            personal_info = session.exec(
                select(DBPersonalInfo).where(DBPersonalInfo.user_id == user_id)
            ).first()

            if not personal_info:
                return None

            employment_list = session.exec(
                select(DBEmployment)
                .where(DBEmployment.user_id == user_id)
                .order_by(DBEmployment.start_date.desc())
            ).all()

            return {
                "personal_info": {
                    "name": personal_info.name,
                    "phone": personal_info.phone,
                    "email": personal_info.email,
                    "linkedin": personal_info.linkedin,
                    "title": personal_info.title
                },
                "professional_summary": personal_info.professional_summary,
                "employment_history": [
                    {
                        "company": emp.company,
                        "title": emp.title or emp.position,
                        "employment_type": emp.employment_type,
                        "start_date": emp.start_date,
                        "end_date": emp.end_date,
                        "description": emp.description,
                        "technologies": json.loads(emp.technologies_json) if emp.technologies_json else [],
                        "achievements": json.loads(emp.achievements_json) if emp.achievements_json else None
                    }
                    for emp in employment_list
                ]
            }

    def save_career_history(self, user_id: str, history_data: Dict[str, Any]) -> None:
        """Save career history to database"""
        with Session(self.engine) as session:
            # Similar to save_master_resume but includes achievements
            personal_info = session.exec(
                select(DBPersonalInfo).where(DBPersonalInfo.user_id == user_id)
            ).first()

            pi_data = history_data.get("personal_info", {})
            if personal_info:
                personal_info.name = pi_data.get("name", personal_info.name)
                personal_info.phone = pi_data.get("phone")
                personal_info.email = pi_data.get("email")
                personal_info.linkedin = pi_data.get("linkedin")
                personal_info.title = pi_data.get("title")
                personal_info.professional_summary = history_data.get("professional_summary")
                personal_info.updated_at = datetime.utcnow()
            else:
                personal_info = DBPersonalInfo(
                    user_id=user_id,
                    name=pi_data.get("name", ""),
                    phone=pi_data.get("phone"),
                    email=pi_data.get("email"),
                    linkedin=pi_data.get("linkedin"),
                    title=pi_data.get("title"),
                    professional_summary=history_data.get("professional_summary")
                )
                session.add(personal_info)

            # Delete and recreate employment history
            for emp in session.exec(select(DBEmployment).where(DBEmployment.user_id == user_id)).all():
                session.delete(emp)

            for emp_data in history_data.get("employment_history", []):
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

            session.commit()

    def add_achievement(self, user_id: str, company: str, achievement: Dict[str, Any]) -> None:
        """Add achievement to employment history"""
        with Session(self.engine) as session:
            employment = session.exec(
                select(DBEmployment)
                .where(DBEmployment.user_id == user_id)
                .where(DBEmployment.company == company)
            ).first()

            if not employment:
                raise ValueError(f"Company '{company}' not found in employment history")

            # Get existing achievements
            achievements = json.loads(employment.achievements_json) if employment.achievements_json else []
            achievements.append(achievement)
            employment.achievements_json = json.dumps(achievements)
            employment.updated_at = datetime.utcnow()

            session.commit()

    def add_technology(self, user_id: str, company: str, technologies: List[str]) -> None:
        """Add technologies to employment history"""
        with Session(self.engine) as session:
            employment = session.exec(
                select(DBEmployment)
                .where(DBEmployment.user_id == user_id)
                .where(DBEmployment.company == company)
            ).first()

            if not employment:
                raise ValueError(f"Company '{company}' not found")

            # Get existing techs
            existing_techs = json.loads(employment.technologies_json) if employment.technologies_json else []

            # Add new ones (avoid duplicates)
            for tech in technologies:
                if tech not in existing_techs:
                    existing_techs.append(tech)

            employment.technologies_json = json.dumps(existing_techs)
            employment.updated_at = datetime.utcnow()

            session.commit()


class SQLiteJobApplicationRepository(JobApplicationRepository):
    """SQLite implementation of job application repository"""

    def __init__(self, db_path: str, user_id: str):
        self.db_path = db_path
        self.user_id = user_id
        self.engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(self.engine)

    def get_job_analysis(self, user_id: str, company: str, job_title: str) -> Optional[Dict[str, Any]]:
        """Get job analysis for application"""
        with Session(self.engine) as session:
            job_app = session.exec(
                select(DBJobApplication)
                .where(DBJobApplication.user_id == user_id)
                .where(DBJobApplication.company == company)
                .where(DBJobApplication.job_title == job_title)
            ).first()

            if not job_app:
                return None

            # Get related data
            required_quals = session.exec(
                select(DBJobQualification)
                .where(DBJobQualification.job_id == job_app.id)
                .where(DBJobQualification.qualification_type == "required")
            ).all()

            preferred_quals = session.exec(
                select(DBJobQualification)
                .where(DBJobQualification.job_id == job_app.id)
                .where(DBJobQualification.qualification_type == "preferred")
            ).all()

            responsibilities = session.exec(
                select(DBJobResponsibility).where(DBJobResponsibility.job_id == job_app.id)
            ).all()

            keywords = session.exec(
                select(DBJobKeyword).where(DBJobKeyword.job_id == job_app.id)
            ).all()

            return {
                "url": job_app.url,
                "fetched_at": job_app.fetched_at,
                "company": job_app.company,
                "job_title": job_app.job_title,
                "location": job_app.location,
                "salary_range": job_app.salary_range,
                "required_qualifications": [q.description for q in required_quals],
                "preferred_qualifications": [q.description for q in preferred_quals],
                "responsibilities": [r.description for r in responsibilities],
                "keywords": [k.keyword for k in keywords],
                "candidate_profile": job_app.candidate_profile,
                "raw_description": job_app.raw_description
            }

    def save_job_analysis(self, user_id: str, job_data: Dict[str, Any]) -> None:
        """Save job analysis"""
        with Session(self.engine) as session:
            # Check if exists
            existing = session.exec(
                select(DBJobApplication)
                .where(DBJobApplication.user_id == user_id)
                .where(DBJobApplication.company == job_data["company"])
                .where(DBJobApplication.job_title == job_data["job_title"])
            ).first()

            if existing:
                # Delete and recreate (simpler than updating related records)
                session.delete(existing)
                session.commit()

            # Create job application
            job_app = DBJobApplication(
                user_id=user_id,
                url=job_data["url"],
                company=job_data["company"],
                job_title=job_data["job_title"],
                location=job_data["location"],
                salary_range=job_data.get("salary_range"),
                candidate_profile=job_data["candidate_profile"],
                raw_description=job_data["raw_description"],
                fetched_at=job_data["fetched_at"]
            )
            session.add(job_app)
            session.flush()

            # Add related data
            for qual in job_data.get("required_qualifications", []):
                q = DBJobQualification(job_id=job_app.id, qualification_type="required", description=qual)
                session.add(q)

            for qual in job_data.get("preferred_qualifications", []):
                q = DBJobQualification(job_id=job_app.id, qualification_type="preferred", description=qual)
                session.add(q)

            for resp in job_data.get("responsibilities", []):
                r = DBJobResponsibility(job_id=job_app.id, description=resp)
                session.add(r)

            for keyword in job_data.get("keywords", []):
                k = DBJobKeyword(job_id=job_app.id, keyword=keyword)
                session.add(k)

            session.commit()

    def get_tailored_resume(self, user_id: str, company: str, job_title: str) -> Optional[str]:
        """Get tailored resume content"""
        with Session(self.engine) as session:
            # Find job application
            job_app = session.exec(
                select(DBJobApplication)
                .where(DBJobApplication.user_id == user_id)
                .where(DBJobApplication.company == company)
                .where(DBJobApplication.job_title == job_title)
            ).first()

            if not job_app:
                return None

            # Get tailored resume
            resume = session.exec(
                select(DBTailoredResume).where(DBTailoredResume.job_id == job_app.id)
            ).first()

            return resume.content if resume else None

    def save_tailored_resume(
        self, user_id: str, company: str, job_title: str,
        content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save tailored resume"""
        with Session(self.engine) as session:
            # Find job application
            job_app = session.exec(
                select(DBJobApplication)
                .where(DBJobApplication.user_id == user_id)
                .where(DBJobApplication.company == company)
                .where(DBJobApplication.job_title == job_title)
            ).first()

            if not job_app:
                raise ValueError(f"Job application not found: {company} - {job_title}")

            # Check if exists
            existing = session.exec(
                select(DBTailoredResume).where(DBTailoredResume.job_id == job_app.id)
            ).first()

            if existing:
                existing.content = content
                existing.updated_at = datetime.utcnow()
                if metadata:
                    if "keywords_used" in metadata:
                        existing.keywords_used_json = json.dumps(metadata["keywords_used"])
                    if "changes_from_master" in metadata:
                        existing.changes_from_master_json = json.dumps(metadata["changes_from_master"])
            else:
                resume = DBTailoredResume(
                    job_id=job_app.id,
                    content=content,
                    keywords_used_json=json.dumps(metadata.get("keywords_used", [])) if metadata else None,
                    changes_from_master_json=json.dumps(metadata.get("changes_from_master", [])) if metadata else None
                )
                session.add(resume)

            session.commit()

    def get_cover_letter(self, user_id: str, company: str, job_title: str) -> Optional[str]:
        """Get cover letter content"""
        with Session(self.engine) as session:
            job_app = session.exec(
                select(DBJobApplication)
                .where(DBJobApplication.user_id == user_id)
                .where(DBJobApplication.company == company)
                .where(DBJobApplication.job_title == job_title)
            ).first()

            if not job_app:
                return None

            cover = session.exec(
                select(DBCoverLetter).where(DBCoverLetter.job_id == job_app.id)
            ).first()

            return cover.content if cover else None

    def save_cover_letter(
        self, user_id: str, company: str, job_title: str,
        content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save cover letter"""
        with Session(self.engine) as session:
            job_app = session.exec(
                select(DBJobApplication)
                .where(DBJobApplication.user_id == user_id)
                .where(DBJobApplication.company == company)
                .where(DBJobApplication.job_title == job_title)
            ).first()

            if not job_app:
                raise ValueError(f"Job application not found: {company} - {job_title}")

            existing = session.exec(
                select(DBCoverLetter).where(DBCoverLetter.job_id == job_app.id)
            ).first()

            if existing:
                existing.content = content
                existing.updated_at = datetime.utcnow()
                if metadata and "talking_points" in metadata:
                    existing.talking_points_json = json.dumps(metadata["talking_points"])
            else:
                cover = DBCoverLetter(
                    job_id=job_app.id,
                    content=content,
                    talking_points_json=json.dumps(metadata.get("talking_points", [])) if metadata else None
                )
                session.add(cover)

            session.commit()

    def save_portfolio_examples(
        self, user_id: str, company: str, job_title: str, content: str
    ) -> None:
        """Save portfolio examples"""
        with Session(self.engine) as session:
            job_app = session.exec(
                select(DBJobApplication)
                .where(DBJobApplication.user_id == user_id)
                .where(DBJobApplication.company == company)
                .where(DBJobApplication.job_title == job_title)
            ).first()

            if not job_app:
                raise ValueError(f"Job application not found: {company} - {job_title}")

            existing = session.exec(
                select(DBPortfolioExamples).where(DBPortfolioExamples.job_id == job_app.id)
            ).first()

            if existing:
                existing.content = content
            else:
                portfolio = DBPortfolioExamples(job_id=job_app.id, content=content)
                session.add(portfolio)

            session.commit()

    def list_applications(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent job applications"""
        with Session(self.engine) as session:
            apps = session.exec(
                select(DBJobApplication)
                .where(DBJobApplication.user_id == user_id)
                .order_by(DBJobApplication.created_at.desc())
                .limit(limit)
            ).all()

            results = []
            for app in apps:
                # Check which files exist
                has_resume = session.exec(
                    select(DBTailoredResume).where(DBTailoredResume.job_id == app.id)
                ).first() is not None

                has_cover = session.exec(
                    select(DBCoverLetter).where(DBCoverLetter.job_id == app.id)
                ).first() is not None

                has_portfolio = session.exec(
                    select(DBPortfolioExamples).where(DBPortfolioExamples.job_id == app.id)
                ).first() is not None

                results.append({
                    "company": app.company,
                    "role": app.job_title,
                    "files": {
                        "resume": has_resume,
                        "cover_letter": has_cover,
                        "analysis": True,
                        "portfolio": has_portfolio
                    },
                    "modified": app.updated_at.timestamp()
                })

            return results

    def get_application_path(
        self, user_id: str, company: str, job_title: str, ensure_exists: bool = False
    ) -> Dict[str, Any]:
        """Get application directory/identifier"""
        # For database backend, we return a virtual path concept
        # This maintains compatibility with existing code
        dir_name = company.replace(" ", "_") + "_" + job_title.replace(" ", "_")

        with Session(self.engine) as session:
            job_app = session.exec(
                select(DBJobApplication)
                .where(DBJobApplication.user_id == user_id)
                .where(DBJobApplication.company == company)
                .where(DBJobApplication.job_title == job_title)
            ).first()

            exists = job_app is not None

        return {
            "directory": f"db://{user_id}/{dir_name}",
            "exists": exists
        }


class SQLitePortfolioLibraryRepository(PortfolioLibraryRepository):
    """SQLite implementation of portfolio library repository"""

    def __init__(self, db_path: str, user_id: str):
        self.db_path = db_path
        self.user_id = user_id
        self.engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(self.engine)

    def add_example(
        self, user_id: str, title: str, content: str,
        company: Optional[str] = None, project: Optional[str] = None,
        description: Optional[str] = None, technologies: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None, source_repo: Optional[str] = None
    ) -> int:
        """Add new portfolio example, returns ID"""
        with Session(self.engine) as session:
            example = DBPortfolioLibrary(
                user_id=user_id,
                title=title,
                company=company,
                project=project,
                description=description,
                content=content,
                technologies_json=json.dumps(technologies) if technologies else None,
                file_paths_json=json.dumps(file_paths) if file_paths else None,
                source_repo=source_repo
            )
            session.add(example)
            session.commit()
            session.refresh(example)
            return example.id

    def list_examples(
        self, user_id: str, limit: Optional[int] = None,
        technology_filter: Optional[str] = None, company_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List portfolio examples with optional filters"""
        with Session(self.engine) as session:
            query = select(DBPortfolioLibrary).where(DBPortfolioLibrary.user_id == user_id)

            if company_filter:
                query = query.where(DBPortfolioLibrary.company == company_filter)

            if technology_filter:
                # Search in JSON array (SQLite doesn't have native JSON functions, so we use LIKE)
                query = query.where(DBPortfolioLibrary.technologies_json.like(f'%"{technology_filter}"%'))

            query = query.order_by(DBPortfolioLibrary.created_at.desc())

            if limit:
                query = query.limit(limit)

            examples = session.exec(query).all()

            return [
                {
                    "id": ex.id,
                    "title": ex.title,
                    "company": ex.company,
                    "project": ex.project,
                    "description": ex.description,
                    "technologies": json.loads(ex.technologies_json) if ex.technologies_json else [],
                    "file_paths": json.loads(ex.file_paths_json) if ex.file_paths_json else [],
                    "source_repo": ex.source_repo,
                    "created_at": ex.created_at.isoformat(),
                    "updated_at": ex.updated_at.isoformat()
                }
                for ex in examples
            ]

    def search_examples(
        self, user_id: str, query: str, technologies: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search portfolio examples by keyword/technology"""
        with Session(self.engine) as session:
            # Build search query
            search_query = select(DBPortfolioLibrary).where(DBPortfolioLibrary.user_id == user_id)

            # Full-text search across title, description, content, company, project
            search_pattern = f"%{query}%"
            search_query = search_query.where(
                (DBPortfolioLibrary.title.like(search_pattern)) |
                (DBPortfolioLibrary.description.like(search_pattern)) |
                (DBPortfolioLibrary.content.like(search_pattern)) |
                (DBPortfolioLibrary.company.like(search_pattern)) |
                (DBPortfolioLibrary.project.like(search_pattern)) |
                (DBPortfolioLibrary.technologies_json.like(search_pattern))
            )

            # Filter by technologies if provided
            if technologies:
                for tech in technologies:
                    search_query = search_query.where(
                        DBPortfolioLibrary.technologies_json.like(f'%"{tech}"%')
                    )

            examples = session.exec(search_query.order_by(DBPortfolioLibrary.updated_at.desc())).all()

            return [
                {
                    "id": ex.id,
                    "title": ex.title,
                    "company": ex.company,
                    "project": ex.project,
                    "description": ex.description,
                    "technologies": json.loads(ex.technologies_json) if ex.technologies_json else [],
                    "file_paths": json.loads(ex.file_paths_json) if ex.file_paths_json else [],
                    "source_repo": ex.source_repo,
                    "created_at": ex.created_at.isoformat(),
                    "updated_at": ex.updated_at.isoformat(),
                    "content_preview": ex.content[:200] + "..." if len(ex.content) > 200 else ex.content
                }
                for ex in examples
            ]

    def get_example(self, user_id: str, example_id: int) -> Optional[Dict[str, Any]]:
        """Get specific portfolio example by ID"""
        with Session(self.engine) as session:
            example = session.exec(
                select(DBPortfolioLibrary)
                .where(DBPortfolioLibrary.user_id == user_id)
                .where(DBPortfolioLibrary.id == example_id)
            ).first()

            if not example:
                return None

            return {
                "id": example.id,
                "title": example.title,
                "company": example.company,
                "project": example.project,
                "description": example.description,
                "content": example.content,
                "technologies": json.loads(example.technologies_json) if example.technologies_json else [],
                "file_paths": json.loads(example.file_paths_json) if example.file_paths_json else [],
                "source_repo": example.source_repo,
                "created_at": example.created_at.isoformat(),
                "updated_at": example.updated_at.isoformat()
            }

    def update_example(
        self, user_id: str, example_id: int,
        title: Optional[str] = None, content: Optional[str] = None,
        company: Optional[str] = None, project: Optional[str] = None,
        description: Optional[str] = None, technologies: Optional[List[str]] = None,
        file_paths: Optional[List[str]] = None, source_repo: Optional[str] = None
    ) -> None:
        """Update existing portfolio example"""
        with Session(self.engine) as session:
            example = session.exec(
                select(DBPortfolioLibrary)
                .where(DBPortfolioLibrary.user_id == user_id)
                .where(DBPortfolioLibrary.id == example_id)
            ).first()

            if not example:
                raise ValueError(f"Portfolio example {example_id} not found")

            if title is not None:
                example.title = title
            if content is not None:
                example.content = content
            if company is not None:
                example.company = company
            if project is not None:
                example.project = project
            if description is not None:
                example.description = description
            if technologies is not None:
                example.technologies_json = json.dumps(technologies)
            if file_paths is not None:
                example.file_paths_json = json.dumps(file_paths)
            if source_repo is not None:
                example.source_repo = source_repo

            example.updated_at = datetime.utcnow()
            session.commit()

    def delete_example(self, user_id: str, example_id: int) -> None:
        """Delete portfolio example"""
        with Session(self.engine) as session:
            example = session.exec(
                select(DBPortfolioLibrary)
                .where(DBPortfolioLibrary.user_id == user_id)
                .where(DBPortfolioLibrary.id == example_id)
            ).first()

            if not example:
                raise ValueError(f"Portfolio example {example_id} not found")

            session.delete(example)
            session.commit()


# ============================================================================
# FILE BACKEND IMPLEMENTATION (Fallback/Default)
# ============================================================================

class FileResumeRepository(ResumeRepository):
    """File-based implementation (current system)"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    def get_master_resume(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get master resume from YAML file"""
        if not MASTER_RESUME.exists():
            return None

        with open(MASTER_RESUME, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def save_master_resume(self, user_id: str, resume_data: Dict[str, Any]) -> None:
        """Save master resume to YAML file"""
        with open(MASTER_RESUME, 'w', encoding='utf-8') as f:
            yaml.dump(resume_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


class FileCareerHistoryRepository(CareerHistoryRepository):
    """File-based implementation (current system)"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    def get_career_history(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get career history from YAML file"""
        if not CAREER_HISTORY.exists():
            return None

        with open(CAREER_HISTORY, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def save_career_history(self, user_id: str, history_data: Dict[str, Any]) -> None:
        """Save career history to YAML file"""
        with open(CAREER_HISTORY, 'w', encoding='utf-8') as f:
            yaml.dump(history_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def add_achievement(self, user_id: str, company: str, achievement: Dict[str, Any]) -> None:
        """Add achievement to career history file"""
        if not CAREER_HISTORY.exists():
            raise FileNotFoundError(f"Career history not found at {CAREER_HISTORY}")

        with open(CAREER_HISTORY, 'r', encoding='utf-8') as f:
            history_data = yaml.safe_load(f)

        # Find employment entry
        found = False
        for employment in history_data.get('employment_history', []):
            if employment.get('company', '').lower() == company.lower():
                if 'achievements' not in employment or employment['achievements'] is None:
                    employment['achievements'] = []
                employment['achievements'].append(achievement)
                found = True
                break

        if not found:
            raise ValueError(f"Company '{company}' not found in employment history")

        # Write back
        with open(CAREER_HISTORY, 'w', encoding='utf-8') as f:
            yaml.dump(history_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    def add_technology(self, user_id: str, company: str, technologies: List[str]) -> None:
        """Add technologies to career history file"""
        if not CAREER_HISTORY.exists():
            raise FileNotFoundError(f"Career history not found at {CAREER_HISTORY}")

        with open(CAREER_HISTORY, 'r', encoding='utf-8') as f:
            history_data = yaml.safe_load(f)

        # Find employment entry
        found = False
        for employment in history_data.get('employment_history', []):
            if employment.get('company', '').lower() == company.lower():
                if 'technologies' not in employment or employment['technologies'] is None:
                    employment['technologies'] = []

                # Add new ones (avoid duplicates)
                for tech in technologies:
                    if tech not in employment['technologies']:
                        employment['technologies'].append(tech)

                found = True
                break

        if not found:
            raise ValueError(f"Company '{company}' not found in employment history")

        # Write back
        with open(CAREER_HISTORY, 'w', encoding='utf-8') as f:
            yaml.dump(history_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


# ============================================================================
# BACKEND FACTORY
# ============================================================================

def get_storage_backend() -> tuple[ResumeRepository, CareerHistoryRepository, JobApplicationRepository, PortfolioLibraryRepository]:
    """
    Factory function to create repository instances based on configuration.

    Reads STORAGE_BACKEND from .env:
    - "sqlite": Use SQLite database
    - "file" (default): Use current YAML file system

    Returns:
        Tuple of (ResumeRepository, CareerHistoryRepository, JobApplicationRepository, PortfolioLibraryRepository)
    """
    backend_type = os.getenv("STORAGE_BACKEND", "file")
    user_id = os.getenv("USER_ID", "default")

    logger.info(f"Initializing storage backend: {backend_type}")

    if backend_type == "sqlite":
        db_path = os.getenv("SQLITE_DATABASE_PATH", "./data/resume_agent.db")
        logger.info(f"Using SQLite database: {db_path}")

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        return (
            SQLiteResumeRepository(db_path, user_id),
            SQLiteCareerHistoryRepository(db_path, user_id),
            SQLiteJobApplicationRepository(db_path, user_id),
            SQLitePortfolioLibraryRepository(db_path, user_id)
        )

    else:  # backend_type == "file" or any other value
        logger.info("Using file-based storage (YAML files)")
        # Note: FileJobApplicationRepository not yet implemented
        # For now, this will cause an error - need to implement it
        raise NotImplementedError("File backend for job applications not yet implemented. Please use STORAGE_BACKEND=sqlite")


# Initialize repositories
resume_repo, career_repo, job_app_repo, portfolio_repo = get_storage_backend()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sanitize_filename(text: str) -> str:
    """Convert text to filesystem-safe name."""
    # Remove or replace problematic characters
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = re.sub(r'\s+', '_', text)
    text = text.strip('._')
    return text[:100]  # Limit length


def get_application_directory_name(company: str, job_title: str) -> str:
    """Generate standardized directory name for an application."""
    clean_company = sanitize_filename(company)
    clean_title = sanitize_filename(job_title)
    return f"{clean_company}_{clean_title}"


def load_command_prompt(command_path: str) -> str:
    """Load slash command prompt from .claude/commands/ directory.

    Args:
        command_path: Path relative to .claude/commands/ (e.g., "career/analyze-job")
    """
    command_file = COMMANDS_DIR / f"{command_path}.md"
    if not command_file.exists():
        logger.warning(f"Command file not found: {command_file}")
        raise FileNotFoundError(f"Command not found: {command_path}")

    with open(command_file, 'r', encoding='utf-8') as f:
        return f.read()


async def invoke_slash_command(command_path: str, arguments: str = "", variables: dict[str, str] = None) -> str:
    """
    Execute a slash command using Claude CLI subprocess (uses MAX subscription).

    This approach spawns the `claude` CLI directly, which authenticates with your
    MAX subscription instead of requiring ANTHROPIC_API_KEY. This saves API costs
    during development.

    Supports both patterns:
    - $ARGUMENTS replacement (Claude Code native pattern)
    - [[VARIABLE]] replacement (agentic-drop-zones pattern)

    Args:
        command_path: Path to command relative to .claude/commands/ (e.g., "career/analyze-job")
        arguments: String to replace $ARGUMENTS placeholder OR passed as CLI args
        variables: Dictionary of variables to replace (e.g., {"FILE_PATH": "/path/to/file"})

    Returns:
        Claude's response as text
    """
    if variables is None:
        variables = {}

    # Get Claude CLI path from environment or use default
    claude_cli = os.getenv("CLAUDE_CODE_PATH", "claude")

    # Build command: claude --dangerously-skip-permissions -- /command:name args
    slash_cmd = command_path.replace("/", ":")
    cmd = [claude_cli, "--dangerously-skip-permissions", "--", f"/{slash_cmd}"]

    # Add arguments if provided
    if arguments:
        cmd.append(arguments)

    # Build command string for shell execution (required for .cmd files on Windows)
    cmd_str = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in cmd)

    logger.info(f"Executing slash command via subprocess: {cmd_str}")
    logger.debug(f"Working directory: {PROJECT_ROOT}")

    try:
        # Use create_subprocess_shell on Windows to support .cmd files
        # This allows execution of claude.cmd which is the npm-installed CLI
        process = await asyncio.create_subprocess_shell(
            cmd_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
            env=os.environ.copy()  # Pass environment variables
        )

        # Collect output
        response_text = ""

        async def read_stream(stream, is_stderr=False):
            """Read and collect stream output."""
            nonlocal response_text
            while True:
                line = await stream.readline()
                if not line:
                    break

                decoded = line.decode('utf-8', errors='replace').rstrip()
                if decoded:
                    if not is_stderr:
                        response_text += decoded + "\n"
                    logger.debug(f"{'[stderr]' if is_stderr else '[stdout]'} {decoded}")

        # Handle both streams concurrently
        await asyncio.gather(
            read_stream(process.stdout, is_stderr=False),
            read_stream(process.stderr, is_stderr=True)
        )

        # Wait for process to complete
        return_code = await process.wait()

        if return_code != 0:
            logger.warning(f"Process exited with code {return_code}")
            raise RuntimeError(f"Claude CLI exited with code {return_code}")

        logger.info(f"Slash command completed successfully")
        return response_text.strip()

    except Exception as e:
        logger.error(f"Error executing slash command {command_path}: {e}")
        raise


# ============================================================================
# MCP TOOLS - DATA ACCESS (Read Operations)
# ============================================================================

@mcp.tool()
def data_read_master_resume() -> dict[str, Any]:
    """
    Read the master resume and return validated data.

    Returns:
        Validated master resume data as dict
    """
    logger.info("Reading master resume")

    try:
        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        resume_data = resume_repo.get_master_resume(user_id)

        if resume_data is None:
            return {
                "status": "error",
                "error": "Master resume not found"
            }

        # Validate with Pydantic
        master_resume = MasterResume(**resume_data)

        return {
            "status": "success",
            "data": master_resume.model_dump()
        }

    except Exception as e:
        logger.error(f"Error reading master resume: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_read_career_history() -> dict[str, Any]:
    """
    Read the career history and return validated data.

    Returns:
        Validated career history data as dict
    """
    logger.info("Reading career history")

    try:
        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        history_data = career_repo.get_career_history(user_id)

        if history_data is None:
            return {
                "status": "error",
                "error": "Career history not found"
            }

        # Validate with Pydantic
        career_history = CareerHistory(**history_data)

        return {
            "status": "success",
            "data": career_history.model_dump()
        }

    except Exception as e:
        logger.error(f"Error reading career history: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_read_job_analysis(company: str, job_title: str) -> dict[str, Any]:
    """
    Read job analysis data for a specific application.

    Args:
        company: Company name
        job_title: Job title

    Returns:
        Validated job analysis data as dict, or error if not found
    """
    logger.info(f"Reading job analysis for {company} - {job_title}")

    try:
        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        analysis_data = job_app_repo.get_job_analysis(user_id, company, job_title)

        if analysis_data is None:
            return {
                "status": "error",
                "error": f"Job analysis not found for {company} - {job_title}"
            }

        # Validate with Pydantic
        job_analysis = JobAnalysis(**analysis_data)

        return {
            "status": "success",
            "data": job_analysis.model_dump()
        }

    except Exception as e:
        logger.error(f"Error reading job analysis: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_read_tailored_resume(company: str, job_title: str) -> dict[str, Any]:
    """
    Read tailored resume for a specific application.

    Args:
        company: Company name
        job_title: Job title

    Returns:
        Tailored resume content as dict, or error if not found
    """
    logger.info(f"Reading tailored resume for {company} - {job_title}")

    try:
        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        content = job_app_repo.get_tailored_resume(user_id, company, job_title)

        if content is None:
            return {
                "status": "error",
                "error": f"Tailored resume not found for {company} - {job_title}"
            }

        return {
            "status": "success",
            "content": content
        }

    except Exception as e:
        logger.error(f"Error reading tailored resume: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_read_cover_letter(company: str, job_title: str) -> dict[str, Any]:
    """
    Read cover letter for a specific application.

    Args:
        company: Company name
        job_title: Job title

    Returns:
        Cover letter content as dict, or error if not found
    """
    logger.info(f"Reading cover letter for {company} - {job_title}")

    try:
        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        content = job_app_repo.get_cover_letter(user_id, company, job_title)

        if content is None:
            return {
                "status": "error",
                "error": f"Cover letter not found for {company} - {job_title}"
            }

        return {
            "status": "success",
            "content": content
        }

    except Exception as e:
        logger.error(f"Error reading cover letter: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_list_applications(limit: int = 10) -> dict[str, Any]:
    """
    List recent job applications.

    Args:
        limit: Maximum number of applications to return (default: 10)

    Returns:
        List of application metadata as dict
    """
    logger.info(f"Listing applications (limit: {limit})")

    try:
        user_id = os.getenv("USER_ID", "default")
        applications = job_app_repo.list_applications(user_id, limit)

        return {
            "status": "success",
            "applications": applications,
            "count": len(applications)
        }

    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# MCP TOOLS - DATA ACCESS (Write Operations)
# ============================================================================

@mcp.tool()
def data_write_job_analysis(company: str, job_title: str, job_data: dict) -> dict[str, Any]:
    """
    Save job analysis data for an application.

    Args:
        company: Company name
        job_title: Job title
        job_data: Job analysis data (will be validated against JobAnalysis schema)

    Returns:
        Status dict
    """
    logger.info(f"Writing job analysis for {company} - {job_title}")

    try:
        # Validate data with Pydantic
        job_analysis = JobAnalysis(**job_data)

        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        job_app_repo.save_job_analysis(user_id, job_analysis.model_dump())

        logger.info(f"Job analysis saved for {company} - {job_title}")

        return {
            "status": "success",
            "message": f"Job analysis saved for {company} - {job_title}"
        }

    except Exception as e:
        logger.error(f"Error writing job analysis: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_write_tailored_resume(company: str, job_title: str, content: str, metadata: dict = None) -> dict[str, Any]:
    """
    Save tailored resume for an application.

    Args:
        company: Company name
        job_title: Job title
        content: Resume content text
        metadata: Optional metadata (keywords_used, changes_from_master, etc.)

    Returns:
        Status dict with file path
    """
    logger.info(f"Writing tailored resume for {company} - {job_title}")

    try:
        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        job_app_repo.save_tailored_resume(user_id, company, job_title, content, metadata)

        logger.info(f"Tailored resume saved for {company} - {job_title}")

        return {
            "status": "success",
            "message": f"Tailored resume saved for {company} - {job_title}"
        }

    except Exception as e:
        logger.error(f"Error writing tailored resume: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_write_cover_letter(company: str, job_title: str, content: str, metadata: dict = None) -> dict[str, Any]:
    """
    Save cover letter for an application.

    Args:
        company: Company name
        job_title: Job title
        content: Cover letter content text
        metadata: Optional metadata (talking_points, etc.)

    Returns:
        Status dict with file path
    """
    logger.info(f"Writing cover letter for {company} - {job_title}")

    try:
        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        job_app_repo.save_cover_letter(user_id, company, job_title, content, metadata)

        logger.info(f"Cover letter saved for {company} - {job_title}")

        return {
            "status": "success",
            "message": f"Cover letter saved for {company} - {job_title}"
        }

    except Exception as e:
        logger.error(f"Error writing cover letter: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_write_portfolio_examples(company: str, job_title: str, content: str) -> dict[str, Any]:
    """
    Save portfolio examples for an application.

    Args:
        company: Company name
        job_title: Job title
        content: Portfolio examples content (can be text or structured data)

    Returns:
        Status dict with file path
    """
    logger.info(f"Writing portfolio examples for {company} - {job_title}")

    try:
        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        job_app_repo.save_portfolio_examples(user_id, company, job_title, content)

        logger.info(f"Portfolio examples saved for {company} - {job_title}")

        return {
            "status": "success",
            "message": f"Portfolio examples saved for {company} - {job_title}"
        }

    except Exception as e:
        logger.error(f"Error writing portfolio examples: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_write_master_resume(resume_data: dict) -> dict[str, Any]:
    """
    Write the master resume with validated data.

    Args:
        resume_data: Master resume data (will be validated against MasterResume schema)

    Returns:
        Status dict with file path
    """
    logger.info("Writing master resume")

    try:
        # Validate data with Pydantic
        master_resume = MasterResume(**resume_data)

        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        resume_repo.save_master_resume(user_id, master_resume.model_dump())

        logger.info("Master resume written successfully")

        return {
            "status": "success",
            "message": "Master resume updated successfully"
        }

    except Exception as e:
        logger.error(f"Error writing master resume: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_write_career_history(history_data: dict) -> dict[str, Any]:
    """
    Write the career history with validated data.

    Args:
        history_data: Career history data (will be validated against CareerHistory schema)

    Returns:
        Status dict with file path
    """
    logger.info("Writing career history")

    try:
        # Validate data with Pydantic
        career_history = CareerHistory(**history_data)

        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        career_repo.save_career_history(user_id, career_history.model_dump())

        logger.info("Career history written successfully")

        return {
            "status": "success",
            "message": "Career history updated successfully"
        }

    except Exception as e:
        logger.error(f"Error writing career history: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_add_achievement(company: str, achievement_description: str, metric: str = None) -> dict[str, Any]:
    """
    Add an achievement to a specific employment entry in career history.

    Args:
        company: Company name to add achievement to
        achievement_description: Description of the achievement
        metric: Optional metric (e.g., "95%", "#1", "10x")

    Returns:
        Status dict with updated file path
    """
    logger.info(f"Adding achievement to {company}")

    try:
        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Build achievement object
        achievement = {
            "description": achievement_description
        }
        if metric:
            achievement["metric"] = metric

        # Use repository (abstracts storage backend)
        career_repo.add_achievement(user_id, company, achievement)

        logger.info(f"Achievement added to {company}")

        return {
            "status": "success",
            "company": company,
            "achievement_added": achievement_description,
            "message": f"Achievement added to {company} successfully"
        }

    except Exception as e:
        logger.error(f"Error adding achievement: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_add_technology(company: str, technologies: List[str]) -> dict[str, Any]:
    """
    Add technologies to a specific employment entry in career history.
    Also updates the master resume skills if needed.

    Args:
        company: Company name to add technologies to
        technologies: List of technology names to add

    Returns:
        Status dict with updated file path
    """
    logger.info(f"Adding technologies to {company}: {technologies}")

    try:
        # Get current user ID from config
        user_id = os.getenv("USER_ID", "default")

        # Use repository (abstracts storage backend)
        career_repo.add_technology(user_id, company, technologies)

        logger.info(f"Technologies added to {company}")

        return {
            "status": "success",
            "company": company,
            "technologies_added": technologies,
            "message": f"Added technologies to {company}"
        }

    except Exception as e:
        logger.error(f"Error adding technologies: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# MCP TOOLS - DATA ACCESS (Utility Operations)
# ============================================================================

@mcp.tool()
def data_get_application_path(company: str, job_title: str, ensure_exists: bool = False) -> dict[str, Any]:
    """
    Get application directory/identifier.

    Args:
        company: Company name
        job_title: Job title
        ensure_exists: If True, creates the directory if it doesn't exist

    Returns:
        Dict with directory path and existence status
    """
    logger.info(f"Getting application path for {company} - {job_title}")

    try:
        user_id = os.getenv("USER_ID", "default")
        result = job_app_repo.get_application_path(user_id, company, job_title, ensure_exists)

        return {
            "status": "success",
            **result  # Includes 'directory' and 'exists' keys
        }

    except Exception as e:
        logger.error(f"Error getting application path: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_add_portfolio_example(
    title: str, content: str, company: str = None, project: str = None,
    description: str = None, technologies: List[str] = None,
    file_paths: List[str] = None, source_repo: str = None
) -> dict[str, Any]:
    """
    Add a new example to your job-agnostic portfolio library.

    Args:
        title: Title of the example (e.g., "RAG Pipeline - Customer Matching")
        content: Full content including code, explanations, file content
        company: Company where this was built (optional, e.g., "D&D Worldwide Logistics")
        project: Project name (optional, e.g., "DDWL Platform")
        description: What this example demonstrates (optional)
        technologies: List of technologies used (e.g., ["RAG", "Redis", "Supabase"])
        file_paths: List of relevant file paths (e.g., ["backend/services/matching.py:536"])
        source_repo: GitHub repository URL (optional)

    Returns:
        Dict with status and created example ID
    """
    logger.info(f"Adding portfolio example: {title}")

    try:
        user_id = os.getenv("USER_ID", "default")
        example_id = portfolio_repo.add_example(
            user_id=user_id,
            title=title,
            content=content,
            company=company,
            project=project,
            description=description,
            technologies=technologies,
            file_paths=file_paths,
            source_repo=source_repo
        )

        return {
            "status": "success",
            "example_id": example_id,
            "title": title,
            "message": f"Portfolio example '{title}' added successfully"
        }

    except Exception as e:
        logger.error(f"Error adding portfolio example: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_list_portfolio_examples(
    limit: int = None, technology_filter: str = None, company_filter: str = None
) -> dict[str, Any]:
    """
    List portfolio examples with optional filters.

    Args:
        limit: Maximum number of examples to return (optional)
        technology_filter: Filter by specific technology (e.g., "RAG")
        company_filter: Filter by company (e.g., "D&D Worldwide Logistics")

    Returns:
        Dict with status and list of examples
    """
    logger.info(f"Listing portfolio examples (limit={limit}, tech={technology_filter}, company={company_filter})")

    try:
        user_id = os.getenv("USER_ID", "default")
        examples = portfolio_repo.list_examples(
            user_id=user_id,
            limit=limit,
            technology_filter=technology_filter,
            company_filter=company_filter
        )

        return {
            "status": "success",
            "count": len(examples),
            "examples": examples
        }

    except Exception as e:
        logger.error(f"Error listing portfolio examples: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_search_portfolio_examples(query: str, technologies: List[str] = None) -> dict[str, Any]:
    """
    Search portfolio examples by keyword and/or technologies.

    Args:
        query: Search query (searches title, description, content, company, project)
        technologies: Filter by technologies (optional, e.g., ["RAG", "Vector Databases"])

    Returns:
        Dict with status and matching examples
    """
    logger.info(f"Searching portfolio for: {query}")

    try:
        user_id = os.getenv("USER_ID", "default")
        examples = portfolio_repo.search_examples(
            user_id=user_id,
            query=query,
            technologies=technologies
        )

        return {
            "status": "success",
            "query": query,
            "count": len(examples),
            "examples": examples
        }

    except Exception as e:
        logger.error(f"Error searching portfolio: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_get_portfolio_example(example_id: int) -> dict[str, Any]:
    """
    Get a specific portfolio example by ID.

    Args:
        example_id: ID of the portfolio example

    Returns:
        Dict with status and example details
    """
    logger.info(f"Getting portfolio example: {example_id}")

    try:
        user_id = os.getenv("USER_ID", "default")
        example = portfolio_repo.get_example(user_id=user_id, example_id=example_id)

        if not example:
            return {
                "status": "error",
                "error": f"Portfolio example {example_id} not found"
            }

        return {
            "status": "success",
            "example": example
        }

    except Exception as e:
        logger.error(f"Error getting portfolio example: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_update_portfolio_example(
    example_id: int, title: str = None, content: str = None,
    company: str = None, project: str = None, description: str = None,
    technologies: List[str] = None, file_paths: List[str] = None,
    source_repo: str = None
) -> dict[str, Any]:
    """
    Update an existing portfolio example.

    Args:
        example_id: ID of the example to update
        title: New title (optional)
        content: New content (optional)
        company: New company (optional)
        project: New project (optional)
        description: New description (optional)
        technologies: New technologies list (optional)
        file_paths: New file paths list (optional)
        source_repo: New source repo URL (optional)

    Returns:
        Dict with status
    """
    logger.info(f"Updating portfolio example: {example_id}")

    try:
        user_id = os.getenv("USER_ID", "default")
        portfolio_repo.update_example(
            user_id=user_id,
            example_id=example_id,
            title=title,
            content=content,
            company=company,
            project=project,
            description=description,
            technologies=technologies,
            file_paths=file_paths,
            source_repo=source_repo
        )

        return {
            "status": "success",
            "example_id": example_id,
            "message": f"Portfolio example {example_id} updated successfully"
        }

    except Exception as e:
        logger.error(f"Error updating portfolio example: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@mcp.tool()
def data_delete_portfolio_example(example_id: int) -> dict[str, Any]:
    """
    Delete a portfolio example.

    Args:
        example_id: ID of the example to delete

    Returns:
        Dict with status
    """
    logger.info(f"Deleting portfolio example: {example_id}")

    try:
        user_id = os.getenv("USER_ID", "default")
        portfolio_repo.delete_example(user_id=user_id, example_id=example_id)

        return {
            "status": "success",
            "example_id": example_id,
            "message": f"Portfolio example {example_id} deleted successfully"
        }

    except Exception as e:
        logger.error(f"Error deleting portfolio example: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# MCP TOOLS (Actions the server can perform)
# ============================================================================

@mcp.tool()
async def analyze_job(job_url: str) -> dict[str, Any]:
    """
    Analyze a job posting and extract structured requirements.

    Executes the /career:analyze-job slash command which:
    - Fetches the job posting from the URL
    - Extracts company, role, requirements, and skills
    - Assesses match with your master resume
    - Provides application recommendations

    Args:
        job_url: URL to the job posting (e.g., https://japan-dev.com/jobs/...)

    Returns:
        Analysis results with match score and recommendations
    """
    logger.info(f"Analyzing job: {job_url}")

    try:
        # Execute the career:analyze-job slash command
        result_text = await invoke_slash_command(
            "career/analyze-job",
            arguments=job_url
        )

        logger.info(f"Job analysis complete")
        return {
            "status": "success",
            "job_url": job_url,
            "analysis": result_text
        }

    except Exception as e:
        logger.error(f"Failed to analyze job: {e}")
        return {
            "status": "error",
            "error": str(e),
            "job_url": job_url
        }


@mcp.tool()
async def tailor_resume(job_url: str) -> dict[str, Any]:
    """
    Tailor your resume for a specific job opportunity.

    Executes the /career:tailor-resume slash command which:
    - Fetches and analyzes the job posting
    - Tailors your master resume for the role
    - Optimizes for ATS compatibility
    - Incorporates relevant keywords
    - Saves the tailored resume to job-applications directory

    Args:
        job_url: URL to job posting

    Returns:
        Status and information about the tailored resume
    """
    logger.info(f"Tailoring resume for job: {job_url}")

    try:
        # Execute the career:tailor-resume slash command
        result_text = await invoke_slash_command(
            "career/tailor-resume",
            arguments=job_url
        )

        logger.info(f"Resume tailoring complete")
        return {
            "status": "success",
            "job_url": job_url,
            "result": result_text
        }

    except Exception as e:
        logger.error(f"Failed to tailor resume: {e}")
        return {
            "status": "error",
            "error": str(e),
            "job_url": job_url
        }


@mcp.tool()
async def apply_to_job(job_url: str, include_cover_letter: bool = True) -> dict[str, Any]:
    """
    Complete end-to-end job application workflow.

    Executes the /career:apply slash command which orchestrates:
    1. Job posting analysis
    2. GitHub portfolio search for relevant code examples
    3. Resume tailoring with project highlights
    4. Cover letter generation (if requested)
    5. Saves all artifacts to job-applications directory

    This is the primary tool - it handles the complete application process.

    Args:
        job_url: URL to the job posting
        include_cover_letter: Whether to generate a cover letter (default: True)

    Returns:
        Complete application package with all generated files
    """
    logger.info(f"Starting complete application workflow for: {job_url}")

    try:
        # Execute the career:apply slash command
        # This handles the full workflow end-to-end
        result_text = await invoke_slash_command(
            "career/apply",
            arguments=job_url
        )

        logger.info(f"Application workflow complete")
        return {
            "status": "success",
            "job_url": job_url,
            "include_cover_letter": include_cover_letter,
            "result": result_text
        }

    except Exception as e:
        logger.error(f"Application workflow failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "job_url": job_url
        }


# ============================================================================
# MCP RESOURCES (Data the server exposes)
# ============================================================================

@mcp.resource("resume://master")
def get_master_resume() -> str:
    """
    Get the master resume data in YAML format.

    This is the canonical source of all career history, skills, and achievements.
    Other tools use this data to generate tailored versions.

    Returns:
        Master resume as YAML string (validated via Pydantic schema)
    """
    logger.info("Fetching master resume via resource")

    # Use the data_read_master_resume tool for consistency
    result = data_read_master_resume()

    if result["status"] == "error":
        return f"Error: {result['error']}"

    # Convert back to YAML for resource consumers
    return yaml.dump(result["data"], default_flow_style=False)


@mcp.resource("resume://career-history")
def get_career_history() -> str:
    """
    Get extended career history with additional details.

    Includes detailed project descriptions, achievements, and context
    that may not fit in the condensed master resume.

    Returns:
        Career history as YAML string (validated via Pydantic schema)
    """
    logger.info("Fetching career history via resource")

    # Use the data_read_career_history tool for consistency
    result = data_read_career_history()

    if result["status"] == "error":
        return f"Error: {result['error']}"

    # Convert back to YAML for resource consumers
    return yaml.dump(result["data"], default_flow_style=False)


@mcp.resource("resume://applications/recent")
def get_recent_applications() -> str:
    """
    Get list of recent 10 job applications.

    Returns:
        JSON string with recent application metadata (validated via Pydantic schema)
    """
    logger.info("Fetching recent applications via resource")

    # Use the data_list_applications tool for consistency
    result = data_list_applications(limit=10)

    if result["status"] == "error":
        return json.dumps({"error": result["error"]})

    return json.dumps(result["applications"], indent=2)


# ============================================================================
# MCP PROMPTS (Reusable Prompt Templates)
# ============================================================================

@mcp.prompt()
def analyze_job_posting(job_url: str) -> list[dict]:
    """
    Analyze a job posting and assess match with your background.

    Use this prompt to get a comprehensive analysis of a job opportunity,
    including required skills, responsibilities, and how well your background
    matches the role.

    Args:
        job_url: URL to the job posting

    Returns:
        Prompt messages for analyzing the job posting
    """
    return [
        {
            "role": "user",
            "content": f"""Analyze this job posting and assess my fit for the role:

Job URL: {job_url}

Please:
1. Extract the company name, job title, and key requirements
2. Identify required vs. preferred qualifications
3. List the main responsibilities
4. Extract relevant keywords for ATS optimization
5. Assess my background match (use the resume://master resource)
6. Provide a match score (0-10) with reasoning
7. Suggest specific achievements or projects from my background to highlight

Use the analyze_job tool to fetch and parse the job posting."""
        }
    ]


@mcp.prompt()
def tailor_resume_for_job(job_url: str) -> list[dict]:
    """
    Generate a tailored resume for a specific job opportunity.

    This prompt guides the creation of an ATS-optimized resume that highlights
    relevant experience and incorporates job-specific keywords.

    Args:
        job_url: URL to the job posting

    Returns:
        Prompt messages for tailoring the resume
    """
    return [
        {
            "role": "user",
            "content": f"""Create a tailored resume for this job posting:

Job URL: {job_url}

Please:
1. Analyze the job requirements (use analyze_job tool)
2. Review my master resume (use resume://master resource)
3. Tailor the resume by:
   - Reordering experiences to highlight most relevant roles
   - Emphasizing achievements that match job requirements
   - Incorporating keywords from the job posting naturally
   - Optimizing for ATS compatibility
   - Keeping it to 1-2 pages maximum
4. Save the tailored resume using data_write_tailored_resume

Provide a summary of key changes made and why."""
        }
    ]


@mcp.prompt()
def generate_cover_letter(job_url: str, company_name: str, role_title: str) -> list[dict]:
    """
    Generate a personalized cover letter for a job application.

    Creates a compelling narrative that demonstrates cultural fit and
    explains why you're interested in the specific role and company.

    Args:
        job_url: URL to the job posting
        company_name: Name of the company
        role_title: Title of the role

    Returns:
        Prompt messages for generating the cover letter
    """
    return [
        {
            "role": "user",
            "content": f"""Write a compelling cover letter for this position:

Company: {company_name}
Role: {role_title}
Job URL: {job_url}

Please:
1. Review the job analysis (use data_read_job_analysis tool)
2. Review my career history (use resume://career-history resource)
3. Write a cover letter that:
   - Opens with a strong hook showing genuine interest
   - Tells a story about relevant experience (not just repeating resume)
   - Demonstrates understanding of company's mission/challenges
   - Shows cultural fit and enthusiasm
   - Closes with a clear call to action
   - Keeps it to 3-4 paragraphs maximum
4. Save using data_write_cover_letter

The tone should be professional but personable."""
        }
    ]


@mcp.prompt()
def find_portfolio_examples(job_url: str) -> list[dict]:
    """
    Search GitHub portfolio for code examples matching job requirements.

    Identifies relevant projects and code samples that demonstrate
    the technical skills required for the role.

    Args:
        job_url: URL to the job posting

    Returns:
        Prompt messages for finding portfolio examples
    """
    return [
        {
            "role": "user",
            "content": f"""Find relevant portfolio examples for this job:

Job URL: {job_url}

Please:
1. Analyze the job's technical requirements (use analyze_job tool)
2. Search my GitHub repositories for matching projects
3. Identify code examples that demonstrate:
   - Required technologies/frameworks
   - Similar problem domains
   - Architectural patterns mentioned in the job
   - Best practices and code quality
4. For each example, provide:
   - Repository name and URL
   - Brief description of the project
   - Which job requirement it demonstrates
   - Specific files/code sections to highlight
5. Save findings using data_write_portfolio_examples

Focus on quality over quantity - 3-5 strong examples."""
        }
    ]


@mcp.prompt()
def complete_application_workflow(job_url: str) -> list[dict]:
    """
    Execute the complete job application workflow.

    Orchestrates all steps: job analysis, portfolio search, resume tailoring,
    and cover letter generation.

    Args:
        job_url: URL to the job posting

    Returns:
        Prompt messages for the complete workflow
    """
    return [
        {
            "role": "user",
            "content": f"""Execute the complete application workflow for this job:

Job URL: {job_url}

Please use the apply_to_job tool which will:
1. Analyze the job posting
2. Search GitHub for relevant portfolio examples
3. Tailor the resume
4. Generate a cover letter
5. Save all artifacts to the job-applications directory

After completion, provide a summary with:
- Match score and key insights
- Top 3 portfolio examples found
- Resume changes made
- Cover letter key points
- File paths for all generated documents"""
        }
    ]


@mcp.prompt()
def update_master_resume() -> list[dict]:
    """
    Guide the process of updating the master resume with new achievements.

    Helps add new skills, experiences, or accomplishments to your
    canonical resume.

    Returns:
        Prompt messages for updating the master resume
    """
    return [
        {
            "role": "user",
            "content": """Help me update my master resume.

Please:
1. Review my current master resume (use resume://master resource)
2. Ask me what I'd like to add:
   - New achievement for an existing role?
   - New technology/skill?
   - New employment position?
   - Update to existing content?
3. Once I provide the information, validate it against the MasterResume schema
4. Update the resume using data_write_master_resume
5. Also update career-history.yaml if needed using data_write_career_history

Ensure all updates maintain professional tone and quantify achievements where possible."""
        }
    ]


# ============================================================================
# Server Entry Point
# ============================================================================

def main():
    """Run the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Resume Agent MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio for Claude Desktop, use streamable-http for production)"
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

    logger.info(f"Starting Resume Agent MCP Server")
    logger.info(f"Transport: {args.transport}")

    if args.transport == "streamable-http":
        logger.info(f"HTTP Server: http://{args.host}:{args.port}/mcp")
        mcp.run(transport=args.transport, host=args.host, port=args.port)
    else:
        logger.info("STDIO mode for Claude Desktop")
        mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
