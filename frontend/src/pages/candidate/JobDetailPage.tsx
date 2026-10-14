import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, MapPin, Briefcase, Clock, CheckCircle2, Sparkles } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { candidatesApi } from "../../api/candidates";
import { jobsApi } from "../../api/jobs";
import { matchingApi } from "../../api/matching";
import { applicationsApi } from "../../api/applications";
import { Card, CardBody } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { MatchScoreCard } from "../../components/common/MatchScoreCard";
import { SkillBadgeList } from "../../components/common/SkillBadgeList";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { getApiErrorMessage, getApiErrorCode } from "../../api/client";
import { toCandidateInput, toJobInput } from "../../utils/formatters";
import type { JobListing } from "../../types/job";
import type { MatchResponse } from "../../types/matching";
import type { ApplicationResponse } from "../../types/application";

export function CandidateJobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { candidateId } = useAuth();
  const [job, setJob] = useState<JobListing | null>(null);
  const [match, setMatch] = useState<MatchResponse | null>(null);
  const [application, setApplication] = useState<ApplicationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isApplying, setIsApplying] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);

  useEffect(() => {
    if (!id || !candidateId) return;
    setIsLoading(true);
    setError(null);
    Promise.all([jobsApi.get(id), candidatesApi.get(candidateId), applicationsApi.listMine()])
      .then(async ([jobData, profile, myApplications]) => {
        setJob(jobData);
        const existing = myApplications.find((a) => a.job_id === id);
        if (existing) setApplication(existing);
        const result = await matchingApi.calculate(toCandidateInput(profile), toJobInput(jobData), true);
        setMatch(result);
      })
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [id, candidateId]);

  async function handleApply() {
    if (!id) return;
    setIsApplying(true);
    setApplyError(null);
    try {
      const result = await applicationsApi.apply(id);
      setApplication(result);
    } catch (err) {
      if (getApiErrorCode(err) === "DUPLICATE_APPLICATION") {
        setApplyError("You have already applied to this job.");
      } else {
        setApplyError(getApiErrorMessage(err));
      }
    } finally {
      setIsApplying(false);
    }
  }

  if (isLoading) return <LoadingBlock label="Loading job…" />;
  if (error) return <ErrorState message={error} />;
  if (!job) return null;

  return (
    <div>
      <Link to="/candidate/jobs" className="mb-4 flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700">
        <ArrowLeft className="h-4 w-4" /> Back to jobs
      </Link>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardBody>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h1 className="text-xl font-semibold text-slate-900">{job.title}</h1>
                  <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-500">
                    {job.company && <span className="flex items-center gap-1"><Briefcase className="h-4 w-4" />{job.company}</span>}
                    {job.location && <span className="flex items-center gap-1"><MapPin className="h-4 w-4" />{job.location}</span>}
                    {job.experience_required !== null && <span className="flex items-center gap-1"><Clock className="h-4 w-4" />{job.experience_required}+ yrs</span>}
                    {job.employment_type && <Badge tone="info">{job.employment_type}</Badge>}
                  </div>
                </div>
                <div className="shrink-0 text-right">
                  {application ? (
                    <div className="flex flex-col items-end gap-1">
                      <span className="flex items-center gap-1.5 text-sm font-medium text-green-600">
                        <CheckCircle2 className="h-4 w-4" /> Applied
                      </span>
                      <Badge tone="info">{application.status}</Badge>
                    </div>
                  ) : (
                    <Button onClick={handleApply} isLoading={isApplying}>
                      Apply Now
                    </Button>
                  )}
                  {applyError && <p className="mt-2 max-w-[200px] text-xs text-red-600">{applyError}</p>}
                </div>
              </div>
              <p className="mt-4 whitespace-pre-line text-sm text-slate-700">{job.description}</p>
            </CardBody>
          </Card>

          {match && (
            <Card className="mt-6">
              <CardBody>
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-slate-900">Match Explanation</h2>
                  <Link
                    to={`/candidate/jobs/${id}/intelligence`}
                    className="flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700"
                  >
                    <Sparkles className="h-4 w-4" /> Skill gaps, learning plan &amp; AI assistant
                  </Link>
                </div>
                <p className="mb-4 mt-2 text-sm text-slate-700">{match.explanation.recommendation} — {match.explanation.experience_analysis}</p>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Matched skills</p>
                    <SkillBadgeList skills={match.skill_gap.matched_skills} tone="success" />
                  </div>
                  <div>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Missing skills</p>
                    <SkillBadgeList skills={match.skill_gap.critical_missing_skills} tone="danger" />
                  </div>
                </div>
              </CardBody>
            </Card>
          )}
        </div>

        <div>{match && <MatchScoreCard match={match} />}</div>
      </div>
    </div>
  );
}
