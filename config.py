from dataclasses import dataclass
from typing import Tuple


@dataclass
class ZeroConfig:
    # ---- vocabulary & dimensions ----
    vocab_size: int = 16000
    hidden_size: int = 512
    intermediate_size: int = 1408
    num_layers: int = 10
    num_heads: int = 8
    num_kv_heads: int = 4                # GQA
    head_dim: int = 64
    max_seq_len: int = 2048

    # ---- BitNet b1.58 (multiplication-free weights) ----
    use_bitnet: bool = True
    bitnet_eps: float = 1e-8

    # ---- TurboQuant (Hadamard rotation + Lloyd-Max, multiply-free) ----
    turboquant_enabled: bool = True
    turboquant_bits: int = 4             # 2, 3, or 4
    turboquant_block: int = 16

    # ---- FP4 KV cache (E2M1 with per-16 E4M3 scale) ----
    fp4_kv: bool = True

    # ---- CSA2 layer pattern (F=Full, R=Reindex, U=Reuse) ----
    csa2_pattern: Tuple[str, ...] = ("F", "U", "R", "U", "F", "U", "R", "U", "F", "U")

    # ---- SWA + Bounded Replay ----
    swa_window: int = 128
    bounded_replay: int = 128

    # ---- CED (Causal Encoder-Decoder activation scheme) ----
    ced_prefill_layers: int = 4          # layers active during prefill

    # ---- RoPE ----
    rope_theta: float = 10000.0

    # ---- misc ----
    rms_eps: float = 1e-6
    dropout: float = 0.0
    tie_embeddings: bool = True

    def __post_init__(self):
        assert len(self.csa2_pattern) == self.num_layers, \
            f"csa2_pattern len {len(self.csa2_pattern)} != num_layers {self.num_layers}"
        assert self.num_heads * self.head_dim == self.hidden_size
        assert self.num_heads % self.num_kv_heads == 0
