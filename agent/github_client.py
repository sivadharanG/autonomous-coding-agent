from dotenv import load_dotenv
load_dotenv()

import os
import time
from github import Github, Auth


def get_github_client():
    """
    Returns an authenticated PyGithub client using the token from .env.
    """
    token = os.environ.get("GITHUB_TOKEN")
    auth = Auth.Token(token)
    return Github(auth=auth)


def fetch_issue(repo_full_name: str, issue_number: int) -> str:
    """
    Fetches a GitHub issue's title + body and returns it as a single
    task description string the agent can use as input.
    """
    client = get_github_client()
    repo = client.get_repo(repo_full_name)
    issue = repo.get_issue(number=issue_number)

    task_description = f"{issue.title}\n\n{issue.body or ''}"
    return task_description.strip()


def create_pull_request(
    repo_full_name: str,
    code: str,
    plan: list,
    test_results: str,
    issue_description: str,
    file_path: str = "agent_generated_solution.py",
    base_branch: str = "main",
) -> str:
    """
    Creates a new branch, commits the generated code, and opens a PR.

    Args:
        repo_full_name (str): e.g. "sivadharanG/agent-test-repo"
        code (str): the final generated code to commit
        plan (list): list of plan steps (for PR description)
        test_results (str): execution output (for PR description)
        issue_description (str): original task description
        file_path (str): where to save the code in the repo
        base_branch (str): branch to open the PR against

    Returns:
        str: URL of the created pull request
    """
    client = get_github_client()
    repo = client.get_repo(repo_full_name)

    # Create a unique branch name using a timestamp
    branch_name = f"agent-fix-{int(time.time())}"

    # Get the latest commit SHA on the base branch to branch from
    base_ref = repo.get_git_ref(f"heads/{base_branch}")
    base_sha = base_ref.object.sha

    # Create the new branch
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_sha)

    # Commit the generated code to the new branch
    repo.create_file(
        path=file_path,
        message="Add agent-generated solution",
        content=code,
        branch=branch_name,
    )

    # Build a descriptive PR body
    plan_text = "\n".join(f"- {step}" for step in plan)
    pr_body = f"""## Task
{issue_description}

## Plan
{plan_text}

## Execution Output
---
*This PR was generated automatically by an autonomous AI coding agent.*
"""

    pr = repo.create_pull(
        title="Automated fix from AI coding agent",
        body=pr_body,
        head=branch_name,
        base=base_branch,
    )

    return pr.html_url