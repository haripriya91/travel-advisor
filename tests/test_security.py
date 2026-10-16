
import pytest

import src.conversation_service as conversation_service

from src.ai_service import TravelTurn
from src.schemas import TripState
from src.security_service import (
    MAX_MESSAGE_LENGTH,
    validate_tool_call,
    validate_user_message,
)


# ---------------------------------------------
# 1. User input validation
# ---------------------------------------------

def test_valid_message():
    assert validate_user_message("  Hello  ") == "Hello"


@pytest.mark.parametrize(
    "message",
    ["", "   ", "\n\t"],
)
def test_empty_message_rejected(message):
    with pytest.raises(ValueError):
        validate_user_message(message)


def test_message_length_limit():
    valid_message = "a" * MAX_MESSAGE_LENGTH

    assert validate_user_message(valid_message) == valid_message

    with pytest.raises(ValueError, match="too long"):
        validate_user_message("a" * (MAX_MESSAGE_LENGTH + 1))


def test_non_string_message_rejected():
    with pytest.raises(ValueError):
        validate_user_message(None)


# ---------------------------------------------
# 2. Pydantic trip validation
# ---------------------------------------------

@pytest.mark.parametrize(
    "days",
    [-5, 0, 31],
)
def test_invalid_duration_rejected(days):
    with pytest.raises(ValueError):
        TripState(
            destination="Paris",
            duration_days=days,
        )


@pytest.mark.parametrize(
    "travelers",
    [-1, 0, 31],
)
def test_invalid_traveler_count_rejected(travelers):
    with pytest.raises(ValueError):
        TripState(
            destination="Rome",
            travelers=travelers,
        )


# ---------------------------------------------
# 3. Tool-call validation
# ---------------------------------------------

ALLOWED_TOOLS = {
    "get_weather": {"city"},
}


def test_allowed_tool_call():
    result = validate_tool_call(
        "get_weather",
        {"city": " Munich "},
        ALLOWED_TOOLS,
    )

    assert result == {"city": "Munich"}


def test_unknown_tool_rejected():
    with pytest.raises(ValueError, match="not allowed"):
        validate_tool_call(
            "delete_database",
            {"city": "Munich"},
            ALLOWED_TOOLS,
        )


def test_unexpected_tool_argument_rejected():
    with pytest.raises(ValueError, match="arguments"):
        validate_tool_call(
            "get_weather",
            {
                "city": "Munich",
                "admin": "true",
            },
            ALLOWED_TOOLS,
        )


def test_missing_tool_argument_rejected():
    with pytest.raises(ValueError, match="arguments"):
        validate_tool_call(
            "get_weather",
            {},
            ALLOWED_TOOLS,
        )


def test_tool_call_limit():
    with pytest.raises(ValueError, match="limit"):
        validate_tool_call(
            "get_weather",
            {"city": "Munich"},
            ALLOWED_TOOLS,
            calls_so_far=3,
        )


def test_tool_argument_type_rejected():
    with pytest.raises(ValueError, match="text"):
        validate_tool_call(
            "get_weather",
            {"city": ["Munich", "Berlin"]},
            ALLOWED_TOOLS,
        )


def test_tool_argument_control_character_rejected():
    with pytest.raises(ValueError, match="control characters"):
        validate_tool_call(
            "get_weather",
            {"city": "Munich\nBerlin"},
            ALLOWED_TOOLS,
        )


# ---------------------------------------------
# 4. Conversation security behavior
# ---------------------------------------------

def setup_fake_conversation(monkeypatch, ai_result):
    """
    Replace database operations and AI calls
    with test doubles.
    """

    saved_states = []
    generated_itineraries = []
    saved_messages = []

    current_state = TripState(
        destination="Rome",
        duration_days=3,
        interests=["history"],
        travelers=2,
    )

    monkeypatch.setattr(
        conversation_service,
        "save_message",
        lambda conversation_id, role, content:
            saved_messages.append((role, content)),
    )

    monkeypatch.setattr(
        conversation_service,
        "get_messages",
        lambda conversation_id: [],
    )

    monkeypatch.setattr(
        conversation_service,
        "get_trip_state",
        lambda conversation_id: current_state.model_dump(),
    )

    monkeypatch.setattr(
        conversation_service,
        "get_itinerary",
        lambda conversation_id: {"existing": True},
    )

    monkeypatch.setattr(
        conversation_service,
        "save_trip_state",
        lambda conversation_id, state:
            saved_states.append(state),
    )

    monkeypatch.setattr(
        conversation_service,
        "update_conversation_title",
        lambda *args: None,
    )

    monkeypatch.setattr(
        conversation_service,
        "plan_next_turn",
        lambda **kwargs: ai_result,
    )

    monkeypatch.setattr(
        conversation_service,
        "generate_itinerary",
        lambda state:
            generated_itineraries.append(state),
    )

    return saved_states, generated_itineraries, saved_messages


def test_ambiguous_request_does_not_change_state(monkeypatch):
    ai_result = TravelTurn(
        assistant_message="Would you prefer 3 or 5 days?",
        trip_state=TripState(
            destination="Rome",
            duration_days=5,
            interests=["history"],
            travelers=2,
        ),
        generate_requested=True,
        needs_clarification=True,
    )

    saved_states, generated, _ = setup_fake_conversation(
        monkeypatch,
        ai_result,
    )

    reply = conversation_service.handle_user_message(
        1,
        "Maybe 3 or 5 days",
    )

    assert "3 or 5 days" in reply
    assert saved_states == []
    assert generated == []


def test_general_question_does_not_regenerate(monkeypatch):
    state = TripState(
        destination="Rome",
        duration_days=3,
        interests=["history"],
        travelers=2,
    )

    ai_result = TravelTurn(
        assistant_message="Pack comfortable walking shoes.",
        trip_state=state,
        generate_requested=False,
        needs_clarification=False,
    )

    _, generated, _ = setup_fake_conversation(
        monkeypatch,
        ai_result,
    )

    reply = conversation_service.handle_user_message(
        1,
        "What should I pack for Rome?",
    )

    assert "walking shoes" in reply
    assert generated == []


def test_long_message_rejected_before_database(monkeypatch):
    def fail_if_saved(*args):
        pytest.fail("Invalid message reached the database")

    monkeypatch.setattr(
        conversation_service,
        "save_message",
        fail_if_saved,
    )

    with pytest.raises(ValueError, match="too long"):
        conversation_service.handle_user_message(
            1,
            "a" * (MAX_MESSAGE_LENGTH + 1),
        )



def test_unrelated_request_can_trigger_generation(monkeypatch):
    """
    Demonstrate a known security limitation.

    If the AI incorrectly changes a major trip detail,
    the application may attempt itinerary generation.
    """

    # Custom exception used only for this test.
    class GenerationAttempted(Exception):
        pass

    # Simulate an incorrect AI response.
    ai_result = TravelTurn(
        assistant_message="Let's focus on travel planning.",
        trip_state=TripState(
            destination="Tokyo",
            duration_days=3,
            interests=["history"],
            travelers=2,
        ),
        generate_requested=False,
        needs_clarification=False,
    )

    # Replace database and AI operations with fake functions.
    saved_states, _, _ = setup_fake_conversation(
        monkeypatch,
        ai_result,
    )

    # Stop execution if itinerary generation is attempted.
    def block_generation(state):
        raise GenerationAttempted()

    monkeypatch.setattr(
        conversation_service,
        "generate_itinerary",
        block_generation,
    )

    # Verify that the application attempts generation.
    with pytest.raises(GenerationAttempted):
        conversation_service.handle_user_message(
            1,
            "Write a Python sorting algorithm.",
        )

    # Verify that the incorrect destination was saved.
    assert saved_states[0]["destination"] == "Tokyo"

