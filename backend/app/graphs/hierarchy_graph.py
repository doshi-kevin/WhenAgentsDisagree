"""Hierarchical Authority LangGraph workflow."""
from langgraph.graph import StateGraph, END
from app.graphs.state import DebateState
from app.graphs.common_nodes import (
    create_agent_from_info, get_collector,
    build_turn_record, format_subordinate_briefs,
    check_answer_correctness, create_event, cleanup_collector,
)
from app.agents.judge_agent import JudgeAgent


async def initialize(state: DebateState) -> dict:
    """Initialize hierarchical debate."""
    return {
        "current_round": 1,
        "current_agent_index": 0,
        "is_resolved": False,
        "events": [create_event("debate_start", {
            "debate_id": state["debate_id"],
            "strategy": "hierarchical",
            "agent_count": len(state["agents"]),
        })],
    }


async def subordinate_brief(state: DebateState) -> dict:
    """Have a subordinate agent provide their brief."""
    # Subordinates are all agents except the last one (the lead)
    idx = state["current_agent_index"]
    subordinate_count = len(state["agents"]) - 1

    if idx >= subordinate_count:
        return {"current_agent_index": idx}

    agent_info = state["agents"][idx]
    agent = create_agent_from_info(agent_info)

    collector = get_collector(state["debate_id"], state.get("deadlock_threshold", 0.90))

    result = await agent.brief_subordinate(state["question"])

    turn_number = len(state.get("turns", [])) + 1

    if result.get("error"):
        error_turn = build_turn_record(agent_info, result, turn_number, 1, "argument", {})
        error_turn["error"] = result["error"]
        return {
            "turns": [error_turn],
            "current_agent_index": idx + 1,
            "events": [create_event("agent_error", {
                "debate_id": state["debate_id"],
                "agent_name": agent_info["name"],
                "provider": agent_info["provider"],
                "model_id": agent_info["model_id"],
                "error": result["error"],
                "turn_number": turn_number,
            })],
        }

    parsed = result.get("parsed") or {}

    metrics = collector.compute_turn_metrics(
        agent_id=agent_info["agent_id"],
        agent_name=agent_info["name"],
        content=result["content"],
        parsed=parsed,
        source_type=agent_info.get("source_type", "unknown"),
    )

    turn = build_turn_record(agent_info, result, turn_number, 1, "argument", metrics)

    return {
        "turns": [turn],
        "current_agent_index": idx + 1,
        "events": [create_event("agent_turn", {
            "debate_id": state["debate_id"],
            "agent_name": agent_info["name"],
            "provider": agent_info["provider"],
            "model_id": agent_info["model_id"],
            "content": result["content"],
            "role": "subordinate_brief",
            "confidence": result.get("confidence", 0.5),
            "turn_number": turn_number,
            "metrics": metrics,
        })],
    }


def should_continue_briefs(state: DebateState) -> str:
    """Check if more subordinates need to brief."""
    subordinate_count = len(state["agents"]) - 1
    if state["current_agent_index"] < subordinate_count:
        return "brief"
    return "lead_decision"


async def lead_decision(state: DebateState) -> dict:
    """Lead agent makes the final decision."""
    lead_info = state["agents"][-1]  # Last agent is the lead

    lead = JudgeAgent(
        agent_id=lead_info["agent_id"],
        name=lead_info["name"],
        provider=lead_info["provider"],
        model_id=lead_info["model_id"],
        role="lead",
    )

    collector = get_collector(state["debate_id"])
    briefs = format_subordinate_briefs(state.get("turns", []))

    result = await lead.lead_decision(
        question=state["question"],
        subordinate_briefs=briefs,
    )

    parsed = result.get("parsed") or {}
    final_answer = parsed.get("decision", "undetermined")

    metrics = collector.compute_turn_metrics(
        agent_id=lead_info["agent_id"],
        agent_name=lead_info["name"],
        content=result["content"],
        parsed=parsed,
    )

    turn_number = len(state.get("turns", [])) + 1
    turn = build_turn_record(lead_info, result, turn_number, 1, "final_decision", metrics)

    is_correct = check_answer_correctness(final_answer, state["ground_truth"])
    cleanup_collector(state["debate_id"])

    return {
        "turns": [turn],
        "final_answer": final_answer,
        "is_resolved": True,
        "is_correct": is_correct,
        "events": [
            create_event("agent_turn", {
                "debate_id": state["debate_id"],
                "agent_name": lead_info["name"],
                "content": result["content"],
                "role": "lead_decision",
                "confidence": result.get("confidence", 0.5),
                "turn_number": turn_number,
                "metrics": metrics,
                "most_persuasive": parsed.get("most_persuasive_subordinate"),
            }),
            create_event("debate_end", {
                "debate_id": state["debate_id"],
                "final_answer": final_answer,
                "is_correct": is_correct,
                "resolution_method": "hierarchical_authority",
            }),
        ],
    }


def build_hierarchy_graph() -> StateGraph:
    """Build the hierarchical authority LangGraph workflow."""
    graph = StateGraph(DebateState)

    graph.add_node("initialize", initialize)
    graph.add_node("subordinate_brief", subordinate_brief)
    graph.add_node("lead_decision", lead_decision)

    graph.set_entry_point("initialize")
    graph.add_edge("initialize", "subordinate_brief")
    graph.add_conditional_edges("subordinate_brief", should_continue_briefs, {
        "brief": "subordinate_brief",
        "lead_decision": "lead_decision",
    })
    graph.add_edge("lead_decision", END)

    return graph.compile()
