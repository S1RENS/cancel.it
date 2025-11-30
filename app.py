import streamlit as st
import uuid


# --- 1. The "Database" ---
# Streamlit re-runs the script on every click. We use @st.cache_resource
# to keep the polls alive in memory across different users/sessions.
@st.cache_resource
def get_poll_storage():
    return {}


polls = get_poll_storage()


# --- 2. The Logic ---
def create_poll(participants):
    poll_id = str(uuid.uuid4())[:8]  # Short ID for easier URL
    polls[poll_id] = {"total": participants, "votes": {}, "status": "active"}
    return poll_id


def calculate_outcome(poll_id):
    poll = polls[poll_id]
    # Filter for valid votes (ignore 'go')
    cancel_count = sum(1 for v in poll["votes"].values() if v in ["soft", "hard"])
    threshold = poll["total"] / 2

    if cancel_count > threshold:
        poll["status"] = "cancelled"
    elif len(poll["votes"]) >= poll["total"]:
        poll["status"] = "confirmed"


# --- 3. The UI (Frontend) ---
st.set_page_config(page_title="Introvert Vote", page_icon="🤫")

# Check URL for ?poll=ID
query_params = st.query_params
poll_id = query_params.get("poll", None)

# === SCENARIO A: LANDING PAGE (Create Poll) ===
if not poll_id:
    st.title("🤫 Secret Cancel")
    st.write("Create a secret vote to cancel plans.")

    participants = st.number_input("How many people?", min_value=2, value=3)

    if st.button("Generate Link"):
        new_id = create_poll(participants)
        # In a real app, replace localhost with your IP/Domain
        link = f"http://localhost:8501/?poll={new_id}"
        st.success("Poll Created! Copy this link to the group chat:")
        st.code(link, language="text")

# === SCENARIO B: VOTING PAGE ===
else:
    if poll_id not in polls:
        st.error("Poll not found. It may have expired or the ID is wrong.")
        st.stop()

    poll = polls[poll_id]

    # Simple header
    st.title("Event Vote")

    if poll["status"] != "active":
        if poll["status"] == "cancelled":
            st.error("🚫 The event has been CANCELLED!")
            st.write("The majority voted to opt out.")
        else:
            st.success("✅ The event is ON!")
            st.write("Not enough people wanted to cancel.")
    else:
        st.info("Vote secretly. Results revealed only if majority cancels.")

        # User Identification (Simple version: Enter name)
        # In a real app, you'd use a browser cookie or login to prevent double voting
        user = st.text_input("Your Name")

        if user:
            if user in poll["votes"]:
                st.warning(f"You voted: **{poll['votes'][user]}**")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("GO 🟢"):
                        poll["votes"][user] = "go"
                        calculate_outcome(poll_id)
                        st.rerun()
                with col2:
                    if st.button("SOFT 🟡"):
                        poll["votes"][user] = "soft"
                        calculate_outcome(poll_id)
                        st.rerun()
                with col3:
                    if st.button("NO 🔴"):
                        poll["votes"][user] = "hard"
                        calculate_outcome(poll_id)
                        st.rerun()

        # Debug/Status view (Optional: Hide this in real version!)
        st.write("---")
        st.caption(f"Votes cast: {len(poll['votes'])} / {poll['total']}")
