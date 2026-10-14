import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileText } from "lucide-react";
import { applicationsApi } from "../../api/applications";
import { Card, CardBody } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { getApiErrorMessage } from "../../api/client";
import { formatDate, formatPercent } from "../../utils/formatters";
import type { ApplicationResponse, ApplicationStatus } from "../../types/application";

const STATUS_TONE: Record<ApplicationStatus, "success" | "warning" | "danger" | "info" | "neutral"> = {
  APPLIED: "info",
  REVIEWING: "warning",
  SHORTLISTED: "success",
  REJECTED: "danger",
  INTERVIEW: "success",
  HIRED: "success",
};

export function CandidateApplicationsPage() {
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setIsLoading(true);
    setError(null);
    applicationsApi
      .listMine()
      .then(setApplications)
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }

  useEffect(load, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">My Applications</h1>
      <p className="mt-1 text-sm text-slate-500">Jobs you have applied to.</p>

      <div className="mt-6">
        {isLoading ? (
          <LoadingBlock />
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : applications.length === 0 ? (
          <EmptyState
            icon={<FileText className="h-8 w-8" />}
            title="No applications yet."
            description="Browse recommended jobs and apply to see them here."
          />
        ) : (
          <Card>
            <CardBody className="divide-y divide-slate-100 p-0">
              {applications.map((app) => (
                <Link
                  key={app.id}
                  to={`/candidate/jobs/${app.job_id}`}
                  className="flex flex-col gap-2 px-5 py-4 transition-colors hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="font-medium text-slate-900">{app.job_title || "Untitled role"}</p>
                    <p className="text-xs text-slate-500">Applied {formatDate(app.applied_at)}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    {app.match_score !== null && (
                      <span className="text-sm font-medium text-slate-700">{formatPercent(app.match_score)} match</span>
                    )}
                    <Badge tone={STATUS_TONE[app.status]}>{app.status}</Badge>
                  </div>
                </Link>
              ))}
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  );
}
