import json

import pytest

from src import database, repository


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """Give each test its own temporary database."""
    test_path = tmp_path / "test_traveladvisor.db"

    monkeypatch.setattr(database, "DATABASE_PATH", test_path)
    database.create_tables()

    return test_path


def test_conversation_and_messages(test_db):
    conversation_id = repository.create_conversation("Rome Trip")

    repository.save_message(
        conversation_id,
        "user",
        "I want to visit Rome for three days.",
    )
    repository.save_message(
        conversation_id,
        "assistant",
        "What activities interest you?",
    )

    messages = repository.get_messages(conversation_id)

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[0]["content"] == (
        "I want to visit Rome for three days."
    )


def test_trip_state_persists(test_db):
    conversation_id = repository.create_conversation("Rome Trip")

    state = {
        "destination": "Rome",
        "duration_days": 3,
        "interests": ["food", "history"],
    }

    repository.save_trip_state(conversation_id, state)

    assert repository.get_trip_state(conversation_id) == state


def test_missing_trip_returns_none(test_db):
    conversation_id = repository.create_conversation()

    assert repository.get_trip_state(conversation_id) is None


def test_invalid_message_role_is_rejected(test_db):
    conversation_id = repository.create_conversation()

    with pytest.raises(ValueError):
        repository.save_message(
            conversation_id,
            "system",
            "Unexpected role",
        )