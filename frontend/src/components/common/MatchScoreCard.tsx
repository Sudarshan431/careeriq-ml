import { Card, CardBody } from "../ui/Card";
import { formatPercent } from "../../utils/formatters";
import type { MatchResponse } from "../../types/matching";

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color = value >= 80 ? "bg-green-500" : value >= 50 ? "bg-amber-500" : "bg-red-500";
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium text-slate-900">{formatPercent(value)}</span>
      </div>
      <div className="h-2 w-full rounded-full bg-slate-100">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
      </div>
    </div>
  );
}

export function MatchScoreCard({ match }: { match: MatchResponse }) {
  const overallColor = match.match_score >= 80 ? "text-green-600" : match.match_score >= 50 ? "text-amber-600" : "text-red-600";

  return (
    <Card>
      <CardBody>
        <div className="mb-6 text-center">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Match Score</p>
          <p className={`text-5xl font-bold ${overallColor}`}>{formatPercent(match.match_score)}</p>
        </div>
        <div className="space-y-3">
          <ScoreBar label="Skills" value={match.skill_score} />
          <ScoreBar label="Experience" value={match.experience_score} />
          <ScoreBar label="Education" value={match.education_score} />
          {match.semantic_similarity_score !== null && <ScoreBar label="Semantic" value={match.semantic_similarity_score} />}
          {match.location_score !== null && <ScoreBar label="Location" value={match.location_score} />}
          {match.preference_score !== null && <ScoreBar label="Preference" value={match.preference_score} />}
        </div>
      </CardBody>
    </Card>
  );
}
