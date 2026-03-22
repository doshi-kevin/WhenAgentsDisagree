"""Structured Debate LangGraph workflow - multi-round argumentation."""
from langgraph.graph import StateGraph, END
from app.graphs.state import DebateState
from app.graphs.common_nodes import (
    create_agent_from_info, create_judge, get_collector,
    build_turn_record, format_conversation_history,
    check_answer_correctness, create_event, cleanup_collector,
)
from collections import Counter


async def initialize(state: DebateState) -> dict:
    """Initialize the structured debate."""
    return {
        "current_round": 1,
        "current_agent_index": 0,
        "is_resolved": False,
        "deadlock_detected": False,
        "events": [create_event("debate_start", {
            "debate_id": state["debate_id"],
            "strategy": "structured_debate",
            "agent_count": len(state["agents"]),
            "max_rounds": state["max_rounds"],
        })],
    }


async def agent_argue(state: DebateState) -> dict:
    """Have the current agent make an argument."""
    idx = state["current_agent_index"]
    agent_info = state["agents"][idx]
    agent = create_agent_from_info(agent_info)

    # Restore position from previous turns
    for turn in reversed(state.get("turns", [])):
        if turn["agent_id"] == agent_info["agent_id"] and turn.get("position_held"):
            agent.position = turn["position_held"]
            break

    collector = get_collector(state["debate_id"], state.get("deadlock_threshold", 0.90))
    history = format_conversation_history(state.get("turns", []))

    result = await agent.argue(
        question=state["question"],
        conversation_history=history,
        round_number=state["current_round"],
        max_rounds=state["max_rounds"],
    )

    parsed = result.get("parsed") or {}
    metrics = collector.compute_turn_metrics(
        agent_id=agent_info["agent_id"],
        agent_name=agent_info["name"],
        content=result["content"],
        parsed=parsed,
        source_type=agent_info.get("source_type", "unknown"),
    )

    turn_number = len(state.get("turns", [])) + 1
    turn = build_turn_record(
        agent_info, result, turn_number, state["current_round"], "argument", metrics
    )

    return {
        "turns": [turn],
        "current_agent_index": idx + 1,
        "events": [create_event("agent_turn", {
            "debate_id": state["debate_id"],
            "agent_name": agent_info["name"],
            "provider": agent_info["provider"],
            "model_id": agent_info["model_id"],
            "content": result["content"],
            "confidence": result.get("confidence", 0.5),
            "position": result.get("position_held", ""),
            "position_changed": result.get("position_changed", False),
            "round_number": state["current_round"],
            "metrics": metrics,
            "turn_number": turn_number,
        })],
    }


def should_continue_round(state: DebateState) -> str:
    """Check if more agents need to argue in this round."""
    if state["current_agent_index"] < len(state["agents"]):
        return "argue"
    return "evaluate"


async def evaluate_round(state: DebateState) -> dict:
    """Evaluate the round - forces all rounds to run for richer debate data.

    Only checks convergence/deadlock in the final round so we always get
    max_rounds × num_agents total messages (e.g. 5 rounds × 3 agents = 15).
    """
    collector = get_collector(state["debate_id"])
    turns = state.get("turns", [])
    current_round = state["current_round"]
    max_rounds = state["max_rounds"]

    # Get latest positions from this round
    round_turns = [t for t in turns if t["round_number"] == current_round]
    positions = [t.get("position_held", "").lower().strip() for t in round_turns if t.get("position_held")]

    # === FINAL ROUND: check convergence or go to judge ===
    if current_round >= max_rounds:
        # Check convergence (all agents agree)
        if positions and len(set(positions)) == 1:
            final_answer = positions[0]
            is_correct = check_answer_correctness(final_answer, state["ground_truth"])
            cleanup_collector(state["debate_id"])
            return {
                "final_answer": final_answer,
                "is_resolved": True,
                "is_correct": is_correct,
                "events": [create_event("debate_end", {
                    "debate_id": state["debate_id"],
                    "final_answer": final_answer,
                    "is_correct": is_correct,
                    "resolution_method": "convergence",
                    "rounds_taken": current_round,
                })],
            }

        # No convergence after all rounds → deadlock, send to judge
        return {
            "deadlock_detected": True,
            "deadlock_resolution": "max_rounds_reached",
            "events": [create_event("deadlock_warning", {
                "debate_id": state["debate_id"],
                "round": current_round,
                "details": f"Max rounds ({max_rounds}) reached without convergence",
            })],
        }

    # === MID-DEBATE: emit deadlock warnings but always continue ===
    events = []
    deadlock_info = collector.check_deadlock()
    if deadlock_info["is_deadlocked"] and current_round >= 3:
        events.append(create_event("deadlock_warning", {
            "debate_id": state["debate_id"],
            "round": current_round,
            "repeating_agents": deadlock_info["repeating_agents"],
            "details": f"Repetition detected in round {current_round}, continuing debate...",
        }))

    # Always continue to next round
    return {
        "current_round": current_round + 1,
        "current_agent_index": 0,
        "events": events,
    }


def should_resolve_or_continue(state: DebateState) -> str:
    """Decide whether to resolve or continue debating."""
    if state.get("is_resolved"):
        return "end"
    if state.get("deadlock_detected"):
        return "resolve_deadlock"
    return "argue"


async def resolve_deadlock(state: DebateState) -> dict:
    """Resolve a deadlocked debate using a judge agent."""
    judge = create_judge(state, name="Arbitrator")
    transcript = format_conversation_history(state.get("turns", []))

    collector = get_collector(state["debate_id"])
    deadlock_info = collector.check_deadlock()

    deadlock_details = f"Repeating agents: {', '.join(deadlock_info.get('repeating_agents', []))}\n"
    deadlock_details += f"Repetition counts: {deadlock_info.get('repetition_counts', {})}"

    result = await judge.resolve_deadlock(
        question=state["question"],
        transcript=transcript,
        deadlock_details=deadlock_details,
    )

    parsed = result.get("parsed") or {}
    final_answer = parsed.get("decision", "undetermined")
    resolution_method = parsed.get("resolution_method", "judge_arbitration")

    # Compute metrics for judge turn
    metrics = collector.compute_turn_metrics(
        agent_id="judge",
        agent_name="Arbitrator",
        content=result["content"],
        parsed=parsed,
    )

    turn_number = len(state.get("turns", [])) + 1
    judge_info = {
        "agent_id": "judge",
        "name": "Arbitrator",
        "provider": state["agents"][0]["provider"],
        "model_id": state["agents"][0]["model_id"],
        "role": "judge",
        "briefing": "",
        "source_type": "judge",
        "source_reliability": 1.0,
        "position": "",
    }

    turn = build_turn_record(judge_info, result, turn_number, state["current_round"], "final_decision", metrics)

    is_correct = check_answer_correctness(final_answer, state["ground_truth"])
    cleanup_collector(state["debate_id"])

    return {
        "turns": [turn],
        "final_answer": final_answer,
        "is_resolved": True,
        "is_correct": is_correct,
        "deadlock_resolution": resolution_method,
        "events": [
            create_event("agent_turn", {
                "debate_id": state["debate_id"],
                "agent_name": "Arbitrator",
                "content": result["content"],
                "role": "final_decision",
                "turn_number": turn_number,
            }),
            create_event("debate_end", {
                "debate_id": state["debate_id"],
                "final_answer": final_answer,
                "is_correct": is_correct,
                "resolution_method": f"deadlock_{resolution_method}",
                "rounds_taken": state["current_round"],
                "deadlock_detected": True,
            }),
        ],
    }


def build_debate_graph() -> StateGraph:
    """Build the structured debate LangGraph workflow."""
    graph = StateGraph(DebateState)

    graph.add_node("initialize", initialize)
    graph.add_node("agent_argue", agent_argue)
    graph.add_node("evaluate_round", evaluate_round)
    graph.add_node("resolve_deadlock", resolve_deadlock)

    graph.set_entry_point("initialize")
    graph.add_edge("initialize", "agent_argue")
    graph.add_conditional_edges("agent_argue", should_continue_round, {
        "argue": "agent_argue",
        "evaluate": "evaluate_round",
    })
    graph.add_conditional_edges("evaluate_round", should_resolve_or_continue, {
        "argue": "agent_argue",
        "resolve_deadlock": "resolve_deadlock",
        "end": END,
    })
    graph.add_edge("resolve_deadlock", END)

    return graph.compile()
