# In-page audio reader for the read-along storybook: research and recommendation

Scope: add a lightweight, self-contained audio reader to the read-along skill's tour page (one local HTML file, Georgia serif, dark bg, `<section class="stop" id="stopN">` blocks, GREEN/AMBER/DASHED boxes, occasional number tables, a final "paper trail" stop). Hard constraint: opens from file://, works with zero network, and still prints cleanly to PDF.

## Bottom line

- PRIMARY: the browser's built-in Web Speech API (`window.speechSynthesis`), driven off a per-section utterance queue, with a top-right docked pill. It adds zero bytes to the file, needs no network (local OS voices speak offline), and disappears from print with one `@media print` rule. This is the only option that satisfies all three hard constraints at once, and it matches the skill's zero-dependency, self-generating ethos: the skill can emit the widget as ~120 lines of inline JS/CSS with no build step and no API keys.
- FALLBACK (opt-in, not default): pre-generated per-section audio embedded as `data:` URIs (one clip per `.stop`, 32 kbps mono MP3). Use only when the operator specifically wants a guaranteed consistent natural voice and accepts a build-time TTS call plus a few MB of file bloat. A 10-minute tour is roughly 2 to 3 MB of audio, about +33 percent to the HTML as base64.
- Honest verdict on cloud TTS at read time: ruled out. Any read-time call to Google/OpenAI/ElevenLabs breaks the zero-network constraint. The natural-sounding Web Speech voices (Chrome's "Google ..." voices, Edge's "Microsoft ... Online (Natural)") are ALSO network voices, so offline you get the local SAPI voices (Windows David/Zira/Mark, macOS Samantha). Those are more robotic but fully offline and perfectly serviceable for a personal work tour. State this tradeoff to the operator rather than hiding it.

## 1. Web Speech API (speechSynthesis)

Support (2026): Baseline "widely available" since Sept 2018. `window.speechSynthesis` + `SpeechSynthesisUtterance` are in Chrome 33+, Edge 14+, Safari 7+, Firefox 49+, Opera, Samsung Internet. On the operator's target (desktop Chrome/Edge on Windows 11) it is solid. Core methods: `speak(u)`, `pause()`, `resume()`, `cancel()`, `getVoices()`; utterance events `onstart`, `onend`, `onerror`, `onboundary`; utterance props `voice`, `rate`, `pitch`, `volume`, `lang`.
- Sources: MDN SpeechSynthesis (https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis), testmuai support matrix (https://www.testmuai.com/learning-hub/speech-synthesis-api-browser-support/).

Voice quality / neural voices:
- Chrome exposes "Google US English" and friends: natural-sounding but NETWORK voices (server-synthesized). Offline they vanish.
- Edge exposes "Microsoft ... Online (Natural)" neural voices: excellent, but also network. Edge/Windows also ships local "Microsoft David/Zira/Mark - English (United States)" SAPI voices that work offline.
- So under the zero-network rule the reader must select a LOCAL voice. Pick the first `voice.localService === true` for the page language; fall back to any en-* voice. Do not hard-require a "Google" voice (see the bug below).

Known gotchas and the proven workarounds:
- The ~15-second / ~200-250-char cutoff (Chromium #40747712, a decade-old open bug): a single long utterance silently stops; `speaking` stays true, no error. Two independently proven fixes, and using BOTH is the robust move:
  1. Chunk text into short utterances (~160-200 chars, sentence-aligned) and queue them. This conveniently coincides with our per-section queue: sub-split each section into sentence chunks. (tomo-kay/tene commit, Kais3rP, many StackOverflow answers.)
  2. A keep-alive timer: on `onstart`, every ~14s call `speechSynthesis.pause()` then `speechSynthesis.resume()` while `speaking`; clear it on `onend`. The bare `resume()` trick stopped working years ago; the `pause()`-then-`resume()` pair still works and is confirmed specifically for the Google/network voices. (Caktus Group, Nov 2025: https://www.caktusgroup.com/blog/2025/11/03/the-halting-problem/.)
- The "stuck speaking" state: after a killed long utterance or a tab-hide, `speechSynthesis.speaking` can stay stuck true, and any `if (speaking) return` guard then goes permanently silent. Always call `cancel()` before starting a fresh play, and drive overlap-avoidance off your own state, not off `.speaking`. (creaseygit/data_as_music commit note.)
- `getVoices()` returns `[]` on first call in Chrome/Edge/Firefox: voices load async. Listen for the `voiceschanged` event and (re)read voices there; Safari populates synchronously. Guard the UI until voices resolve, but do not block play forever (a browser with no voices should degrade, see section 6).
- `cancel()` fires `onerror` with `error === 'interrupted'` or `'canceled'` on the in-flight utterance. Treat those two as normal, not errors; only propagate other error codes. (tene commit.)
- Rate range: spec allows 0.1-10 but real engines are stable roughly 0.5-2.0; clamp to that. Substack-style presets 0.8/1.0/1.25/1.5/2.0 are a good discrete cycle.
- iOS/Safari: `speak()` must be called inside a user-gesture handler (a tap), synchronously, no awaits before it. Not the primary target here but cheap to honor by starting playback straight from the click handler.
- `onboundary` (word/sentence position events) fires in Chrome/Edge but is unreliable in Firefox. We do NOT need it: section-level highlighting keys off `onstart`/`onend` per chunk, which is universal.

Self-containment scorecard for Web Speech: file bytes added = 0; offline = yes (local voices); prints clean = yes (widget is one DOM node, hidden with `@media print { #reader{display:none} }`, and it never touches the page's text nodes destructively, only wraps a highlight class it can remove). This is the decisive win.

## 2. Pre-generated embedded audio (the fallback)

Shape: at storybook-build time, synthesize one audio clip per `.stop` section, embed each as a `data:audio/mpeg;base64,...` on a hidden `<audio>` (or in a JS array). Section = natural skip unit (one clip each). Playback is an `<audio>` element, so speed (`playbackRate`), pause/resume, and progress are free and rock-solid, and the voice is a consistent high-quality neural voice chosen at build time.

Sizing (measured guidance, mono speech):
- Opus voip mode: ~0.18-0.24 MB/min at 24-32 kbps (WhatsApp/Telegram-class clarity). 10 min ≈ 2.0-2.4 MB.
- MP3 mono at 32 kbps: ~0.24 MB/min; 10 min ≈ 2.4 MB. MP3 is the safe embed format (Opus-in-WebM data URIs only play in Safari 15+/iOS 15+; MP3 plays everywhere).
- base64 inflates bytes ~33 percent, so a 2.4 MB MP3 tour becomes ~3.2 MB of inline text in the HTML. Still opens from file:// and prints fine (audio is display:none for print).
- Sources: Xiph Opus recommended settings (https://wiki.xiph.org/Opus_Recommended_Settings), CleverUtils and ChangeThisFile bitrate guides.

Honest tradeoffs vs Web Speech:
- Cost/latency/keys at BUILD time (not read time): needs an OpenAI/ElevenLabs/Azure call while generating the tour, plus network then. The read-along skill currently mints the page with zero external calls; this adds a dependency and a failure mode.
- File bloat: a few MB per tour vs zero.
- Staleness: if the operator edits a stop's prose (the skill says the storybook is "living" and gets new stops mid-tour), the embedded audio is instantly wrong; Web Speech always reads the current DOM.
- Upside: one consistent premium voice, perfect skip mapping (one file per section), no 15s bug, no voice-availability roulette.
- Net: keep it as an explicit opt-in ("bake narration") for a keepsake/shareable artifact, not the default.

## 3. Open-source widgets worth borrowing patterns from

- readium/speech (https://github.com/readium/speech) - TypeScript read-aloud engine built on Web Speech, follows the read-aloud-best-practices spec (https://github.com/HadrienGardeur/read-aloud-best-practices). Best reference for voice selection (grouped by region, sorted by quality), utterance generation from document fragments, and highlighting. Heavier than we need but the architecture and the best-practices doc are gold.
- Vanilla Breeze `<text-reader>` web component (https://profpowell.github.io/vanilla-breeze/docs/elements/web-components/text-reader/) - closest to our need: a zero-dependency custom element, Web Speech + CSS Custom Highlight API, progressive-enhancement (hides itself if no `speechSynthesis`), exposes `play/pause/resume/stop`, `progress` (0-1), `voices`. Uses system `Mark`/`MarkText` colors so highlighting respects contrast prefs. Borrow: the feature-detect-and-hide degradation, the `role="group"` + per-button `aria-label` a11y, cancel-on-unload.
- ResponsiveVoice web-player example (https://github.com/responsivevoice/examples/blob/main/browser/web-player/index.html) - the exact UX we want: a pill strip with play/pause, speed cycle, PARAGRAPH-skip controls, live progress, a `data-rv-skip` attribute to exclude blocks, click-a-paragraph-to-jump, and a compact floating mini-player when you scroll past. Great pattern source (the engine is cloud, ignore that part).
- SahilAggarwal2004/react-text-to-speech (https://github.com/SahilAggarwal2004/react-text-to-speech) - auto-chunks long text past the utterance limit and stitches it back; `highlightMode: word|sentence|line|paragraph`. Good chunking reference.
- albirrkarim react/vanilla-speech-highlight (https://react-speech-highlight.vercel.app/, 45 KB vanilla build) - dual mode (Web Speech OR embedded audio files) with word/sentence highlight; useful as proof of the exact PRIMARY-plus-FALLBACK split we recommend.
- Kais3rP/react-text2speech and tomo-kay/tene's blog player (https://github.com/tomo-kay/tene/commit/ce1d01f) - tene is the single most on-point code sample: a "Listen" button, Web Speech only, ~160-char sentence chunking for the 15s bug, blockIndex-tagged chunks so scroll-sync can `scrollIntoView` on paragraph transitions, and the `error !== 'interrupted'/'canceled'` filter. Nearly a drop-in template for our section queue.

## 4. UX conventions users expect

From Substack (redesigned podcast player, July 2026: speed control in-player, offline, sleep timer), Pocket/Speechify/CastReader, and browser Read Aloud modes:
- A small FLOATING pill/bar, not inline-blocking. Substack and CastReader use a persistent floating player; the operator's spec docks it TOP-RIGHT (good: out of the reading column, out of the way of the sticky stop-nav which is usually top-left/top).
- Expected controls, left to right: play/pause (primary), skip back / skip forward, speed (a cycling chip like "1x" -> "1.25x"), and a minimize/dismiss. Volume is optional for speech and can be dropped.
- Progress: for a section-based unit, show "Stop N of M" plus a thin segmented or fractional bar, NOT a seconds timeline (there is no reliable total duration for live TTS, and the operator explicitly wants section granularity). CastReader/ResponsiveVoice both highlight the active block and auto-scroll it into view ("the page follows the voice") - that read-along property is the thing users love most.
- Click-to-jump: clicking a section to start there is a common affordance elsewhere (ResponsiveVoice, CastReader), but for THIS page it is deliberately NOT implemented (v5.0.1). The reading surface is where the operator reads, selects, and scrolls; wiring clicks to playback made ordinary reading resume the voice and felt like the whole page was a resume button. Keep all playback control on the pill; navigate sections with prev/next.
- Skip semantics: jump at BLOCK boundaries, not mid-sentence (ResponsiveVoice makes this explicit as a v1 correctness choice) - which is exactly the operator's "skip by section" requirement, so we cancel and restart at the next section rather than seeking within audio.
- Minimize: collapse to just a play/pause dot in the corner; expand on hover/click. Substack keeps a mini-player; the operator wants a minimize toggle.

## 5. Implementation sketch for the storybook template

Design decisions mapped to the page:
- Read unit = each `<section class="stop">` in document order, top to bottom, whether or not the reader clicked the nav (satisfies "reads the whole page").
- Per section, build narration text by walking child nodes but EXCLUDING un-speakable blocks: `table`, `pre`, `code`, the DASHED `.demo` box, and the sticky `nav`. Replace an excluded block with a one-line spoken stub ("A table of 8 rows follows. Skipping to the next part.") so the listener knows something was there. Everything else contributes `textContent`.
- Sub-chunk each section into <=200-char sentence pieces for the 15s bug; queue is a flat list of `{sectionIdx, text}`. Skip next/prev moves to the next/prev distinct `sectionIdx`. Highlight + `scrollIntoView` the section whose chunk is currently speaking.
- Belt-and-suspenders: sentence chunking AND the 14s pause/resume keep-alive.

```html
<div id="reader" data-min="0" aria-label="Storybook reader" role="group">
  <button id="rd-min"  aria-label="Minimize reader">_</button>
  <button id="rd-prev" aria-label="Previous section">|<</button>
  <button id="rd-play" aria-label="Play">&#9654;</button>
  <button id="rd-next" aria-label="Next section">>|</button>
  <button id="rd-rate" aria-label="Speed">1x</button>
  <span   id="rd-prog" aria-live="polite">-- / --</span>
</div>
<style>
  #reader{position:fixed;top:14px;right:14px;z-index:9999;display:flex;gap:6px;
    align-items:center;padding:6px 10px;border-radius:999px;font:14px system-ui;
    background:rgba(30,30,34,.92);color:#f2efe6;box-shadow:0 4px 18px rgba(0,0,0,.4)}
  #reader button{background:transparent;border:0;color:inherit;cursor:pointer;
    font-size:15px;line-height:1;padding:4px 6px;border-radius:6px}
  #reader button:hover{background:rgba(255,255,255,.14)}
  #reader[data-min="1"] > :not(#rd-min):not(#rd-play){display:none}
  .stop.rd-active{outline:2px solid #d9a441;outline-offset:8px;border-radius:6px}
  @media print{#reader{display:none!important}.stop.rd-active{outline:0}}
  @media (prefers-reduced-motion:no-preference){.stop{scroll-margin-top:70px}}
</style>
<script>
(function(){
  var synth = window.speechSynthesis;
  var R = document.getElementById('reader');
  if(!synth){ R.style.display='none'; return; }           // graceful degradation
  var SKIP='table,pre,code,.demo,nav,#reader';
  var RATES=[0.8,1,1.25,1.5,2], ri=1;
  var voice=null, queue=[], qi=0, playing=false, keep=null, lastChar=0, cancelling=false;
  function deliberateCancel(){ cancelling=true; synth.cancel(); }

  function pickVoice(){
    var v=synth.getVoices();
    voice=v.find(function(x){return x.localService&&/^en/i.test(x.lang);})
        || v.find(function(x){return /^en/i.test(x.lang);}) || v[0] || null;
  }
  synth.onvoiceschanged=pickVoice; pickVoice();

  function sectionText(sec){                                // narration, minus un-speakable blocks
    var out=[];
    sec.querySelectorAll(':scope *').forEach(function(){});  // (walk below)
    (function walk(node){
      node.childNodes.forEach(function(n){
        if(n.nodeType===3){ var t=n.textContent.trim(); if(t) out.push(t); return; }
        if(n.nodeType!==1) return;
        if(n.matches(SKIP)){
          var tag=n.tagName.toLowerCase();
          if(tag==='table'){ out.push('A table follows. Skipping to the next part.'); }
          else if(tag==='pre'||tag==='code'){ out.push('A code block follows. Skipping.'); }
          return;                                            // demo/nav: silent skip
        }
        walk(n);
      });
    })(sec);
    return out.join(' ').replace(/\s+/g,' ');
  }
  function chunk(t){                                         // <=200 char, sentence-aligned (15s bug)
    return t.match(/[\s\S]{1,200}[.!?](?=\s|$)|[\s\S]{1,200}/g)||[t];
  }
  function build(){
    queue=[]; var secs=[].slice.call(document.querySelectorAll('.stop'));
    secs.forEach(function(sec,i){ chunk(sectionText(sec)).forEach(function(c){
      queue.push({s:i,el:sec,text:c}); }); });
  }
  function highlight(i){
    document.querySelectorAll('.stop.rd-active').forEach(function(e){e.classList.remove('rd-active');});
    var el=queue[i]&&queue[i].el; if(el){ el.classList.add('rd-active');
      el.scrollIntoView({behavior:'smooth',block:'start'}); }
    var total=document.querySelectorAll('.stop').length;
    document.getElementById('rd-prog').textContent=(queue[i]?queue[i].s+1:'--')+' / '+total;
  }
  function speak(fromChar){
    if(qi>=queue.length){ stop(); return; }
    highlight(qi);
    var base=fromChar||0, full=queue[qi].text;
    lastChar=base;
    var u=new SpeechSynthesisUtterance(base?full.slice(base):full);
    if(voice) u.voice=voice; u.rate=RATES[ri];
    u.onboundary=function(e){ lastChar=base+e.charIndex; };   // where the voice IS (word granularity)
    u.onstart=function(){ clearInterval(keep); keep=setInterval(function(){       // keep-alive
      if(!synth.speaking){clearInterval(keep);} else {synth.pause();synth.resume();} },14000); };
    u.onend=function(){ clearInterval(keep); if(cancelling){cancelling=false;return;}
      if(playing){ qi++; lastChar=0; speak(); } };
    u.onerror=function(e){ clearInterval(keep); if(cancelling){cancelling=false;return;}
      if(e.error!=='interrupted'&&e.error!=='canceled'){ qi++; lastChar=0; if(playing) speak(); } };
    synth.speak(u);
  }
  function play(){ if(!queue.length) build(); synth.cancel(); playing=true;
    document.getElementById('rd-play').innerHTML='&#10073;&#10073;';
    speak(lastChar); }   // pause glyph; resume from the last spoken word (v4.1)
  function pause(){ playing=false; synth.cancel(); clearInterval(keep);
    document.getElementById('rd-play').innerHTML='&#9654;'; }
  function stop(){ pause(); qi=0; lastChar=0;
    document.querySelectorAll('.stop.rd-active').forEach(function(e){e.classList.remove('rd-active');}); }
  function jump(dir){ var cur=queue[qi]?queue[qi].s:0, t=cur+dir;
    var idx=queue.findIndex(function(q){return q.s===t;}); if(idx<0) return;
    qi=idx; lastChar=0; if(playing){ deliberateCancel(); speak(); } else highlight(qi); }

  document.getElementById('rd-play').onclick=function(){ playing?pause():play(); };
  document.getElementById('rd-next').onclick=function(){ jump(1); };
  document.getElementById('rd-prev').onclick=function(){ jump(-1); };
  document.getElementById('rd-rate').onclick=function(){ ri=(ri+1)%RATES.length;
    this.textContent=RATES[ri]+'x';
    if(playing){ deliberateCancel(); speak(lastChar); } };  // resume at the last word, new speed
  document.getElementById('rd-min').onclick=function(){ R.dataset.min=R.dataset.min==='1'?'0':'1'; };
  // The reading area is intentionally NOT a player control (v5.0.1). Clicking, selecting, or
  // scrolling-then-clicking story text must never start or stop the voice - an earlier
  // click-a-section-to-play affordance hijacked ordinary reading and felt like the whole page
  // was a resume button. All playback control now lives on the pill; use prev/next to change section.
  window.addEventListener('beforeunload',function(){ synth.cancel(); });          // no orphan audio
})();
</script>
```

Notes on the sketch:
- v4.1 operator-feedback fix: a SPEED CHANGE and a PAUSE/RESUME must both pick up from the last spoken word, not the section start. The engine cannot seek inside an utterance, but `onboundary` reports the charIndex of each word as it is spoken; track it (`lastChar`), and on rate change cancel and re-speak `text.slice(lastChar)` at the new rate. Same fix hardened the deliberate-cancel race: `cancel()` can fire the old utterance's `onend` (advancing the queue) - a `cancelling` guard flag consumes exactly one such event. If a voice never fires boundary events, `lastChar` stays at the chunk start and the behavior degrades to the old chunk-restart, never worse.
- ~110 lines, zero dependencies, all inline: the skill can paste it verbatim into the generated file.
- `sectionText` is where the "exclude tables/code/demo, or replace with a spoken stub" requirement lives. Tune the stubs to taste (e.g. count rows: "a table of N rows").
- Highlight is a non-destructive class + outline; it removes cleanly and is suppressed in print. It never rewrites the page's text nodes, so PDF export is unaffected.
- Skip is section-granular by construction (`jump` moves by distinct `s` index; `cancel()` + restart at the boundary, never a mid-sentence seek).
- Progress reads "Stop N of M", matching the section unit, not seconds.

## 6. Graceful degradation

- No `speechSynthesis` at all (rare on desktop, and Firefox-Android): the script hides the pill immediately (`R.style.display='none'`) and the page is unchanged. Progressive enhancement, same as Vanilla Breeze.
- `speechSynthesis` present but `getVoices()` empty even after `voiceschanged` (some Linux Chrome with no engine, headless): `voice` stays null, utterances still attempt with the engine default; if nothing speaks, the user simply hears nothing and can close the pill. Optionally detect "no voices after 2s" and hide. Do not let a null voice block play.
- Offline: local voices only (documented tradeoff). If the operator wants the premium voice regardless, that is the pre-generated-audio fallback in section 2.
- Print: `@media print` hides the reader and the highlight outline; the file prints identically with or without the widget.

## Key sources
- MDN SpeechSynthesis: https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis
- Chromium 15s bug: https://issues.chromium.org/40747712 ; pause/resume fix write-up (Caktus, Nov 2025): https://www.caktusgroup.com/blog/2025/11/03/the-halting-problem/
- Browser support / voice quirks: https://www.testmuai.com/learning-hub/speech-synthesis-api-browser-support/
- Section-queue + scroll-sync template: https://github.com/tomo-kay/tene/commit/ce1d01f3ba97724a707ccca5d16b592fd62756fe
- readium/speech + read-aloud best practices: https://github.com/readium/speech , https://github.com/HadrienGardeur/read-aloud-best-practices
- Vanilla Breeze text-reader web component: https://profpowell.github.io/vanilla-breeze/docs/elements/web-components/text-reader/
- ResponsiveVoice pill/paragraph-skip UX: https://github.com/responsivevoice/examples/blob/main/browser/web-player/index.html
- Substack redesigned player (speed/offline/sleep): https://on.substack.com/p/new-on-substack-subscriber-perks
- CastReader read-along UX writeup: https://castreader.ai/blog/listen-to-substack-newsletters
- Opus/MP3 speech sizing: https://wiki.xiph.org/Opus_Recommended_Settings , https://cleverutils.com/opus-to-mp3/opus-bitrate-guide
