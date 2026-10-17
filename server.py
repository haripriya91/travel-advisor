"""Expose TravelAdvisor's conversation, usage, and travel-tool APIs.

This module handles HTTP requests and request validation.
Conversation logic, database access, and external tool calls
are delegated to their respective services.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from datetime import date
from src.tools import get_weather_forecast, convert_currency
from fastapi.middleware.cors import CORSMiddleware

from src.conversation_service import (
    start_conversation,
    handle_user_message,
)
from src.repository import (
    list_conversations,
    get_messages,
    get_itinerary,
    get_trip_state,
)
from src.usage_service import get_usage_summary

# Create the API application and configure its /docs metadata.

app = FastAPI(
    title="TravelAdvisor AI API",
    version="1.0.0",
)

# Allow the deployed frontend and local development frontend
# to make browser requests to this API.
# CORS does not provide authentication or conversation ownership checks.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://travel-advisor-frontend.vercel.app",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Request schemas define the JSON bodies accepted by POST routes.
# FastAPI validates these before calling the endpoint function.

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

class WeatherRequest(BaseModel):
    city: str = Field(min_length=1, max_length=100)
    start_date: date
    days: int = Field(default=3, ge=1, le=16)


class CurrencyRequest(BaseModel):
    amount: float = Field(gt=0)
    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(min_length=3, max_length=3)


@app.get("/api/health")
def health():
    """Confirm that the API can respond.

    This endpoint does not check database or external-provider access.
    """
    return {"status": "ok"}


@app.post("/api/conversations", status_code=201)
def create_conversation():
    """Create a conversation and return its ID and initial messages."""
    conversation_id = start_conversation()

    return {
        "conversation_id": conversation_id,
        "messages": get_messages(conversation_id),
    }


@app.get("/api/conversations")
def conversations():
    """Return saved conversations for the frontend sidebar."""
    return list_conversations()


@app.get("/api/conversations/{conversation_id}")
def conversation_details(conversation_id: str):
    """Return a saved conversation's messages, trip state, and itinerary.

    Raise HTTP 404 if the conversation does not exist.
    """
    messages = get_messages(conversation_id)
    conversations_list = list_conversations()

    exists = any(
        item["id"] == conversation_id
        for item in conversations_list
    )

    if not exists:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "trip_state": get_trip_state(conversation_id),
        "itinerary": get_itinerary(conversation_id),
    }


@app.post("/api/conversations/{conversation_id}/messages")
def send_message(conversation_id: str, request: ChatRequest):
    """Process a user message and return the updated conversation.

    The conversation service decides whether to answer, ask a
    follow-up question, or generate an itinerary.

    Raise HTTP 404 for an unknown conversation and HTTP 400
    for ValueError exceptions raised during processing.
    """
    conversations_list = list_conversations()

    if not any(
        item["id"] == conversation_id
        for item in conversations_list
    ):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    try:
        result = handle_user_message(
            conversation_id,
            request.message,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "result": result,
        "messages": get_messages(conversation_id),
        "trip_state": get_trip_state(conversation_id),
        "itinerary": get_itinerary(conversation_id),
    }


@app.get("/api/usage")
def usage():
    """Return aggregate recorded AI usage and estimated costs."""
    return get_usage_summary()



@app.post("/api/tools/weather")
def weather(request: WeatherRequest):
    """Fetch a forecast directly for the frontend weather form.

    Convert the validated date to the string format expected
    by the weather tool. Raised exceptions become HTTP 500 responses.
    """
    try:
        result = get_weather_forecast(
            city=request.city.strip(),
            start_date=request.start_date.isoformat(),
            days=request.days,
        )
        return result
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Weather request failed: {error}",
        )


@app.post("/api/tools/currency")
def currency(request: CurrencyRequest):
    """Convert an amount directly for the frontend currency form.

    Normalize currency codes to uppercase before calling the tool.
    Raised exceptions become HTTP 500 responses.
    """
    try:
        result = convert_currency(
            amount=request.amount,
            from_currency=request.from_currency.upper(),
            to_currency=request.to_currency.upper(),
        )
        return result
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Currency conversion failed: {error}",
        )

