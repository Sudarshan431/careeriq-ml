"""Text normalization utilities shared by resume and job parsing."""
from __future__ import annotations

import re
import unicodedata

_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
_BULLET_RE = re.compile(r"^[\u2022\u25cf\u25aa\-\*\u2023\u2043]\s*", re.MULTILINE)
_EMAIL_RE = re.compile(r"[\w\.\-+]+@[\w\-]+\.[\w\.\-]+")
_PHONE_RE = re.compile(r"(\+?\d{1,3}[\s\-.]?)?(\(?\d{2,4}\)?[\s\-.]?){2,4}\d{3,4}")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")


def normalize_unicode(text: str) -> str:
    """Fold unicode variants (curly quotes, ligatures, non-breaking spaces) to ASCII-friendly form."""
    text = unicodedata.normalize("NFKD", text)
    text = text.replace("\u00a0", " ").replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    return text


def clean_text(text: str) -> str:
    """General-purpose cleaning: normalize whitespace/unicode, strip bullet markers."""
    if not text:
        return ""
    text = normalize_unicode(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _BULLET_RE.sub("", text)
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


def extract_email(text: str) -> str | None:
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    for line in text.splitlines()[:40]:
        match = _PHONE_RE.search(line)
        if match:
            digits = re.sub(r"\D", "", match.group(0))
            if 7 <= len(digits) <= 15:
                return match.group(0).strip()
    return None


def strip_urls(text: str) -> str:
    return _URL_RE.sub(" ", text)


def to_lower_alnum(token: str) -> str:
    return re.sub(r"[^a-z0-9\+\#\. ]", "", token.lower()).strip()


def sentences(text: str) -> list[str]:
    """Very lightweight sentence splitter (avoids a hard NLTK/spaCy dependency)."""
    text = clean_text(text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])|\n+", text)
    return [p.strip() for p in parts if p.strip()]
