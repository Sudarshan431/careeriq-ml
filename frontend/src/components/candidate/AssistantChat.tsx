import { useState, type FormEvent } from "react";
import { Send, Sparkles } from "lucide-react";
import { Button } from "../ui/Button";
import { assistantApi } from "../../api/assistant";
import { getApiErrorMessage } from "../../api/client";

interface Turn {
  role: "user" | "assistant";
  content: string;
}

export function AssistantChat({ jobId }: { jobId?: string }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    const question = input.trim();
    setTurns((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setIsLoading(true);
    setError(null);
    try {
      const result = await assistantApi.chat({ message: question, job_id: jobId, conversation_id: conversationId });
      setConversationId(result.conversation_id);
      setTurns((prev) => [...prev, { role: "assistant", content: result.answer }]);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900">
        <Sparkles className="h-4 w-4 text-brand-600" /> AI Career Assistant
      </div>
      <div className="mb-3 max-h-80 space-y-3 overflow-y-auto rounded-lg bg-slate-50 p-3">
        {turns.length === 0 && (
          <p className="text-sm text-slate-400">Ask things like "Why am I not matching this job?" or "What should I learn next?"</p>
        )}
        {turns.map((turn, i) => (
          <div key={i} className={turn.role === "user" ? "text-right" : "text-left"}>
            <span
              className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                turn.role === "user" ? "bg-brand-600 text-white" : "bg-white text-slate-700 shadow-sm"
              }`}
            >
              {turn.content}
            </span>
          </div>
        ))}
      </div>
      {error && <p className="mb-2 text-sm text-red-600">{error}</p>}
      <form onSubmit={onSubmit} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your matches, skills, or what to learn…"
          className="flex-1 rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <Button type="submit" isLoading={isLoading} icon={<Send className="h-4 w-4" />} />
      </form>
    </div>
  );
}
