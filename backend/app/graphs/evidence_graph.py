"""Evidence-Weighted Consensus LangGraph workflow."""
import json
from langgraph.graph import StateGraph, END
from app.graphs.state import DebateState
from app.graphs.common_nodes import (
    create_agent_from_info, get_collector,
    build_turn_record, check_answer_correctness,
    create_event, cleanup_collector,
)
from collections import Counter


async def initialize(state: DebateState) -> dict:
    """Initialize evidence-weighted debate."""
    return {
        "current_round": 1,
        "current_agent_index": 0,
        "source_rankings": {},
        "votes": {},
        "is_resolved": False,
        "events": [create_event("debate_start", {
            "debate_id": state["debate_id"],
            "strategy": "evidence_weighted",
            "agent_count": len(state["agents"]),
        })],
    }


def format_all_sources(agents: list) -> str:
    """Format all agent sources for ranking."""
    lines = []
    for i, agent in enumerate(agents):
        lines.append(f"**Source {chr(65+i)} ({agent['name']}):**")
        lines.append(f"Type: {agent.get('source_type', 'unknown')}")
        lines.append(f"Content: {agent.get('briefing', '')}")
        lines.append("")
    return "\n".join(lines)


async def rank_sources(state: DebateState) -> dict:
    """Have the current agent rank all sources."""
    idx = state["current_agent_index"]
    agent_info = state["agents"][idx]
    agent = create_agent_from_info(agent_info)

    collector = get_collector(state["debate_id"], state.get("deadlock_threshold", 0.90))
    all_sources = format_all_sources(state["agents"])

    result = await agent.rank_sources(
        question=state["question"],
        all_sources=all_sources,
    )

    turn_number = len(state.get("turns", [])) + 1

    if result.get("error"):
        error_turn = build_turn_record(agent_info, result, turn_number, 1, "evaluation", {})
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

    turn = build_turn_record(agent_info, result, turn_number, 1, "evaluation", metrics)

    # Store rankings
    rankings = dict(state.get("source_rankings", {}))
    rankings[agent_info["agent_id"]] = parsed.get("rankings", [])

    return {
        "turns": [turn],
        "source_rankings": rankings,
        "current_agent_index": idx + 1,
        "events": [create_event("agent_turn", {
            "debate_id": state["debate_id"],
            "agent_name": agent_info["name"],
            "content": result["content"],
            "role": "source_ranking",
            "confidence": result.get("confidence", 0.5),
            "turn_number": turn_number,
            "metrics": metrics,
        })],
    }


def should_continue_ranking(state: DebateState) -> str:
    """Check if more agents need to rank sources."""
    if state["current_agent_index"] < len(state["agents"]):
        return "rank"
    return "compute_weights"


async def compute_consensus_weights(state: DebateState) -> dict:
    """Compute consensus weights from all agent rankings."""
    all_rankings = state.get("source_rankings", {})

    # Aggregate reliability scores per source
    source_scores: dict[str, list[float]] = {}
    for agent_id, rankings in all_rankings.items():
        if isinstance(rankings, list):
            for r in rankings:
                if isinstance(r, dict):
                    source_id = r.get("source_id", "")
                    score = r.get("reliability_score", 0.5)
                    if source_id:
                        source_scores.setdefault(source_id, []).append(score)

    # Compute average per source
    consensus = {}
    for source_id, scores in source_scores.items():
        consensus[source_id] = round(sum(scores) / len(scores), 4) if scores else 0.5

    return {
        "current_round": 2,
        "current_agent_index": 0,
        "source_rankings": {"consensus": consensus, **all_rankings},
        "events": [create_event("metrics_update", {
            "debate_id": state["debate_id"],
            "consensus_weights": consensus,
            "phase": "weights_computed",
        })],
    }


async def weighted_vote(state: DebateState) -> dict:
    """Have agents make weighted arguments and vote."""
    idx = state["current_agent_index"]
    agent_info = state["agents"][idx]
    agent = create_agent_from_info(agent_info)

    collector = get_collector(state["debate_id"])
    consensus = state.get("source_rankings", {}).get("consensus", {})
    rankings_str = json.dumps(consensus, indent=2)

    # Restore position
    for turn in reversed(state.get("turns", [])):
        if turn["agent_id"] == agent_info["agent_id"] and turn.get("position_held"):
            agent.position = turn["position_held"]
            break

    result = await agent.weighted_argue(
        question=state["question"],
        source_rankings=rankings_str,
        conversation_history="",
    )

    turn_number = len(state.get("turns", [])) + 1

    if result.get("error"):
        error_turn = build_turn_record(agent_info, result, turn_number, 2, "vote", {})
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

    turn = build_turn_record(agent_info, result, turn_number, 2, "vote", metrics)

    # Record vote with evidence weight
    votes = dict(state.get("votes", {}))
    vote = parsed.get("vote", "").strip()
    evidence_weight = parsed.get("evidence_weight_total", 0.5)
    votes[agent_info["agent_id"]] = {"vote": vote, "weight": evidence_weight}

    return {
        "turns": [turn],
        "votes": votes,
        "current_agent_index": idx + 1,
        "events": [create_event("agent_turn", {
            "debate_id": state["debate_id"],
            "agent_name": agent_info["name"],
            "content": result["content"],
            "role": "weighted_vote",
            "vote": vote,
            "evidence_weight": evidence_weight,
            "confidence": result.get("confidence", 0.5),
            "turn_number": turn_number,
            "metrics": metrics,
        })],
    }


def should_continue_voting(state: DebateState) -> str:
    """Check if more agents need to vote."""
    if state["current_agent_index"] < len(state["agents"]):
        return "vote"
    return "resolve"


async def resolve(state: DebateState) -> dict:
    """Resolve using evidence-weighted votes."""
    votes = state.get("votes", {})

    # Aggregate weighted votes per position
    position_weights: dict[str, float] = {}
    for agent_id, vote_data in votes.items():
        if isinstance(vote_data, dict):
            pos = vote_data.get("vote", "").lower().strip()
            weight = vote_data.get("weight", 0.5)
        else:
            pos = str(vote_data).lower().strip()
            weight = 0.5

        if pos:
            position_weights[pos] = position_weights.get(pos, 0) + weight

    # Winner is the position with highest total evidence weight
    if position_weights:
        winner = max(position_weights, key=position_weights.get)
    else:
        winner = "undetermined"

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
            "resolution_method": "evidence_weighted_consensus",
            "position_weights": position_weights,
        })],
    }


def build_evidence_graph() -> StateGraph:
    """Build the evidence-weighted consensus LangGraph workflow."""
    graph = StateGraph(DebateState)

    graph.add_node("initialize", initialize)
    graph.add_node("rank_sources", rank_sources)
    graph.add_node("compute_consensus_weights", compute_consensus_weights)
    graph.add_node("weighted_vote", weighted_vote)
    graph.add_node("resolve", resolve)

    graph.set_entry_point("initialize")
    graph.add_edge("initialize", "rank_sources")
    graph.add_conditional_edges("rank_sources", should_continue_ranking, {
        "rank": "rank_sources",
        "compute_weights": "compute_consensus_weights",
    })
    graph.add_edge("compute_consensus_weights", "weighted_vote")
    graph.add_conditional_edges("weighted_vote", should_continue_voting, {
        "vote": "weighted_vote",
        "resolve": "resolve",
    })
    graph.add_edge("resolve", END)

    return graph.compile()
