#!/usr/bin/env python3
"""Speech-to-text shared by ingest.py and transcribe_cut.py (needs the skill's venv: faster-whisper).

transcribe(wav, lang, stage, prompt) -> (segments, words)
  lang 'he' -> ivrit.ai's Hebrew Whisper (large-v3-turbo, CT2); 'en' -> small.en / medium.en (skillenv.WHISPER).
  Always on the CPU: 'auto' picks CUDA on any PC with an NVIDIA card and dies without the CUDA toolkit.
  Prompt safety: Whisper can silently SKIP the opening words of a clip when they also appear in initial_prompt
  (a reel lost "היום הבחירות בישראל" this way). With a prompt, the first OPENING seconds are transcribed again
  without it, and whichever pass heard more words there wins for that stretch.
"""
import os
import subprocess
import sys
import tempfile

from faster_whisper import WhisperModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

OPENING = 8.0
_models = {}


def model(name):
    if name not in _models:
        _models[name] = WhisperModel(name, device='cpu', compute_type='int8')
    return _models[name]


def _words(segs, offset=0.0):
    return [{'text': w.word.strip(), 'start': round(w.start + offset, 3), 'end': round(w.end + offset, 3)}
            for s in segs for w in s.words if w.word.strip()]


def _run(m, wav, lang, prompt):
    kw = {'word_timestamps': True, 'vad_filter': False, 'beam_size': 5, 'initial_prompt': prompt}
    if m.model.is_multilingual:   # small.en / medium.en are English-only and take no language
        kw['language'] = lang
    segs, _ = m.transcribe(wav, **kw)
    return list(segs)


def transcribe(wav, lang, stage, prompt=None):
    m = model(skillenv.whisper_model(lang, stage))
    segs = _run(m, wav, lang, prompt)
    words = _words(segs)
    if not prompt or not words:
        return segs, words
    with tempfile.TemporaryDirectory() as d:
        head = os.path.join(d, 'head.wav')
        subprocess.run([skillenv.tool('ffmpeg'), '-loglevel', 'error', '-y', '-i', wav, '-t', str(OPENING), head], check=True)
        bare = _words(_run(m, head, lang, None))
    # compare up to the last word the bare pass finished well inside the window (its final word may be cut off)
    bare = [w for w in bare if w['end'] <= OPENING - 1.0]
    if not bare:
        return segs, words
    cut = bare[-1]['end']
    prompted = [w for w in words if w['start'] < cut]
    if len(bare) > len(prompted):
        print(f'  opening re-transcribed without the prompt: {len(bare)} words instead of {len(prompted)} '
              f'in the first {cut:.1f}s', flush=True)
        words = bare + [w for w in words if w['start'] >= cut]
    return segs, words
