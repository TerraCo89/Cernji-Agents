# Claude Skills Cookbook - Python Examples

Practical code examples for building, testing, and managing custom Claude Skills.

## Table of Contents
- [Environment Setup](#environment-setup)
- [Creating Custom Skills](#creating-custom-skills)
- [Managing Skills](#managing-skills)
- [Testing Skills](#testing-skills)
- [Skill Versioning](#skill-versioning)
- [Utility Functions](#utility-functions)

---

## Environment Setup

### Basic Setup

```python
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from anthropic import Anthropic
from anthropic.lib import files_from_dir
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

if not API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY not found. "
        "Copy .env.example to .env and add your API key."
    )

# Initialize client with Skills beta
client = Anthropic(
    api_key=API_KEY,
    default_headers={"anthropic-beta": "skills-2025-10-02"}
)

# Setup directories
SKILLS_DIR = Path.cwd() / "custom_skills"
OUTPUT_DIR = Path.cwd() / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

print("✓ API key loaded")
print(f"✓ Using model: {MODEL}")
print(f"✓ Custom skills directory: {SKILLS_DIR}")
print(f"✓ Output directory: {OUTPUT_DIR}")
```

---

## Creating Custom Skills

### Create Skill from Directory

```python
def create_skill(
    client: Anthropic,
    skill_path: str,
    display_title: str
) -> dict[str, Any]:
    """
    Create a new custom skill from a directory.

    Args:
        client: Anthropic client instance
        skill_path: Path to skill directory
        display_title: Human-readable skill name

    Returns:
        Dictionary with skill_id, version, and metadata
    """
    try:
        # Create skill using files_from_dir
        skill = client.beta.skills.create(
            display_title=display_title,
            files=files_from_dir(skill_path)
        )

        return {
            "success": True,
            "skill_id": skill.id,
            "display_title": skill.display_title,
            "latest_version": skill.latest_version,
            "created_at": skill.created_at,
            "source": skill.source,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Usage example
result = create_skill(
    client,
    skill_path="./custom_skills/financial-analyzer",
    display_title="Financial Ratio Analyzer"
)

if result["success"]:
    print(f"✅ Skill created: {result['skill_id']}")
    print(f"   Version: {result['latest_version']}")
else:
    print(f"❌ Error: {result['error']}")
```

### Create Multiple Skills

```python
# Define skills to create
skills_to_create = [
    {
        "path": SKILLS_DIR / "analyzing-financial-statements",
        "title": "Financial Ratio Analyzer",
    },
    {
        "path": SKILLS_DIR / "brand-guidelines-skill",
        "title": "Corporate Brand Guidelines",
    },
    {
        "path": SKILLS_DIR / "financial-modeling-suite",
        "title": "Financial Modeling Suite",
    },
]

# Create all skills
created_skills = {}

for skill_def in skills_to_create:
    print(f"\nCreating skill: {skill_def['title']}...")

    result = create_skill(
        client,
        str(skill_def["path"]),
        skill_def["title"]
    )

    if result["success"]:
        created_skills[skill_def["title"]] = result["skill_id"]
        print(f"✅ Created: {result['skill_id']}")
    else:
        print(f"❌ Failed: {result['error']}")

print(f"\n📊 Successfully created {len(created_skills)} skill(s)")
```

---

## Managing Skills

### List Custom Skills

```python
def list_custom_skills(client: Anthropic) -> list[dict[str, Any]]:
    """
    List all custom skills in the workspace.

    Returns:
        List of skill dictionaries
    """
    try:
        skills_response = client.beta.skills.list(source="custom")

        skills = []
        for skill in skills_response.data:
            skills.append({
                "skill_id": skill.id,
                "display_title": skill.display_title,
                "latest_version": skill.latest_version,
                "created_at": skill.created_at,
                "updated_at": skill.updated_at,
            })

        return skills
    except Exception as e:
        print(f"Error listing skills: {e}")
        return []


# Usage
skills = list_custom_skills(client)
print(f"Found {len(skills)} custom skill(s):")
for skill in skills:
    print(f"  • {skill['display_title']} (v{skill['latest_version']})")
```

### Delete Skill

```python
def delete_skill(client: Anthropic, skill_id: str) -> bool:
    """
    Delete a custom skill.

    Args:
        client: Anthropic client
        skill_id: ID of skill to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        client.beta.skills.delete(skill_id)
        return True
    except Exception as e:
        print(f"Error deleting skill {skill_id}: {e}")
        return False


# Usage
if delete_skill(client, "skill-abc123"):
    print("✅ Skill deleted successfully")
else:
    print("❌ Failed to delete skill")
```

### Review and Cleanup Skills

```python
def review_and_cleanup_skills(client, dry_run=True):
    """
    Review all skills and optionally clean up specified skills.

    Args:
        client: Anthropic client
        dry_run: If True, only show what would be deleted
    """
    # Get all current skills
    all_skills = list_custom_skills(client)

    # Skills created by notebook/script
    notebook_skill_names = [
        "Financial Ratio Analyzer",
        "Corporate Brand Guidelines",
        "Financial Modeling Suite",
    ]

    # Categorize skills
    notebook_skills = []
    other_skills = []

    for skill in all_skills:
        if skill["display_title"] in notebook_skill_names:
            notebook_skills.append(skill)
        else:
            other_skills.append(skill)

    print("=" * 70)
    print("SKILL INVENTORY REPORT")
    print("=" * 70)

    print(f"\nTotal custom skills: {len(all_skills)}")

    if notebook_skills:
        print(f"\n📚 Target skills ({len(notebook_skills)}):")
        for skill in notebook_skills:
            print(f"   • {skill['display_title']}")
            print(f"     ID: {skill['skill_id']}")
            print(f"     Version: {skill['latest_version']}")

    if other_skills:
        print(f"\n🔧 Other skills ({len(other_skills)}):")
        for skill in other_skills:
            print(f"   • {skill['display_title']} (v{skill['latest_version']})")

    if notebook_skills:
        print("\n" + "=" * 70)
        print("CLEANUP OPTIONS")
        print("=" * 70)

        if dry_run:
            print("\n🔍 DRY RUN - No skills will be deleted")
            print("\nTo delete, run with dry_run=False")
        else:
            print("\n⚠️ DELETING SKILLS...")
            success_count = 0
            for skill in notebook_skills:
                if delete_skill(client, skill["skill_id"]):
                    print(f"   ✅ Deleted: {skill['display_title']}")
                    success_count += 1
                else:
                    print(f"   ❌ Failed: {skill['display_title']}")

            print(f"\n📊 Deleted {success_count}/{len(notebook_skills)} skills")

    return {
        "total_skills": len(all_skills),
        "notebook_skills": len(notebook_skills),
        "other_skills": len(other_skills),
    }


# Usage
cleanup_summary = review_and_cleanup_skills(client, dry_run=True)
```

---

## Testing Skills

### Test Skill with Prompt

```python
def test_skill(
    client: Anthropic,
    skill_id: str,
    test_prompt: str,
    model: str = "claude-sonnet-4-5-20250929",
) -> Any:
    """
    Test a custom skill with a prompt.

    Args:
        client: Anthropic client
        skill_id: ID of skill to test
        test_prompt: Prompt to test the skill
        model: Model to use for testing

    Returns:
        Response from Claude
    """
    response = client.beta.messages.create(
        model=model,
        max_tokens=4096,
        container={
            "skills": [{
                "type": "custom",
                "skill_id": skill_id,
                "version": "latest"
            }]
        },
        tools=[{
            "type": "code_execution_20250825",
            "name": "code_execution"
        }],
        messages=[{
            "role": "user",
            "content": test_prompt
        }],
        betas=[
            "code-execution-2025-08-25",
            "files-api-2025-04-14",
            "skills-2025-10-02",
        ],
    )

    return response


# Usage example
test_prompt = """
Analyze these financial statements for Q4 2024:
- Revenue: $2.5M
- Operating Expenses: $1.8M
- Net Income: $650K
- Total Assets: $8.2M
- Total Liabilities: $3.1M
"""

response = test_skill(
    client,
    skill_id="skill-abc123",
    test_prompt=test_prompt
)

# Extract and print response
for block in response.content:
    if hasattr(block, 'text'):
        print(block.text)
```

### Check for Conflicting Skills

```python
def check_conflicting_skills(client, skill_titles_to_create):
    """
    Check for existing skills that might conflict with new ones.

    Args:
        client: Anthropic client
        skill_titles_to_create: List of skill titles to check

    Returns:
        List of conflicting skills
    """
    existing_skills = list_custom_skills(client)
    conflicting_skills = []

    if existing_skills:
        print(f"Found {len(existing_skills)} existing skill(s):")
        for skill in existing_skills:
            print(f"  - {skill['display_title']} (ID: {skill['skill_id']})")

            if skill["display_title"] in skill_titles_to_create:
                conflicting_skills.append(skill)

        if conflicting_skills:
            print(f"\n⚠️ Found {len(conflicting_skills)} conflicting skill(s):")
            for skill in conflicting_skills:
                print(f"  - {skill['display_title']} (ID: {skill['skill_id']})")

            return conflicting_skills
        else:
            print("\n✅ No conflicts found!")
    else:
        print("✅ No existing skills found. Ready to create!")

    return []


# Usage
skill_titles = [
    "Financial Ratio Analyzer",
    "Corporate Brand Guidelines",
]

conflicts = check_conflicting_skills(client, skill_titles)
```

---

## Skill Versioning

### Create New Skill Version

```python
def create_skill_version(
    client: Anthropic,
    skill_id: str,
    skill_path: str
) -> dict[str, Any]:
    """
    Create a new version of an existing skill.

    Args:
        client: Anthropic client
        skill_id: ID of existing skill
        skill_path: Path to updated skill directory

    Returns:
        Dictionary with version info or error
    """
    try:
        version = client.beta.skills.versions.create(
            skill_id=skill_id,
            files=files_from_dir(skill_path)
        )

        return {
            "success": True,
            "version": version.version,
            "created_at": version.created_at,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Usage example
result = create_skill_version(
    client,
    skill_id="skill-abc123",
    skill_path="./custom_skills/financial-analyzer-v2"
)

if result["success"]:
    print(f"✅ Version {result['version']} created")
    print(f"   Created at: {result['created_at']}")
else:
    print(f"❌ Error: {result['error']}")
```

### Version History Example

```python
# After creating multiple versions
print("📊 Version History:")
print("   v1: Original skill with basic features")
print("   v2: Enhanced with healthcare benchmarks")
print("   v3: Added real-time data integration")
```

---

## Utility Functions

### Extract File IDs from Response

```python
def extract_file_ids(response) -> list[str]:
    """Extract all file IDs from a Claude response."""
    file_ids = []

    for block in response.content:
        if block.type == 'tool_use' and block.name == 'code_execution':
            for result_block in block.content:
                if hasattr(result_block, 'file_id'):
                    file_ids.append(result_block.file_id)

    return file_ids


# Usage
file_ids = extract_file_ids(response)
print(f"Found {len(file_ids)} generated file(s)")
```

### Download Generated Files

```python
def download_file(client: Anthropic, file_id: str, output_path: Path):
    """Download a file from Claude's response."""
    try:
        file_content = client.beta.files.download(
            file_id=file_id,
            betas=["files-api-2025-04-14"]
        )

        with open(output_path, "wb") as f:
            file_content.write_to_file(f.name)

        print(f"✅ Downloaded: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error downloading {file_id}: {e}")
        return False


# Usage
for file_id in file_ids:
    download_file(
        client,
        file_id,
        OUTPUT_DIR / f"{file_id}.xlsx"
    )
```

---

## Complete Workflow Example

```python
# 1. Setup
client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    default_headers={"anthropic-beta": "skills-2025-10-02"}
)

# 2. Check for conflicts
conflicts = check_conflicting_skills(client, ["My Skill"])

# 3. Create skill
result = create_skill(
    client,
    skill_path="./custom_skills/my-skill",
    display_title="My Skill"
)

skill_id = result["skill_id"]

# 4. Test skill
response = test_skill(
    client,
    skill_id=skill_id,
    test_prompt="Test this skill with sample data"
)

# 5. Extract files
file_ids = extract_file_ids(response)

# 6. Download results
for file_id in file_ids:
    download_file(client, file_id, OUTPUT_DIR / f"{file_id}.pdf")

print("✅ Workflow complete!")
```

---

## Best Practices

1. **Always use try-except blocks** for API calls
2. **Validate skill directories** before uploading
3. **Test skills thoroughly** before production use
4. **Version your skills** when making significant changes
5. **Document skill capabilities** in SKILL.md
6. **Use descriptive display titles** for easy identification
7. **Clean up unused skills** to avoid clutter
8. **Monitor API rate limits** when creating multiple skills
9. **Use dry_run mode** when testing cleanup operations
10. **Store skill IDs** for easy reference

---

## Error Handling

```python
def safe_skill_operation(operation_func, *args, **kwargs):
    """
    Safely execute a skill operation with error handling.

    Args:
        operation_func: Function to execute
        *args, **kwargs: Arguments for the function

    Returns:
        Result or None if error
    """
    try:
        return operation_func(*args, **kwargs)
    except anthropic.APIError as e:
        print(f"API Error: {e.message}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None


# Usage
result = safe_skill_operation(
    create_skill,
    client,
    "./custom_skills/my-skill",
    "My Skill"
)
```
