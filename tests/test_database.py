
import pytest

from src import database, repository


@pytest.fixture
def test_db():
    """Initialize the PostgreSQL test database."""
    database.create_tables()

    yield

    # These tests create only conversations.
    # Remove their records separately using their IDs
    # rather than deleting all database data.


def test_conversation_and_messages(test_db):
    conversation_id = repository.create_conversation("Rome Trip")

    try:
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
    finally:
        delete_test_conversation(conversation_id)


def delete_test_conversation(conversation_id):
    """Delete only the conversation created by a test."""
    with database.get_connection() as connection:
        connection.execute(
            "DELETE FROM conversations WHERE id = %s",
            (conversation_id,),
        )


def test_trip_state_persists(test_db):
    conversation_id = repository.create_conversation("Rome Trip")

    try:
        state = {
            "destination": "Rome",
            "duration_days": 3,
            "interests": ["food", "history"],
        }

        repository.save_trip_state(conversation_id, state)

        assert repository.get_trip_state(conversation_id) == state
    finally:
        delete_test_conversation(conversation_id)


def test_missing_trip_returns_none(test_db):
    conversation_id = repository.create_conversation()

    try:
        assert repository.get_trip_state(conversation_id) is None
    finally:
        delete_test_conversation(conversation_id)


def test_invalid_message_role_is_rejected(test_db):
    conversation_id = repository.create_conversation()

    try:
        with pytest.raises(ValueError):
            repository.save_message(
                conversation_id,
                "system",
                "Unexpected role",
            )
    finally:
        delete_test_conversation(conversation_id)
