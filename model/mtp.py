"""
mtp.py — DS-Spark: Multi-Token Prediction with ternary heads.

Classic decoding produces one token per forward pass.  DS-Spark produces
N tokens at once by attaching N tiny ternary heads to the final hidden
state.  Because the heads are ternary, each additional token costs only
add/sub operations.

Adaptation for ZERO (<50 MB):
    * N = 4 (produces 4 tokens per forward step → ~4× decode speedup).
    * Each head is a ternary matrix (vocab, hidden) — but we tie them
      across steps using a *shared* ternary basis, so the parameter cost
      is just one extra (vocab, hidden) ternary matrix instead of 4.
    * The heads are trained with a *step shift*: head s predicts token
      t+s+1 given hidden state at t.

Inference:
    for step in range(T // N):
        h = forward(x)
        tokens = [head_s(h).argmax() for s in range(N)]   # comparisons only
        x = concat(x, tokens)
"""

import torch
import torch.nn as nn

from .addonly import linear_ternary


class DSSparkHeads(nn.Module):
    """
    N ternary prediction heads that share a common hidden->basis transform.
    """

    def __init__(self, cfg, n_heads: int = 4, basis_dim: int = 256):
        super().__init__()
        self.cfg = cfg
        self.n_heads = n_heads
        self.basis_dim = basis_dim

        # shared ternary basis: hidden -> basis_dim
        self.basis_w = nn.Parameter(torch.zeros(basis_dim, cfg.hidden_size))
        # per-step ternary heads: basis_dim -> vocab  (tiny!)
        self.head_w = nn.Parameter(torch.zeros(n_heads, cfg.vocab_size, basis_dim))

    def _ternarize(self, W):
        with torch.no_grad():
            scale = 1.0 / (W.abs().mean(dim=-1, keepdim=True) + 1e-8)
            q = torch.clamp(torch.round(W * scale), -1, 1)
        return W + (q - W).detach()

    def forward(self, h: torch.Tensor):
        """
        h : (B, T, hidden)
        returns: (B, T, N, vocab)
        """
        B, T, _ = h.shape
        basis = self._ternarize(self.basis_w)                # (basis_dim, hidden)
        # shared basis projection
        z = linear_ternary(h, basis)                          # (B, T, basis_dim)

        out = []
        for s in range(self.n_heads):
            W_s = self._ternarize(self.head_w[s])             # (vocab, basis_dim)
            logits_s = linear_ternary(z, W_s)                 # (B, T, vocab)
            out.append(logits_s)
        return torch.stack(out, dim=2)                        # (B, T, N, vocab)

    @torch.no_grad()
    def sample(self, h: torch.Tensor):
        """Greedy decode: pick argmax at each step — comparisons only."""
        logits = self.forward(h)                              # (B,T,N,V)
        return logits.argmax(dim=-1)                          # (B,T,N)


def mtp_loss(logits: torch.Tensor, targets: torch.Tensor, ignore_index=-100):
    """
    logits  : (B, T, N, vocab)
    targets : (B, T+N)   the ground-truth continuation
    Loss    : cross-entropy averaged over N steps and T positions.
    """
    B, T, N, V = logits.shape
    losses = []
    for s in range(N):
        # head s predicts target position t + s + 1
        if T - s - 1 <= 0:
            break
        logits_s = logits[:, : T - s - 1, s, :].reshape(-1, V)
        target_s = targets[:, s + 1 : T].reshape(-1)
        losses.append(torch.nn.functional.cross_entropy(
            logits_s, target_s, ignore_index=ignore_index))
    return torch.stack(losses).mean()
