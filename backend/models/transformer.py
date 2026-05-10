"""
Transformer Architecture
------------------------
Defines SingleEncoderTransformer and DualEncoderTransformer models for
Java code review, as specified in Section 3 of the project proposal.

SingleEncoderTransformer  — contributor mode
  • Encoder: processes abstracted Java method tokens
  • Decoder: generates improved Java method tokens

DualEncoderTransformer    — reviewer mode
  • Code Encoder: processes abstracted Java method tokens
  • Comment Encoder: processes reviewer NL comment tokens
  • Cross-attention fusion layer merges both representations
  • Decoder: generates revised Java method tokens

Both models use beam search decoding (see BeamSearchDecoder).
ModelConfig holds all hyperparameters and can be serialised to JSON.
"""

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F


# ─── Hyperparameter config ────────────────────────────────────────────────────

@dataclass
class ModelConfig:
    vocab_size: int = 5000
    d_model: int = 256
    n_heads: int = 8
    num_encoder_layers: int = 4
    num_decoder_layers: int = 4
    d_ff: int = 1024
    dropout: float = 0.1
    max_seq_len: int = 150
    pad_token_id: int = 0
    bos_token_id: int = 1
    eos_token_id: int = 2

    def save(self, path: Path) -> None:
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "ModelConfig":
        with open(path) as f:
            data = json.load(f)
        return cls(**data)


# ─── Positional Encoding ──────────────────────────────────────────────────────

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, dropout: float, max_len: int = 512):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, : x.size(1)]
        return self.dropout(x)


# ─── Shared encoder block ─────────────────────────────────────────────────────

class TransformerEncoder(nn.Module):
    """Standard Transformer encoder stack."""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.embedding = nn.Embedding(config.vocab_size, config.d_model, padding_idx=config.pad_token_id)
        self.pos_enc = PositionalEncoding(config.d_model, config.dropout, config.max_seq_len)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.n_heads,
            dim_feedforward=config.d_ff,
            dropout=config.dropout,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=config.num_encoder_layers)

    def forward(
        self, src: torch.Tensor, src_key_padding_mask: torch.Tensor | None = None
    ) -> torch.Tensor:
        x = self.pos_enc(self.embedding(src))
        return self.encoder(x, src_key_padding_mask=src_key_padding_mask)


# ─── Shared decoder block ─────────────────────────────────────────────────────

class TransformerDecoder(nn.Module):
    """Standard Transformer decoder stack with projection to vocab."""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.embedding = nn.Embedding(config.vocab_size, config.d_model, padding_idx=config.pad_token_id)
        self.pos_enc = PositionalEncoding(config.d_model, config.dropout, config.max_seq_len)
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=config.d_model,
            nhead=config.n_heads,
            dim_feedforward=config.d_ff,
            dropout=config.dropout,
            batch_first=True,
        )
        self.decoder = nn.TransformerDecoder(decoder_layer, num_layers=config.num_decoder_layers)
        self.proj = nn.Linear(config.d_model, config.vocab_size)

    def forward(
        self,
        tgt: torch.Tensor,
        memory: torch.Tensor,
        tgt_mask: torch.Tensor | None = None,
        tgt_key_padding_mask: torch.Tensor | None = None,
        memory_key_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        x = self.pos_enc(self.embedding(tgt))
        out = self.decoder(
            x,
            memory,
            tgt_mask=tgt_mask,
            tgt_key_padding_mask=tgt_key_padding_mask,
            memory_key_padding_mask=memory_key_padding_mask,
        )
        return self.proj(out)  # (batch, tgt_len, vocab_size)


# ─── Beam Search ─────────────────────────────────────────────────────────────

def beam_search_decode(
    decode_fn,
    memory: torch.Tensor,
    config: ModelConfig,
    num_beams: int,
    max_len: int = 128,
    memory_padding_mask: torch.Tensor | None = None,
) -> list[tuple[list[int], float]]:
    """
    Greedy-style beam search that returns `num_beams` candidate token sequences.

    Args:
        decode_fn: callable(tgt, memory, ...) → logits of shape (1, tgt_len, vocab)
        memory: encoder output  (1, src_len, d_model)
        config: ModelConfig
        num_beams: number of beams
        max_len: maximum output length

    Returns:
        list of (token_ids, log_prob_score) sorted by score descending
    """
    device = memory.device
    beams: list[tuple[list[int], float]] = [([config.bos_token_id], 0.0)]
    completed: list[tuple[list[int], float]] = []

    for _ in range(max_len):
        if len(beams) == 0:
            break
        all_candidates: list[tuple[list[int], float]] = []

        for seq, score in beams:
            if seq[-1] == config.eos_token_id:
                completed.append((seq, score))
                continue

            tgt = torch.tensor([seq], dtype=torch.long, device=device)
            tgt_mask = nn.Transformer.generate_square_subsequent_mask(
                len(seq), device=device
            )
            with torch.no_grad():
                logits = decode_fn(
                    tgt,
                    memory,
                    tgt_mask=tgt_mask,
                    memory_key_padding_mask=memory_padding_mask,
                )
            log_probs = F.log_softmax(logits[0, -1], dim=-1)
            top_probs, top_ids = torch.topk(log_probs, num_beams)

            for prob, token_id in zip(top_probs.tolist(), top_ids.tolist()):
                all_candidates.append((seq + [token_id], score + prob))

        if not all_candidates:
            break
        all_candidates.sort(key=lambda x: x[1], reverse=True)
        beams = all_candidates[:num_beams]

    # Collect any unfinished beams as completed
    completed.extend(beams)
    completed.sort(key=lambda x: x[1], reverse=True)
    return completed[:num_beams]


# ─── Single-Encoder Transformer (contributor mode) ────────────────────────────

class SingleEncoderTransformer(nn.Module):
    """
    Encoder–Decoder Transformer for contributor-mode code review.

    Input:  abstracted Java method token ids
    Output: revised Java method token ids (beam search)
    """

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.encoder = TransformerEncoder(config)
        self.decoder = TransformerDecoder(config)

    def forward(
        self,
        src: torch.Tensor,
        tgt: torch.Tensor,
        src_padding_mask: torch.Tensor | None = None,
        tgt_mask: torch.Tensor | None = None,
        tgt_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        memory = self.encoder(src, src_key_padding_mask=src_padding_mask)
        return self.decoder(
            tgt,
            memory,
            tgt_mask=tgt_mask,
            tgt_key_padding_mask=tgt_padding_mask,
            memory_key_padding_mask=src_padding_mask,
        )

    def generate(self, src: torch.Tensor, num_beams: int = 3) -> list[tuple[list[int], float]]:
        """Run beam search and return (token_ids, score) pairs."""
        self.eval()
        src_padding_mask = (src == self.config.pad_token_id)
        memory = self.encoder(src, src_key_padding_mask=src_padding_mask)

        def decode_fn(tgt, mem, tgt_mask=None, memory_key_padding_mask=None):
            return self.decoder(
                tgt, mem,
                tgt_mask=tgt_mask,
                memory_key_padding_mask=memory_key_padding_mask,
            )

        return beam_search_decode(
            decode_fn, memory, self.config, num_beams,
            memory_padding_mask=src_padding_mask,
        )


# ─── Dual-Encoder Transformer (reviewer mode) ─────────────────────────────────

class CrossAttentionFusion(nn.Module):
    """
    Fuses code-encoder memory and comment-encoder memory via
    a single cross-attention layer:
      query = code memory
      key/value = comment memory
    The output is added back to the code memory (residual).
    """

    def __init__(self, d_model: int, n_heads: int, dropout: float):
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        code_memory: torch.Tensor,
        comment_memory: torch.Tensor,
        comment_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        attn_out, _ = self.attn(
            query=code_memory,
            key=comment_memory,
            value=comment_memory,
            key_padding_mask=comment_padding_mask,
        )
        return self.norm(code_memory + self.dropout(attn_out))


class DualEncoderTransformer(nn.Module):
    """
    Dual-Encoder Transformer for reviewer-mode code review.

    Inputs:
      code_src     — abstracted Java method token ids
      comment_src  — tokenised reviewer NL comment ids
    Output:
      revised Java method token ids (beam search)

    Architecture (as per proposal Section 3.2):
      1. Code Encoder    →  code memory    (seq_c, d_model)
      2. Comment Encoder →  comment memory (seq_n, d_model)
      3. Fusion layer    →  cross-attends code memory over comment memory
      4. Decoder         →  generates output from fused memory
    """

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.code_encoder = TransformerEncoder(config)
        self.comment_encoder = TransformerEncoder(config)
        self.fusion = CrossAttentionFusion(config.d_model, config.n_heads, config.dropout)
        self.decoder = TransformerDecoder(config)

    def encode(
        self,
        code_src: torch.Tensor,
        comment_src: torch.Tensor,
        code_padding_mask: torch.Tensor | None = None,
        comment_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        code_mem = self.code_encoder(code_src, src_key_padding_mask=code_padding_mask)
        comment_mem = self.comment_encoder(
            comment_src, src_key_padding_mask=comment_padding_mask
        )
        return self.fusion(code_mem, comment_mem, comment_padding_mask=comment_padding_mask)

    def forward(
        self,
        code_src: torch.Tensor,
        comment_src: torch.Tensor,
        tgt: torch.Tensor,
        code_padding_mask: torch.Tensor | None = None,
        comment_padding_mask: torch.Tensor | None = None,
        tgt_mask: torch.Tensor | None = None,
        tgt_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        fused_memory = self.encode(
            code_src, comment_src, code_padding_mask, comment_padding_mask
        )
        return self.decoder(
            tgt,
            fused_memory,
            tgt_mask=tgt_mask,
            tgt_key_padding_mask=tgt_padding_mask,
            memory_key_padding_mask=code_padding_mask,
        )

    def generate(
        self,
        code_src: torch.Tensor,
        comment_src: torch.Tensor,
        num_beams: int = 3,
    ) -> list[tuple[list[int], float]]:
        """Run beam search and return (token_ids, score) pairs."""
        self.eval()
        code_padding_mask = (code_src == self.config.pad_token_id)
        comment_padding_mask = (comment_src == self.config.pad_token_id)
        fused_memory = self.encode(
            code_src, comment_src, code_padding_mask, comment_padding_mask
        )

        def decode_fn(tgt, mem, tgt_mask=None, memory_key_padding_mask=None):
            return self.decoder(
                tgt, mem,
                tgt_mask=tgt_mask,
                memory_key_padding_mask=memory_key_padding_mask,
            )

        return beam_search_decode(
            decode_fn, fused_memory, self.config, num_beams,
            memory_padding_mask=code_padding_mask,
        )
