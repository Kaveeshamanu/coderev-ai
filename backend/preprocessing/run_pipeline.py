"""
Preprocessing Pipeline — CLI Orchestrator
------------------------------------------
Runs all preprocessing steps end-to-end in the correct order:

  Step 1 — Download   microsoft/codereview from HuggingFace (Java split)
  Step 2 — Filter     validate Java methods, remove noise
  Step 3 — Abstract   replace identifiers/literals with VAR_N / METHOD_N tokens
  Step 4 — Tokenizer  train BPE tokenizer on the abstracted corpus
  Step 5 — Splits     create tokenised train / val / test .jsonl files

Usage:
  # From the backend/ directory:
  python preprocessing/run_pipeline.py

  # Skip already-completed steps (default):
  python preprocessing/run_pipeline.py

  # Force re-run of all steps:
  python preprocessing/run_pipeline.py --force

  # Run only specific steps:
  python preprocessing/run_pipeline.py --steps download abstract

  # Limit dataset size for a quick smoke test:
  python preprocessing/run_pipeline.py --max-rows 5000

Output layout:
  backend/data/
  ├── raw/
  │   └── codereview_java.jsonl          ← step 1
  ├── corpus/
  │   ├── abstracted_code.txt            ← step 3 (tokenizer training corpus)
  │   └── abstracted_pairs.jsonl         ← step 3 (per-pair abstracted records)
  ├── tokenizer/
  │   ├── tokenizer.json                 ← step 4
  │   ├── vocab.json                     ← step 4
  │   └── tokenizer_config.json          ← step 4
  └── splits/
      ├── train.jsonl                    ← step 5
      ├── val.jsonl                      ← step 5
      ├── test.jsonl                     ← step 5
      └── stats.json                     ← step 5
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Ensure backend/ is on the path so we can import preprocessing.* and models.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

log = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="CodeRev AI — preprocessing pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        choices=["download", "abstract", "tokenizer", "splits", "all"],
        default=["all"],
        help="Which steps to run (default: all).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run steps even if output files already exist.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Cap the number of raw rows used (useful for quick smoke tests).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING"],
        help="Logging verbosity.",
    )
    return parser.parse_args()


def _should_run(step: str, requested: list[str]) -> bool:
    return "all" in requested or step in requested


def run(force: bool = False, max_rows: int | None = None, steps: list[str] | None = None):
    if steps is None:
        steps = ["all"]

    # ── Step 1: Download ──────────────────────────────────────────────────────
    if _should_run("download", steps):
        _section("Step 1 — Download dataset")
        from preprocessing import config as cfg
        if max_rows is not None:
            cfg.MAX_ROWS = max_rows

        from preprocessing.download import download
        t = time.time()
        raw_path = download(force=force)
        log.info("Download complete in %.1fs → %s", time.time() - t, raw_path)

    # ── Step 2+3: Filter + Abstract (corpus builder handles both) ─────────────
    if _should_run("abstract", steps):
        _section("Step 2+3 — Filter & Abstract")
        from preprocessing.build_corpus import build
        t = time.time()
        corpus_txt, pairs_jsonl = build(force=force)
        log.info(
            "Corpus built in %.1fs\n  txt   → %s\n  pairs → %s",
            time.time() - t, corpus_txt, pairs_jsonl,
        )

    # ── Step 4: Train tokenizer ───────────────────────────────────────────────
    if _should_run("tokenizer", steps):
        _section("Step 4 — Train BPE tokenizer")
        from preprocessing.train_tokenizer import train
        t = time.time()
        tok_dir = train(force=force)
        log.info("Tokenizer trained in %.1fs → %s", time.time() - t, tok_dir)

    # ── Step 5: Build splits ──────────────────────────────────────────────────
    if _should_run("splits", steps):
        _section("Step 5 — Build train/val/test splits")
        from preprocessing.build_splits import build as build_splits
        t = time.time()
        split_paths = build_splits(force=force)
        log.info("Splits built in %.1fs", time.time() - t)
        for name, path in split_paths.items():
            log.info("  %s → %s", name, path)

    _section("Pipeline complete")
    log.info(
        "All preprocessing steps done.\n"
        "Next step: run the training script.\n"
        "  python training/train_contributor.py\n"
        "  python training/train_reviewer.py"
    )


def _section(title: str) -> None:
    bar = "─" * 56
    log.info("\n%s\n  %s\n%s", bar, title, bar)


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )
    run(force=args.force, max_rows=args.max_rows, steps=args.steps)
