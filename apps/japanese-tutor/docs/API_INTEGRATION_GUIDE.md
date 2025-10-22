# API Integration Guide
**Japanese Learning Application - Database API Patterns**

Version: 1.0  
Last Updated: 2025-10-22  
Target Audience: Backend Developers, API Designers

---

## Table of Contents

1. [Overview](#overview)
2. [Database Connection](#database-connection)
3. [Core API Patterns](#core-api-patterns)
4. [CRUD Operations](#crud-operations)
5. [Complex Queries](#complex-queries)
6. [Transaction Management](#transaction-management)
7. [Error Handling](#error-handling)
8. [Performance Best Practices](#performance-best-practices)
9. [API Examples](#api-examples)

---

## Overview

This guide provides code examples and best practices for interacting with the Japanese Learning application database. All examples use prepared statements and proper error handling to ensure security and reliability.

### Technology Stack Assumptions

- **Database**: SQLite 3
- **Primary Examples**: Python (sqlite3), TypeScript (better-sqlite3)
- **Patterns**: Applicable to any SQLite driver

---

## Database Connection

### Python (sqlite3)

```python
import sqlite3
from contextlib import contextmanager

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        # CRITICAL: Enable foreign keys
        conn.execute('PRAGMA foreign_keys = ON')
        # Use Row factory for dict-like access
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute(self, query: str, params=None):
        """Execute a single query"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            conn.commit()
            return cursor
    
    def fetchone(self, query: str, params=None):
        """Fetch a single row"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            return cursor.fetchone()
    
    def fetchall(self, query: str, params=None):
        """Fetch all rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            return cursor.fetchall()

# Usage
db = Database('data/japanese_agent.db')
```

### TypeScript (better-sqlite3)

```typescript
import Database from 'better-sqlite3';

class DatabaseClient {
  private db: Database.Database;
  
  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    // CRITICAL: Enable foreign keys
    this.db.pragma('foreign_keys = ON');
    // Enable WAL mode for better concurrency
    this.db.pragma('journal_mode = WAL');
  }
  
  prepare<T = any>(sql: string) {
    return this.db.prepare<T>(sql);
  }
  
  transaction<T>(fn: () => T): T {
    const trans = this.db.transaction(fn);
    return trans();
  }
  
  close() {
    this.db.close();
  }
}

// Usage
const db = new DatabaseClient('data/japanese_agent.db');
```

### Node.js (better-sqlite3) Alternative

```typescript
import Database from 'better-sqlite3';

const db = new Database('data/japanese_agent.db');
db.pragma('foreign_keys = ON');
db.pragma('journal_mode = WAL');

export default db;
```

---

## Core API Patterns

### Pattern 1: Repository Pattern

**Python Example**:

```python
from typing import Optional, List
from datetime import datetime
import sqlite3

class VocabularyRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, vocab: dict) -> int:
        """Create new vocabulary entry"""
        query = """
            INSERT INTO vocabulary (
                kanji_form, hiragana_reading, english_meaning,
                romaji_reading, part_of_speech, jlpt_level,
                study_status, encounter_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.db.execute(query, [
            vocab['kanji_form'],
            vocab['hiragana_reading'],
            vocab['english_meaning'],
            vocab.get('romaji_reading'),
            vocab.get('part_of_speech'),
            vocab.get('jlpt_level'),
            vocab.get('study_status', 'new'),
            vocab.get('encounter_count', 1)
        ])
        return cursor.lastrowid
    
    def get_by_id(self, vocab_id: int) -> Optional[dict]:
        """Get vocabulary by ID"""
        query = "SELECT * FROM vocabulary WHERE id = ?"
        row = self.db.fetchone(query, [vocab_id])
        return dict(row) if row else None
    
    def find_by_text(self, kanji: str, reading: str) -> Optional[dict]:
        """Find vocabulary by text and reading"""
        query = """
            SELECT * FROM vocabulary 
            WHERE kanji_form = ? AND hiragana_reading = ?
        """
        row = self.db.fetchone(query, [kanji, reading])
        return dict(row) if row else None
    
    def update(self, vocab_id: int, updates: dict) -> bool:
        """Update vocabulary fields"""
        # Build dynamic UPDATE query
        fields = ', '.join(f"{k} = ?" for k in updates.keys())
        query = f"UPDATE vocabulary SET {fields} WHERE id = ?"
        params = list(updates.values()) + [vocab_id]
        
        cursor = self.db.execute(query, params)
        return cursor.rowcount > 0
    
    def increment_encounter(self, vocab_id: int):
        """Increment encounter count"""
        query = """
            UPDATE vocabulary 
            SET encounter_count = encounter_count + 1,
                last_seen_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        self.db.execute(query, [vocab_id])
    
    def list_by_status(self, status: str, limit: int = 50, 
                      offset: int = 0) -> List[dict]:
        """List vocabulary by study status"""
        query = """
            SELECT * FROM vocabulary 
            WHERE study_status = ?
            ORDER BY last_seen_at DESC
            LIMIT ? OFFSET ?
        """
        rows = self.db.fetchall(query, [status, limit, offset])
        return [dict(row) for row in rows]
    
    def search(self, search_term: str, limit: int = 50) -> List[dict]:
        """Search vocabulary by kanji or meaning"""
        query = """
            SELECT * FROM vocabulary 
            WHERE kanji_form LIKE ? 
               OR hiragana_reading LIKE ?
               OR english_meaning LIKE ?
            LIMIT ?
        """
        pattern = f"%{search_term}%"
        rows = self.db.fetchall(query, [pattern, pattern, pattern, limit])
        return [dict(row) for row in rows]
    
    def delete(self, vocab_id: int) -> bool:
        """Delete vocabulary (cascades to flashcards)"""
        query = "DELETE FROM vocabulary WHERE id = ?"
        cursor = self.db.execute(query, [vocab_id])
        return cursor.rowcount > 0
```

**TypeScript Example**:

```typescript
interface Vocabulary {
  id?: number;
  kanji_form: string;
  hiragana_reading: string;
  english_meaning: string;
  romaji_reading?: string;
  part_of_speech?: string;
  jlpt_level?: 'N5' | 'N4' | 'N3' | 'N2' | 'N1';
  study_status?: 'new' | 'learning' | 'reviewing' | 'mastered' | 'suspended';
  encounter_count?: number;
  // ... other fields
}

class VocabularyRepository {
  constructor(private db: DatabaseClient) {}
  
  create(vocab: Vocabulary): number {
    const stmt = this.db.prepare(`
      INSERT INTO vocabulary (
        kanji_form, hiragana_reading, english_meaning,
        romaji_reading, part_of_speech, jlpt_level,
        study_status, encounter_count
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);
    
    const result = stmt.run(
      vocab.kanji_form,
      vocab.hiragana_reading,
      vocab.english_meaning,
      vocab.romaji_reading || null,
      vocab.part_of_speech || null,
      vocab.jlpt_level || null,
      vocab.study_status || 'new',
      vocab.encounter_count || 1
    );
    
    return result.lastInsertRowid as number;
  }
  
  getById(id: number): Vocabulary | null {
    const stmt = this.db.prepare('SELECT * FROM vocabulary WHERE id = ?');
    return stmt.get(id) as Vocabulary | null;
  }
  
  findByText(kanji: string, reading: string): Vocabulary | null {
    const stmt = this.db.prepare(`
      SELECT * FROM vocabulary 
      WHERE kanji_form = ? AND hiragana_reading = ?
    `);
    return stmt.get(kanji, reading) as Vocabulary | null;
  }
  
  update(id: number, updates: Partial<Vocabulary>): boolean {
    const fields = Object.keys(updates);
    const values = Object.values(updates);
    
    const setClause = fields.map(f => `${f} = ?`).join(', ');
    const stmt = this.db.prepare(
      `UPDATE vocabulary SET ${setClause} WHERE id = ?`
    );
    
    const result = stmt.run(...values, id);
    return result.changes > 0;
  }
  
  incrementEncounter(id: number): void {
    const stmt = this.db.prepare(`
      UPDATE vocabulary 
      SET encounter_count = encounter_count + 1,
          last_seen_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `);
    stmt.run(id);
  }
  
  listByStatus(
    status: string, 
    limit: number = 50, 
    offset: number = 0
  ): Vocabulary[] {
    const stmt = this.db.prepare(`
      SELECT * FROM vocabulary 
      WHERE study_status = ?
      ORDER BY last_seen_at DESC
      LIMIT ? OFFSET ?
    `);
    return stmt.all(status, limit, offset) as Vocabulary[];
  }
}
```

### Pattern 2: Service Layer

**Encapsulates business logic and coordinates between repositories**

```python
class VocabularyService:
    def __init__(self, db: Database):
        self.vocab_repo = VocabularyRepository(db)
        self.flashcard_repo = FlashcardRepository(db)
        self.screenshot_vocab_repo = ScreenshotVocabularyRepository(db)
    
    def create_or_update_from_screenshot(
        self, 
        kanji: str, 
        reading: str, 
        screenshot_id: int,
        position: int,
        context: str
    ) -> dict:
        """Create new vocabulary or update existing from screenshot"""
        
        # Check if vocabulary exists
        existing = self.vocab_repo.find_by_text(kanji, reading)
        
        if existing:
            # Update encounter count
            self.vocab_repo.increment_encounter(existing['id'])
            vocab_id = existing['id']
        else:
            # Create new vocabulary (requires meaning lookup)
            meaning = self._lookup_meaning(kanji, reading)
            vocab_id = self.vocab_repo.create({
                'kanji_form': kanji,
                'hiragana_reading': reading,
                'english_meaning': meaning,
                'study_status': 'new',
                'encounter_count': 1
            })
        
        # Link to screenshot
        self.screenshot_vocab_repo.create({
            'screenshot_id': screenshot_id,
            'vocabulary_id': vocab_id,
            'position_in_text': position,
            'context_snippet': context
        })
        
        return self.vocab_repo.get_by_id(vocab_id)
    
    def create_flashcard_for_vocabulary(
        self, 
        vocab_id: int, 
        card_type: str = 'recognition',
        screenshot_id: Optional[int] = None
    ) -> dict:
        """Create flashcard and update vocabulary status"""
        
        # Check if flashcard already exists
        existing_card = self.flashcard_repo.find_by_vocabulary(vocab_id)
        if existing_card:
            raise ValueError("Flashcard already exists for this vocabulary")
        
        # Create flashcard
        flashcard_id = self.flashcard_repo.create({
            'vocabulary_id': vocab_id,
            'screenshot_id': screenshot_id,
            'card_type': card_type,
            'status': 'active',
            'next_review_at': datetime.now(),  # Due immediately
            'ease_factor': 2.5,
            'interval_days': 0.0
        })
        
        # Update vocabulary status to 'learning'
        self.vocab_repo.update(vocab_id, {'study_status': 'learning'})
        
        return self.flashcard_repo.get_by_id(flashcard_id)
    
    def _lookup_meaning(self, kanji: str, reading: str) -> str:
        """Lookup meaning from external dictionary API"""
        # Implementation would call dictionary API
        # Placeholder for now
        return "Unknown meaning"
```

---

## CRUD Operations

### Create Operations

**Single Insert**:
```python
def create_source(name: str, source_type: str, difficulty: str) -> int:
    query = """
        INSERT INTO sources (name, type, difficulty_level, is_active)
        VALUES (?, ?, ?, 1)
    """
    cursor = db.execute(query, [name, source_type, difficulty])
    return cursor.lastrowid
```

**Batch Insert** (More efficient):
```python
def create_multiple_vocabulary(vocab_list: List[dict]):
    """Insert multiple vocabulary entries in one transaction"""
    query = """
        INSERT INTO vocabulary (
            kanji_form, hiragana_reading, english_meaning
        ) VALUES (?, ?, ?)
    """
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        data = [
            (v['kanji_form'], v['hiragana_reading'], v['english_meaning'])
            for v in vocab_list
        ]
        cursor.executemany(query, data)
        conn.commit()
```

### Read Operations

**Single Record**:
```typescript
function getVocabularyById(id: number): Vocabulary | null {
  const stmt = db.prepare('SELECT * FROM vocabulary WHERE id = ?');
  return stmt.get(id) as Vocabulary | null;
}
```

**List with Pagination**:
```typescript
interface PaginationOptions {
  limit: number;
  offset: number;
  orderBy?: string;
  orderDir?: 'ASC' | 'DESC';
}

function listVocabulary(options: PaginationOptions): Vocabulary[] {
  const { limit, offset, orderBy = 'created_at', orderDir = 'DESC' } = options;
  
  const stmt = db.prepare(`
    SELECT * FROM vocabulary
    ORDER BY ${orderBy} ${orderDir}
    LIMIT ? OFFSET ?
  `);
  
  return stmt.all(limit, offset) as Vocabulary[];
}
```

**Filtered List**:
```python
def get_due_flashcards(limit: int = 100) -> List[dict]:
    """Get flashcards due for review"""
    query = """
        SELECT f.*, v.*
        FROM flashcards f
        JOIN vocabulary v ON f.vocabulary_id = v.id
        WHERE f.status = 'active'
          AND f.next_review_at <= datetime('now')
        ORDER BY f.next_review_at
        LIMIT ?
    """
    rows = db.fetchall(query, [limit])
    return [dict(row) for row in rows]
```

### Update Operations

**Single Field Update**:
```python
def update_study_status(vocab_id: int, new_status: str):
    query = "UPDATE vocabulary SET study_status = ? WHERE id = ?"
    db.execute(query, [new_status, vocab_id])
```

**Multiple Fields**:
```typescript
function updateFlashcard(id: number, updates: Partial<Flashcard>): boolean {
  const fields = Object.keys(updates);
  const values = Object.values(updates);
  
  const setClause = fields.map(f => `${f} = ?`).join(', ');
  const stmt = db.prepare(`
    UPDATE flashcards SET ${setClause} WHERE id = ?
  `);
  
  const result = stmt.run(...values, id);
  return result.changes > 0;
}
```

**Conditional Update**:
```python
def update_if_not_modified(vocab_id: int, expected_updated_at: str, 
                          updates: dict) -> bool:
    """Update only if record hasn't been modified (optimistic locking)"""
    fields = ', '.join(f"{k} = ?" for k in updates.keys())
    query = f"""
        UPDATE vocabulary 
        SET {fields}
        WHERE id = ? AND updated_at = ?
    """
    params = list(updates.values()) + [vocab_id, expected_updated_at]
    cursor = db.execute(query, params)
    return cursor.rowcount > 0
```

### Delete Operations

**Simple Delete**:
```typescript
function deleteSource(id: number): boolean {
  // Foreign key constraints will handle cascading
  const stmt = db.prepare('DELETE FROM sources WHERE id = ?');
  const result = stmt.run(id);
  return result.changes > 0;
}
```

**Soft Delete**:
```python
def archive_flashcard(flashcard_id: int):
    """Soft delete by changing status"""
    query = "UPDATE flashcards SET status = 'archived' WHERE id = ?"
    db.execute(query, [flashcard_id])
```

---

## Complex Queries

### Query 1: Vocabulary with Related Data

```python
def get_vocabulary_with_context(vocab_id: int) -> dict:
    """Get vocabulary with all related information"""
    
    # Main vocabulary
    vocab = db.fetchone(
        "SELECT * FROM vocabulary WHERE id = ?", 
        [vocab_id]
    )
    
    if not vocab:
        return None
    
    result = dict(vocab)
    
    # Get flashcards
    result['flashcards'] = db.fetchall("""
        SELECT * FROM flashcards 
        WHERE vocabulary_id = ?
    """, [vocab_id])
    
    # Get example sentences
    result['examples'] = db.fetchall("""
        SELECT * FROM example_sentences 
        WHERE vocabulary_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    """, [vocab_id])
    
    # Get kanji breakdown
    result['kanji'] = db.fetchall("""
        SELECT k.*, vk.position
        FROM kanji k
        JOIN vocabulary_kanji vk ON k.id = vk.kanji_id
        WHERE vk.vocabulary_id = ?
        ORDER BY vk.position
    """, [vocab_id])
    
    # Get screenshots where this word appears
    result['screenshots'] = db.fetchall("""
        SELECT s.*, sv.context_snippet
        FROM screenshots s
        JOIN screenshot_vocabulary sv ON s.id = sv.screenshot_id
        WHERE sv.vocabulary_id = ?
        ORDER BY s.created_at DESC
        LIMIT 10
    """, [vocab_id])
    
    # Get tags
    result['tags'] = db.fetchall("""
        SELECT t.*
        FROM tags t
        JOIN vocabulary_tags vt ON t.id = vt.tag_id
        WHERE vt.vocabulary_id = ?
    """, [vocab_id])
    
    return result
```

### Query 2: Dashboard Statistics

```typescript
interface DashboardStats {
  dueCards: {
    overdue: number;
    today: number;
    thisWeek: number;
  };
  todayActivity: {
    reviews: number;
    accuracy: number;
    avgQuality: number;
  };
  vocabularyProgress: {
    new: number;
    learning: number;
    reviewing: number;
    mastered: number;
  };
  studyGoals: Array<{
    type: string;
    target: number;
    current: number;
    progress: number;
  }>;
}

function getDashboardStats(): DashboardStats {
  // Due cards
  const dueCards = db.prepare(`
    SELECT 
      SUM(CASE WHEN next_review_at < datetime('now') THEN 1 ELSE 0 END) as overdue,
      SUM(CASE WHEN date(next_review_at) = date('now') THEN 1 ELSE 0 END) as today,
      SUM(CASE WHEN next_review_at <= datetime('now', '+7 days') THEN 1 ELSE 0 END) as this_week
    FROM flashcards
    WHERE status = 'active'
  `).get() as any;
  
  // Today's activity
  const todayActivity = db.prepare(`
    SELECT 
      COUNT(*) as reviews,
      ROUND(AVG(CASE WHEN correct THEN 100.0 ELSE 0 END), 1) as accuracy,
      ROUND(AVG(quality_rating), 2) as avg_quality
    FROM review_sessions
    WHERE date(reviewed_at) = date('now')
  `).get() as any;
  
  // Vocabulary progress
  const vocabProgress = db.prepare(`
    SELECT 
      study_status,
      COUNT(*) as count
    FROM vocabulary
    GROUP BY study_status
  `).all() as any[];
  
  const vocabByStatus = {
    new: 0,
    learning: 0,
    reviewing: 0,
    mastered: 0
  };
  vocabProgress.forEach(row => {
    vocabByStatus[row.study_status] = row.count;
  });
  
  // Study goals
  const goals = db.prepare(`
    SELECT 
      goal_type as type,
      target_value as target,
      current_value as current,
      ROUND(current_value * 100.0 / target_value, 1) as progress
    FROM study_goals
    WHERE is_active = 1
      AND date('now') BETWEEN start_date AND COALESCE(end_date, date('now'))
  `).all() as any[];
  
  return {
    dueCards,
    todayActivity,
    vocabularyProgress: vocabByStatus,
    studyGoals: goals
  };
}
```

### Query 3: Advanced Vocabulary Search

```python
def advanced_vocabulary_search(filters: dict) -> List[dict]:
    """
    Search vocabulary with multiple filters:
    - text: Search in kanji, reading, or meaning
    - jlpt_level: Filter by JLPT level
    - study_status: Filter by status
    - tags: Filter by tags (array)
    - has_flashcard: Boolean
    - min_encounters: Minimum encounter count
    """
    
    conditions = ["1=1"]  # Always true, for easy AND chaining
    params = []
    
    # Text search
    if filters.get('text'):
        conditions.append("""
            (kanji_form LIKE ? OR hiragana_reading LIKE ? OR english_meaning LIKE ?)
        """)
        pattern = f"%{filters['text']}%"
        params.extend([pattern, pattern, pattern])
    
    # JLPT level
    if filters.get('jlpt_level'):
        conditions.append("jlpt_level = ?")
        params.append(filters['jlpt_level'])
    
    # Study status
    if filters.get('study_status'):
        if isinstance(filters['study_status'], list):
            placeholders = ','.join('?' * len(filters['study_status']))
            conditions.append(f"study_status IN ({placeholders})")
            params.extend(filters['study_status'])
        else:
            conditions.append("study_status = ?")
            params.append(filters['study_status'])
    
    # Minimum encounters
    if filters.get('min_encounters'):
        conditions.append("encounter_count >= ?")
        params.append(filters['min_encounters'])
    
    # Has flashcard
    if filters.get('has_flashcard') is not None:
        if filters['has_flashcard']:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM flashcards 
                    WHERE vocabulary_id = vocabulary.id 
                      AND status != 'archived'
                )
            """)
        else:
            conditions.append("""
                NOT EXISTS (
                    SELECT 1 FROM flashcards 
                    WHERE vocabulary_id = vocabulary.id 
                      AND status != 'archived'
                )
            """)
    
    # Tags
    if filters.get('tags'):
        tag_conditions = []
        for tag in filters['tags']:
            tag_conditions.append("""
                EXISTS (
                    SELECT 1 FROM vocabulary_tags vt
                    JOIN tags t ON vt.tag_id = t.id
                    WHERE vt.vocabulary_id = vocabulary.id
                      AND t.name = ?
                )
            """)
            params.append(tag)
        conditions.append(f"({' AND '.join(tag_conditions)})")
    
    # Build final query
    where_clause = " AND ".join(conditions)
    
    # Pagination
    limit = filters.get('limit', 50)
    offset = filters.get('offset', 0)
    order_by = filters.get('order_by', 'last_seen_at')
    order_dir = filters.get('order_dir', 'DESC')
    
    query = f"""
        SELECT DISTINCT vocabulary.*
        FROM vocabulary
        WHERE {where_clause}
        ORDER BY {order_by} {order_dir}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    
    rows = db.fetchall(query, params)
    return [dict(row) for row in rows]
```

---

## Transaction Management

### Pattern 1: Simple Transaction

```python
def transfer_vocabulary_between_sources(
    vocab_id: int, 
    from_source_id: int, 
    to_source_id: int
):
    """Move vocabulary between sources atomically"""
    with db.get_connection() as conn:
        try:
            cursor = conn.cursor()
            
            # Update screenshots
            cursor.execute("""
                UPDATE screenshots 
                SET source_id = ?
                WHERE source_id = ?
                  AND id IN (
                      SELECT screenshot_id 
                      FROM screenshot_vocabulary 
                      WHERE vocabulary_id = ?
                  )
            """, [to_source_id, from_source_id, vocab_id])
            
            # Update source last_accessed
            cursor.execute("""
                UPDATE sources 
                SET last_accessed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, [to_source_id])
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
```

### Pattern 2: Review Session Transaction

```typescript
interface ReviewResult {
  qualityRating: number;
  responseTimeMs: number;
  userAnswer?: string;
}

function processReview(
  flashcardId: number, 
  result: ReviewResult
): void {
  // Use transaction for atomic updates
  db.transaction(() => {
    // Get current flashcard state
    const flashcard = db.prepare(
      'SELECT * FROM flashcards WHERE id = ?'
    ).get(flashcardId) as Flashcard;
    
    if (!flashcard) {
      throw new Error('Flashcard not found');
    }
    
    // Calculate new SRS values
    const correct = result.qualityRating >= 3;
    const srsUpdate = calculateSRS(flashcard, result.qualityRating);
    
    // 1. Create review session record
    db.prepare(`
      INSERT INTO review_sessions (
        flashcard_id, session_id, quality_rating,
        user_answer, correct, response_time_ms,
        interval_before_days, ease_factor_before,
        ease_factor_after
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      flashcardId,
      generateSessionId(),
      result.qualityRating,
      result.userAnswer || null,
      correct ? 1 : 0,
      result.responseTimeMs,
      flashcard.interval_days,
      flashcard.ease_factor,
      srsUpdate.easeFactor
    );
    
    // 2. Update flashcard
    db.prepare(`
      UPDATE flashcards SET
        last_reviewed_at = CURRENT_TIMESTAMP,
        next_review_at = ?,
        ease_factor = ?,
        interval_days = ?,
        review_count = review_count + 1,
        consecutive_correct = ?,
        lapses = ?
      WHERE id = ?
    `).run(
      srsUpdate.nextReviewAt,
      srsUpdate.easeFactor,
      srsUpdate.intervalDays,
      srsUpdate.consecutiveCorrect,
      srsUpdate.lapses,
      flashcardId
    );
    
    // 3. Update vocabulary
    db.prepare(`
      UPDATE vocabulary 
      SET last_seen_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `).run(flashcard.vocabulary_id);
    
    // 4. Update study goals
    db.prepare(`
      UPDATE study_goals 
      SET current_value = current_value + 1
      WHERE goal_type = 'daily_reviews'
        AND is_active = 1
        AND date('now') BETWEEN start_date AND COALESCE(end_date, date('now'))
    `).run();
  })();
}

function calculateSRS(flashcard: Flashcard, quality: number) {
  // SM-2 algorithm implementation
  let easeFactor = flashcard.ease_factor;
  let intervalDays = flashcard.interval_days;
  let consecutiveCorrect = flashcard.consecutive_correct;
  let lapses = flashcard.lapses;
  
  if (quality >= 3) {
    // Correct answer
    consecutiveCorrect += 1;
    
    if (intervalDays === 0) {
      intervalDays = 1;
    } else if (intervalDays === 1) {
      intervalDays = 6;
    } else {
      intervalDays = Math.round(intervalDays * easeFactor);
    }
    
    // Adjust ease factor
    easeFactor = easeFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
  } else {
    // Incorrect answer
    consecutiveCorrect = 0;
    lapses += 1;
    intervalDays = 0;  // Relearn
    easeFactor = Math.max(1.3, easeFactor - 0.2);
  }
  
  easeFactor = Math.max(1.3, easeFactor);
  
  const now = new Date();
  const nextReviewAt = new Date(now.getTime() + intervalDays * 24 * 60 * 60 * 1000);
  
  return {
    easeFactor,
    intervalDays,
    consecutiveCorrect,
    lapses,
    nextReviewAt: nextReviewAt.toISOString()
  };
}
```

### Pattern 3: Screenshot Import Transaction

```python
def import_screenshot_with_vocabulary(
    image_path: str,
    source_id: int,
    ocr_results: dict
) -> dict:
    """Import screenshot and extract vocabulary atomically"""
    
    with db.get_connection() as conn:
        try:
            cursor = conn.cursor()
            
            # 1. Create screenshot
            cursor.execute("""
                INSERT INTO screenshots (
                    file_path, source_id, ocr_confidence,
                    extracted_text_json, checksum, has_furigana
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, [
                image_path,
                source_id,
                ocr_results['confidence'],
                json.dumps(ocr_results['blocks']),
                calculate_checksum(image_path),
                ocr_results['has_furigana']
            ])
            screenshot_id = cursor.lastrowid
            
            # 2. Process each detected word
            vocab_created = []
            vocab_updated = []
            
            for word in ocr_results['words']:
                # Check if vocabulary exists
                cursor.execute("""
                    SELECT id, encounter_count 
                    FROM vocabulary
                    WHERE kanji_form = ? AND hiragana_reading = ?
                """, [word['text'], word['reading']])
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    vocab_id = existing[0]
                    cursor.execute("""
                        UPDATE vocabulary
                        SET encounter_count = encounter_count + 1,
                            last_seen_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, [vocab_id])
                    vocab_updated.append(vocab_id)
                else:
                    # Create new
                    meaning = lookup_meaning(word['text'], word['reading'])
                    cursor.execute("""
                        INSERT INTO vocabulary (
                            kanji_form, hiragana_reading, english_meaning,
                            study_status, encounter_count
                        ) VALUES (?, ?, ?, 'new', 1)
                    """, [word['text'], word['reading'], meaning])
                    vocab_id = cursor.lastrowid
                    vocab_created.append(vocab_id)
                
                # 3. Link vocabulary to screenshot
                cursor.execute("""
                    INSERT INTO screenshot_vocabulary (
                        screenshot_id, vocabulary_id,
                        position_in_text, context_snippet
                    ) VALUES (?, ?, ?, ?)
                """, [
                    screenshot_id,
                    vocab_id,
                    word['position'],
                    word['context']
                ])
            
            # 4. Update source last_accessed
            cursor.execute("""
                UPDATE sources
                SET last_accessed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, [source_id])
            
            conn.commit()
            
            return {
                'screenshot_id': screenshot_id,
                'vocabulary_created': vocab_created,
                'vocabulary_updated': vocab_updated
            }
            
        except Exception as e:
            conn.rollback()
            raise
```

---

## Error Handling

### SQLite Error Types

```python
import sqlite3

class DatabaseError(Exception):
    """Base database error"""
    pass

class ConstraintViolationError(DatabaseError):
    """Foreign key or check constraint violated"""
    pass

class DuplicateRecordError(DatabaseError):
    """Unique constraint violated"""
    pass

class NotFoundError(DatabaseError):
    """Record not found"""
    pass

def handle_sqlite_error(e: sqlite3.Error) -> DatabaseError:
    """Convert SQLite errors to application errors"""
    error_msg = str(e)
    
    if "FOREIGN KEY constraint failed" in error_msg:
        return ConstraintViolationError(
            "Referenced record does not exist"
        )
    elif "UNIQUE constraint failed" in error_msg:
        return DuplicateRecordError(
            "Record with these values already exists"
        )
    elif "CHECK constraint failed" in error_msg:
        field = error_msg.split("CHECK constraint failed: ")[-1]
        return ConstraintViolationError(
            f"Invalid value for {field}"
        )
    else:
        return DatabaseError(error_msg)

# Usage in repository
def create_vocabulary(vocab: dict) -> int:
    try:
        cursor = db.execute(query, params)
        return cursor.lastrowid
    except sqlite3.Error as e:
        raise handle_sqlite_error(e)
```

### TypeScript Error Handling

```typescript
class DatabaseError extends Error {
  constructor(message: string, public code?: string) {
    super(message);
    this.name = 'DatabaseError';
  }
}

class ConstraintViolationError extends DatabaseError {
  constructor(message: string) {
    super(message, 'CONSTRAINT_VIOLATION');
    this.name = 'ConstraintViolationError';
  }
}

class DuplicateRecordError extends DatabaseError {
  constructor(message: string) {
    super(message, 'DUPLICATE_RECORD');
    this.name = 'DuplicateRecordError';
  }
}

function handleDatabaseError(e: Error): never {
  if (e.message.includes('FOREIGN KEY constraint failed')) {
    throw new ConstraintViolationError('Referenced record does not exist');
  } else if (e.message.includes('UNIQUE constraint failed')) {
    throw new DuplicateRecordError('Record already exists');
  } else if (e.message.includes('CHECK constraint failed')) {
    const field = e.message.split('CHECK constraint failed: ')[1];
    throw new ConstraintViolationError(`Invalid value for ${field}`);
  } else {
    throw new DatabaseError(e.message);
  }
}

// Usage
function createVocabulary(vocab: Vocabulary): number {
  try {
    const stmt = db.prepare(`INSERT INTO vocabulary ...`);
    const result = stmt.run(...);
    return result.lastInsertRowid as number;
  } catch (e) {
    handleDatabaseError(e as Error);
  }
}
```

---

## Performance Best Practices

### 1. Use Prepared Statements

**Bad** (SQL injection risk + slow):
```python
# DON'T DO THIS
def get_vocabulary_bad(kanji: str):
    query = f"SELECT * FROM vocabulary WHERE kanji_form = '{kanji}'"
    return db.fetchone(query, [])
```

**Good**:
```python
def get_vocabulary_good(kanji: str):
    query = "SELECT * FROM vocabulary WHERE kanji_form = ?"
    return db.fetchone(query, [kanji])
```

### 2. Batch Operations

**Bad** (N queries):
```typescript
// Slow - 100 individual queries
for (const vocab of vocabularyList) {
  db.prepare('INSERT INTO vocabulary ...').run(vocab);
}
```

**Good** (1 transaction):
```typescript
// Fast - single transaction
const insert = db.prepare('INSERT INTO vocabulary ...');
const insertMany = db.transaction((items) => {
  for (const item of items) insert.run(item);
});
insertMany(vocabularyList);
```

### 3. Use Indexes

```python
# Always query on indexed columns
def get_due_cards_efficient():
    # Uses idx_flashcards_status_next_review
    query = """
        SELECT * FROM flashcards
        WHERE status = 'active'  -- indexed
          AND next_review_at <= datetime('now')  -- indexed
        ORDER BY next_review_at  -- indexed
    """
    return db.fetchall(query, [])
```

### 4. Limit Result Sets

```typescript
// Always use LIMIT for potentially large results
function getVocabulary(limit: number = 50) {
  return db.prepare(`
    SELECT * FROM vocabulary
    ORDER BY created_at DESC
    LIMIT ?
  `).all(limit);
}
```

### 5. Use Transactions for Multiple Writes

```python
# Group related writes in a transaction
with db.get_connection() as conn:
    cursor = conn.cursor()
    # Multiple writes here...
    conn.commit()
```

### 6. Connection Pooling (For Multi-threaded Apps)

```python
from queue import Queue
import threading

class ConnectionPool:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.pool = Queue(maxsize=pool_size)
        for _ in range(pool_size):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.execute('PRAGMA foreign_keys = ON')
            self.pool.put(conn)
    
    @contextmanager
    def get_connection(self):
        conn = self.pool.get()
        try:
            yield conn
        finally:
            self.pool.put(conn)
```

---

## API Examples

### REST API Endpoints (Flask Example)

```python
from flask import Flask, request, jsonify
from typing import Optional

app = Flask(__name__)
db = Database('data/japanese_agent.db')
vocab_repo = VocabularyRepository(db)
flashcard_repo = FlashcardRepository(db)

# GET /api/vocabulary?status=learning&limit=50&offset=0
@app.route('/api/vocabulary', methods=['GET'])
def list_vocabulary():
    status = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    try:
        if status:
            items = vocab_repo.list_by_status(status, limit, offset)
        else:
            items = vocab_repo.list_all(limit, offset)
        
        return jsonify({
            'data': items,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'has_more': len(items) == limit
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET /api/vocabulary/:id
@app.route('/api/vocabulary/<int:vocab_id>', methods=['GET'])
def get_vocabulary(vocab_id):
    try:
        vocab = vocab_repo.get_by_id(vocab_id)
        if not vocab:
            return jsonify({'error': 'Not found'}), 404
        return jsonify({'data': vocab})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST /api/vocabulary
@app.route('/api/vocabulary', methods=['POST'])
def create_vocabulary():
    try:
        data = request.get_json()
        
        # Validation
        required = ['kanji_form', 'hiragana_reading', 'english_meaning']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        vocab_id = vocab_repo.create(data)
        vocab = vocab_repo.get_by_id(vocab_id)
        
        return jsonify({'data': vocab}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PATCH /api/vocabulary/:id
@app.route('/api/vocabulary/<int:vocab_id>', methods=['PATCH'])
def update_vocabulary(vocab_id):
    try:
        data = request.get_json()
        
        # Check exists
        if not vocab_repo.get_by_id(vocab_id):
            return jsonify({'error': 'Not found'}), 404
        
        success = vocab_repo.update(vocab_id, data)
        if not success:
            return jsonify({'error': 'Update failed'}), 500
        
        vocab = vocab_repo.get_by_id(vocab_id)
        return jsonify({'data': vocab})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DELETE /api/vocabulary/:id
@app.route('/api/vocabulary/<int:vocab_id>', methods=['DELETE'])
def delete_vocabulary(vocab_id):
    try:
        success = vocab_repo.delete(vocab_id)
        if not success:
            return jsonify({'error': 'Not found'}), 404
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST /api/flashcards/:id/review
@app.route('/api/flashcards/<int:flashcard_id>/review', methods=['POST'])
def review_flashcard(flashcard_id):
    try:
        data = request.get_json()
        quality = data.get('quality_rating')
        
        if quality is None or not (0 <= quality <= 5):
            return jsonify({'error': 'Invalid quality_rating'}), 400
        
        result = {
            'qualityRating': quality,
            'responseTimeMs': data.get('response_time_ms', 0),
            'userAnswer': data.get('user_answer')
        }
        
        # Process review in transaction
        process_review(flashcard_id, result)
        
        # Get updated flashcard
        flashcard = flashcard_repo.get_by_id(flashcard_id)
        return jsonify({'data': flashcard})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET /api/dashboard/stats
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    try:
        stats = get_dashboard_statistics()
        return jsonify({'data': stats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### GraphQL API (Strawberry Example)

```python
import strawberry
from typing import List, Optional

@strawberry.type
class Vocabulary:
    id: int
    kanji_form: str
    hiragana_reading: str
    english_meaning: str
    study_status: str
    encounter_count: int

@strawberry.type
class Flashcard:
    id: int
    vocabulary: Vocabulary
    card_type: str
    status: str
    next_review_at: str
    review_count: int

@strawberry.type
class Query:
    @strawberry.field
    def vocabulary(self, id: int) -> Optional[Vocabulary]:
        vocab = vocab_repo.get_by_id(id)
        return Vocabulary(**vocab) if vocab else None
    
    @strawberry.field
    def vocabularies(
        self, 
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Vocabulary]:
        if status:
            items = vocab_repo.list_by_status(status, limit, offset)
        else:
            items = vocab_repo.list_all(limit, offset)
        return [Vocabulary(**item) for item in items]
    
    @strawberry.field
    def due_flashcards(self, limit: int = 100) -> List[Flashcard]:
        cards = flashcard_repo.get_due_cards(limit)
        return [Flashcard(**card) for card in cards]

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_vocabulary(
        self,
        kanji_form: str,
        hiragana_reading: str,
        english_meaning: str
    ) -> Vocabulary:
        vocab_id = vocab_repo.create({
            'kanji_form': kanji_form,
            'hiragana_reading': hiragana_reading,
            'english_meaning': english_meaning
        })
        vocab = vocab_repo.get_by_id(vocab_id)
        return Vocabulary(**vocab)
    
    @strawberry.mutation
    def review_flashcard(
        self,
        flashcard_id: int,
        quality_rating: int
    ) -> Flashcard:
        process_review(flashcard_id, {
            'qualityRating': quality_rating,
            'responseTimeMs': 0
        })
        card = flashcard_repo.get_by_id(flashcard_id)
        return Flashcard(**card)

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

---

## Related Documents

- [Database Schema Reference](DATABASE_SCHEMA_REFERENCE.md) - Complete schema details
- [User Workflows](USER_WORKFLOWS.md) - User interaction patterns
- [UI/UX Design Guide](UI_UX_DESIGN_GUIDE.md) - Interface design guidance

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-22  
**Maintained By**: Development Team
