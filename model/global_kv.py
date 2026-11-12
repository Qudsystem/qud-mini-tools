"""
global_kv.py — Explicit Global KV Cache produced by the Encoder half
and *borrowed* by the Decoder half (video 07:18, 08:21).

The classic transformer builds a KV cache in EVERY layer.  In the
encoder-decoder split, only the *last encoder layer* builds the Global
KV Cache once; every decoder layer reads from that single buffer.

Combined with CSA2:
    F (Full)    → the encoder layer builds the Global KV Cache here.
    R (Reindex) → the decoder layer reuses the Global KV Cache as-is but
                  also learns a per-token "route" that reorders it.
    U (Reuse)   → the decoder layer borrows both the Global KV Cache and
                  the route from the nearest previous layer.

The Global KV Cache is stored in FP4 (E2M1) via TurboQuant, so the total
footprint stays at ~890 bytes/token as in the paper.
"""

import torch
import torch.nn as nn

from .turboquant import FP4KV


class GlobalKVCache:
    """
    Persistent, single-copy KV buffer shared by the whole decoder stack.

    Layout:
        * k_codes / v_codes  : int8 codes (E2M1, 4 bits packed as uint8)
        * k_scale / v_scale  : fp32 per-16-channel scales
        * routes[layer_id]   : optional int32 permutation learned by an R layer
    """

    def __init__(self, cfg, device="cpu"):
        self.cfg = cfg
        self.device = device
        self.fp4 = FP4KV(block=16, device=device)

        # storage (populated once by the F layer)
        self.k_codes = None
        self.k_scale = None
        self.v_codes = None
        self.v_scale = None

        # optional "route" (index permutation) created by R layers
        self.routes = {}

    # ------------------------------------------------------------------
    def write(self, k: torch.Tensor, v: torch.Tensor):
        """Called exactly ONCE by the F (Full) encoder layer."""
        self.k_codes, self.k_scale = self.fp4.quantize(k.contiguous())
        self.v_codes, self.v_scale = self.fp4.quantize(v.contiguous())

    def read(self):
        """Return (k, v) in fp16-ish precision. Called by every decoder layer."""
        if self.k_codes is None:
            return None, None
        k = self.fp4.dequantize(self.k_codes, self.k_scale)
        v = self.fp4.dequantize(self.v_codes, self.v_scale)
        return k, v

    # ------------------------------------------------------------------
    def set_route(self, layer_idx: int, route: torch.Tensor):
        """An R layer stores its reordering here (int32 permutation)."""
        self.routes[layer_idx] = route.to(torch.int32)

    def get_route(self, layer_idx: int):
        return self.routes.get(layer_idx, None)

    # ------------------------------------------------------------------
    def size_bytes(self) -> int:
        b = 0
        if self.k_codes is not None:
            b += self.k_codes.numel() // 2   # 4-bit packed
            b += self.v_codes.numel() // 2
            b += self.k_scale.numel() * 4
            b += self.v_scale.numel() * 4
        for r in self.routes.values():
            b += r.numel() * 4
        return b

    def bytes_per_token(self, seq_len: int) -> float:
        if seq_len == 0:
            return 0.0
        return self.size_bytes() / seq_len


class GlobalKVBuilder(nn.Module):
    """
    A tiny additive head that produces the F layer's Global KV Cache.

    We wrap this around the existing ternary K/V projections so that the
    Encoder half only writes to GlobalKVCache once (regardless of how many
    encoder layers there are).
    """

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.gkv = None

    def attach(self, gkv: GlobalKVCache):
        self.gkv = gkv

    @torch.no_grad()
    def finalize(self, k: torch.Tensor, v: torch.Tensor):
        """Write K, V once. After this, decoder layers only borrow."""
        assert self.gkv is not None, "GlobalKVBuilder.attach() first"
        self.gkv.write(k, v)
