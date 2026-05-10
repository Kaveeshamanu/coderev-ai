"""
Dataset Download
----------------
Downloads the Microsoft CodeReviewer dataset from HuggingFace and saves
it as a JSONL file under data/raw/.

Dataset: microsoft/codereview
Paper:   "Automating Code Review Activities by Large-Scale Pre-training"
         (Shi et al., 2022 — https://arxiv.org/abs/2203.09095)

Schema of each row (relevant columns):
  old_hunk    — original code fragment (before the review change)
  new_hunk    — revised code fragment (after implementing the review)
  comment     — natural language reviewer comment
  lang        — programming language (we keep only "java")

Both models use the same dataset:
  Contributor mode:  old_hunk → new_hunk
  Reviewer mode:     (old_hunk + comment) → new_hunk
"""

import json
import logging
import sys
from pathlib import Path

# Allow running this file directly from the preprocessing/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessing.config import (
    RAW_DIR, DATASET_NAME, DATASET_SPLIT, JAVA_LANG_TAG, MAX_ROWS
)

log = logging.getLogger(__name__)


def download(force: bool = False) -> Path:
    """
    Download and filter the CodeReviewer dataset.

    Args:
        force: Re-download even if the file already exists.

    Returns:
        Path to the saved JSONL file.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "codereview_java.jsonl"

    if out_path.exists() and not force:
        log.info("Raw dataset already exists at %s — skipping download.", out_path)
        return out_path

    log.info("Loading dataset '%s' (split=%s) from HuggingFace…", DATASET_NAME, DATASET_SPLIT)

    try:
        from datasets import load_dataset
    except ImportError:
        log.error("'datasets' package not installed. Run: pip install datasets")
        raise

    try:
        ds = load_dataset(DATASET_NAME, split=DATASET_SPLIT, trust_remote_code=True)
    except Exception as exc:
        log.error(
            "Failed to load '%s'. Trying alternative dataset name…\n%s",
            DATASET_NAME, exc,
        )
        # Fallback: microsoft/codereview may be under a different slug
        ds = _load_fallback_dataset()

    log.info("Total rows loaded: %d", len(ds))

    # ── Filter for Java ────────────────────────────────────────────────────────
    java_rows = _filter_java(ds)
    log.info("Java rows after filtering: %d", len(java_rows))

    if MAX_ROWS is not None:
        java_rows = java_rows[:MAX_ROWS]
        log.info("Capped to MAX_ROWS=%d", MAX_ROWS)

    # ── Normalise and save ─────────────────────────────────────────────────────
    written = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for row in java_rows:
            record = _normalise_row(row)
            if record is None:
                continue
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    log.info("Saved %d valid Java records → %s", written, out_path)
    return out_path


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _filter_java(ds) -> list:
    """Return only Java rows regardless of which column stores the language tag."""
    java_rows = []
    for row in ds:
        lang = (
            row.get("lang") or
            row.get("language") or
            row.get("file_type") or
            row.get("programming_language") or
            ""
        ).lower()
        if lang == JAVA_LANG_TAG or lang.endswith(".java"):
            java_rows.append(row)

    # If no explicit language column, fall back to heuristic detection
    if not java_rows:
        log.warning(
            "No 'lang' column found or no Java rows matched. "
            "Applying Java keyword heuristic on all rows."
        )
        java_rows = [r for r in ds if _looks_like_java(r.get("old_hunk", ""))]

    return java_rows


def _normalise_row(row: dict) -> dict | None:
    """
    Map dataset-specific column names to our canonical schema:
      old_hunk, new_hunk, comment
    Returns None if any required field is empty.
    """
    old = (
        row.get("old_hunk") or
        row.get("src") or
        row.get("input") or
        row.get("code_before") or
        ""
    ).strip()

    new = (
        row.get("new_hunk") or
        row.get("tgt") or
        row.get("output") or
        row.get("code_after") or
        ""
    ).strip()

    comment = (
        row.get("comment") or
        row.get("review") or
        row.get("nl") or
        row.get("msg") or
        ""
    ).strip()

    if not old or not new:
        return None

    return {"old_hunk": old, "new_hunk": new, "comment": comment}


def _looks_like_java(text: str) -> bool:
    """Heuristic: does this snippet look like Java?"""
    java_indicators = [
        "public ", "private ", "protected ",
        "void ", "int ", "String ", "boolean ",
        "class ", "interface ", "import java",
    ]
    return any(kw in text for kw in java_indicators)


def _load_fallback_dataset():
    """
    Try alternative dataset identifiers if the primary name fails.
    Falls back to code_search_net Java split as a last resort
    (which has methods but no review pairs — comment will be empty).
    """
    from datasets import load_dataset

    alternatives = [
        ("microsoft/CodeReviewer", "train"),
        ("code_review_automation", "train"),
    ]
    for name, split in alternatives:
        try:
            log.info("Trying fallback dataset '%s'…", name)
            return load_dataset(name, split=split, trust_remote_code=True)
        except Exception:
            continue

    # Last resort: code_search_net (no review pairs, but gives Java methods)
    log.warning(
        "All CodeReview datasets unavailable. "
        "Falling back to code_search_net Java split (no review comments)."
    )
    ds = load_dataset("code_search_net", "java", split="train", trust_remote_code=True)

    # Adapt code_search_net schema → our schema
    # code_search_net: whole_func_string, func_code_string, func_documentation_string
    adapted = []
    for row in ds:
        code = row.get("func_code_string") or row.get("whole_func_string") or ""
        doc  = row.get("func_documentation_string") or ""
        if code:
            adapted.append({
                "old_hunk": code,
                "new_hunk": code,   # no revised version — identity target
                "comment":  doc[:200] if doc else "",
                "lang": "java",
            })
    return adapted


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    path = download()
    print(f"Done → {path}")
