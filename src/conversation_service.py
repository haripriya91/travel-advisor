
from src.ai_service import (
    generate_itinerary,
    plan_next_turn,
)

from src.repository import (
    create_conversation,
    get_itinerary,
    get_messages,
    get_trip_state,
    save_itinerary,
    save_message,
    save_trip_state,
    update_conversation_title,
)

from src.schemas import TripState, TravelItinerary


HISTORY_LIMIT = 20


def start_conversation():
    """Create a conversation and save the initial greeting."""

    conversation_id = create_conversation()

    save_message(
        conversation_id,
        "assistant",
        (
            "Hi! 👋 I'm TravelAdvisor AI, your travel planning assistant. "
            "Where would you like to travel?"
        ),
    )

    return conversation_id


def has_required_details(state: TripState) -> bool:
    """Check whether enough information exists to generate an itinerary."""

    return (
        bool(state.destination and state.destination.strip())
        and state.duration_days is not None
        and state.duration_days > 0
        and any(
            interest.strip()
            for interest in state.interests
        )
        and state.travelers is not None
        and state.travelers > 0
    )


def handle_user_message(conversation_id, user_text):
    """Process a message and generate an itinerary when appropriate."""

    user_text = user_text.strip()

    if not user_text:
        raise ValueError("Please enter a message.")

    # Step 1: Save the user's message.
    save_message(
        conversation_id,
        "user",
        user_text,
    )

    # Step 2: Retrieve conversation history from SQLite.
    history = get_messages(conversation_id)

    # Step 3: Load previously collected trip information.
    saved_state = get_trip_state(conversation_id)

    current_state = TripState.model_validate(
        saved_state or {}
    )

    # Step 4: Check whether an itinerary already exists.
    existing_itinerary = get_itinerary(conversation_id)

    has_itinerary = existing_itinerary is not None

    # Step 5: Send only recent messages to OpenAI.
    recent_messages = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in history[-HISTORY_LIMIT:]
    ]

    # Step 6: Ask OpenAI to update the trip information.
    result = plan_next_turn(
        messages=recent_messages,
        current_state=current_state.model_dump(),
        itinerary=existing_itinerary,
    )

    state = result.trip_state 

    # Step 7: Save updated trip information.
    # Preserve confirmed details when clarification is needed.

    if result.needs_clarification:
        state = current_state
    else:
        save_trip_state(
            conversation_id,
            state.model_dump(),
        )

    # Step 8: Update the conversation title.
    if state.destination and state.destination.strip():
        update_conversation_title(
            conversation_id,
            f"{state.destination.strip()} Trip",
        )

    # Step 9: Ask follow-up questions when details are missing.
    if result.needs_clarification or not has_required_details(state):

        reply = result.assistant_message

        save_message(
            conversation_id,
            "assistant",
            reply,
        )

        return reply

    # Step 10: Decide whether to generate an itinerary.
    #
    # Generate when:
    # 1. OpenAI requests itinerary generation.
    # 2. An existing trip's destination, duration,
    #    or traveler count changes.
    #
    # Do not generate when clarification is needed.

    major_details_changed = (
        current_state.destination != state.destination
        or current_state.duration_days != state.duration_days
        or current_state.travelers != state.travelers
    )

    should_generate = (
        not result.needs_clarification
        and (
            result.generate_requested
            or (
                has_itinerary
                and major_details_changed
            )
        )
    )

    if not should_generate:
        reply = result.assistant_message

        save_message(
            conversation_id,
            "assistant",
            reply,
        )

        return reply
    
    # Step 11: Generate the itinerary.
    itinerary = generate_itinerary(state)

    # Step 12: Validate the itinerary with Pydantic.
    validated_itinerary = TravelItinerary.model_validate(
        itinerary.model_dump()
    )

    # Check duration.
    if validated_itinerary.duration_days != state.duration_days:
        raise ValueError(
            "Generated itinerary has an incorrect duration."
        )

    # Normalize destination to the requested destination.
    validated_itinerary.destination = state.destination.strip()

    # Step 13: Save the itinerary to SQLite.
    save_itinerary(
        conversation_id,
        validated_itinerary.model_dump(),
    )

    # Step 14: Prepare assistant reply.
    reply = (
        f"I've prepared your {state.duration_days}-day "
        f"trip to {state.destination} "
        f"for {state.travelers} traveler(s)! "
        "Your itinerary is ready below."
    )

    save_message(
        conversation_id,
        "assistant",
        reply,
    )

    return reply
