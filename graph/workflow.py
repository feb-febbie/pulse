"""
LangGraph StateGraph for PulseCare.

Routing:
  companion_node → [conditional] → analyst_node → END
                               → END (when no significant signal logged)

The conditional router keeps LLM costs low: AnalystAgent only runs when
CompanionAgent detected a meaningful health signal (symptoms or severity ≥ 5).
This is the architecture that makes per-user costs stay near $0.10/month.
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from agents.companion import companion_node
from agents.analyst import analyst_node
from graph.state import HealthState


def _route_after_companion(state: HealthState) -> str:
    """Route to analyst only when a significant signal was logged."""
    if state.get("route_to_analyst"):
        return "analyst"
    return END


def build_graph():
    g = StateGraph(HealthState)

    g.add_node("companion", companion_node)
    g.add_node("analyst", analyst_node)

    g.set_entry_point("companion")

    g.add_conditional_edges(
        "companion",
        _route_after_companion,
        {"analyst": "analyst", END: END},
    )
    g.add_edge("analyst", END)

    return g.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
