import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, MapPin, Briefcase, Clock, Users, FileCheck } from "lucide-react";
import { jobsApi } from "../../api/jobs";
import { Card, CardBody } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { getApiErrorMessage } from "../../api/client";
import type { JobListing } from "../../types/job";

export function RecruiterJobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [job, setJob] = useState<JobListing | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    jobsApi
      .get(id)
      .then(setJob)
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [id]);

  if (isLoading) return <LoadingBlock label="Loading job…" />;
  if (error) return <ErrorState message={error} />;
  if (!job) return null;

  return (
    <div>
      <Link to="/recruiter/jobs" className="mb-4 flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Back to jobs
      </Link>

      <Card>
        <CardBody>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-xl font-semibold text-slate-900">{job.title}</h1>
              <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-500">
                {job.company && <span className="flex items-center gap-1"><Briefcase className="h-4 w-4" />{job.company}</span>}
                {job.location && <span className="flex items-center gap-1"><MapPin className="h-4 w-4" />{job.location}</span>}
                {job.experience_required !== null && <span className="flex items-center gap-1"><Clock className="h-4 w-4" />{job.experience_required}+ yrs</span>}
              </div>
            </div>
            <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
              <Link to={`/recruiter/jobs/${job.id}/applicants`}>
                <Button variant="secondary" icon={<FileCheck className="h-4 w-4" />}>
                  Applicants
                </Button>
              </Link>
              <Link to={`/recruiter/jobs/${job.id}/candidates`}>
                <Button icon={<Users className="h-4 w-4" />}>Rank candidates</Button>
              </Link>
            </div>
          </div>
          <p className="mt-4 whitespace-pre-line text-sm text-slate-700">{job.description}</p>
          <div className="mt-4">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Required skills</p>
            <div className="flex flex-wrap gap-1.5">
              {job.required_skills.map((s) => (
                <Badge key={s} tone="info">{s}</Badge>
              ))}
            </div>
          </div>
          {job.preferred_skills.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Preferred skills</p>
              <div className="flex flex-wrap gap-1.5">
                {job.preferred_skills.map((s) => (
                  <Badge key={s}>{s}</Badge>
                ))}
              </div>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
