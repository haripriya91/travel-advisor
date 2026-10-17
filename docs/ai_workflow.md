# AI workflow

## Processing a message

1. The browser posts a message to `/api/conversations/{conversation_id}/messages`.
2. FastAPI validates the request and checks that the conversation exists.
3. The conversation service validates input, saves the user message, and loads recent history, current trip state, and any existing itinerary.
4. The AI service sends instructions and context to the configured OpenAI model. Tool integrations can supply weather, currency, or travel-research information as supported by the current implementation.
5. The model returns a structured turn. The service uses clarification and generation signals to decide whether to ask a follow-up or generate/revise an itinerary.
6. Pydantic validates structured data; the service persists accepted state, assistant messages, and itinerary results.
7. The API returns messages, trip state, and itinerary for browser rendering. Usage is recorded through the project's usage integration.

## State and context

Trip state captures destination, duration, interests, travelers, and optional preferences/budget. Itinerary data contains daily activities, practical tips, and budget estimates. Validation enforces the constraints defined in `schemas.py`, including itinerary-day consistency.

The database stores history, but the model only sees context explicitly included in each request. Current context is bounded recent history plus supplied trip state/itinerary information. Do not document a fixed message count without checking the current service code.

## Tools and trust

The application executes supported tool integrations and supplies their results to the AI workflow. Input types, allowed tool names, argument fields, and call limits should be validated by application code. External content and tool output are untrusted data, not instructions that may override application rules.

Weather and currency have direct API endpoints as well as integration into the broader application. Web research does not verify every itinerary detail automatically. Estimates remain estimates.

## Planned summarization

Automatic long-conversation summarization is not part of the current documented implementation. A future approach would measure context size, summarize older turns, and send the summary with recent turns and authoritative trip state. Retain original messages for history and track which turns the summary covers.

## UI feedback

Typing dots indicate a pending request. They are not token streaming. The browser displays a locally appended user message immediately, then replaces the conversation with saved server messages when the response arrives.
