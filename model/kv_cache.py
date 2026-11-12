"""
KV cache with three storage tiers:
  * SWA tail   — last `window` tokens kept in fp16 (for exact local attention).
  * FP4 main   — older tokens stored in E2M1 (DeepSeek V4.1-Flash layout).
  * Bounded replay — on cache loss, replay only the last `replay` tokens.
"""

import torch
from .turboquant import FP4KV


class KVCache:
    def __init__(self, num_kv_heads, head_dim, window=128, replay=128,
                 device="cpu", dtype=torch.float32):
        self.num_kv_heads = num_kv_heads
        self.head_dim = head_dim
        self.window = window
        self.replay = replay
        self.device = device
        self.dtype = dtype
        self.fp4 = FP4KV(block=16, device=device)

        # tail (fp16) — bounded by window
        self.k_tail = None
        self.v_tail = None
        # cold storage (fp4 codes + scales)
        self.k_codes = None
        self.k_scales = None
        self.v_codes = None
        self.v_scales = None

    def append(self, k_new, v_new):
        """k_new/v_new: (B, H_kv, T_new, D). Move old tail -> fp4, keep tail."""
        if self.k_tail is None:
            self.k_tail, self.v_tail = k_new, v_new
        else:
            self.k_tail = torch.cat([self.k_tail, k_new], dim=-2)
            self.v_tail = torch.cat([self.v_tail, v_new], dim=-2)

        # spill to fp4
        if self.k_tail.shape[-2] > self.window:
            spill = self.k_tail.shape[-2] - self.window
            k_spill = self.k_tail[..., :spill, :]
            v_spill = self.v_tail[..., :spill, :]
            self.k_tail = self.k_tail[..., spill:, :]
            self.v_tail = self.v_tail[..., spill:, :]

            kc, ks = self.fp4.quantize(k_spill.contiguous())
            vc, vs = self.fp4.quantize(v_spill.contiguous())
            if self.k_codes is None:
                self.k_codes, self.k_scales = kc, ks
                self.v_codes, self.v_scales = vc, vs
            else:
                # codes are (B, H, T, nb, block) -> cat on T (dim=-3)
                self.k_codes = torch.cat([self.k_codes, kc], dim=-3)
                self.v_codes = torch.cat([self.v_codes, vc], dim=-3)
                # scales are (B, H, T, nb) -> cat on T (dim=-2)
                self.k_scales = torch.cat([self.k_scales, ks], dim=-2)
                self.v_scales = torch.cat([self.v_scales, vs], dim=-2)

    def bounded_replay(self, encode_fn, prefix_tokens):
        """On cache loss, re-encode only the last `replay` tokens."""
        if prefix_tokens is None or prefix_tokens.shape[-1] == 0:
            return
        tail = prefix_tokens[..., -self.replay:, :]
        k, v = encode_fn(tail)
        self.append(k, v)

    def get_kv(self):
        """Return (k_all, v_all) as fp16/float."""
        parts_k, parts_v = [], []
        if self.k_codes is not None:
            parts_k.append(self.fp4.dequantize(self.k_codes, self.k_scales))
            parts_v.append(self.fp4.dequantize(self.v_codes, self.v_scales))
        if self.k_tail is not None:
            parts_k.append(self.k_tail)
            parts_v.append(self.v_tail)
        if not parts_k:
            return None, None
        return torch.cat(parts_k, dim=-2), torch.cat(parts_v, dim=-2)

    def size_bytes(self):
        b = 0
        if self.k_tail is not None:
            b += self.k_tail.numel() * self.k_tail.element_size() * 2
        if self.k_codes is not None:
            # 4-bit codes assumed packed as uint8 (1 byte / 2 channels) => numel/2 bytes
            b += self.k_codes.numel() // 2
            b += self.v_codes.numel() // 2
            b += self.k_scales.numel() * 4    # e4m3 as 4-byte
            b += self.v_scales.numel() * 4
        return b
