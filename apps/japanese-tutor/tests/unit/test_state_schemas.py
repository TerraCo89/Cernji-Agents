"""Unit tests for state schemas and reducers."""

import pytest
from japanese_agent.state.schemas import (
    append_unique_vocabulary,
    append_unique_flashcards,
    replace_with_latest,
    create_initial_state,
    update_state,
    validate_screenshot_exists,
    validate_has_vocabulary,
)


class TestReducers:
    """Test custom state reducers."""

    def test_append_unique_vocabulary_empty_existing(self):
        """Test appending to empty vocabulary list."""
        existing = []
        new = [{"id": 1, "word": "test"}]
        result = append_unique_vocabulary(existing, new)
        assert len(result) == 1
        assert result[0]["word"] == "test"

    def test_append_unique_vocabulary_deduplication_by_id(self):
        """Test deduplication by id field."""
        existing = [{"id": 1, "word": "test1"}]
        new = [{"id": 1, "word": "test2"}]  # Same ID, different word
        result = append_unique_vocabulary(existing, new)
        assert len(result) == 1  # Should not add duplicate

    def test_append_unique_vocabulary_deduplication_by_word(self):
        """Test deduplication by word field."""
        existing = [{"word": "ポケモン", "meaning": "Pokemon"}]
        new = [{"word": "ポケモン", "meaning": "Pocket Monsters"}]  # Same word
        result = append_unique_vocabulary(existing, new)
        assert len(result) == 1  # Should not add duplicate

    def test_append_unique_vocabulary_adds_new_entries(self):
        """Test adding genuinely new entries."""
        existing = [{"id": 1, "word": "test1"}]
        new = [{"id": 2, "word": "test2"}]
        result = append_unique_vocabulary(existing, new)
        assert len(result) == 2

    def test_replace_with_latest(self):
        """Test replace_with_latest reducer."""
        existing = {"old": "value"}
        new = {"new": "value"}
        result = replace_with_latest(existing, new)
        assert result == new

    def test_replace_with_latest_none_handling(self):
        """Test that None new value preserves existing."""
        existing = {"old": "value"}
        new = None
        result = replace_with_latest(existing, new)
        assert result == existing


class TestStateInitialization:
    """Test state initialization helpers."""

    def test_create_initial_state_default_user(self):
        """Test creating initial state with default user."""
        state = create_initial_state()
        assert state["user_id"] == "default"
        assert state["messages"] == []
        assert state["vocabulary"] == []
        assert state["total_vocabulary"] == 0

    def test_create_initial_state_custom_user(self):
        """Test creating initial state with custom user."""
        state = create_initial_state(user_id="test-user")
        assert state["user_id"] == "test-user"

    def test_update_state(self):
        """Test update_state helper."""
        current_state = create_initial_state()
        updates = update_state(
            current_state,
            total_vocabulary=5,
            known_vocabulary=2
        )
        assert updates == {
            "total_vocabulary": 5,
            "known_vocabulary": 2,
        }


class TestValidators:
    """Test state validation helpers."""

    def test_validate_screenshot_exists_true(self):
        """Test validator when screenshot exists."""
        state = create_initial_state()
        state["current_screenshot"] = {"id": 1}
        assert validate_screenshot_exists(state) is True

    def test_validate_screenshot_exists_false(self):
        """Test validator when screenshot is None."""
        state = create_initial_state()
        assert validate_screenshot_exists(state) is False

    def test_validate_has_vocabulary_true(self):
        """Test validator when vocabulary exists."""
        state = create_initial_state()
        state["vocabulary"] = [{"id": 1, "word": "test"}]
        assert validate_has_vocabulary(state) is True

    def test_validate_has_vocabulary_false(self):
        """Test validator when vocabulary is empty."""
        state = create_initial_state()
        assert validate_has_vocabulary(state) is False
