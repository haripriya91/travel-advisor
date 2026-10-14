# AI workflow — TravelAdvisor AI

## Two separate OpenAI tasks

**Conversation understanding:** `plan_next_turn(messages, current_state, has_itinerary)` uses structured outputs to return a `TravelTurn` containing an assistant message, updated `TripState`, and a generation decision.

**Itinerary generation:** `generate_itinerary(trip_state)` uses structured outputs to return `TravelItinerary`, with a summary, day-by-day activities, practical tips, estimated budget, and budget basis.

Keeping these tasks separate avoids regenerating an entire itinerary for every user message.

## Conversation context

The app persists all messages and trip details in SQLite. Each conversation API request includes the saved structured trip state and up to six recent messages (`HISTORY_LIMIT = 6`). The notebook separately demonstrates `previous_response_id`; the app itself does not depend on that mechanism for persistence.

## Validation

- Destination, positive trip duration, at least one interest, and traveler count are required for generation.
- Pydantic validates types, value ranges, and itinerary day numbering.
- The assistant is prompted to ask for clarification when details are ambiguous or contradictory.
- Estimated prices are not verified against live travel providers.

## Next development step

Implement a weather tool using Open-Meteo, expose it to OpenAI as a function tool, execute it in Python with validated arguments, and return the external result to the model before answering the user.
