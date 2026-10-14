import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Users } from "lucide-react";
import { jobsApi } from "../../api/jobs";
import { candidatesApi } from "../../api/candidates";
import { matchingApi } from "../../api/matching";
import { Card, CardBody } from "../../components/ui/Card";
import { CandidateRankRow } from "../../components/recruiter/CandidateRankRow";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { getApiErrorMessage } from "../../api/client";
import type { RankedCandidate } from "../../types/matching";

export function RecruiterJobCandidatesPage() {
  const { id } = useParams<{ id: string }>();
  const [jobTitle, setJobTitle] = useState("");
  const [ranked, setRanked] = useState<RankedCandidate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    Promise.all([jobsApi.get(id), candidatesApi.listForRecruiter()])
      .then(async ([job, candidates]) => {
        setJobTitle(job.title);
        if (candidates.length === 0) {
          setRanked([]);
          return;
        }
        const result = await matchingApi.rankCandidatesForJob(id, candidates);
        setRanked(result);
      })
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [id]);

  return (
    <div>
      <Link to={`/recruiter/jobs/${id}`} className="mb-4 flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Back to job
      </Link>
      <h1 className="text-2xl font-semibold text-slate-900">Ranked Candidates</h1>
      <p className="mt-1 text-sm text-slate-500">{jobTitle && `For ${jobTitle}`}</p>

      <div className="mt-6">
        {isLoading ? (
          <LoadingBlock label="Ranking candidates…" />
        ) : error ? (
          <ErrorState message={error} />
        ) : ranked.length === 0 ? (
          <EmptyState icon={<Users className="h-8 w-8" />} title="No candidates to rank yet." description="Candidates will appear here once they have uploaded a resume." />
        ) : (
          <Card>
            <CardBody>
              {ranked.map((c) => (
                <CandidateRankRow key={c.candidate_id ?? c.rank} candidate={c} />
              ))}
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  );
}
