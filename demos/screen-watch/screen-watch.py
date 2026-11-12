#!/usr/bin/env python3
"""
screen-watch.py — Real-time screen change detector (fast)
Uses mss + numpy for ~30-70ms per frame (20-30x faster than PowerShell version).

Emits JSONL events to events-fast.jsonl whenever a screen region changes.
"""
import sys
import json
import time
import argparse
from pathlib import Path

try:
    import mss
    import numpy as np
except ImportError as e:
    print(f"Missing dependency: {e}", file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fps', type=int, default=20)
    ap.add_argument('--threshold', type=int, default=40)
    ap.add_argument('--duration', type=int, default=30)
    ap.add_argument('--downscale', type=int, default=4)
    ap.add_argument('--min-cells', type=int, default=20)
    ap.add_argument('--out', type=str, default='events-fast.jsonl')
    args = ap.parse_args()

    out = Path(args.out).resolve()
    out.write_text('', encoding='utf-8')

    interval = 1.0 / args.fps
    end_time = time.time() + args.duration

    with mss.MSS() as sct:
        monitor = sct.monitors[1]
        W = monitor['width']
        H = monitor['height']
        SW = max(1, W // args.downscale)
        SH = max(1, H // args.downscale)

        with open(out, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'meta': 'start', 'ts': int(time.time() * 1000),
                'fps': args.fps, 'threshold': args.threshold,
                'scale': args.downscale, 'screenW': W, 'screenH': H,
                'engine': 'python-mss-numpy'
            }) + '\n')
            f.flush()

            prev = None
            frame = 0
            total_events = 0
            bbox = {'left': monitor['left'], 'top': monitor['top'],
                    'width': W, 'height': H}

            while time.time() < end_time:
                t0 = time.perf_counter()
                img = np.array(sct.grab(bbox))            # BGRA, shape (H, W, 4)
                small = img[::args.downscale, ::args.downscale, :3].astype(np.int16)

                if prev is not None and prev.shape == small.shape:
                    diff = np.abs(small - prev).sum(axis=2)
                    mask = diff > args.threshold
                    changed = int(mask.sum())
                    if changed > args.min_cells:
                        ys, xs = np.where(mask)
                        x0 = int(xs.min() * args.downscale)
                        y0 = int(ys.min() * args.downscale)
                        x1 = int((xs.max() + 1) * args.downscale)
                        y1 = int((ys.max() + 1) * args.downscale)
                        pct = round(changed * 100.0 / (SW * SH), 3)
                        rec = {
                            'ts': int(time.time() * 1000),
                            'frame': frame,
                            'changed': changed,
                            'pct': pct,
                            'x': x0, 'y': y0,
                            'w': x1 - x0, 'h': y1 - y0,
                            'latency_ms': round((time.perf_counter() - t0) * 1000, 2)
                        }
                        f.write(json.dumps(rec, separators=(',', ':')) + '\n')
                        f.flush()
                        total_events += 1

                prev = small
                frame += 1
                elapsed = time.perf_counter() - t0
                sleep_for = interval - elapsed
                if sleep_for > 0:
                    time.sleep(sleep_for)

            f.write(json.dumps({
                'meta': 'end', 'ts': int(time.time() * 1000),
                'frames': frame, 'events': total_events
            }) + '\n')
            f.flush()

    print(f'Done. frames={frame} events={total_events} out={out}')


if __name__ == '__main__':
    main()
