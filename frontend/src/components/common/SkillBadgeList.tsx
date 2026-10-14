import { Badge } from "../ui/Badge";

export function SkillBadgeList({ skills, tone }: { skills: string[]; tone: "success" | "warning" | "danger" | "info" }) {
  if (skills.length === 0) return <p className="text-sm text-slate-400">None</p>;
  return (
    <div className="flex flex-wrap gap-2">
      {skills.map((s) => (
        <Badge key={s} tone={tone}>
          {s}
        </Badge>
      ))}
    </div>
  );
}
