"use client";
import { useState, useEffect } from "react";
import { getModelComparison, getConfidenceTrajectories } from "@/lib/api";
import { PROVIDER_LABELS, PROVIDER_COLORS } from "@/lib/constants";
import { formatPercentage, formatLatency, formatTokens } from "@/lib/utils";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer, LineChart, Line, Legend } from "recharts";

const MODEL_CHART_COLORS = ["#FF6B6B", "#6C5CE7", "#2ECC71", "#FFD93D", "#4ECDC4", "#FF8A5C"];
const TOOLTIP_STYLE = { backgroundColor: "#FFFFFF", border: "2px solid #1A1A2E", borderRadius: "6px", boxShadow: "4px 4px 0px #1A1A2E", fontSize: 14 };
const AXIS_TICK = { fontSize: 14, fill: "#1A1A2E", fontWeight: 700 };
const GRID_COLOR = "#D1D5DB";

export default function ModelsPage() {
  const [models, setModels] = useState<any[]>([]);
  const [trajectories, setTrajectories] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      getModelComparison().catch(() => []),
      getConfidenceTrajectories().catch(() => []),
    ]).then(([m, t]) => {
      setModels(m);
      setTrajectories(t);
    });
  }, []);

  const chartData = models.map((m, i) => ({
    name: m.model_id.split("/").pop()?.split(":")[0] || m.model_id,
    accuracy: +(m.accuracy * 100).toFixed(1),
    confidence: +(m.avg_confidence * 100).toFixed(1),
    aggressiveness: +(m.avg_aggressiveness * 100).toFixed(1),
    fill: MODEL_CHART_COLORS[i % MODEL_CHART_COLORS.length],
  }));

  const modelGroups = trajectories.reduce((acc: any, t: any) => {
    const key = t.model_id || "unknown";
    if (!acc[key]) acc[key] = [];
    acc[key].push(t);
    return acc;
  }, {});

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8 uppercase tracking-wide">Model Comparison</h1>

      {/* Model Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
        {models.map((m, i) => (
          <div key={i} className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
            <div className="flex items-center gap-2 mb-3">
              <div
                className="w-5 h-5 rounded-sm border-2 border-[var(--border)]"
                style={{ backgroundColor: PROVIDER_COLORS[m.provider] || "#6C5CE7" }}
              />
              <span className="font-bold text-lg">
                {m.model_id.split("/").pop()?.split(":")[0]}
              </span>
            </div>
            <div className="text-sm text-[var(--muted-foreground)] mb-4 font-medium">
              {PROVIDER_LABELS[m.provider] || m.provider} &middot; {m.total_debates} debates
            </div>
            <div className="grid grid-cols-2 gap-4 text-base">
              <div>
                <div className="text-[var(--muted-foreground)] text-sm font-bold uppercase">Accuracy</div>
                <div className="font-bold text-lg text-[#2ECC71]">{formatPercentage(m.accuracy)}</div>
              </div>
              <div>
                <div className="text-[var(--muted-foreground)] text-sm font-bold uppercase">Avg Latency</div>
                <div className="font-bold text-lg">{formatLatency(m.avg_latency_ms)}</div>
              </div>
              <div>
                <div className="text-[var(--muted-foreground)] text-sm font-bold uppercase">Confidence</div>
                <div className="font-bold text-lg text-[#4ECDC4]">{formatPercentage(m.avg_confidence)}</div>
              </div>
              <div>
                <div className="text-[var(--muted-foreground)] text-sm font-bold uppercase">Aggressiveness</div>
                <div className="font-bold text-lg text-[#FF6B6B]">{formatPercentage(m.avg_aggressiveness)}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {models.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Accuracy Comparison */}
          <div className="p-4 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
            <h3 className="text-lg font-bold mb-4 uppercase tracking-wide">Model Accuracy Comparison</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
                <XAxis dataKey="name" tick={{ fontSize: 13, fill: "#1A1A2E", fontWeight: 700 }} />
                <YAxis tick={AXIS_TICK} domain={[0, 100]} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="accuracy" name="Accuracy %">
                  {chartData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Confidence vs Aggressiveness */}
          <div className="p-4 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
            <h3 className="text-lg font-bold mb-4 uppercase tracking-wide">Confidence vs Aggressiveness</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={GRID_COLOR} />
                <XAxis dataKey="name" tick={{ fontSize: 13, fill: "#1A1A2E", fontWeight: 700 }} />
                <YAxis tick={AXIS_TICK} domain={[0, 100]} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="confidence" name="Confidence %" fill="#4ECDC4" />
                <Bar dataKey="aggressiveness" name="Aggressiveness %" fill="#FF6B6B" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {models.length === 0 && (
        <div className="text-center py-16 text-[var(--muted-foreground)] font-medium">
          Run debates to see model comparisons.
        </div>
      )}
    </div>
  );
}
