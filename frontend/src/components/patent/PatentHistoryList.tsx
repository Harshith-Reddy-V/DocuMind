import React, { useState, useEffect } from "react";
import type { PatentAnalysisSummaryItem } from "../../types";
import { listPatentAnalyses, deletePatentAnalysis } from "../../services/api";

interface Props {
  onSelectAnalysis: (analysisId: string) => void;
  onNewAnalysis: () => void;
}

export default function PatentHistoryList({ onSelectAnalysis, onNewAnalysis }: Props) {
  const [history, setHistory] = useState<PatentAnalysisSummaryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const items = await listPatentAnalyses();
      setHistory(items);
    } catch (err: any) {
      setError(err.message || "Failed to load saved analyses.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (e: React.MouseEvent, analysisId: string) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this saved patent evaluation?")) {
      return;
    }

    try {
      setDeletingId(analysisId);
      await deletePatentAnalysis(analysisId);
      setHistory((prev) => prev.filter((item) => item.analysis_id !== analysisId));
    } catch (err: any) {
      alert(`Error deleting analysis: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const getBadgeStyle = (assessment: string) => {
    switch (assessment) {
      case "Potentially worth further investigation":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "Significant overlap found in supplied papers":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "Insufficient evidence to assess":
      default:
        return "bg-slate-100 text-slate-700 border-slate-300";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Saved Patent Feasibility Evaluations</h2>
          <p className="mt-1 text-xs text-slate-500">
            Revisit or export previous prior-art comparisons and feasibility reports.
          </p>
        </div>
        <button
          onClick={onNewAnalysis}
          className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-2 text-xs font-semibold text-white shadow-sm hover:bg-brand-700 transition-colors"
        >
          + New Evaluation
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-xs text-red-700 border border-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400">Loading saved evaluations...</div>
      ) : history.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
          <svg className="mx-auto h-10 w-10 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-3 text-sm font-semibold text-slate-700">No saved evaluations</h3>
          <p className="mt-1 text-xs text-slate-500">
            Submit an idea form and run an analysis to save your first patent feasibility report.
          </p>
          <button
            onClick={onNewAnalysis}
            className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-700 transition-colors"
          >
            Start an Evaluation
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {history.map((item) => (
            <div
              key={item.analysis_id}
              onClick={() => onSelectAnalysis(item.analysis_id)}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:border-brand-300 hover:shadow-md cursor-pointer transition-all"
            >
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded border px-2 py-0.5 text-[10px] font-bold ${getBadgeStyle(
                      item.preliminary_assessment
                    )}`}
                  >
                    {item.preliminary_assessment}
                  </span>
                  {item.jurisdiction && (
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600">
                      {item.jurisdiction}
                    </span>
                  )}
                  <span className="text-[11px] text-slate-400">
                    {item.num_papers} paper{item.num_papers !== 1 ? "s" : ""}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-800">{item.title}</h3>
                {item.created_at && (
                  <p className="text-[11px] text-slate-400">
                    {new Date(item.created_at).toLocaleDateString()} at {new Date(item.created_at).toLocaleTimeString()}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2 pt-2 sm:pt-0">
                <button
                  type="button"
                  onClick={() => onSelectAnalysis(item.analysis_id)}
                  className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors"
                >
                  View Report
                </button>
                <button
                  type="button"
                  onClick={(e) => handleDelete(e, item.analysis_id)}
                  disabled={deletingId === item.analysis_id}
                  className="rounded-lg border border-red-200 bg-red-50 p-1.5 text-xs font-semibold text-red-600 hover:bg-red-100 transition-colors disabled:opacity-50"
                  title="Delete evaluation"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
