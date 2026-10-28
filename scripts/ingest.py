#!/usr/bin/env python3
"""Register raw clips for a /video-edit-linkedin project, make contact sheets, transcribe every clip.

Usage (run with PY, the skill's Python from .platform.json; it has faster-whisper):
  PY ingest.py <project_dir> <clip files or one folder> [--newest N] [--lang he|en] [--prompt "names, keywords"]
--lang: default is config.json "language". Hebrew uses ivrit.ai's Whisper, English small.en (see speech.py).
--prompt: names and keywords to spell right. Never paste the script's opening line into it (see speech.py).

Writes into <project_dir>:
  sources.json             {"c1": "/abs/original.MP4", ...}  (ordered oldest -> newest by file time)
  work/sheet_cN.jpg        8 frames across each clip; work/sheets.jpg stacks them (look at it: setups, angles,
                           and whether it was shot on a green screen -> key.py instead of cutout.py)
  words_cN.json            word timestamps per clip
  transcript.txt           per clip: segments, "words:" word@time, "speech map cN:" silencedetect S/E marks
Originals are never modified. Everything is read straight from them (no proxies).
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402
import speech  # noqa: E402

FF, FP = skillenv.tool('ffmpeg'), skillenv.tool('ffprobe')
VIDEO_EXT = ('.mp4', '.mov', '.m4v')


def probe(f):
    out = subprocess.run([FP, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate',
                          '-show_entries', 'format=duration', '-of', 'json', f], **skillenv.TEXT).stdout
    j = json.loads(out)
    s = j['streams'][0]
    return s['width'], s['height'], s['r_frame_rate'], float(j['format']['duration'])


def speech_regions(f):
    out = subprocess.run([FF, '-hide_banner', '-i', f, '-af', 'silencedetect=n=-38dB:d=0.25', '-f', 'null', '-'],
                         **skillenv.TEXT).stderr
    marks = [(l.split('silence_')[1].split(':')[0], float(l.split(': ')[1].split(' ')[0]))
             for l in out.splitlines() if 'silence_start' in l or 'silence_end' in l]
    return ' '.join(f"{k[0].upper()}{v:.2f}" for k, v in marks)   # S=silence start, E=silence end


def opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        val = args[i + 1]
        del args[i:i + 2]
        return val
    return default


def main():
    skillenv.utf8_stdio()
    proj, args = skillenv.path_arg(sys.argv[1]), sys.argv[2:]
    newest = opt(args, '--newest')
    lang = opt(args, '--lang', skillenv.config().get('language', 'en'))
    prompt = opt(args, '--prompt')
    files = []
    for a in map(skillenv.path_arg, args):
        if os.path.isdir(a):
            files += [os.path.join(a, f) for f in os.listdir(a) if f.lower().endswith(VIDEO_EXT)]
        else:
            files.append(a)
    files = sorted(set(os.path.abspath(f) for f in files), key=os.path.getmtime)
    if newest:
        files = files[-int(newest):]
    work = os.path.join(proj, 'work')
    os.makedirs(work, exist_ok=True)
    sources = {f'c{k + 1}': f for k, f in enumerate(files)}
    with open(os.path.join(proj, 'sources.json'), 'w', encoding='utf-8') as fh:
        json.dump(sources, fh, indent=1, ensure_ascii=False)

    sheets = []
    for cid, f in sources.items():
        w, h, fr, d = probe(f)
        print(f'{cid}  {w}x{h} {fr} {d:.1f}s  {os.path.basename(f)}')
        sh = os.path.join(work, f'sheet_{cid}.jpg')
        subprocess.run([FF, '-loglevel', 'error', '-y', '-i', f, '-vf', f'fps=8/{d},scale=200:-2,tile=8x1', '-frames:v', '1', sh], check=True)
        sheets.append(sh)
    ins = sum((['-i', s] for s in sheets), [])
    stack = ['-filter_complex', f'vstack={len(sheets)}'] if len(sheets) > 1 else []
    subprocess.run([FF, '-loglevel', 'error', '-y', *ins, *stack, os.path.join(work, 'sheets.jpg')], check=True)

    print(f'transcribing in {lang!r} with {skillenv.whisper_model(lang, "ingest")}', flush=True)
    lines = []
    for cid, f in sources.items():
        wav = os.path.join(work, f'{cid}.wav')
        subprocess.run([FF, '-loglevel', 'error', '-y', '-i', f, '-vn', '-ac', '1', '-ar', '16000', wav], check=True)
        segs, raw = speech.transcribe(wav, lang, 'ingest', prompt)
        words = []
        for w in raw:
            t = w['text']
            if words and t[:1] in '-.' and len(t) > 1 and t[1:2].isdigit():   # "GPT" "-6" / "5" ".1"
                words[-1]['text'] += t
                words[-1]['end'] = w['end']
                continue
            words.append(dict(w))
        lines.append(f'===== {cid}  {os.path.basename(f)}')
        lines += [f'[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}' for s in segs]
        with open(os.path.join(proj, f'words_{cid}.json'), 'w', encoding='utf-8') as fh:
            json.dump(words, fh, indent=1, ensure_ascii=False)
        lines.append('words: ' + ' '.join(f"{w['text']}@{w['start']:.2f}" for w in words))
        lines.append(f'speech map {cid}: ' + speech_regions(f))
    with open(os.path.join(proj, 'transcript.txt'), 'w', encoding='utf-8') as fh:   # utf-8: Hebrew, curly quotes
        fh.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
