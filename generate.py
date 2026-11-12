"""Sample from a trained ZERO checkpoint."""

import argparse
import torch

from config import ZeroConfig
from model.transformer import build_model, ZeroLM
from model.bitnet import replace_linear_with_bitnet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="out/zero.pt")
    ap.add_argument("--prompt", default="Once upon a time")
    ap.add_argument("--tokens", type=int, default=100)
    ap.add_argument("--temp", type=float, default=0.9)
    ap.add_argument("--top_k", type=int, default=40)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    blob = torch.load(args.ckpt, map_location=args.device, weights_only=False)
    cfg = blob["config"]
    model = build_model(cfg, device=args.device)
    model.blocks.apply(lambda m: replace_linear_with_bitnet(m, eps=cfg.bitnet_eps))
    model.load_state_dict(blob["model"], strict=False)
    model.eval()

    ids = torch.tensor([[b % cfg.vocab_size for b in args.prompt.encode("utf-8")]],
                       dtype=torch.long, device=args.device)

    out = model.generate(ids, max_new_tokens=args.tokens,
                         temperature=args.temp, top_k=args.top_k)
    tail = out[0, ids.shape[1]:].tolist()
    text = bytes([t % 256 for t in tail]).decode("utf-8", errors="ignore")
    print("PROMPT :", args.prompt)
    print("OUTPUT :", text)


if __name__ == "__main__":
    main()
