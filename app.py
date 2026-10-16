
import streamlit as st

from src.usage_service import get_usage_summary
from src.database import create_tables
from src.repository import (
    get_itinerary,
    get_messages,
    list_conversations,
)
from src.conversation_service import (
    handle_user_message,
    start_conversation,
)

from datetime import date, timedelta

from src.tools import (
    get_weather_forecast,
    convert_currency,
)


# --------------------------------------------------
# 1. Page configuration and database initialization
# --------------------------------------------------

st.set_page_config(
    page_title="TravelAdvisor AI",
    page_icon="✈️",
    layout="wide",
)

create_tables()

st.title("✈️ TravelAdvisor AI")
st.caption("Plan your next trip through conversation.")


# --------------------------------------------------
# 2. Sidebar: saved conversations
# --------------------------------------------------

with st.sidebar:
    st.header("Your conversations")

    if st.button("＋ New trip", use_container_width=True):
        conversation_id = start_conversation()
        st.session_state["conversation_id"] = conversation_id
        st.rerun()

    conversations = list_conversations()

    if not conversations:
        st.info("Start a new trip to begin.")
        st.stop()

    # Get the IDs of all saved conversations.
    conversation_ids = [
        item["id"]
        for item in conversations
    ]

    # Show the title, creation time, and short ID.
    labels = {
        item["id"]: (
            f"{item['title']} — "
            f"{item['created_at']} — "
            f"{item['id'][:8]}"
        )
        for item in conversations
    }

    # Select the current conversation.
    selected_id = st.session_state.get("conversation_id")

    # If no valid conversation is selected, use the newest one.
    if selected_id not in conversation_ids:
        selected_id = conversation_ids[0]

    selected_id = st.selectbox(
        "Saved trips",
        options=conversation_ids,
        index=conversation_ids.index(selected_id),
        format_func=lambda cid: labels[cid],
    )

    # Save the selected conversation ID.
    st.session_state["conversation_id"] = selected_id

    st.divider()

    # extra tools 

    st.sidebar.divider()
    st.sidebar.subheader("Travel Tools")

    if st.sidebar.button(
        "🌦️ Weather Forecast",
        use_container_width=True,
    ):
        st.session_state["active_tool"] = "weather"

    if st.sidebar.button(
        "💱 Currency Converter",
        use_container_width=True,
    ):
        st.session_state["active_tool"] = "currency"


    # Show the selected travel tool
    active_tool = st.session_state.get("active_tool")

    if active_tool == "weather":
        st.subheader("🌦️ Weather Forecast")

        city = st.text_input(
            "Destination city",
            key="weather_city",
            placeholder="e.g. Berlin",
        )

        weather_start = st.date_input(
            "Forecast start date",
            value=date.today(),
            key="weather_start",
        )

        weather_days = st.number_input(
            "Number of days",
            min_value=1,
            max_value=16,
            value=3,
            key="weather_days",
        )

        if st.button("Get Weather Forecast"):
            if not city.strip():
                st.warning("Please enter a destination city.")
            else:
                result = get_weather_forecast(
                    city=city.strip(),
                    start_date=weather_start.isoformat(),
                    days=int(weather_days),
                )

                if result.get("error"):
                    st.error(result["error"])
                else:
                    st.dataframe(
                        result["forecast"],
                        use_container_width=True,
                        hide_index=True,
                    )

    elif active_tool == "currency":
        st.subheader("💱 Currency Converter")

        currencies = [
            "EUR", "USD", "GBP", "JPY", "CHF",
            "CAD", "AUD", "INR", "CNY", "SGD",
        ]

        amount = st.number_input(
            "Amount",
            min_value=0.01,
            value=100.0,
            key="currency_amount",
        )

        col1, col2 = st.columns(2)

        with col1:
            from_currency = st.selectbox(
                "From",
                currencies,
                index=0,
                key="currency_from",
            )

        with col2:
            to_currency = st.selectbox(
                "To",
                currencies,
                index=1,
                key="currency_to",
            )

        if st.button("Convert Currency"):
            result = convert_currency(
                amount=float(amount),
                from_currency=from_currency,
                to_currency=to_currency,
            )

            if result.get("error"):
                st.error(result["error"])
            elif result.get("converted") is not None:
                st.success(
                    f"{result['amount']:.2f} {result['from']} = "
                    f"{result['converted']:.2f} {result['to']}"
                )
            else:
                st.error("The exchange rate could not be retrieved.")    











    st.subheader("📊 API Usage")

    usage_summary = get_usage_summary()

    st.metric(
        "Total API Requests",
        usage_summary["request_count"],
    )

    st.metric(
        "Total Tokens",
        f"{usage_summary['total_tokens']:,}",
    )

    if (
        usage_summary["priced_requests"]
        == usage_summary["request_count"]
    ):
        st.metric(
            "Estimated API Cost",
            f"${(usage_summary['total_cost_usd'] or 0):.6f}",
        )
    else:
        st.caption(
            "Total cost unavailable: some models "
            "do not have configured pricing."
        )

    st.caption("Local usage history · Estimated USD")



# --------------------------------------------------
# 3. Display saved conversation messages
# --------------------------------------------------

messages = get_messages(selected_id)

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------------------------
# 4. Display saved itinerary
# --------------------------------------------------

itinerary = get_itinerary(selected_id)

if itinerary:
    st.divider()

    st.subheader(itinerary["title"])
    st.write(itinerary["summary"])

    # Display each day.
    for day in itinerary["days"]:
        with st.expander(
            f"Day {day['day']}: {day['title']}",
            expanded=True,
        ):
            for activity in day["activities"]:
                st.markdown(
                    f"**{activity['time']} — {activity['title']}**"
                )

                st.write(activity["description"])

                st.caption(
                    f"Estimated activity cost: "
                    f"{activity['estimated_cost']:.2f} "
                    f"{itinerary['currency']}"
                )

    # Practical tips.
    st.subheader("Practical tips")

    for tip in itinerary["practical_tips"]:
        st.markdown(f"- {tip}")

    # Estimated budget.
    st.subheader("Estimated budget")

    st.write(
        f"{itinerary['estimated_budget']:.2f} "
        f"{itinerary['currency']}"
    )

    st.caption(
        itinerary.get(
            "budget_basis",
            "Estimated travel budget"
        )
    )

    # --------------------------------------------------
    # 5. Export itinerary as Markdown
    # --------------------------------------------------

    markdown = [
        f"# {itinerary['title']}",
        "",
        itinerary["summary"],
        "",
    ]

    for day in itinerary["days"]:
        markdown.extend(
            [
                f"## Day {day['day']}: {day['title']}",
                "",
            ]
        )

        for activity in day["activities"]:
            markdown.extend(
                [
                    f"### {activity['time']} — {activity['title']}",
                    activity["description"],
                    (
                        f"Estimated activity cost: "
                        f"{activity['estimated_cost']:.2f} "
                        f"{itinerary['currency']}"
                    ),
                    "",
                ]
            )

    markdown.extend(
        [
            "## Practical tips",
            "",
        ]
    )

    markdown.extend(
        [
            f"- {tip}"
            for tip in itinerary["practical_tips"]
        ]
    )

    markdown.extend(
        [
            "",
            "## Estimated budget",
            "",
            (
                f"{itinerary['estimated_budget']:.2f} "
                f"{itinerary['currency']}"
            ),
            "",
            itinerary.get(
                "budget_basis",
                "Estimated travel budget"
            ),
        ]
    )

    st.download_button(
        "Download itinerary as Markdown",
        data="\n".join(markdown),
        file_name="traveladvisor_itinerary.md",
        mime="text/markdown",
    ) 

    

# --------------------------------------------------
# 6. Handle new user messages
# --------------------------------------------------

if prompt := st.chat_input("Where would you like to travel?"):
    with st.spinner("Planning your trip..."):
        try:
            handle_user_message(
                selected_id,
                prompt,
            )

            st.rerun()

        except Exception as exc:
            st.error(
                f"Could not process your message: {exc}"
            )

            st.caption(
                "Your submitted message may already be saved. "
                "Check the conversation history before retrying."
            )


