import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Briefcase, PlusCircle } from "lucide-react";
import { jobsApi } from "../../api/jobs";
import { Card, CardBody } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { getApiErrorMessage } from "../../api/client";
import type { JobListing } from "../../types/job";

export function RecruiterJobsPage() {
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

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Jobs</h1>
          <p className="mt-1 text-sm text-slate-500">Jobs you have posted.</p>
        </div>
        <Link to="/recruiter/jobs/create">
          <Button icon={<PlusCircle className="h-4 w-4" />}>New job</Button>
        </Link>
      </div>

      <div className="mt-6">
        {isLoading ? (
          <LoadingBlock />
        ) : error ? (
          <ErrorState message={error} />
        ) : jobs.length === 0 ? (
          <EmptyState icon={<Briefcase className="h-8 w-8" />} title="No jobs posted yet." description="Create your first job to start ranking candidates." />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {jobs.map((job) => (
              <Link key={job.id} to={`/recruiter/jobs/${job.id}`}>
                <Card className="transition-shadow hover:shadow-md">
                  <CardBody>
                    <h3 className="font-semibold text-slate-900">{job.title}</h3>
                    <p className="mt-1 text-sm text-slate-500">{job.location || "Location not specified"}</p>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {job.required_skills.slice(0, 5).map((s) => (
                        <Badge key={s}>{s}</Badge>
                      ))}
                    </div>
                  </CardBody>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
