"""
CodeRev AI — FastAPI Backend
Endpoints:
  POST /api/contributor/review   — Single-Encoder model (code → suggestions)
  POST /api/reviewer/implement   — Dual-Encoder model   (code + comment → implementations)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import Optional
import re
import time

from models.inference import contributor_inference, reviewer_inference

app = FastAPI(
    title="CodeRev AI API",
    description="Automated Java code review using Transformer-based NMT models.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


# ─── Request / Response schemas ───────────────────────────────────────────────

class ContributorRequest(BaseModel):
    code: str
    beams: int = 3

    @field_validator("code")
    @classmethod
    def code_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("code must not be empty")
        return v.strip()

    @field_validator("beams")
    @classmethod
    def beams_must_be_valid(cls, v: int) -> int:
        if v not in (1, 3, 5, 10):
            raise ValueError("beams must be one of 1, 3, 5, 10")
        return v


class ReviewerRequest(BaseModel):
    code: str
    comment: str
    beams: int = 3

    @field_validator("code")
    @classmethod
    def code_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("code must not be empty")
        return v.strip()

    @field_validator("comment")
    @classmethod
    def comment_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("comment must not be empty")
        return v.strip()

    @field_validator("beams")
    @classmethod
    def beams_must_be_valid(cls, v: int) -> int:
        if v not in (1, 3, 5, 10):
            raise ValueError("beams must be one of 1, 3, 5, 10")
        return v


class Suggestion(BaseModel):
    rank: int
    score: float
    code: str
    explanation: str
    tags: list[str]


class ContributorResponse(BaseModel):
    suggestions: list[Suggestion]
    processing_time_ms: int


class Implementation(BaseModel):
    rank: int
    score: float
    code: str
    explanation: str
    tags: list[str]


class ReviewerResponse(BaseModel):
    implementations: list[Implementation]
    processing_time_ms: int


# ─── Health check ─────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "models_loaded": True}


# ─── Contributor endpoint ──────────────────────────────────────────────────────

@app.post("/api/contributor/review", response_model=ContributorResponse)
def contributor_review(req: ContributorRequest):
    """
    Single-Encoder Transformer: Java method → ranked code suggestions.

    The model was trained on method-level code review pairs
    (original_code → revised_code). It applies code abstraction
    internally before inference and de-abstracts the output.
    """
    _validate_java(req.code)

    t0 = time.time()
    try:
        results = contributor_inference(code=req.code, beams=req.beams)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {e}")

    elapsed_ms = int((time.time() - t0) * 1000)
    return ContributorResponse(suggestions=results, processing_time_ms=elapsed_ms)


# ─── Reviewer endpoint ─────────────────────────────────────────────────────────

@app.post("/api/reviewer/implement", response_model=ReviewerResponse)
def reviewer_implement(req: ReviewerRequest):
    """
    Dual-Encoder Transformer: (Java method + NL comment) → ranked implementations.

    The code encoder processes the abstracted Java method; the comment encoder
    processes the natural language reviewer comment. Both representations are
    fused and decoded with beam search.
    """
    _validate_java(req.code)

    t0 = time.time()
    try:
        results = reviewer_inference(
            code=req.code, comment=req.comment, beams=req.beams
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference failed: {e}")

    elapsed_ms = int((time.time() - t0) * 1000)
    return ReviewerResponse(implementations=results, processing_time_ms=elapsed_ms)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _validate_java(code: str) -> None:
    """Basic structural validation — no execution, no compilation."""
    stripped = code.strip()
    if len(stripped) < 10:
        raise HTTPException(status_code=400, detail="Code is too short.")
    if stripped.count("{") != stripped.count("}"):
        raise HTTPException(
            status_code=400,
            detail="Unbalanced braces — please paste a complete Java method.",
        )
    # Must look like a method declaration
    method_pattern = re.compile(
        r"\b(public|private|protected|static|void|int|boolean|String|List|Map|Set|"
        r"long|double|float|Object|Optional)\b"
    )
    if not method_pattern.search(stripped):
        raise HTTPException(
            status_code=400,
            detail="Input does not appear to be a valid Java method.",
        )
