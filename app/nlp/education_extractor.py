"""Extracts education entries (degree, field, institution, year) from resume text."""
from __future__ import annotations

import re

_DEGREE_PATTERNS = [
    (r"\bb\.?\s?tech\b", "Bachelor of Technology"),
    (r"\bm\.?\s?tech\b", "Master of Technology"),
    (r"\bbachelor of engineering\b|\bb\.?\s?e\b", "Bachelor of Engineering"),
    (r"\bmaster of engineering\b|\bm\.?\s?e\b", "Master of Engineering"),
    (r"\bb\.?\s?sc\b|\bbachelor of science\b", "Bachelor of Science"),
    (r"\bm\.?\s?sc\b|\bmaster of science\b", "Master of Science"),
    (r"\bbca\b", "Bachelor of Computer Applications"),
    (r"\bmca\b", "Master of Computer Applications"),
    (r"\bmba\b", "Master of Business Administration"),
    (r"\bphd\b|\bdoctorate\b", "Doctor of Philosophy"),
    (r"\bb\.?\s?a\b|\bbachelor of arts\b", "Bachelor of Arts"),
    (r"\bdiploma\b", "Diploma"),
]

_FIELD_PATTERNS = [
    "computer science", "information technology", "electronics", "electrical engineering",
    "mechanical engineering", "civil engineering", "data science", "artificial intelligence",
    "software engineering", "information systems", "mathematics", "statistics", "business administration",
]

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _find_degree(line: str) -> str | None:
    lower = line.lower()
    for pattern, normalized in _DEGREE_PATTERNS:
        if re.search(pattern, lower):
            return normalized
    return None


def _find_field(line: str) -> str | None:
    lower = line.lower()
    for field in _FIELD_PATTERNS:
        if field in lower:
            return field.title()
    return None


def _find_institution(line: str) -> str | None:
    match = re.search(
        r"\b([A-Z][A-Za-z.&\- ]{2,60}\b(?:University|Institute|College|School|Polytechnic))\b", line
    )
    return match.group(1).strip() if match else None


def extract_education(section_text: str) -> list[dict]:
    """
    Extract education entries from the education section (or full resume text
    as a fallback). Returns a list of dicts; missing fields are None rather
    than guessed.
    """
    if not section_text:
        return []

    entries = []
    # Group by blank-line-separated blocks first, fall back to per-line.
    blocks = [b.strip() for b in re.split(r"\n\s*\n", section_text) if b.strip()]
    if not blocks:
        blocks = [section_text]

    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        degree = field = institution = year = None
        for line in lines:
            degree = degree or _find_degree(line)
            field = field or _find_field(line)
            institution = institution or _find_institution(line)
            year_match = _YEAR_RE.search(line)
            if year_match and not year:
                year = year_match.group(0)

        if degree or institution:
            entries.append(
                {
                    "degree": degree,
                    "field": field,
                    "institution": institution,
                    "graduation_year": year,
                }
            )

    return entries
