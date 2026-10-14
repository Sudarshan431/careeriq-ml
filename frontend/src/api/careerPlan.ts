import { client } from "./client";
import type { CareerPlanResponse } from "../types/careerPlan";

export const careerPlanApi = {
  generate: (candidateId: string, jobId: string) =>
    client.post<CareerPlanResponse>(`/api/v1/career-plans/candidates/${candidateId}/jobs/${jobId}`).then((r) => r.data),

  list: (candidateId: string) =>
    client.get<{ plans: CareerPlanResponse[] }>(`/api/v1/career-plans/candidates/${candidateId}`).then((r) => r.data.plans),

  get: (planId: string) => client.get<CareerPlanResponse>(`/api/v1/career-plans/${planId}`).then((r) => r.data),
};
