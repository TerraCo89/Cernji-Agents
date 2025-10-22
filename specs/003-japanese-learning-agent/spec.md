# Feature Specification: Japanese Learning Agent

**Feature Branch**: `003-japanese-learning-agent`
**Created**: 2025-10-21
**Status**: Draft
**Input**: User description: "An agent that helps me learn Japanese by reviewing screenshots from games, tracking the words I know, creating flashcards."

## Clarifications

### Session 2025-10-21

- Q: Agent Architecture Pattern - How should Claude Code 2.0 agents integrate with the screenshot workflow? → A: Claude Code agents orchestrate workflow - File watcher detects screenshots and invokes custom Claude Code agents (e.g., `/japanese:analyze`, `/japanese:review`). Agents handle OCR, vocabulary, flashcards.
- Q: Slash Command Organization - How should slash commands be structured? → A: Namespaced commands under `/japanese:` prefix - Separate slash commands under `/japanese:` namespace (e.g., `/japanese:analyze`, `/japanese:review`, `/japanese:vocab-list`, `/japanese:flashcards`)
- Q: Agent Specialization Strategy - How should agents be organized? → A: Specialized agents for major workflows - 3-4 focused agents: analyze-agent (OCR + vocab extraction), review-agent (flashcard review), vocab-agent (vocabulary management), stats-agent (analytics)
- Q: Data Access Pattern for Agents - How should agents interact with database and services? → A: MCP tools for data operations - Define MCP tools (e.g., `analyze_screenshot`, `get_vocabulary`, `create_flashcard`) that agents invoke. Similar to resume-agent's `data_read_master_resume` pattern.
- Q: Flashcard Review Interface - How should flashcard review sessions be presented? → A: Agent-guided conversational review in Claude Code terminal - review-agent presents cards conversationally, can explain mistakes, adapt difficulty, provide encouragement. Rich interaction within Claude Code environment.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Screenshot Text Analysis (Priority: P1)

As a Japanese language learner, I want to capture screenshots from games and have the agent extract and explain Japanese text, so I can understand what I'm reading in real-time without breaking my gaming flow.

**Why this priority**: This is the core value proposition - immediate assistance with understanding Japanese text in context. Without this, the feature provides no immediate value to learners.

**Independent Test**: Can be fully tested by submitting a screenshot with Japanese text and receiving extracted text with translations/explanations. Delivers immediate value even without vocabulary tracking or flashcards.

**Acceptance Scenarios**:

1. **Given** a screenshot containing Japanese text, **When** I submit it to the agent, **Then** the agent extracts all visible Japanese text and provides character-by-character or word-by-word breakdown
2. **Given** extracted Japanese text, **When** I view the analysis, **Then** I see readings (hiragana/romaji), meanings, and grammar notes for each word
3. **Given** a screenshot with mixed kanji, hiragana, and katakana, **When** the agent processes it, **Then** all character types are correctly identified and explained
4. **Given** a screenshot with no Japanese text, **When** I submit it, **Then** the agent informs me that no Japanese text was detected

**Performance Requirements** (see Constitution VI):
- [ ] Response time: <5s for screenshot analysis and text extraction
- [ ] Error handling: Clear feedback when OCR fails or image is unreadable
- [ ] Observability: Track screenshot submissions, OCR success rate, text extraction accuracy

---

### User Story 2 - Vocabulary Tracking (Priority: P2)

As a Japanese language learner, I want the agent to remember which words I've encountered and studied, so I can track my learning progress and avoid re-learning words I already know.

**Why this priority**: Provides cumulative value over time and enables personalized learning, but the agent is still useful without it (P1 works standalone).

**Independent Test**: Can be tested by analyzing multiple screenshots over time and verifying that the agent correctly identifies known vs. new vocabulary. Delivers value by reducing cognitive load during study sessions.

**Acceptance Scenarios**:

1. **Given** I've analyzed 10 screenshots, **When** I view my vocabulary status, **Then** I see a list of all unique words encountered with their study status (new, learning, known)
2. **Given** a word I've marked as "known", **When** it appears in a new screenshot, **Then** the agent indicates I already know this word
3. **Given** a new word I haven't seen before, **When** it appears in a screenshot, **Then** the agent highlights it as new vocabulary
4. **Given** my vocabulary database, **When** I request statistics, **Then** I see total words learned, words encountered this week, and learning streak

**Performance Requirements** (see Constitution VI):
- [ ] Response time: <2s for vocabulary lookup and status check
- [ ] Error handling: Graceful handling of vocabulary database corruption
- [ ] Observability: Track vocabulary growth rate, review frequency, retention metrics

---

### User Story 3 - Flashcard Generation (Priority: P3)

As a Japanese language learner, I want the agent to automatically create flashcards from new words I encounter, so I can systematically review and memorize vocabulary through spaced repetition.

**Why this priority**: Enhances long-term retention but requires both P1 (text extraction) and P2 (vocabulary tracking) to be valuable. It's an optimization layer on top of core functionality.

**Independent Test**: Can be tested by encountering new words, generating flashcards, and reviewing them. Delivers value by automating the flashcard creation process that would otherwise be manual.

**Acceptance Scenarios**:

1. **Given** a new word encountered in a screenshot, **When** I mark it for study, **Then** a flashcard is automatically created with front (Japanese word) and back (reading + meaning)
2. **Given** flashcards are due for review, **When** I run `/japanese:review`, **Then** the review-agent presents cards conversationally in Claude Code terminal
3. **Given** the review-agent shows me a flashcard, **When** I respond with my answer or indicate difficulty, **Then** the agent provides feedback, explanations, and encouragement
4. **Given** I've reviewed a flashcard, **When** I rate my recall (easy/medium/hard), **Then** the next review interval is adjusted accordingly and the agent adapts future explanations
5. **Given** flashcards with example sentences, **When** I review them, **Then** I see the word in context from the original game screenshot

**Performance Requirements** (see Constitution VI):
- [ ] Response time: <1s for flashcard creation, <500ms for flashcard display
- [ ] Error handling: Handle missing translations or malformed word data gracefully
- [ ] Observability: Track flashcard creation rate, review completion rate, retention scores

---

### Edge Cases

- What happens when a screenshot contains vertical text (common in Japanese games)?
- How does the system handle text with furigana (small reading guides above kanji)?
- What happens when OCR misreads similar-looking characters (e.g., ソ vs ン)?
- How does the agent handle words with multiple meanings depending on context?
- What happens when a game uses stylized fonts that are difficult to recognize?
- How does the system handle partial screenshots or cropped text?
- What happens when the same word appears in different grammatical forms (e.g., verb conjugations)?
- How does the agent handle proper nouns (character names, place names)?

## Requirements *(mandatory)*

### Functional Requirements

#### Agent Integration & Workflow
- **FR-001**: System MUST provide namespaced slash commands under `/japanese:` prefix for all major operations
  - `/japanese:analyze` - Analyze a screenshot (automatic via watcher or manual invocation)
  - `/japanese:review` - Start flashcard review session
  - `/japanese:vocab-list` - List vocabulary with filtering options
  - `/japanese:vocab-stats` - Display vocabulary statistics
  - `/japanese:flashcards` - Manage flashcards (list due cards, view progress)
- **FR-002**: File watcher MUST detect new screenshots and automatically invoke Claude Code agent analysis
- **FR-003**: System MUST implement specialized agents for major workflows:
  - **analyze-agent**: Orchestrates OCR processing, text extraction, vocabulary identification, and learning explanations
  - **review-agent**: Manages flashcard review sessions with spaced repetition logic
  - **vocab-agent**: Handles vocabulary listing, searching, status updates, and corrections
  - **stats-agent**: Generates learning analytics and progress reports
- **FR-004**: System MUST provide MCP tools for all data operations (following resume-agent pattern):
  - Screenshot operations: `analyze_screenshot`, `get_screenshot`, `list_screenshots`
  - Vocabulary operations: `get_vocabulary`, `list_vocabulary`, `update_vocab_status`, `search_vocabulary`
  - Flashcard operations: `create_flashcard`, `get_due_flashcards`, `update_flashcard_review`
  - Statistics operations: `get_vocab_stats`, `get_review_stats`
- **FR-005**: Agents MUST be data-agnostic and interact only through MCP tools (no direct database/library access)
- **FR-006**: System MUST support both automatic (file watcher) and manual (slash command) screenshot analysis

#### Screenshot & Text Processing
- **FR-007**: System MUST accept image files (PNG, JPG, JPEG) as input for screenshot analysis
- **FR-008**: System MUST extract Japanese text from screenshots using optical character recognition
- **FR-009**: System MUST identify and separate kanji, hiragana, katakana, and romaji characters
- **FR-010**: System MUST provide readings (hiragana or romaji) for all kanji characters
- **FR-011**: System MUST provide English translations or explanations for extracted Japanese text
- **FR-012**: System MUST preserve the original screenshot alongside extracted text for context

#### Vocabulary Management
- **FR-013**: System MUST maintain a persistent vocabulary database tracking all encountered words
- **FR-014**: System MUST allow users to mark words with status indicators (new, learning, known)
- **FR-015**: System MUST prevent duplicate entries when the same word is encountered multiple times
- **FR-016**: System MUST provide vocabulary statistics (total words, new words, review due)
- **FR-017**: System MUST allow users to manually correct OCR errors

#### Flashcard System
- **FR-018**: System MUST generate flashcards automatically from new vocabulary
- **FR-019**: System MUST include both the Japanese word and its reading on flashcard fronts
- **FR-020**: System MUST include English meaning and example usage on flashcard backs
- **FR-021**: review-agent MUST present flashcards conversationally in Claude Code terminal (not bare CLI)
- **FR-022**: review-agent MUST provide contextual feedback, explanations, and encouragement during review
- **FR-023**: review-agent MUST adapt explanations based on user performance and difficulty ratings
- **FR-024**: System MUST track user performance on flashcard reviews (correct/incorrect responses)
- **FR-025**: System MUST adjust flashcard review intervals based on user performance

#### Error Handling & Quality
- **FR-026**: System MUST handle errors gracefully with informative user feedback
- **FR-027**: Agents MUST provide contextual explanations suitable for language learners

### Key Entities *(include if feature involves data)*

- **Screenshot**: An image file submitted by the user containing Japanese text. Attributes include submission timestamp, original image data, extraction status, and associated extracted text.

- **ExtractedText**: Japanese text extracted from a screenshot. Attributes include original text, character type breakdown, position in image, and confidence score from OCR.

- **Vocabulary**: A unique Japanese word or phrase encountered during learning. Attributes include kanji form, hiragana reading, romaji reading, English meaning, part of speech, first encountered date, study status, and encounter count.

- **Flashcard**: A study card for vocabulary review. Attributes include associated vocabulary, creation date, last review date, next review date, ease factor (for spaced repetition), and review history.

- **ReviewSession**: A single flashcard review instance. Attributes include flashcard reference, review timestamp, user response (easy/medium/hard), response time, and whether the answer was correct.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can submit a screenshot and receive text analysis results in under 5 seconds
- **SC-002**: OCR accuracy rate exceeds 90% for clear, standard Japanese text
- **SC-003**: Users can track at least 500 unique vocabulary words without performance degradation
- **SC-004**: Users successfully create and review flashcards within 30 seconds of encountering a new word
- **SC-005**: Users can complete a review session of 20 flashcards in under 3 minutes
- **SC-006**: Vocabulary retention rate (as measured by flashcard review performance) improves by 30% compared to manual study methods
- **SC-007**: 80% of users successfully analyze their first screenshot without requiring help documentation
- **SC-008**: Users reduce the time spent looking up unknown words by 70% compared to manual dictionary lookup

## Assumptions

- Users have access to a device capable of capturing screenshots from games
- Users are learning Japanese and have at least basic familiarity with hiragana and katakana
- Screenshots will primarily contain printed digital text (not handwritten Japanese)
- Users understand basic flashcard/spaced repetition learning methodology
- **Hybrid OCR approach**: Claude Vision API for immediate translation + manga-ocr for structured vocabulary extraction
- Vocabulary tracking will use a local database (not cloud-based initially)
- **Architecture follows resume-agent pattern**: MCP server provides tools, agents are data-agnostic
- **File watcher triggers agent invocation**: Automatic screenshot detection invokes `/japanese:analyze` slash command
- **All data operations through MCP tools**: Agents never directly access database, OCR libraries, or dictionary APIs
- **Conversational review interface**: Flashcard review happens in Claude Code terminal via review-agent (not bare CLI or web UI)
- **Adaptive learning assistance**: Agents provide contextual explanations, adapt to user performance, and offer encouragement
- Custom Claude Code agents orchestrate all intelligent processing (OCR analysis, vocabulary extraction, learning recommendations)
- **Reuses existing codebase patterns**: Builds upon proven `apps/japanese-tutor/screenshot_watcher.py` implementation
- **File watcher library**: Uses `watchdog` (already in project, Windows-tested) instead of introducing new dependencies
- The agent will provide general-purpose translations (not game-specific context)

## Dependencies

- **MCP Server** (similar to resume-agent architecture):
  - MCP tools for screenshot operations (`analyze_screenshot`, `get_screenshot`, `list_screenshots`)
  - MCP tools for vocabulary operations (`get_vocabulary`, `list_vocabulary`, `update_vocab_status`, `search_vocabulary`)
  - MCP tools for flashcard operations (`create_flashcard`, `get_due_flashcards`, `update_flashcard_review`)
  - MCP tools for statistics operations (`get_vocab_stats`, `get_review_stats`)
  - Backend services:
    - **OCR**: Hybrid approach using both Claude Vision API (real-time translation) and manga-ocr (structured vocabulary extraction)
    - **Dictionary**: jamdict (offline Japanese dictionary)
    - **Database**: SQLite (vocabulary and flashcard storage)
    - **Spaced Repetition**: SM-2 algorithm
- **Claude Code 2.0 agent framework** with specialized agents:
  - `.claude/agents/analyze-agent.md` - Screenshot analysis and OCR orchestration
  - `.claude/agents/review-agent.md` - Flashcard review workflow
  - `.claude/agents/vocab-agent.md` - Vocabulary management
  - `.claude/agents/stats-agent.md` - Learning analytics
- **Slash command infrastructure** (`.claude/commands/` directory):
  - `/japanese:analyze`, `/japanese:review`, `/japanese:vocab-list`, `/japanese:vocab-stats`, `/japanese:flashcards`
- **File system watcher** for automatic screenshot detection (reuses existing `watchdog` library from japanese-tutor)
- **Existing Codebase Integration**:
  - Leverages proven patterns from `apps/japanese-tutor/screenshot_watcher.py`
  - Reuses `watchdog` Observer pattern for file monitoring (already Windows-tested)
  - Maintains existing Claude Vision API integration for real-time translation workflow
  - Extends with new vocabulary tracking and flashcard generation capabilities

## Scope

### In Scope
- Screenshot analysis with OCR for Japanese text extraction
- Vocabulary tracking and status management (new/learning/known)
- Automatic flashcard generation from encountered vocabulary
- Spaced repetition review system
- Vocabulary statistics and progress tracking
- Manual OCR correction capabilities

### Out of Scope
- Real-time text overlay on running games
- Audio pronunciation or text-to-speech
- Grammar lessons or structured curriculum
- Multiplayer or social learning features
- Mobile app version (initial release is desktop-focused)
- Cloud synchronization across devices
- Advanced linguistic analysis (sentence parsing, grammar breakdown)
- Automated game-specific context detection
- Handwriting recognition for handwritten Japanese
- Video analysis or animated text detection
