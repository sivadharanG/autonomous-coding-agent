from agent.state import AgentState
from agent.nodes.executor import executor_node

test_state: AgentState = {
    "issue_description": "Add input validation to the signup form to reject empty emails",
    "plan": ["Add email validation"],
    "current_code": '''
def validate_email(email):
    return email.strip() != ""

print("Testing validate_email:")
print("Empty string:", validate_email(""))
print("Valid email:", validate_email("user@example.com"))
''',
    "test_results": None,
    "critic_feedback": None,
    "is_approved": False,
    "retry_count": 0,
    "max_retries": 3,
    "status": "coded",
}

result = executor_node(test_state)

print("Status:", result["status"])
print("\nTest Results:\n")
print(result["test_results"])