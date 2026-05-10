"""
Shared Training Utilities
--------------------------
Loss function, learning-rate scheduler, checkpoint management,
and TensorBoard logging — shared by both training scripts.
"""

import json
import logging
import math
import shutil
from pathlib import Path

import torch
import torch.nn as nn

log = logging.getLogger(__name__)


# ─── Loss ────────────────────────────────────────────────────────────────────

class LabelSmoothedCrossEntropy(nn.Module):
    """
    Cross-entropy with label smoothing — reduces overconfidence and helps
    generalisation on small datasets like ours (~4 k pairs).
    """
    def __init__(self, vocab_size: int, pad_id: int, smoothing: float = 0.1):
        super().__init__()
        self.pad_id    = pad_id
        self.smoothing = smoothing
        self.vocab_size = vocab_size
        self.ce = nn.CrossEntropyLoss(ignore_index=pad_id, reduction="sum")

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        logits:  (batch, seq_len, vocab_size)
        targets: (batch, seq_len)
        """
        B, T, V = logits.shape
        logits_flat  = logits.reshape(-1, V)
        targets_flat = targets.reshape(-1)

        # Hard CE
        hard = self.ce(logits_flat, targets_flat)

        # Smooth component: uniform over all non-pad tokens
        non_pad_mask = (targets_flat != self.pad_id).float()
        smooth = -(logits_flat.log_softmax(-1).sum(-1) * non_pad_mask).sum()

        n_tokens = non_pad_mask.sum().clamp(min=1)
        loss = (1 - self.smoothing) * hard + self.smoothing * smooth / self.vocab_size
        return loss / n_tokens


# ─── LR Scheduler (warmup + cosine decay) ────────────────────────────────────

class WarmupCosineScheduler:
    """
    Linear warmup for `warmup_steps`, then cosine decay to `min_lr`.
    Compatible with any torch optimizer.
    """
    def __init__(
        self,
        optimizer: torch.optim.Optimizer,
        warmup_steps: int,
        total_steps: int,
        base_lr: float,
        min_lr: float = 1e-6,
    ):
        self.optimizer     = optimizer
        self.warmup_steps  = warmup_steps
        self.total_steps   = total_steps
        self.base_lr       = base_lr
        self.min_lr        = min_lr
        self._step         = 0

    def step(self):
        self._step += 1
        lr = self._get_lr()
        for pg in self.optimizer.param_groups:
            pg["lr"] = lr

    def _get_lr(self) -> float:
        s = self._step
        if s < self.warmup_steps:
            return self.base_lr * s / max(self.warmup_steps, 1)
        progress = (s - self.warmup_steps) / max(self.total_steps - self.warmup_steps, 1)
        cosine   = 0.5 * (1 + math.cos(math.pi * progress))
        return self.min_lr + (self.base_lr - self.min_lr) * cosine

    def get_lr(self) -> float:
        return self._get_lr()


# ─── Checkpoint manager ───────────────────────────────────────────────────────

class CheckpointManager:
    """
    Saves the best model (lowest val loss) and a rolling last checkpoint.
    """
    def __init__(self, save_dir: Path, model_name: str):
        self.save_dir   = save_dir
        self.model_name = model_name
        self.best_loss  = float("inf")
        save_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        model: nn.Module,
        config,
        epoch: int,
        val_loss: float,
        extra: dict | None = None,
    ) -> bool:
        """
        Always saves 'last.pt'. Saves 'best.pt' when val_loss improves.
        Returns True if this was a new best.
        """
        payload = {
            "epoch":    epoch,
            "val_loss": val_loss,
            "model":    model.state_dict(),
            **(extra or {}),
        }

        last_path = self.save_dir / f"{self.model_name}_last.pt"
        torch.save(payload, last_path)

        is_best = val_loss < self.best_loss
        if is_best:
            self.best_loss = val_loss
            best_path = self.save_dir / f"{self.model_name}.pt"
            shutil.copy(last_path, best_path)
            config.save(self.save_dir / f"{self.model_name}_config.json")
            log.info(
                "  ✓ New best val_loss=%.4f  saved → %s", val_loss, best_path
            )

        return is_best

    def load_best(self, model: nn.Module) -> dict:
        best_path = self.save_dir / f"{self.model_name}.pt"
        if not best_path.exists():
            raise FileNotFoundError(f"No best checkpoint at {best_path}")
        payload = torch.load(best_path, map_location="cpu")
        model.load_state_dict(payload["model"])
        return payload


# ─── TensorBoard writer wrapper ───────────────────────────────────────────────

class TrainLogger:
    """Thin wrapper around SummaryWriter — silently no-ops if tensorboard is absent."""

    def __init__(self, log_dir: Path):
        try:
            from torch.utils.tensorboard import SummaryWriter
            log_dir.mkdir(parents=True, exist_ok=True)
            self._writer = SummaryWriter(log_dir=str(log_dir))
            log.info("TensorBoard logs → %s  (run: tensorboard --logdir %s)", log_dir, log_dir.parent)
        except Exception:
            self._writer = None

    def scalar(self, tag: str, value: float, step: int):
        if self._writer:
            self._writer.add_scalar(tag, value, step)

    def close(self):
        if self._writer:
            self._writer.close()


# ─── Collate helper ───────────────────────────────────────────────────────────

def to_tensor_batch(batch: dict, device: torch.device) -> dict[str, torch.Tensor]:
    """Convert a collated dict-of-lists to a dict-of-LongTensors on `device`."""
    return {k: torch.tensor(v, dtype=torch.long, device=device) for k, v in batch.items()}
