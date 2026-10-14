import { client } from "./client";
import type { CandidateInput, CandidateProfileResponse } from "../types/candidate";

export const candidatesApi = {
  me: () => client.get<CandidateProfileResponse>("/api/v1/candidates/me").then((r) => r.data),

  get: (candidateId: string) =>
    client.get<CandidateProfileResponse>(`/api/v1/candidates/${candidateId}`).then((r) => r.data),

  listForRecruiter: () => client.get<{ candidates: CandidateInput[] }>("/api/v1/recruiter/candidates").then((r) => r.data.candidates),

  uploadResume: (candidateId: string, file: File, onProgress?: (pct: number) => void) => {
    const form = new FormData();
    form.append("file", file);
    return client
      .post<CandidateProfileResponse>(`/api/v1/candidates/${candidateId}/resume`, form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
        },
      })
      .then((r) => r.data);
  },

  runWorkflow: (
    candidateId: string,
    payload: { job_description: string; other_job_descriptions?: { title: string; description: string }[]; use_semantic?: boolean }
  ) => client.post(`/api/v1/candidates/${candidateId}/workflow`, payload).then((r) => r.data),
};
