"use client";

type Props = {
  suggestions: any[];
  loading: boolean;
  onBuild: (suggestionId: string) => void;
  busyBuilding: boolean;
};

export default function DashboardSuggestions({ suggestions, loading, onBuild, busyBuilding }: Props) {
  if (loading) return <p className="text-sm text-blue-600 animate-pulse">Suggesting dashboards…</p>;
  if (!suggestions.length) return null;

  return (
    <div className="grid md:grid-cols-2 gap-3">
      {suggestions.map((s) => (
        <div key={s.id} className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col">
          <h4 className="font-semibold text-slate-800">{s.title}</h4>
          <p className="text-sm text-slate-500 mt-1 flex-1">{s.context}</p>
          <p className="text-xs text-slate-400 mt-2">
            {Array.isArray(s.charts) ? s.charts.join(" · ") : ""}
          </p>
          <button
            onClick={() => onBuild(s.id)}
            disabled={busyBuilding}
            className="mt-3 self-start bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50"
          >
            {busyBuilding ? "Building…" : "Build dashboard"}
          </button>
        </div>
      ))}
    </div>
  );
}