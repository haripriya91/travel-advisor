
import json
from uuid import uuid4

from src.database import get_connection


def create_conversation(title="New Travel Plan"):
    """Create a conversation and return its ID."""
    conversation_id = str(uuid4())

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO conversations (id, title)
            VALUES (%s, %s)
            """,
            (conversation_id, title),
        )

    return conversation_id


def list_conversations():
    """Return conversations, newest activity first."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC, created_at DESC
            """
        ).fetchall()

    return rows


def save_message(conversation_id, role, content):
    """Save a user or assistant message."""
    if role not in {"user", "assistant"}:
        raise ValueError("Role must be 'user' or 'assistant'.")

    if not isinstance(content, str) or not content.strip():
        raise ValueError("Message content cannot be empty.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (conversation_id, role, content.strip()),
        )

        message_id = cursor.fetchone()["id"]

        connection.execute(
            """
            UPDATE conversations
            SET updated_at = NOW()
            WHERE id = %s
            """,
            (conversation_id,),
        )

    return message_id


def get_messages(conversation_id):
    """Retrieve a conversation's messages in order."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, conversation_id, role, content, created_at
            FROM messages
            WHERE conversation_id = %s
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()

    return rows


def save_trip_state(conversation_id, trip_state):
    """Create or update collected trip details."""
    trip_json = json.dumps(trip_state)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO trips (conversation_id, trip_state_json)
            VALUES (%s, %s)
            ON CONFLICT (conversation_id)
            DO UPDATE SET
                trip_state_json = EXCLUDED.trip_state_json,
                updated_at = NOW()
            """,
            (conversation_id, trip_json),
        )

        connection.execute(
            """
            UPDATE conversations
            SET updated_at = NOW()
            WHERE id = %s
            """,
            (conversation_id,),
        )


def get_trip_state(conversation_id):
    """Return collected trip details as a dictionary."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT trip_state_json
            FROM trips
            WHERE conversation_id = %s
            """,
            (conversation_id,),
        ).fetchone()

    if row is None:
        return None

    return json.loads(row["trip_state_json"])


def save_itinerary(conversation_id, itinerary):
    """Save a validated itinerary as JSON."""
    itinerary_json = json.dumps(itinerary)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE trips
            SET itinerary_json = %s,
                status = 'completed',
                updated_at = NOW()
            WHERE conversation_id = %s
            """,
            (itinerary_json, conversation_id),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Trip record not found. Save trip state first."
            )


def get_itinerary(conversation_id):
    """Retrieve the saved itinerary as a dictionary."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT itinerary_json
            FROM trips
            WHERE conversation_id = %s
            """,
            (conversation_id,),
        ).fetchone()

    if row is None or row["itinerary_json"] is None:
        return None

    return json.loads(row["itinerary_json"])


def update_conversation_title(conversation_id, title):
    """Update the title of an existing conversation."""
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE conversations
            SET title = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (title, conversation_id),
        )
