"use client";

import { useState } from "react";
import UploadZone from "@/components/UploadZone";
import DataTable from "@/components/DataTable";
import InsightsPanel from "@/components/InsightsPanel";
import DashboardSuggestions from "@/components/DashboardSuggestions";
import DashboardRenderer from "@/components/DashboardRenderer";
import ChatPanel from "@/components/ChatPanel";
import { api, downloadUrl } from "@/lib/api";

type Step = "upload" | "table" | "insights" | "suggest" | "build" | "chat";

export default function Home() {
  const [step, setStep] = useState<Step>("upload");
  const [dataset, setDataset] = useState<any>(null);
  const [insights, setInsights] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [explore, setExplore] = useState<any>({ title: "", summary: "", layouts: [] });
  const [busy, setBusy] = useState(false);
  const [building, setBuilding] = useState(false);
  const [customScenario, setCustomScenario] = useState("");

  async function onUploaded(d: any) {
    setDataset(d);
    setStep("table");
    setBusy(true);
    try {
      const doc = await api.post(`/api/datasets/${d.dataset_id}/insights`);
      setInsights(doc);
      const sug = await api.post(`/api/datasets/${d.dataset_id}/dashboards/suggest`);
      setSuggestions(sug.suggestions || []);
      setStep("insights");
    } finally {
      setBusy(false);
    }
  }

  async function buildFromSuggestion(id: string) {
    setBuilding(true);
    try {
      const spec = await api.post(`/api/datasets/${dataset.dataset_id}/dashboards/build`, { suggestion_id: id });
      setExplore(spec);
      setStep("build");
    } finally {
      setBuilding(false);
    }
  }

  async function buildCustom() {
    if (!customScenario.trim()) return;
    setBuilding(true);
    try {
      const spec = await api.post(`/api/datasets/${dataset!.dataset_id}/dashboards/build`, { custom_scenario: customScenario.trim() });
      setExplore(spec);
      setStep("build");
    } finally {
      setBuilding(false);
    }
  }

  async function regenerateInsights() {
    if (!dataset) return;
    setBusy(true);
    try {
      const doc = await api.post(`/api/datasets/${dataset.dataset_id}/insights`, { force: true });
      setInsights(doc);
    } finally {
      setBusy(false);
    }
  }

  const nav = [
    { key: "upload", label: "1 · Upload" },
    { key: "table", label: "2 · Cleaned Table" },
    { key: "insights", label: "3 · Insights" },
    { key: "suggest", label: "4 · Suggest & Build" },
    { key: "chat", label: "5 · Ask Questions" },
  ];

  return (
    <main className="min-h-screen">
      <header className="bg-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Excel Intelligence Agent</h1>
            <p className="text-slate-400 text-sm">Upload any sheet → refined table → deep insights → AI-built dashboards</p>
          </div>
          <span className={`text-xs px-3 py-1 rounded-full ${busy ? "bg-amber-500/20 text-amber-300" : "bg-green-500/20 text-green-300"}`}>
            {busy ? "Working…" : "Ready"}
          </span>
        </div>
      </header>

      {/* Stepper */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 flex gap-1 overflow-x-auto py-3">
          {nav.map((n) => (
            <button
              key={n.key}
              onClick={() => step !== "chat" && setStep(n.key as Step)}
              className={`text-sm px-3 py-1.5 rounded-lg whitespace-nowrap ${
                step === n.key ? "bg-blue-600 text-white" : "text-slate-500 hover:bg-slate-100"
              }`}
            >
              {n.label}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {step === "upload" && (
          <div className="max-w-2xl mx-auto">
            <UploadZone onUploaded={onUploaded} busy={busy} setBusy={setBusy} />
          </div>
        )}

        {step === "table" && dataset && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-slate-800">Refined Table</h2>
              <a
                href={downloadUrl(dataset.dataset_id)}
                className="text-sm bg-green-600 hover:bg-green-700 text-white font-medium px-4 py-2 rounded-lg"
              >
                ⬇ Download refined .xlsx
              </a>
            </div>
            <DataTable columns={dataset.columns} preview={dataset.preview} quality={dataset.quality} notes={dataset.notes} />
            {busy && <p className="text-sm text-blue-600 animate-pulse">Generating insights…</p>}
          </section>
        )}

        {step === "insights" && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-slate-800">Knowledge Document</h2>
              {!busy && (
                <button onClick={() => setStep("suggest")} className="text-sm bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg">
                  Continue →
                </button>
              )}
            </div>
            <InsightsPanel doc={busy ? null : insights} loading={busy} onRegenerate={regenerateInsights} />
          </section>
        )}

        {step === "suggest" && (
          <section className="space-y-6">
            <h2 className="text-xl font-semibold text-slate-800">Suggested Dashboards</h2>
            <DashboardSuggestions suggestions={suggestions} loading={busy} onBuild={buildFromSuggestion} busyBuilding={building} />

            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-1">Build a custom dashboard</h3>
              <p className="text-sm text-slate-500 mb-3">Describe any scenario and I&apos;ll design a dashboard for it.</p>
              <textarea
                value={customScenario}
                onChange={(e) => setCustomScenario(e.target.value)}
                rows={3}
                placeholder='e.g. "Show sales performance by region over time with a Pareto breakdown of top products"'
                className="w-full border border-slate-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={buildCustom}
                disabled={building || !customScenario.trim()}
                className="mt-3 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50"
              >
                {building ? "Building…" : "Build custom dashboard"}
              </button>
            </div>

            <p className="text-sm text-slate-500">Also try: <button onClick={() => setStep("chat")} className="text-blue-600 underline">Ask questions about your data →</button></p>
          </section>
        )}

        {step === "build" && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-slate-800">{explore.title}</h2>
              <div className="flex gap-2">
                <button onClick={() => setStep("suggest")} className="text-sm bg-slate-200 hover:bg-slate-300 text-slate-700 font-medium px-4 py-2 rounded-lg">
                  Back
                </button>
                <button onClick={() => setStep("chat")} className="text-sm bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg">
                  Ask AI →
                </button>
              </div>
            </div>
            <p className="text-sm text-slate-600">{explore.summary}</p>
            <DashboardRenderer spec={explore} />
          </section>
        )}

        {step === "chat" && (
          <section className="space-y-4">
            <h2 className="text-xl font-semibold text-slate-800">Ask your data anything</h2>
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <ChatPanel datasetId={dataset?.dataset_id} />
            </div>
          </section>
        )}
      </div>
    </main>
  );
}