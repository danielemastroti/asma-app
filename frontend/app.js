/**
 * THE New ASMA - Live Band PWA Client Core
 * Pure Vanilla Touch-First SPA (0ms latency, zero popovers, 1-touch actions)
 */

const API_BASE = window.location.origin;

// Application State
const state = {
  currentTab: 'songs',
  repertoires: [],
  activeRepertoire: '__ALL__',
  songs: [],
  selectedSong: null,
  setlists: [],
  selectedSetlist: null,
  scoreMode: 'chords', // 'chords' or 'lyrics'
  currentUser: { email: 'cico@band.org', name: 'Cico', role: 'ADMIN' },
  // Live Stage State
  isStageActive: false,
  isAutoscrolling: false,
  scrollSpeed: 28, // px per second
  scrollIntervalId: null,
  // Stage Setlist tracking
  stageSongs: [],
  stageIndex: 0
};

// ----------------------------------------------------------------------------
// INITIALIZATION
// ----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initServiceWorker();
  initNav();
  initKeyboardAndPedals();
  loadRepertoires();
  loadSongs();
  loadSetlists();
});

function initServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(err => {
      console.log('SW registration note:', err);
    });
  }
}

function initNav() {
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const target = tab.dataset.tab;
      switchTab(target);
    });
  });

  const searchBox = document.getElementById('search-songs');
  if (searchBox) {
    searchBox.addEventListener('input', (e) => {
      renderSongCards(e.target.value.trim().toLowerCase());
    });
  }
}

function switchTab(tabName) {
  state.currentTab = tabName;
  document.getElementById('view-songs').style.display = tabName === 'songs' ? 'block' : 'none';
  document.getElementById('view-setlists').style.display = tabName === 'setlists' ? 'block' : 'none';
  document.getElementById('view-settings').style.display = tabName === 'settings' ? 'block' : 'none';

  if (tabName === 'setlists') {
    renderSetlists();
  }
}

// ----------------------------------------------------------------------------
// TOAST NOTIFICATIONS (No blocking popovers!)
// ----------------------------------------------------------------------------
function showToast(message) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  }, 2600);
}

// ----------------------------------------------------------------------------
// REPERTOIRES & SONGS (0ms Client Filtering)
// ----------------------------------------------------------------------------
async function loadRepertoires() {
  try {
    const res = await fetch(`${API_BASE}/api/repertoires`);
    if (res.ok) {
      state.repertoires = await res.json();
      renderRepertoireChips();
    }
  } catch (err) {
    console.warn('Repertoires offline/cache:', err);
  }
}

function renderRepertoireChips() {
  const container = document.getElementById('repertoire-chips');
  if (!container) return;

  const totalSongs = state.songs.length;
  let html = `<button class="chip ${state.activeRepertoire === '__ALL__' ? 'active' : ''}" onclick="selectRepertoire('__ALL__')">🌐 Tutti i Repertori (${totalSongs})</button>`;

  state.repertoires.forEach(r => {
    const isActive = state.activeRepertoire === r.uuid ? 'active' : '';
    html += `<button class="chip ${isActive}" onclick="selectRepertoire('${r.uuid}')">📁 ${r.name} (${r.song_count})</button>`;
  });

  container.innerHTML = html;
}

function selectRepertoire(repUuid) {
  state.activeRepertoire = repUuid;
  renderRepertoireChips();
  renderSongCards();
  showToast(`Filtro repertorio aggiornato`);
}

async function loadSongs() {
  try {
    const res = await fetch(`${API_BASE}/api/songs`);
    if (res.ok) {
      state.songs = await res.json();
      renderRepertoireChips();
      renderSongCards();
      // Select first song by default if none selected
      if (state.songs.length > 0 && !state.selectedSong) {
        selectSong(state.songs[0].uuid);
      }
    }
  } catch (err) {
    console.warn('Songs offline/cache:', err);
  }
}

function getFilteredSongs(searchKw = '') {
  let list = state.songs;
  if (state.activeRepertoire !== '__ALL__') {
    const rep = state.repertoires.find(r => r.uuid === state.activeRepertoire);
    if (rep && rep.song_uuids) {
      const allowed = new Set(rep.song_uuids);
      list = list.filter(s => allowed.has(s.uuid));
    }
  }
  if (searchKw) {
    list = list.filter(s =>
      s.title.toLowerCase().includes(searchKw) ||
      (s.artist && s.artist.toLowerCase().includes(searchKw)) ||
      (s.author && s.author.toLowerCase().includes(searchKw))
    );
  }
  return list;
}

function renderSongCards(searchKw = '') {
  const container = document.getElementById('song-grid');
  if (!container) return;

  const filtered = getFilteredSongs(searchKw);
  if (filtered.length === 0) {
    container.innerHTML = `<div style="grid-column: 1/-1; padding: 24px; text-align: center; color: #94a3b8;">Nessun brano presente in questa vista.</div>`;
    return;
  }

  container.innerHTML = filtered.map(s => {
    const isSel = state.selectedSong && state.selectedSong.uuid === s.uuid ? 'selected' : '';
    const repsStr = (s.assigned_repertoires || []).join(', ') || 'Archivio';
    return `
      <div class="song-card ${isSel}" onclick="selectSong('${s.uuid}')">
        <div class="song-card-title">${escapeHtml(s.title)}</div>
        <div class="song-card-artist">${escapeHtml(s.artist || 'Band')} &bull; ${s.author || ''}</div>
        <div class="song-card-meta">
          <span class="badge">Key: ${s.key_current || '-'}</span>
          <span class="badge">${s.bpm || 120} BPM</span>
          <span class="badge">📁 ${escapeHtml(repsStr)}</span>
        </div>
      </div>
    `;
  }).join('');
}

async function selectSong(uuid) {
  try {
    const res = await fetch(`${API_BASE}/api/songs/${uuid}`);
    if (res.ok) {
      state.selectedSong = await res.json();
      renderSongCards();
      renderSongViewer();
      // Auto-scroll on mobile to viewer if tapped
      if (window.innerWidth < 768) {
        document.getElementById('song-viewer')?.scrollIntoView({ behavior: 'smooth' });
      }
    }
  } catch (err) {
    console.error('Error fetching song details:', err);
  }
}

// ----------------------------------------------------------------------------
// SONG VIEWER & AML RENDERING (1-Touch Mode Toggle)
// ----------------------------------------------------------------------------
function toggleScoreMode() {
  state.scoreMode = state.scoreMode === 'chords' ? 'lyrics' : 'chords';
  renderSongViewer();
  showToast(`Modalità: ${state.scoreMode === 'chords' ? 'Testo + Accordi' : 'Solo Testo (Cantante)'}`);
}

function transposeSong(semitones) {
  if (!state.selectedSong) return;
  fetch(`${API_BASE}/api/songs/${state.selectedSong.uuid}/transpose`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ semitones: semitones, user_email: state.currentUser.email })
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      state.selectedSong = data.song;
      // Update in songs array
      const idx = state.songs.findIndex(s => s.uuid === state.selectedSong.uuid);
      if (idx !== -1) state.songs[idx] = data.song;
      renderSongCards();
      renderSongViewer();
      showToast(`Tonalità aggiornata a: ${state.selectedSong.key_current}`);
    }
  });
}

function renderSongViewer() {
  const container = document.getElementById('song-viewer');
  if (!container || !state.selectedSong) return;

  const s = state.selectedSong;
  const hasChords = state.scoreMode === 'chords';
  const modeLabel = hasChords ? '🎸 Testo + Accordi' : '🎤 Solo Testo';

  // Format AML into readable lyrics + chord tokens
  const formattedHtml = parseAmlForWeb(s.aml_content, hasChords);

  container.innerHTML = `
    <div class="viewer-header">
      <div>
        <h2 style="font-size: 22px; font-weight: 900; color: #fff;">${escapeHtml(s.title)}</h2>
        <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
          <b>${escapeHtml(s.artist || 'Band')}</b> &bull; Tonalità: <code style="color:#ffd600; font-weight:700;">${s.key_current}</code>
          &bull; Tempo: <code style="color:#00e5ff;">${s.bpm || 120} BPM</code> &bull; Capo: <b>${s.capo || 0}°</b>
        </div>
      </div>
      <div class="viewer-tools">
        <button class="btn btn-secondary" onclick="transposeSong(-1)">♭ -1 Semitono</button>
        <button class="btn btn-secondary" onclick="transposeSong(1)">♯ +1 Semitono</button>
        <button class="btn btn-secondary" onclick="toggleScoreMode()">${modeLabel}</button>
        <button class="btn btn-primary" onclick="startSingleSongStage()">🎤 Avvia Palco</button>
        <button class="btn btn-secondary" onclick="printA4()">🖨️ Stampa A4</button>
        <button class="btn btn-secondary" onclick="downloadPdf()">💾 Salva PDF</button>
      </div>
    </div>
    <div class="lyrics-container" id="printable-lyrics">
      ${formattedHtml}
    </div>
  `;
}

function parseAmlForWeb(aml, showChords) {
  if (!aml) return '<i>Nessun testo inserito.</i>';

  let html = '';
  const lines = aml.split('\n');

  for (let line of lines) {
    line = line.trimEnd();

    // Section header: {verse}, {chorus}, etc.
    if (line.startsWith('{') && line.endsWith('}')) {
      const tag = line.slice(1, -1).toUpperCase();
      html += `<div style="font-weight: 800; color: #0284c7; margin: 16px 0 6px 0; border-bottom: 1px solid #e2e8f0; padding-bottom: 2px;">[${escapeHtml(tag)}]</div>`;
      continue;
    }

    if (!showChords) {
      // Remove chords completely: [DO] -> ""
      const cleanLine = line.replace(/\[[^\]]+\]/g, '');
      if (cleanLine.trim()) {
        html += `<div>${escapeHtml(cleanLine)}</div>`;
      } else {
        html += `<div style="height: 10px;"></div>`;
      }
    } else {
      // Render chord token highlighted
      const lineWithChords = line.replace(/\[([^\]]+)\]/g, '<span class="chord-token">[$1]</span>');
      html += `<div>${lineWithChords || '&nbsp;'}</div>`;
    }
  }

  return html;
}

function downloadPdf() {
  if (!state.selectedSong) return;
  const chordsParam = state.scoreMode === 'chords' ? 'true' : 'false';
  const url = `${API_BASE}/api/songs/${state.selectedSong.uuid}/pdf?chords=${chordsParam}&device=Huawei MediaPad M5`;
  window.open(url, '_blank');
}

function printA4() {
  if (!state.selectedSong) return;
  const chordsParam = state.scoreMode === 'chords' ? 'true' : 'false';
  const url = `${API_BASE}/api/songs/${state.selectedSong.uuid}/pdf?chords=${chordsParam}&device=Foglio A4`;
  const printWindow = window.open(url, '_blank');
  if (printWindow) {
    printWindow.focus();
  }
}

// ----------------------------------------------------------------------------
// LIVE STAGE & TELEPROMPTER (60fps Touch & Bluetooth Pedals)
// ----------------------------------------------------------------------------
function startSingleSongStage() {
  if (!state.selectedSong) return;
  state.stageSongs = [state.selectedSong];
  state.stageIndex = 0;
  openStageModal();
}

function openStageModal() {
  state.isStageActive = true;
  state.isAutoscrolling = false;

  const currentSong = state.stageSongs[state.stageIndex];
  const stageModal = document.getElementById('stage-modal');
  if (!stageModal || !currentSong) return;

  stageModal.style.display = 'flex';
  document.getElementById('stage-song-title').textContent = currentSong.title;
  document.getElementById('stage-song-meta').textContent = `${currentSong.artist} • Key: ${currentSong.key_current} • ${currentSong.bpm || 120} BPM`;

  const container = document.getElementById('stage-lyrics');
  container.innerHTML = parseAmlForWeb(currentSong.aml_content, state.scoreMode === 'chords');
  container.scrollTop = 0;

  // Wake lock API (keep screen awake on mobile)
  if ('wakeLock' in navigator) {
    navigator.wakeLock.request('screen').catch(console.warn);
  }
}

function closeStageModal() {
  stopAutoscroll();
  state.isStageActive = false;
  const stageModal = document.getElementById('stage-modal');
  if (stageModal) stageModal.style.display = 'none';
}

function toggleAutoscroll() {
  if (state.isAutoscrolling) {
    stopAutoscroll();
  } else {
    startAutoscroll();
  }
}

function startAutoscroll() {
  state.isAutoscrolling = true;
  const btn = document.getElementById('btn-stage-toggle');
  if (btn) {
    btn.innerHTML = '⏸️';
    btn.style.backgroundColor = '#ef4444';
  }

  const container = document.getElementById('stage-lyrics');
  if (state.scrollIntervalId) clearInterval(state.scrollIntervalId);

  // 60fps smooth scroll step
  state.scrollIntervalId = setInterval(() => {
    if (container) {
      container.scrollTop += (state.scrollSpeed / 60);
    }
  }, 1000 / 60);
}

function stopAutoscroll() {
  state.isAutoscrolling = false;
  const btn = document.getElementById('btn-stage-toggle');
  if (btn) {
    btn.innerHTML = '▶️';
    btn.style.backgroundColor = '#10b981';
  }
  if (state.scrollIntervalId) {
    clearInterval(state.scrollIntervalId);
    state.scrollIntervalId = null;
  }
}

function stageNextSong() {
  if (state.stageIndex < state.stageSongs.length - 1) {
    state.stageIndex++;
    openStageModal();
    showToast(`Brano ${state.stageIndex + 1} di ${state.stageSongs.length}`);
  }
}

function stagePrevSong() {
  if (state.stageIndex > 0) {
    state.stageIndex--;
    openStageModal();
  }
}

// ----------------------------------------------------------------------------
// BLUETOOTH PEDALS & KEYBOARD LISTENERS
// ----------------------------------------------------------------------------
function initKeyboardAndPedals() {
  window.addEventListener('keydown', (e) => {
    if (!state.isStageActive) return;

    // Pedals / PageDown / Down: Page down or start autoscroll
    if (e.key === 'PageDown' || e.key === 'ArrowDown' || e.key === '3') {
      const container = document.getElementById('stage-lyrics');
      if (container) container.scrollTop += 320;
      e.preventDefault();
    }
    // Pedals / PageUp / Up: Page up
    else if (e.key === 'PageUp' || e.key === 'ArrowUp' || e.key === '1') {
      const container = document.getElementById('stage-lyrics');
      if (container) container.scrollTop -= 320;
      e.preventDefault();
    }
    // Space or Enter: Toggle Autoscroll
    else if (e.key === ' ' || e.key === 'Enter') {
      toggleAutoscroll();
      e.preventDefault();
    }
    // Escape: Close stage mode
    else if (e.key === 'Escape') {
      closeStageModal();
    }
  });

  // Swipe gesture detection on stage screen
  let touchStartY = 0;
  let touchStartX = 0;
  window.addEventListener('touchstart', (e) => {
    if (state.isStageActive && e.touches.length === 1) {
      touchStartY = e.touches[0].clientY;
      touchStartX = e.touches[0].clientX;
    }
  });

  window.addEventListener('touchend', (e) => {
    if (!state.isStageActive || e.changedTouches.length === 0) return;
    const diffX = e.changedTouches[0].clientX - touchStartX;
    const diffY = e.changedTouches[0].clientY - touchStartY;

    // Horizontal swipe: change song in stage setlist
    if (Math.abs(diffX) > 80 && Math.abs(diffY) < 50) {
      if (diffX < 0) {
        stageNextSong();
      } else {
        stagePrevSong();
      }
    }
  });
}

// ----------------------------------------------------------------------------
// SETLISTS
// ----------------------------------------------------------------------------
async function loadSetlists() {
  try {
    const res = await fetch(`${API_BASE}/api/setlists`);
    if (res.ok) {
      state.setlists = await res.json();
    }
  } catch (err) {
    console.warn('Setlists error:', err);
  }
}

function renderSetlists() {
  const container = document.getElementById('setlists-list');
  if (!container) return;

  if (state.setlists.length === 0) {
    container.innerHTML = '<div style="padding: 20px; color:#94a3b8;">Nessuna scaletta presente.</div>';
    return;
  }

  container.innerHTML = state.setlists.map(s => `
    <div class="song-card" style="margin-bottom: 10px;" onclick="loadAndPlaySetlist('${s.uuid}')">
      <div class="song-card-title">📑 ${escapeHtml(s.title)}</div>
      <div class="song-card-artist">${s.date || ''} &bull; ${s.description || 'Scaletta Live'}</div>
      <div class="song-card-meta">
        <span class="badge">${s.item_count} Brani</span>
        <button class="btn btn-primary" style="margin-left:auto; min-height:36px; padding:4px 12px;" onclick="event.stopPropagation(); loadAndPlaySetlist('${s.uuid}')">🎤 Avvia Palco</button>
      </div>
    </div>
  `).join('');
}

async function loadAndPlaySetlist(uuid) {
  try {
    const res = await fetch(`${API_BASE}/api/setlists/${uuid}`);
    if (res.ok) {
      const data = await res.json();
      state.selectedSetlist = data;
      // Fetch full song objects for the setlist
      state.stageSongs = [];
      for (let item of data.items) {
        const sRes = await fetch(`${API_BASE}/api/songs/${item.song_uuid}`);
        if (sRes.ok) {
          const sObj = await sRes.json();
          state.stageSongs.push(sObj);
        }
      }
      if (state.stageSongs.length > 0) {
        state.stageIndex = 0;
        openStageModal();
        showToast(`Scaletta caricata: ${data.title} (${state.stageSongs.length} brani)`);
      }
    }
  } catch (err) {
    console.error('Setlist play error:', err);
  }
}

// ----------------------------------------------------------------------------
// UTILITY
// ----------------------------------------------------------------------------
function escapeHtml(text) {
  if (!text) return '';
  return text.replace(/[&<>"']/g, function(m) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
  });
}
