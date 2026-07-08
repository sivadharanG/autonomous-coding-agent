import pytest
from agent.state import AgentState
from agent.nodes.coder import strip_markdown_fences
from agent.graph import route_after_critic


class TestStripMarkdownFences:
    """Tests for the defensive markdown-fence-stripping logic in coder.py"""

    def test_removes_python_fence(self):
        raw = "```python\ndef foo():\n    pass\n```"
        result = strip_markdown_fences(raw)
        assert result == "def foo():\n    pass"

    def test_removes_plain_fence(self):
        raw = "```\nprint('hello')\n```"
        result = strip_markdown_fences(raw)
        assert result == "print('hello')"

    def test_no_fence_unchanged(self):
        raw = "def foo():\n    pass"
        result = strip_markdown_fences(raw)
        assert result == "def foo():\n    pass"

    def test_strips_surrounding_whitespace(self):
        raw = "   \ndef foo():\n    pass\n   "
        result = strip_markdown_fences(raw)
        assert result == "def foo():\n    pass"


class TestRouteAfterCritic:
    """Tests for the conditional routing logic that drives the retry loop"""

    def _base_state(self, **overrides) -> AgentState:
        state = {
            "issue_description": "test task",
            "plan": ["step 1"],
            "current_code": "print('test')",
            "test_results": "test",
            "critic_feedback": None,
            "is_approved": False,
            "retry_count": 0,
            "max_retries": 3,
            "status": "new",
        }
        state.update(overrides)
        return state

    def test_approved_routes_to_end(self):
        state = self._base_state(is_approved=True)
        assert route_after_critic(state) == "end"

    def test_rejected_with_retries_left_routes_to_retry(self):
        state = self._base_state(is_approved=False, retry_count=1, max_retries=3)
        assert route_after_critic(state) == "retry"

    def test_rejected_at_max_retries_routes_to_end(self):
        state = self._base_state(is_approved=False, retry_count=3, max_retries=3)
        assert route_after_critic(state) == "end"

    def test_rejected_over_max_retries_routes_to_end(self):
        state = self._base_state(is_approved=False, retry_count=4, max_retries=3)
        assert route_after_critic(state) == "end"


class TestAgentStateSchema:
    """Sanity checks that the shared state dict has the expected shape"""

    def test_state_accepts_all_required_fields(self):
        state: AgentState = {
            "issue_description": "task",
            "plan": None,
            "current_code": None,
            "test_results": None,
            "critic_feedback": None,
            "is_approved": False,
            "retry_count": 0,
            "max_retries": 3,
            "status": "new",
        }
        assert state["status"] == "new"
        assert state["retry_count"] == 0
        assert state["is_approved"] is False