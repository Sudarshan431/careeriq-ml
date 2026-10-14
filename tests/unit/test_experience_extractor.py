import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest

from app.nlp.experience_extractor import compute_total_years_experience


class TestExperienceExtractor(unittest.TestCase):
    def test_stated_years(self):
        years = compute_total_years_experience("I have 5 years of experience in backend development.")
        self.assertEqual(years, 5.0)

    def test_no_experience_info_returns_none(self):
        self.assertIsNone(compute_total_years_experience("Just a plain resume with no dates.", []))

    def test_zero_experience_not_fabricated(self):
        # Intern with no explicit years stated and no parseable entries -> None, not 0
        self.assertIsNone(compute_total_years_experience("Software Engineer Intern", []))


if __name__ == "__main__":
    unittest.main()
