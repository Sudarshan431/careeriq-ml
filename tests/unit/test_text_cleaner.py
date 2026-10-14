import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest

from app.nlp.text_cleaner import clean_text, extract_email, extract_phone


class TestTextCleaner(unittest.TestCase):
    def test_clean_text_collapses_whitespace(self):
        self.assertEqual(clean_text("Hello    world\n\n\n\nfoo"), "Hello world\n\nfoo")

    def test_clean_text_empty(self):
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")

    def test_extract_email_found(self):
        self.assertEqual(extract_email("Contact: john.doe@example.com today"), "john.doe@example.com")

    def test_extract_email_not_found(self):
        self.assertIsNone(extract_email("no email here"))

    def test_extract_phone_found(self):
        phone = extract_phone("Call me at +91 98765 43210 anytime")
        self.assertIsNotNone(phone)


if __name__ == "__main__":
    unittest.main()
