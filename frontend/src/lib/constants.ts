export const STRATEGY_LABELS: Record<string, string> = {
  majority_voting: "Majority Voting",
  structured_debate: "Structured Debate",
  hierarchical: "Hierarchical Authority",
  evidence_weighted: "Evidence-Weighted Consensus",
};

export const STRATEGY_DESCRIPTIONS: Record<string, string> = {
  majority_voting: "Each agent votes independently. Simple majority wins.",
  structured_debate: "Multi-round argumentation. Agents debate until convergence or deadlock.",
  hierarchical: "One lead agent decides after hearing subordinate briefs.",
  evidence_weighted: "Agents rank source reliability, then vote with weighted evidence.",
};

export const STRATEGY_COLORS: Record<string, string> = {
  majority_voting: "#FF6B6B",
  structured_debate: "#4ECDC4",
  hierarchical: "#6C5CE7",
  evidence_weighted: "#FFD93D",
};

export const PROVIDER_COLORS: Record<string, string> = {
  groq: "#FF6B6B",
  cerebras: "#6C5CE7",
  openrouter: "#2ECC71",
};

export const PROVIDER_LABELS: Record<string, string> = {
  groq: "Groq",
  cerebras: "Cerebras",
  openrouter: "OpenRouter",
};

export const AGENT_COLORS = ["#FF6B6B", "#4ECDC4", "#FFD93D", "#6C5CE7", "#FF8A5C"];

export const CATEGORY_LABELS: Record<string, string> = {
  factual: "Factual Contradictions",
  evidence_quality: "Evidence Quality",
  instruction_conflict: "Instruction Conflicts",
};

export const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "#2ECC71",
  medium: "#FFD93D",
  hard: "#FF6B6B",
};

export const STATUS_COLORS: Record<string, string> = {
  pending: "#6B7280",
  running: "#4ECDC4",
  completed: "#2ECC71",
  failed: "#FF6B6B",
  deadlocked: "#FFD93D",
};
