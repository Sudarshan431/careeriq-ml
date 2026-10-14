"""Extracts certification names and, where present, issuer/year."""
from __future__ import annotations

import re

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

_KNOWN_CERT_KEYWORDS = [
    "certified", "certification", "certificate", "aws certified", "azure certified",
    "google certified", "pmp", "scrum master", "csm", "oracle certified", "cka", "ckad",
]


def extract_certifications(section_text: str) -> list[dict]:
    if not section_text:
        return []

    certs = []
    for line in section_text.splitlines():
        line = line.strip()
        if not line:
            continue
        lower = line.lower()
        if any(kw in lower for kw in _KNOWN_CERT_KEYWORDS) or len(section_text.splitlines()) <= 15:
            year_match = _YEAR_RE.search(line)
            name = _YEAR_RE.sub("", line).strip(" -,()")
            if name:
                certs.append({"name": name, "year": year_match.group(0) if year_match else None})

    return certs
