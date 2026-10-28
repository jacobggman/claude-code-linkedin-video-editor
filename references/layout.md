# Layout rules (1080x1920)

## LinkedIn safe zone (HARD)
Measured on the LinkedIn iPhone app, Hebrew UI, from a real post (feed + full-screen viewer), Oct 2026. The numbers
live in one place, `scripts/skillenv.py` `SAFE`; the template's guide, its warnings and `safe_check.py` read them.

| zone | covers | rule |
|---|---|---|
| **top 340** | feed: the card crops 9:16 to 2:3 (~150px off the top) and lays name / headline / "18h" over the top to ~331 | nothing important above **y = 340** |
| **bottom 1620** | full screen: avatar, name, headline, post text from ~1663. Feed: post text + mute button from ~1627, crop from 1770 | nothing below **y = 1620** |
| **action bars 160** | full screen: like / count / comment / repost / send / "..." column, 44-132px wide, from y ~1127. **Left in the Hebrew UI, right in the English UI**, so both are reserved | nothing in **x < 160 or x > 920 below y = 1100**, and that includes the speaker's face |
| sides 40 | breathing room | nothing in x < 40 or x > 1040 |

The first post lost its headline: "הייתם נותנים ל-AI" sat at y 226-320, right under the feed's name and headline.
Hook text starts at y >= 352.

Check it, do not eyeball it:
1. `PY build.py --safe`: the template prints `SAFE ZONE ...` for every element whose box (left / top / width / height
   in its style) reaches into the zone, then `safe zone: OK`. Elements without a height are only checked at the top.
2. Snapshots with the red guide on (10-20 moments). Fix, then build WITHOUT `--safe` for the render
   (grep the html for `rgba(255,0,0,.28)` -> must be 0).
3. After the render: `PY SK/scripts/safe_check.py renders/<slug>-vN.mp4` paints the zone on frames of the real file.

## Speaker layouts (green screen / any keyed subject)
`subject.webm` is the full frame; `#subj` scales it from the bottom centre. At scale s the head top is at
1920 - 1760*s, the eyes at 1920 - 1360*s, the chin at 1920 - 750*s (for a phone selfie framing; check headpos.py).

| layout | scale | head top | captions (CAP_Y) | room for |
|---|---|---|---|---|
| FULL | 1.0 | 160 | 1290 | punch moments, no top inserts (hook text 352-536 stays above the eyes at 560) |
| MID | .80 | 512 | 1336 | behind-head words up to S = 238, small cards up to y ~500 |
| LOW | .68 | 723 | 1424 | a full-width card or diagram in 350-700 |
| SL / SR | .62 | 829 | 1462 | a 440px panel on the other side, y 360-1090 |

SL / SR place the head by measurement, not by a fixed slide: `side_x()` reads `work/headpos.json` and centres the
head in the gap between the action bar (x 160) and the panel (x 596). A fixed slide put the jaw under LinkedIn's
icons whenever the speaker leaned. Panels on the right side end at y <= 1090 (the right action bar starts at 1100).

## Where things go
- Captions: one line, under the chin, centred, at most ~16 characters per chunk so the line stays inside x 160-920.
- Behind-head words: `bword()`; `top = head_top - .68 * S` (Heebo's Hebrew letters are ~.73em tall: this keeps
  ~75% of each letter clear of the hair). Must stay >= 340: the template warns and tells you the largest S that fits.
  Show them at least .4s after a layout change, or they land on a head that is still moving.
- Cards: inside 340-1620 and 40-1040; below y 1100 also inside 160-920. Never over the face (eyes to chin).
- The ending: the speaker leaves (exit tween) and the LinkedIn card sits alone at y 640-1060, centred.

## Cut timing
Cut times = first frame of each segment from segments.json: `frame/30 - 0.002`. The 2ms nudge makes a `tl.set` land ON
the first frame of the new shot (without it, float rounding fires it one frame late and the next shot shows the old
shot's overlays for a frame).
