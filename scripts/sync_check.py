#!/usr/bin/env python3
"""Lip-sync check for the assembled cut: for every 4th segment (and the last), cross-correlate that segment's source
audio with the cut's audio where segments.json says the segment starts (frame/30). Video frames sit exactly there
(setpts=N/30), so a lag near 0 means the voice matches the lips. More than ~40 ms is visible: re-run assemble.py.
Usage:  PY sync_check.py <project_dir>
"""
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

SR = 8000


def pcm(f, ss, d):
    raw = subprocess.run([skillenv.tool('ffmpeg'), '-loglevel', 'error', '-ss', f'{ss:.3f}', '-t', f'{d:.3f}', '-i', f, '-vn',
                          '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32)


def main():
    skillenv.utf8_stdio()
    proj = skillenv.path_arg(sys.argv[1])
    with open(os.path.join(proj, 'sources.json'), encoding='utf-8') as fh:
        src = json.load(fh)
    with open(os.path.join(proj, 'segments.json'), encoding='utf-8') as fh:
        segs = json.load(fh)
    worst = 0.0
    for s in segs[1::4] + [segs[-1]]:
        d = min(1.5, s['src_out'] - s['src_in'])
        a = pcm(src[s['clip']], s['src_in'], d)
        t = s['frame'] / 30
        b = pcm(os.path.join(proj, 'assets', 'aroll.mp4'), max(0, t - .3), d + .6)
        lag = np.argmax(np.correlate(b, a, mode='valid')) / SR - min(.3, t)
        worst = max(worst, abs(lag))
        print(f"{s['id']}  cut {t:7.3f}s  audio lag {lag * 1000:+6.1f} ms")
    print('SYNC OK' if worst < .04 else f'SYNC OFF by up to {worst * 1000:.0f} ms: re-run assemble.py')


if __name__ == '__main__':
    main()
