import { Badge } from "../ui/Badge";
import type { LearningRecommendationItem } from "../../types/learning";

const TONE: Record<string, "danger" | "warning" | "neutral"> = { HIGH: "danger", MEDIUM: "warning", LOW: "neutral" };

export function LearningRecommendationList({ items }: { items: LearningRecommendationItem[] }) {
  if (items.length === 0) return <p className="text-sm text-slate-400">Nothing to learn — you already cover this job's skills.</p>;
  return (
    <ol className="space-y-4">
      {items.map((item) => (
        <li key={item.skill} className="rounded-lg border border-slate-100 p-3">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
              {item.recommended_order}
            </span>
            <p className="text-sm font-medium text-slate-900">{item.skill}</p>
            <Badge tone={TONE[item.priority]}>{item.priority}</Badge>
            <Badge tone="neutral">{item.difficulty}</Badge>
          </div>
          <p className="mt-1.5 text-xs text-slate-500">{item.reason}</p>
          {item.prerequisite_skills.length > 0 && (
            <p className="mt-1 text-xs text-slate-400">Prerequisite: {item.prerequisite_skills.join(", ")}</p>
          )}
          {item.suggested_resource_types.length > 0 && (
            <p className="mt-1 text-xs text-slate-400">Look for: {item.suggested_resource_types.join(", ")}</p>
          )}
        </li>
      ))}
    </ol>
  );
}
