import { client } from "./client";
import type { ApplicationResponse, ApplicationStatus } from "../types/application";

export const applicationsApi = {
  apply: (jobId: string) => client.post<ApplicationResponse>(`/api/v1/jobs/${jobId}/apply`).then((r) => r.data),

  listMine: () =>
    client.get<{ applications: ApplicationResponse[] }>("/api/v1/applications/me").then((r) => r.data.applications),

  listForJob: (jobId: string) =>
    client
      .get<{ applications: ApplicationResponse[] }>(`/api/v1/jobs/${jobId}/applications`)
      .then((r) => r.data.applications),

  updateStatus: (applicationId: string, status: ApplicationStatus) =>
    client
      .patch<ApplicationResponse>(`/api/v1/applications/${applicationId}/status`, { status })
      .then((r) => r.data),
};
