"use client";

type Props = {
  columns: { name: string; dtype: string; role: string }[];
  preview: { columns: string[]; rows: (string | number | null)[][] };
  quality: string;
  notes: string[];
};

const roleBadge: Record<string, string> = {
  measure: "bg-amber-100 text-amber-700",
  date: "bg-green-100 text-green-700",
  dimension: "bg-blue-100 text-blue-700",
};

export default function DataTable({ columns, preview, quality, notes }: Props) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold ${
            quality === "excellent"
              ? "bg-green-100 text-green-700"
              : quality === "good"
              ? "bg-emerald-100 text-emerald-700"
              : "bg-amber-100 text-amber-700"
          }`}
        >
          Quality: {quality}
        </span>
        <span className="text-sm text-slate-500">{columns.length} columns</span>
      </div>

      {notes.length > 0 && (
        <ul className="text-sm text-slate-600 space-y-1 bg-slate-50 border border-slate-200 rounded-lg p-3">
          {notes.map((n, i) => (
            <li key={i}>• {n}</li>
          ))}
        </ul>
      )}

      <div className="flex flex-wrap gap-2">
        {columns.map((c, i) => (
          <span key={i} className="inline-flex items-center gap-2 text-sm bg-white border border-slate-200 rounded-lg px-3 py-1.5">
            <span className="font-medium">{c.name}</span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${roleBadge[c.role] || "bg-slate-100 text-slate-600"}`}>
              {c.role}
            </span>
          </span>
        ))}
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              {preview.columns.map((c, i) => (
                <th key={i} className="px-3 py-2 font-medium whitespace-nowrap">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.rows.map((row, i) => (
              <tr key={i} className="border-t border-slate-100">
                {row.map((cell, j) => (
                  <td key={j} className="px-3 py-2 whitespace-nowrap">
                    {cell === null || cell === undefined ? "—" : String(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-400">Preview of first {preview.rows.length} rows.</p>
    </div>
  );
}