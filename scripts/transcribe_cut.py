#!/usr/bin/env python3
"""Word timings for the assembled cut, when there is NO script to align to (with a script: align.py + cut_words.py,
so the captions say exactly what the creator wrote).

Usage:  PY transcribe_cut.py <project_dir> ["names and keywords"] [--lang he|en]
Writes words.json (every word) and work/words_cut.json ({i, text, start, end, sent}), the file the template's
captions read; "sent" counts sentences, split after . ? ! :
Whisper mishears names ("Claude" -> "cloud", "skill" -> "scale"): pass them in the prompt and still fix captions by
hand from what the speaker actually said.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402
import speech  # noqa: E402

skillenv.utf8_stdio()
args = sys.argv[1:]
lang = skillenv.config().get('language', 'en')
if '--lang' in args:
    i = args.index('--lang')
    lang = args[i + 1]
    del args[i:i + 2]
proj = skillenv.path_arg(args[0])
prompt = args[1] if len(args) > 1 else None
wav = os.path.join(proj, 'work', 'aroll.wav')
os.makedirs(os.path.join(proj, 'work'), exist_ok=True)
subprocess.run([skillenv.tool('ffmpeg'), '-loglevel', 'error', '-y', '-i', os.path.join(proj, 'assets', 'aroll.mp4'), '-vn', '-ac', '1',
                '-ar', '16000', wav], check=True)
_, ws = speech.transcribe(wav, lang, 'cut', prompt)
with open(os.path.join(proj, 'words.json'), 'w', encoding='utf-8') as fh:
    json.dump(ws, fh, indent=1, ensure_ascii=False)
out, sent = [], 0
for i, w in enumerate(ws):
    out.append({'i': i, **w, 'sent': sent})
    if w['text'][-1:] in '.?!:':
        sent += 1
with open(os.path.join(proj, 'work', 'words_cut.json'), 'w', encoding='utf-8') as fh:
    json.dump(out, fh, indent=0, ensure_ascii=False)
print(' '.join(f"{w['i']}:{w['text']}@{w['start']:.2f}" for w in out))
