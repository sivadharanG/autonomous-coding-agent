import json
import os
from datetime import datetime

LOGS_DIR = "logs"


def log_run(issue_description: str, result: dict, pr_url: str = None):
    """
    Saves a full run's result to a timestamped JSON file in logs/.

    Args:
        issue_description (str): the original task
        result (dict): the final AgentState after the graph run
        pr_url (str): optional PR URL if one was created
    """
    os.makedirs(LOGS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{LOGS_DIR}/run_{timestamp}.json"

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "issue_description": issue_description,
        "status": result.get("status"),
        "is_approved": result.get("is_approved"),
        "retry_count": result.get("retry_count"),
        "max_retries": result.get("max_retries"),
        "plan": result.get("plan"),
        "final_code": result.get("current_code"),
        "test_results": result.get("test_results"),
        "critic_feedback": result.get("critic_feedback"),
        "pull_request_url": pr_url,
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)

    print(f"\n[LOG] Run saved to {filename}")

    return filename