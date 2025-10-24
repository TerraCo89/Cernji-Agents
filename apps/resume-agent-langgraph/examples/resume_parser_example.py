"""Example usage of resume parser tool.

This script demonstrates how to use the resume parser functions
to load, parse, and extract information from resume files.
"""

from pathlib import Path
from src.resume_agent.tools.resume_parser import (
    load_master_resume,
    parse_resume_yaml,
    extract_skills_from_resume,
    extract_achievements_from_resume,
)


def main():
    """Demonstrate resume parser usage."""
    print("=" * 60)
    print("Resume Parser Example")
    print("=" * 60)

    # Example 1: Parse YAML string
    print("\n1. Parsing YAML string:")
    yaml_content = """
personal_info:
  name: Jane Smith
  email: jane@example.com
  location: San Francisco, CA

professional_summary: |
  Senior Software Engineer with 8+ years of experience in cloud-native
  architectures, microservices, and DevOps practices.

employment_history:
  - company: CloudTech Inc
    position: Senior Software Engineer
    start_date: "2020-03"
    end_date: Present
    description: Lead backend development for cloud platform
    technologies:
      - Python
      - Kubernetes
      - AWS
      - PostgreSQL
    achievements:
      - description: Reduced infrastructure costs by 35%
        metric: "35% cost reduction"
      - description: Led migration to Kubernetes
      - description: Improved API response time by 50%
        metric: "50% faster"

  - company: StartupCo
    position: Software Engineer
    start_date: "2017-06"
    end_date: "2020-02"
    description: Full-stack development for SaaS platform
    technologies:
      - Python
      - React
      - Docker
    achievements:
      - Built MVP in 3 months
      - Grew user base from 0 to 10,000

skills:
  - Python
  - AWS
  - Kubernetes
  - Docker
  - PostgreSQL
  - React
  - CI/CD
"""

    result = parse_resume_yaml(yaml_content)
    if result["status"] == "success":
        resume_data = result["data"]
        print(f"   Name: {resume_data['personal_info']['name']}")
        print(f"   Email: {resume_data['personal_info']['email']}")
        print(f"   Employment entries: {len(resume_data['employment_history'])}")
    else:
        print(f"   Error: {result['error']}")

    # Example 2: Extract skills
    print("\n2. Extracting skills:")
    if result["status"] == "success":
        skills = extract_skills_from_resume(resume_data)
        print(f"   Total unique skills: {len(skills)}")
        print(f"   Skills: {', '.join(skills[:10])}")
        if len(skills) > 10:
            print(f"   ... and {len(skills) - 10} more")

    # Example 3: Extract achievements
    print("\n3. Extracting achievements:")
    if result["status"] == "success":
        achievements = extract_achievements_from_resume(resume_data)
        print(f"   Total achievements: {len(achievements)}")
        for i, achievement in enumerate(achievements[:3], 1):
            print(f"\n   Achievement {i}:")
            print(f"     Company: {achievement['company']}")
            print(f"     Role: {achievement['role']}")
            print(f"     Achievement: {achievement['achievement']}")
            if "metric" in achievement:
                print(f"     Metric: {achievement['metric']}")
        if len(achievements) > 3:
            print(f"\n   ... and {len(achievements) - 3} more achievements")

    # Example 4: Load from file (if exists)
    print("\n4. Loading from file:")
    # Try to find a resume file in the project
    potential_paths = [
        "job-applications/resumes/career-history.yaml",
        "../../job-applications/resumes/career-history.yaml",
        "../../../job-applications/resumes/career-history.yaml",
    ]

    resume_loaded = False
    for path in potential_paths:
        result = load_master_resume(path)
        if result["status"] == "success":
            print(f"   Successfully loaded from: {path}")
            resume_data = result["data"]
            print(f"   Name: {resume_data['personal_info'].get('name', 'N/A')}")
            resume_loaded = True
            break

    if not resume_loaded:
        print("   No resume file found at expected locations")
        print("   (This is expected if career-history.yaml doesn't exist yet)")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
