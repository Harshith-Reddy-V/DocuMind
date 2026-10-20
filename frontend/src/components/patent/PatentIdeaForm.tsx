import React, { useState } from "react";
import type { PatentAnalysisRequest } from "../../types";

interface Props {
  selectedDocIds: string[];
  onSubmit: (request: PatentAnalysisRequest) => void;
  isLoading: boolean;
}

export default function PatentIdeaForm({ selectedDocIds, onSubmit, isLoading }: Props) {
  const [title, setTitle] = useState("");
  const [ideaDescription, setIdeaDescription] = useState("");
  const [problemSolved, setProblemSolved] = useState("");
  const [technicalSolution, setTechnicalSolution] = useState("");
  const [differentiationNotes, setDifferentiationNotes] = useState("");
  const [targetIndustry, setTargetIndustry] = useState("");
  const [jurisdiction, setJurisdiction] = useState("United States");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (!title.trim() || title.trim().length < 2) {
      setValidationError("Project title must be at least 2 characters.");
      return;
    }
    if (!problemSolved.trim() || problemSolved.trim().length < 5) {
      setValidationError("Please clearly describe the problem being solved (at least 5 characters).");
      return;
    }
    if (!technicalSolution.trim() || technicalSolution.trim().length < 10) {
      setValidationError("Please describe the proposed technical solution in detail (at least 10 characters).");
      return;
    }
    if (!ideaDescription.trim() || ideaDescription.trim().length < 10) {
      setValidationError("Please provide a project description (at least 10 characters).");
      return;
    }

    onSubmit({
      title: title.trim(),
      idea_description: ideaDescription.trim(),
      problem_solved: problemSolved.trim(),
      technical_solution: technicalSolution.trim(),
      differentiation_notes: differentiationNotes.trim() || undefined,
      target_industry: targetIndustry.trim() || undefined,
      jurisdiction: jurisdiction || "United States",
      document_ids: selectedDocIds,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="border-b border-slate-100 pb-4">
        <h3 className="text-lg font-semibold text-slate-800">Invention / Project Idea Details</h3>
        <p className="mt-1 text-xs text-slate-500">
          Provide technical specifics regarding the problem, mechanism, and differentiators to compare against research papers.
        </p>
      </div>

      {validationError && (
        <div className="rounded-lg bg-red-50 p-3 text-xs font-medium text-red-700 border border-red-200">
          {validationError}
        </div>
      )}

      {/* Project Title */}
      <div>
        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
          Project Title <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Asynchronous Neuromorphic Optical Sensor for Low-Power Edge Vision"
          className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          required
        />
      </div>

      {/* Project Description */}
      <div>
        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
          Idea Overview & Description <span className="text-red-500">*</span>
        </label>
        <textarea
          rows={3}
          value={ideaDescription}
          onChange={(e) => setIdeaDescription(e.target.value)}
          placeholder="Explain the broader context, operational principles, and goals of this invention..."
          className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          required
        />
      </div>

      {/* Problem Being Solved */}
      <div>
        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
          Problem Being Solved <span className="text-red-500">*</span>
        </label>
        <textarea
          rows={2}
          value={problemSolved}
          onChange={(e) => setProblemSolved(e.target.value)}
          placeholder="What technical limitation, inefficiency, or barrier in the prior art does this address?"
          className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          required
        />
      </div>

      {/* Proposed Technical Solution */}
      <div>
        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
          Proposed Technical Solution <span className="text-red-500">*</span>
        </label>
        <textarea
          rows={3}
          value={technicalSolution}
          onChange={(e) => setTechnicalSolution(e.target.value)}
          placeholder="Describe how the system functions: architectures, algorithms, circuits, chemicals, or mechanics..."
          className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          required
        />
      </div>

      {/* Differentiation */}
      <div>
        <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
          What Makes It Different (Differentiators)
        </label>
        <textarea
          rows={2}
          value={differentiationNotes}
          onChange={(e) => setDifferentiationNotes(e.target.value)}
          placeholder="Why isn't this an obvious combination? What non-trivial changes differentiate this from standard practice?"
          className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        />
      </div>

      {/* Industry and Jurisdiction Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
            Target Industry / Domain (Optional)
          </label>
          <input
            type="text"
            value={targetIndustry}
            onChange={(e) => setTargetIndustry(e.target.value)}
            placeholder="e.g. Autonomous Vehicles, Biomedical, Clean Energy"
            className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
            Target Patent Jurisdiction
          </label>
          <select
            value={jurisdiction}
            onChange={(e) => setJurisdiction(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="United States">United States (USPTO - 35 U.S.C.)</option>
            <option value="India">India (Indian Patent Office - Section 3)</option>
            <option value="European Union">European Union (EPO - EPC Art. 52/56)</option>
            <option value="International / PCT">International / PCT Application</option>
          </select>
        </div>
      </div>

      {/* Submit Button */}
      <div className="pt-2">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          {isLoading ? (
            <>
              <svg className="h-4 w-4 animate-spin text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Analyzing Prior Art & Feasibility...</span>
            </>
          ) : (
            <>
              <span>⚡ Analyze Patent Potential</span>
              {selectedDocIds.length > 0 && (
                <span className="rounded-full bg-brand-500 px-2 py-0.5 text-xs text-white">
                  against {selectedDocIds.length} paper{selectedDocIds.length > 1 ? "s" : ""}
                </span>
              )}
            </>
          )}
        </button>
      </div>
    </form>
  );
}
