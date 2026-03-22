"""Majority Voting LangGraph workflow."""
from langgraph.graph import StateGraph, END
from app.graphs.state import DebateState
from app.graphs.common_nodes import (
    create_agent_from_info, create_judge, get_collector,
    build_turn_record, check_answer_correctness, create_event, cleanup_collector,
)
from collections import Counter


async def initialize(state: DebateState) -> dict:
    """Initialize the voting debate."""
    return {
        "current_round": 1,
        "current_agent_index": 0,
        "votes": {},
        "is_resolved": False,
        "events": [create_event("debate_start", {
            "debate_id": state["debate_id"],
            "strategy": "majority_voting",
            "agent_count": len(state["agents"]),
        })],
    }


async def agent_vote(state: DebateState) -> dict:
    """Have the current agent cast a vote."""
    idx = state["current_agent_index"]
    agent_info = state["agents"][idx]
    agent = create_agent_from_info(agent_info)

    collector = get_collector(state["debate_id"], state.get("deadlock_threshold", 0.90))

    # Agent votes
    result = await agent.vote(state["question"])
    parsed = result.get("parsed") or {}

    # Compute metrics
    metrics = collector.compute_turn_metrics(
        agent_id=agent_info["agent_id"],
        agent_name=agent_info["name"],
        content=result["content"],
        parsed=parsed,
        source_type=agent_info.get("source_type", "unknown"),
    )

    turn_number = len(state.get("turns", [])) + 1
    turn = build_turn_record(agent_info, result, turn_number, 1, "vote", metrics)

    # Record vote
    vote = parsed.get("vote", "").strip()
    votes = dict(state.get("votes", {}))
    votes[agent_info["agent_id"]] = vote

    return {
        "turns": [turn],
        "votes": votes,
        "current_agent_index": idx + 1,
        "events": [create_event("agent_turn", {
            "debate_id": state["debate_id"],
            "agent_name": agent_info["name"],
            "provider": agent_info["provider"],
            "model_id": agent_info["model_id"],
            "content": result["content"],
            "vote": vote,
            "confidence": result.get("confidence", 0.5),
            "metrics": metrics,
            "turn_number": turn_number,
        })],
    }


def should_continue_voting(state: DebateState) -> str:
    """Check if more agents need to vote."""
    if state["current_agent_index"] < len(state["agents"]):
        return "vote"
    return "tally"


async def tally_votes(state: DebateState) -> dict:
    """Tally votes and determine winner."""
    votes = state.get("votes", {})
    vote_values = [v.lower().strip() for v in votes.values() if v]

    if not vote_values:
        return {
            "final_answer": "No votes cast",
            "is_resolved": True,
            "is_correct": False,
            "events": [create_event("debate_end", {
                "debate_id": state["debate_id"],
                "final_answer": "No votes cast",
                "is_correct": False,
                "resolution_method": "no_votes",
            })],
        }

    counter = Counter(vote_values)
    most_common = counter.most_common()

    # Check for clear majority
    if len(most_common) == 1 or most_common[0][1] > most_common[1][1]:
        winner = most_common[0][0]
        is_correct = check_answer_correctness(winner, state["ground_truth"])

        cleanup_collector(state["debate_id"])
        return {
            "final_answer": winner,
            "is_resolved": True,
            "is_correct": is_correct,
            "events": [create_event("debate_end", {
                "debate_id": state["debate_id"],
                "final_answer": winner,
                "is_correct": is_correct,
                "vote_counts": dict(counter),
                "resolution_method": "majority_vote",
            })],
        }

    # Tie - use confidence to break
    tied_positions = [pos for pos, count in most_common if count == most_common[0][1]]
    best_confidence = -1
    winner = tied_positions[0]

    for turn in state.get("turns", []):
        pos = (turn.get("position_held") or "").lower().strip()
        if pos in tied_positions:
            conf = turn.get("confidence", 0)
            if conf > best_confidence:
                best_confidence = conf
                winner = pos

    is_correct = check_answer_correctness(winner, state["ground_truth"])
    cleanup_collector(state["debate_id"])

    return {
        "final_answer": winner,
        "is_resolved": True,
        "is_correct": is_correct,
        "events": [create_event("debate_end", {
            "debate_id": state["debate_id"],
            "final_answer": winner,
            "is_correct": is_correct,
            "vote_counts": dict(counter),
            "resolution_method": "confidence_tiebreak",
        })],
    }


def build_voting_graph() -> StateGraph:
    """Build the majority voting LangGraph workflow."""
    graph = StateGraph(DebateState)

    graph.add_node("initialize", initialize)
    graph.add_node("agent_vote", agent_vote)
    graph.add_node("tally_votes", tally_votes)

    graph.set_entry_point("initialize")
    graph.add_edge("initialize", "agent_vote")
    graph.add_conditional_edges("agent_vote", should_continue_voting, {
        "vote": "agent_vote",
        "tally": "tally_votes",
    })
    graph.add_edge("tally_votes", END)

    return graph.compile()
