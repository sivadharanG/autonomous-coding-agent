from dotenv import load_dotenv
load_dotenv()

import os
import re
from groq import Groq
from agent.state import AgentState

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

CODER_SYSTEM_PROMPT = """You are a senior software engineer implementing a coding task.

You will be given a step-by-step plan. Write clean, working Python code that implements ALL the steps.

Rules:
- Return ONLY the code, no explanations before or after.
- Do NOT wrap the code in markdown code fences (no ```python or ```).
- Include docstrings and comments where helpful.
- Include a simple test/example usage at the bottom if relevant.
- Write complete, runnable code, not pseudocode or placeholders like "# TODO".
"""


def strip_markdown_fences(text: str) -> str:
    """
    Removes markdown code fences (```python ... ```) if the LLM adds them
    despite instructions not to. Defensive parsing — LLMs don't always follow
    formatting instructions perfectly.
    """
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    return text.strip()


def coder_node(state: AgentState) -> AgentState:
    """
    Takes the plan from state and generates code implementing it.
    Updates state['current_code'] and state['status'].
    """
    plan = state["plan"]
    plan_text = "\n".join(f"- {step}" for step in plan)

    feedback_context = ""
    if state.get("critic_feedback"):
        feedback_context = f"\n\nPrevious attempt had issues. Feedback to fix:\n{state['critic_feedback']}"

    user_message = f"Plan:\n{plan_text}{feedback_context}"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2000,
        messages=[
            {"role": "system", "content": CODER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    raw_code = response.choices[0].message.content
    clean_code = strip_markdown_fences(raw_code)

    state["current_code"] = clean_code
    state["status"] = "coded"
    print(f"\n[CODER] Attempt {state['retry_count'] + 1} — code generated ({len(clean_code)} chars)")

    return state