---
description: Analyze Japanese screenshot with OCR and dictionary lookup
allowed-tools: Read, Bash
argument-hint: [image-path]
---

# Analyze Japanese Screenshot

Screenshot path: $ARGUMENTS

## Purpose
Extracts Japanese text from a game screenshot using Claude's multimodal capabilities, provides translations, and saves vocabulary to the database for tracking.

## Process

### Step 1: Validate Image Path
1. Check if $ARGUMENTS is provided
2. If empty, ask user: "Please provide the path to a screenshot image"
3. If provided, verify it exists and is a valid image file (PNG/JPG/JPEG)

### Step 2: Read and Analyze Image
1. Use the Read tool to load the image
2. Visually analyze the image to extract Japanese text
3. Identify all visible Japanese characters (kanji, hiragana, katakana)
4. Provide the extracted text with confidence assessment

### Step 3: Dictionary Lookup and Translation
For each Japanese word/phrase found:
1. Provide the kanji form (if applicable)
2. Provide the hiragana reading (pronunciation)
3. Provide English meaning(s)
4. Identify part of speech
5. Note any cultural or contextual information

### Step 4: Save to Database
Use a simple Python script to save the results to `data/japanese_agent.db`:

```bash
python -c "
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Data from Claude's analysis
image_path = '''$ARGUMENTS'''
extracted_text = '''EXTRACTED_TEXT'''
kanji_form = '''KANJI_FORM'''
hiragana_reading = '''HIRAGANA_READING'''
english_meaning = '''ENGLISH_MEANING'''
part_of_speech = '''PART_OF_SPEECH'''

db_path = Path('D:/source/Cernji-Agents/data/japanese_agent.db')

if not db_path.exists():
    print('⚠️  WARNING: Database not found, skipping save')
    sys.exit(0)

try:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if already processed
    cursor.execute('SELECT id FROM screenshots WHERE file_path = ?', (image_path,))
    existing = cursor.fetchone()

    if existing:
        print(f'⚠️  Screenshot already processed (ID: {existing[\"id\"]})')
    else:
        # Save screenshot
        extracted_text_json = json.dumps([{
            'text': extracted_text,
            'confidence': 0.90,
            'bounds': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
            'character_type': 'mixed'
        }])

        cursor.execute('''
            INSERT INTO screenshots (file_path, processed_at, ocr_confidence, extracted_text_json)
            VALUES (?, ?, ?, ?)
        ''', (image_path, datetime.now().isoformat(), 0.90, extracted_text_json))

        screenshot_id = cursor.lastrowid

        # Save vocabulary
        if kanji_form and hiragana_reading:
            cursor.execute('''
                INSERT INTO vocabulary (
                    kanji_form, hiragana_reading, english_meaning, part_of_speech,
                    first_seen_at, last_seen_at, study_status, encounter_count
                ) VALUES (?, ?, ?, ?, ?, ?, \"new\", 1)
                ON CONFLICT(kanji_form, hiragana_reading) DO UPDATE SET
                    last_seen_at = CURRENT_TIMESTAMP,
                    encounter_count = encounter_count + 1
                RETURNING id
            ''', (
                kanji_form,
                hiragana_reading,
                english_meaning,
                part_of_speech,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            vocab_id = cursor.fetchone()['id']
            print(f'✅ Saved to database!')
            print(f'   Screenshot ID: {screenshot_id}')
            print(f'   Vocabulary ID: {vocab_id}')

    conn.commit()
    conn.close()

except Exception as e:
    print(f'❌ ERROR saving to database: {e}')
"
```

### Step 5: Summarize for User
Present the findings in this format:

```
============================================================
Japanese Screenshot Analysis
============================================================

📸 Image: [filename]

✅ Extracted Text:
   [Japanese text as it appears]

📚 Dictionary Entry:
   Kanji: [kanji_form]
   Reading: [hiragana_reading]
   Meaning: [english_meaning]
   Part of Speech: [part_of_speech]

💡 Context Notes:
   [Any relevant cultural or usage notes]

💾 Database: [Saved successfully / Already exists / Skipped]
============================================================
```

## Output Requirements

1. **Always show the extracted Japanese text prominently**
2. **Provide complete translation with readings**
3. **Confirm database save status**
4. **Note if word was previously encountered** (encounter count)
5. **Include any context about the text** (game UI, dialogue, menu items, etc.)

## Error Handling

- **No image path provided**: Ask user for the path
- **Image not found**: Show error and ask user to verify the path
- **No Japanese text detected**: Inform user and ask if they want to try a different area
- **Multiple words detected**: Process all words and ask which one to save (or save all)
- **Database not found**: Show warning but still provide translation
- **Already processed**: Note the encounter count increment

## Technical Details

- **Execution**: Direct image reading via Claude's multimodal capabilities
- **Database**: `data/japanese_agent.db` (SQLite)
- **OCR**: Claude's visual analysis (no external dependencies)
- **Dictionary**: Claude's built-in Japanese knowledge
- **Deduplication**: Same screenshot won't be processed twice (checked by file path)
- **Vocabulary tracking**: Same word increments `encounter_count`

## Advantages Over manga-ocr

- ✅ No installation required (no 1GB model download)
- ✅ Works immediately with no setup
- ✅ Can understand context and provide better explanations
- ✅ Can handle multiple words in one image
- ✅ Can identify UI elements, dialogue, and other visual context
- ✅ Provides cultural notes and usage examples

## Usage Examples

```bash
/japanese:analyze E:\SteamLibrary\steamapps\common\RetroArch\screenshots\pokemon.png

/japanese:analyze C:\Users\YourName\Desktop\game_screenshot.jpg

/japanese:analyze "D:\My Games\Screenshots\zelda_001.png"
```
