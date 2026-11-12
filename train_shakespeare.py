"""Train ZERO on TinyShakespeare (char-level).

Config is sized to fit the <50MB budget while training fast on CPU.
"""
import argparse, os, pickle, time
import torch, torch.nn.functional as F

from config import ZeroConfig
from model.transformer import build_model
from model.bitnet import replace_linear_with_bitnet


def get_batch(data, batch, seq, device):
    ix = torch.randint(len(data) - seq - 1, (batch,))
    x = torch.stack([data[i:i+seq] for i in ix]).to(device)
    y = torch.stack([data[i+1:i+seq+1] for i in ix]).to(device)
    return x, y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1000)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--seq", type=int, default=128)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", default="out_shakespeare")
    ap.add_argument("--hidden", type=int, default=256)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--heads", type=int, default=4)
    ap.add_argument("--inter", type=int, default=512)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    with open("data.pkl", "rb") as f:
        d = pickle.load(f)
    train_data, val_data = d["train"], d["val"]
    vocab_size = len(d["stoi"])
    itos = d["itos"]

    cfg = ZeroConfig()
    cfg.vocab_size = vocab_size
    cfg.hidden_size = args.hidden
    cfg.intermediate_size = args.inter
    cfg.num_layers = args.layers
    cfg.num_heads = args.heads
    cfg.num_kv_heads = max(1, args.heads // 2)
    cfg.head_dim = args.hidden // args.heads
    cfg.max_seq_len = 256
    cfg.ced_prefill_layers = args.layers  # keep all layers active for training
    cfg.csa2_pattern = tuple(["F"] + ["U", "R", "U"] * 10)[:args.layers]

    model = build_model(cfg, device=args.device)
    model.blocks.apply(lambda m: replace_linear_with_bitnet(m, cfg.bitnet_eps))

    n_params = sum(p.numel() for p in model.parameters())
    est_mb = n_params * 1.58 / 8 / 1024 / 1024
    print(f"model: {n_params/1e6:.3f}M params, ~{est_mb:.2f} MB (ternary)")
    print(f"vocab_size={vocab_size}, hidden={args.hidden}, layers={args.layers}")

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    model.train()
    t0 = time.time()
    best_val = float("inf")

    for step in range(args.steps):
        x, y = get_batch(train_data, args.batch, args.seq, args.device)
        logits, loss = model(x, targets=y)
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        if step % 25 == 0 or step == args.steps - 1:
            # quick val
            model.eval()
            with torch.no_grad():
                xv, yv = get_batch(val_data, args.batch, args.seq, args.device)
                _, vloss = model(xv, targets=yv)
            model.train()
            print(f"step {step:5d}  train {loss.item():.4f}  val {vloss.item():.4f}  t={time.time()-t0:.0f}s")
            if vloss.item() < best_val:
                best_val = vloss.item()
                torch.save({"model": model.state_dict(), "config": cfg,
                            "stoi": d["stoi"], "itos": itos},
                           os.path.join(args.out, "best.pt"))

    print(f"saved {args.out}/best.pt  (best val {best_val:.4f})")


if __name__ == "__main__":
    main()
