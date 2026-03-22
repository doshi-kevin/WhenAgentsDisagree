"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getDebate, getConfidenceTrajectories } from "@/lib/api";
import { STRATEGY_LABELS, AGENT_COLORS, PROVIDER_LABELS } from "@/lib/constants";
import { formatPercentage, formatLatency, formatTokens } from "@/lib/utils";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, Cell } from "recharts";

const TOOLTIP_STYLE = { backgroundColor: "#FFFFFF", border: "2px solid #1A1A2E", borderRadius: "6px", boxShadow: "4px 4px 0px #1A1A2E", fontSize: 14 };
const AXIS_TICK = { fontSize: 14, fill: "#1A1A2E", fontWeight: 700 };
const GRID_COLOR = "#D1D5DB";

export default function DebateDeepDivePage() {
  const { id } = useParams<{ id: string }>();
  const [debate, setDebate] = useState<any>(null);
  const [trajectories, setTrajectories] = useState<any[]>([]);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      getDebate(id),
      getConfidenceTrajectories(id).catch(() => []),
    ]).then(([d, t]) => {
      setDebate(d);
      setTrajectories(t);
    });
  }, [id]);

  if (!debate) {
    return <div className="text-center py-16 text-[var(--muted-foreground)] font-bold">Loading...</div>;
  }

  const turns = debate.turns || [];
  const agents = debate.agents || [];

  const confData: any[] = [];
  turns.forEach((t: any) => {
    let point = confData.find((p) => p.turn === t.turn_number);
    if (!point) {
      point = { turn: t.turn_number };
      confData.push(point);
    }
    point[t.agent_name] = t.confidence_score ?? 0.5;
  });
  confData.sort((a, b) => a.turn - b.turn);

  const aggrData = turns.map((t: any) => ({
    turn: `T${t.turn_number}`,
    agent: t.agent_name,
    aggressiveness: t.metrics?.aggressiveness_score ?? 0,
    sentiment: t.metrics?.sentiment_score ?? 0,
  }));

  const STAT_COLORS = ["#FF6B6B", "#4ECDC4", "#FFD93D", "#6C5CE7", "#2ECC71"];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wide">Debate Deep Dive</h1>
          <p className="text-base text-[var(--muted-foreground)] font-medium">
            {debate.scenario?.title || "Debate"} &middot; {STRATEGY_LABELS[debate.strategy]}
          </p>
        </div>
        <span className={`text-sm px-3 py-1 rounded-md font-bold border-2 border-[var(--border)] shadow-[2px_2px_0px_var(--shadow-color)] ${
          debate.is_correct ? "bg-[#2ECC71] text-[var(--foreground)]" : "bg-[#FF6B6B] text-white"
        }`}>
          {debate.is_correct ? "Correct" : "Incorrect"} - &quot;{debate.final_answer}&quot;
        </span>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-5 mb-8">
        {[
          { label: "Total Turns", value: debate.total_turns },
          { label: "Tokens Used", value: formatTokens(debate.total_tokens) },
          { label: "Total Time", value: formatLatency(debate.total_latency_ms) },
          { label: "Deadlock?", value: debate.deadlock_detected ? "Yes" : "No" },
          { label: "Correct Answer", value: debate.scenario?.ground_truth || "N/A" },
        ].map((stat, i) => (
          <div
            key={stat.label}
            className="p-4 rounded-md border-2 border-[var(--border)] shadow-[3px_3px_0px_var(--shadow-color)]"
            style={{ backgroundColor: STAT_COLORS[i] }}
          >
            <div className="text-sm font-bold uppercase tracking-wider text-[var(--foreground)]">{stat.label}</div>
            <div className="text-2xl font-bold text-[var(--foreground)] mt-1">{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Confidence Trajectory */}
        <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
          <h3 className="text-lg font-bold mb-4 uppercase tracking-wide">How Confident Each Agent Was</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={confData}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
              <XAxis dataKey="turn" tick={AXIS_TICK} />
              <YAxis domain={[0, 1]} tick={AXIS_TICK} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend />
              {agents.map((agent: any, i: number) => (
                <Line
                  key={agent.agent_name}
                  type="monotone"
                  dataKey={agent.agent_name}
                  stroke={AGENT_COLORS[i]}
                  strokeWidth={3}
                  dot={{ fill: AGENT_COLORS[i], r: 5, stroke: "#1A1A2E", strokeWidth: 2 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Aggressiveness Per Turn */}
        <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
          <h3 className="text-lg font-bold mb-4 uppercase tracking-wide">How Aggressive Each Turn Was</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={aggrData}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
              <XAxis dataKey="turn" tick={AXIS_TICK} />
              <YAxis domain={[0, 1]} tick={AXIS_TICK} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="aggressiveness" name="Aggressiveness">
                {aggrData.map((entry: any, i: number) => {
                  const agentIdx = agents.findIndex((a: any) => a.agent_name === entry.agent);
                  return <Cell key={i} fill={AGENT_COLORS[agentIdx >= 0 ? agentIdx : 0]} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Full Transcript */}
      <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
        <h3 className="text-xl font-bold mb-5 uppercase tracking-wide">Full Debate Transcript</h3>
        <div className="space-y-4">
          {turns.map((turn: any, i: number) => {
            const agentIdx = agents.findIndex((a: any) => a.agent_name === turn.agent_name);
            const color = AGENT_COLORS[agentIdx >= 0 ? agentIdx : 0];
            const metrics = turn.metrics;

            let displayContent = turn.content;
            try {
              const parsed = JSON.parse(turn.content);
              displayContent = parsed?.argument || parsed?.reasoning || parsed?.summary || parsed?.decision || turn.content;
            } catch {}

            return (
              <div key={turn.id || i} className="border-l-4 pl-4 pb-4" style={{ borderColor: color }}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-bold text-base" style={{ color }}>{turn.agent_name}</span>
                  <span className="text-sm px-2.5 py-1 rounded-md bg-[var(--secondary)] font-bold border-2 border-[var(--border)]">
                    Round {turn.round_number} &middot; Turn {turn.turn_number} &middot; {turn.role}
                  </span>
                  <span className="text-sm text-[var(--muted-foreground)] font-medium">
                    {formatLatency(turn.latency_ms)} &middot; {formatTokens(turn.total_tokens)} tokens
                  </span>
                </div>

                <p className="text-base leading-relaxed mb-3 whitespace-pre-wrap">{displayContent}</p>

                {/* Detailed metrics */}
                {metrics && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 text-sm">
                    {[
                      { label: "Confidence", value: formatPercentage(turn.confidence_score || 0) },
                      { label: "Aggressiveness", value: `${(metrics.aggressiveness_score * 100).toFixed(0)}%` },
                      { label: "Sentiment", value: metrics.sentiment_score.toFixed(2) },
                      { label: "Word Count", value: metrics.word_count },
                      ...(metrics.semantic_similarity_to_prev !== null ? [{ label: "Similarity", value: metrics.semantic_similarity_to_prev?.toFixed(2) }] : []),
                      { label: "Citations", value: metrics.citation_count },
                      { label: "Hedging", value: metrics.hedging_language_count },
                      { label: "Persuasion", value: `${(metrics.persuasion_attempt_score * 100).toFixed(0)}%` },
                    ].map((metric) => (
                      <div key={metric.label} className="px-3 py-1.5 rounded-md bg-[var(--secondary)] border-2 border-[var(--border)]">
                        <span className="text-[var(--muted-foreground)] font-medium">{metric.label}: </span>
                        <span className="font-bold">{metric.value}</span>
                      </div>
                    ))}
                  </div>
                )}

                {turn.position_changed && (
                  <div className="mt-2 text-xs px-2 py-1 rounded-md bg-[#FFD93D] text-[var(--foreground)] font-bold border-2 border-[var(--border)]">
                    Position changed to &quot;{turn.position_held}&quot; - {turn.change_reason || "No reason given"}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
