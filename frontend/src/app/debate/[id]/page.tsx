"use client";
import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { getDebate } from "@/lib/api";
import { useDebateStream } from "@/hooks/useDebateStream";
import { STRATEGY_LABELS, STRATEGY_COLORS, AGENT_COLORS, PROVIDER_LABELS } from "@/lib/constants";
import { formatLatency, formatTokens, formatPercentage } from "@/lib/utils";

export default function DebatePage() {
  const { id } = useParams<{ id: string }>();
  const [debate, setDebate] = useState<any>(null);
  const [isLive, setIsLive] = useState(false);
  const { events, agentTurns, deadlockWarnings, status, finalResult } = useDebateStream(isLive ? id : null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id) return;
    getDebate(id).then((d) => {
      setDebate(d);
      if (d.status === "running" || d.status === "pending") {
        setIsLive(true);
      }
    }).catch(() => {
      setIsLive(true);
    });
  }, [id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [agentTurns, debate?.turns]);

  const turns = isLive && agentTurns.length > 0 ? agentTurns : debate?.turns || [];
  const result = finalResult || (debate?.status === "completed" ? debate : null);
  const agents = debate?.agents || [];
  const scenario = debate?.scenario;
  const strategy = debate?.strategy || "";

  useEffect(() => {
    if (status === "ended" && id) {
      setTimeout(() => getDebate(id).then(setDebate), 1000);
    }
  }, [status, id]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-3xl font-bold">
              {scenario?.title || "Debate"}
            </h1>
            {strategy && (
              <span
                className="text-xs px-3 py-1 rounded-md font-bold border-2 border-[var(--border)]"
                style={{ backgroundColor: STRATEGY_COLORS[strategy] || "#4ECDC4" }}
              >
                {STRATEGY_LABELS[strategy] || strategy}
              </span>
            )}
          </div>
          <p className="text-sm text-[var(--muted-foreground)] font-medium">
            {scenario?.question}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {(status === "live" || debate?.status === "running") && (
            <span className="flex items-center gap-2 text-sm font-bold text-[var(--foreground)] px-3 py-1 bg-[#FF6B6B] text-white border-2 border-[var(--border)] rounded-md shadow-[2px_2px_0px_var(--shadow-color)]">
              <span className="w-3 h-3 bg-white border-2 border-[var(--border)] animate-pulse" />
              LIVE
            </span>
          )}
          {result?.is_correct !== undefined && (
            <span
              className={`text-sm px-3 py-1 rounded-md font-bold border-2 border-[var(--border)] shadow-[2px_2px_0px_var(--shadow-color)] ${
                result.is_correct
                  ? "bg-[#2ECC71] text-[var(--foreground)]"
                  : "bg-[#FF6B6B] text-white"
              }`}
            >
              {result.is_correct ? "Correct" : "Incorrect"}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Agents Panel */}
        <div className="space-y-3">
          <h3 className="font-bold text-base text-[var(--foreground)] uppercase tracking-wider">
            Agents
          </h3>
          {agents.map((agent: any, i: number) => {
            const latestTurn = [...turns].reverse().find(
              (t: any) => (t.agent_name || t.debate_agent_id) === (agent.agent_name || agent.id)
            );
            const confidence = latestTurn?.confidence_score ?? latestTurn?.confidence ?? null;

            return (
              <div
                key={agent.id || i}
                className="p-3 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="w-5 h-5 rounded-sm border-2 border-[var(--border)]"
                    style={{ backgroundColor: AGENT_COLORS[i] }}
                  />
                  <span className="font-bold text-base">{agent.agent_name}</span>
                </div>
                <div className="text-sm text-[var(--muted-foreground)] space-y-1 font-medium">
                  <div>{PROVIDER_LABELS[agent.provider] || agent.provider}</div>
                  <div className="truncate">{agent.model_id}</div>
                  <div>Role: {agent.role}</div>
                  {agent.assigned_position && (
                    <div className="mt-1 px-2 py-0.5 rounded-md bg-[var(--secondary)] text-[var(--foreground)] font-bold border-2 border-[var(--border)]">
                      Position: {agent.assigned_position}
                    </div>
                  )}
                </div>
                {confidence !== null && (
                  <div className="mt-2">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-[var(--muted-foreground)] font-medium">Confidence</span>
                      <span className="font-bold">{formatPercentage(confidence)}</span>
                    </div>
                    <div className="h-3 bg-[var(--secondary)] rounded-sm overflow-hidden border-2 border-[var(--border)]">
                      <div
                        className="h-full transition-all duration-500"
                        style={{
                          width: `${confidence * 100}%`,
                          backgroundColor: AGENT_COLORS[i],
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          {/* Deadlock Warning */}
          {deadlockWarnings.length > 0 && (
            <div className="p-3 rounded-md border-2 border-[var(--border)] bg-[#FFD93D] shadow-[4px_4px_0px_var(--shadow-color)]">
              <div className="flex items-center gap-2 text-[var(--foreground)] text-sm font-bold mb-1">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                DEADLOCK DETECTED
              </div>
              <p className="text-xs text-[var(--foreground)] font-medium">
                Agents are repeating similar arguments. Arbitration may be triggered.
              </p>
            </div>
          )}
        </div>

        {/* Debate Timeline */}
        <div className="lg:col-span-2">
          <h3 className="font-bold text-base text-[var(--foreground)] uppercase tracking-wider mb-3">
            Debate Timeline
          </h3>
          <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-2">
            {turns.map((turn: any, i: number) => {
              const agentIndex = agents.findIndex(
                (a: any) => a.agent_name === turn.agent_name || a.id === turn.debate_agent_id
              );
              const color = AGENT_COLORS[agentIndex >= 0 ? agentIndex : i % AGENT_COLORS.length];
              const confidence = turn.confidence_score ?? turn.confidence;
              const metrics = turn.metrics;

              let displayContent = turn.content;
              try {
                const parsed = typeof turn.content === "string" ? JSON.parse(turn.content) : turn.content;
                displayContent = parsed?.argument || parsed?.reasoning || parsed?.summary || parsed?.answer || parsed?.decision || turn.content;
              } catch {
                // Not JSON, use raw content
              }

              return (
                <div
                  key={turn.id || i}
                  className="animate-slide-in p-4 rounded-md border-2 border-[var(--border)] bg-white shadow-[3px_3px_0px_var(--shadow-color)]"
                  style={{ borderLeftWidth: "6px", borderLeftColor: color }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-base" style={{ color }}>
                        {turn.agent_name}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded-md bg-[var(--secondary)] text-[var(--foreground)] font-bold border-2 border-[var(--border)]">
                        R{turn.round_number || 1} &middot; T{turn.turn_number}
                      </span>
                      <span className="text-xs px-1.5 py-0.5 rounded-md bg-[var(--secondary)] text-[var(--muted-foreground)] font-medium">
                        {turn.role}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)] font-medium">
                      {turn.latency_ms > 0 && <span>{formatLatency(turn.latency_ms)}</span>}
                      {(turn.total_tokens > 0) && <span>{formatTokens(turn.total_tokens)} tok</span>}
                    </div>
                  </div>

                  <p className="text-base leading-relaxed whitespace-pre-wrap">
                    {displayContent}
                  </p>

                  {/* Position & Confidence */}
                  <div className="flex flex-wrap items-center gap-2 mt-3">
                    {turn.position_held && (
                      <span className="text-xs px-2 py-0.5 rounded-md border-2 border-[var(--border)] font-bold bg-[var(--secondary)]">
                        Position: {turn.position_held}
                      </span>
                    )}
                    {confidence !== null && confidence !== undefined && (
                      <span className="text-xs px-2 py-0.5 rounded-md bg-[var(--secondary)] border-2 border-[var(--border)] font-bold">
                        Confidence: {formatPercentage(confidence)}
                      </span>
                    )}
                    {turn.position_changed && (
                      <span className="text-xs px-2 py-0.5 rounded-md bg-[#FFD93D] text-[var(--foreground)] font-bold border-2 border-[var(--border)]">
                        Changed Position!
                      </span>
                    )}
                  </div>

                  {/* Metrics Bar */}
                  {metrics && (
                    <div className="flex gap-3 mt-2 text-xs text-[var(--muted-foreground)] font-medium">
                      <span>Aggr: {(metrics.aggressiveness_score ?? metrics.aggressiveness ?? 0).toFixed(2)}</span>
                      <span>Sent: {(metrics.sentiment_score ?? metrics.sentiment ?? 0).toFixed(2)}</span>
                      {metrics.citation_count > 0 && <span>Citations: {metrics.citation_count}</span>}
                      {metrics.semantic_similarity_to_prev !== null && metrics.semantic_similarity_to_prev !== undefined && (
                        <span>Similarity: {metrics.semantic_similarity_to_prev.toFixed(2)}</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}

            {(status === "live" || debate?.status === "running") && turns.length > 0 && (
              <div className="flex items-center justify-center py-4">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 bg-[#FF6B6B] border-2 border-[var(--border)] animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-3 h-3 bg-[#4ECDC4] border-2 border-[var(--border)] animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-3 h-3 bg-[#FFD93D] border-2 border-[var(--border)] animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            )}

            {turns.length === 0 && (
              <div className="text-center py-12 text-[var(--muted-foreground)] font-medium">
                {status === "connecting" || debate?.status === "pending" ? (
                  <p>Waiting for debate to start...</p>
                ) : (
                  <p>No turns recorded yet.</p>
                )}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Results Panel */}
        <div className="space-y-4">
          {/* Resolution */}
          {(result?.final_answer || debate?.final_answer) && (
            <div className={`p-4 rounded-md border-2 border-[var(--border)] shadow-[4px_4px_0px_var(--shadow-color)] ${
              (result?.is_correct ?? debate?.is_correct) ? "bg-[#2ECC71]" : "bg-[#FF6B6B]"
            }`}>
              <h3 className="font-bold text-base mb-2 text-white">Resolution</h3>
              <div className="text-lg font-bold mb-1 text-white">
                {result?.final_answer || debate?.final_answer}
              </div>
              {scenario?.ground_truth && (
                <div className="text-xs text-white/80 mt-2">
                  <span className="font-bold">Ground Truth:</span> {scenario.ground_truth}
                </div>
              )}
              {debate?.deadlock_detected && (
                <div className="text-xs text-white/80 mt-1 font-bold">
                  Resolved via: {debate.deadlock_resolution || "arbitration"}
                </div>
              )}
            </div>
          )}

          {/* Stats */}
          <div className="p-4 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
            <h3 className="font-bold text-base mb-3 uppercase tracking-wide">Debate Stats</h3>
            <div className="space-y-2.5 text-base">
              <div className="flex justify-between">
                <span className="text-[var(--muted-foreground)] font-medium">Total Turns</span>
                <span className="font-bold">{debate?.total_turns || turns.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--muted-foreground)] font-medium">Total Tokens</span>
                <span className="font-bold">{formatTokens(debate?.total_tokens || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--muted-foreground)] font-medium">Total Latency</span>
                <span className="font-bold">{formatLatency(debate?.total_latency_ms || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--muted-foreground)] font-medium">Deadlock</span>
                <span className="font-bold">{debate?.deadlock_detected ? "Yes" : "No"}</span>
              </div>
            </div>
          </div>

          {/* Per-Turn Confidence */}
          {turns.length > 0 && (
            <div className="p-4 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
              <h3 className="font-bold text-base mb-3 uppercase tracking-wide">Confidence Over Time</h3>
              <div className="space-y-1">
                {turns.map((t: any, i: number) => {
                  const conf = t.confidence_score ?? t.confidence ?? 0.5;
                  const agentIdx = agents.findIndex((a: any) => a.agent_name === t.agent_name);
                  const color = AGENT_COLORS[agentIdx >= 0 ? agentIdx : 0];
                  return (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      <span className="w-12 text-[var(--muted-foreground)] font-medium">T{t.turn_number}</span>
                      <div className="flex-1 h-3 bg-[var(--secondary)] rounded-sm overflow-hidden border-2 border-[var(--border)]">
                        <div
                          className="h-full transition-all"
                          style={{ width: `${conf * 100}%`, backgroundColor: color }}
                        />
                      </div>
                      <span className="w-10 text-right font-bold">{formatPercentage(conf)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <a
            href={`/admin/debate/${id}`}
            className="block text-center py-3 px-4 rounded-md border-2 border-[var(--border)] bg-[#6C5CE7] text-white font-bold shadow-[2px_2px_0px_var(--shadow-color)] hover:shadow-[4px_4px_0px_var(--shadow-color)] hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all text-base"
          >
            View Full Analysis
          </a>
        </div>
      </div>
    </div>
  );
}
