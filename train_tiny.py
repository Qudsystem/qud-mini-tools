"""Tiny fast Shakespeare trainer - for quick readable output on CPU."""
import argparse, os, pickle, time
import torch, torch.nn.functional as F
from config import ZeroConfig
from model.transformer import build_model
from model.bitnet import replace_linear_with_bitnet


def get_batch(data, batch, seq):
    ix = torch.randint(len(data) - seq - 1, (batch,))
    x = torch.stack([data[i:i+seq] for i in ix])
    y = torch.stack([data[i+1:i+seq+1] for i in ix])
    return x, y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=800)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--seq", type=int, default=64)
    ap.add_argument("--lr", type=float, default=8e-3)
    ap.add_argument("--hidden", type=int, default=128)
    ap.add_argument("--layers", type=int, default=3)
    ap.add_argument("--heads", type=int, default=4)
    ap.add_argument("--inter", type=int, default=256)
    ap.add_argument("--out", default="out_tiny")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    with open("data.pkl", "rb") as f:
        d = pickle.load(f)
    train_data, val_data = d["train"], d["val"]
    vocab_size = len(d["stoi"])

    cfg = ZeroConfig()
    cfg.vocab_size = vocab_size
    cfg.hidden_size = args.hidden
    cfg.intermediate_size = args.inter
    cfg.num_layers = args.layers
    cfg.num_heads = args.heads
    cfg.num_kv_heads = 2
    cfg.head_dim = args.hidden // args.heads
    cfg.max_seq_len = args.seq
    cfg.ced_prefill_layers = args.layers
    cfg.csa2_pattern = ("F", "U", "R")[:args.layers]

    model = build_model(cfg)
    model.blocks.apply(lambda m: replace_linear_with_bitnet(m, cfg.bitnet_eps))
    n = sum(p.numel() for p in model.parameters())
    print(f"model: {n/1e6:.3f}M params, hidden={args.hidden}, layers={args.layers}", flush=True)

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.steps)
    model.train()
    t0 = time.time()
    best = float("inf")

    for step in range(args.steps):
        x, y = get_batch(train_data, args.batch, args.seq)
        logits, loss = model(x, targets=y)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()

        if step % 25 == 0 or step == args.steps - 1:
            model.eval()
            with torch.no_grad():
                xv, yv = get_batch(val_data, 16, args.seq)
                _, vl = model(xv, targets=yv)
            model.train()
            print(f"step {step:4d}  train {loss.item():.4f}  val {vl.item():.4f}  t={time.time()-t0:.0f}s", flush=True)
            if vl.item() < best:
                best = vl.item()
                torch.save({"model": model.state_dict(), "config": cfg,
                            "stoi": d["stoi"], "itos": d["itos"]},
                           os.path.join(args.out, "best.pt"))
    print(f"DONE best val {best:.4f}", flush=True)


if __name__ == "__main__":
    main()
