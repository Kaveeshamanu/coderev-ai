"""
Preprocessing Pipeline — Configuration
---------------------------------------
Single source of truth for all paths, constants, and dataset settings
used across the preprocessing scripts.
"""

from pathlib import Path

# ─── Root directories ──────────────────────────────────────────────────────────

# backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent

# backend/data/
DATA_DIR = BACKEND_DIR / "data"

RAW_DIR      = DATA_DIR / "raw"          # downloaded dataset files
CORPUS_DIR   = DATA_DIR / "corpus"       # abstracted .txt files for tokenizer
TOKENIZER_DIR = DATA_DIR / "tokenizer"  # trained tokenizer artefacts
SPLITS_DIR   = DATA_DIR / "splits"      # final .jsonl train/val/test

# ─── Dataset settings ─────────────────────────────────────────────────────────

# Primary dataset — Microsoft CodeReviewer
# Paper: "Automating Code Review Activities by Large-Scale Pre-training" (2022)
# HuggingFace: microsoft/codereview
DATASET_NAME    = "microsoft/codereview"
DATASET_SPLIT   = "train"          # download training split; we re-split ourselves
JAVA_LANG_TAG   = "java"           # value used to filter Java rows

# Minimum / maximum token counts for a valid Java method (whitespace-split)
MIN_TOKENS = 10
MAX_TOKENS = 300

# ─── Tokenizer settings ───────────────────────────────────────────────────────

VOCAB_SIZE    = 5000               # must match ModelConfig.vocab_size
SPECIAL_TOKENS = ["<PAD>", "<BOS>", "<EOS>", "<UNK>"]
PAD_TOKEN_ID  = 0
BOS_TOKEN_ID  = 1
EOS_TOKEN_ID  = 2
UNK_TOKEN_ID  = 3

# ─── Dataset split ratios ─────────────────────────────────────────────────────

TRAIN_RATIO = 0.80
VAL_RATIO   = 0.10
TEST_RATIO  = 0.10   # remainder goes to test

# Seed for reproducible shuffling
RANDOM_SEED = 42

# Maximum rows to use (set to None to use everything)
# Reduce during development to speed up iteration
MAX_ROWS = None          # e.g. 50_000 for a quick run
