"""
ASMA Accordi Next Generation - Live Stage Web Component
Standalone HTML5/JS/Canvas Component for Live Stage Execution.
Conforms to SRS Cap. 12 and Blueprint Sec. 9.
Features: 60fps Smooth Scroll, WakeLock, Bluetooth Pedals, WebAudio Metronome, Offline Cache.
"""

from __future__ import annotations
import json
from typing import List, Dict, Any, Optional
from asma_core.models import Song
from asma_core.aml_parser import AMLParser, ChordLyricLineNode, ChordGridLineNode, SectionNode, CustomTagNode


class LiveStageComponent:
    """Generates the self-contained HTML/JS bundle for the Live Stage View."""

    @classmethod
    def render_html_bundle(
        cls,
        songs: List[Song],
        initial_index: int = 0,
        dark_theme: bool = True,
        initial_speed: int = 35,  # px/second
        auto_start: bool = True,
        auto_start_delay: int = 2  # seconds
    ) -> str:
        """
        Builds a self-contained HTML/CSS/JS application that runs client-side inside the browser.
        """
        import base64
        import os
        logo_b64 = ""
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "band_logo.png")
        if not os.path.exists(logo_path):
            logo_path = "assets/band_logo.png"
        if os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as f:
                    logo_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                pass

        # Pre-process songs into structured JSON for client-side rendering
        client_songs: List[Dict[str, Any]] = []
        for s in songs:
            doc = AMLParser.parse(s.aml_content)
            sections_data = []
            curr_section = {"name": "INIZIO", "lines": []}

            for node in doc.nodes:
                if isinstance(node, SectionNode):
                    if curr_section["lines"]:
                        sections_data.append(curr_section)
                    curr_section = {"name": node.section_name.upper(), "lines": []}
                elif isinstance(node, ChordGridLineNode):
                    curr_section["lines"].append({
                        "type": "grid",
                        "measures": node.measures
                    })
                elif isinstance(node, ChordLyricLineNode):
                    chord_parts = []
                    lyric_parts = []
                    for seg in node.segments:
                        chord_parts.append(seg.chord.chord_text if seg.chord else "")
                        lyric_parts.append(seg.text or "")
                    curr_section["lines"].append({
                        "type": "chord_lyric",
                        "chords": chord_parts,
                        "lyrics": lyric_parts
                    })
                elif isinstance(node, CustomTagNode):
                    curr_section["lines"].append({
                        "type": "tag",
                        "tag": node.tag_type.upper(),
                        "content": node.content
                    })

            if curr_section["lines"]:
                sections_data.append(curr_section)

            client_songs.append({
                "uuid": s.uuid,
                "title": s.title,
                "artist": s.artist,
                "key": s.key_current,
                "bpm": s.bpm,
                "time_signature": s.time_signature,
                "shared_notes": s.shared_notes,
                "sections": sections_data
            })

        songs_json = json.dumps(client_songs, ensure_ascii=False)

        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>ASMA Live Stage</title>
<style>
  :root {{
    --bg-color: {'#000000' if dark_theme else '#FFFFFF'};
    --text-color: {'#FFFFFF' if dark_theme else '#111111'};
    --chord-color: {'#FFD600' if dark_theme else '#C62828'};
    --badge-bg: {'#1A237E' if dark_theme else '#E0E0E0'};
    --badge-color: {'#FFFFFF' if dark_theme else '#0D47A1'};
    --grid-bg: {'#121212' if dark_theme else '#F5F5F5'};
    --grid-border: {'#37474F' if dark_theme else '#B0BEC5'};
    --tag-bg: {'#311B92' if dark_theme else '#EDE7F6'};
    --tag-color: {'#D1C4E9' if dark_theme else '#4A148C'};
  }}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    user-select: none;
    -webkit-user-select: none;
  }}

  html, body {{
    background-color: var(--bg-color);
    color: var(--text-color);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    overflow: hidden;
    height: 100%;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
  }}

  /* Top Stage HUD */
  #stage-hud {{
    background: #111111;
    border-bottom: 2px solid #333333;
    color: #FFFFFF;
    padding: 8px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 14px;
    z-index: 100;
  }}

  .hud-group {{
    display: flex;
    align-items: center;
    gap: 12px;
  }}

  .btn {{
    background: #263238;
    color: #FFFFFF;
    border: 1px solid #455A64;
    padding: 6px 14px;
    border-radius: 6px;
    font-weight: bold;
    cursor: pointer;
    font-size: 13px;
  }}

  .btn:active {{
    background: #37474F;
  }}

  .btn-accent {{
    background: #0288D1;
    border-color: #039BE5;
  }}

  .btn-warning {{
    background: #E65100;
    border-color: #F57C00;
  }}

  .badge-key {{
    background: var(--chord-color);
    color: #000000;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 900;
    font-size: 15px;
  }}

  .badge-metro {{
    background: #37474F;
    color: #00E676;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: bold;
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  .metro-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #555555;
    display: inline-block;
  }}

  .metro-dot.flash {{
    background: #00E676 !important;
    box-shadow: 0 0 10px #00E676;
  }}

  /* Song Content View */
  #stage-viewport {{
    flex: 1;
    height: 100%;
    overflow-y: scroll;
    -webkit-overflow-scrolling: touch;
    padding: 20px 24px 220px 24px;
    scroll-behavior: auto;
  }}

  /* Hide Scrollbar */
  #stage-viewport::-webkit-scrollbar {{
    display: none;
  }}
  #stage-viewport {{
    -ms-overflow-style: none;
    scrollbar-width: none;
  }}

  .song-header {{
    margin-bottom: 20px;
    border-bottom: 2px solid #333333;
    padding-bottom: 12px;
  }}

  .song-title {{
    font-size: 32px;
    font-weight: 900;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
  }}

  .song-artist {{
    font-size: 18px;
    color: #888888;
    margin-bottom: 8px;
  }}

  .section-banner {{
    background: var(--badge-bg);
    color: var(--badge-color);
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    font-weight: 800;
    font-size: 14px;
    margin-top: 22px;
    margin-bottom: 10px;
    letter-spacing: 0.5px;
  }}

  .line-pair {{
    font-family: "JetBrains Mono", "Courier New", monospace;
    font-size: 22px;
    line-height: 1.35;
    margin-bottom: 12px;
    white-space: pre-wrap;
    word-break: break-word;
  }}

  .chord-row {{
    color: var(--chord-color);
    font-weight: 900;
    font-size: 24px;
  }}

  .lyric-row {{
    color: var(--text-color);
  }}

  .grid-table {{
    display: flex;
    background: var(--grid-bg);
    border: 1px solid var(--grid-border);
    border-radius: 6px;
    margin: 10px 0;
    overflow: hidden;
  }}

  .grid-measure {{
    flex: 1;
    text-align: center;
    padding: 10px 4px;
    font-family: "JetBrains Mono", monospace;
    font-weight: 900;
    font-size: 22px;
    color: var(--chord-color);
    border-right: 1px solid var(--grid-border);
  }}
  .grid-measure:last-child {{
    border-right: none;
  }}

  .tag-box {{
    background: var(--tag-bg);
    color: var(--tag-color);
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 16px;
    font-style: italic;
    margin: 10px 0;
    display: inline-block;
  }}

  /* Floating Bottom Live Controller */
  #live-controller {{
    position: fixed;
    bottom: 12px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid #334155;
    border-radius: 30px;
    padding: 6px 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.85);
    z-index: 1000;
    max-width: 95vw;
    white-space: nowrap;
  }}

  .ctrl-btn {{
    background: #1E293B;
    color: #F8FAFC;
    border: 1px solid #475569;
    padding: 6px 12px;
    border-radius: 6px;
    font-weight: bold;
    cursor: pointer;
    font-size: 13px;
  }}

  .ctrl-btn:active {{
    background: #334155;
  }}
</style>
</head>
<body>

<!-- TOP HUD -->
<div id="stage-hud">
  <div class="hud-group" style="display:flex; align-items:center; gap:10px;">
    {f'<img src="{logo_b64}" style="height:26px; object-fit:contain;" alt="Logo" />' if logo_b64 else ''}
    <button class="btn" onclick="prevSong()">◀ Prec (1)</button>
    <span id="hud-counter" style="font-weight: bold;">Brano 1 di 1</span>
    <button class="btn" onclick="nextSong()">Succ (2) ▶</button>
  </div>

  <div class="hud-group">
    <span id="hud-key" class="badge-key">KEY: C</span>
    <div class="badge-metro">
      <span id="metro-light" class="metro-dot"></span>
      <span id="hud-bpm">120 BPM</span>
      <button class="btn btn-accent" style="padding: 2px 8px; margin-left: 6px;" onclick="toggleMetronome()">Click</button>
    </div>
  </div>

  <div class="hud-group">
    <button class="btn" onclick="toggleWakeLock()" id="btn-wakelock">☀️ Schermo Attivo</button>
    <button class="btn" onclick="toggleFullscreen()">⛶ Schermo Intero</button>
  </div>
</div>

<!-- SCROLLABLE VIEWPORT -->
<div id="stage-viewport">
  <div id="song-container"></div>
</div>

<!-- FLOATING CONTROLLER -->
<div id="live-controller">
  <button id="btn-scroll" class="btn btn-warning" onclick="toggleScroll()" style="min-width: 125px;">⏳ AVVIO IN {auto_start_delay}s</button>
  <button class="btn" onclick="resetScroll()" title="Torna all'inizio">⏮</button>
  <button class="btn" onclick="updateSpeed(Math.max(10, scrollSpeed - 5))" title="Rallenta">➖</button>
  <span id="speed-label" style="font-size: 13px; font-weight: bold; width: 62px; text-align: center; color: #38BDF8;">{initial_speed} px/s</span>
  <button class="btn" onclick="updateSpeed(Math.min(150, scrollSpeed + 5))" title="Accelera">➕</button>
</div>

<script>
  // Songs Payload from Server
  const songs = {songs_json};
  let currentSongIndex = {initial_index};
  let isScrolling = false;
  let scrollSpeed = {initial_speed}; // px per second
  let currentScrollY = 0;
  let lastFrameTime = null;
  let scrollAnimId = null;
  let wakeLock = null;
  const autoStartEnabled = {'true' if auto_start else 'false'};
  const autoStartDelaySec = {auto_start_delay};
  let countdownTimer = null;

  // Web Audio Metronome Variables
  let audioCtx = null;
  let metronomeActive = false;
  let metroIntervalId = null;
  let currentBeat = 0;

  // Save to LocalStorage for Offline Fallback (SRS Cap. 12.28)
  try {{
    localStorage.setItem("asma_live_songs_cache", JSON.stringify(songs));
    localStorage.setItem("asma_live_cache_timestamp", new Date().toISOString());
  }} catch(e) {{
    console.warn("Storage quota exceeded", e);
  }}

  function renderCurrentSong() {{
    if (!songs || songs.length === 0) return;
    const song = songs[currentSongIndex];

    document.getElementById("hud-counter").innerText = `Brano ${{currentSongIndex + 1}} di ${{songs.length}}`;
    document.getElementById("hud-key").innerText = `KEY: ${{song.key}}`;
    document.getElementById("hud-bpm").innerText = `${{song.bpm}} BPM (${{song.time_signature}})`;

    let html = `<div class="song-header">
      <div class="song-title">${{song.title}}</div>
      <div class="song-artist">${{song.artist}}</div>
      ${{song.shared_notes ? `<div class="tag-box">&#128227; Note Band: ${{song.shared_notes}}</div>` : ''}}
    </div>`;

    song.sections.forEach(sec => {{
      html += `<div class="section-banner">${{sec.name}}</div>`;
      sec.lines.forEach(line => {{
        if (line.type === "grid") {{
          html += `<div class="grid-table">`;
          line.measures.forEach(m => {{
            html += `<div class="grid-measure">${{m.join(" ")}}</div>`;
          }});
          html += `</div>`;
        }} else if (line.type === "chord_lyric") {{
          html += `<div class="line-pair">`;
          const chordStr = line.chords.join(" ").trim();
          if (chordStr.length > 0) {{
            html += `<div class="chord-row">${{line.chords.join("&nbsp;&nbsp;")}}</div>`;
          }}
          html += `<div class="lyric-row">${{line.lyrics.join("")}}</div>`;
          html += `</div>`;
        }} else if (line.type === "tag") {{
          html += `<div class="tag-box">&#9835; [${{line.tag}}]: ${{line.content}}</div>`;
        }}
      }});
    }});

    document.getElementById("song-container").innerHTML = html;
    resetScroll();
    if (autoStartEnabled) {{
      startAutoScrollCountdown();
    }}
    if (metronomeActive) {{
      restartMetronome();
    }}
  }}

  // --- SMOOTH 60FPS SCROLL ENGINE ---
  function scrollStep(timestamp) {{
    if (!isScrolling) return;
    if (lastFrameTime !== null) {{
      const deltaSec = (timestamp - lastFrameTime) / 1000.0;
      const cappedDelta = Math.min(deltaSec, 0.1);
      currentScrollY += (scrollSpeed * cappedDelta);
      const viewport = document.getElementById("stage-viewport");
      if (viewport) {{
        viewport.scrollTop = currentScrollY;
        if (viewport.scrollTop + viewport.clientHeight >= viewport.scrollHeight - 5) {{
          pauseScroll();
          const btn = document.getElementById("btn-scroll");
          if (btn) {{
            btn.innerText = "🏁 FINE BRANO";
            btn.className = "btn btn-warning";
          }}
          return;
        }}
      }}
    }}
    lastFrameTime = timestamp;
    scrollAnimId = requestAnimationFrame(scrollStep);
  }}

  function startScroll() {{
    if (isScrolling) return;
    if (countdownTimer) {{
      clearInterval(countdownTimer);
      countdownTimer = null;
    }}
    isScrolling = true;
    const btn = document.getElementById("btn-scroll");
    if (btn) {{
      btn.innerText = "⏸ PAUSA";
      btn.className = "btn btn-accent";
    }}
    lastFrameTime = performance.now();
    scrollAnimId = requestAnimationFrame(scrollStep);
  }}

  function pauseScroll() {{
    if (!isScrolling) return;
    isScrolling = false;
    const btn = document.getElementById("btn-scroll");
    if (btn) {{
      btn.innerText = "▶ RIPRENDI";
      btn.className = "btn btn-warning";
    }}
    if (scrollAnimId) cancelAnimationFrame(scrollAnimId);
    scrollAnimId = null;
    lastFrameTime = null;
  }}

  function toggleScroll() {{
    if (countdownTimer) {{
      clearInterval(countdownTimer);
      countdownTimer = null;
      startScroll();
      return;
    }}
    if (isScrolling) {{
      pauseScroll();
    }} else {{
      startScroll();
    }}
  }}

  function resetScroll() {{
    if (countdownTimer) {{
      clearInterval(countdownTimer);
      countdownTimer = null;
    }}
    pauseScroll();
    currentScrollY = 0;
    const viewport = document.getElementById("stage-viewport");
    if (viewport) viewport.scrollTop = 0;
    const btn = document.getElementById("btn-scroll");
    if (btn) {{
      btn.innerText = "▶ AVVIA SCROLL";
      btn.className = "btn btn-warning";
    }}
  }}

  function startAutoScrollCountdown() {{
    if (countdownTimer) clearInterval(countdownTimer);
    if (!autoStartEnabled) return;

    let remaining = autoStartDelaySec;
    const btn = document.getElementById("btn-scroll");
    if (btn) {{
      btn.innerText = `⏳ AVVIO IN ${{remaining}}s`;
      btn.className = "btn btn-accent";
    }}

    countdownTimer = setInterval(() => {{
      remaining--;
      if (remaining <= 0) {{
        clearInterval(countdownTimer);
        countdownTimer = null;
        if (!isScrolling) {{
          startScroll();
        }}
      }} else {{
        if (btn) btn.innerText = `⏳ AVVIO IN ${{remaining}}s`;
      }}
    }}, 1000);
  }}

  function updateSpeed(val) {{
    scrollSpeed = Math.max(5, Math.min(150, parseInt(val, 10)));
    const lbl = document.getElementById("speed-label");
    if (lbl) lbl.innerText = `${{scrollSpeed}} px/s`;
  }}

  // --- SETLIST NAVIGATION ---
  function nextSong() {{
    if (currentSongIndex < songs.length - 1) {{
      currentSongIndex++;
      renderCurrentSong();
    }}
  }}

  function prevSong() {{
    if (currentSongIndex > 0) {{
      currentSongIndex--;
      renderCurrentSong();
    }}
  }}

  // --- BLUETOOTH PEDAL LISTENERS (AirTurn, PageFlip, BlueTurn) ---
  window.addEventListener("keydown", (e) => {{
    switch(e.code) {{
      case "PageDown":
      case "ArrowDown":
        // Pedal Down: Next page or start scroll
        if (!isScrolling) toggleScroll();
        else updateSpeed(Math.min(120, scrollSpeed + 5));
        e.preventDefault();
        break;
      case "PageUp":
      case "ArrowUp":
        // Pedal Up: Pause or rewind
        if (isScrolling) toggleScroll();
        else {{
          document.getElementById("stage-viewport").scrollTop -= 150;
        }}
        e.preventDefault();
        break;
      case "Digit1":
        prevSong();
        e.preventDefault();
        break;
      case "Digit2":
        nextSong();
        e.preventDefault();
        break;
      case "Space":
        toggleScroll();
        e.preventDefault();
        break;
    }}
  }});

  // --- SCREEN WAKE LOCK API (Keep Screen Awake) ---
  async function toggleWakeLock() {{
    if ('wakeLock' in navigator) {{
      try {{
        if (!wakeLock) {{
          wakeLock = await navigator.wakeLock.request('screen');
          document.getElementById("btn-wakelock").style.background = "#00E676";
          document.getElementById("btn-wakelock").style.color = "#000000";
        }} else {{
          await wakeLock.release();
          wakeLock = null;
          document.getElementById("btn-wakelock").style.background = "#263238";
          document.getElementById("btn-wakelock").style.color = "#FFFFFF";
        }}
      }} catch(err) {{
        console.warn("WakeLock error", err);
      }}
    }}
  }}

  function toggleFullscreen() {{
    if (!document.fullscreenElement) {{
      document.documentElement.requestFullscreen().catch(err => {{}});
    }} else {{
      document.exitFullscreen().catch(err => {{}});
    }}
  }}

  // --- WEB AUDIO API METRONOME (< 1ms Latency) ---
  function toggleMetronome() {{
    metronomeActive = !metronomeActive;
    if (metronomeActive) {{
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      restartMetronome();
    }} else {{
      if (metroIntervalId) clearInterval(metroIntervalId);
      document.getElementById("metro-light").classList.remove("flash");
    }}
  }}

  function restartMetronome() {{
    if (metroIntervalId) clearInterval(metroIntervalId);
    if (!metronomeActive) return;

    const bpm = songs[currentSongIndex].bpm || 120;
    const intervalMs = (60.0 / bpm) * 1000.0;
    currentBeat = 0;

    metroIntervalId = setInterval(() => {{
      playClick(currentBeat === 0);
      currentBeat = (currentBeat + 1) % 4;
    }}, intervalMs);
  }}

  function playClick(isFirstBeat) {{
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.frequency.value = isFirstBeat ? 1000 : 700; // 1kHz beat 1, 700Hz other beats
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.05);

    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.05);

    // Visual Flash
    const dot = document.getElementById("metro-light");
    dot.classList.add("flash");
    setTimeout(() => dot.classList.remove("flash"), 60);
  }}

  // Initial Boot
  renderCurrentSong();
  toggleWakeLock(); // Auto-engage screen wake lock

  // Tap-to-pause and manual scroll sync
  const _vp = document.getElementById("stage-viewport");
  if (_vp) {{
    _vp.addEventListener("scroll", () => {{
      if (!isScrolling) {{
        currentScrollY = _vp.scrollTop;
      }}
    }}, {{ passive: true }});

    _vp.addEventListener("click", (e) => {{
      if (!e.target.closest("button") && !e.target.closest("input")) {{
        toggleScroll();
      }}
    }});
  }}
</script>
</body>
</html>"""
        return html
