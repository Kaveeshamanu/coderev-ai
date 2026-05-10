"""
Reviewer Model Training — Dual-Encoder Transformer
----------------------------------------------------
Trains the DualEncoderTransformer on
  (abstracted_old_hunk + comment) → abstracted_new_hunk  triplets.

Usage (from backend/ with venv active):
    python training/train_reviewer.py
    python training/train_reviewer.py --epochs 80 --batch-size 32 --lr 3e-4
    python training/train_reviewer.py --resume

Output:
    models/weights/dual_encoder.pt            ← best checkpoint
    models/weights/dual_encoder_last.pt       ← rolling last
    models/weights/dual_encoder_config.json   ← ModelConfig used
    runs/reviewer/                            ← TensorBoard logs
"""

import argparse
import logging
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.transformer import DualEncoderTransformer, ModelConfig
from preprocessing.build_splits import CodeReviewDataset, collate_fn
from preprocessing.config import PAD_TOKEN_ID, BOS_TOKEN_ID, EOS_TOKEN_ID
from preprocessing.train_tokenizer import load_tokenizer, decode
from training.trainer import (
    LabelSmoothedCrossEntropy, WarmupCosineScheduler,
    CheckpointManager, TrainLogger, to_tensor_batch,
)
from training.evaluate import compute_all, print_metrics

log = logging.getLogger(__name__)

WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "models" / "weights"
RUNS_DIR    = Path(__file__).resolve().parent.parent / "runs" / "reviewer"


# ─── Argument parser ──────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Train DualEncoderTransformer")
    p.add_argument("--epochs",       type=int,   default=60)
    p.add_argument("--batch-size",   type=int,   default=32)
    p.add_argument("--lr",           type=float, default=1e-4)
    p.add_argument("--d-model",      type=int,   default=256)
    p.add_argument("--n-heads",      type=int,   default=8)
    p.add_argument("--enc-layers",   type=int,   default=4)
    p.add_argument("--dec-layers",   type=int,   default=4)
    p.add_argument("--d-ff",         type=int,   default=1024)
    p.add_argument("--dropout",      type=float, default=0.1)
    p.add_argument("--warmup-steps", type=int,   default=200)
    p.add_argument("--patience",     type=int,   default=12)
    p.add_argument("--resume",       action="store_true")
    p.add_argument("--device",       default="auto",
                   choices=["auto", "cpu", "cuda", "mps"])
    return p.parse_args()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    device = _pick_device(args.device)
    log.info("Device: %s", device)

    # ── Tokenizer ─────────────────────────────────────────────────────────────
    tokenizer  = load_tokenizer()
    vocab_size = len(tokenizer.get_vocab())
    log.info("Vocabulary size: %d", vocab_size)

    # ── Datasets & loaders ────────────────────────────────────────────────────
    train_ds = CodeReviewDataset(split="train", mode="reviewer")
    val_ds   = CodeReviewDataset(split="val",   mode="reviewer")
    log.info("Train: %d  Val: %d", len(train_ds), len(val_ds))

    def _collate(batch):
        batch = [
            {
                "code_ids":    b["code_ids"],
                "comment_ids": b["comment_ids"],
                "tgt_ids":     b["tgt_ids"],
            }
            for b in batch
        ]
        return collate_fn(batch, pad_id=PAD_TOKEN_ID)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size,
                              shuffle=True,  collate_fn=_collate, drop_last=True)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size,
                              shuffle=False, collate_fn=_collate)

    # ── Model ─────────────────────────────────────────────────────────────────
    config = ModelConfig(
        vocab_size         = vocab_size,
        d_model            = args.d_model,
        n_heads            = args.n_heads,
        num_encoder_layers = args.enc_layers,
        num_decoder_layers = args.dec_layers,
        d_ff               = args.d_ff,
        dropout            = args.dropout,
        pad_token_id       = PAD_TOKEN_ID,
        bos_token_id       = BOS_TOKEN_ID,
        eos_token_id       = EOS_TOKEN_ID,
    )
    model = DualEncoderTransformer(config).to(device)
    _log_params(model)

    # ── Loss, optimiser, scheduler ────────────────────────────────────────────
    criterion   = LabelSmoothedCrossEntropy(vocab_size, PAD_TOKEN_ID, smoothing=0.1)
    optimizer   = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    total_steps = args.epochs * len(train_loader)
    scheduler   = WarmupCosineScheduler(optimizer, args.warmup_steps, total_steps, args.lr)

    # ── Checkpoint & logger ───────────────────────────────────────────────────
    ckpt    = CheckpointManager(WEIGHTS_DIR, "dual_encoder")
    tlogger = TrainLogger(RUNS_DIR)

    start_epoch = 0
    if args.resume:
        start_epoch = _maybe_resume(model, optimizer, ckpt)

    # ── Training loop ─────────────────────────────────────────────────────────
    global_step = start_epoch * len(train_loader)
    no_improve  = 0

    log.info("Starting training for %d epochs…", args.epochs)
    for epoch in range(start_epoch, args.epochs):
        t0 = time.time()

        train_loss = _train_epoch(
            model, train_loader, criterion, optimizer, scheduler,
            device, global_step, tlogger,
        )
        global_step += len(train_loader)

        val_loss = _eval_epoch(model, val_loader, criterion, device)

        elapsed = time.time() - t0
        log.info(
            "Epoch %3d/%d  train_loss=%.4f  val_loss=%.4f  lr=%.2e  (%.1fs)",
            epoch + 1, args.epochs, train_loss, val_loss,
            scheduler.get_lr(), elapsed,
        )

        tlogger.scalar("loss/train", train_loss, epoch)
        tlogger.scalar("loss/val",   val_loss,   epoch)
        tlogger.scalar("lr",         scheduler.get_lr(), epoch)

        is_best = ckpt.save(model, config, epoch, val_loss)

        if not is_best:
            no_improve += 1
        else:
            no_improve = 0

        if no_improve >= args.patience:
            log.info("No improvement for %d epochs — stopping early.", args.patience)
            break

    # ── Final evaluation on test set ──────────────────────────────────────────
    log.info("\n─── Test Set Evaluation ───────────────────────────────")
    ckpt.load_best(model)
    test_ds     = CodeReviewDataset(split="test", mode="reviewer")
    test_loader = DataLoader(test_ds, batch_size=args.batch_size,
                             shuffle=False, collate_fn=_collate)

    metrics = _evaluate_metrics(model, test_loader, tokenizer, config, device)
    print_metrics(metrics, prefix="test")
    tlogger.scalar("test/bleu4",       metrics["bleu4"],       0)
    tlogger.scalar("test/lev_sim",     metrics["lev_sim"],     0)
    tlogger.scalar("test/exact_match", metrics["exact_match"], 0)

    tlogger.close()
    log.info("Training complete. Best model → %s/dual_encoder.pt", WEIGHTS_DIR)


# ─── Epoch helpers ────────────────────────────────────────────────────────────

def _train_epoch(model, loader, criterion, optimizer, scheduler,
                 device, global_step, tlogger) -> float:
    model.train()
    total_loss = 0.0

    for batch in loader:
        batch       = to_tensor_batch(batch, device)
        code_ids    = batch["code_ids"]
        comment_ids = batch["comment_ids"]
        tgt_full    = batch["tgt_ids"]
        tgt_in      = tgt_full[:, :-1]
        tgt_out     = tgt_full[:, 1:]

        code_pad    = (code_ids    == PAD_TOKEN_ID)
        comment_pad = (comment_ids == PAD_TOKEN_ID)
        tgt_len     = tgt_in.size(1)
        tgt_mask    = nn.Transformer.generate_square_subsequent_mask(
            tgt_len, device=device
        )

        logits = model(
            code_ids, comment_ids, tgt_in,
            code_padding_mask    = code_pad,
            comment_padding_mask = comment_pad,
            tgt_mask             = tgt_mask,
        )

        loss = criterion(logits, tgt_out)
        optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()

        total_loss += loss.item()
        tlogger.scalar("loss/train_step", loss.item(), global_step)
        global_step += 1

    return total_loss / max(len(loader), 1)


@torch.no_grad()
def _eval_epoch(model, loader, criterion, device) -> float:
    model.eval()
    total_loss = 0.0

    for batch in loader:
        batch       = to_tensor_batch(batch, device)
        code_ids    = batch["code_ids"]
        comment_ids = batch["comment_ids"]
        tgt_full    = batch["tgt_ids"]
        tgt_in      = tgt_full[:, :-1]
        tgt_out     = tgt_full[:, 1:]

        code_pad    = (code_ids    == PAD_TOKEN_ID)
        comment_pad = (comment_ids == PAD_TOKEN_ID)
        tgt_len     = tgt_in.size(1)
        tgt_mask    = nn.Transformer.generate_square_subsequent_mask(
            tgt_len, device=device
        )

        logits = model(
            code_ids, comment_ids, tgt_in,
            code_padding_mask    = code_pad,
            comment_padding_mask = comment_pad,
            tgt_mask             = tgt_mask,
        )
        total_loss += criterion(logits, tgt_out).item()

    return total_loss / max(len(loader), 1)


@torch.no_grad()
def _evaluate_metrics(model, loader, tokenizer, config, device) -> dict:
    model.eval()
    refs, hyps = [], []

    for batch in loader:
        batch       = to_tensor_batch(batch, device)
        code_ids    = batch["code_ids"]
        comment_ids = batch["comment_ids"]
        tgt         = batch["tgt_ids"]

        for i in range(code_ids.size(0)):
            code_i    = code_ids[i].unsqueeze(0)
            comment_i = comment_ids[i].unsqueeze(0)
            beams     = model.generate(code_i, comment_i, num_beams=1)
            pred_ids  = beams[0][0] if beams else []

            refs.append(decode(tokenizer, tgt[i].tolist()))
            hyps.append(decode(tokenizer, pred_ids))

    return compute_all(refs, hyps)


# ─── Misc helpers ─────────────────────────────────────────────────────────────

def _pick_device(choice: str) -> torch.device:
    if choice == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        # MPS skipped — several transformer attention ops are not yet
        # supported on Apple Silicon (aten::_nested_tensor_from_mask_left_aligned)
        return torch.device("cpu")
    return torch.device(choice)


def _log_params(model: nn.Module):
    total     = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log.info("Parameters: %s total  /  %s trainable",
             f"{total:,}", f"{trainable:,}")


def _maybe_resume(model, optimizer, ckpt: CheckpointManager) -> int:
    last = WEIGHTS_DIR / "dual_encoder_last.pt"
    if last.exists():
        payload = torch.load(last, map_location="cpu")
        model.load_state_dict(payload["model"])
        start = payload.get("epoch", 0) + 1
        log.info("Resumed from epoch %d  (val_loss=%.4f)", start - 1, payload["val_loss"])
        return start
    log.info("No checkpoint found — starting from scratch.")
    return 0


if __name__ == "__main__":
    main()
