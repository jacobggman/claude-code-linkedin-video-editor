#!/usr/bin/env python3
"""Green-screen footage: key assets/aroll.mp4 into assets/subject.webm (VP9 + alpha), the same file cutout.py makes
with an AI matte, in a few minutes on any CPU and with cleaner hair. Then the background is designed per section
(the template's PLATES) instead of graded.

Usage:  PY key.py <project_dir> [--check]
Looks at the frame border of 6 frames; if most of it is one saturated green, keys that exact colour (chromakey
similarity .18 blend .08 + despill) and asserts subject frames == aroll frames. --check only reports.
Exit code 2 = not a green screen: run cutout.py instead.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

FF, FP = skillenv.tool('ffmpeg'), skillenv.tool('ffprobe')
W, H = 54, 96


def frames(f):
    out = subprocess.run([FP, '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames',
                          '-of', 'csv=p=0', f], **skillenv.TEXT).stdout
    return out.strip().split(',')[0]


def border_green(aroll):
    """-> (share of border pixels that are saturated green, median green as 0xRRGGBB)"""
    dur = float(subprocess.run([FP, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', aroll],
                               **skillenv.TEXT).stdout.strip())
    greens, total = [], 0
    for k in range(6):
        raw = subprocess.run([FF, '-loglevel', 'error', '-ss', f'{dur * (k + .5) / 6:.2f}', '-i', aroll, '-frames:v', '1',
                              '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
        px = [tuple(raw[i:i + 3]) for i in range(0, len(raw), 3)]
        for y in range(H):
            for x in range(W):
                if x in (0, 1, W - 2, W - 1) or y in (0, 1):   # sides and top (the body touches the bottom)
                    total += 1
                    r, g, b = px[y * W + x]
                    if g > 140 and g > r + 60 and g > b + 60:
                        greens.append((r, g, b))
    if not greens:
        return 0.0, None
    med = [sorted(c[i] for c in greens)[len(greens) // 2] for i in range(3)]
    return len(greens) / total, '0x%02X%02X%02X' % tuple(med)


def main():
    skillenv.utf8_stdio()
    proj = skillenv.path_arg(sys.argv[1])
    aroll, subject = os.path.join(proj, 'assets', 'aroll.mp4'), os.path.join(proj, 'assets', 'subject.webm')
    share, colour = border_green(aroll)
    print(f'green border: {share:.0%}  key colour {colour}')
    if share < .6:
        print('not a green screen: run cutout.py (AI background removal) instead')
        sys.exit(2)
    if '--check' in sys.argv:
        return
    subprocess.run([FF, '-loglevel', 'error', '-y', '-i', aroll, '-an', '-vf',
                    f'chromakey={colour}:0.18:0.08,despill=type=green:mix=0.5,format=yuva420p',
                    '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '28', '-row-mt', '1', '-tile-columns', '2',
                    '-deadline', 'good', '-cpu-used', '5', '-auto-alt-ref', '0', subject], check=True)
    a, s = frames(aroll), frames(subject)
    print(f'aroll frames {a} / subject frames {s}')
    if not a or a != s:
        sys.exit('FRAME MISMATCH: the subject will drift. Re-run assemble.py, then this script.')


if __name__ == '__main__':
    main()
