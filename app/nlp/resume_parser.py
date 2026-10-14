"""
Resume parsing pipeline:

  document bytes -> text extraction -> cleaning -> section detection
  -> entity extraction (skills / education / experience / projects / certs)
  -> structured profile dict

Supports .pdf, .docx, .txt. Falls back gracefully when a resume doesn't
follow a standard section layout (extraction runs on the whole document
instead of failing).
"""
from __future__ import annotations

import io
import re

from app.core.exceptions import CorruptedDocumentError, EmptyDocumentError, UnsupportedFileTypeError
from app.core.logging_config import get_logger
from app.nlp.text_cleaner import clean_text, extract_email, extract_phone
from app.nlp.skill_extractor import extract_skills, extract_from_skill_line
from app.nlp.education_extractor import extract_education
from app.nlp.experience_extractor import extract_experience_entries, compute_total_years_experience
from app.nlp.project_extractor import extract_projects
from app.nlp.certification_extractor import extract_certifications

logger = get_logger(__name__)

_SECTION_ALIASES = {
    "summary": "summary",
    "objective": "summary",
    "professional summary": "summary",
    "career objective": "summary",
    "skills": "skills",
    "technical skills": "skills",
    "core competencies": "skills",
    "key skills": "skills",
    "education": "education",
    "academic background": "education",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment history": "experience",
    "projects": "projects",
    "personal projects": "projects",
    "academic projects": "projects",
    "certifications": "certifications",
    "certificates": "certifications",
    "licenses & certifications": "certifications",
    "achievements": "achievements",
    "accomplishments": "achievements",
    "languages": "languages",
    "interests": "interests",
    "hobbies": "interests",
}

_HEADER_RE = re.compile(
    r"^\s*(" + "|".join(re.escape(k) for k in sorted(_SECTION_ALIASES, key=len, reverse=True)) + r")\s*:?\s*$",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
# Text extraction per file type
# --------------------------------------------------------------------------

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import pdfplumber
    except ImportError as e:
        raise ModuleNotFoundError("pdfplumber is required for PDF parsing") from e

    text_parts = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
    except Exception as e:
        raise CorruptedDocumentError(f"Could not read PDF: {e}") from e

    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        import docx
    except ImportError as e:
        raise ModuleNotFoundError("python-docx is required for DOCX parsing") from e

    try:
        document = docx.Document(io.BytesIO(file_bytes))
    except Exception as e:
        raise CorruptedDocumentError(f"Could not read DOCX: {e}") from e

    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(parts)


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        raw = extract_text_from_pdf(file_bytes)
    elif ext == "docx":
        raw = extract_text_from_docx(file_bytes)
    elif ext == "txt":
        try:
            raw = file_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            raise CorruptedDocumentError(f"Could not decode text file: {e}") from e
    else:
        raise UnsupportedFileTypeError(f"Unsupported file extension: .{ext}")

    if not raw or not raw.strip():
        raise EmptyDocumentError()
    return raw


# --------------------------------------------------------------------------
# Section detection
# --------------------------------------------------------------------------

def detect_sections(text: str) -> dict[str, str]:
    """
    Split resume text into named sections based on header lines. Any text
    before the first recognized header is treated as 'header' (name/contact
    block + optional summary). If NO headers are found at all, the whole
    document is returned under 'full_text' so downstream extractors can
    still run on it (robust fallback for non-standard resumes).
    """
    lines = text.split("\n")
    sections: dict[str, list[str]] = {}
    current = "header"
    sections[current] = []
    found_any_header = False

    for line in lines:
        stripped = line.strip()
        match = _HEADER_RE.match(stripped)
        if match:
            canonical = _SECTION_ALIASES[match.group(1).lower()]
            current = canonical
            sections.setdefault(current, [])
            found_any_header = True
            continue
        sections[current].append(line)

    if not found_any_header:
        return {"full_text": text}

    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


# --------------------------------------------------------------------------
# Top-level orchestration
# --------------------------------------------------------------------------

def parse_resume(file_bytes: bytes, filename: str) -> dict:
    raw_text = extract_text(file_bytes, filename)
    text = clean_text(raw_text)
    sections = detect_sections(text)

    header_text = sections.get("header", "") or sections.get("full_text", "")
    skills_section = sections.get("skills", "")
    education_section = sections.get("education", "") or sections.get("full_text", "")
    experience_section = sections.get("experience", "") or sections.get("full_text", "")
    projects_section = sections.get("projects", "")
    certs_section = sections.get("certifications", "")
    summary_section = sections.get("summary", "")

    # Skills: prefer the dedicated skills section (precise, low false-positive),
    # then fall back to taxonomy phrase-matching across the whole document to
    # also catch skills only mentioned inline in experience/projects.
    explicit_skills = extract_from_skill_line(skills_section) if skills_section else []
    doc_wide_skills = [r["skill"] for r in extract_skills(text)]
    all_skills = list(dict.fromkeys(explicit_skills + doc_wide_skills))

    experience_entries = extract_experience_entries(experience_section)
    for entry in experience_entries:
        entry["technologies"] = [r["skill"] for r in extract_skills(entry.get("raw_block", ""))]
        entry.pop("raw_block", None)

    total_years = compute_total_years_experience(text, experience_entries)

    profile = {
        "name": _guess_name(header_text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "location": None,  # left None rather than guessed; a geocoding/NER step could fill this in later
        "summary": summary_section.strip() or None,
        "skills": all_skills,
        "education": extract_education(education_section),
        "experience": experience_entries,
        "total_years_experience": total_years,
        "projects": extract_projects(projects_section),
        "certifications": extract_certifications(certs_section),
        "sections_detected": list(sections.keys()),
    }
    return profile


def _guess_name(header_text: str) -> str | None:
    """
    Heuristic only: the first non-empty line of the header block that looks
    like a name (2-4 capitalized words, no digits/@/common header words).
    Returns None rather than a wrong guess when uncertain.
    """
    for line in header_text.splitlines()[:5]:
        candidate = line.strip()
        if not candidate or "@" in candidate or any(ch.isdigit() for ch in candidate):
            continue
        words = candidate.split()
        if 1 < len(words) <= 4 and all(w[:1].isupper() for w in words if w[:1].isalpha()):
            return candidate
    return None
