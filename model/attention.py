"""
Attention with CSA2 pattern (Full / Reindex / Reuse), SWA, and additive-only
score computation on the ternary-projected QK.

The L1 (Manhattan) distance is computed with torch.cdist(p=1), which uses
optimized C++ kernels and returns (B,H,T,S) directly — no 5D intermediate.
This is the multiply-free score (additions + subtractions only).
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

from .bitnet import BitLinear
from .kv_cache import KVCache


def rope(x, positions, theta=10000.0):
    B, H, T, D = x.shape
    half = D // 2
    freqs = 1.0 / (theta ** (torch.arange(0, half, device=x.device).float() / half))
    pos = positions[:, -T:].float()
    angles = pos[:, :, None] * freqs[None, None, :]
    cos = angles.cos()[:, None, :, :]
    sin = angles.sin()[:, None, :, :]
    x1, x2 = x[..., :half], x[..., half:]
    return torch.cat([x1 * cos - x2 * sin, x1 * sin + x2 * cos], dim=-1)


class CSA2Attention(nn.Module):
    def __init__(self, cfg, layer_idx: int, pattern_char: str):
        super().__init__()
        self.cfg = cfg
        self.layer_idx = layer_idx
        self.pattern_char = pattern_char

        self.q_proj = BitLinear(cfg.hidden_size, cfg.num_heads * cfg.head_dim, bias=False, eps=cfg.bitnet_eps)
        self.k_proj = BitLinear(cfg.hidden_size, cfg.num_kv_heads * cfg.head_dim, bias=False, eps=cfg.bitnet_eps)
        self.v_proj = BitLinear(cfg.hidden_size, cfg.num_kv_heads * cfg.head_dim, bias=False, eps=cfg.bitnet_eps)
        self.o_proj = BitLinear(cfg.num_heads * cfg.head_dim, cfg.hidden_size, bias=False, eps=cfg.bitnet_eps)
        self.n_rep = cfg.num_heads // cfg.num_kv_heads

    def _compute_kv(self, x, positions):
        B, T, _ = x.shape
        k = self.k_proj(x).view(B, T, self.cfg.num_kv_heads, self.cfg.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, T, self.cfg.num_kv_heads, self.cfg.head_dim).transpose(1, 2)
        k = rope(k, positions, self.cfg.rope_theta)
        return k, v

    def forward(self, x, positions, cache=None, shared_kv=None):
        B, T, _ = x.shape
        q = self.q_proj(x).view(B, T, self.cfg.num_heads, self.cfg.head_dim).transpose(1, 2)
        q = rope(q, positions, self.cfg.rope_theta)

        if self.pattern_char == "F" or shared_kv is None:
            k, v = self._compute_kv(x, positions)
        else:
            k, v = shared_kv

        if cache is not None and self.pattern_char == "F":
            cache.append(k, v)
            k_c, v_c = cache.get_kv()
            if k_c is not None:
                w = self.cfg.swa_window
                k, v = k_c[:, :, -w:, :], v_c[:, :, -w:, :]

        reuse_kv = (k, v)

        k_e = k.repeat_interleave(self.n_rep, dim=1)
        v_e = v.repeat_interleave(self.n_rep, dim=1)

        S = k_e.shape[2]

        # ---- multiply-free L1 attention via optimized cdist ----
        # cdist(q, k, p=1) -> (B, H, T, S), uses only adds/subs internally.
        dist = torch.cdist(q, k_e, p=1)                   # (B, H, T, S)
        score = -dist / math.sqrt(self.cfg.head_dim)

        pos_full = positions
        if pos_full.shape[1] < S:
            pos_full = torch.arange(S, device=x.device).unsqueeze(0).expand(B, S)
        k_pos = pos_full[:, -S:]
        q_pos = pos_full[:, -T:]
        causal = k_pos[:, None, :] <= q_pos[:, :, None]
        window = (q_pos[:, :, None] - k_pos[:, None, :]) <= self.cfg.swa_window
        allowed = causal & window
        mask = ~allowed[:, None, :, :].expand(B, self.cfg.num_heads, T, S)
        score = score.masked_fill(mask, float("-inf"))

        attn = F.softmax(score, dim=-1)
        y = torch.einsum("bhts,bhsd->bhtd", attn, v_e)
        y = y.transpose(1, 2).contiguous().view(B, T, self.cfg.hidden_size)
        return self.o_proj(y), reuse_kv
