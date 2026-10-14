export type ApplicationStatus = "APPLIED" | "REVIEWING" | "SHORTLISTED" | "REJECTED" | "INTERVIEW" | "HIRED";

export const APPLICATION_STATUSES: ApplicationStatus[] = [
  "APPLIED",
  "REVIEWING",
  "SHORTLISTED",
  "REJECTED",
  "INTERVIEW",
  "HIRED",
];

export interface ApplicationResponse {
  id: string;
  candidate_id: string;
  job_id: string;
  status: ApplicationStatus;
  match_score: number | null;
  applied_at: string;
  job_title: string | null;
  candidate_email: string | null;
}
