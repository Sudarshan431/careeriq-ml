import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest

from app.nlp.skill_extractor import extract_skill_names, extract_from_skill_line
from app.nlp.skill_normalizer import normalize_skill, normalize_skill_list


class TestSkillExtraction(unittest.TestCase):
    def test_extracts_known_skills(self):
        skills = extract_skill_names("I built a service with Java, Spring Boot, and PostgreSQL.")
        self.assertIn("Java", skills)
        self.assertIn("Spring Boot", skills)
        self.assertIn("PostgreSQL", skills)

    def test_alias_normalization(self):
        self.assertEqual(normalize_skill("postgres"), "PostgreSQL")
        self.assertEqual(normalize_skill("reactjs"), "React")
        self.assertEqual(normalize_skill("k8s"), "Kubernetes")

    def test_unknown_skill_returns_none(self):
        self.assertIsNone(normalize_skill("underwater basket weaving"))

    def test_no_false_positive_on_unrelated_words(self):
        # "R" and "Go" are ambiguous short tokens; free text shouldn't trigger them.
        skills = extract_skill_names("I will go to the store and get bread.")
        self.assertNotIn("Go", skills)

    def test_skill_line_parsing(self):
        skills = extract_from_skill_line("Skills: Java, Python, postgres, reactjs")
        self.assertIn("Java", skills)
        self.assertIn("Python", skills)
        self.assertIn("PostgreSQL", skills)
        self.assertIn("React", skills)

    def test_normalize_skill_list_dedupes(self):
        result = normalize_skill_list(["Java", "java", "JAVA", "Python"])
        self.assertEqual(result, ["Java", "Python"])

    def test_empty_text(self):
        self.assertEqual(extract_skill_names(""), [])


if __name__ == "__main__":
    unittest.main()
