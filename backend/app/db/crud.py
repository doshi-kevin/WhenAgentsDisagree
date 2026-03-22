from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timezone

from app.db.models import (
    Experiment, Scenario, Debate, DebateAgent, Turn, TurnMetrics, ExperimentResult
)


# --- Scenarios ---
async def get_scenarios(db: AsyncSession, category: Optional[str] = None) -> list[Scenario]:
    q = select(Scenario)
    if category:
        q = q.where(Scenario.category == category)
    q = q.order_by(Scenario.created_at)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_scenario(db: AsyncSession, scenario_id: str) -> Optional[Scenario]:
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    return result.scalar_one_or_none()


async def create_scenario(db: AsyncSession, **kwargs) -> Scenario:
    scenario = Scenario(**kwargs)
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    return scenario


# --- Debates ---
async def get_debates(
    db: AsyncSession,
    experiment_id: Optional[str] = None,
    strategy: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> list[Debate]:
    q = select(Debate).options(selectinload(Debate.agents))
    if experiment_id:
        q = q.where(Debate.experiment_id == experiment_id)
    if strategy:
        q = q.where(Debate.strategy == strategy)
    if status:
        q = q.where(Debate.status == status)
    q = q.order_by(Debate.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().unique().all())


async def get_debate(db: AsyncSession, debate_id: str) -> Optional[Debate]:
    q = (
        select(Debate)
        .options(
            selectinload(Debate.agents),
            selectinload(Debate.turns).selectinload(Turn.metrics),
            selectinload(Debate.turns).selectinload(Turn.agent),
            selectinload(Debate.scenario),
        )
        .where(Debate.id == debate_id)
    )
    result = await db.execute(q)
    return result.scalar_one_or_none()


async def create_debate(db: AsyncSession, **kwargs) -> Debate:
    debate = Debate(**kwargs)
    db.add(debate)
    await db.commit()
    await db.refresh(debate)
    return debate


async def update_debate(db: AsyncSession, debate_id: str, **kwargs) -> Debate:
    result = await db.execute(select(Debate).where(Debate.id == debate_id))
    debate = result.scalar_one()
    for k, v in kwargs.items():
        setattr(debate, k, v)
    await db.commit()
    await db.refresh(debate)
    return debate


# --- Debate Agents ---
async def create_debate_agent(db: AsyncSession, **kwargs) -> DebateAgent:
    agent = DebateAgent(**kwargs)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


# --- Turns ---
async def create_turn(db: AsyncSession, **kwargs) -> Turn:
    turn = Turn(**kwargs)
    db.add(turn)
    await db.commit()
    await db.refresh(turn)
    return turn


async def create_turn_metrics(db: AsyncSession, **kwargs) -> TurnMetrics:
    metrics = TurnMetrics(**kwargs)
    db.add(metrics)
    await db.commit()
    await db.refresh(metrics)
    return metrics


# --- Experiments ---
async def get_experiments(db: AsyncSession) -> list[Experiment]:
    q = select(Experiment).order_by(Experiment.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_experiment(db: AsyncSession, experiment_id: str) -> Optional[Experiment]:
    q = (
        select(Experiment)
        .options(selectinload(Experiment.results))
        .where(Experiment.id == experiment_id)
    )
    result = await db.execute(q)
    return result.scalar_one_or_none()


async def create_experiment(db: AsyncSession, **kwargs) -> Experiment:
    experiment = Experiment(**kwargs)
    db.add(experiment)
    await db.commit()
    await db.refresh(experiment)
    return experiment


async def update_experiment(db: AsyncSession, experiment_id: str, **kwargs) -> Experiment:
    result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    exp = result.scalar_one()
    for k, v in kwargs.items():
        setattr(exp, k, v)
    await db.commit()
    await db.refresh(exp)
    return exp


# --- Admin Queries ---
async def get_overview_stats(db: AsyncSession) -> dict:
    debates = await db.execute(select(func.count(Debate.id)))
    total_debates = debates.scalar() or 0

    experiments = await db.execute(select(func.count(Experiment.id)))
    total_experiments = experiments.scalar() or 0

    scenarios = await db.execute(select(func.count(Scenario.id)))
    total_scenarios = scenarios.scalar() or 0

    completed = await db.execute(
        select(Debate).where(Debate.status == "completed")
    )
    completed_debates = list(completed.scalars().all())

    if completed_debates:
        correct = sum(1 for d in completed_debates if d.is_correct)
        avg_accuracy = correct / len(completed_debates)
        avg_latency = sum(d.total_latency_ms for d in completed_debates) / len(completed_debates)
        deadlocked = sum(1 for d in completed_debates if d.deadlock_detected)
        deadlock_rate = deadlocked / len(completed_debates)
    else:
        avg_accuracy = 0.0
        avg_latency = 0.0
        deadlock_rate = 0.0

    return {
        "total_debates": total_debates,
        "total_experiments": total_experiments,
        "avg_accuracy": round(avg_accuracy, 4),
        "avg_latency_ms": round(avg_latency, 2),
        "deadlock_rate": round(deadlock_rate, 4),
        "total_scenarios": total_scenarios,
    }


async def get_strategy_comparison(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Debate)
        .options(selectinload(Debate.turns).selectinload(Turn.metrics))
        .where(Debate.status == "completed")
    )
    debates = list(result.scalars().unique().all())

    strategy_data = {}
    for d in debates:
        s = d.strategy
        if s not in strategy_data:
            strategy_data[s] = {
                "strategy": s, "debates": [], "correct": 0,
                "total_latency": 0, "total_tokens": 0, "total_turns": 0,
                "deadlocks": 0, "confidences": [], "aggressiveness_scores": []
            }
        sd = strategy_data[s]
        sd["debates"].append(d)
        if d.is_correct:
            sd["correct"] += 1
        sd["total_latency"] += d.total_latency_ms
        sd["total_tokens"] += d.total_tokens
        sd["total_turns"] += d.total_turns
        if d.deadlock_detected:
            sd["deadlocks"] += 1
        for t in d.turns:
            if t.confidence_score is not None:
                sd["confidences"].append(t.confidence_score)
            if t.metrics and t.metrics.aggressiveness_score is not None:
                sd["aggressiveness_scores"].append(t.metrics.aggressiveness_score)

    results = []
    for s, sd in strategy_data.items():
        n = len(sd["debates"])
        results.append({
            "strategy": s,
            "total_debates": n,
            "accuracy": round(sd["correct"] / n, 4) if n else 0,
            "avg_latency_ms": round(sd["total_latency"] / n, 2) if n else 0,
            "avg_tokens": round(sd["total_tokens"] / n, 2) if n else 0,
            "avg_turns": round(sd["total_turns"] / n, 2) if n else 0,
            "deadlock_rate": round(sd["deadlocks"] / n, 4) if n else 0,
            "avg_confidence": round(sum(sd["confidences"]) / len(sd["confidences"]), 4) if sd["confidences"] else 0,
            "avg_aggressiveness": round(sum(sd["aggressiveness_scores"]) / len(sd["aggressiveness_scores"]), 4) if sd["aggressiveness_scores"] else 0,
        })
    return results


async def get_model_comparison(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Debate)
        .options(
            selectinload(Debate.agents),
            selectinload(Debate.turns).selectinload(Turn.metrics),
            selectinload(Debate.turns).selectinload(Turn.agent),
        )
        .where(Debate.status == "completed")
    )
    debates = list(result.scalars().unique().all())

    model_data = {}
    for d in debates:
        for agent in d.agents:
            key = f"{agent.provider}:{agent.model_id}"
            if key not in model_data:
                model_data[key] = {
                    "provider": agent.provider, "model_id": agent.model_id,
                    "debate_ids": set(), "correct_debates": set(),
                    "total_latency": 0, "total_tokens": 0, "turn_count": 0,
                    "confidences": [], "aggressiveness_scores": []
                }
            md = model_data[key]
            md["debate_ids"].add(d.id)
            if d.is_correct:
                md["correct_debates"].add(d.id)

            for t in d.turns:
                if t.debate_agent_id == agent.id:
                    md["total_latency"] += t.latency_ms
                    md["total_tokens"] += t.total_tokens
                    md["turn_count"] += 1
                    if t.confidence_score is not None:
                        md["confidences"].append(t.confidence_score)
                    if t.metrics and t.metrics.aggressiveness_score is not None:
                        md["aggressiveness_scores"].append(t.metrics.aggressiveness_score)

    results = []
    for key, md in model_data.items():
        n = len(md["debate_ids"])
        tc = md["turn_count"] or 1
        results.append({
            "provider": md["provider"],
            "model_id": md["model_id"],
            "total_debates": n,
            "accuracy": round(len(md["correct_debates"]) / n, 4) if n else 0,
            "avg_latency_ms": round(md["total_latency"] / tc, 2),
            "avg_tokens": round(md["total_tokens"] / tc, 2),
            "avg_confidence": round(sum(md["confidences"]) / len(md["confidences"]), 4) if md["confidences"] else 0,
            "avg_aggressiveness": round(sum(md["aggressiveness_scores"]) / len(md["aggressiveness_scores"]), 4) if md["aggressiveness_scores"] else 0,
        })
    return results
