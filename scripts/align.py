#!/usr/bin/env python3
"""Put Whisper's word times on the creator's own script, so captions show exactly what they wrote (Whisper hears
"קיבלו" for "כיבו", "cloud" for "Claude"...). Use it whenever the creator gives you the script.

Usage:  PY align.py <project_dir> <script.txt> [--clip c1]
Reads words_<clip>.json, writes work/aligned_src.json: [{"text", "start", "end", "sent", "matched"}] in SOURCE time
(then make_edl.py / assemble.py / cut_words.py). Niqqud is stripped from the display text. "sent" counts sentences
(split after . ? ! :). Script words Whisper missed get times spread over the gap between matched neighbours; the
printout marks them with *. Check the first sentence is there: if Whisper dropped it, the stars show it.
"""
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

# vowel points and cantillation only: NOT maqaf U+05BE ("ה־code" lost its hyphen), paseq 05C0, sof pasuq 05C3, 05C6
NIQQUD = re.compile('[֑-ׇֽֿׁׂׅׄ]')


def norm(w):
    w = NIQQUD.sub('', w).lower()
    return re.sub(r'[^\w%]', '', w)   # drop punctuation, hyphens, quotes


def main():
    skillenv.utf8_stdio()
    args = sys.argv[1:]
    clip = 'c1'
    if '--clip' in args:
        i = args.index('--clip')
        clip = args[i + 1]
        del args[i:i + 2]
    proj, script = skillenv.path_arg(args[0]), skillenv.path_arg(args[1])
    with open(os.path.join(proj, f'words_{clip}.json'), encoding='utf-8') as fh:
        words = json.load(fh)
    with open(script, encoding='utf-8') as fh:
        text = fh.read()
    toks, sent = [], 0
    for raw in text.split():
        toks.append({'text': NIQQUD.sub('', raw), 'sent': sent})
        if raw[-1] in '.?!:':
            sent += 1
    a, b = [norm(t['text']) for t in toks], [norm(w['text']) for w in words]
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == 'equal':
            for k in range(i2 - i1):
                toks[i1 + k].update(start=words[j1 + k]['start'], end=words[j1 + k]['end'], matched=True)
        elif op == 'replace' and j2 > j1:   # same stretch, different spelling: spread Whisper's span over it
            t0, t1, n = words[j1]['start'], words[j2 - 1]['end'], i2 - i1
            for k in range(n):
                toks[i1 + k].update(start=round(t0 + (t1 - t0) * k / n, 3), end=round(t0 + (t1 - t0) * (k + 1) / n, 3),
                                    matched=False)
    for i, t in enumerate(toks):   # inserted words: interpolate between the neighbours
        if 'start' in t:
            continue
        prev = next((toks[j]['end'] for j in range(i - 1, -1, -1) if 'end' in toks[j]), 0.0)
        nxt_i = next((j for j in range(i + 1, len(toks)) if 'start' in toks[j]), None)
        nxt = toks[nxt_i]['start'] if nxt_i is not None else prev + .4
        gap = [j for j in range(i, nxt_i if nxt_i is not None else len(toks)) if 'start' not in toks[j]]
        step = (nxt - prev) / len(gap)
        for k, j in enumerate(gap):
            toks[j].update(start=round(prev + step * k, 3), end=round(prev + step * (k + 1), 3), matched=False)
    os.makedirs(os.path.join(proj, 'work'), exist_ok=True)
    with open(os.path.join(proj, 'work', 'aligned_src.json'), 'w', encoding='utf-8') as fh:
        json.dump(toks, fh, ensure_ascii=False, indent=0)
    miss = [t['text'] for t in toks if not t.get('matched')]
    print(f'{len(toks)} script words, {len(toks) - len(miss)} matched exactly; * = estimated')
    cur = -1
    for t in toks:
        if t['sent'] != cur:
            cur = t['sent']
            print(f'\n[{cur}] ', end='')
        print(f"{t['text']}@{t['start']:.2f}{'' if t.get('matched') else '*'} ", end='')
    print()


if __name__ == '__main__':
    main()
