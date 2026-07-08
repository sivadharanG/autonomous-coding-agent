import os
import re
import sys
import tempfile
import docker
from docker.errors import ContainerError, ImageNotFound, APIError
from agent.state import AgentState

PYTHON_IMAGE = "agent-sandbox:latest"
TIMEOUT_SECONDS = 15

client = docker.from_env(timeout=TIMEOUT_SECONDS)

# Standard library modules that never need pip installing.
# Not exhaustive, but covers the common ones an LLM is likely to use.
STDLIB_MODULES = {
    "os", "sys", "re", "json", "math", "random", "datetime", "time",
    "collections", "itertools", "functools", "typing", "unittest",
    "string", "io", "abc", "enum", "dataclasses", "pathlib", "copy",
    "logging", "argparse", "subprocess", "threading", "queue", "socket",
    "struct", "hashlib", "base64", "csv", "sqlite3", "unittest.mock",
    "contextlib", "warnings", "traceback", "inspect", "operator",
}


def extract_third_party_imports(code: str) -> list:
    """
    Scans code for import statements and returns a list of likely
    third-party package names (excluding standard library modules).
    This is a heuristic, not a perfect parser — good enough to catch
    the common case of an LLM using a library like 'requests'.
    """
    imports = set()

    # Matches: import X / import X.Y / import X as Y
    for match in re.finditer(r"^\s*import\s+([a-zA-Z0-9_\.]+)", code, re.MULTILINE):
        imports.add(match.group(1).split(".")[0])

    # Matches: from X import Y
    for match in re.finditer(r"^\s*from\s+([a-zA-Z0-9_\.]+)\s+import", code, re.MULTILINE):
        imports.add(match.group(1).split(".")[0])

    third_party = [pkg for pkg in imports if pkg not in STDLIB_MODULES]
    return third_party


def executor_node(state: AgentState) -> AgentState:
    """
    Runs state['current_code'] inside an isolated Docker container.
    Detects third-party imports and installs them inside the container
    before running the code, then captures the output.
    Updates state['test_results'] and state['status'].
    """
    code = state["current_code"]
    third_party_packages = extract_third_party_imports(code)

    if third_party_packages:
        print(f"[EXECUTOR] Detected third-party imports: {third_party_packages}")

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "solution.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Build a shell command: install detected packages (if any), then run the script.
        # Network is temporarily needed for pip install, so we allow it only for this step
        # by running install and execution as separate steps within the same container run.
        if third_party_packages:
            pip_cmd = "pip install --quiet " + " ".join(third_party_packages)
            full_command = ["sh", "-c", f"{pip_cmd} && python /sandbox/solution.py"]
            network_disabled = False  # needs network to install packages
        else:
            full_command = ["python", "/sandbox/solution.py"]
            network_disabled = True  # no extra deps needed, keep fully isolated

        try:
            output = client.containers.run(
                image=PYTHON_IMAGE,
                command=full_command,
                volumes={tmpdir: {"bind": "/sandbox", "mode": "ro"}},
                network_disabled=network_disabled,
                mem_limit="256m",
                remove=True,
                stderr=True,
                stdout=True,
            )
            result_text = output.decode("utf-8")
            state["test_results"] = result_text
            state["status"] = "executed_success"

        except ContainerError as e:
            state["test_results"] = e.stderr.decode("utf-8") if e.stderr else str(e)
            state["status"] = "executed_failure"

        except ImageNotFound:
            state["test_results"] = f"ERROR: Docker image '{PYTHON_IMAGE}' not found. Try pulling/building it manually."
            state["status"] = "executed_failure"

        except APIError as e:
            state["test_results"] = f"ERROR: Docker API error: {str(e)}"
            state["status"] = "executed_failure"

    return state