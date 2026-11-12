"""
export_cpp.py — serialize an AddZeroLM checkpoint to the .zbin format
consumed by cpp/zero_infer.cpp.

Header layout (little-endian):
    magic          4 bytes  "ZER1"
    vocab_size     int32
    hidden_size    int32
    intermediate   int32
    num_layers     int32
    num_heads      int32
    num_kv_heads   int32
    head_dim       int32
    max_seq_len    int32
    swa_window     int32
    top_k          int32
    pattern        num_layers int32   (0=F, 1=R, 2=U)
    embed          vocab*hidden fp32
    layers         for each layer, 7 ternary matrices:
                     int32 out, int32 in, out*in int8
    head           int32 out, int32 in, out*in int8
    norm_gain      hidden int8
"""

import argparse
import struct
import torch
from config import ZeroConfig
from model.addonly_model import AddZeroLM


def ternarize(W: torch.Tensor) -> torch.Tensor:
    scale = 1.0 / (W.abs().mean(dim=1, keepdim=True) + 1e-8)
    q = torch.clamp(torch.round(W * scale), -1, 1)
    return q.to(torch.int8)


def write_ternary(f, W_fp: torch.Tensor):
    q = ternarize(W_fp).cpu().contiguous()
    out, inn = q.shape
    f.write(struct.pack("<ii", out, inn))
    f.write(q.numpy().tobytes())


def export(ckpt_path: str, out_path: str):
    blob = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    cfg: ZeroConfig = blob["config"]
    sd = blob["model"]

    model = AddZeroLM(cfg)
    model.load_state_dict(sd, strict=False)

    pattern_map = {"F": 0, "R": 1, "U": 2}
    pattern = [pattern_map[cfg.csa2_pattern[i]] for i in range(cfg.num_layers)]

    with open(out_path, "wb") as f:
        f.write(b"ZER1")
        f.write(struct.pack("<i", cfg.vocab_size))
        f.write(struct.pack("<i", cfg.hidden_size))
        f.write(struct.pack("<i", cfg.intermediate_size))
        f.write(struct.pack("<i", cfg.num_layers))
        f.write(struct.pack("<i", cfg.num_heads))
        f.write(struct.pack("<i", cfg.num_kv_heads))
        f.write(struct.pack("<i", cfg.head_dim))
        f.write(struct.pack("<i", cfg.max_seq_len))
        f.write(struct.pack("<i", cfg.swa_window))
        f.write(struct.pack("<i", cfg.swa_window))  # top_k == swa_window
        for p in pattern:
            f.write(struct.pack("<i", p))

        emb = model.embed.weight.detach().cpu().contiguous()
        f.write(emb.numpy().astype("float32").tobytes())

        for blk in model.blocks:
            write_ternary(f, blk.q_w.detach())
            write_ternary(f, blk.k_w.detach())
            write_ternary(f, blk.v_w.detach())
            write_ternary(f, blk.o_w.detach())
            write_ternary(f, blk.g_w.detach())
            write_ternary(f, blk.u_w.detach())
            write_ternary(f, blk.d_w.detach())

        write_ternary(f, model.head_w.detach())

        gain = ternarize(model.norm_gain.unsqueeze(0)).squeeze(0).cpu().numpy()
        f.write(gain.tobytes())

    print(f"Exported {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="out/zero.pt")
    ap.add_argument("--out", default="out/zero.zbin")
    args = ap.parse_args()
    export(args.ckpt, args.out)
