
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

    conversation_ids = [
        item["id"]
        for item in conversations
    ]

    selected_id = st.session_state.get("conversation_id")

    if selected_id not in conversation_ids:
        selected_id = conversation_ids[0]

    labels = {
        item["id"]: item["title"]
        for item in conversations
    }

    selected_id = st.selectbox(
        "Saved trips",
        options=conversation_ids,
        index=conversation_ids.index(selected_id),
        format_func=lambda cid: labels[cid],
    )

    st.session_state["conversation_id"] = selected_id

    st.divider()
    
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
