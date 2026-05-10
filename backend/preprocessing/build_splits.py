"""
Dataset Split Builder
----------------------
Reads the abstracted pairs (data/corpus/abstracted_pairs.jsonl) and the
trained tokenizer, then produces tokenised train / val / test splits as
.jsonl files under data/splits/.

Output schema per record (both splits):
  For contributor model (single-encoder):
    src_ids   — token IDs of abstracted old_hunk  (BOS + ids + EOS)
    tgt_ids   — token IDs of abstracted new_hunk  (BOS + ids + EOS)

  For reviewer model (dual-encoder):
    code_ids    — token IDs of abstracted old_hunk
    comment_ids — token IDs of cleaned comment
    tgt_ids     — token IDs of abstracted new_hunk

Both schemas are stored in every record so the same split files work
for both training runs.

Split sizes (default 80 / 10 / 10):
  data/splits/train.jsonl
  data/splits/val.jsonl
  data/splits/test.jsonl

Stats are written to data/splits/stats.json.
"""

import json
import logging
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessing.config import (
    CORPUS_DIR, SPLITS_DIR, TOKENIZER_DIR,
    TRAIN_RATIO, VAL_RATIO, RANDOM_SEED,
    BOS_TOKEN_ID, EOS_TOKEN_ID, PAD_TOKEN_ID,
)
from preprocessing.train_tokenizer import load_tokenizer, encode

log = logging.getLogger(__name__)

# Max token length per sequence (longer sequences are truncated)
MAX_SEQ_LEN = 148  # leaves room for BOS and EOS within ModelConfig.max_seq_len=150


def build(pairs_path: Path | None = None, force: bool = False) -> dict[str, Path]:
    """
    Tokenise and split the abstracted pairs into train/val/test.

    Returns:
        Dict mapping split name → path.
    """
    if pairs_path is None:
        pairs_path = CORPUS_DIR / "abstracted_pairs.jsonl"

    if not pairs_path.exists():
        raise FileNotFoundError(
            f"Abstracted pairs not found at {pairs_path}. "
            "Run preprocessing/build_corpus.py first."
        )

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    split_paths = {
        "train": SPLITS_DIR / "train.jsonl",
        "val":   SPLITS_DIR / "val.jsonl",
        "test":  SPLITS_DIR / "test.jsonl",
    }

    if all(p.exists() for p in split_paths.values()) and not force:
        log.info("Splits already exist at %s — skipping.", SPLITS_DIR)
        return split_paths

    # ── Load tokenizer ────────────────────────────────────────────────────────
    log.info("Loading tokenizer from %s…", TOKENIZER_DIR)
    tokenizer = load_tokenizer(TOKENIZER_DIR)

    # ── Load pairs ────────────────────────────────────────────────────────────
    log.info("Loading abstracted pairs from %s…", pairs_path)
    records = []
    with open(pairs_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    log.info("Loaded %d pairs.", len(records))

    # ── Tokenise ──────────────────────────────────────────────────────────────
    log.info("Tokenising…")
    tokenised: list[dict] = []
    skipped = 0

    for rec in records:
        try:
            src_ids     = _tokenise(tokenizer, rec["old_abs"])
            tgt_ids     = _tokenise(tokenizer, rec["new_abs"])
            comment_ids = _tokenise(tokenizer, rec["comment"], add_special=False)

            tokenised.append({
                # Contributor model inputs/targets
                "src_ids":     src_ids,
                "tgt_ids":     tgt_ids,
                # Reviewer model inputs (code_ids == src_ids)
                "code_ids":    src_ids,
                "comment_ids": comment_ids,
                # Human-readable fields (useful for debugging / evaluation)
                "old_raw":  rec.get("old_raw", ""),
                "new_raw":  rec.get("new_raw", ""),
                "comment":  rec.get("comment", ""),
            })
        except Exception as e:
            log.debug("Tokenisation error (skipping): %s", e)
            skipped += 1

    log.info("Tokenised: %d  skipped: %d", len(tokenised), skipped)

    # ── Shuffle + split ───────────────────────────────────────────────────────
    random.seed(RANDOM_SEED)
    random.shuffle(tokenised)

    n = len(tokenised)
    n_train = int(n * TRAIN_RATIO)
    n_val   = int(n * VAL_RATIO)

    splits = {
        "train": tokenised[:n_train],
        "val":   tokenised[n_train : n_train + n_val],
        "test":  tokenised[n_train + n_val :],
    }

    # ── Write ─────────────────────────────────────────────────────────────────
    for name, data in splits.items():
        path = split_paths[name]
        with open(path, "w", encoding="utf-8") as f:
            for rec in data:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        log.info("  %s → %s  (%d records)", name, path, len(data))

    # ── Stats ─────────────────────────────────────────────────────────────────
    src_lengths = [len(r["src_ids"]) for r in tokenised]
    tgt_lengths = [len(r["tgt_ids"]) for r in tokenised]
    cmt_lengths = [len(r["comment_ids"]) for r in tokenised]

    stats = {
        "total":           n,
        "train":           len(splits["train"]),
        "val":             len(splits["val"]),
        "test":            len(splits["test"]),
        "skipped":         skipped,
        "src_len_mean":    round(sum(src_lengths) / max(n, 1), 1),
        "src_len_max":     max(src_lengths, default=0),
        "tgt_len_mean":    round(sum(tgt_lengths) / max(n, 1), 1),
        "tgt_len_max":     max(tgt_lengths, default=0),
        "comment_len_mean": round(sum(cmt_lengths) / max(n, 1), 1),
    }
    stats_path = SPLITS_DIR / "stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    log.info("Stats → %s", stats_path)
    _print_stats(stats)

    return split_paths


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _tokenise(tokenizer, text: str, add_special: bool = True) -> list[int]:
    """
    Tokenise `text`, truncate to MAX_SEQ_LEN, and optionally wrap with BOS/EOS.
    Collapses multi-line code to a single line before encoding.
    """
    flat = text.replace("\n", " ").strip()
    ids = tokenizer.encode(flat).ids[:MAX_SEQ_LEN]
    if add_special:
        ids = [BOS_TOKEN_ID] + ids + [EOS_TOKEN_ID]
    return ids


def _print_stats(stats: dict) -> None:
    print("\n─── Dataset Statistics ───────────────────────────────")
    print(f"  Total pairs   : {stats['total']:>8,}")
    print(f"  Train         : {stats['train']:>8,}")
    print(f"  Val           : {stats['val']:>8,}")
    print(f"  Test          : {stats['test']:>8,}")
    print(f"  Skipped       : {stats['skipped']:>8,}")
    print(f"  src len (avg) : {stats['src_len_mean']:>8.1f}  max={stats['src_len_max']}")
    print(f"  tgt len (avg) : {stats['tgt_len_mean']:>8.1f}  max={stats['tgt_len_max']}")
    print(f"  comment (avg) : {stats['comment_len_mean']:>8.1f}")
    print("──────────────────────────────────────────────────────\n")


class CodeReviewDataset:
    """
    Minimal PyTorch Dataset wrapper for the .jsonl split files.
    Used during model training.

    Usage:
        from preprocessing.build_splits import CodeReviewDataset
        train_ds = CodeReviewDataset(split="train", mode="contributor")
        # mode: "contributor" → yields (src_ids, tgt_ids)
        #       "reviewer"    → yields (code_ids, comment_ids, tgt_ids)
    """

    def __init__(
        self,
        split: str = "train",
        mode: str = "contributor",
        splits_dir: Path | None = None,
        pad_id: int = PAD_TOKEN_ID,
        max_len: int = 150,
    ):
        if splits_dir is None:
            splits_dir = SPLITS_DIR
        path = splits_dir / f"{split}.jsonl"
        if not path.exists():
            raise FileNotFoundError(
                f"Split not found: {path}. Run preprocessing/build_splits.py first."
            )

        self.mode    = mode
        self.pad_id  = pad_id
        self.max_len = max_len
        self.records: list[dict] = []

        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.records.append(json.loads(line))

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int):
        """
        Returns a dict with tensor-ready token ID lists.
        Actual tensor conversion happens in the collate_fn during DataLoader.
        """
        rec = self.records[idx]
        if self.mode == "contributor":
            return {
                "src_ids": rec["src_ids"][: self.max_len],
                "tgt_ids": rec["tgt_ids"][: self.max_len],
            }
        else:  # reviewer
            return {
                "code_ids":    rec["code_ids"][: self.max_len],
                "comment_ids": rec["comment_ids"][: self.max_len],
                "tgt_ids":     rec["tgt_ids"][: self.max_len],
            }


def collate_fn(batch: list[dict], pad_id: int = PAD_TOKEN_ID) -> dict:
    """
    Pad a batch of variable-length sequences to the same length.
    Pass as `collate_fn` to torch.utils.data.DataLoader.

    Returns a dict of lists (caller converts to tensors).
    """
    keys = batch[0].keys()
    result: dict[str, list] = {k: [] for k in keys}

    for sample in batch:
        for k in keys:
            result[k].append(sample[k])

    # Pad each key to the max length in this batch
    for k in keys:
        max_len = max(len(seq) for seq in result[k])
        result[k] = [
            seq + [pad_id] * (max_len - len(seq))
            for seq in result[k]
        ]

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    paths = build()
    for name, path in paths.items():
        print(f"  {name:6s} → {path}")
