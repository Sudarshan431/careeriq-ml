import { client } from "./client";
import type { JobSkillGapResponse } from "../types/skillGap";

export const skillGapApi = {
  forJob: (candidateId: string, jobId: string) =>
    client.get<JobSkillGapResponse>(`/api/v1/skill-gaps/candidates/${candidateId}/jobs/${jobId}`).then((r) => r.data),
};
