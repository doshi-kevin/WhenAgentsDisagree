"""Shared node functions used across LangGraph workflows."""
import json
from datetime import datetime, timezone
from app.agents.conflict_agent import ConflictAgent
from app.agents.judge_agent import JudgeAgent
from app.metrics.collector import MetricsCollector
from app.graphs.state import DebateState, AgentInfo, TurnRecord

# Per-debate metrics collectors (keyed by debate_id)
_collectors: dict[str, MetricsCollector] = {}


def get_collector(debate_id: str, threshold: float = 0.90) -> MetricsCollector:
    """Get or create a metrics collector for a debate."""
    if debate_id not in _collectors:
        _collectors[debate_id] = MetricsCollector(similarity_threshold=threshold)
    return _collectors[debate_id]


def cleanup_collector(debate_id: str):
    """Remove collector after debate completes."""
    _collectors.pop(debate_id, None)


def create_agent_from_info(info: AgentInfo) -> ConflictAgent:
    """Create a ConflictAgent from AgentInfo."""
    return ConflictAgent(
        agent_id=info["agent_id"],
        name=info["name"],
        provider=info["provider"],
        model_id=info["model_id"],
        role=info["role"],
        briefing=info["briefing"],
        source_type=info["source_type"],
        position=info["position"],
        bias_role=info.get("bias_role", ""),
    )


def create_judge(state: DebateState, name: str = "Judge") -> JudgeAgent:
    """Create a JudgeAgent using the first available provider."""
    agents = state["agents"]
    # Use the first agent's provider for the judge
    return JudgeAgent(
        name=name,
        provider=agents[0]["provider"],
        model_id=agents[0]["model_id"],
    )


def format_conversation_history(turns: list[TurnRecord]) -> str:
    """Format turn history into readable conversation."""
    if not turns:
        return "No previous discussion yet."

    lines = []
    for t in turns:
        parsed = t.get("parsed") or {}
        content = parsed.get("argument") or parsed.get("reasoning") or t.get("content", "")
        position = t.get("position_held", "")
        confidence = t.get("confidence", 0.5)

        line = f"**{t['agent_name']}** (Position: {position}, Confidence: {confidence:.2f}):\n{content}"
        if t.get("position_changed"):
            line += f"\n[POSITION CHANGED: {t.get('change_reason', 'No reason given')}]"
        lines.append(line)

    return "\n\n---\n\n".join(lines)


def format_subordinate_briefs(turns: list[TurnRecord]) -> str:
    """Format subordinate briefs for lead agent."""
    lines = []
    for t in turns:
        if t["role"] != "argument":
            continue
        parsed = t.get("parsed") or {}
        summary = parsed.get("summary", t.get("content", ""))
        recommendation = parsed.get("recommendation", "")
        confidence = parsed.get("confidence", t.get("confidence", 0.5))
        evidence = parsed.get("key_evidence", [])

        line = f"### {t['agent_name']}\n"
        line += f"**Summary:** {summary}\n"
        line += f"**Recommendation:** {recommendation}\n"
        line += f"**Confidence:** {confidence}\n"
        if evidence:
            line += f"**Key Evidence:** {', '.join(str(e) for e in evidence)}\n"
        lines.append(line)

    return "\n\n".join(lines)


def build_turn_record(
    agent_info: AgentInfo,
    turn_result: dict,
    turn_number: int,
    round_number: int,
    role: str,
    metrics: dict,
) -> TurnRecord:
    """Build a TurnRecord from agent invocation result."""
    return {
        "turn_number": turn_number,
        "round_number": round_number,
        "agent_id": agent_info["agent_id"],
        "agent_name": agent_info["name"],
        "provider": agent_info["provider"],
        "model_id": agent_info["model_id"],
        "role": role,
        "content": turn_result.get("content", ""),
        "parsed": turn_result.get("parsed"),
        "confidence": turn_result.get("confidence", 0.5),
        "position_held": turn_result.get("position_held", ""),
        "position_changed": turn_result.get("position_changed", False),
        "change_reason": turn_result.get("change_reason"),
        "prompt_tokens": turn_result.get("prompt_tokens", 0),
        "completion_tokens": turn_result.get("completion_tokens", 0),
        "total_tokens": turn_result.get("total_tokens", 0),
        "latency_ms": turn_result.get("latency_ms", 0),
        "metrics": metrics,
    }


def check_answer_correctness(answer: str, ground_truth: str, evaluation_criteria: dict = None) -> bool:
    """Check if an answer matches ground truth."""
    if not answer or not ground_truth:
        return False

    answer_lower = answer.lower().strip()
    truth_lower = ground_truth.lower().strip()

    # Direct match
    if answer_lower == truth_lower:
        return True

    # Check if answer contains truth or vice versa
    if truth_lower in answer_lower or answer_lower in truth_lower:
        return True

    # Normalize: underscores/hyphens to spaces for matching
    truth_normalized = truth_lower.replace("_", " ").replace("-", " ")
    answer_normalized = answer_lower.replace("_", " ").replace("-", " ")

    # Check containment after normalization
    if truth_normalized in answer_normalized or answer_normalized in truth_normalized:
        return True

    # Remove stopwords for content comparison
    stopwords = {"a", "an", "the", "is", "are", "was", "were", "be", "been",
                 "and", "or", "but", "in", "on", "at", "to", "for", "of",
                 "with", "by", "from", "it", "that", "this", "not", "no"}
    truth_content = [w for w in truth_normalized.split() if w not in stopwords]
    answer_content = [w for w in answer_normalized.split() if w not in stopwords]

    # Check if all content words of truth appear in answer
    if truth_content and all(w in answer_normalized for w in truth_content):
        return True

    # Check if all content words of answer appear in truth
    if answer_content and all(w in truth_normalized for w in answer_content):
        return True

    # Check significant content word overlap (>= 50%)
    if truth_content:
        matching = sum(1 for w in truth_content if w in answer_normalized)
        if matching / len(truth_content) >= 0.5:
            return True

    # Check evaluation criteria if available
    if evaluation_criteria:
        strict = evaluation_criteria.get("strict_match", [])
        for s in strict:
            if s.lower() in answer_lower:
                return True

        partial = evaluation_criteria.get("partial_match", [])
        for p in partial:
            if p.lower() in answer_lower:
                return True

    return False


def create_event(event_type: str, data: dict) -> dict:
    """Create a streaming event."""
    return {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
