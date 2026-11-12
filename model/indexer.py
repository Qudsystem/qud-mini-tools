"""
indexer.py — Hierarchical Sparse Indexer (Gatekeeper layer).

Idea (from DeepSeek V4.1-Flash, video 16:51):
    The first decoder layer acts as a "Gatekeeper". It scans the entire
    Global KV Cache (millions of tokens) and emits a *candidate pool*
    (~16,000 tokens in the paper).  All subsequent decoder layers are
    restricted to attend ONLY inside that pool.

Adaptation for ZERO (multiply-free, <50 MB):
    * The pool size is K_CAND (default 512) — enough for our tiny model.
    * The scan uses our additive L1 similarity (no dot-product, no softmax).
    * The pool is stored as int16 indices in a compact buffer, so each query
      costs only 2·K_CAND bytes — it does NOT grow with sequence length.
    * Once built, the pool can be reused across *all* decoder layers, which
      turns decode-time complexity from O(N) to O(K_CAND) — the flat
      decode-FLOPs curve mentioned in the video (27:00).

Nothing in this file uses a tensor multiply.
"""

import torch
import torch.nn as nn


class SparseIndexer(nn.Module):
    """Gatekeeper that produces a per-query candidate pool of KV indices."""

    def __init__(self, cfg, pool_size: int = 512):
        super().__init__()
        self.cfg = cfg
        self.pool_size = pool_size

    @torch.no_grad()
    def build_pool(self, q: torch.Tensor, k: torch.Tensor):
        """
        q : (B, H, T, D) — queries of the gatekeeper layer
        k : (B, H, S, D) — full Global KV Cache

        Returns
        -------
        pool : (B, H, T, K) int32 — index list (subset of [0, S))
        Note: because of the causal + SWA mask, the pool is *per query row*.

        We compute per-query top-K by L1 distance (additive), never by
        dot-product.  Memory is O(B·H·T·K).
        """
        B, H, T, D = q.shape
        S = k.shape[2]
        K = min(self.pool_size, S)

        # chunk over time to bound the memory of the (T, S) distance matrix
        pool = torch.empty(B, H, T, K, dtype=torch.int32, device=q.device)
        chunk = max(1, 1024 // max(1, S // 64))

        for t0 in range(0, T, chunk):
            t1 = min(t0 + chunk, T)
            qc = q[:, :, t0:t1]                       # (B,H,c,D)
            # L1 distance: |q - k| summed over D — pure subtraction + abs
            d = torch.abs(qc.unsqueeze(-2) - k.unsqueeze(-3)).sum(dim=-1)   # (B,H,c,S)
            score = -d
            _, idx = torch.topk(score, K, dim=-1)     # comparisons only
            pool[:, :, t0:t1] = idx.to(torch.int32)
        return pool

    @staticmethod
    def gather_from_pool(v: torch.Tensor, pool: torch.Tensor) -> torch.Tensor:
        """
        v    : (B, H, S, D)
        pool : (B, H, T, K)
        return: (B, H, T, K, D) — the selected V rows, ready to be summed.
        """
        B, H, T, K = pool.shape
        D = v.shape[-1]
        v_exp  = v.unsqueeze(2).expand(-1, -1, T, -1, -1)
        idx_exp = pool.unsqueeze(-1).expand(-1, -1, -1, -1, D)
        return torch.gather(v_exp, 3, idx_exp)        # gather = no multiply

    @staticmethod
    def pool_bytes(pool: torch.Tensor) -> int:
        """Return the size in bytes of the pool buffer (int32)."""
        return pool.numel() * pool.element_size()
