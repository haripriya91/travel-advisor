# ✈️ TravelAdvisor AI

A conversational travel-planning MVP built with **Python, Streamlit, OpenAI Responses API, Pydantic, and SQLite**.

Users describe a trip in natural language. The assistant asks for missing details, maintains context across messages, and produces a structured day-by-day itinerary with practical tips and estimated costs.

## Current features (Phase 1)

- Conversational trip planning and follow-up questions
- Collects destination, trip duration, interests, and traveler count; budget and preferences are optional
- Saves conversations, trip state, and generated itineraries locally in SQLite
- Generates structured itineraries validated by Pydantic, including one day per requested day
- Shows activity estimates, practical tips, total estimated budget, and budget basis
- Exports itineraries as Markdown
- Basic database tests with pytest

**Status:** Core MVP manually tested. Live weather, flight/hotel availability, current prices, and real-time travel research are **not yet integrated**. Estimates are AI-generated, not verified quotes.

## Technology

| Layer | Technology |
| --- | --- |
| UI | Streamlit |
| AI | OpenAI Responses API |
| Data validation | Pydantic |
| Persistence | SQLite (`sqlite3`) |
| Testing | pytest |

## Project structure

```text
travel-advisor/
├── app.py                         # Streamlit UI and Markdown export
├── src/
│   ├── ai_service.py              # OpenAI calls: conversation + itinerary
│   ├── conversation_service.py    # Conversation orchestration and generation decision
│   ├── schemas.py                 # Pydantic data models and validation
│   ├── database.py                # SQLite connection and table creation
│   └── repository.py              # Database reads and writes
├── tests/
│   └── test_database.py           # Isolated database tests
├── notebooks/
│   └── 01_openai_basics.ipynb      # Responses API and token usage experiments
├── docs/
│   ├── architecture.md            # Architecture diagram and data flow
│   └── ai_workflow.md             # Structured outputs and conversation context
├── requirements.txt
├── .env                           # Local secrets: do not commit
└── traveladvisor.db               # Local data: do not commit
```

## Getting started

1. Clone the repository and open the project directory.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` in the project root:

   ```dotenv
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=your_available_model_id
   ```

   Use a model available to your OpenAI account that supports the structured-output calls used in `ai_service.py`.

4. Run the application from the project root:

   ```bash
   streamlit run app.py
   ```

5. Select **New trip** in the sidebar and start chatting.

## Example interaction

**User:** I want to visit Bavaria.

**Assistant:** How many days will you stay, and what interests you?

**User:** Five days. Hiking and sightseeing.

**Assistant:** How many people are traveling?

**User:** Two adults.

The application can then generate a five-day itinerary with activities, tips, and an estimated group budget. Actual wording varies by model.

## Tests

```bash
python -m pytest tests/ -v
```

The current automated tests cover basic database operations. Conversation behavior has also been checked manually; automated AI-behavior coverage is not comprehensive.

## Architecture and AI workflow

See [Architecture](docs/architecture.md) and [AI workflow](docs/ai_workflow.md).

## Next phases

- **Phase 2:** External tools, beginning with live weather using Open-Meteo and OpenAI function calling
- **Phase 3:** Token/cost tracking, model comparison, and expanded project documentation
- **Later enhancements:** Prompt-injection defenses, long-chat summaries, image generation, and optional hotel/transport research

## Security and limitations

- Never commit `.env`, API keys, or the local SQLite database.
- Weather and travel prices are not currently verified in real time.
- Model-generated itineraries may need human review for feasibility and accuracy.
- This is a local educational MVP; production deployment requires additional security and operational work.

## References

- [OpenAI API documentation](https://platform.openai.com/docs)
- [Streamlit documentation](https://docs.streamlit.io/)
- [Pydantic documentation](https://docs.pydantic.dev/)
- [Open-Meteo](https://open-meteo.com/) (planned integration)
