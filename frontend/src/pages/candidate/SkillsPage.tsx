import { useEffect, useState } from "react";
import { Target, Link2 } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { candidatesApi } from "../../api/candidates";
import { jobsApi } from "../../api/jobs";
import { skillsApi } from "../../api/skills";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { SkillBadgeList } from "../../components/common/SkillBadgeList";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { getApiErrorMessage } from "../../api/client";
import type { JobListing } from "../../types/job";
import type { SkillGapResponse } from "../../types/skill";

export function CandidateSkillsPage() {
  const { candidateId } = useAuth();
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [gap, setGap] = useState<SkillGapResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGapLoading, setIsGapLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!candidateId) return;
    jobsApi
      .list()
      .then((jobList) => {
        setJobs(jobList);
        if (jobList.length > 0) setSelectedJobId(jobList[0].id);
      })
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [candidateId]);

  useEffect(() => {
    if (!candidateId || !selectedJobId) return;
    const job = jobs.find((j) => j.id === selectedJobId);
    if (!job) return;
    setIsGapLoading(true);
    Promise.all([candidatesApi.get(candidateId)])
      .then(([profile]) =>
        skillsApi.gap({
          candidate_skills: profile.skills,
          required_skills: job.required_skills,
          preferred_skills: job.preferred_skills,
        })
      )
      .then(setGap)
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsGapLoading(false));
  }, [candidateId, selectedJobId, jobs]);

  if (isLoading) return <LoadingBlock label="Loading…" />;
  if (error) return <ErrorState message={error} />;

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Skill Gap</h1>
      <p className="mt-1 text-sm text-slate-500">See how your skills compare against job requirements.</p>

      {jobs.length === 0 ? (
        <div className="mt-6">
          <EmptyState icon={<Target className="h-8 w-8" />} title="No jobs available yet." description="Skill gap analysis needs a job to compare against." />
        </div>
      ) : (
        <>
          <div className="mt-6 max-w-sm">
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Compare against</label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title}
                </option>
              ))}
            </select>
          </div>

          <div className="mt-6">
            {isGapLoading ? (
              <LoadingBlock />
            ) : gap ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <Card>
                  <CardHeader>
                    <Badge tone="success">Matched</Badge>
                  </CardHeader>
                  <CardBody>
                    <SkillBadgeList skills={gap.matched_skills} tone="success" />
                  </CardBody>
                </Card>
                <Card>
                  <CardHeader>
                    <Badge tone="warning">Partially matched</Badge>
                  </CardHeader>
                  <CardBody>
                    {gap.partially_matched_skills.length === 0 ? (
                      <p className="text-sm text-slate-400">None</p>
                    ) : (
                      <ul className="space-y-2">
                        {gap.partially_matched_skills.map((p) => (
                          <li key={p.skill} className="flex items-center gap-2 text-sm">
                            <Link2 className="h-3.5 w-3.5 text-amber-500" />
                            <span className="font-medium text-slate-800">{p.skill}</span>
                            <span className="text-slate-400">via {p.related_skills_present.join(", ")}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </CardBody>
                </Card>
                <Card>
                  <CardHeader>
                    <Badge tone="danger">Critical missing</Badge>
                  </CardHeader>
                  <CardBody>
                    <SkillBadgeList skills={gap.critical_missing_skills} tone="danger" />
                  </CardBody>
                </Card>
                <Card>
                  <CardHeader>
                    <Badge tone="neutral">Optional missing</Badge>
                  </CardHeader>
                  <CardBody>
                    <SkillBadgeList skills={gap.optional_missing_skills} tone="info" />
                  </CardBody>
                </Card>
              </div>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
