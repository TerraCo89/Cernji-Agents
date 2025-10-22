# UI/UX Design Guide
**Japanese Learning Application - Database-Driven Interface Design**

Version: 1.0  
Last Updated: 2025-10-22  
Target Audience: UI/UX Designers, Frontend Developers

---

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [Core User Interfaces](#core-user-interfaces)
4. [Component Specifications](#component-specifications)
5. [Data Visualization](#data-visualization)
6. [State Management](#state-management)
7. [Performance Considerations](#performance-considerations)
8. [Accessibility Requirements](#accessibility-requirements)
9. [Mobile Considerations](#mobile-considerations)

---

## Overview

This guide translates database structure into UI/UX requirements. Each database entity maps to specific interface components, and understanding these relationships is crucial for creating an intuitive, performant application.

### Database-to-UI Mapping Philosophy

**Database Entity → UI Component**
- Tables represent data models
- Relationships inform navigation structure
- Constraints define validation rules
- Status fields control UI states
- Timestamps enable activity tracking

---

## Design Principles

### 1. Progressive Disclosure
Show only what users need when they need it. The database has rich metadata—use it wisely.

**Example**: 
- Initial vocabulary display: kanji_form + english_meaning
- On click/expand: readings, JLPT level, example sentences
- Advanced: frequency rank, etymology, kanji breakdown

### 2. Status-Driven UI
Database status fields should drive visual states.

**study_status Values → UI States**:
- `new` → Blue badge, "New" label
- `learning` → Yellow badge, progress indicator
- `reviewing` → Orange badge, review streak
- `mastered` → Green badge, graduation icon
- `suspended` → Gray badge, paused state

### 3. Real-Time Feedback
Leverage `updated_at` timestamps to show freshness.

**Display Patterns**:
- "Last seen 2 hours ago" (from `vocabulary.last_seen_at`)
- "Reviewed today" (from `flashcards.last_reviewed_at`)
- "Added 3 days ago" (from `created_at`)

### 4. Contextual Actions
Present actions based on data state and relationships.

**Vocabulary Word Actions**:
- Has flashcard → "Review Now" button
- No flashcard → "Create Flashcard" button
- In screenshot → "View Context" link
- Has kanji → "Study Kanji" option

---

## Core User Interfaces

### 1. Vocabulary Browser

**Primary Data Source**: `vocabulary` table

**Display Requirements**:

```
┌─────────────────────────────────────────────────────┐
│ Filters: [Status ▼] [JLPT ▼] [Tags ▼] [🔍 Search] │
├─────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────┐   │
│ │ 日本語          [N4] [new]                   │   │
│ │ にほんご nihongo                              │   │
│ │ Japanese language                             │   │
│ │ First seen: 2 days ago | Seen: 3 times       │   │
│ │ [Create Flashcard] [View Examples] [...]     │   │
│ └───────────────────────────────────────────────┘   │
│ ┌───────────────────────────────────────────────┐   │
│ │ 勉強            [N5] [learning] ⭐⭐⭐        │   │
│ │ べんきょう benkyou                            │   │
│ │ Study                                         │   │
│ │ Next review: in 2 hours                       │   │
│ │ [Review Now] [View Examples] [...]           │   │
│ └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Data Fields to Display**:
- **Primary**: `kanji_form`, `english_meaning`
- **Secondary**: `hiragana_reading`, `romaji_reading`
- **Metadata**: `jlpt_level`, `study_status`, `encounter_count`
- **Timestamps**: `first_seen_at`, `last_seen_at`
- **Related**: Flashcard count, example sentence count

**Filter Options**:
- Study Status (from CHECK constraint values)
- JLPT Level (N5-N1 + None)
- Tags (from `vocabulary_tags` join)
- Has Flashcard (JOIN check)
- Has Examples (JOIN check)
- Recently Seen (ORDER BY `last_seen_at`)

**Sort Options**:
- Alphabetical (by `kanji_form`)
- By Study Status
- By Last Seen (newest/oldest)
- By Encounter Count (most/least common)
- By Frequency Rank (common words first)
- By Creation Date

**Actions**:
- Create/View Flashcard
- Add Example Sentence
- View in Context (link to screenshots)
- Edit Word Details
- Change Study Status
- Add Tags

### 2. Flashcard Review Interface

**Primary Data Source**: `flashcards` table with `vocabulary` JOIN

**Query Pattern**:
```sql
SELECT f.*, v.*
FROM flashcards f
JOIN vocabulary v ON f.vocabulary_id = v.id
WHERE f.status = 'active'
  AND f.next_review_at <= datetime('now')
ORDER BY f.next_review_at
LIMIT 1;
```

**Card Display** (Recognition Type):

```
┌─────────────────────────────────────────────────────┐
│                 Review Session                       │
│                                                      │
│           Progress: ████████░░░░ 8/20                │
├─────────────────────────────────────────────────────┤
│                                                      │
│                                                      │
│                     日本語                           │
│                                                      │
│                                                      │
│               [Show Answer]                          │
│                                                      │
│                                                      │
│   [Screenshot Context] [Audio 🔊] [Hint 💡]         │
└─────────────────────────────────────────────────────┘
```

**After Answer Reveal**:

```
┌─────────────────────────────────────────────────────┐
│                     日本語                           │
│                   にほんご                            │
│                                                      │
│                Japanese language                     │
│                                                      │
│   How well did you know this?                       │
│                                                      │
│   [Again]  [Hard]  [Good]  [Easy]                  │
│     1        2       3        4                      │
│                                                      │
│   Next review: 10min | 1day | 4days | 10days        │
└─────────────────────────────────────────────────────┘
```

**Data-Driven Elements**:

**Quality Ratings → UI Labels**:
```javascript
const ratingLabels = {
  0: { label: "Again", color: "red", interval: "10min" },
  1: { label: "Again", color: "red", interval: "10min" },
  2: { label: "Hard", color: "orange", interval: "current * 1.2" },
  3: { label: "Good", color: "green", interval: "current * ease_factor" },
  4: { label: "Easy", color: "blue", interval: "current * ease_factor * 1.3" }
};
```

**Card Type → Display Mode**:
- `recognition`: Show kanji → Answer with reading + meaning
- `recall`: Show meaning → Answer with kanji + reading
- `production`: Show meaning → Type the kanji
- `listening`: Play audio → Answer with meaning/reading

**Status Indicators**:
- Show `consecutive_correct` streak: "🔥 5 day streak"
- Display `review_count`: "Review #23"
- Warn on `lapses`: "⚠️ Forgotten 2 times"
- Show `ease_factor` for advanced users: "Ease: 2.3x"

**Context Display** (if `screenshot_id` exists):
```
┌─────────────────────────────────┐
│ From: [Source Name]             │
│ Context: "...日本語を..." │
│ [View Full Screenshot]          │
└─────────────────────────────────┘
```

### 3. Screenshot Import Interface

**Primary Data Source**: `screenshots` table

**Upload Flow**:

```
┌─────────────────────────────────────────────────────┐
│  📸 Import Screenshot                                │
├─────────────────────────────────────────────────────┤
│                                                      │
│   [Drop image here or click to upload]              │
│                                                      │
│   Source: [Select source ▼] or [+ New Source]       │
│   Language: [Japanese ▼]                            │
│                                                      │
│              [Upload & Process]                      │
└─────────────────────────────────────────────────────┘
```

**Processing State**:

```
┌─────────────────────────────────────────────────────┐
│  Processing Screenshot...                            │
├─────────────────────────────────────────────────────┤
│                                                      │
│   ✓ Uploaded                                        │
│   ⏳ Running OCR...                                 │
│   ⏳ Extracting vocabulary...                       │
│   ⏳ Matching known words...                        │
│                                                      │
│   Confidence: ████████░░ 87%                        │
└─────────────────────────────────────────────────────┘
```

**Results Display**:

```
┌─────────────────────────────────────────────────────┐
│  📸 Screenshot Results                               │
├─────────────────────────────────────────────────────┤
│  [Screenshot Preview]       │  Extracted Text:       │
│                             │                        │
│  ┌───────────────────────┐ │  日本語を勉強します    │
│  │                       │ │                        │
│  │   [Image with OCR     │ │  Found 3 words:       │
│  │    bounding boxes]    │ │  • 日本語 (known)     │
│  │                       │ │  • 勉強 (known)        │
│  │                       │ │  • します (new) [+]    │
│  └───────────────────────┘ │                        │
│                             │                        │
│  Confidence: 87%            │  [Add All New Words]   │
│  Detected: Japanese         │                        │
│  Has Furigana: Yes          │                        │
└─────────────────────────────────────────────────────┘
```

**Data Points**:
- `ocr_confidence` → Progress bar + percentage
- `extracted_text_json` → Bounding boxes overlay
- `language_detected` → Display in UI
- `has_furigana` → Icon indicator
- `checksum` → Duplicate detection ("This screenshot was already imported")

**Actions Per Word**:
- Known words: "View Details" → Jump to vocabulary
- New words: "[+] Add" → Create vocabulary entry
- Uncertain matches: "[?] Review" → Manual confirmation

### 4. Study Dashboard

**Primary Data Sources**: Multiple tables aggregated

**Layout**:

```
┌─────────────────────────────────────────────────────┐
│  📊 Study Dashboard                   [Oct 22, 2025]│
├─────────────────────────────────────────────────────┤
│  Today's Goals                 Progress              │
│  ─────────────────────────────────────────          │
│  Reviews: ████████████░░░░ 30/50                   │
│  New Words: ████████░░░░░░ 5/10                    │
│  Study Time: ██████░░░░░░░░ 25/60 min              │
├─────────────────────────────────────────────────────┤
│  📚 Due for Review                                   │
│  ┌────────────────────────────────────┐            │
│  │  🔴 Overdue: 12 cards              │            │
│  │  🟡 Due today: 18 cards            │            │
│  │  🟢 Due this week: 45 cards        │            │
│  │           [Start Review]            │            │
│  └────────────────────────────────────┘            │
├─────────────────────────────────────────────────────┤
│  📈 Statistics (Last 7 Days)                        │
│  ┌────────────────────────────────────┐            │
│  │  Reviews: 156 | Accuracy: 87%     │            │
│  │  New Words: 23 | Mastered: 5      │            │
│  │  [View Detailed Stats]             │            │
│  └────────────────────────────────────┘            │
└─────────────────────────────────────────────────────┘
```

**Queries for Each Section**:

**Due Cards Count**:
```sql
SELECT 
  SUM(CASE WHEN next_review_at < datetime('now') THEN 1 ELSE 0 END) as overdue,
  SUM(CASE WHEN date(next_review_at) = date('now') THEN 1 ELSE 0 END) as due_today,
  SUM(CASE WHEN next_review_at <= datetime('now', '+7 days') THEN 1 ELSE 0 END) as due_week
FROM flashcards
WHERE status = 'active';
```

**Study Goals Progress**:
```sql
SELECT goal_type, target_value, current_value,
  ROUND(current_value * 100.0 / target_value, 1) as progress_pct
FROM study_goals
WHERE is_active = 1
  AND date('now') BETWEEN start_date AND COALESCE(end_date, date('now'));
```

**Recent Activity**:
```sql
SELECT COUNT(*) as review_count,
  SUM(CASE WHEN correct THEN 1 ELSE 0 END) as correct_count,
  ROUND(AVG(CASE WHEN correct THEN 100.0 ELSE 0 END), 1) as accuracy
FROM review_sessions
WHERE date(reviewed_at) >= date('now', '-7 days');
```

### 5. Source Management

**Primary Data Source**: `sources` table

**List View**:

```
┌─────────────────────────────────────────────────────┐
│  📚 Learning Sources                 [+ Add Source] │
├─────────────────────────────────────────────────────┤
│  Active Sources                                     │
│  ┌────────────────────────────────────────────┐    │
│  │ 📖 Genki Textbook I          [N5] [Active] │    │
│  │    Type: Textbook | Beginner               │    │
│  │    Started: 30 days ago                    │    │
│  │    Last used: 2 hours ago                  │    │
│  │    Screenshots: 45 | Vocab: 234            │    │
│  │    [View] [Edit] [⋮]                      │    │
│  └────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────┐    │
│  │ 📺 Your Name (Anime)         [N3] [Active] │    │
│  │    Type: Anime | Intermediate              │    │
│  │    Started: 15 days ago                    │    │
│  │    Last used: Yesterday                    │    │
│  │    Screenshots: 89 | Vocab: 567            │    │
│  │    [View] [Edit] [⋮]                      │    │
│  └────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────┤
│  Archived Sources (3) [Show ▼]                     │
└─────────────────────────────────────────────────────┘
```

**Detail View**:

```
┌─────────────────────────────────────────────────────┐
│  ← Back to Sources                                   │
├─────────────────────────────────────────────────────┤
│  📖 Genki Textbook I                                │
│                                                      │
│  Type: Textbook              Difficulty: Beginner   │
│  Genre: Educational          JLPT: N5               │
│  Status: Active              Started: Jan 15, 2025  │
│                                                      │
│  Notes: Focus on grammar patterns from chapters 1-5 │
│                                                      │
│  ─────────────────────────────────────────────────  │
│  Statistics                                          │
│  • Total Screenshots: 45                            │
│  • Unique Vocabulary: 234 words                     │
│  • New Words Found: 12                              │
│  • Last Activity: 2 hours ago                       │
│                                                      │
│  [View All Screenshots] [Edit Details] [Archive]    │
└─────────────────────────────────────────────────────┘
```

**Data Aggregations**:
```sql
-- Screenshot count per source
SELECT source_id, COUNT(*) as screenshot_count
FROM screenshots
GROUP BY source_id;

-- Vocabulary count per source (via screenshots)
SELECT s.source_id, COUNT(DISTINCT sv.vocabulary_id) as vocab_count
FROM screenshots s
JOIN screenshot_vocabulary sv ON s.id = sv.screenshot_id
GROUP BY s.source_id;
```

---

## Component Specifications

### 1. Vocabulary Card Component

**Props** (from `vocabulary` table):
```typescript
interface VocabularyCardProps {
  id: number;
  kanjiForm: string;
  hiraganaReading: string;
  romajiReading?: string;
  englishMeaning: string;
  jlptLevel?: 'N5' | 'N4' | 'N3' | 'N2' | 'N1';
  studyStatus: 'new' | 'learning' | 'reviewing' | 'mastered' | 'suspended';
  encounterCount: number;
  firstSeenAt: Date;
  lastSeenAt: Date;
  hasFlashcard: boolean;
  exampleCount: number;
  tags: Tag[];
  onCreateFlashcard?: () => void;
  onViewExamples?: () => void;
  onEdit?: () => void;
}
```

**Styling Variants**:
- Compact (list view): Minimal info
- Expanded (detail view): All metadata
- Card (grid view): Medium detail with image

### 2. Flashcard Component

**Props** (from `flashcards` + `vocabulary`):
```typescript
interface FlashcardProps {
  flashcard: {
    id: number;
    cardType: 'recognition' | 'recall' | 'production' | 'listening';
    status: 'active' | 'suspended' | 'buried' | 'archived';
    easeFactor: number;
    intervalDays: number;
    reviewCount: number;
    consecutiveCorrect: number;
    lapses: number;
  };
  vocabulary: VocabularyCardProps;
  screenshotContext?: {
    id: number;
    contextSnippet: string;
    sourceName: string;
  };
  onAnswer: (quality: 0 | 1 | 2 | 3 | 4 | 5) => void;
  onShowHint?: () => void;
  onPlayAudio?: () => void;
}
```

**States**:
- `question`: Show front of card
- `revealed`: Show answer
- `answering`: User providing answer (production type)
- `grading`: Show quality rating buttons

### 3. Progress Bar Component

**Props**:
```typescript
interface ProgressBarProps {
  current: number;
  target: number;
  label?: string;
  showPercentage?: boolean;
  color?: 'blue' | 'green' | 'yellow' | 'red';
  size?: 'sm' | 'md' | 'lg';
}
```

**Usage with `study_goals`**:
```jsx
<ProgressBar 
  current={goal.current_value}
  target={goal.target_value}
  label={goal.goal_type}
  showPercentage={true}
/>
```

### 4. Tag Component

**Props** (from `tags` table):
```typescript
interface TagProps {
  id: number;
  name: string;
  category?: string;
  color?: string;
  onRemove?: () => void;
  onClick?: () => void;
}
```

**Display Variants**:
- Pill (small, colored badge)
- Chip (removable, with X)
- Button (clickable filter)

### 5. Status Badge Component

**Props**:
```typescript
interface StatusBadgeProps {
  status: 'new' | 'learning' | 'reviewing' | 'mastered' | 'suspended';
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showLabel?: boolean;
}
```

**Color Scheme**:
```typescript
const statusColors = {
  new: { bg: 'blue-100', text: 'blue-800', icon: '🆕' },
  learning: { bg: 'yellow-100', text: 'yellow-800', icon: '📚' },
  reviewing: { bg: 'orange-100', text: 'orange-800', icon: '🔄' },
  mastered: { bg: 'green-100', text: 'green-800', icon: '✅' },
  suspended: { bg: 'gray-100', text: 'gray-800', icon: '⏸️' }
};
```

---

## Data Visualization

### 1. Review Heatmap

**Data Source**: `review_sessions` table

**Query**:
```sql
SELECT 
  date(reviewed_at) as review_date,
  COUNT(*) as review_count,
  ROUND(AVG(CASE WHEN correct THEN 100 ELSE 0 END), 1) as accuracy
FROM review_sessions
WHERE reviewed_at >= date('now', '-90 days')
GROUP BY date(reviewed_at)
ORDER BY review_date;
```

**Visualization**:
```
         Oct 2025
    S  M  T  W  T  F  S
    ┌──┬──┬──┬──┬──┬──┬──┐
    │░░│██│██│▓▓│██│▓▓│░░│
    │░░│██│▓▓│██│██│██│▓▓│
    │██│▓▓│██│▓▓│░░│██│██│
    │██│██│▓▓│▓▓│██│██│░░│
    └──┴──┴──┴──┴──┴──┴──┘
    
Legend: ░░ 0-10  ▓▓ 11-25  ██ 26+ reviews
```

### 2. Progress Chart

**Data Source**: `vocabulary` table + `review_sessions`

**Query**:
```sql
SELECT 
  date(created_at) as date,
  study_status,
  COUNT(*) as count
FROM vocabulary
WHERE created_at >= date('now', '-30 days')
GROUP BY date(created_at), study_status
ORDER BY date;
```

**Visualization**: Stacked area chart showing vocabulary progression through study stages

### 3. Accuracy Over Time

**Data Source**: `review_sessions`

**Query**:
```sql
SELECT 
  date(reviewed_at) as date,
  ROUND(AVG(CASE WHEN correct THEN 100 ELSE 0 END), 1) as accuracy,
  ROUND(AVG(quality_rating), 2) as avg_quality
FROM review_sessions
WHERE reviewed_at >= date('now', '-30 days')
GROUP BY date(reviewed_at)
ORDER BY date;
```

**Visualization**: Line chart with accuracy percentage over time

---

## State Management

### Application State Structure

```typescript
interface AppState {
  // User data
  user: {
    studyGoals: StudyGoal[];
    preferences: UserPreferences;
  };
  
  // Vocabulary state
  vocabulary: {
    items: Vocabulary[];
    filters: VocabularyFilters;
    selectedId?: number;
  };
  
  // Flashcard state
  flashcards: {
    dueCards: Flashcard[];
    currentCard?: Flashcard;
    sessionStats: SessionStats;
  };
  
  // Screenshot state
  screenshots: {
    items: Screenshot[];
    processingQueue: Screenshot[];
  };
  
  // Source state
  sources: {
    active: Source[];
    archived: Source[];
  };
  
  // UI state
  ui: {
    sidebarOpen: boolean;
    currentView: string;
    loading: boolean;
    error?: string;
  };
}
```

### State Updates Based on Database Changes

**After Review**:
```typescript
// Update flashcard
flashcard.last_reviewed_at = now;
flashcard.next_review_at = calculateNextReview(quality, flashcard);
flashcard.review_count += 1;
flashcard.consecutive_correct = quality >= 3 ? flashcard.consecutive_correct + 1 : 0;
flashcard.lapses += quality < 3 ? 1 : 0;

// Update vocabulary
vocabulary.last_seen_at = now;

// Update study goal
studyGoal.current_value += 1;

// Create review session record
createReviewSession({
  flashcard_id: flashcard.id,
  quality_rating: quality,
  correct: quality >= 3,
  ...
});
```

**After Screenshot Import**:
```typescript
// Create screenshot
const screenshot = createScreenshot({
  file_path: uploadedFile.path,
  ocr_confidence: ocrResult.confidence,
  extracted_text_json: JSON.stringify(ocrResult.blocks),
  ...
});

// For each detected word
for (const word of detectedWords) {
  // Check if vocabulary exists
  let vocab = findVocabulary(word.text, word.reading);
  
  if (!vocab) {
    // Create new vocabulary
    vocab = createVocabulary({
      kanji_form: word.text,
      hiragana_reading: word.reading,
      ...
    });
  } else {
    // Update existing
    vocab.encounter_count += 1;
    vocab.last_seen_at = now;
  }
  
  // Link to screenshot
  createScreenshotVocabulary({
    screenshot_id: screenshot.id,
    vocabulary_id: vocab.id,
    position_in_text: word.position,
    context_snippet: word.context,
  });
}
```

---

## Performance Considerations

### Pagination

**Vocabulary List**:
```typescript
const PAGE_SIZE = 50;

function loadVocabularyPage(page: number, filters: Filters) {
  return query(`
    SELECT * FROM vocabulary
    WHERE study_status IN (?)
    ORDER BY last_seen_at DESC
    LIMIT ? OFFSET ?
  `, [filters.statuses, PAGE_SIZE, page * PAGE_SIZE]);
}
```

**Infinite Scroll Implementation**:
- Load initial 50 items
- Load next 50 when scrolled to bottom
- Show loading indicator
- Cache loaded pages

### Lazy Loading

**Example Sentences**:
- Don't load until vocabulary card is expanded
- Load on-demand via API call
- Cache for session

**Screenshot Images**:
- Use thumbnail versions in lists
- Load full resolution on click
- Implement image lazy loading (Intersection Observer)

### Caching Strategy

**Client-Side Cache**:
- Due flashcards: Refresh every 5 minutes
- Vocabulary list: Refresh on navigation
- Study stats: Refresh daily or on review completion
- Sources: Refresh on edit only

**Database Indexes Usage**:
- Always use WHERE clauses on indexed columns
- Order by indexed columns when possible
- Use composite indexes for complex queries

---

## Accessibility Requirements

### Screen Reader Support

**Vocabulary Card**:
```html
<article aria-label="Vocabulary: 日本語 (nihongo), means Japanese language">
  <h3>日本語</h3>
  <p class="reading" aria-label="Reading: nihongo">にほんご</p>
  <p class="meaning">Japanese language</p>
  <div class="metadata">
    <span aria-label="JLPT Level N4">N4</span>
    <span aria-label="Status: currently learning">Learning</span>
  </div>
</article>
```

**Flashcard**:
```html
<section aria-live="polite" aria-label="Flashcard review session">
  <div role="status" aria-label="Progress: 8 of 20 cards completed">
    8/20
  </div>
  <div class="card" role="article" aria-label="Question: 日本語">
    日本語
  </div>
  <button aria-label="Reveal answer">Show Answer</button>
</section>
```

### Keyboard Navigation

**Must Support**:
- Tab through all interactive elements
- Enter/Space to activate buttons
- Arrow keys for navigation in lists
- Escape to close modals/panels
- Shortcuts for common actions (customizable)

**Recommended Shortcuts**:
- `1-4`: Quality rating buttons during review
- `Space`: Reveal answer
- `n`: Next card
- `r`: Start review session
- `/`: Focus search

### Color Contrast

**Status Colors**:
- All status badges must meet WCAG AA (4.5:1)
- Use patterns/icons in addition to color
- Support high contrast mode

**Text Readability**:
- Japanese text: Minimum 16px for kanji
- Furigana: 10px minimum
- English text: 14px minimum
- Line height: 1.5 for readability

---

## Mobile Considerations

### Touch Targets

**Minimum Sizes**:
- Buttons: 44x44px (iOS), 48x48px (Android)
- Interactive cards: Full width, min 60px height
- Swipe zones: Full card width

### Gestures

**Flashcard Review**:
- Swipe right: Easy (quality 4)
- Swipe up: Good (quality 3)
- Swipe down: Hard (quality 2)
- Swipe left: Again (quality 1)
- Tap: Reveal answer

**Vocabulary List**:
- Pull down: Refresh
- Long press: Context menu (Edit, Delete, etc.)
- Swipe left: Quick actions (Create Flashcard, etc.)

### Responsive Breakpoints

```css
/* Mobile first */
.vocabulary-grid {
  display: flex;
  flex-direction: column;
}

/* Tablet (768px+) */
@media (min-width: 768px) {
  .vocabulary-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop (1024px+) */
@media (min-width: 1024px) {
  .vocabulary-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

### Offline Considerations

**Must Work Offline**:
- Review due flashcards
- View vocabulary list
- Browse existing content

**Requires Online**:
- Import screenshots (OCR processing)
- Add new vocabulary
- Sync with cloud
- Load audio files

**Queue System**:
- Queue reviews completed offline
- Sync when online
- Show pending sync indicator

---

## Design Tokens

### Colors

```typescript
const colors = {
  // Status colors
  status: {
    new: '#3B82F6',        // blue-500
    learning: '#EAB308',   // yellow-500
    reviewing: '#F97316',  // orange-500
    mastered: '#22C55E',   // green-500
    suspended: '#6B7280',  // gray-500
  },
  
  // JLPT level colors
  jlpt: {
    N5: '#10B981',  // green-500 (easiest)
    N4: '#3B82F6',  // blue-500
    N3: '#8B5CF6',  // violet-500
    N2: '#F59E0B',  // amber-500
    N1: '#EF4444',  // red-500 (hardest)
  },
  
  // UI colors
  ui: {
    primary: '#3B82F6',
    secondary: '#6B7280',
    success: '#22C55E',
    warning: '#F59E0B',
    error: '#EF4444',
    background: '#FFFFFF',
    surface: '#F9FAFB',
    border: '#E5E7EB',
  }
};
```

### Typography

```typescript
const typography = {
  japanese: {
    // Kanji display
    primary: {
      fontFamily: "'Noto Sans JP', sans-serif",
      fontSize: '24px',
      fontWeight: 500,
      lineHeight: 1.4,
    },
    // Furigana/reading
    secondary: {
      fontFamily: "'Noto Sans JP', sans-serif",
      fontSize: '12px',
      fontWeight: 400,
      lineHeight: 1.5,
    },
  },
  english: {
    body: {
      fontFamily: "'Inter', sans-serif",
      fontSize: '14px',
      fontWeight: 400,
      lineHeight: 1.5,
    },
    heading: {
      fontFamily: "'Inter', sans-serif",
      fontSize: '18px',
      fontWeight: 600,
      lineHeight: 1.3,
    },
  },
};
```

### Spacing

```typescript
const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
};
```

---

## Testing Considerations

### Visual States to Test

**Vocabulary Card**:
- Empty state (no vocabulary)
- With all fields populated
- Without optional fields (romaji, notes, etc.)
- Each study status
- Each JLPT level
- Long text overflow
- Multiple tags

**Flashcard**:
- Each card type
- With/without screenshot context
- With/without audio
- Each quality rating state
- High streak count display
- High lapse count warning

**Lists**:
- Empty state
- Loading state
- Error state
- Single item
- Many items (pagination)
- Filtered results (0 matches)

### Data Edge Cases

**Vocabulary**:
- Hiragana-only words (no kanji)
- Words with multiple kanji
- Very long meanings
- No JLPT level assigned
- Never encountered before

**Flashcards**:
- Brand new card (0 reviews)
- Mastered card (long interval)
- Frequently failed card (high lapses)
- Edge ease factors (1.3, 5.0+)

**Screenshots**:
- Low confidence OCR (<50%)
- No text detected
- Non-Japanese text
- Very long text (>1000 chars)

---

## Next Steps

After implementing the UI based on this guide:

1. **User Testing**: Test with real learners
2. **Analytics**: Track feature usage
3. **Performance**: Monitor query times
4. **Accessibility**: Run WCAG audits
5. **Iteration**: Refine based on feedback

**Related Documents**:
- [User Workflows](USER_WORKFLOWS.md) - Common user journeys
- [API Integration Guide](API_INTEGRATION_GUIDE.md) - Backend integration
- [Database Schema Reference](DATABASE_SCHEMA_REFERENCE.md) - Technical details

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-22  
**Next Review**: After first implementation sprint
