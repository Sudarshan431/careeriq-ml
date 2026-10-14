"""
Extracts work-experience entries and computes an approximate total years of
experience. Precision is intentionally limited (month-level at best) since
resumes rarely give exact dates -- we never claim false precision.
"""
from __future__ import annotations

import re
from datetime import date

_MONTHS = (
    "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
    "january|february|march|april|june|july|august|september|october|november|december"
)

_DATE_RANGE_RE = re.compile(
    rf"(?P<start>(?:{_MONTHS})?\.?\s?\d{{4}}|(?:{_MONTHS})\.?\s?\d{{4}})\s*"
    r"(?:-|–|to)\s*"
    rf"(?P<end>(?:{_MONTHS})?\.?\s?\d{{4}}|present|current|now)",
    re.IGNORECASE,
)

_YEARS_STATED_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?experience", re.IGNORECASE)

_ROLE_TITLES = [
    "software engineer", "software developer", "backend developer", "backend engineer",
    "frontend developer", "frontend engineer", "full stack developer", "full-stack developer",
    "data scientist", "data analyst", "machine learning engineer", "ml engineer",
    "devops engineer", "site reliability engineer", "sre", "product manager",
    "engineering manager", "tech lead", "team lead", "senior software engineer",
    "software engineer intern", "intern", "qa engineer", "test engineer",
]


def _parse_year(token: str) -> int | None:
    match = re.search(r"\d{4}", token)
    return int(match.group(0)) if match else None


def _extract_role(line: str) -> str | None:
    lower = line.lower()
    for title in _ROLE_TITLES:
        if title in lower:
            return title.title()
    return None


def _extract_company(line: str) -> str | None:
    # Heuristic: capitalized multi-word sequence not matching a role title,
    # often following a role and a separator like "at", "|", "-", "@".
    match = re.search(r"(?:at|@)\s+([A-Z][A-Za-z0-9&.,\- ]{2,50})", line)
    if match:
        return match.group(1).strip().rstrip(",.")
    return None


def extract_experience_entries(section_text: str) -> list[dict]:
    if not section_text:
        return []

    entries = []
    blocks = [b.strip() for b in re.split(r"\n\s*\n", section_text) if b.strip()]
    if not blocks:
        blocks = [section_text]

    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue

        role = None
        company = None
        duration_text = None
        for line in lines[:5]:
            role = role or _extract_role(line)
            company = company or _extract_company(line)
            date_match = _DATE_RANGE_RE.search(line)
            if date_match and not duration_text:
                duration_text = date_match.group(0)

        if role or company or duration_text:
            entries.append(
                {
                    "role": role,
                    "company": company,
                    "duration_text": duration_text,
                    "technologies": [],  # filled in by resume_service after skill extraction on this block
                    "raw_block": block[:500],
                }
            )

    return entries


def compute_total_years_experience(text: str, experience_entries: list[dict] | None = None) -> float | None:
    """
    Two strategies, in priority order:
    1. An explicitly stated "X years of experience" phrase (most reliable).
    2. Sum of date ranges found in experience entries (approximate, rounded
       to the nearest 0.5 year; overlapping ranges are not de-duplicated,
       which we document as a known limitation).
    Returns None if neither strategy finds anything -- we do not guess.
    """
    stated = _YEARS_STATED_RE.search(text or "")
    if stated:
        return round(float(stated.group(1)), 1)

    if not experience_entries:
        return None

    total_months = 0
    found_any = False
    current_year = date.today().year
    current_month = date.today().month

    for entry in experience_entries:
        dtext = entry.get("duration_text")
        if not dtext:
            continue
        match = _DATE_RANGE_RE.search(dtext)
        if not match:
            continue
        start_year = _parse_year(match.group("start"))
        end_raw = match.group("end").lower()
        if end_raw in ("present", "current", "now"):
            end_year, end_month = current_year, current_month
        else:
            end_year = _parse_year(match.group("end"))
            end_month = 6  # unknown month within the year -> assume mid-year
        if start_year is None or end_year is None:
            continue
        months = max(0, (end_year - start_year) * 12 + (end_month - 6))
        total_months += months
        found_any = True

    if not found_any:
        return None
    return round(total_months / 12, 1)
