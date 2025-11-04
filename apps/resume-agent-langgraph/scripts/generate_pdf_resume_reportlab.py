"""
Generate a professional PDF resume using reportlab.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import HexColor
from pathlib import Path


def create_resume_pdf(resume_content: str, output_path: str) -> str:
    """
    Create a professional PDF from resume content using reportlab.

    Args:
        resume_content: The resume text content
        output_path: Path where PDF should be saved

    Returns:
        Path to the created PDF file
    """
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Create PDF document
    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    name_style = ParagraphStyle(
        'Name',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=HexColor('#000000'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )

    contact_style = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#3C3C3C'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica',
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=HexColor('#000000'),
        spaceBefore=12,
        spaceAfter=6,
        fontName='Helvetica-Bold',
    )

    job_title_style = ParagraphStyle(
        'JobTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#000000'),
        spaceBefore=6,
        spaceAfter=3,
        fontName='Helvetica-Bold',
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#282828'),
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=3,
        fontName='Helvetica',
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#282828'),
        spaceAfter=3,
        fontName='Helvetica',
    )

    # Build content
    story = []
    lines = resume_content.split('\n')

    first_line = True

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            story.append(Spacer(1, 0.1*inch))
            continue

        # Name (first line)
        if first_line:
            first_line = False
            story.append(Paragraph(line, name_style))
            continue

        # Contact info
        if '@' in line or 'linkedin.com' in line:
            story.append(Paragraph(line, contact_style))
            continue

        # Section headers (all caps)
        if line.isupper() and len(line) < 50 and not line.startswith('•'):
            story.append(Paragraph(line, section_header_style))
            continue

        # Job titles (lines with |)
        if ' | ' in line and not line.startswith('•'):
            story.append(Paragraph(line, job_title_style))
            continue

        # Bullet points
        if line.startswith('•'):
            text = line[1:].strip()
            if text:
                # Use bullet formatting
                bullet_text = f'• {text}'
                story.append(Paragraph(bullet_text, bullet_style))
            continue

        # Regular text
        if line:
            story.append(Paragraph(line, body_style))

    # Build PDF
    doc.build(story)

    return str(output_file)


if __name__ == "__main__":
    # Resume content from database
    resume_content = """KRIS CERNJAVIC
0448 813 513 | cernji@live.com | linkedin.com/in/kris-cernjavic

PROFESSIONAL SUMMARY
Senior Backend Engineer with 8+ years of experience designing and maintaining scalable, high-performance systems. Deep expertise in Python, FastAPI, cloud services, and complex database architectures (PostgreSQL, NoSQL, Redis, Elasticsearch). Proven track record building microservices, orchestrating Docker/Kubernetes deployments, and developing APIs for AI-driven applications. Strong problem-solving skills with experience balancing system performance and cost efficiency.

SKILLS
Backend Development: Python, FastAPI, Django, C#, ASP.NET Core, API Design, Microservices, System Architecture
Databases: PostgreSQL, NoSQL, Redis, Elasticsearch, Graph Databases, SQLite, Vector Databases
Cloud & Infrastructure: AWS, Azure, Cloud Services, Docker, Kubernetes, CI/CD Pipelines
AI & LLM Integration: OpenAI GPT-4, Anthropic Claude, Model Context Protocol (MCP), Multi-agent Systems, RAG Pipelines
Development Tools: Git, Jenkins, Azure DevOps, pytest, asyncio, Pydantic, SQLModel

PROFESSIONAL EXPERIENCE

AI Engineer (Contract) | D&D Worldwide Logistics | January 2024 - Present
• Architected and deployed production multi-agent AI system coordinating 3+ specialized agents using Model Context Protocol (MCP), demonstrating enterprise-level agent orchestration expertise
• Built microservices architecture with Python and FastAPI, integrating multiple LLM providers (OpenAI GPT-4, Anthropic Claude) with intelligent routing for freight forwarding operations
• Designed multi-stage RAG pipeline for semantic search using Supabase pgvector, achieving 90%+ accuracy in customer matching and reducing required agent interactions by 30%+
• Implemented Docker containerization and Redis caching strategy, optimizing API performance and enabling seamless deployment across development and production environments
• Developed MCP server infrastructure enabling discovery and coordination of 4+ specialized tools, achieving 98%+ agent accuracy through Test-Driven Agent Evolution framework
• Architected scalable backend systems handling PostgreSQL and vector databases, balancing performance with cost efficiency for high-volume operations

Senior Consultant (Contract) | Aryza | October 2024 - September 2025
• Developed AI-driven automation frameworks for fintech debt management platform, reducing implementation costs by over 95% through agent-based migration tools using Python
• Engineered workflow automation system with parameterized SQL and PowerShell scripts, enabling non-technical users to execute complex data migrations
• Integrated SQLite backend for Phase 1 database migration (100% completion) and deployed Qdrant vector database as MCP server for long-term agent memory
• Collaborated with product engineering team to standardize migration methodology across clients, improving scalability and operational efficiency
• Built custom MCP servers for data access, demonstrating expertise in backend development principles and design patterns

Senior Software Engineer | Domain | May 2022 - September 2024
• Developed and maintained Elasticsearch-based solutions within Search Platform team, optimizing search performance for high-traffic applications serving millions of daily users
• Built C# .NET REST APIs hosted in AWS, coordinating deployments across multiple indexers and ML inference services to dev/staging/prod environments
• Managed Jenkins CI/CD pipelines, ensuring continuous delivery and operational efficiency across distributed backend systems
• Implemented monitoring solutions ensuring robust metrics for system performance and reliability

Senior Software Engineer | Signature Software | November 2021 - April 2022
• Developed .NET REST APIs facilitating connections between on-premises databases (SQL Server, PostgreSQL) and web/mobile applications
• Created and maintained CI/CD pipelines with Azure DevOps, implementing automated testing with comprehensive code coverage reports
• Designed backend services following software development best practices and design patterns for enterprise applications

Senior Software Engineer | Axcess Consulting | July 2019 - September 2021
• Integrated 3rd party APIs (Xero, SharePoint) with on-premises backend systems, building scalable microservices architecture
• Automated cloud deployments for web apps, databases, and VMs using Azure ARM Templates, demonstrating strong understanding of cloud services and infrastructure
• Configured and maintained CI/CD pipelines using Jenkins, ensuring reliable deployments across development and production environments
• Collaborated with product managers and stakeholders to define and deliver technical requirements for cloud-based solutions

Lead Developer | League of Monkeys | April 2017 - August 2017
• Designed and developed backend tools enabling creators to manage asset catalogues with localized pricing using SQL databases
• Implemented reinforcement learning system using Python and TensorFlow to train AI-controlled vehicles, running distributed training simulations
• Served as Build Master and CI/CD engineer for Android and iOS pipelines, coordinating releases across multiple platforms"""

    # Create PDF
    output_path = "D:/source/Cernji-Agents/job-applications/Tektome_Senior_Software_Engineer/Kris_Cernjavic_Resume_Tektome.pdf"

    result = create_resume_pdf(resume_content, output_path)
    print(f"PDF created successfully: {result}")
