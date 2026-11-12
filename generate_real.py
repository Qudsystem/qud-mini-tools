"""Generate text from a trained ZERO checkpoint (char-level)."""
import argparse, pickle, torch
from config import ZeroConfig
from model.transformer import build_model
from model.bitnet import replace_linear_with_bitnet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="out_shakespeare/best.pt")
    ap.add_argument("--prompt", default="ROMEO: ")
    ap.add_argument("--tokens", type=int, default=300)
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--top_k", type=int, default=20)
    args = ap.parse_args()

    blob = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    cfg = blob["config"]
    itos = blob["itos"]
    stoi = blob["stoi"]

    model = build_model(cfg, device="cpu")
    model.blocks.apply(lambda m: replace_linear_with_bitnet(m, cfg.bitnet_eps))
    model.load_state_dict(blob["model"], strict=False)
    model.eval()

    # encode prompt (skip unseen chars)
    ids = [stoi[c] for c in args.prompt if c in stoi]
    if not ids:
        ids = [0]
    x = torch.tensor([ids], dtype=torch.long)

    with torch.no_grad():
        out = model.generate(x, max_new_tokens=args.tokens,
                             temperature=args.temp, top_k=args.top_k)
    text = "".join(itos.get(int(t), "?") for t in out[0].tolist())
    print("=" * 60)
    print(text)
    print("=" * 60)


if __name__ == "__main__":
    main()
