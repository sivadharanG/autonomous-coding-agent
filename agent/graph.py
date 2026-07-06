from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes.planner import planner_node
from agent.nodes.coder import coder_node
from agent.nodes.executor import executor_node
from agent.nodes.critic import critic_node


def route_after_critic(state: AgentState) -> str:
    """
    Conditional routing function: decides what happens after the Critic runs.
    - If approved -> END
    - If not approved but retries remain -> loop back to coder
    - If not approved and retries exhausted -> END anyway (give up gracefully)
    """
    if state["is_approved"]:
        return "end"

    if state["retry_count"] >= state["max_retries"]:
        state["status"] = "failed_max_retries"
        return "end"

    return "retry"


def build_graph():
    """
    Builds and compiles the LangGraph state machine.
    Flow: planner -> coder -> executor -> critic -> (loop back to coder OR end)
    This loop is what makes the system self-correcting/autonomous.
    """
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("coder", coder_node)
    graph.add_node("executor", executor_node)
    graph.add_node("critic", critic_node)

    graph.set_entry_point("planner")

    graph.add_edge("planner", "coder")
    graph.add_edge("coder", "executor")
    graph.add_edge("executor", "critic")

    # Conditional edge: critic decides whether to loop back or end
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "retry": "coder",
            "end": END,
        }
    )

    app = graph.compile()

    return app