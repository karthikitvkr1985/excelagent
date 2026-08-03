"use client";

import { useRef, useState } from "react";
import { uploadExcel } from "@/lib/api";

type Props = {
  onUploaded: (data: any) => void;
  busy: boolean;
  setBusy: (b: boolean) => void;
};

export default function UploadZone({ onUploaded, busy, setBusy }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    setError("");
    setBusy(true);
    try {
      const res = await uploadExcel(file);
      onUploaded(res);
    } catch (e: any) {
      setError(e.message || "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className={`rounded-2xl border-2 border-dashed p-12 text-center transition ${
        dragOver ? "border-blue-500 bg-blue-50" : "border-slate-300 bg-white"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFile(e.dataTransfer.files?.[0]);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <div className="text-4xl mb-3">📊</div>
      <h2 className="text-lg font-semibold text-slate-800">
        Drag & drop your Excel file here
      </h2>
      <p className="text-sm text-slate-500 mt-1 mb-5">
        Messy, structured or unstructured — .xlsx, .xls or .csv
      </p>
      <button
        onClick={() => inputRef.current?.click()}
        disabled={busy}
        className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-5 py-2.5 rounded-lg disabled:opacity-50"
      >
        {busy ? "Analyzing…" : "Choose file"}
      </button>
      {busy && <p className="text-sm text-blue-600 mt-4 animate-pulse">Extracting, cleaning and understanding your data…</p>}
      {error && <p className="text-sm text-red-600 mt-4">{error}</p>}
    </div>
  );
}
