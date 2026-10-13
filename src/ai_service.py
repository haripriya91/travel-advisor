import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from src.schemas import TripState, TravelItinerary


load_dotenv()


class TravelTurn(BaseModel):
    """Structured result for one conversation turn."""

    assistant_message: str
    trip_state: TripState
    generate_requested: bool


def get_client():
    """Create an OpenAI client using the API key."""

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing. Add it to your .env file."
        )

    return OpenAI(
        api_key=api_key,
        timeout=45.0,
        max_retries=1,
    )


def get_model():
    """Read the configured OpenAI model."""

    return os.getenv("OPENAI_MODEL", "gpt-6-luna")


def log_usage(response, task):
    """Print token usage for development."""

    if response.usage:
        print(f"\nTask: {task}")
        print("Input tokens:", response.usage.input_tokens)
        print("Output tokens:", response.usage.output_tokens)


def plan_next_turn(messages, current_state, has_itinerary=False):
    """
    Extract trip preferences and determine the next action.

    This function does NOT generate an itinerary.
    """

    client = get_client()

    instructions = """
    You are TravelAdvisor AI, a friendly travel planning assistant.

    Your job is to understand the user's message and update
    their trip preferences.

    REQUIRED TRIP DETAILS:
    1. Destination
    2. Duration in days
    3. At least one travel interest
    4. Number of travelers

    OPTIONAL TRIP DETAILS:
    - Travel group composition (solo, couple, friends, family)
    - Budget
    - Travel preferences
    - Constraints

    CONVERSATION RULES:
    - Preserve previously collected trip information.
    - Update details when the user explicitly changes them.
    - Never invent preferences, constraints or traveler counts.
    - Do not assume the user is traveling with children.
    - Ask short, natural follow-up questions.
    - Ask only for missing required details.
    - If the number of travelers is unknown, ask whether the
      user is traveling solo or with others.
    - You may ask about budget together with traveler count,
      but make it clear that budget is optional.
    - Do not repeatedly ask about optional information.
    - Do not generate an itinerary inside this function.
    - If the user asks a general travel question, answer briefly.

    WHEN REQUIRED DETAILS ARE MISSING:
    - Set generate_requested=false.
    - Ask a useful follow-up question.

    WHEN REQUIRED DETAILS ARE COMPLETE:
    - Set generate_requested=true if this is a new trip
      and no itinerary exists.
    - Also set generate_requested=true when the user explicitly
      requests an updated itinerary.
    - Otherwise set generate_requested=false.

    EXISTING ITINERARY RULES:
    - If an itinerary already exists and the user asks a
      general question, answer the question directly.
    - Do not regenerate the entire itinerary for every message.
    - If the user requests changes to an existing itinerary,
      update the trip preferences and request regeneration.

    GENERATION DECISION:
    - Generate only when required details are complete.
    - If the user explicitly asks for an itinerary but traveler
      count is missing, ask for traveler count first.
    - Do not ask unnecessary questions after all required
      details are collected.

    The application will independently verify the required
    information before generating an itinerary.

    Return a structured TravelTurn response.
    """

    response = client.responses.parse(
        model=get_model(),
        instructions=instructions,
        input=[
            {
                "role": "user",
                "content": (
                    "Previously collected trip state:\n"
                    + json.dumps(current_state)
                    + "\n\nExisting itinerary: "
                    + str(has_itinerary)
                ),
            },
            *messages,
        ],
        text_format=TravelTurn,
    )

    result = response.output_parsed

    log_usage(response, "Conversation")

    if result is None:
        raise RuntimeError(
            "OpenAI did not return a valid conversation response."
        )

    return result


def generate_itinerary(trip_state: TripState):
    """
    Generate an itinerary using the collected trip preferences.
    """

    client = get_client()

    instructions = """
    You are TravelAdvisor AI, an expert travel itinerary planner.

    Generate a practical, personalized itinerary based
    on the supplied trip preferences.

    REQUIREMENTS:
    - Use the exact destination label supplied.
    - Generate exactly the requested number of days.
    - Include a title and a short summary.
    - Include realistic activities in a sensible order.
    - Include practical travel tips.
    - Include an estimated total budget.
    - Reflect the user's interests and constraints.
    - Consider the number of travelers when estimating costs.
    - Consider the group composition when suggesting activities.
    - If children are included, suggest age-appropriate activities.
    - Do not assume children's ages unless provided.
    - State whether the budget is per person or for the whole group.
    - Avoid double-counting shared costs such as accommodation.
    - Clearly label all costs as estimates.
    - Do not claim to have checked live prices, weather,
      opening hours, or transport availability.
    - Do not invent additional user preferences.

    Return the itinerary using the required schema.
    """

    response = client.responses.parse(
        model=get_model(),
        instructions=instructions,
        input=[
            {
                "role": "user",
                "content": (
                    "Generate an itinerary for:\n"
                    + trip_state.model_dump_json(indent=2)
                ),
            }
        ],
        text_format=TravelItinerary,
    )

    itinerary = response.output_parsed

    log_usage(response, "Itinerary generation")

    if itinerary is None:
        raise RuntimeError(
            "OpenAI did not return a valid itinerary."
        )

    return itinerary