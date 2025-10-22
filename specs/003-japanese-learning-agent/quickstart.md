# Quick Start Guide: Japanese Learning Agent

**For**: Developers implementing feature 003-japanese-learning-agent
**Last Updated**: 2025-10-21

This guide provides the fastest path from zero to working implementation of the Japanese Learning Agent.

---

## 📋 Prerequisites

- ✅ Python 3.10 or higher
- ✅ UV package manager installed (`pip install uv`)
- ✅ Windows OS (existing watcher runs on Windows)
- ✅ Git repository access

---

## 🚀 5-Minute Setup

### Step 1: Navigate to Project

```bash
cd D:\source\Cernji-Agents\apps\japanese-tutor
```

### Step 2: Install Dependencies

```bash
# UV will auto-create a virtual environment and install dependencies
uv pip install -r requirements.txt

# Additional dependencies for this feature (will be added to requirements.txt)
uv pip install manga-ocr jamdict pillow pydantic pytest
```

### Step 3: Initialize Database

```bash
# Create database with schema
uv run python -c "from src.repositories.base import init_database; init_database()"

# Or run the SQL script directly
sqlite3 ../../data/japanese_learning.db < ../specs/003-japanese-learning-agent/contracts/database_schema.sql
```

### Step 4: Download Dictionary Data

```bash
# jamdict will auto-download JMDict on first use (~100MB)
uv run python -c "import jamdict; jamdict.Jamdict()"
```

### Step 5: Configure Screenshot Directory

Edit `config.yaml`:

```yaml
screenshot_dir: "C:\\Path\\To\\Your\\Screenshots"
database_path: "../../data/japanese_learning.db"
ocr_model: "manga-ocr"
min_confidence: 0.7
auto_flashcard: true
```

### Step 6: Run the Watcher

```bash
uv run watcher.py
```

You should see:
```
🎮 Japanese Learning Agent - Screenshot Watcher
📁 Monitoring: C:\Path\To\Your\Screenshots
💾 Database: ../../data/japanese_learning.db
🤖 OCR Model: manga-ocr
⚙️  Auto-flashcard: enabled

Waiting for new screenshots...
```

---

## 📚 Development Workflow

### Phase 0: Read the Specs

1. **Feature Specification**: `specs/003-japanese-learning-agent/spec.md`
   - User stories and acceptance criteria
   - Success criteria and performance requirements

2. **Implementation Plan**: `specs/003-japanese-learning-agent/plan.md`
   - Technical decisions and architecture
   - Project structure and complexity tracking

3. **Research Document**: `specs/003-japanese-learning-agent/research.md`
   - Library comparisons and technology choices
   - Performance benchmarks and optimization strategies

4. **Data Model**: `specs/003-japanese-learning-agent/data-model.md`
   - Entity definitions and relationships
   - Pydantic models and validation rules
   - Database schema and query patterns

5. **Contracts**: `specs/003-japanese-learning-agent/contracts/`
   - `database_schema.sql` - SQLite schema
   - `pydantic_models.py` - Data models with validation
   - `uv_scripts.md` - CLI interface specifications

### Phase 1: Implement Core Services (P1 - MVP)

**Priority**: Screenshot OCR + Vocabulary Tracking

#### 1.1 Create Pydantic Models

File: `apps/japanese-tutor/src/models/schemas.py`

Copy from: `specs/003-japanese-learning-agent/contracts/pydantic_models.py`

**Test first**:
```bash
uv run pytest tests/contract/test_pydantic_models.py -v
```

#### 1.2 Implement Base Repository

File: `apps/japanese-tutor/src/repositories/base.py`

```python
import sqlite3
from pathlib import Path

class BaseRepository:
    def __init__(self, db_path: str = "../../data/japanese_learning.db"):
        self.db_path = Path(db_path)
        self.conn = self._connect()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
```

**Test first**:
```bash
uv run pytest tests/contract/test_database_schema.py -v
```

#### 1.3 Implement OCR Service

File: `apps/japanese-tutor/src/services/ocr_service.py`

```python
from manga_ocr import MangaOcr
from PIL import Image
from models.schemas import Screenshot, ExtractedTextSegment

class OCRService:
    def __init__(self):
        self.ocr = MangaOcr()

    def process_screenshot(self, file_path: str) -> Screenshot:
        # TODO: Implement OCR logic
        pass
```

**Test first**:
```bash
uv run pytest tests/integration/test_ocr_pipeline.py::test_process_simple_screenshot -v
```

#### 1.4 Implement Dictionary Service

File: `apps/japanese-tutor/src/services/dictionary_service.py`

```python
import jamdict

class DictionaryService:
    def __init__(self):
        self.jmd = jamdict.Jamdict()

    def lookup(self, word: str) -> dict:
        # TODO: Implement dictionary lookup
        pass
```

**Test first**:
```bash
uv run pytest tests/unit/test_dictionary_service.py -v
```

#### 1.5 Refactor Screenshot Watcher

File: `apps/japanese-tutor/src/cli/watcher.py`

1. Copy existing `screenshot_watcher.py` logic
2. Add OCR service integration
3. Add vocabulary repository integration
4. Update legacy `screenshot_watcher.py` to redirect

**Test first**:
```bash
uv run pytest tests/integration/test_watcher_flow.py -v
```

### Phase 2: Implement Vocabulary Management (P2)

**Priority**: vocab-cli.py script

#### 2.1 Implement Vocabulary Repository

File: `apps/japanese-tutor/src/repositories/vocabulary_repo.py`

```python
from repositories.base import BaseRepository
from models.schemas import Vocabulary

class VocabularyRepository(BaseRepository):
    def find_or_create(self, kanji_form, hiragana_reading) -> Vocabulary:
        # TODO: Implement upsert logic
        pass
```

**Test first**:
```bash
uv run pytest tests/unit/test_vocabulary_service.py -v
```

#### 2.2 Implement vocab-cli.py

File: `apps/japanese-tutor/src/cli/vocab_cli.py`

Follow contract: `specs/003-japanese-learning-agent/contracts/uv_scripts.md#2-vocab-clipy`

**Test first**:
```bash
uv run pytest tests/contract/test_cli_interfaces.py::test_vocab_list_command -v
```

### Phase 3: Implement Flashcard System (P3)

**Priority**: Flashcard generation + review

#### 3.1 Implement SM-2 Algorithm

File: `apps/japanese-tutor/src/models/spaced_repetition.py`

```python
from datetime import datetime, timedelta
from models.schemas import Flashcard

def update_flashcard_sm2(
    flashcard: Flashcard,
    user_response: str
) -> Flashcard:
    # TODO: Implement SM-2 algorithm
    # See: specs/003-japanese-learning-agent/contracts/pydantic_models.py
    pass
```

**Test first**:
```bash
uv run pytest tests/unit/test_spaced_repetition.py -v
```

#### 3.2 Implement Flashcard Service

File: `apps/japanese-tutor/src/services/flashcard_service.py`

```python
from repositories.flashcard_repo import FlashcardRepository
from models.schemas import Flashcard, Vocabulary

class FlashcardService:
    def create_flashcard(
        self,
        vocabulary: Vocabulary,
        screenshot_id: int = None
    ) -> Flashcard:
        # TODO: Implement flashcard creation
        pass
```

**Test first**:
```bash
uv run pytest tests/unit/test_flashcard_service.py -v
```

#### 3.3 Implement flashcard-cli.py

File: `apps/japanese-tutor/src/cli/flashcard_cli.py`

Follow contract: `specs/003-japanese-learning-agent/contracts/uv_scripts.md#3-flashcard-clipy`

**Test first**:
```bash
uv run pytest tests/contract/test_cli_interfaces.py::test_flashcard_review_command -v
```

---

## 🧪 Testing Strategy

### Test Execution Order

```bash
# 1. Contract tests (verify interfaces match contracts)
uv run pytest tests/contract/ -v

# 2. Unit tests (verify business logic)
uv run pytest tests/unit/ -v

# 3. Integration tests (verify end-to-end flows)
uv run pytest tests/integration/ -v

# 4. All tests with coverage
uv run pytest --cov=src --cov-report=html
```

### Key Test Files

| Test File | Purpose | Priority |
|-----------|---------|----------|
| `tests/contract/test_database_schema.py` | Verify SQLite schema | P1 |
| `tests/contract/test_pydantic_models.py` | Verify data models | P1 |
| `tests/contract/test_cli_interfaces.py` | Verify CLI contracts | P2 |
| `tests/unit/test_spaced_repetition.py` | Verify SM-2 algorithm | P3 |
| `tests/integration/test_ocr_pipeline.py` | Verify OCR + vocab flow | P1 |
| `tests/integration/test_watcher_flow.py` | Verify file watcher | P1 |

---

## 🎯 Acceptance Criteria Checklist

Use this checklist to verify implementation against spec requirements:

### P1: Screenshot Text Analysis (MVP)

- [ ] **AC1.1**: Screenshot with Japanese text → extracts all visible text
- [ ] **AC1.2**: Extracted text → shows readings, meanings, grammar notes
- [ ] **AC1.3**: Mixed kanji/hiragana/katakana → all types identified
- [ ] **AC1.4**: No Japanese text → informs user of no detection
- [ ] **Perf**: OCR + translation pipeline completes in <5s
- [ ] **Error**: Clear feedback when OCR fails
- [ ] **Obs**: Hook events for screenshot processing

### P2: Vocabulary Tracking

- [ ] **AC2.1**: 10 screenshots analyzed → list of unique words with status
- [ ] **AC2.2**: Known word appears → agent indicates already known
- [ ] **AC2.3**: New word appears → agent highlights as new vocabulary
- [ ] **AC2.4**: Statistics query → total words, weekly words, streak
- [ ] **Perf**: Vocabulary lookup completes in <2s
- [ ] **Error**: Graceful handling of database corruption
- [ ] **Obs**: Hook events for vocabulary growth

### P3: Flashcard Generation

- [ ] **AC3.1**: New word encountered → flashcard auto-created
- [ ] **AC3.2**: Review mode → cards presented in spaced repetition order
- [ ] **AC3.3**: Rate recall → next interval adjusted (SM-2)
- [ ] **AC3.4**: Review flashcard → see word in context from screenshot
- [ ] **Perf**: Flashcard creation in <1s, display in <500ms
- [ ] **Error**: Handle missing translations gracefully
- [ ] **Obs**: Hook events for flashcard creation and reviews

---

## 🐛 Common Issues

### Issue: manga-ocr takes forever to download

**Solution**: Pre-download PyTorch models:
```bash
uv run python -c "from manga_ocr import MangaOcr; MangaOcr()"
```
This will download ~1GB of models. Be patient.

### Issue: Database locked error

**Solution**: Ensure WAL mode is enabled:
```python
conn.execute("PRAGMA journal_mode=WAL")
```

### Issue: OCR accuracy is low (<90%)

**Solution**: Check image preprocessing:
1. Ensure grayscale conversion
2. Apply contrast enhancement
3. Upscale small text (2x)

### Issue: jamdict dictionary lookup is slow

**Solution**: Cache common words in memory:
```python
self.cache = {}  # Simple LRU cache
```

---

## 📦 Deployment

### Prerequisites

- ✅ All tests passing
- ✅ Constitution check gates passed
- ✅ Documentation updated (README.md, CLAUDE.md)

### Build Steps

```bash
# 1. Run full test suite
uv run pytest --cov=src --cov-report=term-missing

# 2. Verify constitution compliance
# (Manual check against .specify/memory/constitution.md)

# 3. Update requirements.txt
uv pip freeze > requirements.txt

# 4. Create database
uv run python -c "from src.repositories.base import init_database; init_database()"

# 5. Download dictionary
uv run python -c "import jamdict; jamdict.Jamdict()"
```

### User Setup

Users will need to:

1. Install dependencies: `uv pip install -r requirements.txt`
2. Configure screenshot directory in `config.yaml`
3. Run watcher: `uv run watcher.py`

---

## 📚 Additional Resources

- **Specification**: `specs/003-japanese-learning-agent/spec.md`
- **Plan**: `specs/003-japanese-learning-agent/plan.md`
- **Research**: `specs/003-japanese-learning-agent/research.md`
- **Data Model**: `specs/003-japanese-learning-agent/data-model.md`
- **Contracts**: `specs/003-japanese-learning-agent/contracts/`
- **Constitution**: `.specify/memory/constitution.md`

### External Documentation

- [manga-ocr](https://github.com/kha-white/manga-ocr)
- [jamdict](https://jamdict.readthedocs.io/)
- [SM-2 Algorithm](https://www.supermemo.com/en/archives1990-2015/english/ol/sm2)
- [UV Documentation](https://docs.astral.sh/uv/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)

---

## ✅ Next Steps

After completing this quickstart:

1. Run `/speckit.tasks` to generate dependency-ordered task list
2. Implement tasks in order (test-first approach)
3. Run `/speckit.analyze` to verify cross-artifact consistency
4. Create PR when all acceptance criteria met

Good luck! 🚀
