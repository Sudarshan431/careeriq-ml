import { Badge } from "../ui/Badge";
import type { SkillPriorityItem } from "../../types/skillGap";

const TONE: Record<string, "danger" | "warning" | "neutral"> = { HIGH: "danger", MEDIUM: "warning", LOW: "neutral" };

export function SkillPriorityList({ items }: { items: SkillPriorityItem[] }) {
  if (items.length === 0) return <p className="text-sm text-slate-400">No skill gaps — great coverage!</p>;
  return (
    <ul className="space-y-3">
      {items.map((item) => (
        <li key={item.skill} className="flex items-start gap-3">
          <Badge tone={TONE[item.priority]} className="mt-0.5 shrink-0">
            {item.priority}
          </Badge>
          <div>
            <p className="text-sm font-medium text-slate-900">{item.skill}</p>
            <p className="text-xs text-slate-500">{item.reason}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
