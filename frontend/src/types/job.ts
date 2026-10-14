export interface JobRequirements {
  title: string | null;
  required_skills: string[];
  preferred_skills: string[];
  experience_required: number | null;
  education: string[];
  location: string | null;
  employment_type: string | null;
  responsibilities: string[];
}

export interface JobInput {
  job_id?: string;
  title?: string;
  required_skills: string[];
  preferred_skills: string[];
  experience_required?: number | null;
  education: string[];
  location?: string | null;
  employment_type?: string | null;
  description?: string | null;
}

export interface JobListing {
  id: string;
  title: string;
  description: string;
  company: string | null;
  location: string | null;
  employment_type: string | null;
  experience_required: number | null;
  required_skills: string[];
  preferred_skills: string[];
  created_at: string;
}
