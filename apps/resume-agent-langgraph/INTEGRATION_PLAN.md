# Resume Agent LangGraph Integration Plan

## Overview
This document outlines the components from `src/resume_agent/` that should be integrated into `src/resume_agent/graph.py` to transform it from a basic chatbot into a full-featured resume assistance agent.

**Current State:** Basic chatbot with simple state (messages only) and no tools
**Target State:** Full resume agent with job analysis, resume tailoring, cover letter generation, and portfolio search capabilities

---

## 1. State Schema Enhancement ✅ COMPLETE

### Current Implementation
```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
```

### Components Added
**Source:** `src/resume_agent/state/schemas.py`

#### Main State Schema
Replaced `State` with `ResumeAgentState` which includes:

**Required Fields:**
- ✅ `messages: Annotated[List[BaseMessage], add_messages]` - Already present

**Job Application Data:**
- ✅ `job_analysis: Annotated[Optional[JobAnalysisDict], replace_with_latest]`
- ✅ `master_resume: Annotated[Optional[MasterResumeDict], replace_with_latest]`
- ✅ `tailored_resume: Annotated[Optional[TailoredResumeDict], replace_with_latest]`
- ✅ `cover_letter: Annotated[Optional[CoverLetterDict], replace_with_latest]`
- ✅ `portfolio_examples: Annotated[List[PortfolioExampleDict], append_unique_examples]`

**Workflow Control:**
- ✅ `current_intent: Annotated[Optional[WorkflowIntent], replace_with_latest]`
- ✅ `workflow_progress: Annotated[Optional[WorkflowProgress], replace_with_latest]`
- ✅ `requires_user_input: Annotated[bool, replace_with_latest]`
- ✅ `error_message: Annotated[Optional[str], replace_with_latest]`

**RAG Pipeline:**
- ✅ `rag_query_results: Annotated[Optional[List[Dict[str, Any]]], replace_with_latest]`
- ✅ `processed_websites: Annotated[Optional[List[Dict[str, Any]]], replace_with_latest]`

**Metadata:**
- ✅ `user_id: Annotated[str, replace_with_latest]`

#### Supporting TypedDicts Imported ✅
- ✅ `PersonalInfoDict` - Contact information
- ✅ `AchievementDict` - Achievement with metrics
- ✅ `EmploymentDict` - Employment history entry
- ✅ `MasterResumeDict` - Complete resume structure
- ✅ `JobAnalysisDict` - Job posting analysis
- ✅ `TailoredResumeDict` - Job-specific resume
- ✅ `CoverLetterDict` - Cover letter content
- ✅ `PortfolioExampleDict` - Code example metadata
- ✅ `WorkflowIntent` - User intent classification
- ✅ `WorkflowProgress` - Multi-step workflow tracking

#### Custom Reducers Imported ✅
```python
from .state.schemas import append_unique_examples, replace_with_latest
```

- ✅ `append_unique_examples()` - Deduplicates portfolio examples by ID/title
- ✅ `replace_with_latest()` - Always uses newest value (for single-value fields)

#### Helper Functions Imported ✅
```python
from .state.schemas import (
    create_initial_state,
    update_state,
    validate_job_analysis_exists,
    validate_master_resume_exists,
    validate_can_tailor_resume,
    validate_can_write_cover_letter,
)
```

**Status:** ✅ **COMPLETE** - See `STATE_INTEGRATION_COMPLETE.md` for details

---

## 2. Tools Integration ✅ COMPLETE

### Current Implementation
```python
tools = []
```

### Components Added
**Source:** `src/resume_agent/tools/__init__.py`

Added 6 LangChain tools (decorated with `@tool`):

#### Job Analysis Tools ✅
- ✅ `analyze_job_posting(url: str) -> Dict`
  - Fetches and analyzes job posting
  - Extracts requirements, responsibilities, keywords
  - Returns structured analysis with company, title, skills, etc.

#### ATS (Applicant Tracking System) Tools ✅
- ✅ `calculate_keyword_match(resume_text: str, job_keywords: List[str]) -> Dict`
  - Compares resume keywords against job requirements
  - Returns match percentage, matched/missing keywords

- ✅ `calculate_ats_score(resume_data: Dict, job_analysis: Dict) -> Dict`
  - Calculates overall ATS compatibility score (0-100)
  - Weighted scoring: keywords (40%), skills (30%), experience (30%)
  - Includes recommendations for improvement

#### Resume Parsing Tools ✅
- ✅ `load_master_resume(file_path: str) -> Dict`
  - Loads user's master resume from YAML
  - Validates structure, returns status/data or error

- ✅ `extract_skills_from_resume(resume_data: Dict) -> List[str]`
  - Extracts all technical skills from resume and employment history
  - Deduplicates and sorts

- ✅ `extract_achievements_from_resume(resume_data: Dict) -> List[Dict]`
  - Extracts quantifiable achievements with context
  - Includes company, role, period, metric

**Import Statement Added:**
```python
from .tools import (
    analyze_job_posting,
    calculate_keyword_match,
    calculate_ats_score,
    load_master_resume,
    extract_skills_from_resume,
    extract_achievements_from_resume,
)

tools = [
    analyze_job_posting,
    calculate_keyword_match,
    calculate_ats_score,
    load_master_resume,
    extract_skills_from_resume,
    extract_achievements_from_resume,
]
```

**Note:** `parse_resume_yaml` and `suggest_improvements` are helper functions used internally by the tools, not exposed as standalone tools.

**Status:** ✅ **COMPLETE** - 6 tools integrated and tested

---

## 3. Node Functions

### Current Implementation
```python
def chatbot(state: State):
    if tools:
        llm_with_tools = llm.bind_tools(tools)
        message = llm_with_tools.invoke(state["messages"])
        assert len(message.tool_calls) <= 1
    else:
        message = llm.invoke(state["messages"])
    return {"messages": [message]}
```

### Components to Add
**Source:** `src/resume_agent/nodes/__init__.py`

#### Conversation Nodes
- ⬜ `chat_node(state: ResumeAgentState) -> Dict`
  - Enhanced chat handling with context awareness
  - Integrates with workflow state

- ⬜ `get_user_input_node(state: ResumeAgentState) -> Dict`
  - Handles user input collection
  - Sets `requires_user_input` flag

#### Job Analysis Workflow Nodes
- ⬜ `check_cache_node(state: ResumeAgentState) -> Dict`
  - Checks if job analysis exists in state
  - Avoids redundant API calls

- ⬜ `fetch_job_node(state: ResumeAgentState) -> Dict`
  - Fetches job posting from URL
  - Handles various job board formats

- ⬜ `analyze_job_node(state: ResumeAgentState) -> Dict`
  - Analyzes job requirements
  - Extracts structured data
  - Updates `job_analysis` in state

#### Resume Tailoring Workflow Nodes
- ⬜ `load_resume_node(state: ResumeAgentState) -> Dict`
  - Loads master resume
  - Updates `master_resume` in state

- ⬜ `analyze_requirements_node(state: ResumeAgentState) -> Dict`
  - Compares resume against job requirements
  - Identifies gaps and strengths

- ⬜ `tailor_resume_node(state: ResumeAgentState) -> Dict`
  - Generates job-specific resume
  - Optimizes keyword placement
  - Updates `tailored_resume` in state

- ⬜ `validate_tailoring_node(state: ResumeAgentState) -> Dict`
  - Validates tailored content
  - Checks ATS score
  - Suggests refinements

#### Cover Letter Workflow Nodes
- ⬜ `prepare_cover_letter_context_node(state: ResumeAgentState) -> Dict`
  - Gathers context from job analysis and resume
  - Identifies talking points

- ⬜ `generate_cover_letter_node(state: ResumeAgentState) -> Dict`
  - Generates personalized cover letter
  - Matches tone to company culture
  - Updates `cover_letter` in state

- ⬜ `review_cover_letter_node(state: ResumeAgentState) -> Dict`
  - Reviews and refines cover letter
  - Checks for consistency with resume
  - Ensures professional tone

**Import Statement:**
```python
from resume_agent.nodes import (
    # Conversation
    chat_node,
    get_user_input_node,
    # Job Analysis
    check_cache_node,
    fetch_job_node,
    analyze_job_node,
    # Resume Tailoring
    load_resume_node,
    analyze_requirements_node,
    tailor_resume_node,
    validate_tailoring_node,
    # Cover Letter
    prepare_cover_letter_context_node,
    generate_cover_letter_node,
    review_cover_letter_node,
)
```

**Priority:** 🟡 **MEDIUM** - Required for workflows but can be added incrementally

---

## 4. LLM Configuration

### Current Implementation
```python
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

if LLM_PROVIDER.lower() == "anthropic":
    model_string = f"anthropic:{ANTHROPIC_MODEL}"
else:
    model_string = f"openai:{OPENAI_MODEL}"

llm = init_chat_model(model_string)
```

### Components to Add
**Source:** `src/resume_agent/config.py`

#### Settings Class
Replace manual env var handling with Pydantic settings:

```python
from resume_agent.config import get_settings

settings = get_settings()

# Access configuration
llm_provider = settings.llm_provider  # "claude" or "openai"
model_name = settings.claude_model if settings.llm_provider == "claude" else settings.openai_model
temperature = settings.temperature
max_tokens = settings.max_tokens
```

#### Configuration Fields
- ⬜ `llm_provider: Literal["claude", "openai"]` - Provider selection
- ⬜ `anthropic_api_key: str` - Anthropic API key
- ⬜ `openai_api_key: str` - OpenAI API key
- ⬜ `claude_model: str` - Claude model name (default: "claude-sonnet-4-5")
- ⬜ `openai_model: str` - OpenAI model name (default: "gpt-4o-mini")
- ⬜ `temperature: float` - LLM temperature (default: 0.7)
- ⬜ `max_tokens: int` - Max tokens per response (default: 2048)
- ⬜ `max_iterations: int` - Max optimization iterations (default: 3)
- ⬜ `ats_score_threshold: int` - Target ATS score (default: 80)

**Benefits:**
- Type validation via Pydantic
- Automatic `.env` file loading
- Centralized configuration management
- Easy testing with `reset_settings()`

**Priority:** 🟢 **LOW** - Nice to have but current approach works

---

## 5. System Prompts

### Current Implementation
No system prompts defined - relies on model defaults

### Components to Add
**Source:** `src/resume_agent/prompts/__init__.py`

Import and use specialized system prompts:

```python
from resume_agent.prompts import (
    SYSTEM_RESUME_AGENT,
    SYSTEM_JOB_ANALYZER,
    SYSTEM_RESUME_EXPERT,
    CONVERSATION_SYSTEM,
    JOB_ANALYSIS_PROMPT,
    RESUME_TAILORING_PROMPT,
    COVER_LETTER_PROMPT,
    COVER_LETTER_REVIEW_PROMPT,
)
```

#### System Prompts
- ⬜ `SYSTEM_RESUME_AGENT` - Main agent persona and capabilities
- ⬜ `SYSTEM_JOB_ANALYZER` - Job analysis expert persona
- ⬜ `SYSTEM_RESUME_EXPERT` - Resume optimization expert persona
- ⬜ `CONVERSATION_SYSTEM` - Conversational flow guidance

#### Task Prompts
- ⬜ `JOB_ANALYSIS_PROMPT` - Template for job analysis tasks
- ⬜ `RESUME_TAILORING_PROMPT` - Template for resume tailoring
- ⬜ `COVER_LETTER_PROMPT` - Template for cover letter generation
- ⬜ `COVER_LETTER_REVIEW_PROMPT` - Template for cover letter review

**Usage Example:**
```python
from langchain_core.messages import SystemMessage

def analyze_job_node(state: ResumeAgentState) -> Dict:
    messages = [
        SystemMessage(content=SYSTEM_JOB_ANALYZER),
        HumanMessage(content=JOB_ANALYSIS_PROMPT.format(
            job_url=state["job_analysis"]["url"],
            raw_description=state["job_analysis"]["raw_description"]
        ))
    ]
    response = llm.invoke(messages)
    # ... process response
```

**Priority:** 🟡 **MEDIUM** - Improves output quality significantly

---

## 6. LLM Provider Abstraction

### Current Implementation
Direct use of `init_chat_model()`:
```python
llm = init_chat_model(model_string)
message = llm.invoke(state["messages"])
```

### Components to Add
**Source:** `src/resume_agent/llm/__init__.py`

Unified LLM calling interface that works with both providers:

```python
from resume_agent.llm import call_llm, get_provider_info, convert_langgraph_messages_to_api_format
```

#### Functions
- ⬜ `call_llm(messages, **kwargs) -> str`
  - Unified interface for both Anthropic and OpenAI
  - Handles message format conversion
  - Manages error handling and retries

- ⬜ `get_provider_info() -> Dict`
  - Returns current provider configuration
  - Includes model name, max tokens, etc.

- ⬜ `convert_langgraph_messages_to_api_format(messages) -> List[Dict]`
  - Converts LangGraph message format to API format
  - Handles special message types

**Benefits:**
- Provider-agnostic code
- Centralized error handling
- Easier testing with mock providers

**Priority:** 🟢 **LOW** - Current approach works, but abstraction is cleaner

---

## 7. Graph Builders

### Current Implementation
Single linear graph:
```python
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
if tools:
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()
```

### Components to Consider
**Source:** `src/resume_agent/graphs/__init__.py`

Specialized graph builders for different workflows:

- ⬜ `build_conversation_graph()` - Conversational flow with intent classification
- ⬜ `build_job_analysis_graph()` - Job analysis workflow (cache → fetch → analyze)
- ⬜ `build_resume_tailoring_graph()` - Resume tailoring workflow (load → analyze → tailor → validate)
- ⬜ `build_cover_letter_graph()` - Cover letter workflow (context → generate → review)

**Decision Point:**
Should we:
1. **Option A:** Import these graphs and use them as subgraphs
2. **Option B:** Merge all nodes into one master graph with conditional routing
3. **Option C:** Keep separate graph builders for different entry points

**Recommendation:** Start with Option B (master graph) for simplicity, refactor to subgraphs later if needed.

**Priority:** 🟢 **LOW** - Can start with simpler approach

---

## 8. Helper Functions

### Components to Add
**Source:** `src/resume_agent/state/schemas.py`

#### State Initialization
```python
from resume_agent.state.schemas import create_initial_state

# Usage
initial_state = create_initial_state(user_id="user_123")
```

#### State Updates
```python
from resume_agent.state.schemas import update_state

def my_node(state: ResumeAgentState) -> Dict:
    # ... do work ...
    return update_state(
        state,
        job_analysis=new_analysis,
        messages=[AIMessage(content="Analysis complete!")]
    )
```

#### State Validation
```python
from resume_agent.state.schemas import (
    validate_job_analysis_exists,
    validate_master_resume_exists,
    validate_can_tailor_resume,
    validate_can_write_cover_letter,
)

def should_tailor_resume(state: ResumeAgentState) -> str:
    """Conditional edge function."""
    if validate_can_tailor_resume(state):
        return "tailor_resume"
    else:
        return "request_missing_data"
```

**Priority:** 🟡 **MEDIUM** - Makes node code cleaner and more maintainable

---

## 9. Web Browser Tool Integration

### Requirement
Add a web browsing tool to enable the agent to fetch and analyze job postings from URLs in real-time.

### Research Tasks
- ⬜ Identify suitable web browser tools for LangChain/LangGraph
  - Options to investigate:
    - Playwright-based tools (langchain-community)
    - Selenium-based tools
    - BeautifulSoup + requests (lightweight)
    - Browserbase/Firecrawl (cloud services)
    - Existing MCP browser tools

### Integration Checklist
- ⬜ Research available web browser tools compatible with LangChain
- ⬜ Evaluate pros/cons (headless vs cloud, cost, reliability)
- ⬜ Choose tool based on: reliability, ease of use, cost
- ⬜ Install required dependencies
- ⬜ Add browser tool to `tools` list in graph.py
- ⬜ Test web scraping with real job posting URLs
- ⬜ Update `analyze_job_posting` to use browser tool instead of httpx
- ⬜ Handle authentication/CAPTCHA if needed
- ⬜ Add error handling for failed page loads

**Priority:** 🟡 **MEDIUM** - Improves job analysis reliability but httpx fallback exists

**Notes:**
- Current `analyze_job_posting` uses `httpx` for fetching
- Many job boards require JavaScript rendering (LinkedIn, Indeed)
- Browser tool would improve data quality and success rate
- Consider cost/performance tradeoff for cloud solutions

---

## Implementation Strategy

### Phase 1: Foundation ✅ COMPLETE
1. ✅ Create this integration plan document
2. ✅ Integrate `ResumeAgentState` and custom reducers
3. ✅ Add helper functions (create_initial_state, update_state, validators)
4. ✅ Update graph to use new state schema
5. ✅ Test basic state persistence

### Phase 2: Core Tools ✅ COMPLETE
1. ✅ Import and integrate job analysis tools
2. ✅ Import and integrate resume parsing tools
3. ✅ Import and integrate ATS scoring tools
4. ✅ Update tools list in graph (6 tools added)
5. ✅ Test tool execution

### Phase 3: Workflows (In Progress)
1. ⬜ Research and add web browser tool
2. ⬜ Import job analysis nodes
3. ⬜ Import resume tailoring nodes
4. ⬜ Import cover letter nodes
5. ⬜ Build graph with conditional routing
6. ⬜ Test end-to-end workflows

### Phase 4: Polish (Not Started)
1. ⬜ Add system prompts
2. ⬜ Integrate configuration management
3. ⬜ Add LLM provider abstraction (optional)
4. ⬜ Add comprehensive error handling
5. ⬜ Write integration tests

---

## Testing Checklist

### Unit Tests
- ⬜ State reducers work correctly (deduplication, replacement)
- ⬜ Validators return correct boolean values
- ⬜ Tools return expected data structures
- ⬜ Nodes update state correctly

### Integration Tests
- ⬜ Job analysis workflow (URL → structured data)
- ⬜ Resume tailoring workflow (master + job → tailored)
- ⬜ Cover letter workflow (resume + job → cover letter)
- ⬜ Full application workflow (all steps in sequence)

### Edge Cases
- ⬜ Invalid job URL handling
- ⬜ Missing master resume handling
- ⬜ Incomplete job analysis handling
- ⬜ State persistence across sessions
- ⬜ Concurrent workflow handling

---

## Dependencies to Verify

Ensure these are in `pyproject.toml`:

```toml
[project]
dependencies = [
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
    "langchain-openai",
    "langchain-anthropic",
    "langchain-community",
    "pydantic>=2.0.0",
    "pydantic-settings",
    "python-dotenv",
    "pyyaml",  # For resume parsing
    "requests",  # For job fetching
    "beautifulsoup4",  # For job scraping
    "tiktoken",  # For token counting
]
```

---

## Notes

### Architecture Decisions
1. **Monolithic vs Modular Graph:** Starting with one graph in `graph.py` that imports nodes from `nodes/` package maintains separation of concerns while keeping the entry point simple.

2. **State Management:** Using custom reducers enables sophisticated state updates without complex logic in every node.

3. **Tool vs Node:** Tools are for LLM-callable functions (e.g., analyze_job_posting), while nodes are graph execution units (e.g., analyze_job_node that calls the tool).

### Migration Path
- Current `graph.py` remains functional throughout migration
- Can deploy incrementally (add tools first, then nodes, then workflows)
- Backward compatible - new state fields are all optional

### Performance Considerations
- State size grows with portfolio examples - implement pagination if needed
- Cache job analyses to avoid redundant API calls
- Consider streaming for long-running operations (resume generation)

---

## Related Documentation
- **Main README:** `apps/resume-agent-langgraph/README.md`
- **State Schema:** `apps/resume-agent-langgraph/src/resume_agent/state/schemas.py`
- **Tools Reference:** `apps/resume-agent/MCP_TOOLS_REFERENCE.md`
- **Architecture Docs:** `apps/resume-agent-langgraph/docs/`

---

**Last Updated:** 2025-10-26
**Status:** Phase 2 Complete - Tools Integrated
**Completed:**
- ✅ Phase 1: State Schema Integration
- ✅ Phase 2: Core Tools Integration (6 tools)

**Next Actions:**
1. Research and integrate web browser tool for better job scraping
2. Begin Phase 3: Workflow Nodes Integration
