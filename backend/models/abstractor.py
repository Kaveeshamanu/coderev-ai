"""
Code Abstraction Module
-----------------------
Replaces identifiers and string/numeric literals with generic tokens
(e.g. VAR_0, METHOD_0, STRING_0, NUMBER_0) before model inference,
and reverses the mapping on the output — exactly as described in the
project proposal (Section 3.3: Preprocessing Pipeline).

This keeps the vocabulary small and improves generalisation across
differently-named codebases.
"""

import re
from dataclasses import dataclass, field


@dataclass
class AbstractionMap:
    """Holds the token ↔ original-value mapping for one abstraction pass."""
    var_map: dict[str, str] = field(default_factory=dict)
    method_map: dict[str, str] = field(default_factory=dict)
    string_map: dict[str, str] = field(default_factory=dict)
    number_map: dict[str, str] = field(default_factory=dict)


# Java reserved words — never abstracted
_JAVA_KEYWORDS = frozenset({
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "null", "package", "private", "protected", "public", "return", "short",
    "static", "strictfp", "super", "switch", "synchronized", "this", "throw",
    "throws", "transient", "true", "false", "try", "void", "volatile", "while",
    # Common stdlib types kept as-is for readability
    "String", "List", "Map", "Set", "Object", "Optional", "ArrayList",
    "HashMap", "HashSet", "Exception", "RuntimeException", "System",
    "Math", "Arrays", "Collections", "Objects", "logger", "Logger",
})


def abstract_code(code: str) -> tuple[str, AbstractionMap]:
    """
    Abstracts a Java method string and returns the abstracted code
    plus the mapping needed to de-abstract model output.
    """
    amap = AbstractionMap()
    result = code

    # 1. String literals  →  STRING_N
    def replace_string(m: re.Match) -> str:
        original = m.group(0)
        if original not in amap.string_map.values():
            tok = f"STRING_{len(amap.string_map)}"
            amap.string_map[tok] = original
            return tok
        # already seen — reuse token
        return next(k for k, v in amap.string_map.items() if v == original)

    result = re.sub(r'"(?:[^"\\]|\\.)*"', replace_string, result)
    result = re.sub(r"'(?:[^'\\]|\\.)*'", replace_string, result)

    # 2. Numeric literals  →  NUMBER_N
    def replace_number(m: re.Match) -> str:
        original = m.group(0)
        if original not in amap.number_map.values():
            tok = f"NUMBER_{len(amap.number_map)}"
            amap.number_map[tok] = original
            return tok
        return next(k for k, v in amap.number_map.items() if v == original)

    result = re.sub(r"\b\d+(?:\.\d+)?[fFlLdD]?\b", replace_number, result)

    # 3. Method calls / declarations  →  METHOD_N
    #    Pattern: identifier immediately followed by '('
    seen_methods: dict[str, str] = {}

    def replace_method(m: re.Match) -> str:
        name = m.group(1)
        if name in _JAVA_KEYWORDS:
            return m.group(0)
        if name not in seen_methods:
            tok = f"METHOD_{len(amap.method_map)}"
            amap.method_map[tok] = name
            seen_methods[name] = tok
        return seen_methods[name] + "("

    result = re.sub(r"\b([a-zA-Z_]\w*)\s*\(", replace_method, result)

    # 4. Remaining identifiers  →  VAR_N
    seen_vars: dict[str, str] = {}

    def replace_var(m: re.Match) -> str:
        name = m.group(0)
        if name in _JAVA_KEYWORDS:
            return name
        if name.startswith(("VAR_", "METHOD_", "STRING_", "NUMBER_")):
            return name  # already abstracted
        if name not in seen_vars:
            tok = f"VAR_{len(amap.var_map)}"
            amap.var_map[tok] = name
            seen_vars[name] = tok
        return seen_vars[name]

    result = re.sub(r"\b[a-zA-Z_]\w*\b", replace_var, result)

    return result, amap


def deabstract_code(abstracted: str, amap: AbstractionMap) -> str:
    """Reverses the abstraction map to recover readable identifiers."""
    result = abstracted

    # Reverse in the same order: strings, numbers, methods, vars
    for tok, original in amap.string_map.items():
        result = result.replace(tok, original)
    for tok, original in amap.number_map.items():
        result = result.replace(tok, original)
    for tok, original in amap.method_map.items():
        result = result.replace(tok, original)
    for tok, original in amap.var_map.items():
        result = result.replace(tok, original)

    return result


def clean_comment(comment: str) -> str:
    """
    Normalise a natural language reviewer comment:
    lowercase, strip punctuation noise, collapse whitespace.
    """
    text = comment.lower().strip()
    text = re.sub(r"[^\w\s\-'.,]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text
