"""
Parses a raw job description into structured requirements: title,
required/preferred skills, experience required, education, location,
employment type, responsibilities.
"""
from __future__ import annotations

import re

from app.nlp.text_cleaner import clean_text
from app.nlp.skill_extractor import extract_skills, extract_from_skill_line

_REQUIRED_HEADERS = re.compile(
    r"(required skills|requirements|must have|must-have|minimum qualifications)\s*:?", re.IGNORECASE
)
_PREFERRED_HEADERS = re.compile(
    r"(preferred skills|nice to have|nice-to-have|good to have|bonus)\s*:?", re.IGNORECASE
)
_RESPONSIBILITIES_HEADERS = re.compile(
    r"(responsibilities|what you.ll do|role and responsibilities|key responsibilities)\s*:?", re.IGNORECASE
)
_EXPERIENCE_RE = re.compile(r"(\d+)\s*\+?\s*(?:to\s*\d+\s*)?years?\s+(?:of\s+)?experience", re.IGNORECASE)
_EMPLOYMENT_TYPES = ["full-time", "full time", "part-time", "part time", "contract", "internship", "freelance", "remote"]
_LOCATION_RE = re.compile(r"location\s*:?\s*([A-Za-z ,]+)", re.IGNORECASE)

_DEGREE_KEYWORDS = ["bachelor", "master", "b.tech", "m.tech", "bsc", "msc", "mca", "bca", "phd", "degree"]


def _split_section(text: str, header_re: re.Pattern, stop_res: list[re.Pattern]) -> str:
    match = header_re.search(text)
    if not match:
        return ""
    start = match.end()
    end = len(text)
    for stop_re in stop_res:
        stop_match = stop_re.search(text, start)
        if stop_match and stop_match.start() < end:
            end = stop_match.start()
    return text[start:end].strip()


def _extract_title(text: str) -> str | None:
    for line in text.splitlines()[:5]:
        candidate = line.strip()
        if candidate and len(candidate.split()) <= 8 and not candidate.endswith(":"):
            return candidate
    return None


def _extract_employment_type(text: str) -> str | None:
    lower = text.lower()
    for etype in _EMPLOYMENT_TYPES:
        if etype in lower:
            return etype.title()
    return None


def _extract_location(text: str) -> str | None:
    match = _LOCATION_RE.search(text)
    if match:
        loc = match.group(1).strip().splitlines()[0]
        return loc.strip(" ,.")
    return None


def _extract_education(text: str) -> list[str]:
    lower = text.lower()
    found = [kw for kw in _DEGREE_KEYWORDS if kw in lower and kw != "degree"]
    return sorted(set(k.title() if len(k) > 4 else k.upper() for k in found))


def _extract_responsibilities(text: str) -> list[str]:
    resp_section = _split_section(text, _RESPONSIBILITIES_HEADERS, [_REQUIRED_HEADERS, _PREFERRED_HEADERS])
    if not resp_section:
        return []
    lines = [l.strip(" -\u2022*") for l in resp_section.splitlines() if l.strip()]
    return [l for l in lines if len(l) > 3][:20]


def parse_job_description(raw_text: str) -> dict:
    text = clean_text(raw_text)

    required_section = _split_section(text, _REQUIRED_HEADERS, [_PREFERRED_HEADERS, _RESPONSIBILITIES_HEADERS])
    preferred_section = _split_section(text, _PREFERRED_HEADERS, [_REQUIRED_HEADERS, _RESPONSIBILITIES_HEADERS])

    if required_section:
        required_skills = extract_from_skill_line(required_section) or [
            r["skill"] for r in extract_skills(required_section)
        ]
    else:
        # No explicit "Requirements" header found -- fall back to scanning
        # the whole JD; everything found is treated as required.
        required_skills = [r["skill"] for r in extract_skills(text)]

    preferred_skills = (
        extract_from_skill_line(preferred_section) or [r["skill"] for r in extract_skills(preferred_section)]
        if preferred_section
        else []
    )
    # Don't double-count a skill as both required and preferred.
    preferred_skills = [s for s in preferred_skills if s not in required_skills]

    exp_match = _EXPERIENCE_RE.search(text)
    experience_required = int(exp_match.group(1)) if exp_match else None

    return {
        "title": _extract_title(text),
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "experience_required": experience_required,
        "education": _extract_education(text),
        "location": _extract_location(text),
        "employment_type": _extract_employment_type(text),
        "responsibilities": _extract_responsibilities(text),
    }
