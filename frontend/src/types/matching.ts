import type { CandidateInput } from "./candidate";
import type { JobInput } from "./job";

export interface MatchExplanation {
  match_score: number;
  strengths: string[];
  matched_skills: string[];
  missing_skills: string[];
  experience_analysis: string;
  recommendation: string;
}

export interface SkillGapPartial {
  skill: string;
  related_skills_present: string[];
}

export interface SkillGapResult {
  matched_skills: string[];
  matched_preferred_skills: string[];
  partially_matched_skills: SkillGapPartial[];
  critical_missing_skills: string[];
  optional_missing_skills: string[];
  match_coverage_percent: number;
}

export interface MatchResponse {
  match_score: number;
  skill_score: number;
  semantic_similarity_score: number | null;
  experience_score: number;
  education_score: number;
  location_score: number | null;
  preference_score: number | null;
  embedding_backend: string | null;
  explanation: MatchExplanation;
  skill_gap: SkillGapResult;
}

export interface MatchRequest {
  candidate: CandidateInput;
  job: JobInput;
  use_semantic?: boolean;
}

export interface RankedCandidate {
  rank: number;
  candidate_id: string | null;
  match_score: number;
  semantic_similarity_score: number;
  matched_skills: string[];
  missing_skills: string[];
  experience_score: number;
}
