import { formatPercent } from "../../utils/formatters";
import { Badge } from "../ui/Badge";
import type { RankedCandidate } from "../../types/matching";

export function CandidateRankRow({ candidate }: { candidate: RankedCandidate }) {
  const tone = candidate.match_score >= 80 ? "success" : candidate.match_score >= 50 ? "warning" : "danger";
  return (
    <div className="flex flex-col gap-3 border-b border-slate-100 py-4 last:border-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-sm font-semibold text-slate-600">
          {candidate.rank}
        </span>
        <div>
          <p className="font-medium text-slate-900">{candidate.candidate_id || "Candidate"}</p>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {candidate.matched_skills.slice(0, 4).map((s) => (
              <Badge key={s} tone="success">
                {s}
              </Badge>
            ))}
            {candidate.missing_skills.slice(0, 3).map((s) => (
              <Badge key={s} tone="danger">
                {s}
              </Badge>
            ))}
          </div>
        </div>
      </div>
      <Badge tone={tone} className="self-start sm:self-center">
        {formatPercent(candidate.match_score)} match
      </Badge>
    </div>
  );
}
