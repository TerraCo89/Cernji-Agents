# Quick Setup Guide

Get your Resume Agent running in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- Anthropic API key (get one at https://console.anthropic.com/)

## Installation

### 1. Navigate to the project directory

```bash
cd /path/to/resume-agent-langgraph
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Quick Test

### Test 1: Run the tools (no API key needed)

```bash
python examples/basic_usage.py
```

This tests the ATS analyzer and keyword matching without making API calls.

### Test 2: Run tests

```bash
pytest tests/
```

Some tests require API keys and are skipped by default.

### Test 3: CLI Help

```bash
python src/cli.py --help
python src/cli.py optimize --help
```

## Usage Examples

### Example 1: Optimize a resume

Create a file `my_resume.txt` with your resume content:

```
John Doe
john.doe@email.com | (555) 123-4567

EXPERIENCE
Software Engineer at TechCorp (2020-2024)
- Developed Python applications
- Led team projects
...
```

Run the optimizer:

```bash
python src/cli.py optimize \
    --resume my_resume.txt \
    --job-url "https://example.com/job-posting" \
    --output optimized_resume.txt \
    --thread-id my-session-1
```

The agent will:
1. ✅ Fetch and analyze the job posting
2. ✅ Analyze your current resume
3. ✅ Optimize for ATS and keywords
4. ⏸️ Pause for your review

### Example 2: Resume from checkpoint

After reviewing the optimized resume:

```bash
python src/cli.py resume \
    --thread-id my-session-1 \
    --output final_resume.txt
```

### Example 3: Visualize the graph

```bash
python src/cli.py visualize
```

## Project Structure Tour

```
resume-agent-langgraph/
├── src/resume_agent/
│   ├── state/           👈 Start here - understand the state schema
│   ├── prompts/         👈 Then check the prompts
│   ├── tools/           👈 Reusable utilities (ATS, scraping)
│   ├── nodes/           👈 Core agent logic
│   └── graphs/          👈 Graph orchestration
```

### Understanding the Flow

1. **State** (`state/schemas.py`): The data structure that flows through the graph
2. **Prompts** (`prompts/templates.py`): What we ask Claude to do
3. **Tools** (`tools/`): Helper functions (web scraping, ATS analysis)
4. **Nodes** (`nodes/`): Functions that transform state
5. **Graph** (`graphs/main.py`): Connects everything together

## Common Issues

### Issue: "ANTHROPIC_API_KEY not found"

**Solution**: Make sure you created `.env` and added your API key:
```bash
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...
```

### Issue: "Failed to fetch job posting"

**Solution**: 
- Make sure the URL is accessible
- Check your internet connection
- Some job boards block scrapers—try a different URL

### Issue: Import errors

**Solution**: Make sure you're in the virtual environment:
```bash
# You should see (venv) in your terminal prompt
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

## Next Steps

### 1. Read the Documentation
- `README.md` - Overview and features
- `ARCHITECTURE.md` - Deep dive into design patterns
- `examples/basic_usage.py` - Code examples

### 2. Explore the Code
- Start with `graphs/main.py` to see the workflow
- Look at `nodes/optimizer.py` to understand node structure
- Check `tools/ats_analyzer.py` for utility functions

### 3. Customize for Your Needs
- Modify prompts in `prompts/templates.py`
- Add new nodes in `nodes/`
- Adjust settings in `.env`

### 4. Run with Real Data
```bash
python src/cli.py optimize \
    --resume your_actual_resume.txt \
    --job-url "https://actual-job-url.com" \
    --output improved_resume.txt
```

## Interview Prep

To showcase this project in your interview:

1. **Open the graph visualization**
   ```bash
   python src/cli.py visualize
   ```

2. **Walk through the architecture**
   - Open `ARCHITECTURE.md`
   - Highlight: state management, node design, tools architecture

3. **Show the code organization**
   - Emphasize separation of concerns
   - Point out type safety with TypedDict
   - Highlight testability

4. **Demonstrate a key feature**
   - Show human-in-the-loop checkpointing
   - Explain conditional routing (ReAct pattern)
   - Compare to your game dev state machines

5. **Discuss scaling**
   - Subgraphs for manager-worker pattern
   - Parallel execution with Send()
   - Stateless tools for microservices

## Getting Help

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Claude API Docs**: https://docs.anthropic.com/
- **Project Issues**: Check ARCHITECTURE.md for design decisions

## Ready for the Interview!

You now have a production-ready LangGraph project that demonstrates:
- ✅ Professional code organization
- ✅ Scalable architecture patterns
- ✅ Type-safe state management
- ✅ Human-in-the-loop workflows
- ✅ Comprehensive testing
- ✅ Production readiness

Good luck at LegalOn! 🚀
