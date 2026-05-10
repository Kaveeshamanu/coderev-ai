"""
Java Method Filter & Validator
-------------------------------
Validates and cleans individual Java code hunks before they enter the
abstraction pipeline.

Rules applied (matching project proposal Section 3.3):
  1. Must contain at least one Java keyword
  2. Must have balanced curly braces  { }
  3. Token count (whitespace-split) must be within [MIN_TOKENS, MAX_TOKENS]
  4. Must not be a pure comment block (no executable code)
  5. Strip leading/trailing whitespace; normalise CRLF → LF
  6. Pairs where old_hunk == new_hunk and comment is empty are discarded
     (identity pairs with no learning signal)
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessing.config import MIN_TOKENS, MAX_TOKENS

# Java reserved keywords — a valid snippet must contain at least one
_JAVA_KEYWORDS = frozenset({
    "abstract", "assert", "boolean", "break", "byte", "case", "catch",
    "char", "class", "const", "continue", "default", "do", "double",
    "else", "enum", "extends", "final", "finally", "float", "for",
    "goto", "if", "implements", "import", "instanceof", "int",
    "interface", "long", "native", "new", "package", "private",
    "protected", "public", "return", "short", "static", "super",
    "switch", "synchronized", "this", "throw", "throws", "transient",
    "try", "void", "volatile", "while",
})

# Regex: a complete Java method signature
_METHOD_SIGNATURE_RE = re.compile(
    r"\b(?:public|private|protected|static|final|abstract|synchronized)\b"
    r"[\w\s<>\[\],?@]*\s+\w+\s*\("
)


def is_valid_java(code: str) -> bool:
    """
    Return True if `code` passes all validation rules.
    Used to filter both old_hunk and new_hunk.
    """
    if not code or not code.strip():
        return False

    text = code.strip()

    # Rule 1: must have at least one Java keyword
    words = set(re.findall(r"\b[a-zA-Z_]\w*\b", text))
    if not (words & _JAVA_KEYWORDS):
        return False

    # Rule 2: balanced braces (allow methods without outer braces for hunks)
    if text.count("{") != text.count("}"):
        return False

    # Rule 3: token count
    tokens = text.split()
    if not (MIN_TOKENS <= len(tokens) <= MAX_TOKENS):
        return False

    # Rule 4: not a pure comment block
    non_comment = re.sub(r"//[^\n]*", "", text)
    non_comment = re.sub(r"/\*.*?\*/", "", non_comment, flags=re.DOTALL)
    if not non_comment.strip():
        return False

    return True


def clean_code(code: str) -> str:
    """
    Normalise a code hunk:
      - CRLF → LF
      - Remove trailing whitespace per line
      - Collapse sequences of 3+ blank lines to 2
    """
    text = code.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]

    # Collapse excessive blank lines
    cleaned: list[str] = []
    blank_run = 0
    for ln in lines:
        if ln == "":
            blank_run += 1
            if blank_run <= 2:
                cleaned.append(ln)
        else:
            blank_run = 0
            cleaned.append(ln)

    return "\n".join(cleaned).strip()


def is_valid_pair(old: str, new: str, comment: str) -> bool:
    """
    Return True if the (old_hunk, new_hunk, comment) triple is worth training on.
    Rejects identity pairs with no comment (zero learning signal).
    """
    if not is_valid_java(old):
        return False
    if not is_valid_java(new):
        return False
    # Identity pairs are fine only if there's a reviewer comment
    if old.strip() == new.strip() and not comment.strip():
        return False
    return True


def clean_comment(comment: str) -> str:
    """
    Normalise a reviewer comment:
      - Lowercase
      - Strip URLs (not informative for the model)
      - Collapse whitespace
      - Truncate to 200 characters
    """
    text = comment.strip().lower()
    text = re.sub(r"https?://\S+", "", text)         # remove URLs
    text = re.sub(r"[^\w\s\-'.,!?]", " ", text)      # keep basic punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text[:200]


def filter_dataset(records: list[dict]) -> list[dict]:
    """
    Apply all filters to a list of raw records.
    Returns cleaned, valid records ready for abstraction.

    Each record must have keys: old_hunk, new_hunk, comment
    """
    valid = []
    stats = {"total": 0, "invalid_old": 0, "invalid_new": 0,
             "identity_no_comment": 0, "passed": 0}

    for rec in records:
        stats["total"] += 1
        old = clean_code(rec.get("old_hunk", ""))
        new = clean_code(rec.get("new_hunk", ""))
        comment = clean_comment(rec.get("comment", ""))

        if not is_valid_java(old):
            stats["invalid_old"] += 1
            continue
        if not is_valid_java(new):
            stats["invalid_new"] += 1
            continue
        if old == new and not comment:
            stats["identity_no_comment"] += 1
            continue

        stats["passed"] += 1
        valid.append({"old_hunk": old, "new_hunk": new, "comment": comment})

    # Print a summary
    print(
        f"[java_filter] {stats['total']} total  →  "
        f"{stats['passed']} passed  |  "
        f"invalid_old={stats['invalid_old']}  "
        f"invalid_new={stats['invalid_new']}  "
        f"identity_no_comment={stats['identity_no_comment']}"
    )
    return valid
