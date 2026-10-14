import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest

from app.core.exceptions import EmptyDocumentError, UnsupportedFileTypeError
from app.nlp.resume_parser import parse_resume, extract_text
from app.ml.matching.skill_gap import analyze_skill_gap


class TestEdgeCases(unittest.TestCase):
    def test_empty_resume_raises(self):
        with self.assertRaises(EmptyDocumentError):
            extract_text(b"   ", "resume.txt")

    def test_unsupported_extension_raises(self):
        with self.assertRaises(UnsupportedFileTypeError):
            extract_text(b"hello", "resume.xyz")

    def test_resume_with_no_skills_section(self):
        text = b"John Smith\njohn@example.com\n\nA person with no listed skills or sections."
        profile = parse_resume(text, "resume.txt")
        self.assertEqual(profile["skills"], [])

    def test_duplicate_skills_deduped(self):
        result = analyze_skill_gap(["Java", "Java", "JAVA"], ["Java"])
        self.assertEqual(result["matched_skills"], ["Java"])

    def test_unknown_skills_ignored_not_crashed(self):
        result = analyze_skill_gap(["Quantum Basket Weaving"], ["Java"])
        self.assertEqual(result["matched_skills"], [])
        self.assertIn("Java", result["critical_missing_skills"])

    def test_extremely_long_text_does_not_crash(self):
        long_text = ("Java Spring Boot PostgreSQL " * 5000).encode("utf-8")
        profile = parse_resume(long_text, "resume.txt")
        self.assertIn("Java", profile["skills"])


if __name__ == "__main__":
    unittest.main()
