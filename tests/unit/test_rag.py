import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest
import uuid

from app.rag.access import is_document_visible
from app.rag.chunker import chunk_text
from app.rag.similarity import rank_texts_by_similarity


class TestChunker(unittest.TestCase):
    def test_empty_and_whitespace_return_no_chunks(self):
        self.assertEqual(chunk_text(""), [])
        self.assertEqual(chunk_text("   \n\n  "), [])

    def test_malformed_none_like_input_does_not_crash(self):
        self.assertEqual(chunk_text(None), [])  # type: ignore[arg-type]

    def test_short_text_is_single_chunk(self):
        self.assertEqual(chunk_text("A short job description."), ["A short job description."])

    def test_chunking_is_deterministic(self):
        text = ("Sentence number one. " * 80) + "\n\n" + ("Another sentence here. " * 80)
        self.assertEqual(chunk_text(text, max_chars=200), chunk_text(text, max_chars=200))

    def test_chunks_respect_size_budget(self):
        # Strict: the budget is an invariant, with no tolerance. (This test
        # originally allowed +20 chars, and a real bug -- an unconditional
        # tail-merge pushing a chunk to 228 chars -- was what it caught.)
        text = "Word. " * 500
        for max_chars in (100, 200, 300, 800):
            for chunk in chunk_text(text, max_chars=max_chars):
                self.assertLessEqual(len(chunk), max_chars)

    def test_budget_holds_across_varied_paragraph_shapes(self):
        shapes = [
            "Short.\n\n" * 60,
            ("Medium sentence number one. " * 7 + "\n\n") * 20,
            "x" * 1000 + "\n\nTiny.",
            "A" * 90 + "\n\n" + "B" * 90 + "\n\nend",
        ]
        for text in shapes:
            for chunk in chunk_text(text, max_chars=120):
                self.assertLessEqual(len(chunk), 120)

    def test_tiny_tail_merged_when_it_fits_budget(self):
        # 60-char body + tiny tail: merged result (60 + 2 + 5) fits in 100.
        text = ("A" * 60) + "\n\nTiny."
        self.assertEqual(len(chunk_text(text, max_chars=100)), 1)

    def test_tiny_tail_left_separate_when_merging_would_break_budget(self):
        # 98-char chunk + tiny tail cannot merge within 100; must stay separate, not overflow.
        text = ("A" * 98) + "\n\nTiny."
        chunks = chunk_text(text, max_chars=100)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(all(len(c) <= 100 for c in chunks))

    def test_single_oversized_sentence_is_truncated_not_dropped(self):
        chunks = chunk_text("x" * 5000, max_chars=300)
        self.assertGreaterEqual(len(chunks), 1)
        self.assertTrue(all(len(c) <= 300 for c in chunks))


class TestSimilarityRanking(unittest.TestCase):
    CANDIDATES = [
        "Java Spring Boot backend engineer with Kafka and microservices experience",
        "Frontend developer skilled in React, TypeScript, and CSS",
        "DevOps engineer experienced with Kubernetes and Docker",
    ]

    def test_relevant_text_ranks_first(self):
        ranked = rank_texts_by_similarity("Kafka event-driven architecture experience", self.CANDIDATES, top_k=3)
        self.assertEqual(ranked[0][0], 0)

    def test_irrelevant_query_scores_low(self):
        ranked = rank_texts_by_similarity("underwater basket weaving championship", self.CANDIDATES, top_k=3)
        self.assertTrue(all(score < 0.2 for _, score in ranked))

    def test_empty_query_returns_empty(self):
        self.assertEqual(rank_texts_by_similarity("", self.CANDIDATES), [])

    def test_empty_corpus_returns_empty(self):
        self.assertEqual(rank_texts_by_similarity("Kafka", []), [])

    def test_top_k_limits_results(self):
        self.assertEqual(len(rank_texts_by_similarity("engineer", self.CANDIDATES, top_k=2)), 2)

    def test_scores_bounded_zero_to_one(self):
        for _, score in rank_texts_by_similarity("Java Kafka", self.CANDIDATES, top_k=3):
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_duplicate_chunks_do_not_crash_and_score_equally(self):
        dupes = ["Kafka backend engineer", "Kafka backend engineer", "Frontend React developer"]
        ranked = dict(rank_texts_by_similarity("Kafka backend", dupes, top_k=3))
        self.assertAlmostEqual(ranked[0], ranked[1], places=6)


class TestCandidateIsolation(unittest.TestCase):
    """The most security-critical RAG property: a candidate never sees another candidate's private documents."""

    def setUp(self):
        self.candidate_a = uuid.uuid4()
        self.candidate_b = uuid.uuid4()

    def test_public_document_visible_to_any_candidate(self):
        self.assertTrue(is_document_visible(None, self.candidate_a))
        self.assertTrue(is_document_visible(None, self.candidate_b))

    def test_public_document_visible_even_with_no_candidate_profile(self):
        self.assertTrue(is_document_visible(None, None))

    def test_own_private_document_visible(self):
        self.assertTrue(is_document_visible(self.candidate_a, self.candidate_a))

    def test_other_candidates_private_document_hidden(self):
        self.assertFalse(is_document_visible(self.candidate_a, self.candidate_b))
        self.assertFalse(is_document_visible(self.candidate_b, self.candidate_a))

    def test_private_document_hidden_from_requester_without_candidate_profile(self):
        self.assertFalse(is_document_visible(self.candidate_a, None))

    def test_admin_sees_everything(self):
        self.assertTrue(is_document_visible(self.candidate_a, self.candidate_b, requesting_user_is_admin=True))
        self.assertTrue(is_document_visible(self.candidate_a, None, requesting_user_is_admin=True))


class TestContextBuilderRagFallback(unittest.TestCase):
    def test_retrieval_failure_returns_empty_list_not_exception(self):
        # sqlalchemy isn't installed in this sandbox, so importing the real retriever fails --
        # a genuine "retrieval backend unavailable" condition. It must degrade to an empty
        # list rather than raise, preserving the non-RAG assistant as the fallback.
        from app.rag.context_retrieval import retrieve_knowledge

        self.assertEqual(retrieve_knowledge(None, "kafka", uuid.uuid4()), [])

    def test_retriever_runtime_error_also_degrades_to_empty(self):
        # Simulate the backend importing fine but failing at search time.
        import sys
        import types
        from unittest.mock import patch

        class ExplodingRetriever:
            def __init__(self, db):
                pass

            def search(self, *a, **k):
                raise RuntimeError("vector backend down")

        fake_module = types.ModuleType("app.rag.simple_vector_retriever")
        fake_module.SimpleVectorRetriever = ExplodingRetriever
        with patch.dict(sys.modules, {"app.rag.simple_vector_retriever": fake_module}):
            from app.rag.context_retrieval import retrieve_knowledge

            self.assertEqual(retrieve_knowledge(None, "kafka", uuid.uuid4()), [])


if __name__ == "__main__":
    unittest.main()
