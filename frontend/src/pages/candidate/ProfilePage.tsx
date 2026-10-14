import { useEffect, useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import { candidatesApi } from "../../api/candidates";
import { ProfileSummary } from "../../components/candidate/ProfileSummary";
import { LoadingBlock } from "../../components/ui/Spinner";
import { ErrorState } from "../../components/ui/ErrorState";
import { getApiErrorMessage } from "../../api/client";
import type { CandidateProfileResponse } from "../../types/candidate";

export function CandidateProfilePage() {
  const { candidateId } = useAuth();
  const [profile, setProfile] = useState<CandidateProfileResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    if (!candidateId) return;
    setIsLoading(true);
    setError(null);
    candidatesApi
      .get(candidateId)
      .then(setProfile)
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }

  useEffect(load, [candidateId]);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Profile</h1>
      <p className="mt-1 text-sm text-slate-500">Your persisted candidate profile.</p>
      <div className="mt-6">
        {isLoading ? <LoadingBlock /> : error ? <ErrorState message={error} onRetry={load} /> : profile ? <ProfileSummary profile={profile} /> : null}
      </div>
    </div>
  );
}
