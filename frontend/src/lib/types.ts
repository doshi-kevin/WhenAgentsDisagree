// --- Core Types ---
export interface Scenario {
  id: string;
  category: string;
  title: string;
  description: string | null;
  question: string;
  agent_briefings: AgentBriefing[];
  ground_truth: string;
  ground_truth_explanation: string | null;
  difficulty: string;
  evaluation_criteria: Record<string, string[]> | null;
  created_at: string;
}

export interface AgentBriefing {
  agent_label: string;
  position: string;
  briefing: string;
  source_type: string;
  source_reliability: number;
  bias_role?: string;
}

export interface DebateAgent {
  id: string;
  agent_name: string;
  provider: string;
  model_id: string;
  role: string;
  assigned_position: string | null;
  bias_role?: string;
}

export interface TurnMetrics {
  aggressiveness_score: number;
  sentiment_score: number;
  persuasion_attempt_score: number;
  citation_count: number;
  citation_quality_score: number;
  semantic_similarity_to_prev: number | null;
  argument_novelty_score: number | null;
  word_count: number;
  hedging_language_count: number;
}

export interface Turn {
  id: string;
  turn_number: number;
  round_number: number;
  role: string;
  agent_name: string;
  agent_provider: string;
  agent_model: string;
  content: string;
  reasoning: string | null;
  confidence_score: number | null;
  position_held: string | null;
  position_changed: boolean;
  change_reason: string | null;
  total_tokens: number;
  latency_ms: number;
  metrics: TurnMetrics | null;
  created_at: string;
}

export interface Debate {
  id: string;
  experiment_id: string | null;
  scenario_id: string;
  strategy: string;
  status: string;
  final_answer: string | null;
  is_correct: boolean | null;
  total_tokens: number;
  total_latency_ms: number;
  total_turns: number;
  deadlock_detected: boolean;
  deadlock_resolution: string | null;
  agents: DebateAgent[];
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface DebateDetail extends Debate {
  turns: Turn[];
  scenario?: Scenario;
}

export interface Experiment {
  id: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  completed_at: string | null;
  debate_count?: number;
  results?: ExperimentResult[];
}

export interface ExperimentResult {
  strategy: string;
  provider: string;
  model_id: string;
  total_debates: number;
  accuracy: number;
  avg_latency_ms: number;
  avg_tokens: number;
  avg_turns: number;
  deadlock_rate: number;
  avg_confidence: number;
  avg_aggressiveness: number;
}

// --- Config Types ---
export interface AgentConfig {
  agent_name: string;
  provider: string;
  model_id: string;
  role: string;
  briefing_index: number;
}

export interface ModelInfo {
  provider: string;
  provider_display: string;
  model_id: string;
  model_display: string;
  rate_limits: Record<string, number | null>;
  color: string;
}

// --- Admin Types ---
export interface OverviewStats {
  total_debates: number;
  total_experiments: number;
  avg_accuracy: number;
  avg_latency_ms: number;
  deadlock_rate: number;
  total_scenarios: number;
}

export interface StrategyComparison {
  strategy: string;
  total_debates: number;
  accuracy: number;
  avg_latency_ms: number;
  avg_tokens: number;
  avg_turns: number;
  deadlock_rate: number;
  avg_confidence: number;
  avg_aggressiveness: number;
}

export interface ModelComparison {
  provider: string;
  model_id: string;
  total_debates: number;
  accuracy: number;
  avg_latency_ms: number;
  avg_tokens: number;
  avg_confidence: number;
  avg_aggressiveness: number;
}

// --- SSE Event Types ---
export interface SSEEvent {
  type: string;
  data: Record<string, any>;
  timestamp?: string;
}
