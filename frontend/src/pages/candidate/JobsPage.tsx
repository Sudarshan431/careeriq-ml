import { useEffect, useState } from "react";
import { Briefcase } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { candidatesApi } from "../../api/candidates";
import { jobsApi } from "../../api/jobs";
import { recommendationsApi } from "../../api/recommendations";
import { JobCard } from "../../components/candidate/JobCard";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { getApiErrorMessage } from "../../api/client";
import { toCandidateInput, toJobInput } from "../../utils/formatters";
import type { JobListing } from "../../types/job";

export function CandidateJobsPage() {
  const { candidateId } = useAuth();
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [scores, setScores] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!candidateId) return;
    setIsLoading(true);
    setError(null);
    Promise.all([candidatesApi.get(candidateId), jobsApi.list()])
      .then(async ([profile, jobList]) => {
        setJobs(jobList);
        if (jobList.length === 0) return;
        const recs = await recommendationsApi.getJobs(toCandidateInput(profile), jobList.map(toJobInput), jobList.length, "hybrid");
        const map: Record<string, number> = {};
        recs.forEach((r) => {
          if (r.job_id) map[r.job_id] = r.score * 100;
        });
        setScores(map);
      })
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [candidateId]);

  const sorted = [...jobs].sort((a, b) => (scores[b.id] ?? -1) - (scores[a.id] ?? -1));

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Recommended Jobs</h1>
      <p className="mt-1 text-sm text-slate-500">Jobs ranked by match to your profile.</p>
      <div className="mt-6">
        {isLoading ? (
          <LoadingBlock label="Finding matches…" />
        ) : error ? (
          <ErrorState message={error} />
        ) : sorted.length === 0 ? (
          <EmptyState icon={<Briefcase className="h-8 w-8" />} title="No recommended jobs yet." description="Check back once recruiters have posted jobs." />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {sorted.map((job) => (
              <JobCard key={job.id} job={job} score={scores[job.id]} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
