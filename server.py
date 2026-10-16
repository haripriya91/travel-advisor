
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from datetime import date
from src.tools import get_weather_forecast, convert_currency

from src.ai_service import generate_destination_image

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


app = FastAPI(
    title="TravelAdvisor AI API",
    version="1.0.0",
)


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

class DestinationImageRequest(BaseModel):
    destination: str = Field(min_length=1, max_length=150) 


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/conversations", status_code=201)
def create_conversation():
    conversation_id = start_conversation()

    return {
        "conversation_id": conversation_id,
        "messages": get_messages(conversation_id),
    }


@app.get("/api/conversations")
def conversations():
    return list_conversations()


@app.get("/api/conversations/{conversation_id}")
def conversation_details(conversation_id: str):
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
    return get_usage_summary()



@app.post("/api/tools/weather")
def weather(request: WeatherRequest):
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

from fastapi.staticfiles import StaticFiles


@app.post("/api/tools/destination-image")
def destination_image(request: DestinationImageRequest):
    try:
        image_url = generate_destination_image(
            request.destination
        )
        return {"image_url": image_url}

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Destination image generation failed: {error}",
        )


app.mount(
    "/",
    StaticFiles(directory="public", html=True),
    name="frontend",
) 

