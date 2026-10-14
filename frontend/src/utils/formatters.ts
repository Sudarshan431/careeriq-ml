export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${Math.round(value)}%`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function initials(name: string | null | undefined): string {
  if (!name) return "?";
  return name
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function toCandidateInput(profile: import("../types/candidate").CandidateProfileResponse): import("../types/candidate").CandidateInput {
  return {
    candidate_id: profile.id,
    skills: profile.skills,
    experience_years: profile.total_years_experience,
    education: profile.education as unknown as Record<string, unknown>[],
    location: profile.location,
    summary: profile.summary,
    profile_text: profile.summary || profile.skills.join(" "),
    preferences: profile.preferences,
  };
}

export function toJobInput(listing: import("../types/job").JobListing): import("../types/job").JobInput {
  return {
    job_id: listing.id,
    title: listing.title,
    required_skills: listing.required_skills,
    preferred_skills: listing.preferred_skills,
    experience_required: listing.experience_required,
    education: [],
    location: listing.location,
    employment_type: listing.employment_type,
    description: listing.description,
  };
}
