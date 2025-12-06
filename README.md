## 🚫 Cancel-It
The "Abilene Paradox" Solver.

A privacy-focused, ephemeral voting tool designed for social groups to opt-out of plans without social friction. Built with Python and Streamlit.

## 📖 The Problem: The Abilene Paradox
In sociology, the Abilene Paradox occurs when a group of people collectively decide on a course of action that is counter to the preferences of many (or all) of the individuals in the group. It stems from a breakdown of communication where each member mistakenly believes that their own preferences are contrary to the group's, and therefore does not raise objections.

> Example: Four friends agree to drive to Abilene for dinner. It is a hot, dusty drive. They arrive, eat a mediocre meal, and return home exhausted. Once back, they realize that none of them actually wanted to go; they only agreed because they thought the others wanted to.

Cancel-It solves this by introducing private preference aggregation. It allows the group to discover the "True Will" of the collective without exposing the "Social Face" of the individual.

## ⚖️ Design Principles & Mechanism
This tool is built on specific game-theoretic and privacy principles to ensure honest voting.

1. The "Black Box" Notification Policy: the system sends zero notifications when a vote is cast. Participants are only notified when the poll concludes.

## Weighting
| Option      | Icon | Weight (Towards Cancel) | Semantic Meaning                                                                                     |
| ----------- | ---- | ----------------------- | ---------------------------------------------------------------------------------------------------- |
| Go          | 🟢  | 0.0                     | "I want to go." This vote actively fights against cancellation.                                      |
| Soft Cancel | 🟡  | 1.0                     | "I prefer not to, but I'll follow the group." (Treats polite hesitation as a valid vote to opt-out). |
| Hard Cancel | 🔴  | 1.0                     | "I am not going." (Mathematically identical to Soft Cancel, but represents a definitive boundary).   |
| Wingman     | 🔗  | Variable                | "I go only if [Name] goes." (Resolves recursively before the count).                                 |

## Wingman system
Your vote can be automatically adjusted based on who is attending.
1. The Pair: Alice needs Bob $\leftrightarrow$ Bob needs Alice.
    - Result: Both GO. (The Pact).
2. The Train: Alice needs Bob $\rightarrow$ Bob needs Charlie $\rightarrow$ Charlie needs Alice.
    - Result: All GO. (The Group Pact).
3. The Broken Chain: Alice needs Bob $\rightarrow$ Bob needs Charlie $\rightarrow$ Charlie Hard Cancels.
    - Result: All CANCEL. (The Domino Effect).

# Install dependencies
```shell
uv sync
```

# Run the app
```shell
uv run streamlit run app.py
```
## 🛡 Security Note
This tool uses URL-based IDs (?poll=uuid). While the UUIDs are unguessable, anyone with the link can vote. Do not share poll links publicly; they are intended for private messaging groups (Signal/WhatsApp) only.

## FAQs
1. Why does "Soft" have the same weight as "Hard"?

**Scenario A: Weight = 1.0** (current weighting)
$$Score = 0 (Alice) + 1 (Bob) + 1 (Charlie) = 2$$
$$Threshold = 1.5$$

Result: $2 > 1.5 \rightarrow$ CANCEL. (Success)

**Scenario B: Weight = 0.5**
$$Score = 0 (Alice) + 0.5 (Bob) + 0.5 (Charlie) = 1.0$$
$$Threshold = 1.5$$

Result: $1.0 < 1.5 \rightarrow$ GO. (Failure)

Conclusion: With 0.5 weighting, even if the majority (2 out of 3) vote "Soft Cancel," the event still happens. This is the Abilene Paradox, as most of the group would rather cancel.
