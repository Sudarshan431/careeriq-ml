export interface TargetJobSummary {
  job_id: string;
  title: string;
  company: string | null;
  required_skills: string[];
  preferred_skills: string[];
}

export interface SkillPriorityItem {
  skill: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  reason: string;
  related_skills_present: string[];
}

export interface SkillGapAnalysisSummary {
  skill_coverage_percent: number;
  total_required_skills: number;
  total_matched_required_skills: number;
  critical_gap_count: number;
  assessment: string;
}

export interface JobSkillGapResponse {
  target_job: TargetJobSummary;
  match_score: number;
  matched_skills: string[];
  partial_matches: { skill: string; related_skills_present: string[] }[];
  missing_skills: string[];
  skill_priorities: SkillPriorityItem[];
  analysis: SkillGapAnalysisSummary;
}
