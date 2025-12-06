import uuid

import streamlit as st

from src import config, storage
from src.logic import calculate_outcome

st.set_page_config(page_title=config.APP_TITLE, page_icon=config.APP_ICON)

polls = storage.get_polls()
lock = storage.get_lock()


st.set_page_config(page_title="Cancel-It Vote", page_icon="🚫")

# Hide Streamlit elements for "App-like" feel
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# URL Routing
query_params = st.query_params
poll_id = query_params.get("poll", None)

# === VIEW 1: CREATE POLL ===
if not poll_id:
    st.title("Cancel-It")
    st.write("### The Abilene Paradox Solver")

    with st.form("create_form"):
        st.write("WHO IS INVITED?")
        st.caption("Enter first names, separated by commas.")
        raw_names = st.text_area("Participants", value="Alice, Bob, Charlie")

        submitted = st.form_submit_button("Create Secret Vote")

        if submitted:
            # Clean up names
            participants = [n.strip() for n in raw_names.split(",") if n.strip()]

            if len(participants) < 2:
                st.error("You need at least 2 people.")
            else:
                new_id = str(uuid.uuid4())[:8]
                polls[new_id] = {
                    "participants": participants,
                    "votes": {},
                    "status": "active",
                }
                st.success("Poll Created!")
                # In production, use your actual domain/IP
                link = f"http://localhost:8501/?poll={new_id}"
                st.code(link, language="text")
                st.write("Copy this link to your group chat.")

# === VIEW 2: VOTING BOOTH ===
else:
    if poll_id not in polls:
        st.error("🚫 Poll not found. It may have expired.")
        st.stop()

    poll = polls[poll_id]

    # HEADER
    st.title("Event Status")

    # RESULTS DISPLAY
    if poll["status"] != "active":
        if poll["status"] == "cancelled":
            st.error("🛑 EVENT CANCELLED")
            st.write("The majority chose to opt out.")
        else:
            st.success("✅ EVENT CONFIRMED")
            st.write("The group is going.")
        st.stop()

    # VOTING FORM
    st.write("Vote secretly. No notifications are sent.")

    # 1. Identify User
    st.write("### 1. Who are you?")
    remaining_voters = [p for p in poll["participants"] if p not in poll["votes"]]

    # If user already voted, just show status
    if len(remaining_voters) == 0:
        st.info("Waiting for results...")
        calculate_outcome(poll)  # Trigger calc if this is the last refresh
        st.rerun()

    me = st.selectbox("Select your name", ["Select..."] + remaining_voters)

    if me != "Select...":
        # 2. Cast Vote
        st.write(f"### 2. Hi {me}, what do you want to do?")

        vote_choice = st.radio(
            "Select an option:",
            [
                "🟢 I'm definitely going (Go)",
                "🟡 I'd rather not, but will follow group (Soft Cancel)",
                "🔴 I am NOT going (Hard Cancel)",
                "🔗 I go only if [Wingman] goes",
            ],
        )

        final_vote_data = {}

        if "Wingman" in vote_choice:
            # Filter self out of wingman list
            others = [p for p in poll["participants"] if p != me]
            wingman = st.selectbox("Who is your Wingman?", others)
            final_vote_data = {"type": "conditional", "target": wingman}
        elif "definitely" in vote_choice:
            final_vote_data = {"type": "go"}
        elif "rather not" in vote_choice:
            final_vote_data = {"type": "soft"}
        elif "NOT going" in vote_choice:
            final_vote_data = {"type": "hard"}

        if st.button("Cast Secret Vote"):
            poll["votes"][me] = final_vote_data

            # Check if this was the last vote needed
            if len(poll["votes"]) >= len(poll["participants"]):
                calculate_outcome(poll)

            st.rerun()

    st.write("---")
    st.caption(f"Waiting for {len(remaining_voters)} more people to vote.")
