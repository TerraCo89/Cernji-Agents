# UV Script Interfaces Contract

**Feature**: Japanese Learning Agent
**Version**: 1.0.0
**Date**: 2025-10-21

This document defines the command-line interface contracts for all UV scripts in the Japanese Learning Agent. These interfaces MUST be implemented exactly as specified to ensure consistency and testability.

## Script Overview

| Script | Purpose | Priority |
|--------|---------|----------|
| `watcher.py` | Monitor screenshots directory and trigger OCR pipeline | P1 (MVP) |
| `vocab-cli.py` | Manage vocabulary (list, search, update status) | P2 |
| `flashcard-cli.py` | Review flashcards with spaced repetition | P3 |
| `stats-cli.py` | Display learning statistics | P2 |

## 1. watcher.py (Screenshot Watcher)

**Location**: `apps/japanese-tutor/src/cli/watcher.py`

**Description**: File system watcher that monitors a screenshot directory and automatically processes new images with OCR, vocabulary extraction, and flashcard generation.

### Usage

```bash
# Start watcher with default config
uv run watcher.py

# Start watcher with custom config
uv run watcher.py --config path/to/config.yaml

# Start watcher with specific directory (override config)
uv run watcher.py --watch-dir "C:\Screenshots"

# Dry run mode (don't save to database)
uv run watcher.py --dry-run
```

### Command-Line Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--config` | path | No | `config.yaml` | Path to configuration file |
| `--watch-dir` | path | No | From config | Directory to monitor (overrides config) |
| `--dry-run` | flag | No | False | Process screenshots but don't save to database |
| `--verbose` | flag | No | False | Enable verbose logging |

### Configuration File (config.yaml)

```yaml
screenshot_dir: "C:\\Path\\To\\Screenshots"
database_path: "../../data/japanese_learning.db"
ocr_model: "manga-ocr"  # or "easyocr"
min_confidence: 0.7  # Minimum OCR confidence to process
auto_flashcard: true  # Auto-create flashcards for new words
prompt_template: "prompts/japanese_tutor.md"  # Claude prompt (legacy)
```

### Behavior

1. **On startup**:
   - Load configuration
   - Initialize database connection
   - Initialize OCR model (manga-ocr)
   - Start file system watcher
   - Print monitoring status

2. **On new screenshot**:
   - Detect new image file (PNG/JPG/JPEG)
   - Run OCR extraction
   - Save screenshot record to database
   - Extract vocabulary words
   - Look up translations in JMDict
   - Update/insert vocabulary records
   - Auto-create flashcards if `auto_flashcard: true`
   - Print summary to console

3. **On error**:
   - Log error to console
   - Save screenshot with error status
   - Continue monitoring (don't crash)

### Output Format

```
🎮 Japanese Learning Agent - Screenshot Watcher
📁 Monitoring: C:\Screenshots
💾 Database: data/japanese_learning.db
🤖 OCR Model: manga-ocr
⚙️  Auto-flashcard: enabled

Waiting for new screenshots...

============================================================
📸 New screenshot: pokemon_red_001.png
============================================================

🔍 OCR Extraction:
   Confidence: 93%
   Text segments: 5
   Characters: 42

📚 Vocabulary Found:
   - ポケモン図鑑 (pokemon zukan) - "Pokémon encyclopedia" [NEW]
   - 完成 (kansei) - "completion" [KNOWN]
   - 夢 (yume) - "dream" [LEARNING]

✨ Flashcards Created: 1
   - ポケモン図鑑

⏱️  Processing time: 2.3s
============================================================
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Clean shutdown (Ctrl+C) |
| 1 | Configuration error |
| 2 | Database connection error |
| 3 | OCR model initialization error |
| 4 | Screenshot directory not found |

---

## 2. vocab-cli.py (Vocabulary Management)

**Location**: `apps/japanese-tutor/src/cli/vocab_cli.py`

**Description**: Command-line interface for managing vocabulary database (list, search, update status, export).

### Usage

```bash
# List all vocabulary
uv run vocab-cli.py list

# List by study status
uv run vocab-cli.py list --status new
uv run vocab-cli.py list --status learning
uv run vocab-cli.py list --status known

# Search vocabulary
uv run vocab-cli.py search "pokemon"
uv run vocab-cli.py search "完成"

# Show vocabulary details
uv run vocab-cli.py show 42

# Update study status
uv run vocab-cli.py mark 42 known
uv run vocab-cli.py mark 42 learning

# Display statistics
uv run vocab-cli.py stats

# Export vocabulary to CSV
uv run vocab-cli.py export vocabulary.csv
```

### Commands

#### `list` - List vocabulary

**Arguments**:

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--status` | choice | No | All | Filter by status: new/learning/known |
| `--sort` | choice | No | last_seen | Sort by: last_seen/encounter_count/kanji |
| `--limit` | int | No | 50 | Maximum results to display |

**Output**:
```
Vocabulary (status: new, sorted by: last_seen)

ID  | Kanji Form     | Reading      | Meaning                  | Encounters | Last Seen
----|----------------|--------------|--------------------------|------------|----------
42  | ポケモン図鑑   | pokemon zukan| Pokémon encyclopedia     | 1          | 2 hours ago
38  | 完成           | kansei       | completion               | 3          | 5 hours ago
...

Total: 45 words
```

#### `search` - Search vocabulary

**Arguments**:

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `query` | string | Yes | Search term (kanji, reading, or meaning) |

**Output**:
```
Search results for "pokemon":

ID  | Kanji Form     | Reading       | Meaning                  | Status
----|----------------|---------------|--------------------------|--------
42  | ポケモン図鑑   | pokemon zukan | Pokémon encyclopedia     | new
...

Found: 1 match
```

#### `show` - Show vocabulary details

**Arguments**:

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | int | Yes | Vocabulary ID |

**Output**:
```
Vocabulary #42

Kanji Form:       ポケモン図鑑
Hiragana Reading: ぽけもんずかん
Romaji Reading:   pokemon zukan
English Meaning:  Pokémon encyclopedia; illustrated Pokémon reference book
Part of Speech:   noun

Study Status:     new
Encounters:       1
First Seen:       2025-10-21 10:30:00
Last Seen:        2025-10-21 10:30:00

Flashcards:       1
  - Card #15 (due: in 6 days, reviews: 0)
```

#### `mark` - Update study status

**Arguments**:

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | int | Yes | Vocabulary ID |
| `status` | choice | Yes | New status: new/learning/known |

**Output**:
```
✓ Updated vocabulary #42 status: new → known
```

#### `stats` - Display statistics

**Output**:
```
Vocabulary Statistics

Total Words:           150
├─ New:                45
├─ Learning:           80
└─ Known:              25

Total Encounters:      420
Average Encounters:    2.8 per word

Most Common Words:
1. の (no) - 34 encounters
2. を (wo) - 28 encounters
3. は (wa) - 25 encounters

Most Recent:
1. ポケモン図鑑 (pokemon zukan) - 2 hours ago
2. 完成 (kansei) - 5 hours ago
3. 夢 (yume) - 1 day ago
```

#### `export` - Export to CSV

**Arguments**:

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `output` | path | Yes | - | Output CSV file path |
| `--status` | choice | No | All | Filter by status |

**Output**:
```
Exporting vocabulary to vocabulary.csv...
✓ Exported 150 words
```

---

## 3. flashcard-cli.py (Flashcard Review)

**Location**: `apps/japanese-tutor/src/cli/flashcard_cli.py`

**Description**: Interactive flashcard review interface with spaced repetition (SM-2 algorithm).

### Usage

```bash
# Start review session (default: 20 cards)
uv run flashcard-cli.py review

# Review specific number of cards
uv run flashcard-cli.py review --limit 10

# Show cards due for review
uv run flashcard-cli.py due

# Show review statistics
uv run flashcard-cli.py stats
```

### Commands

#### `review` - Start review session

**Arguments**:

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--limit` | int | No | 20 | Maximum cards to review |
| `--shuffle` | flag | No | False | Randomize card order |

**Behavior**:

1. Query flashcards where `next_review_at <= NOW`
2. Display front (Japanese word + reading)
3. Wait for user input (press Enter to reveal)
4. Display back (meaning + example)
5. Prompt for rating: 1=again, 2=hard, 3=medium, 4=easy
6. Update flashcard with SM-2 algorithm
7. Save review session record
8. Repeat for next card

**Interactive Output**:
```
Flashcard Review Session
========================

Cards due: 23
Reviewing: 20 cards

Card 1/20

Front:
┌─────────────────────────────────┐
│                                 │
│       ポケモン図鑑               │
│                                 │
│     (pokemon zukan)             │
│                                 │
└─────────────────────────────────┘

[Press Enter to reveal answer]

Back:
┌─────────────────────────────────┐
│                                 │
│   Pokémon encyclopedia          │
│                                 │
│   Example:                      │
│   "Completing the Pokédex       │
│    is my dream!"                │
│                                 │
└─────────────────────────────────┘

How well did you know this?
  1 = Again (forgot completely)
  2 = Hard (difficult to recall)
  3 = Medium (some effort required)
  4 = Easy (perfect recall)

Your rating [1-4]: 3

✓ Card scheduled for review in 6 days

---

[Continue to next card...]

Review Session Complete!
========================

Cards reviewed:    20
Correct:           17 (85%)
Again:             3
Hard:              4
Medium:            8
Easy:              5

Average response:  3.2s

Great work! 23 cards remaining for today.
```

#### `due` - Show due flashcards

**Output**:
```
Flashcards Due for Review

Due Now:           23 cards
Overdue:           5 cards

Next 7 Days:
  Today:           23
  Tomorrow:        15
  Day 3:           12
  Day 4:           8
  Day 5:           20
  Day 6:           6
  Day 7:           10

Total flashcards:  150
Average interval:  12.5 days
```

#### `stats` - Review statistics

**Output**:
```
Review Statistics

All Time:
  Total Reviews:        342
  Accuracy Rate:        87%
  Avg Response Time:    4.2s

This Week:
  Reviews:              78
  New Cards:            12
  Accuracy Rate:        89%

Today:
  Reviews:              15
  Accuracy Rate:        93%
  Study Time:           2m 30s

Performance Trend:
  Week 1:  82% ████████░░
  Week 2:  85% █████████░
  Week 3:  87% █████████░
  Week 4:  89% ██████████
```

---

## 4. stats-cli.py (Statistics Dashboard)

**Location**: `apps/japanese-tutor/src/cli/stats_cli.py`

**Description**: Display comprehensive learning statistics and analytics.

### Usage

```bash
# Show overall statistics
uv run stats-cli.py

# Show statistics for specific date range
uv run stats-cli.py --from 2025-10-01 --to 2025-10-21

# Export statistics to JSON
uv run stats-cli.py --export stats.json
```

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--from` | date | No | 30 days ago | Start date (YYYY-MM-DD) |
| `--to` | date | No | Today | End date (YYYY-MM-DD) |
| `--export` | path | No | - | Export to JSON file |

### Output

```
Japanese Learning Statistics
============================

Vocabulary Progress
-------------------
Total Words:           150
├─ New:                45 (30%)
├─ Learning:           80 (53%)
└─ Known:              25 (17%)

Total Encounters:      420
Avg per Word:          2.8

Flashcard Performance
---------------------
Total Flashcards:      120
Cards Reviewed:        342 times
Overall Accuracy:      87%

Current Streak:        12 days 🔥
Best Streak:           18 days

Review Activity (Last 30 Days)
-------------------------------
  Oct 21: ████████████ 23 reviews
  Oct 20: ████████░░░░ 15 reviews
  Oct 19: ██████░░░░░░ 10 reviews
  ...

Study Time (Last 30 Days)
-------------------------
Total:                 12h 45m
Average per Day:       25m
Most Active Day:       Oct 15 (1h 20m)

Top Vocabulary
--------------
Most Encountered:
  1. の (no) - 34 times
  2. を (wo) - 28 times
  3. は (wa) - 25 times

Recently Mastered:
  1. ポケモン (pokemon) - Oct 20
  2. 図鑑 (zukan) - Oct 19
  3. 完成 (kansei) - Oct 18

Achievement Unlocked!
---------------------
🏆 "Week Warrior" - 7 day study streak
🏆 "Vocabulary Voyager" - 100 words learned
```

---

## Error Handling

All scripts MUST handle errors gracefully with:

1. **Clear error messages**: Explain what went wrong and how to fix it
2. **Non-zero exit codes**: Return appropriate exit code for error type
3. **No stack traces in production**: Only show stack traces with `--verbose` flag
4. **Validation**: Validate all inputs before processing

### Common Error Exit Codes

| Code | Error Type | Description |
|------|------------|-------------|
| 0 | Success | Operation completed successfully |
| 1 | Configuration Error | Invalid config file or missing settings |
| 2 | Database Error | Database connection or query error |
| 3 | File Not Found | Required file or directory not found |
| 4 | Validation Error | Invalid input arguments |
| 5 | OCR Error | OCR model initialization or processing error |
| 10 | General Error | Unexpected error (catch-all) |

### Example Error Output

```
❌ Error: Screenshot directory not found

The configured screenshot directory does not exist:
  C:\Invalid\Path\Screenshots

Please check your config.yaml and ensure:
  1. The path is correct
  2. The directory exists
  3. You have read permissions

Exit code: 3
```

---

## Testing Requirements

All CLI scripts MUST have contract tests that verify:

1. **Argument parsing**: All arguments are accepted and validated correctly
2. **Exit codes**: Correct exit codes for success/error scenarios
3. **Output format**: Output matches the contract specification
4. **Error handling**: Errors produce expected messages and exit codes
5. **Integration**: Scripts interact correctly with database and services

### Test Location

`apps/japanese-tutor/tests/contract/test_cli_interfaces.py`

### Example Test

```python
def test_vocab_list_command():
    """Test vocab-cli.py list command"""
    result = subprocess.run(
        ['uv', 'run', 'vocab-cli.py', 'list', '--status', 'new', '--limit', '10'],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert 'Vocabulary (status: new' in result.stdout
    assert 'Total:' in result.stdout
```

---

## Implementation Notes

1. **Use argparse**: All scripts use `argparse` for argument parsing
2. **Use rich library**: Optional but recommended for colored/formatted output
3. **Use Pydantic models**: All data validation via Pydantic models
4. **Use repositories**: Database access only through repository layer
5. **PEP 723 dependencies**: Use inline script dependencies for UV
6. **Logging**: Use Python `logging` module, not print statements
7. **Internationalization**: Prepare for future i18n (English only for MVP)

---

This contract MUST be followed during implementation. Any deviations require updating this document first.
