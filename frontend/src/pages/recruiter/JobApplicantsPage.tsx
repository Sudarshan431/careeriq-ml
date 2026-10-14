import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, FileCheck } from "lucide-react";
import { jobsApi } from "../../api/jobs";
import { applicationsApi } from "../../api/applications";
import { Card, CardBody } from "../../components/ui/Card";
import { ApplicantRow } from "../../components/recruiter/ApplicantRow";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { getApiErrorMessage } from "../../api/client";
import type { ApplicationResponse } from "../../types/application";

export function RecruiterJobApplicantsPage() {
  const { id } = useParams<{ id: string }>();
  const [jobTitle, setJobTitle] = useState("");
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    Promise.all([jobsApi.get(id), applicationsApi.listForJob(id)])
      .then(([job, apps]) => {
        setJobTitle(job.title);
        setApplications(apps);
      })
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }

  useEffect(load, [id]);

  function handleStatusChange(updated: ApplicationResponse) {
    setApplications((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
  }

  return (
    <div>
      <Link to={`/recruiter/jobs/${id}`} className="mb-4 flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Back to job
      </Link>
      <h1 className="text-2xl font-semibold text-slate-900">Applicants</h1>
      <p className="mt-1 text-sm text-slate-500">
        {jobTitle && `People who have applied to ${jobTitle}.`} Match score is captured at the time each candidate applied.
      </p>

      <div className="mt-6">
        {isLoading ? (
          <LoadingBlock label="Loading applicants…" />
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : applications.length === 0 ? (
          <EmptyState icon={<FileCheck className="h-8 w-8" />} title="No applicants yet." description="Candidates who apply to this job will appear here." />
        ) : (
          <Card>
            <CardBody>
              {applications.map((app) => (
                <ApplicantRow key={app.id} application={app} onStatusChange={handleStatusChange} />
              ))}
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  );
}
