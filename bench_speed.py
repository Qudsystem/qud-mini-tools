import time, torch
torch.set_float32_matmul_precision("high")
from config import ZeroConfig
from model.transformer import build_model
from model.bitnet import replace_linear_with_bitnet, refresh_bitnet_cache

cfg = ZeroConfig()
cfg.vocab_size = 65
cfg.hidden_size = 256
cfg.intermediate_size = 512
cfg.num_layers = 4
cfg.num_heads = 4
cfg.num_kv_heads = 2
cfg.head_dim = 64
cfg.max_seq_len = 128
cfg.ced_prefill_layers = 4
cfg.csa2_pattern = ("F", "U", "R", "U")

m = build_model(cfg)
m.blocks.apply(lambda x: replace_linear_with_bitnet(x, cfg.bitnet_eps))
refresh_bitnet_cache(m)
m.train()
opt = torch.optim.AdamW(m.parameters(), lr=1e-3)

for seq, bsz in [(64, 32), (128, 32)]:
    x = torch.randint(0, 65, (bsz, seq))
    y = torch.randint(0, 65, (bsz, seq))
    # warmup
    logits, loss = m(x, targets=y)
    opt.zero_grad(set_to_none=True); loss.backward(); opt.step(); refresh_bitnet_cache(m)
    # timed
    t0 = time.time()
    for _ in range(3):
        logits, loss = m(x, targets=y)
        opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
        refresh_bitnet_cache(m)
    dt = (time.time()-t0)/3
    print(f"seq={seq} batch={bsz}: {dt*1000:.0f} ms/step", flush=True)
