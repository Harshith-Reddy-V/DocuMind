import React from "react";
import type { PatentFeasibilityReport } from "../../types";

interface Props {
  report: PatentFeasibilityReport;
  onReset: () => void;
}

export default function PatentReportView({ report, onReset }: Props) {
  const getAssessmentStyle = (assessment: string) => {
    switch (assessment) {
      case "Potentially worth further investigation":
        return {
          bg: "bg-emerald-50 border-emerald-300 text-emerald-900",
          badge: "bg-emerald-100 text-emerald-800 border-emerald-300",
          iconColor: "text-emerald-600",
          dot: "bg-emerald-500",
        };
      case "Significant overlap found in supplied papers":
        return {
          bg: "bg-amber-50 border-amber-300 text-amber-900",
          badge: "bg-amber-100 text-amber-800 border-amber-300",
          iconColor: "text-amber-600",
          dot: "bg-amber-500",
        };
      case "Insufficient evidence to assess":
      default:
        return {
          bg: "bg-slate-50 border-slate-300 text-slate-800",
          badge: "bg-slate-100 text-slate-700 border-slate-300",
          iconColor: "text-slate-500",
          dot: "bg-slate-400",
        };
    }
  };

  const style = getAssessmentStyle(report.preliminary_assessment);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-8 print:space-y-4">
      {/* Top action bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 print:hidden">
        <button
          onClick={onReset}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition-colors"
        >
          ← New Analysis
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition-colors"
          >
            <svg className="h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            <span>Print / Save PDF</span>
          </button>
        </div>
      </div>

      {/* Prominent Legal Disclaimer Banner */}
      <div className="rounded-xl border border-amber-300 bg-amber-50/80 p-5 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 text-amber-600">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-amber-900">
                Mandatory Legal Disclaimer & Preliminary Scope
              </h4>
              <span className="rounded bg-amber-200/80 px-2 py-0.5 text-[10px] font-semibold text-amber-900">
                AI Preliminary Research Tool
              </span>
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-amber-800">
              {report.disclaimer}
            </p>
            <div className="mt-2.5 flex flex-wrap gap-2 text-[11px] text-amber-700">
              <span className="inline-flex items-center gap-1 font-medium">
                • External patent databases (USPTO, EPO, WIPO): <strong>Not searched</strong>
              </span>
              <span className="inline-flex items-center gap-1 font-medium">
                • Scope of evaluation: <strong>Strictly against {report.paper_ids.length} supplied research paper{report.paper_ids.length !== 1 ? "s" : ""}</strong>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Report Header Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded bg-brand-50 px-2 py-0.5 text-[11px] font-semibold text-brand-700 border border-brand-200">
                Patent Feasibility Evaluation
              </span>
              {report.jurisdiction && (
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                  Jurisdiction: {report.jurisdiction}
                </span>
              )}
              {report.target_industry && (
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                  Domain: {report.target_industry}
                </span>
              )}
            </div>
            <h2 className="mt-2 text-2xl font-bold text-slate-900">{report.title}</h2>
            {report.created_at && (
              <p className="mt-1 text-xs text-slate-400">
                Generated on {new Date(report.created_at).toLocaleDateString()} at {new Date(report.created_at).toLocaleTimeString()}
              </p>
            )}
          </div>
        </div>

        {/* Assessment Banner */}
        <div className={`mt-6 rounded-lg border p-4 ${style.bg}`}>
          <div className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${style.dot}`} />
            <h3 className="text-sm font-bold uppercase tracking-wider">
              Preliminary Assessment:
            </h3>
            <span className={`rounded-md border px-2.5 py-0.5 text-xs font-bold ${style.badge}`}>
              {report.preliminary_assessment}
            </span>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-slate-700">
            {report.preliminary_assessment_explanation}
          </p>
        </div>

        {/* Executive Summary */}
        <div className="mt-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">Executive Summary</h3>
          <p className="mt-1.5 text-sm leading-relaxed text-slate-700">
            {report.executive_summary}
          </p>
        </div>
      </div>

      {/* Idea Technical Decomposition */}
      {report.idea_decomposition && report.idea_decomposition.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
            1. Technical Idea Decomposition
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Breakdown of the proposed invention into discrete technical modules and functional characteristics:
          </p>
          <div className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            {report.idea_decomposition.map((feat, idx) => (
              <div key={idx} className="flex items-start gap-2.5 rounded-lg border border-slate-100 bg-slate-50/70 p-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-100 text-[10px] font-bold text-brand-700">
                  {idx + 1}
                </span>
                <span className="text-xs font-medium text-slate-800 leading-snug">{feat}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Paper-by-Paper Comparative Analysis */}
      {report.paper_comparisons && report.paper_comparisons.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
                2. Paper-by-Paper Comparative Analysis
              </h3>
              <p className="mt-0.5 text-xs text-slate-500">
                Technical mapping against each supplied research document with page citations.
              </p>
            </div>
            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
              {report.paper_comparisons.length} Paper{report.paper_comparisons.length !== 1 ? "s" : ""}
            </span>
          </div>

          <div className="mt-6 space-y-6">
            {report.paper_comparisons.map((comp, idx) => (
              <div key={idx} className="rounded-lg border border-slate-200 bg-slate-50/30 p-5">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/60 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-brand-700">Ref [{idx + 1}]</span>
                    <h4 className="text-sm font-semibold text-slate-900">{comp.paper_title}</h4>
                  </div>
                  {comp.page_references && comp.page_references.length > 0 && (
                    <div className="flex items-center gap-1.5">
                      <span className="text-[11px] text-slate-400">Cited pages:</span>
                      {comp.page_references.map((p, pIdx) => (
                        <span key={pIdx} className="rounded bg-brand-50 border border-brand-200 px-1.5 py-0.2 text-[11px] font-bold text-brand-700">
                          p. {p}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="mt-3">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Document Technical Approach</p>
                  <p className="mt-1 text-xs text-slate-700 leading-relaxed">{comp.relevant_approach}</p>
                </div>

                <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                  {/* Overlapping Features */}
                  <div className="rounded-md border border-amber-200 bg-amber-50/50 p-3">
                    <h5 className="flex items-center gap-1.5 text-xs font-bold text-amber-900">
                      <span>⚠️ Overlapping Features / Prior Art Signals</span>
                    </h5>
                    {comp.overlapping_features && comp.overlapping_features.length > 0 ? (
                      <ul className="mt-2 space-y-1 text-xs text-amber-800 list-disc list-inside">
                        {comp.overlapping_features.map((item, fIdx) => (
                          <li key={fIdx}>{item}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="mt-1.5 text-xs text-amber-700 italic">No direct feature overlap identified.</p>
                    )}
                  </div>

                  {/* Technical Differences */}
                  <div className="rounded-md border border-emerald-200 bg-emerald-50/50 p-3">
                    <h5 className="flex items-center gap-1.5 text-xs font-bold text-emerald-900">
                      <span>✓ Key Technical Differences</span>
                    </h5>
                    {comp.differences && comp.differences.length > 0 ? (
                      <ul className="mt-2 space-y-1 text-xs text-emerald-800 list-disc list-inside">
                        {comp.differences.map((item, dIdx) => (
                          <li key={dIdx}>{item}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="mt-1.5 text-xs text-emerald-700 italic">No significant differences noted from this reference.</p>
                    )}
                  </div>
                </div>

                {/* Strongest Evidence Excerpt */}
                {comp.strongest_evidence && (
                  <div className="mt-3.5 rounded-md border border-slate-200 bg-white p-3">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      Strongest Supporting Excerpt from Reference:
                    </p>
                    <blockquote className="mt-1 border-l-2 border-brand-500 pl-2 text-xs italic text-slate-600">
                      "{comp.strongest_evidence}"
                    </blockquote>
                  </div>
                )}

                {/* Remaining Uncertainties */}
                {comp.remaining_uncertainties && (
                  <p className="mt-2 text-[11px] text-slate-500">
                    <strong className="text-slate-600">Remaining Uncertainties:</strong> {comp.remaining_uncertainties}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Potentially Differentiating Features (Novelty Signals) */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
          3. Potentially Differentiating Technical Features
        </h3>
        <p className="mt-1 text-xs text-slate-500">
          Aspects appearing distinct from the supplied research papers that warrant deeper investigation:
        </p>
        {report.potentially_differentiating_features && report.potentially_differentiating_features.length > 0 ? (
          <div className="mt-4 space-y-2">
            {report.potentially_differentiating_features.map((feat, idx) => (
              <div key={idx} className="flex items-start gap-2.5 rounded-lg border border-emerald-100 bg-emerald-50/60 p-3">
                <span className="text-emerald-600 font-bold">✓</span>
                <span className="text-xs font-medium text-emerald-900 leading-relaxed">{feat}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-4 rounded-lg bg-slate-50 p-4 text-xs text-slate-500 italic">
            No clear differentiating technical features identified based on the provided documents.
          </div>
        )}
      </div>

      {/* Prior-Art Grounded Evidence Findings */}
      {report.prior_art_findings && report.prior_art_findings.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
            4. Grounded Prior-Art Findings & Page Citations
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Directly traceable excerpts from the documents establishing prior-art grounding:
          </p>

          <div className="mt-4 space-y-3">
            {report.prior_art_findings.map((f, idx) => (
              <div key={idx} className="rounded-lg border border-slate-200 bg-slate-50/50 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-slate-900">{f.finding}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${
                        f.is_direct_support
                          ? "bg-blue-100 text-blue-800 border border-blue-200"
                          : "bg-purple-100 text-purple-800 border border-purple-200"
                      }`}
                    >
                      {f.is_direct_support ? "Direct Evidence" : "AI Inference"}
                    </span>
                    <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700 capitalize">
                      {f.confidence} confidence
                    </span>
                  </div>
                </div>

                {f.explanation && (
                  <p className="mt-1.5 text-xs text-slate-600">{f.explanation}</p>
                )}

                <div className="mt-2.5 rounded bg-white p-2.5 border border-slate-200/80">
                  <p className="text-[11px] text-slate-600 italic">
                    "{f.supporting_evidence}"
                  </p>
                  <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-400">
                    <span>Source: <strong className="text-slate-600">{f.source_paper_title}</strong></span>
                    {f.page_number && (
                      <span className="rounded bg-brand-50 border border-brand-200 px-1.5 py-0.2 font-bold text-brand-700">
                        Page {f.page_number}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statutory & Patentability Concerns */}
      {report.patentability_concerns && Object.keys(report.patentability_concerns).length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
            5. Statutory & Patentability Considerations
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Statutory criteria under {report.jurisdiction || "patent law"} (Novelty, Inventive Step, Subject Matter Eligibility):
          </p>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            {Object.entries(report.patentability_concerns).map(([criterion, note], idx) => (
              <div key={idx} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 capitalize">
                  {criterion.replace(/_/g, " ")}
                </h4>
                <p className="mt-2 text-xs text-slate-600 leading-relaxed">{note}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Technical Feasibility Risks & Research Gaps Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Feasibility Risks */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
            6. Technical Feasibility & Implementation Risks
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Engineering hurdles, hardware dependencies, and scalability limits:
          </p>
          <ul className="mt-4 space-y-2 text-xs text-slate-700 list-disc list-inside">
            {report.technical_feasibility_risks && report.technical_feasibility_risks.length > 0 ? (
              report.technical_feasibility_risks.map((risk, idx) => (
                <li key={idx} className="leading-relaxed">{risk}</li>
              ))
            ) : (
              <li className="italic text-slate-400">No specific technical risks identified.</li>
            )}
          </ul>
        </div>

        {/* Research Gaps */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800">
            7. Research Gaps in Prior Art
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Where supplied papers leave off and the idea could establish novel technical effect:
          </p>
          <ul className="mt-4 space-y-2 text-xs text-slate-700 list-disc list-inside">
            {report.research_gaps && report.research_gaps.length > 0 ? (
              report.research_gaps.map((gap, idx) => (
                <li key={idx} className="leading-relaxed">{gap}</li>
              ))
            ) : (
              <li className="italic text-slate-400">No prominent research gaps noted.</li>
            )}
          </ul>
        </div>
      </div>

      {/* Suggested Actionable Next Steps */}
      {report.suggested_next_steps && report.suggested_next_steps.length > 0 && (
        <div className="rounded-xl border border-brand-200 bg-brand-50/40 p-6 shadow-sm">
          <h3 className="text-sm font-bold uppercase tracking-wider text-brand-900">
            8. Recommended Next Steps for the Inventor
          </h3>
          <p className="mt-1 text-xs text-brand-700">
            Actionable measures to strengthen technical disclosure and prepare for formal assessment:
          </p>

          <div className="mt-4 space-y-2.5">
            {report.suggested_next_steps.map((step, idx) => (
              <div key={idx} className="flex items-start gap-3 rounded-lg border border-brand-200 bg-white p-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-600 text-[10px] font-bold text-white">
                  {idx + 1}
                </span>
                <span className="text-xs font-medium text-slate-800 leading-relaxed">{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
