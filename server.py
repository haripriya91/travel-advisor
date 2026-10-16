
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

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


from fastapi.staticfiles import StaticFiles

app.mount(
    "/",
    StaticFiles(directory="public", html=True),
    name="frontend",
)