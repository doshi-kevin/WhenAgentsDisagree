"""Scenario API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.engine import get_db
from app.db import crud
from app.db.schemas import ScenarioCreate, ScenarioResponse

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioResponse])
async def list_scenarios(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    scenarios = await crud.get_scenarios(db, category=category)
    return scenarios


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    scenarios = await crud.get_scenarios(db)
    categories = list(set(s.category for s in scenarios))
    return {"categories": sorted(categories)}


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: str, db: AsyncSession = Depends(get_db)):
    scenario = await crud.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.post("", response_model=ScenarioResponse)
async def create_scenario(data: ScenarioCreate, db: AsyncSession = Depends(get_db)):
    scenario = await crud.create_scenario(
        db,
        category=data.category,
        title=data.title,
        description=data.description,
        question=data.question,
        agent_briefings=[b.model_dump() for b in data.agent_briefings],
        ground_truth=data.ground_truth,
        ground_truth_explanation=data.ground_truth_explanation,
        difficulty=data.difficulty,
        evaluation_criteria=data.evaluation_criteria,
        metadata_json=data.metadata_json,
    )
    return scenario
