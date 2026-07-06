from agent.github_client import fetch_issue

task = fetch_issue("psf/requests", 1)

print("Fetched task description:\n")
print(task)