import { Link } from "react-router-dom";
import { MapPin, Briefcase } from "lucide-react";
import { Card, CardBody } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { formatPercent } from "../../utils/formatters";
import type { JobListing } from "../../types/job";

export function JobCard({ job, score }: { job: JobListing; score?: number }) {
  const scoreTone = score === undefined ? "neutral" : score >= 80 ? "success" : score >= 50 ? "warning" : "danger";
  return (
    <Link to={`/candidate/jobs/${job.id}`}>
      <Card className="transition-shadow hover:shadow-md">
        <CardBody>
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-semibold text-slate-900">{job.title}</h3>
              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-500">
                {job.company && <span className="flex items-center gap-1"><Briefcase className="h-3.5 w-3.5" />{job.company}</span>}
                {job.location && <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{job.location}</span>}
              </div>
            </div>
            {score !== undefined && (
              <Badge tone={scoreTone} className="shrink-0">
                {formatPercent(score)} match
              </Badge>
            )}
          </div>
          {job.required_skills.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {job.required_skills.slice(0, 6).map((s) => (
                <Badge key={s}>{s}</Badge>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </Link>
  );
}
