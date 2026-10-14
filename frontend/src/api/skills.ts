import { client } from "./client";
import type { SkillGapRequest, SkillGapResponse } from "../types/skill";

export const skillsApi = {
  gap: (payload: SkillGapRequest) => client.post<SkillGapResponse>("/api/v1/skills/gap", payload).then((r) => r.data),
};
