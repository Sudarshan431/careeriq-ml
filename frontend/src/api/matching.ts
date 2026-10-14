import { client } from "./client";
import type { CandidateInput } from "../types/candidate";
import type { JobInput } from "../types/job";
import type { MatchResponse, RankedCandidate } from "../types/matching";

export const matchingApi = {
  calculate: (candidate: CandidateInput, job: JobInput, useSemantic = true) =>
    client
      .post<MatchResponse>("/api/v1/matching/calculate", { candidate, job, use_semantic: useSemantic })
      .then((r) => r.data),

  rankCandidates: (job: JobInput, candidates: CandidateInput[]) =>
    client
      .post<{ ranked_candidates: RankedCandidate[] }>("/api/v1/matching/rank-candidates", { job, candidates })
      .then((r) => r.data.ranked_candidates),

  rankCandidatesForJob: (jobId: string, candidates: CandidateInput[]) =>
    client
      .post<{ ranked_candidates: RankedCandidate[] }>(`/api/v1/recruiter/jobs/${jobId}/rank-candidates`, candidates)
      .then((r) => r.data.ranked_candidates),
};
