import json
from contextlib import closing
from uuid import uuid4

from src.database import get_connection


def create_conversation(title="New Travel Plan"):
    """Create a conversation and return its ID."""
    conversation_id = str(uuid4())

    with closing(get_connection()) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO conversations (id, title)
                VALUES (?, ?)
                """,
                (conversation_id, title),
            )

    return conversation_id


def list_conversations():
    """Return all conversations, newest activity first."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC, created_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def save_message(conversation_id, role, content):
    """Save a user or assistant message."""
    if role not in {"user", "assistant"}:
        raise ValueError("Role must be 'user' or 'assistant'.")

    if not content.strip():
        raise ValueError("Message content cannot be empty.")

    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO messages (conversation_id, role, content)
                VALUES (?, ?, ?)
                """,
                (conversation_id, role, content.strip()),
            )

            connection.execute(
                """
                UPDATE conversations
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (conversation_id,),
            )

            if cursor.rowcount == 0:
                raise ValueError("Message was not saved.")

            return cursor.lastrowid


def get_messages(conversation_id):
    """Retrieve a conversation's messages in order."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def save_trip_state(conversation_id, trip_state):
    """Create or update collected trip details."""
    trip_json = json.dumps(trip_state)

    with closing(get_connection()) as connection:
        with connection:
            existing = connection.execute(
                """
                SELECT id
                FROM trips
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()

            if existing is None:
                connection.execute(
                    """
                    INSERT INTO trips (
                        conversation_id,
                        trip_state_json
                    )
                    VALUES (?, ?)
                    """,
                    (conversation_id, trip_json),
                )
            else:
                connection.execute(
                    """
                    UPDATE trips
                    SET trip_state_json = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE conversation_id = ?
                    """,
                    (trip_json, conversation_id),
                )

            connection.execute(
                """
                UPDATE conversations
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (conversation_id,),
            )


def get_trip_state(conversation_id):
    """Return collected trip details as a Python dictionary."""
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT trip_state_json
            FROM trips
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ).fetchone()

    if row is None:
        return None

    return json.loads(row["trip_state_json"])


def save_itinerary(conversation_id, itinerary):
    """Save a validated itinerary as JSON."""
    itinerary_json = json.dumps(itinerary)

    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                """
                UPDATE trips
                SET itinerary_json = ?,
                    status = 'completed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE conversation_id = ?
                """,
                (itinerary_json, conversation_id),
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    "Trip record not found. Save trip state first."
                )


def get_itinerary(conversation_id):
    """Retrieve the saved itinerary as a Python dictionary."""
    with closing(get_connection()) as connection:
        row = connection.execute(
            """
            SELECT itinerary_json
            FROM trips
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ).fetchone()

    if row is None or row["itinerary_json"] is None:
        return None

    return json.loads(row["itinerary_json"])

def update_conversation_title(conversation_id, title):
    """Update the title of an existing conversation."""

    with closing(get_connection()) as connection:
        with connection:
            connection.execute(
                """
                UPDATE conversations
                SET title = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, conversation_id),
            )