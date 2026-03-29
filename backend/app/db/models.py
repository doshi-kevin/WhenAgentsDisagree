import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.db.engine import Base


def gen_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, running, completed, failed
    config_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)

    debates = relationship("Debate", back_populates="experiment", cascade="all, delete-orphan")
    results = relationship("ExperimentResult", back_populates="experiment", cascade="all, delete-orphan")


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True, default=gen_uuid)
    category = Column(String, nullable=False)  # factual, evidence_quality, instruction_conflict
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    question = Column(Text, nullable=False)
    agent_briefings = Column(JSON, nullable=False)  # list of briefing objects
    ground_truth = Column(String, nullable=False)
    ground_truth_explanation = Column(Text, nullable=True)
    difficulty = Column(String, default="medium")  # easy, medium, hard
    evaluation_criteria = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    debates = relationship("Debate", back_populates="scenario")


class Debate(Base):
    __tablename__ = "debates"

    id = Column(String, primary_key=True, default=gen_uuid)
    experiment_id = Column(String, ForeignKey("experiments.id"), nullable=True)
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=False)
    strategy = Column(String, nullable=False)  # majority_voting, structured_debate, hierarchical, evidence_weighted
    status = Column(String, default="pending")  # pending, running, completed, deadlocked, failed
    final_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    total_tokens = Column(Integer, default=0)
    total_latency_ms = Column(Integer, default=0)
    total_turns = Column(Integer, default=0)
    deadlock_detected = Column(Boolean, default=False)
    deadlock_resolution = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    experiment = relationship("Experiment", back_populates="debates")
    scenario = relationship("Scenario", back_populates="debates")
    agents = relationship("DebateAgent", back_populates="debate", cascade="all, delete-orphan")
    turns = relationship("Turn", back_populates="debate", cascade="all, delete-orphan", order_by="Turn.turn_number")


class DebateAgent(Base):
    __tablename__ = "debate_agents"

    id = Column(String, primary_key=True, default=gen_uuid)
    debate_id = Column(String, ForeignKey("debates.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    provider = Column(String, nullable=False)  # groq, cerebras, openrouter
    model_id = Column(String, nullable=False)
    role = Column(String, default="advocate")  # advocate, judge, lead
    assigned_position = Column(Text, nullable=True)
    bias_role = Column(String, nullable=True)  # truth_teller, liar, manipulator
    briefing_index = Column(Integer, nullable=True)

    debate = relationship("Debate", back_populates="agents")
    turns = relationship("Turn", back_populates="agent", cascade="all, delete-orphan")


class Turn(Base):
    __tablename__ = "turns"

    id = Column(String, primary_key=True, default=gen_uuid)
    debate_id = Column(String, ForeignKey("debates.id"), nullable=False)
    debate_agent_id = Column(String, ForeignKey("debate_agents.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    round_number = Column(Integer, default=1)
    role = Column(String, default="argument")  # argument, vote, evaluation, rebuttal, final_decision
    content = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    position_held = Column(Text, nullable=True)
    position_changed = Column(Boolean, default=False)
    change_reason = Column(Text, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    raw_response_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    debate = relationship("Debate", back_populates="turns")
    agent = relationship("DebateAgent", back_populates="turns")
    metrics = relationship("TurnMetrics", back_populates="turn", uselist=False, cascade="all, delete-orphan")


class TurnMetrics(Base):
    __tablename__ = "turn_metrics"

    id = Column(String, primary_key=True, default=gen_uuid)
    turn_id = Column(String, ForeignKey("turns.id"), nullable=False)
    aggressiveness_score = Column(Float, default=0.0)
    sentiment_score = Column(Float, default=0.0)  # -1 adversarial to 1 cooperative
    persuasion_attempt_score = Column(Float, default=0.0)
    citation_count = Column(Integer, default=0)
    citation_quality_score = Column(Float, default=0.0)
    semantic_similarity_to_prev = Column(Float, nullable=True)
    argument_novelty_score = Column(Float, nullable=True)
    word_count = Column(Integer, default=0)
    hedging_language_count = Column(Integer, default=0)

    turn = relationship("Turn", back_populates="metrics")


class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id = Column(String, primary_key=True, default=gen_uuid)
    experiment_id = Column(String, ForeignKey("experiments.id"), nullable=False)
    strategy = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    model_id = Column(String, nullable=False)
    total_debates = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    avg_latency_ms = Column(Float, default=0.0)
    avg_tokens = Column(Float, default=0.0)
    avg_turns = Column(Float, default=0.0)
    deadlock_rate = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)
    avg_aggressiveness = Column(Float, default=0.0)
    computed_at = Column(DateTime, default=utcnow)

    experiment = relationship("Experiment", back_populates="results")
