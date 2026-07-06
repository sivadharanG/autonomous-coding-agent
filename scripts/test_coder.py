from agent.state import AgentState
from agent.nodes.coder import coder_node

test_state: AgentState = {
    "issue_description": "Add input validation to the signup form to reject empty emails",
    "plan": [
        "Locate the signup form handler function",
        "Add a check for empty or whitespace-only email input",
        "Return a clear error message if validation fails",
        "Write a test case for empty email input",
    ],
    "current_code": None,
    "test_results": None,
    "critic_feedback": None,
    "is_approved": False,
    "retry_count": 0,
    "max_retries": 3,
    "status": "planned",
}

result = coder_node(test_state)

print("Status:", result["status"])
print("\nGenerated Code:\n")
print(result["current_code"])