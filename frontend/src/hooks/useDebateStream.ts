"use client";
import { useState, useEffect, useCallback } from "react";

interface StreamEvent {
  type: string;
  data: Record<string, any>;
}

export function useDebateStream(debateId: string | null) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [status, setStatus] = useState<"idle" | "connecting" | "live" | "ended" | "error">("idle");
  const [finalResult, setFinalResult] = useState<any>(null);

  useEffect(() => {
    if (!debateId) return;

    setStatus("connecting");
    setEvents([]);
    setFinalResult(null);

    const eventSource = new EventSource(`/api/stream/debate/${debateId}`);

    eventSource.addEventListener("connected", () => {
      setStatus("live");
    });

    eventSource.addEventListener("debate_start", (e) => {
      const data = JSON.parse(e.data);
      setEvents((prev) => [...prev, { type: "debate_start", data }]);
    });

    eventSource.addEventListener("agent_turn", (e) => {
      const data = JSON.parse(e.data);
      setEvents((prev) => [...prev, { type: "agent_turn", data }]);
    });

    eventSource.addEventListener("metrics_update", (e) => {
      const data = JSON.parse(e.data);
      setEvents((prev) => [...prev, { type: "metrics_update", data }]);
    });

    eventSource.addEventListener("deadlock_warning", (e) => {
      const data = JSON.parse(e.data);
      setEvents((prev) => [...prev, { type: "deadlock_warning", data }]);
    });

    eventSource.addEventListener("debate_end", (e) => {
      const data = JSON.parse(e.data);
      setEvents((prev) => [...prev, { type: "debate_end", data }]);
      setFinalResult(data);
      setStatus("ended");
      eventSource.close();
    });

    eventSource.addEventListener("error", (e) => {
      const data = JSON.parse((e as any).data || "{}");
      setStatus("error");
      eventSource.close();
    });

    eventSource.onerror = () => {
      if (status !== "ended") {
        setStatus("error");
      }
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [debateId]);

  const agentTurns = events.filter((e) => e.type === "agent_turn").map((e) => e.data);
  const deadlockWarnings = events.filter((e) => e.type === "deadlock_warning");

  return {
    events,
    agentTurns,
    deadlockWarnings,
    status,
    finalResult,
  };
}
