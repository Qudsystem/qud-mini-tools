"""Self-test: instantiate ZERO, print size, run a forward + one decode step."""

import torch
from config import ZeroConfig
from model.transformer import build_model, model_size_bytes
from model.bitnet import replace_linear_with_bitnet


def main():
    cfg = ZeroConfig()
    model = build_model(cfg, device="cpu")
    model.blocks.apply(lambda m: replace_linear_with_bitnet(m, eps=cfg.bitnet_eps))
    model.eval()

    n_params = sum(p.numel() for p in model.parameters())
    size_bytes = model_size_bytes(model)
    print(f"params     : {n_params/1e6:.3f} M")
    print(f"approx size: {size_bytes/1024/1024:.3f} MB  (target < 50 MB)")

    # forward pass
    x = torch.randint(0, cfg.vocab_size, (1, 32))
    cache = model.make_cache(1, "cpu")
    logits, _ = model(x, mode="prefill", cache_list=cache)
    print("prefill logits:", tuple(logits.shape))

    # one decode step
    nxt = torch.randint(0, cfg.vocab_size, (1, 1))
    pos = torch.tensor([[32]], dtype=torch.long)
    logits2, _ = model(nxt, mode="decode", cache_list=cache, positions=pos)
    print("decode logits :", tuple(logits2.shape))

    # KV cache footprint for the 33 generated tokens
    total_kv_bytes = sum(c.size_bytes() for c in cache)
    print(f"KV bytes     : {total_kv_bytes}")
    print(f"KV B/token   : {total_kv_bytes / 33:.1f}")

    assert size_bytes / 1024 / 1024 < 50.0, "model exceeds 50 MB budget"
    print("OK — all checks passed.")


if __name__ == "__main__":
    main()
