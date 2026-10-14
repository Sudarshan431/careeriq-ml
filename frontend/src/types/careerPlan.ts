export interface LearningPlanStep {
  skill: string;
  priority: string;
  difficulty: string;
  reason: string;
  prerequisite_skills: string[];
  suggested_resource_types: string[];
  recommended_order: number;
  is_completed?: boolean | null;
  practice_suggestion?: string | null;
}

export interface CareerPlanMilestone {
  label: string;
  skills: string[];
  steps: LearningPlanStep[];
}

export interface CareerPlanResponse {
  plan_id: string | null;
  target_role: string;
  target_job_id: string | null;
  strengths: string[];
  job_readiness_percent: number;
  job_readiness_assessment: string | null;
  summary: string | null;
  milestones: CareerPlanMilestone[];
  created_at: string | null;
}
