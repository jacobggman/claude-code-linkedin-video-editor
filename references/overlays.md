# UI recreations and animated inserts (built by parallel sub-agents)

The main session owns the cut, grade, captions and integration; each animated insert (app recreation, social UI,
code file scroll) is delegated to its own sub-agent (Opus if available) working in its own folder, in parallel.

## Pattern
1. Lock the insert's timing to the speaker's words first (word timings from transcribe_cut.py / the clip's words json).
   Convert to the insert's own clock: insert t=0 at a known source moment, every beat = word time - that moment.
2. Spawn one sub-agent per insert (Agent tool, `model: opus`, `run_in_background: true`), all in parallel.
3. Each agent builds a standalone HyperFrames project in `<project>/agents/<name>/` and renders a TRANSPARENT VP9 WebM
   at a fixed size and duration. The main build places it with a wrapper div (position/scale/tilt) and a timed `<video>`.
4. When an agent reports back, read its notes (things it flags as "might look off" are usually real, e.g. a grid
   thumbnail with an off-brand title). Send fixes back with SendMessage instead of redoing the work.

## Brief template (fill every bracket; the specifics are what make the result good)
`[PY]` and `[skill]` are the `python` and `skill_dir` values from `.platform.json` (full paths, so the sub-agent
runs the same commands on Mac, Linux and Windows).
```
Build ONE short animated UI clip with HyperFrames: [what it shows]. It plays in a LinkedIn video while [speaker]
says "[line]", so it must look premium, realistic and readable on a phone. Hebrew text: right to left,
Heebo (copy fonts-he.css + its woff2), see [skill]/references/hebrew.md.

Where to work: [project]/agents/[name]/ (touch nothing else). Inputs: [files]. Copy setup (fonts.css + woff2,
hyperframes.json, package.json) from [project]/ ; mirror [skill]/assets/overlay-examples/[closest]/ for structure.

Output: composition [W x H], transparent background outside a [window/card] with ~[R]px rounded corners (corners
transparent, inside opaque). Duration [D]s, 30fps. Render renders/[name].webm with --format webm. Verify alpha
(ffprobe alpha_mode=1; decode a frame with -c:v libvpx-vp9 and check a corner pixel is transparent).

Look: [palette, fonts, real data to show, generic placeholders for anything that isn't real; no copied logos].
Readable sizes: key text >= 24px at the size it will be shown. Where it will be placed: [x, y, scale]; once
placed it must sit inside the LinkedIn safe zone (y 340-1620, x 40-1040, and x 160-920 below y 1100).

Timeline (seconds, locked to the voice, keep within ±0.05s): [beat list].

HyperFrames rules: run it as `"[PY]" "[skill]/scripts/hf.py" <lint|snapshot|render ...>` from your folder (pinned
hyperframes@0.8.34 with Node 22+, same command on Mac, Linux and Windows; in PowerShell put `&` in front), run
build.py with "[PY]" and write index.html with encoding='utf-8', root div with data-composition-id/start/duration/
width/height, paused GSAP timeline registered in window.__timelines["main"], gsap.set for initial states OUTSIDE the
timeline, immediateRender:false on fromTo, no apostrophes in ids, no onUpdate text tricks (one span per typed
character revealed with tl.set), lint 0 errors, snapshot and LOOK at the PNGs, then render. Never delete files.

Report back: path, exact duration, alpha confirmed, actual beat times (for sound effects), anything that looks off.
```

## Example inserts (assets/overlay-examples/ has their index.html / build.py)
- **claude-desktop** (1000x720, 4.35s): Claude desktop light theme, 5 clip thumbnails dragged into the input with a
  count badge, `/video-edit` typed with a slash-command menu, Claude reply with a "Using skill" pill and a checklist
  ending in a "reel.mp4 · ready" file card. Placed on the wall BEHIND the speaker (z between base video and cutout).
- **ig-follow** (760x1000, 2.9s): the creator's IG profile in dark mode (profile pic, verified badge, posts /
  followers / following, bio, post grid from their reels), a touch dot taps Follow at 0.70s (button -> Following),
  the comment sheet slides up, the CTA keyword is typed and posted at 1.75s. Scaled .7 under the chin in the CTA.
  Click sounds at the two taps. Fill it with the user's REAL numbers (handle from config.json; pull stats with an
  Instagram profile scraper on Apify if connected, otherwise ask). Example commenters must stay generic placeholders.
- **skill-md** (860x1000, 2.15s): dark code editor showing a SKILL.md with markdown highlighting, a smooth eased
  scroll on a wrapper `y`, a line glow as a section passes. Scaled .72 with a slight rotateX tilt under the face.

## Creator reels as cards
Instagram: Apify's official Instagram scraper (pay-per-use; currently `apify/instagram-scraper` with `directUrls`
and `resultsType: posts`) returns a `videoUrl` you can curl. Pinterest pins: the pin page HTML contains
`v1.pinimg.com/videos/.../*_720w.mp4`. Transcribe to pick the 2-3s that match the line. Trim to 260x462 tiles,
muted, `-g 30`. Always show the @handle.

The creator's own reels (for the orbit, the profile grid): Apify's official Instagram post scraper with the handle
from config.json, 6 reels, trim each to 300x534 muted tiles. Without Apify, ask the user to drop 6 of their reels
into the project's `assets/reels/` folder.

## The LinkedIn card (default ending, built into the template, no sub-agent)
`linkedin_card()` in the template: white card, LinkedIn logo, round photo (config "photo"), name (config "name"),
the "let's connect" line (config "linkedinSubtitle", "בואו נתחבר בלינקדאין!" / "Let's connect on LinkedIn!"), a blue
"+ Connect" button that a touch dot taps after 1s -> outlined "✓ Pending", whoosh / click / chime. The creator approved
this exact look: keep it as is on every reel; only the text and photo come from config.json.

The ig-follow example above is from the Instagram version of this skill; on LinkedIn the card replaces it.
