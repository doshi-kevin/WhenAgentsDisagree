"""Debate lifecycle management and SSE pub/sub."""
import asyncio
import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.db.models import Debate, DebateAgent, Turn, TurnMetrics
from app.graphs.state import DebateState, AgentInfo
from app.graphs.voting_graph import build_voting_graph
from app.graphs.debate_graph import build_debate_graph
from app.graphs.hierarchy_graph import build_hierarchy_graph
from app.graphs.evidence_graph import build_evidence_graph
from app.config import settings


# SSE subscribers per debate
_subscribers: dict[str, list[asyncio.Queue]] = {}


def subscribe(debate_id: str) -> asyncio.Queue:
    """Subscribe to debate events."""
    queue: asyncio.Queue = asyncio.Queue()
    if debate_id not in _subscribers:
        _subscribers[debate_id] = []
    _subscribers[debate_id].append(queue)
    return queue


def unsubscribe(debate_id: str, queue: asyncio.Queue):
    """Unsubscribe from debate events."""
    if debate_id in _subscribers:
        _subscribers[debate_id] = [q for q in _subscribers[debate_id] if q is not queue]
        if not _subscribers[debate_id]:
            del _subscribers[debate_id]


async def publish_event(debate_id: str, event: dict):
    """Publish an event to all subscribers."""
    if debate_id in _subscribers:
        for queue in _subscribers[debate_id]:
            await queue.put(event)


STRATEGY_BUILDERS = {
    "majority_voting": build_voting_graph,
    "structured_debate": build_debate_graph,
    "hierarchical": build_hierarchy_graph,
    "evidence_weighted": build_evidence_graph,
}


async def run_debate(
    db: AsyncSession,
    debate_id: str,
    scenario_id: str,
    strategy: str,
    agent_configs: list[dict],
    experiment_id: Optional[str] = None,
    max_rounds: int = 3,
) -> dict:
    """Run a complete debate and store results."""
    # Get scenario
    scenario = await crud.get_scenario(db, scenario_id)
    if not scenario:
        raise ValueError(f"Scenario not found: {scenario_id}")

    # Update debate status
    await crud.update_debate(db, debate_id, status="running", started_at=datetime.now(timezone.utc))

    # Create debate agents in DB
    agents_info = []
    for i, config in enumerate(agent_configs):
        briefing_idx = config.get("briefing_index")
        if briefing_idx is None:
            briefing_idx = i  # Auto-assign: agent 0→briefing 0, agent 1→briefing 1, etc.
        briefings = scenario.agent_briefings
        briefing_data = briefings[briefing_idx] if briefing_idx < len(briefings) else briefings[i % len(briefings)]

        db_agent = await crud.create_debate_agent(
            db,
            debate_id=debate_id,
            agent_name=config["agent_name"],
            provider=config["provider"],
            model_id=config["model_id"],
            role=config.get("role", "advocate"),
            assigned_position=briefing_data.get("position", ""),
            briefing_index=briefing_idx,
        )

        agents_info.append(AgentInfo(
            agent_id=db_agent.id,
            name=config["agent_name"],
            provider=config["provider"],
            model_id=config["model_id"],
            role=config.get("role", "advocate"),
            briefing=briefing_data.get("briefing", ""),
            source_type=briefing_data.get("source_type", "unknown"),
            source_reliability=briefing_data.get("source_reliability", 0.5),
            position=briefing_data.get("position", ""),
        ))

    # Build initial state
    initial_state: DebateState = {
        "debate_id": debate_id,
        "scenario_id": scenario_id,
        "strategy": strategy,
        "question": scenario.question,
        "ground_truth": scenario.ground_truth,
        "max_rounds": max_rounds,
        "deadlock_threshold": settings.deadlock_similarity_threshold,
        "agents": agents_info,
        "turns": [],
        "current_round": 1,
        "current_agent_index": 0,
        "votes": {},
        "source_rankings": {},
        "final_answer": "",
        "is_resolved": False,
        "is_correct": None,
        "deadlock_detected": False,
        "deadlock_resolution": "",
        "events": [],
        "error": None,
    }

    # Get the right graph
    builder = STRATEGY_BUILDERS.get(strategy)
    if not builder:
        raise ValueError(f"Unknown strategy: {strategy}")

    graph = builder()

    try:
        # Run the graph
        final_state = await graph.ainvoke(initial_state)

        # Publish all events
        for event in final_state.get("events", []):
            await publish_event(debate_id, event)

        # Store turns and metrics in DB
        total_tokens = 0
        total_latency = 0
        for turn_data in final_state.get("turns", []):
            db_turn = await crud.create_turn(
                db,
                debate_id=debate_id,
                debate_agent_id=turn_data["agent_id"],
                turn_number=turn_data["turn_number"],
                round_number=turn_data["round_number"],
                role=turn_data["role"],
                content=turn_data["content"],
                reasoning=turn_data.get("parsed", {}).get("reasoning") if turn_data.get("parsed") else None,
                confidence_score=turn_data.get("confidence", 0.5),
                position_held=turn_data.get("position_held", ""),
                position_changed=turn_data.get("position_changed", False),
                change_reason=turn_data.get("change_reason"),
                prompt_tokens=turn_data.get("prompt_tokens", 0),
                completion_tokens=turn_data.get("completion_tokens", 0),
                total_tokens=turn_data.get("total_tokens", 0),
                latency_ms=turn_data.get("latency_ms", 0),
                raw_response_json=turn_data.get("raw_response") if isinstance(turn_data.get("raw_response"), dict) else None,
            )

            total_tokens += turn_data.get("total_tokens", 0)
            total_latency += turn_data.get("latency_ms", 0)

            # Store metrics
            metrics = turn_data.get("metrics", {})
            if metrics:
                await crud.create_turn_metrics(
                    db,
                    turn_id=db_turn.id,
                    aggressiveness_score=metrics.get("aggressiveness_score", 0),
                    sentiment_score=metrics.get("sentiment_score", 0),
                    persuasion_attempt_score=metrics.get("persuasion_attempt_score", 0),
                    citation_count=metrics.get("citation_count", 0),
                    citation_quality_score=metrics.get("citation_quality_score", 0),
                    semantic_similarity_to_prev=metrics.get("semantic_similarity_to_prev"),
                    argument_novelty_score=metrics.get("argument_novelty_score"),
                    word_count=metrics.get("word_count", 0),
                    hedging_language_count=metrics.get("hedging_language_count", 0),
                )

        # Update debate with results
        status = "completed"
        if final_state.get("deadlock_detected"):
            status = "completed"  # Still completed, but with deadlock

        await crud.update_debate(
            db,
            debate_id=debate_id,
            status=status,
            final_answer=final_state.get("final_answer", ""),
            is_correct=final_state.get("is_correct", False),
            total_tokens=total_tokens,
            total_latency_ms=total_latency,
            total_turns=len(final_state.get("turns", [])),
            deadlock_detected=final_state.get("deadlock_detected", False),
            deadlock_resolution=final_state.get("deadlock_resolution", ""),
            completed_at=datetime.now(timezone.utc),
        )

        return {
            "debate_id": debate_id,
            "status": status,
            "final_answer": final_state.get("final_answer", ""),
            "is_correct": final_state.get("is_correct", False),
            "total_turns": len(final_state.get("turns", [])),
            "total_tokens": total_tokens,
            "total_latency_ms": total_latency,
            "deadlock_detected": final_state.get("deadlock_detected", False),
        }

    except Exception as e:
        await crud.update_debate(
            db, debate_id=debate_id,
            status="failed",
            completed_at=datetime.now(timezone.utc),
        )
        await publish_event(debate_id, {
            "type": "error",
            "data": {"error": str(e)},
        })
        raise
