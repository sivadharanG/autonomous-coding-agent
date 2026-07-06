from dotenv import load_dotenv
load_dotenv()

import os
import json
from groq import Groq
from agent.state import AgentState

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

PLANNER_SYSTEM_PROMPT = """You are a senior software engineer planning how to solve a coding task.

Given a task description, break it down into a clear, ordered list of concrete steps needed to implement it.

Rules:
- Return ONLY valid JSON, no other text, no markdown code fences.
- Format: {"steps": ["step 1", "step 2", "step 3"]}
- Each step should be specific and actionable (not vague like "write code").
- Keep the plan to 3-6 steps.

Example:
Task: "Add input validation to the signup form to reject empty emails"
Output: {"steps": [
    "Locate the signup form handler function",
    "Add a check for empty or whitespace-only email input",
    "Return a clear error message if validation fails",
    "Write a test case for empty email input"
]}
"""


def planner_node(state: AgentState) -> AgentState:
    """
    Takes the issue description from state and generates a step-by-step plan.
    Updates state['plan'] and state['status'].
    """
    issue = state["issue_description"]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Task: {issue}"}
        ]
    )

    raw_text = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw_text)
        plan = parsed["steps"]
    except (json.JSONDecodeError, KeyError) as e:
        # If the LLM didn't return valid JSON, fail gracefully
        plan = [f"ERROR: Could not parse plan. Raw output: {raw_text}"]

    state["plan"] = plan
    state["status"] = "planned"

    return state