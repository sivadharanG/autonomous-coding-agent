from agent.state import AgentState
from agent.nodes.planner import planner_node

# Create a fake initial state to test the planner
test_state: AgentState = {
    "issue_description": "Add input validation to the signup form to reject empty emails",
    "plan": None,
    "current_code": None,
    "test_results": None,
    "critic_feedback": None,
    "is_approved": False,
    "retry_count": 0,
    "max_retries": 3,
    "status": "new",
}

result = planner_node(test_state)

print("Status:", result["status"])
print("Plan:")
for i, step in enumerate(result["plan"], 1):
    print(f"  {i}. {step}")