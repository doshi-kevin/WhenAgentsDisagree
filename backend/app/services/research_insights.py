"""Research-grade analytics with statistical significance testing for multi-agent conflict resolution studies."""
import math
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Debate, Turn, TurnMetrics, DebateAgent, Scenario


# --- Statistical Helpers ---

def _safe_mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _safe_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return round(variance ** 0.5, 4)


def _confidence_interval_95(values: list[float]) -> tuple[float, float]:
    """Compute 95% confidence interval using t-distribution approximation."""
    n = len(values)
    if n < 2:
        return (0.0, 0.0)
    mean = sum(values) / n
    std = _safe_std(values)
    # t-critical for 95% CI (approximation for df > 2)
    t_crit = 12.706 if n == 2 else 4.303 if n == 3 else 3.182 if n == 4 else 2.776 if n == 5 else 2.571 if n == 6 else 2.447 if n == 7 else 2.365 if n == 8 else 2.262 if n == 9 else 2.228 if n == 10 else 2.086 if n <= 20 else 1.96
    margin = t_crit * std / math.sqrt(n)
    return (round(mean - margin, 4), round(mean + margin, 4))


def _cohens_d(group1: list[float], group2: list[float]) -> float:
    """Compute Cohen's d effect size between two groups."""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    m1 = sum(group1) / n1
    m2 = sum(group2) / n2
    v1 = sum((x - m1) ** 2 for x in group1) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in group2) / (n2 - 1)
    pooled_std = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return round((m1 - m2) / pooled_std, 4)


def _effect_size_label(d: float) -> str:
    """Interpret Cohen's d magnitude."""
    d = abs(d)
    if d < 0.2:
        return "negligible"
    if d < 0.5:
        return "small"
    if d < 0.8:
        return "medium"
    return "large"


def _chi_squared_2x2(a: int, b: int, c: int, d: int) -> dict:
    """Chi-squared test for 2x2 contingency table: [[a,b],[c,d]]."""
    n = a + b + c + d
    if n == 0:
        return {"chi2": 0, "p_value": 1.0, "significant": False}
    expected_a = (a + b) * (a + c) / n
    expected_b = (a + b) * (b + d) / n
    expected_c = (c + d) * (a + c) / n
    expected_d = (c + d) * (b + d) / n
    chi2 = 0
    for obs, exp in [(a, expected_a), (b, expected_b), (c, expected_c), (d, expected_d)]:
        if exp > 0:
            chi2 += (obs - exp) ** 2 / exp
    # p-value approximation from chi2 with df=1
    # Using survival function of chi-squared distribution
    p_value = _chi2_sf(chi2, 1)
    return {
        "chi2": round(chi2, 4),
        "p_value": round(p_value, 4),
        "significant": p_value < 0.05,
    }


def _chi2_sf(x: float, df: int = 1) -> float:
    """Approximate chi-squared survival function (1 - CDF). Uses scipy if available, else approximation."""
    try:
        from scipy.stats import chi2
        return float(chi2.sf(x, df))
    except ImportError:
        pass
    # Fallback: Wilson-Hilferty approximation
    if x <= 0:
        return 1.0
    z = ((x / df) ** (1 / 3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
    # Standard normal CDF approximation
    p = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return max(0.0, min(1.0, 1 - p))


def _welch_t_test(group1: list[float], group2: list[float]) -> dict:
    """Welch's t-test for unequal variances."""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return {"t_stat": 0, "p_value": 1.0, "significant": False}
    try:
        from scipy.stats import ttest_ind
        stat, p = ttest_ind(group1, group2, equal_var=False)
        return {"t_stat": round(float(stat), 4), "p_value": round(float(p), 4), "significant": float(p) < 0.05}
    except ImportError:
        pass
    # Fallback manual Welch's t-test
    m1 = sum(group1) / n1
    m2 = sum(group2) / n2
    v1 = sum((x - m1) ** 2 for x in group1) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in group2) / (n2 - 1)
    se = math.sqrt(v1 / n1 + v2 / n2)
    if se == 0:
        return {"t_stat": 0, "p_value": 1.0, "significant": False}
    t_stat = (m1 - m2) / se
    # Rough p-value from t (two-tailed, approximation)
    p = 2 * _chi2_sf(t_stat ** 2, 1)
    return {"t_stat": round(t_stat, 4), "p_value": round(p, 4), "significant": p < 0.05}


# --- Data Loading ---

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


# --- Main Entry Point ---

async def compute_research_insights(db: AsyncSession) -> dict:
    """Compute comprehensive research insights across all completed debates."""
    debates = await _load_completed_debates(db)

    if not debates:
        return {"error": "No completed debates found", "debate_count": 0}

    return {
        "debate_count": len(debates),
        "strategy_effectiveness": _strategy_effectiveness(debates),
        "statistical_tests": _statistical_significance_tests(debates),
        "source_quality_impact": _source_quality_impact(debates),
        "model_behavioral_profiles": _model_behavioral_profiles(debates),
        "behavioral_dna": _behavioral_dna_fingerprints(debates),
        "position_change_dynamics": _position_change_dynamics(debates),
        "misinformation_resistance": _misinformation_resistance(debates),
        "argument_quality_over_time": _argument_quality_over_rounds(debates),
        "deadlock_analysis": _deadlock_analysis(debates),
        "cross_strategy_effect_sizes": _cross_strategy_effect_sizes(debates),
        "key_findings": _generate_key_findings(debates),
    }


# --- Statistical Significance Tests ---

def _statistical_significance_tests(debates: list[Debate]) -> dict:
    """Run formal statistical tests across strategies."""
    by_strategy = defaultdict(list)
    for d in debates:
        by_strategy[d.strategy].append(d)

    strategies = list(by_strategy.keys())
    pairwise_accuracy = []
    pairwise_aggressiveness = []
    pairwise_confidence = []

    for i in range(len(strategies)):
        for j in range(i + 1, len(strategies)):
            s1, s2 = strategies[i], strategies[j]
            acc1 = [1.0 if d.is_correct else 0.0 for d in by_strategy[s1]]
            acc2 = [1.0 if d.is_correct else 0.0 for d in by_strategy[s2]]

            # Chi-squared for accuracy (binary outcome)
            a = sum(1 for x in acc1 if x == 1.0)
            b = sum(1 for x in acc1 if x == 0.0)
            c = sum(1 for x in acc2 if x == 1.0)
            d_val = sum(1 for x in acc2 if x == 0.0)
            chi2_result = _chi_squared_2x2(a, b, c, d_val)

            # Aggressiveness t-test
            aggr1 = _extract_metric(by_strategy[s1], "aggressiveness_score")
            aggr2 = _extract_metric(by_strategy[s2], "aggressiveness_score")
            t_aggr = _welch_t_test(aggr1, aggr2)

            # Confidence t-test
            conf1 = [t.confidence_score for d in by_strategy[s1] for t in d.turns if t.confidence_score is not None]
            conf2 = [t.confidence_score for d in by_strategy[s2] for t in d.turns if t.confidence_score is not None]
            t_conf = _welch_t_test(conf1, conf2)

            pairwise_accuracy.append({
                "comparison": f"{s1} vs {s2}",
                "n1": len(acc1), "n2": len(acc2),
                "accuracy_1": _safe_mean(acc1), "accuracy_2": _safe_mean(acc2),
                **chi2_result,
                "effect_size_d": _cohens_d(acc1, acc2),
                "effect_magnitude": _effect_size_label(_cohens_d(acc1, acc2)),
            })

            pairwise_aggressiveness.append({
                "comparison": f"{s1} vs {s2}",
                "mean_1": _safe_mean(aggr1), "mean_2": _safe_mean(aggr2),
                **t_aggr,
                "effect_size_d": _cohens_d(aggr1, aggr2),
                "effect_magnitude": _effect_size_label(_cohens_d(aggr1, aggr2)),
            })

            pairwise_confidence.append({
                "comparison": f"{s1} vs {s2}",
                "mean_1": _safe_mean(conf1), "mean_2": _safe_mean(conf2),
                **t_conf,
                "effect_size_d": _cohens_d(conf1, conf2),
                "effect_magnitude": _effect_size_label(_cohens_d(conf1, conf2)),
            })

    return {
        "pairwise_accuracy_chi2": pairwise_accuracy,
        "pairwise_aggressiveness_ttest": pairwise_aggressiveness,
        "pairwise_confidence_ttest": pairwise_confidence,
        "methodology_note": "Accuracy: Chi-squared test on 2x2 tables. Continuous metrics: Welch's t-test (unequal variances). Effect sizes: Cohen's d. Significance threshold: p < 0.05.",
    }


def _extract_metric(debates: list[Debate], metric_name: str) -> list[float]:
    """Extract a specific turn metric across all turns in given debates."""
    values = []
    for d in debates:
        for t in d.turns:
            if t.metrics:
                val = getattr(t.metrics, metric_name, None)
                if val is not None:
                    values.append(val)
    return values


# --- Cross-Strategy Effect Sizes ---

def _cross_strategy_effect_sizes(debates: list[Debate]) -> list[dict]:
    """Compute effect sizes for all metric dimensions across strategy pairs."""
    by_strategy = defaultdict(list)
    for d in debates:
        by_strategy[d.strategy].append(d)

    metrics = ["aggressiveness_score", "sentiment_score", "argument_novelty_score", "citation_quality_score"]
    strategies = list(by_strategy.keys())
    results = []

    for metric in metrics:
        for i in range(len(strategies)):
            for j in range(i + 1, len(strategies)):
                s1, s2 = strategies[i], strategies[j]
                v1 = _extract_metric(by_strategy[s1], metric)
                v2 = _extract_metric(by_strategy[s2], metric)
                d = _cohens_d(v1, v2)
                results.append({
                    "metric": metric.replace("_score", "").replace("_", " ").title(),
                    "strategy_1": s1,
                    "strategy_2": s2,
                    "cohens_d": d,
                    "magnitude": _effect_size_label(d),
                    "n1": len(v1),
                    "n2": len(v2),
                })

    return results


# --- Behavioral DNA Fingerprints ---

def _behavioral_dna_fingerprints(debates: list[Debate]) -> list[dict]:
    """
    Compute a unique 'Behavioral DNA' fingerprint for each model.
    This is a 10-dimensional vector representing a model's behavioral signature
    across all debates it has participated in. This is a NOVEL metric — no existing
    research platform computes multi-dimensional behavioral fingerprints for LLMs.
    """
    model_data = defaultdict(lambda: {
        "confidence_mean": [], "confidence_volatility": [],
        "aggressiveness_mean": [], "aggressiveness_escalation": [],
        "sentiment_polarity": [], "novelty_decay_rate": [],
        "stubbornness": [], "citation_density": [],
        "verbosity": [], "hedging_ratio": [],
    })

    for d in debates:
        for agent in d.agents:
            key = f"{agent.provider}:{agent.model_id}"
            agent_turns = sorted(
                [t for t in d.turns if t.debate_agent_id == agent.id],
                key=lambda t: t.turn_number
            )
            if not agent_turns:
                continue

            md = model_data[key]

            # 1. Confidence mean
            confs = [t.confidence_score for t in agent_turns if t.confidence_score is not None]
            if confs:
                md["confidence_mean"].append(_safe_mean(confs))

            # 2. Confidence volatility (std dev across turns within a debate)
            if len(confs) >= 2:
                md["confidence_volatility"].append(_safe_std(confs))

            # 3. Aggressiveness mean
            aggrs = [t.metrics.aggressiveness_score for t in agent_turns if t.metrics and t.metrics.aggressiveness_score is not None]
            if aggrs:
                md["aggressiveness_mean"].append(_safe_mean(aggrs))

            # 4. Aggressiveness escalation (slope from first to last)
            if len(aggrs) >= 2:
                escalation = aggrs[-1] - aggrs[0]
                md["aggressiveness_escalation"].append(escalation)

            # 5. Sentiment polarity
            sents = [t.metrics.sentiment_score for t in agent_turns if t.metrics and t.metrics.sentiment_score is not None]
            if sents:
                md["sentiment_polarity"].append(_safe_mean(sents))

            # 6. Novelty decay rate (how fast novelty decreases)
            novelties = [t.metrics.argument_novelty_score for t in agent_turns if t.metrics and t.metrics.argument_novelty_score is not None]
            if len(novelties) >= 2:
                decay = novelties[-1] - novelties[0]
                md["novelty_decay_rate"].append(decay)

            # 7. Stubbornness (1 - position change rate)
            changes = sum(1 for t in agent_turns if t.position_changed)
            stubbornness = 1.0 - (changes / len(agent_turns))
            md["stubbornness"].append(stubbornness)

            # 8. Citation density
            citations = [t.metrics.citation_count for t in agent_turns if t.metrics and t.metrics.citation_count is not None]
            if citations:
                md["citation_density"].append(_safe_mean(citations))

            # 9. Verbosity (avg word count)
            words = [t.metrics.word_count for t in agent_turns if t.metrics and t.metrics.word_count is not None]
            if words:
                md["verbosity"].append(_safe_mean(words))

            # 10. Hedging ratio
            hedges = [t.metrics.hedging_language_count for t in agent_turns if t.metrics and t.metrics.hedging_language_count is not None]
            wc = [t.metrics.word_count for t in agent_turns if t.metrics and t.metrics.word_count]
            if hedges and wc:
                total_words = sum(wc)
                total_hedges = sum(hedges)
                md["hedging_ratio"].append(total_hedges / max(total_words, 1))

    fingerprints = []
    for key, md in model_data.items():
        provider, model_id = key.split(":", 1)

        dna = {
            "confidence": _safe_mean(md["confidence_mean"]),
            "confidence_volatility": _safe_mean(md["confidence_volatility"]),
            "aggressiveness": _safe_mean(md["aggressiveness_mean"]),
            "aggression_escalation": _safe_mean(md["aggressiveness_escalation"]),
            "sentiment": _safe_mean(md["sentiment_polarity"]),
            "novelty_decay": _safe_mean(md["novelty_decay_rate"]),
            "stubbornness": _safe_mean(md["stubbornness"]),
            "citation_density": _safe_mean(md["citation_density"]),
            "verbosity": _safe_mean(md["verbosity"]),
            "hedging_ratio": _safe_mean(md["hedging_ratio"]),
        }

        # Normalize to 0-1 for radar visualization
        dna_normalized = {
            "confidence": dna["confidence"],
            "volatility": min(1.0, dna["confidence_volatility"] * 5),  # Scale up, std rarely > 0.2
            "aggressiveness": dna["aggressiveness"],
            "escalation": min(1.0, max(0.0, (dna["aggression_escalation"] + 0.5))),  # Center at 0.5
            "cooperation": max(0.0, min(1.0, (dna["sentiment"] + 1) / 2)),  # -1..1 → 0..1
            "novelty_retention": max(0.0, min(1.0, 1.0 + dna["novelty_decay"])),  # Decay is negative
            "stubbornness": dna["stubbornness"],
            "evidence_use": min(1.0, dna["citation_density"] / 5),  # Normalize citations
            "verbosity": min(1.0, dna["verbosity"] / 200),  # Normalize word count
            "hedging": min(1.0, dna["hedging_ratio"] * 20),  # Scale up small ratios
        }

        # Classify behavioral archetype based on DNA
        archetype = _classify_dna_archetype(dna, dna_normalized)

        fingerprints.append({
            "provider": provider,
            "model_id": model_id,
            "dna_raw": dna,
            "dna_normalized": dna_normalized,
            "archetype": archetype,
            "debates_sampled": len(md["confidence_mean"]),
        })

    return sorted(fingerprints, key=lambda f: f["debates_sampled"], reverse=True)


def _classify_dna_archetype(dna: dict, norm: dict) -> dict:
    """Classify model into a behavioral archetype based on its DNA fingerprint."""
    archetypes = {
        "The Bulldozer": {
            "description": "High aggression, high stubbornness, low cooperation — dominates through force",
            "match": norm["aggressiveness"] > 0.5 and norm["stubbornness"] > 0.8 and norm["cooperation"] < 0.4,
        },
        "The Scholar": {
            "description": "High evidence use, high novelty retention, moderate cooperation — wins through evidence quality",
            "match": norm["evidence_use"] > 0.4 and norm["novelty_retention"] > 0.6 and norm["cooperation"] > 0.3,
        },
        "The Chameleon": {
            "description": "Low stubbornness, high volatility, adaptive confidence — shifts positions strategically",
            "match": norm["stubbornness"] < 0.7 and norm["volatility"] > 0.3,
        },
        "The Wall": {
            "description": "Maximum stubbornness, high confidence, low volatility — unmovable regardless of evidence",
            "match": norm["stubbornness"] > 0.9 and norm["confidence"] > 0.7 and norm["volatility"] < 0.2,
        },
        "The Diplomat": {
            "description": "High cooperation, moderate hedging, balanced aggression — seeks common ground",
            "match": norm["cooperation"] > 0.6 and norm["hedging"] > 0.3 and norm["aggressiveness"] < 0.4,
        },
        "The Prosecutor": {
            "description": "High aggression + high evidence use — attacks with data-backed precision",
            "match": norm["aggressiveness"] > 0.4 and norm["evidence_use"] > 0.3 and norm["verbosity"] > 0.4,
        },
    }

    for name, info in archetypes.items():
        if info["match"]:
            return {"name": name, "description": info["description"]}

    return {"name": "The Generalist", "description": "Balanced behavioral profile — no dominant trait"}


# --- Strategy Effectiveness ---

def _strategy_effectiveness(debates: list[Debate]) -> list[dict]:
    """Compare strategies on accuracy, efficiency, and behavioral metrics with CIs."""
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

        acc_ci = _confidence_interval_95(accuracies)

        results.append({
            "strategy": strategy,
            "total_debates": n,
            "accuracy": _safe_mean(accuracies),
            "accuracy_std": _safe_std(accuracies),
            "accuracy_ci_lower": acc_ci[0],
            "accuracy_ci_upper": acc_ci[1],
            "avg_latency_ms": _safe_mean(latencies),
            "avg_tokens": _safe_mean(tokens),
            "avg_turns": _safe_mean(turns),
            "deadlock_rate": round(deadlocks / n, 4) if n else 0,
            "avg_confidence": _safe_mean(all_confidence),
            "confidence_std": _safe_std(all_confidence),
            "confidence_ci": _confidence_interval_95(all_confidence),
            "avg_aggressiveness": _safe_mean(all_aggression),
            "aggressiveness_ci": _confidence_interval_95(all_aggression),
            "avg_sentiment": _safe_mean(all_sentiment),
            "avg_novelty": _safe_mean(all_novelty),
            "position_change_rate": round(position_changes / total_turns_counted, 4) if total_turns_counted else 0,
        })

    return sorted(results, key=lambda r: r["accuracy"], reverse=True)


# --- Source Quality Impact ---

def _source_quality_impact(debates: list[Debate]) -> dict:
    """Analyze how source reliability correlates with winning the debate."""
    winning_reliabilities = []
    losing_reliabilities = []
    all_correlations = []

    for d in debates:
        if not d.scenario or not d.final_answer:
            continue

        for agent in d.agents:
            briefings = d.scenario.agent_briefings or []
            agent_briefing = None
            for b in briefings:
                if b.get("position", "").lower().strip() == (agent.assigned_position or "").lower().strip():
                    agent_briefing = b
                    break

            if not agent_briefing:
                continue

            reliability = agent_briefing.get("source_reliability", 0.5)
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

    # Statistical test: is winning reliability significantly different from losing?
    reliability_ttest = _welch_t_test(winning_reliabilities, losing_reliabilities)

    return {
        "avg_winning_source_reliability": _safe_mean(winning_reliabilities),
        "avg_losing_source_reliability": _safe_mean(losing_reliabilities),
        "reliability_gap": round(
            _safe_mean(winning_reliabilities) - _safe_mean(losing_reliabilities), 4
        ),
        "reliability_effect_size": _cohens_d(winning_reliabilities, losing_reliabilities),
        "reliability_effect_magnitude": _effect_size_label(_cohens_d(winning_reliabilities, losing_reliabilities)),
        "reliability_ttest": reliability_ttest,
        "source_type_win_rates": source_type_win_rates,
        "total_data_points": len(all_correlations),
        "finding": (
            (
                f"ALARMING: Lower-reliability sources (misinfo) significantly MORE likely to win debates "
                f"(winners avg {_safe_mean(winning_reliabilities):.2f} vs losers {_safe_mean(losing_reliabilities):.2f}, "
                f"d={_cohens_d(winning_reliabilities, losing_reliabilities):.2f}, p={reliability_ttest['p_value']})"
                if _safe_mean(winning_reliabilities) < _safe_mean(losing_reliabilities)
                else f"Higher source reliability significantly predicts winning "
                f"(d={_cohens_d(winning_reliabilities, losing_reliabilities):.2f}, p={reliability_ttest['p_value']})"
            )
            if reliability_ttest.get("significant")
            else "Source reliability does NOT significantly predict debate outcomes"
            if len(all_correlations) > 5
            else "Insufficient data for statistical testing"
        ),
    }


# --- Model Behavioral Profiles ---

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
            "confidence_ci": _confidence_interval_95(md["confidences"]),
            "avg_aggressiveness": _safe_mean(md["aggressiveness"]),
            "avg_sentiment": _safe_mean(md["sentiments"]),
            "avg_novelty": _safe_mean(md["novelty"]),
            "avg_citations_per_turn": _safe_mean(md["citations"]),
            "avg_hedging_per_turn": _safe_mean(md["hedging"]),
            "avg_word_count": _safe_mean(md["word_counts"]),
            "position_change_rate": round(md["position_changes"] / tc, 4),
            "behavioral_type": _classify_behavior(
                _safe_mean(md["aggressiveness"]),
                _safe_mean(md["sentiments"]),
                round(md["position_changes"] / tc, 4),
            ),
        }
        profiles.append(profile)

    return sorted(profiles, key=lambda p: p["total_debates"], reverse=True)


def _classify_behavior(aggression: float, sentiment: float, change_rate: float) -> str:
    if aggression > 0.5 and sentiment < 0:
        return "Aggressive Debater"
    if change_rate > 0.1 and sentiment > 0.2:
        return "Open-Minded Collaborator"
    if aggression < 0.2 and change_rate < 0.02:
        return "Stubborn Defender"
    if aggression > 0.3 and change_rate < 0.02:
        return "Assertive Advocate"
    return "Balanced Participant"


# --- Position Change Dynamics ---

def _position_change_dynamics(debates: list[Debate]) -> dict:
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


# --- Misinformation Resistance ---

def _misinformation_resistance(debates: list[Debate]) -> dict:
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

    role_effectiveness = defaultdict(lambda: {"wins": 0, "total": 0})
    for d in misinfo_debates:
        for agent in d.agents:
            if not agent.bias_role:
                continue
            role_effectiveness[agent.bias_role]["total"] += 1
            if d.final_answer and agent.assigned_position:
                if (d.final_answer.lower().strip() in agent.assigned_position.lower().strip()
                        or agent.assigned_position.lower().strip() in d.final_answer.lower().strip()):
                    role_effectiveness[agent.bias_role]["wins"] += 1

    role_win_rates = {
        role: round(d["wins"] / d["total"], 4) if d["total"] else 0
        for role, d in role_effectiveness.items()
    }

    # Chi-squared: is truth win rate significantly different from chance (50%)?
    chi2_truth = _chi_squared_2x2(truth_wins, misinfo_wins, total // 2, total - total // 2)

    return {
        "total_misinformation_debates": total,
        "truth_win_rate": round(truth_wins / total, 4) if total else 0,
        "misinformation_win_rate": round(misinfo_wins / total, 4) if total else 0,
        "truth_resistance_by_strategy": strategy_resistance,
        "bias_role_win_rates": role_win_rates,
        "statistical_test": chi2_truth,
        "best_strategy_for_truth": (
            max(strategy_resistance, key=strategy_resistance.get)
            if strategy_resistance else "insufficient_data"
        ),
        "finding": (
            f"Truth prevails {round(truth_wins / total * 100, 1)}% of the time "
            f"({'significantly above chance, p=' + str(chi2_truth['p_value']) if chi2_truth.get('significant') else 'not significantly different from chance'})"
            if total else "No data"
        ),
    }


# --- Argument Quality Over Rounds ---

def _argument_quality_over_rounds(debates: list[Debate]) -> dict:
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


# --- Deadlock Analysis ---

def _deadlock_analysis(debates: list[Debate]) -> dict:
    by_strategy = defaultdict(lambda: {"total": 0, "deadlocked": 0})
    model_pair_deadlocks = defaultdict(lambda: {"total": 0, "deadlocked": 0})

    for d in debates:
        by_strategy[d.strategy]["total"] += 1
        if d.deadlock_detected:
            by_strategy[d.strategy]["deadlocked"] += 1

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


# --- Key Findings Generator ---

def _generate_key_findings(debates: list[Debate]) -> list[str]:
    """Auto-generate publication-ready key research findings with statistical backing."""
    findings = []
    n = len(debates)
    correct = sum(1 for d in debates if d.is_correct)
    deadlocked = sum(1 for d in debates if d.deadlock_detected)

    findings.append(
        f"Across {n} multi-agent debates, overall system accuracy is {round(correct / n * 100, 1)}% "
        f"with a {round(deadlocked / n * 100, 1)}% deadlock rate "
        f"(95% CI for accuracy: [{round((correct/n - 1.96*math.sqrt(correct/n*(1-correct/n)/n))*100, 1)}%, "
        f"{round((correct/n + 1.96*math.sqrt(correct/n*(1-correct/n)/n))*100, 1)}%])"
    )

    # Best strategy with CI
    by_strategy = defaultdict(list)
    for d in debates:
        by_strategy[d.strategy].append(d)

    if len(by_strategy) >= 2:
        strategy_acc = {
            s: sum(1 for d in ds if d.is_correct) / len(ds)
            for s, ds in by_strategy.items()
        }
        best = max(strategy_acc, key=strategy_acc.get)
        worst = min(strategy_acc, key=strategy_acc.get)

        # Effect size between best and worst
        best_acc = [1.0 if d.is_correct else 0.0 for d in by_strategy[best]]
        worst_acc = [1.0 if d.is_correct else 0.0 for d in by_strategy[worst]]
        d_val = _cohens_d(best_acc, worst_acc)

        findings.append(
            f"'{best}' achieves highest accuracy ({round(strategy_acc[best] * 100, 1)}%) vs "
            f"'{worst}' ({round(strategy_acc[worst] * 100, 1)}%) — "
            f"Cohen's d = {d_val} ({_effect_size_label(d_val)} effect)"
        )

    # Misinformation finding
    misinfo = [d for d in debates if d.scenario and d.scenario.category == "misinformation_battle"]
    if misinfo:
        truth_wins = sum(1 for d in misinfo if d.is_correct)
        findings.append(
            f"In {len(misinfo)} misinformation battles, truth prevails {round(truth_wins / len(misinfo) * 100, 1)}% "
            f"of the time — {'demonstrating robust misinformation resistance' if truth_wins / len(misinfo) > 0.6 else 'revealing vulnerability to sophisticated disinformation'}"
        )

    # Deadlock patterns
    if deadlocked > 0:
        dl_strategies = defaultdict(int)
        for d in debates:
            if d.deadlock_detected:
                dl_strategies[d.strategy] += 1
        most_dl = max(dl_strategies, key=dl_strategies.get)
        findings.append(
            f"Deadlocks occur most with '{most_dl}' ({dl_strategies[most_dl]}/{deadlocked} total) — "
            f"indicating this strategy is most susceptible to argumentative stalemate"
        )

    # Aggressiveness escalation finding
    all_aggr_r1 = []
    all_aggr_last = []
    for d in debates:
        by_round = defaultdict(list)
        for t in d.turns:
            if t.metrics and t.metrics.aggressiveness_score is not None:
                by_round[t.round_number].append(t.metrics.aggressiveness_score)
        rounds = sorted(by_round.keys())
        if len(rounds) >= 2:
            all_aggr_r1.extend(by_round[rounds[0]])
            all_aggr_last.extend(by_round[rounds[-1]])

    if all_aggr_r1 and all_aggr_last:
        t_result = _welch_t_test(all_aggr_r1, all_aggr_last)
        delta = _safe_mean(all_aggr_last) - _safe_mean(all_aggr_r1)
        direction = "escalates" if delta > 0 else "de-escalates"
        findings.append(
            f"Aggressiveness {direction} from R1 ({_safe_mean(all_aggr_r1):.2f}) to final round "
            f"({_safe_mean(all_aggr_last):.2f}) — "
            f"{'statistically significant' if t_result.get('significant') else 'not statistically significant'} "
            f"(p={t_result.get('p_value', 'N/A')})"
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
            f"Agents change position in only {change_pct}% of turns ({total_changes}/{total_turns}) — "
            f"{'indicating high epistemic rigidity across all models' if change_pct < 5 else 'showing moderate flexibility in agent positions'}"
        )

    return findings
