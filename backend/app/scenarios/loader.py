"""Load conflict scenarios from JSON files into the database."""
import json
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Scenario


SCENARIOS_DIR = Path(__file__).parent.parent.parent / "data" / "scenarios"


async def load_scenarios(db: AsyncSession, force_reload: bool = False) -> int:
    """Load all scenarios from JSON files into the database."""
    # Check if scenarios already exist
    if not force_reload:
        result = await db.execute(select(Scenario).limit(1))
        if result.scalar_one_or_none():
            return 0

    loaded = 0
    for json_file in SCENARIOS_DIR.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            scenarios = json.load(f)

        for s in scenarios:
            # Check if scenario already exists
            existing = await db.execute(
                select(Scenario).where(Scenario.id == s.get("id", ""))
            )
            if existing.scalar_one_or_none():
                continue

            scenario = Scenario(
                id=s.get("id", None),
                category=s["category"],
                title=s["title"],
                description=s.get("description", ""),
                question=s["question"],
                agent_briefings=s["agent_briefings"],
                ground_truth=s["ground_truth"],
                ground_truth_explanation=s.get("ground_truth_explanation", ""),
                difficulty=s.get("difficulty", "medium"),
                evaluation_criteria=s.get("evaluation_criteria"),
                metadata_json=s.get("metadata"),
            )
            db.add(scenario)
            loaded += 1

    await db.commit()
    return loaded
