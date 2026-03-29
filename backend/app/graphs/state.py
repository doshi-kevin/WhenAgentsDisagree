"""LangGraph state definitions for debate workflows."""
from typing import TypedDict, Annotated, Optional, Any
from operator import add


class AgentInfo(TypedDict):
    agent_id: str
    name: str
    provider: str
    model_id: str
    role: str
    briefing: str
    source_type: str
    source_reliability: float
    position: str
    bias_role: str


class TurnRecord(TypedDict):
    turn_number: int
    round_number: int
    agent_id: str
    agent_name: str
    provider: str
    model_id: str
    role: str
    content: str
    parsed: Optional[dict]
    confidence: float
    position_held: str
    position_changed: bool
    change_reason: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    metrics: dict
    error: Optional[str]


class DebateState(TypedDict):
    """Shared state for all LangGraph debate workflows."""
    # Immutable config
    debate_id: str
    scenario_id: str
    strategy: str
    question: str
    ground_truth: str
    max_rounds: int
    deadlock_threshold: float

    # Agents
    agents: list[AgentInfo]

    # Accumulating turns
    turns: Annotated[list[TurnRecord], add]

    # Mutable tracking
    current_round: int
    current_agent_index: int
    votes: dict  # agent_id -> voted_position
    source_rankings: dict  # agent_id -> rankings

    # Resolution
    final_answer: str
    is_resolved: bool
    is_correct: Optional[bool]
    deadlock_detected: bool
    deadlock_resolution: str

    # Streaming events
    events: Annotated[list[dict], add]

    # Error tracking
    error: Optional[str]
