"""
Corpus Builder — Abstraction Pipeline
--------------------------------------
Reads the filtered JSONL dataset, applies the code abstractor to every
old_hunk and new_hunk, then writes two output files:

  data/corpus/abstracted_code.txt   — one abstracted snippet per line
                                      (used to train the BPE tokenizer)
  data/corpus/abstracted_pairs.jsonl — full abstracted records:
                                      {old_abs, new_abs, comment, old_raw, new_raw}

The abstractor (backend/models/abstractor.py) replaces:
  - string literals   →  STRING_N
  - numeric literals  →  NUMBER_N
  - method names      →  METHOD_N
  - variable names    →  VAR_N

Keeping Java keywords and common stdlib types unchanged so the tokenizer
learns their structure naturally.
"""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessing.config import RAW_DIR, CORPUS_DIR
from preprocessing.java_filter import filter_dataset
from models.abstractor import abstract_code, clean_comment

log = logging.getLogger(__name__)


def build(raw_path: Path | None = None, force: bool = False) -> tuple[Path, Path]:
    """
    Run the abstraction pipeline over the raw dataset.

    Args:
        raw_path: Path to the raw JSONL file (defaults to data/raw/codereview_java.jsonl).
        force:    Overwrite existing corpus files.

    Returns:
        (corpus_txt_path, abstracted_pairs_jsonl_path)
    """
    if raw_path is None:
        raw_path = RAW_DIR / "codereview_java.jsonl"

    if not raw_path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {raw_path}. "
            "Run preprocessing/download.py first."
        )

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    corpus_txt   = CORPUS_DIR / "abstracted_code.txt"
    pairs_jsonl  = CORPUS_DIR / "abstracted_pairs.jsonl"

    if corpus_txt.exists() and pairs_jsonl.exists() and not force:
        log.info("Corpus already built at %s — skipping.", CORPUS_DIR)
        return corpus_txt, pairs_jsonl

    # ── Load raw records ───────────────────────────────────────────────────────
    log.info("Loading raw records from %s…", raw_path)
    records = []
    with open(raw_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    log.info("Loaded %d raw records.", len(records))

    # ── Filter ────────────────────────────────────────────────────────────────
    valid_records = filter_dataset(records)
    log.info("Valid records after filtering: %d", len(valid_records))

    # ── Abstractify + write ───────────────────────────────────────────────────
    skipped = 0
    processed = 0

    with (
        open(corpus_txt,  "w", encoding="utf-8") as f_txt,
        open(pairs_jsonl, "w", encoding="utf-8") as f_pairs,
    ):
        for rec in valid_records:
            try:
                old_abs, _ = abstract_code(rec["old_hunk"])
                new_abs, _ = abstract_code(rec["new_hunk"])
                comment     = clean_comment(rec.get("comment", ""))

                # Write each abstracted snippet as a training line for the tokenizer
                # (both old and new go into the same corpus so the tokenizer sees all patterns)
                f_txt.write(old_abs.replace("\n", " ") + "\n")
                f_txt.write(new_abs.replace("\n", " ") + "\n")

                # Write the full abstracted pair for dataset building
                f_pairs.write(json.dumps({
                    "old_abs":  old_abs,
                    "new_abs":  new_abs,
                    "comment":  comment,
                    "old_raw":  rec["old_hunk"],
                    "new_raw":  rec["new_hunk"],
                }, ensure_ascii=False) + "\n")

                processed += 1
            except Exception as e:
                log.debug("Skipping record due to abstraction error: %s", e)
                skipped += 1

    log.info(
        "Corpus built: %d pairs processed, %d skipped.",
        processed, skipped,
    )
    log.info("  Tokenizer corpus → %s (%d lines)", corpus_txt, processed * 2)
    log.info("  Abstracted pairs → %s", pairs_jsonl)

    return corpus_txt, pairs_jsonl


def iter_corpus_lines(corpus_txt: Path, batch_size: int = 1000):
    """
    Yield lines from the corpus text file in batches.
    Used by the tokenizer trainer.
    """
    batch: list[str] = []
    with open(corpus_txt, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                batch.append(line)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
    if batch:
        yield batch


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    txt, pairs = build()
    print(f"Done:\n  corpus  → {txt}\n  pairs   → {pairs}")
