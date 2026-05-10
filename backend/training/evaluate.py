"""
Evaluation Metrics
------------------
BLEU-4, Levenshtein edit distance, and exact-match accuracy.
Used at the end of every training epoch and during final test evaluation.

Metrics match the project proposal (Section 4 — Evaluation):
  • BLEU-4       — standard MT quality metric (token-level n-gram overlap)
  • Levenshtein  — character-level edit distance (normalised 0–1)
  • Exact Match  — fraction of predictions identical to the reference
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def bleu4(references: list[str], hypotheses: list[str]) -> float:
    """
    Corpus-level BLEU-4 score (0–100).
    Each string is tokenised by whitespace (works well for abstracted code).
    """
    try:
        from nltk.translate.bleu_score import corpus_bleu, SmoothingFunction
    except ImportError:
        return 0.0

    smoother = SmoothingFunction().method3
    refs = [[ref.split()] for ref in references]
    hyps = [hyp.split() for hyp in hypotheses]
    score = corpus_bleu(refs, hyps, smoothing_function=smoother)
    return round(score * 100, 2)


def levenshtein_similarity(references: list[str], hypotheses: list[str]) -> float:
    """
    Mean normalised Levenshtein similarity (0–1, higher is better).
    similarity = 1 - edit_distance / max(len(ref), len(hyp))
    """
    try:
        import Levenshtein as lev
    except ImportError:
        return 0.0

    scores = []
    for ref, hyp in zip(references, hypotheses):
        dist    = lev.distance(ref, hyp)
        max_len = max(len(ref), len(hyp), 1)
        scores.append(1.0 - dist / max_len)
    return round(sum(scores) / max(len(scores), 1), 4)


def exact_match(references: list[str], hypotheses: list[str]) -> float:
    """Fraction of predictions that exactly match the reference (0–1)."""
    if not references:
        return 0.0
    hits = sum(r.strip() == h.strip() for r, h in zip(references, hypotheses))
    return round(hits / len(references), 4)


def compute_all(references: list[str], hypotheses: list[str]) -> dict:
    """Return all three metrics in one dict."""
    return {
        "bleu4":        bleu4(references, hypotheses),
        "lev_sim":      levenshtein_similarity(references, hypotheses),
        "exact_match":  exact_match(references, hypotheses),
    }


def print_metrics(metrics: dict, prefix: str = "") -> None:
    tag = f"[{prefix}] " if prefix else ""
    print(
        f"{tag}BLEU-4={metrics['bleu4']:.2f}  "
        f"Lev-Sim={metrics['lev_sim']:.4f}  "
        f"Exact={metrics['exact_match']:.4f}"
    )
