# Hebrew (and English) reels

`config.json` "language" is the default (`he` or `en`); `--lang` on ingest.py / transcribe_cut.py overrides it per
reel. The template reads it: `DIR = rtl` for Hebrew, captions and cards flip with it.

## Speech to text
- Hebrew: ivrit.ai's Whisper (`ivrit-ai/whisper-large-v3-turbo-ct2`, ~1.6 GB, downloaded on first use, cached in
  `~/.cache/huggingface`). Plain Whisper small/medium is not usable for Hebrew. English: small.en / medium.en.
- CPU only (`device='cpu'`): 85s of Hebrew takes ~3 min on an 8-core laptop.
- **The prompt can delete the opening.** With "הבחירות בישראל" in initial_prompt, Whisper skipped the clip's first
  sentence "היום הבחירות בישראל" and stretched the next word over it. speech.py now re-transcribes the first 8s
  without the prompt and keeps whichever pass heard more words. Still: never paste the script's opening into --prompt.
- Whisper mishears Hebrew words that matter ("כיבו" -> "קיבלו"). When the creator gives the script, ALWAYS align to it
  (align.py): captions show their exact words, only the times come from Whisper. Niqqud in the script (מֵרוֹצֵי) is
  stripped for display.

## Captions (RTL)
- `.cap{direction:rtl}`, one `<span class="cw">` per word with `unicode-bidi:isolate`, and a real space between the
  spans (joined with '' the words ran together: "כיבמחקרשפורסם").
- Mixed words render correctly that way: "ל-AI" shows as ל on the right, AI on the left. Pure Latin/number items
  that must read left to right on their own ("<10%", "~500", "24/30") get `dir="ltr"`.
- Fonts (bundled, OFL): Heebo 500/700/800/900 (captions, cards), Secular One, Suez One, in `assets/fonts/fonts-he.css`
  with `unicode-range` split hebrew / latin. Latin-only fonts (Inter, Montserrat...) have no Hebrew glyphs.
- Hebrew letters in Heebo 900 are ~.73em tall (taller than a Latin x-height): behind-head words use
  `top = head_top - .68*S`, not the Latin formula.
- Gershayim and geresh: use ״ (U+05F4) and ׳ (U+05F3) ("ארה״ב", "א׳"); Heebo's Hebrew subset has them.

## Arrows and symbols
Heebo's latin subset has no ← → (U+2190/2192). Draw arrows as inline SVG (`arrow()` in the template), checks and
crosses as SVG (`CHECK`, `CROSS`). Avoid emoji: the renderer's emoji font is not the phone's.

## English reels
Set `"language": "en"` (or `--lang en`): small.en / medium.en, `DIR = ltr`, captions read left to right; the
LinkedIn card's line becomes `linkedinSubtitle.en` ("Let's connect on LinkedIn!"). Inter / Inter Tight
(`fonts.css`) are the Latin display fonts; Heebo also has Latin.
