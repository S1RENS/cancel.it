import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage. Structure:
# {
#   "poll_id": {
#       "total_participants": 3,
#       "votes": { "user_1": "go", "user_2": "soft_cancel" ... },
#       "status": "pending" # or "cancelled", "confirmed"
#   }
# }
polls = {}


@app.route("/create", methods=["POST"])
def create_poll():
    data = request.json
    try:
        total_participants = int(data.get("participants"))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid participant count"}), 400

    # Generate a random UUID so poll URLs are not guessable (Privacy)
    poll_id = str(uuid.uuid4())

    polls[poll_id] = {
        "total_participants": total_participants,
        "votes": {},
        "status": "pending",
    }

    return jsonify(
        {"poll_id": poll_id, "link": f"http://localhost:5000/vote/{poll_id}"}
    )


@app.route("/vote/<poll_id>", methods=["POST"])
def cast_vote(poll_id):
    if poll_id not in polls:
        return jsonify({"error": "Poll not found"}), 404

    poll = polls[poll_id]

    # Simple privacy check: Prevent voting if poll is closed
    if poll["status"] != "pending":
        return jsonify({"message": f"Poll closed. Result: {poll['status']}"})

    data = request.json
    user_id = data.get("user_id")  # In a real app, this would be a session token
    vote_type = data.get("vote")  # 'go', 'soft', 'hard'

    if vote_type not in ["go", "soft", "hard"]:
        return jsonify({"error": "Invalid vote type"}), 400

    # Record vote
    poll["votes"][user_id] = vote_type

    # Check if we have enough votes to calculate result
    current_votes = len(poll["votes"])

    if current_votes >= poll["total_participants"]:
        return calculate_results(poll_id)

    return jsonify(
        {
            "message": "Vote received",
            "votes_needed": poll["total_participants"] - current_votes,
        }
    )


def calculate_results(poll_id):
    poll = polls[poll_id]
    votes = poll["votes"]

    cancel_sentiment = 0

    for v in votes.values():
        if v in ["soft", "hard"]:
            cancel_sentiment += 1

    # Majority logic
    threshold = poll["total_participants"] / 2

    if cancel_sentiment > threshold:
        poll["status"] = "cancelled"
    else:
        poll["status"] = "confirmed"

    # PRIVACY FEATURE: Once calculated, we could wipe the individual votes
    # poll['votes'] = {}

    return jsonify(
        {
            "status": "complete",
            "result": poll["status"],
            "cancel_votes": cancel_sentiment,
            "total_participants": poll["total_participants"],
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
