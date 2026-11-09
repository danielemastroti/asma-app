/**
 * THE New ASMA - Live Band PWA Client Core
 * Pure Vanilla Touch-First SPA (0ms latency, zero popovers, 1-touch actions)
 * Full User & Device Preferences synced to Turso Cloud DB.
 */

const API_BASE = window.location.origin;

const savedScoreMode = (() => {
  try { return localStorage.getItem('asma_score_mode'); } catch (e) { return null; }
})();
const savedUserEmail = (() => {
  try { return localStorage.getItem('asma_user_email'); } catch (e) { return null; }
})();
const savedDevice = (() => {
  try { return localStorage.getItem('asma_active_device'); } catch (e) { return null; }
})();

// Application State
const state = {
  currentTab: 'songs',
  repertoires: [],
  activeRepertoire: '__ALL__',
  songs: [],
  selectedSong: null,
  setlists: [],
  selectedSetlist: null,
  scoreMode: savedScoreMode || 'lyrics', // Default to 'lyrics' for Cico/singer
  currentUser: { email: savedUserEmail || 'acicchelli65@gmail.com', name: 'Cico', role: 'BAND_MEMBER' },
  activeDevice: savedDevice || 'Huawei MediaPad M5',
  usersList: [],
  devicesList: [],
  userPrefs: {
    layout_font_size: 12.0,
    layout_font_size_chords: 13.0,
    layout_columns: 1,
    layout_margin_lateral: 10.0,
    color_lyrics: '#111111',
    color_chords: '#B71C1C',
    color_aml_markup: '#4A148C',
    score_display_mode: savedScoreMode || 'lyrics',
    app_mode: 'simplified'
  },
  // Live Stage State
  isStageActive: false,
  isAutoscrolling: false,
  scrollSpeed: 28, // px per second
  scrollIntervalId: null,
  stageSongs: [],
  stageIndex: 0
};

// ----------------------------------------------------------------------------
// INITIALIZATION
// ----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  initServiceWorker();
  initNav();
  initKeyboardAndPedals();
  await loadUsersAndDevices();
  await loadUserPreferences();
  loadRepertoires();
  loadSongs();
  loadSetlists();
});

function initServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').then(reg => {
      reg.update();
    }).catch(err => {
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
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tabName);
  });
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
  }, 2400);
}

// ----------------------------------------------------------------------------
// USER & HARDWARE PREFERENCES (TURSO CLOUD DB)
// ----------------------------------------------------------------------------
async function loadUsersAndDevices() {
  try {
    const [uRes, dRes] = await Promise.all([
      fetch(`${API_BASE}/api/users`),
      fetch(`${API_BASE}/api/devices`)
    ]);
    if (uRes.ok) {
      const users = await uRes.json();
      state.usersList = users;
      const musSelect = document.getElementById('setting-musician-select');
      if (musSelect && users.length) {
        musSelect.innerHTML = users.map(u => 
          `<option value="${escapeHtml(u.email)}" ${u.email === state.currentUser.email ? 'selected' : ''}>${escapeHtml(u.name)} (${escapeHtml(u.role)})</option>`
        ).join('');
      }
      const matched = users.find(u => u.email === state.currentUser.email);
      if (matched) {
        state.currentUser.name = matched.name;
      } else if (users.length) {
        state.currentUser.email = users[0].email;
        state.currentUser.name = users[0].name;
      }
      const nameSpan = document.getElementById('current-user-name');
      if (nameSpan) nameSpan.textContent = state.currentUser.name;
    }
    if (dRes.ok) {
      const devices = await dRes.json();
      state.devicesList = devices;
      const devSelect = document.getElementById('setting-device-select');
      if (devSelect && devices.length) {
        devSelect.innerHTML = devices.map(d => 
          `<option value="${escapeHtml(d.name)}" ${d.name === state.activeDevice ? 'selected' : ''}>${escapeHtml(d.name)}</option>`
        ).join('');
      }
    }
  } catch (err) {
    console.warn('Could not load users or devices dynamically:', err);
  }
}

async function loadUserPreferences() {
  try {
    const res = await fetch(`${API_BASE}/api/preferences/${encodeURIComponent(state.currentUser.email)}?device=${encodeURIComponent(state.activeDevice)}`);
    if (res.ok) {
      const prefs = await res.json();
      state.userPrefs = Object.assign(state.userPrefs, prefs);
      // Prioritize local setting on device if explicitly chosen
      const localMode = (() => {
        try { return localStorage.getItem('asma_score_mode'); } catch (e) { return null; }
      })();
      state.scoreMode = localMode || state.userPrefs.score_display_mode || 'lyrics';
      applyPreferencesToDom();
      updateSettingsFormValues();
      updateStageScoreModeButton();
    }
  } catch (err) {
    console.warn('Preferences load error:', err);
    applyPreferencesToDom();
    updateStageScoreModeButton();
  }
}

function applyPreferencesToDom() {
  const root = document.documentElement;
  const p = state.userPrefs;

  root.style.setProperty('--pref-lyrics-color', p.color_lyrics || '#111111');
  root.style.setProperty('--pref-chords-color', p.color_chords || '#B71C1C');
  root.style.setProperty('--pref-aml-color', p.color_aml_markup || '#4A148C');
  root.style.setProperty('--pref-lyrics-size', `${p.layout_font_size || 12}px`);
  root.style.setProperty('--pref-chords-size', `${p.layout_font_size_chords || 13}px`);
  root.style.setProperty('--pref-columns', p.layout_columns || 1);
  root.style.setProperty('--pref-lateral-margin', `${p.layout_margin_lateral || 10}px`);

  // Update live preview in settings if visible
  const prevBox = document.getElementById('settings-live-preview');
  if (prevBox) {
    prevBox.style.color = p.color_lyrics;
    prevBox.style.fontSize = `${p.layout_font_size}px`;
    prevBox.style.columnCount = p.layout_columns;
  }
}

function updateSettingsFormValues() {
  const p = state.userPrefs;
  const nameSpan = document.getElementById('current-user-name');
  if (nameSpan) nameSpan.textContent = state.currentUser.name;

  const musSelect = document.getElementById('setting-musician-select');
  if (musSelect) musSelect.value = state.currentUser.email;

  const devSelect = document.getElementById('setting-device-select');
  if (devSelect) devSelect.value = state.activeDevice;

  // Buttons state
  const btnChords = document.getElementById('btn-score-chords');
  const btnLyrics = document.getElementById('btn-score-lyrics');
  if (btnChords && btnLyrics) {
    btnChords.classList.toggle('active', state.scoreMode === 'chords');
    btnLyrics.classList.toggle('active', state.scoreMode === 'lyrics');
  }

  const btnCol1 = document.getElementById('btn-col-1');
  const btnCol2 = document.getElementById('btn-col-2');
  if (btnCol1 && btnCol2) {
    btnCol1.classList.toggle('active', p.layout_columns === 1);
    btnCol2.classList.toggle('active', p.layout_columns === 2);
  }

  // Steppers text
  const valLyrics = document.getElementById('val-font-lyrics');
  if (valLyrics) valLyrics.textContent = p.layout_font_size;
  const valChords = document.getElementById('val-font-chords');
  if (valChords) valChords.textContent = p.layout_font_size_chords;
  const valMargin = document.getElementById('val-margin-lat');
  if (valMargin) valMargin.textContent = p.layout_margin_lateral;

  // Color inputs
  const cLyrics = document.getElementById('pick-color-lyrics');
  if (cLyrics) cLyrics.value = p.color_lyrics;
  const cChords = document.getElementById('pick-color-chords');
  if (cChords) cChords.value = p.color_chords;
  const cAml = document.getElementById('pick-color-aml');
  if (cAml) cAml.value = p.color_aml_markup;

  const tLyrics = document.getElementById('val-color-lyrics');
  if (tLyrics) tLyrics.textContent = p.color_lyrics;
  const tChords = document.getElementById('val-color-chords');
  if (tChords) tChords.textContent = p.color_chords;
  const tAml = document.getElementById('val-color-aml');
  if (tAml) tAml.textContent = p.color_aml_markup;
}

async function autosaveUserPreferences() {
  applyPreferencesToDom();
  updateSettingsFormValues();

  try {
    const payload = Object.assign({}, state.userPrefs, {
      device_name: state.activeDevice,
      score_display_mode: state.scoreMode
    });
    const res = await fetch(`${API_BASE}/api/preferences/${encodeURIComponent(state.currentUser.email)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast(`Preferenze salvate nel cloud Turso ✓`);
    }
  } catch (err) {
    console.warn('Autosave offline:', err);
  }
}

function onMusicianChange(email) {
  state.currentUser.email = email;
  try { localStorage.setItem('asma_user_email', email); } catch (e) {}
  const user = (state.usersList || []).find(u => u.email === email);
  state.currentUser.name = user ? user.name : (email.split('@')[0]);
  const nameSpan = document.getElementById('current-user-name');
  if (nameSpan) nameSpan.textContent = state.currentUser.name;
  loadUserPreferences();
  showToast(`Profilo attivo: ${state.currentUser.name}`);
}

function onDeviceChange(deviceName) {
  state.activeDevice = deviceName;
  try { localStorage.setItem('asma_active_device', deviceName); } catch (e) {}
  loadUserPreferences();
  showToast(`Hardware selezionato: ${deviceName}`);
}

function setPrefScoreMode(mode) {
  state.scoreMode = mode;
  state.userPrefs.score_display_mode = mode;
  try { localStorage.setItem('asma_score_mode', mode); } catch (e) {}
  updateStageScoreModeButton();
  autosaveUserPreferences();
  if (state.selectedSong) renderSongViewer();
}

function setPrefColumns(cols) {
  state.userPrefs.layout_columns = cols;
  applyPreferencesToDom();
  autosaveUserPreferences();
  if (state.selectedSong) renderSongViewer();
}

function toggleColumns() {
  const newCols = (state.userPrefs.layout_columns === 2) ? 1 : 2;
  setPrefColumns(newCols);
  showToast(`Layout: ${newCols} ${newCols === 1 ? 'Colonna' : 'Colonne'}`);
}

function adjustFontSize(type, delta) {
  if (type === 'lyrics') {
    state.userPrefs.layout_font_size = Math.max(8, Math.min(26, (state.userPrefs.layout_font_size || 12) + delta));
  } else {
    state.userPrefs.layout_font_size_chords = Math.max(8, Math.min(28, (state.userPrefs.layout_font_size_chords || 13) + delta));
  }
  autosaveUserPreferences();
  if (state.selectedSong) renderSongViewer();
}

function adjustMargin(delta) {
  state.userPrefs.layout_margin_lateral = Math.max(4, Math.min(30, (state.userPrefs.layout_margin_lateral || 10) + delta));
  autosaveUserPreferences();
  if (state.selectedSong) renderSongViewer();
}

function onColorChange(type, hexColor) {
  if (type === 'lyrics') state.userPrefs.color_lyrics = hexColor;
  else if (type === 'chords') state.userPrefs.color_chords = hexColor;
  else if (type === 'aml') state.userPrefs.color_aml_markup = hexColor;
  autosaveUserPreferences();
  if (state.selectedSong) renderSongViewer();
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
    console.warn('Repertoires offline:', err);
  }
}

function renderRepertoireChips() {
  const container = document.getElementById('repertoire-chips');
  if (!container) return;

  const totalSongs = state.songs.length;
  let html = `<button class="chip ${state.activeRepertoire === '__ALL__' ? 'active' : ''}" onclick="selectRepertoire('__ALL__')">🌐 Tutti i Repertori (${totalSongs})</button>`;

  state.repertoires.forEach(r => {
    const isActive = state.activeRepertoire === r.uuid ? 'active' : '';
    html += `<button class="chip ${isActive}" onclick="selectRepertoire('${r.uuid}')">📁 ${escapeHtml(r.name)} (${r.song_count})</button>`;
  });

  container.innerHTML = html;
}

function selectRepertoire(repUuid) {
  state.activeRepertoire = repUuid;
  renderRepertoireChips();
  renderSongCards();
}

async function loadSongs() {
  try {
    const res = await fetch(`${API_BASE}/api/songs`);
    if (res.ok) {
      state.songs = await res.json();
      renderRepertoireChips();
      renderSongCards();
      if (state.songs.length > 0 && !state.selectedSong) {
        selectSong(state.songs[0].uuid);
      }
    }
  } catch (err) {
    console.warn('Songs offline:', err);
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
        <div class="song-card-artist">${escapeHtml(s.artist || 'Band')} &bull; ${escapeHtml(s.author || '')}</div>
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
      if (window.innerWidth < 768) {
        document.getElementById('song-viewer')?.scrollIntoView({ behavior: 'smooth' });
      }
    }
  } catch (err) {
    console.error('Error fetching song details:', err);
  }
}

// ----------------------------------------------------------------------------
// ZERO-LATENCY CLIENT-SIDE CHORD TRANSPOSITION
// ----------------------------------------------------------------------------
const ITA_SCALE = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"];
const INT_SCALE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const FLAT_MAP = {
  "DB": "C#", "EB": "D#", "GB": "F#", "AB": "G#", "BB": "A#",
  "REB": "DO#", "MIB": "RE#", "SOLB": "FA#", "LAB": "SOL#", "SIB": "LA#"
};

function transposeSingleChord(chordStr, semitones) {
  if (!chordStr || semitones === 0) return chordStr;
  let s = chordStr.trim();

  // Root note regex matching ITA or INT
  const m = s.match(/^(DO#|RE#|FA#|SOL#|LA#|REB|MIB|SOLB|LAB|SIB|DO|RE|MI|FA|SOL|LA|SI|C#|D#|F#|G#|A#|DB|EB|GB|AB|BB|[CDEFGAB])(.*)$/i);
  if (!m) return chordStr;

  let root = m[1].toUpperCase();
  const rest = m[2];

  if (FLAT_MAP[root]) root = FLAT_MAP[root];

  let scale = INT_SCALE;
  let idx = scale.indexOf(root);
  if (idx === -1) {
    scale = ITA_SCALE;
    idx = scale.indexOf(root);
  }
  if (idx === -1) return chordStr;

  const newIdx = (idx + semitones + 120) % 12;
  const newRoot = scale[newIdx];

  // Also handle bass chord if slash: e.g. DO/MI
  if (rest.includes('/')) {
    const parts = rest.split('/');
    const mainSuffix = parts[0];
    const bass = transposeSingleChord(parts[1], semitones);
    return `${newRoot}${mainSuffix}/${bass}`;
  }

  return `${newRoot}${rest}`;
}

function transposeAmlText(aml, semitones) {
  if (!aml || semitones === 0) return aml;
  return aml.replace(/\[([^\]]+)\]/g, (match, chord) => {
    return `[${transposeSingleChord(chord, semitones)}]`;
  });
}

function transposeSong(semitones) {
  if (!state.selectedSong) return;

  // 1. Instant Client-Side Transposition (0ms!)
  state.selectedSong.aml_content = transposeAmlText(state.selectedSong.aml_content, semitones);
  state.selectedSong.key_current = transposeSingleChord(state.selectedSong.key_current, semitones);

  // Update memory list
  const idx = state.songs.findIndex(s => s.uuid === state.selectedSong.uuid);
  if (idx !== -1) {
    state.songs[idx].key_current = state.selectedSong.key_current;
  }

  renderSongCards();
  renderSongViewer();
  showToast(`Tonalità: ${state.selectedSong.key_current} (${semitones > 0 ? '+' : ''}${semitones})`);

  // 2. Background Cloud Persistence (Turso)
  fetch(`${API_BASE}/api/songs/${state.selectedSong.uuid}/transpose`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ semitones: semitones, user_email: state.currentUser.email })
  }).catch(console.warn);
}

// ----------------------------------------------------------------------------
// SONG VIEWER & AML RENDERING (1-Touch Mode Toggle)
// ----------------------------------------------------------------------------
function toggleScoreMode() {
  state.scoreMode = state.scoreMode === 'chords' ? 'lyrics' : 'chords';
  state.userPrefs.score_display_mode = state.scoreMode;
  try { localStorage.setItem('asma_score_mode', state.scoreMode); } catch (e) {}
  renderSongViewer();
  updateStageScoreModeButton();
  updateSettingsFormValues();
  showToast(`Modalità: ${state.scoreMode === 'chords' ? '🎸 Testo + Accordi' : '🎤 Solo Testo (Cantante)'}`);
  autosaveUserPreferences();
}

function renderSongViewer() {
  const container = document.getElementById('song-viewer');
  if (!container || !state.selectedSong) return;

  const s = state.selectedSong;

  // IN-PLACE TOUCH AML EDITOR MODE
  if (state.isEditingSong) {
    container.innerHTML = `
      <div class="viewer-header">
        <div>
          <h2 style="font-size: 20px; font-weight: 900; color: #38bdf8;">✏️ Modifica Brano: ${escapeHtml(s.title)}</h2>
          <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Modifica testo, accordi o dati musicali</div>
        </div>
        <div class="viewer-tools">
          <button class="btn btn-success" style="font-weight: 800; min-height: 38px; padding: 4px 14px;" onclick="saveSongEdit()">💾 Salva Modifiche</button>
          <button class="btn btn-secondary" style="min-height: 38px; padding: 4px 12px;" onclick="closeSongEditor()">✕ Annulla</button>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; margin: 12px 0;">
        <div>
          <label style="font-size: 11px; color: #94a3b8; font-weight: 700;">Titolo</label>
          <input type="text" id="edit-song-title" class="search-input" style="width: 100%; margin-top: 2px;" value="${escapeHtml(s.title)}">
        </div>
        <div>
          <label style="font-size: 11px; color: #94a3b8; font-weight: 700;">Artista</label>
          <input type="text" id="edit-song-artist" class="search-input" style="width: 100%; margin-top: 2px;" value="${escapeHtml(s.artist || '')}">
        </div>
        <div>
          <label style="font-size: 11px; color: #94a3b8; font-weight: 700;">Tonalità</label>
          <input type="text" id="edit-song-key" class="search-input" style="width: 100%; margin-top: 2px;" value="${escapeHtml(s.key_current || 'C')}">
        </div>
        <div>
          <label style="font-size: 11px; color: #94a3b8; font-weight: 700;">BPM</label>
          <input type="number" id="edit-song-bpm" class="search-input" style="width: 100%; margin-top: 2px;" value="${s.bpm || 120}">
        </div>
        <div>
          <label style="font-size: 11px; color: #94a3b8; font-weight: 700;">Capo</label>
          <input type="number" id="edit-song-capo" class="search-input" style="width: 100%; margin-top: 2px;" value="${s.capo || 0}">
        </div>
      </div>

      <div style="margin-bottom: 6px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
          <label style="font-size: 12px; color: #94a3b8; font-weight: 700;">Testo AML (tocca i tasti rapidi per inserire accordi nel testo):</label>
        </div>
        <div class="quick-chips-bar">
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[DO]')">[DO]</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[RE]')">[RE]</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[MI]')">[MI]</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[FA]')">[FA]</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[SOL]')">[SOL]</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[LA]')">[LA]</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[SI]')">[SI]</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[m]')">[m]</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[7]')">[7]</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '|')">|</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '\\n[INTRO]\\n')">[INTRO]</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '\\n[RITORNELLO]\\n')">[RIT]</button>
          <button class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '\\n♪ (Strumentale)\\n')">♪ Inst</button>
        </div>
        <textarea id="edit-song-aml" class="touch-textarea" style="min-height: 340px;">${escapeHtml(s.aml_content || '')}</textarea>
      </div>

      <div style="display: flex; gap: 10px; margin-top: 14px;">
        <button class="btn btn-success" style="font-weight: 800; min-height: 42px; padding: 6px 18px;" onclick="saveSongEdit()">💾 Salva Modifiche</button>
        <button class="btn btn-secondary" style="min-height: 42px; padding: 6px 14px;" onclick="closeSongEditor()">✕ Annulla</button>
      </div>
    `;
    return;
  }

  const hasChords = state.scoreMode === 'chords';
  const modeLabel = hasChords ? '🎸 Accordi: ON' : '🎤 Solo Testo';
  const colsLabel = state.userPrefs.layout_columns === 2 ? '2 Colonne' : '1 Colonna';

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
        <button class="btn btn-secondary" onclick="transposeSong(-1)" title="Abbassa di 1 semitono">♭ -1</button>
        <button class="btn btn-secondary" onclick="transposeSong(1)" title="Alza di 1 semitono">♯ +1</button>
        <button class="btn btn-secondary" onclick="adjustFontSize('lyrics', -1)" title="Riduci dimensione caratteri">A−</button>
        <button class="btn btn-secondary" onclick="adjustFontSize('lyrics', 1)" title="Ingrandisci dimensione caratteri">A+</button>
        <button class="btn btn-secondary" onclick="toggleScoreMode()">${modeLabel}</button>
        <button class="btn btn-secondary" onclick="toggleColumns()">${colsLabel}</button>
        <button class="btn btn-primary" onclick="startSingleSongStage()">🎤 Palco</button>
        <button class="btn btn-secondary" onclick="openSongEditor()" title="Modifica testo o accordi">✏️ Modifica</button>
        <button class="btn btn-secondary" onclick="printA4()">🖨️ Stampa A4</button>
        <button class="btn btn-secondary" onclick="downloadPdf()">💾 Salva PDF</button>
      </div>
    </div>
    <div class="lyrics-container" id="printable-lyrics">
      ${formattedHtml}
    </div>
  `;
}

// ----------------------------------------------------------------------------
// TOUCH EDITOR & SONG IMPORT ENGINE (1-Touch Actions)
// ----------------------------------------------------------------------------
function openSongEditor() {
  state.isEditingSong = true;
  renderSongViewer();
}

function closeSongEditor() {
  state.isEditingSong = false;
  renderSongViewer();
}

async function saveSongEdit() {
  if (!state.selectedSong) return;
  const titleInput = document.getElementById('edit-song-title');
  const artistInput = document.getElementById('edit-song-artist');
  const keyInput = document.getElementById('edit-song-key');
  const bpmInput = document.getElementById('edit-song-bpm');
  const capoInput = document.getElementById('edit-song-capo');
  const amlInput = document.getElementById('edit-song-aml');

  const payload = {
    title: titleInput ? titleInput.value.trim() : state.selectedSong.title,
    artist: artistInput ? artistInput.value.trim() : state.selectedSong.artist,
    key_current: keyInput ? keyInput.value.trim() : state.selectedSong.key_current,
    bpm: bpmInput ? (parseInt(bpmInput.value) || 120) : state.selectedSong.bpm,
    capo: capoInput ? (parseInt(capoInput.value) || 0) : state.selectedSong.capo,
    aml_content: amlInput ? amlInput.value : state.selectedSong.aml_content,
    user_email: state.currentUser.email,
    user_name: state.currentUser.name,
    comment: 'Modifica touch da tablet'
  };

  try {
    const res = await fetch(`${API_BASE}/api/songs/${state.selectedSong.uuid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json();
      state.selectedSong = data.song;
      const idx = state.songs.findIndex(x => x.uuid === state.selectedSong.uuid);
      if (idx !== -1) {
        state.songs[idx] = Object.assign(state.songs[idx], state.selectedSong);
      }
      state.isEditingSong = false;
      renderSongGrid();
      renderSongViewer();
      showToast(`Brano "${state.selectedSong.title}" salvato con successo ✓`);
    } else {
      showToast('Errore durante il salvataggio del brano');
    }
  } catch (err) {
    console.error('Song edit error:', err);
    showToast('Errore di connessione');
  }
}

function insertChordAtCursor(textareaId, textToInsert) {
  const textarea = document.getElementById(textareaId);
  if (!textarea) return;

  const start = textarea.selectionStart || 0;
  const end = textarea.selectionEnd || 0;
  const val = textarea.value;

  textarea.value = val.substring(0, start) + textToInsert + val.substring(end);
  textarea.selectionStart = textarea.selectionEnd = start + textToInsert.length;
  textarea.focus();
}

function showNewSongForm() {
  const form = document.getElementById('new-song-form');
  if (form) {
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function hideNewSongForm() {
  const form = document.getElementById('new-song-form');
  if (form) form.style.display = 'none';
}

function switchImportTab(tab) {
  const btnPaste = document.getElementById('btn-import-tab-paste');
  const btnUrl = document.getElementById('btn-import-tab-url');
  const btnManual = document.getElementById('btn-import-tab-manual');

  if (btnPaste) btnPaste.classList.toggle('active', tab === 'paste');
  if (btnUrl) btnUrl.classList.toggle('active', tab === 'url');
  if (btnManual) btnManual.classList.toggle('active', tab === 'manual');

  const panePaste = document.getElementById('import-pane-paste');
  const paneUrl = document.getElementById('import-pane-url');

  if (panePaste) panePaste.style.display = tab === 'paste' ? 'block' : 'none';
  if (paneUrl) paneUrl.style.display = tab === 'url' ? 'block' : 'none';
}

async function convertPastedText() {
  const rawInput = document.getElementById('import-paste-text');
  const text = rawInput ? rawInput.value.trim() : '';
  if (!text) {
    showToast('Incolla prima il testo con gli accordi');
    return;
  }

  showToast('Conversione in AML in corso...');
  try {
    const res = await fetch(`${API_BASE}/api/songs/convert-text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_text: text })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.title && data.title !== 'Nuovo Brano') {
        const tField = document.getElementById('new-song-title');
        if (tField && !tField.value) tField.value = data.title;
      }
      if (data.artist && data.artist !== 'Band') {
        const aField = document.getElementById('new-song-artist');
        if (aField && !aField.value) aField.value = data.artist;
      }
      if (data.key) {
        const kField = document.getElementById('new-song-key');
        if (kField) kField.value = data.key;
      }
      const amlField = document.getElementById('new-song-aml');
      if (amlField) amlField.value = data.aml;

      showToast('Testo convertito con successo in AML ✓');
    }
  } catch (err) {
    console.error('Convert text error:', err);
    showToast('Errore durante la conversione');
  }
}

async function fetchSongFromUrl() {
  const urlInput = document.getElementById('import-url-input');
  const url = urlInput ? urlInput.value.trim() : '';
  if (!url || !url.startsWith('http')) {
    showToast('Inserisci un URL valido');
    return;
  }

  showToast('Scaricamento accordi dal web...');
  try {
    const res = await fetch(`${API_BASE}/api/songs/import-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url })
    });
    if (res.ok) {
      const data = await res.json();
      const tField = document.getElementById('new-song-title');
      if (tField) tField.value = data.title;
      const aField = document.getElementById('new-song-artist');
      if (aField) aField.value = data.artist;
      const kField = document.getElementById('new-song-key');
      if (kField) kField.value = data.key;
      const bpmField = document.getElementById('new-song-bpm');
      if (bpmField) bpmField.value = data.bpm || 120;
      const amlField = document.getElementById('new-song-aml');
      if (amlField) amlField.value = data.aml;

      showToast(`Brano "${data.title}" estratto dal web ✓`);
    } else {
      const err = await res.json();
      showToast(err.detail || 'Impossibile estrarre accordi da questo link');
    }
  } catch (err) {
    console.error('URL import error:', err);
    showToast('Errore connessione importazione web');
  }
}

async function submitNewSong() {
  const tField = document.getElementById('new-song-title');
  const title = tField ? tField.value.trim() : '';
  if (!title) {
    showToast('Inserisci almeno il titolo del brano');
    if (tField) tField.focus();
    return;
  }

  const artist = (document.getElementById('new-song-artist')?.value || 'Band').trim();
  const key = (document.getElementById('new-song-key')?.value || 'C').trim();
  const bpm = parseInt(document.getElementById('new-song-bpm')?.value) || 120;
  const capo = parseInt(document.getElementById('new-song-capo')?.value) || 0;
  const aml = document.getElementById('new-song-aml')?.value || '';

  const payload = {
    title: title.toUpperCase(),
    artist: artist,
    key_current: key,
    bpm: bpm,
    capo: capo,
    aml_content: aml,
    repertoire_uuid: state.activeRepertoire !== '__ALL__' ? state.activeRepertoire : null,
    user_email: state.currentUser.email,
    user_name: state.currentUser.name
  };

  try {
    const res = await fetch(`${API_BASE}/api/songs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json();
      showToast(`Brano "${title}" creato con successo ✓`);
      hideNewSongForm();
      // Reload repertoire and select created song
      await loadSongs();
      const created = state.songs.find(s => s.uuid === data.song.uuid);
      if (created) {
        selectSong(created);
      }
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore creazione brano');
    }
  } catch (err) {
    console.error('Create song error:', err);
    showToast('Errore creazione brano');
  }
}

// Musical chords recognition for Web viewer & Stage Prompter
const ROOT_NOTES_REGEX = /^(SOL|DO|RE|MI|FA|LA|SI|[A-G])(#|b|♯|♭)?/i;
const CHORD_SUFFIX_REGEX = /^(m|min|minor|-|maj|major|M|\+|7\+|aug|dim|dim7|°|o|sus|sus2|sus4|2|4|5|6|7|8|9|11|13|add9|add2|m7|maj7|m9|m11|m13|m7b5|7b5|7#5|7b9|7#9|7sus4|6\/9|7\/4|7\/9|\/[0-9]|\/[A-G]|\/(?:SOL|DO|RE|MI|FA|LA|SI)(?:#|b)?)*$/i;
const ITALIAN_COMMON_WORDS = new Set([
  'da', 'di', 'ha', 'ho', 'ma', 'se', 'un', 'il', 'lo', 'la', 'i', 'gli', 'le',
  'a', 'e', 'o', 'fa', 'si', 'su', 'in', 'con', 'per', 'tra', 'fra', 'che', 'non',
  'ci', 'vi', 'ti', 'mi', 'me', 'te', 'lui', 'lei', 'noi', 'voi', 'loro', 'ed', 'od',
  'ad', 'del', 'della', 'dei', 'delle', 'al', 'alla', 'ai', 'alle', 'dal', 'dalla',
  'dai', 'dalle', 'nel', 'nella', 'nei', 'nelle', 'sul', 'sulla', 'sui', 'sulle',
  'piu', 'più', 'gia', 'già', 'poi', 'qui', 'qua', 'va', 'vai', 'sto', 'sta'
]);

function isMusicalChord(token) {
  if (!token) return false;
  const clean = token.trim().replace(/[(),]/g, '');
  if (!clean) return false;
  if (['/', '%', '-', '--', '|', 'NC', 'N.C.'].includes(clean)) return true;
  if (clean.length <= 2 && ITALIAN_COMMON_WORDS.has(clean.toLowerCase()) && clean === clean.toLowerCase()) return false;
  const match = clean.match(ROOT_NOTES_REGEX);
  if (!match) return false;
  const rest = clean.slice(match[0].length);
  return CHORD_SUFFIX_REGEX.test(rest);
}

function isChordGridOrTabLine(trimmedLine) {
  if (!trimmedLine) return false;
  // Guitar tab lines (e.g. e|---0---| or lines with many dashes)
  if (/^[eEaAdDgGbB]\|/.test(trimmedLine)) return true;
  if (trimmedLine.startsWith('|') && trimmedLine.endsWith('|') && (trimmedLine.match(/-/g) || []).length >= 4) return true;
  if ((trimmedLine.match(/-/g) || []).length >= 8 && !/[a-zA-Z]{4,}/.test(trimmedLine)) return true;

  // Chord grid lines with measures (e.g. | SOL | DO | MIm | RE |)
  if (trimmedLine.includes('|')) {
    const rawTokens = trimmedLine.split('|').map(x => x.trim()).filter(Boolean);
    const tokens = rawTokens.flatMap(x => x.split(/\s+/)).filter(Boolean);
    if (tokens.length > 0) {
      const chordCount = tokens.filter(isMusicalChord).length;
      if ((chordCount / tokens.length) >= 0.5) return true;
    }
  }

  // Pure chords lines without brackets or pipes (e.g. SOL DO MIm RE)
  if (!trimmedLine.includes('[') && !trimmedLine.includes(']')) {
    const words = trimmedLine.split(/\s+/).filter(Boolean);
    if (words.length >= 2 && words.length <= 16) {
      const chordCount = words.filter(isMusicalChord).length;
      if ((chordCount / words.length) >= 0.75) return true;
    }
  }

  return false;
}

function parseAmlForWeb(aml, showChords) {
  if (!aml) return '<i>Nessun testo inserito.</i>';

  let html = '';
  const lines = aml.split('\n');
  let inSection = false;
  let lastWasInstrumental = false;

  for (let rawLine of lines) {
    const line = rawLine.trimEnd();
    const trimmed = line.trim();

    if (!trimmed) {
      continue;
    }

    // 1. Detect Section Header ([INTRO], {verse}, Intro:, etc.)
    let sectionTitle = null;
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
      sectionTitle = trimmed.slice(1, -1).replace(/^[c|comment]:\s*/i, '').toUpperCase();
    } else if (trimmed.startsWith('[') && trimmed.endsWith(']') && !trimmed.slice(1, -1).includes(' ')) {
      const candidate = trimmed.slice(1, -1).toUpperCase();
      const standardSections = ['INTRO', 'STROFA', 'VERSE', 'RITORNELLO', 'CHORUS', 'BRIDGE', 'SPECIAL', 'OUTRO', 'FINALE', 'STRUMENTALE', 'SOLO', 'CODA', 'STACCO'];
      if (standardSections.some(s => candidate.includes(s))) {
        sectionTitle = candidate;
      }
    } else if (trimmed.endsWith(':') && trimmed.length < 35 && !trimmed.includes('[')) {
      sectionTitle = trimmed.slice(0, -1).toUpperCase();
    }

    if (sectionTitle) {
      if (inSection) html += '</div>';
      html += `<div class="aml-section"><div class="aml-tag-header">[${escapeHtml(sectionTitle)}]</div>`;
      inSection = true;
      // If the section title itself is instrumental/solo, avoid duplicate ♪ (Strumentale) marker
      lastWasInstrumental = sectionTitle.includes('STRUMENTALE') || sectionTitle.includes('SOLO');
      continue;
    }

    if (!inSection) {
      html += '<div class="aml-section">';
      inSection = true;
    }

    // 2. Chord Grids, Guitar Tabs, or Pure Unbracketed Chords
    if (isChordGridOrTabLine(trimmed)) {
      if (!showChords) {
        if (!lastWasInstrumental) {
          html += `<div class="aml-instrumental">♪ (Strumentale)</div>`;
          lastWasInstrumental = true;
        }
      } else {
        html += `<div class="aml-chord-line aml-grid-line"><span class="chord-token">${escapeHtml(trimmed)}</span></div>`;
        lastWasInstrumental = false;
      }
      continue;
    }

    // 3. Render Line (interleaved chords and lyrics)
    const lyricsOnly = line.replace(/\[[^\]]+\]/g, '').trim();
    const hasChordTokens = /\[[^\]]+\]/.test(line);

    if (!showChords) {
      if (hasChordTokens && !lyricsOnly) {
        // Pure chords line without lyrics -> Instrumental line for singer
        if (!lastWasInstrumental) {
          html += `<div class="aml-instrumental">♪ (Strumentale)</div>`;
          lastWasInstrumental = true;
        }
      } else if (lyricsOnly) {
        html += `<div class="aml-lyric-line">${escapeHtml(line.replace(/\[[^\]]+\]/g, ''))}</div>`;
        lastWasInstrumental = false;
      }
    } else {
      const lineWithChords = line.replace(/\[([^\]]+)\]/g, '<span class="chord-token">[$1]</span>');
      html += `<div class="aml-chord-line">${lineWithChords || '&nbsp;'}</div>`;
      lastWasInstrumental = false;
    }
  }

  if (inSection) html += '</div>';
  return html;
}

function downloadPdf() {
  if (!state.selectedSong) return;
  const chordsParam = state.scoreMode === 'chords' ? 'true' : 'false';
  const url = `${API_BASE}/api/songs/${state.selectedSong.uuid}/pdf?chords=${chordsParam}&device=${encodeURIComponent(state.activeDevice)}&email=${encodeURIComponent(state.currentUser.email)}`;
  window.open(url, '_blank');
}

function printA4() {
  if (!state.selectedSong) return;
  const chordsParam = state.scoreMode === 'chords' ? 'true' : 'false';
  const url = `${API_BASE}/api/songs/${state.selectedSong.uuid}/pdf?chords=${chordsParam}&device=Foglio%20A4&email=${encodeURIComponent(state.currentUser.email)}`;
  const printWindow = window.open(url, '_blank');
  if (printWindow) printWindow.focus();
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
  document.getElementById('stage-song-meta').textContent = `${currentSong.artist} • Key: ${currentSong.key_current} • ${currentSong.bpm || 120} BPM • Capo: ${currentSong.capo || 0}°`;

  const container = document.getElementById('stage-lyrics');
  container.innerHTML = parseAmlForWeb(currentSong.aml_content, state.scoreMode === 'chords');
  container.scrollTop = 0;
  scrollAccumulator = 0;

  // Sync scrollAccumulator whenever user manually scrolls or touches lyrics
  container.onscroll = () => {
    if (!state.isAutoscrolling) {
      scrollAccumulator = container.scrollTop;
    }
  };

  const speedDisp = document.getElementById('stage-speed-display');
  if (speedDisp) speedDisp.textContent = `${Math.round(state.scrollSpeed)} px/s`;

  if (isMetronomeActive) {
    startMetronomePulse(currentSong.bpm || 120);
  }

  updateStageScoreModeButton();

  if ('wakeLock' in navigator) {
    navigator.wakeLock.request('screen').catch(console.warn);
  }
}

function toggleStageScoreMode() {
  state.scoreMode = state.scoreMode === 'chords' ? 'lyrics' : 'chords';
  state.userPrefs.score_display_mode = state.scoreMode;
  try { localStorage.setItem('asma_score_mode', state.scoreMode); } catch (e) {}
  updateStageScoreModeButton();
  updateSettingsFormValues();

  // Re-render current stage song preserving exact scroll position
  const currentSong = state.stageSongs[state.stageIndex];
  if (currentSong) {
    const container = document.getElementById('stage-lyrics');
    if (container) {
      const prevScroll = container.scrollTop;
      container.innerHTML = parseAmlForWeb(currentSong.aml_content, state.scoreMode === 'chords');
      container.scrollTop = prevScroll;
      scrollAccumulator = prevScroll;
    }
  }
  showToast(`Modalità: ${state.scoreMode === 'chords' ? '🎸 Testo + Accordi' : '🎤 Solo Testo (Cantante)'}`);
  autosaveUserPreferences();
}

function updateStageScoreModeButton() {
  const btn = document.getElementById('stage-mode-btn');
  if (btn) {
    if (state.scoreMode === 'chords') {
      btn.textContent = '🎸 Accordi: ON';
      btn.style.color = '#ffd600';
      btn.style.borderColor = '#ffd600';
    } else {
      btn.textContent = '🎤 Solo Testo';
      btn.style.color = '#38bdf8';
      btn.style.borderColor = '#38bdf8';
    }
  }
}

let scrollAccumulator = 0;
let lastScrollTime = 0;
let metronomeTimer = null;
let isMetronomeActive = false;

function toggleMetronome() {
  isMetronomeActive = !isMetronomeActive;
  const dot = document.getElementById('stage-metronome-dot');
  if (!isMetronomeActive) {
    if (metronomeTimer) clearInterval(metronomeTimer);
    metronomeTimer = null;
    if (dot) dot.classList.remove('pulse');
    showToast('Metronomo visivo: Spento');
    return;
  }
  const currentSong = state.stageSongs[state.stageIndex];
  const bpm = (currentSong && currentSong.bpm) ? currentSong.bpm : 120;
  startMetronomePulse(bpm);
  showToast(`Metronomo visivo: ${bpm} BPM`);
}

function startMetronomePulse(bpm) {
  if (metronomeTimer) clearInterval(metronomeTimer);
  const dot = document.getElementById('stage-metronome-dot');
  const intervalMs = (60 / (bpm || 120)) * 1000;
  metronomeTimer = setInterval(() => {
    if (dot) {
      dot.classList.add('pulse');
      setTimeout(() => dot.classList.remove('pulse'), 90);
    }
  }, intervalMs);
}

function adjustStageScrollSpeed(delta) {
  state.scrollSpeed = Math.max(5, Math.min(180, state.scrollSpeed + delta));
  const disp = document.getElementById('stage-speed-display');
  if (disp) disp.textContent = `${Math.round(state.scrollSpeed)} px/s`;
  showToast(`Velocità palco: ${Math.round(state.scrollSpeed)} px/s`);
}

function adjustStageFontSize(delta) {
  const container = document.getElementById('stage-lyrics');
  if (container) {
    const currentSize = parseFloat(window.getComputedStyle(container).fontSize) || 22;
    const newSize = Math.max(14, Math.min(38, currentSize + delta));
    container.style.fontSize = `${newSize}px`;
    showToast(`Font Palco: ${newSize}px`);
  }
}

function closeStageModal() {
  stopAutoscroll();
  if (metronomeTimer) {
    clearInterval(metronomeTimer);
    metronomeTimer = null;
  }
  isMetronomeActive = false;
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
  if (container) {
    scrollAccumulator = container.scrollTop;
  }
  lastScrollTime = performance.now();

  if (state.scrollIntervalId) {
    cancelAnimationFrame(state.scrollIntervalId);
    state.scrollIntervalId = null;
  }

  function step(now) {
    if (!state.isAutoscrolling) return;
    const dt = (now - lastScrollTime) / 1000;
    lastScrollTime = now;

    if (dt > 0 && dt < 0.2) {
      scrollAccumulator += (state.scrollSpeed * dt);
      if (container) {
        container.scrollTop = scrollAccumulator;
      }
    }
    state.scrollIntervalId = requestAnimationFrame(step);
  }

  state.scrollIntervalId = requestAnimationFrame(step);
}

function stopAutoscroll() {
  state.isAutoscrolling = false;
  const btn = document.getElementById('btn-stage-toggle');
  if (btn) {
    btn.innerHTML = '▶️';
    btn.style.backgroundColor = '#10b981';
  }
  if (state.scrollIntervalId) {
    cancelAnimationFrame(state.scrollIntervalId);
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

    if (e.key === 'PageDown' || e.key === 'ArrowDown' || e.key === '3') {
      const container = document.getElementById('stage-lyrics');
      if (container) container.scrollTop += 320;
      e.preventDefault();
    }
    else if (e.key === 'PageUp' || e.key === 'ArrowUp' || e.key === '1') {
      const container = document.getElementById('stage-lyrics');
      if (container) container.scrollTop -= 320;
      e.preventDefault();
    }
    else if (e.key === ' ' || e.key === 'Enter') {
      toggleAutoscroll();
      e.preventDefault();
    }
    else if (e.key === 'Escape') {
      closeStageModal();
    }
  });

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
      renderSetlists();
    }
  } catch (err) {
    console.warn('Setlists error:', err);
  }
}

function renderSetlists() {
  const container = document.getElementById('setlists-list');
  if (!container) return;

  if (state.setlists.length === 0) {
    container.innerHTML = '<div style="padding: 20px; color:#94a3b8;">Nessuna scaletta presente. Creane una con il tasto "+ Nuova Scaletta".</div>';
    return;
  }

  container.innerHTML = state.setlists.map(s => `
    <div class="song-card" style="margin-bottom: 12px; cursor: pointer;" onclick="openSetlistDetail('${s.uuid}')">
      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
          <div class="song-card-title">📑 ${escapeHtml(s.title)}</div>
          <div class="song-card-artist">${escapeHtml(s.date || 'Data da definire')} &bull; ${escapeHtml(s.description || 'Scaletta Concerto')}</div>
        </div>
        <span class="badge" style="background:#0284c7; color:#fff;">${s.item_count} Brani</span>
      </div>
      <div class="song-card-meta" style="margin-top: 12px; display:flex; gap:8px; flex-wrap:wrap;">
        <button class="btn btn-primary" style="min-height:36px; padding:4px 12px;" onclick="event.stopPropagation(); loadAndPlaySetlist('${s.uuid}')">🎤 Palco Live</button>
        <button class="btn btn-secondary" style="min-height:36px; padding:4px 12px;" onclick="event.stopPropagation(); downloadSetlistPdf('${s.uuid}')">💾 PDF Tablet</button>
        <button class="btn btn-secondary" style="min-height:36px; padding:4px 12px;" onclick="event.stopPropagation(); printSetlistA4('${s.uuid}')">🖨️ Stampa A4</button>
        <button class="btn btn-secondary" style="min-height:36px; padding:4px 12px;" onclick="event.stopPropagation(); openSetlistDetail('${s.uuid}')">✏️ Modifica</button>
        <button class="btn btn-danger" style="min-height:36px; padding:4px 12px;" onclick="event.stopPropagation(); deleteSetlist('${s.uuid}')">🗑️ Elimina</button>
      </div>
    </div>
  `).join('');
}

function downloadSetlistPdf(uuid) {
  const chordsParam = state.scoreMode === 'chords' ? 'true' : 'false';
  const url = `${API_BASE}/api/setlists/${uuid}/pdf?chords=${chordsParam}&device=${encodeURIComponent(state.activeDevice)}&email=${encodeURIComponent(state.currentUser.email)}`;
  window.open(url, '_blank');
}

function printSetlistA4(uuid) {
  const chordsParam = state.scoreMode === 'chords' ? 'true' : 'false';
  const url = `${API_BASE}/api/setlists/${uuid}/pdf?chords=${chordsParam}&device=Foglio%20A4&email=${encodeURIComponent(state.currentUser.email)}`;
  const win = window.open(url, '_blank');
  if (win) win.focus();
}

async function openSetlistDetail(uuid) {
  try {
    const res = await fetch(`${API_BASE}/api/setlists/${uuid}`);
    if (!res.ok) return;
    const data = await res.json();
    state.selectedSetlist = data;

    const detailContainer = document.getElementById('setlist-detail-view');
    const listContainer = document.getElementById('setlists-list');
    if (!detailContainer) return;

    if (listContainer) listContainer.style.display = 'none';
    detailContainer.style.display = 'block';

    renderSetlistEditor();
  } catch (err) {
    console.error('Error opening setlist:', err);
  }
}

function closeSetlistDetail() {
  const detailContainer = document.getElementById('setlist-detail-view');
  const listContainer = document.getElementById('setlists-list');
  if (detailContainer) detailContainer.style.display = 'none';
  if (listContainer) listContainer.style.display = 'block';
  loadSetlists();
}

function renderSetlistEditor() {
  const container = document.getElementById('setlist-detail-view');
  if (!container || !state.selectedSetlist) return;

  const s = state.selectedSetlist;
  const minutes = Math.floor((s.total_duration_seconds || 0) / 60);

  const itemsHtml = (s.items || []).map((item, idx) => `
    <div class="setlist-item-row">
      <div style="font-weight:900; color:#38bdf8; min-width:24px;">${idx + 1}.</div>
      <div style="flex:1;">
        <div style="font-weight:700; color:#fff;">${escapeHtml(item.title)}</div>
        <div style="font-size:12px; color:#94a3b8;">
          ${escapeHtml(item.artist || '')} &bull; Tonalità: <b style="color:#ffd600;">${item.key}</b>
          &bull; Tempo: <b>${item.bpm} BPM</b> ${item.is_medley ? '<span class="badge" style="background:#7c3aed; color:#fff; font-size:10px; margin-left:6px;">🔗 MEDLEY</span>' : ''}
        </div>
      </div>
      <div style="display:flex; gap:6px;">
        <button class="btn btn-secondary" style="min-height:34px; width:34px; padding:0;" title="Sposta su" onclick="moveSetlistItem(${idx}, -1)" ${idx === 0 ? 'disabled' : ''}>▲</button>
        <button class="btn btn-secondary" style="min-height:34px; width:34px; padding:0;" title="Sposta giù" onclick="moveSetlistItem(${idx}, 1)" ${idx === s.items.length - 1 ? 'disabled' : ''}>▼</button>
        <button class="btn btn-secondary" style="min-height:34px; padding:0 8px; font-size:11px;" title="Attiva/disattiva Medley" onclick="toggleSetlistMedley(${idx})">🔗</button>
        <button class="btn btn-secondary" style="min-height:34px; width:34px; padding:0; color:#ef4444;" title="Rimuovi" onclick="removeSetlistItem(${idx})">✕</button>
      </div>
    </div>
  `).join('');

  // Song options for "+ Aggiungi Brano"
  const songOptions = (state.songs || []).map(song => 
    `<option value="${song.uuid}">${escapeHtml(song.title)} (${escapeHtml(song.artist || '')})</option>`
  ).join('');

  container.innerHTML = `
    <div class="song-viewer" style="margin-bottom:14px;">
      <div class="viewer-header">
        <div>
          <h2 style="font-size: 22px; font-weight: 900; color: #fff;">📑 ${escapeHtml(s.title)}</h2>
          <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
            <b>${escapeHtml(s.date || '')}</b> &bull; ${escapeHtml(s.description || '')} &bull; Durata: <b>${minutes} min</b> (${s.total_songs || s.items.length} brani)
          </div>
        </div>
        <div class="viewer-tools">
          <button class="btn btn-primary" onclick="loadAndPlaySetlist('${s.uuid}')">🎤 Avvia Palco</button>
          <button class="btn btn-secondary" onclick="downloadSetlistPdf('${s.uuid}')">💾 PDF Tablet</button>
          <button class="btn btn-secondary" onclick="printSetlistA4('${s.uuid}')">🖨️ Stampa A4</button>
          <button class="btn btn-danger" onclick="deleteSetlist('${s.uuid}')">🗑️ Elimina Scaletta</button>
          <button class="btn btn-secondary" onclick="closeSetlistDetail()">✕ Chiudi</button>
        </div>
      </div>

      <!-- ADD SONG CONTROLS -->
      <div style="display:flex; gap:10px; margin: 16px 0; align-items:center; background:var(--bg-surface-elevated); padding:10px 14px; border-radius:8px; border:1px solid var(--border-color);">
        <label style="font-size:13px; font-weight:700; color:#38bdf8;">+ Aggiungi Brano:</label>
        <select id="select-add-song-setlist" class="search-input" style="flex:1;">
          <option value="">-- Seleziona un brano dal repertorio --</option>
          ${songOptions}
        </select>
        <button class="btn btn-primary" onclick="addSelectedSongToSetlist()">Aggiungi</button>
      </div>

      <!-- ITEMS LIST -->
      <div style="margin-top:14px;">
        ${itemsHtml || '<div style="color:#94a3b8; padding:16px;">Nessun brano in questa scaletta. Aggiungine uno sopra!</div>'}
      </div>
    </div>
  `;
}

function moveSetlistItem(index, delta) {
  if (!state.selectedSetlist || !state.selectedSetlist.items) return;
  const items = state.selectedSetlist.items;
  const target = index + delta;
  if (target < 0 || target >= items.length) return;

  const temp = items[index];
  items[index] = items[target];
  items[target] = temp;

  renderSetlistEditor();
  saveCurrentSetlist();
}

function toggleSetlistMedley(index) {
  if (!state.selectedSetlist || !state.selectedSetlist.items) return;
  const item = state.selectedSetlist.items[index];
  item.is_medley = !item.is_medley;
  renderSetlistEditor();
  saveCurrentSetlist();
}

function removeSetlistItem(index) {
  if (!state.selectedSetlist || !state.selectedSetlist.items) return;
  state.selectedSetlist.items.splice(index, 1);
  renderSetlistEditor();
  saveCurrentSetlist();
}

function addSelectedSongToSetlist() {
  const sel = document.getElementById('select-add-song-setlist');
  if (!sel || !sel.value || !state.selectedSetlist) return;
  const songUuid = sel.value;
  const song = (state.songs || []).find(s => s.uuid === songUuid);
  if (!song) return;

  if (!state.selectedSetlist.items) state.selectedSetlist.items = [];
  state.selectedSetlist.items.push({
    index: state.selectedSetlist.items.length + 1,
    song_uuid: song.uuid,
    title: song.title,
    artist: song.artist,
    key: song.key_current,
    bpm: song.bpm,
    duration_seconds: song.duration_seconds || 0,
    is_medley: false,
    medley_group_id: null,
    notes: ""
  });

  renderSetlistEditor();
  saveCurrentSetlist();
  showToast(`Aggiunto: ${song.title} ✓`);
}

async function saveCurrentSetlist() {
  if (!state.selectedSetlist) return;
  const s = state.selectedSetlist;
  const payload = {
    uuid: s.uuid,
    title: s.title,
    date: s.date,
    description: s.description,
    items: (s.items || []).map(it => ({
      song_uuid: it.song_uuid,
      is_medley: it.is_medley || false,
      medley_group_id: it.medley_group_id || null,
      custom_key: it.custom_key || null,
      custom_bpm: it.custom_bpm || null,
      notes: it.notes || ""
    })),
    user_email: state.currentUser.email,
    user_name: state.currentUser.name
  };

  try {
    const res = await fetch(`${API_BASE}/api/setlists`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast('Scaletta salvata su Turso Cloud DB ✓');
    }
  } catch (err) {
    console.warn('Setlist save error:', err);
  }
}

function showNewSetlistForm() {
  const form = document.getElementById('new-setlist-form');
  const btn = document.getElementById('btn-open-new-setlist');
  if (form) {
    form.style.display = 'block';
    const titleInput = document.getElementById('new-setlist-title');
    if (titleInput) {
      titleInput.value = '';
      titleInput.focus();
    }
    const dateInput = document.getElementById('new-setlist-date');
    if (dateInput) {
      dateInput.value = new Date().toISOString().split('T')[0];
    }
  }
  if (btn) btn.style.display = 'none';
}

function hideNewSetlistForm() {
  const form = document.getElementById('new-setlist-form');
  const btn = document.getElementById('btn-open-new-setlist');
  if (form) form.style.display = 'none';
  if (btn) btn.style.display = 'inline-flex';
}

async function submitNewSetlist() {
  const titleInput = document.getElementById('new-setlist-title');
  const dateInput = document.getElementById('new-setlist-date');
  const descInput = document.getElementById('new-setlist-desc');

  const title = titleInput ? titleInput.value.trim() : '';
  if (!title) {
    alert('Inserisci il titolo della scaletta');
    if (titleInput) titleInput.focus();
    return;
  }

  const payload = {
    title: title,
    date: dateInput ? dateInput.value.trim() : '',
    description: descInput ? descInput.value.trim() : 'Nuova Scaletta Live',
    items: [],
    user_email: state.currentUser.email,
    user_name: state.currentUser.name
  };

  try {
    const res = await fetch(`${API_BASE}/api/setlists`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json();
      showToast(`Scaletta "${title}" creata ✓`);
      hideNewSetlistForm();
      await loadSetlists();
      if (data.setlist && data.setlist.uuid) {
        openSetlistDetail(data.setlist.uuid);
      }
    }
  } catch (err) {
    console.error('Error creating setlist:', err);
  }
}

async function deleteSetlist(uuid) {
  const s = (state.setlists || []).find(item => item.uuid === uuid) || (state.selectedSetlist && state.selectedSetlist.uuid === uuid ? state.selectedSetlist : null);
  const title = s ? s.title : 'questa scaletta';
  if (!confirm(`Sei sicuro di voler eliminare definitivamente la scaletta "${title}"?`)) return;

  try {
    const res = await fetch(`${API_BASE}/api/setlists/${uuid}?user_email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name)}`, {
      method: 'DELETE'
    });
    if (res.ok) {
      showToast(`Scaletta "${title}" eliminata ✓`);
      closeSetlistDetail();
      await loadSetlists();
    }
  } catch (err) {
    console.error('Error deleting setlist:', err);
  }
}

async function loadAndPlaySetlist(uuid) {
  try {
    const res = await fetch(`${API_BASE}/api/setlists/${uuid}`);
    if (res.ok) {
      const data = await res.json();
      state.selectedSetlist = data;
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
      } else {
        showToast('Questa scaletta non contiene brani');
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
