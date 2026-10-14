import { Loader2 } from "lucide-react";

export function Spinner({ size = 24 }: { size?: number }) {
  return <Loader2 className="animate-spin text-brand-600" width={size} height={size} />;
}

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-500">
      <Spinner size={28} />
      <p className="text-sm">{label}</p>
    </div>
  );
}
