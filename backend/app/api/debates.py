"""Debate API endpoints."""
import uuid
import traceback
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.engine import get_db, async_session
from app.db import crud
from app.db.schemas import DebateCreate, DebateResponse, DebateDetailResponse, TurnResponse, TurnMetricsResponse
from app.services.debate_service import run_debate

router = APIRouter(prefix="/debates", tags=["debates"])


@router.get("", response_model=list[DebateResponse])
async def list_debates(
    experiment_id: Optional[str] = None,
    strategy: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    debates = await crud.get_debates(db, experiment_id, strategy, status, limit)
    return [_debate_to_response(d) for d in debates]


@router.get("/{debate_id}")
async def get_debate(debate_id: str, db: AsyncSession = Depends(get_db)):
    debate = await crud.get_debate(db, debate_id)
    if not debate:
        raise HTTPException(status_code=404, detail="Debate not found")
    return _debate_detail_to_response(debate)


@router.post("")
async def create_and_run_debate(
    data: DebateCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a debate and run it (optionally in background)."""
    debate_id = str(uuid.uuid4())

    # Create debate record
    debate = await crud.create_debate(
        db,
        id=debate_id,
        scenario_id=data.scenario_id,
        strategy=data.strategy,
        experiment_id=data.experiment_id,
    )

    agent_configs = [a.model_dump() for a in data.agents]

    # Run in background
    background_tasks.add_task(
        _run_debate_bg,
        debate_id=debate_id,
        scenario_id=data.scenario_id,
        strategy=data.strategy,
        agent_configs=agent_configs,
        experiment_id=data.experiment_id,
        max_rounds=data.max_rounds,
    )

    return {
        "debate_id": debate_id,
        "status": "running",
        "message": "Debate started. Use /api/stream/debate/{id} for live updates.",
    }


async def _run_debate_bg(
    debate_id: str,
    scenario_id: str,
    strategy: str,
    agent_configs: list[dict],
    experiment_id: str = None,
    max_rounds: int = 5,
):
    """Background task to run a debate."""
    async with async_session() as db:
        try:
            await run_debate(
                db=db,
                debate_id=debate_id,
                scenario_id=scenario_id,
                strategy=strategy,
                agent_configs=agent_configs,
                experiment_id=experiment_id,
                max_rounds=max_rounds,
            )
        except Exception as e:
            print(f"[DEBATE ERROR] {debate_id}: {e}")
            traceback.print_exc()
            await crud.update_debate(db, debate_id, status="failed")


def _debate_to_response(debate) -> dict:
    return {
        "id": debate.id,
        "experiment_id": debate.experiment_id,
        "scenario_id": debate.scenario_id,
        "strategy": debate.strategy,
        "status": debate.status,
        "final_answer": debate.final_answer,
        "is_correct": debate.is_correct,
        "total_tokens": debate.total_tokens,
        "total_latency_ms": debate.total_latency_ms,
        "total_turns": debate.total_turns,
        "deadlock_detected": debate.deadlock_detected,
        "deadlock_resolution": debate.deadlock_resolution,
        "agents": [
            {
                "id": a.id,
                "agent_name": a.agent_name,
                "provider": a.provider,
                "model_id": a.model_id,
                "role": a.role,
                "assigned_position": a.assigned_position,
                "bias_role": a.bias_role,
            }
            for a in debate.agents
        ],
        "started_at": debate.started_at,
        "completed_at": debate.completed_at,
        "created_at": debate.created_at,
    }


def _debate_detail_to_response(debate) -> dict:
    base = _debate_to_response(debate)
    base["turns"] = []
    for t in debate.turns:
        turn_data = {
            "id": t.id,
            "turn_number": t.turn_number,
            "round_number": t.round_number,
            "role": t.role,
            "agent_name": t.agent.agent_name if t.agent else "",
            "agent_provider": t.agent.provider if t.agent else "",
            "agent_model": t.agent.model_id if t.agent else "",
            "content": t.content,
            "reasoning": t.reasoning,
            "confidence_score": t.confidence_score,
            "position_held": t.position_held,
            "position_changed": t.position_changed,
            "change_reason": t.change_reason,
            "total_tokens": t.total_tokens,
            "latency_ms": t.latency_ms,
            "created_at": t.created_at,
            "metrics": None,
        }
        if t.metrics:
            turn_data["metrics"] = {
                "aggressiveness_score": t.metrics.aggressiveness_score,
                "sentiment_score": t.metrics.sentiment_score,
                "persuasion_attempt_score": t.metrics.persuasion_attempt_score,
                "citation_count": t.metrics.citation_count,
                "citation_quality_score": t.metrics.citation_quality_score,
                "semantic_similarity_to_prev": t.metrics.semantic_similarity_to_prev,
                "argument_novelty_score": t.metrics.argument_novelty_score,
                "word_count": t.metrics.word_count,
                "hedging_language_count": t.metrics.hedging_language_count,
            }
        base["turns"].append(turn_data)

    if debate.scenario:
        base["scenario"] = {
            "id": debate.scenario.id,
            "category": debate.scenario.category,
            "title": debate.scenario.title,
            "question": debate.scenario.question,
            "ground_truth": debate.scenario.ground_truth,
            "difficulty": debate.scenario.difficulty,
        }

    return base
