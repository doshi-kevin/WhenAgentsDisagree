"use client";
import { useState, useEffect } from "react";
import { getScenarios, getDebates, createDebate, getAvailableModels } from "@/lib/api";
import { STRATEGY_LABELS, STRATEGY_DESCRIPTIONS, STRATEGY_COLORS, CATEGORY_LABELS, DIFFICULTY_COLORS, STATUS_COLORS, BIAS_ROLE_LABELS, BIAS_ROLE_COLORS } from "@/lib/constants";
import { formatLatency, timeAgo } from "@/lib/utils";

export default function HomePage() {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [debates, setDebates] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedScenario, setSelectedScenario] = useState<any>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<string>("structured_debate");
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getScenarios().catch(() => []),
      getDebates({ limit: "20" }).catch(() => []),
      getAvailableModels().catch(() => []),
    ]).then(([s, d, m]) => {
      setScenarios(s);
      setDebates(d);
      const available = m.filter((m: any) => m.available);
      setModels(available);
      if (available.length > 0) {
        const seen = new Set<string>();
        const perProvider: string[] = [];
        for (const model of available) {
          if (!seen.has(model.provider)) {
            seen.add(model.provider);
            perProvider.push(`${model.provider}:${model.model_id}`);
          }
        }
        setSelectedModels(perProvider);
      }
    });
  }, []);

  const categories = ["all", ...new Set(scenarios.map((s) => s.category))];
  const filtered = selectedCategory === "all" ? scenarios : scenarios.filter((s) => s.category === selectedCategory);

  const handleRunDebate = async () => {
    if (!selectedScenario || selectedModels.length < 3) return;
    setLoading(true);
    setError(null);

    const agents = selectedModels.map((m, i) => {
      const [provider, ...modelParts] = m.split(":");
      return {
        agent_name: `Agent ${String.fromCharCode(65 + i)}`,
        provider,
        model_id: modelParts.join(":"),
        role: selectedStrategy === "hierarchical" && i === selectedModels.length - 1 ? "lead" : "advocate",
        briefing_index: i,
      };
    });

    try {
      const result = await createDebate({
        scenario_id: selectedScenario.id,
        strategy: selectedStrategy,
        agents,
        max_rounds: 5,
      });
      window.location.href = `/debate/${result.debate_id}`;
    } catch (e: any) {
      setError(e.message);
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Hero */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold mb-4">
          When Agents{" "}
          <span className="bg-[#FF6B6B] text-white px-3 py-1 border-2 border-[var(--border)] shadow-[3px_3px_0px_var(--shadow-color)] inline-block rotate-[-1deg]">
            Disagree
          </span>
        </h1>
        <p className="text-[var(--muted-foreground)] text-xl max-w-2xl mx-auto font-medium mt-4">
          Evaluating Conflict Resolution Strategies in Multi-Agent LLM Systems.
          Select a scenario, choose your strategy, and watch agents debate in real-time.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Scenario Selection */}
        <div className="lg:col-span-2">
          <h2 className="text-2xl font-bold mb-5 uppercase tracking-wide">Pick a Conflict Scenario</h2>

          {/* Category Tabs */}
          <div className="flex gap-2 mb-4 flex-wrap">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-4 py-2.5 text-base font-bold border-2 border-[var(--border)] rounded-md transition-all ${
                  selectedCategory === cat
                    ? "bg-[#4ECDC4] text-[var(--foreground)] shadow-[2px_2px_0px_var(--shadow-color)]"
                    : "bg-white text-[var(--foreground)] shadow-[2px_2px_0px_var(--shadow-color)] hover:bg-[var(--secondary)]"
                }`}
              >
                {cat === "all" ? "All" : CATEGORY_LABELS[cat] || cat}
              </button>
            ))}
          </div>

          {/* Scenario Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filtered.map((scenario) => (
              <button
                key={scenario.id}
                onClick={() => setSelectedScenario(scenario)}
                className={`text-left p-4 rounded-md border-2 border-[var(--border)] transition-all ${
                  selectedScenario?.id === scenario.id
                    ? "bg-[#FFD93D] shadow-[4px_4px_0px_var(--shadow-color)]"
                    : "bg-white shadow-[4px_4px_0px_var(--shadow-color)] hover:shadow-[6px_6px_0px_var(--shadow-color)] hover:translate-x-[-2px] hover:translate-y-[-2px]"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className="text-xs px-2 py-0.5 rounded-md font-bold border-2 border-[var(--border)]"
                    style={{ backgroundColor: DIFFICULTY_COLORS[scenario.difficulty] }}
                  >
                    {scenario.difficulty}
                  </span>
                  <span className="text-xs text-[var(--muted-foreground)] font-medium">
                    {CATEGORY_LABELS[scenario.category] || scenario.category}
                  </span>
                </div>
                <h3 className="font-bold text-base mb-1">{scenario.title}</h3>
                <p className="text-sm text-[var(--muted-foreground)] line-clamp-2 leading-relaxed">
                  {scenario.question}
                </p>
              </button>
            ))}
          </div>

          {/* Misinformation Battle Info */}
          {selectedScenario?.category === "misinformation_battle" && (
            <div className="mt-4 p-4 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
              <h3 className="font-bold text-base mb-3 uppercase tracking-wide">Agent Roles (2 vs 1)</h3>
              <div className="flex gap-3 flex-wrap">
                {selectedScenario.agent_briefings?.map((b: any, i: number) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-md border-2 border-[var(--border)] text-white font-bold text-sm"
                    style={{ backgroundColor: BIAS_ROLE_COLORS[b.bias_role] || "#6B7280" }}
                  >
                    <span>Agent {String.fromCharCode(65 + i)}:</span>
                    <span>{BIAS_ROLE_LABELS[b.bias_role] || b.bias_role}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-[var(--muted-foreground)] mt-2 font-medium">
                Can truth prevail when outnumbered by misinformation? The Liar and Manipulator team up against the Truth Teller.
              </p>
            </div>
          )}

          {scenarios.length === 0 && (
            <div className="text-center py-12 nb-card p-8">
              <p className="text-lg mb-2 font-bold">No scenarios loaded yet</p>
              <p className="text-sm text-[var(--muted-foreground)]">Start the backend server and load scenarios first.</p>
            </div>
          )}
        </div>

        {/* Configuration Panel */}
        <div className="space-y-6">
          {/* Strategy Selection */}
          <div>
            <h3 className="text-lg font-bold mb-3 uppercase tracking-wide">Resolution Strategy</h3>
            <div className="space-y-2">
              {Object.entries(STRATEGY_LABELS).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setSelectedStrategy(key)}
                  className={`w-full text-left p-3 rounded-md border-2 border-[var(--border)] transition-all ${
                    selectedStrategy === key
                      ? "bg-[#4ECDC4] shadow-[4px_4px_0px_var(--shadow-color)]"
                      : "bg-white shadow-[2px_2px_0px_var(--shadow-color)] hover:shadow-[4px_4px_0px_var(--shadow-color)] hover:translate-x-[-2px] hover:translate-y-[-2px]"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div
                      className="w-4 h-4 rounded-sm border-2 border-[var(--border)]"
                      style={{ backgroundColor: STRATEGY_COLORS[key] }}
                    />
                    <span className="font-bold text-base">{label}</span>
                  </div>
                  <p className="text-xs text-[var(--muted-foreground)] mt-1 ml-6">
                    {STRATEGY_DESCRIPTIONS[key]}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Model Selection */}
          <div>
            <h3 className="text-lg font-bold mb-3 uppercase tracking-wide">Select Models (min 3)</h3>
            <div className="space-y-4">
              {Array.from(new Set(models.map((m: any) => m.provider))).map((provider) => (
                <div key={provider as string}>
                  <div className="text-xs font-bold text-[var(--foreground)] mb-1.5 uppercase tracking-widest">
                    {models.find((m: any) => m.provider === provider)?.provider_display}
                  </div>
                  <div className="space-y-1.5">
                    {models
                      .filter((m: any) => m.provider === provider)
                      .map((model: any) => {
                        const key = `${model.provider}:${model.model_id}`;
                        const isSelected = selectedModels.includes(key);
                        return (
                          <button
                            key={key}
                            onClick={() =>
                              setSelectedModels((prev) =>
                                isSelected ? prev.filter((m) => m !== key) : [...prev, key]
                              )
                            }
                            className={`w-full text-left p-3 rounded-md border-2 border-[var(--border)] transition-all ${
                              isSelected
                                ? "bg-[#2ECC71] shadow-[4px_4px_0px_var(--shadow-color)]"
                                : "bg-white shadow-[2px_2px_0px_var(--shadow-color)] hover:shadow-[4px_4px_0px_var(--shadow-color)] hover:translate-x-[-2px] hover:translate-y-[-2px]"
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              <div
                                className="w-3 h-3 rounded-sm border-2 border-[var(--border)]"
                                style={{ backgroundColor: model.color }}
                              />
                              <span className="text-base font-bold">{model.model_display}</span>
                            </div>
                          </button>
                        );
                      })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Run Button */}
          <button
            onClick={handleRunDebate}
            disabled={!selectedScenario || selectedModels.length < 3 || loading}
            className="w-full py-4 px-6 rounded-md bg-[#FF6B6B] text-white font-bold text-lg border-2 border-[var(--border)] shadow-[4px_4px_0px_var(--shadow-color)] hover:shadow-[6px_6px_0px_var(--shadow-color)] hover:translate-x-[-2px] hover:translate-y-[-2px] active:shadow-[2px_2px_0px_var(--shadow-color)] active:translate-x-[2px] active:translate-y-[2px] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-[4px_4px_0px_var(--shadow-color)] disabled:hover:translate-x-0 disabled:hover:translate-y-0 transition-all uppercase tracking-wider"
          >
            {loading ? "Starting Debate..." : "Run Debate"}
          </button>
          {error && <p className="text-sm text-[var(--destructive)] font-bold mt-2">{error}</p>}

          {/* Recent Debates */}
          <div>
            <h3 className="text-lg font-bold mb-3 uppercase tracking-wide">Recent Debates</h3>
            <div className="space-y-2">
              {debates.slice(0, 5).map((d) => (
                <a
                  key={d.id}
                  href={`/debate/${d.id}`}
                  className="block p-3 rounded-md border-2 border-[var(--border)] bg-white shadow-[2px_2px_0px_var(--shadow-color)] hover:shadow-[4px_4px_0px_var(--shadow-color)] hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className="text-xs px-2 py-0.5 rounded-md font-bold border-2 border-[var(--border)]"
                      style={{ backgroundColor: STATUS_COLORS[d.status] }}
                    >
                      {d.status}
                    </span>
                    <span className="text-xs text-[var(--muted-foreground)] font-medium">
                      {timeAgo(d.created_at)}
                    </span>
                  </div>
                  <div className="text-sm font-bold">
                    {STRATEGY_LABELS[d.strategy] || d.strategy}
                  </div>
                  <div className="text-xs text-[var(--muted-foreground)] font-medium">
                    {d.agents?.length || 0} agents &middot; {d.total_turns} turns &middot; {formatLatency(d.total_latency_ms)}
                  </div>
                </a>
              ))}
              {debates.length === 0 && (
                <p className="text-sm text-[var(--muted-foreground)] font-medium">No debates yet</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
