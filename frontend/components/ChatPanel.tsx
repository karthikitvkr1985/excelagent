"use client";

import { useState } from "react";
import { api } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string; table?: any[] | null; sql?: string };

type Props = {
  datasetId: string | null;
};

export default function ChatPanel({ datasetId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  if (!datasetId) {
    return (
      <p className="text-sm text-slate-400 text-center py-10">
        Upload a file and generate insights to start asking questions.
      </p>
    );
  }

  async function send() {
    const q = input.trim();
    if (!q || busy) return;
    setMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");
    setBusy(true);
    try {
      const res = await api.post(`/api/datasets/${datasetId}/chat`, { question: q });
      setMessages((m) => [...m, { role: "assistant", content: res.answer, table: res.table, sql: res.sql }]);
    } catch (e: any) {
      setMessages((m) => [...m, { role: "assistant", content: "Error: " + (e.message || "Failed") }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col h-[420px]">
      <div className="flex-1 overflow-y-auto space-y-3 p-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] text-sm rounded-xl px-3 py-2 ${
                m.role === "user" ? "bg-blue-600 text-white" : "bg-white border border-slate-200 text-slate-700"
              }`}
            >
              <p>{m.content}</p>
              {m.table && m.table.length > 0 && (
                <table className="mt-2 border border-slate-200 text-xs">
                  <tbody>
                    <tr>
                      {Object.keys(m.table[0]).map((k) => (
                        <th key={k} className="font-medium px-2 py-1 bg-slate-50">{k}</th>
                      ))}
                    </tr>
                    {m.table.slice(0, 6).map((row: any, j: number) => (
                      <tr key={j}>
                        {Object.values(row).map((v: any, k: number) => (
                          <td key={k} className="px-2 py-1 border-t border-slate-100">{String(v)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        ))}
        {busy && <p className="text-xs text-blue-500 animate-pulse">Thinking…</p>}
      </div>
      <div className="flex gap-2 p-3 border-t border-slate-200">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder='Ask anything, e.g. "total sales by region"'
          className="flex-1 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={send}
          disabled={busy}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}