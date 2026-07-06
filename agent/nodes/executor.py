import os
import tempfile
import docker
from docker.errors import ContainerError, ImageNotFound, APIError
from agent.state import AgentState

PYTHON_IMAGE = "agent-sandbox:latest"
TIMEOUT_SECONDS = 15

client = docker.from_env(timeout=TIMEOUT_SECONDS)


def executor_node(state: AgentState) -> AgentState:
    """
    Runs state['current_code'] inside an isolated Docker container
    and captures the output. Updates state['test_results'] and state['status'].
    """
    code = state["current_code"]

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "solution.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            output = client.containers.run(
                image=PYTHON_IMAGE,
                command=["python", "/sandbox/solution.py"],
                volumes={tmpdir: {"bind": "/sandbox", "mode": "ro"}},
                network_disabled=True,
                mem_limit="128m",
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
            state["test_results"] = f"ERROR: Docker image '{PYTHON_IMAGE}' not found. Try pulling it manually."
            state["status"] = "executed_failure"

        except APIError as e:
            state["test_results"] = f"ERROR: Docker API error: {str(e)}"
            state["status"] = "executed_failure"

    return state