#!/usr/bin/env python3
"""Script words with SOURCE times (work/aligned_src.json from align.py) -> times in the assembled cut
(segments.json from assemble.py). Writes work/words_cut.json ({i, text, start, end, sent}), the file the template's
captions and word-timed inserts read, and work/words_cut.txt: one line per sentence, index:word@time, plus every
segment's start. Time inserts by word INDEX (WT(i) in build.py), so a re-cut moves them with the words.
Usage:  PY cut_words.py <project_dir>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402


def main():
    skillenv.utf8_stdio()
    proj = skillenv.path_arg(sys.argv[1])
    with open(os.path.join(proj, 'segments.json'), encoding='utf-8') as fh:
        segs = json.load(fh)
    with open(os.path.join(proj, 'work', 'aligned_src.json'), encoding='utf-8') as fh:
        words = json.load(fh)

    def to_cut(t):
        # the segment holding t, else the next one (a word Whisper starts inside a trimmed pause snaps to its cut)
        for s in segs:
            if t < s['src_out']:
                return s['frame'] / 30 + (max(t, s['src_in']) - s['src_in'])
        s = segs[-1]
        return s['frame'] / 30 + (s['src_out'] - s['src_in'])

    out = []
    for i, w in enumerate(words):
        a = to_cut(w['start'])
        out.append({'i': i, 'text': w['text'], 'start': round(a, 3), 'end': round(max(to_cut(w['end']), a + .08), 3),
                    'sent': w['sent']})
    with open(os.path.join(proj, 'work', 'words_cut.json'), 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=0)
    lines, cur = [], -1
    for w in out:
        if w['sent'] != cur:
            cur = w['sent']
            lines.append(f"[{cur}] {w['start']:.2f}  ")
        lines[-1] += f"{w['i']}:{w['text']}@{w['start']:.2f} "
    lines.append('segment starts (cut s): ' + ' '.join(f"{s['id']}={s['frame'] / 30:.3f}" for s in segs))
    with open(os.path.join(proj, 'work', 'words_cut.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
