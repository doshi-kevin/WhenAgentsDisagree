const API_BASE = "/api";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API Error ${res.status}: ${error}`);
  }
  return res.json();
}

// --- Scenarios ---
export const getScenarios = (category?: string) =>
  fetchAPI<any[]>(`/scenarios${category ? `?category=${category}` : ""}`);

export const getScenario = (id: string) => fetchAPI<any>(`/scenarios/${id}`);

// --- Debates ---
export const getDebates = (params?: Record<string, string>) => {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return fetchAPI<any[]>(`/debates${qs}`);
};

export const getDebate = (id: string) => fetchAPI<any>(`/debates/${id}`);

export const createDebate = (data: any) =>
  fetchAPI<any>("/debates", { method: "POST", body: JSON.stringify(data) });

// --- Experiments ---
export const getExperiments = () => fetchAPI<any[]>("/experiments");
export const getExperiment = (id: string) => fetchAPI<any>(`/experiments/${id}`);
export const createExperiment = (data: any) =>
  fetchAPI<any>("/experiments", { method: "POST", body: JSON.stringify(data) });

// --- Admin ---
export const getOverview = () => fetchAPI<any>("/admin/overview");
export const getStrategyComparison = () => fetchAPI<any[]>("/admin/strategies/compare");
export const getModelComparison = () => fetchAPI<any[]>("/admin/models/compare");
export const getAvailableModels = () => fetchAPI<any[]>("/admin/models/available");
export const getConfidenceTrajectories = (debateId?: string) =>
  fetchAPI<any[]>(`/admin/confidence/trajectories${debateId ? `?debate_id=${debateId}` : ""}`);
export const getAggressivenessHeatmap = () => fetchAPI<any[]>("/admin/aggressiveness/heatmap");
export const getDeadlockStats = () => fetchAPI<any[]>("/admin/deadlocks/stats");
export const getResearchInsights = () => fetchAPI<any>("/admin/research/insights");
