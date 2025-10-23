# Testing Notes: Job Analyzer Skill MVP

**Date**: 2025-10-23
**Feature**: Job Analyzer Skill
**Testing Type**: Manual validation in Claude Code

---

## Testing Checklist

### Prerequisites
- [ ] Claude Code 0.4.0+ installed
- [ ] Working directory: `D:\source\Cernji-Agents`
- [ ] Internet connection active
- [ ] `.claude/skills/job-analyzer/SKILL.md` exists

### Test Case 1: Supported Job Board (japan-dev.com)

**Objective**: Verify skill autodiscovery and successful job analysis

**Steps**:
1. Open Claude Code in `D:\source\Cernji-Agents` directory
2. Start new conversation
3. Enter: "Analyze this job posting: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
4. Observe skill invocation

**Expected Results**:
- [ ] T018: Skill automatically discovered (Claude mentions "job-analyzer" or invokes it)
- [ ] T019: Analysis completes within 5 seconds
- [ ] T020: JSON output includes all required fields:
  - company
  - job_title
  - location
  - required_qualifications (at least 1 item)
  - responsibilities (at least 1 item)
  - keywords (10-15 items)
  - candidate_profile
- [ ] T021: File created at `job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json`
- [ ] T022: JSON is well-formed (can parse with json.loads())
- [ ] T023: Processing time <5 seconds

**Actual Results**:
- Skill invocation: [PENDING USER TEST]
- Processing time: [PENDING USER TEST]
- Output quality: [PENDING USER TEST]
- File creation: [PENDING USER TEST]

---

### Test Case 2: Error Handling (Invalid URL)

**Objective**: Verify graceful error handling

**Steps**:
1. In Claude Code, enter: "Analyze this job posting: https://invalid-site-12345.com/job"
2. Observe error handling

**Expected Results**:
- [ ] T024: No skill crash or uncaught exceptions
- [ ] Error message is clear and actionable
- [ ] Error message suggests recovery steps (e.g., "verify URL", "check connectivity")

**Actual Results**:
- Error handling: [PENDING USER TEST]
- Error message quality: [PENDING USER TEST]

---

### Test Case 3: Complex Parsing (Mixed Language)

**Objective**: Verify skill handles Japanese-English content

**Steps**:
1. Find job posting from recruit.legalontech.jp or japan-dev.com
2. Analyze posting with mixed JP/EN content
3. Verify keyword extraction

**Expected Results**:
- [ ] T025: Skill successfully parses mixed-language posting
- [ ] Company name extracted correctly (Japanese or English)
- [ ] Keywords in English (for ATS compatibility)
- [ ] No encoding errors in JSON output

**Actual Results**:
- Parsing success: [PENDING USER TEST]
- Keyword quality: [PENDING USER TEST]
- Encoding: [PENDING USER TEST]

---

## Validation Summary

### Success Criteria

**MUST PASS** (MVP blocker):
- [x] Skill file structure created correctly
- [x] SKILL.md <500 lines (267 lines ✓)
- [x] YAML frontmatter valid (name ≤64 chars, description ≤1024 chars)
- [x] File references use forward slashes
- [ ] **Test Case 1 passes** (USER VALIDATION REQUIRED)
- [ ] **File saved to correct location** (USER VALIDATION REQUIRED)
- [ ] **JSON output is valid** (USER VALIDATION REQUIRED)

**SHOULD PASS** (quality, but not MVP blocker):
- [ ] Test Case 2 (error handling)
- [ ] Test Case 3 (mixed language)
- [ ] Processing time <5s

### Issues Found

**None yet** - Awaiting user testing

---

## Next Steps

1. **User Action Required**: Perform manual tests in Claude Code
2. Document any issues found in this file
3. If critical issues found: Fix before proceeding to Phase 5
4. If minor issues found: Document and defer to future iterations
5. If all tests pass: Proceed to Phase 5 (Documentation)

---

## Testing Guide for User

### How to Test the Skill

**Step 1: Verify Skill Discovery**
```
1. Open Claude Code in D:\source\Cernji-Agents
2. Start new conversation
3. Type: "What career skills are available?"
4. Expected: Claude mentions "job-analyzer" skill
```

**Step 2: Test Job Analysis**
```
1. In Claude Code, paste this exact message:
   "Analyze this job posting: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"

2. Wait for response (should be <5 seconds)

3. Check if Claude:
   - Automatically invoked the job-analyzer skill
   - Returned structured JSON output
   - Saved file to job-applications directory
```

**Step 3: Verify File Creation**
```
1. Open file explorer
2. Navigate to: D:\source\Cernji-Agents\job-applications\
3. Check if directory exists: Cookpad_Senior_Backend_Engineer/
4. Check if file exists: job-analysis.json
5. Open job-analysis.json in text editor
6. Verify it's valid JSON with all required fields
```

**Step 4: Test Error Handling**
```
1. In Claude Code, paste:
   "Analyze this job posting: https://invalid-site-xyz.com/job"

2. Check if error message is clear and helpful
3. Verify no crash or uncaught exception
```

---

## Troubleshooting

### Issue: Skill Not Discovered

**Symptoms**: Claude doesn't mention or use the job-analyzer skill

**Solutions**:
1. Verify you're in `D:\source\Cernji-Agents` directory
2. Check `.claude/skills/job-analyzer/SKILL.md` exists
3. Restart Claude Code session
4. Try explicit invocation: "Use the job-analyzer skill to analyze [URL]"

### Issue: File Not Created

**Symptoms**: Analysis succeeds but no file saved

**Solutions**:
1. Check write permissions on `job-applications/` directory
2. Manually create `job-applications/` directory if missing
3. Verify disk space available
4. Check Claude Code logs for errors

### Issue: Invalid JSON Output

**Symptoms**: JSON parse error or missing fields

**Solutions**:
1. Copy the JSON output
2. Paste into online JSON validator
3. Identify syntax errors
4. Report issue for skill refinement

---

## Post-Testing Actions

**If all tests pass:**
- Mark tasks T018-T025 as [X] in tasks.md
- Update this file with test results
- Proceed to Phase 5: Documentation

**If critical issues found:**
- Document issues in "Issues Found" section above
- Fix skill implementation (SKILL.md)
- Re-test before proceeding

**If minor issues found:**
- Document in "Issues Found" section
- Create future improvement tasks
- Proceed to Phase 5 if core functionality works

---

**Testing Status**: ⏳ Awaiting user validation

**Next Update**: After manual testing complete
