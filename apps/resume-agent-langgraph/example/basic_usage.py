"""
Basic usage examples for Resume Agent.

This demonstrates how to use the Resume Agent programmatically.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure API key is set
if not os.getenv("ANTHROPIC_API_KEY"):
    print("❌ Please set ANTHROPIC_API_KEY in your .env file")
    exit(1)


def example_1_basic_optimization():
    """Example 1: Basic resume optimization workflow."""
    from resume_agent import run_resume_agent
    
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Optimization")
    print("="*60)
    
    # Sample resume
    resume = """
    John Doe
    john.doe@email.com | (555) 123-4567
    
    EXPERIENCE
    Software Engineer at TechCorp (2020-2024)
    - Wrote code and fixed bugs
    - Worked with team members
    - Used various technologies
    
    EDUCATION
    BS Computer Science, State University
    
    SKILLS
    Python, JavaScript, some databases
    """
    
    # Run optimization
    result = run_resume_agent(
        resume_text=resume,
        job_posting_url="https://example.com/job",  # Replace with real URL
        thread_id="example-1",
        max_iterations=2,
    )
    
    print(f"\n📊 Results:")
    print(f"   ATS Score: {result['ats_score']}/100")
    print(f"   Skills Found: {len(result['current_skills'])}")
    print(f"   Skill Gaps: {len(result['skill_gaps'])}")
    print(f"   Needs Review: {result['needs_manual_review']}")


def example_2_with_checkpoint():
    """Example 2: Using checkpoints for human-in-the-loop."""
    from resume_agent import run_resume_agent, resume_from_checkpoint
    
    print("\n" + "="*60)
    print("EXAMPLE 2: Checkpoint and Resume")
    print("="*60)
    
    resume = "Your resume text here..."
    
    # Phase 1: Run until checkpoint
    print("\n▶️  Phase 1: Running until checkpoint...")
    result = run_resume_agent(
        resume_text=resume,
        job_posting_url="https://example.com/job",
        thread_id="example-2",
    )
    
    print("\n⏸️  Agent paused for review")
    print(f"   Current ATS Score: {result['ats_score']}")
    
    # Simulate human review
    print("\n👤 Human reviewer checks the optimized resume...")
    print("   (In production, this would be a UI interaction)")
    
    # Phase 2: Resume from checkpoint
    print("\n▶️  Phase 2: Resuming from checkpoint...")
    final_result = resume_from_checkpoint("example-2")
    
    print(f"\n✅ Final Results:")
    print(f"   ATS Score: {final_result['ats_score']}/100")
    print(f"   Approved: {final_result['reviewer_approved']}")


def example_3_custom_graph():
    """Example 3: Creating and using a custom graph configuration."""
    from resume_agent.graphs import compile_resume_agent
    from resume_agent.config import Settings
    
    print("\n" + "="*60)
    print("EXAMPLE 3: Custom Configuration")
    print("="*60)
    
    # Custom settings
    settings = Settings(
        max_iterations=5,  # More iterations
        ats_score_threshold=90,  # Higher threshold
        require_manual_review=False,  # Skip manual review
    )
    
    # Compile with custom settings
    app = compile_resume_agent(checkpointing=False)
    
    # Run
    result = app.invoke({
        "resume_text": "Your resume...",
        "job_posting_url": "https://example.com/job",
        "job_title": "",
        "job_requirements": [],
        "job_skills": [],
        "ats_keywords": [],
        "current_skills": [],
        "experience_summary": "",
        "skill_gaps": [],
        "optimized_sections": [],
        "ats_score": 0,
        "optimization_suggestions": [],
        "needs_manual_review": False,
        "reviewer_approved": False,
        "iteration_count": 0,
        "max_iterations": 5,
        "final_resume": "",
        "cover_letter": "",
    })
    
    print(f"\n📊 Results with custom config:")
    print(f"   Final ATS Score: {result['ats_score']}/100")
    print(f"   Iterations: {result['iteration_count']}")


def example_4_streaming():
    """Example 4: Streaming execution for real-time updates."""
    from resume_agent.graphs import compile_resume_agent
    
    print("\n" + "="*60)
    print("EXAMPLE 4: Streaming Execution")
    print("="*60)
    
    app = compile_resume_agent(checkpointing=False)
    
    initial_state = {
        "resume_text": "Your resume...",
        "job_posting_url": "https://example.com/job",
        "job_title": "",
        "job_requirements": [],
        "job_skills": [],
        "ats_keywords": [],
        "current_skills": [],
        "experience_summary": "",
        "skill_gaps": [],
        "optimized_sections": [],
        "ats_score": 0,
        "optimization_suggestions": [],
        "needs_manual_review": False,
        "reviewer_approved": False,
        "iteration_count": 0,
        "max_iterations": 2,
        "final_resume": "",
        "cover_letter": "",
    }
    
    # Stream execution
    print("\n📡 Streaming updates:")
    for i, chunk in enumerate(app.stream(initial_state), 1):
        print(f"\n   Update {i}: {list(chunk.keys())}")
        # In production, you'd send these updates to a UI


def example_5_tools_only():
    """Example 5: Using tools independently without the full graph."""
    from resume_agent.tools import analyze_resume_ats, calculate_keyword_match
    
    print("\n" + "="*60)
    print("EXAMPLE 5: Using Tools Independently")
    print("="*60)
    
    resume = """
    Senior Developer with 5 years experience.
    Skills: Python, Django, PostgreSQL, Docker, AWS
    """
    
    # ATS Analysis
    ats_result = analyze_resume_ats(resume)
    print(f"\n📊 ATS Analysis:")
    print(f"   Score: {ats_result['ats_score']}/100")
    print(f"   Issues: {len(ats_result['issues'])}")
    print(f"   Warnings: {len(ats_result['warnings'])}")
    
    # Keyword Matching
    job_keywords = ["Python", "Django", "PostgreSQL", "Docker", "Kubernetes"]
    keyword_result = calculate_keyword_match(resume, job_keywords)
    print(f"\n🔑 Keyword Match:")
    print(f"   Match: {keyword_result['match_percentage']:.1f}%")
    print(f"   Matched: {keyword_result['matched_keywords']}")
    print(f"   Missing: {keyword_result['missing_keywords']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("RESUME AGENT - USAGE EXAMPLES")
    print("="*60)
    
    # Run examples
    # Note: Comment out examples that require real API calls
    
    # example_1_basic_optimization()  # Requires API key and real job URL
    # example_2_with_checkpoint()     # Requires API key and real job URL
    # example_3_custom_graph()        # Requires API key and real job URL
    # example_4_streaming()           # Requires API key and real job URL
    example_5_tools_only()          # Works without API key!
    
    print("\n" + "="*60)
    print("✅ Examples complete!")
    print("="*60)
