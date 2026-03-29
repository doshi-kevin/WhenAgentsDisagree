"use client";
import { useState, useEffect } from "react";
import { getResearchInsights, getOverview } from "@/lib/api";
import { STRATEGY_LABELS, STRATEGY_COLORS } from "@/lib/constants";

const SECTION_STYLE = "nb-card p-6 md:p-8";
const H2 = "text-2xl font-black uppercase tracking-wider mb-4";
const H3 = "text-lg font-black uppercase tracking-wider mb-3";
const BADGE = "inline-block text-xs font-bold px-2.5 py-1 rounded border-2 border-[var(--border)] shadow-[2px_2px_0px_var(--shadow-color)]";

export default function AboutPage() {
  const [insights, setInsights] = useState<any>(null);
  const [overview, setOverview] = useState<any>(null);

  useEffect(() => {
    getResearchInsights().then(setInsights).catch(() => {});
    getOverview().then(setOverview).catch(() => {});
  }, []);

  const findings = insights?.key_findings || [];
  const strategies = insights?.strategy_effectiveness || [];
  const misinfo = insights?.misinformation_resistance || {};
  const sourceImpact = insights?.source_quality_impact || {};
  const profiles = insights?.model_behavioral_profiles || [];

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">
      {/* Hero */}
      <div className="text-center mb-4">
        <h1 className="text-4xl md:text-5xl font-black uppercase tracking-tight leading-tight">
          When Agents{" "}
          <span className="bg-[#FF6B6B] text-white px-3 py-1 border-2 border-[var(--border)] shadow-[3px_3px_0px_var(--shadow-color)] inline-block -rotate-1">
            Disagree
          </span>
        </h1>
        <p className="text-lg font-bold text-gray-600 mt-4 max-w-3xl mx-auto">
          A Research Platform for Studying Multi-Agent Conflict Resolution in LLM Systems
        </p>
        <p className="text-sm text-gray-500 mt-2">CS-584 Course Project</p>
      </div>

      {/* Research Question */}
      <div className={`${SECTION_STYLE} border-l-8 border-l-[#4ECDC4]`}>
        <h2 className={H2}>Research Question</h2>
        <blockquote className="text-lg italic font-medium text-gray-700 leading-relaxed">
          &ldquo;How do different conflict resolution strategies affect the accuracy, efficiency,
          and behavior of multi-LLM agent systems when agents are given contradictory
          instructions or evidence?&rdquo;
        </blockquote>
      </div>

      {/* What This Platform Does */}
      <div className={SECTION_STYLE}>
        <h2 className={H2}>What This Platform Does</h2>
        <p className="text-sm text-gray-600 mb-5 leading-relaxed">
          This platform creates controlled experiments where multiple LLM agents receive
          contradictory briefings about a factual question, then resolve their disagreement
          using one of four conflict resolution strategies. Every turn is instrumented with
          behavioral metrics, enabling quantitative comparison of strategies, models, and
          information quality effects.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { title: "Assign Contradictory Briefings", desc: "Each agent receives different (often conflicting) evidence about the same question, from sources of varying reliability.", color: "#FF6B6B" },
            { title: "Run Structured Debates", desc: "Agents argue across multiple rounds using one of four resolution strategies, with real LLM inference powering each turn.", color: "#4ECDC4" },
            { title: "Measure Behavioral Metrics", desc: "Every turn is scored on 9+ metrics: aggressiveness, sentiment, persuasion, citation quality, novelty, hedging, confidence, similarity, and word count.", color: "#FFD93D" },
            { title: "Analyze & Compare", desc: "Cross-debate analytics reveal which strategies, models, and source types produce the most accurate, efficient, and robust outcomes.", color: "#6C5CE7" },
          ].map((item) => (
            <div
              key={item.title}
              className="p-4 border-2 border-[var(--border)] rounded-lg shadow-[3px_3px_0px_var(--shadow-color)]"
              style={{ borderLeftWidth: "6px", borderLeftColor: item.color }}
            >
              <div className="font-black text-sm mb-1">{item.title}</div>
              <div className="text-xs text-gray-600 leading-relaxed">{item.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Four Strategies */}
      <div className={SECTION_STYLE}>
        <h2 className={H2}>Four Conflict Resolution Strategies</h2>
        <p className="text-sm text-gray-600 mb-5">
          Each strategy is implemented as a LangGraph workflow with distinct resolution mechanics:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {[
            {
              key: "majority_voting",
              icon: "1",
              desc: "Each agent independently evaluates evidence and casts a vote. Simple majority wins; ties broken by confidence scores.",
              mechanism: "Single-round, independent voting",
              strength: "Fast, simple, no inter-agent influence",
              weakness: "No deliberation; ignores argument quality",
            },
            {
              key: "structured_debate",
              icon: "2",
              desc: "Agents argue across multiple rounds (default 5), directly rebutting opponents. If deadlocked, a neutral judge arbitrates.",
              mechanism: "Multi-round argumentation with deadlock detection",
              strength: "Rich deliberation; exposes weak arguments",
              weakness: "Slower; risk of repetition and deadlock",
            },
            {
              key: "hierarchical",
              icon: "3",
              desc: "Subordinate agents submit persuasive briefs. A lead agent reviews all briefs and makes a binding decision.",
              mechanism: "Brief submission + authority decision",
              strength: "Decisive; single point of accountability",
              weakness: "Lead bias; subordinates have limited influence",
            },
            {
              key: "evidence_weighted",
              icon: "4",
              desc: "All agents rank each other's sources by reliability. Consensus weights are computed, then agents vote with evidence-weighted arguments.",
              mechanism: "Source ranking + weighted voting",
              strength: "Rewards high-quality evidence",
              weakness: "Agents may misjudge source reliability",
            },
          ].map((s) => (
            <div
              key={s.key}
              className="p-5 border-2 border-[var(--border)] rounded-lg shadow-[3px_3px_0px_var(--shadow-color)] bg-white"
            >
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="w-8 h-8 rounded-md flex items-center justify-center text-white font-black text-sm border-2 border-[var(--border)]"
                  style={{ backgroundColor: STRATEGY_COLORS[s.key] }}
                >
                  {s.icon}
                </div>
                <h3 className="font-black text-base">{STRATEGY_LABELS[s.key]}</h3>
              </div>
              <p className="text-xs text-gray-600 leading-relaxed mb-3">{s.desc}</p>
              <div className="space-y-1 text-xs">
                <div><span className="text-gray-500">Mechanism:</span> <strong>{s.mechanism}</strong></div>
                <div><span className="text-gray-500">Strength:</span> <span className="text-green-700">{s.strength}</span></div>
                <div><span className="text-gray-500">Weakness:</span> <span className="text-red-700">{s.weakness}</span></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Metrics */}
      <div className={SECTION_STYLE}>
        <h2 className={H2}>Behavioral Metrics Computed Per Turn</h2>
        <p className="text-sm text-gray-600 mb-5">
          Every LLM response is analyzed across 9 behavioral dimensions, enabling quantitative study
          of agent behavior under conflict:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { name: "Aggressiveness", range: "0-1", desc: "Detects dismissive, confrontational, and assertive language patterns", method: "Weighted keyword matching (strong/moderate/dismissive phrases)" },
            { name: "Sentiment", range: "-1 to +1", desc: "Measures cooperative vs. adversarial tone", method: "Cooperative/adversarial word ratio analysis" },
            { name: "Confidence", range: "0-1", desc: "Agent's self-reported confidence in its position", method: "Extracted from structured JSON output" },
            { name: "Persuasion Attempt", range: "0-1", desc: "Degree to which agent uses persuasive rhetoric", method: "Persuasion phrase detection (\"evidence shows\", \"consider that\")" },
            { name: "Citation Count", range: "0+", desc: "Number of evidence citations in the argument", method: "Regex matching for source references, studies, agencies" },
            { name: "Citation Quality", range: "0-1", desc: "Quality of cited sources weighted by type", method: "Source type scoring (peer_reviewed=0.9, social_media=0.2)" },
            { name: "Semantic Similarity", range: "0-1", desc: "How similar this turn is to the agent's previous turn", method: "Sentence-transformer cosine similarity (all-MiniLM-L6-v2)" },
            { name: "Argument Novelty", range: "0-1", desc: "How much new content vs. repetition (1 - similarity)", method: "Inverse of semantic similarity to previous turn" },
            { name: "Hedging Language", range: "0+", desc: "Count of uncertainty/hedging phrases", method: "Keyword detection (\"perhaps\", \"maybe\", \"might\")" },
          ].map((m) => (
            <div key={m.name} className="p-3 border-2 border-[var(--border)] rounded-md bg-white">
              <div className="flex items-center justify-between mb-1">
                <span className="font-black text-sm">{m.name}</span>
                <span className="text-[10px] font-mono bg-gray-100 px-1.5 py-0.5 rounded border">{m.range}</span>
              </div>
              <p className="text-[11px] text-gray-600 mb-1">{m.desc}</p>
              <p className="text-[10px] text-gray-400 italic">{m.method}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Scenario Types */}
      <div className={SECTION_STYLE}>
        <h2 className={H2}>Scenario Categories</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { name: "Factual Contradictions", color: "#FF6B6B", count: "15+ scenarios", desc: "Agents receive opposing factual claims (e.g., \"Is the Great Wall visible from space?\"). Tests whether debate can surface truth from conflicting information.", example: "Agent A briefed: \"Visible\" (social media). Agent B briefed: \"Not visible\" (NASA)." },
            { name: "Evidence Quality", color: "#4ECDC4", count: "12+ scenarios", desc: "Agents receive the same claim but from sources of varying reliability (peer-reviewed vs. blog post). Tests whether systems can weight evidence quality.", example: "Same conclusion, different source types: peer-reviewed journal vs. anonymous blog." },
            { name: "Instruction Conflicts", color: "#FFD93D", count: "10+ scenarios", desc: "Agents receive conflicting directives on ethical/business dilemmas. Tests how systems handle value trade-offs.", example: "Agent A: \"Prioritize user privacy.\" Agent B: \"Prioritize data collection.\"" },
            { name: "Misinformation Battles", color: "#6C5CE7", count: "8+ scenarios", desc: "Truth-teller vs. liar vs. manipulator roles. Tests system resilience against deliberate misinformation with varying persuasion tactics.", example: "2 truth-tellers vs. 1 manipulator with fabricated statistics." },
          ].map((cat) => (
            <div
              key={cat.name}
              className="p-4 border-2 border-[var(--border)] rounded-lg shadow-[3px_3px_0px_var(--shadow-color)]"
              style={{ borderLeftWidth: "6px", borderLeftColor: cat.color }}
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-black text-sm">{cat.name}</h3>
                <span className={`${BADGE} bg-gray-100`}>{cat.count}</span>
              </div>
              <p className="text-xs text-gray-600 mb-2">{cat.desc}</p>
              <p className="text-[11px] text-gray-400 italic">{cat.example}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Research Potential */}
      <div className={`${SECTION_STYLE} border-l-8 border-l-[#6C5CE7]`}>
        <h2 className={H2}>Research Potential &amp; Unique Contributions</h2>

        <div className="space-y-5">
          <div>
            <h3 className={H3}>1. Comparative Strategy Analysis</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              This platform enables direct, controlled comparison of four distinct conflict resolution
              strategies using the same scenarios, models, and metrics. Researchers can answer:
              Which strategy produces the most accurate outcomes? Which minimizes deadlock?
              Which produces the richest deliberation? No existing platform offers this level of
              controlled multi-strategy experimentation with behavioral instrumentation.
            </p>
          </div>

          <div>
            <h3 className={H3}>2. Misinformation Resistance Testing</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              The misinformation battle scenarios (truth-teller vs. liar vs. manipulator) provide
              a unique testbed for studying how well multi-agent systems resist deliberate
              misinformation. This has direct implications for AI safety: if a compromised agent
              injects false information, which resolution strategy is most robust?
            </p>
          </div>

          <div>
            <h3 className={H3}>3. Source Quality as a Variable</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              Each scenario includes explicit source reliability metadata (peer-reviewed: 0.9,
              social media: 0.2, etc.). This enables studying whether agents appropriately weight
              evidence quality, and whether strategies like Evidence-Weighted Consensus outperform
              brute-force voting when source quality varies.
            </p>
          </div>

          <div>
            <h3 className={H3}>4. Behavioral Profiling of LLMs Under Conflict</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              The 9-metric behavioral instrumentation reveals how different LLM models behave
              under adversarial conditions. Do some models become more aggressive? Do others
              cave under pressure? Which models maintain argument novelty across rounds?
              This produces model-level behavioral profiles that go beyond standard benchmarks.
            </p>
          </div>

          <div>
            <h3 className={H3}>5. Deadlock Dynamics</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              Semantic similarity-based deadlock detection (using sentence-transformers) enables
              studying when and why multi-agent systems fail to converge. Analysis reveals which
              strategy/model combinations are most deadlock-prone, informing system design choices.
            </p>
          </div>

          <div>
            <h3 className={H3}>6. Position Change Analysis</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              The platform tracks when agents change positions, in which round, and for what
              stated reason. This enables studying persuasion dynamics: what makes an LLM
              change its mind? Is it opponent confidence, evidence quality, or debate round?
            </p>
          </div>
        </div>
      </div>

      {/* Live Findings (from actual data) */}
      {findings.length > 0 && (
        <div className={`${SECTION_STYLE} border-l-8 border-l-[#FF6B6B]`}>
          <h2 className={H2}>Findings From Your Data</h2>
          <p className="text-xs text-gray-500 mb-4">
            Auto-generated from {insights?.debate_count || 0} completed debates
          </p>
          <div className="space-y-3">
            {findings.map((f: string, i: number) => (
              <div key={i} className="flex gap-3 p-3 bg-white border-2 border-[var(--border)] rounded-md">
                <span className="font-black text-[#FF6B6B] text-lg shrink-0">{i + 1}</span>
                <span className="text-sm font-medium">{f}</span>
              </div>
            ))}
          </div>

          {/* Strategy comparison from real data */}
          {strategies.length > 0 && (
            <div className="mt-6">
              <h3 className={H3}>Strategy Performance Summary</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 border-[var(--border)]">
                      <th className="text-left py-2 font-black">Strategy</th>
                      <th className="text-right py-2 font-black">Debates</th>
                      <th className="text-right py-2 font-black">Accuracy</th>
                      <th className="text-right py-2 font-black">Deadlock Rate</th>
                      <th className="text-right py-2 font-black">Avg Confidence</th>
                      <th className="text-right py-2 font-black">Avg Aggression</th>
                    </tr>
                  </thead>
                  <tbody>
                    {strategies.map((s: any) => (
                      <tr key={s.strategy} className="border-b border-gray-200">
                        <td className="py-2 font-bold flex items-center gap-2">
                          <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: STRATEGY_COLORS[s.strategy] || "#6B7280" }} />
                          {STRATEGY_LABELS[s.strategy] || s.strategy}
                        </td>
                        <td className="text-right py-2">{s.total_debates}</td>
                        <td className="text-right py-2 font-bold">{(s.accuracy * 100).toFixed(1)}%</td>
                        <td className="text-right py-2">{(s.deadlock_rate * 100).toFixed(1)}%</td>
                        <td className="text-right py-2">{(s.avg_confidence * 100).toFixed(0)}%</td>
                        <td className="text-right py-2">{(s.avg_aggressiveness * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Source quality finding */}
          {sourceImpact.total_data_points > 0 && (
            <div className="mt-5 p-4 bg-white border-2 border-[var(--border)] rounded-md">
              <h3 className="font-black text-sm mb-2">Source Quality Impact</h3>
              <p className="text-sm">
                Avg winning source reliability: <strong>{((sourceImpact.avg_winning_source_reliability || 0) * 100).toFixed(0)}%</strong>
                {" vs "} losing: <strong>{((sourceImpact.avg_losing_source_reliability || 0) * 100).toFixed(0)}%</strong>
                {" "}&mdash; {sourceImpact.finding}
              </p>
            </div>
          )}

          {/* Misinformation finding */}
          {misinfo.total_misinformation_debates > 0 && (
            <div className="mt-4 p-4 bg-white border-2 border-[var(--border)] rounded-md">
              <h3 className="font-black text-sm mb-2">Misinformation Resistance</h3>
              <p className="text-sm">{misinfo.finding}</p>
              {misinfo.best_strategy_for_truth && misinfo.best_strategy_for_truth !== "insufficient_data" && (
                <p className="text-xs text-gray-500 mt-1">
                  Best strategy for truth detection: <strong>{STRATEGY_LABELS[misinfo.best_strategy_for_truth] || misinfo.best_strategy_for_truth}</strong>
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tech Stack */}
      <div className={SECTION_STYLE}>
        <h2 className={H2}>Technical Architecture</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className={H3}>Backend</h3>
            <div className="space-y-2">
              {[
                ["Web Framework", "FastAPI (async)"],
                ["LLM Orchestration", "LangGraph + LangChain"],
                ["LLM Providers", "Groq, Cerebras, OpenRouter"],
                ["Models", "Llama 3.3 70B, Llama 3.1 8B, Nemotron 120B"],
                ["Database", "SQLite (async via SQLAlchemy + aiosqlite)"],
                ["Semantic Analysis", "sentence-transformers (all-MiniLM-L6-v2)"],
                ["Streaming", "Server-Sent Events (SSE)"],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between text-sm border-b border-gray-100 pb-1">
                  <span className="text-gray-500">{label}</span>
                  <span className="font-bold">{value}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h3 className={H3}>Frontend</h3>
            <div className="space-y-2">
              {[
                ["Framework", "Next.js 16 (App Router)"],
                ["Language", "TypeScript"],
                ["Styling", "Tailwind CSS (Neo-Brutalism)"],
                ["Charts", "Recharts"],
                ["Real-time", "EventSource (SSE)"],
                ["Data Export", "JSON, CSV, Excel (.xlsx)"],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between text-sm border-b border-gray-100 pb-1">
                  <span className="text-gray-500">{label}</span>
                  <span className="font-bold">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* How to Use for Research */}
      <div className={`${SECTION_STYLE} border-l-8 border-l-[#FFD93D]`}>
        <h2 className={H2}>How to Use This for Research</h2>
        <div className="space-y-4">
          {[
            { step: "1", title: "Run Debates Across All Strategies", desc: "For each scenario, run all 4 strategies with the same model combination. This gives you controlled comparisons." },
            { step: "2", title: "Use Multiple Model Combinations", desc: "Vary which models play each agent role. This isolates strategy effects from model effects." },
            { step: "3", title: "Run Misinformation Battles", desc: "Test truth vs. misinformation scenarios across strategies to measure resistance." },
            { step: "4", title: "Visit Research Insights", desc: "Go to Admin > Research Insights for auto-generated cross-debate analytics, strategy rankings, and behavioral profiles." },
            { step: "5", title: "Export Data", desc: "Export full debate data as Excel/CSV for external analysis (R, Python, SPSS). All 9 metrics are included per turn." },
            { step: "6", title: "Use Debate Deep Dives", desc: "Admin > click any debate for per-turn metrics, confidence trajectories, novelty charts, and agent behavioral radar plots." },
          ].map((item) => (
            <div key={item.step} className="flex gap-4 items-start">
              <div className="w-8 h-8 bg-[#FFD93D] border-2 border-[var(--border)] rounded-md flex items-center justify-center font-black text-sm shrink-0 shadow-[2px_2px_0px_var(--shadow-color)]">
                {item.step}
              </div>
              <div>
                <div className="font-black text-sm">{item.title}</div>
                <div className="text-xs text-gray-600">{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Platform Stats */}
      {overview && (
        <div className={SECTION_STYLE}>
          <h2 className={H2}>Platform Status</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Debates Run", value: overview.total_debates, color: "#FF6B6B" },
              { label: "Accuracy", value: `${(overview.avg_accuracy * 100).toFixed(1)}%`, color: "#4ECDC4" },
              { label: "Deadlock Rate", value: `${(overview.deadlock_rate * 100).toFixed(1)}%`, color: "#FFD93D" },
              { label: "Scenarios", value: overview.total_scenarios, color: "#6C5CE7" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="p-4 rounded-md border-2 border-[var(--border)] shadow-[3px_3px_0px_var(--shadow-color)] text-center"
                style={{ backgroundColor: stat.color }}
              >
                <div className="text-xs font-bold uppercase tracking-wider">{stat.label}</div>
                <div className="text-3xl font-black mt-1">{stat.value}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="text-center text-sm text-gray-500 pb-8">
        <p className="font-bold">When Agents Disagree &mdash; CS-584 Course Project</p>
        <p className="mt-1">Multi-Agent Conflict Resolution Research Platform</p>
      </div>
    </div>
  );
}
