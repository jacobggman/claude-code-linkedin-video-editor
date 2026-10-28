# Notice: third-party work in this repository

This skill is built on **/video-edit** by tenfoldmarc
(https://github.com/tenfoldmarc/video-edit-skill, commit 3f01f2e), a Claude Code skill for Instagram reels.
That repository does not state a license. Its files below are included with credit, and they remain the work of
their author. The MIT License in [LICENSE](LICENSE) covers only the contributions made in this repository.

**Included unchanged from /video-edit**
- `scripts/cutout.py`, `scripts/cutout.sh`, `scripts/hf.py`, `scripts/setup.sh`
- `tests/test_platform.py`
- `references/looks.md`
- `assets/overlay-examples/` (claude-desktop, ig-follow, skill-md)
- `assets/template/hyperframes.json`, `assets/template/package.json`, `assets/template/assets/fonts/fonts.css`

**Adapted from /video-edit** (LinkedIn, Hebrew and frame-rate changes made here)
- `scripts/setup.py`, `scripts/skillenv.py`, `scripts/check_cuts.py`, `scripts/headpos.py`,
  `scripts/transcribe_cut.py`, `scripts/ingest.py`, `scripts/assemble.py`
- `SKILL.md`, `references/gotchas.md`, `references/layout.md`, `references/overlays.md`
- `assets/template/build.py` (rewritten as a finished LinkedIn video)

**Written for this repository**
- `scripts/align.py`, `scripts/cut_words.py`, `scripts/key.py`, `scripts/make_edl.py`, `scripts/safe_check.py`,
  `scripts/speech.py`, `scripts/sync_check.py`
- `references/hebrew.md`, `assets/template/assets/fonts/fonts-he.css`, `docs/`

**Other third-party components**
- Fonts in `assets/template/assets/fonts/`: Google Fonts, SIL Open Font License 1.1 (see `OFL.txt` there).
- Sound effects: Pixabay Content License. They are downloaded by `scripts/setup.py` from the HyperFrames project
  and are not stored in this repository.
- HyperFrames (https://github.com/heygen-com/hyperframes), faster-whisper (https://github.com/SYSTRAN/faster-whisper)
  and the ivrit.ai Hebrew Whisper model (https://huggingface.co/ivrit-ai) are installed at setup, not bundled.

LinkedIn is a trademark of LinkedIn Corporation. This project is not affiliated with or endorsed by LinkedIn.
