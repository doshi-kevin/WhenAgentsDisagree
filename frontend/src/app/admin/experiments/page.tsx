"use client";
import { useState, useEffect } from "react";
import { getExperiments, getDebates } from "@/lib/api";
import { STRATEGY_LABELS, STATUS_COLORS } from "@/lib/constants";
import { formatLatency, timeAgo, formatPercentage } from "@/lib/utils";

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<any[]>([]);
  const [debates, setDebates] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([
      getExperiments().catch(() => []),
      getDebates({ limit: "100" }).catch(() => []),
    ]).then(([e, d]) => {
      setExperiments(e);
      setDebates(d);
    });
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8 uppercase tracking-wide">Experiments</h1>

      {experiments.length > 0 && (
        <div className="space-y-4 mb-8">
          {experiments.map((exp) => (
            <div key={exp.id} className="p-4 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-bold">{exp.name}</h3>
                <span
                  className="text-xs px-2.5 py-1 rounded-md font-bold border-2 border-[var(--border)]"
                  style={{ backgroundColor: STATUS_COLORS[exp.status] || "#6B7280" }}
                >
                  {exp.status}
                </span>
              </div>
              <p className="text-sm text-[var(--muted-foreground)] font-medium">
                {exp.description || "No description"}
              </p>
              <div className="text-xs text-[var(--muted-foreground)] mt-2 font-medium">
                Created: {timeAgo(exp.created_at)}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* All Debates Table */}
      <h2 className="text-2xl font-bold mb-5 uppercase tracking-wide">All Debates</h2>
      <div className="p-5 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
        <div className="overflow-x-auto">
          <table className="w-full text-base">
            <thead>
              <tr className="bg-[#F5E6D3]">
                <th className="pb-3 pt-3 px-3 text-left font-bold border-b-2 border-[var(--border)]">Status</th>
                <th className="pb-3 pt-3 px-3 text-left font-bold border-b-2 border-[var(--border)]">Strategy</th>
                <th className="pb-3 pt-3 px-3 text-left font-bold border-b-2 border-[var(--border)]">Agents</th>
                <th className="pb-3 pt-3 px-3 text-left font-bold border-b-2 border-[var(--border)]">Result</th>
                <th className="pb-3 pt-3 px-3 text-left font-bold border-b-2 border-[var(--border)]">Turns</th>
                <th className="pb-3 pt-3 px-3 text-left font-bold border-b-2 border-[var(--border)]">Latency</th>
                <th className="pb-3 pt-3 px-3 text-left font-bold border-b-2 border-[var(--border)]">Deadlock</th>
                <th className="pb-3 pt-3 px-3 text-left font-bold border-b-2 border-[var(--border)]">Created</th>
                <th className="pb-3 pt-3 px-3 text-left font-bold border-b-2 border-[var(--border)]"></th>
              </tr>
            </thead>
            <tbody>
              {debates.map((d) => (
                <tr key={d.id} className="border-b border-[var(--border)]/20">
                  <td className="py-3 px-3">
                    <span
                      className="text-xs px-2 py-0.5 rounded-md font-bold border-2 border-[var(--border)]"
                      style={{ backgroundColor: STATUS_COLORS[d.status] || "#6B7280" }}
                    >
                      {d.status}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-medium">{STRATEGY_LABELS[d.strategy] || d.strategy}</td>
                  <td className="py-3 px-3 font-bold">{d.agents?.length || 0}</td>
                  <td className="py-3 px-3">
                    {d.is_correct !== null && (
                      <span className={`font-bold ${d.is_correct ? "text-[#2ECC71]" : "text-[#FF6B6B]"}`}>
                        {d.is_correct ? "Correct" : "Wrong"}
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-bold">{d.total_turns}</td>
                  <td className="py-3 px-3 font-medium">{formatLatency(d.total_latency_ms)}</td>
                  <td className="py-3 px-3 font-medium">{d.deadlock_detected ? "Yes" : "No"}</td>
                  <td className="py-3 px-3 text-[var(--muted-foreground)] font-medium">{timeAgo(d.created_at)}</td>
                  <td className="py-3 px-3">
                    <a
                      href={`/admin/debate/${d.id}`}
                      className="text-xs px-3 py-1 rounded-md bg-[#4ECDC4] font-bold border-2 border-[var(--border)] shadow-[2px_2px_0px_var(--shadow-color)] hover:shadow-[3px_3px_0px_var(--shadow-color)] hover:translate-x-[-1px] hover:translate-y-[-1px] transition-all"
                    >
                      View
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {debates.length === 0 && (
          <p className="text-center py-8 text-[var(--muted-foreground)] font-bold">No debates yet</p>
        )}
      </div>
    </div>
  );
}
