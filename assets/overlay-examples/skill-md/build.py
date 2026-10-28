#!/usr/bin/env python3
"""SKILL.md in a dark code editor, smooth scroll top -> near bottom.
860x1000, transparent outside the rounded window, 2.15s @30fps.
PY build.py  -> index.html      (PY = the skill's Python; any Python 3 works for this file)
"""
import re
import html as H

DUR = 2.15
W, HT = 860, 1000
ORANGE = '#D97757'
FS = 26            # font size
LH = 40            # row height (~1.55)
CW = FS * 0.6      # JetBrains Mono advance
HEAD = 104         # titlebar 62 + breadcrumb 42
PAD_T = 18
PAD_B = 120
GUT = 82           # x where text starts
COLS = 47          # chars per visual row
VIEW_H = HT - HEAD

SRC = """---
name: video-edit
description: Turn raw talking-head clips into a finished Instagram reel. Picks the best takes, cuts filler, adds captions, motion graphics and sound, in the creator's chosen aesthetic.
---

# Video Edit

Drop your raw clips in a folder and run `/video-edit`.

## Workflow
1. Transcribe every clip with word-level timestamps
2. Find the cleanest take of each line, cut false starts and filler
3. Assemble the cut at `1080x1920`, punch-ins from 4K
4. Cut the creator out of the background (for text behind them)
5. Apply the aesthetic, captions and motion graphics
6. Add sound design, render, check every cut frame by frame

## Aesthetics
- **cool girl**: warm faded grade, lowercase sans + big serif italic in butter yellow `#FAE67A`, handwritten notes, sparkles
- **cool dude**: dark moody grade, tiny wide-tracked caps + heavy serif punch words
- **bold**: heavy lowercase words scattered around the speaker, big words behind the head

## Tools
- `whisper` for word-level transcripts
- `ffmpeg` for cuts, grades and the final render
- `hyperframes` for captions and motion graphics

## Rules
- Never cover the face
- Captions inside Instagram safe zones
- Words land on the exact spoken frame
- Sound effects subtle, never louder than the voice

## Output
- `reel.mp4`, 1080x1920, 30fps
- a phone-size preview for quick review
- an edit log with every cut and why
"""


def inline(s, base='tx'):
    """bold + inline code -> tokens"""
    out = []
    for part in re.split(r'(`[^`]+`|\*\*[^*]+\*\*)', s):
        if not part:
            continue
        if part.startswith('`'):
            out.append((part[1:-1], 'code'))
        elif part.startswith('**'):
            out += [('**', 'bm'), (part[2:-2], 'b'), ('**', 'bm')]
        else:
            out.append((part, base))
    return out


def tokenize(lines):
    res = []
    fm = 0
    for ln in lines:
        if ln == '---':
            fm += 1
            res.append(([('---', 'fence')], 0, 'fence'))
            continue
        if fm == 1 and ':' in ln:
            k, v = ln.split(':', 1)
            cls = 'desc' if k == 'description' else 'val'
            res.append(([(k, 'key'), (':', 'punc'), (v, cls)], 2, 'fm-' + k))
            continue
        m = re.match(r'^(#+) (.*)$', ln)
        if m:
            res.append(([(m.group(1) + ' ', 'hm'), (m.group(2), 'h')], 0, 'h-' + m.group(2).lower()))
            continue
        m = re.match(r'^(\d+\.) (.*)$', ln)
        if m:
            res.append(([(m.group(1) + ' ', 'bul')] + inline(m.group(2)), 3, 'ol'))
            continue
        if ln.startswith('- '):
            body = ln[2:]
            m2 = re.match(r'^(\*\*[^*]+\*\*)(:)(.*)$', body)
            if m2:
                toks = [('- ', 'bul')] + inline(m2.group(1)) + [(':', 'punc')] + inline(m2.group(3), 'muted')
                tag = 'li-' + m2.group(1).strip('*').replace(' ', '-')
            else:
                toks = [('- ', 'bul')] + inline(body)
                tag = 'li'
            res.append((toks, 2, tag))
            continue
        res.append((inline(ln) if ln else [], 0, 'p'))
    return res


def chunks(tokens):
    """split into wrap units; code tokens are atomic, other text splits after spaces"""
    out = []
    for text, cls in tokens:
        if cls in ('code', 'bm', 'bul', 'hm', 'key', 'punc', 'fence'):
            out.append([(text, cls)])
            continue
        for w in re.findall(r'\S+\s*|\s+', text):
            out.append([(w, cls)])
    # glue punctuation-only chunks to the previous one (no wrap before ":" or "**" closers)
    glued = []
    for c in out:
        t = c[0][0]
        if glued and (t in (':', '**') and c[0][1] in ('punc', 'bm') and not glued[-1][-1][0].endswith(' ')):
            glued[-1] = glued[-1] + c
        elif glued and t.startswith(('.', ',')) and c[0][1] != 'code':
            glued[-1] = glued[-1] + c
        else:
            glued.append(c)
    # glue opening "**" / code to following chunk when no space between
    return glued


def wrap(tokens, indent):
    rows, cur, n = [], [], 0
    for c in chunks(tokens):
        txt = ''.join(t for t, _ in c)
        vis = len(txt.rstrip())
        if n + vis > COLS and cur:
            rows.append(cur)
            cur, n = [(' ' * indent, 'tx')], indent
            # drop leading spaces on continuation
            c = [(c[0][0].lstrip(), c[0][1])] + c[1:]
            txt = ''.join(t for t, _ in c)
        cur += c
        n += len(txt)
    rows.append(cur)
    return rows


def span(t, cls):
    t = H.escape(t)
    if cls == 'code':
        return f'<span class="code">{t}</span>'
    return f'<span class="{cls}">{t}</span>'


def build():
    lines = SRC.rstrip('\n').split('\n')
    toks = tokenize(lines)
    rows_html = []
    row = 0
    marks = {}
    for i, (tk, ind, tag) in enumerate(toks):
        wr = wrap(tk, ind)
        marks.setdefault(tag, (row, len(wr)))
        for j, r in enumerate(wr):
            num = str(i + 1) if j == 0 else ''
            lnid = f' id="ln{i+1}"' if j == 0 else ''
            inner = ''.join(span(t, c) for t, c in r)
            rows_html.append(f'<div class="r"><span class="ln"{lnid}>{num}</span><span class="lt">{inner}</span></div>')
            row += 1
    total_rows = row
    content_h = PAD_T + total_rows * LH + PAD_B
    scroll = content_h - VIEW_H
    # scrollbar geometry
    track_top, track_h = 10, VIEW_H - 20
    thumb_h = round(track_h * VIEW_H / content_h)
    thumb_travel = track_h - thumb_h

    name_row = marks['fm-name'][0]
    dude_row, dude_n = marks['li-cool-dude']
    aes_row = marks['h-aesthetics'][0]
    # time when Aesthetics heading crosses mid-viewport (power2.inOut 0.45 -> 1.95)
    import math
    target = PAD_T + aes_row * LH + LH / 2 - VIEW_H / 2
    p = target / scroll

    def inv(p):  # power2.inOut inverse
        return math.sqrt(p / 2) if p < .5 else 1 - math.sqrt((1 - p) / 2)
    t_mid = 0.45 + 1.5 * inv(p)
    print(f'rows={total_rows} content_h={content_h} scroll={scroll} thumb_h={thumb_h} aesthetics_mid_t={t_mid:.2f}')

    CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{HT}px;overflow:hidden;background:transparent}}
#root{{position:relative;width:{W}px;height:{HT}px;overflow:hidden;background:transparent}}
#win{{position:absolute;left:0;top:0;width:{W}px;height:{HT}px;border-radius:28px;overflow:hidden;background:#141413;
  transform-origin:50% 60%;font-family:'Inter',sans-serif}}
#winline{{position:absolute;inset:0;border-radius:28px;border:1px solid #2A2A28;z-index:50;pointer-events:none;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.05)}}
/* title bar */
#tbar{{position:absolute;left:0;top:0;width:{W}px;height:62px;background:#1C1C1A;border-bottom:1px solid #2A2A28}}
#lights{{position:absolute;left:26px;top:24px;display:flex;gap:9px}}
#lights i{{display:block;width:14px;height:14px;border-radius:50%}}
#tab{{position:absolute;left:112px;top:12px;height:51px;width:228px;background:#141413;border:1px solid #2A2A28;border-bottom:none;
  border-radius:11px 11px 0 0;display:flex;align-items:center;gap:11px;padding:0 16px;font-size:19px;font-weight:600;color:#ECEAE2}}
#tab::after{{content:'';position:absolute;left:14px;right:14px;top:-1px;height:2px;border-radius:2px;background:{ORANGE}}}
#tab .x{{margin-left:auto;color:#6E6B63;font-weight:500;font-size:20px;line-height:1}}
#md{{width:30px;height:20px;flex:none}}
#tright{{position:absolute;right:24px;top:20px;display:flex;gap:16px}}
/* breadcrumb */
#crumb{{position:absolute;left:0;top:62px;width:{W}px;height:42px;display:flex;align-items:center;gap:9px;padding-left:28px;
  font-size:16.5px;color:#7D7A71;border-bottom:1px solid #22221F}}
#crumb .s{{color:#4F4D47}}
#crumb .e{{color:#B9B6AC}}
/* editor */
#view{{position:absolute;left:0;top:{HEAD}px;width:{W}px;height:{VIEW_H}px;overflow:hidden}}
#code{{position:absolute;left:0;top:0;width:{W}px;padding-top:{PAD_T}px;font-family:'JetBrains Mono',monospace;font-weight:500;
  font-size:{FS}px;line-height:{LH}px;color:#D6D3C8;font-variant-ligatures:none}}
.r{{position:relative;height:{LH}px;white-space:pre;display:flex}}
.ln{{width:56px;flex:none;text-align:right;color:#4A4843;font-size:21px;padding-right:0}}
.r .lt{{position:absolute;left:{GUT}px;top:0}}
.key{{color:{ORANGE}}}
.punc{{color:#8A877E}}
.val{{color:#ECEAE2}}
.desc,.muted{{color:#A39F91}}
.fence{{color:#5E5C55}}
.hm{{color:#ECEAE2;opacity:.55;font-weight:700}}
.h{{color:#F6F4EC;font-weight:700}}
.bul{{color:{ORANGE}}}
.bm{{color:#6A675F}}
.b{{color:#F2EFE6;font-weight:700}}
.code{{color:#EBC3A8;background:#26241F;border-radius:7px;box-shadow:0 0 0 1px #34312A, 0 0 0 0 transparent;
  padding:0 2px;margin:0 -2px}}
#hl{{position:absolute;left:0;width:{W}px;height:{LH}px;top:{PAD_T + name_row * LH}px;transform-origin:0 50%;
  background:linear-gradient(90deg,rgba(217,119,87,.26),rgba(217,119,87,.10) 70%,rgba(217,119,87,.04))}}
#hlbar{{position:absolute;left:0;top:{PAD_T + name_row * LH}px;width:4px;height:{LH}px;background:{ORANGE}}}
#dude{{position:absolute;left:0;width:{W}px;top:{PAD_T + dude_row * LH}px;height:{dude_n * LH}px;
  background:linear-gradient(90deg,rgba(217,119,87,.20),rgba(217,119,87,.07) 75%,rgba(217,119,87,0))}}
#dudebar{{position:absolute;left:0;top:{PAD_T + dude_row * LH}px;width:5px;height:{dude_n * LH}px;background:{ORANGE};
  box-shadow:0 0 14px 2px rgba(217,119,87,.55)}}
#ftop{{position:absolute;left:0;top:{HEAD}px;width:{W}px;height:22px;background:linear-gradient(#141413,rgba(20,20,19,0))}}
#fbot{{position:absolute;left:0;bottom:0;width:{W}px;height:130px;background:linear-gradient(rgba(20,20,19,0),rgba(20,20,19,.85) 60%,#141413)}}
#track{{position:absolute;right:8px;top:{HEAD + track_top}px;width:9px;height:{track_h}px;border-radius:9px;background:rgba(255,255,255,.025)}}
#thumb{{position:absolute;left:0;top:0;width:9px;height:{thumb_h}px;border-radius:9px;background:rgba(236,234,226,.22)}}
"""

    MD = ('<svg id="md" viewBox="0 0 30 20"><rect x=".75" y=".75" width="28.5" height="18.5" rx="4" fill="none" stroke="#7FA7D9" stroke-width="1.5"/>'
          '<path d="M5 14.5V5.5l3.5 4.3 3.5-4.3v9" fill="none" stroke="#7FA7D9" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>'
          '<path d="M21 5.5v8.5M17.6 11l3.4 3.5 3.4-3.5" fill="none" stroke="#7FA7D9" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/></svg>')
    SPLIT = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6E6B63" stroke-width="1.8"><rect x="3" y="4" width="18" height="16" rx="2.5"/><path d="M12 4v16"/></svg>')
    DOTS = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="#6E6B63"><circle cx="5" cy="12" r="1.8"/><circle cx="12" cy="12" r="1.8"/><circle cx="19" cy="12" r="1.8"/></svg>')

    body = []
    A = body.append
    A('<div id="tbar"><div id="lights"><i style="background:#FF5F57"></i><i style="background:#FEBC2E"></i><i style="background:#28C840"></i></div>')
    A(f'<div id="tab">{MD}<span>SKILL.md</span><span class="x">&times;</span></div>')
    A(f'<div id="tright">{SPLIT}{DOTS}</div></div>')
    A('<div id="crumb"><span>.claude</span><span class="s">/</span><span>skills</span><span class="s">/</span>'
      '<span>video-edit</span><span class="s">/</span><span class="e">SKILL.md</span></div>')
    A('<div id="view"><div id="code">')
    A('<div id="hl"></div><div id="hlbar"></div><div id="dude"></div><div id="dudebar"></div>')
    A('\n'.join(rows_html))
    A('</div></div>')
    A('<div id="ftop"></div><div id="fbot"></div>')
    A('<div id="track"><div id="thumb"></div></div>')
    A('<div id="winline"></div>')

    J = []
    T = J.append
    T("const tl = gsap.timeline({ paused: true });")
    T("gsap.set('#win',{autoAlpha:0,y:40,scale:.96});")
    T("gsap.set('#hl',{scaleX:0,autoAlpha:1});")
    T("gsap.set('#hlbar',{autoAlpha:0});")
    T("gsap.set(['#dude','#dudebar'],{autoAlpha:0});")
    T("gsap.set('#code',{y:0});")
    T("gsap.set('#thumb',{y:0});")
    # entrance
    T("tl.to('#win',{autoAlpha:1,y:0,scale:1,duration:.30,ease:'power3.out'},0);")
    # name highlight sweep, stays faintly
    T("tl.to('#hl',{scaleX:1,duration:.38,ease:'power2.inOut'},0.15);")
    T("tl.fromTo('#hlbar',{autoAlpha:0},{autoAlpha:1,duration:.15,ease:'power1.out',immediateRender:false},0.15);")
    T("tl.to('#ln2',{color:'#CFCBBF',duration:.2},0.15);")
    T("tl.to('#hl',{autoAlpha:.45,duration:.4,ease:'power1.inOut'},0.62);")
    T("tl.to('#hlbar',{autoAlpha:.5,duration:.4,ease:'power1.inOut'},0.62);")
    # scroll
    T(f"tl.to('#code',{{y:{-scroll},duration:1.5,ease:'power2.inOut'}},0.45);")
    T(f"tl.to('#thumb',{{y:{thumb_travel},duration:1.5,ease:'power2.inOut'}},0.45);")
    # cool dude glow around 1.2s
    T("tl.fromTo(['#dude','#dudebar'],{autoAlpha:0},{autoAlpha:1,duration:.16,ease:'power2.out',immediateRender:false},1.08);")
    T("tl.to(['#dude','#dudebar'],{autoAlpha:0,duration:.35,ease:'power1.inOut'},1.55);")
    T(f"tl.set({{}}, {{}}, {DUR});")
    T('window.__timelines = window.__timelines || {};')
    T('window.__timelines["main"] = tl;')

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={W}, height={HT}" />
<link rel="stylesheet" href="assets/fonts/fonts.css" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="{W}" data-height="{HT}">
<div id="win">
{''.join(body)}
</div>
</div>
<script>
{chr(10).join(J)}
</script>
</body>
</html>
"""
    with open('index.html', 'w', encoding='utf-8', newline='\n') as f:   # utf-8 on every OS (Windows defaults to cp1252)
        f.write(page)
    print('wrote index.html')


if __name__ == '__main__':
    build()
