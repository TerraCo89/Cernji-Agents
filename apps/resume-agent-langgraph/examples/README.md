# Resume Agent - LangGraph

A production-ready, scalable AI agent for resume optimization built with LangGraph and Claude.

## 🎯 Features

- **Job Posting Analysis**: Automatically scrapes and analyzes job postings to extract requirements
- **ATS Optimization**: Optimizes resumes for Applicant Tracking Systems
- **Keyword Matching**: Intelligent keyword extraction and matching
- **Iterative Optimization**: Multiple optimization rounds with scoring
- **Human-in-the-Loop**: Manual review checkpoints for quality control
- **Modular Architecture**: Scalable, production-ready code structure
- **State Persistence**: Checkpoint and resume capability

## 🏗️ Architecture

```
resume-agent-langgraph/
├── src/
│   ├── resume_agent/
│   │   ├── state/              # State schemas (TypedDict)
│   │   ├── nodes/              # Node implementations
│   │   ├── tools/              # Reusable tools (scraper, ATS analyzer)
│   │   ├── graphs/             # Graph definitions
│   │   │   └── subgraphs/      # Specialized subgraphs
│   │   ├── prompts/            # Centralized prompt templates
│   │   └── config.py           # Configuration management
│   └── cli.py                  # CLI interface
├── tests/                      # Unit and integration tests
├── examples/                   # Usage examples
└── README.md
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd resume-agent-langgraph

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Basic Usage

```python
from resume_agent import run_resume_agent

# Run the agent
result = run_resume_agent(
    resume_text="Your resume content...",
    job_posting_url="https://example.com/job",
    thread_id="my-session",
    max_iterations=3
)

# Resume from checkpoint after manual review
from resume_agent import resume_from_checkpoint
final_result = resume_from_checkpoint("my-session")
```

### CLI Usage

```bash
# Optimize a resume
python src/cli.py optimize \
    --resume my_resume.txt \
    --job-url https://example.com/job \
    --output optimized_resume.txt

# Resume from checkpoint
python src/cli.py resume \
    --thread-id my-session \
    --output final_resume.txt

# Visualize the graph
python src/cli.py visualize
```

## 📊 Graph Structure

The agent follows this workflow:

1. **Analyze Job** → Extract requirements from job posting
2. **Analyze Resume** → Identify skills and gaps
3. **Optimize** → Improve resume for ATS and keywords
4. **Score** → Calculate ATS score and keyword match
5. **Iterate** → Loop back if score < threshold (max 3 times)
6. **Validate** → Check for errors and warnings
7. **Await Approval** → Human checkpoint (pausable)
8. **Finalize** → Generate final resume

### Key Concepts

#### State Management
```python
class ResumeState(TypedDict):
    resume_text: str
    job_posting_url: str
    ats_score: int
    optimized_sections: Annotated[list[dict], add]  # Append-only
    needs_manual_review: bool
    # ... more fields
```

#### Node Functions
```python
def optimize_resume_sections(state: ResumeState) -> dict:
    """Node that optimizes resume sections."""
    # Access full state
    resume = state['resume_text']
    keywords = state['ats_keywords']
    
    # Return partial updates
    return {
        "optimized_sections": [optimized_data],
        "ats_score": new_score,
    }
```

#### Conditional Routing
```python
def should_iterate(state: ResumeState) -> Literal["optimize", "validate"]:
    """Router function for conditional edges."""
    if state['iteration_count'] >= state['max_iterations']:
        return "validate"
    if state['ats_score'] >= 80:
        return "validate"
    return "optimize"
```

## 🔧 Configuration

Edit `.env` or use `config.py`:

```python
from resume_agent.config import Settings

settings = Settings(
    anthropic_api_key="sk-...",
    model_name="claude-sonnet-4-20250514",
    max_iterations=3,
    ats_score_threshold=80,
    require_manual_review=True,
)
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_nodes.py

# Run with coverage
pytest --cov=src/resume_agent tests/
```

## 📦 Project Structure Explained

### State (`state/`)
- **Centralized state schemas** using `TypedDict`
- Type-safe state management
- Clear contracts between nodes

### Nodes (`nodes/`)
- **Single responsibility** - each node does one thing
- **Testable** - pure functions that take state, return updates
- **Reusable** - can be composed into different graphs

### Tools (`tools/`)
- **Utility functions** that nodes can use
- **Stateless** - don't depend on graph state
- **Testable** - can be unit tested independently

### Graphs (`graphs/`)
- **Main workflow** definition
- **Subgraphs** for complex sub-workflows
- **Compilation** logic with checkpointing

### Prompts (`prompts/`)
- **Centralized prompt management**
- Easy to iterate and A/B test
- Version control friendly

## 🎓 Interview Tips

When discussing this architecture:

1. **Separation of Concerns**: Each module has a clear responsibility
2. **Type Safety**: TypedDict for compile-time checks
3. **Testability**: Pure functions, dependency injection
4. **Scalability**: Easy to add new nodes, tools, or subgraphs
5. **Production-Ready**: Config management, error handling, logging

### Key Comparisons

| Concept | Your Experience | LangGraph Equivalent |
|---------|----------------|---------------------|
| Manager-Worker Pattern | Orchestrator with sub-agents | Subgraphs + Send() API |
| State Machine | Game AI FSM | StateGraph with conditional edges |
| Parallel Agents | Multi-threading | Send() for dynamic fan-out |
| Checkpointing | Save/Load game state | MemorySaver with interrupt_before |

## 🚢 Deployment

### Local
```bash
python src/cli.py optimize --resume resume.txt --job-url URL
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["python", "src/cli.py"]
```

### API Server
```python
from fastapi import FastAPI
from resume_agent import compile_resume_agent

app = FastAPI()
agent = compile_resume_agent()

@app.post("/optimize")
async def optimize_resume(resume: str, job_url: str):
    result = agent.invoke({...})
    return result
```

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Tutorials](https://langchain-ai.github.io/langgraph/tutorials/)
- [Claude API Documentation](https://docs.anthropic.com/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## ⭐ Show Your Support

If this helped with your interview prep, give it a star! ⭐

---

**Built for the LegalOn Technologies interview** | Demonstrating production-ready LangGraph architecture
