"use client";
import { useState, useEffect } from "react";
import { getStrategyComparison, getAggressivenessHeatmap } from "@/lib/api";
import { STRATEGY_LABELS, STRATEGY_COLORS } from "@/lib/constants";
import { formatPercentage, formatLatency, formatTokens } from "@/lib/utils";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from "recharts";

const TOOLTIP_STYLE = { backgroundColor: "#FFFFFF", border: "2px solid #1A1A2E", borderRadius: "6px", boxShadow: "4px 4px 0px #1A1A2E", fontSize: 14 };
const AXIS_TICK = { fontSize: 14, fill: "#1A1A2E", fontWeight: 700 };
const GRID_COLOR = "#D1D5DB";

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<any[]>([]);
  const [heatmap, setHeatmap] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      getStrategyComparison().catch(() => []),
      getAggressivenessHeatmap().catch(() => []),
    ]).then(([s, h]) => {
      setStrategies(s);
      setHeatmap(h);
    });
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8 uppercase tracking-wide">Strategy Comparison</h1>

      {/* Strategy Table */}
      <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)] mb-8">
        <div className="overflow-x-auto">
          <table className="w-full text-base">
            <thead>
              <tr className="bg-[#F5E6D3]">
                <th className="pb-3 pt-3 pr-4 pl-4 text-left font-bold border-b-2 border-[var(--border)]">Strategy</th>
                <th className="pb-3 pt-3 pr-4 text-left font-bold border-b-2 border-[var(--border)]">Debates</th>
                <th className="pb-3 pt-3 pr-4 text-left font-bold border-b-2 border-[var(--border)]">Accuracy</th>
                <th className="pb-3 pt-3 pr-4 text-left font-bold border-b-2 border-[var(--border)]">Avg Latency</th>
                <th className="pb-3 pt-3 pr-4 text-left font-bold border-b-2 border-[var(--border)]">Avg Tokens</th>
                <th className="pb-3 pt-3 pr-4 text-left font-bold border-b-2 border-[var(--border)]">Avg Turns</th>
                <th className="pb-3 pt-3 pr-4 text-left font-bold border-b-2 border-[var(--border)]">Deadlock Rate</th>
                <th className="pb-3 pt-3 pr-4 text-left font-bold border-b-2 border-[var(--border)]">Confidence</th>
                <th className="pb-3 pt-3 text-left font-bold border-b-2 border-[var(--border)]">Aggressiveness</th>
              </tr>
            </thead>
            <tbody>
              {strategies.map((s) => (
                <tr key={s.strategy} className="border-b border-[var(--border)]/20">
                  <td className="py-3 pr-4 pl-4">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded-sm border-2 border-[var(--border)]" style={{ backgroundColor: STRATEGY_COLORS[s.strategy] }} />
                      <span className="font-bold">{STRATEGY_LABELS[s.strategy] || s.strategy}</span>
                    </div>
                  </td>
                  <td className="py-3 pr-4 font-bold">{s.total_debates}</td>
                  <td className="py-3 pr-4 font-bold" style={{ color: s.accuracy > 0.7 ? "#2ECC71" : s.accuracy > 0.4 ? "#FFD93D" : "#FF6B6B" }}>
                    {formatPercentage(s.accuracy)}
                  </td>
                  <td className="py-3 pr-4 font-medium">{formatLatency(s.avg_latency_ms)}</td>
                  <td className="py-3 pr-4 font-medium">{formatTokens(s.avg_tokens)}</td>
                  <td className="py-3 pr-4 font-medium">{s.avg_turns.toFixed(1)}</td>
                  <td className="py-3 pr-4 font-medium">{formatPercentage(s.deadlock_rate)}</td>
                  <td className="py-3 pr-4 font-medium">{formatPercentage(s.avg_confidence)}</td>
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-3 bg-[var(--secondary)] rounded-sm overflow-hidden border-2 border-[var(--border)]">
                        <div className="h-full bg-[#FF8A5C]" style={{ width: `${s.avg_aggressiveness * 100}%` }} />
                      </div>
                      <span className="text-xs font-bold">{(s.avg_aggressiveness * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {strategies.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Multi-metric Bar Chart */}
          <div className="p-4 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
            <h3 className="text-lg font-bold mb-4 uppercase tracking-wide">Accuracy vs Deadlock Rate</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={strategies.map(s => ({
                name: (STRATEGY_LABELS[s.strategy] || s.strategy).split(" ")[0],
                accuracy: +(s.accuracy * 100).toFixed(1),
                deadlock: +(s.deadlock_rate * 100).toFixed(1),
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
                <XAxis dataKey="name" tick={AXIS_TICK} />
                <YAxis tick={AXIS_TICK} domain={[0, 100]} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="accuracy" name="Accuracy %" fill="#2ECC71" />
                <Bar dataKey="deadlock" name="Deadlock %" fill="#FF6B6B" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Aggressiveness Heatmap */}
          <div className="p-4 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
            <h3 className="text-lg font-bold mb-4 uppercase tracking-wide">Aggressiveness Heatmap</h3>
            {heatmap.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr>
                      <th className="pb-2 text-left font-bold text-[var(--foreground)]">Model</th>
                      {[...new Set(heatmap.map(h => h.strategy))].map(s => (
                        <th key={s} className="pb-2 text-center text-xs font-bold text-[var(--foreground)]">
                          {(STRATEGY_LABELS[s] || s).split(" ")[0]}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[...new Set(heatmap.map(h => h.model_id))].map(model => (
                      <tr key={model} className="border-t border-[var(--border)]/20">
                        <td className="py-2 text-xs font-bold">{model.split("/").pop()?.split(":")[0]}</td>
                        {[...new Set(heatmap.map(h => h.strategy))].map(strategy => {
                          const cell = heatmap.find(h => h.model_id === model && h.strategy === strategy);
                          const val = cell?.avg_aggressiveness || 0;
                          const bg = val > 0.5 ? "#FF6B6B" : val > 0.3 ? "#FF8A5C" : val > 0.15 ? "#FFD93D" : "#F5E6D3";
                          return (
                            <td key={strategy} className="py-2 text-center">
                              <div
                                className="mx-auto w-12 h-8 rounded-sm flex items-center justify-center text-xs font-bold border-2 border-[var(--border)]"
                                style={{ backgroundColor: bg }}
                              >
                                {(val * 100).toFixed(0)}%
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-[var(--muted-foreground)] font-medium">No heatmap data yet</p>
            )}
          </div>
        </div>
      )}

      {strategies.length === 0 && (
        <div className="text-center py-16 text-[var(--muted-foreground)] font-medium">
          Run debates to see strategy comparisons.
        </div>
      )}
    </div>
  );
}
