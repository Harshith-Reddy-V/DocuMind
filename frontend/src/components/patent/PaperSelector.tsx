import React, { useState, useEffect, useRef } from "react";
import type { DocumentInfo } from "../../types";
import { listDocuments, uploadDocument } from "../../services/api";

interface Props {
  selectedDocIds: string[];
  onSelectionChange: (docIds: string[]) => void;
  disabled?: boolean;
}

export default function PaperSelector({ selectedDocIds, onSelectionChange, disabled }: Props) {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = async () => {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch {
      // Graceful fallback if list cannot be fetched
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleToggleDoc = (docId: string) => {
    if (disabled) return;
    if (selectedDocIds.includes(docId)) {
      onSelectionChange(selectedDocIds.filter((id) => id !== docId));
    } else {
      onSelectionChange([...selectedDocIds, docId]);
    }
  };

  const handleSelectAll = () => {
    if (disabled) return;
    const readyIds = documents.filter((d) => d.status === "ready").map((d) => d.document_id);
    onSelectionChange(readyIds);
  };

  const handleClearAll = () => {
    if (disabled) return;
    onSelectionChange([]);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadError(null);

    const newlyAddedIds: string[] = [];

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (!file.name.toLowerCase().endsWith(".pdf")) {
          setUploadError(`File ${file.name} is not a PDF.`);
          continue;
        }
        const uploadedDoc = await uploadDocument(file);
        newlyAddedIds.push(uploadedDoc.document_id);
      }

      await fetchDocs();
      // Auto-select uploaded documents
      if (newlyAddedIds.length > 0) {
        onSelectionChange(Array.from(new Set([...selectedDocIds, ...newlyAddedIds])));
      }
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload one or more papers.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">Prior-Art Research Papers</h3>
          <p className="mt-1 text-xs text-slate-500">
            Select papers to compare against, or upload related academic PDFs.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleSelectAll}
            disabled={disabled || documents.length === 0}
            className="text-xs font-medium text-brand-600 hover:text-brand-700 disabled:opacity-40"
          >
            Select All
          </button>
          <span className="text-slate-300">|</span>
          <button
            type="button"
            onClick={handleClearAll}
            disabled={disabled || selectedDocIds.length === 0}
            className="text-xs font-medium text-slate-500 hover:text-slate-700 disabled:opacity-40"
          >
            Clear
          </button>
        </div>
      </div>

      {uploadError && (
        <div className="rounded-lg bg-red-50 p-3 text-xs font-medium text-red-700 border border-red-200">
          {uploadError}
        </div>
      )}

      {/* Upload button & drop hint */}
      <div className="flex items-center gap-3">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileUpload}
          className="hidden"
          disabled={disabled || uploading}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || uploading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 hover:border-slate-400 disabled:opacity-50 transition-colors"
        >
          {uploading ? (
            <>
              <svg className="h-3.5 w-3.5 animate-spin text-slate-600" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              <span>Uploading & Processing...</span>
            </>
          ) : (
            <>
              <svg className="h-3.5 w-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Upload Related PDF Paper(s)</span>
            </>
          )}
        </button>
        <span className="text-xs text-slate-400">
          Selected: <strong className="text-slate-700">{selectedDocIds.length}</strong> of {documents.length} paper{documents.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Documents List */}
      <div className="max-h-60 overflow-y-auto divide-y divide-slate-100 rounded-lg border border-slate-200">
        {loadingDocs ? (
          <div className="p-4 text-center text-xs text-slate-400">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-400">
            No research papers uploaded yet. Upload PDFs using the button above to analyze prior art.
          </div>
        ) : (
          documents.map((d) => {
            const isSelected = selectedDocIds.includes(d.document_id);
            const isReady = d.status === "ready";

            return (
              <label
                key={d.document_id}
                className={`flex items-center gap-3 p-3 transition-colors cursor-pointer select-none ${
                  isSelected ? "bg-brand-50/50" : "hover:bg-slate-50"
                } ${!isReady ? "opacity-60 cursor-not-allowed" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => handleToggleDoc(d.document_id)}
                  disabled={disabled || !isReady}
                  className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-xs font-medium text-slate-800" title={d.filename}>
                      {d.filename}
                    </span>
                    {d.used_ocr && (
                      <span className="rounded bg-amber-100 px-1.5 py-0.2 text-[10px] font-semibold text-amber-800">
                        OCR
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400">
                    <span>{d.num_pages} pages</span>
                    <span>•</span>
                    <span>{d.num_chunks} chunks</span>
                    <span>•</span>
                    <span
                      className={`capitalize ${
                        d.status === "ready"
                          ? "text-emerald-600"
                          : d.status === "processing"
                          ? "text-blue-500"
                          : "text-red-500"
                      }`}
                    >
                      {d.status}
                    </span>
                  </div>
                </div>
              </label>
            );
          })
        )}
      </div>
    </div>
  );
}
