"""Experiment API endpoints."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db, async_session
from app.db import crud
from app.db.schemas import ExperimentCreate
from app.services.experiment_runner import run_experiment

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("")
async def list_experiments(db: AsyncSession = Depends(get_db)):
    experiments = await crud.get_experiments(db)
    results = []
    for exp in experiments:
        results.append({
            "id": exp.id,
            "name": exp.name,
            "description": exp.description,
            "status": exp.status,
            "created_at": exp.created_at,
            "completed_at": exp.completed_at,
        })
    return results


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: str, db: AsyncSession = Depends(get_db)):
    exp = await crud.get_experiment(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    debates = await crud.get_debates(db, experiment_id=experiment_id)

    return {
        "id": exp.id,
        "name": exp.name,
        "description": exp.description,
        "status": exp.status,
        "created_at": exp.created_at,
        "completed_at": exp.completed_at,
        "debate_count": len(debates),
        "results": [
            {
                "strategy": r.strategy,
                "provider": r.provider,
                "model_id": r.model_id,
                "total_debates": r.total_debates,
                "accuracy": r.accuracy,
                "avg_latency_ms": r.avg_latency_ms,
                "avg_tokens": r.avg_tokens,
                "avg_turns": r.avg_turns,
                "deadlock_rate": r.deadlock_rate,
                "avg_confidence": r.avg_confidence,
                "avg_aggressiveness": r.avg_aggressiveness,
            }
            for r in exp.results
        ],
    }


@router.post("")
async def create_experiment(
    data: ExperimentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    experiment_id = str(uuid.uuid4())
    exp = await crud.create_experiment(
        db,
        id=experiment_id,
        name=data.name,
        description=data.description,
        config_json={
            "scenario_ids": data.scenario_ids,
            "strategies": data.strategies,
            "agent_configs": [a.model_dump() for a in data.agent_configs],
        },
    )

    agent_configs = [a.model_dump() for a in data.agent_configs]

    background_tasks.add_task(
        _run_experiment_bg,
        experiment_id=experiment_id,
        scenario_ids=data.scenario_ids,
        strategies=data.strategies,
        agent_configs=agent_configs,
    )

    return {
        "experiment_id": experiment_id,
        "status": "running",
        "message": "Experiment started in background.",
    }


async def _run_experiment_bg(
    experiment_id: str,
    scenario_ids: list[str],
    strategies: list[str],
    agent_configs: list[dict],
):
    async with async_session() as db:
        try:
            await run_experiment(
                db=db,
                experiment_id=experiment_id,
                scenario_ids=scenario_ids,
                strategies=strategies,
                agent_configs=agent_configs,
            )
        except Exception as e:
            await crud.update_experiment(db, experiment_id, status="failed")
