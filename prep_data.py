"""Prepare TinyShakespeare for char-level training."""
import os, pickle, torch

path = "tinyshakespeare.txt"
text = open(path, "r", encoding="utf-8").read()
print(f"corpus size: {len(text)} chars")

chars = sorted(set(text))
vocab_size = len(chars)
print(f"vocab size: {vocab_size}")
print(f"chars: {''.join(chars)!r}")

stoi = {c: i for i, c in enumerate(chars)}
itos = {i: c for c, i in stoi.items()}

data = torch.tensor([stoi[c] for c in text], dtype=torch.long)
n = int(0.9 * len(data))
train_data = data[:n]
val_data = data[n:]
print(f"train: {len(train_data)}, val: {len(val_data)}")

with open("data.pkl", "wb") as f:
    pickle.dump({"train": train_data, "val": val_data, "stoi": stoi, "itos": itos}, f)
print("saved data.pkl")
