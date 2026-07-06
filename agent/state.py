from typing import TypedDict, Optional


class AgentState(TypedDict):
    """
    Shared state object passed between all nodes in the LangGraph.
    Every node reads from this and returns updates to it.
    """

    # Input: the original task given to the agent
    issue_description: str

    # Set by the Planner node: list of steps to accomplish the task
    plan: Optional[list[str]]

    # Set by the Coder node: the current version of generated code
    current_code: Optional[str]

    # Set by the Executor node: output/errors from running the code
    test_results: Optional[str]

    # Set by the Critic node: feedback on whether the code is correct
    critic_feedback: Optional[str]

    # Whether the critic approved the code (True = done, False = retry)
    is_approved: bool

    # How many retry loops we've done — prevents infinite loops
    retry_count: int

    # Max retries allowed before giving up
    max_retries: int

    # Current stage of the pipeline (for debugging/logging)
    status: str