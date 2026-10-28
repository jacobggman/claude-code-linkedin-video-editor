#!/usr/bin/env python3
"""Cut the reel straight from the originals into <project>/assets/aroll.mp4 (1080x1920, 30fps CFR from t=0),
frame-locked so the audio cannot drift.

Usage:  PY assemble.py <project_dir> [--hold 0.5]
Needs <project>/sources.json (ingest.py) and <project>/edl.json (by hand, or make_edl.py for one continuous take):
  [{"id": "hook", "clip": "c1", "in": 12.66, "out": 15.72, "zoom": 1.0, "cx": 0.5, "cy": 0.5, "line": "..."}, ...]
  zoom > 1 = punch-in cropped from the original (sharp when the source is 4K), centred on (cx, cy) as frame fractions.
Writes segments.json: each segment's first frame in the cut ("frame"), its length ("frames") and the exact source
span it uses (src_in / src_out, snapped to the 30fps grid).

Why frame-locked: every segment gets n = round(out*30) - round(in*30) video frames AND exactly n/30 s of audio, cut
from the same seek point. The first version of this skill cut video and audio separately; with a 25fps phone clip
each segment came out a frame long or short and the concat added it up to 0.3s of lip-sync error by the end.
--hold: seconds of the last frame held after the speech (with silence), for the speaker's exit animation.
Check with sync_check.py.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

FF, FP = skillenv.tool('ffmpeg'), skillenv.tool('ffprobe')


def size(f):
    w, h = subprocess.run([FP, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', f],
                          **skillenv.TEXT).stdout.strip().split(',')[:2]
    return int(w), int(h)


def crop(z, cx, cy, sw, sh):
    if z <= 1:
        return ''
    w, h = round(sw / z / 2) * 2, round(sh / z / 2) * 2
    x = min(max(round(cx * sw - w / 2), 0), sw - w)
    y = min(max(round(cy * sh - h / 2), 0), sh - h)
    return f'crop={w}:{h}:{x}:{y},'


def main():
    skillenv.utf8_stdio()
    args = sys.argv[1:]
    hold = 0.5
    if '--hold' in args:
        i = args.index('--hold')
        hold = float(args[i + 1])
        del args[i:i + 2]
    proj = skillenv.path_arg(args[0])
    work, assets = os.path.join(proj, 'work'), os.path.join(proj, 'assets')
    with open(os.path.join(proj, 'sources.json'), encoding='utf-8') as fh:
        src = json.load(fh)
    with open(os.path.join(proj, 'edl.json'), encoding='utf-8') as fh:
        edl = json.load(fh)
    os.makedirs(work, exist_ok=True)
    os.makedirs(assets, exist_ok=True)
    parts, meta, fr = [], [], 0
    for k, s in enumerate(edl):
        f = src[s['clip']]
        sw, sh = size(f)
        f0, f1 = round(s['in'] * 30), round(s['out'] * 30)
        n, t_in = f1 - f0, f0 / 30
        d = n / 30
        out = os.path.join(work, f'seg_{k}.mp4')
        # 30fps grid first, then the punch-in crop and a cover-fill to 1080x1920, then exactly n frames
        vf = (f"fps=30,{crop(s.get('zoom', 1), s.get('cx', .5), s.get('cy', .5), sw, sh)}"
              f'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,'
              f'trim=end_frame={n},setpts=PTS-STARTPTS')
        af = (f'atrim=end={d:.5f},apad=whole_dur={d:.5f},asetpts=PTS-STARTPTS,'
              f'afade=t=in:d=0.02,afade=t=out:st={d - .03:.4f}:d=0.03')   # no clicks at the joins
        subprocess.run([FF, '-loglevel', 'error', '-y', '-ss', f'{t_in:.4f}', '-i', f, '-map', '0:v:0', '-map', '0:a:0',
                        '-vf', vf, '-af', af, '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                        '-c:a', 'pcm_s16le', '-ar', '48000', out], check=True)
        parts.append(out)
        meta.append({**s, 'src_in': t_in, 'src_out': t_in + d, 'frame': fr, 'frames': n})
        fr += n
    # the list holds bare file names (resolved next to concat.txt), so no drive letters or backslashes end up in it
    concat = os.path.join(work, 'concat.txt')
    with open(concat, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(''.join(skillenv.concat_entry(os.path.basename(p)) for p in parts))
    total = fr / 30 + hold
    subprocess.run([FF, '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', concat,
                    '-vf', f'setpts=N/30/TB,tpad=stop_mode=clone:stop_duration={hold}', '-r', '30', '-fps_mode', 'cfr',
                    '-af', f'asetpts=N/SR/TB,apad=whole_dur={total:.4f},atrim=end={total:.4f}',
                    '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-g', '30', '-keyint_min', '30', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', os.path.join(assets, 'aroll.mp4')], check=True)
    with open(os.path.join(proj, 'segments.json'), 'w', encoding='utf-8') as fh:
        json.dump(meta, fh, indent=1, ensure_ascii=False)
    for m in meta:
        print(f"frame {m['frame']:4d} ({m['frame'] / 30:6.3f}s) +{m['frames']:3d}f  {m['id']:8s} {m['clip']} "
              f"{m['src_in']:.3f}-{m['src_out']:.3f}  {m.get('line', '')}")
    print(f'{len(meta)} segments, {fr} frames ({fr / 30:.3f}s) + {hold}s hold = {total:.3f}s')


if __name__ == '__main__':
    main()
