"""Persuasion and mind-change tracking."""
from typing import Optional


def detect_position_change(
    current_position: Optional[str],
    previous_position: Optional[str],
    parsed: Optional[dict] = None,
) -> dict:
    """Detect if an agent changed its position."""
    if not current_position or not previous_position:
        return {
            "position_changed": False,
            "from_position": previous_position,
            "to_position": current_position,
            "change_reason": None,
        }

    changed = current_position.lower().strip() != previous_position.lower().strip()

    # Also check the parsed response for explicit declaration
    if parsed and parsed.get("position_changed"):
        changed = True

    return {
        "position_changed": changed,
        "from_position": previous_position,
        "to_position": current_position if changed else previous_position,
        "change_reason": parsed.get("change_reason") if parsed and changed else None,
    }


def analyze_persuasion_flow(debate_turns: list[dict]) -> list[dict]:
    """Analyze the full persuasion flow across a debate.

    Returns a list of persuasion events (mind-changes).
    """
    events = []
    agent_positions: dict[str, str] = {}

    for turn in debate_turns:
        agent_id = turn.get("agent_id", "")
        agent_name = turn.get("agent_name", "")
        position = turn.get("position_held", "")
        turn_number = turn.get("turn_number", 0)
        round_number = turn.get("round_number", 1)

        if agent_id in agent_positions:
            prev = agent_positions[agent_id]
            if position and prev and position.lower().strip() != prev.lower().strip():
                # Find which opponent likely caused the change
                # Look at the most recent turn before this one from an agent with the new position
                influencer = None
                for prev_turn in reversed(debate_turns):
                    if prev_turn.get("turn_number", 0) >= turn_number:
                        continue
                    if prev_turn.get("agent_id") == agent_id:
                        continue
                    prev_pos = prev_turn.get("position_held", "")
                    if prev_pos and prev_pos.lower().strip() == position.lower().strip():
                        influencer = prev_turn.get("agent_name", "")
                        break

                events.append({
                    "agent_name": agent_name,
                    "from_position": prev,
                    "to_position": position,
                    "at_turn": turn_number,
                    "at_round": round_number,
                    "likely_influencer": influencer,
                    "change_reason": turn.get("change_reason"),
                })

        if position:
            agent_positions[agent_id] = position

    return events
