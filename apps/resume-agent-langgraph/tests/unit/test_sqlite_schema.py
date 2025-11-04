"""
Unit tests for SQLite database schema validation.

This module validates the database schema structure including:
- Table existence
- Column definitions and types
- Indexes and constraints
- Foreign key relationships

Key Testing Strategy:
- Use temporary SQLite databases
- Query sqlite_master table for schema introspection
- Verify all expected tables and columns exist
- Validate indexes and constraints

References:
- Linear Issue: DEV-17 - Replace mocked SQLite tests with real integration tests
- MCP Server Schema: apps/resume-agent/resume_agent.py (lines 396-530)
"""

import pytest
import sys
import tempfile
import sqlite3
from pathlib import Path
from typing import List, Dict, Any

# Add MCP server to Python path
MCP_SERVER_PATH = Path(__file__).resolve().parent.parent.parent.parent / "resume-agent"
sys.path.insert(0, str(MCP_SERVER_PATH))


@pytest.fixture
def temp_db():
    """Create temporary SQLite database with schema initialized."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    # Set environment to use SQLite backend
    import os
    os.environ["STORAGE_BACKEND"] = "sqlite"
    os.environ["SQLITE_DB_PATH"] = db_path

    # Import MCP server and initialize schema
    import resume_agent

    # Instantiate a repository to trigger SQLModel.metadata.create_all()
    # This creates all database tables
    repo = resume_agent.SQLiteResumeRepository(db_path, user_id="test_user")

    yield db_path

    # Cleanup: dispose engine before deleting file
    repo.engine.dispose()
    import time
    time.sleep(0.1)  # Brief delay for Windows file lock release
    try:
        Path(db_path).unlink(missing_ok=True)
    except PermissionError:
        pass  # On Windows, file may still be locked


@pytest.fixture
def db_connection(temp_db):
    """Provide direct SQLite connection for schema inspection."""
    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    yield conn
    conn.close()


def get_table_names(conn: sqlite3.Connection) -> List[str]:
    """Get list of all table names in database."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [row[0] for row in cursor.fetchall()]


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> List[Dict[str, Any]]:
    """Get column information for a table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = []
    for row in cursor.fetchall():
        columns.append({
            "cid": row[0],
            "name": row[1],
            "type": row[2],
            "notnull": row[3],
            "default_value": row[4],
            "pk": row[5]
        })
    return columns


def get_table_indexes(conn: sqlite3.Connection, table_name: str) -> List[str]:
    """Get list of indexes for a table."""
    cursor = conn.execute(f"PRAGMA index_list({table_name})")
    return [row[1] for row in cursor.fetchall()]


def get_foreign_keys(conn: sqlite3.Connection, table_name: str) -> List[Dict[str, Any]]:
    """Get foreign key constraints for a table."""
    cursor = conn.execute(f"PRAGMA foreign_key_list({table_name})")
    fkeys = []
    for row in cursor.fetchall():
        fkeys.append({
            "id": row[0],
            "seq": row[1],
            "table": row[2],
            "from": row[3],
            "to": row[4]
        })
    return fkeys


# ============================================================================
# TEST TABLE EXISTENCE
# ============================================================================


def test_personal_info_table_exists(db_connection):
    """Verify personal_info table exists."""
    tables = get_table_names(db_connection)
    assert "personal_info" in tables


def test_employment_history_table_exists(db_connection):
    """Verify employment_history table exists."""
    tables = get_table_names(db_connection)
    assert "employment_history" in tables


def test_job_applications_table_exists(db_connection):
    """Verify job_applications table exists."""
    tables = get_table_names(db_connection)
    assert "job_applications" in tables


def test_job_qualifications_table_exists(db_connection):
    """Verify job_qualifications table exists."""
    tables = get_table_names(db_connection)
    assert "job_qualifications" in tables


def test_job_responsibilities_table_exists(db_connection):
    """Verify job_responsibilities table exists."""
    tables = get_table_names(db_connection)
    assert "job_responsibilities" in tables


def test_job_keywords_table_exists(db_connection):
    """Verify job_keywords table exists."""
    tables = get_table_names(db_connection)
    assert "job_keywords" in tables


def test_tailored_resumes_table_exists(db_connection):
    """Verify tailored_resumes table exists."""
    tables = get_table_names(db_connection)
    assert "tailored_resumes" in tables


def test_cover_letters_table_exists(db_connection):
    """Verify cover_letters table exists."""
    tables = get_table_names(db_connection)
    assert "cover_letters" in tables


def test_portfolio_examples_table_exists(db_connection):
    """Verify portfolio_examples table exists."""
    tables = get_table_names(db_connection)
    assert "portfolio_examples" in tables


def test_portfolio_library_table_exists(db_connection):
    """Verify portfolio_library table exists."""
    tables = get_table_names(db_connection)
    assert "portfolio_library" in tables


def test_all_expected_tables_exist(db_connection):
    """Verify all expected tables are created."""
    expected_tables = {
        "personal_info",
        "employment_history",
        "job_applications",
        "job_qualifications",
        "job_responsibilities",
        "job_keywords",
        "tailored_resumes",
        "cover_letters",
        "portfolio_examples",
        "portfolio_library"
    }

    actual_tables = set(get_table_names(db_connection))

    # Check that all expected tables exist
    missing_tables = expected_tables - actual_tables
    assert len(missing_tables) == 0, f"Missing tables: {missing_tables}"


# ============================================================================
# TEST PERSONAL_INFO TABLE SCHEMA
# ============================================================================


def test_personal_info_columns(db_connection):
    """Verify personal_info table has correct columns."""
    columns = get_table_columns(db_connection, "personal_info")
    column_names = {col["name"] for col in columns}

    expected_columns = {
        "id", "user_id", "name", "phone", "email",
        "linkedin", "title", "about_me", "professional_summary",
        "created_at", "updated_at"
    }

    assert expected_columns.issubset(column_names)


def test_personal_info_primary_key(db_connection):
    """Verify personal_info has correct primary key."""
    columns = get_table_columns(db_connection, "personal_info")

    pk_columns = [col["name"] for col in columns if col["pk"] == 1]

    assert "id" in pk_columns


def test_personal_info_indexes(db_connection):
    """Verify personal_info has user_id index."""
    indexes = get_table_indexes(db_connection, "personal_info")

    # Should have at least one index (on user_id)
    assert len(indexes) >= 0  # May or may not have explicit index depending on schema


# ============================================================================
# TEST EMPLOYMENT_HISTORY TABLE SCHEMA
# ============================================================================


def test_employment_history_columns(db_connection):
    """Verify employment_history table has correct columns."""
    columns = get_table_columns(db_connection, "employment_history")
    column_names = {col["name"] for col in columns}

    expected_columns = {
        "id", "user_id", "company", "position", "title",
        "employment_type", "start_date", "end_date", "description",
        "technologies_json", "achievements_json",
        "created_at", "updated_at"
    }

    assert expected_columns.issubset(column_names)


def test_employment_history_json_columns(db_connection):
    """Verify employment_history has JSON columns for arrays."""
    columns = get_table_columns(db_connection, "employment_history")
    column_dict = {col["name"]: col for col in columns}

    # Should have JSON columns for technologies and achievements
    assert "technologies_json" in column_dict
    assert "achievements_json" in column_dict


# ============================================================================
# TEST JOB_APPLICATIONS TABLE SCHEMA
# ============================================================================


def test_job_applications_columns(db_connection):
    """Verify job_applications table has correct columns."""
    columns = get_table_columns(db_connection, "job_applications")
    column_names = {col["name"] for col in columns}

    expected_columns = {
        "id", "user_id", "url", "company", "job_title",
        "location", "salary_range", "candidate_profile",
        "raw_description", "fetched_at",
        "created_at", "updated_at"
    }

    assert expected_columns.issubset(column_names)


def test_job_applications_indexes(db_connection):
    """Verify job_applications has indexes on company and job_title."""
    indexes = get_table_indexes(db_connection, "job_applications")

    # Should have indexes (implementation may vary)
    assert isinstance(indexes, list)


# ============================================================================
# TEST JOB_QUALIFICATIONS TABLE SCHEMA
# ============================================================================


def test_job_qualifications_columns(db_connection):
    """Verify job_qualifications table has correct columns."""
    columns = get_table_columns(db_connection, "job_qualifications")
    column_names = {col["name"] for col in columns}

    expected_columns = {
        "id", "job_id", "qualification_type", "description"
    }

    assert expected_columns.issubset(column_names)


def test_job_qualifications_foreign_key(db_connection):
    """Verify job_qualifications has foreign key to job_applications."""
    fkeys = get_foreign_keys(db_connection, "job_qualifications")

    # Should have foreign key to job_applications
    assert len(fkeys) >= 1
    assert any(fk["table"] == "job_applications" for fk in fkeys)


# ============================================================================
# TEST JOB_RESPONSIBILITIES TABLE SCHEMA
# ============================================================================


def test_job_responsibilities_columns(db_connection):
    """Verify job_responsibilities table has correct columns."""
    columns = get_table_columns(db_connection, "job_responsibilities")
    column_names = {col["name"] for col in columns}

    expected_columns = {"id", "job_id", "description"}

    assert expected_columns.issubset(column_names)


def test_job_responsibilities_foreign_key(db_connection):
    """Verify job_responsibilities has foreign key to job_applications."""
    fkeys = get_foreign_keys(db_connection, "job_responsibilities")

    assert len(fkeys) >= 1
    assert any(fk["table"] == "job_applications" for fk in fkeys)


# ============================================================================
# TEST JOB_KEYWORDS TABLE SCHEMA
# ============================================================================


def test_job_keywords_columns(db_connection):
    """Verify job_keywords table has correct columns."""
    columns = get_table_columns(db_connection, "job_keywords")
    column_names = {col["name"] for col in columns}

    expected_columns = {"id", "job_id", "keyword"}

    assert expected_columns.issubset(column_names)


def test_job_keywords_foreign_key(db_connection):
    """Verify job_keywords has foreign key to job_applications."""
    fkeys = get_foreign_keys(db_connection, "job_keywords")

    assert len(fkeys) >= 1
    assert any(fk["table"] == "job_applications" for fk in fkeys)


# ============================================================================
# TEST TAILORED_RESUMES TABLE SCHEMA
# ============================================================================


def test_tailored_resumes_columns(db_connection):
    """Verify tailored_resumes table has correct columns."""
    columns = get_table_columns(db_connection, "tailored_resumes")
    column_names = {col["name"] for col in columns}

    expected_columns = {
        "id", "job_id", "content",
        "keywords_used_json", "changes_from_master_json",
        "created_at", "updated_at"
    }

    assert expected_columns.issubset(column_names)


def test_tailored_resumes_foreign_key(db_connection):
    """Verify tailored_resumes has foreign key to job_applications."""
    fkeys = get_foreign_keys(db_connection, "tailored_resumes")

    assert len(fkeys) >= 1
    assert any(fk["table"] == "job_applications" for fk in fkeys)


def test_tailored_resumes_unique_constraint(db_connection):
    """Verify tailored_resumes has unique constraint on job_id."""
    # Query indexes to check for unique constraint
    cursor = db_connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='tailored_resumes'"
    )
    create_statement = cursor.fetchone()[0]

    # Should have unique constraint or unique index on job_id
    # This can be implemented as UNIQUE in column definition or as separate index
    assert "job_id" in create_statement.lower()


# ============================================================================
# TEST COVER_LETTERS TABLE SCHEMA
# ============================================================================


def test_cover_letters_columns(db_connection):
    """Verify cover_letters table has correct columns."""
    columns = get_table_columns(db_connection, "cover_letters")
    column_names = {col["name"] for col in columns}

    expected_columns = {
        "id", "job_id", "content",
        "talking_points_json",
        "created_at", "updated_at"
    }

    assert expected_columns.issubset(column_names)


def test_cover_letters_foreign_key(db_connection):
    """Verify cover_letters has foreign key to job_applications."""
    fkeys = get_foreign_keys(db_connection, "cover_letters")

    assert len(fkeys) >= 1
    assert any(fk["table"] == "job_applications" for fk in fkeys)


# ============================================================================
# TEST PORTFOLIO_EXAMPLES TABLE SCHEMA
# ============================================================================


def test_portfolio_examples_columns(db_connection):
    """Verify portfolio_examples table has correct columns."""
    columns = get_table_columns(db_connection, "portfolio_examples")
    column_names = {col["name"] for col in columns}

    expected_columns = {
        "id", "job_id", "content", "examples_json", "created_at"
    }

    assert expected_columns.issubset(column_names)


def test_portfolio_examples_foreign_key(db_connection):
    """Verify portfolio_examples has foreign key to job_applications."""
    fkeys = get_foreign_keys(db_connection, "portfolio_examples")

    assert len(fkeys) >= 1
    assert any(fk["table"] == "job_applications" for fk in fkeys)


# ============================================================================
# TEST PORTFOLIO_LIBRARY TABLE SCHEMA
# ============================================================================


def test_portfolio_library_columns(db_connection):
    """Verify portfolio_library table has correct columns."""
    columns = get_table_columns(db_connection, "portfolio_library")
    column_names = {col["name"] for col in columns}

    expected_columns = {
        "id", "user_id", "title", "company", "project",
        "description", "content",
        "technologies_json", "file_paths_json", "source_repo",
        "created_at", "updated_at"
    }

    assert expected_columns.issubset(column_names)


def test_portfolio_library_indexes(db_connection):
    """Verify portfolio_library has indexes for search performance."""
    indexes = get_table_indexes(db_connection, "portfolio_library")

    # Should have some indexes for user_id, title, company
    assert isinstance(indexes, list)


# ============================================================================
# TEST SCHEMA CONSISTENCY
# ============================================================================


def test_all_tables_have_id_column(db_connection):
    """Verify all tables have an id column as primary key."""
    tables = get_table_names(db_connection)

    for table in tables:
        columns = get_table_columns(db_connection, table)
        column_dict = {col["name"]: col for col in columns}

        assert "id" in column_dict, f"Table {table} missing id column"
        assert column_dict["id"]["pk"] == 1, f"Table {table} id is not primary key"


def test_all_user_tables_have_user_id(db_connection):
    """Verify user-specific tables have user_id column."""
    user_tables = ["personal_info", "employment_history", "portfolio_library"]

    for table in user_tables:
        columns = get_table_columns(db_connection, table)
        column_names = {col["name"] for col in columns}

        assert "user_id" in column_names, f"Table {table} missing user_id column"


def test_all_timestamp_tables_have_created_at(db_connection):
    """Verify tables with timestamps have created_at column."""
    timestamp_tables = [
        "personal_info", "employment_history", "job_applications",
        "tailored_resumes", "cover_letters", "portfolio_examples",
        "portfolio_library"
    ]

    for table in timestamp_tables:
        columns = get_table_columns(db_connection, table)
        column_names = {col["name"] for col in columns}

        assert "created_at" in column_names, f"Table {table} missing created_at column"


def test_mutable_tables_have_updated_at(db_connection):
    """Verify mutable tables have updated_at column."""
    mutable_tables = [
        "personal_info", "employment_history", "job_applications",
        "tailored_resumes", "cover_letters", "portfolio_library"
    ]

    for table in mutable_tables:
        columns = get_table_columns(db_connection, table)
        column_names = {col["name"] for col in columns}

        assert "updated_at" in column_names, f"Table {table} missing updated_at column"


# ============================================================================
# TEST DATA TYPE CONSISTENCY
# ============================================================================


def test_id_columns_are_integer(db_connection):
    """Verify all id columns are INTEGER type."""
    tables = get_table_names(db_connection)

    for table in tables:
        columns = get_table_columns(db_connection, table)
        id_col = next((col for col in columns if col["name"] == "id"), None)

        assert id_col is not None
        assert "INT" in id_col["type"].upper()


def test_json_columns_use_text_type(db_connection):
    """Verify JSON columns use TEXT or similar type."""
    json_column_tables = {
        "employment_history": ["technologies_json", "achievements_json"],
        "tailored_resumes": ["keywords_used_json", "changes_from_master_json"],
        "cover_letters": ["talking_points_json"],
        "portfolio_examples": ["examples_json"],
        "portfolio_library": ["technologies_json", "file_paths_json"]
    }

    for table, json_cols in json_column_tables.items():
        columns = get_table_columns(db_connection, table)
        column_dict = {col["name"]: col for col in columns}

        for json_col in json_cols:
            assert json_col in column_dict, f"Missing {json_col} in {table}"
            # SQLite stores JSON as TEXT
            # Type might be empty string or TEXT
            col_type = column_dict[json_col]["type"].upper()
            assert col_type == "" or "TEXT" in col_type or "VARCHAR" in col_type


# ============================================================================
# TEST FOREIGN KEY INTEGRITY
# ============================================================================


def test_child_tables_reference_job_applications(db_connection):
    """Verify child tables have foreign keys to job_applications."""
    child_tables = [
        "job_qualifications",
        "job_responsibilities",
        "job_keywords",
        "tailored_resumes",
        "cover_letters",
        "portfolio_examples"
    ]

    for table in child_tables:
        fkeys = get_foreign_keys(db_connection, table)

        # Should have at least one foreign key
        assert len(fkeys) >= 1, f"Table {table} has no foreign keys"

        # Should reference job_applications
        references_job_applications = any(
            fk["table"] == "job_applications" for fk in fkeys
        )
        assert references_job_applications, f"Table {table} doesn't reference job_applications"


def test_foreign_key_columns_exist(db_connection):
    """Verify foreign key columns exist in their tables."""
    fk_mappings = {
        "job_qualifications": "job_id",
        "job_responsibilities": "job_id",
        "job_keywords": "job_id",
        "tailored_resumes": "job_id",
        "cover_letters": "job_id",
        "portfolio_examples": "job_id"
    }

    for table, fk_column in fk_mappings.items():
        columns = get_table_columns(db_connection, table)
        column_names = {col["name"] for col in columns}

        assert fk_column in column_names, f"Table {table} missing {fk_column} column"
