import streamlit as st
import uuid


# --- 1. EPHEMERAL STORAGE ---
# Data lives in memory. Restarting the server wipes all secrets.
@st.cache_resource
def get_poll_storage():
    return {}


polls = get_poll_storage()


# --- 2. THE ALGORITHM ---
def calculate_outcome(poll_id):
    poll = polls[poll_id]
    votes = poll["votes"]

    # A. Initialization: Map raw votes to effective states
    # 'pending' means the user is waiting on someone else
    effective_votes = {}

    for user, data in votes.items():
        v_type = data["type"]
        if v_type == "hard":
            effective_votes[user] = "cancel"
        elif v_type == "go":
            effective_votes[user] = "go"
        elif v_type == "soft":
            effective_votes[user] = "cancel"  # Soft cancel counts towards threshold
        else:
            effective_votes[user] = "pending"  # Conditional

    # B. Chain Resolution (Iterative)
    # Solves linear chains: A needs B -> B needs C -> C Cancels === All Cancel
    changes = True
    while changes:
        changes = False
        for user, data in votes.items():
            if data["type"] == "conditional":
                target = data["target"]

                # If the target hasn't voted (shouldn't happen if we wait for full house), ignore
                if target not in effective_votes:
                    continue

                target_status = effective_votes[target]
                current_status = effective_votes.get(user)

                # Resolve based on target's effective status
                new_status = current_status
                if target_status == "go":
                    new_status = "go"
                elif target_status == "cancel":
                    new_status = "cancel"  # If wingman bails, I bail (soft cancel)

                if new_status != current_status:
                    effective_votes[user] = new_status
                    changes = True

    # C. Deadlock Resolution (The "Mutual Pact")
    # If users are still 'pending', they are in a circular loop (A needs B, B needs A).
    # Logic: We treat mutual dependency as a BLOOD PACT -> GO.
    for user, status in effective_votes.items():
        if status == "pending":
            effective_votes[user] = "go"

    # D. Final Tally
    # We count how many effective 'cancels' exist
    cancel_count = sum(1 for status in effective_votes.values() if status == "cancel")
    total_participants = len(poll["participants"])
    threshold = total_participants / 2

    if cancel_count > threshold:
        poll["status"] = "cancelled"
    else:
        poll["status"] = "confirmed"

    return


# --- 3. THE UI ---
st.set_page_config(page_title="Ghost Vote", page_icon="👻")

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
        calculate_outcome(poll_id)  # Trigger calc if this is the last refresh
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
                calculate_outcome(poll_id)

            st.rerun()

    st.write("---")
    st.caption(f"Waiting for {len(remaining_voters)} more people to vote.")
