import React, { useState } from "react";
import PatentIdeaForm from "./PatentIdeaForm";
import PaperSelector from "./PaperSelector";
import PatentReportView from "./PatentReportView";
import PatentHistoryList from "./PatentHistoryList";
import type { PatentAnalysisRequest, PatentFeasibilityReport } from "../../types";
import { analyzePatentFeasibility, getPatentAnalysis } from "../../services/api";

export default function PatentAnalyzerView() {
  const [activeTab, setActiveTab] = useState<"analyze" | "history">("analyze");
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingStep, setLoadingStep] = useState<string>("");
  const [currentReport, setCurrentReport] = useState<PatentFeasibilityReport | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleRunAnalysis = async (request: PatentAnalysisRequest) => {
    setIsLoading(true);
    setErrorMessage(null);
    setLoadingStep("Retrieving candidate technical chunks from selected papers...");

    try {
      setTimeout(() => {
        setLoadingStep("Comparing technical solutions & evaluating prior art with Gemini...");
      }, 1200);

      const report = await analyzePatentFeasibility(request);
      setCurrentReport(report);
      setActiveTab("analyze");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to complete patent feasibility analysis.");
    } finally {
      setIsLoading(false);
      setLoadingStep("");
    }
  };

  const handleSelectSavedAnalysis = async (analysisId: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const report = await getPatentAnalysis(analysisId);
      setCurrentReport(report);
      setActiveTab("analyze");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load saved analysis.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetToNew = () => {
    setCurrentReport(null);
    setErrorMessage(null);
  };

  return (
    <div className="space-y-6">
      {/* Navigation Sub-Tabs */}
      <div className="flex items-center justify-between border-b border-slate-200">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab("analyze")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === "analyze"
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            💡 Patent Potential Analyzer
          </button>
          <button
            onClick={() => {
              setActiveTab("history");
              setCurrentReport(null);
            }}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === "history"
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            📁 Saved Evaluations
          </button>
        </div>

        {activeTab === "analyze" && currentReport && (
          <button
            onClick={handleResetToNew}
            className="text-xs font-medium text-brand-600 hover:text-brand-700"
          >
            + New Evaluation
          </button>
        )}
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-medium text-red-700 flex items-start justify-between">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-red-500 hover:text-red-700 ml-4 font-bold">
            ✕
          </button>
        </div>
      )}

      {/* Main Content Area */}
      {activeTab === "history" ? (
        <PatentHistoryList
          onSelectAnalysis={handleSelectSavedAnalysis}
          onNewAnalysis={() => {
            setActiveTab("analyze");
            setCurrentReport(null);
          }}
        />
      ) : currentReport ? (
        <PatentReportView report={currentReport} onReset={handleResetToNew} />
      ) : (
        <div className="space-y-6">
          {/* Header intro */}
          <div className="rounded-xl border border-brand-100 bg-gradient-to-r from-brand-50/60 to-slate-50 p-6">
            <h2 className="text-xl font-bold text-slate-800">
              AI Patent Feasibility & Prior-Art Analyzer
            </h2>
            <p className="mt-1 text-xs text-slate-600 leading-relaxed max-w-2xl">
              Evaluate your project or invention idea against academic research papers. DocuMind breaks down your idea,
              retrieves grounded technical excerpts from supplied papers, evaluates novelty signals and potential inventive step,
              and generates a structured feasibility report with page citations.
            </p>
          </div>

          {/* Loading Overlay */}
          {isLoading ? (
            <div className="rounded-xl border border-slate-200 bg-white p-12 text-center shadow-sm">
              <svg className="mx-auto h-10 w-10 animate-spin text-brand-600" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <h3 className="mt-4 text-sm font-semibold text-slate-800">
                Evaluating Patent Feasibility with Gemini
              </h3>
              <p className="mt-1.5 text-xs text-slate-500 max-w-md mx-auto">
                {loadingStep || "Comparing technical specifications against paper excerpts..."}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
              <div className="lg:col-span-7">
                <PatentIdeaForm
                  selectedDocIds={selectedDocIds}
                  onSubmit={handleRunAnalysis}
                  isLoading={isLoading}
                />
              </div>
              <div className="lg:col-span-5 space-y-6">
                <PaperSelector
                  selectedDocIds={selectedDocIds}
                  onSelectionChange={setSelectedDocIds}
                  disabled={isLoading}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
