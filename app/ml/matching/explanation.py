"""
Generates a human-readable explanation for a match result. Every statement
is derived directly from the matched/missing skill lists and scores passed
in -- nothing is invented.
"""
from __future__ import annotations


def _recommendation_label(match_score: float) -> str:
    if match_score >= 85:
        return "Strong candidate"
    if match_score >= 65:
        return "Good candidate"
    if match_score >= 45:
        return "Potential candidate with gaps"
    return "Not a strong match"


def explain_match(match_result: dict, matched_skills: list[str], missing_skills: list[str], experience_score: float | None = None) -> dict:
    strengths = [f"{skill} matches the job's requirements" for skill in matched_skills[:5]]

    if experience_score is not None:
        if experience_score >= 90:
            experience_analysis = "Candidate meets or exceeds the required experience level."
        elif experience_score >= 50:
            experience_analysis = "Candidate has some, but not all, of the required experience."
        else:
            experience_analysis = "Candidate's experience falls short of the job's requirement."
    else:
        experience_analysis = "Experience data was not available for comparison."

    return {
        "match_score": match_result.get("match_score"),
        "strengths": strengths,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "experience_analysis": experience_analysis,
        "recommendation": _recommendation_label(match_result.get("match_score", 0)),
    }
