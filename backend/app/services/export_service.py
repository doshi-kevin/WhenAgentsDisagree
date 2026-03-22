"""Export service for CSV/JSON data export."""
import csv
import io
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Debate, Turn, TurnMetrics, DebateAgent


async def export_debates_csv(db: AsyncSession, experiment_id: str = None) -> str:
    """Export debate data as CSV."""
    q = select(Debate).options(
        selectinload(Debate.agents),
        selectinload(Debate.turns).selectinload(Turn.metrics),
        selectinload(Debate.turns).selectinload(Turn.agent),
        selectinload(Debate.scenario),
    )
    if experiment_id:
        q = q.where(Debate.experiment_id == experiment_id)
    q = q.where(Debate.status == "completed")

    result = await db.execute(q)
    debates = list(result.scalars().unique().all())

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "debate_id", "scenario_title", "category", "strategy",
        "final_answer", "ground_truth", "is_correct",
        "total_tokens", "total_latency_ms", "total_turns",
        "deadlock_detected", "turn_number", "round_number",
        "agent_name", "provider", "model_id",
        "content", "confidence", "position_held", "position_changed",
        "aggressiveness", "sentiment", "persuasion_attempt",
        "citation_count", "semantic_similarity", "word_count",
    ])

    for debate in debates:
        scenario_title = debate.scenario.title if debate.scenario else ""
        category = debate.scenario.category if debate.scenario else ""

        for turn in debate.turns:
            agent = turn.agent
            metrics = turn.metrics

            writer.writerow([
                debate.id, scenario_title, category, debate.strategy,
                debate.final_answer, debate.scenario.ground_truth if debate.scenario else "",
                debate.is_correct,
                debate.total_tokens, debate.total_latency_ms, debate.total_turns,
                debate.deadlock_detected,
                turn.turn_number, turn.round_number,
                agent.agent_name if agent else "", agent.provider if agent else "",
                agent.model_id if agent else "",
                turn.content[:500], turn.confidence_score, turn.position_held,
                turn.position_changed,
                metrics.aggressiveness_score if metrics else "",
                metrics.sentiment_score if metrics else "",
                metrics.persuasion_attempt_score if metrics else "",
                metrics.citation_count if metrics else "",
                metrics.semantic_similarity_to_prev if metrics else "",
                metrics.word_count if metrics else "",
            ])

    return output.getvalue()


async def export_debates_json(db: AsyncSession, experiment_id: str = None) -> list:
    """Export debate data as JSON."""
    q = select(Debate).options(
        selectinload(Debate.agents),
        selectinload(Debate.turns).selectinload(Turn.metrics),
        selectinload(Debate.turns).selectinload(Turn.agent),
        selectinload(Debate.scenario),
    )
    if experiment_id:
        q = q.where(Debate.experiment_id == experiment_id)
    q = q.where(Debate.status == "completed")

    result = await db.execute(q)
    debates = list(result.scalars().unique().all())

    export = []
    for debate in debates:
        turns_data = []
        for turn in debate.turns:
            agent = turn.agent
            metrics = turn.metrics
            turns_data.append({
                "turn_number": turn.turn_number,
                "round_number": turn.round_number,
                "agent_name": agent.agent_name if agent else "",
                "provider": agent.provider if agent else "",
                "model_id": agent.model_id if agent else "",
                "content": turn.content,
                "confidence": turn.confidence_score,
                "position_held": turn.position_held,
                "position_changed": turn.position_changed,
                "change_reason": turn.change_reason,
                "tokens": turn.total_tokens,
                "latency_ms": turn.latency_ms,
                "metrics": {
                    "aggressiveness": metrics.aggressiveness_score if metrics else None,
                    "sentiment": metrics.sentiment_score if metrics else None,
                    "persuasion_attempt": metrics.persuasion_attempt_score if metrics else None,
                    "citation_count": metrics.citation_count if metrics else None,
                    "citation_quality": metrics.citation_quality_score if metrics else None,
                    "semantic_similarity": metrics.semantic_similarity_to_prev if metrics else None,
                    "novelty": metrics.argument_novelty_score if metrics else None,
                    "word_count": metrics.word_count if metrics else None,
                } if metrics else None,
            })

        export.append({
            "debate_id": debate.id,
            "scenario_title": debate.scenario.title if debate.scenario else "",
            "category": debate.scenario.category if debate.scenario else "",
            "strategy": debate.strategy,
            "final_answer": debate.final_answer,
            "ground_truth": debate.scenario.ground_truth if debate.scenario else "",
            "is_correct": debate.is_correct,
            "total_tokens": debate.total_tokens,
            "total_latency_ms": debate.total_latency_ms,
            "total_turns": debate.total_turns,
            "deadlock_detected": debate.deadlock_detected,
            "deadlock_resolution": debate.deadlock_resolution,
            "turns": turns_data,
        })

    return export
