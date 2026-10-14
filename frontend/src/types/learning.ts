export interface LearningRecommendationItem {
  skill: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  reason: string;
  related_skills_present: string[];
  prerequisite_skills: string[];
  difficulty: "FOUNDATIONAL" | "STANDARD" | "FOCUSED";
  recommended_order: number;
  suggested_resource_types: string[];
}

export interface LearningRecommendationsResponse {
  target_job_id: string | null;
  target_job_title: string | null;
  recommendations: LearningRecommendationItem[];
}
