from dotenv import load_dotenv
load_dotenv()

import os
import json
from groq import Groq
from agent.state import AgentState

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CRITIC_SYSTEM_PROMPT = """You are a senior code reviewer evaluating whether a coding task was completed correctly.

You will be given:
1. The original task description
2. The code that was written
3. The output from running that code

Decide if the code correctly and completely solves the task.

Rules:
- Return ONLY valid JSON, no other text, no markdown code fences.
- Format: {"approved": true/false, "feedback": "explanation"}
- If approved is true, feedback should briefly confirm why it's correct.
- If approved is false, feedback should clearly explain what's wrong or missing,
  so the coder can fix it in the next attempt.
- Be strict: placeholder comments like "TODO", missing edge cases, or code that
  doesn't fully address the task should NOT be approved.

Example:
Task: "Validate that email is not empty"
Code: includes a TODO for validation logic
Output: {"approved": false, "feedback": "The email validation logic is a TODO placeholder and is not actually implemented. The task is not complete."}
"""


def critic_node(state: AgentState) -> AgentState:
    """
    Evaluates the generated code and execution results.
    Updates state['is_approved'], state['critic_feedback'], state['retry_count'], state['status'].
    """
    issue = state["issue_description"]
    code = state["current_code"]
    test_results = state["test_results"]

    user_message = f"""Task: {issue}

Code:
{code}

Execution Output:
{test_results}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=500,
        messages=[
            {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    raw_text = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw_text)
        approved = parsed["approved"]
        feedback = parsed["feedback"]
    except (json.JSONDecodeError, KeyError):
        # If critic output is malformed, default to NOT approved (safe default)
        approved = False
        feedback = f"ERROR: Could not parse critic response. Raw output: {raw_text}"

    state["is_approved"] = approved
    state["critic_feedback"] = feedback

    if not approved:
        state["retry_count"] += 1

    state["status"] = "approved" if approved else "rejected"

    print(f"[CRITIC] Approved: {approved} | Retry Count: {state['retry_count']}")
    print(f"[CRITIC] Feedback: {feedback}\n")

    return state