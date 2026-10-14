import { useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import { ResumeUploader } from "../../components/candidate/ResumeUploader";
import { ProfileSummary } from "../../components/candidate/ProfileSummary";
import type { CandidateProfileResponse } from "../../types/candidate";

export function CandidateResumePage() {
  const { candidateId } = useAuth();
  const [profile, setProfile] = useState<CandidateProfileResponse | null>(null);

  if (!candidateId) return null;

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Resume</h1>
      <p className="mt-1 text-sm text-slate-500">Upload a resume to update your profile.</p>
      <div className="mt-6 max-w-xl">
        <ResumeUploader candidateId={candidateId} onSuccess={setProfile} />
      </div>
      {profile && (
        <div className="mt-8">
          <h2 className="mb-4 text-lg font-semibold text-slate-900">Extracted profile</h2>
          <ProfileSummary profile={profile} />
        </div>
      )}
    </div>
  );
}
