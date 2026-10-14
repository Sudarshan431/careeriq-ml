export interface JobRecommendation {
  job_id: string | null;
  title: string | null;
  score: number;
  reason: string | null;
}
