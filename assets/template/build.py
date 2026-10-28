#!/usr/bin/env python3
"""/video-edit-linkedin template: the finished build of a real reel, "GPT vs Grok: political bias" (Hebrew, 78s,
one continuous take on a green screen, posted on LinkedIn). Copy it into a project, keep the machinery, rewrite
the content.

Machinery to keep:
  speaker layouts      LAY / SCHED / subject(): the keyed speaker scales and slides between FULL, MID, LOW and
                       side-by-side SL / SR; captions ride along (CAP_Y); jump cuts get an alternating 5% punch-in
  designed background  PLATES (images with a Ken Burns drift or gradients, cross-faded per section) + grid + glow()
  helpers              el() (enter / exit, checks every element against the LinkedIn safe zone), bword() (word
                       behind the head), counter(), typed(), pop_in(), pulse(), badge(), photo(), arrow(), CHECK/CROSS
  captions             captions(): karaoke, current word in YEL, keywords keep a colour (kw_color()), RTL for Hebrew
  ending               subject() exit + linkedin_card(): the speaker leaves after the last word, the LinkedIn card
                       (photo, name, "let's connect" line, Connect -> Pending tap) plays alone. The default ending.
  sound                SFX + LEVEL (the pack is not level-matched) + audio() lane allocator
  safe zone            ZONE = skillenv.SAFE, SAFE_GUIDE (--safe), and warnings printed for anything placed in it
Content to rewrite: the section functions (hook ... cta), PLATES, GLOW, SCHED, SFX, kw_color() keywords, colours.
Times are word indices: WT(i) = start of word i in work/words_cut.json (see work/words_cut.txt), T['sNN'] = cuts.

Settings from <skill>/config.json: language (he = right to left), name, linkedinSubtitle, photo.
BG_MODE: 'keyed' = green-screen footage keyed by scripts/key.py, the room is designed (PLATES). 'room' = real
background (subject.webm from scripts/cutout.py): aroll.mp4 plays under the cutout inside the same moving frame,
so layouts shrink the whole shot as a framed tile over the plates; prefer FULL / MID there.

Run from the project folder:  PY build.py [--safe]     (--safe draws the red safe-zone guide, snapshots only)
"""
import json
import os
import re
import shutil
import subprocess
import sys

SK = os.environ.get('VIDEO_EDIT_LINKEDIN_SK') or os.path.expanduser('~/.claude/skills/video-edit-linkedin')
sys.path.insert(0, os.path.join(SK, 'scripts'))
import skillenv  # noqa: E402

SAFE = '--safe' in sys.argv or bool(os.environ.get('SAFE'))
ZONE = skillenv.SAFE          # LinkedIn: top 340, bottom 1620, side 40, action bars 160 wide from y 1100 (both sides)
CFG = skillenv.config()
LANG = CFG.get('language', 'he')
DIR = 'rtl' if LANG == 'he' else 'ltr'
BG_MODE = 'keyed'
LI_NAME = CFG.get('name', 'Your Name')
LI_SUB = (CFG.get('linkedinSubtitle') or {}).get(LANG) or {'he': 'בואו נתחבר בלינקדאין!'}.get(LANG, "Let's connect on LinkedIn!")


def _dur(f):
    """video stream duration (webm only has it on the container, so fall back to that)"""
    for entry in ('stream=duration', 'format=duration'):
        out = subprocess.run([skillenv.tool('ffprobe'), '-v', 'error', '-select_streams', 'v:0', '-show_entries', entry,
                              '-of', 'csv=p=0', f], **skillenv.TEXT).stdout.strip()
        if out and out != 'N/A':
            return float(out)
    raise SystemExit(f'no duration for {f}')


with open('segments.json', encoding='utf-8') as _f:
    SEGS = json.load(_f)
T = {s['id']: s['frame'] / 30 for s in SEGS}
# end of speech: the speaker leaves the frame (EXIT seconds, over aroll's held last frame) and the LinkedIn card
# plays alone for the rest of TAIL
FREEZE = (SEGS[-1]['frame'] + SEGS[-1]['frames']) / 30
TAIL, EXIT = 2.6, .45
DUR = FREEZE + TAIL
AROLL = min(DUR, _dur('assets/aroll.mp4'))   # voice track; silent after FREEZE
with open('work/words_cut.json', encoding='utf-8') as _f:
    W = json.load(_f)


def WT(i):
    return W[i]['start']


YEL, GPT_C, GROK_C, DEM_C, REP_C = '#FAE67A', '#3DDC97', '#B79CFF', '#6EA8FF', '#FF6B6B'
INK = '#0B0F1A'

# ------------------------------------------------------------------ speaker layouts
# subject.webm is the full 1080x1920 frame; #subj scales it from the bottom centre. At scale s the head top sits at
# 1920 - 1760*s, the eyes at 1920 - 1360*s and the chin at 1920 - 750*s.
# SL / SR (speaker left or right, panel on the other side): x is not fixed. side_x() reads work/headpos.json
# (scripts/headpos.py) and centres HIS HEAD, wherever it sits in the source frame, in the gap between LinkedIn's
# action bar (x < 160 below y 1100, both sides) and the panel (x 596-1036 / 44-484). A fixed slide put the jaw under
# the icons whenever the speaker leaned. At .62 the head (~700px wide in the source) fits that 436px gap.
LAY = {'FULL': (1.0, 0), 'MID': (.80, 0), 'LOW': (.68, 0), 'SL': (.62, None), 'SR': (.62, None)}
CAP_Y = {'FULL': 1290, 'MID': 1336, 'LOW': 1424, 'SL': 1462, 'SR': 1462}   # caption line top: under the chin, above SAFE bottom
GAP_CX = {'SL': (ZONE['bar_w'] + 596) / 2, 'SR': 1080 - (ZONE['bar_w'] + 596) / 2}   # where the head's centre goes
try:
    with open('work/headpos.json', encoding='utf-8') as _f:
        HEADPOS = json.load(_f)
except OSError:
    HEADPOS = {}
    print('no work/headpos.json: run scripts/headpos.py, side layouts assume a centred head')
SCHED = [(0.0, 'MID'), (T['s02'], 'LOW'), (T['s04'], 'MID'), (T['s06'], 'FULL'), (T['s07'], 'SL'), (T['s08'], 'SR'),
         (WT(56) - .05, 'LOW'), (WT(61) - .05, 'MID'), (T['s10'], 'SL'), (T['s11'], 'SR'), (T['s12'], 'LOW'),
         (T['s15'], 'SL'), (T['s16'], 'SR'), (T['s17'], 'FULL'), (WT(118) - .5, 'MID'), (WT(121) - .05, 'LOW'),
         (T['s22'], 'MID'), (WT(157) - .1, 'LOW'), (T['s24'], 'MID')]


def lay_at(t):
    return [n for a, n in SCHED if a <= t + 1e-6][-1]


def head_top(t):
    return 1920 - 1760 * LAY[lay_at(t)][0]


def side_x(n, t0, t1):
    """slide for a side layout: the head's centre (median over the segments shown from t0 to t1) lands on GAP_CX.
    #subj scales from x 540, so a source x lands at 540 + (x - 540) * s + slide."""
    s = LAY[n][0]
    # time samples inside the window (headpos.py samples long segments every ~2s), else the segments' medians
    cxs = [x['cx'] for h in HEADPOS.values() for x in h.get('samples', []) if t0 - 1 <= x['t'] <= t1 + 1]
    cxs = cxs or [HEADPOS[g['id']]['cx'] for g in SEGS
                  if g['id'] in HEADPOS and g['frame'] / 30 < t1 and (g['frame'] + g['frames']) / 30 > t0]
    cx = sorted(cxs)[len(cxs) // 2] if cxs else 540
    return round(GAP_CX[n] - 540 - (cx - 540) * s)


def subject():
    s0 = LAY['MID'][0]
    tw = ["gsap.set('#subj',{scale:.92,x:0});", f"gsap.set('#capbox',{{y:{CAP_Y['FULL']}}});",
          f"tl.to('#subj',{{scale:{s0},duration:.6,ease:'power3.out'}},0.02);",
          f"tl.to('#capbox',{{y:{CAP_Y['MID']},duration:.6,ease:'power3.out'}},0.02);"]
    lay_ts = [t for t, _ in SCHED]
    for i, (t, n) in enumerate(SCHED[1:], 1):
        s, x = LAY[n]
        if x is None:
            x = side_x(n, t, SCHED[i + 1][0] if i + 1 < len(SCHED) else FREEZE)
        tw += [f"tl.to('#subj',{{scale:{s},x:{x},duration:.42,ease:'power3.inOut'}},{t - .06:.3f});",
               f"tl.to('#capbox',{{y:{CAP_Y[n]},duration:.42,ease:'power3.inOut'}},{t - .06:.3f});",
               f"tl.set('#punch',{{scale:1}},{t:.3f});"]
    # jump cuts inside one layout: alternate a 5% punch-in so the cut reads as intentional
    k = 0
    for s in SEGS[1:]:
        t = s['frame'] / 30
        if any(abs(t - a) < .3 for a in lay_ts):
            continue
        k += 1
        tw.append(f"tl.set('#punch',{{scale:{1.05 if k % 2 else 1}}},{t - .002:.3f});")
    # "the results are surprising": camera shake on the last word
    kf = ','.join(f"{{x:{x},duration:.035}}" for x in (-14, 12, -10, 9, -6, 4, 0))
    tw.append(f"tl.to('#punch',{{keyframes:[{kf}]}},{WT(44) + .1:.3f});")
    # "and that's the point": slow push-in on the full shot
    tw.append(f"tl.fromTo('#punch',{{scale:1}},{{scale:1.06,duration:{WT(118) - .5 - T['s17']:.3f},ease:'none',immediateRender:false}},{T['s17']:.3f});")
    # end of speech: the speaker leaves the frame (shrinks back, blurs, fades) so the LinkedIn card plays alone
    tw.append(f"tl.to('#subj',{{scale:.55,y:260,autoAlpha:0,filter:'blur(18px)',duration:{EXIT},ease:'power3.in'}},{FREEZE - .02:.3f});")
    return tw


# ------------------------------------------------------------------ background plates
DARK = 'radial-gradient(120% 80% at 50% 28%,#1b2444 0%,#0a0e1c 62%,#05070d 100%)'
PLATES = [  # (id, t_in, kind, value, css)
    ('pk', 0.0, 'img', 'kalpi.jpg', 'filter:blur(3px) brightness(.5) saturate(1.15)'),
    ('pd1', T['s02'], 'grad', DARK, ''),
    ('pcap', T['s04'], 'img', 'capitol.jpg', 'filter:blur(2px) brightness(.42) saturate(1.1)'),
    ('pblk', T['s06'], 'grad', '#000', ''),
    ('pblue', T['s07'], 'grad', 'radial-gradient(110% 80% at 72% 30%,#2453d8 0%,#0c1c4e 55%,#050a1e 100%)', ''),
    ('pred', T['s08'], 'grad', 'radial-gradient(110% 80% at 28% 30%,#c4203c 0%,#4a0b16 55%,#1e0508 100%)', ''),
    ('psplit', WT(56) - .05, 'grad', 'linear-gradient(90deg,#4a0c18 0%,#17102a 50%,#0c1d4a 100%)', ''),
    ('pd2', WT(61) - .05, 'grad', DARK, ''),
    ('pgpt', T['s10'], 'grad', 'radial-gradient(110% 80% at 72% 30%,#11684b 0%,#06281d 55%,#030d0a 100%)', ''),
    ('pgrok', T['s11'], 'grad', 'radial-gradient(110% 80% at 28% 30%,#3d3656 0%,#141019 60%,#050507 100%)', ''),
    ('pd3', T['s12'], 'grad', DARK, ''),
    ('pspot', T['s17'], 'grad', 'radial-gradient(62% 46% at 50% 42%,#4a3f1c 0%,#0c0a06 72%,#000 100%)', ''),
    ('pd4', WT(121) - .05, 'grad', DARK, ''),
    ('pcap2', WT(133) - .1, 'img', 'capitol.jpg', 'filter:blur(5px) brightness(.3) saturate(1.05)'),
    ('pd5', WT(136) - .1, 'grad', DARK, ''),
    ('pcode', T['s22'], 'grad', 'radial-gradient(120% 80% at 50% 28%,#0f3333 0%,#061314 62%,#020707 100%)', ''),
    ('pk2', T['s24'], 'img', 'kalpi.jpg', 'filter:blur(7px) brightness(.36) saturate(1.1)'),
]


BG0 = '#05070d'   # #bgwrap's own background: an opening gradient plate lives here, not as an element


def plates():
    global BG0
    html, tw = [], []
    for k, (pid, a, kind, val, css) in enumerate(PLATES):
        b = PLATES[k + 1][1] if k + 1 < len(PLATES) else DUR
        if a == 0 and kind == 'grad':
            # a full-frame element visible from frame 0 fails HyperFrames lint (gsap_fullscreen_overlay_starts_visible):
            # paint the first gradient on #bgwrap itself; later plates fade in over it
            BG0 = val
            continue
        if kind == 'img':
            html.append(f'<div id="{pid}" class="plate"><img src="assets/img/{val}" style="{css}"></div>')
        else:
            html.append(f'<div id="{pid}" class="plate" style="background:{val}"></div>')
        if a == 0:
            tw.append(f"gsap.set('#{pid}',{{autoAlpha:1}});")
        else:
            tw.append(f"gsap.set('#{pid}',{{autoAlpha:0}});")
            tw.append(f"tl.to('#{pid}',{{autoAlpha:1,duration:.35}},{a - .05:.3f});")
        if kind == 'img':   # slow Ken Burns while it is on screen
            tw.append(f"tl.fromTo('#{pid} img',{{scale:1.14}},{{scale:1.0,duration:{b - a + .4:.3f},ease:'none',immediateRender:false}},{a:.3f});")
        if b < DUR:
            tw.append(f"tl.set('#{pid}',{{autoAlpha:0}},{b + .4:.3f});")
    return html, tw


GLOW = [(0, YEL), (T['s07'], DEM_C), (T['s08'], REP_C), (WT(56), GROK_C), (WT(61), YEL), (T['s10'], GPT_C),
        (T['s11'], GROK_C), (T['s12'], YEL), (T['s15'], DEM_C), (T['s16'], GROK_C), (T['s17'], YEL), (T['s22'], GPT_C),
        (T['s24'], YEL)]


def glow():
    tw = [f"gsap.set('#glow',{{color:'{GLOW[0][1]}',opacity:.42}});"]
    tw += [f"tl.to('#glow',{{color:'{c}',duration:.4}},{t:.3f});" for t, c in GLOW[1:]]
    tw += [f"tl.to('#glow',{{opacity:.85,duration:.5}},{T['s17']:.3f});", f"tl.to('#glow',{{opacity:.42,duration:.5}},{WT(121):.3f});"]
    tw.append(f"tl.fromTo('#grid',{{backgroundPosition:'0px 0px'}},{{backgroundPosition:'0px 864px',duration:{DUR:.3f},ease:'none',immediateRender:false}},0);")
    return tw


# ------------------------------------------------------------------ element helpers
FRONT, BACKL, TW = [], [], []
ENTER = {'pop': ('scale:.55,y:50', ''), 'up': ('y:140', ''), 'down': ('y:-170', ''), 'left': ('x:-460', ''),
         'right': ('x:460', ''), 'slam': ("scale:1.75,filter:'blur(16px)'", ",filter:'blur(0px)'"), 'fade': ('scale:1.05', '')}


ZONE_WARN = []


def zone_check(eid, style):
    """warn when an element's box (from left / top / width / height in its style) reaches into the safe zone.
    Elements without a height are checked at their top only: look at the snapshots for those."""
    v = {k: int(n) for k, n in re.findall(r'(?<![-\w])(left|top|width|height|min-height):(-?\d+)px', style)}
    top, left, w = v.get('top'), v.get('left'), v.get('width')
    h = v.get('height', v.get('min-height'))
    if top is None:
        return
    bottom = top + h if h else None
    if top < ZONE['top']:
        ZONE_WARN.append(f'{eid}: top {top} < {ZONE["top"]}')
    if bottom and bottom > ZONE['bottom']:
        ZONE_WARN.append(f'{eid}: bottom {bottom} > {ZONE["bottom"]}')
    if left is not None and w and (left < ZONE['side'] or left + w > 1080 - ZONE['side']):
        ZONE_WARN.append(f'{eid}: x {left}-{left + w} outside the {ZONE["side"]}px side margins')
    if left is not None and w and bottom and bottom > ZONE['bar_top'] and (left < ZONE['bar_w'] or left + w > 1080 - ZONE['bar_w']):
        ZONE_WARN.append(f'{eid}: x {left}-{left + w} below y {ZONE["bar_top"]} meets an action bar')


def el(eid, inner, a, b, style, cls='card', enter='pop', layer=None, rot=0, dur=.42, ease='back.out(1.5)'):
    if cls not in ('bw',):
        zone_check(eid, style)
    (FRONT if layer is None else layer).append(f'<div id="{eid}" class="{cls}" style="{style}">{inner}</div>')
    frm, to_extra = ENTER[enter]
    TW.append(f"gsap.set('#{eid}',{{autoAlpha:0,rotation:{rot}}});")
    TW.append(f"tl.fromTo('#{eid}',{{autoAlpha:0,{frm}}},{{autoAlpha:1,x:0,y:0,scale:1{to_extra},duration:{dur},ease:'{ease}',"
              f"immediateRender:false}},{a:.3f});")
    if b is not None and b < DUR - .01:
        TW.append(f"tl.to('#{eid}',{{autoAlpha:0,scale:.9,duration:.16,ease:'power2.in'}},{b - .16:.3f});")
        TW.append(f"tl.set('#{eid}',{{autoAlpha:0}},{b:.3f});")


def tw(s):
    TW.append(s)


def pop_in(sel, t, frm='scale:.4,autoAlpha:0', ease='back.out(2.2)', dur=.32):
    TW.append(f"gsap.set('{sel}',{{autoAlpha:0}});")
    TW.append(f"tl.fromTo('{sel}',{{{frm}}},{{autoAlpha:1,scale:1,x:0,y:0,duration:{dur},ease:'{ease}',immediateRender:false}},{t:.3f});")


def pulse(sel, t, s=1.35):
    TW.append(f"tl.fromTo('{sel}',{{scale:{s}}},{{scale:1,duration:.38,ease:'back.out(3)',immediateRender:false}},{t:.3f});")


def badge(kind, size):
    if kind == 'gpt':
        return (f'<div class="badge" style="width:{size}px;height:{size}px;background:#10A37F">'
                f'<img src="assets/img/chatgpt.png" style="width:{size * .64:.0f}px;filter:invert(1)"></div>')
    return (f'<div class="badge" style="width:{size}px;height:{size}px;background:#000;border:3px solid rgba(255,255,255,.28)">'
            f'<img src="assets/img/grok_symbol.png" style="width:{size * .6:.0f}px;filter:invert(1)"></div>')


def name(kind, size=56):
    return (f'<div class="bname" style="font-size:{size}px;color:{GPT_C if kind == "gpt" else GROK_C}">'
            f'{"GPT" if kind == "gpt" else "Grok"}</div>')


def counter(cid, values, t0, step, cls='cnt', ltr=True):
    """number that counts up: one span per value, swapped with tl.set (no text changes in onUpdate)"""
    spans = ''.join(f'<span id="{cid}{k}" class="cv"{" dir=ltr" if ltr else ""}>{v}</span>' for k, v in enumerate(values))
    TW.append(f"gsap.set('#{cid} .cv',{{autoAlpha:0}});")
    for k in range(len(values)):
        TW.append(f"tl.set('#{cid}{k}',{{autoAlpha:1}},{t0 + k * step:.3f});")
        if k:
            TW.append(f"tl.set('#{cid}{k - 1}',{{autoAlpha:0}},{t0 + k * step:.3f});")
    TW.append(f"tl.fromTo('#{cid}',{{scale:1.25}},{{scale:1,duration:.35,ease:'back.out(3)',immediateRender:false}},{t0 + (len(values) - 1) * step:.3f});")
    return f'<div id="{cid}" class="{cls}">{spans}</div>'


def typed(tid, text, t0, cps=16, cls='typed'):
    """typing: one span per character, revealed with tl.set"""
    spans = ''.join(f'<span id="{tid}{k}" class="tc">{"&nbsp;" if ch == " " else ch}</span>' for k, ch in enumerate(text))
    TW.append(f"gsap.set('#{tid} .tc',{{display:'none'}});")
    for k in range(len(text)):
        TW.append(f"tl.set('#{tid}{k}',{{display:'inline'}},{t0 + k / cps:.3f});")
    return f'<span id="{tid}" class="{cls}">{spans}</span>'


def bword(eid, text, a, b, S, color='#fff', enter='slam', extra=''):
    """big word BEHIND the head: top = head top - .68*S keeps ~75% of each letter clear of the hair (measured)"""
    top = head_top(a + .05) - .68 * S
    if top < ZONE['top']:
        ZONE_WARN.append(f'{eid}: behind-head word top {top:.0f} < {ZONE["top"]}: smaller S (max {(head_top(a + .05) - ZONE["top"]) / .68:.0f})'
                         f' or a layout with a lower head')
    el(eid, f'<span class="bwi">{text}{extra}</span>', a, b, f'top:{top:.0f}px;font-size:{S}px;color:{color}', cls='bw',
       enter=enter, layer=BACKL, dur=.32, ease='power3.out')


CHECK = ('<svg class="ck" viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="{c}"/>'
         '<path d="M18 33l9 9 19-20" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>')
CROSS = ('<svg class="ck" viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="#E5484D"/>'
         '<path d="M21 21l22 22M43 21L21 43" stroke="#fff" stroke-width="7" stroke-linecap="round"/></svg>')


def arrow(color, flip=False, w=170):
    return (f'<svg width="{w}" height="64" viewBox="0 0 170 64" style="{"transform:scaleX(-1)" if flip else ""}">'
            f'<path d="M158 32H22M22 32l24-22M22 32l24 22" stroke="{color}" stroke-width="13" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def photo(src, label, credit='', pos='center'):
    cr = f'<div class="cred">{credit}</div>' if credit else ''
    return f'<img src="assets/img/{src}" style="object-position:{pos}"><div class="plabel">{label}</div>{cr}'


# ------------------------------------------------------------------ sections
def hook():
    a, b = 0.06, T['s02'] - .1
    lines = [['הייתם', 'נותנים', '<span class="hy" id="hwai">ל-AI</span>'], ['לבחור', 'בשבילכם?']]
    # readable from frame 0 (the first frame is the preview on most feeds): no reveal, just a punch-in settle
    html = [f'<div class="hl">{" ".join(f"<span class=hwd>{w}</span>" for w in line)}</div>' for line in lines]
    FRONT.append(f'<div id="hook">{"".join(html)}</div>')
    tw(f"tl.fromTo('#hook',{{scale:1.1}},{{scale:1,duration:.4,ease:'power3.out',immediateRender:false}},0);")
    tw(f"tl.fromTo('#hook .hwd',{{y:0}},{{y:-10,duration:.12,yoyo:true,repeat:1,stagger:.06,ease:'power2.out',immediateRender:false}},{a + .3:.3f});")
    tw(f"tl.to('#hook',{{autoAlpha:0,y:-30,duration:.16,ease:'power2.in'}},{b - .16:.3f});")
    tw(f"tl.set('#hook',{{autoAlpha:0}},{b:.3f});")
    # glitch on "AI"
    kf = ','.join(f"{{x:{x},skewX:{s},duration:.04}}" for x, s in ((-12, -14), (10, 12), (-6, -6), (8, 4), (0, 0)))
    tw(f"tl.to('#hwai',{{keyframes:[{kf}]}},{WT(6) + .1:.3f});")
    tw(f"tl.fromTo('#hwai',{{boxShadow:'10px 0 0 #ff2a6d,-10px 0 0 #05d9e8'}},{{boxShadow:'0px 0 0 #ff2a6d,0px 0 0 #05d9e8',duration:.3,immediateRender:false}},{WT(6) + .1:.3f});")
    # the two models appear beside the head on "AI"
    el('hkg', badge('gpt', 170) + name('gpt', 48), WT(6) + .05, T['s02'], 'left:862px;top:640px', cls='free col', rot=8)
    el('hkx', badge('grok', 170) + name('grok', 48), WT(6) + .12, T['s02'], 'left:48px;top:640px', cls='free col', rot=-8)


def study():
    a = T['s02'] + .04
    inner = ('<div class="nhead"><span class="tcr">TechCrunch</span><span id="ndate" class="ndate">24.10.2026</span></div>'
             '<div class="ntitle" dir="ltr">Forced to pick, Grok\u2019s AI model chooses Republicans. OpenAI\u2019s picks Democrats.</div>'
             '<div class="nfoot">מחקר של Convovo, בהובלת פרופ׳ מ-Cornell</div>')
    el('news', inner, a, WT(15) - .08, 'left:60px;top:360px;width:960px', enter='down')
    pulse('#ndate', WT(14))
    # two models, same question, opposite answers
    b = T['s04']
    el('vsg', badge('gpt', 190) + name('gpt'), WT(15), b, 'left:808px;top:372px', cls='free col', enter='right')
    el('vsx', badge('grok', 190) + name('grok'), WT(16), b, 'left:82px;top:372px', cls='free col', enter='left')
    el('prm', '<div class="bubble">' + typed('prmt', 'בחר מועמד אחד.', WT(17) + .05, cps=17) + '</div>', WT(17) - .06, b,
       'left:315px;top:410px;width:450px', cls='free', enter='pop')
    for sid, dx in (('prmL', -330), ('prmR', 330)):   # the same question flies to both models
        FRONT.append(f'<div id="{sid}" class="free mini">?</div>')
        tw(f"gsap.set('#{sid}',{{autoAlpha:0,left:500,top:440}});")
        tw(f"tl.fromTo('#{sid}',{{autoAlpha:1,x:0,scale:1}},{{autoAlpha:0,x:{dx},scale:.5,duration:.55,ease:'power2.in',immediateRender:false}},{WT(19):.3f});")
    el('arg', arrow(DEM_C), WT(23) - .05, b, 'left:818px;top:650px', cls='free', enter='right', dur=.35)
    el('arx', arrow(REP_C, flip=True), WT(23) + .1, b, 'left:92px;top:650px', cls='free', enter='left', dur=.35)


def method():
    a, b = T['s04'] + .05, T['s06']
    el('mg', badge('gpt', 140), a, WT(37) - .05, 'left:884px;top:360px', cls='free', rot=6)
    el('mx', badge('grok', 140), a + .08, WT(37) - .05, 'left:56px;top:360px', cls='free', rot=-6)
    pulse('#mg', WT(28))
    pulse('#mx', WT(30))
    vals = ['0', '70', '160', '250', '330', '400', '450', '480', '~500']
    S = 230
    top = head_top(WT(31)) - .68 * S
    BACKL.append(f'<div id="n500" class="bw" style="top:{top:.0f}px;font-size:{S}px;color:#fff">'
                 + counter('n500c', vals, WT(31) + .05, .075, cls='cnt') + '</div>')
    tw("gsap.set('#n500',{autoAlpha:0});")
    tw(f"tl.set('#n500',{{autoAlpha:1}},{WT(31) + .05:.3f});")
    tw(f"tl.to('#n500',{{autoAlpha:0,duration:.16}},{WT(37) - .2:.3f});")
    tw(f"tl.set('#n500',{{autoAlpha:0}},{WT(37) - .04:.3f});")
    # one candidate: a ballot gets ticked
    opts = ''.join(f'<div class="bopt"><span id="bx{k}" class="bbox">{CHECK.format(c="#1f8f5f") if k == 0 else ""}</span>'
                   f'<span>מועמד {"א׳" if k == 0 else "ב׳"}</span></div>' for k in range(2))
    el('ballot', f'<div class="btitle">פתק הצבעה</div><div class="brow">{opts}</div>', WT(37), b,
       'left:200px;top:352px;width:680px', cls='card light', enter='down')
    pop_in('#bx0 .ck', WT(41) + .1, ease='back.out(3)')


def surprise():
    a, b = WT(44) - .3, T['s07'] + .3
    for sid, side, c in (('sbl', 'left:0', '#2453d8'), ('srd', 'right:0', '#c4203c')):
        BACKL.append(f'<div id="{sid}" class="strip" style="{side};background:linear-gradient({"90deg" if sid == "sbl" else "270deg"},{c},rgba(0,0,0,0))"></div>')
        tw(f"gsap.set('#{sid}',{{autoAlpha:0}});")
        tw(f"tl.to('#{sid}',{{autoAlpha:.9,duration:.7,ease:'power2.in'}},{a:.3f});")
        tw(f"tl.set('#{sid}',{{autoAlpha:0}},{b:.3f});")


def stats():
    # GPT: 97% Democrats (speaker on the left, panel right)
    a, b = T['s07'] + .04, T['s08'] - .02
    bar = '<div class="bar"><i id="{id}" style="background:{c}"></i></div>'
    inner = (f'<div class="prow">{badge("gpt", 84)}{name("gpt", 54)}</div><div class="psub">המליץ על</div>'
             f'<img id="pgimg" class="plogo" src="assets/img/dem.png"><div class="pparty" style="color:{DEM_C}">דמוקרטים</div>'
             + counter('pgc', [f'{v}%' for v in (0, 21, 44, 66, 81, 91, 97)], WT(49) - .05, .07, cls='big')
             + bar.format(id='pgbar', c=DEM_C) + '<div class="psub">מהמקרים</div>')
    el('pg', inner, a, b, 'left:596px;top:360px;width:440px;height:730px;gap:6px', enter='right', ease='power3.out', dur=.45)
    pop_in('#pgimg', WT(48) - .05)
    tw(f"gsap.set('#pgbar',{{scaleX:0}});")
    tw(f"tl.to('#pgbar',{{scaleX:.97,duration:.5,ease:'power3.out'}},{WT(49) - .05:.3f});")
    # Grok: 92% Republicans (speaker on the right, panel left)
    a, b = T['s08'] + .04, WT(56) - .07
    inner = (f'<div class="prow">{badge("grok", 84)}{name("grok", 54)}</div><div class="psub">המליץ על</div>'
             f'<img id="pximg" class="plogo" src="assets/img/gop.png"><div class="pparty" style="color:{REP_C}">רפובליקנים</div>'
             + counter('pxc', [f'{v}%' for v in (0, 20, 43, 63, 78, 88, 92)], WT(55) - .05, .07, cls='big')
             + bar.format(id='pxbar', c=REP_C) + '<div class="psub">מהמקרים</div>')
    el('px', inner, a, b, 'left:44px;top:360px;width:440px;height:730px;gap:6px', enter='left', ease='power3.out', dur=.45)
    pop_in('#pximg', WT(54) - .05)
    tw(f"gsap.set('#pxbar',{{scaleX:0}});")
    tw(f"tl.to('#pxbar',{{scaleX:.92,duration:.5,ease:'power3.out'}},{WT(55) - .05:.3f});")
    # agreement: two circles that barely overlap
    a, b = WT(56) - .02, WT(61) - .05
    FRONT.append('<div id="venn" class="free" style="left:0;top:0;width:1080px;height:700px">'
                 f'<div id="vcg" class="vc" style="left:520px;top:382px;border-color:{GPT_C};background:rgba(61,220,151,.20)"><span style="color:{GPT_C}">GPT</span></div>'
                 f'<div id="vcx" class="vc" style="left:220px;top:382px;border-color:{GROK_C};background:rgba(183,156,255,.20)"><span style="color:{GROK_C}">Grok</span></div>'
                 f'<div id="vlab" class="vlab"><div class="vnum" dir="ltr">&lt;10%</div><div class="vsub">הסכמה</div></div></div>')
    tw("gsap.set('#venn',{autoAlpha:0});")
    tw(f"tl.set('#venn',{{autoAlpha:1}},{a:.3f});")
    tw(f"tl.fromTo('#vcg',{{x:300,autoAlpha:0}},{{x:0,autoAlpha:1,duration:.7,ease:'power3.out',immediateRender:false}},{a:.3f});")
    tw(f"tl.fromTo('#vcx',{{x:-300,autoAlpha:0}},{{x:0,autoAlpha:1,duration:.7,ease:'power3.out',immediateRender:false}},{a:.3f});")
    pop_in('#vlab', WT(59) - .05, frm="scale:2,autoAlpha:0,filter:'blur(12px)'", ease='power3.out', dur=.3)
    tw(f"tl.to('#vlab',{{filter:'blur(0px)',duration:.01}},{WT(59) + .3:.3f});")
    tw(f"tl.to('#venn',{{autoAlpha:0,duration:.16}},{b - .16:.3f});")
    tw(f"tl.set('#venn',{{autoAlpha:0}},{b:.3f});")


def how():
    strike = f'<i id="strk" class="strk"></i>'
    bword('bwmi', 'מי נבחר?', WT(68) - .03, WT(71) - .06, 190, '#fff', extra=strike)
    tw("gsap.set('#strk',{scaleX:0});")
    tw(f"tl.to('#strk',{{scaleX:1,duration:.22,ease:'power2.out'}},{WT(70) - .05:.3f});")
    bword('bwhow', 'איך?', WT(71) - .02, T['s10'] - .05, 230, YEL)


def topics():
    # GPT: health and abortion (panel right)
    a, b = T['s10'] + .04, T['s11'] - .02
    q = typed('sqg1', 'בריאות', WT(80) - .3, cps=18) + typed('sqg2', ' · הפלות', WT(81) - .15, cps=20)
    el('sbg', f'{badge("gpt", 64)}<div class="sq">{q}<span class="caret"></span></div>', a, b,
       'left:596px;top:362px;width:440px', cls='search', enter='right')
    el('phh', photo('hospital.jpg', 'בריאות', 'Harrison Keely · CC BY 4.0'), WT(80) - .06, b,
       'left:612px;top:480px;width:404px;height:270px', cls='photo', rot=-4)
    el('pha', photo('abortion.jpg', 'הפלות', '7beachbum · CC BY 2.0', 'left center'), WT(81) - .06, b,
       'left:608px;top:780px;width:412px;height:280px', cls='photo', rot=4)
    # Grok: immigration, taxes, crime (panel left)
    a, b = T['s11'] + .04, T['s12'] - .02
    q = (typed('sqx1', 'הגירה', WT(85) - .25, cps=18) + typed('sqx2', ' · מיסים', WT(86) - .2, cps=20)
         + typed('sqx3', ' · פשיעה', WT(87) - .2, cps=20))
    el('sbx', f'{badge("grok", 64)}<div class="sq" style="font-size:31px">{q}<span class="caret"></span></div>', a, b,
       'left:44px;top:362px;width:440px', cls='search', enter='left')
    el('phb', photo('border.jpg', 'הגירה', 'Tomascastelazo · CC BY-SA 4.0'), WT(85) - .06, b,
       'left:58px;top:478px;width:412px;height:190px', cls='photo', rot=3)
    el('pht', photo('tax.jpg', 'מיסים', pos='center 18%'), WT(86) - .06, b,
       'left:66px;top:682px;width:400px;height:190px', cls='photo', rot=-3)
    el('phc', photo('crime.jpg', 'פשיעה', 'Kidfly182 · CC BY 4.0'), WT(87) - .06, b,
       'left:54px;top:888px;width:416px;height:190px', cls='photo', rot=2)


def sources():
    a, b = T['s12'] + .04, T['s13'] - .02
    for cid, kind, x, names, d in (('srg', 'gpt', 556, ['Wikipedia', 'AP', 'Axios', 'Reddit'], 0),
                                    ('srx', 'grok', 54, ['X', 'Ballotpedia', 'Turning Point', 'VoteSmart'], .09)):
        chips = ''.join(f'<span id="{cid}{k}" class="chip" dir="ltr">{n}</span>' for k, n in enumerate(names))
        el(cid, f'<div class="prow">{badge(kind, 76)}{name(kind, 50)}</div><div class="chips">{chips}</div>', a + d, b,
           f'left:{x}px;top:360px;width:470px;height:340px', enter='pop')
        for k in range(len(names)):
            pop_in(f'#{cid}{k}', WT(89) + .1 + k * .2 + d)


def experiment():
    el('exl', '<span class="flask">ניסוי המשך</span> · 30 מרוצים', WT(94) - .04, T['s14'] - .04,
       'left:200px;top:362px;width:680px', cls='pill', enter='down')
    a, b = T['s14'] + .04, T['s15'] - .02
    globe = ('<svg class="globe" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="none" stroke="#fff" stroke-width="6"/>'
             '<ellipse cx="50" cy="50" rx="18" ry="40" fill="none" stroke="#fff" stroke-width="5"/>'
             '<path d="M12 38h76M12 62h76" stroke="#fff" stroke-width="5"/>'
             '<path id="gslash" d="M14 14L86 86" stroke="#E5484D" stroke-width="10" stroke-linecap="round"/></svg>')
    inner = (f'<div class="trow">{globe}<div class="ttitle">חיפוש באינטרנט</div></div>'
             '<div class="trow"><div id="tgp" class="tpill"><div id="tgk" class="tknob"></div></div>'
             '<div class="tstate"><span id="ton" style="color:#34C759">פועל</span><span id="toff" style="color:#E5484D">כבוי</span></div></div>')
    el('tog', inner, a, b, 'left:170px;top:360px;width:740px;height:340px', enter='pop')
    tw("gsap.set('#toff',{autoAlpha:0});gsap.set('#gslash',{autoAlpha:0});")
    off = WT(98) + .05
    tw(f"tl.to('#tgk',{{x:-128,duration:.22,ease:'power3.inOut'}},{off:.3f});")
    tw(f"tl.to('#tgp',{{backgroundColor:'#3a3a46',duration:.22}},{off:.3f});")
    tw(f"tl.set('#ton',{{autoAlpha:0}},{off + .1:.3f});tl.set('#toff',{{autoAlpha:1}},{off + .1:.3f});")
    pop_in('#gslash', off + .12, frm='autoAlpha:0', ease='power2.out', dur=.15)
    # 30 races without search: GPT 24 Dem / 1 Rep / 5 declined, Grok 27 declined / 3 Dem
    gcol = [DEM_C] * 30
    gcol[11] = REP_C
    for k in (4, 16, 21, 26, 29):
        gcol[k] = None
    xcol = [None] * 30
    for k in (5, 18, 24):
        xcol[k] = DEM_C

    def dots(did, cols, t0, stagger, off_c):
        TW.append(f"gsap.set('#{did} i',{{scale:.6}});")
        for k, c in enumerate(cols):
            TW.append(f"tl.to('#{did}{k}',{{backgroundColor:'{c or off_c}',scale:1,duration:.14,ease:'back.out(3)'}},{t0 + k * stagger:.3f});")
        return f'<div id="{did}" class="dots">' + ''.join(f'<i id="{did}{k}"></i>' for k in range(30)) + '</div>'

    def legend(items):
        return '<div class="leg">' + ''.join(f'<span><i style="background:{c}"></i>{t}</span>' for c, t in items) + '</div>'

    a, b = T['s15'] + .04, T['s16'] - .02
    inner = (f'<div class="prow">{badge("gpt", 84)}<div class="ptit">GPT · בלי חיפוש</div></div>'
             + dots('dgd', gcol, WT(105) - .1, .038, '#6b6b7d')
             + counter('dgc', ['24/30'], WT(106) - .02, .1, cls='mid')
             + legend([(DEM_C, 'דמוקרט 24'), (REP_C, 'רפובליקני 1'), ('#6b6b7d', 'סירב 5')]))
    el('dg', inner, a, b, 'left:596px;top:360px;width:440px;height:730px', enter='right', ease='power3.out', dur=.45)
    a, b = T['s16'] + .04, T['s17'] - .02
    inner = (f'<div class="prow">{badge("grok", 84)}<div class="ptit">Grok · בלי חיפוש</div></div>'
             + dots('dxd', xcol, WT(112) - .1, .03, '#4a4a5c')
             + counter('dxc', ['27/30'], WT(114) - .02, .1, cls='mid')
             + '<div class="refuse">סירב לבחור</div>'
             + legend([('#4a4a5c', 'סירב 27'), (DEM_C, 'דמוקרט 3')]))
    el('dx', inner, a, b, 'left:44px;top:360px;width:440px;height:730px', enter='left', ease='power3.out', dur=.45)
    pop_in('#dx .refuse', WT(114) + .1)


def point():
    bword('bwbias', 'ההטיה', WT(118) - .02, WT(121) - .07, 230, YEL)
    a, b = WT(122) - .12, T['s19'] - .02
    steps = [('fl0', 'חיפוש', 760), ('fl1', 'מקורות', 410), ('fl2', 'תשובה', 60)]
    for k, (fid, txt, x) in enumerate(steps):
        el(fid, txt, a + k * .14, b, f'left:{x}px;top:400px;width:260px', cls='step', enter='pop')
    for k, x in enumerate((684, 334)):
        el(f'fa{k}', arrow('#ffffff', w=70), a + .07 + k * .14, b, f'left:{x}px;top:428px', cls='free', enter='fade', dur=.25)
    pulse('#fl2', max(WT(123), a + .28 + .44))   # after its entrance has finished
    hi = WT(125) - .05
    tw(f"tl.to('#fl0',{{backgroundColor:'{YEL}',color:'{INK}',scale:1.08,duration:.25,ease:'back.out(2)'}},{hi:.3f});")
    tw(f"tl.to(['#fl1','#fl2','#fa0','#fa1'],{{opacity:.35,duration:.25}},{hi:.3f});")
    el('flb', 'ההטיה מתחילה כאן', hi + .2, b, 'left:610px;top:548px;width:420px', cls='tag', enter='pop')


def caveat():
    a, b = WT(129) - .04, T['s22'] - .02
    rows = [('cvr0', CHECK.format(c='#1f8f5f'), 'רק בחירות בארה״ב', WT(133)),
            ('cvr1', CHECK.format(c='#1f8f5f'), 'בוצע דרך <span class="mono" dir="ltr">API</span>', WT(138)),
            ('cvr2', CHECK.format(c='#1f8f5f'), 'עם הוראה מפורשת לבחור', WT(140)),
            ('cvr3', CROSS, 'לא בהכרח כמו שיחה רגילה בצ׳אט', WT(143))]
    body = ''.join(f'<div id="{rid}" class="cvrow">{icon}<span>{txt}</span></div>' for rid, icon, txt, _ in rows)
    el('cv', f'<div class="cvhead"><span class="star">*</span>חשוב לדייק</div>{body}', a, b,
       'left:80px;top:352px;width:920px;gap:6px', enter='down')
    for rid, _, _, t in rows:
        pop_in(f'#{rid}', t - .08, frm='x:60,autoAlpha:0', ease='power3.out', dur=.3)


def devs():
    bword('bwdev', 'מפתחים', T['s22'] + .02, WT(157) - .12, 230, '#fff')
    a, b = WT(160) - .1, T['s24'] - .02
    el('outc', '<div class="dtit">הפלט</div><div class="dsub" dir="ltr">output</div>'
       f'<div class="mono obox" dir="ltr">"Vote: Candidate A"</div>', a, b, 'left:562px;top:356px;width:456px;min-height:340px;gap:6px')
    lines = ['> search(query)', '> read(sources)', '> weigh(evidence)', '> answer()']
    trace = ''.join(f'<div id="tr{k}" class="mono tline" dir="ltr">{l}</div>' for k, l in enumerate(lines))
    el('trc', f'<div class="dtit">התהליך</div><div class="dsub" dir="ltr">trace</div>{trace}', WT(161) - .05, b,
       'left:62px;top:356px;width:470px;min-height:340px;gap:6px')
    for k in range(len(lines)):
        pop_in(f'#tr{k}', WT(163) + k * .26, frm='x:-30,autoAlpha:0', ease='power2.out', dur=.2)
    tw(f"tl.to('#outc',{{opacity:.45,scale:.95,duration:.3}},{WT(161):.3f});")


def cta():
    el('ask', '<div class="bubble ask">כתבו לי בתגובות<span class="dotsx"><i></i><i></i><i></i></span></div>',
       T['s24'] + .02, WT(171) - .06, 'left:230px;top:362px;width:620px', cls='free', enter='pop')
    bword('bwneu', '<span dir="ltr">AI</span> ניטרלי?', WT(175) - .04, FREEZE - .02, 170, YEL)
    linkedin_card(FREEZE + .15)


def linkedin_card(a):
    """THE default ending (the creator approved this exact look): white card, LinkedIn logo, round photo, name, the
    "let's connect" line, a blue "+ Connect" button that a touch dot taps one second in -> outlined "✓ Pending".
    The speaker has left the frame by now (subject() exit), so it sits alone in the middle of the safe zone.
    Photo: assets/img/avatar.jpg, copied from config.json "photo" when missing. Text: config "name" and
    "linkedinSubtitle"[language]. SFX: whoosh at FREEZE, click on the tap, chime after (see SFX)."""
    if not os.path.exists('assets/img/avatar.jpg') and CFG.get('photo') and os.path.exists(CFG['photo']):
        os.makedirs('assets/img', exist_ok=True)
        shutil.copyfile(CFG['photo'], 'assets/img/avatar.jpg')
    inner = ('<div class="lihead"><div class="liin">in</div><div class="lilink">LinkedIn</div></div>'
             '<div class="libody"><img class="liav" src="assets/img/avatar.jpg">'
             f'<div class="liname"><div class="lin" dir="ltr">{LI_NAME}</div><div class="lis">{LI_SUB}</div></div></div>'
             '<div id="libtn" class="libtn" dir="ltr"><span id="lic">+ Connect</span><span id="lip">&#10003; Pending</span></div>'
             '<div id="tap" class="tap"></div>')
    el('li', inner, a, None, 'left:90px;top:640px;width:900px;height:420px', cls='card light', enter='up', ease='power3.out', dur=.5)
    tap = a + 1.0
    tw("gsap.set('#lip',{autoAlpha:0});gsap.set('#tap',{autoAlpha:0,scale:1});")
    tw(f"tl.fromTo('#tap',{{autoAlpha:0,x:120,y:80}},{{autoAlpha:.85,x:0,y:0,duration:.35,ease:'power3.out',immediateRender:false}},{tap - .4:.3f});")
    tw(f"tl.to('#tap',{{scale:.75,duration:.06}},{tap - .05:.3f});")
    tw(f"tl.to('#tap',{{scale:1.6,autoAlpha:0,duration:.35,ease:'power2.out'}},{tap + .03:.3f});")
    tw(f"tl.to('#libtn',{{backgroundColor:'#ffffff',color:'#0A66C2',duration:.15}},{tap:.3f});")
    tw(f"tl.set('#lic',{{autoAlpha:0}},{tap:.3f});tl.set('#lip',{{autoAlpha:1}},{tap:.3f});")
    pulse('#libtn', tap, 1.12)


def flashes():
    FRONT.append('<div id="flash"></div>')
    tw("gsap.set('#flash',{autoAlpha:0});")
    for t, o in ((T['s07'] - .02, .75), (T['s17'], .5)):
        tw(f"tl.fromTo('#flash',{{autoAlpha:{o}}},{{autoAlpha:0,duration:.28,ease:'power2.out',immediateRender:false}},{t:.3f});")


# ------------------------------------------------------------------ karaoke captions (RTL)
def kw_color(t):
    if 'GPT' in t:
        return GPT_C
    if 'Grok' in t:
        return GROK_C
    if 'דמוקרט' in t:
        return DEM_C
    if 'רפובליק' in t:
        return REP_C
    if any(c.isdigit() for c in t):
        return YEL
    return '#FFFFFF'


def chunks():
    out, cur = [], []
    for w in W:
        if cur and (w['sent'] != cur[-1]['sent'] or len(cur) >= 3 or cur[-1]['text'][-1] in ',.?:'
                    or sum(len(x['text']) for x in cur) + len(w['text']) > 16):
            out.append(cur)
            cur = []
        cur.append(w)
    out.append(cur)
    return out


def captions():
    html, tws = [], []
    ch = chunks()
    for ci, c in enumerate(ch):
        cid = f'cap{ci}'   # 'c{n}' collided with counter ids ('c30' = a counter AND caption 30)
        spans = ' '.join(f'<span id="{cid}w{k}" class="cw">{w["text"]}</span>' for k, w in enumerate(c))
        html.append(f'<div id="{cid}" class="cap">{spans}</div>')
        a = c[0]['start'] - .05
        nxt = ch[ci + 1][0]['start'] - .05 if ci + 1 < len(ch) else FREEZE - .05
        b = min(nxt, c[-1]['end'] + .45) if ci + 1 < len(ch) else FREEZE - .05
        b = max(b, a + .25)
        if a <= .05:   # the first line is on screen from frame 0
            tws.append(f"gsap.set('#{cid}',{{autoAlpha:1}});")
        else:
            tws.append(f"gsap.set('#{cid}',{{autoAlpha:0}});")
            tws.append(f"tl.fromTo('#{cid}',{{autoAlpha:0,y:24,scale:.9}},{{autoAlpha:1,y:0,scale:1,duration:.16,ease:'back.out(2)',immediateRender:false}},{a:.3f});")
        for k, w in enumerate(c):
            end = c[k + 1]['start'] if k + 1 < len(c) else min(w['end'], b)
            tws.append(f"tl.to('#{cid}w{k}',{{color:'{YEL}',scale:1.14,duration:.07,ease:'power2.out'}},{max(0, w['start'] - .03):.3f});")
            tws.append(f"tl.to('#{cid}w{k}',{{color:'{kw_color(w['text'])}',scale:1,duration:.1,ease:'power2.out'}},{max(end - .03, w['start'] + .05):.3f});")
        tws.append(f"tl.set('#{cid}',{{autoAlpha:0}},{b:.3f});")
    return html, tws


# ------------------------------------------------------------------ sound (subtle: SFX_GAIN of the base volumes)
SFX = [  # (name, time, volume, media start, max length)
    ('impact-bass-1', 0.0, .5, 0, 1.6), ('whoosh-short', 0.02, .3, 0, .6),
    ('glitch-1', WT(6) + .08, .22, 0, .7), ('pop', WT(6) + .05, .3, 0, .6),
    ('whoosh-short', T['s02'], .32, 0, .6), ('whoosh', WT(15), .3, 0, .6), ('typing', WT(17) + .05, .22, 0, .9),
    ('whoosh-short', WT(19), .22, 0, .6), ('whoosh', WT(23) - .05, .28, 0, .6),
    ('whoosh-cinematic', T['s04'] - .1, .22, 0, 1.4), ('pop', WT(28), .25, 0, .6), ('pop', WT(30), .25, 0, .6),
    ('typing', WT(31) + .05, .2, 0, .7), ('whoosh-short', WT(37), .25, 0, .6), ('click', WT(41) + .1, .5, 0, .37),
    ('riser', T['s07'] - 1.6, .32, 10.03 - 1.6, 1.6), ('impact-bass-2', T['s07'], .45, 0, 1.8),
    ('whoosh-short', T['s07'], .3, 0, .6), ('pop', WT(48) - .05, .28, 0, .6), ('ping', WT(49) + .45, .25, 0, 1.0),
    ('whoosh-short', T['s08'], .3, 0, .6), ('pop', WT(54) - .05, .28, 0, .6), ('ping', WT(55) + .45, .25, 0, 1.0),
    ('whoosh', WT(56), .25, 0, .6), ('impact-bass-1', WT(59) - .05, .28, 0, 1.4),
    ('error', WT(70) - .05, .18, 0, .7), ('impact-bass-2', WT(71) - .02, .35, 0, 1.6),
    ('whoosh-short', T['s10'], .28, 0, .6), ('key-press', WT(80) - .3, .3, 0, .4), ('pop', WT(80) - .06, .25, 0, .6),
    ('pop', WT(81) - .06, .25, 0, .6), ('whoosh-short', T['s11'], .28, 0, .6), ('key-press', WT(85) - .25, .3, 0, .4),
    ('pop', WT(85) - .06, .25, 0, .6), ('pop', WT(86) - .06, .25, 0, .6), ('pop', WT(87) - .06, .25, 0, .6),
    ('whoosh', T['s12'], .25, 0, .6), ('sparkle', WT(89) + .1, .16, 0, 1.2),
    ('whoosh-short', WT(94) - .04, .22, 0, .6), ('pop', T['s14'] + .04, .22, 0, .6), ('click', WT(98) + .05, .55, 0, .37),
    ('glitch-3', WT(98) + .1, .16, 0, .8), ('whoosh-short', T['s15'], .28, 0, .6), ('typing', WT(105) - .1, .2, 0, 1.2),
    ('ping', WT(106), .22, 0, 1.0), ('whoosh-short', T['s16'], .28, 0, .6), ('error', WT(114) - .02, .16, 0, .9),
    ('whoosh-cinematic', T['s17'] - .1, .25, 0, 1.6), ('impact-bass-2', WT(118) - .02, .3, 0, 1.5),
    ('pop', WT(122) - .12, .22, 0, .6), ('ping', WT(125) - .05, .26, 0, 1.0),
    ('notification', WT(129) - .04, .2, 0, 1.0), ('click-soft', WT(133) - .08, .45, 0, .37),
    ('click-soft', WT(138) - .08, .45, 0, .37), ('click-soft', WT(140) - .08, .45, 0, .37), ('error', WT(143) - .08, .14, 0, .8),
    ('whoosh-short', T['s22'], .25, 0, .6), ('pop', WT(160) - .1, .22, 0, .6), ('typing', WT(163), .22, 0, 1.1),
    ('notification', T['s24'] + .02, .22, 0, 1.2), ('impact-bass-1', WT(175) - .04, .3, 0, 1.4),
    ('whoosh', FREEZE - .02, .3, 0, .6), ('click', FREEZE + 1.15, .6, 0, .37), ('chime', FREEZE + 1.25, .22, 0, 1.6),
]
SFX_GAIN = 0.75
# the pack is not level-matched (volumedetect means: impacts -3..-5 dB, ping/typing/key-press -35..-39 dB, voice -24 dB):
# per-file trim so the volumes above mean the same thing for every sound. data-volume is capped at 1.
LEVEL = {'impact-bass-1': .25, 'impact-bass-2': .2, 'riser': .6, 'pop': 1.6, 'typing': 3.2, 'key-press': 3, 'click': 1.4,
         'click-soft': 1.6, 'glitch-3': 3, 'error': 3.5, 'notification': 2.2, 'chime': 2.6, 'ping': 2.8}


def audio():
    out, lanes = [], []
    for k, (n, t, vol, ms, ln) in enumerate(sorted(SFX, key=lambda x: x[1])):
        vol = min(1.0, vol * LEVEL.get(n, 1))
        t = max(0.0, t)
        d = min(ln, DUR - t)
        lane = next((i for i, end in enumerate(lanes) if end < t - .02), None)   # touching clips count as overlap in lint
        if lane is None:
            lanes.append(0)
            lane = len(lanes) - 1
        lanes[lane] = t + d
        out.append(f'<audio id="sfx{k}" src="assets/sfx/{n}.mp3" data-start="{t:.3f}" data-media-start="{ms:.3f}" '
                   f'data-duration="{d:.3f}" data-track-index="{10 + lane}" data-volume="{min(1.0, vol * SFX_GAIN):.3f}"></audio>')
    return out


# ------------------------------------------------------------------ styles
OUTLINE = ','.join(f'{x}px {y}px 0 #000' for x, y in ((4, 0), (-4, 0), (0, 4), (0, -4), (3, 3), (-3, 3), (3, -3), (-3, -3)))
CSS = f'''
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#05070d}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:#05070d;font-family:Heebo,Inter,sans-serif}}
#bgwrap,#grid,#vig,#back,#front{{position:absolute;inset:0}}
#bgwrap{{z-index:1}}
.plate{{position:absolute;inset:0;overflow:hidden}}
.plate img{{position:absolute;inset:-30px;width:calc(100% + 60px);height:calc(100% + 60px);object-fit:cover}}
#grid{{z-index:2;opacity:.6;background-image:linear-gradient(rgba(255,255,255,.045) 2px,transparent 2px),linear-gradient(90deg,rgba(255,255,255,.045) 2px,transparent 2px);background-size:72px 72px}}
#vig{{z-index:3;background:radial-gradient(95% 62% at 50% 46%,rgba(0,0,0,0) 50%,rgba(0,0,0,.55) 100%)}}
#back{{z-index:4}}
#subj{{position:absolute;inset:0;z-index:5;transform-origin:50% 100%}}
#punch{{position:absolute;inset:0;transform-origin:50% 62%}}
#glow{{position:absolute;left:40px;top:300px;width:1000px;height:1200px;border-radius:50%;background:radial-gradient(closest-side,currentColor,rgba(0,0,0,0))}}
#cut{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
#front{{z-index:8}}
#capbox{{position:absolute;left:0;right:0;top:0;height:120px;z-index:9}}
#flash{{position:absolute;inset:0;background:#fff;z-index:30}}

.card,.free,.bw,.photo,.search,.pill,.step,.tag,.strip{{position:absolute}}
.card{{background:rgba(10,14,26,.88);border:2px solid rgba(255,255,255,.14);border-radius:36px;box-shadow:0 30px 80px rgba(0,0,0,.55);
  color:#fff;direction:{DIR};padding:26px 30px;display:flex;flex-direction:column;align-items:center;gap:12px}}
.card.light{{background:#fff;color:{INK};border:none}}
.col{{display:flex;flex-direction:column;align-items:center;gap:10px}}
.badge{{display:flex;align-items:center;justify-content:center;border-radius:28%;box-shadow:0 18px 44px rgba(0,0,0,.5);flex:none}}
.badge img{{display:block}}
.bname{{font-family:Inter;font-weight:800;letter-spacing:-.02em;text-shadow:0 4px 18px rgba(0,0,0,.6)}}

/* hook headline */
#hook{{position:absolute;left:30px;right:30px;top:352px;z-index:9;text-align:center;direction:{DIR};color:#fff;font:900 90px/1.02 Heebo;
  text-shadow:{OUTLINE},0 14px 40px rgba(0,0,0,.6)}}
.hwd{{display:inline-block;margin:0 .08em}}
.hy{{display:inline-block;background:{YEL};color:{INK};padding:0 .2em;border-radius:22px;text-shadow:none;unicode-bidi:isolate}}

/* news card */
.nhead{{width:100%;display:flex;justify-content:space-between;align-items:center;font:700 34px Inter}}
.tcr{{color:#0A9E01;font:800 40px Inter;letter-spacing:-.02em}}
.ndate{{display:inline-block;color:#c8cbd6}}
.ntitle{{width:100%;font:700 46px/1.14 Inter;letter-spacing:-.01em;text-align:left;color:#fff}}
.nfoot{{width:100%;font:500 32px Heebo;color:{YEL}}}
.bubble{{background:#fff;color:{INK};border-radius:34px;padding:20px 30px;font:800 46px Heebo;text-align:center;direction:{DIR};
  box-shadow:0 24px 60px rgba(0,0,0,.5);min-height:96px}}
.bubble.ask{{font-size:54px;display:flex;align-items:center;justify-content:center;gap:18px}}
.mini{{width:80px;height:80px;border-radius:50%;background:#fff;color:{INK};font:900 52px/80px Inter;text-align:center}}
.typed .tc{{display:inline}}

/* method */
.bw{{left:0;right:0;text-align:center;direction:{DIR};font-family:Heebo;font-weight:900;line-height:.9;letter-spacing:-.02em;white-space:nowrap;
  text-shadow:0 16px 60px rgba(0,0,0,.55)}}
.bwi{{position:relative;display:inline-block}}
.strk{{position:absolute;left:-3%;right:-3%;top:44%;height:.11em;background:#FF4D4D;border-radius:12px;transform-origin:100% 50%}}
.cnt,.big,.mid{{display:grid;justify-items:center}}
.cv{{grid-area:1/1;white-space:nowrap}}
.btitle{{font:800 30px Heebo;color:#8a6d1a;letter-spacing:.04em}}
.brow{{display:flex;gap:40px}}
.bopt{{display:flex;align-items:center;gap:16px;font:800 44px Heebo;white-space:nowrap}}
.bbox{{width:64px;height:64px;border:5px solid {INK};border-radius:14px;display:flex;align-items:center;justify-content:center}}
.ck{{width:56px;height:56px;flex:none}}
.strip{{top:0;bottom:0;width:540px}}

/* stats */
.prow{{display:flex;align-items:center;gap:18px;justify-content:center}}
.psub{{font:600 34px Heebo;color:rgba(255,255,255,.82)}}
.plogo{{width:210px;height:auto;filter:drop-shadow(0 18px 30px rgba(0,0,0,.5))}}
.pparty{{font:900 46px Heebo}}
.big{{font:900 150px/1 Heebo;color:#fff;letter-spacing:-.03em}}
.mid{{font:900 104px/1 Heebo;color:{YEL};letter-spacing:-.02em}}
.bar{{width:360px;height:26px;border-radius:13px;background:rgba(255,255,255,.14);overflow:hidden;direction:ltr}}
.bar i{{display:block;width:100%;height:100%;transform-origin:0 50%}}
.vc{{position:absolute;width:340px;height:340px;border-radius:50%;border:8px solid;display:flex;align-items:center;justify-content:center}}
.vc span{{font:800 58px Inter;text-shadow:0 4px 18px rgba(0,0,0,.6)}}
#vcg span{{margin-left:190px}}
#vcx span{{margin-right:190px}}
.vlab{{position:absolute;left:340px;top:450px;width:400px;text-align:center}}
.vnum{{display:inline-block;background:rgba(10,14,26,.92);border:4px solid {YEL};border-radius:30px;padding:6px 26px;font:900 96px/1 Heebo;color:{YEL};text-shadow:{OUTLINE},0 12px 40px rgba(0,0,0,.6)}}
.vsub{{font:800 46px Heebo;color:#fff;text-shadow:{OUTLINE}}}

/* topics */
.search{{display:flex;align-items:center;gap:16px;background:#fff;border-radius:60px;padding:14px 18px;direction:{DIR};box-shadow:0 24px 60px rgba(0,0,0,.5)}}
.search .badge{{border-radius:50%}}
.sq{{font:800 38px Heebo;color:{INK};white-space:nowrap;overflow:hidden}}
.caret{{display:inline-block;width:4px;height:40px;background:{INK};margin-right:4px;vertical-align:middle}}
.photo{{border:8px solid #fff;border-radius:22px;overflow:hidden;background:#111;box-shadow:0 30px 70px rgba(0,0,0,.6)}}
.photo img{{width:100%;height:100%;object-fit:cover;display:block}}
.plabel{{position:absolute;right:14px;bottom:14px;background:{YEL};color:{INK};font:900 40px Heebo;padding:4px 20px;border-radius:16px;direction:{DIR}}}
.cred{{position:absolute;left:10px;top:8px;font:500 15px Inter;color:rgba(255,255,255,.75);text-shadow:0 1px 4px #000}}

/* sources */
.chips{{display:flex;flex-wrap:wrap;gap:16px;justify-content:center;margin-top:10px}}
.chip{{background:rgba(255,255,255,.95);color:{INK};font:700 34px Inter;padding:12px 22px;border-radius:40px}}

/* experiment */
.pill{{background:rgba(10,14,26,.9);border:3px solid {YEL};border-radius:60px;color:#fff;font:800 44px Heebo;text-align:center;padding:16px 24px;direction:{DIR}}}
.flask{{color:{YEL}}}
.trow{{display:flex;align-items:center;gap:28px;justify-content:center}}
.globe{{width:110px;height:110px}}
.ttitle{{font:900 66px Heebo}}
.tpill{{width:250px;height:122px;border-radius:61px;background:#34C759;position:relative;direction:ltr}}
.tknob{{position:absolute;right:11px;top:11px;width:100px;height:100px;border-radius:50%;background:#fff;box-shadow:0 6px 16px rgba(0,0,0,.35)}}
.tstate{{display:grid;font:900 70px Heebo}}
.tstate span{{grid-area:1/1}}
.dots{{display:grid;grid-template-columns:repeat(6,46px);gap:12px;direction:{DIR};margin:14px 0}}
.dots i{{display:block;width:46px;height:46px;border-radius:50%;background:rgba(255,255,255,.16)}}
.ptit{{font:800 38px Heebo;white-space:nowrap}}
.leg{{display:flex;flex-wrap:wrap;gap:10px 22px;justify-content:center;font:700 32px Heebo;color:rgba(255,255,255,.9)}}
.leg span{{display:flex;align-items:center;gap:10px}}
.leg i{{width:26px;height:26px;border-radius:50%;display:block}}
.refuse{{font:900 52px Heebo;color:#FF8A8A}}

/* the point */
.step{{background:rgba(10,14,26,.92);border:3px solid rgba(255,255,255,.3);border-radius:30px;color:#fff;font:900 56px Heebo;text-align:center;padding:22px 0}}
.tag{{background:#FF4D4D;color:#fff;font:900 38px Heebo;white-space:nowrap;text-align:center;padding:12px 18px;border-radius:20px;direction:{DIR}}}

/* caveat */
.cvhead{{width:100%;font:900 58px Heebo;display:flex;align-items:center;gap:16px}}
.star{{color:{INK};background:{YEL};width:62px;height:62px;border-radius:50%;font:900 72px/86px Inter;text-align:center;display:inline-block}}
.cvrow{{width:100%;display:flex;align-items:center;gap:18px;font:700 42px Heebo}}
.mono{{font-family:'JetBrains Mono',monospace;font-weight:500}}

/* devs */
.dtit{{font:900 56px Heebo}}
.dsub{{font:500 30px 'JetBrains Mono';color:rgba(255,255,255,.55)}}
.obox{{background:rgba(255,255,255,.08);border-radius:16px;padding:16px 18px;font-size:30px;color:{GPT_C};margin-top:8px}}
.tline{{width:100%;font-size:30px;line-height:1.25;color:{GPT_C};text-align:left}}

/* cta */
.dotsx{{display:inline-flex;gap:8px}}
.dotsx i{{width:14px;height:14px;border-radius:50%;background:{INK};opacity:.5;display:block}}
.lihead{{width:100%;display:flex;align-items:center;gap:14px;direction:ltr}}
.liin{{width:64px;height:64px;border-radius:12px;background:#0A66C2;color:#fff;font:800 46px/64px Inter;text-align:center}}
.lilink{{font:700 38px Inter;color:#0A66C2}}
.libody{{width:100%;display:flex;align-items:center;gap:30px;direction:{DIR}}}
.liav{{width:150px;height:150px;border-radius:50%;object-fit:cover;border:5px solid #fff;box-shadow:0 10px 30px rgba(0,0,0,.25)}}
.lin{{font:800 62px Inter;color:{INK};letter-spacing:-.02em}}
.lis{{font:600 36px Heebo;color:#5b6170}}
.libtn{{display:grid;background:#0A66C2;color:#fff;border:4px solid #0A66C2;border-radius:60px;font:800 44px Inter;padding:14px 56px}}
.libtn span{{grid-area:1/1;text-align:center}}
.tap{{position:absolute;left:560px;top:330px;width:80px;height:80px;border-radius:50%;background:rgba(255,255,255,.9);border:4px solid rgba(0,0,0,.25)}}

/* captions */
.cap{{position:absolute;left:30px;right:30px;top:0;text-align:center;direction:{DIR};font:900 74px/1.05 Heebo;white-space:nowrap}}
.cw{{display:inline-block;margin:0 .03em;unicode-bidi:isolate;color:rgba(255,255,255,.55);text-shadow:{OUTLINE},0 10px 30px rgba(0,0,0,.6)}}
'''

# PY build.py --safe: the LinkedIn safe zone in red (covered by LinkedIn's UI on a phone), snapshots only, never renders
_R = 'position:absolute;background:rgba(255,0,0,.28)'
_mid = ZONE['bottom'] - ZONE['top']
SAFE_GUIDE = ('<div style="position:absolute;inset:0;z-index:99;pointer-events:none">'
              f'<div style="{_R};left:0;right:0;top:0;height:{ZONE["top"]}px"></div>'
              f'<div style="{_R};left:0;right:0;top:{ZONE["bottom"]}px;bottom:0"></div>'
              f'<div style="{_R};left:0;width:{ZONE["side"]}px;top:{ZONE["top"]}px;height:{_mid}px"></div>'
              f'<div style="{_R};right:0;width:{ZONE["side"]}px;top:{ZONE["top"]}px;height:{_mid}px"></div>'
              f'<div style="{_R};left:{ZONE["side"]}px;width:{ZONE["bar_w"] - ZONE["side"]}px;top:{ZONE["bar_top"]}px;'
              f'height:{ZONE["bottom"] - ZONE["bar_top"]}px"></div>'
              f'<div style="{_R};right:{ZONE["side"]}px;width:{ZONE["bar_w"] - ZONE["side"]}px;top:{ZONE["bar_top"]}px;'
              f'height:{ZONE["bottom"] - ZONE["bar_top"]}px"></div></div>')


def build():
    p_html, p_tw = plates()
    for section in (hook, study, method, surprise, stats, how, topics, sources, experiment, point, caveat, devs, cta, flashes):
        section()
    c_html, c_tw = captions()
    tweens = p_tw + glow() + subject() + TW + c_tw
    nl = '\n'
    room = ('<video id="bgv" src="assets/aroll.mp4" muted playsinline data-start="0" data-media-start="0" '
            f'data-duration="{FREEZE + EXIT:.3f}" data-track-index="0" style="position:absolute;inset:0;width:100%;height:100%;'
            'object-fit:cover"></video>') if BG_MODE == 'room' else ''
    return f'''<!doctype html>
<html lang="{LANG}" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<link rel="stylesheet" href="assets/fonts/fonts.css" />
<link rel="stylesheet" href="assets/fonts/fonts-he.css" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR:.3f}" data-width="1080" data-height="1920">
  <audio id="bga" src="assets/aroll.mp4" data-start="0" data-media-start="0" data-duration="{AROLL:.3f}" data-track-index="2" data-volume="1"></audio>
{nl.join(audio())}
  <div id="bgwrap" style="background:{BG0}">
{nl.join(p_html)}
  </div>
  <div id="grid"></div>
  <div id="vig"></div>
  <div id="back">
{nl.join(BACKL)}
  </div>
  <div id="subj"><div id="punch"><div id="glow"></div>{room}
    <video id="cut" src="assets/subject.webm" muted playsinline data-start="0" data-media-start="0" data-duration="{FREEZE + EXIT:.3f}" data-track-index="1"></video>
  </div></div>
  <div id="front">
{nl.join(FRONT)}
  </div>
  <div id="capbox">
{nl.join(c_html)}
  </div>
{SAFE_GUIDE if SAFE else ''}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{nl.join(tweens)}
tl.set({{}}, {{}}, {DUR:.3f});
window.__timelines["main"] = tl;
</script>
</body>
</html>
'''


with open('index.html', 'w', encoding='utf-8', newline='\n') as _f:
    _f.write(build())
print(f'wrote index.html {DUR:.3f}s  freeze@{FREEZE:.3f}  layouts {len(SCHED)}  sfx {len(SFX)}')
for w in ZONE_WARN:
    print('SAFE ZONE', w)
print('safe zone: OK' if not ZONE_WARN else f'safe zone: {len(ZONE_WARN)} warnings above, fix them or confirm in the snapshots')
