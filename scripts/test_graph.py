from agent.graph import build_graph

app = build_graph()

initial_state = {
    "issue_description": "Build a password strength checker function that requires at least 8 characters, one uppercase letter, one number, and one special character. Return specific error messages listing exactly which requirements are missing, and include test cases covering each individual failure condition plus a fully valid password.",
    "plan": None,
    "current_code": None,
    "test_results": None,
    "critic_feedback": None,
    "is_approved": False,
    "retry_count": 0,
    "max_retries": 3,
    "status": "new",
}

result = app.invoke(initial_state)

print("Final Status:", result["status"])

print("\nPlan:")
for i, step in enumerate(result["plan"], 1):
    print(f"  {i}. {step}")

print("\nGenerated Code:\n")
print(result["current_code"])

print("\nTest Results:\n")
print(result["test_results"])

print("\nApproved:", result["is_approved"])
print("Retry Count:", result["retry_count"])
print("Critic Feedback:", result["critic_feedback"])
print("Final Status:", result["status"])