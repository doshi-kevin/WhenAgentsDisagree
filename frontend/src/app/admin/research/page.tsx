"use client";
import { useState, useEffect } from "react";
import { getResearchInsights } from "@/lib/api";
import { STRATEGY_LABELS, STRATEGY_COLORS } from "@/lib/constants";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  LineChart, Line, Legend,
} from "recharts";

export default function ResearchInsightsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getResearchInsights()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-2xl font-black mb-2">Analyzing...</div>
          <div className="text-sm text-gray-600">Computing research insights across all debates</div>
        </div>
      </div>
    );
  }

  if (!data || data.error) {
    return (
      <div className="nb-card p-8 text-center">
        <h2 className="text-xl font-black mb-2">No Data Yet</h2>
        <p className="text-gray-600">Run some debates first to generate research insights.</p>
      </div>
    );
  }

  const strategyData = (data.strategy_effectiveness || []).map((s: any) => ({
    ...s,
    name: STRATEGY_LABELS[s.strategy] || s.strategy,
    accuracy_pct: Math.round(s.accuracy * 100),
    deadlock_pct: Math.round(s.deadlock_rate * 100),
    change_pct: Math.round(s.position_change_rate * 100),
    fill: STRATEGY_COLORS[s.strategy] || "#6B7280",
  }));

  const radarData = strategyData.map((s: any) => ({
    strategy: s.name,
    Accuracy: s.accuracy * 100,
    Novelty: (s.avg_novelty || 0) * 100,
    Confidence: (s.avg_confidence || 0) * 100,
    "Low Aggression": Math.max(0, (1 - (s.avg_aggressiveness || 0)) * 100),
    "Low Deadlock": (1 - s.deadlock_rate) * 100,
  }));

  const roundsData = (data.argument_quality_over_time?.rounds || []).map((r: any) => ({
    round: `R${r.round}`,
    Novelty: Math.round((r.avg_novelty || 0) * 100),
    Aggressiveness: Math.round((r.avg_aggressiveness || 0) * 100),
    Confidence: Math.round((r.avg_confidence || 0) * 100),
    "Avg Citations": r.avg_citations || 0,
  }));

  const sourceImpact = data.source_quality_impact || {};
  const sourceTypeWinRates = Object.entries(sourceImpact.source_type_win_rates || {}).map(
    ([type, rate]: [string, any]) => ({
      name: type.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()),
      win_rate: Math.round(rate * 100),
    })
  ).sort((a, b) => b.win_rate - a.win_rate);

  const profiles = (data.model_behavioral_profiles || []).map((p: any) => ({
    ...p,
    display_name: p.model_id.split("/").pop()?.replace(/:.*/, "") || p.model_id,
  }));

  const misinfo = data.misinformation_resistance || {};
  const posChanges = data.position_change_dynamics || {};
  const deadlockData = data.deadlock_analysis || {};
  const findings = data.key_findings || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black">Research Insights</h1>
        <p className="text-gray-600 mt-1">
          Cross-debate analytics from {data.debate_count} completed debates
        </p>
      </div>

      {/* Key Findings */}
      <div className="nb-card p-6 border-l-8 border-l-[#4ECDC4]">
        <h2 className="text-lg font-black uppercase tracking-wider mb-3">Key Findings</h2>
        <ul className="space-y-2">
          {findings.map((f: string, i: number) => (
            <li key={i} className="flex gap-3 text-sm">
              <span className="font-black text-[#4ECDC4] shrink-0">{i + 1}.</span>
              <span>{f}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Strategy Effectiveness */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="nb-card p-6">
          <h3 className="text-base font-black uppercase tracking-wider mb-4">
            Strategy Accuracy Comparison
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={strategyData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} unit="%" />
              <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 12, fontWeight: 700 }} />
              <Tooltip formatter={(v: any) => `${v}%`} />
              <Bar dataKey="accuracy_pct" name="Accuracy" fill="#4ECDC4" radius={[0, 4, 4, 0]} />
              <Bar dataKey="deadlock_pct" name="Deadlock Rate" fill="#FF6B6B" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="nb-card p-6">
          <h3 className="text-base font-black uppercase tracking-wider mb-4">
            Strategy Multi-Dimensional Profile
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="strategy" tick={{ fontSize: 10, fontWeight: 700 }} />
              <PolarRadiusAxis domain={[0, 100]} />
              {radarData.map((entry: any, i: number) => (
                <Radar
                  key={entry.strategy}
                  name={entry.strategy}
                  dataKey={entry.strategy}
                  stroke="none"
                  fill="none"
                />
              ))}
              <Radar name="Accuracy" dataKey="Accuracy" stroke="#4ECDC4" fill="#4ECDC4" fillOpacity={0.2} />
              <Radar name="Novelty" dataKey="Novelty" stroke="#FFD93D" fill="#FFD93D" fillOpacity={0.2} />
              <Radar name="Low Deadlock" dataKey="Low Deadlock" stroke="#6C5CE7" fill="#6C5CE7" fillOpacity={0.2} />
              <Tooltip />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Strategy Detail Table */}
      <div className="nb-card p-6">
        <h3 className="text-base font-black uppercase tracking-wider mb-4">
          Strategy Detailed Metrics
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-[var(--border)]">
                <th className="text-left py-2 font-black">Strategy</th>
                <th className="text-right py-2 font-black">Debates</th>
                <th className="text-right py-2 font-black">Accuracy</th>
                <th className="text-right py-2 font-black">Deadlock</th>
                <th className="text-right py-2 font-black">Avg Confidence</th>
                <th className="text-right py-2 font-black">Avg Aggression</th>
                <th className="text-right py-2 font-black">Avg Novelty</th>
                <th className="text-right py-2 font-black">Pos. Changes</th>
                <th className="text-right py-2 font-black">Avg Tokens</th>
              </tr>
            </thead>
            <tbody>
              {strategyData.map((s: any) => (
                <tr key={s.strategy} className="border-b border-gray-200">
                  <td className="py-2 font-bold flex items-center gap-2">
                    <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: s.fill }} />
                    {s.name}
                  </td>
                  <td className="text-right py-2">{s.total_debates}</td>
                  <td className="text-right py-2 font-bold">{s.accuracy_pct}%</td>
                  <td className="text-right py-2">{s.deadlock_pct}%</td>
                  <td className="text-right py-2">{(s.avg_confidence * 100).toFixed(0)}%</td>
                  <td className="text-right py-2">{(s.avg_aggressiveness * 100).toFixed(0)}%</td>
                  <td className="text-right py-2">{((s.avg_novelty || 0) * 100).toFixed(0)}%</td>
                  <td className="text-right py-2">{s.change_pct}%</td>
                  <td className="text-right py-2">{Math.round(s.avg_tokens)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Argument Quality Over Rounds */}
      {roundsData.length > 1 && (
        <div className="nb-card p-6">
          <h3 className="text-base font-black uppercase tracking-wider mb-2">
            Argument Quality Over Rounds
          </h3>
          <p className="text-xs text-gray-500 mb-4">
            {data.argument_quality_over_time?.finding}
          </p>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={roundsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="round" tick={{ fontWeight: 700 }} />
              <YAxis domain={[0, 100]} unit="%" />
              <Tooltip formatter={(v: any) => typeof v === "number" ? `${v}%` : v} />
              <Legend />
              <Line type="monotone" dataKey="Novelty" stroke="#FFD93D" strokeWidth={3} dot={{ r: 5 }} />
              <Line type="monotone" dataKey="Aggressiveness" stroke="#FF6B6B" strokeWidth={3} dot={{ r: 5 }} />
              <Line type="monotone" dataKey="Confidence" stroke="#4ECDC4" strokeWidth={3} dot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Source Quality Impact + Misinformation Resistance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Source Quality */}
        <div className="nb-card p-6">
          <h3 className="text-base font-black uppercase tracking-wider mb-4">
            Source Quality Impact
          </h3>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-green-50 border-2 border-green-300 rounded-md">
                <div className="text-xs font-bold text-green-700 uppercase">Winning Source Reliability</div>
                <div className="text-2xl font-black text-green-800">
                  {((sourceImpact.avg_winning_source_reliability || 0) * 100).toFixed(0)}%
                </div>
              </div>
              <div className="p-3 bg-red-50 border-2 border-red-300 rounded-md">
                <div className="text-xs font-bold text-red-700 uppercase">Losing Source Reliability</div>
                <div className="text-2xl font-black text-red-800">
                  {((sourceImpact.avg_losing_source_reliability || 0) * 100).toFixed(0)}%
                </div>
              </div>
            </div>
            <p className="text-sm font-bold">{sourceImpact.finding}</p>
            {sourceTypeWinRates.length > 0 && (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={sourceTypeWinRates} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} unit="%" />
                  <YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 11, fontWeight: 600 }} />
                  <Tooltip formatter={(v: any) => `${v}%`} />
                  <Bar dataKey="win_rate" name="Win Rate" fill="#6C5CE7" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Misinformation Resistance */}
        <div className="nb-card p-6">
          <h3 className="text-base font-black uppercase tracking-wider mb-4">
            Misinformation Resistance
          </h3>
          {misinfo.total_misinformation_debates > 0 ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-green-50 border-2 border-green-300 rounded-md">
                  <div className="text-xs font-bold text-green-700 uppercase">Truth Wins</div>
                  <div className="text-2xl font-black text-green-800">
                    {((misinfo.truth_win_rate || 0) * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="p-3 bg-red-50 border-2 border-red-300 rounded-md">
                  <div className="text-xs font-bold text-red-700 uppercase">Misinfo Wins</div>
                  <div className="text-2xl font-black text-red-800">
                    {((misinfo.misinformation_win_rate || 0) * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
              <p className="text-sm font-bold">{misinfo.finding}</p>
              {misinfo.bias_role_win_rates && Object.keys(misinfo.bias_role_win_rates).length > 0 && (
                <div>
                  <div className="text-xs font-bold uppercase tracking-wider mb-2 text-gray-600">
                    Win Rate by Bias Role
                  </div>
                  <div className="space-y-2">
                    {Object.entries(misinfo.bias_role_win_rates).map(([role, rate]: [string, any]) => (
                      <div key={role} className="flex items-center gap-3">
                        <span className="text-sm font-bold w-28 capitalize">{role.replace(/_/g, " ")}</span>
                        <div className="flex-1 bg-gray-200 rounded-full h-4 border border-gray-300">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${Math.round(rate * 100)}%`,
                              backgroundColor: role === "truth_teller" ? "#2ECC71" : role === "liar" ? "#FF6B6B" : "#FF8A5C",
                            }}
                          />
                        </div>
                        <span className="text-sm font-bold w-12 text-right">{Math.round(rate * 100)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {misinfo.best_strategy_for_truth && misinfo.best_strategy_for_truth !== "insufficient_data" && (
                <p className="text-xs text-gray-500">
                  Best strategy for truth detection: <strong>{STRATEGY_LABELS[misinfo.best_strategy_for_truth] || misinfo.best_strategy_for_truth}</strong>
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              Run misinformation battle scenarios to see resistance analysis
            </p>
          )}
        </div>
      </div>

      {/* Model Behavioral Profiles */}
      {profiles.length > 0 && (
        <div className="nb-card p-6">
          <h3 className="text-base font-black uppercase tracking-wider mb-4">
            Model Behavioral Profiles
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {profiles.map((p: any) => (
              <div
                key={`${p.provider}:${p.model_id}`}
                className="p-4 border-2 border-[var(--border)] rounded-lg shadow-[3px_3px_0px_var(--shadow-color)]"
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <div className="text-sm font-black">{p.display_name}</div>
                    <div className="text-xs text-gray-500">{p.provider}</div>
                  </div>
                  <span className={`text-xs font-bold px-2 py-1 rounded border-2 border-[var(--border)] ${
                    p.behavioral_type === "Aggressive Debater" ? "bg-red-100 text-red-800" :
                    p.behavioral_type === "Open-Minded Collaborator" ? "bg-green-100 text-green-800" :
                    p.behavioral_type === "Stubborn Defender" ? "bg-yellow-100 text-yellow-800" :
                    p.behavioral_type === "Assertive Advocate" ? "bg-blue-100 text-blue-800" :
                    "bg-gray-100 text-gray-800"
                  }`}>
                    {p.behavioral_type}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div><span className="text-gray-500">Accuracy:</span> <strong>{(p.accuracy * 100).toFixed(0)}%</strong></div>
                  <div><span className="text-gray-500">Confidence:</span> <strong>{(p.avg_confidence * 100).toFixed(0)}%</strong></div>
                  <div><span className="text-gray-500">Aggression:</span> <strong>{(p.avg_aggressiveness * 100).toFixed(0)}%</strong></div>
                  <div><span className="text-gray-500">Novelty:</span> <strong>{((p.avg_novelty || 0) * 100).toFixed(0)}%</strong></div>
                  <div><span className="text-gray-500">Sentiment:</span> <strong>{(p.avg_sentiment * 100).toFixed(0)}%</strong></div>
                  <div><span className="text-gray-500">Pos. Changes:</span> <strong>{(p.position_change_rate * 100).toFixed(1)}%</strong></div>
                  <div><span className="text-gray-500">Citations/turn:</span> <strong>{(p.avg_citations_per_turn || 0).toFixed(1)}</strong></div>
                  <div><span className="text-gray-500">Avg Words:</span> <strong>{Math.round(p.avg_word_count || 0)}</strong></div>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  {p.total_debates} debates, {p.total_turns} turns
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Position Change Dynamics */}
      {posChanges.change_rate_by_round && Object.keys(posChanges.change_rate_by_round).length > 0 && (
        <div className="nb-card p-6">
          <h3 className="text-base font-black uppercase tracking-wider mb-2">
            Position Change Dynamics
          </h3>
          <p className="text-xs text-gray-500 mb-4">
            Total position changes: {posChanges.total_position_changes} | {posChanges.finding}
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <div className="text-xs font-bold uppercase mb-2 text-gray-600">Change Rate by Round</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={Object.entries(posChanges.change_rate_by_round).map(([r, rate]: [string, any]) => ({
                  round: `Round ${r}`,
                  rate: Math.round(rate * 100),
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="round" tick={{ fontSize: 11, fontWeight: 700 }} />
                  <YAxis unit="%" />
                  <Tooltip formatter={(v: any) => `${v}%`} />
                  <Bar dataKey="rate" name="Change Rate" fill="#6C5CE7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div>
              <div className="text-xs font-bold uppercase mb-2 text-gray-600">Change Rate by Strategy</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={Object.entries(posChanges.change_rate_by_strategy || {}).map(([s, rate]: [string, any]) => ({
                  strategy: STRATEGY_LABELS[s] || s,
                  rate: Math.round(rate * 100),
                  fill: STRATEGY_COLORS[s] || "#6B7280",
                }))} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" unit="%" />
                  <YAxis type="category" dataKey="strategy" width={140} tick={{ fontSize: 11, fontWeight: 700 }} />
                  <Tooltip formatter={(v: any) => `${v}%`} />
                  <Bar dataKey="rate" name="Change Rate">
                    {Object.entries(posChanges.change_rate_by_strategy || {}).map(([s]: [string, any], i: number) => (
                      <rect key={s} fill={STRATEGY_COLORS[s] || "#6B7280"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Deadlock Analysis */}
      {deadlockData.model_combo_deadlock_rates && Object.keys(deadlockData.model_combo_deadlock_rates).length > 0 && (
        <div className="nb-card p-6">
          <h3 className="text-base font-black uppercase tracking-wider mb-4">
            Deadlock Analysis
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-[var(--border)]">
                  <th className="text-left py-2 font-black">Model Combination</th>
                  <th className="text-right py-2 font-black">Total Debates</th>
                  <th className="text-right py-2 font-black">Deadlocked</th>
                  <th className="text-right py-2 font-black">Deadlock Rate</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(deadlockData.model_combo_deadlock_rates)
                  .sort(([, a]: any, [, b]: any) => b.rate - a.rate)
                  .map(([combo, d]: [string, any]) => (
                    <tr key={combo} className="border-b border-gray-200">
                      <td className="py-2 font-mono text-xs">{combo}</td>
                      <td className="text-right py-2">{d.total}</td>
                      <td className="text-right py-2">{d.deadlocked}</td>
                      <td className="text-right py-2 font-bold">
                        <span className={d.rate > 0.5 ? "text-red-600" : d.rate > 0.2 ? "text-yellow-600" : "text-green-600"}>
                          {(d.rate * 100).toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
