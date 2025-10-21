#!/usr/bin/env python3
"""
Resume Agent - LangChain/LangGraph Implementation

Demonstrates multi-agent orchestration using LangGraph for job applications
requiring LangChain/LangGraph experience.

Architecture:
- LangGraph StateGraph for workflow orchestration
- ChatAnthropic for LLM invocation
- Pydantic models for data validation
- Tool calling for GitHub/web searches
- Checkpointing for state persistence

Key Patterns:
- Multi-agent collaboration
- Conditional routing
- RAG over resume history
- Tool calling with structured output
- State management and persistence
"""

import os
from typing import TypedDict, Optional, Annotated, Sequence, List, Dict, Any
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# LangChain core imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.tools import tool
from langchain_core.runnables import RunnablePassthrough

# LangChain model imports
from langchain_anthropic import ChatAnthropic

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

# Vector store for RAG (optional but impressive for portfolio)
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# ============================================================================
# PYDANTIC SCHEMAS (Reuse existing ones)
# ============================================================================

class PersonalInfo(BaseModel):
    """Personal contact information"""
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    title: Optional[str] = None


class Employment(BaseModel):
    """Employment history entry"""
    company: str
    position: Optional[str] = None
    title: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    description: str
    technologies: List[str] = Field(default_factory=list)
    achievements: Optional[List[Dict[str, str]]] = None


class JobAnalysis(BaseModel):
    """Structured job posting data"""
    url: str
    fetched_at: str
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


class MasterResume(BaseModel):
    """Master resume data structure"""
    personal_info: PersonalInfo
    about_me: Optional[str] = None
    professional_summary: Optional[str] = None
    employment_history: List[Employment] = Field(default_factory=list)


# ============================================================================
# LANGGRAPH STATE DEFINITION
# ============================================================================

class ApplicationState(TypedDict):
    """
    State for the job application workflow.

    This TypedDict defines all data that flows through the LangGraph workflow.
    Each node can read from and write to this shared state.
    """
    # Input
    job_url: str
    include_cover_letter: bool

    # Job analysis
    job_analysis: Optional[JobAnalysis]
    match_score: Optional[float]

    # Resume data
    master_resume: Optional[MasterResume]
    tailored_resume: Optional[str]

    # Portfolio
    portfolio_examples: Optional[List[Dict[str, str]]]

    # Cover letter
    cover_letter: Optional[str]

    # Messages for conversation history
    messages: Annotated[Sequence[BaseMessage], "The conversation history"]

    # Output paths
    output_directory: Optional[str]


# ============================================================================
# LANGCHAIN TOOLS (Convert from MCP)
# ============================================================================

@tool
def fetch_job_posting(url: str) -> str:
    """
    Fetch a job posting from a URL using web scraping.

    Args:
        url: Job posting URL

    Returns:
        Raw HTML or text content of the job posting
    """
    # In production, use Playwright or httpx
    # For demo, return mock data
    from langchain_community.document_loaders import WebBaseLoader

    loader = WebBaseLoader(url)
    docs = loader.load()

    return docs[0].page_content if docs else ""


@tool
def search_github_repos(keywords: List[str], technologies: List[str]) -> List[Dict[str, str]]:
    """
    Search GitHub repositories for code examples matching job requirements.

    Args:
        keywords: Search keywords from job description
        technologies: List of technologies to find examples for

    Returns:
        List of relevant repositories with descriptions
    """
    # In production, use GitHub API
    # For demo purposes, return mock data
    return [
        {
            "repo": "user/langchain-rag-example",
            "description": "RAG system using LangChain + FAISS",
            "url": "https://github.com/user/langchain-rag-example",
            "technologies": ["LangChain", "FAISS", "OpenAI"]
        },
        {
            "repo": "user/multi-agent-system",
            "description": "Multi-agent orchestration with LangGraph",
            "url": "https://github.com/user/multi-agent-system",
            "technologies": ["LangGraph", "LangChain", "Anthropic"]
        }
    ]


@tool
def load_master_resume() -> dict:
    """
    Load the master resume from YAML file.

    Returns:
        Master resume data as dictionary
    """
    import yaml

    resume_path = Path("./resumes/kris-cernjavic-resume.yaml")

    if not resume_path.exists():
        raise FileNotFoundError(f"Master resume not found at {resume_path}")

    with open(resume_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@tool
def save_application_files(
    company: str,
    job_title: str,
    resume_content: str,
    cover_letter_content: Optional[str] = None,
    portfolio_content: Optional[str] = None
) -> str:
    """
    Save generated application files to disk.

    Args:
        company: Company name
        job_title: Job title
        resume_content: Tailored resume text
        cover_letter_content: Cover letter text (optional)
        portfolio_content: Portfolio examples (optional)

    Returns:
        Path to the application directory
    """
    # Create application directory
    import re

    def sanitize(text: str) -> str:
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        text = re.sub(r'\s+', '_', text)
        return text[:100]

    dir_name = f"{sanitize(company)}_{sanitize(job_title)}"
    app_dir = Path("./job-applications") / dir_name
    app_dir.mkdir(parents=True, exist_ok=True)

    # Save resume
    resume_file = app_dir / f"Resume_{sanitize(company)}.txt"
    resume_file.write_text(resume_content, encoding='utf-8')

    # Save cover letter
    if cover_letter_content:
        cover_file = app_dir / f"CoverLetter_{sanitize(company)}.txt"
        cover_file.write_text(cover_letter_content, encoding='utf-8')

    # Save portfolio examples
    if portfolio_content:
        portfolio_file = app_dir / "portfolio_examples.txt"
        portfolio_file.write_text(portfolio_content, encoding='utf-8')

    return str(app_dir)


# ============================================================================
# LANGCHAIN MODELS & PARSERS
# ============================================================================

# Initialize chat model
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0.7,
    max_tokens=4096
)

# Model with structured output for job analysis
job_analysis_llm = llm.with_structured_output(JobAnalysis)


# ============================================================================
# LANGGRAPH NODES (Agents)
# ============================================================================

def job_analyzer_node(state: ApplicationState) -> Dict[str, Any]:
    """
    Node 1: Fetch and analyze job posting.

    Uses LangChain structured output to parse job requirements.
    """
    job_url = state["job_url"]

    # Fetch job posting content
    job_content = fetch_job_posting.invoke({"url": job_url})

    # Create analysis prompt
    analysis_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert job posting analyzer. Extract structured information
from job postings including requirements, responsibilities, and keywords for ATS optimization."""),
        ("human", """Analyze this job posting and extract:
- Company name and job title
- Location and salary range (if mentioned)
- Required qualifications
- Preferred qualifications
- Key responsibilities
- ATS keywords
- Ideal candidate profile

Job Posting:
{job_content}

URL: {job_url}
""")
    ])

    # Create chain with structured output
    chain = analysis_prompt | job_analysis_llm

    # Execute analysis
    job_analysis = chain.invoke({
        "job_content": job_content,
        "job_url": job_url
    })

    # Calculate match score (simplified - could be more sophisticated)
    match_score = 0.75  # Placeholder

    return {
        "job_analysis": job_analysis,
        "match_score": match_score,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"✓ Analyzed job posting for {job_analysis.company} - {job_analysis.job_title}")
        ]
    }


def portfolio_finder_node(state: ApplicationState) -> Dict[str, Any]:
    """
    Node 2: Search GitHub portfolio for relevant code examples.

    Demonstrates tool calling in LangChain.
    """
    job_analysis = state["job_analysis"]

    if not job_analysis:
        return {"messages": state.get("messages", [])}

    # Search for relevant repos
    portfolio_examples = search_github_repos.invoke({
        "keywords": job_analysis.keywords[:5],
        "technologies": job_analysis.keywords[:10]
    })

    return {
        "portfolio_examples": portfolio_examples,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"✓ Found {len(portfolio_examples)} relevant portfolio examples")
        ]
    }


def resume_writer_node(state: ApplicationState) -> Dict[str, Any]:
    """
    Node 3: Tailor resume for the specific job.

    Uses few-shot prompting and LCEL chains.
    """
    job_analysis = state["job_analysis"]
    master_resume = state.get("master_resume")

    # Load master resume if not in state
    if not master_resume:
        master_resume_data = load_master_resume.invoke({})
        master_resume = MasterResume(**master_resume_data)

    # Create resume tailoring prompt
    resume_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert resume writer specializing in ATS optimization.
Tailor resumes to highlight relevant experience and incorporate job-specific keywords naturally."""),
        ("human", """Create a tailored resume for this job opportunity:

Job Title: {job_title}
Company: {company}
Required Skills: {required_skills}
Keywords: {keywords}

Master Resume:
{master_resume}

Portfolio Examples:
{portfolio_examples}

Guidelines:
- Reorder experiences to highlight most relevant roles
- Incorporate keywords naturally
- Quantify achievements
- Keep to 1-2 pages
- Optimize for ATS parsing

Output the complete tailored resume in plain text format.""")
    ])

    # Build chain
    chain = resume_prompt | llm

    # Execute
    tailored_resume = chain.invoke({
        "job_title": job_analysis.job_title,
        "company": job_analysis.company,
        "required_skills": ", ".join(job_analysis.required_qualifications[:10]),
        "keywords": ", ".join(job_analysis.keywords[:15]),
        "master_resume": str(master_resume.model_dump()),
        "portfolio_examples": str(state.get("portfolio_examples", []))
    })

    return {
        "master_resume": master_resume,
        "tailored_resume": tailored_resume.content,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"✓ Created tailored resume")
        ]
    }


def cover_letter_writer_node(state: ApplicationState) -> Dict[str, Any]:
    """
    Node 4: Generate personalized cover letter.

    Uses chain-of-thought prompting for storytelling.
    """
    if not state.get("include_cover_letter", True):
        return {"messages": state.get("messages", [])}

    job_analysis = state["job_analysis"]
    master_resume = state["master_resume"]

    # Create cover letter prompt
    cover_letter_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert cover letter writer. Create compelling narratives
that demonstrate cultural fit and genuine interest while highlighting relevant experience."""),
        ("human", """Write a personalized cover letter for this position:

Company: {company}
Role: {job_title}
Candidate Profile: {candidate_profile}

My Background:
{professional_summary}

Recent Achievements:
{achievements}

Guidelines:
- Open with a strong hook
- Tell a story (don't repeat resume)
- Show cultural fit and enthusiasm
- 3-4 paragraphs maximum
- Professional but personable tone

Write the complete cover letter.""")
    ])

    # Extract achievements from resume
    achievements = []
    for emp in master_resume.employment_history[:2]:  # Last 2 roles
        if emp.achievements:
            achievements.extend([a.get('description', '') for a in emp.achievements[:2]])

    # Build chain
    chain = cover_letter_prompt | llm

    # Execute
    cover_letter = chain.invoke({
        "company": job_analysis.company,
        "job_title": job_analysis.job_title,
        "candidate_profile": job_analysis.candidate_profile,
        "professional_summary": master_resume.professional_summary or "",
        "achievements": "\n- " + "\n- ".join(achievements[:5])
    })

    return {
        "cover_letter": cover_letter.content,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"✓ Generated cover letter")
        ]
    }


def save_files_node(state: ApplicationState) -> Dict[str, Any]:
    """
    Node 5: Save all generated files to disk.

    Final node that persists the application materials.
    """
    job_analysis = state["job_analysis"]

    # Format portfolio examples
    portfolio_content = None
    if state.get("portfolio_examples"):
        portfolio_content = "\n\n".join([
            f"**{ex['repo']}**\n{ex['description']}\n{ex['url']}\nTechnologies: {', '.join(ex['technologies'])}"
            for ex in state["portfolio_examples"]
        ])

    # Save files
    output_dir = save_application_files.invoke({
        "company": job_analysis.company,
        "job_title": job_analysis.job_title,
        "resume_content": state["tailored_resume"],
        "cover_letter_content": state.get("cover_letter"),
        "portfolio_content": portfolio_content
    })

    return {
        "output_directory": output_dir,
        "messages": state.get("messages", []) + [
            AIMessage(content=f"✓ Saved application materials to {output_dir}")
        ]
    }


# ============================================================================
# LANGGRAPH WORKFLOW
# ============================================================================

def create_application_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for job applications.

    This demonstrates:
    - Multi-agent orchestration
    - State management
    - Conditional routing
    - Tool integration
    """
    # Create graph
    workflow = StateGraph(ApplicationState)

    # Add nodes (agents)
    workflow.add_node("analyze_job", job_analyzer_node)
    workflow.add_node("find_portfolio", portfolio_finder_node)
    workflow.add_node("write_resume", resume_writer_node)
    workflow.add_node("write_cover_letter", cover_letter_writer_node)
    workflow.add_node("save_files", save_files_node)

    # Define edges (workflow)
    workflow.add_edge(START, "analyze_job")
    workflow.add_edge("analyze_job", "find_portfolio")
    workflow.add_edge("find_portfolio", "write_resume")
    workflow.add_edge("write_resume", "write_cover_letter")
    workflow.add_edge("write_cover_letter", "save_files")
    workflow.add_edge("save_files", END)

    return workflow


def create_application_workflow_with_conditional_routing() -> StateGraph:
    """
    Advanced workflow with conditional routing based on match score.

    This demonstrates:
    - Conditional edges
    - Decision nodes
    - Dynamic workflow paths
    """
    workflow = StateGraph(ApplicationState)

    # Add all nodes
    workflow.add_node("analyze_job", job_analyzer_node)
    workflow.add_node("find_portfolio", portfolio_finder_node)
    workflow.add_node("write_resume", resume_writer_node)
    workflow.add_node("write_cover_letter", cover_letter_writer_node)
    workflow.add_node("save_files", save_files_node)

    # Define conditional routing function
    def should_continue(state: ApplicationState) -> str:
        """Route based on match score."""
        match_score = state.get("match_score", 0)

        if match_score >= 0.7:
            # High match - proceed with full workflow
            return "find_portfolio"
        else:
            # Low match - skip portfolio search to save time
            return "write_resume"

    # Add conditional edges
    workflow.add_edge(START, "analyze_job")
    workflow.add_conditional_edges(
        "analyze_job",
        should_continue,
        {
            "find_portfolio": "find_portfolio",
            "write_resume": "write_resume"
        }
    )
    workflow.add_edge("find_portfolio", "write_resume")
    workflow.add_edge("write_resume", "write_cover_letter")
    workflow.add_edge("write_cover_letter", "save_files")
    workflow.add_edge("save_files", END)

    return workflow


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def apply_to_job_langchain(job_url: str, include_cover_letter: bool = True) -> Dict[str, Any]:
    """
    Execute the complete job application workflow using LangChain/LangGraph.

    Args:
        job_url: URL to the job posting
        include_cover_letter: Whether to generate a cover letter

    Returns:
        Final state with all generated materials
    """
    # Create workflow
    workflow = create_application_workflow()

    # Add memory/checkpointing for persistence
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    # Initialize state
    initial_state = ApplicationState(
        job_url=job_url,
        include_cover_letter=include_cover_letter,
        messages=[HumanMessage(content=f"Apply to job: {job_url}")]
    )

    # Execute workflow
    config = {"configurable": {"thread_id": "application-001"}}
    final_state = app.invoke(initial_state, config=config)

    return final_state


# ============================================================================
# BONUS: RAG FOR RESUME SEARCH (Portfolio Demonstration)
# ============================================================================

def create_resume_rag_system():
    """
    Create a RAG system for searching resume/career history.

    This demonstrates:
    - Document loading and splitting
    - Vector embeddings
    - Semantic search
    - Retrieval-augmented generation

    Use case: "Find relevant experience for Java backend roles"
    """
    from langchain_community.document_loaders import DirectoryLoader, TextLoader

    # Load career documents
    loader = DirectoryLoader(
        "./resumes",
        glob="*.yaml",
        loader_cls=TextLoader
    )
    docs = loader.load()

    # Split documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    splits = splitter.split_documents(docs)

    # Create embeddings and vector store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vectorstore = FAISS.from_documents(splits, embeddings)

    # Create retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # Create RAG chain
    rag_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a career advisor. Use the following context from the candidate's background to answer questions."),
        ("system", "Context: {context}"),
        ("human", "{question}")
    ])

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt
        | llm
    )

    return rag_chain


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python resume_agent_langchain.py <job_url>")
        sys.exit(1)

    job_url = sys.argv[1]

    print(f"🚀 Starting LangChain/LangGraph job application workflow...")
    print(f"📋 Job URL: {job_url}\n")

    result = apply_to_job_langchain(job_url)

    print("\n✅ Application Complete!")
    print(f"📁 Output directory: {result['output_directory']}")
    print(f"🎯 Match score: {result['match_score']:.0%}")
    print(f"📄 Resume tailored: ✓")
    print(f"✉️ Cover letter: {'✓' if result.get('cover_letter') else '✗'}")
    print(f"💼 Portfolio examples: {len(result.get('portfolio_examples', []))}")