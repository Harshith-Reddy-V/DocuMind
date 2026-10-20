import type { DocumentInfo } from "../types";

interface Props {
  doc: DocumentInfo;
  onReset: () => void;
}

export default function DocumentCard({ doc, onReset }: Props) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div>
        <p className="text-sm font-medium text-slate-800">{doc.filename}</p>
        <p className="text-xs text-slate-400">
          {doc.num_pages} pages · {doc.num_chunks} chunks · <span className="text-green-600">✓ Processed</span>
        </p>
      </div>
      <button
        onClick={onReset}
        className="text-xs font-medium text-slate-400 hover:text-red-500"
      >
        Remove
      </button>
    </div>
  );
}
