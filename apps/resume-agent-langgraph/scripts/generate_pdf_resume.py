"""
Generate a professional PDF resume from tailored resume content.
"""

from fpdf import FPDF
from pathlib import Path


class ResumePDF(FPDF):
    """Custom PDF class for resume generation."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(left=15, top=15, right=15)

    def header(self):
        """Override header to keep it clean (no header needed for resume)."""
        pass

    def footer(self):
        """Add page number at bottom."""
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


def create_resume_pdf(resume_content: str, output_path: str) -> str:
    """
    Create a professional PDF from resume content.

    Args:
        resume_content: The resume text content
        output_path: Path where PDF should be saved

    Returns:
        Path to the created PDF file
    """
    pdf = ResumePDF()
    pdf.add_page()

    # Split content into lines
    lines = resume_content.split('\n')

    first_line = True

    for line in lines:
        # Strip whitespace
        original_line = line
        line = line.strip()

        # Skip completely empty lines in content
        if not line:
            pdf.ln(3)
            continue

        # Name (first line) - Large and bold
        if first_line:
            first_line = False
            pdf.set_font('Helvetica', 'B', 16)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, line, 0, 1, 'C')
            pdf.ln(2)
            continue

        # Contact info (line with email/phone)
        if '@' in line or 'linkedin.com' in line:
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(0, 5, line, 0, 1, 'C')
            pdf.ln(3)
            continue

        # Section headers (all caps lines)
        if line.isupper() and len(line) < 50 and not line.startswith('•'):
            pdf.ln(2)
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 6, line, 0, 1, 'L')
            pdf.ln(1)
            continue

        # Job titles or positions (lines with | separator)
        if ' | ' in line and not line.startswith('•'):
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 5, line)
            pdf.ln(1)
            continue

        # Bullet points
        if line.startswith('•'):
            text = line[1:].strip()
            if not text:  # Skip empty bullets
                continue

            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(40, 40, 40)

            # Get current position
            x = pdf.get_x()
            y = pdf.get_y()

            # Draw bullet
            pdf.set_xy(x + 3, y)
            pdf.write(5, '• ')

            # Draw text with indent, ensuring we don't exceed page width
            pdf.set_xy(x + 7, y)

            # Use write_html or multi_cell with proper width
            effective_width = pdf.w - pdf.l_margin - pdf.r_margin - 7
            pdf.multi_cell(effective_width, 5, text)
            continue

        # Regular text (descriptions, skills, etc.)
        # Only process lines with actual content
        if len(line) > 0:
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(40, 40, 40)

            # Ensure we have valid width for multi_cell
            pdf.multi_cell(0, 5, line)

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save PDF
    pdf.output(str(output_file))

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
