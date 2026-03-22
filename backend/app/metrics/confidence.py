"""Confidence score extraction and tracking."""
import re
from typing import Optional


def extract_confidence(parsed: Optional[dict], content: str) -> float:
    """Extract confidence score from parsed response or raw content."""
    # Strategy 1: From parsed JSON
    if parsed and "confidence" in parsed:
        try:
            conf = float(parsed["confidence"])
            return max(0.0, min(1.0, conf))
        except (ValueError, TypeError):
            pass

    # Strategy 2: Regex from raw content
    patterns = [
        r'confidence["\s:]+([0-9]+\.?[0-9]*)',
        r'(\d+\.?\d*)\s*(?:out of|/)\s*(?:1\.0|1|10)',
        r'(?:I am|I\'m)\s+(\d+)%?\s+(?:confident|certain|sure)',
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                if val > 1.0:
                    val = val / 100.0 if val <= 100 else val / 10.0
                return max(0.0, min(1.0, val))
            except ValueError:
                continue

    return 0.5  # Default confidence


def track_confidence_trajectory(turns: list[dict]) -> list[dict]:
    """Track confidence changes across turns for an agent."""
    trajectory = []
    for i, turn in enumerate(turns):
        trajectory.append({
            "turn_number": i + 1,
            "confidence": turn.get("confidence", 0.5),
            "position": turn.get("position_held", ""),
            "position_changed": turn.get("position_changed", False),
        })
    return trajectory
