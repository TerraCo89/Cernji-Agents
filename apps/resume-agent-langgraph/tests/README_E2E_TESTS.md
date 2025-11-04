# End-to-End Test for Job Analysis Workflow

## Overview

`test_job_analysis_e2e.py` validates the complete job analysis workflow integration.

## Tests Included

### 1. **Graph Structure Test** (No external dependencies)
- Validates graph has all expected nodes
- Checks node connections are correct
- **Status**: ✅ Passing

### 2. **Initial State Structure Test** (No external dependencies)
- Validates state schema contains required fields
- Checks initial values are correct
- **Status**: ✅ Passing

### 3. **End-to-End Workflow Test** (Requires API keys + browser)
- Tests complete workflow execution
- Validates state transitions
- Checks job_analysis is populated
- **Status**: ⚠️ Requires configuration

## Running Tests

### Quick Structure Validation (No API keys needed)

```bash
cd apps/resume-agent-langgraph
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'src'))
from tests.test_job_analysis_e2e import test_graph_structure, test_initial_state_structure
test_graph_structure()
test_initial_state_structure()
print('All structure tests passed!')
"
```

### Full E2E Test (Requires API keys)

**Prerequisites:**
1. Create `.env` file with API key:
   ```bash
   # Choose one:
   ANTHROPIC_API_KEY=sk-ant-...
   # OR
   OPENAI_API_KEY=sk-...
   ```

2. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

3. Run the test:
   ```bash
   python tests/test_job_analysis_e2e.py
   ```

   The script will:
   - Run structure tests
   - Ask for confirmation before E2E test
   - Execute the full workflow
   - Display detailed results

### Using Pytest

```bash
# Run all tests
pytest tests/test_job_analysis_e2e.py -v -s

# Run only structure tests (no API keys)
pytest tests/test_job_analysis_e2e.py::test_graph_structure -v
pytest tests/test_job_analysis_e2e.py::test_initial_state_structure -v

# Run E2E test (requires API keys)
pytest tests/test_job_analysis_e2e.py::test_job_analysis_workflow_e2e -v -s
```

## Expected Output (Structure Tests)

```
================================================================================
GRAPH STRUCTURE TEST
================================================================================

Graph nodes:
  1. __start__
  2. chatbot
  3. check_cache
  4. fetch_job
  5. analyze_job
  6. tools
  7. process_tool_results

Expected nodes: 7
Actual nodes: 7

[OK] All expected nodes present
[OK] Graph structure test passed

================================================================================
INITIAL STATE STRUCTURE TEST
================================================================================

Checking required fields:
  [OK] messages: list
  [OK] job_url: NoneType
  [OK] job_content: NoneType
  [OK] job_analysis: NoneType
  ...

[OK] Initial state structure test passed
```

## Expected Output (E2E Test)

```
[1/5] Creating initial state...
    [OK] Initial state created

[2/5] Adding user message...
    [OK] User message: 'Please analyze this job posting: https://...'

[3/5] Invoking graph workflow...
    This may take 30-60 seconds for browser automation...
    Graph execution starting...

[4/5] Workflow completed!
    [OK] Total messages in state: 5

[5/5] Analyzing results...
    [OK] job_url extracted: https://...
    [OK] job_content fetched: Job Posting from https://...
    [OK] job_analysis completed:
       - Company: Example Corp
       - Job Title: Software Engineer
       - Location: Remote
       - Required Qualifications: 5 items
       - Keywords: 12 items
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'resume_agent'"
- Make sure you're running from `apps/resume-agent-langgraph` directory
- Or use: `cd apps/resume-agent-langgraph && python tests/test_job_analysis_e2e.py`

### "Could not resolve authentication method"
- Add API key to `.env` file
- Make sure `.env` is in `apps/resume-agent-langgraph/` directory

### "Browser executable doesn't exist"
- Run: `playwright install chromium`

### "UnicodeEncodeError" on Windows
- This has been fixed - all Unicode symbols replaced with ASCII
- If you still see this, check your terminal encoding

## What the Test Validates

### Workflow Integration ✅
- Job analysis nodes are integrated into graph
- Conditional routing works (cache hit/miss)
- Tool trigger mechanism functions

### State Management ✅
- job_url extracted from tool calls
- job_content fetched via browser automation
- job_analysis populated by LLM
- State persists across nodes

### Error Handling ⏳
- Errors accumulated in state (not raised)
- Partial success supported
- Error messages displayed to user

## Next Steps

After this test passes, you can:

1. **Test with Real Job URLs**
   - Replace the example URL with actual job postings
   - Verify japan-dev.com scraper works
   - Verify recruit.legalontech.jp scraper works

2. **Add More Test Cases**
   - Test cache hit scenario
   - Test error scenarios
   - Test different job posting formats

3. **Performance Testing**
   - Measure workflow duration
   - Verify <15s for new analysis
   - Verify <3s for cached analysis

4. **Integration with Resume Tailoring**
   - Test full application workflow
   - Verify job_analysis -> resume_tailoring flow
