import { client } from "./client";
import type { CandidateInput } from "../types/candidate";
import type { JobInput } from "../types/job";
import type { JobRecommendation } from "../types/recommendation";

export const recommendationsApi = {
  getJobs: (candidate: CandidateInput, jobs: JobInput[], topK = 5, strategy: "content" | "semantic" | "hybrid" = "hybrid") =>
    client
      .post<{ recommendations: JobRecommendation[] }>("/api/v1/recommendations/jobs", {
        candidate,
        jobs,
        top_k: topK,
        strategy,
      })
      .then((r) => r.data.recommendations),
};
