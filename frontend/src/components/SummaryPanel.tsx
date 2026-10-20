import { useState } from "react";
import { summarizeDocument } from "../services/api";
import type { SummarizeResponse } from "../types";

interface Props {
  documentId: string;
}

export default function SummaryPanel({ documentId }: Props) {
  const [summary, setSummary] = useState<SummarizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"short" | "detailed">("short");

  async function handleSummarize() {
    setLoading(true);
    setError(null);
    try {
      const result = await summarizeDocument(documentId);
      setSummary(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate summary.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-brand-700">Document Summary</h3>
        <button
          onClick={handleSummarize}
          disabled={loading}
          className="rounded-lg bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-700 hover:bg-brand-100 disabled:opacity-50"
        >
          {loading ? "Generating…" : summary ? "Regenerate" : "Summarize Document"}
        </button>
      </div>

      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}

      {summary && (
        <div className="mt-3">
          <div className="flex gap-2 border-b border-slate-100 pb-2">
            <button
              onClick={() => setTab("short")}
              className={`text-xs font-medium ${tab === "short" ? "text-brand-700" : "text-slate-400"}`}
            >
              Short
            </button>
            <button
              onClick={() => setTab("detailed")}
              className={`text-xs font-medium ${tab === "detailed" ? "text-brand-700" : "text-slate-400"}`}
            >
              Detailed
            </button>
          </div>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-600">
            {tab === "short" ? summary.short_summary : summary.detailed_summary}
          </p>
        </div>
      )}
    </div>
  );
}
