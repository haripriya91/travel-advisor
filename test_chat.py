"""Quick terminal test for tool calling and itinerary generation.

Run from the project root:  python test_chat.py
"""

import json

from src.database import create_tables
from src.conversation_service import start_conversation, handle_user_message
from src.repository import get_itinerary

create_tables()

conversation_id = start_conversation()

test_messages = [
    "What's the weather like in Rome this weekend?",
    "How much is 200 EUR in Japanese yen?",
    "I want to go to Rome for 3 days, starting in 3 days",
    "I like history and food, just me",
]

for text in test_messages:
    print("\n" + "=" * 60)
    print("USER:", text)
    reply = handle_user_message(conversation_id, text)
    print("ASSISTANT:", reply)

itinerary = get_itinerary(conversation_id)

print("\n" + "=" * 60)
if itinerary is None:
    print("No itinerary was generated.")
else:
    print("ITINERARY TITLE:", itinerary["title"])
    print("WEATHER SUMMARY:", itinerary.get("weather_summary"))
    print("TRANSPORT TIPS:", json.dumps(itinerary.get("transport_tips"), indent=2))
    print("CURRENCY NOTE:", itinerary.get("currency_note"))
