# Autonomous AI Coding Agent

An autonomous, self-correcting AI agent that reads a coding task (or a real GitHub issue), plans a solution, writes code, executes it in an isolated Docker sandbox, critiques its own output, retries on failure, and — when approved — opens a real pull request with the fix.

Built as a final year project to explore agentic AI architectures using **LangGraph** for stateful multi-step orchestration, combined with sandboxed code execution and real developer-workflow integration (GitHub).

---

## Why this project

Most "AI coding tools" are single-turn: you ask, the model answers, and a human closes the loop — running the code, checking for errors, and deciding whether it's actually correct. This project removes the human from that loop.

The agent:
1. **Plans** the task into concrete steps
2. **Writes** code implementing the plan
3. **Executes** the code safely inside a sandboxed Docker container
4. **Critiques** its own output against the original task
5. **Retries** automatically with feedback if the critic rejects it
6. **Opens a pull request** once the code is verified correct

This turns the LLM from a text generator into one component inside a larger, engineered, self-correcting system.

---

## Architecture

```
                ┌─────────────┐
   Task/Issue ─▶│   Planner   │  Breaks task into ordered steps
                └──────┬──────┘
                       ▼
                ┌─────────────┐
          ┌────▶│    Coder    │  Writes code implementing the plan
          │     └──────┬──────┘  (uses prior critic feedback on retries)
          │            ▼
          │     ┌─────────────┐
          │     │  Executor   │  Runs code in an isolated Docker sandbox
          │     └──────┬──────┘  (no network, memory-capped, read-only mount)
          │            ▼
          │     ┌─────────────┐
          │     │   Critic    │  Judges correctness of code + output
          │     └──────┬──────┘
          │            │
          │     approved? ──── No ──── retries left? ── Yes ─┘
          │            │                      │
          │           Yes                     No
          │            │                      │
          │            ▼                      ▼
          │     ┌─────────────┐        ┌─────────────┐
          │     │ Open PR on  │        │  Fail with  │
          │     │  GitHub     │        │  feedback   │
          │     └─────────────┘        └─────────────┘
          │
          └── (loop back to Coder with critic_feedback in state)
```

All nodes communicate through a single shared **state object** (a `TypedDict`), which is the core LangGraph pattern: every node reads from and writes to this state rather than calling each other directly.

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent orchestration | LangGraph (StateGraph, conditional edges) |
| LLM inference | Groq API (LLaMA 3.3 70B Versatile) |
| Sandboxed execution | Docker (custom image with common dependencies) |
| GitHub integration | PyGithub (issue reading, branch/commit/PR creation) |
| Language | Python 3.11+ |
| Config/secrets | python-dotenv (`.env`) |

---

## Project Structure

```
autonomous-coding-agent/
├── agent/
│   ├── state.py          # Shared state schema (TypedDict)
│   ├── graph.py          # LangGraph wiring: nodes, edges, conditional routing
│   ├── github_client.py  # GitHub issue fetching + PR creation
│   ├── logger.py         # Saves each run's result to logs/
│   └── nodes/
│       ├── planner.py    # Breaks task into steps
│       ├── coder.py      # Generates code from the plan (+ retry feedback)
│       ├── executor.py   # Runs code in sandboxed Docker container
│       └── critic.py     # Evaluates correctness, decides approve/retry
├── sandbox/
│   └── Dockerfile         # Custom sandbox image (Python + common libs)
├── logs/                  # JSON logs of every run (gitignored)
├── scripts/                # Isolated test scripts for each node/graph
├── main.py                 # CLI entry point
├── requirements.txt
└── .env                    # API keys (not committed)
```

---

## Setup

### 1. Prerequisites
- Python 3.11+
- Docker Desktop (must be running before executing the agent)
- A [Groq API key](https://console.groq.com) (free tier)
- A [GitHub Personal Access Token](https://github.com/settings/tokens) with `repo` scope (only needed for GitHub issue/PR features)

### 2. Clone and set up the environment
```powershell
git clone <your-repo-url>
cd autonomous-coding-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_key_here
GITHUB_TOKEN=your_github_token_here
```

### 4. Build the sandbox image
```powershell
docker build -t agent-sandbox:latest sandbox/
```

### 5. Make sure Docker Desktop is running
The Executor node requires a live Docker engine. Open Docker Desktop and confirm with:
```powershell
docker ps
```

---

## Usage

### Run on a plain text task
```powershell
python main.py "Write a function to check if a number is prime, with test cases"
```

### Run on a real GitHub issue
```powershell
python main.py --github <owner/repo> <issue_number>
```
Example:
```powershell
python main.py --github psf/requests 1
```

### Run on a GitHub issue and open a PR with the fix
```powershell
python main.py --github <owner/repo> <issue_number> --pr <target_owner/target_repo>
```
Example:
```powershell
python main.py --github sivadharanG/agent-test-repo 1 --pr sivadharanG/agent-test-repo
```

Every run is automatically logged to `logs/run_<timestamp>.json`, containing the task, plan, generated code, execution output, critic feedback, approval status, retry count, and PR URL (if created).

---

## Key Design Decisions

**Why LangGraph over a simple prompt chain?**
A linear chain (prompt → response) has no way to loop back and retry based on evaluation. LangGraph's `StateGraph` with conditional edges allows the graph itself to decide, based on live state, whether to retry a node or terminate — which is what makes this an *agent* rather than a script.

**Why Docker sandboxing?**
Running LLM-generated code directly on the host machine is a real security risk — the model could write code that is destructive or unpredictable. The sandbox is configured with:
- `network_disabled=True` — no outbound network access
- `mem_limit="128m"` — prevents runaway resource usage
- Read-only volume mount — the container cannot modify the host filesystem
- `remove=True` — containers are destroyed immediately after execution

**Why Groq (LLaMA 3.3 70B) instead of a paid API?**
The project is architecture-agnostic with respect to the LLM provider — swapping in Claude or GPT-4 would require changing only the client initialization inside each node. Groq was chosen for its free tier and fast inference, which suited iterative development and testing without ongoing cost. Model choice is a deployment detail, not a structural dependency.

**Fail-safe defaults**
If the Critic's LLM response fails to parse as valid JSON, the system defaults to `approved = False` rather than `True` — a deliberate "fail closed" choice so that malformed evaluation output never silently lets bad code through.

---

## Known Limitations

- **Network-disabled sandbox**: Tasks requiring live HTTP calls (e.g., testing an API client) cannot be fully execution-verified, since the sandbox has no network access. The Critic can still reason about correctness from the traceback context, but true end-to-end network testing would require a more permissive (and less safe) sandbox mode.
- **Single-file scope**: The agent currently generates and tests a single Python file/function per task. It does not yet handle multi-file changes across an existing codebase.
- **Sandbox dependencies**: The custom Docker image (`agent-sandbox`) only pre-installs a small set of common libraries (`requests`, `pytest`). Tasks requiring other third-party packages will fail at execution unless the image is extended.
- **LLM non-determinism**: Because generation is LLM-based, code quality and whether a retry is triggered can vary between runs on the same task.

---

## Future Work

- Dynamic dependency detection and installation inside the sandbox before execution
- Multi-file / whole-repository context awareness
- Support for a permissive, rate-limited sandbox mode for network-dependent tasks
- Web dashboard to browse run history from `logs/` instead of raw JSON
- Support for alternate LLM providers (Claude, GPT-4) as a configurable option

---

## Author

Sivadharan G — B.Sc. AI & Machine Learning, VLB Janakiammal College of Arts and Science
[GitHub](https://github.com/sivadharanG) · [LinkedIn](https://linkedin.com/in/sivadharang)
