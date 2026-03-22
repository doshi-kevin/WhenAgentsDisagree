"use client";
import { useState } from "react";

export default function ExportPage() {
  const [format, setFormat] = useState("json");
  const [downloading, setDownloading] = useState(false);

  const handleExport = async () => {
    setDownloading(true);
    try {
      const res = await fetch(`/api/admin/export?format=${format}`);
      if (format === "csv") {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `debates_export.${format}`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `debates_export.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (e) {
      console.error("Export failed:", e);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8 uppercase tracking-wide">Export Data</h1>

      <div className="max-w-lg p-8 rounded-md border-2 border-[var(--border)] bg-white shadow-[4px_4px_0px_var(--shadow-color)]">
        <h3 className="text-lg font-bold mb-5 uppercase tracking-wide">Export All Debate Data</h3>

        <div className="mb-5">
          <label className="text-base font-bold text-[var(--foreground)] mb-2 block">Format</label>
          <div className="flex gap-3">
            {["json", "csv"].map((f) => (
              <button
                key={f}
                onClick={() => setFormat(f)}
                className={`px-5 py-2.5 rounded-md text-base font-bold border-2 border-[var(--border)] transition-all ${
                  format === f
                    ? "bg-[#4ECDC4] shadow-[2px_2px_0px_var(--shadow-color)]"
                    : "bg-white shadow-[2px_2px_0px_var(--shadow-color)] hover:bg-[var(--secondary)]"
                }`}
              >
                {f.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <p className="text-sm text-[var(--muted-foreground)] mb-5 font-medium">
          Exports all completed debates with full turn data, metrics, agent configurations, and scenario information.
        </p>

        <button
          onClick={handleExport}
          disabled={downloading}
          className="w-full py-3.5 px-4 rounded-md bg-[#FF6B6B] text-white text-lg font-bold border-2 border-[var(--border)] shadow-[4px_4px_0px_var(--shadow-color)] hover:shadow-[6px_6px_0px_var(--shadow-color)] hover:translate-x-[-2px] hover:translate-y-[-2px] active:shadow-[2px_2px_0px_var(--shadow-color)] active:translate-x-[2px] active:translate-y-[2px] disabled:opacity-50 disabled:cursor-not-allowed transition-all uppercase tracking-wider"
        >
          {downloading ? "Exporting..." : `Export as ${format.toUpperCase()}`}
        </button>
      </div>
    </div>
  );
}
