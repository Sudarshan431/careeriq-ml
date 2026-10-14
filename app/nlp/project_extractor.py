"""Extracts project entries: title + associated technologies (from a title line like
'AI Career Platform — Java, Spring Boot, React, Python')."""
from __future__ import annotations

import re

from app.nlp.skill_extractor import extract_skill_names

_TITLE_SEP_RE = re.compile(r"\s*[-–—:|]\s*")


def extract_projects(section_text: str) -> list[dict]:
    if not section_text:
        return []

    projects = []
    blocks = [b.strip() for b in re.split(r"\n\s*\n", section_text) if b.strip()]
    if not blocks:
        blocks = [section_text]

    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        title_line = lines[0]
        parts = _TITLE_SEP_RE.split(title_line, maxsplit=1)
        title = parts[0].strip()
        rest = parts[1] if len(parts) > 1 else ""

        description = " ".join(lines[1:]) if len(lines) > 1 else ""
        tech_source = f"{rest} {description}"
        technologies = extract_skill_names(tech_source) or extract_skill_names(title_line)

        if title:
            projects.append(
                {
                    "title": title,
                    "technologies": technologies,
                    "description": description[:500] or None,
                }
            )

    return projects
