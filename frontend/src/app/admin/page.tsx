"use client";
import { useState, useEffect } from "react";
import { getOverview, getStrategyComparison, getModelComparison, getDeadlockStats } from "@/lib/api";
import { STRATEGY_LABELS, STRATEGY_COLORS, PROVIDER_LABELS } from "@/lib/constants";
import { formatPercentage, formatLatency, formatTokens } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  PieChart, Pie, Cell
} from "recharts";

const TOOLTIP_STYLE = { backgroundColor: "#FFFFFF", border: "2px solid #1A1A2E", borderRadius: "6px", boxShadow: "4px 4px 0px #1A1A2E", fontSize: 14 };
const AXIS_TICK = { fontSize: 14, fill: "#1A1A2E", fontWeight: 700 };
const GRID_COLOR = "#D1D5DB";

export default function AdminOverview() {
  const [overview, setOverview] = useState<any>(null);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [deadlocks, setDeadlocks] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      getOverview().catch(() => null),
      getStrategyComparison().catch(() => []),
      getModelComparison().catch(() => []),
      getDeadlockStats().catch(() => []),
    ]).then(([o, s, m, d]) => {
      setOverview(o);
      setStrategies(s);
      setModels(m);
      setDeadlocks(d);
    });
  }, []);

  const kpis = overview
    ? [
        { label: "Total Debates", value: overview.total_debates, bg: "#FF6B6B" },
        { label: "Avg Accuracy", value: formatPercentage(overview.avg_accuracy), bg: "#2ECC71" },
        { label: "Avg Latency", value: formatLatency(overview.avg_latency_ms), bg: "#FFD93D" },
        { label: "Deadlock Rate", value: formatPercentage(overview.deadlock_rate), bg: "#FF8A5C" },
        { label: "Scenarios", value: overview.total_scenarios, bg: "#6C5CE7" },
        { label: "Experiments", value: overview.total_experiments, bg: "#4ECDC4" },
      ]
    : [];

  const strategyChartData = strategies.map((s) => ({
    name: STRATEGY_LABELS[s.strategy] || s.strategy,
    accuracy: +(s.accuracy * 100).toFixed(1),
    deadlock_rate: +(s.deadlock_rate * 100).toFixed(1),
    avg_turns: s.avg_turns,
    fill: STRATEGY_COLORS[s.strategy] || "#FF6B6B",
  }));

  const radarData = strategies.map((s) => ({
    strategy: (STRATEGY_LABELS[s.strategy] || s.strategy).replace(" ", "\n"),
    accuracy: s.accuracy * 100,
    speed: Math.max(0, 100 - s.avg_latency_ms / 100),
    confidence: s.avg_confidence * 100,
    low_aggression: (1 - s.avg_aggressiveness) * 100,
    reliability: (1 - s.deadlock_rate) * 100,
  }));

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8 uppercase tracking-wide">Dashboard Overview</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-5 mb-10">
        {kpis.map((kpi) => (
          <div
            key={kpi.label}
            className="p-5 rounded-md border-2 border-[var(--border)] shadow-[4px_4px_0px_var(--shadow-color)]"
            style={{ backgroundColor: kpi.bg }}
          >
            <div className="text-sm font-bold uppercase tracking-wider text-[var(--foreground)]">{kpi.label}</div>
            <div className="text-4xl font-bold text-[var(--foreground)] mt-1">
              {kpi.value}
            </div>
          </div>
        ))}
      </div>

      {strategies.length === 0 && (
        <div className="text-center py-16 nb-card p-8">
          <p className="text-lg mb-2 font-bold">No data yet</p>
          <p className="text-sm text-[var(--muted-foreground)]">Run some debates to see analytics here.</p>
        </div>
      )}

      {strategies.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Strategy Accuracy Bar Chart */}
          <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
            <h3 className="text-lg font-bold mb-4 uppercase tracking-wide">Strategy Accuracy</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={strategyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
                <XAxis dataKey="name" tick={AXIS_TICK} />
                <YAxis tick={AXIS_TICK} domain={[0, 100]} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="accuracy" name="Accuracy %">
                  {strategyChartData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Strategy Radar */}
          <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
            <h3 className="text-lg font-bold mb-4 uppercase tracking-wide">Strategy Performance Radar</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid stroke={GRID_COLOR} />
                <PolarAngleAxis dataKey="strategy" tick={{ fontSize: 13, fill: "#1A1A2E", fontWeight: 700 }} />
                <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 12, fill: "#1A1A2E" }} />
                <Radar name="Metrics" dataKey="accuracy" stroke="#6C5CE7" fill="#6C5CE7" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Model Comparison */}
          <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
            <h3 className="text-lg font-bold mb-4 uppercase tracking-wide">Model Performance</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-base border-2 border-[var(--border)] rounded-md overflow-hidden">
                <thead>
                  <tr className="bg-[#F5E6D3]">
                    <th className="pb-3 pt-3 px-4 text-left font-bold border-b-2 border-[var(--border)]">Model</th>
                    <th className="pb-3 pt-3 px-4 text-left font-bold border-b-2 border-[var(--border)]">Accuracy</th>
                    <th className="pb-3 pt-3 px-4 text-left font-bold border-b-2 border-[var(--border)]">Avg Latency</th>
                    <th className="pb-3 pt-3 px-4 text-left font-bold border-b-2 border-[var(--border)]">Confidence</th>
                    <th className="pb-3 pt-3 px-4 text-left font-bold border-b-2 border-[var(--border)]">Aggressiveness</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((m, i) => (
                    <tr key={i} className="border-b border-[var(--border)]/20">
                      <td className="py-3 px-4">
                        <div className="font-bold text-base">{m.model_id.split("/").pop()?.split(":")[0]}</div>
                        <div className="text-sm text-[var(--muted-foreground)] font-medium">{PROVIDER_LABELS[m.provider] || m.provider}</div>
                      </td>
                      <td className="py-3 px-4 font-bold">{formatPercentage(m.accuracy)}</td>
                      <td className="py-3 px-4 font-bold">{formatLatency(m.avg_latency_ms)}</td>
                      <td className="py-3 px-4 font-bold">{formatPercentage(m.avg_confidence)}</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-3 bg-[var(--secondary)] rounded-sm overflow-hidden border-2 border-[var(--border)]">
                            <div
                              className="h-full bg-[#FF6B6B]"
                              style={{ width: `${m.avg_aggressiveness * 100}%` }}
                            />
                          </div>
                          <span className="font-bold">{(m.avg_aggressiveness * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Deadlock Stats */}
          <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
            <h3 className="text-lg font-bold mb-4 uppercase tracking-wide">Deadlock Rates by Strategy</h3>
            {deadlocks.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={deadlocks.map(d => ({
                  name: STRATEGY_LABELS[d.strategy] || d.strategy,
                  deadlock_rate: +(d.deadlock_rate * 100).toFixed(1),
                  total: d.total_debates,
                  fill: STRATEGY_COLORS[d.strategy] || "#FF6B6B",
                }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
                  <XAxis dataKey="name" tick={AXIS_TICK} />
                  <YAxis tick={AXIS_TICK} domain={[0, 100]} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="deadlock_rate" name="Deadlock Rate %">
                    {deadlocks.map((_, i) => (
                      <Cell key={i} fill={Object.values(STRATEGY_COLORS)[i] || "#FF6B6B"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-[var(--muted-foreground)] font-medium">No deadlock data yet</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
