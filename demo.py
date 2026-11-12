"""Fast demo: tiny model, tiny vocab, quick training + generation."""

import torch, torch.nn.functional as F
from config import ZeroConfig
from model.transformer import build_model
from model.bitnet import replace_linear_with_bitnet

torch.manual_seed(0)

# ---- tiny config ----
cfg = ZeroConfig()
cfg.vocab_size = 64
cfg.hidden_size = 64
cfg.intermediate_size = 128
cfg.num_layers = 2
cfg.num_heads = 4
cfg.num_kv_heads = 2
cfg.head_dim = 16
cfg.max_seq_len = 32
cfg.ced_prefill_layers = 2
cfg.csa2_pattern = ("F", "U")

model = build_model(cfg)
model.blocks.apply(lambda m: replace_linear_with_bitnet(m, cfg.bitnet_eps))

print(f"tiny model: {sum(p.numel() for p in model.parameters())} params")
opt = torch.optim.AdamW(model.parameters(), lr=3e-3)

# ---- learning task: predict i+1 from i (cyclic sequence) ----
seq_len = 16
data = torch.arange(cfg.vocab_size).repeat(4)  # 256 tokens

def make_batch(bsz=4):
    starts = torch.randint(0, len(data) - seq_len - 1, (bsz,))
    x = torch.stack([data[s:s+seq_len] for s in starts])
    y = torch.stack([data[s+1:s+seq_len+1] for s in starts])
    return x, y

model.train()
for step in range(200):
    x, y = make_batch()
    logits, loss = model(x, targets=y)
    opt.zero_grad()
    loss.backward()
    opt.step()
    if step % 20 == 0:
        print(f"step {step:3d}  loss {loss.item():.4f}")

# ---- generate ----
model.eval()
prompt = torch.tensor([[1, 2, 3, 4]], dtype=torch.long)
with torch.no_grad():
    out = model.generate(prompt, max_new_tokens=12)
print("prompt    :", prompt[0].tolist())
print("generated :", out[0].tolist())
print("target    :", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
