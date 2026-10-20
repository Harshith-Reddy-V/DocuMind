import { useState } from "react";
import UploadBox from "./components/UploadBox";
import ChatWindow from "./components/ChatWindow";
import SummaryPanel from "./components/SummaryPanel";
import DocumentCard from "./components/DocumentCard";
import PatentAnalyzerView from "./components/patent/PatentAnalyzerView";
import type { DocumentInfo } from "./types";

export default function App() {
  const [mainTab, setMainTab] = useState<"workspace" | "patent">("workspace");
  const [doc, setDoc] = useState<DocumentInfo | null>(null);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white sticky top-0 z-10">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3.5">
          <div>
            <h1 className="text-xl font-bold text-brand-700">DocuMind</h1>
            <p className="text-xs text-slate-400">Gemini-Powered Academic Assistant & Patent Feasibility Engine</p>
          </div>

          <nav className="flex items-center gap-1.5 rounded-lg bg-slate-100 p-1 border border-slate-200">
            <button
              onClick={() => setMainTab("workspace")}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${
                mainTab === "workspace"
                  ? "bg-white text-slate-800 shadow-sm"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              <span>📄 Document Workspace</span>
            </button>
            <button
              onClick={() => setMainTab("patent")}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-all ${
                mainTab === "patent"
                  ? "bg-white text-brand-700 shadow-sm"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              <span>💡 Patent Feasibility Analyzer</span>
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8">
        {mainTab === "patent" ? (
          <PatentAnalyzerView />
        ) : !doc ? (
          <div className="mt-8">
            <div className="mx-auto mb-8 max-w-xl text-center">
              <h2 className="text-2xl font-semibold text-slate-800">
                Ask grounded questions about your academic documents
              </h2>
              <p className="mt-2 text-sm text-slate-500">
                Upload a research paper, textbook chapter, or lecture notes. DocuMind answers
                strictly from the document — with page references — and tells you honestly
                when the answer isn't there.
              </p>
            </div>
            <UploadBox onUploaded={setDoc} />
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="space-y-4 lg:col-span-1">
              <DocumentCard doc={doc} onReset={() => setDoc(null)} />
              <SummaryPanel documentId={doc.document_id} />
            </div>
            <div className="lg:col-span-2">
              <ChatWindow documentId={doc.document_id} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
