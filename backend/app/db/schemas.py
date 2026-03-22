from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# --- Scenario Schemas ---
class AgentBriefing(BaseModel):
    agent_label: str
    position: str
    briefing: str
    source_type: str
    source_reliability: float = Field(ge=0.0, le=1.0)


class ScenarioCreate(BaseModel):
    category: str
    title: str
    description: Optional[str] = None
    question: str
    agent_briefings: list[AgentBriefing]
    ground_truth: str
    ground_truth_explanation: Optional[str] = None
    difficulty: str = "medium"
    evaluation_criteria: Optional[dict] = None
    metadata_json: Optional[dict] = None


class ScenarioResponse(BaseModel):
    id: str
    category: str
    title: str
    description: Optional[str]
    question: str
    agent_briefings: list[dict]
    ground_truth: str
    ground_truth_explanation: Optional[str]
    difficulty: str
    evaluation_criteria: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Debate Schemas ---
class AgentConfig(BaseModel):
    agent_name: str
    provider: str  # groq, cerebras, openrouter
    model_id: str
    role: str = "advocate"
    briefing_index: Optional[int] = None  # None = auto-assign by position (0, 1, 2...)


class DebateCreate(BaseModel):
    scenario_id: str
    strategy: str  # majority_voting, structured_debate, hierarchical, evidence_weighted
    agents: list[AgentConfig]
    experiment_id: Optional[str] = None
    max_rounds: int = 5


class TurnMetricsResponse(BaseModel):
    aggressiveness_score: float
    sentiment_score: float
    persuasion_attempt_score: float
    citation_count: int
    citation_quality_score: float
    semantic_similarity_to_prev: Optional[float]
    argument_novelty_score: Optional[float]
    word_count: int
    hedging_language_count: int

    model_config = {"from_attributes": True}


class TurnResponse(BaseModel):
    id: str
    turn_number: int
    round_number: int
    role: str
    agent_name: str
    agent_provider: str
    agent_model: str
    content: str
    reasoning: Optional[str]
    confidence_score: Optional[float]
    position_held: Optional[str]
    position_changed: bool
    change_reason: Optional[str]
    total_tokens: int
    latency_ms: int
    metrics: Optional[TurnMetricsResponse]
    created_at: datetime


class DebateAgentResponse(BaseModel):
    id: str
    agent_name: str
    provider: str
    model_id: str
    role: str
    assigned_position: Optional[str]

    model_config = {"from_attributes": True}


class DebateResponse(BaseModel):
    id: str
    experiment_id: Optional[str]
    scenario_id: str
    strategy: str
    status: str
    final_answer: Optional[str]
    is_correct: Optional[bool]
    total_tokens: int
    total_latency_ms: int
    total_turns: int
    deadlock_detected: bool
    deadlock_resolution: Optional[str]
    agents: list[DebateAgentResponse]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class DebateDetailResponse(DebateResponse):
    turns: list[TurnResponse]
    scenario: Optional[ScenarioResponse]


# --- Experiment Schemas ---
class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scenario_ids: list[str]
    strategies: list[str]
    agent_configs: list[AgentConfig]


class ExperimentResultResponse(BaseModel):
    strategy: str
    provider: str
    model_id: str
    total_debates: int
    accuracy: float
    avg_latency_ms: float
    avg_tokens: float
    avg_turns: float
    deadlock_rate: float
    avg_confidence: float
    avg_aggressiveness: float

    model_config = {"from_attributes": True}


class ExperimentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    debate_count: int = 0
    results: list[ExperimentResultResponse] = []

    model_config = {"from_attributes": True}


# --- Admin Schemas ---
class OverviewStats(BaseModel):
    total_debates: int
    total_experiments: int
    avg_accuracy: float
    avg_latency_ms: float
    deadlock_rate: float
    total_scenarios: int


class StrategyComparison(BaseModel):
    strategy: str
    total_debates: int
    accuracy: float
    avg_latency_ms: float
    avg_tokens: float
    avg_turns: float
    deadlock_rate: float
    avg_confidence: float
    avg_aggressiveness: float


class ModelComparison(BaseModel):
    provider: str
    model_id: str
    total_debates: int
    accuracy: float
    avg_latency_ms: float
    avg_tokens: float
    avg_confidence: float
    avg_aggressiveness: float


class ConfidenceTrajectoryPoint(BaseModel):
    turn_number: int
    agent_name: str
    provider: str
    model_id: str
    confidence: float


class AggressivenessHeatmapCell(BaseModel):
    model_id: str
    strategy: str
    avg_aggressiveness: float
    debate_count: int
