"""Research-grade analytics for multi-agent conflict resolution studies."""
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Debate, Turn, TurnMetrics, DebateAgent, Scenario


async def _load_completed_debates(db: AsyncSession) -> list[Debate]:
    """Load all completed debates with full eager loading."""
    result = await db.execute(
        select(Debate)
        .options(
            selectinload(Debate.agents),
            selectinload(Debate.turns).selectinload(Turn.metrics),
            selectinload(Debate.turns).selectinload(Turn.agent),
            selectinload(Debate.scenario),
        )
        .where(Debate.status == "completed")
    )
    return list(result.scalars().unique().all())


def _safe_mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _safe_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return round(variance ** 0.5, 4)


async def compute_research_insights(db: AsyncSession) -> dict:
    """Compute comprehensive research insights across all completed debates."""
    debates = await _load_completed_debates(db)

    if not debates:
        return {"error": "No completed debates found", "debate_count": 0}

    return {
        "debate_count": len(debates),
        "strategy_effectiveness": _strategy_effectiveness(debates),
        "source_quality_impact": _source_quality_impact(debates),
        "model_behavioral_profiles": _model_behavioral_profiles(debates),
        "position_change_dynamics": _position_change_dynamics(debates),
        "misinformation_resistance": _misinformation_resistance(debates),
        "argument_quality_over_time": _argument_quality_over_rounds(debates),
        "deadlock_analysis": _deadlock_analysis(debates),
        "key_findings": _generate_key_findings(debates),
    }


def _strategy_effectiveness(debates: list[Debate]) -> list[dict]:
    """Compare strategies on accuracy, efficiency, and behavioral metrics."""
    by_strategy = defaultdict(list)
    for d in debates:
        by_strategy[d.strategy].append(d)

    results = []
    for strategy, strategy_debates in by_strategy.items():
        n = len(strategy_debates)
        accuracies = [1.0 if d.is_correct else 0.0 for d in strategy_debates]
        latencies = [d.total_latency_ms for d in strategy_debates if d.total_latency_ms]
        tokens = [d.total_tokens for d in strategy_debates if d.total_tokens]
        turns = [d.total_turns for d in strategy_debates if d.total_turns]
        deadlocks = sum(1 for d in strategy_debates if d.deadlock_detected)

        # Per-turn metrics
        all_confidence = []
        all_aggression = []
        all_sentiment = []
        all_novelty = []
        position_changes = 0
        total_turns_counted = 0

        for d in strategy_debates:
            for t in d.turns:
                total_turns_counted += 1
                if t.confidence_score is not None:
                    all_confidence.append(t.confidence_score)
                if t.metrics:
                    if t.metrics.aggressiveness_score is not None:
                        all_aggression.append(t.metrics.aggressiveness_score)
                    if t.metrics.sentiment_score is not None:
                        all_sentiment.append(t.metrics.sentiment_score)
                    if t.metrics.argument_novelty_score is not None:
                        all_novelty.append(t.metrics.argument_novelty_score)
                if t.position_changed:
                    position_changes += 1

        results.append({
            "strategy": strategy,
            "total_debates": n,
            "accuracy": _safe_mean(accuracies),
            "accuracy_std": _safe_std(accuracies),
            "avg_latency_ms": _safe_mean(latencies),
            "avg_tokens": _safe_mean(tokens),
            "avg_turns": _safe_mean(turns),
            "deadlock_rate": round(deadlocks / n, 4) if n else 0,
            "avg_confidence": _safe_mean(all_confidence),
            "confidence_std": _safe_std(all_confidence),
            "avg_aggressiveness": _safe_mean(all_aggression),
            "avg_sentiment": _safe_mean(all_sentiment),
            "avg_novelty": _safe_mean(all_novelty),
            "position_change_rate": round(position_changes / total_turns_counted, 4) if total_turns_counted else 0,
        })

    return sorted(results, key=lambda r: r["accuracy"], reverse=True)


def _source_quality_impact(debates: list[Debate]) -> dict:
    """Analyze how source reliability correlates with winning the debate."""
    winning_reliabilities = []
    losing_reliabilities = []
    all_correlations = []

    for d in debates:
        if not d.scenario or not d.final_answer:
            continue

        for agent in d.agents:
            # Find this agent's source reliability from scenario briefings
            briefings = d.scenario.agent_briefings or []
            agent_briefing = None
            for b in briefings:
                if b.get("position", "").lower().strip() == (agent.assigned_position or "").lower().strip():
                    agent_briefing = b
                    break

            if not agent_briefing:
                continue

            reliability = agent_briefing.get("source_reliability", 0.5)
            # Did this agent's position win?
            agent_won = (
                agent.assigned_position
                and d.final_answer.lower().strip() in agent.assigned_position.lower().strip()
                or agent.assigned_position.lower().strip() in d.final_answer.lower().strip()
            )

            if agent_won:
                winning_reliabilities.append(reliability)
            else:
                losing_reliabilities.append(reliability)

            all_correlations.append({
                "reliability": reliability,
                "won": agent_won,
                "source_type": agent_briefing.get("source_type", "unknown"),
            })

    # Group by source type
    by_source_type = defaultdict(lambda: {"wins": 0, "total": 0})
    for c in all_correlations:
        st = c["source_type"]
        by_source_type[st]["total"] += 1
        if c["won"]:
            by_source_type[st]["wins"] += 1

    source_type_win_rates = {
        st: round(d["wins"] / d["total"], 4) if d["total"] else 0
        for st, d in by_source_type.items()
    }

    return {
        "avg_winning_source_reliability": _safe_mean(winning_reliabilities),
        "avg_losing_source_reliability": _safe_mean(losing_reliabilities),
        "reliability_gap": round(
            _safe_mean(winning_reliabilities) - _safe_mean(losing_reliabilities), 4
        ),
        "source_type_win_rates": source_type_win_rates,
        "total_data_points": len(all_correlations),
        "finding": (
            "Higher source reliability correlates with winning"
            if _safe_mean(winning_reliabilities) > _safe_mean(losing_reliabilities)
            else "Source reliability does NOT predict debate outcomes"
        ),
    }


def _model_behavioral_profiles(debates: list[Debate]) -> list[dict]:
    """Build behavioral profiles for each model across all debates."""
    model_data = defaultdict(lambda: {
        "confidences": [], "aggressiveness": [], "sentiments": [],
        "novelty": [], "citations": [], "hedging": [],
        "position_changes": 0, "total_turns": 0, "debate_ids": set(),
        "correct_debates": set(), "word_counts": [],
    })

    for d in debates:
        for agent in d.agents:
            key = f"{agent.provider}:{agent.model_id}"
            model_data[key]["debate_ids"].add(d.id)
            if d.is_correct:
                model_data[key]["correct_debates"].add(d.id)

            for t in d.turns:
                if t.debate_agent_id != agent.id:
                    continue
                md = model_data[key]
                md["total_turns"] += 1
                if t.position_changed:
                    md["position_changes"] += 1
                if t.confidence_score is not None:
                    md["confidences"].append(t.confidence_score)
                if t.metrics:
                    m = t.metrics
                    if m.aggressiveness_score is not None:
                        md["aggressiveness"].append(m.aggressiveness_score)
                    if m.sentiment_score is not None:
                        md["sentiments"].append(m.sentiment_score)
                    if m.argument_novelty_score is not None:
                        md["novelty"].append(m.argument_novelty_score)
                    if m.citation_count is not None:
                        md["citations"].append(m.citation_count)
                    if m.hedging_language_count is not None:
                        md["hedging"].append(m.hedging_language_count)
                    if m.word_count is not None:
                        md["word_counts"].append(m.word_count)

    profiles = []
    for key, md in model_data.items():
        provider, model_id = key.split(":", 1)
        n_debates = len(md["debate_ids"])
        tc = md["total_turns"] or 1

        profile = {
            "provider": provider,
            "model_id": model_id,
            "total_debates": n_debates,
            "total_turns": md["total_turns"],
            "accuracy": round(len(md["correct_debates"]) / n_debates, 4) if n_debates else 0,
            "avg_confidence": _safe_mean(md["confidences"]),
            "confidence_std": _safe_std(md["confidences"]),
            "avg_aggressiveness": _safe_mean(md["aggressiveness"]),
            "avg_sentiment": _safe_mean(md["sentiments"]),
            "avg_novelty": _safe_mean(md["novelty"]),
            "avg_citations_per_turn": _safe_mean(md["citations"]),
            "avg_hedging_per_turn": _safe_mean(md["hedging"]),
            "avg_word_count": _safe_mean(md["word_counts"]),
            "position_change_rate": round(md["position_changes"] / tc, 4),
            # Behavioral classification
            "behavioral_type": _classify_behavior(
                _safe_mean(md["aggressiveness"]),
                _safe_mean(md["sentiments"]),
                round(md["position_changes"] / tc, 4),
            ),
        }
        profiles.append(profile)

    return sorted(profiles, key=lambda p: p["total_debates"], reverse=True)


def _classify_behavior(aggression: float, sentiment: float, change_rate: float) -> str:
    """Classify a model's behavioral type based on its metrics."""
    if aggression > 0.5 and sentiment < 0:
        return "Aggressive Debater"
    if change_rate > 0.1 and sentiment > 0.2:
        return "Open-Minded Collaborator"
    if aggression < 0.2 and change_rate < 0.02:
        return "Stubborn Defender"
    if aggression > 0.3 and change_rate < 0.02:
        return "Assertive Advocate"
    return "Balanced Participant"


def _position_change_dynamics(debates: list[Debate]) -> dict:
    """Analyze when and why agents change positions."""
    changes_by_round = defaultdict(int)
    total_turns_by_round = defaultdict(int)
    changes_by_strategy = defaultdict(int)
    total_turns_by_strategy = defaultdict(int)
    change_reasons = []

    for d in debates:
        for t in d.turns:
            total_turns_by_round[t.round_number] += 1
            total_turns_by_strategy[d.strategy] += 1
            if t.position_changed:
                changes_by_round[t.round_number] += 1
                changes_by_strategy[d.strategy] += 1
                if t.change_reason:
                    change_reasons.append({
                        "round": t.round_number,
                        "strategy": d.strategy,
                        "agent": t.agent.agent_name if t.agent else "unknown",
                        "model": t.agent.model_id if t.agent else "unknown",
                        "reason": t.change_reason[:200],
                    })

    round_change_rates = {
        r: round(changes_by_round[r] / total_turns_by_round[r], 4)
        for r in sorted(total_turns_by_round.keys())
    }

    strategy_change_rates = {
        s: round(changes_by_strategy[s] / total_turns_by_strategy[s], 4)
        for s in total_turns_by_strategy.keys()
    }

    return {
        "total_position_changes": sum(changes_by_round.values()),
        "change_rate_by_round": round_change_rates,
        "change_rate_by_strategy": strategy_change_rates,
        "recent_change_reasons": change_reasons[-10:],
        "finding": (
            "Position changes are most frequent in later rounds"
            if round_change_rates and max(round_change_rates, key=round_change_rates.get) > 2
            else "Position changes are distributed across rounds"
        ),
    }


def _misinformation_resistance(debates: list[Debate]) -> dict:
    """Analyze how well the system resists misinformation (misinformation_battle scenarios)."""
    misinfo_debates = [
        d for d in debates
        if d.scenario and d.scenario.category == "misinformation_battle"
    ]

    if not misinfo_debates:
        return {
            "total_misinformation_debates": 0,
            "finding": "No misinformation battle scenarios have been run yet",
        }

    truth_wins = 0
    misinfo_wins = 0
    by_strategy = defaultdict(lambda: {"truth_wins": 0, "misinfo_wins": 0, "total": 0})

    for d in misinfo_debates:
        by_strategy[d.strategy]["total"] += 1

        # Determine if truth won by checking if debate is_correct
        # (ground_truth represents the factually correct answer)
        if d.is_correct:
            truth_wins += 1
            by_strategy[d.strategy]["truth_wins"] += 1
        else:
            misinfo_wins += 1
            by_strategy[d.strategy]["misinfo_wins"] += 1

    total = len(misinfo_debates)
    strategy_resistance = {
        s: round(d["truth_wins"] / d["total"], 4) if d["total"] else 0
        for s, d in by_strategy.items()
    }

    # Analyze which bias roles are most effective
    role_effectiveness = defaultdict(lambda: {"wins": 0, "total": 0})
    for d in misinfo_debates:
        for agent in d.agents:
            if not agent.bias_role:
                continue
            role_effectiveness[agent.bias_role]["total"] += 1
            # Check if this agent's position won
            if d.final_answer and agent.assigned_position:
                if (d.final_answer.lower().strip() in agent.assigned_position.lower().strip()
                        or agent.assigned_position.lower().strip() in d.final_answer.lower().strip()):
                    role_effectiveness[agent.bias_role]["wins"] += 1

    role_win_rates = {
        role: round(d["wins"] / d["total"], 4) if d["total"] else 0
        for role, d in role_effectiveness.items()
    }

    return {
        "total_misinformation_debates": total,
        "truth_win_rate": round(truth_wins / total, 4) if total else 0,
        "misinformation_win_rate": round(misinfo_wins / total, 4) if total else 0,
        "truth_resistance_by_strategy": strategy_resistance,
        "bias_role_win_rates": role_win_rates,
        "best_strategy_for_truth": (
            max(strategy_resistance, key=strategy_resistance.get)
            if strategy_resistance else "insufficient_data"
        ),
        "finding": (
            f"Truth prevails {round(truth_wins / total * 100, 1)}% of the time in misinformation battles"
            if total else "No data"
        ),
    }


def _argument_quality_over_rounds(debates: list[Debate]) -> dict:
    """Track how argument quality metrics evolve across debate rounds."""
    rounds_data = defaultdict(lambda: {
        "novelty": [], "aggressiveness": [], "confidence": [],
        "sentiment": [], "citations": [], "word_count": [],
    })

    for d in debates:
        for t in d.turns:
            rd = rounds_data[t.round_number]
            if t.confidence_score is not None:
                rd["confidence"].append(t.confidence_score)
            if t.metrics:
                m = t.metrics
                if m.argument_novelty_score is not None:
                    rd["novelty"].append(m.argument_novelty_score)
                if m.aggressiveness_score is not None:
                    rd["aggressiveness"].append(m.aggressiveness_score)
                if m.sentiment_score is not None:
                    rd["sentiment"].append(m.sentiment_score)
                if m.citation_count is not None:
                    rd["citations"].append(m.citation_count)
                if m.word_count is not None:
                    rd["word_count"].append(m.word_count)

    trajectory = []
    for r in sorted(rounds_data.keys()):
        rd = rounds_data[r]
        trajectory.append({
            "round": r,
            "avg_novelty": _safe_mean(rd["novelty"]),
            "avg_aggressiveness": _safe_mean(rd["aggressiveness"]),
            "avg_confidence": _safe_mean(rd["confidence"]),
            "avg_sentiment": _safe_mean(rd["sentiment"]),
            "avg_citations": _safe_mean(rd["citations"]),
            "avg_word_count": _safe_mean(rd["word_count"]),
            "data_points": len(rd["confidence"]),
        })

    return {
        "rounds": trajectory,
        "finding": _trajectory_finding(trajectory),
    }


def _trajectory_finding(trajectory: list[dict]) -> str:
    """Generate a finding about argument quality trajectory."""
    if len(trajectory) < 2:
        return "Insufficient rounds for trajectory analysis"
    first = trajectory[0]
    last = trajectory[-1]
    novelty_delta = last["avg_novelty"] - first["avg_novelty"]
    aggr_delta = last["avg_aggressiveness"] - first["avg_aggressiveness"]

    parts = []
    if novelty_delta < -0.1:
        parts.append("Argument novelty decreases over rounds (repetition increases)")
    elif novelty_delta > 0.1:
        parts.append("Argument novelty increases over rounds (agents find new angles)")

    if aggr_delta > 0.1:
        parts.append("Aggressiveness escalates as debate progresses")
    elif aggr_delta < -0.1:
        parts.append("Agents become less aggressive over time")

    return "; ".join(parts) if parts else "Argument quality remains relatively stable across rounds"


def _deadlock_analysis(debates: list[Debate]) -> dict:
    """Detailed deadlock analysis across strategies and model combinations."""
    by_strategy = defaultdict(lambda: {"total": 0, "deadlocked": 0})
    model_pair_deadlocks = defaultdict(lambda: {"total": 0, "deadlocked": 0})

    for d in debates:
        by_strategy[d.strategy]["total"] += 1
        if d.deadlock_detected:
            by_strategy[d.strategy]["deadlocked"] += 1

        # Track model combinations
        models = sorted([a.model_id for a in d.agents])
        combo_key = " + ".join(models)
        model_pair_deadlocks[combo_key]["total"] += 1
        if d.deadlock_detected:
            model_pair_deadlocks[combo_key]["deadlocked"] += 1

    strategy_deadlock_rates = {
        s: round(d["deadlocked"] / d["total"], 4) if d["total"] else 0
        for s, d in by_strategy.items()
    }

    combo_deadlock_rates = {
        combo: {
            "total": d["total"],
            "deadlocked": d["deadlocked"],
            "rate": round(d["deadlocked"] / d["total"], 4) if d["total"] else 0,
        }
        for combo, d in model_pair_deadlocks.items()
    }

    return {
        "strategy_deadlock_rates": strategy_deadlock_rates,
        "model_combo_deadlock_rates": combo_deadlock_rates,
        "most_deadlock_prone_strategy": (
            max(strategy_deadlock_rates, key=strategy_deadlock_rates.get)
            if strategy_deadlock_rates else "N/A"
        ),
    }


def _generate_key_findings(debates: list[Debate]) -> list[str]:
    """Auto-generate key research findings from the data."""
    findings = []
    n = len(debates)
    correct = sum(1 for d in debates if d.is_correct)
    deadlocked = sum(1 for d in debates if d.deadlock_detected)

    findings.append(
        f"Across {n} debates, overall accuracy is {round(correct / n * 100, 1)}% "
        f"with a {round(deadlocked / n * 100, 1)}% deadlock rate"
    )

    # Best strategy
    by_strategy = defaultdict(list)
    for d in debates:
        by_strategy[d.strategy].append(d)

    if by_strategy:
        strategy_acc = {
            s: sum(1 for d in ds if d.is_correct) / len(ds)
            for s, ds in by_strategy.items()
        }
        best = max(strategy_acc, key=strategy_acc.get)
        worst = min(strategy_acc, key=strategy_acc.get)
        findings.append(
            f"'{best}' achieves the highest accuracy ({round(strategy_acc[best] * 100, 1)}%), "
            f"while '{worst}' performs worst ({round(strategy_acc[worst] * 100, 1)}%)"
        )

    # Deadlock patterns
    if deadlocked > 0:
        dl_strategies = defaultdict(int)
        for d in debates:
            if d.deadlock_detected:
                dl_strategies[d.strategy] += 1
        most_dl = max(dl_strategies, key=dl_strategies.get)
        findings.append(
            f"Deadlocks occur most frequently with '{most_dl}' strategy "
            f"({dl_strategies[most_dl]} of {deadlocked} total deadlocks)"
        )

    # Position changes
    total_changes = 0
    total_turns = 0
    for d in debates:
        for t in d.turns:
            total_turns += 1
            if t.position_changed:
                total_changes += 1

    if total_turns:
        change_pct = round(total_changes / total_turns * 100, 1)
        findings.append(
            f"Agents change position in {change_pct}% of turns "
            f"({total_changes} changes across {total_turns} total turns)"
        )

    return findings
