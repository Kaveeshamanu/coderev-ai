"""
BPE Tokenizer Training
-----------------------
Trains a Byte-Pair Encoding (BPE) tokenizer on the abstracted Java corpus
using HuggingFace `tokenizers` library.

The trained tokenizer is saved to data/tokenizer/ as:
  tokenizer.json    — full tokenizer (load with Tokenizer.from_file)
  vocab.json        — token → id mapping
  merges.txt        — BPE merge rules

Vocabulary size (5 000) matches ModelConfig.vocab_size in transformer.py.

Special tokens (fixed IDs):
  <PAD>  → 0
  <BOS>  → 1
  <EOS>  → 2
  <UNK>  → 3
"""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessing.config import (
    CORPUS_DIR, TOKENIZER_DIR,
    VOCAB_SIZE, SPECIAL_TOKENS,
    PAD_TOKEN_ID, BOS_TOKEN_ID, EOS_TOKEN_ID,
)
from preprocessing.build_corpus import iter_corpus_lines

log = logging.getLogger(__name__)


def train(corpus_txt: Path | None = None, force: bool = False) -> Path:
    """
    Train a BPE tokenizer on the abstracted corpus.

    Args:
        corpus_txt: Path to the flat .txt corpus (one abstracted snippet per line).
        force:      Retrain even if the tokenizer already exists.

    Returns:
        Path to the saved tokenizer directory.
    """
    if corpus_txt is None:
        corpus_txt = CORPUS_DIR / "abstracted_code.txt"

    if not corpus_txt.exists():
        raise FileNotFoundError(
            f"Corpus not found at {corpus_txt}. "
            "Run preprocessing/build_corpus.py first."
        )

    TOKENIZER_DIR.mkdir(parents=True, exist_ok=True)
    tokenizer_path = TOKENIZER_DIR / "tokenizer.json"

    if tokenizer_path.exists() and not force:
        log.info("Tokenizer already trained at %s — skipping.", tokenizer_path)
        return TOKENIZER_DIR

    try:
        from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders
        from tokenizers.normalizers import NFC
    except ImportError:
        log.error("'tokenizers' package not installed. Run: pip install tokenizers")
        raise

    log.info("Initialising BPE tokenizer (vocab_size=%d)…", VOCAB_SIZE)

    # ── Build tokenizer ────────────────────────────────────────────────────────
    tokenizer = Tokenizer(models.BPE(unk_token="<UNK>"))

    # Whitespace pre-tokenizer: split on spaces and newlines
    # This is appropriate for abstracted code which already has tokens
    # separated by whitespace or Java punctuation.
    tokenizer.pre_tokenizer = pre_tokenizers.Sequence([
        pre_tokenizers.Whitespace(),
    ])

    # BPE decoder to reconstruct text from subword tokens
    tokenizer.decoder = decoders.BPEDecoder()

    # ── Trainer ────────────────────────────────────────────────────────────────
    trainer = trainers.BpeTrainer(
        vocab_size=VOCAB_SIZE,
        special_tokens=SPECIAL_TOKENS,
        min_frequency=2,          # ignore tokens that appear < 2 times
        show_progress=True,
        initial_alphabet=_java_initial_alphabet(),
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    log.info("Training on corpus: %s", corpus_txt)

    def line_iterator():
        """Yield individual lines from the corpus file."""
        with open(corpus_txt, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield line

    tokenizer.train_from_iterator(line_iterator(), trainer=trainer)

    # ── Verify special token IDs match ModelConfig ────────────────────────────
    _verify_special_tokens(tokenizer)

    # ── Save ──────────────────────────────────────────────────────────────────
    tokenizer.save(str(tokenizer_path))
    log.info("Tokenizer saved → %s", tokenizer_path)

    # Also save standalone vocab.json for easy inspection
    vocab = tokenizer.get_vocab()
    vocab_path = TOKENIZER_DIR / "vocab.json"
    with open(vocab_path, "w", encoding="utf-8") as f:
        json.dump(vocab, f, indent=2, ensure_ascii=False)
    log.info("Vocab saved → %s  (%d tokens)", vocab_path, len(vocab))

    # Save tokenizer config for inference loading
    config = {
        "vocab_size": len(vocab),
        "pad_token": "<PAD>",
        "bos_token": "<BOS>",
        "eos_token": "<EOS>",
        "unk_token": "<UNK>",
        "pad_token_id": PAD_TOKEN_ID,
        "bos_token_id": BOS_TOKEN_ID,
        "eos_token_id": EOS_TOKEN_ID,
        "model_type": "bpe",
    }
    config_path = TOKENIZER_DIR / "tokenizer_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    log.info("Tokenizer config → %s", config_path)

    return TOKENIZER_DIR


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _java_initial_alphabet() -> list[str]:
    """
    Seed the BPE alphabet with characters that appear in Java code.
    This prevents the tokenizer from splitting common operators/punctuation
    into unknown character sequences.
    """
    chars = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    chars += list("0123456789")
    chars += list("{}()[].;,<>!=+-*/%&|^~?:@_\\\"'`")
    chars += [" ", "\t", "\n"]
    return chars


def _verify_special_tokens(tokenizer) -> None:
    """
    Check that <PAD>=0, <BOS>=1, <EOS>=2, <UNK>=3.
    The HuggingFace trainer assigns IDs in the order special_tokens is given,
    so this should always pass — but we assert to catch misconfiguration early.
    """
    vocab = tokenizer.get_vocab()
    expected = {
        "<PAD>": PAD_TOKEN_ID,
        "<BOS>": BOS_TOKEN_ID,
        "<EOS>": EOS_TOKEN_ID,
        "<UNK>": 3,
    }
    for token, expected_id in expected.items():
        actual_id = vocab.get(token)
        if actual_id != expected_id:
            raise ValueError(
                f"Special token '{token}' has id={actual_id}, expected {expected_id}. "
                "Check SPECIAL_TOKENS order in config.py."
            )
    log.info("Special token IDs verified: PAD=0 BOS=1 EOS=2 UNK=3 ✓")


def load_tokenizer(tokenizer_dir: Path | None = None):
    """
    Load the trained tokenizer from disk.
    Returns a HuggingFace Tokenizer object.
    """
    if tokenizer_dir is None:
        tokenizer_dir = TOKENIZER_DIR
    from tokenizers import Tokenizer
    path = tokenizer_dir / "tokenizer.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Tokenizer not found at {path}. "
            "Run preprocessing/train_tokenizer.py first."
        )
    return Tokenizer.from_file(str(path))


def encode(tokenizer, text: str, add_special_tokens: bool = True) -> list[int]:
    """Encode text → list of token IDs, optionally wrapping with BOS/EOS."""
    ids = tokenizer.encode(text).ids
    if add_special_tokens:
        ids = [BOS_TOKEN_ID] + ids + [EOS_TOKEN_ID]
    return ids


def decode(tokenizer, ids: list[int], skip_special_tokens: bool = True) -> str:
    """Decode token IDs → text, optionally stripping special tokens."""
    if skip_special_tokens:
        special = {PAD_TOKEN_ID, BOS_TOKEN_ID, EOS_TOKEN_ID, 3}  # 3 = UNK
        ids = [i for i in ids if i not in special]
    return tokenizer.decode(ids)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    out = train()
    print(f"Done → {out}")
