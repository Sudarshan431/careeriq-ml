export interface SkillGapRequest {
  candidate_skills: string[];
  required_skills: string[];
  preferred_skills?: string[];
}

export interface SkillGapPartialMatch {
  skill: string;
  related_skills_present: string[];
}

export interface SkillGapResponse {
  matched_skills: string[];
  matched_preferred_skills: string[];
  partially_matched_skills: SkillGapPartialMatch[];
  critical_missing_skills: string[];
  optional_missing_skills: string[];
  match_coverage_percent: number;
}
