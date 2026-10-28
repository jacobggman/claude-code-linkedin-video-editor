#!/usr/bin/env python3
"""Frame-exact QA of a render: the last frame before and first frame after every cut, in one strip, plus a phone copy.

Usage:  PY check_cuts.py <project_dir> <render.mp4> [--phone]
Writes work/cut_check.jpg (pairs left->right: before|after for each cut). LOOK at it: every 'after' frame must show the
new shot with that section's look and no leftovers (room plates, cutout of the previous shot, stale captions).
Snapshots from `hyperframes snapshot` seek approximately at cuts; only frames pulled from the final render are proof.
--phone also writes <render>-phone.mp4 (720p, crf 26; SendUserFile uploads over ~5MB often fail, drop to crf 28).
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

skillenv.utf8_stdio()
FF = skillenv.tool('ffmpeg')
proj, render = skillenv.path_arg(sys.argv[1]), skillenv.path_arg(sys.argv[2])
with open(os.path.join(proj, 'segments.json'), encoding='utf-8') as fh:
    segs = json.load(fh)
cf = os.path.join(proj, 'work', 'cf')
sheet = os.path.join(proj, 'work', 'cut_check.jpg')
os.makedirs(cf, exist_ok=True)
pngs = []
for s in segs[1:]:
    for n in (s['frame'] - 1, s['frame']):
        p = os.path.join(cf, f'f{n}.png')
        subprocess.run([FF, '-loglevel', 'error', '-y', '-i', render, '-vf', f'select=eq(n\\,{n}),scale=150:-2', '-frames:v', '1', p], check=True)
        pngs.append(p)
if pngs:
    ins = sum((['-i', p] for p in pngs), [])
    subprocess.run([FF, '-loglevel', 'error', '-y', *ins, '-filter_complex', f'hstack={len(pngs)}', sheet], check=True)
    print('cuts at frames', [s['frame'] for s in segs[1:]], '->', sheet)
else:   # the default now: one continuous take, nothing cut
    print('no cuts (one continuous take): nothing to check')
if '--phone' in sys.argv:
    out = os.path.splitext(render)[0] + '-phone.mp4'
    subprocess.run([FF, '-loglevel', 'error', '-y', '-i', render, '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'slow',
                    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out], check=True)
    print('phone copy', out, f'{os.path.getsize(out) / 1e6:.1f} MB')
