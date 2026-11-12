import torch
import torch.nn as nn
import torch.nn.functional as F

from .bitnet import BitLinear


class RMSNorm(nn.Module):
    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))
        self.eps = eps

    def forward(self, x):
        var = x.pow(2).mean(-1, keepdim=True)
        return x * torch.rsqrt(var + self.eps) * self.weight


class SwiGLU(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        h = cfg.hidden_size
        i = cfg.intermediate_size
        # BitLinear everywhere -> ternary {–1,0,+1}
        self.gate = BitLinear(h, i, bias=False, eps=cfg.bitnet_eps)
        self.up   = BitLinear(h, i, bias=False, eps=cfg.bitnet_eps)
        self.down = BitLinear(i, h, bias=False, eps=cfg.bitnet_eps)

    def forward(self, x):
        return self.down(F.silu(self.gate(x)) * self.up(x))
