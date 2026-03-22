"""Cross-experiment aggregation utilities."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Debate, Turn, TurnMetrics, DebateAgent, ExperimentResult
from sqlalchemy.orm import selectinload


async def compute_experiment_results(db: AsyncSession, experiment_id: str) -> list[dict]:
    """Compute aggregated results for an experiment and store them."""
    result = await db.execute(
        select(Debate)
        .options(
            selectinload(Debate.agents),
            selectinload(Debate.turns).selectinload(Turn.metrics),
        )
        .where(Debate.experiment_id == experiment_id)
        .where(Debate.status == "completed")
    )
    debates = list(result.scalars().unique().all())

    # Group by (strategy, provider, model)
    groups: dict[str, dict] = {}
    for d in debates:
        for agent in d.agents:
            key = f"{d.strategy}:{agent.provider}:{agent.model_id}"
            if key not in groups:
                groups[key] = {
                    "strategy": d.strategy,
                    "provider": agent.provider,
                    "model_id": agent.model_id,
                    "debates": set(),
                    "correct": 0,
                    "total_latency": 0,
                    "total_tokens": 0,
                    "total_turns": 0,
                    "deadlocks": 0,
                    "confidences": [],
                    "aggressiveness_scores": [],
                }
            g = groups[key]
            if d.id not in g["debates"]:
                g["debates"].add(d.id)
                if d.is_correct:
                    g["correct"] += 1
                g["total_latency"] += d.total_latency_ms
                g["total_tokens"] += d.total_tokens
                g["total_turns"] += d.total_turns
                if d.deadlock_detected:
                    g["deadlocks"] += 1

            for t in d.turns:
                if t.debate_agent_id == agent.id:
                    if t.confidence_score is not None:
                        g["confidences"].append(t.confidence_score)
                    if t.metrics and t.metrics.aggressiveness_score is not None:
                        g["aggressiveness_scores"].append(t.metrics.aggressiveness_score)

    # Store results
    results = []
    for key, g in groups.items():
        n = len(g["debates"])
        if n == 0:
            continue

        exp_result = ExperimentResult(
            experiment_id=experiment_id,
            strategy=g["strategy"],
            provider=g["provider"],
            model_id=g["model_id"],
            total_debates=n,
            accuracy=round(g["correct"] / n, 4),
            avg_latency_ms=round(g["total_latency"] / n, 2),
            avg_tokens=round(g["total_tokens"] / n, 2),
            avg_turns=round(g["total_turns"] / n, 2),
            deadlock_rate=round(g["deadlocks"] / n, 4),
            avg_confidence=round(
                sum(g["confidences"]) / len(g["confidences"]), 4
            ) if g["confidences"] else 0.0,
            avg_aggressiveness=round(
                sum(g["aggressiveness_scores"]) / len(g["aggressiveness_scores"]), 4
            ) if g["aggressiveness_scores"] else 0.0,
        )
        db.add(exp_result)
        results.append(exp_result)

    await db.commit()
    return results
