"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getDebate, getConfidenceTrajectories } from "@/lib/api";
import { STRATEGY_LABELS, AGENT_COLORS, PROVIDER_LABELS } from "@/lib/constants";
import { formatPercentage, formatLatency, formatTokens } from "@/lib/utils";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, BarChart, Bar, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, AreaChart, Area,
} from "recharts";

const TOOLTIP_STYLE = { backgroundColor: "#FFFFFF", border: "2px solid #1A1A2E", borderRadius: "6px", boxShadow: "4px 4px 0px #1A1A2E", fontSize: 14 };
const AXIS_TICK = { fontSize: 12, fill: "#1A1A2E", fontWeight: 700 };
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

  // --- Confidence trajectory data ---
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

  // --- Aggressiveness per turn ---
  const aggrData = turns.map((t: any) => ({
    turn: `T${t.turn_number}`,
    agent: t.agent_name,
    aggressiveness: t.metrics?.aggressiveness_score ?? 0,
    sentiment: t.metrics?.sentiment_score ?? 0,
  }));

  // --- Novelty / similarity evolution per turn ---
  const noveltyData = turns
    .filter((t: any) => t.metrics?.argument_novelty_score != null)
    .map((t: any) => ({
      turn: `T${t.turn_number}`,
      agent: t.agent_name,
      novelty: Math.round((t.metrics.argument_novelty_score ?? 1) * 100),
      similarity: Math.round((t.metrics.semantic_similarity_to_prev ?? 0) * 100),
    }));

  // --- Per-agent summary stats ---
  const agentSummaries: any[] = agents.map((agent: any, idx: number) => {
    const agentTurns = turns.filter((t: any) => t.agent_name === agent.agent_name);
    const withMetrics = agentTurns.filter((t: any) => t.metrics);
    const mean = (arr: number[]) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;

    return {
      name: agent.agent_name,
      provider: agent.provider,
      model_id: agent.model_id,
      position: agent.assigned_position,
      bias_role: agent.bias_role,
      color: AGENT_COLORS[idx],
      turns: agentTurns.length,
      avg_confidence: mean(agentTurns.map((t: any) => t.confidence_score ?? 0.5)),
      avg_aggressiveness: mean(withMetrics.map((t: any) => t.metrics.aggressiveness_score ?? 0)),
      avg_sentiment: mean(withMetrics.map((t: any) => t.metrics.sentiment_score ?? 0)),
      avg_novelty: mean(withMetrics.filter((t: any) => t.metrics.argument_novelty_score != null).map((t: any) => t.metrics.argument_novelty_score)),
      total_citations: withMetrics.reduce((sum: number, t: any) => sum + (t.metrics.citation_count ?? 0), 0),
      position_changes: agentTurns.filter((t: any) => t.position_changed).length,
      total_tokens: agentTurns.reduce((s: number, t: any) => s + (t.total_tokens ?? 0), 0),
      total_latency: agentTurns.reduce((s: number, t: any) => s + (t.latency_ms ?? 0), 0),
    };
  });

  // --- Radar data for agent comparison ---
  const radarData: Record<string, any>[] = [
    { metric: "Confidence" },
    { metric: "Aggressiveness" },
    { metric: "Novelty" },
    { metric: "Citations" },
    { metric: "Cooperation" },
  ];
  agentSummaries.forEach((a: any) => {
    radarData[0][a.name] = Math.round(a.avg_confidence * 100);
    radarData[1][a.name] = Math.round(a.avg_aggressiveness * 100);
    radarData[2][a.name] = Math.round(a.avg_novelty * 100);
    radarData[3][a.name] = Math.min(100, a.total_citations * 20);
    radarData[4][a.name] = Math.round(Math.max(0, (a.avg_sentiment + 1) * 50));
  });

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
          { label: "Ground Truth", value: debate.scenario?.ground_truth || "N/A" },
        ].map((stat, i) => (
          <div
            key={stat.label}
            className="p-4 rounded-md border-2 border-[var(--border)] shadow-[3px_3px_0px_var(--shadow-color)]"
            style={{ backgroundColor: STAT_COLORS[i] }}
          >
            <div className="text-xs font-bold uppercase tracking-wider text-[var(--foreground)]">{stat.label}</div>
            <div className="text-2xl font-bold text-[var(--foreground)] mt-1">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Agent Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {agentSummaries.map((a) => (
          <div
            key={a.name}
            className="p-4 rounded-md border-2 border-[var(--border)] shadow-[3px_3px_0px_var(--shadow-color)] bg-white"
            style={{ borderLeftWidth: "6px", borderLeftColor: a.color }}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="font-black" style={{ color: a.color }}>{a.name}</div>
              {a.bias_role && (
                <span className={`text-xs font-bold px-2 py-0.5 rounded border border-[var(--border)] ${
                  a.bias_role === "truth_teller" ? "bg-green-100" : a.bias_role === "liar" ? "bg-red-100" : "bg-orange-100"
                }`}>
                  {a.bias_role.replace(/_/g, " ")}
                </span>
              )}
            </div>
            <div className="text-xs text-gray-500 mb-3">{a.provider} / {a.model_id.split("/").pop()}</div>
            <div className="text-xs text-gray-600 mb-2">Position: <strong>{a.position || "N/A"}</strong></div>
            <div className="grid grid-cols-2 gap-1.5 text-xs">
              <div>Confidence: <strong>{(a.avg_confidence * 100).toFixed(0)}%</strong></div>
              <div>Aggression: <strong>{(a.avg_aggressiveness * 100).toFixed(0)}%</strong></div>
              <div>Novelty: <strong>{(a.avg_novelty * 100).toFixed(0)}%</strong></div>
              <div>Citations: <strong>{a.total_citations}</strong></div>
              <div>Pos. Changes: <strong>{a.position_changes}</strong></div>
              <div>Tokens: <strong>{formatTokens(a.total_tokens)}</strong></div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row 1: Confidence + Agent Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
          <h3 className="text-sm font-black mb-4 uppercase tracking-wide">Confidence Trajectory</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={confData}>
              <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
              <XAxis dataKey="turn" tick={AXIS_TICK} label={{ value: "Turn", position: "insideBottom", offset: -2, fontWeight: 700 }} />
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

        <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
          <h3 className="text-sm font-black mb-4 uppercase tracking-wide">Agent Behavioral Comparison</h3>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={radarData}>
              <PolarGrid stroke={GRID_COLOR} />
              <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fontWeight: 700 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={false} />
              {agents.map((agent: any, i: number) => (
                <Radar
                  key={agent.agent_name}
                  name={agent.agent_name}
                  dataKey={agent.agent_name}
                  stroke={AGENT_COLORS[i]}
                  fill={AGENT_COLORS[i]}
                  fillOpacity={0.15}
                  strokeWidth={2}
                />
              ))}
              <Legend />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2: Aggressiveness + Novelty Evolution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
          <h3 className="text-sm font-black mb-4 uppercase tracking-wide">Aggressiveness Per Turn</h3>
          <ResponsiveContainer width="100%" height={220}>
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

        {noveltyData.length > 2 && (
          <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
            <h3 className="text-sm font-black mb-4 uppercase tracking-wide">Argument Novelty Over Time</h3>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={noveltyData}>
                <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
                <XAxis dataKey="turn" tick={AXIS_TICK} />
                <YAxis domain={[0, 100]} unit="%" tick={AXIS_TICK} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v: any) => `${v}%`} />
                <Legend />
                <Area type="monotone" dataKey="novelty" name="Novelty" stroke="#4ECDC4" fill="#4ECDC4" fillOpacity={0.3} strokeWidth={2} />
                <Area type="monotone" dataKey="similarity" name="Similarity" stroke="#FF6B6B" fill="#FF6B6B" fillOpacity={0.15} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Full Transcript */}
      <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
        <h3 className="text-lg font-bold mb-5 uppercase tracking-wide">Full Debate Transcript</h3>
        <div className="space-y-4">
          {turns.map((turn: any, i: number) => {
            const agentIdx = agents.findIndex((a: any) => a.agent_name === turn.agent_name);
            const color = AGENT_COLORS[agentIdx >= 0 ? agentIdx : 0];
            const metrics = turn.metrics;
            const isError = turn.content?.startsWith("Error:");

            let displayContent = turn.content;
            try {
              const parsed = JSON.parse(turn.content);
              displayContent = parsed?.argument || parsed?.reasoning || parsed?.summary || parsed?.decision || turn.content;
            } catch {}

            return (
              <div key={turn.id || i} className={`border-l-4 pl-4 pb-4 ${isError ? "opacity-50" : ""}`} style={{ borderColor: color }}>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="font-bold text-base" style={{ color }}>{turn.agent_name}</span>
                  <span className="text-xs px-2 py-0.5 rounded-md bg-[var(--secondary)] font-bold border border-[var(--border)]">
                    R{turn.round_number} &middot; T{turn.turn_number}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-gray-100 font-semibold">{turn.role}</span>
                  <span className="text-xs text-[var(--muted-foreground)]">
                    {formatLatency(turn.latency_ms)} &middot; {formatTokens(turn.total_tokens)} tokens
                  </span>
                  {isError && (
                    <span className="text-xs px-2 py-0.5 rounded bg-red-100 text-red-700 font-bold border border-red-300">
                      API Error
                    </span>
                  )}
                </div>

                <p className="text-sm leading-relaxed mb-3 whitespace-pre-wrap">{displayContent}</p>

                {/* Metrics grid */}
                {metrics && !isError && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                    {[
                      { label: "Confidence", value: formatPercentage(turn.confidence_score || 0), color: turn.confidence_score > 0.8 ? "text-green-700" : "" },
                      { label: "Aggression", value: `${(metrics.aggressiveness_score * 100).toFixed(0)}%`, color: metrics.aggressiveness_score > 0.5 ? "text-red-700" : "" },
                      { label: "Sentiment", value: metrics.sentiment_score.toFixed(2), color: metrics.sentiment_score > 0 ? "text-green-700" : metrics.sentiment_score < 0 ? "text-red-700" : "" },
                      { label: "Words", value: metrics.word_count },
                      ...(metrics.semantic_similarity_to_prev != null ? [{ label: "Similarity", value: `${(metrics.semantic_similarity_to_prev * 100).toFixed(0)}%`, color: metrics.semantic_similarity_to_prev > 0.9 ? "text-red-700" : "text-green-700" }] : []),
                      ...(metrics.argument_novelty_score != null ? [{ label: "Novelty", value: `${(metrics.argument_novelty_score * 100).toFixed(0)}%`, color: metrics.argument_novelty_score < 0.2 ? "text-red-700" : "text-green-700" }] : []),
                      { label: "Citations", value: metrics.citation_count },
                      { label: "Persuasion", value: `${(metrics.persuasion_attempt_score * 100).toFixed(0)}%` },
                    ].map((metric) => (
                      <div key={metric.label} className="px-2 py-1 rounded bg-[var(--secondary)] border border-[var(--border)]">
                        <span className="text-gray-500">{metric.label}: </span>
                        <span className={`font-bold ${(metric as any).color || ""}`}>{metric.value}</span>
                      </div>
                    ))}
                  </div>
                )}

                {turn.position_changed && (
                  <div className="mt-2 text-xs px-2 py-1 rounded bg-[#FFD93D] text-[var(--foreground)] font-bold border-2 border-[var(--border)] inline-block">
                    Position changed to &quot;{turn.position_held}&quot; &mdash; {turn.change_reason || "No reason given"}
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
