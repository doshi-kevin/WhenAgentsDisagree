"""Central metrics collector that aggregates all behavioral metrics per debate."""
import json
from typing import Optional
from app.metrics.confidence import extract_confidence
from app.metrics.aggressiveness import score_aggressiveness
from app.metrics.sentiment import score_sentiment
from app.metrics.citation_quality import analyze_citations
from app.metrics.deadlock import DeadlockDetector
from app.metrics.persuasion import detect_position_change


def _extract_argument_text(content: str, parsed: Optional[dict]) -> str:
    """Extract the actual argument/reasoning text from LLM response.

    LLMs often output JSON. We need the natural language text for metrics.
    """
    # Try to get text from parsed JSON fields
    if parsed:
        # Check common fields in order of preference
        for field in ["argument", "reasoning", "analysis", "summary",
                      "explanation", "rationale", "justification",
                      "evidence_analysis", "key_evidence", "response",
                      "decision_reasoning", "brief"]:
            val = parsed.get(field)
            if val and isinstance(val, str) and len(val) > 20:
                return val
            elif val and isinstance(val, list):
                return " ".join(str(v) for v in val)

    # Try to parse content as JSON and extract text
    try:
        data = json.loads(content) if isinstance(content, str) else content
        if isinstance(data, dict):
            texts = []
            for field in ["argument", "reasoning", "analysis", "summary",
                          "explanation", "rationale", "vote", "decision",
                          "evidence_analysis", "brief"]:
                val = data.get(field)
                if val and isinstance(val, str):
                    texts.append(val)
            if texts:
                return " ".join(texts)
    except (json.JSONDecodeError, TypeError):
        pass

    # Fall back to raw content
    return content


class MetricsCollector:
    """Collects and computes all behavioral metrics for a debate."""

    def __init__(self, similarity_threshold: float = 0.90):
        self.deadlock_detector = DeadlockDetector(
            similarity_threshold=similarity_threshold
        )
        self.all_turn_metrics: list[dict] = []
        self.agent_previous_positions: dict[str, str] = {}

    def compute_turn_metrics(
        self,
        agent_id: str,
        agent_name: str,
        content: str,
        parsed: Optional[dict],
        source_type: str = "unknown",
    ) -> dict:
        """Compute all metrics for a single turn."""
        # Extract actual argument text for linguistic analysis
        argument_text = _extract_argument_text(content, parsed)

        # Confidence
        confidence = extract_confidence(parsed, content)

        # Aggressiveness - use argument text for accurate scoring
        aggr = score_aggressiveness(argument_text)

        # Sentiment - use argument text
        sentiment = score_sentiment(argument_text)

        # Citation quality - use argument text
        citations = analyze_citations(argument_text, source_type)

        # Deadlock detection - use argument text for similarity
        deadlock_info = self.deadlock_detector.check_turn(agent_id, argument_text)

        # Position change
        current_position = None
        if parsed:
            current_position = (
                parsed.get("current_position")
                or parsed.get("vote")
                or parsed.get("decision")
                or parsed.get("recommendation")
            )

        prev_position = self.agent_previous_positions.get(agent_id)
        position_change = detect_position_change(current_position, prev_position, parsed)

        if current_position:
            self.agent_previous_positions[agent_id] = current_position

        metrics = {
            "confidence": confidence,
            "aggressiveness_score": aggr["aggressiveness_score"],
            "sentiment_score": sentiment,
            "persuasion_attempt_score": aggr["persuasion_attempt_score"],
            "citation_count": citations["citation_count"],
            "citation_quality_score": citations["citation_quality_score"],
            "semantic_similarity_to_prev": deadlock_info["semantic_similarity_to_prev"],
            "argument_novelty_score": deadlock_info["argument_novelty_score"],
            "word_count": aggr["word_count"],
            "hedging_language_count": aggr["hedging_language_count"],
            "is_repeating": deadlock_info["is_repeating"],
            "position_changed": position_change["position_changed"],
            "position_held": current_position or prev_position,
            "change_reason": position_change["change_reason"],
        }

        self.all_turn_metrics.append({
            "agent_id": agent_id,
            "agent_name": agent_name,
            **metrics,
        })

        return metrics

    def check_deadlock(self) -> dict:
        """Check if the debate is deadlocked."""
        return self.deadlock_detector.is_deadlocked()

    def get_summary(self) -> dict:
        """Get aggregate metrics summary for the debate."""
        if not self.all_turn_metrics:
            return {
                "avg_confidence": 0.0,
                "avg_aggressiveness": 0.0,
                "avg_sentiment": 0.0,
                "total_position_changes": 0,
                "total_citations": 0,
                "deadlock_status": self.check_deadlock(),
            }

        return {
            "avg_confidence": sum(m["confidence"] for m in self.all_turn_metrics) / len(self.all_turn_metrics),
            "avg_aggressiveness": sum(m["aggressiveness_score"] for m in self.all_turn_metrics) / len(self.all_turn_metrics),
            "avg_sentiment": sum(m["sentiment_score"] for m in self.all_turn_metrics) / len(self.all_turn_metrics),
            "total_position_changes": sum(1 for m in self.all_turn_metrics if m["position_changed"]),
            "total_citations": sum(m["citation_count"] for m in self.all_turn_metrics),
            "deadlock_status": self.check_deadlock(),
        }
