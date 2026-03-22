"""Experiment runner - orchestrates running multiple debates."""
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.services.debate_service import run_debate
from app.metrics.aggregator import compute_experiment_results


async def run_experiment(
    db: AsyncSession,
    experiment_id: str,
    scenario_ids: list[str],
    strategies: list[str],
    agent_configs: list[dict],
    max_rounds: int = 3,
) -> dict:
    """Run a full experiment across scenarios and strategies."""
    await crud.update_experiment(db, experiment_id, status="running")

    results = []
    total = len(scenario_ids) * len(strategies)
    completed = 0
    errors = []

    for scenario_id in scenario_ids:
        for strategy in strategies:
            debate_id = str(uuid.uuid4())

            # Create debate record
            await crud.create_debate(
                db,
                id=debate_id,
                experiment_id=experiment_id,
                scenario_id=scenario_id,
                strategy=strategy,
            )

            try:
                result = await run_debate(
                    db=db,
                    debate_id=debate_id,
                    scenario_id=scenario_id,
                    strategy=strategy,
                    agent_configs=agent_configs,
                    experiment_id=experiment_id,
                    max_rounds=max_rounds,
                )
                results.append(result)
                completed += 1
            except Exception as e:
                errors.append({
                    "scenario_id": scenario_id,
                    "strategy": strategy,
                    "error": str(e),
                })

    # Compute aggregated results
    try:
        await compute_experiment_results(db, experiment_id)
    except Exception:
        pass

    await crud.update_experiment(
        db,
        experiment_id,
        status="completed" if not errors else "completed",
        completed_at=datetime.now(timezone.utc),
    )

    return {
        "experiment_id": experiment_id,
        "total_debates": total,
        "completed": completed,
        "errors": errors,
        "results": results,
    }
