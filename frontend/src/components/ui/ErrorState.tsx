import { AlertTriangle } from "lucide-react";
import { Button } from "./Button";

export function ErrorState({ message, requestId, onRetry }: { message: string; requestId?: string | null; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-red-200 bg-red-50 py-12 text-center">
      <AlertTriangle className="mb-1 h-6 w-6 text-red-500" />
      <p className="text-sm font-medium text-red-700">{message}</p>
      {requestId && <p className="text-xs text-red-400">Request ID: {requestId}</p>}
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-2" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
