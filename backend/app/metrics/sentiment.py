"""Sentiment analysis - cooperative vs adversarial scoring."""
import re

COOPERATIVE_WORDS = [
    "agree", "understand", "fair", "valid", "good point", "appreciate",
    "acknowledge", "reasonable", "common ground", "compromise", "collaborate",
    "together", "shared", "mutual", "respect", "thank", "helpful",
    "constructive", "balanced", "nuanced", "open-minded", "insightful",
    "well-reasoned", "compelling", "interesting", "thoughtful", "excellent",
    "correct", "rightly", "indeed", "absolutely right", "good observation",
    "well put", "i concur", "builds on", "complements", "strengthens",
    "consensus", "aligned", "harmonize", "bridge", "reconcile",
]

ADVERSARIAL_WORDS = [
    "wrong", "incorrect", "false", "misleading", "flawed", "reject",
    "refuse", "unacceptable", "nonsense", "absurd", "ridiculous",
    "impossible", "foolish", "ignorant", "biased", "propaganda",
    "misinformation", "deceptive", "dishonest", "manipulative",
    "dangerous", "irresponsible", "baseless", "unfounded",
    "pseudoscience", "debunked", "discredited", "unreliable",
    "contradicts", "undermines", "disproves", "refutes",
    "cherry-pick", "fallacy", "logical error", "misrepresent",
    "distort", "exaggerate", "fabricate", "unsupported",
]


def score_sentiment(content: str) -> float:
    """Score sentiment from -1.0 (adversarial) to 1.0 (cooperative).

    Returns 0.0 for neutral.
    """
    content_lower = content.lower()
    word_count = len(content.split())

    if word_count == 0:
        return 0.0

    coop_count = sum(
        len(re.findall(r'\b' + re.escape(w) + r'\b', content_lower))
        for w in COOPERATIVE_WORDS
    )
    adv_count = sum(
        len(re.findall(r'\b' + re.escape(w) + r'\b', content_lower))
        for w in ADVERSARIAL_WORDS
    )

    if coop_count == 0 and adv_count == 0:
        return 0.0

    # Net sentiment normalized by total markers
    total_markers = coop_count + adv_count
    raw_score = (coop_count - adv_count) / total_markers  # -1 to 1

    # Scale slightly to avoid extremes being too easy to hit
    # Most debate text should fall between -0.7 and 0.7
    return round(raw_score * 0.85, 4)


def analyze_sentiment_trajectory(turns: list[dict]) -> list[dict]:
    """Analyze how sentiment changes over the course of a debate."""
    trajectory = []
    for turn in turns:
        content = turn.get("content", "")
        trajectory.append({
            "turn_number": turn.get("turn_number", 0),
            "agent_name": turn.get("agent_name", ""),
            "sentiment_score": score_sentiment(content),
        })
    return trajectory
