import { client } from "./client";
import type { JobRequirements, JobListing } from "../types/job";

export const jobsApi = {
  analyze: (description: string) =>
    client.post<{ job: JobRequirements }>("/api/v1/job/analyze", { description }).then((r) => r.data.job),

  list: (limit = 100) => client.get<{ jobs: JobListing[] }>("/api/v1/jobs", { params: { limit } }).then((r) => r.data.jobs),

  get: (jobId: string) => client.get<JobListing>(`/api/v1/jobs/${jobId}`).then((r) => r.data),

  create: (description: string) =>
    client.post<{ job_id: string; parsed: JobRequirements }>("/api/v1/recruiter/jobs", { description }).then((r) => r.data),
};
