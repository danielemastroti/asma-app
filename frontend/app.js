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
const savedUserName = (() => {
  try { return localStorage.getItem('asma_user_name'); } catch (e) { return null; }
})();
const savedDevice = (() => {
  try { return localStorage.getItem('asma_active_device'); } catch (e) { return null; }
})();
const savedAppMode = (() => {
  try { return localStorage.getItem('asma_app_mode'); } catch (e) { return null; }
})();

// Application State
const state = {
  currentTab: 'dashboard',
  appMode: (savedAppMode === 'editing' || savedAppMode === 'simplified') ? savedAppMode : 'simplified',
  repertoires: [],
  activeRepertoire: '__ALL__',
  songs: [],
  selectedSong: null,
  setlists: [],
  selectedSetlist: null,
  scoreMode: savedScoreMode || 'chords',
  currentUser: {
    email: savedUserEmail || '',
    name: savedUserName || '',
    role: (savedUserEmail === 'danyposta@gmail.com' || savedUserEmail === 'danyposta@yahoo.it') ? 'ADMIN' : 'BAND_MEMBER'
  },
  activeDevice: savedDevice || (() => {
    try {
      const cp = localStorage.getItem('asma_user_prefs');
      return cp ? JSON.parse(cp).active_device : null;
    } catch (e) { return null; }
  })() || null,
  usersList: [],
  devicesList: [],
  songViewType: (() => { try { return localStorage.getItem('asma_song_view_type') || 'pdf'; } catch (e) { return 'pdf'; } })(),
  stageViewType: (() => { try { return localStorage.getItem('asma_stage_view_type') || 'prompter'; } catch (e) { return 'prompter'; } })(),
  userPrefs: (() => {
    const base = {
      layout_font_size: 12.0,
      layout_font_size_chords: 13.0,
      layout_columns: 1,
      layout_margin_lateral: 10.0,
      layout_margin_top: 10.0,
      layout_margin_bottom: 14.0,
      color_lyrics: '#111111',
      color_chords: '#B71C1C',
      color_aml_markup: '#4A148C',
      stage_color_lyrics: '#FFFFFF',
      stage_color_chords: '#FFD600',
      stage_color_aml_markup: '#38BDF8',
      score_display_mode: savedScoreMode || 'lyrics',
      app_mode: (savedAppMode === 'editing' || savedAppMode === 'simplified') ? savedAppMode : 'simplified'
    };
    try {
      const cp = localStorage.getItem('asma_user_prefs');
      if (cp) Object.assign(base, JSON.parse(cp));
    } catch (e) {}
    return base;
  })(),
  // Live Stage State
  isStageActive: false,
  isAutoscrolling: false,
  scrollSpeed: 28, // px per second
  scrollIntervalId: null,
  stageSongs: [],
  stageIndex: 0,
  selectedSongUuids: new Set(),
  filterOnlyIncomplete: false,
  importOriginalAml: '',
  importOfficialLyrics: '',
  importCompletenessStatus: '',
  importCompletenessRatio: 0
};

// ----------------------------------------------------------------------------
// OFFLINE SNAPSHOT & DRAFT STORAGE (PWA 100% Offline & Caso B)
// ----------------------------------------------------------------------------
const SNAPSHOT_KEYS = {
  SONGS: 'asma_snapshot_songs',
  REPERTOIRES: 'asma_snapshot_repertoires',
  SETLISTS: 'asma_snapshot_setlists',
  USERS: 'asma_snapshot_users',
  DEVICES: 'asma_snapshot_devices',
  TIMESTAMP: 'asma_snapshot_timestamp',
  DRAFTS: 'asma_offline_drafts'
};

function saveOfflineSnapshot(key, data) {
  try {
    localStorage.setItem(key, JSON.stringify(data));
    localStorage.setItem(SNAPSHOT_KEYS.TIMESTAMP, String(Date.now()));
  } catch (e) {
    console.warn('Error saving offline snapshot:', e);
  }
}

function loadOfflineSnapshot(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    console.warn('Error loading offline snapshot:', e);
    return null;
  }
}

function getOfflineDrafts() {
  return loadOfflineSnapshot(SNAPSHOT_KEYS.DRAFTS) || {};
}

function saveOfflineDraft(songUuid, draftPayload) {
  const drafts = getOfflineDrafts();
  drafts[songUuid] = {
    ...draftPayload,
    saved_at: new Date().toISOString()
  };
  saveOfflineSnapshot(SNAPSHOT_KEYS.DRAFTS, drafts);
}

function removeOfflineDraft(songUuid) {
  const drafts = getOfflineDrafts();
  if (drafts[songUuid]) {
    delete drafts[songUuid];
    saveOfflineSnapshot(SNAPSHOT_KEYS.DRAFTS, drafts);
  }
}

function applyOfflineDraftsToMemory() {
  const drafts = getOfflineDrafts();
  const uuids = Object.keys(drafts);
  if (uuids.length === 0 || !state.songs) return;
  for (const uid of uuids) {
    const d = drafts[uid];
    const idx = state.songs.findIndex(s => s.uuid === uid);
    if (idx !== -1) {
      state.songs[idx] = {
        ...state.songs[idx],
        title: d.title || state.songs[idx].title,
        artist: d.artist || state.songs[idx].artist,
        key_current: d.key_current || state.songs[idx].key_current,
        bpm: d.bpm || state.songs[idx].bpm,
        capo: d.capo || state.songs[idx].capo,
        aml_content: d.aml_content || state.songs[idx].aml_content,
        _is_offline_draft: true
      };
    }
  }
}

function updateConnectionStatus(isOnline) {
  const pill = document.getElementById('offline-status-pill');
  if (!pill) return;
  if (!isOnline) {
    pill.style.display = 'inline-flex';
    pill.innerHTML = '<span>🟡 Offline</span>';
    pill.style.background = 'rgba(234, 179, 8, 0.15)';
    pill.style.borderColor = '#eab308';
    pill.style.color = '#facc15';
  } else {
    const drafts = getOfflineDrafts();
    const draftCount = Object.keys(drafts).length;
    if (draftCount > 0) {
      pill.style.display = 'inline-flex';
      pill.innerHTML = `<span>🔄 Sincronizzo (${draftCount})...</span>`;
      pill.style.background = 'rgba(56, 189, 248, 0.15)';
      pill.style.borderColor = '#38bdf8';
      pill.style.color = '#38bdf8';
    } else {
      pill.style.display = 'inline-flex';
      pill.innerHTML = '<span>🟢 Online</span>';
      pill.style.background = 'rgba(34, 197, 94, 0.15)';
      pill.style.borderColor = '#22c55e';
      pill.style.color = '#4ade80';
      setTimeout(() => {
        if (navigator.onLine && pill) {
          pill.style.display = 'none';
        }
      }, 3500);
    }
  }
}

function showOfflineInfoModal() {
  const modal = document.getElementById('modal-offline-info');
  const meta = document.getElementById('offline-snapshot-meta');
  if (meta) {
    const ts = localStorage.getItem(SNAPSHOT_KEYS.TIMESTAMP);
    const dateStr = ts ? new Date(parseInt(ts)).toLocaleString('it-IT') : 'Recente';
    const songCount = (state.songs || []).length;
    const repCount = (state.repertoires || []).length;
    const drafts = getOfflineDrafts();
    const draftCount = Object.keys(drafts).length;
    meta.innerHTML = `<b>Snapshot Locale:</b> ${songCount} brani in memoria &bull; ${repCount} repertori<br/><b>Ultimo salvataggio:</b> ${dateStr}${draftCount > 0 ? `<br/><span style="color:#facc15;"><b>Bozze Offline in sospeso:</b> ${draftCount} brano/i da sincronizzare</span>` : ''}`;
  }
  if (modal) modal.style.display = 'flex';
}

function closeOfflineInfoModal() {
  const modal = document.getElementById('modal-offline-info');
  if (modal) modal.style.display = 'none';
}

async function syncOfflineDrafts() {
  const drafts = getOfflineDrafts();
  const uuids = Object.keys(drafts);
  if (uuids.length === 0) return;

  console.log(`[ASMA Offline Sync] Trovate ${uuids.length} bozze offline da sincronizzare...`);
  let synced = 0;
  for (const uid of uuids) {
    const payload = drafts[uid];
    try {
      if (uid.startsWith('offline_')) {
        const cleanPayload = { ...payload };
        delete cleanPayload.saved_at;
        const res = await fetch(`${API_BASE}/api/songs`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(cleanPayload)
        });
        if (res.ok) {
          removeOfflineDraft(uid);
          synced++;
        }
      } else {
        const cleanPayload = { ...payload };
        delete cleanPayload.saved_at;
        const res = await fetch(`${API_BASE}/api/songs/${uid}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(cleanPayload)
        });
        if (res.ok) {
          removeOfflineDraft(uid);
          synced++;
        }
      }
    } catch (e) {
      console.warn(`[ASMA Offline Sync] Errore sincronizzazione bozza ${uid}:`, e);
    }
  }

  if (synced > 0) {
    showToast(`🌐 Sincronizzazione completata: ${synced} bozza/e offline salvata/e nel DB centrale ✓`);
    updateConnectionStatus(true);
    await loadRepertoires();
    await loadSongs({ autoSelect: false });
    if (state.selectedSong && drafts[state.selectedSong.uuid]) {
      selectSong(state.selectedSong.uuid);
    }
  }
}

function initConnectionListeners() {
  window.addEventListener('online', () => {
    updateConnectionStatus(true);
    showToast('🌐 Connessione Internet ripristinata: sincronizzazione archivio...');
    loadRepertoires();
    loadSongs({ autoSelect: false });
    loadSetlists();
    syncOfflineDrafts();
  });

  window.addEventListener('offline', () => {
    updateConnectionStatus(false);
    showToast('📡 Sei offline: attivata Modalità Offline con snapshot locale protetto.');
  });
}

// ----------------------------------------------------------------------------
// INITIALIZATION
// ----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  const initialName = state.currentUser.name || savedUserName;
  if (initialName) {
    const nameSpan = document.getElementById('current-user-name');
    if (nameSpan) nameSpan.textContent = initialName;
    const dashUser = document.getElementById('dash-user-name');
    if (dashUser) dashUser.textContent = initialName;
  }
  initServiceWorker();
  initNav();
  initHistoryNavigation();
  initKeyboardAndPedals();
  initConnectionListeners();
  updateConnectionStatus(navigator.onLine);
  const authed = await checkGoogleAuth();
  if (!authed) return;
  await loadUsersAndDevices();
  await loadUserPreferences();
  await loadRepertoires();
  await loadSongs();
  await loadSetlists();
  applyAppModeToUi();
});

async function checkGoogleAuth() {
  const gate = document.getElementById('login-gate');
  const warn = document.getElementById('login-config-warning');
  const params = new URLSearchParams(window.location.search);
  const urlMode = params.get('mode');
  if (urlMode === 'editing' || urlMode === 'simplified') {
    state.appMode = urlMode;
    state.userPrefs.app_mode = urlMode;
    try { localStorage.setItem('asma_app_mode', urlMode); } catch (e) {}
    params.delete('mode');
    const cleanSearch = params.toString();
    const cleanUrl = window.location.pathname + (cleanSearch ? `?${cleanSearch}` : '') + window.location.hash;
    window.history.replaceState(window.history.state, '', cleanUrl);
  }

  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, { credentials: 'same-origin' });
    if (res.ok) {
      const data = await res.json();
      if (data && data.authenticated && data.user && data.user.email) {
        const savedMusName = localStorage.getItem('asma_user_name');
        state.currentUser = {
          email: data.user.email,
          name: savedMusName || data.user.name || data.user.email.split('@')[0],
          role: data.user.role || 'BAND_MEMBER',
          picture: data.user.picture || ''
        };
        state.authenticatedUserEmail = data.user.email;
        try { localStorage.setItem('asma_user_email', data.user.email); } catch (e) {}
        const savedDev = (() => { try { return localStorage.getItem('asma_active_device'); } catch (e) { return null; } })();
        if (savedDev) {
          state.activeDevice = savedDev;
        } else if (data.user && data.user.active_device) {
          state.activeDevice = data.user.active_device;
          try { localStorage.setItem('asma_active_device', data.user.active_device); } catch (e) {}
        }
        if (gate) gate.style.display = 'none';
        syncAuthProfileUi();
        updateConnectionStatus(navigator.onLine);
        return true;
      }
      if (warn) {
        warn.style.display = (data && data.google_configured === false) ? 'block' : 'none';
      }
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    console.warn('Auth check error (network/offline):', err);
    // FALLBACK OFFLINE: se il dispositivo è offline ma l'utente si era già autenticato in precedenza
    const cachedEmail = localStorage.getItem('asma_user_email');
    const cachedName = localStorage.getItem('asma_user_name');
    if (cachedEmail) {
      state.currentUser = {
        email: cachedEmail,
        name: cachedName || cachedEmail.split('@')[0],
        role: cachedEmail === 'danyposta@gmail.com' ? 'ADMIN' : 'BAND_MEMBER',
        picture: ''
      };
      state.authenticatedUserEmail = cachedEmail;
      const savedDev = (() => { try { return localStorage.getItem('asma_active_device'); } catch (e) { return null; } })();
      if (savedDev) state.activeDevice = savedDev;
      if (gate) gate.style.display = 'none';
      syncAuthProfileUi();
      updateConnectionStatus(false);
      showToast('🟡 Avvio in Modalità Offline: sessione locale ripristinata ✓');
      return true;
    }
  }

  if (gate) {
    gate.style.display = 'flex';
    const modeRadio = document.querySelector(`input[name="login-app-mode"][value="${state.appMode === 'editing' ? 'editing' : 'simplified'}"]`);
    if (modeRadio) modeRadio.checked = true;
  }
  return false;
}

function startGoogleLogin() {
  const checked = document.querySelector('input[name="login-app-mode"]:checked');
  const chosenMode = checked ? checked.value : 'simplified';
  try { localStorage.setItem('asma_app_mode', chosenMode); } catch (e) {}
  (window.top || window).location.href = `${API_BASE}/api/auth/google/login?mode=${encodeURIComponent(chosenMode)}`;
}

async function logoutGoogle() {
  try {
    await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST', credentials: 'same-origin' });
  } catch (e) {}
  try { localStorage.removeItem('asma_user_email'); } catch (e) {}
  window.location.href = '/';
}

function syncAuthProfileUi() {
  const emailEl = document.getElementById('auth-google-email');
  if (emailEl) emailEl.textContent = state.authenticatedUserEmail || state.currentUser.email || '-';
  const nameSpan = document.getElementById('current-user-name');
  if (nameSpan) nameSpan.textContent = state.currentUser.name || 'Musicista';

  const authEmail = (state.authenticatedUserEmail || state.currentUser.email || '').toLowerCase();
  const isAuthAdmin = ['danyposta@gmail.com', 'danyposta@yahoo.it'].includes(authEmail) ||
                      state.currentUser.role === 'ADMIN' || state.currentUser.role === 'admin' || state.currentUser.role === 'BAND_LEADER';
  const musRow = document.getElementById('setting-musician-row');
  const nonAdminNote = document.getElementById('auth-nonadmin-note');
  if (musRow) musRow.style.display = isAuthAdmin ? 'flex' : 'none';
  if (nonAdminNote) {
    nonAdminNote.style.display = isAuthAdmin ? 'none' : 'block';
    nonAdminNote.innerHTML = `ℹ️ Profilo attivo: <strong style="color: #ffd600;">${escapeHtml(state.currentUser.name || '')}</strong> (<span style="color: #38bdf8;">${escapeHtml(authEmail)}</span>). Il cambio profilo è riservato esclusivamente all'Amministratore.`;
  }

  const adminDbCard = document.getElementById('admin-db-card');
  if (adminDbCard) adminDbCard.style.display = isAuthAdmin ? 'block' : 'none';

  const headerAuditBtn = document.getElementById('btn-header-audit');
  if (headerAuditBtn) headerAuditBtn.style.display = isAuthAdmin ? 'flex' : 'none';
}

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

function syncStickyBarsHeights() {
  try {
    const topNav = document.getElementById('top-nav-sticky-wrapper');
    if (topNav) {
      const rect = topNav.getBoundingClientRect();
      const h = rect.height || topNav.offsetHeight;
      if (h > 0) {
        document.documentElement.style.setProperty('--top-nav-height', `${Math.round(h)}px`);
      }
    }
    const songsToolbar = document.getElementById('songs-sticky-toolbar');
    if (songsToolbar) {
      const rect = songsToolbar.getBoundingClientRect();
      const sh = rect.height || songsToolbar.offsetHeight;
      if (sh > 0) {
        document.documentElement.style.setProperty('--songs-toolbar-height', `${Math.round(sh)}px`);
      }
    }
  } catch (e) {
    console.debug('syncStickyBarsHeights error:', e);
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

  window.addEventListener('resize', syncStickyBarsHeights, { passive: true });
  window.addEventListener('orientationchange', () => {
    setTimeout(syncStickyBarsHeights, 150);
  }, { passive: true });
  syncStickyBarsHeights();
}

function initHistoryNavigation() {
  try {
    if (!history.state || !history.state.asmaTab) {
      history.replaceState({ asmaTab: state.currentTab || 'dashboard' }, '', window.location.href);
    }
  } catch (e) {}

  window.addEventListener('popstate', (e) => {
    const st = e.state || {};
    const stageModal = document.getElementById('stage-modal');
    if (stageModal && stageModal.style.display !== 'none' && st.asmaModal !== 'stage') {
      closeStageModal({ fromPopstate: true });
    }
    const pdfModal = document.getElementById('pdf-export-modal');
    if (pdfModal && pdfModal.style.display !== 'none' && st.asmaModal !== 'pdf-export') {
      closePdfExportModal({ fromPopstate: true });
    }
    if (st.asmaTab && st.asmaTab !== state.currentTab) {
      switchTab(st.asmaTab, { skipHistory: true });
    }
  });
}

function switchTab(tabName, { skipHistory = false } = {}) {
  if (!skipHistory && tabName && tabName !== state.currentTab) {
    try {
      history.pushState({ asmaTab: tabName }, '', window.location.href);
    } catch (e) {}
  }
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
  requestAnimationFrame(() => syncStickyBarsHeights());
}

function isOwnPersonalRepertoire(rep) {
  if (!rep || rep.is_official || !rep.owner_email) return false;
  const currentEmail = (state.currentUser?.email || '').toLowerCase().trim();
  const ownerEmail = (rep.owner_email || '').toLowerCase().trim();
  if (!currentEmail || !ownerEmail) return false;
  if (ownerEmail === currentEmail) return true;
  // Admin alias: danyposta@gmail.com and danyposta@yahoo.it represent the same administrator (Daniele / Sentimental)
  const adminEmails = ['danyposta@gmail.com', 'danyposta@yahoo.it'];
  if (adminEmails.includes(currentEmail) && adminEmails.includes(ownerEmail)) {
    return true;
  }
  return false;
}

/**
 * Restituisce i repertori del workspace dell'utente attivo (Ufficiale, condivisi senza owner,
 * e il proprio repertorio personale), escludendo cartelle personali di altri musicisti.
 */
function getWorkspaceRepertoires() {
  const reps = Array.isArray(state.repertoires) ? state.repertoires : [];
  const isAdmin = isCurrentUserAdmin();
  const adminEmails = ['danyposta@gmail.com', 'danyposta@yahoo.it'];

  return reps.filter(r => {
    if (r.is_official) return true;
    if (isOwnPersonalRepertoire(r)) return true;
    if (!r.owner_email) return true;
    if (isAdmin && (adminEmails.includes((r.owner_email || '').toLowerCase().trim()) || (r.name || '').toLowerCase() === 'daniele')) {
      return true;
    }
    return false;
  });
}

/**
 * Restituisce i brani unici appartenenti ai repertori del workspace attivo (esclude file orfani).
 */
function getWorkspaceSongs() {
  const songs = Array.isArray(state.songs) ? state.songs : [];
  const reps = getWorkspaceRepertoires();
  if (reps.length === 0) return songs;
  const allowed = new Set();
  reps.forEach(r => (r.song_uuids || []).forEach(uid => allowed.add(uid)));
  const EXCLUDED = ['albachiara', 'alba chiara', 'test undo song', 'temp transpose song', 'unique test song xyz'];
  return songs.filter(s => {
    if (!allowed.has(s.uuid)) return false;
    const t = (s.title || '').trim().toLowerCase();
    if (EXCLUDED.includes(t) || t.startsWith('test undo') || t.startsWith('temp transpose')) return false;
    return true;
  });
}

function renderDashboard() {
  const userEl = document.getElementById('dash-user-name');
  if (userEl) userEl.textContent = (state.currentUser && state.currentUser.name) || 'Musicista';
  const devEl = document.getElementById('dash-device-name');
  if (devEl) devEl.textContent = state.activeDevice || 'Tablet';

  const songs = getWorkspaceSongs();
  const reps = getWorkspaceRepertoires();
  const setlists = Array.isArray(state.setlists) ? state.setlists : [];

  const songsStat = document.getElementById('dash-stat-songs');
  const songsSub = document.getElementById('dash-stat-songs-sub');
  const officialRep = reps.find(r => r.is_official);
  const personalRep = reps.find(r => isOwnPersonalRepertoire(r));
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
        const icon = r.is_official ? '🌟' : (isOwnPersonalRepertoire(r) ? '👤' : '📁');
        const label = r.is_official
          ? escapeHtml(r.name)
          : (isOwnPersonalRepertoire(r) ? `Personale (${escapeHtml(r.name)})` : escapeHtml(r.name));
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
function showToast(message, customDuration) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = 'toast';

  const textSpan = document.createElement('span');
  textSpan.style.flex = '1';
  textSpan.textContent = message;
  toast.appendChild(textSpan);

  const closeBtn = document.createElement('button');
  closeBtn.className = 'toast-close-btn';
  closeBtn.innerHTML = '&times;';
  closeBtn.title = 'Chiudi';
  toast.appendChild(closeBtn);

  container.appendChild(toast);

  let duration = customDuration;
  if (!duration) {
    const len = (message || '').length;
    if (len > 70 || /errore|http|fallit/i.test(message)) {
      duration = 8000;
    } else if (len > 35 || /completat|verificat|convalidat|necessari/i.test(message)) {
      duration = 6000;
    } else {
      duration = 4500;
    }
  }

  let dismissTimer = null;
  const dismiss = () => {
    if (toast.classList.contains('toast-hiding')) return;
    toast.classList.add('toast-hiding');
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  };

  const startTimer = () => {
    clearTimeout(dismissTimer);
    dismissTimer = setTimeout(dismiss, duration);
  };

  startTimer();

  toast.addEventListener('mouseenter', () => clearTimeout(dismissTimer));
  toast.addEventListener('mouseleave', () => startTimer());
  toast.addEventListener('touchstart', () => clearTimeout(dismissTimer), { passive: true });

  closeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    clearTimeout(dismissTimer);
    dismiss();
  });
  toast.addEventListener('click', () => {
    clearTimeout(dismissTimer);
    dismiss();
  });
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
      saveOfflineSnapshot(SNAPSHOT_KEYS.USERS, users);
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
      } else if (!state.currentUser.email && users.length) {
        state.currentUser.email = users[0].email;
        state.currentUser.name = users[0].name;
        state.currentUser.role = users[0].role;
      }
      const nameSpan = document.getElementById('current-user-name');
      if (nameSpan) nameSpan.textContent = state.currentUser.name;
      syncAuthProfileUi();
    }
    if (dRes.ok) {
      const devices = await dRes.json();
      state.devicesList = devices;
      saveOfflineSnapshot(SNAPSHOT_KEYS.DEVICES, devices);
      const devSelect = document.getElementById('setting-device-select');
      if (devSelect && devices.length) {
        devSelect.innerHTML = devices.map(d => 
          `<option value="${escapeHtml(d.name)}" ${d.name === state.activeDevice ? 'selected' : ''}>${escapeHtml(d.name)}</option>`
        ).join('');
        devSelect.value = state.activeDevice;
      }
    }
  } catch (err) {
    console.warn('Could not load users or devices dynamically, using cached snapshot:', err);
    const cachedUsers = loadOfflineSnapshot(SNAPSHOT_KEYS.USERS);
    if (cachedUsers && Array.isArray(cachedUsers)) {
      state.usersList = cachedUsers;
      const musSelect = document.getElementById('setting-musician-select');
      if (musSelect && cachedUsers.length) {
        musSelect.innerHTML = cachedUsers.map(u => 
          `<option value="${escapeHtml(u.email)}" ${u.email === state.currentUser.email ? 'selected' : ''}>${escapeHtml(u.name)} (${escapeHtml(u.role)})</option>`
        ).join('');
      }
    }
    const cachedDevices = loadOfflineSnapshot(SNAPSHOT_KEYS.DEVICES);
    if (cachedDevices && Array.isArray(cachedDevices)) {
      state.devicesList = cachedDevices;
      const devSelect = document.getElementById('setting-device-select');
      if (devSelect && cachedDevices.length) {
        devSelect.innerHTML = cachedDevices.map(d => 
          `<option value="${escapeHtml(d.name)}" ${d.name === state.activeDevice ? 'selected' : ''}>${escapeHtml(d.name)}</option>`
        ).join('');
        devSelect.value = state.activeDevice;
      }
    }
  }
}

async function loadUserPreferences(requestedDevice = null) {
  try {
    const savedDev = (() => { try { return localStorage.getItem('asma_active_device'); } catch (e) { return null; } })();
    const targetDevice = requestedDevice || savedDev || state.activeDevice || null;
    const devParam = targetDevice ? `?device=${encodeURIComponent(targetDevice)}` : '';
    const email = (state.currentUser && state.currentUser.email) || localStorage.getItem('asma_user_email') || 'danyposta@gmail.com';
    const res = await fetch(`${API_BASE}/api/preferences/${encodeURIComponent(email)}${devParam}`);
    if (res.ok) {
      const prefs = await res.json();
      state.userPrefs = Object.assign(state.userPrefs, prefs);
      try { localStorage.setItem('asma_user_prefs', JSON.stringify(state.userPrefs)); } catch (e) {}

      // Mantieni e sincronizza sempre il dispositivo hardware reale
      const effectiveDev = prefs.active_device || targetDevice;
      if (effectiveDev) {
        state.activeDevice = effectiveDev;
        try { localStorage.setItem('asma_active_device', effectiveDev); } catch (e) {}
      }
      const devSelect = document.getElementById('setting-device-select');
      if (devSelect && state.activeDevice) {
        devSelect.value = state.activeDevice;
      }
      // Prioritize local setting on device if explicitly chosen
      const localMode = (() => {
        try { return localStorage.getItem('asma_score_mode'); } catch (e) { return null; }
      })();
      state.scoreMode = localMode || state.userPrefs.score_display_mode || 'lyrics';
      const localAppMode = (() => {
        try { return localStorage.getItem('asma_app_mode'); } catch (e) { return null; }
      })();
      state.appMode = (localAppMode === 'editing' || localAppMode === 'simplified')
        ? localAppMode
        : (state.userPrefs.app_mode === 'editing' ? 'editing' : 'simplified');
      state.userPrefs.app_mode = state.appMode;
      applyPreferencesToDom();
      updateSettingsFormValues();
      updateStageScoreModeButton();
      applyAppModeToUi();
      renderDashboard();
    }
  } catch (err) {
    console.warn('Preferences load error:', err);
    applyPreferencesToDom();
    updateStageScoreModeButton();
    applyAppModeToUi();
  }
}

function isEditingMode() {
  return state.appMode === 'editing';
}

function requireEditingMode() {
  if (isEditingMode()) return true;
  showToast('Passa a "Editing Completo" dalla Home per modificare brani o scalette');
  return false;
}

function setAppMode(mode) {
  const next = mode === 'editing' ? 'editing' : 'simplified';
  state.appMode = next;
  state.userPrefs.app_mode = next;
  try { localStorage.setItem('asma_app_mode', next); } catch (e) {}

  if (next !== 'editing') {
    state.isEditingSong = false;
    hideNewSongForm();
    hideNewSetlistForm();
    if (typeof closeAdminRepertoiresModal === 'function') closeAdminRepertoiresModal();
    if (typeof closeAddToSetlistModal === 'function') closeAddToSetlistModal();
  }

  applyAppModeToUi();
  autosaveUserPreferences();
  showToast(next === 'editing'
    ? '✏️ Modalità Editing Completo attiva'
    : '🎤 Modalità Casa / Palco (Semplificata) attiva');
}

function applyAppModeToUi() {
  const editing = isEditingMode();

  const pill = document.getElementById('header-mode-pill');
  if (pill) {
    pill.innerHTML = editing
      ? '<span class="mode-pill-full">✏️ Editing Completo</span><span class="mode-pill-short">✏️ Edit</span>'
      : '<span class="mode-pill-full">🎤 Casa / Palco</span><span class="mode-pill-short">🎤 Palco</span>';
    pill.classList.toggle('mode-pill-editing', editing);
    pill.classList.toggle('mode-pill-simplified', !editing);
  }

  const btnSimp = document.getElementById('btn-mode-simplified');
  const btnEdit = document.getElementById('btn-mode-editing');
  if (btnSimp) btnSimp.classList.toggle('active', !editing);
  if (btnEdit) btnEdit.classList.toggle('active', editing);

  const badge = document.getElementById('dash-mode-badge');
  if (badge) {
    badge.textContent = editing ? '✏️ Editing Completo' : '🎤 Casa / Palco';
    badge.classList.toggle('dash-mode-badge-editing', editing);
    badge.classList.toggle('dash-mode-badge-simplified', !editing);
  }

  const hint = document.getElementById('dash-mode-hint');
  if (hint) {
    hint.textContent = editing
      ? 'Modalità Editing Completo attiva: puoi modificare testi/accordi, salvare trasposizioni nel DB, creare brani e gestire scalette.'
      : 'Modalità Semplificata attiva: ideale per studiare a casa, prove e palco live senza rischio di alterare i brani.';
  }

  const newSongBtn = document.getElementById('btn-open-new-song');
  if (newSongBtn) newSongBtn.style.display = editing ? 'inline-flex' : 'none';

  const newSetlistBtn = document.getElementById('btn-open-new-setlist');
  if (newSetlistBtn) newSetlistBtn.style.display = editing ? 'inline-flex' : 'none';

  renderRepertoireChips();
  renderSongCards();
  renderSongViewer();
  renderSetlists();
  if (state.selectedSetlist) {
    renderSetlistEditor();
  }
  renderDashboard();
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
  const valMarginBottom = document.getElementById('val-margin-bottom');
  if (valMarginBottom) valMarginBottom.textContent = p.layout_margin_bottom || 14;

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

  // Salva subito in localStorage per persistenza 0ms locale
  try {
    localStorage.setItem('asma_user_prefs', JSON.stringify(state.userPrefs));
    if (state.activeDevice) {
      localStorage.setItem('asma_active_device', state.activeDevice);
    }
  } catch (e) {}

  try {
    const email = (state.currentUser && state.currentUser.email) || localStorage.getItem('asma_user_email') || 'danyposta@gmail.com';
    const payload = Object.assign({}, state.userPrefs, {
      device_name: state.activeDevice,
      score_display_mode: state.scoreMode
    });
    const res = await fetch(`${API_BASE}/api/preferences/${encodeURIComponent(email)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json().catch(() => ({}));
      if (data && data.active_device) {
        state.activeDevice = data.active_device;
        try { localStorage.setItem('asma_active_device', data.active_device); } catch (e) {}
      }
      showToast(`Preferenze salvate nel cloud Turso ✓`);
    }
  } catch (err) {
    console.warn('Autosave offline:', err);
  }
}

async function onMusicianChange(email) {
  if (!isCurrentUserAdmin()) {
    showToast('⚠️ Solo l\'amministratore può commutare il profilo musicista.');
    const musSelect = document.getElementById('setting-musician-select');
    if (musSelect && state.currentUser?.email) musSelect.value = state.currentUser.email;
    return;
  }
  state.currentUser.email = email;
  try { localStorage.setItem('asma_user_email', email); } catch (e) {}
  const user = (state.usersList || []).find(u => u.email.toLowerCase() === email.toLowerCase());
  state.currentUser.name = user ? user.name : (email.split('@')[0]);
  state.currentUser.role = user ? user.role : 'BAND_MEMBER';
  try { localStorage.setItem('asma_user_name', state.currentUser.name); } catch (e) {}
  const nameSpan = document.getElementById('current-user-name');
  if (nameSpan) nameSpan.textContent = state.currentUser.name;
  showToast(`Profilo attivo: ${state.currentUser.name}`);
  logAuditEvent('SWITCH_PROFILE', 'USER', email, { name: state.currentUser.name });

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

async function onDeviceChange(deviceName) {
  state.activeDevice = deviceName;
  try { localStorage.setItem('asma_active_device', deviceName); } catch (e) {}
  await loadUserPreferences(deviceName);
  await autosaveUserPreferences();
  renderDashboard();
  if (state.selectedSong) renderSongViewer();
  showToast(`Hardware selezionato e salvato: ${deviceName}`);
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

function adjustMarginBottom(delta) {
  state.userPrefs.layout_margin_bottom = Math.max(4, Math.min(50, (state.userPrefs.layout_margin_bottom || 14) + delta));
  const val = document.getElementById('val-margin-bottom');
  if (val) val.textContent = state.userPrefs.layout_margin_bottom;
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
      saveOfflineSnapshot(SNAPSHOT_KEYS.REPERTOIRES, state.repertoires);
      const workspaceReps = getWorkspaceRepertoires();
      const isAdmin = isCurrentUserAdmin();
      const official = workspaceReps.find(r => r.is_official);

      // Default to Official Repertoire for everyone (musicians and admin) to keep band songs clean
      const currentExists = workspaceReps.some(r => r.uuid === state.activeRepertoire);
      if (state.activeRepertoire === '__ALL__' || !currentExists) {
        state.activeRepertoire = official ? official.uuid : (workspaceReps[0]?.uuid || '');
      }
      renderRepertoireChips();
      renderDashboard();
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    console.warn('Repertoires offline, loading from local snapshot:', err);
    const cachedReps = loadOfflineSnapshot(SNAPSHOT_KEYS.REPERTOIRES);
    if (cachedReps && Array.isArray(cachedReps) && cachedReps.length > 0) {
      state.repertoires = cachedReps;
      updateConnectionStatus(false);
      const workspaceReps = getWorkspaceRepertoires();
      const official = workspaceReps.find(r => r.is_official);
      const currentExists = workspaceReps.some(r => r.uuid === state.activeRepertoire);
      if (state.activeRepertoire === '__ALL__' || !currentExists) {
        state.activeRepertoire = official ? official.uuid : (workspaceReps[0]?.uuid || '');
      }
      renderRepertoireChips();
      renderDashboard();
    }
  }
}

function renderRepertoireChips() {
  const container = document.getElementById('repertoire-chips');
  if (!container) return;

  const isAdmin = isCurrentUserAdmin();
  const workspaceReps = getWorkspaceRepertoires();
  let html = '';

  workspaceReps.forEach(r => {
    const isActive = state.activeRepertoire === r.uuid ? 'active' : '';
    let icon = '📁';
    let label = escapeHtml(r.name);
    let extraStyle = '';
    if (r.is_official) {
      icon = '🌟';
      label = `<b>${escapeHtml(r.name)}</b>`;
      extraStyle = 'border-color: #ffd600; color: #ffd600; font-weight: 800;';
    } else if (isOwnPersonalRepertoire(r) || (isAdmin && (r.owner_email || '').toLowerCase().includes('danyposta'))) {
      icon = '👤';
      label = `Personale (${escapeHtml(r.name)})`;
    }
    html += `<button class="chip ${isActive}" style="${isActive ? '' : extraStyle}" onclick="selectRepertoire('${r.uuid}')">${icon} ${label} (${r.song_count})</button>`;
  });

  container.innerHTML = html;

  const adminBtn = document.getElementById('btn-admin-manage-rep');
  if (adminBtn) {
    adminBtn.style.display = (isAdmin && isEditingMode()) ? 'inline-block' : 'none';
  }
  updateTopDownloadPdfButton();
  updateAdminCompletenessToolbar();
  requestAnimationFrame(() => syncStickyBarsHeights());
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
      const titleMatch = prevTitle
        ? filtered.find(s => (s.title || '').trim().toUpperCase() === prevTitle)
        : null;
      if (titleMatch) {
        selectSong(titleMatch.uuid);
      } else if (filtered.length > 0) {
        selectSong(filtered[0].uuid);
      } else {
        state.selectedSong = null;
        renderSongViewer();
      }
    }
  } else if (filtered.length > 0) {
    selectSong(filtered[0].uuid);
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
      saveOfflineSnapshot(SNAPSHOT_KEYS.SONGS, state.songs);
      applyOfflineDraftsToMemory();
      renderRepertoireChips();
      renderSongCards();
      renderDashboard();
      if (autoSelect && !state.selectedSong) {
        const filtered = getFilteredSongs();
        if (filtered.length > 0) {
          selectSong(filtered[0].uuid);
        }
      }
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    console.warn('Songs offline, loading from local snapshot:', err);
    const cachedSongs = loadOfflineSnapshot(SNAPSHOT_KEYS.SONGS);
    if (cachedSongs && Array.isArray(cachedSongs) && cachedSongs.length > 0) {
      state.songs = cachedSongs;
      applyOfflineDraftsToMemory();
      updateConnectionStatus(false);
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
  }
}

function getFilteredSongs(searchKw = '') {
  let list = getWorkspaceSongs();
  if (state.activeRepertoire && state.activeRepertoire !== '__ALL__') {
    const rep = state.repertoires.find(r => r.uuid === state.activeRepertoire);
    if (rep && rep.song_uuids) {
      const allowed = new Set(rep.song_uuids);
      list = state.songs.filter(s => allowed.has(s.uuid));
    }
  } else {
    // If __ALL__ or not specified, default to official repertoire
    const official = (state.repertoires || []).find(r => r.is_official);
    if (official && official.song_uuids) {
      const allowed = new Set(official.song_uuids);
      list = state.songs.filter(s => allowed.has(s.uuid));
    }
  }
  // Exclude test/default songs and de-duplicate strictly by unique song UUID (never collapse distinct titles like 'MEDLEY ROCK' and 'MEDLEY-ROCK')
  const EXCLUDED = ['albachiara', 'alba chiara', 'test undo song', 'temp transpose song', 'unique test song xyz'];
  const seenUuids = new Set();
  list = list.filter(s => {
    if (!s || !s.uuid) return false;
    const t = (s.title || '').trim().toLowerCase();
    if (EXCLUDED.includes(t) || t.startsWith('test undo') || t.startsWith('temp transpose')) return false;
    if (seenUuids.has(s.uuid)) return false;
    seenUuids.add(s.uuid);
    return true;
  });
  if (searchKw) {
    list = list.filter(s =>
      s.title.toLowerCase().includes(searchKw) ||
      (s.artist && s.artist.toLowerCase().includes(searchKw)) ||
      (s.author && s.author.toLowerCase().includes(searchKw))
    );
  }
  if (state.filterOnlyIncomplete) {
    list = list.filter(s => !isMedleySong(s) && s.completeness_status === 'INCOMPLETO');
  }
  return list;
}

function isMedleySong(s) {
  if (!s) return false;
  const t = (s.title || '').toLowerCase();
  return t.includes('medley') || s.completeness_status === 'MEDLEY';
}

function renderCompletenessBadge(s) {
  if (!s) return '';
  if (isMedleySong(s)) {
    return `<span class="badge badge-medley" title="Medley manuale - Escluso da verifiche e modifiche AI">🎵 MEDLEY</span>`;
  }
  const status = (s.completeness_status || 'NON_VERIFICATO').toUpperCase();
  if (status === 'DEFINITIVO') {
    return `<span class="badge badge-definitivo" title="Brano verificato e consolidato">🔒 DEFINITIVO</span>`;
  }
  if (status === 'COMPLETO') {
    return `<span class="badge badge-completo" title="Testo completo verificato con LRCLIB">✓ COMPLETO</span>`;
  }
  if (status === 'INCOMPLETO') {
    const pct = s.completeness_ratio ? Math.round(s.completeness_ratio * 100) : 0;
    const pctStr = pct > 0 ? ` (${pct}%)` : '';
    return `<span class="badge badge-incompleto" title="Testo apparentemente tronco rispetto all'originale">⚠️ INCOMPLETO${pctStr}</span>`;
  }
  return `<span class="badge badge-unverified" title="Completezza non ancora verificata con LRCLIB">❓ NON VERIFICATO</span>`;
}

function renderSongCards(searchKw = '') {
  const container = document.getElementById('song-grid');
  if (!container) return;

  const filtered = getFilteredSongs(searchKw);
  if (filtered.length === 0) {
    container.innerHTML = `<div style="grid-column: 1/-1; padding: 24px; text-align: center; color: #94a3b8;">Nessun brano presente in questa vista.</div>`;
    updateAdminCompletenessToolbar();
    return;
  }

  const isAdmin = typeof isCurrentUserAdmin === 'function' ? isCurrentUserAdmin() : false;
  const official = (state.repertoires || []).find(r => r.is_official);
  const isOfficialRep = official && (state.activeRepertoire === official.uuid || state.activeRepertoire === '__ALL__');

  container.innerHTML = filtered.map(s => {
    const isSel = state.selectedSong && state.selectedSong.uuid === s.uuid ? 'selected' : '';
    const repsStr = (s.assigned_repertoires || []).join(', ') || 'Archivio';
    const cardBtn = isEditingMode()
      ? `<button class="btn btn-secondary" style="min-height: 26px; padding: 2px 8px; font-size: 11px; color: #38bdf8; border-color: #38bdf8; font-weight: 800; white-space: nowrap;" onclick="event.stopPropagation(); openAddToSetlistModal('${s.uuid}')" title="Aggiungi a una scaletta">+ Scaletta</button>`
      : '';
    const draftBadge = s._is_offline_draft
      ? '<span style="font-size:10px; background:#eab308; color:#0f172a; padding:1px 5px; border-radius:4px; font-weight:800; margin-left:4px;">💾 Bozza Offline</span>'
      : '';

    let batchCheckbox = '';
    if (isAdmin && isOfficialRep) {
      if (isMedleySong(s)) {
        batchCheckbox = `<span style="display:inline-block; font-size:10px; color:#c084fc; font-weight:800; margin-right:6px;" title="Medley protetto da verifiche e modifiche batch">[Protetto]</span>`;
      } else {
        const isChecked = state.selectedSongUuids && state.selectedSongUuids.has(s.uuid) ? 'checked' : '';
        batchCheckbox = `<input type="checkbox" style="width: 17px; height: 17px; margin-right: 8px; cursor: pointer; accent-color: #38bdf8;" ${isChecked} onclick="event.stopPropagation(); toggleSongBatchSelect('${s.uuid}')" title="Seleziona brano per operazione batch">`;
      }
    }

    return `
      <div class="song-card ${isSel}" onclick="selectSong('${s.uuid}')">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <div class="song-card-title" style="display: flex; align-items: center; flex-wrap: wrap;">
            ${batchCheckbox}
            <span>${escapeHtml(s.title)}</span>${draftBadge}
          </div>
          ${cardBtn}
        </div>
        <div class="song-card-artist">${escapeHtml(s.artist || 'Band')} &bull; ${escapeHtml(s.author || '')}</div>
        <div class="song-card-meta">
          <span class="badge">Tonalità: ${toLatinKey(s.key_current)}</span>
          <span class="badge">${s.bpm || 120} BPM</span>
          <span class="badge">📁 ${escapeHtml(repsStr)}</span>
          ${renderCompletenessBadge(s)}
        </div>
      </div>
    `;
  }).join('');
  updateAdminCompletenessToolbar();
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
      const sIdx = (state.songs || []).findIndex(s => s.uuid === uuid);
      if (sIdx !== -1) {
        state.songs[sIdx] = Object.assign(state.songs[sIdx], songData);
      }
      renderSongCards();
      renderSongViewer();
      if (window.innerWidth < 768) {
        document.getElementById('song-viewer')?.scrollIntoView({ behavior: 'smooth' });
      }
      return;
    }
  } catch (err) {
    console.warn('Error fetching song details online, falling back to local snapshot:', err);
  }

  // FALLBACK OFFLINE / SNAPSHOT
  if (seq === _selectSongSeq && state.activeRepertoire === repAtRequest) {
    const local = (state.songs || []).find(s => s.uuid === uuid);
    if (local) {
      state.isEditingSong = false;
      state.selectedSong = local;
      renderSongCards();
      renderSongViewer();
      if (window.innerWidth < 768) {
        document.getElementById('song-viewer')?.scrollIntoView({ behavior: 'smooth' });
      }
    }
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
  if (!state.selectedSong || !requireEditingMode()) return;

  const officialRep = state.repertoires.find(r => r.is_official);
  const isInOfficial = officialRep && officialRep.song_uuids && officialRep.song_uuids.includes(state.selectedSong.uuid);
  if (isInOfficial) {
    if (confirm(`I brani del Repertorio Ufficiale non possono essere modificati direttamente.\n\nVuoi creare una copia personale nel tuo repertorio per cambiare tonalità?`)) {
      await forkSongToPersonal(state.selectedSong.uuid);
    }
    return;
  }

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
  updateTopDownloadPdfButton();
  if (!state.selectedSong) {
    state.isEditingSong = false;
    container.innerHTML = `<div style="text-align: center; color: #94a3b8; padding: 24px 16px; font-size: 13px;">🎵 Tocca un brano dalla lista sopra per visualizzarne lo spartito o teleprompter</div>`;
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
          <button type="button" class="btn btn-secondary" style="font-weight: 800; min-height: 38px; padding: 4px 12px; color: #c084fc; border-color: #a855f7;" onclick="openMedleyPageFormatterModal()" title="Formatta le pagine del Medley su base dispositivo (tablet, smartphone, A4)">📐 Impagina Medley</button>
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
            <button type="button" class="btn btn-secondary" style="min-height: 28px; padding: 2px 10px; font-size: 11.5px; font-weight: 800; color: #facc15; border-color: #eab308;" onclick="openCircleOfFifthsModal(document.getElementById('edit-song-key') ? document.getElementById('edit-song-key').value : '')" title="Apri il Circolo delle Quinte per analizzare accordi, tonalità e modulazioni">🎼 Circolo Quinte</button>
            <button type="button" class="btn btn-secondary" style="min-height: 28px; padding: 2px 10px; font-size: 11.5px; font-weight: 800; color: #38bdf8; border-color: #38bdf8;" onclick="toggleEditorLivePreview('edit-song-aml', 'edit-song-live-preview', this)">👁️ Anteprima Live</button>
          </div>
        </div>
        <!-- QUICK CHIPS TOOLBAR -->
        <div class="quick-chips-bar" style="display: flex; flex-direction: column; gap: 6px;">
          <!-- RIGA 1: ACCORDI BASE (ITA & ANGLO) & MODIFICATORI -->
          <div style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;">
            <span style="font-size: 10.5px; color: #94a3b8; font-weight: 800; margin-right: 4px;">Accordi ITA:</span>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[DO]')">[DO]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[RE]')">[RE]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[MI]')">[MI]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[FA]')">[FA]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[SOL]')">[SOL]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[LA]')">[LA]</button>
            <button type="button" class="quick-chip" onclick="insertChordAtCursor('edit-song-aml', '[SI]')">[SI]</button>
            <span style="font-size: 10.5px; color: #38bdf8; font-weight: 800; margin-left: 6px; margin-right: 4px;">Anglo:</span>
            <button type="button" class="quick-chip quick-chip-anglo" onclick="insertChordAtCursor('edit-song-aml', '[C]')">[C]</button>
            <button type="button" class="quick-chip quick-chip-anglo" onclick="insertChordAtCursor('edit-song-aml', '[D]')">[D]</button>
            <button type="button" class="quick-chip quick-chip-anglo" onclick="insertChordAtCursor('edit-song-aml', '[E]')">[E]</button>
            <button type="button" class="quick-chip quick-chip-anglo" onclick="insertChordAtCursor('edit-song-aml', '[F]')">[F]</button>
            <button type="button" class="quick-chip quick-chip-anglo" onclick="insertChordAtCursor('edit-song-aml', '[G]')">[G]</button>
            <button type="button" class="quick-chip quick-chip-anglo" onclick="insertChordAtCursor('edit-song-aml', '[A]')">[A]</button>
            <button type="button" class="quick-chip quick-chip-anglo" onclick="insertChordAtCursor('edit-song-aml', '[B]')">[B]</button>
            <span style="font-size: 10.5px; color: #94a3b8; font-weight: 800; margin-left: 6px; margin-right: 4px;">Mod:</span>
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
            <button type="button" class="quick-chip quick-chip-directive" onclick="openCircleOfFifthsModal(document.getElementById('edit-song-key') ? document.getElementById('edit-song-key').value : '')" style="background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid #eab308; font-weight: 800;" title="Apri il Circolo delle Quinte per tonalità e cambi armonici">🎼 Circolo Quinte</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="openMedleyModal('edit-song-aml')" style="background: rgba(168, 85, 247, 0.22); color: #c084fc; border: 1px solid #a855f7; font-weight: 800;" title="Aggiungi spezzone Medley (gestione fino a 20 brani distinti con titolo, artista e tonalità)">🎶 + Spezzone Medley</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="openMedleyPageFormatterModal()" style="background: rgba(168, 85, 247, 0.22); color: #c084fc; border: 1px solid #a855f7; font-weight: 800;" title="Formatta e impagina gli spezzoni del Medley su base dispositivo (tablet, smartphone, A4)">📐 Impagina Medley</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="insertDirectiveAtCursor('edit-song-aml', 'scena')" style="background: rgba(6, 182, 212, 0.18); color: #22d3ee; border: 1px solid #06b6d4; font-weight: 800;" title="Preset / tasto setup per tastierista live (es. {scena: 3})">🎹 {scena: 1}</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="insertDirectiveAtCursor('edit-song-aml', 'stacco')" style="background: rgba(239, 68, 68, 0.18); color: #f87171; border: 1px solid #ef4444; font-weight: 800;" title="Stacco musicale con strumento o d'insieme (es. {stacco: guitar} o {stacco: Tutti})">⚡ {stacco: Tutti}</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="insertDirectiveAtCursor('edit-song-aml', 'chorus')" title="Racchiudi o inserisci ritornello">{soc} Rit {eoc}</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="insertDirectiveAtCursor('edit-song-aml', 'verse')" title="Racchiudi o inserisci strofa">{sov} Strofa {eov}</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="insertDirectiveAtCursor('edit-song-aml', 'bridge')" title="Racchiudi o inserisci ponte/speciale">{sob} Bridge {eob}</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="insertDirectiveAtCursor('edit-song-aml', 'solo')" title="Inserisci sezione assolo strumentale">{solo: Strumento}</button>
            <button type="button" class="quick-chip quick-chip-directive" onclick="insertDirectiveAtCursor('edit-song-aml', 'comment')" title="Inserisci nota o commento">{c: Commento}</button>
            <button type="button" class="quick-chip quick-chip-layout" onclick="insertDirectiveAtCursor('edit-song-aml', 'riga_bianca')" style="background: rgba(148, 163, 184, 0.18); color: #cbd5e1; border: 1px solid #64748b; font-weight: 800;" title="Inserisci una riga bianca nello spartito e nel PDF ({riga_bianca})">␣ {riga_bianca}</button>
            <button type="button" class="quick-chip quick-chip-layout" onclick="insertDirectiveAtCursor('edit-song-aml', 'np')" style="background: rgba(245, 158, 11, 0.18); color: #fbbf24; border: 1px solid #f59e0b; font-weight: 800;" title="Inserisci salto pagina per dispositivo ({np})">📄 {np} Salto Pagina</button>
            <button type="button" class="quick-chip quick-chip-layout" onclick="insertDirectiveAtCursor('edit-song-aml', 'colb')" title="Interruzione colonna">{colb} Salto Colonna</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n[INTRO]\\n')">[INTRO]</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n[STROFA]\\n')">[STROFA]</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n[RITORNELLO]\\n')">[RIT]</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n[SPECIALE]\\n')">[SPECIAL]</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n[OUTRO]\\n')">[OUTRO]</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n[END]\\n')">[END]</button>
            <button type="button" class="quick-chip quick-chip-section" onclick="insertChordAtCursor('edit-song-aml', '\\n♪ (Strumentale)\\n')">♪ Inst</button>
          </div>
        </div>
        <textarea id="edit-song-aml" class="touch-textarea" style="min-height: 340px;">${escapeHtml(s.aml_content || '')}</textarea>
        <div id="edit-song-live-preview" class="editor-preview-pane" style="display: none;"></div>
      </div>

      <div style="display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap;">
        <button class="btn btn-success" style="font-weight: 800; min-height: 42px; padding: 6px 18px;" onclick="saveSongEdit(false)">💾 Salva nel DB</button>
        <button class="btn btn-primary" style="font-weight: 800; min-height: 42px; padding: 6px 18px;" onclick="saveSongEdit(true)">📄 Salva & Scarica PDF</button>
        <button type="button" class="btn btn-secondary" style="font-weight: 800; min-height: 42px; padding: 6px 14px; color: #c084fc; border-color: #a855f7;" onclick="openMedleyPageFormatterModal()" title="Formatta le pagine del Medley su base dispositivo">📐 Impagina Medley</button>
        <button class="btn btn-secondary" style="min-height: 42px; padding: 6px 14px;" onclick="closeSongEditor()">✕ Annulla</button>
      </div>
    `;
    return;
  }

  const hasChords = state.scoreMode === 'chords';
  const modeLabel = hasChords ? '🎸 Accordi: ON' : '🎤 Solo Testo';
  const colsLabel = state.userPrefs.layout_columns === 2 ? '2 Colonne' : '1 Colonna';
  const isPdf = state.songViewType === 'pdf';
  const viewTypeBtnStyle = isPdf
    ? 'color: #38bdf8; border-color: #38bdf8; font-weight: 800;'
    : 'color: #ffd600; border-color: #ffd600; font-weight: 800; background: rgba(255, 214, 0, 0.1);';
  const viewTypeBtnText = isPdf ? '📄 Vista: PDF' : '📝 Vista: Testo (Tocca per PDF)';
  const viewTypeBtnTitle = isPdf ? 'Stai visualizzando lo Spartito PDF reale. Tocca per passare al Testo Web.' : 'Stai visualizzando il Testo Web. Tocca per tornare allo Spartito PDF reale.';

  const officialRep = state.repertoires.find(r => r.is_official);
  const isInOfficial = officialRep && officialRep.song_uuids && officialRep.song_uuids.includes(s.uuid);
  const editing = isEditingMode();
  const isAdmin = typeof isCurrentUserAdmin === 'function' ? isCurrentUserAdmin() : false;
  const promoteBtn = (editing && !isInOfficial && officialRep) ? 
    `<button class="btn btn-secondary" style="color: #ffd600; border-color: #ffd600; font-weight: 800;" onclick="promoteSongToOfficial('${s.uuid}')" title="Sposta nel Repertorio Ufficiale Band (se già presente su Ufficiale lo sovrascrive ed elimina questa copia personale)">⭐ Promuovi a Ufficiale</button>` : '';

  // Transpose buttons: solo per brani personali (l'ufficiale è protetto da modifiche dirette)
  const editingToolsHtml = (editing && !isInOfficial) ? `
        <button class="btn btn-secondary" onclick="transposeSong(-1)" title="Abbassa di 1 semitono (salva nel DB)">♭ -1</button>
        <button class="btn btn-secondary" onclick="transposeSong(1)" title="Alza di 1 semitono (salva nel DB)">♯ +1</button>` : '';

  let editingActionsHtml = '';
  if (editing) {
    if (isInOfficial) {
      const adminDeleteBtn = isAdmin ? `
        <button class="btn btn-danger" onclick="deleteSongWithUndo('${s.uuid}')" title="Elimina brano dal Repertorio Ufficiale Band (Richiede conferma Admin)">🗑️ Elimina dall'Ufficiale</button>` : '';
      editingActionsHtml = `
        <button class="btn btn-secondary" style="color: #38bdf8; border-color: #38bdf8; font-weight: 800;" onclick="openAddToSetlistModal('${s.uuid}')" title="Aggiungi questo brano a una scaletta">📑 + Scaletta</button>
        <button class="btn btn-primary" style="font-weight: 800; background: linear-gradient(135deg, #0284c7, #0369a1); border-color: #38bdf8;" onclick="forkSongToPersonalAndEdit('${s.uuid}')" title="Copia questo brano nel tuo repertorio personale per poterlo modificare liberamente">📋 Copia nel Personale per Modificare</button>
        ${adminDeleteBtn}`;
    } else {
      editingActionsHtml = `
        <button class="btn btn-secondary" style="color: #38bdf8; border-color: #38bdf8; font-weight: 800;" onclick="openAddToSetlistModal('${s.uuid}')" title="Aggiungi questo brano a una scaletta">📑 + Scaletta</button>
        ${promoteBtn}
        <button class="btn btn-secondary" onclick="openSongEditor()" title="Modifica testo o accordi">✏️ Modifica</button>
        <button class="btn btn-danger" onclick="deleteSongWithUndo('${s.uuid}')" title="Elimina brano con protezione e recupero immediato">🗑️</button>`;
    }
  }

  const officialBadgeHtml = isInOfficial ? '<span style="display:inline-block; background:rgba(56,189,248,0.15); color:#38bdf8; border:1px solid rgba(56,189,248,0.4); border-radius:4px; padding:1px 6px; font-size:11px; font-weight:800; margin-left:6px;">🔒 Ufficiale Protetto</span>' : '';
  const completenessBadgeHtml = renderCompletenessBadge(s);

  let completenessViewerActions = '';
  // Info versione precedente / UNDO: visibile SOLO agli amministratori
  if (isAdmin && s.previous_content) {
    completenessViewerActions += `<button class="btn btn-secondary" style="color: #fbbf24; border-color: #f59e0b; font-weight: 800;" onclick="undoSongInViewer('${s.uuid}')" title="Ripristina il contenuto e lo stato precedenti all'intervento AI">↩️ UNDO Versione Precedente</button>`;
  }
  // Completa con AI: visibile su brani personali O su brani ufficiali SOLO se Admin
  const canModifySong = !isInOfficial || isAdmin;
  if (canModifySong && !isMedleySong(s) && s.completeness_status === 'INCOMPLETO') {
    completenessViewerActions += `<button class="btn btn-primary" style="font-weight: 800; background: linear-gradient(135deg, #10b981, #059669); border-color: #34d399;" onclick="completeSongInViewerAi('${s.uuid}')" title="Completa le sezioni mancanti con AI Gemini confrontando con LRCLIB">🤖 Completa con AI</button>`;
  }
  if (!isMedleySong(s) && s.completeness_status !== 'DEFINITIVO' && (typeof isCurrentUserAdmin === 'function' && isCurrentUserAdmin())) {
    completenessViewerActions += `<button class="btn btn-secondary" style="color: #38bdf8; border-color: #38bdf8; font-weight: 800;" onclick="finalizeSongInViewer('${s.uuid}')" title="Rimuove i tag di autocompletamento e imposta lo stato a DEFINITIVO">🔒 Rendi Definitivo</button>`;
  }

  const headerHtml = `
    <div class="viewer-header">
      <div>
        <h2 style="font-size: 22px; font-weight: 900; color: #fff; display: flex; align-items: center; flex-wrap: wrap; gap: 8px;">
          <span>${escapeHtml(s.title)}</span>
          ${officialBadgeHtml}
          ${completenessBadgeHtml}
        </h2>
        <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
          <b>${escapeHtml(s.artist || 'Band')}</b> &bull; Tonalità: <code style="color:#ffd600; font-weight:700;">${toLatinKey(s.key_current)}</code>
          &bull; Tempo: <code style="color:#00e5ff;">${s.bpm || 120} BPM</code> &bull; Capo: <b>${s.capo || 0}°</b>
          &bull; Formato: <code style="color:#38bdf8;">${escapeHtml(state.activeDevice)}</code>
        </div>
      </div>
      <div class="viewer-tools">
        ${editingToolsHtml}
        ${completenessViewerActions}
        <button class="btn btn-secondary" onclick="adjustFontSize('lyrics', -1)" title="Riduci dimensione caratteri">A−</button>
        <button class="btn btn-secondary" onclick="adjustFontSize('lyrics', 1)" title="Ingrandisci dimensione caratteri">A+</button>
        <button class="btn btn-secondary" onclick="toggleScoreMode()">${modeLabel}</button>
        <button class="btn btn-secondary" onclick="toggleColumns()">${colsLabel}</button>
        <button class="btn btn-secondary" style="${viewTypeBtnStyle}" onclick="toggleSongViewType()" title="${viewTypeBtnTitle}">${viewTypeBtnText}</button>
        <button class="btn btn-primary" onclick="startSingleSongStage()">🎤 Palco</button>
        <button class="btn btn-secondary" style="color: #facc15; border-color: #eab308; font-weight: 800;" onclick="openCircleOfFifthsModal('${s.key_current || ''}')" title="Apri il Circolo delle Quinte per visualizzare relazioni armoniche e modulazioni">🎼 Circolo Quinte</button>
        <button class="btn btn-secondary" style="color: #ffd600; border-color: #ffd600; font-weight: 800;" onclick="openAiSuggestionsModal('${s.uuid}')" title="Suggerimenti live per musicisti o per l'intera band con AI Gemini Free">💡 Consigli Live</button>
        ${editingActionsHtml}
        ${isMedleyAml(s.aml_content) ? `<button class="btn btn-secondary" style="color: #c084fc; border-color: #a855f7; font-weight: 800;" onclick="openMedleyPageFormatterModal('${s.uuid}')" title="Formatta e impagina gli spezzoni del Medley su base dispositivo (tablet, smartphone, A4)">📐 Impagina Medley</button>` : ''}
        <button class="btn btn-secondary" style="color: #25D366; border-color: #25D366; font-weight: 800;" onclick="openShareA4Modal()" title="Condividi o stampa PDF in formato A4 con font personalizzato su WhatsApp per la band">📤 A4 / WhatsApp</button>
        <button class="btn btn-secondary" onclick="printA4()">🖨️ Stampa A4</button>
        <button class="btn btn-secondary" onclick="downloadPdf()">💾 Salva PDF</button>
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
    try {
      const formattedHtml = parseAmlForWeb(s.aml_content, hasChords);
      container.innerHTML = `
        ${headerHtml}
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid #334155; border-radius: 8px; padding: 6px 12px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: #94a3b8; flex-wrap: wrap; gap: 6px;">
          <span>📝 Modalità <b>Testo Web</b> attiva</span>
          <button type="button" class="btn btn-secondary" style="min-height: 28px; padding: 2px 10px; font-size: 11.5px; color: #38bdf8; border-color: #38bdf8; font-weight: 800;" onclick="setSongViewType('pdf')">📄 Torna a Spartito PDF</button>
        </div>
        <div class="lyrics-container" id="printable-lyrics">
          ${formattedHtml}
        </div>
      `;
    } catch (err) {
      console.error('Error rendering web lyrics view:', err);
      container.innerHTML = `
        ${headerHtml}
        <div class="lyrics-container" id="printable-lyrics">
          <pre style="white-space: pre-wrap; font-family: monospace;">${escapeHtml(s.aml_content || '')}</pre>
        </div>
      `;
    }
  }
}

// ----------------------------------------------------------------------------
// PDF PREVIEW OFFLINE CACHE (Session & Local Cache)
// ----------------------------------------------------------------------------
const _pdfPreviewMemoryCache = new Map();

function getPdfCacheKey(songUuid, device, hasChords, transpose = 0) {
  return `asma_pdf_cache_${songUuid}_${device}_${hasChords ? 'chords' : 'lyrics'}_t${transpose || 0}`;
}

function savePdfPreviewCache(songUuid, device, hasChords, transpose, data) {
  if (!songUuid || !data || !data.pages) return;
  const key = getPdfCacheKey(songUuid, device, hasChords, transpose);
  _pdfPreviewMemoryCache.set(key, data);
  try {
    sessionStorage.setItem(key, JSON.stringify(data));
  } catch (e) {
    // Quota reached or private mode; memory cache is still active
  }
}

function getPdfPreviewCache(songUuid, device, hasChords, transpose = 0) {
  if (!songUuid) return null;
  const key = getPdfCacheKey(songUuid, device, hasChords, transpose);
  if (_pdfPreviewMemoryCache.has(key)) {
    return _pdfPreviewMemoryCache.get(key);
  }
  try {
    const raw = sessionStorage.getItem(key);
    if (raw) {
      const parsed = JSON.parse(raw);
      _pdfPreviewMemoryCache.set(key, parsed);
      return parsed;
    }
  } catch (e) {}
  return null;
}

async function loadSongPdfPreview(songUuid, retryCount = 0) {
  const hasChords = state.scoreMode === 'chords';
  const container = document.getElementById('printable-lyrics');
  if (!container) return;

  // 1. Check if cached PDF preview is available
  const cachedData = getPdfPreviewCache(songUuid, state.activeDevice, hasChords, 0);
  let renderedFromCache = false;

  if (cachedData && cachedData.pages && cachedData.pages.length > 0) {
    if (state.selectedSong && state.selectedSong.uuid === songUuid && state.songViewType === 'pdf') {
      container.innerHTML = `
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 6px; padding: 6px 12px; margin-bottom: 10px; font-size: 12px; color: #38bdf8; display: flex; align-items: center; justify-content: space-between;">
          <span>📄 <b>Spartito PDF da Cache Offline</b> (${escapeHtml(cachedData.device || state.activeDevice)})</span>
          <span style="color: #94a3b8; font-size: 11px;">Caricato dalla memoria locale</span>
        </div>
        <div class="pdf-pages-container">
          ${cachedData.pages.map((b64, idx) => `
            <div class="pdf-page-wrapper">
              <img src="${b64}" class="pdf-page-img" alt="Pagina ${idx + 1} di ${cachedData.total_pages}" />
              <div class="pdf-page-badge">Pagina ${idx + 1} di ${cachedData.total_pages} &bull; Profilo ${escapeHtml(cachedData.device || state.activeDevice)}</div>
            </div>
          `).join('')}
        </div>
      `;
      renderedFromCache = true;
    }
  }

  try {
    const p = state.userPrefs || {};
    const userEmail = (state.currentUser && state.currentUser.email) || '';
    const userName = (state.currentUser && state.currentUser.name) || '';
    const dev = state.activeDevice || 'Huawei MediaPad M5';
    const url = `${API_BASE}/api/songs/${songUuid}/pdf/preview?chords=${hasChords}&device=${encodeURIComponent(dev)}&email=${encodeURIComponent(userEmail)}&user_name=${encodeURIComponent(userName)}&columns=${p.layout_columns || 1}&font_size=${p.layout_font_size || 12}&font_size_chords=${p.layout_font_size_chords || 13}&margin_lateral=${p.layout_margin_lateral || 10}&margin_top=${p.layout_margin_top || 10}&margin_bottom=${p.layout_margin_bottom || 14}&_v=${Date.now()}`;
    
    // Timeout a 8s per gestire risvegli o offline
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      savePdfPreviewCache(songUuid, state.activeDevice, hasChords, 0, data);
      if (state.selectedSong && state.selectedSong.uuid === songUuid && state.songViewType === 'pdf') {
        if (!data.pages || data.pages.length === 0) {
          throw new Error('Nessuna pagina generata');
        }
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
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    console.warn('PDF preview error:', err);
    if (renderedFromCache) return;
    if (retryCount < 1 && state.selectedSong && state.selectedSong.uuid === songUuid && state.songViewType === 'pdf' && navigator.onLine) {
      // 1 tentativo di riprova automatica dopo 1.2s se online per gestire cold-start
      setTimeout(() => loadSongPdfPreview(songUuid, retryCount + 1), 1200);
      return;
    }
    if (state.selectedSong && state.selectedSong.uuid === songUuid && state.songViewType === 'pdf') {
      const isOff = !navigator.onLine;
      container.innerHTML = `
        <div style="padding: 24px 16px; text-align: center; color: #ef4444; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 10px; margin: 16px 0;">
          <div style="font-size: 24px; margin-bottom: 8px;">${isOff ? '🟡' : '⚠️'}</div>
          <div style="font-size: 14px; font-weight: 700; margin-bottom: 6px;">${isOff ? 'Modalità Offline Attiva' : "Impossibile caricare l'anteprima PDF"}</div>
          <div style="font-size: 12px; color: #94a3b8; margin-bottom: 14px;">${isOff ? 'Il rendering grafico del PDF richiede il server o pre-cache, ma il brano è visualizzabile subito al 100% in formato Testo Web e in Modalità Palco.' : 'Il server cloud potrebbe essere in fase di risveglio o la connessione è rallentata.'}</div>
          <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
            <button class="btn btn-primary" style="font-weight: 800; min-height: 36px; padding: 4px 14px;" onclick="setSongViewType('web')">📝 Apri Vista Testo Web</button>
            <button class="btn btn-secondary" style="min-height: 36px; padding: 4px 14px;" onclick="startSingleSongStage()">🎤 Avvia Modalità Palco</button>
            ${!isOff ? `<button class="btn btn-secondary" style="font-weight: 700; min-height: 36px; padding: 4px 12px;" onclick="loadSongPdfPreview('${songUuid}', 0)">🔄 Riprova PDF</button>` : ''}
          </div>
        </div>
      `;
    }
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
async function openSongEditor() {
  if (!requireEditingMode()) return;
  const officialRep = state.repertoires.find(r => r.is_official);
  const isInOfficial = officialRep && officialRep.song_uuids && officialRep.song_uuids.includes(state.selectedSong?.uuid);
  if (isInOfficial) {
    if (!navigator.onLine) {
      showToast('⚠️ Sei in modalità Offline. Non è possibile modificare o clonare il Repertorio Ufficiale sul server finché non torni online.');
      return;
    }
    if (confirm(`I brani del Repertorio Ufficiale non possono essere modificati direttamente.\n\nVuoi creare subito una copia personale nel tuo repertorio da modificare e poi promuovere a ufficiale?`)) {
      await forkSongToPersonalAndEdit(state.selectedSong.uuid);
    }
    return;
  }
  state.isEditingSong = true;
  renderSongViewer();
}

function closeSongEditor() {
  state.isEditingSong = false;
  renderSongViewer();
}

async function saveSongEdit(downloadPdfAfter = false) {
  if (!state.selectedSong) return;
  const officialRep = state.repertoires.find(r => r.is_official);
  const isInOfficial = officialRep && officialRep.song_uuids && officialRep.song_uuids.includes(state.selectedSong?.uuid);
  if (isInOfficial) {
    showToast('⚠️ Non è possibile modificare direttamente il Repertorio Ufficiale. Crea una copia personale.');
    return;
  }
  const titleInput = document.getElementById('edit-song-title');
  const artistInput = document.getElementById('edit-song-artist');
  const keyInput = document.getElementById('edit-song-key');
  const bpmInput = document.getElementById('edit-song-bpm');
  const capoInput = document.getElementById('edit-song-capo');
  const amlInput = document.getElementById('edit-song-aml');

  const newKeyVal = keyInput ? keyInput.value.trim() : state.selectedSong.key_current;
  let newAmlVal = amlInput ? amlInput.value : state.selectedSong.aml_content;
  if (newAmlVal) {
    newAmlVal = newAmlVal.replace(/\[\/?AUTO-COMPLETATO\]/gi, '').trim();
  }
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

  // CASO B: Se siamo offline, salva subito in Bozza Locale Offline
  if (!navigator.onLine) {
    handleOfflineSaveEdit(oldUuid, payload, downloadPdfAfter);
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/songs/${oldUuid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json();
      removeOfflineDraft(oldUuid);
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
      saveOfflineSnapshot(SNAPSHOT_KEYS.SONGS, state.songs);
      state.isEditingSong = false;
      renderSongCards();
      renderSongViewer();
      showToast(`Brano "${state.selectedSong.title}" salvato nel DB ✓`);
      if (downloadPdfAfter) {
        await downloadPdf();
      }
      if (isMedleyAml(state.selectedSong?.aml_content)) {
        setTimeout(() => showMedleyPostSavePrompt(state.selectedSong), 300);
      }
    } else {
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || 'Errore durante il salvataggio del brano');
    }
  } catch (err) {
    console.warn('Network error while saving song, falling back to Offline Draft (Caso B):', err);
    handleOfflineSaveEdit(oldUuid, payload, downloadPdfAfter);
  }
}

function handleOfflineSaveEdit(songUuid, payload, downloadPdfAfter = false) {
  saveOfflineDraft(songUuid, payload);

  if (state.selectedSong && state.selectedSong.uuid === songUuid) {
    state.selectedSong = {
      ...state.selectedSong,
      title: payload.title,
      artist: payload.artist,
      key_current: payload.key_current,
      bpm: payload.bpm,
      capo: payload.capo,
      aml_content: payload.aml_content,
      _is_offline_draft: true
    };
  }
  const idx = (state.songs || []).findIndex(x => x.uuid === songUuid);
  if (idx !== -1) {
    state.songs[idx] = {
      ...state.songs[idx],
      title: payload.title,
      artist: payload.artist,
      key_current: payload.key_current,
      bpm: payload.bpm,
      capo: payload.capo,
      aml_content: payload.aml_content,
      _is_offline_draft: true
    };
    saveOfflineSnapshot(SNAPSHOT_KEYS.SONGS, state.songs);
  }

  state.isEditingSong = false;
  renderSongCards();
  renderSongViewer();
  updateConnectionStatus(false);
  showToast(`💾 Salvato in Bozza Locale Offline! Le modifiche sono attive su questo dispositivo e verranno sincronizzate non appena tornerai online.`);
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
  if (!requireEditingMode()) return;
  const form = document.getElementById('new-song-form');
  if (form) {
    const banner = document.getElementById('import-completeness-banner');
    if (banner) banner.style.display = 'none';
    state.importOriginalAml = '';
    state.importOfficialLyrics = '';
    state.importCompletenessStatus = '';
    state.importCompletenessRatio = 0;
    const repSelect = document.getElementById('new-song-repertoire');
    const workspaceReps = getWorkspaceRepertoires();
    // CRITICAL: Newly created or imported songs NEVER go to "Repertorio Ufficiale Band"!
    // They are always placed in personal repertoires and can only enter Official via promotion.
    const personalReps = (workspaceReps || []).filter(r => !r.is_official);
    if (repSelect) {
      if (personalReps.length > 0) {
        repSelect.innerHTML = personalReps.map(r => {
          const isSelected = (state.activeRepertoire === r.uuid) || isOwnPersonalRepertoire(r);
          return `<option value="${r.uuid}" ${isSelected ? 'selected' : ''}>${escapeHtml(r.name)} (Personale)</option>`;
        }).join('');
      } else {
        const uName = (state.currentUser && state.currentUser.name) || 'Personale';
        repSelect.innerHTML = `<option value="" selected>${escapeHtml(uName)} (Personale)</option>`;
      }
    }
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function hideNewSongForm() {
  const form = document.getElementById('new-song-form');
  if (form) form.style.display = 'none';
  const banner = document.getElementById('import-completeness-banner');
  if (banner) banner.style.display = 'none';
  state.importOriginalAml = '';
  state.importOfficialLyrics = '';
  state.importCompletenessStatus = '';
  state.importCompletenessRatio = 0;
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
    case 'medley':
    case 'start_of_song':
      openMedleyModal(textareaId);
      return;
    case 'scena':
      if (selectedText) {
        insertion = `{scena: ${selectedText}}\n`;
      } else {
        insertion = `{scena: 1}\n`;
        cursorOffset = 8;
      }
      break;
    case 'stacco':
      if (selectedText) {
        insertion = `{stacco: ${selectedText}}\n`;
      } else {
        insertion = `{stacco: Tutti}\n`;
        cursorOffset = 9;
      }
      break;
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
    case 'solo':
      if (selectedText) {
        insertion = `{solo: ${selectedText}}\n`;
      } else {
        insertion = `{solo: brass ensemble}\n`;
        cursorOffset = 7;
      }
      break;
    case 'comment':
      if (selectedText) {
        insertion = `{c: ${selectedText}}`;
      } else {
        insertion = `{c: }`;
        cursorOffset = 4;
      }
      break;
    case 'colb':
      insertion = `\n{colb}\n`;
      break;
    case 'riga_bianca':
      insertion = `\n{riga_bianca}\n`;
      break;
    case 'np':
    case 'salto_pagina':
    case 'page_break':
      insertion = `\n{np}\n`;
      break;
    default:
      insertion = `{${type}}\n`;
  }

  textarea.value = val.substring(0, start) + insertion + val.substring(end);
  const newPos = cursorOffset > 0 ? (start + cursorOffset) : (start + insertion.length);
  textarea.selectionStart = textarea.selectionEnd = newPos;
  textarea.focus();
}

function openMedleyModal(textareaId = 'edit-song-aml') {
  const existingModal = document.getElementById('medley-builder-modal');
  if (existingModal) existingModal.remove();

  const textarea = document.getElementById(textareaId);
  const currentText = textarea ? textarea.value : '';
  const matches = currentText.match(/\{(?:start_of_song|sos|start_of_medley)\b/gi) || [];
  const nextNum = Math.min(matches.length + 1, 20);

  const modalHtml = `
    <div id="medley-builder-modal" class="modal-backdrop" style="position: fixed; inset: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 9999; padding: 12px; backdrop-filter: blur(4px);">
      <div class="modal-card" style="background: #0f172a; border: 1px solid #7c3aed; border-radius: 12px; width: 100%; max-width: 480px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.8);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <h3 style="margin: 0; font-size: 17px; font-weight: 900; color: #c084fc; display: flex; align-items: center; gap: 6px;">
            <span>🎶</span> Nuovo Spezzone Medley (${nextNum}/20)
          </h3>
          <button type="button" class="btn btn-secondary" style="min-height: 28px; padding: 2px 8px; font-size: 13px;" onclick="document.getElementById('medley-builder-modal').remove()">✕</button>
        </div>
        <p style="font-size: 12px; color: #94a3b8; margin: 0 0 14px 0; line-height: 1.4;">
          Inserisci un brano indipendente nel tuo Medley con titolo, artista e tonalità dedicati. Sul PDF e a schermo avrà un <b>colore alternato</b> distintivo e una <b>riga di separazione</b>.
        </p>

        <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px;">
          <div>
            <label style="font-size: 11px; font-weight: 700; color: #cbd5e1;">Titolo Brano *</label>
            <input type="text" id="medley-input-title" class="search-input" style="width: 100%; margin-top: 3px;" placeholder="Es. Gloria, Certe Notti, Ti amo..." autofocus>
          </div>
          <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 8px;">
            <div>
              <label style="font-size: 11px; font-weight: 700; color: #cbd5e1;">Artista (opzionale)</label>
              <input type="text" id="medley-input-artist" class="search-input" style="width: 100%; margin-top: 3px;" placeholder="Es. Umberto Tozzi">
            </div>
            <div>
              <label style="font-size: 11px; font-weight: 700; color: #cbd5e1;">Tonalità</label>
              <input type="text" id="medley-input-key" class="search-input" style="width: 100%; margin-top: 3px; font-weight: 800; color: #ffd600;" placeholder="Es. MI, DO...">
            </div>
          </div>
          <div>
            <label style="font-size: 11px; font-weight: 700; color: #cbd5e1;">Struttura iniziale dello spezzone</label>
            <select id="medley-input-structure" class="search-input" style="width: 100%; margin-top: 3px; background: #1e293b; color: #fff;">
              <option value="standard" selected>Intro + Strofa + Ritornello</option>
              <option value="chorus_only">Solo Ritornello</option>
              <option value="intro_chorus">Intro + Ritornello</option>
              <option value="empty">Vuoto (solo direttive {sos} e {eos})</option>
            </select>
          </div>
        </div>

        <div style="display: flex; gap: 8px; justify-content: flex-end;">
          <button type="button" class="btn btn-secondary" onclick="document.getElementById('medley-builder-modal').remove()">Annulla</button>
          <button type="button" class="btn btn-primary" style="background: linear-gradient(135deg, #7c3aed, #9333ea); border-color: #a855f7; font-weight: 800;" onclick="confirmInsertMedleyFragment('${textareaId}')">➕ Inserisci Spezzone</button>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', modalHtml);
  setTimeout(() => {
    const titleInput = document.getElementById('medley-input-title');
    if (titleInput) titleInput.focus();
  }, 50);
}

function confirmInsertMedleyFragment(textareaId) {
  const titleInput = document.getElementById('medley-input-title');
  const artistInput = document.getElementById('medley-input-artist');
  const keyInput = document.getElementById('medley-input-key');
  const structInput = document.getElementById('medley-input-structure');

  const title = (titleInput?.value || '').trim() || 'Spezzone Medley';
  const artist = (artistInput?.value || '').trim();
  const key = (keyInput?.value || '').trim();
  const struct = structInput?.value || 'standard';

  const parts = [title];
  if (artist) parts.push(artist);
  if (key) parts.push(key);
  const directiveVal = parts.join(' | ');

  let body = '';
  const keyChord = key || 'DO';
  if (struct === 'standard') {
    body = `[INTRO]\n| ${keyChord} | SOL | LAm | FA |\n\n{sov}\n[${keyChord}]Testo della strofa...\n{eov}\n\n{soc}\n[FA]Testo del ritornello... [SOL]\n{eoc}\n`;
  } else if (struct === 'chorus_only') {
    body = `{soc}\n[${keyChord}]Testo del ritornello...\n{eoc}\n`;
  } else if (struct === 'intro_chorus') {
    body = `[INTRO]\n| ${keyChord} | FA | SOL |\n\n{soc}\n[${keyChord}]Testo del ritornello...\n{eoc}\n`;
  }

  const snippet = `\n{start_of_song: ${directiveVal}}\n${body}{end_of_song}\n`;

  const textarea = document.getElementById(textareaId);
  if (textarea) {
    const start = textarea.selectionStart || 0;
    const end = textarea.selectionEnd || 0;
    const val = textarea.value;
    textarea.value = val.substring(0, start) + snippet + val.substring(end);
    textarea.selectionStart = textarea.selectionEnd = start + snippet.length;
    textarea.focus();
  }

  document.getElementById('medley-builder-modal')?.remove();
  showToast(`🎶 Spezzone Medley "${title}" inserito!`);
}

// ----------------------------------------------------------------------------
// MEDLEY DEVICE-AWARE PAGE FORMATTING ENGINE
// ----------------------------------------------------------------------------

function isMedleyAml(amlText) {
  if (!amlText) return false;
  return /\{(?:start_of_song|sos|start_of_medley|start_of_medley_song|soms)\b/i.test(amlText);
}

function showMedleyPostSavePrompt(song) {
  if (!song) return;
  const existing = document.getElementById('medley-post-save-prompt');
  if (existing) existing.remove();

  const devName = state.activeDevice || 'Tablet';
  const modal = document.createElement('div');
  modal.id = 'medley-post-save-prompt';
  modal.className = 'modal-backdrop';
  modal.style.cssText = 'position: fixed; inset: 0; background: rgba(0,0,0,0.78); display: flex; align-items: center; justify-content: center; z-index: 10000; padding: 14px; backdrop-filter: blur(4px);';
  modal.innerHTML = `
    <div style="background: #0f172a; border: 2px solid #a855f7; border-radius: 12px; width: 100%; max-width: 520px; box-shadow: 0 20px 40px rgba(0,0,0,0.8); overflow: hidden;">
      <div style="background: linear-gradient(135deg, rgba(168, 85, 247, 0.25), rgba(56, 189, 248, 0.15)); padding: 16px 20px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center;">
        <div style="font-weight: 900; font-size: 16px; color: #c084fc; display: flex; align-items: center; gap: 8px;">
          <span>🎶</span> Medley Salvato nel Personale!
        </div>
        <button type="button" class="btn btn-secondary" style="min-height: 28px; padding: 2px 8px; font-size: 13px;" onclick="document.getElementById('medley-post-save-prompt').remove()">✕</button>
      </div>
      <div style="padding: 20px; font-size: 13.5px; color: #cbd5e1; line-height: 1.55;">
        <p style="margin-top: 0; font-weight: 700; color: #f8fafc; font-size: 15px;">
          "${escapeHtml(song.title)}" è composto da vari spezzoni di brani.
        </p>
        <p style="margin: 10px 0; color: #94a3b8;">
          Per garantire la migliore leggibilità dal vivo sul tuo dispositivo <b>${escapeHtml(devName)}</b>, desideri formattare e distribuire ora gli spezzoni sulle pagine?
        </p>
        <div style="background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38bdf8; padding: 8px 12px; border-radius: 0 6px 6px 0; margin: 14px 0 18px 0; font-size: 12px; color: #94a3b8;">
          💡 <i>Come sempre, potrai visualizzare lo spartito impaginato per il tuo dispositivo in uso o stamparne una copia in formato <b>A4</b> tramite "🖨️ Stampa A4".</i>
        </div>
        <div style="display: flex; gap: 10px; justify-content: flex-end; flex-wrap: wrap;">
          <button type="button" class="btn btn-secondary" style="min-height: 40px; padding: 4px 14px;" onclick="document.getElementById('medley-post-save-prompt').remove()">👁️ Visualizza Spartito</button>
          <button type="button" class="btn btn-primary" style="background: linear-gradient(135deg, #7c3aed, #9333ea); border-color: #a855f7; font-weight: 800; min-height: 40px; padding: 4px 18px;" onclick="document.getElementById('medley-post-save-prompt').remove(); openMedleyPageFormatterModal('${song.uuid}')">📐 Formatta Pagine per ${escapeHtml(devName)}</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

function splitMedleyAmlClient(aml) {
  if (!aml) return { header: '', fragments: [] };
  const pattern = /(\n?[ \t]*\{(?:np|new_page|page_break|salto_pagina|salto_di_pagina)[^\}]*\}\s*)?(\{(?:start_of_song|sos|start_of_medley|start_of_medley_song|soms)(?:[:\s]\s*([^\}]+))?\})/gi;
  const matches = [];
  let m;
  while ((m = pattern.exec(aml)) !== null) {
    matches.push({
      start: m.index,
      length: m[0].length,
      hasNp: !!m[1],
      npLength: m[1] ? m[1].length : 0,
      tagVal: m[3] ? m[3].trim() : ''
    });
  }
  if (!matches.length) return { header: aml, fragments: [] };

  const header = aml.substring(0, matches[0].start).trimEnd();
  const fragments = [];

  for (let i = 0; i < matches.length; i++) {
    const cur = matches[i];
    const nextStart = (i + 1 < matches.length) ? matches[i + 1].start : aml.length;
    const bodyStart = cur.start + cur.npLength;
    let rawContent = aml.substring(bodyStart, nextStart).trimEnd();
    rawContent = rawContent.replace(/\n?[ \t]*\{(?:np|new_page|page_break|salto_pagina|salto_di_pagina)[^\}]*\}\s*$/i, '').trimEnd();

    let title = '', artist = '', key = '';
    const val = cur.tagVal;
    if (val.includes('|')) {
      const parts = val.split('|').map(s => s.trim());
      title = parts[0] || '';
      artist = parts[1] || '';
      key = parts[2] || '';
    } else if (val.includes(' - ')) {
      const parts = val.split(' - ').map(s => s.trim());
      title = parts[0] || '';
      artist = parts[1] || '';
    } else {
      title = val;
    }

    const lines = rawContent.split('\n').filter(l => l.trim().length > 0);
    fragments.push({
      index: i + 1,
      title: title || `Spezzone ${i + 1}`,
      artist: artist,
      key: key,
      hasPageBreak: cur.hasNp,
      rawContent: rawContent,
      lineCount: lines.length,
      assignedPage: 1
    });
  }
  return { header, fragments };
}

function assembleMedleyAmlClient(header, fragments, breakIndices) {
  const parts = header ? [header] : [];
  let curPage = 1;
  fragments.forEach((f, idx) => {
    const isNewPage = idx > 0 && breakIndices.has(f.index);
    if (isNewPage) {
      curPage++;
      parts.push(`\n\n{np}\n${f.rawContent}`);
    } else {
      parts.push(`\n\n${f.rawContent}`);
    }
    f.assignedPage = curPage;
    f.hasPageBreak = isNewPage;
  });
  return parts.join('').trim() + '\n';
}

function getDeviceCapacity(deviceName) {
  const devStr = (deviceName || '').toLowerCase();
  if (devStr.includes('smartphone') || devStr.includes('pixel') || devStr.includes('iphone') || devStr.includes('oppo')) {
    return { type: 'smartphone', cap: 22, cols: 1, label: 'Smartphone (1 Colonna • Capienza ~22 righe)' };
  } else if (devStr.includes('a4') || devStr.includes('foglio')) {
    return { type: 'printable_a4', cap: 40, cols: 1, label: 'Foglio A4 Stampabile (Capienza ~40 righe)' };
  } else {
    return { type: 'tablet', cap: 52, cols: 2, label: 'Tablet (2 Colonne • Capienza ~52 righe)' };
  }
}

let medleyFormatterState = null;

function openMedleyPageFormatterModal(songUuid = null, textareaId = 'edit-song-aml') {
  const existing = document.getElementById('medley-page-formatter-modal');
  if (existing) existing.remove();

  // Find source AML
  let sourceAml = '';
  let targetSong = null;
  const textarea = document.getElementById(textareaId);

  if (songUuid) {
    targetSong = (state.songs || []).find(s => s.uuid === songUuid) || state.selectedSong;
    if (targetSong) sourceAml = targetSong.aml_content || '';
  } else if (state.isEditingSong && textarea) {
    sourceAml = textarea.value || '';
    targetSong = state.selectedSong;
  } else if (textarea) {
    sourceAml = textarea.value || '';
  } else if (state.selectedSong) {
    targetSong = state.selectedSong;
    sourceAml = state.selectedSong.aml_content || '';
  }

  if (!isMedleyAml(sourceAml)) {
    showToast('⚠️ Nessuno spezzone medley rilevato. Inserisci prima almeno uno spezzone con "🎶 + Spezzone Medley".');
    return;
  }

  const { header, fragments } = splitMedleyAmlClient(sourceAml);
  if (!fragments || fragments.length === 0) {
    showToast('⚠️ Impossibile analizzare gli spezzoni del Medley.');
    return;
  }

  const currentDev = state.activeDevice || (state.devicesList && state.devicesList[0]?.name) || 'Huawei MediaPad M5';
  const customBreaks = new Set(fragments.filter(f => f.hasPageBreak).map(f => f.index));

  medleyFormatterState = {
    songUuid: songUuid || targetSong?.uuid || null,
    songTitle: targetSong?.title || (document.getElementById('edit-song-title')?.value) || 'Medley',
    textareaId: textareaId,
    targetDevice: currentDev,
    header: header,
    fragments: fragments,
    customBreaks: customBreaks,
    strategy: customBreaks.size > 0 ? 'custom' : 'smart_fit',
    showPdfPreview: false
  };

  calculateMedleyPageAllocation();

  const devOptionsHtml = (state.devicesList || []).map(d => {
    const isSel = d.name === medleyFormatterState.targetDevice;
    const isAct = d.name === state.activeDevice ? ' ★ (In Uso)' : '';
    return `<option value="${escapeHtml(d.name)}" ${isSel ? 'selected' : ''}>${escapeHtml(d.name)}${isAct}</option>`;
  }).join('');

  const modalHtml = `
    <div id="medley-page-formatter-modal" class="modal-backdrop" style="position: fixed; inset: 0; background: rgba(0,0,0,0.85); display: flex; align-items: center; justify-content: center; z-index: 10000; padding: 12px; backdrop-filter: blur(5px);">
      <div class="modal-card" style="background: #0b1329; border: 2px solid #a855f7; border-radius: 14px; width: 100%; max-width: 720px; max-height: 92vh; display: flex; flex-direction: column; box-shadow: 0 25px 50px rgba(0,0,0,0.9); overflow: hidden;">
        
        <!-- HEADER -->
        <div style="background: linear-gradient(135deg, rgba(168, 85, 247, 0.25), rgba(56, 189, 248, 0.15)); padding: 14px 18px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0;">
          <div>
            <h3 style="margin: 0; font-size: 17px; font-weight: 900; color: #c084fc; display: flex; align-items: center; gap: 8px;">
              <span>📐</span> Impaginazione Medley su Base Dispositivo
            </h3>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">
              Brano: <b style="color: #fff;">${escapeHtml(medleyFormatterState.songTitle)}</b> &bull; ${medleyFormatterState.fragments.length} spezzoni rilevati
            </div>
          </div>
          <button type="button" class="btn btn-secondary" style="min-height: 30px; padding: 2px 10px; font-size: 13px;" onclick="closeMedleyPageFormatterModal()">✕</button>
        </div>

        <!-- BODY SCROLLABLE -->
        <div style="padding: 16px 18px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 14px;">
          
          <!-- SELETTORE DISPOSITIVO -->
          <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid #334155; border-radius: 8px; padding: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 6px;">
              <label style="font-size: 12px; font-weight: 800; color: #cbd5e1;">📱 Dispositivo Target di Formattazione:</label>
              <span id="medley-fmt-device-badge" class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35); font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px;">
                ${escapeHtml(getDeviceCapacity(medleyFormatterState.targetDevice).label)}
              </span>
            </div>
            <select id="medley-fmt-device-select" class="search-input" style="width: 100%; font-size: 13.5px; background: #1e293b; color: #fff; font-weight: 700;" onchange="onMedleyFormatterDeviceChanged(this.value)">
              ${devOptionsHtml}
            </select>
            <div style="font-size: 11.5px; color: #94a3b8; margin-top: 6px;">
              Tutti i margini, colonne e dimensione dei caratteri vengono calcolati specificamente per questo schermo.
            </div>
          </div>

          <!-- STRATEGIE DI IMPAGINAZIONE -->
          <div>
            <label style="font-size: 12px; font-weight: 800; color: #cbd5e1; margin-bottom: 6px; display: block;">⚡ Strategia di Distribuzione Pagine:</label>
            <div style="display: flex; gap: 6px; flex-wrap: wrap;">
              <button type="button" id="btn-strat-smart" class="btn ${medleyFormatterState.strategy === 'smart_fit' ? 'btn-primary' : 'btn-secondary'}" style="font-size: 12px; padding: 6px 12px; font-weight: 800;" onclick="applyMedleyStrategy('smart_fit')">
                ⚡ Compattazione Ottimizzata Dispositivo
              </button>
              <button type="button" id="btn-strat-one" class="btn ${medleyFormatterState.strategy === 'one_per_page' ? 'btn-primary' : 'btn-secondary'}" style="font-size: 12px; padding: 6px 12px; font-weight: 800;" onclick="applyMedleyStrategy('one_per_page')">
                🎯 1 Spezzone per Pagina
              </button>
              <button type="button" id="btn-strat-clear" class="btn ${medleyFormatterState.strategy === 'clear' ? 'btn-primary' : 'btn-secondary'}" style="font-size: 12px; padding: 6px 12px; font-weight: 800;" onclick="applyMedleyStrategy('clear')">
                🔄 Flusso Continuo Libero
              </button>
            </div>
          </div>

          <!-- RIEPILOGO PAGINE & FLOW VISUALE -->
          <div id="medley-fmt-summary-box" style="background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 8px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <!-- Riempito dinamicamente -->
          </div>

          <!-- LISTA SPEZZONI INTERATTIVA -->
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
              <label style="font-size: 12px; font-weight: 800; color: #cbd5e1;">🎶 Spezzoni del Medley & Salti Pagina Manuali:</label>
              <span style="font-size: 11px; color: #94a3b8;">Tocca un pulsante per forzare o togliere il salto pagina</span>
            </div>
            <div id="medley-fmt-fragments-list" style="display: flex; flex-direction: column; gap: 8px;">
              <!-- Riempito dinamicamente -->
            </div>
          </div>

          <!-- NOTA DI COMPATIBILITA A4 -->
          <div style="background: rgba(37, 211, 102, 0.08); border-left: 3px solid #25D366; border-radius: 0 6px 6px 0; padding: 8px 12px; font-size: 12px; color: #cbd5e1; line-height: 1.45;">
            🖨️ <b>Flessibilità Palco & Stampa A4:</b> Questa formattazione personalizza l'esperienza visiva per <b>${escapeHtml(medleyFormatterState.targetDevice)}</b>. Come per tutti gli altri brani di ASMA, puoi sempre visualizzare o stampare la copia in formato standard <b>Foglio A4</b> tramite il pulsante <b>"🖨️ Stampa A4"</b> o <b>"📤 A4 / WhatsApp"</b>.
          </div>

          <!-- ANTEPRIMA PDF EMBEDDED TOGGLE -->
          <div style="border-top: 1px solid #334155; padding-top: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <button type="button" class="btn btn-secondary" style="font-size: 12px; padding: 4px 12px; color: #38bdf8; border-color: #38bdf8; font-weight: 800;" onclick="toggleMedleyPdfPreview()">
                👁️ Mostra / Ricarica Anteprima Reale PDF (${escapeHtml(medleyFormatterState.targetDevice)})
              </button>
            </div>
            <div id="medley-fmt-pdf-preview" style="display: none; margin-top: 10px; max-height: 280px; overflow-y: auto; background: #020617; border: 1px solid #334155; border-radius: 8px; padding: 10px;">
              <div style="text-align: center; color: #94a3b8; padding: 20px;">Tocca il pulsante sopra per generare l'anteprima reale ad alta risoluzione.</div>
            </div>
          </div>

        </div>

        <!-- FOOTER ACTIONS -->
        <div style="background: #0f172a; padding: 12px 18px; border-top: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; flex-shrink: 0;">
          <button type="button" class="btn btn-secondary" onclick="closeMedleyPageFormatterModal()">✕ Chiudi</button>
          <button type="button" class="btn btn-success" style="font-weight: 800; min-height: 40px; padding: 6px 18px; background: linear-gradient(135deg, #059669, #10b981); border-color: #34d399;" onclick="saveAndApplyMedleyFormatting()">
            💾 Applica & Salva Formattazione Pagine
          </button>
        </div>

      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', modalHtml);
  renderMedleyFormatterFragmentCards();
}

function calculateMedleyPageAllocation() {
  if (!medleyFormatterState) return;
  const dev = getDeviceCapacity(medleyFormatterState.targetDevice);
  const cap = dev.cap;
  const frags = medleyFormatterState.fragments;

  const breaks = new Set();
  if (medleyFormatterState.strategy === 'one_per_page') {
    for (let i = 2; i <= frags.length; i++) breaks.add(i);
  } else if (medleyFormatterState.strategy === 'smart_fit') {
    let curLines = 0;
    frags.forEach((f, idx) => {
      const needed = f.lineCount + 3;
      if (idx === 0) {
        curLines = needed;
      } else {
        if (curLines + needed > cap) {
          breaks.add(f.index);
          curLines = needed;
        } else {
          curLines += needed;
        }
      }
    });
  } else if (medleyFormatterState.strategy === 'clear') {
    // None
  } else if (medleyFormatterState.strategy === 'custom') {
    medleyFormatterState.customBreaks.forEach(b => { if (b > 1) breaks.add(b); });
  }

  let curPage = 1;
  frags.forEach((f, idx) => {
    if (idx > 0 && breaks.has(f.index)) {
      curPage++;
    }
    f.assignedPage = curPage;
    f.hasPageBreak = breaks.has(f.index);
  });
  medleyFormatterState.totalPages = curPage;
  medleyFormatterState.activeBreaks = breaks;
}

function renderMedleyFormatterFragmentCards() {
  if (!medleyFormatterState) return;
  calculateMedleyPageAllocation();

  // Summary box
  const summaryBox = document.getElementById('medley-fmt-summary-box');
  if (summaryBox) {
    const dev = getDeviceCapacity(medleyFormatterState.targetDevice);
    summaryBox.innerHTML = `
      <div style="font-size: 13px; font-weight: 800; color: #fff;">
        📄 Totale Pagine Medley: <span style="color: #ffd600; font-size: 16px;">${medleyFormatterState.totalPages} pagine</span>
        <span style="font-weight: 500; font-size: 12px; color: #94a3b8; margin-left: 6px;">(${escapeHtml(medleyFormatterState.targetDevice)})</span>
      </div>
      <div style="font-size: 11.5px; color: #cbd5e1;">
        Capienza schermo: <b>~${dev.cap} righe/pag.</b> (${dev.cols} ${dev.cols === 1 ? 'colonna' : 'colonne'})
      </div>
    `;
  }

  // Update strategy buttons active state
  const bSmart = document.getElementById('btn-strat-smart');
  const bOne = document.getElementById('btn-strat-one');
  const bClear = document.getElementById('btn-strat-clear');
  if (bSmart) bSmart.className = `btn ${medleyFormatterState.strategy === 'smart_fit' ? 'btn-primary' : 'btn-secondary'}`;
  if (bOne) bOne.className = `btn ${medleyFormatterState.strategy === 'one_per_page' ? 'btn-primary' : 'btn-secondary'}`;
  if (bClear) bClear.className = `btn ${medleyFormatterState.strategy === 'clear' ? 'btn-primary' : 'btn-secondary'}`;

  // Fragment cards
  const container = document.getElementById('medley-fmt-fragments-list');
  if (!container) return;

  const MEDLEY_COLORS_FMT = [
    { bg: 'rgba(2, 132, 199, 0.22)', border: '#0284c7', text: '#38bdf8' },
    { bg: 'rgba(217, 119, 6, 0.22)', border: '#d97706', text: '#fbbf24' },
    { bg: 'rgba(5, 150, 105, 0.22)', border: '#059669', text: '#34d399' },
    { bg: 'rgba(124, 58, 237, 0.22)', border: '#7c3aed', text: '#c084fc' },
    { bg: 'rgba(225, 29, 72, 0.22)', border: '#e11d48', text: '#fb7185' },
    { bg: 'rgba(8, 145, 178, 0.22)', border: '#0891b2', text: '#22d3ee' },
    { bg: 'rgba(234, 88, 12, 0.22)', border: '#ea580c', text: '#fb923c' },
    { bg: 'rgba(79, 70, 229, 0.22)', border: '#4f46e5', text: '#818cf8' },
    { bg: 'rgba(22, 163, 74, 0.22)', border: '#16a34a', text: '#4ade80' },
    { bg: 'rgba(219, 39, 119, 0.22)', border: '#db2777', text: '#f472b6' }
  ];

  container.innerHTML = medleyFormatterState.fragments.map((f, idx) => {
    const col = MEDLEY_COLORS_FMT[(idx) % MEDLEY_COLORS_FMT.length];
    const isFirst = idx === 0;

    let breakBtnHtml = '';
    if (isFirst) {
      breakBtnHtml = `<span style="font-size: 11.5px; font-weight: 800; color: #10b981; background: rgba(16, 185, 129, 0.15); padding: 3px 8px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.4);">📌 Inizio Medley (Pagina 1)</span>`;
    } else {
      if (f.hasPageBreak) {
        breakBtnHtml = `
          <button type="button" class="btn btn-primary" style="background: rgba(245, 158, 11, 0.25); border-color: #f59e0b; color: #fbbf24; font-weight: 800; font-size: 11.5px; padding: 4px 10px;" onclick="toggleMedleyFragmentBreak(${f.index})" title="Tocca per unire alla pagina precedente">
            📄 Nuova Pagina (Pag. ${f.assignedPage})
          </button>`;
      } else {
        breakBtnHtml = `
          <button type="button" class="btn btn-secondary" style="color: #94a3b8; font-size: 11.5px; padding: 4px 10px;" onclick="toggleMedleyFragmentBreak(${f.index})" title="Tocca per iniziare questo spezzone su una nuova pagina">
            🔗 Unito su Pagina ${f.assignedPage}
          </button>`;
      }
    }

    const keyBadge = f.key ? `<span style="color: #ffd600; font-weight: 800; font-size: 11.5px; margin-left: 6px;">[${escapeHtml(toLatinKey(f.key))}]</span>` : '';
    const artistStr = f.artist ? `<span style="color: #94a3b8; font-size: 11.5px; margin-left: 6px;">&bull; ${escapeHtml(f.artist)}</span>` : '';

    return `
      <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid ${col.border}; border-left: 4px solid ${col.border}; border-radius: 6px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
        <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px;">
          <span style="background: ${col.bg}; color: ${col.text}; font-weight: 900; font-size: 12px; padding: 2px 7px; border-radius: 4px;">🎵 ${f.index}</span>
          <span style="font-weight: 800; font-size: 13.5px; color: #fff;">${escapeHtml(f.title.toUpperCase())}</span>
          ${keyBadge}
          ${artistStr}
          <span style="font-size: 10.5px; color: #64748b; margin-left: 4px;">(~${f.lineCount} righe)</span>
        </div>
        <div>
          ${breakBtnHtml}
        </div>
      </div>
    `;
  }).join('');
}

function applyMedleyStrategy(strategy) {
  if (!medleyFormatterState) return;
  medleyFormatterState.strategy = strategy;
  if (strategy === 'clear') {
    medleyFormatterState.customBreaks.clear();
  }
  renderMedleyFormatterFragmentCards();
}

function toggleMedleyFragmentBreak(fragIndex) {
  if (!medleyFormatterState) return;
  medleyFormatterState.strategy = 'custom';
  if (medleyFormatterState.customBreaks.has(fragIndex)) {
    medleyFormatterState.customBreaks.delete(fragIndex);
  } else {
    medleyFormatterState.customBreaks.add(fragIndex);
  }
  renderMedleyFormatterFragmentCards();
}

function onMedleyFormatterDeviceChanged(newDevice) {
  if (!medleyFormatterState) return;
  medleyFormatterState.targetDevice = newDevice;
  const dev = getDeviceCapacity(newDevice);
  const badge = document.getElementById('medley-fmt-device-badge');
  if (badge) badge.textContent = dev.label;
  renderMedleyFormatterFragmentCards();
}

async function toggleMedleyPdfPreview() {
  if (!medleyFormatterState) return;
  const container = document.getElementById('medley-fmt-pdf-preview');
  if (!container) return;

  if (container.style.display !== 'none' && medleyFormatterState.showPdfPreview) {
    container.style.display = 'none';
    medleyFormatterState.showPdfPreview = false;
    return;
  }

  container.style.display = 'block';
  medleyFormatterState.showPdfPreview = true;
  container.innerHTML = `<div style="text-align: center; color: #38bdf8; padding: 20px;">⏳ Generazione anteprima reale PDF per ${escapeHtml(medleyFormatterState.targetDevice)}...</div>`;

  try {
    const formattedAml = assembleMedleyAmlClient(medleyFormatterState.header, medleyFormatterState.fragments, medleyFormatterState.activeBreaks);
    
    // We send to backend format API or preview
    await fetch(`${API_BASE}/api/medley/format-pages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        aml_content: formattedAml,
        device: medleyFormatterState.targetDevice,
        strategy: 'custom',
        custom_breaks: Array.from(medleyFormatterState.activeBreaks)
      })
    });

    if (medleyFormatterState.songUuid) {
      // If we have a saved song, we can fetch real page preview images!
      const hasChords = state.scoreMode === 'chords';
      const previewUrl = `${API_BASE}/api/songs/${medleyFormatterState.songUuid}/pdf/preview?chords=${hasChords}&device=${encodeURIComponent(medleyFormatterState.targetDevice)}&email=${encodeURIComponent(state.currentUser?.email || '')}&_v=${Date.now()}`;
      
      const pRes = await fetch(previewUrl);
      if (pRes.ok) {
        const pData = await pRes.json();
        if (pData.pages && pData.pages.length > 0) {
          container.innerHTML = `
            <div style="font-size: 11.5px; color: #ffd600; font-weight: 700; margin-bottom: 8px;">
              📄 Anteprima Reale PDF (${pData.total_pages} pagine su ${escapeHtml(pData.device)}):
            </div>
            <div style="display: flex; gap: 10px; overflow-x: auto; padding-bottom: 6px;">
              ${pData.pages.map((b64, idx) => `
                <div style="flex: 0 0 160px; text-align: center;">
                  <img src="${b64}" style="width: 100%; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.6);" alt="Pagina ${idx+1}">
                  <div style="font-size: 10.5px; color: #94a3b8; margin-top: 3px;">Pagina ${idx+1}</div>
                </div>
              `).join('')}
            </div>
          `;
          return;
        }
      }
    }

    // Fallback info if preview images not ready
    container.innerHTML = `
      <div style="font-size: 12px; color: #cbd5e1; padding: 12px; background: rgba(56, 189, 248, 0.08); border-radius: 6px;">
        ✅ Struttura pagine validata: <b>${medleyFormatterState.totalPages} pagine</b> generate per <b>${escapeHtml(medleyFormatterState.targetDevice)}</b>.
        Tocca "💾 Applica & Salva Formattazione" per visualizzarle a schermo intero nel visualizzatore PDF.
      </div>
    `;
  } catch (err) {
    console.warn('Medley preview error:', err);
    container.innerHTML = `<div style="color: #ef4444; padding: 10px; font-size: 12px;">⚠️ Impossibile generare anteprima immagini al volo. La formattazione verrà applicata al salvataggio.</div>`;
  }
}

async function saveAndApplyMedleyFormatting() {
  if (!medleyFormatterState) return;

  const formattedAml = assembleMedleyAmlClient(
    medleyFormatterState.header,
    medleyFormatterState.fragments,
    medleyFormatterState.activeBreaks
  );

  const textarea = document.getElementById(medleyFormatterState.textareaId);
  if (textarea) {
    textarea.value = formattedAml;
  }

  const targetDev = medleyFormatterState.targetDevice;
  const totalPages = medleyFormatterState.totalPages;
  const songUuid = medleyFormatterState.songUuid;

  if (songUuid) {
    try {
      showToast('Salvataggio formattazione pagine in corso...');
      const payload = {
        strategy: 'custom',
        device: targetDev,
        custom_breaks: Array.from(medleyFormatterState.activeBreaks),
        aml_content: formattedAml,
        user_email: state.currentUser?.email || 'musicista@band.org',
        user_name: state.currentUser?.name || 'Musicista',
        repertoire_uuid: state.activeRepertoire !== '__ALL__' ? state.activeRepertoire : null,
        save_to_db: true
      };

      const res = await fetch(`${API_BASE}/api/songs/${songUuid}/format-medley-pages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        if (data.song) {
          state.selectedSong = data.song;
          const idx = (state.songs || []).findIndex(x => x.uuid === songUuid);
          if (idx !== -1) state.songs[idx] = Object.assign(state.songs[idx], data.song);
        }
        renderSongCards();
        renderSongViewer();
        showToast(`🎶 Pagine Medley formattate per ${targetDev} (${totalPages} pag.) ✓`);
      } else {
        const err = await res.json().catch(() => ({}));
        showToast(err.detail || 'Errore salvataggio formattazione');
      }
    } catch (err) {
      console.error('Error saving formatted medley:', err);
      showToast('Formattazione applicata all\'editor!');
    }
  } else {
    showToast(`🎶 Pagine Medley formattate per ${targetDev} (${totalPages} pag.) nell'editor!`);
  }

  closeMedleyPageFormatterModal();
}

function closeMedleyPageFormatterModal() {
  document.getElementById('medley-page-formatter-modal')?.remove();
  medleyFormatterState = null;
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
  return `<div class="lyrics-container" style="padding: 14px 16px; column-count: 1; box-shadow: none;">${parseAmlForWeb(amlText, true)}</div>`;
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
      user_email: state.currentUser ? state.currentUser.email : 'musicista@band.org',
      user_name: state.currentUser ? state.currentUser.name : 'Musicista'
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
        const isBest = cand.is_best || cand.badge === 'Migliore';
        const bestBadge = isBest
          ? `<span class="badge-best-candidate" title="Migliore per accuratezza di sezioni e accordi">⭐ Migliore</span>`
          : '';
        const metaDetails = [];
        if (cand.rating && cand.rating > 0) metaDetails.push(`★ ${cand.rating}`);
        if (cand.votes && cand.votes > 0) metaDetails.push(`${cand.votes} voti`);
        if (cand.version && cand.version > 1) metaDetails.push(`Ver. ${cand.version}`);
        const metaStr = metaDetails.length > 0 ? ` &bull; <span style="color: #fbbf24; font-size: 11px; font-weight: 700;">${metaDetails.join(' &bull; ')}</span>` : '';

        cardsHtml += `
          <div class="web-result-card ${isBest ? 'is-best' : ''}">
            <div style="flex: 1; min-width: 0;">
              <div style="font-weight: 800; font-size: 14px; color: #fff; display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%;">${escapeHtml(cand.title)}</span>
                ${bestBadge}
              </div>
              <div style="font-size: 12px; color: #38bdf8; margin-top: 2px;">
                <b>${escapeHtml(cand.artist)}</b> &bull; <span class="portal-badge">${escapeHtml(cand.portal)}</span>${metaStr}
              </div>
            </div>
            <button class="btn ${isBest ? 'btn-success' : 'btn-secondary'}" style="font-weight: 800; min-height: 36px; padding: 4px 14px; white-space: nowrap;" onclick="importCandidateUrl('${encodeURIComponent(cand.url)}')">
              ${isBest ? '⭐ Importa Consigliato' : '⚡ Importa'}
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

// ----------------------------------------------------------------------------
// COMPLETENESS, LRCLIB CHECK, AI AUTO-COMPLETION & ADMIN BATCH AUDIT
// ----------------------------------------------------------------------------

function updateAdminCompletenessToolbar() {
  const tb = document.getElementById('admin-completeness-toolbar');
  if (!tb) return;

  const isAdmin = typeof isCurrentUserAdmin === 'function' ? isCurrentUserAdmin() : false;
  const official = (state.repertoires || []).find(r => r.is_official);
  const isOfficialRep = official && (state.activeRepertoire === official.uuid || state.activeRepertoire === '__ALL__');

  if (!isAdmin || !isOfficialRep) {
    tb.style.display = 'none';
    return;
  }

  tb.style.display = 'flex';

  const chkFilter = document.getElementById('chk-filter-incomplete');
  if (chkFilter) chkFilter.checked = !!state.filterOnlyIncomplete;

  const countBadge = document.getElementById('admin-selected-count-badge');
  const btnBatchComplete = document.getElementById('btn-admin-batch-complete-ai');
  const btnBatchFinalize = document.getElementById('btn-admin-batch-finalize');
  const btnSelectAll = document.getElementById('btn-admin-select-all-incomplete');

  const selCount = state.selectedSongUuids ? state.selectedSongUuids.size : 0;
  if (countBadge) {
    countBadge.style.display = selCount > 0 ? 'inline-block' : 'none';
    countBadge.textContent = `${selCount} selezionat${selCount === 1 ? 'o' : 'i'}`;
  }
  if (btnBatchComplete) {
    btnBatchComplete.style.display = selCount > 0 ? 'inline-block' : 'none';
  }
  if (btnBatchFinalize) {
    btnBatchFinalize.style.display = selCount > 0 ? 'inline-block' : 'none';
  }
  if (btnSelectAll) {
    btnSelectAll.style.display = 'inline-block';
  }
}

function toggleFilterIncomplete(checked) {
  state.filterOnlyIncomplete = !!checked;
  renderSongCards();
}

function toggleSongBatchSelect(uuid) {
  if (!state.selectedSongUuids) state.selectedSongUuids = new Set();
  if (state.selectedSongUuids.has(uuid)) {
    state.selectedSongUuids.delete(uuid);
  } else {
    state.selectedSongUuids.add(uuid);
  }
  renderSongCards();
  updateAdminCompletenessToolbar();
}

function toggleSelectAllIncomplete() {
  if (!state.selectedSongUuids) state.selectedSongUuids = new Set();
  const list = getFilteredSongs().filter(s => {
    const isMedley = isMedleySong(s);
    return !isMedley && s.completeness_status === 'INCOMPLETO';
  });

  if (list.length === 0) {
    showToast('Nessun brano incompleto presente nella vista attuale');
    return;
  }

  const allSelected = list.every(s => state.selectedSongUuids.has(s.uuid));
  if (allSelected) {
    list.forEach(s => state.selectedSongUuids.delete(s.uuid));
  } else {
    list.forEach(s => state.selectedSongUuids.add(s.uuid));
  }
  renderSongCards();
  updateAdminCompletenessToolbar();
}

async function adminAuditRepertoireCompleteness() {
  const isAdmin = typeof isCurrentUserAdmin === 'function' ? isCurrentUserAdmin() : false;
  if (!isAdmin) {
    showToast('Azione riservata all\'Amministratore');
    return;
  }

  const btn = document.getElementById('btn-admin-audit-completeness');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '⏳ <span>Analisi LRCLIB in corso...</span>';
  }
  showToast('🔍 Scansione brani con LRCLIB in corso... attendere');

  try {
    const official = (state.repertoires || []).find(r => r.is_official);
    const res = await fetch(`${API_BASE}/api/admin/repertoire/audit-completeness`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_email: state.currentUser.email,
        repertoire_uuid: official ? official.uuid : null
      })
    });

    if (res.ok) {
      const data = await res.json();
      showToast(`Audit completato: ${data.processed_count} brani analizzati (${data.incomplete_count} incompleti, ${data.complete_count} completi, ${data.skipped_count} saltati/medley)`);
      await loadSongs({ autoSelect: false });
      if (data.incomplete_count > 0) {
        state.filterOnlyIncomplete = true;
        const chk = document.getElementById('chk-filter-incomplete');
        if (chk) chk.checked = true;
        renderSongCards();
      }
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore durante l\'audit del repertorio');
    }
  } catch (e) {
    console.error('Audit repertoire error:', e);
    showToast('Errore di connessione durante l\'audit');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<span>🔍</span> <span>Analizza Completezza Repertorio</span>';
    }
  }
}

async function adminBatchCompleteSelectedAi() {
  const isAdmin = typeof isCurrentUserAdmin === 'function' ? isCurrentUserAdmin() : false;
  if (!isAdmin) {
    showToast('Azione riservata all\'Amministratore');
    return;
  }

  const count = state.selectedSongUuids ? state.selectedSongUuids.size : 0;
  if (count === 0) {
    showToast('Nessun brano selezionato');
    return;
  }

  if (!confirm(`Sei sicuro di voler completare con AI ${count} brani selezionati?\nI brani Medley verranno automaticamente saltati e protetti.\nPer ogni brano modificato verrà salvato uno snapshot per eventuale UNDO.`)) {
    return;
  }

  const btn = document.getElementById('btn-admin-batch-complete-ai');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '⏳ Elaborazione AI in corso...';
  }
  showToast(`🤖 Elaborazione AI di ${count} brani in corso...`);

  try {
    const res = await fetch(`${API_BASE}/api/admin/repertoire/batch-complete-ai`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_email: state.currentUser.email,
        user_name: state.currentUser.name || 'Admin',
        song_uuids: Array.from(state.selectedSongUuids)
      })
    });

    if (res.ok) {
      const data = await res.json();
      const nCompleted = data.completed_count !== undefined
        ? data.completed_count
        : ((data.completed_songs || data.completed_uuids || []).length);
      const nSkipped = data.skipped_count !== undefined
        ? data.skipped_count
        : ((data.skipped_songs || data.skipped_details || []).length);
      if (nCompleted > 0) {
        showToast(`Completamento AI terminato: ${nCompleted} brani completati, ${nSkipped} saltati ✓`);
      } else {
        const firstSkip = (data.skipped_details || data.skipped_songs || [])[0];
        const skipReason = firstSkip && firstSkip.reason ? `: ${firstSkip.reason}` : '';
        showToast(`Nessun brano modificato (${nSkipped} saltati${skipReason})`);
      }
      state.selectedSongUuids.clear();
      await loadSongs({ autoSelect: false });
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore durante il completamento AI batch');
    }
  } catch (e) {
    console.error('Batch complete AI error:', e);
    showToast('Errore di connessione durante il completamento AI');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '🤖 Completa Selezionati con AI';
    }
  }
}

async function adminBatchFinalizeSelected() {
  const isAdmin = typeof isCurrentUserAdmin === 'function' ? isCurrentUserAdmin() : false;
  if (!isAdmin) {
    showToast('Azione riservata all\'Amministratore');
    return;
  }

  const count = state.selectedSongUuids ? state.selectedSongUuids.size : 0;
  if (count === 0) {
    showToast('Nessun brano selezionato');
    return;
  }

  if (!confirm(`Vuoi rendere DEFINITIVI ${count} brani selezionati?\nVerranno rimossi tutti i tag [AUTO-COMPLETATO] e lo stato sarà impostato su DEFINITIVO (escluso da futuri audit). Snapshot salvato per UNDO.`)) {
    return;
  }

  const btn = document.getElementById('btn-admin-batch-finalize');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '⏳ Consolidamento...';
  }

  try {
    const res = await fetch(`${API_BASE}/api/admin/repertoire/batch-finalize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_email: state.currentUser.email,
        user_name: state.currentUser.name || 'Admin',
        song_uuids: Array.from(state.selectedSongUuids)
      })
    });

    if (res.ok) {
      const data = await res.json();
      const nFinal = data.finalized_count !== undefined
        ? data.finalized_count
        : ((data.finalized_songs || data.finalized_uuids || []).length);
      showToast(`${nFinal} brani resi DEFINITIVI ✓`);
      state.selectedSongUuids.clear();
      await loadSongs({ autoSelect: false });
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore durante il consolidamento dei brani');
    }
  } catch (e) {
    console.error('Batch finalize error:', e);
    showToast('Errore di connessione');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '🔒 Rendi Definitivo';
    }
  }
}

async function undoSongInViewer(uuid) {
  const isAdmin = typeof isCurrentUserAdmin === 'function' ? isCurrentUserAdmin() : false;
  if (!isAdmin) {
    showToast('Operazione consentita solo agli amministratori');
    return;
  }
  if (!confirm('Ripristinare il contenuto e lo stato precedenti all\'intervento dell\'AI?')) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/songs/${uuid}/undo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_email: state.currentUser.email,
        user_name: state.currentUser.name || 'Musicista'
      })
    });

    if (res.ok) {
      showToast('Versione precedente ripristinata con successo (UNDO eseguito) ✓');
      await selectSong(uuid);
      await loadSongs({ autoSelect: false });
    } else {
      const err = await res.json();
      showToast(err.detail || 'Impossibile ripristinare la versione precedente');
    }
  } catch (e) {
    console.error('Undo song error:', e);
    showToast('Errore durante il ripristino UNDO');
  }
}

async function finalizeSongInViewer(uuid) {
  const isAdmin = typeof isCurrentUserAdmin === 'function' ? isCurrentUserAdmin() : false;
  if (!isAdmin) {
    showToast('Solo gli amministratori possono rendere un brano definitivo');
    return;
  }

  if (!confirm('Rendere questo brano DEFINITIVO? Verranno rimossi i tag [AUTO-COMPLETATO] e non sarà più modificato dagli audit automatici.')) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/admin/repertoire/batch-finalize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_email: state.currentUser.email,
        user_name: state.currentUser.name || 'Admin',
        song_uuids: [uuid]
      })
    });

    if (res.ok) {
      showToast('Brano reso DEFINITIVO ✓');
      await selectSong(uuid);
      await loadSongs({ autoSelect: false });
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore durante il consolidamento');
    }
  } catch (e) {
    console.error('Finalize song error:', e);
    showToast('Errore di connessione');
  }
}

async function completeSongInViewerAi(uuid) {
  const s = state.selectedSong;
  if (!s || s.uuid !== uuid) return;

  if (isMedleySong(s)) {
    showToast('I brani Medley sono protetti e non possono essere modificati dall\'AI');
    return;
  }

  const isAdmin = typeof isCurrentUserAdmin === 'function' ? isCurrentUserAdmin() : false;
  const official = (state.repertoires || []).find(r => r.is_official);
  const isInOfficial = official && official.song_uuids && official.song_uuids.includes(s.uuid);

  if (isInOfficial && !isAdmin) {
    showToast('Modifica consentita solo agli amministratori sul Repertorio Ufficiale');
    return;
  }

  showToast('🤖 Completamento sezioni mancanti con AI in corso... attendere');

  try {
    const res = await fetch(`${API_BASE}/api/admin/repertoire/batch-complete-ai`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_email: state.currentUser.email,
        user_name: state.currentUser.name || 'Admin',
        song_uuids: [uuid]
      })
    });

    if (res.ok) {
      const data = await res.json();
      const nCompleted = data.completed_count !== undefined
        ? data.completed_count
        : ((data.completed_songs || data.completed_uuids || []).length);
      if (nCompleted > 0) {
        showToast('✓ Convalida AI completata: brano aggiornato a COMPLETO (Snapshot salvato)', 6000);
        await selectSong(uuid);
        await loadSongs({ autoSelect: false });
      } else {
        const skipped = (data.skipped_details || data.skipped_songs || [])[0];
        showToast((skipped && skipped.reason) || 'L\'AI ha verificato il brano: nessuna sezione mancante rilevata.', 6500);
      }
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore completamento AI');
    }
  } catch (e) {
    console.error('Complete song in viewer AI error:', e);
    showToast('Errore di connessione completamento AI');
  }
}

function updateImportCompletenessBanner(completeness, title, artist, originalAml) {
  const banner = document.getElementById('import-completeness-banner');
  const textEl = document.getElementById('import-completeness-text');
  const completeAiBtn = document.getElementById('btn-import-complete-ai');
  const undoBtn = document.getElementById('btn-import-undo-ai');
  if (!banner || !textEl) return;

  state.importOriginalAml = originalAml || '';
  state.importOfficialLyrics = (completeness && completeness.official_lyrics) || '';
  state.importCompletenessStatus = (completeness && completeness.status) || 'NON_VERIFICATO';
  state.importCompletenessRatio = (completeness && completeness.ratio) || 0;

  if (undoBtn) undoBtn.style.display = 'none';

  if (!completeness || completeness.status === 'NON_VERIFICATO') {
    banner.style.display = 'none';
    return;
  }

  const isMedley = completeness.is_medley || (title && title.toLowerCase().includes('medley')) || completeness.status === 'MEDLEY';

  if (isMedley) {
    banner.style.display = 'block';
    banner.style.borderColor = '#a855f7';
    banner.style.background = 'rgba(168, 85, 247, 0.12)';
    textEl.innerHTML = `<span style="color: #c084fc; font-weight: 800;">🎵 MEDLEY Rilevato:</span> Questo brano è escluso automaticamente da verifiche e modifiche AI per proteggere gli arrangiamenti manuali.`;
    if (completeAiBtn) completeAiBtn.style.display = 'none';
    if (undoBtn) undoBtn.style.display = 'none';
    return;
  }

  if (completeness.status === 'INCOMPLETO') {
    banner.style.display = 'block';
    banner.style.borderColor = '#f59e0b';
    banner.style.background = 'rgba(245, 158, 11, 0.15)';
    const pct = Math.round((completeness.ratio || 0) * 100);
    textEl.innerHTML = `<span style="color: #fbbf24; font-weight: 800;">⚠️ Attenzione: Brano apparentemente incompleto (${pct}% del testo ufficiale LRCLIB).</span> Mancano strofe, bridge o outro rispetto all'originale. Clicca sul pulsante a fianco per completarlo automaticamente con l'AI.`;
    if (completeAiBtn) {
      completeAiBtn.style.display = 'inline-block';
      completeAiBtn.disabled = false;
      completeAiBtn.innerHTML = '🤖 Completa con AI';
    }
    return;
  }

  if (completeness.status === 'COMPLETO') {
    banner.style.display = 'block';
    banner.style.borderColor = '#10b981';
    banner.style.background = 'rgba(16, 185, 129, 0.12)';
    textEl.innerHTML = `<span style="color: #34d399; font-weight: 800;">✓ Testo Completo:</span> Confrontato con il testo ufficiale LRCLIB, tutte le sezioni principali risultano presenti.`;
    if (completeAiBtn) completeAiBtn.style.display = 'none';
    if (undoBtn) undoBtn.style.display = 'none';
    return;
  }

  banner.style.display = 'none';
}

async function completeImportedSongAi() {
  const btn = document.getElementById('btn-import-complete-ai');
  const undoBtn = document.getElementById('btn-import-undo-ai');
  const textEl = document.getElementById('import-completeness-text');
  const titleField = document.getElementById('new-song-title');
  const artistField = document.getElementById('new-song-artist');
  const amlField = document.getElementById('new-song-aml');

  const title = (titleField?.value || '').trim();
  const artist = (artistField?.value || '').trim();
  const aml = amlField?.value || '';

  if (!title) {
    showToast('Inserisci prima il titolo del brano');
    return;
  }

  if (title.toLowerCase().includes('medley')) {
    showToast('I brani Medley sono protetti e non possono essere modificati dall\'AI');
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '⏳ AI in elaborazione...';
  }

  try {
    const res = await fetch(`${API_BASE}/api/songs/complete-ai`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: title,
        artist: artist,
        aml: aml,
        official_lyrics: state.importOfficialLyrics || ''
      })
    });

    if (res.ok) {
      const data = await res.json();
      if (data.status === 'unchanged') {
        showToast(data.message || 'Nessuna sezione mancante rilevata');
        if (textEl) {
          textEl.innerHTML = `<span style="color: #60a5fa; font-weight: 800;">ℹ️ Verifica AI:</span> ${data.message || 'Nessuna sezione aggiuntiva necessaria.'}`;
        }
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '🤖 Completa con AI';
        }
        return;
      }
      if (!state.importOriginalAml) {
        state.importOriginalAml = aml;
      }
      if (amlField) {
        amlField.value = data.completed_aml;
      }
      if (textEl) {
        textEl.innerHTML = `<span style="color: #34d399; font-weight: 800;">🤖 Brano completato con successo dall'AI!</span> Le sezioni aggiunte sono evidenziate con <code>[AUTO-COMPLETATO]</code>. Puoi verificare gli accordi, modificarli o cliccare <b>UNDO</b> per ripristinare il testo originale.`;
      }
      if (btn) btn.style.display = 'none';
      if (undoBtn) undoBtn.style.display = 'inline-block';
      showToast('Brano completato con AI ✓ Nuove sezioni marcate');
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore durante il completamento AI');
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '🤖 Completa con AI';
      }
    }
  } catch (e) {
    console.error('Error completing song with AI:', e);
    showToast('Errore di connessione durante il completamento AI');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '🤖 Completa con AI';
    }
  }
}

function undoImportedSongAi() {
  const amlField = document.getElementById('new-song-aml');
  const btn = document.getElementById('btn-import-complete-ai');
  const undoBtn = document.getElementById('btn-import-undo-ai');
  const textEl = document.getElementById('import-completeness-text');

  if (state.importOriginalAml && amlField) {
    amlField.value = state.importOriginalAml;
    state.importOriginalAml = '';
    if (undoBtn) undoBtn.style.display = 'none';
    if (btn) {
      btn.style.display = 'inline-block';
      btn.disabled = false;
      btn.innerHTML = '🤖 Completa con AI';
    }
    if (textEl) {
      const pct = Math.round((state.importCompletenessRatio || 0) * 100);
      textEl.innerHTML = `<span style="color: #fbbf24; font-weight: 800;">↩️ Versione originale ripristinata (${pct}% del testo LRCLIB).</span> Puoi completare di nuovo con AI se desideri.`;
    }
    showToast('Ripristinato testo originale scaricato ✓');
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

      if (data.completeness) {
        updateImportCompletenessBanner(data.completeness, data.title, data.artist, data.aml);
      }

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

      if (data.completeness) {
        updateImportCompletenessBanner(data.completeness, data.title || '', data.artist || '', data.aml);
      }

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

      if (data.completeness) {
        updateImportCompletenessBanner(data.completeness, data.title, data.artist, data.aml);
      }

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
  let aml = document.getElementById('new-song-aml')?.value || '';
  aml = aml.replace(/\[\/?AUTO-COMPLETATO\]/gi, '').trim();

  const repSelect = document.getElementById('new-song-repertoire');
  let targetRepertoire = repSelect?.value;
  const officialRep = (state.repertoires || []).find(r => r.is_official);
  if (!targetRepertoire || (officialRep && targetRepertoire === officialRep.uuid) || targetRepertoire === '__ALL__') {
    const personal = (state.repertoires || []).find(r => isOwnPersonalRepertoire(r) || (!r.is_official && !r.owner_email));
    targetRepertoire = personal ? personal.uuid : null;
  }

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

  // CASO B: Se siamo offline, salva subito come Bozza Locale Offline
  if (!navigator.onLine) {
    handleOfflineSubmitNewSong(payload);
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/songs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json();
      const targetRepName = data.target_repertoire_name || 'personale';
      showToast(`Brano "${title}" salvato in ${targetRepName} ✓ (Usa '⭐ Promuovi a Ufficiale' per pubblicarlo nella band)`);
      hideNewSongForm();
      const finalRepUuid = data.target_repertoire_uuid || targetRepertoire;
      if (finalRepUuid) {
        state.activeRepertoire = finalRepUuid;
      }
      // Reload both repertoires and songs to immediately reflect new assignment in UI
      await loadRepertoires();
      await loadSongs();
      if (data.song && data.song.uuid) {
        selectSong(data.song.uuid);
        if (isMedleyAml(data.song.aml_content || aml)) {
          setTimeout(() => showMedleyPostSavePrompt(data.song), 400);
        }
      }
    } else {
      const err = await res.json();
      showToast(err.detail || 'Errore creazione brano');
    }
  } catch (err) {
    console.warn('Create song error, falling back to Offline Draft (Caso B):', err);
    handleOfflineSubmitNewSong(payload);
  }
}

function handleOfflineSubmitNewSong(payload) {
  const tempUuid = `offline_${Date.now()}`;
  const newSong = {
    uuid: tempUuid,
    title: payload.title,
    artist: payload.artist,
    key_current: payload.key_current,
    bpm: payload.bpm,
    capo: payload.capo,
    aml_content: payload.aml_content,
    assigned_repertoires: ['Personale (Bozza Offline)'],
    _is_offline_draft: true
  };
  saveOfflineDraft(tempUuid, payload);
  if (!state.songs) state.songs = [];
  state.songs.unshift(newSong);
  saveOfflineSnapshot(SNAPSHOT_KEYS.SONGS, state.songs);
  hideNewSongForm();
  renderSongCards();
  selectSong(tempUuid);
  updateConnectionStatus(false);
  showToast(`💾 Brano "${payload.title}" salvato come Bozza Locale Offline! Verrà sincronizzato non appena tornerai online.`);
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

  // Pure chords lines without brackets or pipes (e.g. DO, or SOL DO MIm RE)
  if (!trimmedLine.includes('[') && !trimmedLine.includes(']')) {
    const words = trimmedLine.split(/\s+/).filter(Boolean);
    if (words.length >= 1 && words.length <= 16) {
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

function renderAmlSectionBadge(secName) {
  const upper = (secName || '').toUpperCase();
  let bg = '#2563eb';
  let icon = '';
  if (upper.includes('STACCO')) {
    bg = '#dc2626';
    icon = '⚡ ';
  } else if (upper.includes('INTRO')) {
    bg = '#059669';
  } else if (upper.includes('STROFA') || upper.includes('VERSE')) {
    bg = '#2563eb';
  } else if (upper.includes('RITORNELLO') || upper.includes('RIT') || upper.includes('CHORUS')) {
    bg = '#7c3aed';
  } else if (upper.includes('BRIDGE') || upper.includes('PONTE')) {
    bg = '#d97706';
  } else if (upper.includes('SOLO') || upper.includes('ASSOLO')) {
    bg = '#b45309';
    icon = '🎸 ';
  } else if (upper.includes('OUTRO') || upper.includes('FINALE') || upper.includes('CODA') || upper.includes('END') || upper.includes('FINE')) {
    bg = '#475569';
  }
  return `<div class="aml-tag-badge" style="display:inline-block; background:${bg}; color:#ffffff; border-radius:5px; padding:2.5px 9px; font-weight:800; margin:10px 0 4px 0; font-size:12.5px; letter-spacing:0.5px; box-shadow: 0 1px 3px rgba(0,0,0,0.35);">${icon}[${escapeHtml(secName)}]</div>`;
}

function parseAmlForWeb(aml, showChords) {
  if (!aml) return '<i>Nessun testo inserito.</i>';

  let html = '';
  const lines = aml.split('\n');
  let inSection = false;
  let lastWasInstrumental = false;
  let medleyCount = 0;

  for (let rawLine of lines) {
    const line = rawLine.trimEnd();
    const trimmed = line.trim();

    if (!trimmed) {
      continue;
    }

    // AI Autocompletion markers: visible ONLY in EDIT mode (textarea), suppressed in teleprompter, palco & web viewer
    if (trimmed.toUpperCase() === '[AUTO-COMPLETATO]' || trimmed.toUpperCase().startsWith('[AUTO-COMPLETATO]') ||
        trimmed.toUpperCase() === '[/AUTO-COMPLETATO]' || trimmed.toUpperCase().startsWith('[/AUTO-COMPLETATO]')) {
      continue;
    }

    // Comments starting with #
    if (trimmed.startsWith('#')) {
      const commText = trimmed.slice(1).trim();
      const cleanComm = commText.replace(/^[♪\u266a\u266b\u25a0■\*\-\#\s]+/, '').replace(/^[\(\[\{]+|[\)\]\}]+$/g, '').trim().toLowerCase();
      const isCommInst = /^(?:strumentale|instrumental|solo|assolo|intermezzo|interlude)(?:\s*[:\-–—]?\s*.*)?$/.test(cleanComm);
      if (!showChords && isCommInst) {
        if (lastWasInstrumental) {
          continue;
        }
        lastWasInstrumental = true;
        html += `<div class="aml-instrumental">♪ (Strumentale)</div>`;
        continue;
      }
      html += `<div style="margin: 4px 0; color: #94a3b8; font-style: italic; font-size: 12px;"># ${escapeHtml(commText)}</div>`;
      if (isCommInst) {
        lastWasInstrumental = true;
      }
      continue;
    }

    // 1. Detect Directives ({tag} or {tag: value})
    const dirMatch = trimmed.match(/^\{([a-zA-Z0-9_-]+)(?:[:\s]\s*([^\}]+))?\}$/);
    if (dirMatch) {
      const tag = dirMatch[1].toLowerCase();
      const val = dirMatch[2] ? dirMatch[2].trim() : '';

      // Spezzone Medley: Inizio brano {start_of_song: Titolo | Artista | Tonalità}
      if (['start_of_song', 'sos', 'start_of_medley', 'start_of_medley_song', 'soms'].includes(tag)) {
        if (inSection) {
          html += '</div>';
          inSection = false;
        }
        medleyCount++;
        if (medleyCount > 1) {
          html += `<div class="medley-web-divider" style="margin: 22px 0 16px 0; border-top: 2px dashed rgba(56, 189, 248, 0.4); text-align: center; position: relative;">
            <span style="position: relative; top: -11px; background: #0f172a; padding: 2px 12px; font-size: 11px; color: #94a3b8; font-weight: 800; border-radius: 4px; border: 1px solid #334155;">✂️ FINE SPEZZONE — CAMBIO BRANO</span>
          </div>`;
        }
        let fragTitle = '';
        let fragArtist = '';
        let fragKey = '';
        if (val.includes('|')) {
          const parts = val.split('|').map(s => s.trim());
          fragTitle = parts[0] || ('Brano ' + medleyCount);
          fragArtist = parts[1] || '';
          fragKey = parts[2] || '';
        } else if (val.includes(' - ')) {
          const parts = val.split(' - ').map(s => s.trim());
          fragTitle = parts[0] || ('Brano ' + medleyCount);
          fragArtist = parts[1] || '';
        } else {
          fragTitle = val || ('Brano ' + medleyCount);
        }

        const MEDLEY_COLORS_WEB = [
          { bg: 'rgba(2, 132, 199, 0.22)', border: '#0284c7', text: '#38bdf8' },
          { bg: 'rgba(217, 119, 6, 0.22)', border: '#d97706', text: '#fbbf24' },
          { bg: 'rgba(5, 150, 105, 0.22)', border: '#059669', text: '#34d399' },
          { bg: 'rgba(124, 58, 237, 0.22)', border: '#7c3aed', text: '#c084fc' },
          { bg: 'rgba(225, 29, 72, 0.22)', border: '#e11d48', text: '#fb7185' },
          { bg: 'rgba(8, 145, 178, 0.22)', border: '#0891b2', text: '#22d3ee' },
          { bg: 'rgba(234, 88, 12, 0.22)', border: '#ea580c', text: '#fb923c' },
          { bg: 'rgba(79, 70, 229, 0.22)', border: '#4f46e5', text: '#818cf8' },
          { bg: 'rgba(22, 163, 74, 0.22)', border: '#16a34a', text: '#4ade80' },
          { bg: 'rgba(219, 39, 119, 0.22)', border: '#db2777', text: '#f472b6' },
          { bg: 'rgba(37, 99, 235, 0.22)', border: '#2563eb', text: '#60a5fa' },
          { bg: 'rgba(202, 138, 4, 0.22)', border: '#ca8a04', text: '#facc15' },
          { bg: 'rgba(13, 148, 136, 0.22)', border: '#0d9488', text: '#2dd4bf' },
          { bg: 'rgba(147, 51, 234, 0.22)', border: '#9333ea', text: '#d8b4fe' },
          { bg: 'rgba(220, 38, 38, 0.22)', border: '#dc2626', text: '#f87171' },
          { bg: 'rgba(30, 64, 175, 0.22)', border: '#1e40af', text: '#93c5fd' },
          { bg: 'rgba(180, 83, 9, 0.22)', border: '#b45309', text: '#fde047' },
          { bg: 'rgba(4, 120, 87, 0.22)', border: '#047857', text: '#6ee7b7' },
          { bg: 'rgba(109, 40, 217, 0.22)', border: '#6d28d9', text: '#ddd6fe' },
          { bg: 'rgba(190, 18, 60, 0.22)', border: '#be123c', text: '#fda4af' }
        ];
        const color = MEDLEY_COLORS_WEB[(medleyCount - 1) % MEDLEY_COLORS_WEB.length];
        const metaParts = [];
        if (fragArtist) metaParts.push(`<b>${escapeHtml(fragArtist)}</b>`);
        if (fragKey) metaParts.push(`Tonalità: <b style="color: #ffd600;">${escapeHtml(toLatinKey(fragKey))}</b>`);
        const metaStr = metaParts.join(' &bull; ');

        html += `
        <div class="medley-fragment-banner" style="background: ${color.bg}; border-left: 4px solid ${color.border}; border-top: 1px solid ${color.border}; border-right: 1px solid ${color.border}; border-bottom: 1px solid ${color.border}; border-radius: 6px; padding: 7px 12px; margin: 14px 0 8px 0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
          <div style="font-weight: 900; font-size: 14.5px; color: ${color.text};">🎵 ${medleyCount}. ${escapeHtml(fragTitle.toUpperCase())}</div>
          <div style="font-size: 12px; color: #cbd5e1;">${metaStr}</div>
        </div>`;
        continue;
      }

      // Spezzone Medley: Fine brano (direttiva invisibile sul web)
      if (['end_of_song', 'eos', 'end_of_medley', 'end_of_medley_song', 'eoms'].includes(tag)) {
        if (inSection) {
          html += '</div>';
          inSection = false;
        }
        continue;
      }

      // Skip metadata directives already displayed in the main song header
      if (['title', 't', 'artist', 'a', 'key', 'tempo', 'bpm', 'capo', 'time'].includes(tag)) {
        continue;
      }

      // Comments / band notes: {c: ...} or {comment: ...}
      if (['c', 'comment', 'ci', 'cb'].includes(tag)) {
        const commText = (val || 'Nota').trim();
        const cleanComm = commText.replace(/^[♪\u266a\u266b\u25a0■\*\-\#\s]+/, '').replace(/^[\(\[\{]+|[\)\]\}]+$/g, '').trim().toLowerCase();
        const isCommInst = /^(?:strumentale|instrumental|solo|assolo|intermezzo|interlude)(?:\s*[:\-–—]?\s*.*)?$/.test(cleanComm);
        if (!showChords && isCommInst) {
          if (lastWasInstrumental) {
            continue;
          }
          lastWasInstrumental = true;
          html += `<div class="aml-instrumental">♪ (Strumentale)</div>`;
          continue;
        }
        html += `<div style="margin: 6px 0; color: #38bdf8; background: rgba(56, 189, 248, 0.12); border-left: 3px solid #38bdf8; padding: 4px 10px; border-radius: 0 4px 4px 0; font-style: italic; font-size: 13px; font-weight: 700;">${escapeHtml(val || 'Nota')}</div>`;
        if (isCommInst) {
          lastWasInstrumental = true;
        }
        continue;
      }

      // Column break: {colb}
      if (['colb', 'column_break', 'col_break'].includes(tag)) {
        html += `<div style="break-before: column; border-top: 1px dashed #a855f7; margin: 12px 0; color: #a855f7; font-size: 11px; font-weight: 700; padding-top: 4px;">--- SALTO COLONNA ---</div>`;
        continue;
      }

      // Page break: {np}, {new_page}, {page_break}, {salto_pagina}
      if (['np', 'new_page', 'page_break', 'salto_pagina', 'salto-pagina'].includes(tag)) {
        if (inSection) {
          html += '</div>';
          inSection = false;
        }
        const activeDevName = escapeHtml(state.activeDevice || 'Dispositivo');
        html += `<div class="aml-page-break" style="break-before: page; margin: 20px 0 16px 0; border-top: 2px dashed #f59e0b; text-align: center; position: relative;">
          <span style="position: relative; top: -11px; background: #0f172a; padding: 2px 14px; font-size: 11px; color: #fbbf24; font-weight: 800; border-radius: 4px; border: 1px solid #d97706; box-shadow: 0 1px 4px rgba(0,0,0,0.4);">📄 SALTO PAGINA (${activeDevName})</span>
        </div>`;
        continue;
      }

      // Section open directives
      let secName = null;
      if (['soc', 'start_of_chorus', 'chorus', 'ritornello'].includes(tag)) {
        secName = val ? val.toUpperCase() : 'RITORNELLO';
      } else if (['sov', 'start_of_verse', 'verse', 'strofa'].includes(tag)) {
        secName = val ? val.toUpperCase() : 'STROFA';
      } else if (['sob', 'start_of_bridge', 'bridge', 'speciale'].includes(tag)) {
        secName = val ? val.toUpperCase() : 'BRIDGE';
      } else if (['solo', 'assolo', 'intro', 'outro', 'finale', 'coda', 'interlude'].includes(tag)) {
        secName = val ? `${tag.toUpperCase()}: ${val.toUpperCase()}` : tag.toUpperCase();
      }

      if (secName) {
        const isInst = secName.includes('STRUMENTALE') || secName.includes('SOLO') || secName.includes('ASSOLO') || secName.includes('INTERMEZZO') || secName.includes('STACCO');
        if (!showChords && isInst && lastWasInstrumental) {
          continue;
        }
        if (inSection) html += '</div>';
        const isChorus = secName.includes('RITORNELLO') || secName.includes('CHORUS');
        const bgTint = isChorus ? 'background: rgba(124, 58, 237, 0.05); border-left: 3px solid #7c3aed; padding-left: 10px; border-radius: 0 6px 6px 0;' : '';
        html += `<div class="aml-section" style="${bgTint}">${renderAmlSectionBadge(secName)}</div>`;
        inSection = true;
        lastWasInstrumental = isInst;
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

      // Direttiva Scena Live Tastiere: {scena: 3} oppure {scena 3}
      if (['scena', 'scene'].includes(tag)) {
        const scenaText = val ? escapeHtml(val.toUpperCase()) : '';
        html += `<div class="aml-scene-badge" style="display:inline-block; background:#0891b2; color:#ffffff; border-radius:5px; padding:2px 8px; font-weight:800; margin:6px 0; font-size:13px; letter-spacing:0.5px; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"><img src="assets/keyboard_icon.png" style="width:14px; height:13px; vertical-align:middle; margin-right:4px;" alt="🎹"/> ${scenaText}</div>`;
        continue;
      }

      // Direttiva Stacco Musicale / Strumento: {stacco: guitar} oppure {stacco organo} oppure {stacco}
      if (['stacco'].includes(tag)) {
        if (!showChords && lastWasInstrumental) {
          continue;
        }
        const staccoText = val ? `STACCO: ${escapeHtml(val.toUpperCase())}` : 'STACCO';
        html += `<div class="aml-stacco-badge" style="display:inline-block; background:#dc2626; color:#ffffff; border-radius:5px; padding:2.5px 9px; font-weight:800; margin:6px 0; font-size:12.5px; letter-spacing:0.5px; box-shadow: 0 1px 3px rgba(0,0,0,0.3);">⚡ [${staccoText}]</div>`;
        lastWasInstrumental = true;
        continue;
      }

      // Direttiva Riga Bianca / Spazio Verticale: {riga_bianca}, {blank_line}, {spazio}
      if (['riga_bianca', 'rigabianca', 'riga-bianca', 'riga_vuota', 'rigavuota', 'blank_line', 'blankline', 'blank-line', 'empty_line', 'emptyline', 'spazio', 'space'].includes(tag)) {
        let count = 1;
        if (val) {
          const parsed = parseInt(val, 10);
          if (!isNaN(parsed) && parsed > 0) count = parsed;
        }
        const heightEm = (count * 1.35).toFixed(1);
        html += `<div class="aml-blank-line" style="height: ${heightEm}em; min-height: 16px;"></div>`;
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
      const standardSections = ['INTRO', 'STROFA', 'VERSE', 'RITORNELLO', 'CHORUS', 'BRIDGE', 'SPECIAL', 'OUTRO', 'FINALE', 'STRUMENTALE', 'SOLO', 'CODA', 'STACCO', 'RIFF', 'END', 'FINE'];
      if (standardSections.some(s => candidate.startsWith(s) || candidate.includes(s))) {
        sectionTitle = candidate;
      }
    } else if (trimmed.endsWith(':') && trimmed.length < 35 && !trimmed.includes('[')) {
      sectionTitle = trimmed.slice(0, -1).toUpperCase();
    }

    if (sectionTitle) {
      const isInst = sectionTitle.includes('STRUMENTALE') || sectionTitle.includes('SOLO') || sectionTitle.includes('ASSOLO') || sectionTitle.includes('INTERMEZZO') || sectionTitle.includes('STACCO');
      if (!showChords && isInst && lastWasInstrumental) {
        continue;
      }
      if (inSection) html += '</div>';
      const isChorus = sectionTitle.includes('RITORNELLO') || sectionTitle.includes('CHORUS');
      const bgTint = isChorus ? 'background: rgba(124, 58, 237, 0.05); border-left: 3px solid #7c3aed; padding-left: 10px; border-radius: 0 6px 6px 0;' : '';
      html += `<div class="aml-section" style="${bgTint}">${renderAmlSectionBadge(sectionTitle)}</div>`;
      inSection = true;
      lastWasInstrumental = isInst;
      continue;
    }

    if (!inSection) {
      html += '<div class="aml-section">';
      inSection = true;
    }

    // Extract inline {c: ...} / {comment: ...} anywhere on a chord/grid/lyric line
    const inlineComments = [];
    const lineClean = line.replace(/\{(?:c|comment|ci|cb)\s*:\s*([^\}]+)\}/gi, (_, txt) => {
      if (txt && txt.trim()) inlineComments.push(txt.trim());
      return '';
    }).replace(/\s+$/, '');
    const trimmedClean = lineClean.trim();
    const inlineCommHtml = inlineComments.length
      ? ` <span style="color: #38bdf8; font-style: italic; font-weight: 700;">(${escapeHtml(inlineComments.join(' '))})</span>`
      : '';

    // 2. Chord Grids, Guitar Tabs, or Pure Unbracketed Chords
    if (isChordGridOrTabLine(trimmedClean)) {
      if (!showChords) {
        if (!lastWasInstrumental) {
          html += `<div class="aml-instrumental">♪ (Strumentale)${inlineCommHtml}</div>`;
          lastWasInstrumental = true;
        }
      } else {
        const isTabLine = /^[eEaAdDgGbB]\|/.test(trimmedClean) || (trimmedClean.match(/-/g) || []).length >= 4;
        if (isTabLine) {
          html += `<div class="aml-tab-line">${escapeHtml(lineClean)}</div>`;
        } else {
          const hasPipes = trimmedClean.includes('|');
          const renderedChordLine = lineClean.replace(/\S+/g, token => {
            if (token === '|' || token === '/' || token === '%' || token === '-') {
              return escapeHtml(token);
            }
            return `<span class="chord-token">${escapeHtml(token)}</span>`;
          });
          html += `<div class="aml-chord-line${hasPipes ? ' aml-grid-line' : ''}">${renderedChordLine}${inlineCommHtml}</div>`;
        }
        lastWasInstrumental = false;
      }
      continue;
    }

    // 3. Render Line (chords above lyrics, without [ ] brackets)
    const lyricsOnly = lineClean.replace(/\[[^\]]+\]/g, '').trim();
    const hasChordTokens = /\[[^\]]+\]/.test(lineClean);

    const cleanLyr = lyricsOnly.replace(/^[♪\u266a\u266b\u25a0■\*\-\#\s]+/, '').replace(/^[\(\[\{]+|[\)\]\}]+$/g, '').trim().toLowerCase();
    const isLyrInst = /^(?:strumentale|instrumental|solo|assolo|intermezzo|interlude)(?:\s*[:\-–—]?\s*.*)?$/.test(cleanLyr);

    if (!showChords) {
      if (isLyrInst) {
        if (!lastWasInstrumental) {
          html += `<div class="aml-instrumental">♪ (Strumentale)${inlineCommHtml}</div>`;
          lastWasInstrumental = true;
        }
      } else if (hasChordTokens && !lyricsOnly) {
        // Pure chords line without lyrics -> Instrumental line for singer
        if (!lastWasInstrumental) {
          html += `<div class="aml-instrumental">♪ (Strumentale)${inlineCommHtml}</div>`;
          lastWasInstrumental = true;
        }
      } else if (lyricsOnly) {
        html += `<div class="aml-lyric-line">${escapeHtml(lineClean.replace(/\[[^\]]+\]/g, ''))}${inlineCommHtml}</div>`;
        lastWasInstrumental = false;
      } else if (inlineCommHtml) {
        html += `<div class="aml-lyric-line">${inlineCommHtml.trim()}</div>`;
        lastWasInstrumental = false;
      }
    } else {
      if (isLyrInst && !hasChordTokens) {
        const dispTitle = cleanLyr ? cleanLyr.charAt(0).toUpperCase() + cleanLyr.slice(1) : 'Strumentale';
        html += `<div class="aml-instrumental">♪ (${escapeHtml(dispTitle)})${inlineCommHtml}</div>`;
        lastWasInstrumental = true;
      } else if (hasChordTokens) {
        const formatted = formatChordLyricLine(lineClean);
        if (formatted.chordHtml && formatted.chordHtml.trim()) {
          const appendToChords = !(formatted.lyricHtml && formatted.lyricHtml.trim());
          html += `<div class="aml-chord-line">${formatted.chordHtml}${appendToChords ? inlineCommHtml : ''}</div>`;
        }
        if (formatted.lyricHtml && formatted.lyricHtml.trim()) {
          html += `<div class="aml-lyric-line">${formatted.lyricHtml}${inlineCommHtml}</div>`;
        }
        lastWasInstrumental = false;
      } else {
        html += `<div class="aml-lyric-line">${escapeHtml(lineClean)}${inlineCommHtml}</div>`;
        lastWasInstrumental = false;
      }
    }
  }

  if (inSection) html += '</div>';

  // Inserisci un badge [END] di default alla fine del brano se non già presente
  const trimmedAml = (aml || '').trim();
  const alreadyHasEnd = /\[\s*(?:END|FINE)\s*\]\s*$/i.test(trimmedAml) || /\{\s*(?:end|fine)\s*\}\s*$/i.test(trimmedAml);
  if (!alreadyHasEnd && trimmedAml.length > 0) {
    html += '<div class="aml-section"><div class="aml-tag-header" style="color: var(--stage-aml-color, #38bdf8); font-weight: 900;">[END]</div></div>';
  }

  return html;
}

/**
 * Costruisce la query string comune per generazione/download PDF con preferenze layout utente.
 */
function buildPdfQueryParams(hasChords, extra = {}) {
  const p = state.userPrefs || {};
  const currentMusician = state.currentUser?.name || localStorage.getItem('asma_user_name') || 'Puma';
  const currentEmail = state.currentUser?.email || localStorage.getItem('asma_user_email') || '';
  const params = new URLSearchParams({
    chords: hasChords ? 'true' : 'false',
    device: state.activeDevice || 'Default',
    email: currentEmail,
    user_name: currentMusician,
    columns: String(p.layout_columns || 1),
    font_size: String(p.layout_font_size || 12),
    font_size_chords: String(p.layout_font_size_chords || 13),
    margin_lateral: String(p.layout_margin_lateral || 10),
    margin_top: String(p.layout_margin_top || 10),
    margin_bottom: String(p.layout_margin_bottom || 14),
  });
  if (state.selectedSong && state.selectedSong._stageDelta) {
    params.set('transpose', String(state.selectedSong._stageDelta));
  }
  Object.entries(extra).forEach(([k, v]) => {
    if (v !== undefined && v !== null) params.set(k, String(v));
  });
  return params.toString();
}

/**
 * Desktop: avvio download sincrono diretto.
 * Mobile: apre la modale di esportazione con Scarica Diretto e Stampa / Salva come PDF.
 */
function triggerPdfDownload(url, filename, onPrint = null) {
  logAuditEvent('DOWNLOAD_PDF', 'PDF', filename, { filename: filename });
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || '');

  if (isStandalone || isMobile) {
    openPdfExportModal(url, filename, onPrint);
    return;
  }

  showToast(`Avvio download "${filename}"...`);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    if (a.parentNode) a.parentNode.removeChild(a);
  }, 1500);
}

function closePdfExportModal({ fromPopstate = false } = {}) {
  const modal = document.getElementById('pdf-export-modal');
  const wasOpen = modal && modal.style.display !== 'none';
  if (modal) modal.style.display = 'none';
  if (state._pdfExport && state._pdfExport.blobUrl) {
    const oldUrl = state._pdfExport.blobUrl;
    setTimeout(() => URL.revokeObjectURL(oldUrl), 1000);
  }
  state._pdfExport = null;
  if (!fromPopstate && wasOpen && history.state && history.state.asmaModal === 'pdf-export') {
    try { history.back(); } catch (e) {}
  }
}

async function openPdfExportModal(url, filename, onPrint = null) {
  closePdfExportModal({ fromPopstate: true });
  const modal = document.getElementById('pdf-export-modal');
  const nameEl = document.getElementById('pdf-export-filename');
  const statusEl = document.getElementById('pdf-export-status');
  const directLink = document.getElementById('pdf-export-direct-link');
  const shareBtn = document.getElementById('pdf-export-share-btn');
  const printBtn = document.getElementById('pdf-export-print-btn');

  if (!modal) return;
  if (nameEl) nameEl.textContent = filename;
  if (statusEl) statusEl.textContent = '⏳ Preparazione file PDF dal server...';
  if (directLink) directLink.style.display = 'none';
  if (shareBtn) shareBtn.style.display = 'none';
  if (printBtn) printBtn.style.display = onPrint ? 'inline-flex' : 'none';

  state._pdfExport = { url, filename, onPrint, blob: null, blobUrl: null };
  try {
    if (!history.state || history.state.asmaModal !== 'pdf-export') {
      history.pushState({ asmaTab: state.currentTab, asmaModal: 'pdf-export' }, '', window.location.href);
    }
  } catch (e) {}
  modal.style.display = 'flex';

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    if (!state._pdfExport || state._pdfExport.url !== url) return;

    const blobUrl = URL.createObjectURL(blob);
    state._pdfExport.blob = blob;
    state._pdfExport.blobUrl = blobUrl;

    const kb = Math.max(1, Math.round(blob.size / 1024));
    if (statusEl) statusEl.textContent = `✅ File pronto (${kb} KB). Scegli come procedere:`;

    if (shareBtn && typeof navigator.share === 'function') {
      try {
        const testFile = new File([blob], filename, { type: 'application/pdf' });
        if (navigator.canShare && navigator.canShare({ files: [testFile] })) {
          shareBtn.style.display = 'inline-flex';
        }
      } catch (e) {
        shareBtn.style.display = 'inline-flex';
      }
    }

    if (directLink) {
      directLink.href = blobUrl;
      directLink.download = filename;
      directLink.style.display = 'inline-flex';
    }
  } catch (err) {
    console.warn('PDF export fetch failed:', err);
    if (statusEl) statusEl.textContent = `⚠️ Errore preparazione PDF (${err.message}). Prova "Stampa / Salva come PDF".`;
  }
}

async function shareExportedPdf() {
  const ctx = state._pdfExport;
  if (!ctx || !ctx.blob) return;
  const dlName = ctx.filename || 'spartito.pdf';
  try {
    const file = new File([ctx.blob], dlName, { type: 'application/pdf' });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({
        files: [file],
        title: dlName,
        text: `Spartito ${dlName} generato da ASMA 2.0`
      });
      closePdfExportModal();
      return;
    } else if (typeof navigator.share === 'function') {
      await navigator.share({
        title: dlName,
        url: window.location.href
      });
      closePdfExportModal();
      return;
    }
  } catch (err) {
    if (err && err.name !== 'AbortError') {
      console.warn('Web Share API error:', err);
      showToast('Condivisione non supportata, usa "Salva nei Download"');
    }
  }
}

function triggerDirectAndroidDownload(e) {
  const ctx = state._pdfExport;
  if (!ctx) return;
  if (e) {
    try { e.preventDefault(); } catch (err) {}
  }
  const blobUrl = ctx.blobUrl || (ctx.blob ? URL.createObjectURL(ctx.blob) : null);
  const dlName = ctx.filename || 'spartito.pdf';
  if (blobUrl) {
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = dlName;
    a.rel = 'noopener';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      if (a.parentNode) a.parentNode.removeChild(a);
      showToast(`Download di "${dlName}" avviato`);
      closePdfExportModal();
    }, 300);
  } else if (ctx.url) {
    const a = document.createElement('a');
    a.href = ctx.url;
    a.download = dlName;
    a.target = '_blank';
    a.rel = 'noopener';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      if (a.parentNode) a.parentNode.removeChild(a);
      closePdfExportModal();
    }, 300);
  }
}

function printExportedPdf() {
  const fn = state._pdfExport && state._pdfExport.onPrint;
  closePdfExportModal();
  if (typeof fn === 'function') fn();
}

function downloadPdf() {
  if (!state.selectedSong) {
    showToast('⚠️ Seleziona prima un brano dalla lista per salvarne il PDF');
    return;
  }
  const cleanTitle = (state.selectedSong.title || 'brano').replace(/[^a-zA-Z0-9_\-]/g, '_');
  const filename = `${cleanTitle}.pdf`;
  const qs = buildPdfQueryParams(state.scoreMode === 'chords', { download: 'true' });
  const url = `${API_BASE}/api/songs/${state.selectedSong.uuid}/pdf?${qs}`;
  triggerPdfDownload(url, filename, () => printA4());
}

function updateTopDownloadPdfButton() {
  const btn = document.getElementById('btn-top-download-pdf');
  if (!btn) return;
  if (state.selectedSong && state.selectedSong.title) {
    btn.title = `Salva / Scarica lo spartito PDF di "${state.selectedSong.title}" (${state.activeDevice || 'Dispositivo'})`;
    btn.style.opacity = '1';
    btn.style.cursor = 'pointer';
  } else {
    btn.title = 'Seleziona un brano dalla lista per salvarne lo spartito PDF';
    btn.style.opacity = '0.75';
  }
}

function downloadActiveRepertoirePdf() {
  const workspaceReps = (typeof getWorkspaceRepertoires === 'function') ? getWorkspaceRepertoires() : (state.repertoires || []);
  const officialRep = workspaceReps.find(r => r.is_official) || workspaceReps[0];
  // Default strictly to official band repertoire unless user explicitly selected a personal one
  const targetRep = (state.activeRepertoire && state.activeRepertoire !== '__ALL__' && officialRep && state.activeRepertoire !== officialRep.uuid)
    ? (workspaceReps.find(r => r.uuid === state.activeRepertoire) || officialRep)
    : officialRep;
  downloadRepertoirePdf(targetRep ? targetRep.uuid : (officialRep ? officialRep.uuid : '__OFFICIAL__'), targetRep ? targetRep.name : 'Repertorio Ufficiale Band');
}

function downloadRepertoirePdf(repUuid, repName) {
  const cleanTitle = (repName || 'Repertorio').replace(/[^a-zA-Z0-9_\-]/g, '_');
  const filename = `Repertorio_${cleanTitle}.pdf`;
  const qs = buildPdfQueryParams(false, { download: 'true' });
  const url = `${API_BASE}/api/repertoires/${encodeURIComponent(repUuid)}/pdf?${qs}`;
  triggerPdfDownload(url, filename, () => {
    const printUrl = `${API_BASE}/api/repertoires/${encodeURIComponent(repUuid)}/pdf?${buildPdfQueryParams(false, { download: 'false', autoprint: 'true', a4: 'true' })}`;
    printDirectA4(printUrl);
  });
}

async function printDirectA4(url) {
  const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || '');

  if (isStandalone || isMobile) {
    const cleanTitle = (state.selectedSong?.title || 'spartito').replace(/[^a-zA-Z0-9_\-]/g, '_');
    openPdfExportModal(url, `${cleanTitle}_A4.pdf`, null);
    return;
  }

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
  const currentMusician = state.currentUser?.name || localStorage.getItem('asma_user_name') || 'Puma';
  const currentEmail = state.currentUser?.email || localStorage.getItem('asma_user_email') || '';
  const url = `${API_BASE}/api/songs/${state.selectedSong.uuid}/pdf?chords=${hasChords}&device=${encodeURIComponent(state.activeDevice || 'A4')}&email=${encodeURIComponent(currentEmail)}&user_name=${encodeURIComponent(currentMusician)}&columns=${p.layout_columns || 1}&font_size=${p.layout_font_size || 12}&font_size_chords=${p.layout_font_size_chords || 13}&margin_lateral=${p.layout_margin_lateral || 10}&margin_top=${p.layout_margin_top || 10}&a4=true&autoprint=true`;
  printDirectA4(url);
}

// ----------------------------------------------------------------------------
// A4 PDF EXPORT WITH CUSTOM FONT SIZES & WHATSAPP WEB SHARE
// ----------------------------------------------------------------------------
const shareA4State = {
  targetType: 'song', // 'song' or 'setlist'
  targetUuid: null,
  targetTitle: '',
  fontSizeLyrics: 12,
  fontSizeChords: 13,
  scoreMode: 'chords', // 'chords' or 'lyrics'
  twoCols: false,
  preparedBlob: null,
  preparedFile: null,
  preparedKey: null,
};

let prefetchA4Timer = null;

function getA4CurrentUrlKey() {
  const isSetlist = shareA4State.targetType === 'setlist';
  const targetUuid = shareA4State.targetUuid;
  const hasChords = shareA4State.scoreMode === 'chords';
  const twoCols = !!(document.getElementById('share-a4-two-cols')?.checked);
  const musSelect = document.getElementById('share-a4-musician-select');
  const chosenMusician = musSelect ? musSelect.value : (state.currentUser?.name || localStorage.getItem('asma_user_name') || '');
  return `${isSetlist ? 'setlist' : 'song'}_${targetUuid}_${shareA4State.fontSizeLyrics}_${shareA4State.fontSizeChords}_${hasChords}_${twoCols}_${chosenMusician}`;
}

function resetShareA4Button() {
  const btnShare = document.getElementById('share-a4-whatsapp-btn');
  if (btnShare) {
    btnShare.disabled = false;
    btnShare.style.background = '#25D366';
    btnShare.style.borderColor = '#25D366';
    btnShare.style.color = '#000';
    btnShare.style.boxShadow = 'none';
    btnShare.innerHTML = '<span style="font-size: 18px;">💬</span> Condividi su WhatsApp (Band)';
  }
}

function onShareA4MusicianChanged(val) {
  if (!val) return;
  // Non altera mai l'utente autenticato: aggiorna solo la formattazione A4
  onShareA4OptionsChanged();
}

function onShareA4OptionsChanged() {
  shareA4State.preparedBlob = null;
  shareA4State.preparedFile = null;
  shareA4State.preparedKey = null;
  resetShareA4Button();
  scheduleA4Prefetch(400);
}

function scheduleA4Prefetch(delay = 200) {
  clearTimeout(prefetchA4Timer);
  prefetchA4Timer = setTimeout(() => {
    prefetchA4Pdf();
  }, delay);
}

async function prefetchA4Pdf() {
  const isSetlist = shareA4State.targetType === 'setlist';
  const targetUuid = shareA4State.targetUuid;
  if (!targetUuid) return;

  const currentKey = getA4CurrentUrlKey();
  if (shareA4State.preparedFile && shareA4State.preparedKey === currentKey) {
    return;
  }

  const targetTitle = shareA4State.targetTitle || (isSetlist ? 'Scaletta' : 'Brano');
  const cleanTitle = targetTitle.replace(/[^a-zA-Z0-9_\-]/g, '_');
  const hasChords = shareA4State.scoreMode === 'chords';
  const modeSuffix = hasChords ? 'Accordi' : 'SoloTesto';
  const filename = isSetlist ? `SCALETTA_${cleanTitle}_A4_${modeSuffix}.pdf` : `${cleanTitle}_A4_${modeSuffix}.pdf`;

  const twoColsInput = document.getElementById('share-a4-two-cols');
  const twoCols = twoColsInput ? twoColsInput.checked : false;
  const musSelect = document.getElementById('share-a4-musician-select');
  const chosenMusician = musSelect ? musSelect.value : (state.currentUser?.name || localStorage.getItem('asma_user_name') || 'Puma');
  const matchedUser = (state.usersList || []).find(u => u.name && u.name.toLowerCase() === chosenMusician.toLowerCase());
  const chosenEmail = (matchedUser && matchedUser.email) || state.currentUser?.email || localStorage.getItem('asma_user_email') || '';

  const qs = new URLSearchParams({
    device: 'A4',
    a4: 'true',
    chords: hasChords ? 'true' : 'false',
    columns: twoCols ? '2' : '1',
    font_size: String(shareA4State.fontSizeLyrics),
    font_size_chords: String(shareA4State.fontSizeChords),
    user_name: chosenMusician,
    email: chosenEmail,
    download: 'true'
  }).toString();

  const endpoint = isSetlist ? `setlists/${targetUuid}/pdf` : `songs/${targetUuid}/pdf`;
  const url = `${API_BASE}/api/${endpoint}?${qs}`;

  const statusEl = document.getElementById('share-a4-status');
  if (statusEl && !statusEl.textContent.includes('pronto')) {
    statusEl.innerHTML = '<span style="color:#94a3b8;">⏳ Preparazione PDF per condivisione...</span>';
  }

  try {
    const res = await fetch(url);
    if (!res.ok) return;
    const blob = await res.blob();
    const file = new File([blob], filename, { type: 'application/pdf' });

    if (getA4CurrentUrlKey() === currentKey) {
      shareA4State.preparedBlob = blob;
      shareA4State.preparedFile = file;
      shareA4State.preparedKey = currentKey;
      if (statusEl && !statusEl.textContent.includes('⚠️')) {
        statusEl.innerHTML = '<span style="color:#22c55e;">✅ PDF pronto per condivisione immediata!</span>';
      }
    }
  } catch (e) {
    // Non bloccare: verrà riprovato al click
  }
}

function setShareA4ScoreMode(mode) {
  shareA4State.scoreMode = mode;
  const btnChords = document.getElementById('share-a4-mode-chords');
  const btnLyrics = document.getElementById('share-a4-mode-lyrics');
  const chordsBox = document.getElementById('share-a4-chords-box');

  if (mode === 'chords') {
    if (btnChords) {
      btnChords.style.borderColor = '#38bdf8';
      btnChords.style.color = '#38bdf8';
      btnChords.style.background = 'rgba(56, 189, 248, 0.14)';
    }
    if (btnLyrics) {
      btnLyrics.style.borderColor = '#475569';
      btnLyrics.style.color = '#94a3b8';
      btnLyrics.style.background = 'transparent';
    }
    if (chordsBox) {
      chordsBox.style.opacity = '1';
      chordsBox.style.pointerEvents = 'auto';
    }
  } else {
    if (btnLyrics) {
      btnLyrics.style.borderColor = '#38bdf8';
      btnLyrics.style.color = '#38bdf8';
      btnLyrics.style.background = 'rgba(56, 189, 248, 0.14)';
    }
    if (btnChords) {
      btnChords.style.borderColor = '#475569';
      btnChords.style.color = '#94a3b8';
      btnChords.style.background = 'transparent';
    }
    if (chordsBox) {
      chordsBox.style.opacity = '0.4';
      chordsBox.style.pointerEvents = 'none';
    }
  }
  onShareA4OptionsChanged();
}

function openShareA4Modal() {
  if (!state.selectedSong) return;
  shareA4State.targetType = 'song';
  shareA4State.targetUuid = state.selectedSong.uuid;
  shareA4State.targetTitle = state.selectedSong.title;

  const modal = document.getElementById('share-a4-modal');
  const titleEl = document.getElementById('share-a4-song-title');
  const lyricsVal = document.getElementById('share-a4-lyrics-val');
  const chordsVal = document.getElementById('share-a4-chords-val');
  const twoCols = document.getElementById('share-a4-two-cols');
  const statusEl = document.getElementById('share-a4-status');

  const p = state.userPrefs || {};
  shareA4State.fontSizeLyrics = p.layout_font_size || 12;
  shareA4State.fontSizeChords = p.layout_font_size_chords || 13;
  shareA4State.scoreMode = state.scoreMode === 'chords' ? 'chords' : 'lyrics';
  shareA4State.twoCols = (p.layout_columns || 1) === 2;

  if (titleEl) titleEl.textContent = `🎵 ${state.selectedSong.title} — ${state.selectedSong.artist || 'Band'}`;
  if (lyricsVal) lyricsVal.textContent = `${shareA4State.fontSizeLyrics} pt`;
  if (chordsVal) chordsVal.textContent = `${shareA4State.fontSizeChords} pt`;
  if (twoCols) twoCols.checked = shareA4State.twoCols;
  setShareA4ScoreMode(shareA4State.scoreMode);

  shareA4State.preparedBlob = null;
  shareA4State.preparedFile = null;
  shareA4State.preparedKey = null;
  resetShareA4Button();

  if (statusEl) statusEl.textContent = '📄 Formato: Foglio A4 standard pronto per stampa e condivisione';
  const musSelect = document.getElementById('share-a4-musician-select');
  if (musSelect) {
    musSelect.value = state.currentUser?.name || localStorage.getItem('asma_user_name') || 'Puma';
  }
  if (modal) modal.style.display = 'flex';
  scheduleA4Prefetch(100);
}

function openShareSetlistA4Modal(uuid) {
  const setlist = (state.setlists || []).find(s => s.uuid === uuid) || state.selectedSetlist;
  if (!setlist) return;

  shareA4State.targetType = 'setlist';
  shareA4State.targetUuid = setlist.uuid;
  shareA4State.targetTitle = setlist.title || 'Scaletta';

  const modal = document.getElementById('share-a4-modal');
  const titleEl = document.getElementById('share-a4-song-title');
  const lyricsVal = document.getElementById('share-a4-lyrics-val');
  const chordsVal = document.getElementById('share-a4-chords-val');
  const twoCols = document.getElementById('share-a4-two-cols');
  const statusEl = document.getElementById('share-a4-status');

  const p = state.userPrefs || {};
  shareA4State.fontSizeLyrics = p.layout_font_size || 12;
  shareA4State.fontSizeChords = p.layout_font_size_chords || 13;
  shareA4State.scoreMode = state.scoreMode === 'chords' ? 'chords' : 'lyrics';
  shareA4State.twoCols = (p.layout_columns || 1) === 2;

  const countStr = setlist.item_count || (setlist.items || []).length;
  if (titleEl) titleEl.textContent = `📑 SCALETTA: ${setlist.title} (${countStr} brani)`;
  if (lyricsVal) lyricsVal.textContent = `${shareA4State.fontSizeLyrics} pt`;
  if (chordsVal) chordsVal.textContent = `${shareA4State.fontSizeChords} pt`;
  if (twoCols) twoCols.checked = shareA4State.twoCols;
  setShareA4ScoreMode(shareA4State.scoreMode);

  shareA4State.preparedBlob = null;
  shareA4State.preparedFile = null;
  shareA4State.preparedKey = null;
  resetShareA4Button();

  if (statusEl) statusEl.textContent = '📄 Formato: Foglio A4 per intera scaletta con copertina e indice';
  const musSelect = document.getElementById('share-a4-musician-select');
  if (musSelect) {
    musSelect.value = state.currentUser?.name || localStorage.getItem('asma_user_name') || 'Puma';
  }
  if (modal) modal.style.display = 'flex';
  scheduleA4Prefetch(100);
}

function closeShareA4Modal() {
  clearTimeout(prefetchA4Timer);
  const modal = document.getElementById('share-a4-modal');
  if (modal) modal.style.display = 'none';
}

function adjustA4FontSize(type, delta) {
  if (type === 'lyrics') {
    shareA4State.fontSizeLyrics = Math.max(9, Math.min(22, shareA4State.fontSizeLyrics + delta));
    const el = document.getElementById('share-a4-lyrics-val');
    if (el) el.textContent = `${shareA4State.fontSizeLyrics} pt`;
  } else if (type === 'chords') {
    shareA4State.fontSizeChords = Math.max(10, Math.min(24, shareA4State.fontSizeChords + delta));
    const el = document.getElementById('share-a4-chords-val');
    if (el) el.textContent = `${shareA4State.fontSizeChords} pt`;
  }
  onShareA4OptionsChanged();
}

async function executeShareA4(action = 'whatsapp') {
  const isSetlist = shareA4State.targetType === 'setlist';
  const targetUuid = shareA4State.targetUuid;
  if (!targetUuid) return;

  const targetTitle = shareA4State.targetTitle || (isSetlist ? 'Scaletta' : 'Brano');
  const cleanTitle = targetTitle.replace(/[^a-zA-Z0-9_\-]/g, '_');
  const hasChords = shareA4State.scoreMode === 'chords';
  const modeSuffix = hasChords ? 'Accordi' : 'SoloTesto';
  const filename = isSetlist ? `SCALETTA_${cleanTitle}_A4_${modeSuffix}.pdf` : `${cleanTitle}_A4_${modeSuffix}.pdf`;

  const statusEl = document.getElementById('share-a4-status');
  const btnShare = document.getElementById('share-a4-whatsapp-btn');
  const twoColsInput = document.getElementById('share-a4-two-cols');
  const twoCols = twoColsInput ? twoColsInput.checked : false;
  const musSelect = document.getElementById('share-a4-musician-select');
  const chosenMusician = musSelect ? musSelect.value : (state.currentUser?.name || localStorage.getItem('asma_user_name') || 'Puma');
  const matchedUser = (state.usersList || []).find(u => u.name && u.name.toLowerCase() === chosenMusician.toLowerCase());
  const chosenEmail = (matchedUser && matchedUser.email) || state.currentUser?.email || localStorage.getItem('asma_user_email') || '';

  const qs = new URLSearchParams({
    device: 'A4',
    a4: 'true',
    chords: hasChords ? 'true' : 'false',
    columns: twoCols ? '2' : '1',
    font_size: String(shareA4State.fontSizeLyrics),
    font_size_chords: String(shareA4State.fontSizeChords),
    user_name: chosenMusician,
    email: chosenEmail,
    download: 'true'
  }).toString();

  const endpoint = isSetlist ? `setlists/${targetUuid}/pdf` : `songs/${targetUuid}/pdf`;
  const url = `${API_BASE}/api/${endpoint}?${qs}`;

  if (action === 'print') {
    closeShareA4Modal();
    printDirectA4(`${url}&autoprint=true`);
    return;
  }

  if (action === 'download') {
    closeShareA4Modal();
    const currentKey = getA4CurrentUrlKey();
    if (shareA4State.preparedBlob && shareA4State.preparedKey === currentKey) {
      const blobUrl = URL.createObjectURL(shareA4State.preparedBlob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);
    } else {
      triggerPdfDownload(url, filename, () => printDirectA4(`${url}&autoprint=true`));
    }
    return;
  }

  // Azione WHATSAPP con Web Share API nativa
  const descType = isSetlist ? 'la scaletta' : 'il brano';
  const descMode = hasChords ? 'Con Accordi' : 'Solo Testo Cantante';
  const shareMsg = `Ecco ${descType} "${targetTitle}" (${descMode}) in formato A4 per la band!`;
  const shareTitle = `${targetTitle} (A4 ${descMode})`;

  const currentKey = getA4CurrentUrlKey();

  // Caso 1: il file è già stato preparato ed è in memoria (nessuna attesa di rete -> transient user activation garantita)
  if (shareA4State.preparedFile && shareA4State.preparedKey === currentKey) {
    try {
      if (navigator.canShare && navigator.canShare({ files: [shareA4State.preparedFile] })) {
        await navigator.share({
          files: [shareA4State.preparedFile],
          title: shareTitle,
          text: shareMsg
        });
        if (statusEl) statusEl.textContent = '✓ Condiviso!';
        closeShareA4Modal();
        return;
      } else if (navigator.share) {
        await navigator.share({
          title: shareTitle,
          text: `${shareMsg}\nScarica PDF: ${url}`,
          url: url
        });
        closeShareA4Modal();
        return;
      }
    } catch (shareErr) {
      if (shareErr && shareErr.name === 'AbortError') {
        return; // Utente ha chiuso il selettore
      }
      console.warn('Direct share attempt failed:', shareErr);
    }
  }

  // Caso 2: non ancora pronto -> effettua fetch
  if (statusEl) statusEl.innerHTML = '<span style="color:#38bdf8;">⏳ Generazione PDF scaletta in corso...</span>';
  if (btnShare) {
    btnShare.disabled = true;
    btnShare.innerHTML = '<span>⏳</span> Generazione in corso...';
  }

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const file = new File([blob], filename, { type: 'application/pdf' });

    shareA4State.preparedBlob = blob;
    shareA4State.preparedFile = file;
    shareA4State.preparedKey = currentKey;

    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      try {
        await navigator.share({
          files: [file],
          title: shareTitle,
          text: shareMsg
        });
        if (statusEl) statusEl.textContent = '✓ Condiviso!';
        closeShareA4Modal();
        return;
      } catch (postFetchErr) {
        if (postFetchErr && postFetchErr.name === 'AbortError') {
          resetShareA4Button();
          return;
        }
        // Se Safari/iOS ha fatto scadere il gesto utente durante l'attesa del download (NotAllowedError)
        console.warn('Share blocked by transient activation expiry, enabling immediate one-tap button:', postFetchErr);
        if (statusEl) {
          statusEl.innerHTML = '<span style="color:#22c55e; font-weight:700;">✅ PDF pronto! Tocca il pulsante qui sotto per inviare:</span>';
        }
        if (btnShare) {
          btnShare.disabled = false;
          btnShare.style.background = '#22c55e';
          btnShare.style.borderColor = '#16a34a';
          btnShare.style.color = '#000';
          btnShare.style.boxShadow = '0 0 16px rgba(34, 197, 94, 0.6)';
          btnShare.innerHTML = '<span style="font-size: 20px;">📲</span> TOCCA QUI PER INVIARE SU WHATSAPP';
        }
        return;
      }
    } else if (navigator.share) {
      await navigator.share({
        title: shareTitle,
        text: `${shareMsg}\nScarica PDF: ${url}`,
        url: url
      });
      closeShareA4Modal();
    } else {
      const msg = encodeURIComponent(`${shareMsg}\n${url}`);
      window.open(`https://api.whatsapp.com/send?text=${msg}`, '_blank');
      triggerPdfDownload(url, filename);
      closeShareA4Modal();
    }
  } catch (err) {
    resetShareA4Button();
    if (err && err.name !== 'AbortError') {
      console.warn('Share error:', err);
      if (statusEl) statusEl.textContent = `⚠️ Errore (${err.message}). Puoi usare "Scarica PDF A4".`;
    }
  }
}

// ----------------------------------------------------------------------------
// LIVE STAGE & TELEPROMPTER (60fps Touch & Bluetooth Pedals)
// ----------------------------------------------------------------------------
function startSingleSongStage() {
  if (!state.selectedSong) return;
  // Resilience: ensure aml_content is present from state.songs or snapshot
  if (!state.selectedSong.aml_content && state.songs) {
    const fullSong = state.songs.find(s => s.uuid === state.selectedSong.uuid);
    if (fullSong && fullSong.aml_content) {
      state.selectedSong.aml_content = fullSong.aml_content;
    }
  }
  state.stageSongs = [{
    ...state.selectedSong,
    _baseAml: state.selectedSong.aml_content,
    _baseKey: state.selectedSong.key_current,
    _stageDelta: 0
  }];
  state.stageIndex = 0;
  openStageModal({ resetScroll: true });
}

async function openStageModal({ resetScroll = true, scrollToBottom = false } = {}) {
  state.isStageActive = true;
  state.isAutoscrolling = false;

  const currentSong = state.stageSongs[state.stageIndex];
  const stageModal = document.getElementById('stage-modal');
  if (!stageModal || !currentSong) return;

  const wasHidden = stageModal.style.display === 'none' || !stageModal.style.display;
  stageModal.style.display = 'flex';
  logAuditEvent('STAGE_VIEW', 'SONG', currentSong.uuid, { title: currentSong.title, mode: state.stageViewType || 'teleprompter' });
  if (wasHidden) {
    try {
      if (!history.state || history.state.asmaModal !== 'stage') {
        history.pushState({ asmaTab: state.currentTab, asmaModal: 'stage' }, '', window.location.href);
      }
    } catch (e) {}
  }
  updateStageHeaderMeta(currentSong);
  updateStageTransposeBadge(currentSong);

  await renderStageSong(currentSong, { resetScroll, scrollToBottom });
}

function updateStageHeaderMeta(currentSong) {
  const titleEl = document.getElementById('stage-song-title');
  const metaEl = document.getElementById('stage-song-meta');
  const isMultiSong = state.stageSongs && state.stageSongs.length > 1;

  if (titleEl) {
    if (isMultiSong) {
      titleEl.textContent = `[${state.stageIndex + 1}/${state.stageSongs.length}] ${currentSong.title}`;
    } else {
      titleEl.textContent = currentSong.title;
    }
  }

  if (metaEl) {
    const delta = currentSong._stageDelta || 0;
    const shiftTag = delta !== 0 ? ` (${delta > 0 ? '+' : ''}${delta} st al volo)` : '';
    const prefix = isMultiSong ? `Brano ${state.stageIndex + 1} di ${state.stageSongs.length} • ` : '';
    metaEl.textContent = `${prefix}${currentSong.artist || 'Band'} • Tonalità: ${toLatinKey(currentSong.key_current)}${shiftTag} • ${currentSong.bpm || 120} BPM • Capo: ${currentSong.capo || 0}°`;
  }

  const prevSongBtn = document.getElementById('stage-btn-prev-song');
  const nextSongBtn = document.getElementById('stage-btn-next-song');
  if (prevSongBtn) prevSongBtn.style.display = isMultiSong ? 'inline-flex' : 'none';
  if (nextSongBtn) nextSongBtn.style.display = isMultiSong ? 'inline-flex' : 'none';
}

function updateStageTransposeBadge(currentSong) {
  const badge = document.getElementById('stage-transpose-badge');
  if (!badge || !currentSong) return;
  const delta = currentSong._stageDelta || 0;
  if (delta === 0) {
    badge.textContent = 'Orig.';
    badge.style.color = '#94a3b8';
  } else {
    badge.textContent = `${delta > 0 ? '+' : ''}${delta} (${toLatinKey(currentSong.key_current)})`;
    badge.style.color = '#ffd600';
  }
}

async function transposeStageLive(semitones) {
  const currentSong = state.stageSongs[state.stageIndex];
  if (!currentSong) return;

  const baseAml = currentSong._baseAml !== undefined ? currentSong._baseAml : currentSong.aml_content;
  const baseKey = currentSong._baseKey !== undefined ? currentSong._baseKey : currentSong.key_current;
  currentSong._baseAml = baseAml;
  currentSong._baseKey = baseKey;

  let nextDelta = (currentSong._stageDelta || 0) + semitones;
  if (nextDelta > 11) nextDelta -= 12;
  if (nextDelta < -11) nextDelta += 12;
  currentSong._stageDelta = nextDelta;

  currentSong.aml_content = nextDelta === 0 ? baseAml : transposeAmlText(baseAml, nextDelta);
  currentSong.key_current = nextDelta === 0 ? baseKey : transposeSingleChord(baseKey, nextDelta);

  updateStageHeaderMeta(currentSong);
  updateStageTransposeBadge(currentSong);
  await renderStageSong(currentSong);

  const label = nextDelta === 0
    ? `Tonalità originale: ${toLatinKey(currentSong.key_current)}`
    : `Tonalità temporanea palco: ${toLatinKey(currentSong.key_current)} (${nextDelta > 0 ? '+' : ''}${nextDelta} st • non salvata)`;
  showToast(label);
}

function _renderPdfPagesInStageContainer(container, data, scrollToBottom, prevScroll, isFromCache = false) {
  container.innerHTML = `
    ${isFromCache ? `
      <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 6px; padding: 6px 12px; margin: 6px 12px 10px 12px; font-size: 12px; color: #38bdf8; display: flex; align-items: center; justify-content: space-between;">
        <span>📄 <b>Spartito PDF da Cache Offline</b> (${escapeHtml(data.device || state.activeDevice)})</span>
        <span style="color: #94a3b8; font-size: 11px;">Pronto per il palco</span>
      </div>
    ` : ''}
    <div class="stage-pdf-container">
      ${data.pages.map((b64, idx) => `
        <div class="stage-pdf-page" id="stage-pdf-page-${idx}" data-page-index="${idx}" style="position: relative;">
          <img src="${b64}" alt="Pagina ${idx + 1} di ${data.total_pages}" />
          ${data.total_pages > 1 ? `
            <div style="position: absolute; top: 10px; right: 12px; background: rgba(15, 23, 42, 0.85); color: #ffd600; font-size: 11.5px; font-weight: 800; padding: 3px 9px; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.5); pointer-events: none; border: 1px solid rgba(255, 214, 0, 0.4);">
              Pag. ${idx + 1} / ${data.total_pages}
            </div>
          ` : ''}
        </div>
      `).join('')}
    </div>
  `;
  if (scrollToBottom) {
    setTimeout(() => {
      const pages = container.querySelectorAll('.stage-pdf-page');
      if (pages.length > 0) {
        const lastPage = pages[pages.length - 1];
        const containerRect = container.getBoundingClientRect();
        const pageRect = lastPage.getBoundingClientRect();
        const target = Math.max(0, container.scrollTop + (pageRect.top - containerRect.top) - 6);
        container.scrollTop = target;
        scrollAccumulator = target;
      }
    }, 40);
  } else {
    container.scrollTop = prevScroll;
    scrollAccumulator = prevScroll;
  }
}

function _renderStageOfflineFallback(container, currentSong, prevScroll, scrollToBottom) {
  let teleprompterHtml = '';
  try {
    teleprompterHtml = parseAmlForWeb(currentSong.aml_content, state.scoreMode === 'chords');
  } catch (e) {
    teleprompterHtml = `<pre style="padding: 20px; color: #fff;">${escapeHtml(currentSong.aml_content || '')}</pre>`;
  }
  const offlineNotice = `
    <div class="stage-offline-pill" style="background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(56, 189, 248, 0.5); border-radius: 8px; padding: 10px 14px; margin: 10px 14px 16px 14px; color: #93c5fd; font-size: 13px; display: flex; align-items: center; justify-content: space-between; gap: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 18px;">📡</span>
        <div>
          <span style="font-weight: 700; color: #fff;">Modalità Palco Offline</span> &bull; Spartito PDF non pre-caricato in cache.
          <div style="font-size: 11.5px; color: #94a3b8; margin-top: 2px;">Teleprompter notturno attivo con accordi e testo completi al 100%.</div>
        </div>
      </div>
      <button onclick="toggleStageViewType()" class="btn btn-secondary" style="background: rgba(56, 189, 248, 0.2); border: 1px solid #38bdf8; color: #38bdf8; font-size: 11.5px; font-weight: 700; padding: 4px 10px; border-radius: 6px; cursor: pointer; white-space: nowrap;">Passa a Teleprompter</button>
    </div>
  `;
  container.innerHTML = offlineNotice + teleprompterHtml;
  if (scrollToBottom) {
    setTimeout(() => {
      const maxScroll = Math.max(0, container.scrollHeight - container.clientHeight);
      container.scrollTop = maxScroll;
      scrollAccumulator = maxScroll;
    }, 40);
  } else {
    container.scrollTop = prevScroll;
    scrollAccumulator = prevScroll;
  }
}

async function renderStageSong(currentSong, { resetScroll = false, scrollToBottom = false } = {}) {
  const container = document.getElementById('stage-lyrics');
  if (!container || !currentSong) return;

  // Resilience: ensure currentSong has aml_content
  if (!currentSong.aml_content) {
    const backup = (state.songs || []).find(s => s.uuid === currentSong.uuid) || state.selectedSong;
    if (backup && backup.aml_content) {
      currentSong.aml_content = backup.aml_content;
      currentSong._baseAml = backup.aml_content;
    }
  }

  updateStageViewButton();
  updateStageScoreModeButton();
  updateStageHeaderMeta(currentSong);
  updateStageTransposeBadge(currentSong);

  const prevScroll = resetScroll ? 0 : (container.scrollTop || 0);

  if (state.stageViewType === 'pdf') {
    const hasChords = state.scoreMode === 'chords';
    const stageDelta = currentSong._stageDelta || 0;

    // Check offline cache first
    const cachedData = getPdfPreviewCache(currentSong.uuid, state.activeDevice, hasChords, stageDelta);
    let renderedFromCache = false;

    if (cachedData && cachedData.pages && cachedData.pages.length > 0) {
      _renderPdfPagesInStageContainer(container, cachedData, scrollToBottom, prevScroll, true);
      renderedFromCache = true;
    } else {
      container.innerHTML = `<div style="text-align:center; padding:50px 16px; color:#94a3b8;"><div style="font-size:32px; margin-bottom:10px;">⏳</div>Caricamento spartito PDF per il palco...</div>`;
    }

    try {
      const p = state.userPrefs;
      const url = `${API_BASE}/api/songs/${currentSong.uuid}/pdf/preview?chords=${hasChords}&device=${encodeURIComponent(state.activeDevice)}&email=${encodeURIComponent(state.currentUser.email)}&user_name=${encodeURIComponent(state.currentUser.name || '')}&columns=${p.layout_columns || 1}&font_size=${p.layout_font_size || 12}&font_size_chords=${p.layout_font_size_chords || 13}&margin_lateral=${p.layout_margin_lateral || 10}&margin_top=${p.layout_margin_top || 10}&margin_bottom=${p.layout_margin_bottom || 14}&transpose=${stageDelta}&_v=${Date.now()}`;
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        savePdfPreviewCache(currentSong.uuid, state.activeDevice, hasChords, stageDelta, data);
        _renderPdfPagesInStageContainer(container, data, scrollToBottom, prevScroll, false);
      } else {
        if (!renderedFromCache) {
          _renderStageOfflineFallback(container, currentSong, prevScroll, scrollToBottom);
        }
      }
    } catch (err) {
      console.warn('Stage PDF preview fetch failed (offline or network error):', err);
      if (!renderedFromCache) {
        _renderStageOfflineFallback(container, currentSong, prevScroll, scrollToBottom);
      }
    }
  } else {
    // TELEPROMPTER VIEW
    try {
      const savedStageSize = localStorage.getItem('asma_stage_font_size');
      if (savedStageSize) {
        container.style.fontSize = `${savedStageSize}px`;
      }
    } catch (e) {}
    try {
      container.innerHTML = parseAmlForWeb(currentSong.aml_content, state.scoreMode === 'chords');
    } catch (parseErr) {
      console.error('Error rendering stage teleprompter:', parseErr);
      container.innerHTML = `<div style="padding: 20px; color: #ef4444;">Errore visualizzazione teleprompter: ${escapeHtml(parseErr.message)}<pre style="color: #fff; margin-top: 10px;">${escapeHtml(currentSong.aml_content || '')}</pre></div>`;
    }

    if (scrollToBottom) {
      setTimeout(() => {
        const maxScroll = Math.max(0, container.scrollHeight - container.clientHeight);
        container.scrollTop = maxScroll;
        scrollAccumulator = maxScroll;
      }, 40);
    } else {
      container.scrollTop = prevScroll;
      scrollAccumulator = prevScroll;
    }
  }

  container.style.scrollBehavior = 'auto';

  container.onscroll = () => {
    if (!state.isAutoscrolling) {
      scrollAccumulator = container.scrollTop;
    } else {
      // Sincronizza accumulator se l'utente interagisce manualmente su PC o tablet
      if (Math.abs(container.scrollTop - scrollAccumulator) > 30) {
        scrollAccumulator = container.scrollTop;
      }
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
  const topBtn = document.getElementById('stage-header-view-btn');
  const isPdf = state.stageViewType === 'pdf';

  if (btn) {
    if (isPdf) {
      btn.innerHTML = '📄 Spartito PDF';
      btn.style.color = '#38bdf8';
      btn.style.borderColor = '#38bdf8';
      btn.title = 'Attualmente su Spartito PDF reale. Clicca per passare al Teleprompter testo.';
    } else {
      btn.innerHTML = '🎤 Teleprompter';
      btn.style.color = '#ffd600';
      btn.style.borderColor = '#ffd600';
      btn.title = 'Attualmente su Teleprompter testo notte. Clicca per passare allo Spartito PDF.';
    }
  }

  if (topBtn) {
    if (isPdf) {
      topBtn.innerHTML = '🎤 <span class="stage-view-full-text">Passa a </span>Teleprompter';
      topBtn.style.color = '#ffd600';
      topBtn.style.borderColor = '#ffd600';
      topBtn.title = 'Passa a Teleprompter testo (sfondo scuro ad alto contrasto)';
    } else {
      topBtn.innerHTML = '📄 <span class="stage-view-full-text">Passa a </span>Spartito PDF';
      topBtn.style.color = '#38bdf8';
      topBtn.style.borderColor = '#38bdf8';
      topBtn.title = 'Passa a visualizzazione Spartito PDF originale';
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
    applyPreferencesToDom();
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

function closeStageModal({ fromPopstate = false } = {}) {
  stopAutoscroll();
  if (metronomeTimer) {
    clearInterval(metronomeTimer);
    metronomeTimer = null;
  }
  isMetronomeActive = false;
  state.isStageActive = false;
  const stageModal = document.getElementById('stage-modal');
  const wasOpen = stageModal && stageModal.style.display !== 'none';
  if (stageModal) stageModal.style.display = 'none';
  if (!fromPopstate && wasOpen && history.state && history.state.asmaModal === 'stage') {
    try { history.back(); } catch (e) {}
  }
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
    container.style.scrollBehavior = 'auto';
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

function applyStageScroll(container, target) {
  scrollAccumulator = target;
  try {
    container.scrollTo({ top: target, behavior: 'smooth' });
  } catch (e) {
    container.scrollTop = target;
  }
}

function stageNextPage() {
  const container = document.getElementById('stage-lyrics');
  if (!container) return;

  const clientH = container.clientHeight || window.innerHeight;
  const scrollH = container.scrollHeight;
  const currentScroll = container.scrollTop;
  const maxScroll = Math.max(0, scrollH - clientH);

  // Se siamo già arrivati in fondo allo spartito (entro 25px dal fondo)
  if (currentScroll >= maxScroll - 25) {
    if (state.stageIndex < state.stageSongs.length - 1) {
      stageNextSong();
    } else {
      showToast('📄 Sei all\'ultima pagina');
    }
    return;
  }

  if (state.stageViewType === 'pdf') {
    const pages = Array.from(container.querySelectorAll('.stage-pdf-page'));
    const totalPages = pages.length;

    if (totalPages > 1) {
      const cRect = container.getBoundingClientRect();
      
      // Trova la pagina attualmente visibile
      let currentIdx = 0;
      for (let i = 0; i < pages.length; i++) {
        const pRect = pages[i].getBoundingClientRect();
        if (pRect.bottom - cRect.top > 80) {
          currentIdx = i;
          break;
        }
      }

      const curPage = pages[currentIdx];
      const curPageRect = curPage.getBoundingClientRect();
      const curPageBottomRel = curPageRect.bottom - cRect.top;

      // Se la pagina corrente ha ancora contenuto nascosto in basso oltre lo schermo
      if (curPageBottomRel > clientH + 40) {
        const step = Math.floor(clientH * 0.85);
        const target = Math.min(maxScroll, currentScroll + step);
        applyStageScroll(container, target);
        showToast(`📄 Pagina ${currentIdx + 1} di ${totalPages}`);
        return;
      }

      // Altrimenti salta alla pagina successiva
      if (currentIdx + 1 < totalPages) {
        const nextPage = pages[currentIdx + 1];
        const nextRelTop = nextPage.getBoundingClientRect().top - cRect.top;
        const target = Math.min(maxScroll, Math.max(0, currentScroll + nextRelTop - 4));
        applyStageScroll(container, target);
        showToast(`📄 Pagina ${currentIdx + 2} di ${totalPages}`);
        return;
      }
    }
  }

  // Modalità Teleprompter o fallback PDF pagina singola:
  // Avanza di una schermata (85% dell'altezza visibile)
  const step = Math.max(200, Math.floor(clientH * 0.85));
  const target = Math.min(maxScroll, currentScroll + step);
  applyStageScroll(container, target);
  showToast('📄 Pagina successiva');
}

function stagePrevPage() {
  const container = document.getElementById('stage-lyrics');
  if (!container) return;

  const clientH = container.clientHeight || window.innerHeight;
  const currentScroll = container.scrollTop;

  // Se siamo già in cima allo spartito (entro 25px dalla cima)
  if (currentScroll <= 25) {
    if (state.stageIndex > 0) {
      stagePrevSong({ scrollToBottom: true });
    } else {
      showToast('📄 Sei all\'inizio dello spartito');
    }
    return;
  }

  if (state.stageViewType === 'pdf') {
    const pages = Array.from(container.querySelectorAll('.stage-pdf-page'));
    const totalPages = pages.length;

    if (totalPages > 1) {
      const cRect = container.getBoundingClientRect();

      let currentIdx = 0;
      for (let i = 0; i < pages.length; i++) {
        const pRect = pages[i].getBoundingClientRect();
        if (pRect.bottom - cRect.top > 80) {
          currentIdx = i;
          break;
        }
      }

      const curPage = pages[currentIdx];
      const curPageTopRel = curPage.getBoundingClientRect().top - cRect.top;

      // Se siamo dentro la pagina corrente ma non alla sua sommità
      if (curPageTopRel < -40) {
        const step = Math.floor(clientH * 0.85);
        const target = Math.max(0, Math.max(currentScroll + curPageTopRel, currentScroll - step));
        applyStageScroll(container, target);
        showToast(`📄 Pagina ${currentIdx + 1} di ${totalPages}`);
        return;
      }

      // Altrimenti salta alla pagina precedente
      if (currentIdx > 0) {
        const prevPage = pages[currentIdx - 1];
        const prevRelTop = prevPage.getBoundingClientRect().top - cRect.top;
        const target = Math.max(0, currentScroll + prevRelTop - 4);
        applyStageScroll(container, target);
        showToast(`📄 Pagina ${currentIdx} di ${totalPages}`);
        return;
      }
    }
  }

  // Modalità Teleprompter o fallback PDF pagina singola:
  // Risali di una schermata (85% dell'altezza visibile)
  const step = Math.max(200, Math.floor(clientH * 0.85));
  const target = Math.max(0, currentScroll - step);
  applyStageScroll(container, target);
  showToast('📄 Pagina precedente');
}

function stageNextSong() {
  if (state.stageIndex < state.stageSongs.length - 1) {
    state.stageIndex++;
    openStageModal({ resetScroll: true });
    showToast(`Brano ${state.stageIndex + 1} di ${state.stageSongs.length}: ${state.stageSongs[state.stageIndex].title}`);
  } else {
    showToast('Ultimo brano della scaletta');
  }
}

function stagePrevSong({ scrollToBottom = false } = {}) {
  if (state.stageIndex > 0) {
    state.stageIndex--;
    openStageModal({ resetScroll: !scrollToBottom, scrollToBottom });
    showToast(`Brano ${state.stageIndex + 1} di ${state.stageSongs.length}: ${state.stageSongs[state.stageIndex].title}`);
  } else {
    showToast('Primo brano della scaletta');
  }
}

// ----------------------------------------------------------------------------
// BLUETOOTH PEDALS & KEYBOARD LISTENERS
// ----------------------------------------------------------------------------
function initKeyboardAndPedals() {
  window.addEventListener('keydown', (e) => {
    if (!state.isStageActive) return;

    if (e.key === 'PageDown' || e.key === 'ArrowDown' || e.key === 'ArrowRight' || e.key === '3') {
      stageNextPage();
      e.preventDefault();
    }
    else if (e.key === 'PageUp' || e.key === 'ArrowUp' || e.key === 'ArrowLeft' || e.key === '1') {
      stagePrevPage();
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

  // Supporto rotella del mouse su PC durante teleprompter palco
  window.addEventListener('wheel', (e) => {
    if (!state.isStageActive) return;
    const container = document.getElementById('stage-lyrics');
    if (!container) return;
    if (state.isAutoscrolling) {
      scrollAccumulator = Math.max(0, scrollAccumulator + e.deltaY);
      container.scrollTop = scrollAccumulator;
    }
  }, { passive: true });

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
        stageNextPage();
      } else {
        stagePrevPage();
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
      saveOfflineSnapshot(SNAPSHOT_KEYS.SETLISTS, state.setlists);
      renderSetlists();
      renderDashboard();
    }
  } catch (err) {
    console.warn('Setlists error, loading from local snapshot:', err);
    const cached = loadOfflineSnapshot(SNAPSHOT_KEYS.SETLISTS);
    if (cached && Array.isArray(cached) && cached.length > 0) {
      state.setlists = cached;
      renderSetlists();
      renderDashboard();
    }
  }
}

function renderSetlists() {
  const container = document.getElementById('setlists-list');
  if (!container) return;

  const editing = isEditingMode();
  if (state.setlists.length === 0) {
    container.innerHTML = editing
      ? '<div style="padding: 20px; color:#94a3b8;">Nessuna scaletta presente. Creane una con il tasto "+ Nuova Scaletta".</div>'
      : '<div style="padding: 20px; color:#94a3b8;">Nessuna scaletta presente.</div>';
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
        <button class="btn btn-secondary" style="color: #25D366; border-color: #25D366; font-weight: 800; min-height:36px; padding:4px 12px;" onclick="event.stopPropagation(); openShareSetlistA4Modal('${s.uuid}')" title="Condividi o stampa la scaletta in formato A4 su WhatsApp">📤 A4 / WhatsApp</button>
        <button class="btn btn-secondary" style="min-height:36px; padding:4px 12px;" onclick="event.stopPropagation(); downloadSetlistPdf('${s.uuid}')">💾 PDF Tablet</button>
        <button class="btn btn-secondary" style="min-height:36px; padding:4px 12px;" onclick="event.stopPropagation(); printSetlistA4('${s.uuid}')">🖨️ Stampa A4</button>
        <button class="btn btn-secondary" style="min-height:36px; padding:4px 12px;" onclick="event.stopPropagation(); openSetlistDetail('${s.uuid}')">${editing ? '✏️ Modifica' : '👁️ Vedi Scaletta'}</button>
        ${editing ? `<button class="btn btn-danger" style="min-height:36px; padding:4px 12px;" onclick="event.stopPropagation(); deleteSetlist('${s.uuid}')">🗑️ Elimina</button>` : ''}
      </div>
    </div>
  `).join('');
}

function downloadSetlistPdf(uuid) {
  const filename = 'SCALETTA_LIVE.pdf';
  const qs = buildPdfQueryParams(state.scoreMode === 'chords', { download: 'true' });
  const url = `${API_BASE}/api/setlists/${uuid}/pdf?${qs}`;
  triggerPdfDownload(url, filename, () => printSetlistA4(uuid));
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
  const editing = isEditingMode();
  const minutes = Math.floor((s.total_duration_seconds || 0) / 60);

  const itemsHtml = (s.items || []).map((item, idx) => {
    let transitionBadge = '';
    if (idx > 0) {
      const prev = s.items[idx - 1];
      const trans = calculateFifthsTransition(prev.key, prev.bpm, item.key, item.bpm);
      transitionBadge = `
        <div style="display:flex; align-items:center; gap:8px; margin: 4px 0 6px 24px; font-size:11.5px; color:${trans.color}; background:rgba(15,23,42,0.85); padding:4px 10px; border-radius:6px; border-left:3px solid ${trans.color};">
          <span>🎼</span>
          <span><b>Transizione:</b> ${escapeHtml(trans.label)} &bull; Quinte: <b>${trans.distance}</b> &bull; Δ BPM: <b>${trans.bpmDelta >= 0 ? '+' : ''}${trans.bpmDelta}</b> (${trans.bpmDiffPct}%)</span>
          <button type="button" class="btn btn-secondary" style="font-size:10px; padding:1px 6px; min-height:20px; margin-left:auto; color:#facc15; border-color:#eab308;" onclick="openCircleOfFifthsModal('${item.key || ''}')">Circolo Quinte ↗</button>
        </div>
      `;
    }
    return `
      ${transitionBadge}
      <div class="setlist-item-row">
        <div style="font-weight:900; color:#38bdf8; min-width:24px;">${idx + 1}.</div>
        <div style="flex:1;">
          <div style="font-weight:700; color:#fff;">${escapeHtml(item.title)}</div>
          <div style="font-size:12px; color:#94a3b8;">
            ${escapeHtml(item.artist || '')} &bull; Tonalità: <b style="color:#ffd600;">${toLatinKey(item.key)}</b>
            &bull; Tempo: <b>${item.bpm} BPM</b> ${item.is_medley ? '<span class="badge" style="background:#7c3aed; color:#fff; font-size:10px; margin-left:6px;">🔗 MEDLEY</span>' : ''}
          </div>
        </div>
        ${editing ? `
        <div style="display:flex; gap:6px;">
          <button class="btn btn-secondary" style="min-height:34px; width:34px; padding:0;" title="Sposta su" onclick="moveSetlistItem(${idx}, -1)" ${idx === 0 ? 'disabled' : ''}>▲</button>
          <button class="btn btn-secondary" style="min-height:34px; width:34px; padding:0;" title="Sposta giù" onclick="moveSetlistItem(${idx}, 1)" ${idx === s.items.length - 1 ? 'disabled' : ''}>▼</button>
          <button class="btn btn-secondary" style="min-height:34px; padding:0 8px; font-size:11px;" title="Attiva/disattiva Medley" onclick="toggleSetlistMedley(${idx})">🔗</button>
          <button class="btn btn-secondary" style="min-height:34px; width:34px; padding:0; color:#ef4444;" title="Rimuovi" onclick="removeSetlistItem(${idx})">✕</button>
        </div>` : ''}
      </div>
    `;
  }).join('');

  // Song options for "+ Aggiungi Brano": raggruppati per Ufficiale e Personale, deduplicati
  let songOptions = '';
  if (editing) {
    const officialRep = (state.repertoires || []).find(r => r.is_official);
    const officialUuids = new Set((officialRep && officialRep.song_uuids) || []);

    const officialSongs = [];
    const personalSongs = [];
    const seenUuids = new Set();

    (state.songs || []).forEach(song => {
      if (!song || !song.uuid || seenUuids.has(song.uuid)) return;
      seenUuids.add(song.uuid);
      if (officialUuids.has(song.uuid)) {
        officialSongs.push(song);
      } else {
        personalSongs.push(song);
      }
    });

    officialSongs.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
    personalSongs.sort((a, b) => (a.title || '').localeCompare(b.title || ''));

    if (officialSongs.length > 0) {
      songOptions += `<optgroup label="⭐ Repertorio Ufficiale Band (${officialSongs.length})">` +
        officialSongs.map(song =>
          `<option value="${song.uuid}">${escapeHtml(song.title)} (${escapeHtml(song.artist || 'Band')}) [Tonalità: ${escapeHtml(toLatinKey(song.key_current))}]</option>`
        ).join('') + `</optgroup>`;
    }
    if (personalSongs.length > 0) {
      songOptions += `<optgroup label="👤 Repertorio Personale / Copie (${personalSongs.length})">` +
        personalSongs.map(song =>
          `<option value="${song.uuid}">[Copia Personale] ${escapeHtml(song.title)} (${escapeHtml(song.artist || 'Band')}) [Tonalità: ${escapeHtml(toLatinKey(song.key_current))}]</option>`
        ).join('') + `</optgroup>`;
    }
  }

  const addSongSectionHtml = editing ? `
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
      </div>` : '';

  container.innerHTML = `
    <div class="song-viewer" style="margin-bottom:14px;">
      <div class="viewer-header">
        <div>
          <h2 id="setlist-header-title" style="font-size: 22px; font-weight: 900; color: #fff;">📑 ${escapeHtml(s.title)}</h2>
          <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
            <b id="setlist-header-date" style="color: #ffd600;">${escapeHtml(formatDateDDMMYYYY(s.date) || 'Data da definire')}</b> &bull; <span id="setlist-header-desc">${escapeHtml(s.description || '')}</span> &bull; Durata: <b>${minutes} min</b> (${s.total_songs || s.items.length} brani)${editing ? '' : ' &bull; <span style="color:#34d399; font-weight:700;">Sola lettura</span>'}
          </div>
        </div>
        <div class="viewer-tools">
          <button class="btn btn-primary" onclick="loadAndPlaySetlist('${s.uuid}')">🎤 Avvia Palco</button>
          <button class="btn btn-secondary" style="color: #facc15; border-color: #eab308; font-weight: 800;" onclick="openCircleOfFifthsModal('')" title="Apri il Circolo delle Quinte per pianificare cambi tonalità e medley">🎼 Circolo Quinte</button>
          <button class="btn btn-secondary" style="color: #25D366; border-color: #25D366; font-weight: 800;" onclick="openShareSetlistA4Modal('${s.uuid}')" title="Condividi o stampa la scaletta in formato A4 su WhatsApp">📤 A4 / WhatsApp</button>
          <button class="btn btn-secondary" onclick="downloadSetlistPdf('${s.uuid}')">💾 PDF Tablet</button>
          <button class="btn btn-secondary" onclick="printSetlistA4('${s.uuid}')">🖨️ Stampa A4</button>
          ${editing ? `<button class="btn btn-danger" onclick="deleteSetlist('${s.uuid}')">🗑️ Elimina Scaletta</button>` : ''}
          <button class="btn btn-secondary" onclick="closeSetlistDetail()">✕ Chiudi</button>
        </div>
      </div>
      ${editing ? `
      <!-- SETLIST METADATA EDITING (DATE, TITLE, DESCRIPTION) -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin: 12px 0; background: rgba(15, 23, 42, 0.6); padding: 12px 14px; border-radius: 8px; border: 1px solid #334155;">
        <div>
          <label style="font-size: 11px; color: #94a3b8; font-weight: 700; display: block; margin-bottom: 3px;">Titolo Scaletta</label>
          <input type="text" id="edit-setlist-title" class="search-input" style="width: 100%;" value="${escapeHtml(s.title || '')}" onchange="updateSetlistMeta('title', this.value)">
        </div>
        <div>
          <label style="font-size: 11px; color: #94a3b8; font-weight: 700; display: block; margin-bottom: 3px;">📅 Data di Esecuzione</label>
          <input type="date" id="edit-setlist-date" class="search-input" style="width: 100%; color: #ffd600; font-weight: 800;" value="${s.date ? s.date.slice(0, 10) : ''}" onchange="updateSetlistMeta('date', this.value)">
        </div>
        <div>
          <label style="font-size: 11px; color: #94a3b8; font-weight: 700; display: block; margin-bottom: 3px;">Descrizione / Location</label>
          <input type="text" id="edit-setlist-desc" class="search-input" style="width: 100%;" value="${escapeHtml(s.description || '')}" onchange="updateSetlistMeta('description', this.value)">
        </div>
      </div>` : ''}
      ${addSongSectionHtml}
      <!-- ITEMS LIST -->
      <div style="margin-top:14px;">
        ${itemsHtml || (editing ? '<div style="color:#94a3b8; padding:16px;">Nessun brano in questa scaletta. Aggiungine uno sopra!</div>' : '<div style="color:#94a3b8; padding:16px;">Nessun brano in questa scaletta.</div>')}
      </div>
    </div>
  `;
}

function updateSetlistMeta(field, val) {
  if (!state.selectedSetlist) return;
  state.selectedSetlist[field] = val;

  const titleDisplay = document.getElementById('setlist-header-title');
  if (titleDisplay && field === 'title') {
    titleDisplay.textContent = `📑 ${val}`;
  }
  const dateDisplay = document.getElementById('setlist-header-date');
  if (dateDisplay && field === 'date') {
    dateDisplay.textContent = formatDateDDMMYYYY(val) || 'Data da definire';
  }
  const descDisplay = document.getElementById('setlist-header-desc');
  if (descDisplay && field === 'description') {
    descDisplay.textContent = val || '';
  }

  saveCurrentSetlist();
}

function moveSetlistItem(index, delta) {
  if (!requireEditingMode() || !state.selectedSetlist || !state.selectedSetlist.items) return;
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
  if (!requireEditingMode() || !state.selectedSetlist || !state.selectedSetlist.items) return;
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
  if (!requireEditingMode()) return;
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
  if (btn) btn.style.display = isEditingMode() ? 'inline-flex' : 'none';
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
  if (!requireEditingMode()) return;
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
  let data = null;
  try {
    const res = await fetch(`${API_BASE}/api/setlists/${uuid}`);
    if (res.ok) {
      data = await res.json();
    }
  } catch (err) {
    console.warn('Setlist play fetch failed (offline), falling back to snapshot:', err);
  }

  if (!data) {
    data = (state.setlists || []).find(s => s.uuid === uuid);
  }
  if (!data) {
    const cachedSetlists = loadOfflineSnapshot(SNAPSHOT_KEYS.SETLISTS);
    if (cachedSetlists && Array.isArray(cachedSetlists)) {
      data = cachedSetlists.find(s => s.uuid === uuid);
    }
  }

  if (data) {
    state.selectedSetlist = data;
    state.stageSongs = [];
    for (let item of (data.items || [])) {
      let sObj = null;
      try {
        const sRes = await fetch(`${API_BASE}/api/songs/${item.song_uuid}`);
        if (sRes.ok) sObj = await sRes.json();
      } catch (e) {}

      if (!sObj) {
        sObj = (state.songs || []).find(s => s.uuid === item.song_uuid);
      }

      if (sObj) {
        state.stageSongs.push({
          ...sObj,
          _baseAml: sObj.aml_content,
          _baseKey: sObj.key_current,
          _stageDelta: 0
        });
      }
    }
    if (state.stageSongs.length > 0) {
      state.stageIndex = 0;
      openStageModal();
      showToast(`Scaletta caricata: ${data.title} (${state.stageSongs.length} brani)`);
    } else {
      showToast('Questa scaletta non contiene brani');
    }
  } else {
    showToast('Impossibile caricare la scaletta');
  }
}

// ----------------------------------------------------------------------------
// ADD TO SETLIST (1-Touch Modal)
// ----------------------------------------------------------------------------
let pendingSetlistSongUuid = null;

async function openAddToSetlistModal(songUuid) {
  if (!requireEditingMode()) return;
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
  if (!requireEditingMode()) return;
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
  if (!requireEditingMode()) return;
  const officialRep = state.repertoires.find(r => r.is_official);
  const isInOfficial = officialRep && officialRep.song_uuids && officialRep.song_uuids.includes(uuid);
  const isAdmin = typeof isCurrentUserAdmin === 'function' ? isCurrentUserAdmin() : false;
  const isTargetingOfficial = isInOfficial && (!state.activeRepertoire || (officialRep && state.activeRepertoire === officialRep.uuid) || state.activeRepertoire === '__ALL__');

  if (isTargetingOfficial && !isAdmin) {
    showToast('⚠️ I brani del Repertorio Ufficiale possono essere eliminati solo dall\'Amministratore.');
    return;
  }
  const song = (state.songs || []).find(s => s.uuid === uuid) || state.selectedSong;
  if (!song) return;

  const confirmMsg = isTargetingOfficial
    ? `⚠️ CONFERMA ELIMINAZIONE DA REPERTORIO UFFICIALE (ADMIN)\n\nSei sicuro di voler eliminare il brano "${song.title}" dal Repertorio Ufficiale Band?\n\nIl brano verrà rimosso per tutti i membri della band e archiviato nel cestino protetto.\n\nConfermi l'eliminazione?`
    : `Vuoi spostare "${song.title}" nel cestino protetto? Potrai ripristinarlo in qualsiasi momento.`;

  if (!confirm(confirmMsg)) {
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
  if (!requireEditingMode()) return;
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

async function forkSongToPersonalAndEdit(uuid) {
  if (!requireEditingMode()) return;
  const song = (state.songs || []).find(s => s.uuid === uuid) || state.selectedSong;
  if (!song) return;

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
      showToast(`✓ Copia personale creata in "${data.target_repertoire_name}"! Ora puoi modificarla.`);
      if (data.target_repertoire_uuid) {
        state.activeRepertoire = data.target_repertoire_uuid;
      }
      await loadRepertoires();
      renderRepertoireChips();
      await loadSongs();
      if (data.cloned_song && data.cloned_song.uuid) {
        selectSong(data.cloned_song.uuid);
        state.isEditingSong = true;
        renderSongViewer();
      }
    } else {
      const err = await res.json().catch(() => ({}));
      showToast(err.detail || 'Errore durante la creazione della copia personale');
    }
  } catch (err) {
    console.error('Error forking song for edit:', err);
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
          <button class="btn btn-secondary" style="min-height:30px; padding:2px 8px; font-size:11px; color:#38bdf8; border-color:#38bdf8;" onclick="downloadRepertoirePdf('${r.uuid}', '${escapeHtml(r.name)}')" title="Scarica Elenco PDF Brani">📑 PDF</button>
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
  if (text === null || text === undefined) return '';
  return String(text).replace(/[&<>"']/g, function(m) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
  });
}

// ----------------------------------------------------------------------------
// REGISTRO MODIFICHE / CHANGELOG (ACCESSIBILE A TUTTI)
// ----------------------------------------------------------------------------
async function openChangelogModal() {
  const modal = document.getElementById('changelog-modal');
  const body = document.getElementById('changelog-modal-body');
  const tagEl = document.getElementById('changelog-latest-tag');
  if (modal) modal.style.display = 'flex';
  if (body) body.innerHTML = '<div style="text-align: center; color: #94a3b8; padding: 24px;">⏳ Caricamento registro novità da database...</div>';

  try {
    const res = await fetch(`${API_BASE}/api/changelog`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const entries = data.entries || [];
    if (tagEl) tagEl.textContent = `Versione attiva: ${data.latest_version || '2026.11.12'}`;

    if (!entries.length) {
      if (body) body.innerHTML = '<div style="text-align: center; color: #94a3b8; padding: 24px;">Nessuna voce presente nel changelog.</div>';
      return;
    }

    let html = '';
    entries.forEach((entry, idx) => {
      const isLatest = idx === 0;
      html += `
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid ${isLatest ? '#38bdf8' : '#334155'}; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 15px; font-weight: 900; color: #38bdf8;">v${escapeHtml(entry.version)}</span>
              <span style="font-size: 12px; color: #94a3b8;">📅 ${escapeHtml(entry.date || '')}</span>
            </div>
            ${isLatest ? '<span style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: 800;">ULTIMA VERSIONE</span>' : ''}
          </div>
          <div style="font-size: 14.5px; font-weight: 800; color: #f8fafc; margin-bottom: 12px;">${escapeHtml(entry.title || '')}</div>
      `;

      if (entry.new_features && entry.new_features.length) {
        html += `
          <div style="margin-bottom: 10px;">
            <div style="font-size: 11px; font-weight: 800; color: #22c55e; text-transform: uppercase; margin-bottom: 4px; display: flex; align-items: center; gap: 4px;">
              <span>🚀</span> Nuove Funzionalità
            </div>
            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #cbd5e1; line-height: 1.5;">
              ${entry.new_features.map(f => `<li style="margin-bottom: 4px;">${escapeHtml(f)}</li>`).join('')}
            </ul>
          </div>
        `;
      }

      if (entry.improvements && entry.improvements.length) {
        html += `
          <div style="margin-bottom: 10px;">
            <div style="font-size: 11px; font-weight: 800; color: #38bdf8; text-transform: uppercase; margin-bottom: 4px; display: flex; align-items: center; gap: 4px;">
              <span>⚡</span> Miglioramenti
            </div>
            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #cbd5e1; line-height: 1.5;">
              ${entry.improvements.map(f => `<li style="margin-bottom: 4px;">${escapeHtml(f)}</li>`).join('')}
            </ul>
          </div>
        `;
      }

      if (entry.security && entry.security.length) {
        html += `
          <div style="margin-bottom: 10px;">
            <div style="font-size: 11px; font-weight: 800; color: #c084fc; text-transform: uppercase; margin-bottom: 4px; display: flex; align-items: center; gap: 4px;">
              <span>🛡️</span> Sicurezza &amp; Accessi
            </div>
            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #cbd5e1; line-height: 1.5;">
              ${entry.security.map(f => `<li style="margin-bottom: 4px;">${escapeHtml(f)}</li>`).join('')}
            </ul>
          </div>
        `;
      }

      if (entry.bug_fixes && entry.bug_fixes.length) {
        html += `
          <div>
            <div style="font-size: 11px; font-weight: 800; color: #f59e0b; text-transform: uppercase; margin-bottom: 4px; display: flex; align-items: center; gap: 4px;">
              <span>🐛</span> Correzioni di Bug
            </div>
            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #cbd5e1; line-height: 1.5;">
              ${entry.bug_fixes.map(f => `<li style="margin-bottom: 4px;">${escapeHtml(f)}</li>`).join('')}
            </ul>
          </div>
        `;
      }

      html += `</div>`;
    });

    if (body) body.innerHTML = html;
  } catch (err) {
    if (body) body.innerHTML = `<div style="text-align: center; color: #ef4444; padding: 24px;">Errore caricamento changelog (${escapeHtml(err.message)})</div>`;
  }
}

function closeChangelogModal() {
  const modal = document.getElementById('changelog-modal');
  if (modal) modal.style.display = 'none';
}

// ----------------------------------------------------------------------------
// AMMINISTRAZIONE DATABASE: BACKUP & RESTORE (SOLO ADMIN)
// ----------------------------------------------------------------------------
async function downloadDatabaseBackup() {
  const statusEl = document.getElementById('admin-restore-status');
  if (statusEl) statusEl.innerHTML = '<span style="color:#38bdf8;">⏳ Generazione backup completo del database in corso...</span>';

  try {
    const email = state.currentUser?.email || '';
    const name = state.currentUser?.name || 'Admin';
    const res = await fetch(`${API_BASE}/api/admin/backup?user_email=${encodeURIComponent(email)}&user_name=${encodeURIComponent(name)}`);

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const blob = await res.blob();
    const nowStr = new Date().toISOString().slice(0, 10);
    const filename = `asma_backup_${nowStr}.json`;

    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(blobUrl), 10000);

    if (statusEl) statusEl.innerHTML = '<span style="color:#22c55e; font-weight:700;">✓ Backup scaricato con successo! Conservalo in un luogo sicuro.</span>';
    showToast('✓ Backup database scaricato!');
  } catch (err) {
    if (statusEl) statusEl.innerHTML = `<span style="color:#ef4444; font-weight:700;">⚠ Errore creazione backup: ${escapeHtml(err.message)}</span>`;
    showToast(`Errore backup: ${err.message}`);
  }
}

function triggerDatabaseRestore() {
  const fileInput = document.getElementById('admin-restore-file');
  if (fileInput) {
    fileInput.value = '';
    fileInput.click();
  }
}

async function handleDatabaseRestoreFile(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  const statusEl = document.getElementById('admin-restore-status');
  const reader = new FileReader();

  reader.onload = async (e) => {
    let backupData = null;
    try {
      backupData = JSON.parse(e.target.result);
    } catch (parseErr) {
      if (statusEl) statusEl.innerHTML = '<span style="color:#ef4444; font-weight:700;">⚠ File non valido: non è un file JSON corretto.</span>';
      showToast('File backup non valido');
      return;
    }

    const confirmed = confirm(
      "⚠️ ATTENZIONE: Il ripristino sovrascriverà tutti i dati correnti (brani, scalette, repertori, utenti e changelog) con quelli del file di backup.\n\nVuoi procedere con il ripristino del database?"
    );
    if (!confirmed) {
      if (statusEl) statusEl.innerHTML = '<span style="color:#94a3b8;">Ripristino annullato dall\'utente.</span>';
      return;
    }

    if (statusEl) statusEl.innerHTML = '<span style="color:#38bdf8; font-weight:700;">⏳ Ripristino database e sincronizzazione Turso in corso...</span>';

    try {
      const email = state.currentUser?.email || '';
      const name = state.currentUser?.name || 'Admin';

      const res = await fetch(`${API_BASE}/api/admin/restore`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_email: email,
          user_name: name,
          backup_data: backupData
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const result = await res.json();
      const c = result.counts || {};
      const msg = `✓ Ripristinati con successo: ${c.songs || 0} brani, ${c.setlists || 0} scalette, ${c.repertoires || 0} repertori, ${c.users || 0} utenti, ${c.changelog || 0} versioni changelog.`;

      if (statusEl) statusEl.innerHTML = `<span style="color:#22c55e; font-weight:700;">${escapeHtml(msg)}</span>`;
      showToast('✓ Database ripristinato con successo!');

      // Ricarica lo stato dell'app
      await fetchRepertoires();
      await fetchSongs();
      await fetchSetlists();
      await fetchRegisteredUsers();
    } catch (err) {
      if (statusEl) statusEl.innerHTML = `<span style="color:#ef4444; font-weight:700;">⚠ Errore durante il ripristino: ${escapeHtml(err.message)}</span>`;
      showToast(`Errore restore: ${err.message}`);
    }
  };

  reader.readAsText(file);
}

// -----------------------------------------------------------------------------
// 12. OFFICIAL USER MANUAL DOWNLOAD (AUTO-UPDATING PDF)
// -----------------------------------------------------------------------------
function downloadOfficialManualPdf() {
  showToast('📖 Download Manuale Ufficiale PDF in corso...');
  const link = document.createElement('a');
  link.href = `${API_BASE}/api/manual/pdf`;
  link.download = `manuale_ufficiale_the_new_asma.pdf`;
  link.target = '_blank';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// -----------------------------------------------------------------------------
// 13. LIVE PERFORMANCE AI SUGGESTIONS (GEMINI FREE / OFFLINE HEURISTICS)
// -----------------------------------------------------------------------------
let currentAiSongUuid = null;
let currentAiMusician = 'band';

async function openAiSuggestionsModal(songUuid) {
  currentAiSongUuid = songUuid || state.selectedSong?.uuid;
  if (!currentAiSongUuid) {
    showToast('Nessun brano selezionato');
    return;
  }

  const modal = document.getElementById('ai-suggestions-modal');
  if (!modal) return;

  modal.style.display = 'flex';
  updateAiMusicianChipsUI(currentAiMusician);
  await loadAiSuggestionsForMusician(currentAiMusician);
}

function closeAiSuggestionsModal() {
  const modal = document.getElementById('ai-suggestions-modal');
  if (modal) modal.style.display = 'none';
}

function updateAiMusicianChipsUI(activeMusician) {
  const chips = document.querySelectorAll('.ai-musician-chip');
  chips.forEach(ch => {
    const m = ch.getAttribute('data-musician');
    if (m === activeMusician) {
      ch.classList.add('active');
      ch.style.background = '#0284c7';
      ch.style.borderColor = '#38bdf8';
      ch.style.color = '#fff';
      ch.style.fontWeight = '800';
    } else {
      ch.classList.remove('active');
      ch.style.background = '';
      ch.style.borderColor = '';
      ch.style.color = '';
      ch.style.fontWeight = '';
    }
  });
}

async function selectAiMusician(musicianKey) {
  currentAiMusician = musicianKey || 'band';
  updateAiMusicianChipsUI(currentAiMusician);
  await loadAiSuggestionsForMusician(currentAiMusician);
}

async function refreshCurrentAiSuggestions() {
  if (!currentAiSongUuid) return;
  await loadAiSuggestionsForMusician(currentAiMusician, true);
}

async function loadAiSuggestionsForMusician(musicianKey, forceRefresh = false) {
  const bodyEl = document.getElementById('ai-sugg-body');
  const titleEl = document.getElementById('ai-sugg-title');
  const subEl = document.getElementById('ai-sugg-subtitle');
  const sourceTagEl = document.getElementById('ai-sugg-source-tag');

  if (bodyEl) {
    bodyEl.innerHTML = `
      <div style="text-align: center; color: #94a3b8; padding: 36px 16px;">
        <div style="font-size: 30px; margin-bottom: 10px;">⏳</div>
        <div style="font-size: 14px; font-weight: 700; color: #38bdf8;">Elaborazione consigli palco in corso...</div>
        <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Modalità leggera &bull; Consigli dedicati per il musicista</div>
      </div>
    `;
  }

  try {
    const res = await fetch(`${API_BASE}/api/songs/${currentAiSongUuid}/ai-suggestions?musician=${encodeURIComponent(musicianKey)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const s = data.suggestions || {};
    const songTitle = data.title || 'Brano';
    const songKey = toLatinKey(data.key || 'DO');
    const songBpm = data.bpm || 120;

    if (titleEl) {
      titleEl.innerHTML = `💡 Consigli Live: <span style="color:#ffd600;">${escapeHtml(songTitle)}</span>`;
    }
    if (subEl) {
      subEl.innerHTML = `Tonalità: <b>${escapeHtml(songKey)}</b> &bull; Tempo: <b>${songBpm} BPM</b> &bull; Destinatario: <b style="color:#38bdf8;">${escapeHtml(s.musician_name || 'Band')}</b>`;
    }
    if (sourceTagEl) {
      sourceTagEl.innerHTML = `⚡ ${escapeHtml(s.source || 'AI Gemini Free')} &bull; Latenza Zero`;
    }

    renderAiSuggestionsContent(s);
  } catch (err) {
    if (bodyEl) {
      bodyEl.innerHTML = `
        <div style="text-align: center; color: #ef4444; padding: 24px;">
          <div style="font-size: 26px; margin-bottom: 6px;">⚠️</div>
          <div style="font-weight: 700;">Impossibile recuperare i suggerimenti live</div>
          <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">${escapeHtml(err.message)}</div>
          <button class="btn btn-secondary" style="margin-top: 14px;" onclick="loadAiSuggestionsForMusician('${musicianKey}')">Riprova</button>
        </div>
      `;
    }
  }
}

function renderAiSuggestionsContent(s) {
  const bodyEl = document.getElementById('ai-sugg-body');
  if (!bodyEl) return;

  const icon = s.musician_icon || '👥';
  const name = s.musician_name || 'Tutta la Band';
  const role = s.musician_role || 'Dinamiche d\'insieme';
  const summary = s.summary || 'Preparazione per l\'esecuzione live del brano.';
  const tips = Array.isArray(s.tips) ? s.tips : [];
  const gear = s.gear_advice || '';
  const watchout = s.watchout || '';

  let tipsHtml = '';
  tips.forEach(t => {
    const secName = escapeHtml(t.section || 'Sezione');
    const tipText = escapeHtml(t.tip || '');
    let badgeColor = '#0284c7';
    if (secName.toLowerCase().includes('intro') || secName.toLowerCase().includes('attacco')) badgeColor = '#0284c7';
    else if (secName.toLowerCase().includes('ritornello') || secName.toLowerCase().includes('apertura')) badgeColor = '#16a34a';
    else if (secName.toLowerCase().includes('stacc') || secName.toLowerCase().includes('assol') || secName.toLowerCase().includes('special')) badgeColor = '#dc2626';
    else if (secName.toLowerCase().includes('final') || secName.toLowerCase().includes('outro')) badgeColor = '#9333ea';

    tipsHtml += `
      <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(51, 65, 85, 0.8); border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
          <span style="background: ${badgeColor}; color: #fff; font-size: 10.5px; font-weight: 800; padding: 1px 8px; border-radius: 4px; text-transform: uppercase;">
            ${secName}
          </span>
        </div>
        <div style="font-size: 13px; color: #e2e8f0; line-height: 1.45;">${tipText}</div>
      </div>
    `;
  });

  const gearHtml = gear ? `
    <div style="background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.35); border-radius: 8px; padding: 12px 14px; margin-top: 10px;">
      <div style="font-size: 12px; font-weight: 800; color: #22d3ee; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
        <span>🎛️</span> SETUP STRUMENTO, PRESET &amp; TIMBRI:
      </div>
      <div style="font-size: 13px; color: #e2e8f0; line-height: 1.4;">${escapeHtml(gear)}</div>
    </div>
  ` : '';

  const watchoutHtml = watchout ? `
    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 8px; padding: 12px 14px; margin-top: 10px;">
      <div style="font-size: 12px; font-weight: 800; color: #f87171; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
        <span>⚠️</span> ATTENZIONE CRITICA DAL VIVO:
      </div>
      <div style="font-size: 13px; color: #e2e8f0; line-height: 1.4;">${escapeHtml(watchout)}</div>
    </div>
  ` : '';

  bodyEl.innerHTML = `
    <!-- Summary Header Card -->
    <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95)); border: 1px solid #0284c7; border-radius: 10px; padding: 14px; margin-bottom: 12px;">
      <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
        <span style="font-size: 28px;">${icon}</span>
        <div>
          <div style="font-size: 15px; font-weight: 800; color: #fff;">${escapeHtml(name)}</div>
          <div style="font-size: 12px; color: #38bdf8;">${escapeHtml(role)}</div>
        </div>
      </div>
      <div style="font-size: 13.5px; color: #cbd5e1; font-style: italic; line-height: 1.4; border-left: 3px solid #38bdf8; padding-left: 10px;">
        "${escapeHtml(summary)}"
      </div>
    </div>

    <!-- Tips List -->
    <div style="margin-bottom: 8px;">
      <div style="font-size: 12px; font-weight: 800; color: #94a3b8; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">
        📋 Indicazioni Esecutive per il Palco:
      </div>
      ${tipsHtml}
    </div>

    ${gearHtml}
    ${watchoutHtml}
  `;
}

// ============================================================================
// CIRCOLO DELLE QUINTE INTERATTIVO (ARMONIA, MEDLEY & SCALETTE)
// ============================================================================
const CIRCLE_OF_FIFTHS_DATA = [
  { pos: 0, keyIt: 'DO', keyInt: 'C', relIt: 'LAm', relInt: 'Am', acc: '0 alterazioni', sub: 'FA', dom: 'SOL', notes: 'DO - RE - MI - FA - SOL - LA - SI', chords: ['DO', 'FA', 'SOL', 'LAm', 'REm', 'MIm'], color: '#38bdf8' },
  { pos: 1, keyIt: 'SOL', keyInt: 'G', relIt: 'MIm', relInt: 'Em', acc: '1 ♯ (FA♯)', sub: 'DO', dom: 'RE', notes: 'SOL - LA - SI - DO - RE - MI - FA♯', chords: ['SOL', 'DO', 'RE', 'MIm', 'LAm', 'SIm'], color: '#22c55e' },
  { pos: 2, keyIt: 'RE', keyInt: 'D', relIt: 'SIm', relInt: 'Bm', acc: '2 ♯ (FA♯, DO♯)', sub: 'SOL', dom: 'LA', notes: 'RE - MI - FA♯ - SOL - LA - SI - DO♯', chords: ['RE', 'SOL', 'LA', 'SIm', 'MIm', 'FA♯m'], color: '#10b981' },
  { pos: 3, keyIt: 'LA', keyInt: 'A', relIt: 'FA♯m', relInt: 'F#m', acc: '3 ♯ (FA♯, DO♯, SOL♯)', sub: 'RE', dom: 'MI', notes: 'LA - SI - DO♯ - RE - MI - FA♯ - SOL♯', chords: ['LA', 'RE', 'MI', 'FA♯m', 'SIm', 'DO♯m'], color: '#eab308' },
  { pos: 4, keyIt: 'MI', keyInt: 'E', relIt: 'DO♯m', relInt: 'C#m', acc: '4 ♯ (FA♯, DO♯, SOL♯, RE♯)', sub: 'LA', dom: 'SI', notes: 'MI - FA♯ - SOL♯ - LA - SI - DO♯ - RE♯', chords: ['MI', 'LA', 'SI', 'DO♯m', 'FA♯m', 'SOL♯m'], color: '#f97316' },
  { pos: 5, keyIt: 'SI', keyInt: 'B', relIt: 'SOL♯m', relInt: 'G#m', acc: '5 ♯ (FA♯, DO♯, SOL♯, RE♯, LA♯)', sub: 'MI', dom: 'FA♯', notes: 'SI - DO♯ - RE♯ - MI - FA♯ - SOL♯ - LA♯', chords: ['SI', 'MI', 'FA♯', 'SOL♯m', 'DO♯m', 'RE♯m'], color: '#ef4444' },
  { pos: 6, keyIt: 'FA♯ / SOL♭', keyInt: 'F# / Gb', relIt: 'RE♯m / MI♭m', relInt: 'D#m / Ebm', acc: '6 ♯ / 6 ♭', sub: 'SI', dom: 'DO♯ / RE♭', notes: 'FA♯ - SOL♯ - LA♯ - SI - DO♯ - RE♯ - MI♯', chords: ['FA♯', 'SI', 'DO♯', 'RE♯m', 'SOL♯m', 'LA♯m'], color: '#d946ef' },
  { pos: 7, keyIt: 'RE♭ / DO♯', keyInt: 'Db / C#', relIt: 'SI♭m', relInt: 'Bbm', acc: '5 ♭ (SI♭, MI♭, LA♭, RE♭, SOL♭)', sub: 'SOL♭', dom: 'LA♭', notes: 'RE♭ - MI♭ - FA - SOL♭ - LA♭ - SI♭ - DO', chords: ['RE♭', 'SOL♭', 'LA♭', 'SI♭m', 'MI♭m', 'FAm'], color: '#ec4899' },
  { pos: 8, keyIt: 'LA♭', keyInt: 'Ab', relIt: 'FAm', relInt: 'Fm', acc: '4 ♭ (SI♭, MI♭, LA♭, RE♭)', sub: 'RE♭', dom: 'MI♭', notes: 'LA♭ - SI♭ - DO - RE♭ - MI♭ - FA - SOL', chords: ['LA♭', 'RE♭', 'MI♭', 'FAm', 'SI♭m', 'DOm'], color: '#a855f7' },
  { pos: 9, keyIt: 'MI♭', keyInt: 'Eb', relIt: 'DOm', relInt: 'Cm', acc: '3 ♭ (SI♭, MI♭, LA♭)', sub: 'LA♭', dom: 'SI♭', notes: 'MI♭ - FA - SOL - LA♭ - SI♭ - DO - RE', chords: ['MI♭', 'LA♭', 'SI♭', 'DOm', 'FAm', 'SOLm'], color: '#6366f1' },
  { pos: 10, keyIt: 'SI♭', keyInt: 'Bb', relIt: 'SOLm', relInt: 'Gm', acc: '2 ♭ (SI♭, MI♭)', sub: 'MI♭', dom: 'FA', notes: 'SI♭ - DO - RE - MI♭ - FA - SOL - LA', chords: ['SI♭', 'MI♭', 'FA', 'SOLm', 'DOm', 'REm'], color: '#0ea5e9' },
  { pos: 11, keyIt: 'FA', keyInt: 'F', relIt: 'REm', relInt: 'Dm', acc: '1 ♭ (SI♭)', sub: 'SI♭', dom: 'DO', notes: 'FA - SOL - LA - SI♭ - DO - RE - MI', chords: ['FA', 'SI♭', 'DO', 'REm', 'SOLm', 'LAm'], color: '#06b6d4' }
];

let circleSelectedPos = 0;

function normalizeKeyToFifthsPos(key) {
  if (!key) return 0;
  const k = String(key).trim().toUpperCase();
  if (k.startsWith('DO#') || k.startsWith('C#') || k.startsWith('REB') || k.startsWith('DB')) return 7;
  if (k.startsWith('DO') || k.startsWith('C')) return 0;
  if (k.startsWith('RE#') || k.startsWith('D#') || k.startsWith('MIB') || k.startsWith('EB')) return 9;
  if (k.startsWith('RE') || k.startsWith('D')) return 2;
  if (k.startsWith('MI#') || k.startsWith('E#') || k.startsWith('FA') || k.startsWith('F')) {
    if (k.startsWith('FA#') || k.startsWith('F#')) return 6;
    return 11;
  }
  if (k.startsWith('MI') || k.startsWith('E')) return 4;
  if (k.startsWith('SOL#') || k.startsWith('G#') || k.startsWith('LAB') || k.startsWith('AB')) return 8;
  if (k.startsWith('SOL') || k.startsWith('G')) return 1;
  if (k.startsWith('LA#') || k.startsWith('A#') || k.startsWith('SIB') || k.startsWith('BB')) return 10;
  if (k.startsWith('LA') || k.startsWith('A')) return 3;
  if (k.startsWith('SI') || k.startsWith('B')) return 5;
  return 0;
}

function calculateFifthsTransition(keyA, bpmA, keyB, bpmB) {
  const posA = normalizeKeyToFifthsPos(keyA);
  const posB = normalizeKeyToFifthsPos(keyB);
  const rawDist = Math.abs(posA - posB);
  const distance = Math.min(rawDist, 12 - rawDist);
  
  const bA = parseInt(bpmA) || 120;
  const bB = parseInt(bpmB) || 120;
  const maxBpm = Math.max(bA, bB, 1);
  const bpmDelta = bB - bA;
  const bpmDiffPct = Math.round((Math.abs(bpmDelta) / maxBpm) * 100);

  let label = '';
  let color = '#22c55e';

  if (distance === 0) {
    label = 'Stessa Tonalità (Passaggio Immediato Perfetto)';
    color = '#22c55e';
  } else if (distance === 1) {
    label = 'Tonalità Vicina (Transizione Fluida / Relativa / Dominante)';
    color = '#38bdf8';
  } else if (distance === 2) {
    label = 'Modulazione di 1 Tono (Slancio / Tipico ritornello)';
    color = '#facc15';
  } else {
    label = `Salto di ${distance} quinte (Consigliata modulazione o pausa ritmica)`;
    color = '#f87171';
  }

  return { distance, bpmDelta, bpmDiffPct, label, color };
}

function openCircleOfFifthsModal(initialKey = '') {
  logAuditEvent('CIRCLE_FIFTHS', 'TOOL', 'circle_of_fifths', { initial_key: initialKey });
  const modal = document.getElementById('circle-of-fifths-modal');
  if (!modal) return;
  modal.style.display = 'flex';

  if (initialKey && initialKey !== 'VARIE') {
    circleSelectedPos = normalizeKeyToFifthsPos(initialKey);
  } else {
    circleSelectedPos = 0;
  }
  renderCircleOfFifthsGrid();
  selectCircleKey(circleSelectedPos);
}

function closeCircleOfFifthsModal() {
  const modal = document.getElementById('circle-of-fifths-modal');
  if (modal) modal.style.display = 'none';
}

function renderCircleOfFifthsGrid() {
  const grid = document.getElementById('circle-keys-grid');
  if (!grid) return;

  grid.innerHTML = CIRCLE_OF_FIFTHS_DATA.map(d => {
    const isSelected = d.pos === circleSelectedPos;
    return `
      <div onclick="selectCircleKey(${d.pos})" style="cursor: pointer; background: ${isSelected ? 'rgba(234, 179, 8, 0.22)' : '#0f172a'}; border: 2px solid ${isSelected ? '#eab308' : '#334155'}; border-radius: 8px; padding: 10px; transition: all 0.15s ease; box-shadow: ${isSelected ? '0 0 14px rgba(234, 179, 8, 0.35)' : 'none'};">
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
          <span style="font-size: 17px; font-weight: 900; color: ${isSelected ? '#facc15' : '#fff'};">${escapeHtml(d.keyIt)}</span>
          <span style="font-size: 11px; color: #94a3b8; font-weight: 700;">(${escapeHtml(d.keyInt)})</span>
        </div>
        <div style="font-size: 12px; color: #38bdf8; margin-top: 2px;">Relativa: <b>${escapeHtml(d.relIt)}</b> <span style="font-size:10px; color:#94a3b8;">(${escapeHtml(d.relInt)})</span></div>
        <div style="font-size: 11px; color: #eab308; margin-top: 4px; font-weight: 600;">${escapeHtml(d.acc)}</div>
      </div>
    `;
  }).join('');
}

function selectCircleKey(pos) {
  circleSelectedPos = pos;
  renderCircleOfFifthsGrid();

  const data = CIRCLE_OF_FIFTHS_DATA.find(d => d.pos === pos);
  const detailEl = document.getElementById('circle-key-detail-content');
  if (!data || !detailEl) return;

  const prevPos = (pos - 1 + 12) % 12;
  const nextPos = (pos + 1) % 12;
  const prevKey = CIRCLE_OF_FIFTHS_DATA[prevPos];
  const nextKey = CIRCLE_OF_FIFTHS_DATA[nextPos];

  const canApplyToEditor = !!document.getElementById('edit-song-key');

  detailEl.innerHTML = `
    <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between; margin-bottom: 10px;">
      <div>
        <span style="font-size: 20px; font-weight: 900; color: #facc15;">${escapeHtml(data.keyIt)} / ${escapeHtml(data.keyInt)} Maggiore</span>
        <span style="font-size: 14px; color: #94a3b8; margin-left: 8px;">(Relativa Minore: <b style="color: #38bdf8;">${escapeHtml(data.relIt)} / ${escapeHtml(data.relInt)}</b>)</span>
      </div>
      ${canApplyToEditor ? `
        <button type="button" class="btn btn-primary" style="font-size: 11.5px; padding: 4px 12px; font-weight: 800;" onclick="applyCircleKeyToEditor('${data.keyIt}')">
          ✏️ Usa questa Tonalità nell'Editor
        </button>
      ` : ''}
    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 10px;">
      <div style="background: #1e293b; padding: 10px; border-radius: 6px; border: 1px solid #334155;">
        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 800;">Scale & Alterazioni</div>
        <div style="font-size: 13px; color: #ffd600; font-weight: 700; margin-top: 3px;">${escapeHtml(data.acc)}</div>
        <div style="font-size: 11px; color: #cbd5e1; margin-top: 3px;">Note: ${escapeHtml(data.notes)}</div>
      </div>

      <div style="background: #1e293b; padding: 10px; border-radius: 6px; border: 1px solid #334155;">
        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 800;">Accordi della Famiglia Armonica</div>
        <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px;">
          ${data.chords.map(c => `<span style="background: #0f172a; border: 1px solid #0284c7; color: #38bdf8; font-weight: 800; font-size: 12px; padding: 2px 7px; border-radius: 4px;">${escapeHtml(c)}</span>`).join('')}
        </div>
      </div>

      <div style="background: #1e293b; padding: 10px; border-radius: 6px; border: 1px solid #334155;">
        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 800;">Transizioni & Medley Diretti (Distanza 1)</div>
        <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px; line-height: 1.4;">
          &bull; Sottodominante (IV): <b style="color: #38bdf8;">${escapeHtml(prevKey.keyIt)}</b> (antiorario)<br/>
          &bull; Dominante (V): <b style="color: #22c55e;">${escapeHtml(nextKey.keyIt)}</b> (orario)
        </div>
      </div>
    </div>
  `;
}

function applyCircleKeyToEditor(keyName) {
  const keyInput = document.getElementById('edit-song-key');
  if (keyInput) {
    keyInput.value = keyName;
    showToast(`Tonalità impostata a ${keyName} nell'editor ✓`);
    closeCircleOfFifthsModal();
  }
}

// -----------------------------------------------------------------------------
// 15. AUDIT LOG & USAGE ANALYTICS (ADMIN ONLY - RETENTION 15 DAYS)
// -----------------------------------------------------------------------------
let cachedAuditEntries = [];
let cachedAuditStats = null;
let auditAutoRefreshTimer = null;

function logAuditEvent(action, entityType = 'SYSTEM', entityId = '', details = {}) {
  try {
    const userEmail = (state.currentUser && state.currentUser.email) || localStorage.getItem('asma_user_email') || 'danyposta@gmail.com';
    const userName = (state.currentUser && state.currentUser.name) || localStorage.getItem('asma_user_name') || 'Musicista';
    fetch(`${API_BASE}/api/audit-log/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: action,
        entity_type: entityType,
        entity_id: entityId || '',
        user_email: userEmail,
        user_name: userName,
        details: details || {}
      })
    }).catch(() => {});
  } catch (e) {}
}

let currentAuditView = 'events';

function switchAuditView(view) {
  currentAuditView = view;
  const tabEvents = document.getElementById('tab-audit-events');
  const tabStats = document.getElementById('tab-audit-stats');
  const kpiContainer = document.getElementById('audit-kpi-container');
  const eventsSection = document.getElementById('audit-events-section');

  if (view === 'events') {
    if (tabEvents) {
      tabEvents.style.borderBottomColor = '#38bdf8';
      tabEvents.style.color = '#38bdf8';
      tabEvents.style.background = 'rgba(56, 189, 248, 0.1)';
    }
    if (tabStats) {
      tabStats.style.borderBottomColor = 'transparent';
      tabStats.style.color = '#94a3b8';
      tabStats.style.background = 'transparent';
    }
    if (kpiContainer) kpiContainer.classList.add('mobile-hidden-kpi');
    if (eventsSection) eventsSection.style.display = 'flex';
  } else {
    if (tabStats) {
      tabStats.style.borderBottomColor = '#ffd600';
      tabStats.style.color = '#ffd600';
      tabStats.style.background = 'rgba(255, 214, 0, 0.1)';
    }
    if (tabEvents) {
      tabEvents.style.borderBottomColor = 'transparent';
      tabEvents.style.color = '#94a3b8';
      tabEvents.style.background = 'transparent';
    }
    if (kpiContainer) kpiContainer.classList.remove('mobile-hidden-kpi');
    if (window.innerWidth <= 768 && eventsSection) {
      eventsSection.style.display = 'none';
    } else if (eventsSection) {
      eventsSection.style.display = 'flex';
    }
  }
}

async function openAuditLogModal() {
  if (!isCurrentUserAdmin()) {
    showToast('⚠️ Accesso riservato esclusivamente all\'Amministratore.');
    return;
  }
  const modal = document.getElementById('audit-log-modal');
  if (!modal) return;
  modal.style.display = 'flex';
  switchAuditView('events');
  await loadAuditLog(false);

  // Setup 5-minute autorefresh for logged-in Admin
  if (auditAutoRefreshTimer) {
    clearInterval(auditAutoRefreshTimer);
  }
  auditAutoRefreshTimer = setInterval(() => {
    const m = document.getElementById('audit-log-modal');
    if (m && m.style.display !== 'none' && isCurrentUserAdmin()) {
      loadAuditLog(true);
    } else {
      if (auditAutoRefreshTimer) {
        clearInterval(auditAutoRefreshTimer);
        auditAutoRefreshTimer = null;
      }
    }
  }, 300000); // 5 minutes (300,000 ms)
}

function closeAuditLogModal() {
  const modal = document.getElementById('audit-log-modal');
  if (modal) modal.style.display = 'none';
  if (auditAutoRefreshTimer) {
    clearInterval(auditAutoRefreshTimer);
    auditAutoRefreshTimer = null;
  }
}

async function loadAuditLog(forceReload = false) {
  if (!forceReload && cachedAuditEntries.length > 0 && cachedAuditStats) {
    renderAuditStats(cachedAuditStats);
    filterAuditLogTable();
    return;
  }

  const tableBody = document.getElementById('audit-table-body');
  if (tableBody) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" style="padding: 30px; text-align: center; color: #94a3b8;">
          Caricamento del registro di audit in corso...
        </td>
      </tr>
    `;
  }

  try {
    const adminEmail = (state.currentUser && state.currentUser.email) || 'danyposta@gmail.com';
    const res = await fetch(`${API_BASE}/api/audit-log?user_email=${encodeURIComponent(adminEmail)}&limit=1000&days=15`);
    if (!res.ok) {
      if (res.status === 403) {
        showToast('⚠️ Permesso negato: solo l\'amministratore può consultare l\'audit log.');
      } else {
        showToast('Errore durante il caricamento dell\'audit log.');
      }
      return;
    }
    const data = await res.json();
    cachedAuditEntries = data.entries || [];
    cachedAuditStats = data.stats || {};

    populateAuditMusicianFilter(cachedAuditStats.active_users || []);
    renderAuditStats(cachedAuditStats);
    filterAuditLogTable();
  } catch (err) {
    console.error('Error loading audit log:', err);
    showToast('Errore di connessione al server audit');
  }
}

function populateAuditMusicianFilter(activeUsers) {
  const sel = document.getElementById('audit-filter-user');
  if (!sel) return;
  const currentVal = sel.value;
  let html = '<option value="">Tutti i musicisti</option>';
  activeUsers.forEach(u => {
    html += `<option value="${escapeHtml(u.email)}">${escapeHtml(u.name)} (${u.count} op)</option>`;
  });
  sel.innerHTML = html;
  sel.value = currentVal;
}

function renderAuditStats(stats) {
  const totalEl = document.getElementById('audit-stat-total');
  const dailyEl = document.getElementById('audit-stat-daily');
  const musEl = document.getElementById('audit-stat-musicians');
  const actEl = document.getElementById('audit-stat-actions');
  const lastTimeEl = document.getElementById('audit-stat-last-time');
  const lastDescEl = document.getElementById('audit-stat-last-desc');
  const badgeCountEl = document.getElementById('audit-badge-event-count');

  if (totalEl) totalEl.textContent = stats.total_events || 0;
  if (badgeCountEl) badgeCountEl.textContent = stats.total_events || cachedAuditEntries.length || 0;
  if (dailyEl) dailyEl.textContent = `Media: ${stats.avg_events_per_day || 0} op/giorno (${stats.period_days || 15} gg)`;

  if (musEl) {
    const users = stats.active_users || [];
    if (users.length === 0) {
      musEl.innerHTML = '<span style="font-size: 11.5px; color: #94a3b8;">Nessun dato registrato</span>';
    } else {
      musEl.innerHTML = users.slice(0, 6).map(u => `
        <span onclick="setAuditUserFilter('${escapeHtml(u.email)}')" style="cursor: pointer; background: #0f172a; border: 1px solid #0284c7; color: #38bdf8; font-size: 11px; font-weight: 800; padding: 2px 7px; border-radius: 6px;" title="Filtra per ${escapeHtml(u.name)}">
          ${escapeHtml(u.name)}: <b>${u.count}</b>
        </span>
      `).join('');
    }
  }

  if (actEl) {
    const acts = stats.action_counts || {};
    const actEntries = Object.entries(acts);
    if (actEntries.length === 0) {
      actEl.innerHTML = '<span style="font-size: 11.5px; color: #94a3b8;">Nessun dato</span>';
    } else {
      actEl.innerHTML = actEntries.slice(0, 5).map(([act, cnt]) => `
        <span style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); color: #f59e0b; font-size: 11px; font-weight: 800; padding: 2px 7px; border-radius: 6px;">
          ${escapeHtml(formatActionLabel(act))}: <b>${cnt}</b>
        </span>
      `).join('');
    }
  }

  if (lastTimeEl && lastDescEl) {
    if (stats.last_event) {
      const le = stats.last_event;
      lastTimeEl.textContent = formatAuditTimestamp(le.timestamp);
      lastDescEl.textContent = `${le.user_name || le.user_email}: ${formatActionLabel(le.action)} (${le.entity_type})`;
    } else {
      lastTimeEl.textContent = 'Nessuna attività';
      lastDescEl.textContent = '--';
    }
  }
}

function setAuditUserFilter(email) {
  const sel = document.getElementById('audit-filter-user');
  if (sel) {
    sel.value = email;
    filterAuditLogTable();
  }
}

function filterAuditLogTable() {
  const userFilter = (document.getElementById('audit-filter-user')?.value || '').toLowerCase().trim();
  const actionFilter = (document.getElementById('audit-filter-action')?.value || '').toUpperCase().trim();
  const searchQuery = (document.getElementById('audit-search-query')?.value || '').toLowerCase().trim();

  let filtered = cachedAuditEntries.filter(e => {
    if (userFilter) {
      const uEmail = (e.user_email || '').toLowerCase();
      const uName = (e.user_name || '').toLowerCase();
      if (!uEmail.includes(userFilter) && !uName.includes(userFilter)) return false;
    }
    if (actionFilter) {
      const act = (e.action || '').toUpperCase();
      if (actionFilter === 'SETLIST') {
        if (!act.includes('SETLIST') && e.entity_type !== 'SETLIST') return false;
      } else if (actionFilter === 'DELETE') {
        if (!act.includes('DELETE') && !act.includes('PURGE')) return false;
      } else if (actionFilter === 'UPDATE') {
        if (!act.includes('UPDATE') && !act.includes('EDIT')) return false;
      } else if (!act.includes(actionFilter)) {
        return false;
      }
    }
    if (searchQuery) {
      const fullStr = `${e.timestamp} ${e.action} ${e.entity_type} ${e.entity_id} ${e.user_email} ${e.user_name} ${JSON.stringify(e.details || {})}`.toLowerCase();
      if (!fullStr.includes(searchQuery)) return false;
    }
    return true;
  });

  renderAuditTable(filtered);
}

function renderAuditTable(entries) {
  const tableBody = document.getElementById('audit-table-body');
  const countEl = document.getElementById('audit-table-count');
  if (countEl) countEl.textContent = `Visualizzate ${entries.length} voci su ${cachedAuditEntries.length} totali`;

  if (!tableBody) return;

  if (entries.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" style="padding: 24px; text-align: center; color: #94a3b8;">
          Nessuna operazione trovata con i filtri correnti.
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = entries.map(e => {
    const formattedTs = formatAuditTimestamp(e.timestamp);
    const actionBadge = renderActionBadge(e.action);
    const detailStr = formatAuditDetails(e.details, e.entity_id);
    const objTitle = (e.details && (e.details.title || e.details.name)) ? escapeHtml(e.details.title || e.details.name) : (e.entity_id || '-');

    return `
      <tr style="border-bottom: 1px solid #1e293b; transition: background 0.15s ease;" onmouseover="this.style.background='rgba(56,189,248,0.05)'" onmouseout="this.style.background='transparent'">
        <td style="padding: 8px 12px; white-space: nowrap; font-family: monospace; color: #cbd5e1; font-size: 11.5px;">${formattedTs}</td>
        <td style="padding: 8px 12px; white-space: nowrap;">
          <div style="font-weight: 800; color: #fff;">${escapeHtml(e.user_name || 'Musicista')}</div>
          <div style="font-size: 10.5px; color: #94a3b8;">${escapeHtml(e.user_email || '')}</div>
        </td>
        <td style="padding: 8px 12px; white-space: nowrap;">${actionBadge}</td>
        <td style="padding: 8px 12px; color: #facc15; font-weight: 700;">${objTitle}</td>
        <td style="padding: 8px 12px; color: #cbd5e1; font-size: 11.5px;">${detailStr}</td>
      </tr>
    `;
  }).join('');
}

function formatAuditTimestamp(isoString) {
  if (!isoString) return '-';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    const hours = String(d.getHours()).padStart(2, '0');
    const mins = String(d.getMinutes()).padStart(2, '0');
    const secs = String(d.getSeconds()).padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${mins}:${secs}`;
  } catch (e) {
    return isoString;
  }
}

function formatActionLabel(act) {
  const map = {
    'LOGIN': 'Accesso',
    'LOGOUT': 'Uscita',
    'CREATE': 'Creazione',
    'UPDATE': 'Modifica',
    'DELETE': 'Cancellazione',
    'RESTORE': 'Ripristino',
    'PURGE': 'Eliminazione Definitiva',
    'PURGE_ALL': 'Svuota Cestino',
    'TRANSPOSE': 'Trasposizione',
    'PROMOTE': 'Promozione Ufficiale',
    'FORK': 'Copia Personale',
    'STAGE_VIEW': 'Vista Palco Live',
    'DOWNLOAD_PDF': 'Download PDF',
    'SHARE_A4': 'Stampa/Condividi A4',
    'CIRCLE_FIFTHS': 'Circolo Quinte',
    'SWITCH_PROFILE': 'Cambio Musicista',
    'PREFERENCES': 'Salvataggio Preferenze'
  };
  return map[act] || act;
}

function renderActionBadge(act) {
  act = (act || '').toUpperCase();
  let bg = '#1e293b';
  let border = '#475569';
  let color = '#cbd5e1';

  if (act.includes('LOGIN')) {
    bg = 'rgba(34, 197, 94, 0.15)'; border = '#22c55e'; color = '#4ade80';
  } else if (act.includes('LOGOUT')) {
    bg = 'rgba(148, 163, 184, 0.15)'; border = '#64748b'; color = '#94a3b8';
  } else if (act.includes('CREATE') || act.includes('PROMOTE')) {
    bg = 'rgba(56, 189, 248, 0.15)'; border = '#38bdf8'; color = '#38bdf8';
  } else if (act.includes('UPDATE') || act.includes('TRANSPOSE')) {
    bg = 'rgba(245, 158, 11, 0.15)'; border = '#f59e0b'; color = '#fbbf24';
  } else if (act.includes('DELETE') || act.includes('PURGE')) {
    bg = 'rgba(239, 68, 68, 0.15)'; border = '#ef4444'; color = '#f87171';
  } else if (act.includes('STAGE') || act.includes('PDF') || act.includes('SHARE')) {
    bg = 'rgba(168, 85, 247, 0.15)'; border = '#a855f7'; color = '#c084fc';
  } else if (act.includes('RESTORE') || act.includes('FORK')) {
    bg = 'rgba(20, 184, 166, 0.15)'; border = '#14b8a6'; color = '#2dd4bf';
  }

  return `<span style="display:inline-block; background:${bg}; border:1px solid ${border}; color:${color}; font-weight:800; font-size:10.5px; padding:2px 7px; border-radius:4px; letter-spacing:0.3px;">${escapeHtml(formatActionLabel(act))}</span>`;
}

function formatAuditDetails(details, fallbackId) {
  if (!details || typeof details !== 'object' || Object.keys(details).length === 0) {
    return fallbackId ? `<span style="font-family:monospace; color:#64748b;">${escapeHtml(fallbackId)}</span>` : '-';
  }
  const parts = [];
  if (details.action) parts.push(`<b>${escapeHtml(details.action)}</b>`);
  if (details.title && details.title !== details.name) parts.push(`"${escapeHtml(details.title)}"`);
  if (details.mode) parts.push(`Modalità: ${escapeHtml(details.mode)}`);
  if (details.device) parts.push(`Dispositivo: ${escapeHtml(details.device)}`);
  if (details.provider) parts.push(`Provider: ${escapeHtml(details.provider)}`);
  if (details.purged_count !== undefined) parts.push(`Eliminati: ${details.purged_count} elementi`);

  // Extra keys
  for (const [k, v] of Object.entries(details)) {
    if (['action', 'title', 'name', 'mode', 'device', 'provider', 'purged_count'].includes(k)) continue;
    if (v !== undefined && v !== null && v !== '') {
      parts.push(`${escapeHtml(k)}: <code>${escapeHtml(typeof v === 'object' ? JSON.stringify(v) : String(v))}</code>`);
    }
  }

  return parts.length > 0 ? parts.join(' &bull; ') : fallbackId;
}

function downloadAuditLog(format = 'csv') {
  if (!isCurrentUserAdmin()) {
    showToast('⚠️ Solo l\'Amministratore può scaricare l\'Audit Log.');
    return;
  }
  const adminEmail = (state.currentUser && state.currentUser.email) || 'danyposta@gmail.com';
  const url = `${API_BASE}/api/audit-log/download?user_email=${encodeURIComponent(adminEmail)}&format=${encodeURIComponent(format)}&days=15`;
  const link = document.createElement('a');
  link.href = url;
  link.download = `audit_log_asma_${new Date().toISOString().slice(0, 10)}.${format}`;
  link.target = '_blank';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast(`📥 Download Audit Log (${format.toUpperCase()}) avviato`);
}

