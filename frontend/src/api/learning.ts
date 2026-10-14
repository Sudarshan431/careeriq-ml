import { client } from "./client";
import type { LearningRecommendationsResponse } from "../types/learning";

export const learningApi = {
  forJob: (candidateId: string, jobId: string) =>
    client
      .get<LearningRecommendationsResponse>(`/api/v1/learning/candidates/${candidateId}/jobs/${jobId}/recommendations`)
      .then((r) => r.data),
};
