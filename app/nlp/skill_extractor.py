"""
Extracts skill mentions from free text using taxonomy-driven phrase
matching (canonical names + aliases), with word-boundary matching to avoid
false positives on short/ambiguous tokens (e.g. "go", "r", "c").
"""
from __future__ import annotations

import re
from functools import lru_cache

from app.nlp.skill_normalizer import _lower_to_canonical, canonical_skill_set
from app.nlp.text_cleaner import normalize_unicode

# Tokens that are technically valid skill names but are also common English
# words / single letters. We require these to be matched more strictly
# (e.g. surrounded by punctuation/skills-list context) to avoid noise.
_AMBIGUOUS_SHORT_TOKENS = {"go", "r", "c", "js"}


def _escape_for_regex(phrase: str) -> str:
    return re.escape(phrase)


@lru_cache(maxsize=1)
def _compiled_patterns() -> list[tuple[re.Pattern, str]]:
    """
    Build one compiled regex per known phrase (alias or canonical), sorted by
    length descending so longer/more-specific phrases (e.g. "Spring Boot")
    match before their substrings (e.g. "Spring").
    """
    patterns = []
    for raw_phrase, canonical in _lower_to_canonical().items():
        if raw_phrase in _AMBIGUOUS_SHORT_TOKENS:
            continue  # handled separately with stricter rules
        escaped = _escape_for_regex(raw_phrase)
        pattern = re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9\+\#])", re.IGNORECASE)
        patterns.append((pattern, canonical))
    patterns.sort(key=lambda p: len(p[0].pattern), reverse=True)
    return patterns


def extract_skills(text: str, min_mentions: int = 1) -> list[dict]:
    """
    Returns a list of {"skill": canonical_name, "mentions": count,
    "evidence": [snippet, ...]} sorted by mention count descending.
    """
    if not text:
        return []
    text = normalize_unicode(text)

    counts: dict[str, int] = {}
    evidence: dict[str, list[str]] = {}

    for pattern, canonical in _compiled_patterns():
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        counts[canonical] = counts.get(canonical, 0) + len(matches)
        if canonical not in evidence:
            m = matches[0]
            start = max(0, m.start() - 25)
            end = min(len(text), m.end() + 25)
            evidence[canonical] = [text[start:end].strip().replace("\n", " ")]

    results = [
        {"skill": skill, "mentions": count, "evidence": evidence.get(skill, [])}
        for skill, count in counts.items()
        if count >= min_mentions
    ]
    results.sort(key=lambda r: (-r["mentions"], r["skill"]))
    return results


def extract_skill_names(text: str) -> list[str]:
    """Convenience wrapper returning just canonical skill names."""
    return [r["skill"] for r in extract_skills(text)]


def extract_from_skill_line(line: str) -> list[str]:
    """
    Parse a comma/pipe/bullet-separated "Skills:" line specifically -- this
    context makes short ambiguous tokens (Go, R, C) safe to match too.
    """
    parts = re.split(r"[,|;/•]", line)
    found = []
    canon_map = _lower_to_canonical()
    for part in parts:
        key = part.strip().lower()
        key = re.sub(r"^(skills?|technical skills?|tech stack)\s*:?\s*", "", key)
        if not key:
            continue
        canonical = canon_map.get(key)
        if canonical and canonical not in found:
            found.append(canonical)
    return found
