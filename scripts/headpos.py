#!/usr/bin/env python3
"""Head position per segment, read from the subject's alpha (assets/subject.webm from key.py or cutout.py).

Usage:  PY headpos.py <project_dir>      (PY = the skill's Python; needs Pillow)
Prints per segment: head top, head x-span (widest point between the top of the hair and ~800px below it, i.e.
ears included, shoulders not), body box. Writes work/headpos.json {segment id: {top, x0, x1, cx}} (medians of 3
frames, 1080x1920 frame coordinates) which the template reads to place the speaker in side-by-side layouts so the
face stays clear of LinkedIn's action bars, and to place behind-head words and cards that must not cover the face.
"""
import json
import os
import statistics
import subprocess
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

skillenv.utf8_stdio()
FF = skillenv.tool('ffmpeg')
proj = skillenv.path_arg(sys.argv[1])
with open(os.path.join(proj, 'segments.json'), encoding='utf-8') as fh:
    segs = json.load(fh)
alpha = os.path.join(proj, 'work', 'alpha')
subject = os.path.join(proj, 'assets', 'subject.webm')
os.makedirs(alpha, exist_ok=True)
out = {}
for s in segs:
    t0, d = s['frame'] / 30, s['frames'] / 30
    rows, tops, x0s, x1s, samples = [], [], [], [], []
    # long segments (a whole take kept in one piece) are sampled every ~2s, so side layouts see where the speaker is THEN
    fracs = (.2, .5, .8) if d < 6 else [(k + .5) / round(d / 2) for k in range(round(d / 2))]
    for k, f in enumerate(fracs):
        png = os.path.join(alpha, f"{skillenv.safe_name(s['id'])}_{k}.png")
        subprocess.run([FF, '-loglevel', 'error', '-y', '-c:v', 'libvpx-vp9', '-ss', f'{t0 + d * f:.2f}',
                        '-i', subject, '-frames:v', '1', '-vf', 'alphaextract,scale=270:480', png], check=True)
        im = Image.open(png).convert('L')
        px, (w, h) = im.load(), im.size
        ys = [y for y in range(h) if any(px[x, y] > 128 for x in range(0, w, 2))]
        if not ys:
            rows.append('no subject')
            continue
        top = ys[0]
        span = [x for y in range(top + 6, min(h, top + 200), 4) for x in range(w) if px[x, y] > 128]
        bb = im.point(lambda v: 255 if v > 128 else 0).getbbox()
        tops.append(top * 4)
        x0s.append(min(span) * 4)
        x1s.append(max(span) * 4)
        samples.append({'t': round(t0 + d * f, 2), 'top': top * 4, 'cx': (min(span) + max(span)) * 2})
        rows.append(f"head top {top * 4:4d}  head x {min(span) * 4}-{max(span) * 4}  body {[v * 4 for v in bb]}")
    if tops:
        x0, x1 = statistics.median(x0s), statistics.median(x1s)
        out[s['id']] = {'top': statistics.median(tops), 'x0': x0, 'x1': x1, 'cx': (x0 + x1) / 2, 'samples': samples}
    print(f"{s['id']:8s} {t0:6.2f}s  " + (' | '.join(rows) if len(rows) <= 3 else f'{len(rows)} samples, head x centre '
                                          f'{min(x["cx"] for x in samples):.0f}-{max(x["cx"] for x in samples):.0f}'))
with open(os.path.join(proj, 'work', 'headpos.json'), 'w', encoding='utf-8') as fh:
    json.dump(out, fh, indent=1)
print('->', os.path.join(proj, 'work', 'headpos.json'))
