import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileUp, Briefcase, Target, ArrowRight } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { candidatesApi } from "../../api/candidates";
import { Card, CardBody } from "../../components/ui/Card";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { getApiErrorMessage } from "../../api/client";
import type { CandidateProfileResponse } from "../../types/candidate";

export function CandidateDashboardPage() {
  const { candidateId } = useAuth();
  const [profile, setProfile] = useState<CandidateProfileResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!candidateId) return;
    candidatesApi
      .get(candidateId)
      .then(setProfile)
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [candidateId]);

  if (isLoading) return <LoadingBlock label="Loading dashboard…" />;
  if (error) return <ErrorState message={error} />;

  const hasResume = !!profile && profile.skills.length > 0;

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
      <p className="mt-1 text-sm text-slate-500">Your CareerIQ overview.</p>

      {!hasResume && (
        <Card className="mt-6 border-brand-200 bg-brand-50">
          <CardBody className="flex items-center justify-between">
            <div>
              <p className="font-medium text-brand-900">Upload your resume to get started</p>
              <p className="text-sm text-brand-700">We will extract your skills, experience, and education automatically.</p>
            </div>
            <Link to="/candidate/resume" className="flex items-center gap-1 text-sm font-medium text-brand-700 hover:text-brand-900">
              Upload <ArrowRight className="h-4 w-4" />
            </Link>
          </CardBody>
        </Card>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <Link to="/candidate/profile">
          <Card className="transition-shadow hover:shadow-md">
            <CardBody className="flex items-center gap-3">
              <FileUp className="h-5 w-5 text-brand-600" />
              <div>
                <p className="font-medium text-slate-900">{profile?.skills.length ?? 0} skills</p>
                <p className="text-xs text-slate-500">View profile</p>
              </div>
            </CardBody>
          </Card>
        </Link>
        <Link to="/candidate/jobs">
          <Card className="transition-shadow hover:shadow-md">
            <CardBody className="flex items-center gap-3">
              <Briefcase className="h-5 w-5 text-brand-600" />
              <div>
                <p className="font-medium text-slate-900">Recommended jobs</p>
                <p className="text-xs text-slate-500">Browse matches</p>
              </div>
            </CardBody>
          </Card>
        </Link>
        <Link to="/candidate/skills">
          <Card className="transition-shadow hover:shadow-md">
            <CardBody className="flex items-center gap-3">
              <Target className="h-5 w-5 text-brand-600" />
              <div>
                <p className="font-medium text-slate-900">Skill gap</p>
                <p className="text-xs text-slate-500">See what to learn next</p>
              </div>
            </CardBody>
          </Card>
        </Link>
      </div>
    </div>
  );
}
