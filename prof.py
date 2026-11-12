import torch, time
from config import ZeroConfig
from model.transformer import build_model
from model.bitnet import replace_linear_with_bitnet

cfg = ZeroConfig()
cfg.vocab_size = 65
cfg.hidden_size = 256
cfg.intermediate_size = 512
cfg.num_layers = 4
cfg.num_heads = 4
cfg.num_kv_heads = 2
cfg.head_dim = 64
cfg.max_seq_len = 256
cfg.ced_prefill_layers = 4
cfg.csa2_pattern = ("F","U","R","U")

m = build_model(cfg)
m.blocks.apply(lambda x: replace_linear_with_bitnet(x, cfg.bitnet_eps))
m.train()

x = torch.randint(0, 65, (16, 64))
y = torch.randint(0, 65, (16, 64))
opt = torch.optim.AdamW(m.parameters(), lr=1e-3)

# profile
for seq in [64, 128]:
    x = torch.randint(0, 65, (16, seq))
    y = torch.randint(0, 65, (16, seq))
    t0 = time.time()
    for _ in range(3):
        logits, loss = m(x, targets=y)
        opt.zero_grad(); loss.backward(); opt.step()
    dt = (time.time()-t0)/3
    print(f"seq={seq}: {dt:.2f} s/step")
