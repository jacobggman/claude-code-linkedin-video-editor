#!/usr/bin/env python3
"""One continuous take -> edl.json.

DEFAULT: the whole take as one segment, pauses and all. The creator speaks in one flow; on the first reel the
pauses were cut and the creator said it looked choppy ("I'm already talking in flow"). Do not cut pauses unless the creator asks.

Usage:  PY make_edl.py <project_dir> [--clip c1]                         whole take (default)
        PY make_edl.py <project_dir> --cut-pauses [--gap .30] [--pre .10] [--post .11] [--keep 20.81:0.30 ...]
For several takes of the same line, pick takes by hand instead (SKILL.md).

--cut-pauses: every silence in transcript.txt's "speech map <clip>:" longer than --gap is cut: the segment before it ends --post
seconds into the silence, the next starts --pre seconds before speech returns (.10, not less: soft Hebrew onsets
like ש / כ sit under the -38dB threshold). Shorter pauses stay as breathing room. --keep <silence start>:<seconds>
keeps a deliberate beat (a pause before a reveal). Line labels come from work/aligned_src.json (align.py) when it
exists, else words_<clip>.json. Segment ids are s00, s01, ...
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402


def main():
    skillenv.utf8_stdio()
    args = sys.argv[1:]
    cut_pauses = '--cut-pauses' in args
    if cut_pauses:
        args.remove('--cut-pauses')
    opts = {'--clip': 'c1', '--gap': '.30', '--pre': '.10', '--post': '.11'}
    keep = {}
    for name in list(opts) + ['--keep']:
        while name in args:
            i = args.index(name)
            if name == '--keep':
                s, k = args[i + 1].split(':')
                keep[round(float(s), 2)] = float(k)
            else:
                opts[name] = args[i + 1]
            del args[i:i + 2]
    proj, clip = skillenv.path_arg(args[0]), opts['--clip']
    gap, pre, post = float(opts['--gap']), float(opts['--pre']), float(opts['--post'])
    with open(os.path.join(proj, 'transcript.txt'), encoding='utf-8') as fh:
        tr = fh.read()
    m = re.search(rf'speech map {clip}:(.*)', tr)
    if not m:
        raise SystemExit(f'no "speech map {clip}:" line in transcript.txt: run ingest.py first')
    marks = re.findall(r'([SE])(\d+\.\d+)', m.group(1))
    raw = [(float(a[1]), float(b[1])) for a, b in zip(marks[::2], marks[1::2])]
    sil = []   # silencedetect splits one pause in two (E78.29 S78.29): merge touching silences into one
    for s, e in raw:
        if sil and s - sil[-1][1] < .02:
            sil[-1] = (sil[-1][0], e)
        else:
            sil.append((s, e))
    with open(os.path.join(proj, 'sources.json'), encoding='utf-8') as fh:
        src = json.load(fh)[clip]
    end = float(subprocess.run([skillenv.tool('ffprobe'), '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src],
                               **skillenv.TEXT).stdout.strip())
    wf = os.path.join(proj, 'work', 'aligned_src.json')
    if not os.path.exists(wf):
        wf = os.path.join(proj, f'words_{clip}.json')
    with open(wf, encoding='utf-8') as fh:
        words = json.load(fh)
    # Trust silencedetect, not Whisper, for the cut points: Whisper starts words up to ~.4s early ("מה" at 78.36 was a
    # breath at -55dB; the voice came back at 78.75). Protecting Whisper's word spans kept every pause.
    edl, t_in = [], 0.0
    cuts = [(s, e) for s, e in sil if e - s > gap] if cut_pauses else []
    for s, e in cuts + [(end, end)]:
        out = min(s + keep.get(round(s, 2), post), end) if s < end else end
        line = ' '.join(w['text'] for w in words if t_in - pre <= w['start'] < out)
        edl.append({'id': f's{len(edl):02d}', 'clip': clip, 'in': round(t_in, 3), 'out': round(out, 3),
                    'zoom': 1.0, 'cx': 0.5, 'cy': 0.5, 'line': line})
        t_in = max(e - pre, out)
    with open(os.path.join(proj, 'edl.json'), 'w', encoding='utf-8') as fh:
        json.dump(edl, fh, ensure_ascii=False, indent=1)
    for x in edl:
        print(f"{x['id']}  {x['in']:7.2f}-{x['out']:7.2f}  {x['out'] - x['in']:5.2f}s  {x['line']}")
    print(f'{len(edl)} segments, {sum(x["out"] - x["in"] for x in edl):.2f}s kept of {end:.2f}s')


if __name__ == '__main__':
    main()
