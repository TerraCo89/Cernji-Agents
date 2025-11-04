#!/usr/bin/env python3
"""Fix test imports to access .func attribute of LangChain tools."""

import re

def fix_test_file(filepath):
    """Update test file to use .func for tool calls."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace tool calls with .func calls
    patterns = [
        (r'await search_vocabulary\(', r'await search_vocabulary.func('),
        (r'await list_vocabulary_by_status\(', r'await list_vocabulary_by_status.func('),
        (r'await update_vocabulary_status\(', r'await update_vocabulary_status.func('),
        (r'await get_vocabulary_statistics\(', r'await get_vocabulary_statistics.func('),
        (r'await get_due_flashcards\(', r'await get_due_flashcards.func('),
        (r'await create_flashcard\(', r'await create_flashcard.func('),
        (r'await record_flashcard_review\(', r'await record_flashcard_review.func('),
        (r'await get_review_statistics\(', r'await get_review_statistics.func('),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Fixed: {filepath}")

# Fix all test files
test_files = [
    'tests/integration/test_vocabulary_database.py',
    'tests/integration/test_flashcard_database.py',
    'tests/integration/test_full_workflow.py',
]

for test_file in test_files:
    try:
        fix_test_file(test_file)
    except Exception as e:
        print(f"Error fixing {test_file}: {e}")

print("\\nAll test files updated!")
