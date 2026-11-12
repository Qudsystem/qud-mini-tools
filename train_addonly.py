"""Train the multiplication-free ZERO-LM (AddZeroLM)."""

import argparse
import os
import time
import torch
from torch.utils.data import Dataset, DataLoader

from config import ZeroConfig
from model.addonly_model import AddZeroLM


class SyntheticDataset(Dataset):
    def __init__(self, n=8000, seq=128, vocab=16000):
        self.n, self.seq, self.vocab = n, seq, vocab

    def __len__(self): return self.n

    def __getitem__(self, i):
        x = torch.randint(0, self.vocab, (self.seq + 1,))
        return x[:-1], x[1:]


def model_size_bytes(model: AddZeroLM) -> int:
    # ternary weights: 1.58 bit; embedding + fp scalars: 16 bit
    bits = 0
    for name, p in model.named_parameters():
        if "embed" in name:
            bits += p.numel() * 16
        else:
            bits += p.numel() * 1.58
    return bits / 8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--seq", type=int, default=128)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    cfg = ZeroConfig()
    cfg.max_seq_len = max(cfg.max_seq_len, args.seq)
    model = AddZeroLM(cfg).to(args.device)

    size = model_size_bytes(model)
    print(f"params     : {sum(p.numel() for p in model.parameters())/1e6:.3f} M")
    print(f"approx size: {size/1024/1024:.3f} MB")

    ds = SyntheticDataset(seq=args.seq, vocab=cfg.vocab_size)
    dl = DataLoader(ds, batch_size=args.batch, shuffle=True, drop_last=True)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    model.train()
    t0 = time.time()
    step = 0
    for x, y in dl:
        if step >= args.steps:
            break
        x, y = x.to(args.device), y.to(args.device)
        logits, loss = model(x, targets=y)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step % 20 == 0:
            print(f"step {step:5d}  loss {loss.item():.4f}  t={time.time()-t0:.1f}s")
        step += 1

    ckpt = os.path.join(args.out, "zero.pt")
    torch.save({"model": model.state_dict(), "config": cfg}, ckpt)
    print(f"saved {ckpt}")


if __name__ == "__main__":
    main()
