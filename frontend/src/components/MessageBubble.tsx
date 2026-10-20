import type { ChatMessage } from "../types";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm shadow-sm
          ${isUser
            ? "bg-brand-600 text-white rounded-br-sm"
            : message.isError
              ? "bg-red-50 text-red-700 border border-red-200 rounded-bl-sm"
              : "bg-white text-slate-800 border border-slate-200 rounded-bl-sm"}`}
      >
        <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 space-y-2 border-t border-slate-100 pt-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Sources
            </p>
            {message.sources.map((s) => (
              <div key={s.chunk_id} className="rounded-lg bg-slate-50 p-2 text-xs text-slate-600">
                <span className="font-medium text-brand-700">📄 Page {s.page}</span>
                <p className="mt-1 italic">"{s.text}"</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
