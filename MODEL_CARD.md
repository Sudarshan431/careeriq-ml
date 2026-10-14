# Model Card — CareerIQ Matching Models

## 1. Candidate-Job Match Classifier (`models/matching/model.joblib`)

**Purpose**: Given engineered features describing a candidate-job pair (skill
overlap, experience compatibility, cluster similarity, etc.), predict
whether the pair is a "good match" (binary). Intended as one input signal
into ranking/recommendation, not as a standalone hiring decision.

**Input features**: `skill_overlap_ratio`, `experience_compatibility`,
`same_cluster`, `candidate_experience_years`, `job_experience_required`,
`n_candidate_skills`, `n_required_skills`. See `app/ml/features/feature_builder.py`.

**Output**: Binary label (`is_good_match`) + probability score.

**Training data**: Synthetic, deterministically generated
(`scripts/generate_synthetic_data.py`, seed=42). 300 synthetic candidates ×
60 synthetic jobs drawn from 5 realistic skill clusters (Java backend,
Python/ML, frontend, DevOps/cloud, full-stack), 900 candidate-job pairs.
Labels are derived from a weighted combination of skill overlap (60%),
experience compatibility (30%), and cluster match (10%) plus Gaussian label
noise (σ=0.07), thresholded at 0.55. **This is not real hiring outcome
data** — no such labelled dataset was available in this environment, so per
the project's data-strategy requirement (spec §5) we built a
non-trivial synthetic dataset instead of fabricating claims about a
labelled dataset that doesn't exist.

**Evaluation** (held-out test split, see `reports/evaluation_report.md` for
the full run): Logistic Regression was selected over Random Forest (nearly
identical validation F1, simpler/more interpretable model preferred per the
project's stated preference). Test accuracy 0.978, F1 0.952, ROC-AUC 0.993.

**Important limitation on these metrics**: because the labels were
partially derived from `skill_overlap_ratio` itself, a pure
threshold-on-skill-overlap baseline also scores very highly (~0.97 F1) on
this same synthetic data. This is expected — the synthetic label
generator is intentionally aligned with the features so the task is
learnable at all — but it means these numbers demonstrate that the
**pipeline mechanics work end-to-end** (data generation → training →
evaluation → persistence → inference), not that the model has learned
something beyond what the rule-based baseline already captures. On real
labelled outcome data, we would expect the learned model's advantage over
the naive threshold to be larger and would re-evaluate before trusting
these numbers for a production decision.

**Intended use**: One scoring signal inside `hybrid_match` / candidate
ranking, always shown alongside its component scores and an evidence-based
explanation (matched/missing skills) — never as an opaque single number.

**Non-intended use**: Sole/automated hiring decisions; use on populations
or job categories not represented in the synthetic clusters above (its
generalization there is untested); use as a probability of real-world job
success.

**Known biases**: The synthetic data does not include any protected
characteristics (gender, ethnicity, age, disability, etc. — see §42 of the
spec) and the feature set only uses job-relevant signals (skills,
experience, education). However, the synthetic *skill clusters* themselves
reflect a narrow slice of tech roles (backend/ML/frontend/DevOps/full-stack)
and will not generalize to other industries or seniority patterns without
retraining on more representative data.

**Inference latency**: ~0.03 ms/call for the underlying feature-based
scorer on this machine (see `reports/evaluation_report.md`); negligible
relative to network/API overhead.

---

## 2. Semantic Similarity Component (`app/ml/embeddings/embedding_service.py`)

**Purpose**: Produce a "semantic similarity score" between a candidate's
profile text and a job description, to catch matches that skill-keyword
overlap alone would miss (e.g. a candidate describing "built distributed
event-driven services" for a job that asks for "microservices" without
using the word "Kafka").

**Primary backend**: `sentence-transformers/all-MiniLM-L6-v2` (configurable
via `EMBEDDING_MODEL`). **Fallback backend** (used automatically, and the
only one exercised/tested in this development environment, which has no
network access to download the sentence-transformers model): TF-IDF
vectorization + cosine similarity. The active backend is always reported in
API responses (`embedding_backend` field) so downstream consumers know
which one produced a given score.

**Output**: Cosine similarity in [0, 1]. Explicitly labeled "semantic
similarity score" — never presented as a probability of any real-world
outcome.

**Limitation**: The TF-IDF fallback is a lexical (word-overlap) similarity
measure, not a true semantic one — it will miss paraphrases and synonyms
that a real sentence-transformer would catch. This is a real quality
degradation, not just a slower/different way of getting the same answer;
treat `hybrid_match` scores computed under the fallback as lower-confidence
than those computed with the real embedding model.

---

## General fairness statement (applies to all models above)

Per spec §42, this system does not use or infer race, gender, religion,
caste, ethnicity, disability, age, or political affiliation anywhere in the
pipeline. Matching and recommendation are restricted to job-relevant
factors: skills, experience, education, and stated preferences. This is a
design constraint, not a guarantee of fairness in all downstream uses —
teams integrating this service should still audit outcomes for disparate
impact when it's used on real applicant populations.

All match/recommendation scores from this service are decision-support
signals, not verdicts. They should never replace human judgment in hiring.

---

## Model registry (added in the Phase 3 backend upgrade)

`model_versions` (see `app/db/models/model_version.py`) tracks metadata
for persisted artifacts — model name, version, type, a path/reference
(never the binary itself), metrics, and an `is_active` flag — separately
from `MatchingResult`/`Recommendation` rows, which optionally reference a
`model_version_id` so past results stay attributable to the model that
produced them even after a newer model is trained. This table has not been
populated by a live run in this environment (no PostgreSQL available here);
`scripts/train_matching.py` still writes metadata to
`models/matching/metadata.json` on disk exactly as before — wiring that up
to also insert a `model_versions` row is a natural next step once DB access
is available.
