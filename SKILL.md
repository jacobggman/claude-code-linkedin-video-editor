---
name: video-edit-linkedin
description: "Turns a raw 9:16 talking-head video (Hebrew or English, green screen or a real room, any frame rate) into a finished LinkedIn video: strong hook from the first frame, karaoke captions in the creator's exact words (right to left for Hebrew), a designed background per section behind a keyed speaker, animated cards, counters and real photos, subtle sound design, everything inside LinkedIn's safe zone (feed header on top, post text at the bottom, the action bar on either side), and the LinkedIn Connect card as the ending. Trigger with /video-edit-linkedin or phrases like 'edit this video for LinkedIn', 'ערוך לי את הסרטון'."
---

# /video-edit-linkedin

Raw video in, finished LinkedIn video out. The creator never opens an editor: they review a phone copy and give
notes; every round is a ~12 minute re-render on a laptop CPU. Built from /video-edit (by @tenfoldmarc) and the first
reel made with it for LinkedIn: "GPT vs Grok", Hebrew, green screen, 25fps. That reel is the template.

Read before building: `references/layout.md` (the LinkedIn safe zone, speaker layouts, placement),
`references/hebrew.md` (Hebrew speech-to-text, RTL captions, fonts), `references/gotchas.md` (every trap already hit
once), `references/looks.md` (looks, exact values). `references/overlays.md` when an insert needs a sub-agent.

## Step 0: Setup

`SK` = this skill's folder (holds this SKILL.md), as a full path: `C:/Users/<name>/.claude/skills/video-edit-linkedin`
on Windows, `~/.claude/skills/video-edit-linkedin` elsewhere.

Run the setup script every time (seconds when nothing is missing): `python "SK/scripts/setup.py"` (or `python3`, or
`py -3`). It checks ffmpeg, Node 22+, the skill's own Python environment and the 19 sound effects, prints a STATUS line
per item with the exact fix for this machine, then READY. Missing ffmpeg/Node/Python on Windows: the user pastes the
winget line into PowerShell. A program installed while Claude Code is open is not on PATH yet: run setup.py again with
its folder prepended to PATH (gotchas.md) instead of asking for a restart.

`SK/config.json` holds the creator: `name`, `photo` (their real profile photo, used on the LinkedIn card),
`linkedinSubtitle` per language, `language` (he / en), `clipsDir`, `projectsDir`. Missing: ask for the name, the
photo (a file path: a photo pasted into the chat is NOT a file, ask them to save it), the default language, and
write it. Never secrets.

## This machine
Read `SK/.platform.json` (written by setup.py): `PY` = its `python` (the skill's venv), `HF` = `PY "SK/scripts/hf.py"`
(pinned HyperFrames with the right Node). Full paths in double quotes with forward slashes, one command per call; in
PowerShell put `&` in front. Run every script of this skill with PY.

## Hard rules
1. **LinkedIn safe zone** (layout.md): nothing important above y 340 or below y 1620, nothing in x < 160 or x > 920
   below y 1100 (the action bar: left in the Hebrew UI, right in the English UI), 40px side margins. The speaker's
   face counts. The template warns about every element that crosses it; snapshot with `--safe`; check the render
   with safe_check.py.
2. Never cover the face (eyes to chin) with text or cards. Behind-head words keep ~75% of each letter visible.
3. Captions say exactly what was said. The creator's script, when given, wins over Whisper (align.py).
   No em dashes in on-screen text. Facts and numbers on screen are checked against the source (search for it).
4. The first frame is the preview: the hook headline is readable at t=0, inside the safe zone.
5. Sound effects subtle and level-matched (LEVEL), never louder than the voice; master to -16 LUFS after rendering.
6. Lip sync is verified (sync_check.py) and cuts are proven from the final render (check_cuts.py), not snapshots.
7. The ending is always the LinkedIn card (`linkedin_card()`, approved design): the speaker leaves the frame, no
   frozen frame, no looping clip.
8. Never delete the user's files. Originals are read, never modified.

## Workflow

### 1. Intake
- The clip(s) the user names, else the newest in `clipsDir`. Project: `<projectsDir>/<short-slug>/`.
- Ask for (or use) the script if they have it: save it as `<project>/script.txt`. It fixes every caption.
- Images / sound / music: real images over AI ones (Wikimedia Commons first, credit CC-BY authors on the photo and in
  CREDITS.txt). No music by default: voice + sound effects. Research the topic's facts (the post will be read by
  professionals) and the hook if unsure.

### 2. Ingest
```bash
PY SK/scripts/ingest.py <project> <clip> --lang he --prompt "names, keywords"
```
Look at `work/sheets.jpg`: setups, angles, and **green screen or not**. Read `transcript.txt`. ingest prints each
clip's size and frame rate; any rate works (25fps phone exports included).

### 3. Script and cut
- With a script: `PY SK/scripts/align.py <project> <project>/script.txt` (check the first sentence is there).
- One continuous take: `PY SK/scripts/make_edl.py <project>` keeps it WHOLE, pauses included (one segment). **Do not
  cut the pauses**: the creator speaks in one flow, and when the first reel's pauses were cut they said it looked
  choppy. Only if they ask: `--cut-pauses` (`--keep <silence start>:<s>` keeps a dramatic beat). Several takes of each
  line: build edl.json by hand, LAST clean take of each line, and keep each take's natural pauses.
- Post the cut list to the user as a short table and keep going.

### 4. Assemble, verify sync, key, track the head
```bash
PY SK/scripts/assemble.py <project>          # frame-locked 30fps cut + .5s hold for the exit
PY SK/scripts/sync_check.py <project>        # must say SYNC OK
PY SK/scripts/key.py <project>               # green screen -> subject.webm in minutes (exit 2 = not green:)
PY SK/scripts/cutout.py <project>            # ...then the AI matte instead, in the background (slow on CPU)
PY SK/scripts/headpos.py <project>           # work/headpos.json: places the speaker in side layouts
PY SK/scripts/cut_words.py <project>         # with a script: work/words_cut.json (+ .txt with word indices)
PY SK/scripts/transcribe_cut.py <project> "names" --lang he   # without a script, instead of cut_words.py
```

### 5. Inserts
Most inserts are HTML in build.py itself (cards, counters, dot grids, toggles, search bars, photo cards, the
LinkedIn card): consistent styling, timed to word indices. Spawn a sub-agent (overlays.md) only for a big app
recreation.

### 6. Build
Copy `SK/assets/template/` into the project (build.py, hyperframes.json, package.json, assets/fonts, assets/sfx).
build.py is the finished GPT vs Grok reel: keep the machinery, rewrite the content (its docstring lists which is
which). Green screen: `BG_MODE = 'keyed'` and design PLATES per section. Real room: `BG_MODE = 'room'`.
Iterate from the project folder: `PY build.py --safe` (read the SAFE ZONE lines), `HF lint` (0 errors), then
`HF snapshot --at <15-25 moments> --no-end --describe false`. Look at every contact sheet: safe zone, face, overlaps,
text that wraps or overflows its card, behind-head readability.

### 7. Render, master, QA
```bash
PY build.py
HF render -o renders/<slug>-vN-raw.mp4 --quality high              # ~11 min for 80s on an 8-core laptop
ffmpeg -i renders/<slug>-vN-raw.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a aac -b:a 192k -movflags +faststart renders/<slug>-vN.mp4
PY SK/scripts/check_cuts.py <project> renders/<slug>-vN.mp4 --phone
PY SK/scripts/safe_check.py renders/<slug>-vN.mp4
```
Look at `work/cut_check.jpg` and `work/safe_check.jpg`, and pull the last frames to see the ending.

### 8. Deliver
Send the phone copy and point to the full-quality file. Say what changed and what needs their call. Keep every
version in `renders/`.

## Defaults from real feedback (do not re-litigate)
- Hook: one bold question headline from frame 0 that ties the topic to what the audience lives today, motion and
  sound in the first second. The creator's own opening line is the hook; do not reorder the script.
- Keep the take whole: no cutting of quiet parts or breaths (it looked choppy; they already talk in flow). Movement
  comes from layouts, inserts and punch-ins, not from jump cuts.
- Karaoke captions: the spoken word in yellow, keywords keep a colour.
- Real images, credited. No music unless asked.
- Ending: the speaker leaves, the LinkedIn card ("בואו נתחבר בלינקדאין!" with "!", real photo, Connect -> Pending).

---
Based on /video-edit by [@tenfoldmarc](https://instagram.com/tenfoldmarc). LinkedIn safe zone, Hebrew pipeline,
green-screen keying and frame-locked assembly added for Jacob Galam's LinkedIn videos.
