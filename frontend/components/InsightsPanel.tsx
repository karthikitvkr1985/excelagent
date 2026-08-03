"use client";

type Props = {
  doc: any;
  loading: boolean;
  onRegenerate: () => void;
};

export default function InsightsPanel({ doc, loading, onRegenerate }: Props) {
  if (loading) {
    return <p className="text-sm text-blue-600 animate-pulse">Generating knowledge document…</p>;
  }
  if (!doc) return null;

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-3">
        <p className="text-slate-700 leading-relaxed">{doc.summary}</p>
        <button onClick={onRegenerate} className="text-xs text-blue-600 hover:underline whitespace-nowrap">
          Regenerate
        </button>
      </div>

      {doc.relationships?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-slate-800 mb-2">Data Relationships</h4>
          <div className="grid md:grid-cols-2 gap-2">
            {doc.relationships.map((r: any, i: number) => (
              <div key={i} className="bg-white border border-slate-200 rounded-lg p-3 text-sm">
                <span className="font-medium">{r.between}</span>{" "}
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 ml-1">{r.type}</span>
                <p className="text-slate-500 mt-1">{r.meaning}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {doc.insights?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-slate-800 mb-2">Insights</h4>
          <div className="space-y-2">
            {doc.insights.map((ins: any, i: number) => (
              <div key={i} className="bg-white border border-slate-200 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full ${
                      ins.severity === "high"
                        ? "bg-red-100 text-red-700"
                        : ins.severity === "medium"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {ins.severity || "info"}
                  </span>
                  <span className="font-medium text-sm">{ins.title}</span>
                </div>
                <p className="text-slate-500 text-sm mt-1">{ins.detail}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {doc.anomalies?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-slate-800 mb-2">Anomalies</h4>
          <div className="space-y-2">
            {doc.anomalies.map((a: any, i: number) => (
              <div key={i} className="bg-red-50 border border-red-100 rounded-lg p-3 text-sm">
                <span className="font-medium text-red-700">{a.what}</span>
                <p className="text-red-500 mt-0.5">{a.detail}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {doc.recommendations?.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-slate-800 mb-2">Recommendations</h4>
          <ul className="space-y-1.5">
            {doc.recommendations.map((r: string, i: number) => (
              <li key={i} className="text-sm text-slate-600 flex gap-2">
                <span className="text-blue-600">→</span> {r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}