import sys
from agent.graph import build_graph
from agent.github_client import fetch_issue, create_pull_request
from agent.logger import log_run


def print_banner():
    print("=" * 60)
    print("  Autonomous AI Coding Agent")
    print("=" * 60)


def run_agent(issue_description: str, repo_for_pr: str = None):
    app = build_graph()

    initial_state = {
        "issue_description": issue_description,
        "plan": None,
        "current_code": None,
        "test_results": None,
        "critic_feedback": None,
        "is_approved": False,
        "retry_count": 0,
        "max_retries": 3,
        "status": "new",
    }

    print(f"\nTask: {issue_description}\n")
    print("Running agent...\n")

    result = app.invoke(initial_state)

    print("\n" + "=" * 60)
    print("  RESULT")
    print("=" * 60)

    print(f"\nFinal Status: {result['status']}")
    print(f"Approved: {result['is_approved']}")
    print(f"Retries used: {result['retry_count']} / {result['max_retries']}")

    print("\nPlan:")
    for i, step in enumerate(result["plan"], 1):
        print(f"  {i}. {step}")

    print("\nFinal Code:\n")
    print(result["current_code"])

    print("\nExecution Output:\n")
    print(result["test_results"])

    pr_url = None

    if not result["is_approved"]:
        print("\nWARNING: Task was not fully approved by the critic.")
        print(f"Last feedback: {result['critic_feedback']}")
    elif repo_for_pr:
        print(f"\nOpening pull request on {repo_for_pr}...")
        pr_url = create_pull_request(
            repo_full_name=repo_for_pr,
            code=result["current_code"],
            plan=result["plan"],
            test_results=result["test_results"],
            issue_description=issue_description,
        )
        print(f"\nPull request created: {pr_url}")

    log_run(issue_description, result, pr_url)

    return result


def print_usage():
    print("\nUsage:")
    print('  python main.py "your task description here"')
    print("  python main.py --github <owner/repo> <issue_number>")
    print("  python main.py --github <owner/repo> <issue_number> --pr <target_repo>")
    print("\nExamples:")
    print('  python main.py "Write a function to reverse a string"')
    print("  python main.py --github psf/requests 1")
    print("  python main.py --github psf/requests 1 --pr sivadharanG/agent-test-repo")


if __name__ == "__main__":
    print_banner()

    args = sys.argv[1:]

    if len(args) == 0:
        task = input("\nDescribe the coding task: ").strip()
        if not task:
            print("No task provided. Exiting.")
            sys.exit(1)
        run_agent(task)

    elif args[0] == "--github":
        if len(args) < 3:
            print_usage()
            sys.exit(1)

        repo_full_name = args[1]
        try:
            issue_number = int(args[2])
        except ValueError:
            print("Issue number must be an integer.")
            sys.exit(1)

        repo_for_pr = None
        if len(args) == 5 and args[3] == "--pr":
            repo_for_pr = args[4]

        print(f"\nFetching issue #{issue_number} from {repo_full_name}...")
        task = fetch_issue(repo_full_name, issue_number)
        run_agent(task, repo_for_pr=repo_for_pr)

    else:
        task = " ".join(args)
        run_agent(task)