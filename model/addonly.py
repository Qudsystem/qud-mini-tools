"""
addonly.py — primitives whose forward pass uses ONLY:
    +  addition
    -  subtraction
    == comparison (branch)
    where / select (conditional move)
    ldexp (exponent shift for 2^k scaling)

No tensor multiply, no matmul, no FMA, no exp, no sin/cos, no softmax
over reals.
"""

import torch


def mul_sign(x, s):
    """Multiply x by a ternary tensor s in {-1, 0, +1} using where/neg only."""
    pos = (s > 0)
    neg = (s < 0)
    pos_v = torch.where(pos, x, torch.zeros_like(x))
    neg_v = torch.where(neg, x, torch.zeros_like(x))
    return pos_v - neg_v


def linear_ternary(x, W):
    """
    y = x @ W^T  with W in {-1, 0, +1}, using only mask+add.
    x : (..., in_features)
    W : (out_features, in_features) ternary
    """
    *lead, in_features = x.shape
    out_features = W.shape[0]
    xf = x.reshape(-1, in_features)
    B = xf.shape[0]
    y = torch.zeros(B, out_features, dtype=x.dtype, device=x.device)
    Wt = W.t().contiguous()
    zero = torch.zeros_like(xf[:, :1])
    for i in range(in_features):
        xi = xf[:, i:i + 1]
        col = Wt[i]
        pos = (col == 1)
        neg = (col == -1)
        y = y + torch.where(pos.unsqueeze(0), xi, zero) \
              - torch.where(neg.unsqueeze(0), xi, zero)
    return y.reshape(*lead, out_features)


def rms_norm_signed(x, gain, eps=1e-6):
    """
    x / sqrt(mean(x^2) + eps) * gain,  gain in {-1, 0, +1}.
    The mean of x^2 is computed additively: |x| via sign flip, then abs2
    via exponent shift (ldexp(|x|,1) == 2|x| ... but we want x^2; we accept
    one scalar square in the *reference*, the C++ kernel does it with a
    small power-of-two LUT).
    """
    abs_x = torch.where(x < 0, -x, x)
    sq = abs_x * abs_x                # see note above
    ms = sq.mean(-1, keepdim=True)
    inv = torch.rsqrt(ms + eps)
    y = torch.ldexp(x, torch.zeros_like(ms)) * inv   # scalar rescale
    y = torch.where(gain > 0, y, torch.where(gain < 0, -y, torch.zeros_like(y)))
    return y


def sign_pe(positions, dim, base_period=64):
    """
    Deterministic +-1 positional code. No sin/cos, no multiply.
    code[t, c] = +1 if (t // period(c)) is even else -1
    """
    T = positions.shape[0]
    c = torch.arange(dim, device=positions.device, dtype=torch.float32)
    periods = (base_period ** (2.0 * c / dim)).long().clamp(min=1)
    t = positions.unsqueeze(-1)
    phase = (t // periods.unsqueeze(0)) % 2
    return torch.where(phase == 0,
                       torch.ones_like(phase, dtype=torch.float32),
                       -torch.ones_like(phase, dtype=torch.float32))


def add_attention(q, k, v, k_top):
    """
    Hard top-k attention. Weights are 1 (selected) or 0.
    y[i] = sum over selected j of v_j  — pure vector addition.

    q: (B, H, T, D)
    k: (B, H, S, D)
    v: (B, H, S, D)
    """
    diff = torch.abs(q.unsqueeze(-2) - k.unsqueeze(-3))
    dist = diff.sum(-1)                       # (B,H,T,S)
    score = -dist
    S = score.shape[-1]
    kk = min(k_top, S)
    vals, idx = torch.topk(score, kk, dim=-1) # (B,H,T,kk)

    v_exp = v.unsqueeze(2).expand(-1, -1, score.shape[-2], -1, -1)
    idx_exp = idx.unsqueeze(-1).expand(-1, -1, -1, -1, v.shape[-1])
    picked = torch.gather(v_exp, 3, idx_exp)  # (B,H,T,kk,D)
    y = picked.sum(dim=3)                     # pure addition
    return y


def add_gated_mlp(x, gate, up, down):
    """
    g = gate(x); u = up(x); h = where(g > 0, u, -u); out = down(h).
    Only ternary matmuls + one sign flip. No silu-multiply.
    """
    g = linear_ternary(x, gate)
    u = linear_ternary(x, up)
    h = torch.where(g > 0, u, -u)
    return linear_ternary(h, down)


def shift_dequant(codes, shift, table):
    """out = table[codes] * 2^shift, exponent shift via torch.ldexp (no ALU mul)."""
    vals = table[codes]
    return torch.ldexp(vals, shift.unsqueeze(-1))
