#!/usr/bin/env python3
"""Claude desktop app recreation: drop 5 clips, type /video-edit, Claude works on it.
1000x720, transparent outside the rounded window, 4.35s @30fps.
PY build.py  -> index.html      (PY = the skill's Python; any Python 3 works for this file)
"""
import math

DUR = 4.35
ORANGE = '#D97757'
CLIPS = 5


def spark(size, color=ORANGE, cls='', id_=''):
    lens = [46, 35, 43, 38, 46, 34, 44, 37, 45, 36]
    out = []
    for k in range(10):
        a = math.radians(k * 36 - 90 + ((k % 3) - 1) * 5)
        L = lens[k]
        out.append(f'<line x1="0" y1="0" x2="{L*math.cos(a):.1f}" y2="{L*math.sin(a):.1f}"/>')
    idattr = f' id="{id_}"' if id_ else ''
    return (f'<svg{idattr} class="{cls}" width="{size}" height="{size}" viewBox="-50 -50 100 100">'
            f'<g stroke="{color}" stroke-width="11" stroke-linecap="round">{"".join(out)}</g></svg>')


CHECK = ('<svg width="28" height="28" viewBox="0 0 28 28"><circle cx="14" cy="14" r="14" fill="#3F8F5A"/>'
         '<path d="M8 14.5l4 4 8-9" fill="none" stroke="#fff" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/></svg>')
CLIP_ICON = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#5E5D59" stroke-width="2" stroke-linecap="round" '
             'stroke-linejoin="round"><path d="M21.4 11.1l-8.6 8.6a5.5 5.5 0 01-7.8-7.8l8.6-8.6a3.7 3.7 0 015.2 5.2l-8.6 8.6a1.8 1.8 0 01-2.6-2.6l7.9-7.9"/></svg>')
SLIDERS = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#5E5D59" stroke-width="2" stroke-linecap="round">'
           '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2.2"/><circle cx="10" cy="17" r="2.2"/></svg>')
ARROW_UP = ('<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.8" stroke-linecap="round" '
            'stroke-linejoin="round"><path d="M12 19V5M5.5 11.5L12 5l6.5 6.5"/></svg>')
FOLDER = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round">'
          '<path d="M3 6.5A1.5 1.5 0 014.5 5H9l2 2.5h8.5A1.5 1.5 0 0121 9v9.5a1.5 1.5 0 01-1.5 1.5h-15A1.5 1.5 0 013 18.5z"/></svg>')
CHAT = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#5E5D59" stroke-width="2" stroke-linejoin="round">'
        '<path d="M4 5h16v11H9l-5 4z"/></svg>')
UPLOAD = ('<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#C2613F" stroke-width="2.2" stroke-linecap="round" '
          'stroke-linejoin="round"><path d="M12 15V4M7 8.5L12 4l5 4.5M4 15v3.5A1.5 1.5 0 005.5 20h13a1.5 1.5 0 001.5-1.5V15"/></svg>')
BOLT = ('<svg width="20" height="20" viewBox="0 0 24 24" fill="#D97757"><path d="M13.5 2L4.5 13.5h6L9.5 22l9-11.5h-6z"/></svg>')
CURSOR = ('<svg width="30" height="38" viewBox="0 0 22 28"><path d="M2 1.5v21.2l5.3-5.1 3.6 8.2 3.4-1.5-3.5-8h7.3z" '
          'fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>')
PLAY = ('<svg width="16" height="16" viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="rgba(0,0,0,.45)"/>'
        '<path d="M9.5 7.5l7 4.5-7 4.5z" fill="#fff"/></svg>')

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1000px;height:720px;overflow:hidden;background:transparent}
#root{position:relative;width:1000px;height:720px;overflow:hidden;background:transparent}
#win{position:absolute;left:0;top:0;width:1000px;height:720px;border-radius:22px;overflow:hidden;background:#FAF9F5;
  font-family:'Inter',sans-serif;font-weight:500;color:#1F1E1D;transform-origin:50% 50%}
#winline{position:absolute;inset:0;border-radius:22px;border:1px solid rgba(31,30,29,.13);z-index:50;pointer-events:none}
.abs{position:absolute}

/* sidebar */
#side{position:absolute;left:0;top:0;width:210px;height:720px;background:#F0EEE6;border-right:1px solid #E4E0D4}
#lights{position:absolute;left:20px;top:20px;display:flex;gap:8px}
#lights i{display:block;width:13px;height:13px;border-radius:50%}
#sbtoggle{position:absolute;left:174px;top:15px;width:22px;height:22px}
#newchat{position:absolute;left:12px;top:60px;width:186px;height:42px;display:flex;align-items:center;gap:11px;padding-left:8px;
  font-size:18px;font-weight:600;color:#1F1E1D}
#newchat b{width:28px;height:28px;border-radius:50%;background:#D97757;display:flex;align-items:center;justify-content:center;
  color:#fff;font-size:22px;font-weight:600;line-height:1}
.nav{position:absolute;left:12px;width:186px;height:36px;display:flex;align-items:center;gap:11px;padding-left:12px;font-size:17px;color:#3D3C38}
.slabel{position:absolute;left:24px;font-size:13.5px;font-weight:600;color:#8C8A83;letter-spacing:.01em}
#proj{position:absolute;left:12px;top:212px;width:186px;height:38px;border-radius:9px;background:#E2DED2;display:flex;align-items:center;
  gap:10px;padding-left:12px;font-size:17px;font-weight:600;color:#1F1E1D}
.rec{position:absolute;left:24px;width:174px;font-size:16.5px;color:#6B6A65;white-space:nowrap;overflow:hidden}
#user{position:absolute;left:12px;top:654px;width:186px;height:48px;display:flex;align-items:center;gap:10px;padding-left:8px;
  border-top:1px solid #E4E0D4}
#user b{width:32px;height:32px;border-radius:50%;background:#3D3929;color:#fff;font-size:15px;font-weight:600;display:flex;
  align-items:center;justify-content:center}
#user .n{font-size:15.5px;font-weight:600;line-height:1.15}
#user .p{font-size:12.5px;color:#8C8A83}

/* main header */
#mhead{position:absolute;left:250px;top:16px;height:26px;display:flex;align-items:center;gap:9px;font-size:17px;color:#6B6A65}
#mhead .sep{color:#B5B2A9}
#ttl{position:relative;display:inline-block;width:260px;height:26px}
#ttl span{position:absolute;left:0;top:0;line-height:26px;white-space:nowrap;color:#1F1E1D;font-weight:600}

/* greeting */
#greet{position:absolute;left:210px;top:112px;width:790px;display:flex;align-items:center;justify-content:center;gap:16px;
  font-size:34px;font-weight:600;letter-spacing:-.015em;color:#2B2A27}

/* conversation */
#conv{position:absolute;left:210px;top:52px;width:790px;height:452px;overflow:hidden}
#thread{position:absolute;left:40px;top:20px;width:710px;height:900px}
#convfade{position:absolute;left:210px;top:52px;width:780px;height:26px;background:linear-gradient(#FAF9F5,rgba(250,249,245,0))}
#umsg{position:absolute;left:0;top:0;width:710px;height:150px}
#uthumbs{position:absolute;right:0;top:0;display:flex;gap:8px}
#uthumbs .ut{position:relative;width:46px;height:80px;border-radius:9px;overflow:hidden;border:1px solid #E3DFD5}
#uthumbs img{width:100%;height:100%;object-fit:cover;display:block}
#uthumbs .ut svg{position:absolute;left:15px;top:32px}
#ububble{position:absolute;right:0;top:90px;height:56px;padding:0 22px;border-radius:18px;background:#F0EEE6;
  font-size:26px;line-height:56px;font-weight:500;color:#1F1E1D}
#ububble em{font-style:normal;color:#B85A3A;font-weight:600}
#rhead{position:absolute;left:0;top:172px;height:44px;display:flex;align-items:center;gap:12px}
#rspark{width:36px;height:36px}
#pill{display:flex;align-items:center;gap:8px;height:42px;padding:0 16px 0 12px;border-radius:999px;background:#fff;
  border:1px solid #E3DFD5;font-size:21px;color:#5E5D59;box-shadow:0 1px 2px rgba(0,0,0,.04)}
#pill b{font-weight:600;color:#1F1E1D}
.step{position:absolute;left:48px;height:36px;display:flex;align-items:center;gap:14px;font-size:24px;color:#1F1E1D;white-space:nowrap}
.ico{position:relative;width:28px;height:28px;flex:none}
.spin{position:absolute;left:1px;top:1px;width:26px;height:26px;border-radius:50%;border:3px solid #ECE3DA;border-top-color:#D97757;border-right-color:#D97757}
.chk{position:absolute;left:0;top:0;width:28px;height:28px}
#ptrack{position:absolute;left:90px;top:416px;width:380px;height:7px;border-radius:7px;background:#ECE7DD;overflow:hidden}
#pfill{width:100%;height:100%;background:#D97757;border-radius:7px;transform-origin:0 50%}
#file{position:absolute;left:48px;top:444px;width:430px;height:86px;border-radius:16px;background:#fff;border:1px solid #E3DFD5;
  box-shadow:0 4px 16px rgba(31,30,29,.06);display:flex;align-items:center;gap:16px;padding:0 18px 0 12px}
#fthumb{position:relative;width:38px;height:66px;border-radius:7px;overflow:hidden;flex:none}
#fthumb img{width:100%;height:100%;object-fit:cover;display:block}
#fthumb svg{position:absolute;left:11px;top:25px}
#file .t{flex:1;line-height:1.2}
#file .n{font-size:24px;font-weight:600;color:#1F1E1D}
#file .m{font-size:20px;color:#6B6A65;margin-top:3px}
#file .m i{font-style:normal;color:#3F8F5A;font-weight:600}
#fchk{width:30px;height:30px}

/* input */
#inp{position:absolute;left:238px;bottom:90px;width:734px;padding:14px 16px 12px;border-radius:22px;background:#fff;
  border:1px solid #E1DDD2;box-shadow:0 8px 28px rgba(31,30,29,.07),0 1px 3px rgba(31,30,29,.05)}
#chips{display:flex;gap:8px;height:0;align-items:flex-start}
.chip{width:132px;height:64px;flex:none;border-radius:12px;border:1px solid #E3DFD5;background:#FAF9F5;display:flex;align-items:center;
  gap:9px;padding:0 6px}
.chip img{width:34px;height:52px;border-radius:6px;object-fit:cover;display:block;flex:none}
.chip .n{font-size:20px;font-weight:600;line-height:1.15;color:#1F1E1D}
.chip .m{font-size:14px;color:#8C8A83;line-height:1.2}
#tline{position:relative;height:40px;font-size:24px;line-height:40px;white-space:nowrap;padding-left:4px}
.ch{display:inline}
#caret{display:inline-block;width:2.5px;height:28px;background:#1F1E1D;vertical-align:-6px;margin:0 1px}
#ph,#ph2{color:#8C8A83}
#tbar{position:relative;height:42px;margin-top:6px;display:flex;align-items:center;gap:8px}
.tb{width:40px;height:40px;border-radius:11px;border:1px solid #E3DFD5;display:flex;align-items:center;justify-content:center}
#send{position:absolute;right:0;top:1px;width:40px;height:40px;border-radius:12px;background:#D97757;display:flex;align-items:center;justify-content:center}
#dropov{position:absolute;inset:-1px;border-radius:22px;border:2.5px dashed #D97757;background:#FDF3EE;display:flex;align-items:center;
  padding-left:56px;gap:12px;font-size:23px;font-weight:600;color:#C2613F}
#disc{position:absolute;left:210px;top:648px;width:790px;text-align:center;font-size:14px;color:#9C9A92}

/* slash menu */
#menu{position:absolute;left:238px;bottom:290px;width:540px;padding:8px;border-radius:18px;background:#fff;border:1px solid #E1DDD2;
  box-shadow:0 14px 40px rgba(31,30,29,.13),0 2px 6px rgba(31,30,29,.06);transform-origin:0 100%}
#menu .hd{font-size:15px;font-weight:600;color:#8C8A83;padding:6px 12px 8px}
.mrow{position:relative;height:68px;border-radius:12px;display:flex;align-items:center;gap:14px;padding:0 12px}
.mrow.on{background:#F8EBE4}
.mrow.dim{opacity:.42}
.mrow .mi{width:42px;height:42px;border-radius:10px;background:#F3E6DE;color:#C2613F;font:500 22px 'JetBrains Mono',monospace;
  display:flex;align-items:center;justify-content:center;flex:none}
.mrow.dim .mi{background:#EFEDE6;color:#6B6A65}
.mrow .nm{font-size:24px;font-weight:600;line-height:1.15}
.mrow .ds{font-size:19px;color:#6B6A65;line-height:1.25}
.mrow .kb{position:absolute;right:14px;top:22px;font-size:15px;color:#B85A3A;border:1px solid #E9C9BA;border-radius:6px;padding:1px 7px}

/* drag */
#drag{position:absolute;left:0;top:0;width:0;height:0;z-index:40}
#stack{position:absolute;left:-180px;top:-150px;width:330px;height:200px;transform-origin:180px 150px}
.card{position:absolute;bottom:6px;width:86px;height:152px;border-radius:10px;overflow:hidden;border:3px solid #fff;background:#222;
  box-shadow:0 10px 26px rgba(0,0,0,.28),0 2px 6px rgba(0,0,0,.18);transform-origin:50% 115%}
.card img{width:100%;height:100%;object-fit:cover;display:block}
.card span{position:absolute;left:0;right:0;bottom:0;height:22px;background:rgba(20,20,20,.62);color:#fff;
  font:500 11.5px/22px 'JetBrains Mono',monospace;padding-left:5px;white-space:nowrap}
#badge{position:absolute;left:286px;top:6px;width:36px;height:36px;border-radius:50%;background:#E5483D;border:2.5px solid #fff;
  color:#fff;font-size:19px;font-weight:600;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 8px rgba(0,0,0,.25)}
#cursor{position:absolute;left:-3px;top:-2px}
"""


def build():
    h = []
    A = h.append
    # ---------- sidebar
    A('<div id="side">')
    A('<div id="lights"><i style="background:#FF5F57"></i><i style="background:#FEBC2E"></i><i style="background:#28C840"></i></div>')
    A('<svg id="sbtoggle" viewBox="0 0 24 24" fill="none" stroke="#8C8A83" stroke-width="2"><rect x="3" y="4.5" width="18" height="15" rx="3"/><path d="M9.5 4.5v15"/></svg>')
    A('<div id="newchat"><b>+</b>New chat</div>')
    A(f'<div class="nav" style="top:110px">{CHAT}Chats</div>')
    A(f'<div class="nav" style="top:146px">{FOLDER.format(c="#5E5D59")}Projects</div>')
    A('<div class="slabel" style="top:192px">Projects</div>')
    A(f'<div id="proj">{FOLDER.format(c="#D97757")}Reels</div>')
    A('<div class="slabel" style="top:272px">Recents</div>')
    for i, t in enumerate(['Launch checklist', 'Content ideas', 'Newsletter draft', 'Hook research', 'Landing page copy', 'Thumbnail tests']):
        A(f'<div class="rec" style="top:{298 + i * 36}px">{t}</div>')
    A('<div id="user"><b>Y</b><div><div class="n">You</div><div class="p">Pro plan</div></div></div>')
    A('</div>')
    # ---------- header
    A(f'<div id="mhead">{FOLDER.format(c="#8C8A83")}<span>Reels</span><span class="sep">/</span>'
      '<span id="ttl"><span id="ttl1">New chat</span><span id="ttl2">Edit clips into a reel</span></span></div>')
    # ---------- greeting
    A(f'<div id="greet">{spark(40)}<span>What are we making today?</span></div>')
    # ---------- conversation
    A('<div id="conv"><div id="thread">')
    A('<div id="umsg"><div id="uthumbs">')
    for i in range(CLIPS):
        A(f'<div class="ut"><img src="inputs/clip{i+1}.jpg" alt="">{PLAY}</div>')
    A('</div><div id="ububble"><em>/video-edit</em></div></div>')
    A(f'<div id="rhead">{spark(36, id_="rspark")}<div id="pill">{BOLT}<span>Using skill <b>video-edit</b></span></div></div>')
    steps = ['Transcribing 5 clips', 'Picking the best takes', 'Cutting, captions, motion graphics', 'Rendering reel.mp4']
    for i, t in enumerate(steps):
        A(f'<div class="step" id="st{i}" style="top:{232 + i * 46}px"><div class="ico"><div class="spin" id="sp{i}"></div>'
          f'<div class="chk" id="ck{i}">{CHECK}</div></div><span>{t}</span></div>')
    A('<div id="ptrack"><div id="pfill"></div></div>')
    A(f'<div id="file"><div id="fthumb"><img src="inputs/clip3.jpg" alt="">{PLAY}</div>'
      '<div class="t"><div class="n">reel.mp4</div><div class="m">0:26 &middot; <i>ready</i></div></div>'
      f'<div id="fchk">{CHECK.replace("28", "30")}</div></div>')
    A('</div></div><div id="convfade"></div>')
    # ---------- input
    A('<div id="inp"><div id="chips">')
    for i in range(CLIPS):
        A(f'<div class="chip" id="chip{i}"><img src="inputs/clip{i+1}.jpg" alt=""><div><div class="n">clip_0{i+1}</div>'
          f'<div class="m">MP4 video</div></div></div>')
    A('</div><div id="tline">')
    A(''.join(f'<span class="ch" id="c{j}">{c}</span>' for j, c in enumerate('/video-edit'))
      + '<span id="caret"></span><span id="ph">How can I help you today?</span><span id="ph2">Reply to Claude...</span></div>')
    A(f'<div id="tbar"><div class="tb">{CLIP_ICON}</div><div class="tb">{SLIDERS}</div><div id="send">{ARROW_UP}</div></div>')
    A(f'<div id="dropov">{UPLOAD}<span>Drop files here</span></div>')
    A('</div>')
    A('<div id="disc">Claude can make mistakes. Please double-check responses.</div>')
    # ---------- slash menu
    A('<div id="menu"><div class="hd">Skills</div>')
    A('<div class="mrow on"><div class="mi">/</div><div><div class="nm">/video-edit</div>'
      '<div class="ds">Edit raw clips into a finished reel</div></div><div class="kb">&#8629;</div></div>')
    A('<div class="mrow dim"><div class="mi">/</div><div><div class="nm">/carousel</div><div class="ds">Turn an idea into a carousel</div></div></div>')
    A('<div class="mrow dim"><div class="mi">/</div><div><div class="nm">/script</div><div class="ds">Write a reel script in your voice</div></div></div>')
    A('</div>')
    # ---------- drag stack + cursor
    A('<div id="drag"><div id="stack">')
    for i in range(CLIPS):
        A(f'<div class="card" id="cd{i}" style="left:{20 + i * 50}px;z-index:{i};transform:rotate({(i - 2) * 7}deg)">'
          f'<img src="inputs/clip{i+1}.jpg" alt=""><span>clip_0{i+1}.mp4</span></div>')
    A('<div id="badge">5</div></div>')
    A(f'<div id="cursor">{CURSOR}</div></div>')
    A('<div id="winline"></div>')
    body = '\n'.join(h)

    # ---------- timeline
    J = []
    T = J.append
    T("const tl = gsap.timeline({ paused: true });")
    # window pop
    T("gsap.set('#win',{autoAlpha:0,scale:.94});")
    T("tl.to('#win',{autoAlpha:1,scale:1,duration:.30,ease:'power3.out'},0);")
    # initial states
    T("gsap.set(['#umsg','#rhead','.step','#ptrack','#file','#menu','#dropov','#drag','#caret','#ttl2','#fchk'],{autoAlpha:0});")
    T("gsap.set('.chk',{autoAlpha:0});")
    T("gsap.set('.chip',{autoAlpha:0});")
    T("gsap.set('.ch',{display:'none'});")
    T("gsap.set('#send',{opacity:.4});")
    T("gsap.set('#ph2',{display:'none'});")
    T("gsap.set('#pfill',{scaleX:0});")
    # drag: cursor + stack from lower-left into input
    X0, Y0, X1, Y1 = -70, 800, 820, 588
    T(f"gsap.set('#drag',{{x:{X0},y:{Y0}}});")
    T("tl.set('#drag',{autoAlpha:1},0.40);")
    T(f"tl.to('#drag',{{x:{X1},duration:.85,ease:'power2.inOut'}},0.40);")
    T(f"tl.to('#drag',{{y:{Y1},duration:.85,ease:'power3.out'}},0.40);")
    T("gsap.set('#stack',{rotation:-6,scale:.92});")
    T("tl.to('#stack',{rotation:3,duration:.5,ease:'sine.inOut'},0.40);")
    T("tl.to('#stack',{rotation:0,scale:.88,duration:.35,ease:'power2.out'},0.90);")
    # hover highlight
    T("tl.fromTo('#dropov',{autoAlpha:0},{autoAlpha:1,duration:.12,ease:'power1.out',immediateRender:false},0.96);")
    # release at 1.30
    T("tl.to('#stack',{scale:.25,autoAlpha:0,y:24,duration:.16,ease:'power2.in'},1.30);")
    T("tl.to('#dropov',{autoAlpha:0,duration:.12,ease:'power1.out'},1.30);")
    T("tl.to('#chips',{height:74,duration:.18,ease:'power2.out'},1.28);")
    for i in range(CLIPS):
        t = 1.30 + i * 0.05
        T(f"tl.fromTo('#chip{i}',{{autoAlpha:0,scale:.6,y:10}},{{autoAlpha:1,scale:1,y:0,duration:.12,ease:'back.out(1.8)',immediateRender:false}},{t:.3f});")
    T("tl.to('#cursor',{x:26,y:-18,duration:.3,ease:'power2.out'},1.34);")
    T("tl.to('#drag',{autoAlpha:0,duration:.12},1.60);")
    # typing
    T("tl.set('#caret',{autoAlpha:1},1.62);")
    T("tl.set('#caret',{autoAlpha:0},1.69);")
    times = [1.76, 1.83, 1.87, 1.92, 1.96, 2.00, 2.06, 2.11, 2.15, 2.19, 2.24]
    T("tl.set('#caret',{autoAlpha:1},1.75);")
    T("tl.set('#ph',{display:'none'},1.76);")
    for j, t in enumerate(times):
        T(f"tl.set('#c{j}',{{display:'inline'}},{t:.2f});")
    T("tl.to('#send',{opacity:1,duration:.1},1.76);")
    T("tl.set('#caret',{autoAlpha:0},2.28);tl.set('#caret',{autoAlpha:1},2.34);")
    # slash menu
    T("tl.fromTo('#menu',{autoAlpha:0,y:10,scale:.97},{autoAlpha:1,y:0,scale:1,duration:.16,ease:'power3.out',immediateRender:false},1.80);")
    # enter at 2.40
    T("tl.to('#send',{scale:.9,duration:.05,ease:'power1.in'},2.35);")
    T("tl.to('#send',{scale:1,opacity:.4,duration:.12,ease:'power2.out'},2.40);")
    T("tl.to('#menu',{autoAlpha:0,y:6,duration:.1,ease:'power1.in'},2.40);")
    T("tl.set('.ch',{display:'none'},2.40);tl.set('#ph2',{display:'inline'},2.40);")
    T("tl.to('.chip',{autoAlpha:0,duration:.08},2.40);")
    T("tl.to('#chips',{height:0,duration:.22,ease:'power2.inOut'},2.40);")
    T("tl.to('#greet',{autoAlpha:0,y:-8,duration:.08,ease:'power1.in'},2.38);")
    T("tl.fromTo('#umsg',{autoAlpha:0,y:46},{autoAlpha:1,y:0,duration:.32,ease:'power3.out',immediateRender:false},2.40);")
    T("tl.to('#ttl1',{autoAlpha:0,duration:.15},2.90);")
    T("tl.fromTo('#ttl2',{autoAlpha:0,y:4},{autoAlpha:1,y:0,duration:.2,ease:'power2.out',immediateRender:false},2.95);")
    # reply
    T("tl.fromTo('#rhead',{autoAlpha:0,y:10},{autoAlpha:1,y:0,duration:.2,ease:'power2.out',immediateRender:false},2.55);")
    T("tl.fromTo('#rspark',{scale:.5,rotation:-60},{scale:1,rotation:0,duration:.25,ease:'back.out(2)',immediateRender:false},2.55);")
    T("tl.to('#rspark',{rotation:200,duration:1.3,ease:'none'},2.80);")
    T("tl.to('#rspark',{rotation:216,duration:.22,ease:'power2.out'},4.10);")
    starts = [2.80, 3.05, 3.30, 3.60]
    checks = [3.05, 3.30, 3.60, 4.05]
    for i, (s, c) in enumerate(zip(starts, checks)):
        T(f"tl.fromTo('#st{i}',{{autoAlpha:0,y:10}},{{autoAlpha:1,y:0,duration:.18,ease:'power2.out',immediateRender:false}},{s:.2f});")
        T(f"tl.fromTo('#sp{i}',{{rotation:0}},{{rotation:{360 * (c - s) / 0.55:.0f},duration:{c - s:.2f},ease:'none',immediateRender:false}},{s:.2f});")
        T(f"tl.set('#sp{i}',{{autoAlpha:0}},{c:.2f});")
        T(f"tl.fromTo('#ck{i}',{{autoAlpha:0,scale:.4}},{{autoAlpha:1,scale:1,duration:.16,ease:'back.out(2.2)',immediateRender:false}},{c:.2f});")
    T("tl.fromTo('#ptrack',{autoAlpha:0},{autoAlpha:1,duration:.15,immediateRender:false},3.62);")
    T("tl.to('#pfill',{scaleX:1,duration:.43,ease:'power1.inOut'},3.62);")
    # auto-scroll the thread to keep newest content in view
    T("tl.to('#thread',{y:-46,duration:.28,ease:'power2.inOut'},3.50);")
    T("tl.to('#thread',{y:-104,duration:.24,ease:'power2.inOut'},3.92);")
    # final file card
    T("tl.fromTo('#file',{autoAlpha:0,y:14,scale:.97},{autoAlpha:1,y:0,scale:1,duration:.2,ease:'power3.out',immediateRender:false},4.10);")
    T("tl.fromTo('#fchk',{autoAlpha:0,scale:.4},{autoAlpha:1,scale:1,duration:.16,ease:'back.out(2.2)',immediateRender:false},4.16);")
    T(f"tl.set({{}}, {{}}, {DUR});")
    T('window.__timelines = window.__timelines || {};')
    T('window.__timelines["main"] = tl;')
    js = '\n'.join(J)

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1000, height=720" />
<link rel="stylesheet" href="assets/fonts/fonts.css" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1000" data-height="720">
<div id="win">
{body}
</div>
</div>
<script>
{js}
</script>
</body>
</html>
"""
    with open('index.html', 'w', encoding='utf-8', newline='\n') as f:   # utf-8 on every OS (Windows defaults to cp1252)
        f.write(html)
    print('wrote index.html')


if __name__ == '__main__':
    build()
