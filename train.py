"""Minimal training loop for ZERO.

Uses a synthetic dataset by default so the whole pipeline is runnable without
downloading anything. Swap `SyntheticDataset` for your real corpus loader.
"""

import argparse
import os
import time
import torch
from torch.utils.data import Dataset, DataLoader

from config import ZeroConfig
from model.transformer import build_model, model_size_bytes
from model.bitnet import replace_linear_with_bitnet


class SyntheticDataset(Dataset):
    """Random token sequences — replace with your tokenized corpus."""
    def __init__(self, n=20000, seq=512, vocab=16000):
        self.n = n
        self.seq = seq
        self.vocab = vocab

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        x = torch.randint(0, self.vocab, (self.seq + 1,))
        return x[:-1], x[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--seq", type=int, default=256)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    cfg = ZeroConfig()
    cfg.max_seq_len = max(cfg.max_seq_len, args.seq)

    model = build_model(cfg, device=args.device)
    # replace all nn.Linear (except tied head) with BitLinear
    # (we do this after build so the tied weights on lm_head are preserved)
    for name, mod in model.named_modules():
        pass
    model.blocks.apply(lambda m: replace_linear_with_bitnet(m, eps=cfg.bitnet_eps))

    size = model_size_bytes(model)
    print(f"[zero] params={sum(p.numel() for p in model.parameters())/1e6:.2f}M  "
          f"approx_size={size/1024/1024:.2f} MB")

    ds = SyntheticDataset(seq=args.seq, vocab=cfg.vocab_size)
    dl = DataLoader(ds, batch_size=args.batch, shuffle=True, num_workers=0, drop_last=True)

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    model.train()
    t0 = time.time()
    step = 0
    for x, y in dl:
        if step >= args.steps:
            break
        x, y = x.to(args.device), y.to(args.device)
        logits, loss = model(x, targets=y, mode="prefill")
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step % 20 == 0:
            print(f"step {step:5d}  loss {loss.item():.4f}  "
                  f"elapsed {time.time()-t0:.1f}s")
        step += 1

    ckpt = os.path.join(args.out, "zero.pt")
    torch.save({"model": model.state_dict(), "config": cfg}, ckpt)
    print(f"[zero] saved {ckpt}")


if __name__ == "__main__":
    main()
