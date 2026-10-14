import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest

from app.auth.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.exceptions import TokenExpiredError, InvalidTokenError


class TestPasswordHashing(unittest.TestCase):
    def test_hash_and_verify_roundtrip(self):
        h = hash_password("correct-horse-battery-staple1")
        self.assertTrue(verify_password("correct-horse-battery-staple1", h))

    def test_wrong_password_rejected(self):
        h = hash_password("correct-horse-battery-staple1")
        self.assertFalse(verify_password("wrong-password", h))

    def test_hash_is_not_plaintext(self):
        password = "correct-horse-battery-staple1"
        h = hash_password(password)
        self.assertNotEqual(h, password)
        self.assertNotIn(password, h)

    def test_same_password_different_hashes(self):
        # Salting means two hashes of the same password should differ.
        h1 = hash_password("same-password-123")
        h2 = hash_password("same-password-123")
        self.assertNotEqual(h1, h2)

    def test_malformed_hash_rejected_not_crashed(self):
        self.assertFalse(verify_password("anything", "not-a-real-hash"))


class TestJWT(unittest.TestCase):
    def test_create_and_decode_roundtrip(self):
        token = create_access_token(subject="user-123", role="CANDIDATE")
        claims = decode_access_token(token)
        self.assertEqual(claims["sub"], "user-123")
        self.assertEqual(claims["role"], "CANDIDATE")

    def test_expired_token_rejected(self):
        token = create_access_token(subject="user-123", role="ADMIN", expires_minutes=-1)
        with self.assertRaises(TokenExpiredError):
            decode_access_token(token)

    def test_tampered_token_rejected(self):
        token = create_access_token(subject="user-123", role="RECRUITER")
        tampered = token[:-4] + "abcd"
        with self.assertRaises(InvalidTokenError):
            decode_access_token(tampered)

    def test_no_sensitive_claims(self):
        # Spec: don't place sensitive information inside JWT claims.
        token = create_access_token(subject="user-123", role="CANDIDATE")
        claims = decode_access_token(token)
        self.assertNotIn("password", claims)
        self.assertNotIn("email", claims)


if __name__ == "__main__":
    unittest.main()
