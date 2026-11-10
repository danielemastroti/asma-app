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
  songViewType: (() => { try { return localStorage.getItem('asma_song_view_type') || 'pdf'; } catch (e) { return 'pdf'; } })(),
  stageViewType: (() => { try { return localStorage.getItem('asma_stage_view_type') || 'pdf'; } catch (e) { return 'pdf'; } })(),
  userPrefs: {
    layout_font_size: 12.0,
    layout_font_size_chords: 13.0,
    layout_columns: 1,
    layout_margin_lateral: 10.0,
    color_lyrics: '#111111',
    color_chords: '#B71C1C',
    color_aml_markup: '#4A148C',
    stage_color_lyrics: '#FFFFFF',
    stage_color_chords: '#FFD600',
    stage_color_aml_markup: '#38BDF8',
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
  await loadRepertoires();
  await loadSongs();
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

function isCurrentUserAdmin() {
  if (!state.currentUser || !state.currentUser.email) return false;
  const email = state.currentUser.email.toLowerCase();
  if (['danyposta@gmail.com', 'danyposta@yahoo.it'].includes(email)) return true;
  if (state.currentUser.role === 'ADMIN' || state.currentUser.role === 'BAND_LEADER') return true;
  const matched = (state.usersList || []).find(u => u.email.toLowerCase() === email);
  if (matched && (matched.role === 'ADMIN' || matched.role === 'BAND_LEADER')) return true;
  return false;
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
        state.currentUser.role = matched.role;
      } else if (users.length) {
        state.currentUser.email = users[0].email;
        state.currentUser.name = users[0].name;
        state.currentUser.role = users[0].role;
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
  root.style.setProperty('--stage-lyrics-color', p.stage_color_lyrics || '#FFFFFF');
  root.style.setProperty('--stage-chords-color', p.stage_color_chords || '#FFD600');
  root.style.setProperty('--stage-aml-color', p.stage_color_aml_markup || '#38BDF8');
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
  const stagePrevBox = document.getElementById('settings-stage-live-preview');
  if (stagePrevBox) {
    stagePrevBox.style.color = p.stage_color_lyrics || '#FFFFFF';
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

  // Color inputs - Spartito & PDF (Sfondo Bianco)
  const cLyrics = document.getElementById('pick-color-lyrics');
  if (cLyrics) cLyrics.value = p.color_lyrics || '#111111';
  const cChords = document.getElementById('pick-color-chords');
  if (cChords) cChords.value = p.color_chords || '#B71C1C';
  const cAml = document.getElementById('pick-color-aml');
  if (cAml) cAml.value = p.color_aml_markup || '#4A148C';

  const tLyrics = document.getElementById('val-color-lyrics');
  if (tLyrics) tLyrics.textContent = p.color_lyrics || '#111111';
  const tChords = document.getElementById('val-color-chords');
  if (tChords) tChords.textContent = p.color_chords || '#B71C1C';
  const tAml = document.getElementById('val-color-aml');
  if (tAml) tAml.textContent = p.color_aml_markup || '#4A148C';

  // Color inputs - Modalità Palco (Teleprompter Sfondo Nero)
  const cStageLyrics = document.getElementById('pick-stage-color-lyrics');
  if (cStageLyrics) cStageLyrics.value = p.stage_color_lyrics || '#FFFFFF';
  const cStageChords = document.getElementById('pick-stage-color-chords');
  if (cStageChords) cStageChords.value = p.stage_color_chords || '#FFD600';
  const cStageAml = document.getElementById('pick-stage-color-aml');
  if (cStageAml) cStageAml.value = p.stage_color_aml_markup || '#38BDF8';

  const tStageLyrics = document.getElementById('val-stage-color-lyrics');
  if (tStageLyrics) tStageLyrics.textContent = p.stage_color_lyrics || '#FFFFFF';
  const tStageChords = document.getElementById('val-stage-color-chords');
  if (tStageChords) tStageChords.textContent = p.stage_color_chords || '#FFD600';
  const tStageAml = document.getElementById('val-stage-color-aml');
  if (tStageAml) tStageAml.textContent = p.stage_color_aml_markup || '#38BDF8';
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

async function onMusicianChange(email) {
  state.currentUser.email = email;
  try { localStorage.setItem('asma_user_email', email); } catch (e) {}
  const user = (state.usersList || []).find(u => u.email.toLowerCase() === email.toLowerCase());
  state.currentUser.name = user ? user.name : (email.split('@')[0]);
  state.currentUser.role = user ? user.role : 'BAND_MEMBER';
  const nameSpan = document.getElementById('current-user-name');
  if (nameSpan) nameSpan.textContent = state.currentUser.name;

  // Non-admins must never have activeRepertoire as __ALL__
  const isAdmin = isCurrentUserAdmin();
  if (!isAdmin && state.activeRepertoire === '__ALL__') {
    state.activeRepertoire = '';
  }

  await loadUserPreferences();
  await loadRepertoires();
  await loadSongs();
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
  else if (type === 'stage_lyrics') state.userPrefs.stage_color_lyrics = hexColor;
  else if (type === 'stage_chords') state.userPrefs.stage_color_chords = hexColor;
  else if (type === 'stage_aml') state.userPrefs.stage_color_aml_markup = hexColor;
  applyPreferencesToDom();
  autosaveUserPreferences();
  if (state.selectedSong) renderSongViewer();
}

// ----------------------------------------------------------------------------
// REPERTOIRES & SONGS (0ms Client Filtering)
// ----------------------------------------------------------------------------
async function loadRepertoires() {
  try {
    const res = await fetch(`${API_BASE}/api/repertoires?user_email=${encodeURIComponent(state.currentUser.email)}`);
    if (res.ok) {
      state.repertoires = await res.json();
      const isAdmin = isCurrentUserAdmin();
      const official = state.repertoires.find(r => r.is_official);

      if (!isAdmin) {
        // Musicians NEVER see '__ALL__' and must default to Official Repertoire
        const currentExists = state.repertoires.some(r => r.uuid === state.activeRepertoire);
        if (state.activeRepertoire === '__ALL__' || !currentExists) {
          state.activeRepertoire = official ? official.uuid : (state.repertoires[0]?.uuid || '');
        }
      } else {
        // Admin can see '__ALL__'
        const currentExists = state.repertoires.some(r => r.uuid === state.activeRepertoire);
        if (state.activeRepertoire !== '__ALL__' && !currentExists) {
          state.activeRepertoire = official ? official.uuid : '__ALL__';
        }
      }
      renderRepertoireChips();
    }
  } catch (err) {
    console.warn('Repertoires offline:', err);
  }
}

function renderRepertoireChips() {
  const container = document.getElementById('repertoire-chips');
  if (!container) return;

  const isAdmin = isCurrentUserAdmin();
  let html = '';

  // Only Admin sees "🌐 Tutti"
  if (isAdmin) {
    const totalSongs = state.songs.length;
    html += `<button class="chip ${state.activeRepertoire === '__ALL__' ? 'active' : ''}" onclick="selectRepertoire('__ALL__')">🌐 Tutti (${totalSongs})</button>`;
  }

  state.repertoires.forEach(r => {
    const isActive = state.activeRepertoire === r.uuid ? 'active' : '';
    let icon = '📁';
    let label = escapeHtml(r.name);
    let extraStyle = '';
    if (r.is_official) {
      icon = '🌟';
      label = `<b>${escapeHtml(r.name)}</b>`;
      extraStyle = 'border-color: #ffd600; color: #ffd600; font-weight: 800;';
    } else if (r.owner_email === state.currentUser.email) {
      icon = '👤';
      label = `Personale (${escapeHtml(r.name)})`;
    }
    html += `<button class="chip ${isActive}" style="${isActive ? '' : extraStyle}" onclick="selectRepertoire('${r.uuid}')">${icon} ${label} (${r.song_count})</button>`;
  });

  container.innerHTML = html;

  const adminBtn = document.getElementById('btn-admin-manage-rep');
  if (adminBtn) {
    adminBtn.style.display = isAdmin ? 'inline-block' : 'none';
  }
}

function selectRepertoire(repUuid) {
  state.activeRepertoire = repUuid;
  renderRepertoireChips();
  renderSongCards();
}

async function loadSongs() {
  try {
    const url = state.currentUser?.email
      ? `${API_BASE}/api/songs?user_email=${encodeURIComponent(state.currentUser.email)}`
      : `${API_BASE}/api/songs`;
    const res = await fetch(url);
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
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <div class="song-card-title">${escapeHtml(s.title)}</div>
          <button class="btn btn-secondary" style="min-height: 26px; padding: 2px 8px; font-size: 11px; color: #38bdf8; border-color: #38bdf8; font-weight: 800; white-space: nowrap;" onclick="event.stopPropagation(); openAddToSetlistModal('${s.uuid}')" title="Aggiungi a una scaletta">+ Scaletta</button>
        </div>
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
  const viewTypeLabel = state.songViewType === 'pdf' ? '📄 Spartito PDF' : '📝 Testo Web';

  const officialRep = state.repertoires.find(r => r.is_official);
  const isInOfficial = officialRep && officialRep.song_uuids && officialRep.song_uuids.includes(s.uuid);
  const promoteBtn = (!isInOfficial && officialRep) ? 
    `<button class="btn btn-secondary" style="color: #ffd600; border-color: #ffd600; font-weight: 800;" onclick="promoteSongToOfficial('${s.uuid}')" title="Aggiungi questo brano al Repertorio Ufficiale della Band">⭐ Promuovi a Ufficiale</button>` : '';

  const headerHtml = `
    <div class="viewer-header">
      <div>
        <h2 style="font-size: 22px; font-weight: 900; color: #fff;">${escapeHtml(s.title)}</h2>
        <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
          <b>${escapeHtml(s.artist || 'Band')}</b> &bull; Tonalità: <code style="color:#ffd600; font-weight:700;">${s.key_current}</code>
          &bull; Tempo: <code style="color:#00e5ff;">${s.bpm || 120} BPM</code> &bull; Capo: <b>${s.capo || 0}°</b>
          &bull; Formato: <code style="color:#38bdf8;">${escapeHtml(state.activeDevice)}</code>
        </div>
      </div>
      <div class="viewer-tools">
        <button class="btn btn-secondary" onclick="transposeSong(-1)" title="Abbassa di 1 semitono">♭ -1</button>
        <button class="btn btn-secondary" onclick="transposeSong(1)" title="Alza di 1 semitono">♯ +1</button>
        <button class="btn btn-secondary" onclick="adjustFontSize('lyrics', -1)" title="Riduci dimensione caratteri">A−</button>
        <button class="btn btn-secondary" onclick="adjustFontSize('lyrics', 1)" title="Ingrandisci dimensione caratteri">A+</button>
        <button class="btn btn-secondary" onclick="toggleScoreMode()">${modeLabel}</button>
        <button class="btn btn-secondary" onclick="toggleColumns()">${colsLabel}</button>
        <button class="btn btn-secondary" style="color: #38bdf8; border-color: #38bdf8; font-weight: 800;" onclick="toggleSongViewType()" title="Passa tra vista Spartito PDF reale e Testo Web">${viewTypeLabel}</button>
        <button class="btn btn-primary" onclick="startSingleSongStage()">🎤 Palco</button>
        <button class="btn btn-secondary" style="color: #38bdf8; border-color: #38bdf8; font-weight: 800;" onclick="openAddToSetlistModal('${s.uuid}')" title="Aggiungi questo brano a una scaletta">📑 + Scaletta</button>
        ${promoteBtn}
        <button class="btn btn-secondary" onclick="forkSongToPersonal('${s.uuid}')" title="Crea una copia indipendente nel tuo repertorio personale per personalizzarla liberamente">📋 Copia Personale</button>
        <button class="btn btn-secondary" onclick="openSongEditor()" title="Modifica testo o accordi">✏️ Modifica</button>
        <button class="btn btn-secondary" onclick="printA4()">🖨️ Stampa A4</button>
        <button class="btn btn-secondary" onclick="downloadPdf()">💾 Salva PDF</button>
        <button class="btn btn-danger" onclick="deleteSongWithUndo('${s.uuid}')" title="Elimina brano con protezione e recupero immediato">🗑️</button>
      </div>
    </div>
  `;

  if (state.songViewType === 'pdf') {
    container.innerHTML = `
      ${headerHtml}
      <div class="lyrics-container" id="printable-lyrics" style="padding: 10px; background: transparent; border: none; box-shadow: none;">
        <div id="pdf-preview-loading" style="text-align: center; padding: 40px 16px; color: #94a3b8;">
          <div style="font-size: 26px; margin-bottom: 8px;">⏳</div>
          Caricamento impaginazione reale PDF (${escapeHtml(state.activeDevice)})...
        </div>
      </div>
    `;
    loadSongPdfPreview(s.uuid);
  } else {
    const formattedHtml = parseAmlForWeb(s.aml_content, hasChords);
    container.innerHTML = `
      ${headerHtml}
      <div class="lyrics-container" id="printable-lyrics">
        ${formattedHtml}
      </div>
    `;
  }
}

async function loadSongPdfPreview(songUuid) {
  const hasChords = state.scoreMode === 'chords';
  const container = document.getElementById('printable-lyrics');
  if (!container) return;

  try {
    const p = state.userPrefs;
    const url = `${API_BASE}/api/songs/${songUuid}/pdf/preview?chords=${hasChords}&device=${encodeURIComponent(state.activeDevice)}&email=${encodeURIComponent(state.currentUser.email)}&columns=${p.layout_columns || 1}&font_size=${p.layout_font_size || 12}&font_size_chords=${p.layout_font_size_chords || 13}&margin_lateral=${p.layout_margin_lateral || 10}`;
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      if (state.selectedSong && state.selectedSong.uuid === songUuid && state.songViewType === 'pdf') {
        container.innerHTML = `
          <div class="pdf-pages-container">
            ${data.pages.map((b64, idx) => `
              <div class="pdf-page-wrapper">
                <img src="${b64}" class="pdf-page-img" alt="Pagina ${idx + 1} di ${data.total_pages}" />
                <div class="pdf-page-badge">Pagina ${idx + 1} di ${data.total_pages} &bull; Profilo ${escapeHtml(data.device)}</div>
              </div>
            `).join('')}
          </div>
        `;
      }
    } else {
      container.innerHTML = `<div style="padding:24px; text-align:center; color:#ef4444;">Impossibile caricare l'anteprima PDF. <button class="btn btn-secondary" style="margin-left:8px;" onclick="setSongViewType('web')">Passa a Vista Testo</button></div>`;
    }
  } catch (err) {
    console.error('PDF preview error:', err);
    container.innerHTML = `<div style="padding:24px; text-align:center; color:#ef4444;">Errore connessione anteprima PDF. <button class="btn btn-secondary" style="margin-left:8px;" onclick="setSongViewType('web')">Passa a Vista Testo</button></div>`;
  }
}

function toggleSongViewType() {
  state.songViewType = (state.songViewType === 'pdf') ? 'web' : 'pdf';
  try { localStorage.setItem('asma_song_view_type', state.songViewType); } catch (e) {}
  renderSongViewer();
  showToast(state.songViewType === 'pdf' ? '📄 Vista: Spartito PDF Reale' : '📝 Vista: Testo Web');
}

function setSongViewType(type) {
  state.songViewType = type;
  try { localStorage.setItem('asma_song_view_type', state.songViewType); } catch (e) {}
  renderSongViewer();
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
      renderSongCards();
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
    const repSelect = document.getElementById('new-song-repertoire');
    if (repSelect && state.repertoires && state.repertoires.length > 0) {
      repSelect.innerHTML = state.repertoires.map(r => {
        const isSelected = (state.activeRepertoire === r.uuid) || (state.activeRepertoire === '__ALL__' && (r.owner_email === state.currentUser.email || r.is_official));
        return `<option value="${r.uuid}" ${isSelected ? 'selected' : ''}>${escapeHtml(r.name)}</option>`;
      }).join('');
    }
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function hideNewSongForm() {
  const form = document.getElementById('new-song-form');
  if (form) form.style.display = 'none';
}

function switchImportTab(tab) {
  const btnWeb = document.getElementById('btn-import-tab-web');
  const btnPaste = document.getElementById('btn-import-tab-paste');
  const btnUrl = document.getElementById('btn-import-tab-url');
  const btnManual = document.getElementById('btn-import-tab-manual');

  if (btnWeb) btnWeb.classList.toggle('active', tab === 'web');
  if (btnPaste) btnPaste.classList.toggle('active', tab === 'paste');
  if (btnUrl) btnUrl.classList.toggle('active', tab === 'url');
  if (btnManual) btnManual.classList.toggle('active', tab === 'manual');

  const paneWeb = document.getElementById('import-pane-web');
  const panePaste = document.getElementById('import-pane-paste');
  const paneUrl = document.getElementById('import-pane-url');

  if (paneWeb) paneWeb.style.display = tab === 'web' ? 'block' : 'none';
  if (panePaste) panePaste.style.display = tab === 'paste' ? 'block' : 'none';
  if (paneUrl) paneUrl.style.display = tab === 'url' ? 'block' : 'none';
}

async function executeWebSearch() {
  const tInput = document.getElementById('web-search-title');
  const aInput = document.getElementById('web-search-artist');
  const title = tInput ? tInput.value.trim() : '';
  const artist = aInput ? aInput.value.trim() : '';

  if (!title) {
    showToast('Inserisci il titolo del brano da cercare');
    if (tInput) tInput.focus();
    return;
  }

  const resultsContainer = document.getElementById('web-search-results');
  if (resultsContainer) {
    resultsContainer.style.display = 'block';
    resultsContainer.innerHTML = '<div style="padding: 12px; color: #38bdf8; text-align: center;">🔍 Ricerca accordi in corso su Accordi e Spartiti & Ultimate-Guitar...</div>';
  }

  try {
    const res = await fetch(`${API_BASE}/api/songs/web-search?title=${encodeURIComponent(title)}&artist=${encodeURIComponent(artist)}`);
    if (res.ok) {
      const data = await res.json();
      if (!data.candidates || data.candidates.length === 0) {
        if (resultsContainer) {
          resultsContainer.innerHTML = `
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; border-radius: 6px; padding: 12px; color: #fca5a5; font-size: 13px;">
              Nessun accordo trovato online per <b>"${escapeHtml(title)}"</b>.<br>
              Puoi provare a incollare il testo nella scheda <i>📋 Incolla Testo</i> oppure scrivere direttamente l'AML.
            </div>
          `;
        }
        return;
      }

      let cardsHtml = `
        <div style="font-size: 12px; color: #10b981; font-weight: 700; margin-bottom: 8px;">
          ✓ Trovati ${data.candidates.length} spartiti online. Tocca un brano per importarlo:
        </div>
      `;

      data.candidates.forEach((cand) => {
        cardsHtml += `
          <div class="web-result-card">
            <div style="flex: 1; min-width: 0;">
              <div style="font-weight: 800; font-size: 14px; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                ${escapeHtml(cand.title)}
              </div>
              <div style="font-size: 12px; color: #38bdf8; margin-top: 2px;">
                <b>${escapeHtml(cand.artist)}</b> &bull; <span class="portal-badge">${escapeHtml(cand.portal)}</span>
              </div>
            </div>
            <button class="btn btn-success" style="font-weight: 800; min-height: 36px; padding: 4px 14px; white-space: nowrap;" onclick="importCandidateUrl('${encodeURIComponent(cand.url)}')">
              ⚡ Importa
            </button>
          </div>
        `;
      });

      if (resultsContainer) {
        resultsContainer.innerHTML = cardsHtml;
      }
    } else {
      if (resultsContainer) {
        resultsContainer.innerHTML = '<div style="color:#ef4444; font-size:13px; padding:8px;">Errore durante la ricerca web. Verifica la connessione.</div>';
      }
    }
  } catch (err) {
    console.error('Web search error:', err);
    if (resultsContainer) {
      resultsContainer.innerHTML = '<div style="color:#ef4444; font-size:13px; padding:8px;">Errore di connessione durante la ricerca online.</div>';
    }
  }
}

async function importCandidateUrl(encodedUrl) {
  const url = decodeURIComponent(encodedUrl);
  showToast('Download ed elaborazione spartito...');

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
      const capoField = document.getElementById('new-song-capo');
      if (capoField) capoField.value = data.capo || 0;
      const amlField = document.getElementById('new-song-aml');
      if (amlField) amlField.value = data.aml;

      // Scroll smoothly down to the form fields
      if (tField) tField.scrollIntoView({ behavior: 'smooth', block: 'center' });
      showToast(`Brano "${data.title}" importato! Tocca "Salva nel Repertorio" per confermare ✓`);
    } else {
      showToast('Impossibile estrarre gli accordi da questo link');
    }
  } catch (err) {
    console.error('Candidate import error:', err);
    showToast('Errore durante l\'importazione');
  }
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

  const repSelect = document.getElementById('new-song-repertoire');
  const targetRepertoire = repSelect?.value || (state.activeRepertoire !== '__ALL__' ? state.activeRepertoire : null);

  const payload = {
    title: title.toUpperCase(),
    artist: artist,
    key_current: key,
    bpm: bpm,
    capo: capo,
    aml_content: aml,
    repertoire_uuid: targetRepertoire,
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
      showToast(`Brano "${title}" salvato nel repertorio ✓`);
      hideNewSongForm();
      if (targetRepertoire) {
        state.activeRepertoire = targetRepertoire;
      }
      // Reload both repertoires and songs to immediately reflect new assignment in UI
      await loadRepertoires();
      await loadSongs();
      if (data.song && data.song.uuid) {
        selectSong(data.song.uuid);
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

async function openStageModal() {
  state.isStageActive = true;
  state.isAutoscrolling = false;

  const currentSong = state.stageSongs[state.stageIndex];
  const stageModal = document.getElementById('stage-modal');
  if (!stageModal || !currentSong) return;

  stageModal.style.display = 'flex';
  document.getElementById('stage-song-title').textContent = currentSong.title;
  document.getElementById('stage-song-meta').textContent = `${currentSong.artist} • Key: ${currentSong.key_current} • ${currentSong.bpm || 120} BPM • Capo: ${currentSong.capo || 0}°`;

  await renderStageSong(currentSong);
}

async function renderStageSong(currentSong) {
  const container = document.getElementById('stage-lyrics');
  if (!container || !currentSong) return;

  updateStageViewButton();
  updateStageScoreModeButton();

  const prevScroll = container.scrollTop || 0;

  if (state.stageViewType === 'pdf') {
    container.innerHTML = `<div style="text-align:center; padding:50px 16px; color:#94a3b8;"><div style="font-size:32px; margin-bottom:10px;">⏳</div>Caricamento spartito PDF per il palco...</div>`;
    try {
      const hasChords = state.scoreMode === 'chords';
      const p = state.userPrefs;
      const url = `${API_BASE}/api/songs/${currentSong.uuid}/pdf/preview?chords=${hasChords}&device=${encodeURIComponent(state.activeDevice)}&email=${encodeURIComponent(state.currentUser.email)}&columns=${p.layout_columns || 1}&font_size=${p.layout_font_size || 12}&font_size_chords=${p.layout_font_size_chords || 13}&margin_lateral=${p.layout_margin_lateral || 10}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        container.innerHTML = `
          <div class="stage-pdf-container">
            ${data.pages.map((b64, idx) => `
              <div class="stage-pdf-page">
                <img src="${b64}" alt="Pagina ${idx + 1} di ${data.total_pages}" />
              </div>
            `).join('')}
          </div>
        `;
      } else {
        container.innerHTML = parseAmlForWeb(currentSong.aml_content, state.scoreMode === 'chords');
      }
    } catch (err) {
      console.error('Stage PDF preview error:', err);
      container.innerHTML = parseAmlForWeb(currentSong.aml_content, state.scoreMode === 'chords');
    }
  } else {
    container.innerHTML = parseAmlForWeb(currentSong.aml_content, state.scoreMode === 'chords');
  }

  container.scrollTop = prevScroll;
  scrollAccumulator = prevScroll;

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

  if ('wakeLock' in navigator) {
    navigator.wakeLock.request('screen').catch(console.warn);
  }
}

function toggleStageViewType() {
  state.stageViewType = (state.stageViewType === 'pdf') ? 'prompter' : 'pdf';
  try { localStorage.setItem('asma_stage_view_type', state.stageViewType); } catch (e) {}
  updateStageViewButton();
  const currentSong = state.stageSongs[state.stageIndex];
  if (currentSong) renderStageSong(currentSong);
  showToast(state.stageViewType === 'pdf' ? '📄 Vista Palco: Spartito PDF Reale' : '🎤 Vista Palco: Teleprompter Notte');
}

function updateStageViewButton() {
  const btn = document.getElementById('stage-view-btn');
  if (btn) {
    if (state.stageViewType === 'pdf') {
      btn.textContent = '📄 Spartito PDF';
      btn.style.color = '#38bdf8';
      btn.style.borderColor = '#38bdf8';
    } else {
      btn.textContent = '🎤 Teleprompter';
      btn.style.color = '#ffd600';
      btn.style.borderColor = '#ffd600';
    }
  }
}

function toggleStageScoreMode() {
  state.scoreMode = state.scoreMode === 'chords' ? 'lyrics' : 'chords';
  state.userPrefs.score_display_mode = state.scoreMode;
  try { localStorage.setItem('asma_score_mode', state.scoreMode); } catch (e) {}
  updateStageScoreModeButton();
  updateSettingsFormValues();

  const currentSong = state.stageSongs[state.stageIndex];
  if (currentSong) {
    renderStageSong(currentSong);
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
    `<option value="${song.uuid}">${escapeHtml(song.title)} (${escapeHtml(song.artist || 'Band')}) [Key: ${escapeHtml(song.key_current || '-')}]</option>`
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

      <!-- ADD SONG CONTROLS WITH EXPLICIT CONFIRM BUTTON -->
      <div style="display:flex; flex-wrap:wrap; gap:12px; margin: 18px 0; align-items:flex-end; background:var(--bg-surface-elevated); padding:14px 16px; border-radius:10px; border:1.5px solid var(--accent-cyan); box-shadow: 0 4px 14px rgba(0,0,0,0.3);">
        <div style="flex:1 1 280px; min-width:0; display:flex; flex-direction:column; gap:6px;">
          <label for="select-add-song-setlist" style="font-size:13.5px; font-weight:800; color:#38bdf8; display:flex; align-items:center; gap:6px;">
            <span>➕</span> Scegli un brano da aggiungere alla scaletta:
          </label>
          <select id="select-add-song-setlist" class="search-input" style="width:100%; min-height:44px; font-size:14px; font-weight:600; padding:8px 12px; background:#0f172a; border:1px solid var(--accent-cyan); color:#fff; border-radius:8px;" onchange="onSetlistSongSelectChange()" onkeydown="if(event.key==='Enter') addSelectedSongToSetlist()">
            <option value="">-- Seleziona un brano dal repertorio --</option>
            ${songOptions}
          </select>
        </div>
        <div style="flex:0 0 auto;">
          <button id="btn-confirm-add-song-setlist" class="btn btn-success" style="min-height:44px; padding:10px 22px; font-size:14px; font-weight:900; white-space:nowrap; display:flex; align-items:center; gap:8px; border-radius:8px; cursor:pointer;" onclick="addSelectedSongToSetlist()">
            ✓ Conferma e Aggiungi
          </button>
        </div>
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

function onSetlistSongSelectChange() {
  const sel = document.getElementById('select-add-song-setlist');
  const btn = document.getElementById('btn-confirm-add-song-setlist');
  if (!sel || !btn) return;

  if (sel.value) {
    const song = (state.songs || []).find(s => s.uuid === sel.value);
    const title = song ? song.title : 'questo brano';
    btn.innerHTML = `✓ Conferma e Inserisci "${escapeHtml(title)}"`;
    btn.style.boxShadow = '0 0 16px rgba(16, 185, 129, 0.7)';
    btn.style.borderColor = '#10b981';
  } else {
    btn.innerHTML = `✓ Conferma e Aggiungi`;
    btn.style.boxShadow = 'none';
    btn.style.borderColor = 'transparent';
  }
}

function addSelectedSongToSetlist() {
  const sel = document.getElementById('select-add-song-setlist');
  if (!sel || !state.selectedSetlist) return;
  if (!sel.value) {
    showToast("⚠️ Seleziona prima un brano dall'elenco a discesa");
    return;
  }
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
  showToast(`Aggiunto alla scaletta: ${song.title} ✓`);
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
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore creazione scaletta');
    }
  } catch (err) {
    console.error('Error creating setlist:', err);
    showToast('Errore di connessione creazione scaletta');
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
// ADD TO SETLIST (1-Touch Modal)
// ----------------------------------------------------------------------------
let pendingSetlistSongUuid = null;

async function openAddToSetlistModal(songUuid) {
  pendingSetlistSongUuid = songUuid;
  const song = (state.songs || []).find(s => s.uuid === songUuid) || state.selectedSong;
  const modal = document.getElementById('add-to-setlist-modal');
  const info = document.getElementById('add-to-setlist-song-info');
  const optionsContainer = document.getElementById('add-to-setlist-options');
  if (!modal || !optionsContainer) return;

  if (info && song) {
    info.textContent = `Brano selezionato: ${song.title} (${song.artist || 'Band'})`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/setlists`);
    if (res.ok) state.setlists = await res.json();
  } catch (e) {}

  if (!state.setlists || state.setlists.length === 0) {
    optionsContainer.innerHTML = '<div style="color: #94a3b8; font-size: 13px; padding: 10px;">Nessuna scaletta esistente. Inserisci un titolo qui sotto per crearla subito!</div>';
  } else {
    optionsContainer.innerHTML = state.setlists.map(set => `
      <button class="btn btn-secondary" style="text-align: left; justify-content: space-between; padding: 10px 14px; font-weight: 700; width: 100%;" onclick="addSongToSpecificSetlist('${set.uuid}', '${songUuid}')">
        <span>📑 ${escapeHtml(set.title)}</span>
        <span class="badge" style="background: #0284c7; color: #fff;">${set.item_count} brani</span>
      </button>
    `).join('');
  }

  modal.style.display = 'flex';
}

function closeAddToSetlistModal() {
  const modal = document.getElementById('add-to-setlist-modal');
  if (modal) modal.style.display = 'none';
  pendingSetlistSongUuid = null;
}

async function addSongToSpecificSetlist(setlistUuid, songUuid) {
  try {
    const res = await fetch(`${API_BASE}/api/setlists/${setlistUuid}/songs/${songUuid}?user_email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name)}`, {
      method: 'POST'
    });
    if (res.ok) {
      const data = await res.json();
      showToast(`✓ "${data.song_title}" aggiunto a "${data.setlist_title}"!`);
      closeAddToSetlistModal();
      loadSetlists();
    } else {
      showToast('Errore durante l\'aggiunta alla scaletta');
    }
  } catch (err) {
    console.error('Error adding to setlist:', err);
    showToast('Errore di connessione');
  }
}

async function createSetlistAndAddCurrentSong() {
  const input = document.getElementById('quick-new-setlist-title');
  const title = input ? input.value.trim() : '';
  if (!title) {
    showToast('Inserisci il titolo della nuova scaletta');
    if (input) input.focus();
    return;
  }
  if (!pendingSetlistSongUuid) return;

  try {
    const todayStr = new Date().toISOString().split('T')[0];
    const res = await fetch(`${API_BASE}/api/setlists`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: title,
        date: todayStr,
        items: [{ song_uuid: pendingSetlistSongUuid }],
        user_email: state.currentUser.email,
        user_name: state.currentUser.name
      })
    });
    if (res.ok) {
      const data = await res.json();
      showToast(`✓ Scaletta "${title}" creata con il brano!`);
      if (input) input.value = '';
      closeAddToSetlistModal();
      loadSetlists();
    }
  } catch (err) {
    console.error('Error creating setlist with song:', err);
  }
}

// ----------------------------------------------------------------------------
// PROMOTE SONG TO OFFICIAL BAND REPERTOIRE
// ----------------------------------------------------------------------------
async function promoteSongToOfficial(songUuid) {
  try {
    const res = await fetch(`${API_BASE}/api/repertoires/promote-song`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        song_uuid: songUuid,
        user_email: state.currentUser.email,
        user_name: state.currentUser.name
      })
    });
    if (res.ok) {
      const data = await res.json();
      showToast(`⭐ "${data.song_title}" aggiunto al Repertorio Ufficiale Band!`);
      await loadRepertoires();
      if (state.selectedSong) {
        selectSong(state.selectedSong.uuid);
      }
    } else {
      showToast('Impossibile promuovere il brano');
    }
  } catch (err) {
    console.error('Error promoting song:', err);
  }
}

// ----------------------------------------------------------------------------
// PROTECTED DELETE WITH IMMEDIATE UNDO
// ----------------------------------------------------------------------------
let lastDeletedSong = null;

async function deleteSongWithUndo(uuid) {
  const song = (state.songs || []).find(s => s.uuid === uuid) || state.selectedSong;
  if (!song) return;

  if (!confirm(`Vuoi spostare "${song.title}" nel cestino protetto? Potrai ripristinarlo in qualsiasi momento.`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/songs/${uuid}?user_email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name)}`, {
      method: 'DELETE'
    });
    if (res.ok) {
      lastDeletedSong = { uuid: song.uuid, title: song.title };
      showToast(`🗑️ "${song.title}" spostato nel cestino`);
      showSongUndoBanner(song.title);
      await loadSongs();
      await loadRepertoires();
    } else {
      showToast('Errore durante l\'eliminazione');
    }
  } catch (err) {
    console.error('Error deleting song:', err);
  }
}

function showSongUndoBanner(title) {
  const banner = document.getElementById('song-undo-banner');
  const txt = document.getElementById('song-undo-text');
  if (banner && txt) {
    txt.innerHTML = `⚠️ Brano <b>"${escapeHtml(title)}"</b> eliminato.`;
    banner.style.display = 'flex';
  }
}

async function undoDeleteSong() {
  if (!lastDeletedSong) return;
  try {
    const res = await fetch(`${API_BASE}/api/songs/${lastDeletedSong.uuid}/restore?user_email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name)}`, {
      method: 'POST'
    });
    if (res.ok) {
      const data = await res.json();
      showToast(`↩️ Brano "${data.song.title}" ripristinato con successo!`);
      const banner = document.getElementById('song-undo-banner');
      if (banner) banner.style.display = 'none';
      const restoredUuid = lastDeletedSong.uuid;
      lastDeletedSong = null;
      await loadSongs();
      await loadRepertoires();
      selectSong(restoredUuid);
    } else {
      showToast('Impossibile ripristinare il brano');
    }
  } catch (err) {
    console.error('Error restoring song:', err);
  }
}

// ----------------------------------------------------------------------------
// FORK SONG TO PERSONAL REPERTOIRE (Independent Copy)
// ----------------------------------------------------------------------------
async function forkSongToPersonal(uuid) {
  const song = (state.songs || []).find(s => s.uuid === uuid) || state.selectedSong;
  if (!song) return;

  if (!confirm(`Vuoi creare una copia personale indipendente di "${song.title}" nel tuo repertorio?\nPotrai modificarla liberamente senza alterare il brano comune della band.`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/songs/${uuid}/fork-personal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_email: state.currentUser.email,
        user_name: state.currentUser.name
      })
    });
    if (res.ok) {
      const data = await res.json();
      showToast(`✓ Copia personale creata in "${data.target_repertoire_name}"!`);
      await loadRepertoires();
      await loadSongs();
      if (data.cloned_song && data.cloned_song.uuid) {
        selectSong(data.cloned_song.uuid);
      }
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore durante la creazione della copia personale');
    }
  } catch (err) {
    console.error('Error forking song:', err);
    showToast('Errore di connessione');
  }
}

// ----------------------------------------------------------------------------
// ADMIN REPERTOIRES MANAGEMENT (Add / Rename / Delete)
// ----------------------------------------------------------------------------
function openAdminRepertoiresModal() {
  const modal = document.getElementById('admin-repertoires-modal');
  if (!modal) return;
  renderAdminRepertoiresList();
  modal.style.display = 'flex';
}

function closeAdminRepertoiresModal() {
  const modal = document.getElementById('admin-repertoires-modal');
  if (modal) modal.style.display = 'none';
}

function renderAdminRepertoiresList() {
  const container = document.getElementById('admin-repertoires-list');
  if (!container) return;

  container.innerHTML = state.repertoires.map(r => {
    const isOff = r.is_official;
    const badge = isOff ? '<span class="badge" style="background:#ffd600; color:#000; font-weight:800;">🌟 UFFICIALE BAND</span>' : (r.owner_email ? `<span class="badge" style="background:#0284c7; color:#fff;">👤 ${escapeHtml(r.owner_email)}</span>` : '<span class="badge">📁 Custom</span>');
    const deleteBtn = isOff ? '<span style="font-size:11px; color:#94a3b8; font-style:italic;">Protetto</span>' : `<button class="btn btn-danger" style="min-height:30px; padding:2px 8px; font-size:11px;" onclick="adminDeleteRepertoire('${r.uuid}', '${escapeHtml(r.name)}')">🗑️</button>`;

    return `
      <div style="background:var(--bg-surface); border:1px solid var(--border-color); border-radius:8px; padding:10px 12px; display:flex; justify-content:space-between; align-items:center; gap:8px;">
        <div style="flex:1; min-width:0;">
          <div style="display:flex; gap:6px; align-items:center;">
            <b style="color:#fff; font-size:14px;">${escapeHtml(r.name)}</b>
            ${badge}
          </div>
          <div style="font-size:11.5px; color:#94a3b8; margin-top:2px;">${escapeHtml(r.description || 'Nessuna descrizione')} &bull; ${r.song_count} brani</div>
        </div>
        <div style="display:flex; gap:6px; align-items:center;">
          <button class="btn btn-secondary" style="min-height:30px; padding:2px 8px; font-size:11px;" onclick="adminRenameRepertoire('${r.uuid}', '${escapeHtml(r.name)}')">✏️</button>
          ${deleteBtn}
        </div>
      </div>
    `;
  }).join('');
}

async function adminCreateRepertoire() {
  const nameInput = document.getElementById('admin-new-rep-name');
  const descInput = document.getElementById('admin-new-rep-desc');
  const name = nameInput ? nameInput.value.trim() : '';
  const desc = descInput ? descInput.value.trim() : '';

  if (!name) {
    showToast('Inserisci un nome per il repertorio');
    if (nameInput) nameInput.focus();
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/repertoires`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        description: desc,
        is_official: false,
        user_email: state.currentUser.email,
        user_name: state.currentUser.name
      })
    });
    if (res.ok) {
      showToast(`✓ Repertorio "${name}" creato!`);
      if (nameInput) nameInput.value = '';
      if (descInput) descInput.value = '';
      await loadRepertoires();
      renderAdminRepertoiresList();
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore creazione repertorio');
    }
  } catch (err) {
    console.error('Error creating repertoire:', err);
  }
}

async function adminRenameRepertoire(uuid, oldName) {
  const newName = prompt(`Rinomina repertorio "${oldName}":`, oldName);
  if (!newName || newName.trim() === '' || newName.trim() === oldName) return;

  try {
    const res = await fetch(`${API_BASE}/api/repertoires`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        uuid: uuid,
        name: newName.trim(),
        user_email: state.currentUser.email,
        user_name: state.currentUser.name
      })
    });
    if (res.ok) {
      showToast(`✓ Repertorio rinominato in "${newName.trim()}"`);
      await loadRepertoires();
      renderAdminRepertoiresList();
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore rinomina');
    }
  } catch (err) {
    console.error('Error renaming repertoire:', err);
  }
}

async function adminDeleteRepertoire(uuid, name) {
  if (!confirm(`Sei sicuro di voler eliminare il repertorio "${name}"?\nI brani contenuti NON verranno cancellati, rimarranno nell'archivio.`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/repertoires/${uuid}?user_email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name)}`, {
      method: 'DELETE'
    });
    if (res.ok) {
      showToast(`🗑️ Repertorio "${name}" eliminato`);
      await loadRepertoires();
      renderAdminRepertoiresList();
    } else {
      const err = await res.json();
      showToast(err.detail || 'Impossibile eliminare il repertorio');
    }
  } catch (err) {
    console.error('Error deleting repertoire:', err);
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
