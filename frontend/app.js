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
  currentTab: 'dashboard',
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
    layout_margin_top: 10.0,
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
  await loadSetlists();
  renderDashboard();
});

function initServiceWorker() {
  if ('serviceWorker' in navigator) {
    const hadController = !!navigator.serviceWorker.controller;
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (hadController && !refreshing) {
        refreshing = true;
        window.location.reload();
      }
    });
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
  const dashEl = document.getElementById('view-dashboard');
  if (dashEl) dashEl.style.display = tabName === 'dashboard' ? 'block' : 'none';
  document.getElementById('view-songs').style.display = tabName === 'songs' ? 'block' : 'none';
  document.getElementById('view-setlists').style.display = tabName === 'setlists' ? 'block' : 'none';
  document.getElementById('view-settings').style.display = tabName === 'settings' ? 'block' : 'none';

  if (tabName === 'dashboard') {
    renderDashboard();
    loadRepertoires();
    loadSongs({ autoSelect: false });
    loadSetlists();
  } else if (tabName === 'setlists') {
    if (state.selectedSetlist && state.selectedSetlist.uuid) {
      openSetlistDetail(state.selectedSetlist.uuid);
    } else {
      const detailContainer = document.getElementById('setlist-detail-view');
      const listContainer = document.getElementById('setlists-list');
      if (detailContainer) detailContainer.style.display = 'none';
      if (listContainer) listContainer.style.display = 'block';
      loadSetlists();
    }
  } else if (tabName === 'settings') {
    loadAiSettingsStatus();
  } else if (tabName === 'songs') {
    loadRepertoires();
  }
}

function renderDashboard() {
  const userEl = document.getElementById('dash-user-name');
  if (userEl) userEl.textContent = (state.currentUser && state.currentUser.name) || 'Musicista';
  const devEl = document.getElementById('dash-device-name');
  if (devEl) devEl.textContent = state.activeDevice || 'Tablet';

  const songs = Array.isArray(state.songs) ? state.songs : [];
  const reps = Array.isArray(state.repertoires) ? state.repertoires : [];
  const setlists = Array.isArray(state.setlists) ? state.setlists : [];

  const songsStat = document.getElementById('dash-stat-songs');
  const songsSub = document.getElementById('dash-stat-songs-sub');
  const officialRep = reps.find(r => r.is_official);
  const personalRep = reps.find(r => !r.is_official && state.currentUser && r.owner_email === state.currentUser.email);
  if (songsStat) songsStat.textContent = songs.length;
  if (songsSub) {
    const offCount = officialRep ? (officialRep.song_count ?? (officialRep.song_uuids || []).length) : 0;
    const persCount = personalRep ? (personalRep.song_count ?? (personalRep.song_uuids || []).length) : 0;
    songsSub.textContent = personalRep
      ? `${offCount} Ufficiale • ${persCount} Personali`
      : `${offCount} nel Repertorio Ufficiale`;
  }

  const repsStat = document.getElementById('dash-stat-repertoires');
  const repsSub = document.getElementById('dash-stat-repertoires-sub');
  if (repsStat) repsStat.textContent = reps.length;
  if (repsSub) {
    const names = reps.slice(0, 2).map(r => r.is_official ? 'Ufficiale' : r.name).join(', ');
    repsSub.textContent = reps.length > 2 ? `${names} +${reps.length - 2}` : (names || 'Nessun repertorio');
  }

  const setlistsStat = document.getElementById('dash-stat-setlists');
  const setlistsSub = document.getElementById('dash-stat-setlists-sub');
  if (setlistsStat) setlistsStat.textContent = setlists.length;
  if (setlistsSub) {
    const totalItems = setlists.reduce((acc, s) => acc + (parseInt(s.item_count, 10) || 0), 0);
    setlistsSub.textContent = setlists.length > 0
      ? `${totalItems} brani in scaletta`
      : 'Crea la prima scaletta';
  }

  const repsListEl = document.getElementById('dash-repertoires-list');
  if (repsListEl) {
    if (reps.length === 0) {
      repsListEl.innerHTML = `<div style="color: var(--text-secondary); font-size: 12.5px; padding: 8px 4px;">Nessun repertorio disponibile.</div>`;
    } else {
      repsListEl.innerHTML = reps.map(r => {
        const icon = r.is_official ? '🌟' : (state.currentUser && r.owner_email === state.currentUser.email ? '👤' : '📁');
        const label = r.is_official
          ? escapeHtml(r.name)
          : (state.currentUser && r.owner_email === state.currentUser.email ? `Personale (${escapeHtml(r.name)})` : escapeHtml(r.name));
        const count = r.song_count ?? (r.song_uuids || []).length;
        return `
          <button type="button" class="dash-quick-item" onclick="openRepertoireFromDashboard('${r.uuid}')">
            <span>${icon} ${label}</span>
            <span class="dash-quick-badge">${count} brani</span>
          </button>
        `;
      }).join('');
    }
  }

  const setlistsListEl = document.getElementById('dash-setlists-list');
  if (setlistsListEl) {
    if (setlists.length === 0) {
      setlistsListEl.innerHTML = `<div style="color: var(--text-secondary); font-size: 12.5px; padding: 8px 4px;">Nessuna scaletta creata. Tocca "Apri Scalette" per iniziare.</div>`;
    } else {
      setlistsListEl.innerHTML = setlists.slice(0, 4).map(s => `
        <button type="button" class="dash-quick-item" onclick="openSetlistFromDashboard('${s.uuid}')">
          <span>📑 ${escapeHtml(s.title)} <small style="color: var(--text-secondary); font-weight: 500;">${escapeHtml(formatDateDDMMYYYY(s.date) || '')}</small></span>
          <span class="dash-quick-badge">${s.item_count || 0} brani</span>
        </button>
      `).join('');
    }
  }
}

function openRepertoireFromDashboard(repUuid) {
  switchTab('songs');
  selectRepertoire(repUuid);
}

function openSetlistFromDashboard(setlistUuid) {
  state.selectedSetlist = { uuid: setlistUuid };
  switchTab('setlists');
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
  root.style.setProperty('--pref-top-margin', `${p.layout_margin_top || 10}px`);

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
  const valMarginTop = document.getElementById('val-margin-top');
  if (valMarginTop) valMarginTop.textContent = p.layout_margin_top || 10;

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
  renderDashboard();
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
    state.userPrefs.layout_font_size_chords = Math.max(8, Math.min(28, (state.userPrefs.layout_font_size_chords || 13) + delta));
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

function adjustMarginTop(delta) {
  state.userPrefs.layout_margin_top = Math.max(0, Math.min(50, (state.userPrefs.layout_margin_top || 10) + delta));
  const val = document.getElementById('val-margin-top');
  if (val) val.textContent = state.userPrefs.layout_margin_top;
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
    const res = await fetch(
      `${API_BASE}/api/repertoires?user_email=${encodeURIComponent(state.currentUser.email)}&_t=${Date.now()}`,
      { cache: 'no-store' }
    );
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
      renderDashboard();
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

let _selectSongSeq = 0;

function selectRepertoire(repUuid) {
  const prevTitle = state.selectedSong && state.selectedSong.title
    ? state.selectedSong.title.trim().toUpperCase()
    : '';
  _selectSongSeq++;
  state.activeRepertoire = repUuid;
  state.isEditingSong = false;
  renderRepertoireChips();
  renderSongCards();

  const filtered = getFilteredSongs();
  if (state.selectedSong) {
    const stillInFiltered = filtered.find(s => s.uuid === state.selectedSong.uuid);
    if (!stillInFiltered) {
      state.selectedSong = null;
      renderSongViewer();
      const titleMatch = prevTitle
        ? filtered.find(s => (s.title || '').trim().toUpperCase() === prevTitle)
        : null;
      if (titleMatch) {
        selectSong(titleMatch.uuid);
      }
    }
  }
}

async function loadSongs({ autoSelect = true } = {}) {
  try {
    const sep = state.currentUser?.email ? `&` : `?`;
    const base = state.currentUser?.email
      ? `${API_BASE}/api/songs?user_email=${encodeURIComponent(state.currentUser.email)}`
      : `${API_BASE}/api/songs`;
    const url = `${base}${sep}_t=${Date.now()}`;
    const res = await fetch(url, { cache: 'no-store' });
    if (res.ok) {
      state.songs = await res.json();
      renderRepertoireChips();
      renderSongCards();
      renderDashboard();
      if (autoSelect && !state.selectedSong) {
        const filtered = getFilteredSongs();
        if (filtered.length > 0) {
          selectSong(filtered[0].uuid);
        }
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
          <span class="badge">Tonalità: ${toLatinKey(s.key_current)}</span>
          <span class="badge">${s.bpm || 120} BPM</span>
          <span class="badge">📁 ${escapeHtml(repsStr)}</span>
        </div>
      </div>
    `;
  }).join('');
}

async function selectSong(uuid) {
  const seq = ++_selectSongSeq;
  const repAtRequest = state.activeRepertoire;
  try {
    const res = await fetch(`${API_BASE}/api/songs/${uuid}?_t=${Date.now()}`, { cache: 'no-store' });
    if (res.ok) {
      const songData = await res.json();
      if (seq !== _selectSongSeq || state.activeRepertoire !== repAtRequest) {
        return;
      }
      state.isEditingSong = false;
      state.selectedSong = songData;
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

const INT_TO_ITA_MAP = {
  "C": "DO", "C#": "DO#", "DB": "REb",
  "D": "RE", "D#": "RE#", "EB": "MIb",
  "E": "MI",
  "F": "FA", "F#": "FA#", "GB": "SOLb",
  "G": "SOL", "G#": "SOL#", "AB": "LAb",
  "A": "LA", "A#": "LA#", "BB": "SIb", "B": "SI"
};

function toLatinKey(keyStr) {
  if (!keyStr) return '-';
  let s = String(keyStr).trim();
  if (!s || s === '-') return '-';
  if (s.includes('/')) {
    const parts = s.split('/');
    return `${toLatinKey(parts[0])}/${toLatinKey(parts[1])}`;
  }
  const m = s.match(/^(DO#|RE#|FA#|SOL#|LA#|REB|MIB|SOLB|LAB|SIB|DO|RE|MI|FA|SOL|LA|SI|C#|D#|F#|G#|A#|DB|EB|GB|AB|BB|[CDEFGAB])(.*)$/i);
  if (!m) return s;
  const root = m[1].toUpperCase();
  const rest = m[2];
  const latinRoot = INT_TO_ITA_MAP[root] || root;
  return `${latinRoot}${rest}`;
}

function formatDateDDMMYYYY(dateStr) {
  if (!dateStr) return '';
  const s = String(dateStr).trim();
  if (!s) return '';
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) {
    return `${m[3]}/${m[2]}/${m[1]}`;
  }
  if (/^\d{2}\/\d{2}\/\d{4}/.test(s)) {
    return s;
  }
  const d = new Date(s);
  if (!isNaN(d.getTime())) {
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  }
  return s;
}

const NON_CHORD_SECTION_TAGS = new Set([
  'INTRO', 'STROFA', 'VERSE', 'RITORNELLO', 'CHORUS', 'RIT', 'BRIDGE',
  'SPECIAL', 'SPECIALE', 'OUTRO', 'FINALE', 'STRUMENTALE', 'SOLO',
  'ASSOLO', 'CODA', 'STACCO', 'RIFF', 'NOTA', 'TAB', 'PRE-CHORUS'
]);

function transposeSingleChord(chordStr, semitones) {
  if (!chordStr || semitones === 0) return chordStr;
  let s = chordStr.trim();
  const upperS = s.toUpperCase();
  if (NON_CHORD_SECTION_TAGS.has(upperS) || Array.from(NON_CHORD_SECTION_TAGS).some(t => upperS.startsWith(t + ' ') || upperS.startsWith(t + ':'))) {
    return chordStr;
  }

  // Root note regex matching ITA or INT
  const m = s.match(/^(DO#|RE#|FA#|SOL#|LA#|REB|MIB|SOLB|LAB|SIB|DO|RE|MI|FA|SOL|LA|SI|C#|D#|F#|G#|A#|DB|EB|GB|AB|BB|[CDEFGAB])(.*)$/i);
  if (!m) return chordStr;

  let root = m[1].toUpperCase();
  const rest = m[2];

  // Validate rest is a musical chord suffix (prevent corrupting plain words)
  if (rest && !/^(m|min|minor|-|maj|major|M|\+|7\+|5\+|5-|aug|dim|dim7|°|o|sus|sus2|sus4|add|2|4|5|6|7|8|9|11|13|b5|#5|b9|#9|\/[0-9#b+-]|\/[A-G]|\/(?:SOL|DO|RE|MI|FA|LA|SI)(?:#|b)?|\s)*$/i.test(rest)) {
    return chordStr;
  }

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
  // 1. Transpose bracketed chords [CHORD]
  let out = aml.replace(/\[([^\]]+)\]/g, (match, chord) => {
    return `[${transposeSingleChord(chord, semitones)}]`;
  });
  // 2. Keep {key: ...} or {tonalita: ...} directive synchronized
  out = out.replace(/^(\{(?:key|tonalita)\s*:\s*)([^\}]+)(\})/gmi, (m, p1, k, p3) => {
    return `${p1}${transposeSingleChord(k.trim(), semitones)}${p3}`;
  });
  // 3. Transpose pipe chord-grid lines like | DO | SOL |
  out = out.split('\n').map(line => {
    const trimmed = line.trim();
    if (trimmed.includes('|') && !trimmed.includes('[') && isChordGridOrTabLine(trimmed)) {
      return line.split('|').map(seg => {
        if (!seg.trim()) return seg;
        return seg.replace(/\S+/g, tok => isMusicalChord(tok) ? transposeSingleChord(tok, semitones) : tok);
      }).join('|');
    }
    return line;
  }).join('\n');
  return out;
}

async function transposeSong(semitones) {
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
  if (state.songViewType !== 'pdf') {
    renderSongViewer();
  }
  showToast(`Tonalità: ${state.selectedSong.key_current} (${semitones > 0 ? '+' : ''}${semitones})`);

  // 2. Cloud Persistence (Turso)
  const oldUuid = state.selectedSong.uuid;
  const activeRepUuid = (state.activeRepertoire && state.activeRepertoire !== '__ALL__') ? state.activeRepertoire : null;
  try {
    const res = await fetch(`${API_BASE}/api/songs/${oldUuid}/transpose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        semitones: semitones,
        user_email: state.currentUser.email,
        user_name: state.currentUser.name,
        repertoire_uuid: activeRepUuid
      })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.song) {
        state.selectedSong = data.song;
        if (data.detached_copy || data.song.uuid !== oldUuid) {
          await loadRepertoires();
          await loadSongs();
          selectSong(data.song.uuid);
        } else if (idx !== -1) {
          state.songs[idx] = Object.assign(state.songs[idx], data.song);
        }
      }
    }
  } catch (err) {
    console.warn('Transpose sync error:', err);
  }
  if (state.songViewType === 'pdf') {
    renderSongViewer();
  }
}

function transposeSongInEditor(semitones) {
  const keyInput = document.getElementById('edit-song-key');
  const amlInput = document.getElementById('edit-song-aml');
  if (!amlInput) return;

  const currentKey = keyInput ? keyInput.value.trim() : '';
  const newKey = currentKey ? transposeSingleChord(currentKey, semitones) : '';
  if (keyInput && newKey) {
    keyInput.value = newKey;
  }

  amlInput.value = transposeAmlText(amlInput.value, semitones);

  // Sync live preview if open
  const previewPane = document.getElementById('edit-song-live-preview');
  if (previewPane && previewPane.style.display !== 'none') {
    previewPane.innerHTML = renderAmlToPreviewHtml(amlInput.value);
  }

  showToast(`Tonalità in modifica: ${newKey || (semitones > 0 ? '+' + semitones : semitones)} (${semitones > 0 ? '+' : ''}${semitones} st) — Premi Salva`);
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
  if (!container) return;
  if (state.selectedSong && state.activeRepertoire && state.activeRepertoire !== '__ALL__') {
    const activeRep = (state.repertoires || []).find(r => r.uuid === state.activeRepertoire);
    if (activeRep && Array.isArray(activeRep.song_uuids) && !activeRep.song_uuids.includes(state.selectedSong.uuid)) {
      state.selectedSong = null;
    }
  }
  if (!state.selectedSong) {
    state.isEditingSong = false;
    container.innerHTML = '';
    return;
  }

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
          <button class="btn btn-success" style="font-weight: 800; min-height: 38px; padding: 4px 14px;" onclick="saveSongEdit(false)">💾 Salva nel DB</button>
          <button class="btn btn-primary" style="font-weight: 800; min-height: 38px; padding: 4px 14px;" onclick="saveSongEdit(true)">📄 Salva & Scarica PDF</button>
          <button class="btn btn-secondary" style="min-height: 38px; padding: 4px 12px;" onclick="closeSongEditor()">✕ Annulla</button>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; margin: 12px 0;">
        <div>
          <label style="font-size: 11px; color: #94a3b8; font-weight: 700;">Titolo</label>
          <input type="text" id="edit-song-title" class="search-input" style="width: 100%; margin-top: 2px;" value="${escapeHtml(s.title)}">
        </div>
        <div>
          <label style="font-size: 11px; color: #94a3b8; font-weight: 700;">Artista</label>
          <input type="text" id="edit-song-artist" class="search-input" style="width: 100%; margin-top: 2px;" value="${escapeHtml(s.artist || '')}">
        </div>
        <div>
          <label style="font-size: 11px; color: #94a3b8; font-weight: 700;">Tonalità (Trasponi)</label>
          <div style="display: flex; gap: 4px; align-items: center; margin-top: 2px;">
            <button type="button" class="btn btn-secondary" style="min-height: 36px; padding: 0 10px; font-weight: 800; color: #ffd600;" onclick="transposeSongInEditor(-1)" title="Abbassa tonalità e tutti gli accordi di 1 semitono">♭ -1</button>
            <input type="text" id="edit-song-key" class="search-input" style="width: 100%; min-width: 50px; text-align: center; font-weight: 800; color: #ffd600;" value="${escapeHtml(s.key_current || 'C')}">
            <button type="button" class="btn btn-secondary" style="min-height: 36px; padding: 0 10px; font-weight: 800; color: #ffd600;" onclick="transposeSongInEditor(1)" title="Alza tonalità e tutti gli accordi di 1 semitono">♯ +1</button>
          </div>
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
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; flex-wrap: wrap; gap: 6px;">
          <label style="font-size: 12px; color: #94a3b8; font-weight: 700;">Testo AML (Pronto per il Palco & PDF):</label>
          <div style="display: flex; gap: 6px;">
            <button type="button" class="btn btn-secondary" style="min-height: 28px; padding: 2px 10px; font-size: 11.5px; font-weight: 800; color: #38bdf8; border-color: #38bdf8;" onclick="toggleEditorLivePreview('edit-song-aml', 'edit-song-live-preview', this)">👁️ Anteprima Live</button>
          </div>
        </div>
        <!-- QUICK CHIPS TOOLBAR -->
        <div class="quick-chips-bar" style="display: flex; flex-direction: column; gap: 6px;">
          <!-- RIGA 1: ACCORDI BASE & MODIFICATORI -->
          <div style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;">
            <span style="font-size: 10.5px; color: #94a3b8; font-weight: 800; margin-right: 4px;">Accordi:</span>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[DO]')">[DO]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[RE]')">[RE]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[MI]')">[MI]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[FA]')">[FA]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[SOL]')">[SOL]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[LA]')">[LA]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[SI]')">[SI]</button>
            <button type="button" class="quick-chip" onclick="insertModifierAtCursor('edit-song-aml', 'm')">m</button>
            <button type="button" class="quick-chip" onclick="insertModifierAtCursor('edit-song-aml', '7')">7</button>
            <button type="button" class="quick-chip" onclick="insertModifierAtCursor('edit-song-aml', 'maj7')">maj7</button>
            <button type="button" class="quick-chip" onclick="insertModifierAtCursor('edit-song-aml', '4')">4</button>
            <button type="button" class="quick-chip" onclick="insertModifierAtCursor('edit-song-aml', 'sus')">sus</button>
            <button type="button" class="quick-chip" onclick="insertModifierAtCursor('edit-song-aml', 'dim')">dim</button>
            <button type="button" class="quick-chip" onclick="insertModifierAtCursor('edit-song-aml', 'b')">b</button>
            <button type="button" class="quick-chip" onclick="insertModifierAtCursor('edit-song-aml', '#')">#</button>
            <button type="button" class="quick-chip" onclick="insertModifierAtCursor('edit-song-aml', '/')">/</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', ' | ')">|</button>
          </div>
          <!-- RIGA 2: DIRETTIVE SEZIONI, NOTE & COLONNE -->
          <div style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;">
            <span style="font-size: 10.5px; color: #94a3b8; font-weight: 800; margin-right: 4px;">Direttive:</span>
            <button type="button" class="quick-chip quick-chip-directive" onclick="insertDirectiveAtCursor('edit-song-aml', 'chorus')" title="Racchiudi o inserisci ritornello">{soc} Rit {eoc}</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="insertDirectiveAtCursor('edit-song-aml', 'verse')" title="Racchiudi o inserisci strofa">{sov} Strofa {eov}</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="insertDirectiveAtCursor('edit-song-aml', 'bridge')" title="Racchiudi o inserisci ponte/speciale">{sob} Bridge {eob}</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="insertDirectiveAtCursor('edit-song-aml', 'comment')" title="Inserisci nota o commento">{c: Commento}</button>
            <button type="button" class="quick-chip quick-chip-layout" onclick="insertDirectiveAtCursor('edit-song-aml', 'colb')" title="Interruzione colonna">{colb} Salto Colonna</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n[INTRO]\\n')">[INTRO]</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n[STROFA]\\n')">[STROFA]</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n[RITORNELLO]\\n')">[RIT]</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n[SPECIALE]\\n')">[SPECIAL]</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n[OUTRO]\\n')">[OUTRO]</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n♪ (Strumentale)\\n')">♪ Inst</button>
          </div>
        </div>
        <textarea id="edit-song-aml" class="touch-textarea" style="min-height: 340px;">${escapeHtml(s.aml_content || '')}</textarea>
        <div id="edit-song-live-preview" class="editor-preview-pane" style="display: none;"></div>
      </div>

      <div style="display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap;">
        <button class="btn btn-success" style="font-weight: 800; min-height: 42px; padding: 6px 18px;" onclick="saveSongEdit(false)">💾 Salva nel DB</button>
        <button class="btn btn-primary" style="font-weight: 800; min-height: 42px; padding: 6px 18px;" onclick="saveSongEdit(true)">📄 Salva & Scarica PDF</button>
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
    `<button class="btn btn-secondary" style="color: #ffd600; border-color: #ffd600; font-weight: 800;" onclick="promoteSongToOfficial('${s.uuid}')" title="Sposta nel Repertorio Ufficiale Band (se già presente su Ufficiale lo sovrascrive ed elimina questa copia personale)">⭐ Promuovi a Ufficiale</button>` : '';

  const headerHtml = `
    <div class="viewer-header">
      <div>
        <h2 style="font-size: 22px; font-weight: 900; color: #fff;">${escapeHtml(s.title)}</h2>
        <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
          <b>${escapeHtml(s.artist || 'Band')}</b> &bull; Tonalità: <code style="color:#ffd600; font-weight:700;">${toLatinKey(s.key_current)}</code>
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
    const url = `${API_BASE}/api/songs/${songUuid}/pdf/preview?chords=${hasChords}&device=${encodeURIComponent(state.activeDevice)}&email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name || '')}&columns=${p.layout_columns || 1}&font_size=${p.layout_font_size || 12}&font_size_chords=${p.layout_font_size_chords || 13}&margin_lateral=${p.layout_margin_lateral || 10}&margin_top=${p.layout_margin_top || 10}`;
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

async function saveSongEdit(downloadPdfAfter = false) {
  if (!state.selectedSong) return;
  const titleInput = document.getElementById('edit-song-title');
  const artistInput = document.getElementById('edit-song-artist');
  const keyInput = document.getElementById('edit-song-key');
  const bpmInput = document.getElementById('edit-song-bpm');
  const capoInput = document.getElementById('edit-song-capo');
  const amlInput = document.getElementById('edit-song-aml');

  const newKeyVal = keyInput ? keyInput.value.trim() : state.selectedSong.key_current;
  let newAmlVal = amlInput ? amlInput.value : state.selectedSong.aml_content;
  if (newKeyVal && newAmlVal) {
    newAmlVal = newAmlVal.replace(/^(\{(?:key|tonalita)\s*:\s*)([^\}]+)(\})/gmi, `$1${newKeyVal}$3`);
  }

  const oldUuid = state.selectedSong.uuid;
  const activeRepUuid = (state.activeRepertoire && state.activeRepertoire !== '__ALL__') ? state.activeRepertoire : null;
  const payload = {
    title: titleInput ? titleInput.value.trim() : state.selectedSong.title,
    artist: artistInput ? artistInput.value.trim() : state.selectedSong.artist,
    key_current: newKeyVal,
    bpm: bpmInput ? (parseInt(bpmInput.value) || 120) : state.selectedSong.bpm,
    capo: capoInput ? (parseInt(capoInput.value) || 0) : state.selectedSong.capo,
    aml_content: newAmlVal,
    user_email: state.currentUser.email,
    user_name: state.currentUser.name,
    comment: 'Modifica touch da tablet',
    repertoire_uuid: activeRepUuid
  };

  try {
    const res = await fetch(`${API_BASE}/api/songs/${oldUuid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json();
      state.selectedSong = data.song;
      if (data.detached_copy || (data.song && data.song.uuid !== oldUuid)) {
        await loadRepertoires();
        await loadSongs();
        const fresh = state.songs.find(x => x.uuid === data.song.uuid);
        if (fresh) state.selectedSong = fresh;
      } else {
        const idx = state.songs.findIndex(x => x.uuid === state.selectedSong.uuid);
        if (idx !== -1) {
          state.songs[idx] = Object.assign(state.songs[idx], state.selectedSong);
        }
      }
      state.isEditingSong = false;
      renderSongCards();
      renderSongViewer();
      showToast(`Brano "${state.selectedSong.title}" salvato nel DB ✓`);
      if (downloadPdfAfter) {
        await downloadPdf();
      }
    } else {
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || 'Errore durante il salvataggio del brano');
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

function insertModifierAtCursor(textareaId, mod) {
  const textarea = document.getElementById(textareaId);
  if (!textarea) return;

  const start = textarea.selectionStart || 0;
  const end = textarea.selectionEnd || 0;
  const val = textarea.value;

  // If cursor is right after a closing bracket like "[DO]|", insert inside the bracket -> "[DOm]|"
  if (start === end && start > 0 && val[start - 1] === ']') {
    textarea.value = val.substring(0, start - 1) + mod + ']' + val.substring(end);
    textarea.selectionStart = textarea.selectionEnd = start - 1 + mod.length + 1;
    textarea.focus();
    return;
  }

  // Normal insertion (e.g. if cursor is already inside "[DO|]" or elsewhere)
  textarea.value = val.substring(0, start) + mod + val.substring(end);
  textarea.selectionStart = textarea.selectionEnd = start + mod.length;
  textarea.focus();
}

function showNewSongForm() {
  const form = document.getElementById('new-song-form');
  if (form) {
    const repSelect = document.getElementById('new-song-repertoire');
    if (repSelect && state.repertoires && state.repertoires.length > 0) {
      repSelect.innerHTML = state.repertoires.map(r => {
        const isSelected = (state.activeRepertoire === r.uuid) || (state.activeRepertoire === '__ALL__' && (r.owner_email === state.currentUser?.email || r.is_official));
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

function insertDirectiveAtCursor(textareaId, type) {
  const textarea = document.getElementById(textareaId);
  if (!textarea) return;

  const start = textarea.selectionStart || 0;
  const end = textarea.selectionEnd || 0;
  const val = textarea.value;
  const selectedText = val.substring(start, end);

  let insertion = '';
  let cursorOffset = 0;

  switch (type) {
    case 'chorus':
      if (selectedText) {
        insertion = `{soc}\n${selectedText}\n{eoc}\n`;
      } else {
        insertion = `{soc}\n\n{eoc}\n`;
        cursorOffset = 6;
      }
      break;
    case 'verse':
      if (selectedText) {
        insertion = `{sov}\n${selectedText}\n{eov}\n`;
      } else {
        insertion = `{sov}\n\n{eov}\n`;
        cursorOffset = 6;
      }
      break;
    case 'bridge':
      if (selectedText) {
        insertion = `{sob}\n${selectedText}\n{eob}\n`;
      } else {
        insertion = `{sob}\n\n{eob}\n`;
        cursorOffset = 6;
      }
      break;
    case 'comment':
      if (selectedText) {
        insertion = `{c: ${selectedText}}\n`;
      } else {
        insertion = `{c: Nota per la band}\n`;
        cursorOffset = 4;
      }
      break;
    case 'colb':
      insertion = `\n{colb}\n`;
      break;
    default:
      insertion = `{${type}}\n`;
  }

  textarea.value = val.substring(0, start) + insertion + val.substring(end);
  const newPos = cursorOffset > 0 ? (start + cursorOffset) : (start + insertion.length);
  textarea.selectionStart = textarea.selectionEnd = newPos;
  textarea.focus();
}

function toggleEditorLivePreview(textareaId, previewId, btn) {
  const textarea = document.getElementById(textareaId);
  const preview = document.getElementById(previewId);
  if (!textarea || !preview) return;

  const isShowingPreview = preview.style.display !== 'none';
  if (isShowingPreview) {
    preview.style.display = 'none';
    textarea.style.display = 'block';
    if (btn) btn.innerHTML = '👁️ Anteprima Live';
  } else {
    const rawText = textarea.value;
    preview.innerHTML = renderAmlToPreviewHtml(rawText);
    textarea.style.display = 'none';
    preview.style.display = 'block';
    if (btn) btn.innerHTML = '✏️ Torna all\'Editor';
  }
}

function renderAmlToPreviewHtml(amlText) {
  if (!amlText || !amlText.trim()) {
    return '<div style="color: #94a3b8; font-style: italic; padding: 20px; text-align: center;">Nessun testo da visualizzare</div>';
  }
  const lines = amlText.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
  let html = '<div style="line-height: 1.8; font-family: monospace;">';
  let inChorus = false;

  for (let line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      html += '<div style="height: 12px;"></div>';
      continue;
    }
    // Directive handling
    const dirMatch = trimmed.match(/^\{([a-zA-Z0-9_-]+)(?::\s*([^\}]+))?\}$/);
    if (dirMatch) {
      const tag = dirMatch[1].toLowerCase();
      const val = dirMatch[2] || '';
      if (tag === 'soc' || tag === 'start_of_chorus') {
        inChorus = true;
        html += '<div style="border-left: 3px solid #ffd600; padding-left: 10px; margin: 8px 0; background: rgba(255, 214, 0, 0.05); border-radius: 0 4px 4px 0;">';
        html += '<div style="color: #ffd600; font-size: 11px; font-weight: 800; text-transform: uppercase;">[RITORNELLO]</div>';
        continue;
      }
      if (tag === 'eoc' || tag === 'end_of_chorus') {
        inChorus = false;
        html += '</div>';
        continue;
      }
      if (tag === 'sov' || tag === 'start_of_verse') {
        html += '<div style="border-left: 3px solid #38bdf8; padding-left: 10px; margin: 8px 0;">';
        continue;
      }
      if (tag === 'eov' || tag === 'end_of_verse') {
        html += '</div>';
        continue;
      }
      if (tag === 'c' || tag === 'comment') {
        html += `<div style="color: #e2e8f0; background: #334155; display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin: 4px 0; font-style: italic;">💬 ${escapeHtml(val)}</div>`;
        continue;
      }
      if (tag === 'colb') {
        html += '<div style="border-top: 1px dashed #a855f7; margin: 10px 0; color: #a855f7; font-size: 11px; font-weight: 700;">--- SALTO COLONNA ---</div>';
        continue;
      }
      if (['title', 't', 'artist', 'a', 'key', 'tempo', 'capo'].includes(tag)) {
        html += `<div style="font-size: 11px; color: #64748b;"><b>{${escapeHtml(tag)}:</b> ${escapeHtml(val)}<b>}</b></div>`;
        continue;
      }
    }

    // Section headings like [INTRO], [RITORNELLO]
    if (trimmed.startsWith('[') && trimmed.endsWith(']') && !trimmed.slice(1, -1).includes('[')) {
      const inner = trimmed.slice(1, -1).trim();
      const isChord = /^[A-G][b#]?(?:m|maj|min|dim|aug|sus|add|\d)*$/i.test(inner) ||
                      /^(?:DO|RE|MI|FA|SOL|LA|SI)[b#]?(?:m|maj|min|dim|aug|sus|add|\d)*$/i.test(inner);
      if (!isChord) {
        html += `<div style="color: #f59e0b; font-weight: 800; font-size: 12px; margin-top: 6px; text-transform: uppercase;">${escapeHtml(trimmed)}</div>`;
        continue;
      }
    }

    // Line with inline chords [DO]Parola
    let renderedLine = escapeHtml(line);
    renderedLine = renderedLine.replace(/\[([^\]]+)\]/g, '<span style="color: #ff5252; font-weight: 800; background: rgba(255, 82, 82, 0.12); padding: 1px 4px; border-radius: 3px; margin: 0 1px;">$1</span>');
    html += `<div>${renderedLine}</div>`;
  }

  if (inChorus) html += '</div>';
  html += '</div>';
  return html;
}

// State for camera/vision multi-page import
state.cameraImages = [];

function handleCameraFilesSelected(event) {
  const files = event.target.files;
  if (!files || files.length === 0) return;

  const filesArray = Array.from(files);
  let loadedCount = 0;

  filesArray.forEach(file => {
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      const mime = file.type || 'image/jpeg';
      state.cameraImages.push({
        data: dataUrl,
        mime_type: mime,
        rotation: 0
      });
      loadedCount++;
      if (loadedCount === filesArray.length) {
        renderCameraThumbnails();
      }
    };
    reader.readAsDataURL(file);
  });
  event.target.value = '';
}

function renderCameraThumbnails() {
  const container = document.getElementById('camera-thumbnails-container');
  const btnRun = document.getElementById('btn-run-vision');
  const btnClear = document.getElementById('btn-clear-camera');

  if (!container) return;

  if (state.cameraImages.length === 0) {
    container.innerHTML = '';
    if (btnRun) btnRun.style.display = 'none';
    if (btnClear) btnClear.style.display = 'none';
    return;
  }

  if (btnRun) btnRun.style.display = 'inline-block';
  if (btnClear) btnClear.style.display = 'inline-block';

  container.innerHTML = state.cameraImages.map((img, idx) => `
    <div class="camera-thumb-card" id="camera-thumb-${idx}">
      <img src="${img.data}" class="camera-thumb-img" style="transform: rotate(${img.rotation || 0}deg);" alt="Pagina ${idx + 1}">
      <div class="camera-thumb-badge">Pag. ${idx + 1}</div>
      <div class="camera-thumb-actions">
        <button type="button" class="camera-thumb-btn" onclick="rotateCameraImage(${idx})" title="Ruota di 90°">🔄</button>
        <button type="button" class="camera-thumb-btn" style="color: #ef4444;" onclick="removeCameraImage(${idx})" title="Rimuovi pagina">✕</button>
      </div>
    </div>
  `).join('');
}

function rotateCameraImage(index) {
  if (!state.cameraImages[index]) return;
  state.cameraImages[index].rotation = ((state.cameraImages[index].rotation || 0) + 90) % 360;
  renderCameraThumbnails();
}

function removeCameraImage(index) {
  state.cameraImages.splice(index, 1);
  renderCameraThumbnails();
}

function clearCameraImages() {
  state.cameraImages = [];
  renderCameraThumbnails();
}

function compressAndOrientImage(dataUrl, rotationDeg = 0, maxWidth = 1600, maxHeight = 1600) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      try {
        let width = img.naturalWidth || img.width;
        let height = img.naturalHeight || img.height;

        // Scale down if larger than max bounds to guarantee light and fast payload
        if (width > maxWidth || height > maxHeight) {
          const ratio = Math.min(maxWidth / width, maxHeight / height);
          width = Math.round(width * ratio);
          height = Math.round(height * ratio);
        }

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const normalizedRot = ((rotationDeg % 360) + 360) % 360;
        const isSwapped = (normalizedRot === 90 || normalizedRot === 270);

        canvas.width = isSwapped ? height : width;
        canvas.height = isSwapped ? width : height;

        ctx.translate(canvas.width / 2, canvas.height / 2);
        ctx.rotate((normalizedRot * Math.PI) / 180);
        ctx.drawImage(img, -width / 2, -height / 2, width, height);

        const outData = canvas.toDataURL('image/jpeg', 0.82);
        resolve({ data: outData, mime_type: 'image/jpeg' });
      } catch (err) {
        console.warn('Canvas optimization fallback:', err);
        resolve({ data: dataUrl, mime_type: 'image/jpeg' });
      }
    };
    img.onerror = () => resolve({ data: dataUrl, mime_type: 'image/jpeg' });
    img.src = dataUrl;
  });
}

async function executeVisionTranscription() {
  if (!state.cameraImages || state.cameraImages.length === 0) {
    showToast('Scatta o seleziona almeno una foto');
    return;
  }

  const btnRun = document.getElementById('btn-run-vision');
  const statusDiv = document.getElementById('camera-vision-status');

  if (btnRun) btnRun.disabled = true;
  if (statusDiv) {
    statusDiv.style.display = 'block';
    statusDiv.innerHTML = `⏳ Ottimizzazione e analisi di ${state.cameraImages.length} pagina/e con Gemini Vision AI... attendi qualche secondo.`;
  }

  try {
    // Process, compress and bake rotation for each page before sending
    const processedImages = await Promise.all(
      state.cameraImages.map(img => compressAndOrientImage(img.data, img.rotation || 0, 1600, 1600))
    );

    const payload = {
      images: processedImages,
      user_email: state.currentUser ? state.currentUser.email : 'cico@band.org',
      user_name: state.currentUser ? state.currentUser.name : 'Cico'
    };

    const res = await fetch(`${API_BASE}/api/songs/import-vision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      if (data.title) {
        const titleField = document.getElementById('new-song-title');
        if (titleField) titleField.value = data.title;
      }
      if (data.artist) {
        const artistField = document.getElementById('new-song-artist');
        if (artistField) artistField.value = data.artist;
      }
      if (data.key) {
        const keyField = document.getElementById('new-song-key');
        if (keyField) keyField.value = data.key;
      }
      if (data.bpm) {
        const bpmField = document.getElementById('new-song-bpm');
        if (bpmField) bpmField.value = data.bpm;
      }
      if (data.capo !== undefined) {
        const capoField = document.getElementById('new-song-capo');
        if (capoField) capoField.value = data.capo;
      }
      if (data.aml) {
        const amlField = document.getElementById('new-song-aml');
        if (amlField) {
          amlField.value = data.aml;
          amlField.focus();
        }
      }

      showToast(`Brano "${data.title || 'Digitalizzato'}" trascritto con successo da Vision AI! ✓`);
      switchImportTab('manual');
    } else {
      const err = await res.json();
      showToast(`Errore Vision AI: ${err.detail || 'Impossibile trascrivere'}`);
    }
  } catch (err) {
    console.error('Vision transcription error:', err);
    showToast('Errore di connessione durante la trascrizione');
  } finally {
    if (btnRun) btnRun.disabled = false;
    if (statusDiv) statusDiv.style.display = 'none';
  }
}

function switchImportTab(tab) {
  const btnWeb = document.getElementById('btn-import-tab-web');
  const btnCamera = document.getElementById('btn-import-tab-camera');
  const btnPaste = document.getElementById('btn-import-tab-paste');
  const btnUrl = document.getElementById('btn-import-tab-url');
  const btnManual = document.getElementById('btn-import-tab-manual');

  if (btnWeb) btnWeb.classList.toggle('active', tab === 'web');
  if (btnCamera) btnCamera.classList.toggle('active', tab === 'camera');
  if (btnPaste) btnPaste.classList.toggle('active', tab === 'paste');
  if (btnUrl) btnUrl.classList.toggle('active', tab === 'url');
  if (btnManual) btnManual.classList.toggle('active', tab === 'manual');

  const paneWeb = document.getElementById('import-pane-web');
  const paneCamera = document.getElementById('import-pane-camera');
  const panePaste = document.getElementById('import-pane-paste');
  const paneUrl = document.getElementById('import-pane-url');

  if (paneWeb) paneWeb.style.display = tab === 'web' ? 'block' : 'none';
  if (paneCamera) paneCamera.style.display = tab === 'camera' ? 'block' : 'none';
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

function formatChordLyricLine(line) {
  const regex = /\[([^\]]+)\]/g;
  let match;
  let lastIndex = 0;
  const segments = [];

  while ((match = regex.exec(line)) !== null) {
    const textBefore = line.slice(lastIndex, match.index);
    if (textBefore || segments.length === 0) {
      if (segments.length === 0 && textBefore) {
        segments.push({ chord: '', text: textBefore });
      } else if (segments.length > 0 && !segments[segments.length - 1].text) {
        segments[segments.length - 1].text = textBefore;
      } else if (textBefore) {
        segments.push({ chord: '', text: textBefore });
      }
    }
    const chordText = match[1].trim();
    segments.push({ chord: chordText, text: '' });
    lastIndex = regex.lastIndex;
  }
  const remainingText = line.slice(lastIndex);
  if (segments.length > 0) {
    segments[segments.length - 1].text += remainingText;
  } else {
    segments.push({ chord: '', text: remainingText });
  }

  let chordHtml = '';
  let lyricHtml = '';
  let hasChords = false;

  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    const c = seg.chord;
    const t = seg.text;

    if (!c && !t) continue;

    if (!c) {
      chordHtml += escapeHtml(' '.repeat(t.length));
      lyricHtml += escapeHtml(t);
    } else {
      hasChords = true;
      const hasFollowingChord = segments.slice(i + 1).some(s => s.chord);
      let targetLen;
      if (hasFollowingChord && t.length <= c.length) {
        const gap = 1;
        targetLen = c.length + gap;
      } else {
        targetLen = Math.max(c.length, t.length);
      }
      chordHtml += `<span class="chord-token">${escapeHtml(c)}</span>` + escapeHtml(' '.repeat(targetLen - c.length));
      lyricHtml += escapeHtml(t.padEnd(targetLen, ' '));
    }
  }

  return {
    hasChords,
    chordHtml: chordHtml.replace(/\s+$/, ''),
    lyricHtml: lyricHtml.replace(/\s+$/, '')
  };
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

    // 1. Detect Directives ({tag} or {tag: value})
    const dirMatch = trimmed.match(/^\{([a-zA-Z0-9_-]+)(?::\s*([^\}]+))?\}$/);
    if (dirMatch) {
      const tag = dirMatch[1].toLowerCase();
      const val = dirMatch[2] ? dirMatch[2].trim() : '';

      // Skip metadata directives already displayed in the main song header
      if (['title', 't', 'artist', 'a', 'key', 'tempo', 'bpm', 'capo', 'time'].includes(tag)) {
        continue;
      }

      // Comments / band notes: {c: ...} or {comment: ...}
      if (['c', 'comment', 'ci', 'cb'].includes(tag)) {
        html += `<div style="margin: 6px 0; color: #38bdf8; background: rgba(56, 189, 248, 0.12); border-left: 3px solid #38bdf8; padding: 4px 10px; border-radius: 0 4px 4px 0; font-style: italic; font-size: 13px;">💬 <b>[NOTA]:</b> ${escapeHtml(val || 'Nota')}</div>`;
        continue;
      }

      // Column break: {colb}
      if (['colb', 'column_break', 'col_break'].includes(tag)) {
        html += `<div style="break-before: column; border-top: 1px dashed #a855f7; margin: 12px 0; color: #a855f7; font-size: 11px; font-weight: 700; padding-top: 4px;">--- SALTO COLONNA ---</div>`;
        continue;
      }

      // Section open directives
      let secName = null;
      if (['soc', 'start_of_chorus', 'chorus', 'ritornello'].includes(tag)) {
        secName = val ? val.toUpperCase() : 'RITORNELLO';
      } else if (['sov', 'start_of_verse', 'verse', 'strofa'].includes(tag)) {
        secName = val ? val.toUpperCase() : 'STROFA';
      } else if (['sob', 'start_of_bridge', 'bridge', 'speciale'].includes(tag)) {
        secName = val ? val.toUpperCase() : 'SPECIALE';
      }

      if (secName) {
        if (inSection) html += '</div>';
        const isChorus = secName.includes('RITORNELLO') || secName.includes('CHORUS');
        const borderColor = isChorus ? '#ffd600' : 'var(--accent-cyan)';
        const bgTint = isChorus ? 'background: rgba(255, 214, 0, 0.06); border-left: 3px solid #ffd600; padding-left: 10px; border-radius: 0 6px 6px 0;' : '';
        html += `<div class="aml-section" style="${bgTint}"><div class="aml-tag-header" style="color: ${borderColor}; font-weight: 900;">[${escapeHtml(secName)}]</div>`;
        inSection = true;
        lastWasInstrumental = false;
        continue;
      }

      // Section close directives
      if (['eoc', 'end_of_chorus', 'eov', 'end_of_verse', 'eob', 'end_of_bridge'].includes(tag)) {
        if (inSection) {
          html += '</div>';
          inSection = false;
        }
        continue;
      }

      if (val) {
        html += `<div style="font-size: 11.5px; color: #94a3b8; margin: 4px 0;"><b>[${escapeHtml(tag.toUpperCase())}]:</b> ${escapeHtml(val)}</div>`;
      }
      continue;
    }

    // 2. Detect Bracketed / Colon Section Header ([INTRO], [STROFA], Intro:, etc.)
    let sectionTitle = null;
    if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
      const candidate = trimmed.slice(1, -1).toUpperCase();
      const standardSections = ['INTRO', 'STROFA', 'VERSE', 'RITORNELLO', 'CHORUS', 'BRIDGE', 'SPECIAL', 'OUTRO', 'FINALE', 'STRUMENTALE', 'SOLO', 'CODA', 'STACCO', 'RIFF'];
      if (standardSections.some(s => candidate.startsWith(s) || candidate.includes(s))) {
        sectionTitle = candidate;
      }
    } else if (trimmed.endsWith(':') && trimmed.length < 35 && !trimmed.includes('[')) {
      sectionTitle = trimmed.slice(0, -1).toUpperCase();
    }

    if (sectionTitle) {
      if (inSection) html += '</div>';
      html += `<div class="aml-section"><div class="aml-tag-header">[${escapeHtml(sectionTitle)}]</div>`;
      inSection = true;
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

    // 3. Render Line (chords above lyrics, without [ ] brackets)
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
      if (hasChordTokens) {
        const formatted = formatChordLyricLine(line);
        if (formatted.chordHtml && formatted.chordHtml.trim()) {
          html += `<div class="aml-chord-line">${formatted.chordHtml}</div>`;
        }
        if (formatted.lyricHtml && formatted.lyricHtml.trim()) {
          html += `<div class="aml-lyric-line">${formatted.lyricHtml}</div>`;
        }
      } else {
        html += `<div class="aml-lyric-line">${escapeHtml(line)}</div>`;
      }
      lastWasInstrumental = false;
    }
  }

  if (inSection) html += '</div>';
  return html;
}

async function downloadPdf() {
  if (!state.selectedSong) return;
  const chordsParam = state.scoreMode === 'chords' ? 'true' : 'false';
  const cleanTitle = (state.selectedSong.title || 'brano').replace(/[^a-zA-Z0-9_\-]/g, '_');
  const filename = `${cleanTitle}.pdf`;
  const url = `${API_BASE}/api/songs/${state.selectedSong.uuid}/pdf?chords=${chordsParam}&device=${encodeURIComponent(state.activeDevice)}&email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name || '')}&download=true`;

  showToast(`Scaricamento "${filename}" in corso...`);
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
    }, 2000);
    showToast(`PDF salvato: ${filename} ✓`);
  } catch (err) {
    console.warn('Blob download fallback:', err);
    window.location.href = url;
  }
}

async function printDirectA4(url) {
  showToast('Invio alla coda di stampa in corso...');

  let printFrame = document.getElementById('asma-direct-print-frame');
  if (!printFrame) {
    printFrame = document.createElement('iframe');
    printFrame.id = 'asma-direct-print-frame';
    printFrame.style.position = 'fixed';
    printFrame.style.right = '0';
    printFrame.style.bottom = '0';
    printFrame.style.width = '0';
    printFrame.style.height = '0';
    printFrame.style.border = '0';
    printFrame.style.visibility = 'hidden';
    document.body.appendChild(printFrame);
  }

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);

    printFrame.src = blobUrl;
    printFrame.onload = () => {
      setTimeout(() => {
        try {
          printFrame.contentWindow.focus();
          printFrame.contentWindow.print();
        } catch (e) {
          const w = window.open(url, '_blank');
          if (w) {
            w.focus();
            try { w.print(); } catch (err) {}
          }
        }
      }, 350);
    };
  } catch (err) {
    console.warn('Iframe print fallback:', err);
    const win = window.open(url, '_blank');
    if (win) win.focus();
  }
}

function printA4() {
  if (!state.selectedSong) return;
  const p = state.userPrefs || {};
  const hasChords = state.scoreMode === 'chords';
  const url = `${API_BASE}/api/songs/${state.selectedSong.uuid}/pdf?chords=${hasChords}&device=${encodeURIComponent(state.activeDevice)}&email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name || '')}&columns=${p.layout_columns || 1}&font_size=${p.layout_font_size || 12}&font_size_chords=${p.layout_font_size_chords || 13}&margin_lateral=${p.layout_margin_lateral || 10}&margin_top=${p.layout_margin_top || 10}&a4=true&autoprint=true`;
  printDirectA4(url);
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
  document.getElementById('stage-song-meta').textContent = `${currentSong.artist} • Tonalità: ${toLatinKey(currentSong.key_current)} • ${currentSong.bpm || 120} BPM • Capo: ${currentSong.capo || 0}°`;

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
      const url = `${API_BASE}/api/songs/${currentSong.uuid}/pdf/preview?chords=${hasChords}&device=${encodeURIComponent(state.activeDevice)}&email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name || '')}&columns=${p.layout_columns || 1}&font_size=${p.layout_font_size || 12}&font_size_chords=${p.layout_font_size_chords || 13}&margin_lateral=${p.layout_margin_lateral || 10}&margin_top=${p.layout_margin_top || 10}`;
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
    try {
      const savedStageSize = localStorage.getItem('asma_stage_font_size');
      if (savedStageSize) {
        container.style.fontSize = `${savedStageSize}px`;
      }
    } catch (e) {}
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

async function adjustStageFontSize(delta) {
  const container = document.getElementById('stage-lyrics');
  if (state.stageViewType === 'pdf') {
    const step = delta > 0 ? 1 : -1;
    state.userPrefs.layout_font_size = Math.max(8, Math.min(28, (state.userPrefs.layout_font_size || 12) + step));
    state.userPrefs.layout_font_size_chords = Math.max(8, Math.min(28, (state.userPrefs.layout_font_size_chords || 13) + step));
    updateSettingsFormValues();
    applyPreferences();
    autosaveUserPreferences();
    showToast(`Font Spartito PDF: Testo ${state.userPrefs.layout_font_size}pt • Accordi ${state.userPrefs.layout_font_size_chords}pt`);
    const currentSong = state.stageSongs[state.stageIndex];
    if (currentSong) {
      await renderStageSong(currentSong);
    }
  } else {
    if (container) {
      const currentSize = parseFloat(window.getComputedStyle(container).fontSize) || 22;
      const newSize = Math.max(14, Math.min(48, currentSize + delta));
      container.style.fontSize = `${newSize}px`;
      try { localStorage.setItem('asma_stage_font_size', String(newSize)); } catch (e) {}
      showToast(`Teleprompter: Testo e Accordi ${newSize}px`);
    }
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
    const res = await fetch(`${API_BASE}/api/setlists?_t=${Date.now()}`, { cache: 'no-store' });
    if (res.ok) {
      state.setlists = await res.json();
      renderSetlists();
      renderDashboard();
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
          <div class="song-card-artist">${escapeHtml(formatDateDDMMYYYY(s.date) || 'Data da definire')} &bull; ${escapeHtml(s.description || 'Scaletta Concerto')}</div>
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

async function downloadSetlistPdf(uuid) {
  const chordsParam = state.scoreMode === 'chords' ? 'true' : 'false';
  const filename = 'SCALETTA_LIVE.pdf';
  const url = `${API_BASE}/api/setlists/${uuid}/pdf?chords=${chordsParam}&device=${encodeURIComponent(state.activeDevice)}&email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name || '')}&download=true`;

  showToast(`Scaricamento "${filename}" in corso...`);
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
    }, 2000);
    showToast(`PDF scaletta salvato: ${filename} ✓`);
  } catch (err) {
    console.warn('Blob setlist download fallback:', err);
    window.location.href = url;
  }
}

function printSetlistA4(uuid) {
  const p = state.userPrefs || {};
  const hasChords = state.scoreMode === 'chords';
  const url = `${API_BASE}/api/setlists/${uuid}/pdf?chords=${hasChords}&device=${encodeURIComponent(state.activeDevice)}&email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name || '')}&columns=${p.layout_columns || 1}&font_size=${p.layout_font_size || 12}&font_size_chords=${p.layout_font_size_chords || 13}&margin_lateral=${p.layout_margin_lateral || 10}&margin_top=${p.layout_margin_top || 10}&a4=true&autoprint=true`;
  printDirectA4(url);
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
  state.selectedSetlist = null;
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
          ${escapeHtml(item.artist || '')} &bull; Tonalità: <b style="color:#ffd600;">${toLatinKey(item.key)}</b>
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
    `<option value="${song.uuid}">${escapeHtml(song.title)} (${escapeHtml(song.artist || 'Band')}) [Tonalità: ${escapeHtml(toLatinKey(song.key_current))}]</option>`
  ).join('');

  container.innerHTML = `
    <div class="song-viewer" style="margin-bottom:14px;">
      <div class="viewer-header">
        <div>
          <h2 style="font-size: 22px; font-weight: 900; color: #fff;">📑 ${escapeHtml(s.title)}</h2>
          <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
            <b>${escapeHtml(formatDateDDMMYYYY(s.date) || '')}</b> &bull; ${escapeHtml(s.description || '')} &bull; Durata: <b>${minutes} min</b> (${s.total_songs || s.items.length} brani)
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
      const idx = (state.setlists || []).findIndex(x => x.uuid === s.uuid);
      if (idx !== -1) {
        state.setlists[idx].item_count = (s.items || []).length;
        state.setlists[idx].title = s.title;
        state.setlists[idx].date = s.date;
      }
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
    const res = await fetch(`${API_BASE}/api/setlists?_t=${Date.now()}`, { cache: 'no-store' });
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
      await loadSetlists();
      if (state.selectedSetlist && state.selectedSetlist.uuid === setlistUuid) {
        await openSetlistDetail(setlistUuid);
      }
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
  const songObj = (state.songs || []).find(s => s.uuid === songUuid) || state.selectedSong;
  const officialRep = (state.repertoires || []).find(r => r.is_official);
  const cleanTitle = songObj && songObj.title ? songObj.title.trim().toUpperCase() : '';
  const existsInOfficialByTitle = !!(officialRep && cleanTitle && (officialRep.song_uuids || []).some(uid => {
    if (uid === songUuid) return false;
    const os = (state.songs || []).find(x => x.uuid === uid);
    return os && os.title && os.title.trim().toUpperCase() === cleanTitle;
  }));

  const confirmMsg = existsInOfficialByTitle
    ? `Il brano "${songObj.title}" è già presente nel Repertorio Ufficiale.\nPromuovendolo, la versione ufficiale verrà SOVRASCRITTA e questa copia personale verrà eliminata.\n(Potrai sempre ricreare una copia personale dall'ufficiale in seguito.)\n\nProcedere?`
    : `Vuoi spostare "${songObj ? songObj.title : 'questo brano'}" dal tuo repertorio personale al Repertorio Ufficiale Band?`;
  if (!confirm(confirmMsg)) return;

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
      if (data.action === 'overwritten') {
        showToast(`⭐ "${data.song_title}" sovrascritto nel Repertorio Ufficiale! Copia personale rimossa.`);
      } else {
        showToast(`⭐ "${data.song_title}" spostato nel Repertorio Ufficiale Band!`);
      }
      const targetUuid = data.song_uuid || songUuid;
      // Immediate optimistic repertoire count update so chips reflect the change at 0ms
      if (Array.isArray(state.repertoires)) {
        state.repertoires.forEach(r => {
          if (!r.is_official && Array.isArray(r.song_uuids) && r.song_uuids.includes(songUuid)) {
            r.song_uuids = r.song_uuids.filter(uid => uid !== songUuid);
            r.song_count = r.song_uuids.length;
          } else if (r.is_official && data.action === 'moved' && Array.isArray(r.song_uuids) && !r.song_uuids.includes(targetUuid)) {
            r.song_uuids.push(targetUuid);
            r.song_count = r.song_uuids.length;
          }
        });
        renderRepertoireChips();
      }
      state.isEditingSong = false;
      state.selectedSong = null;
      renderSongViewer();
      await loadRepertoires();
      await loadSongs({ autoSelect: false });
      const inCurrentFilter = (typeof getFilteredSongs === 'function' ? getFilteredSongs() : state.songs || [])
        .some(x => x.uuid === targetUuid);
      if (inCurrentFilter) {
        selectSong(targetUuid);
      } else {
        state.isEditingSong = false;
        state.selectedSong = null;
        renderRepertoireChips();
        renderSongCards();
        renderSongViewer();
      }
    } else {
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || 'Impossibile promuovere il brano');
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
    const activeRepParam = (state.activeRepertoire && state.activeRepertoire !== '__ALL__')
      ? `&repertoire_uuid=${encodeURIComponent(state.activeRepertoire)}`
      : '';
    const res = await fetch(`${API_BASE}/api/songs/${uuid}?user_email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name)}${activeRepParam}`, {
      method: 'DELETE'
    });
    if (res.ok) {
      const delData = await res.json().catch(() => ({}));
      if (delData.detached_only) {
        showToast(`🗑️ "${song.title}" rimosso da questo repertorio`);
      } else {
        lastDeletedSong = { uuid: song.uuid, title: song.title };
        showToast(`🗑️ "${song.title}" spostato nel cestino`);
        showSongUndoBanner(song.title);
      }
      if (state.selectedSong && state.selectedSong.uuid === uuid) {
        state.isEditingSong = false;
        state.selectedSong = null;
      }
      await loadRepertoires();
      await loadSongs({ autoSelect: false });
      renderRepertoireChips();
      renderSongCards();
      renderDashboard();
      renderSongViewer();
    } else {
      showToast('Errore durante l\'eliminazione');
    }
  } catch (err) {
    console.error('Error deleting song:', err);
  }
}

function showSongUndoBanner(title) {
  // Banner eliminato su richiesta utente
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
      await loadRepertoires();
      await loadSongs({ autoSelect: false });
      renderRepertoireChips();
      renderSongCards();
      renderDashboard();
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
      if (data.target_repertoire_uuid) {
        state.activeRepertoire = data.target_repertoire_uuid;
      }
      await loadRepertoires();
      renderRepertoireChips();
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
// AI SETTINGS (Turso Persistent Gemini Key)
// ----------------------------------------------------------------------------
async function loadAiSettingsStatus() {
  const statusEl = document.getElementById('set-gemini-status');
  if (!statusEl) return;
  try {
    const res = await fetch(`${API_BASE}/api/settings/ai`);
    if (res.ok) {
      const data = await res.json();
      if (data.configured) {
        statusEl.innerHTML = `<span style="color:#10b981; font-weight:700;">✓ Chiave Gemini AI configurata (${escapeHtml(data.masked_key || 'Attiva')})</span>`;
      } else {
        statusEl.innerHTML = `<span style="color:#f59e0b; font-weight:700;">⚠ Chiave API Gemini non ancora configurata</span>`;
      }
    }
  } catch (err) {
    console.warn('AI status load error:', err);
  }
}

async function saveGeminiApiKey() {
  const inputEl = document.getElementById('set-gemini-key');
  const val = inputEl ? inputEl.value.trim() : '';
  if (!val) {
    showToast('Incolla una chiave API Gemini valida');
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/api/settings/ai`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gemini_api_key: val })
    });
    if (res.ok) {
      if (inputEl) inputEl.value = '';
      showToast('✓ Chiave Gemini Vision AI salvata nel Cloud DB!');
      loadAiSettingsStatus();
    } else {
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || 'Errore salvataggio chiave API');
    }
  } catch (err) {
    console.error('Save Gemini key error:', err);
    showToast('Errore di connessione');
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
