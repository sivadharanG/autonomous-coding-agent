import streamlit as st
from agent.graph import build_graph
from agent.github_client import fetch_issue, create_pull_request
from agent.logger import log_run

st.set_page_config(page_title="Autonomous AI Coding Agent", page_icon="🤖", layout="wide")

st.title("🤖 Autonomous AI Coding Agent")
st.caption("Plans, writes, executes, critiques, and self-corrects code — powered by LangGraph, Groq, and Docker sandboxing.")

# --- Input mode selection ---
mode = st.radio("Choose input mode:", ["Plain task description", "GitHub issue"], horizontal=True)

issue_description = None
repo_for_pr = None

if mode == "Plain task description":
    issue_description = st.text_area(
        "Describe the coding task:",
        placeholder="e.g. Write a function to check if a number is prime, with test cases",
        height=100,
    )

else:
    col1, col2 = st.columns(2)
    with col1:
        source_repo = st.text_input("Source repo (owner/repo)", placeholder="sivadharanG/agent-test-repo")
    with col2:
        issue_number = st.number_input("Issue number", min_value=1, step=1)

    open_pr = st.checkbox("Open a pull request when approved")
    if open_pr:
        repo_for_pr = st.text_input("Target repo for PR (owner/repo)", value=source_repo)

run_button = st.button("🚀 Run Agent", type="primary")

if run_button:
    # Resolve the task description
    if mode == "GitHub issue":
        if not source_repo or not issue_number:
            st.error("Please provide both a repo and issue number.")
            st.stop()
        with st.spinner(f"Fetching issue #{int(issue_number)} from {source_repo}..."):
            issue_description = fetch_issue(source_repo, int(issue_number))

    if not issue_description or not issue_description.strip():
        st.error("Please provide a task description.")
        st.stop()

    st.subheader("📋 Task")
    st.info(issue_description)

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

    with st.spinner("Running agent (planning → coding → executing → critiquing)..."):
        result = app.invoke(initial_state)

    # --- Results ---
    st.subheader("✅ Result" if result["is_approved"] else "❌ Result")

    col1, col2, col3 = st.columns(3)
    col1.metric("Status", result["status"])
    col2.metric("Approved", "Yes" if result["is_approved"] else "No")
    col3.metric("Retries used", f"{result['retry_count']} / {result['max_retries']}")

    st.subheader("🗺️ Plan")
    for i, step in enumerate(result["plan"], 1):
        st.markdown(f"**{i}.** {step}")

    st.subheader("💻 Final Code")
    st.code(result["current_code"], language="python")

    st.subheader("🧪 Execution Output")
    st.code(result["test_results"], language="text")

    pr_url = None

    if not result["is_approved"]:
        st.warning(f"Task was not fully approved. Last feedback: {result['critic_feedback']}")
    elif repo_for_pr:
        with st.spinner(f"Opening pull request on {repo_for_pr}..."):
            pr_url = create_pull_request(
                repo_full_name=repo_for_pr,
                code=result["current_code"],
                plan=result["plan"],
                test_results=result["test_results"],
                issue_description=issue_description,
            )
        st.success(f"Pull request created: {pr_url}")
        st.markdown(f"[🔗 View Pull Request]({pr_url})")

    log_run(issue_description, result, pr_url)
    st.caption("Run saved to logs/")