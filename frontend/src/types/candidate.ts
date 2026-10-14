export interface EducationEntry {
  degree: string | null;
  field: string | null;
  institution: string | null;
  graduation_year: string | null;
}

export interface ExperienceEntry {
  role: string | null;
  company: string | null;
  duration_text: string | null;
  technologies: string[];
}

export interface ProjectEntry {
  title: string;
  technologies: string[];
  description: string | null;
}

export interface CertificationEntry {
  name: string;
  year: string | null;
}

export interface ResumeProfile {
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  summary: string | null;
  skills: string[];
  education: EducationEntry[];
  experience: ExperienceEntry[];
  total_years_experience: number | null;
  projects: ProjectEntry[];
  certifications: CertificationEntry[];
  sections_detected: string[];
}

export interface CandidateProfileResponse {
  id: string;
  location: string | null;
  summary: string | null;
  total_years_experience: number | null;
  preferences: Record<string, unknown> | null;
  skills: string[];
  education: EducationEntry[];
  experience: ExperienceEntry[];
  projects: ProjectEntry[];
  certifications: CertificationEntry[];
}

export interface CandidateInput {
  candidate_id?: string;
  skills: string[];
  experience_years?: number | null;
  education: Record<string, unknown>[];
  location?: string | null;
  summary?: string | null;
  profile_text?: string | null;
  preferences?: Record<string, unknown> | null;
}
