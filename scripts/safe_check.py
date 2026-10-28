#!/usr/bin/env python3
"""LinkedIn safe-zone QA on the FINAL render: frames pulled from the mp4 with the red zones (skillenv.SAFE) painted
on, in one contact sheet. Anything important under red is covered by LinkedIn's UI on a phone: the feed's name /
headline over the top, the post text and mute button at the bottom, the action bar on the left (Hebrew UI) or right
(English UI). Snapshots with build.py --safe check layout while building; this checks what actually shipped.

Usage:  PY safe_check.py <render.mp4> [t1,t2,...]      (default: 10 moments spread over the video)
Writes <project>/work/safe_check.jpg next to the render's project.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

S = skillenv.SAFE
ZONES = [(0, 0, 1080, S['top']), (0, S['bottom'], 1080, 1920), (0, S['top'], S['side'], S['bottom']),
         (1080 - S['side'], S['top'], 1080, S['bottom']), (0, S['bar_top'], S['bar_w'], S['bottom']),
         (1080 - S['bar_w'], S['bar_top'], 1080, S['bottom'])]


def paint(im):
    over = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for z in ZONES:
        d.rectangle(z, fill=(255, 0, 0, 80))
    for y in (S['top'], S['bottom']):
        d.line([(0, y), (1080, y)], fill=(255, 30, 30, 255), width=4)
    for x in (S['bar_w'], 1080 - S['bar_w']):
        d.line([(x, S['bar_top']), (x, S['bottom'])], fill=(255, 30, 30, 255), width=4)
    return Image.alpha_composite(im.convert('RGBA'), over).convert('RGB')


def main():
    skillenv.utf8_stdio()
    render = skillenv.path_arg(sys.argv[1])
    dur = float(subprocess.run([skillenv.tool('ffprobe'), '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', render],
                               **skillenv.TEXT).stdout.strip())
    times = [float(t) for t in sys.argv[2].split(',')] if len(sys.argv) > 2 else [dur * (k + .5) / 10 for k in range(10)]
    tiles = []
    for t in times:
        raw = subprocess.run([skillenv.tool('ffmpeg'), '-loglevel', 'error', '-ss', f'{t:.3f}', '-i', render, '-frames:v', '1',
                              '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-'], capture_output=True).stdout
        tiles.append(paint(Image.frombytes('RGB', (1080, 1920), raw)).resize((270, 480)))
    cols = 5
    rows = -(-len(tiles) // cols)
    sheet = Image.new('RGB', (cols * 274, rows * 484), (25, 25, 25))
    for k, im in enumerate(tiles):
        sheet.paste(im, ((k % cols) * 274, (k // cols) * 484))
    proj = os.path.dirname(os.path.dirname(render))
    out = os.path.join(proj, 'work', 'safe_check.jpg')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out, quality=88)
    print('safe zone sheet ->', out, ' times', [round(t, 2) for t in times])


if __name__ == '__main__':
    main()
