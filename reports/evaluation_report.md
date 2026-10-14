# CareerIQ Matching Model Evaluation

Model: `logistic_regression`  
Trained: 2026-08-15T16:59:26.194144+00:00

## Full-dataset metrics

- **accuracy**: 0.95
- **precision**: 0.9453
- **recall**: 0.8482
- **f1**: 0.8941
- **confusion_matrix**: [[665, 11], [34, 190]]
- **roc_auc**: 0.9891

## Latency (rules-based baseline vs hybrid w/ semantic step)

- Baseline matcher: 0.03 ms/call
- Hybrid matcher: 1.64 ms/call

_Note: this environment does not have `sentence-transformers` installed, so the hybrid matcher's semantic component is running on the TF-IDF cosine-similarity fallback, not true sentence embeddings. Latency and quality will differ once the real embedding model is installed._
