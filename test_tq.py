import torch
from model.turboquant import FP4KV, TurboQuant
x = torch.randn(2, 4, 8, 64)
fp4 = FP4KV(block=16)
c, s = fp4.quantize(x)
print("codes:", c.shape, "scales:", s.shape)
y = fp4.dequantize(c, s)
print("deq:", y.shape, "matches input:", y.shape == x.shape)

tq = TurboQuant(bits=4, block=16)
c2, s2 = tq.quantize(x)
y2 = tq.dequantize(c2, s2)
print("tq deq:", y2.shape, "matches:", y2.shape == x.shape)
print("OK")
