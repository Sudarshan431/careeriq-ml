import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Briefcase, PlusCircle } from "lucide-react";
import { jobsApi } from "../../api/jobs";
import { Card, CardBody } from "../../components/ui/Card";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { getApiErrorMessage } from "../../api/client";
import type { JobListing } from "../../types/job";

export function RecruiterDashboardPage() {
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    jobsApi
      .list()
      .then(setJobs)
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <LoadingBlock label="Loading dashboard…" />;
  if (error) return <ErrorState message={error} />;

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
      <p className="mt-1 text-sm text-slate-500">Your recruiting overview.</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <Card>
          <CardBody className="flex items-center gap-3">
            <Briefcase className="h-5 w-5 text-brand-600" />
            <div>
              <p className="text-2xl font-semibold text-slate-900">{jobs.length}</p>
              <p className="text-xs text-slate-500">Posted jobs</p>
            </div>
          </CardBody>
        </Card>
        <Link to="/recruiter/jobs/create">
          <Card className="transition-shadow hover:shadow-md">
            <CardBody className="flex items-center gap-3">
              <PlusCircle className="h-5 w-5 text-brand-600" />
              <p className="font-medium text-slate-900">Create a new job</p>
            </CardBody>
          </Card>
        </Link>
      </div>
    </div>
  );
}
