"""Admin dashboard API endpoints."""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import io

from app.db.engine import get_db
from app.db import crud
from app.db.schemas import OverviewStats
from app.services.export_service import export_debates_csv, export_debates_json
from app.llm.model_registry import get_all_models_info
from app.llm.provider import rate_limiter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db)):
    stats = await crud.get_overview_stats(db)
    return stats


@router.get("/strategies/compare")
async def compare_strategies(db: AsyncSession = Depends(get_db)):
    return await crud.get_strategy_comparison(db)


@router.get("/models/compare")
async def compare_models(db: AsyncSession = Depends(get_db)):
    return await crud.get_model_comparison(db)


@router.get("/models/available")
async def get_available_models():
    return get_all_models_info()


@router.get("/models/health")
async def models_health():
    """Check rate limit status for all providers."""
    from app.llm.provider import PROVIDER_CONFIG
    health = []
    for provider, config in PROVIDER_CONFIG.items():
        for model_id in config["models"]:
            usage = rate_limiter.get_usage(provider, model_id)
            health.append(usage)
    return health


@router.get("/confidence/trajectories")
async def confidence_trajectories(
    debate_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get confidence trajectory data."""
    if debate_id:
        debate = await crud.get_debate(db, debate_id)
        if not debate:
            return []
        points = []
        for turn in debate.turns:
            points.append({
                "turn_number": turn.turn_number,
                "agent_name": turn.agent.agent_name if turn.agent else "",
                "provider": turn.agent.provider if turn.agent else "",
                "model_id": turn.agent.model_id if turn.agent else "",
                "confidence": turn.confidence_score or 0.5,
            })
        return points

    # Aggregate across all completed debates
    debates = await crud.get_debates(db, status="completed", limit=100)
    points = []
    for debate in debates:
        full = await crud.get_debate(db, debate.id)
        if full:
            for turn in full.turns:
                points.append({
                    "turn_number": turn.turn_number,
                    "agent_name": turn.agent.agent_name if turn.agent else "",
                    "provider": turn.agent.provider if turn.agent else "",
                    "model_id": turn.agent.model_id if turn.agent else "",
                    "confidence": turn.confidence_score or 0.5,
                    "strategy": full.strategy,
                })
    return points


@router.get("/aggressiveness/heatmap")
async def aggressiveness_heatmap(db: AsyncSession = Depends(get_db)):
    """Get aggressiveness heatmap data (model x strategy)."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.db.models import Debate, Turn, TurnMetrics, DebateAgent

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

    cells: dict[str, dict] = {}
    for d in debates:
        for agent in d.agents:
            key = f"{agent.model_id}:{d.strategy}"
            if key not in cells:
                cells[key] = {
                    "model_id": agent.model_id,
                    "strategy": d.strategy,
                    "scores": [],
                    "debate_count": 0,
                }
            cells[key]["debate_count"] += 1
            for t in d.turns:
                if t.debate_agent_id == agent.id and t.metrics:
                    cells[key]["scores"].append(t.metrics.aggressiveness_score)

    return [
        {
            "model_id": c["model_id"],
            "strategy": c["strategy"],
            "avg_aggressiveness": round(sum(c["scores"]) / len(c["scores"]), 4) if c["scores"] else 0,
            "debate_count": c["debate_count"],
        }
        for c in cells.values()
    ]


@router.get("/deadlocks/stats")
async def deadlock_stats(db: AsyncSession = Depends(get_db)):
    """Get deadlock frequency stats."""
    debates = await crud.get_debates(db, status="completed", limit=1000)
    strategy_stats: dict[str, dict] = {}
    for d in debates:
        s = d.strategy
        if s not in strategy_stats:
            strategy_stats[s] = {"total": 0, "deadlocked": 0}
        strategy_stats[s]["total"] += 1
        if d.deadlock_detected:
            strategy_stats[s]["deadlocked"] += 1

    return [
        {
            "strategy": s,
            "total_debates": data["total"],
            "deadlocked": data["deadlocked"],
            "deadlock_rate": round(data["deadlocked"] / data["total"], 4) if data["total"] else 0,
        }
        for s, data in strategy_stats.items()
    ]


@router.get("/export")
async def export_data(
    format: str = Query("json", pattern="^(json|csv)$"),
    experiment_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Export data in CSV or JSON format."""
    if format == "csv":
        csv_data = await export_debates_csv(db, experiment_id)
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=debates_export.csv"},
        )
    else:
        json_data = await export_debates_json(db, experiment_id)
        return json_data
