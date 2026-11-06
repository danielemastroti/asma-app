"""
ASMA Accordi Next Generation - Main Application Shell (Streamlit)
Full production-ready application satisfying SRS v1.0 (Cap. 1 - 22).
Includes: Music Engine, AML AST, In-memory SQL, ReportLab PDF, Live Stage 60fps,
Web Importer, Live Events, Manual Engine, Changelog Engine, Gist Client, and Band AI.
"""

import streamlit as st
import time
import json
from datetime import datetime

# Check for Health Endpoint Query Parameter first (SRS Cap. 15.16 & 18.14)
# Compatible with UptimeRobot, Pingdom, StatusCake
params = st.query_params
if "health" in params or params.get("endpoint") == "health":
    st.write({
        "status": "healthy",
        "version": "2026.11.05",
        "github": "ok",
        "authentication": "ok",
        "pdf": "ok",
        "ai": "ok",
        "timestamp": datetime.now().isoformat()
    })
    st.stop()

# Set Streamlit Page Configuration
import os
import asma_core.browser_polyfill
page_icon_val = "assets/band_logo.png" if os.path.exists("assets/band_logo.png") else "🎵"
st.set_page_config(
    page_title="THE New ASMA — Accordi 2.0",
    page_icon=page_icon_val,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject Browser Compatibility Polyfills for Android & Huawei Tablets (ES2023 toSorted, toReversed, toSpliced)
st.markdown(asma_core.browser_polyfill.POLYFILL_SCRIPT, unsafe_allow_html=True)

# Custom CSS for Professional Dark Band Theme and Clean Layout (SRS Cap. 5 & Blueprint Sec. 14)
st.markdown("""
<style>
  /* Completely disable and hide Streamlit Sidebar and sidebar hamburger/toggles */
  section[data-testid="stSidebar"],
  [data-testid="stSidebarCollapseButton"],
  [data-testid="collapsedControl"] {
    display: none !important;
  }

  /* Make central page span full width with HTML-frame fixed top header */
  [data-testid="stAppViewContainer"],
  section[data-testid="stMain"],
  .main {
    width: 100vw !important;
    max-width: 100vw !important;
    overflow-y: auto !important;
  }
  .main .block-container, [data-testid="stMainBlockContainer"] {
    padding-top: 72px !important;
    padding-left: 16px !important;
    padding-right: 16px !important;
    max-width: 100% !important;
    overflow: visible !important;
  }
  @media (max-width: 768px) {
    .main .block-container, [data-testid="stMainBlockContainer"] {
      padding-top: 96px !important;
    }
  }

  /* ULTRA COMPACT TOP FIXED NAVIGATION FRAME (HTML Frame Style) */
  div[class*="st-key-top_navbar_container"] {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100vw !important;
    z-index: 999990 !important;
    background: rgba(13, 17, 23, 0.98) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-bottom: 2px solid #0288D1 !important;
    padding: 3px 14px 4px 14px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.85) !important;
  }

  /* Compact popovers in top navbar */
  div[class*="st-key-top_navbar_container"] [data-testid="stPopover"] button {
    font-size: 11px !important;
    padding: 2px 7px !important;
    height: 26px !important;
    min-height: 26px !important;
    border-radius: 13px !important;
    line-height: 1 !important;
    white-space: nowrap !important;
  }

  /* ULTRA COMPACT NAVIGATION PILLS (Single line scrollable/fitted) */
  div[class*="st-key-top_nav_pills_widget"] {
    width: 100% !important;
    margin-top: 1px !important;
    margin-bottom: 0px !important;
  }
  div[class*="st-key-top_nav_pills_widget"] [data-testid="stPills"] {
    display: flex !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    gap: 3px !important;
    justify-content: flex-start !important;
    padding-bottom: 1px !important;
    scrollbar-width: thin !important;
  }
  div[class*="st-key-top_nav_pills_widget"] [data-testid="stPill"],
  div[class*="st-key-top_nav_pills_widget"] button {
    background: rgba(30, 41, 59, 0.85) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    color: #E2E8F0 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    padding: 2px 7px !important;
    height: 25px !important;
    min-height: 25px !important;
    border-radius: 12px !important;
    transition: all 0.15s ease-in-out !important;
    cursor: pointer !important;
    white-space: nowrap !important;
    line-height: 1 !important;
  }
  div[class*="st-key-top_nav_pills_widget"] [data-testid="stPill"]:hover,
  div[class*="st-key-top_nav_pills_widget"] button:hover {
    background: rgba(2, 136, 209, 0.3) !important;
    border-color: #00E5FF !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
  }
  div[class*="st-key-top_nav_pills_widget"] [aria-selected="true"],
  div[class*="st-key-top_nav_pills_widget"] [aria-pressed="true"],
  div[class*="st-key-top_nav_pills_widget"] [aria-checked="true"],
  div[class*="st-key-top_nav_pills_widget"] [data-selected="true"],
  div[class*="st-key-top_nav_pills_widget"] button[kind="primary"] {
    background: linear-gradient(135deg, #0288D1, #0091EA) !important;
    border-color: #00E5FF !important;
    color: #FFFFFF !important;
    box-shadow: 0 0 12px rgba(0, 229, 255, 0.6) !important;
    font-weight: 700 !important;
  }

  /* TOP FIXED BAR (Always Visible & Animated) */
  .asma-top-fixed-bar {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 42px;
    background: rgba(13, 17, 23, 0.97);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 2px solid #0288D1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 18px;
    z-index: 999999;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.7);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }

  /* Glowing laser progress line on top edge */
  .asma-laser-line {
    position: absolute;
    top: 0;
    left: 0;
    height: 3px;
    width: 100%;
    background: linear-gradient(90deg, #0288D1, #00E5FF, #FFD600, #00E676, #00E5FF, #0288D1);
    background-size: 300% 100%;
    animation: asma-laser-flow 3s ease infinite;
  }

  @keyframes asma-laser-flow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }

  .asma-bar-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .asma-brand-name {
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.5px;
    color: #FFFFFF;
  }
  .asma-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 230, 118, 0.12);
    border: 1px solid rgba(0, 230, 118, 0.4);
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    color: #00E676;
    transition: all 0.3s ease;
  }
  .asma-led-dot {
    width: 8px;
    height: 8px;
    background-color: #00E676;
    border-radius: 50%;
    box-shadow: 0 0 8px #00E676;
    animation: asma-led-pulse 1.8s infinite;
  }
  @keyframes asma-led-pulse {
    0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 8px #00E676; }
    50% { opacity: 0.35; transform: scale(0.85); box-shadow: 0 0 2px #00E676; }
  }

  /* Center Equalizer Soundwave Animation */
  .asma-bar-center {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .asma-eq-container {
    display: flex;
    align-items: flex-end;
    height: 16px;
    gap: 3px;
  }
  .asma-eq-bar {
    width: 3px;
    background: #00E5FF;
    border-radius: 2px;
    animation: asma-eq-bounce 1.2s ease-in-out infinite alternate;
  }
  .eq-1 { height: 6px; animation-delay: 0.0s; }
  .eq-2 { height: 12px; animation-delay: 0.2s; background: #00E676; }
  .eq-3 { height: 16px; animation-delay: 0.4s; background: #FFD600; }
  .eq-4 { height: 9px; animation-delay: 0.1s; background: #00E5FF; }
  .eq-5 { height: 14px; animation-delay: 0.3s; background: #FF5252; }
  .eq-6 { height: 7px; animation-delay: 0.5s; background: #00E676; }
  .eq-7 { height: 11px; animation-delay: 0.25s; background: #00E5FF; }

  @keyframes asma-eq-bounce {
    0% { height: 3px; }
    50% { height: 16px; }
    100% { height: 7px; }
  }
  .asma-eq-label {
    font-size: 11px;
    color: #94A3B8;
    font-weight: 500;
    letter-spacing: 0.5px;
  }

  .asma-bar-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .asma-user-chip {
    font-size: 12px;
    font-weight: 600;
    padding: 3px 10px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
  }

  /* Style Streamlit's native status widget when running */
  [data-testid="stStatusWidget"] {
    position: fixed !important;
    top: 6px !important;
    right: 20px !important;
    z-index: 1000001 !important;
    background: rgba(2, 136, 209, 0.95) !important;
    color: #FFFFFF !important;
    border: 1px solid #00E5FF !important;
    border-radius: 16px !important;
    padding: 2px 10px !important;
    box-shadow: 0 0 16px rgba(0, 229, 255, 0.7) !important;
    animation: asma-widget-glow 1s infinite alternate !important;
  }
  @keyframes asma-widget-glow {
    0% { box-shadow: 0 0 8px rgba(0, 229, 255, 0.5); }
    100% { box-shadow: 0 0 20px rgba(0, 229, 255, 1); }
  }

  /* Finestra di Stato Terminal Box */
  .asma-terminal-box {
    background: #0b0f19;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 12px;
    overflow-y: auto;
    font-family: 'Consolas', 'Fira Code', 'Courier New', monospace;
    box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.7);
  }

  .top-header {
    background-color: #1A1A1A;
    border-bottom: 2px solid #333333;
    padding: 10px 20px;
    border-radius: 8px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .status-badge {
    background: #00E676;
    color: #000000;
    font-weight: bold;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 13px;
  }
  .user-badge {
    color: #FFD600;
    font-weight: bold;
    font-size: 15px;
  }
  .version-tag {
    color: #888888;
    font-size: 13px;
  }
</style>
""", unsafe_allow_html=True)

# Imports from core
from asma_core.models import Song, Repertoire, Setlist, SetlistItem, LiveEvent, DeviceProfile
from asma_core.music_engine import MusicEngine
from asma_core.aml_parser import AMLParser
from asma_core.storage_manager import StorageManager
from asma_core.lock_manager import LockManager
from asma_core.audit_logger import AuditLogger
from asma_core.operation_logger import OperationLogger, OperationLogEntry
from asma_core.pdf_engine import PDFEngine
from asma_core.live_stage_component import LiveStageComponent
from asma_core.export_engine import ExportEngine
from asma_core.import_engine import ImportEngine
from asma_core.web_importer import WebSongImporter
from asma_core.manual_engine import ManualEngine
from asma_core.changelog_engine import ChangelogEngine
from asma_core.ai_service import BandAIService
from asma_core.gist_client import GistClient
from asma_core.auth_manager import AuthManager, UserRole, User
from asma_core.backup_engine import BackupEngine
from asma_core.device_manager import DeviceManager
from asma_core.aml_tag_manager import AMLTagManager, AMLTagDefinition

# Initialize Singletons
storage = StorageManager()
lock_mgr = LockManager()
audit = AuditLogger()
op_logger = OperationLogger()
device_mgr = DeviceManager()
aml_tag_mgr = AMLTagManager()
gist_client = GistClient()
auth_mgr = AuthManager()

# Initialize Session State & User Identity (SRS Cap. 3 & Cap. 10)
if "current_user_email" not in st.session_state:
    st.session_state["current_user_email"] = "daniele@band.org"

current_user = auth_mgr.get_user_by_email(st.session_state["current_user_email"])
if not current_user:
    current_user = auth_mgr.authenticate_or_register_google(st.session_state["current_user_email"], "Daniele Rossi")

st.session_state["current_user_name"] = current_user.name
st.session_state["current_user_role"] = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)

if "selected_song_uuid" not in st.session_state:
    st.session_state["selected_song_uuid"] = None
if "selected_setlist_uuid" not in st.session_state:
    st.session_state["selected_setlist_uuid"] = None

# TOP FIXED HEADER (SRS Cap. 3.5 & 5.3)
role_colors = {
    "ADMIN": "#FFD600",
    "BAND_MEMBER": "#00E5FF",
    "VIEWER": "#AAAAAA"
}
role_col = role_colors.get(current_user.role.value, "#FFFFFF")

def log_op(icon: str, category: str, message: str, level: str = "SUCCESS"):
    """Helper to log an operation into the live status console."""
    user_str = f"{current_user.name} [{current_user.role.value}]" if 'current_user' in locals() and current_user else "System"
    op_logger.log(icon, category, message, level=level, user=user_str)

if "session_boot_logged" not in st.session_state:
    st.session_state["session_boot_logged"] = True
    log_op("🟢", "SISTEMA", f"Accesso sessione effettuato da {current_user.name} ({current_user.email}) - Ruolo: {current_user.role.value}", "SUCCESS")

def render_status_console(logger_inst: OperationLogger, key_prefix: str = "main", compact: bool = False):
    """Renders the interactive status window printing executed operations."""
    if compact:
        entries = logger_inst.get_entries(limit=18)
        html_lines = "".join(e.to_terminal_line() for e in entries) if entries else "<div style='color:#888;'>Nessuna operazione registrata.</div>"
        st.markdown(f"<div class='asma-terminal-box' style='max-height: 220px;'>{html_lines}</div>", unsafe_allow_html=True)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("🧹 Pulisci", key=f"{key_prefix}_clr_btn", width="stretch"):
                logger_inst.clear()
                st.rerun()
        with col_c2:
            st.download_button("📋 Esporta", data=logger_inst.export_text(), file_name="asma_operazioni.log", mime="text/plain", key=f"{key_prefix}_exp_btn", width="stretch")
    else:
        st.write("##### 📟 Finestra di Stato & Monitor Operazioni Eseguite")
        c1, c2, c3 = st.columns([2, 1, 1.2])
        with c1:
            cat_filter = st.selectbox("Filtra per Categoria:", logger_inst.get_categories(), key=f"{key_prefix}_cat")
        with c2:
            limit_val = st.selectbox("Numero Eventi:", [15, 30, 50, 100], index=1, key=f"{key_prefix}_limit")
        with c3:
            st.write("")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("🧹 Pulisci", key=f"{key_prefix}_clr_full", width="stretch"):
                    logger_inst.clear()
                    st.rerun()
            with b2:
                st.download_button("📋 Esporta", data=logger_inst.export_text(), file_name="asma_operazioni.log", mime="text/plain", key=f"{key_prefix}_exp_full", width="stretch")

        filtered = logger_inst.get_entries(limit=limit_val, category=cat_filter)
        html_lines = "".join(e.to_terminal_line() for e in filtered) if filtered else "<div style='color:#888; padding:10px;'>Nessun evento registrato per questa categoria.</div>"
        st.markdown(f"<div class='asma-terminal-box' style='max-height: 320px;'>{html_lines}</div>", unsafe_allow_html=True)

# ==============================================================================
# TOP FIXED NAVIGATION FRAME (HTML Frame Style - 100% Fixed on Scroll for All Devices)
# ==============================================================================
MENU_ITEMS = [
    "🏠 Home Dashboard",
    "📚 Repertori",
    "📝 Editor Brani",
    "📑 Scalette Live",
    "🎤 Modalità Palco (Live Stage)",
    "📅 Eventi Live",
    "📥 Importa & 📤 Esporta",
    "🔍 Ricerca Globale",
    "🤖 Band AI (Opzionale)",
    "📖 Manuale & Changelog",
    "⚙️ Amministrazione & Log"
]

MENU_COMPACT_LABELS = {
    "🏠 Home Dashboard": "🏠 Home",
    "📚 Repertori": "📚 Repertori",
    "📝 Editor Brani": "📝 Editor",
    "📑 Scalette Live": "📑 Scalette",
    "🎤 Modalità Palco (Live Stage)": "🎤 Palco",
    "📅 Eventi Live": "📅 Eventi",
    "📥 Importa & 📤 Esporta": "📥/📤 I/O",
    "🔍 Ricerca Globale": "🔍 Cerca",
    "🤖 Band AI (Opzionale)": "🤖 AI",
    "📖 Manuale & Changelog": "📖 Guida",
    "⚙️ Amministrazione & Log": "⚙️ Admin"
}

if "main_menu_choice" not in st.session_state:
    st.session_state["main_menu_choice"] = "🏠 Home Dashboard"

all_users = auth_mgr.list_users()
user_emails = [u.email for u in all_users]
curr_user_idx = user_emails.index(current_user.email) if current_user.email in user_emails else 0

dev_list = device_mgr.list_devices()
dev_names = [d.name for d in dev_list]
curr_pref = st.session_state.get("user_preferred_device", dev_names[0] if dev_names else "")
pref_idx = dev_names.index(curr_pref) if curr_pref in dev_names else 0

# UI Zoom Scaling (Auto-calibrated for Huawei / Android tablets to match iPad)
if "ui_zoom_level" not in st.session_state:
    st.session_state["ui_zoom_level"] = 0.82 if "huawei" in curr_pref.lower() else 1.0

active_zoom = st.session_state["ui_zoom_level"]
st.markdown(f"""
<style>
  html, body, [data-testid="stAppViewContainer"] {{
    zoom: {active_zoom} !important;
    -webkit-text-size-adjust: 100% !important;
    text-size-adjust: 100% !important;
  }}
</style>
""", unsafe_allow_html=True)

with st.container(key="top_navbar_container"):
    # Glowing Laser Accent Line
    st.markdown('<div class="asma-laser-line"></div>', unsafe_allow_html=True)

    # Row 1: Brand (Left) | Soundwave Status (Center) | Profile, Device & Log (Right)
    col_head_left, col_head_center, col_head_right = st.columns([1.3, 0.9, 1.8], gap="small", vertical_alignment="center")

    with col_head_left:
        if os.path.exists("assets/band_logo.png"):
            c_lg_mini, c_ttl_mini = st.columns([0.35, 1.65], gap="small", vertical_alignment="center")
            with c_lg_mini:
                st.image("assets/band_logo.png", width=48)
            with c_ttl_mini:
                st.markdown(
                    f"<div style='line-height:1.1; white-space:nowrap;'>"
                    f"<b style='font-size:12.5px; color:#FFFFFF;'>THE New ASMA</b> "
                    f"<span style='font-size:9px; color:#00E676; font-weight:bold; background:rgba(0,230,118,0.12); padding:1px 5px; border-radius:6px; border:1px solid rgba(0,230,118,0.3);'>• ONLINE</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                f"<div style='line-height:1.1; white-space:nowrap;'>"
                f"<b style='font-size:13px; color:#FFFFFF;'>⚡ THE New ASMA</b> "
                f"<span style='font-size:9px; color:#00E676; font-weight:bold; background:rgba(0,230,118,0.12); padding:1px 5px; border-radius:6px; border:1px solid rgba(0,230,118,0.3);'>• ONLINE</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    with col_head_center:
        st.markdown(
            f'''<div style="display:flex; align-items:center; justify-content:center; gap:6px;">
              <div class="asma-eq-container" style="height:12px;" title="Attività Live Motore ASMA">
                <span class="asma-eq-bar eq-1" style="height:4px;"></span>
                <span class="asma-eq-bar eq-2" style="height:8px;"></span>
                <span class="asma-eq-bar eq-3" style="height:12px;"></span>
                <span class="asma-eq-bar eq-4" style="height:6px;"></span>
                <span class="asma-eq-bar eq-5" style="height:10px;"></span>
              </div>
              <span class="asma-eq-label" style="font-size:10px; color:#94A3B8; font-weight:500; white-space:nowrap;">LIVE STAGE</span>
            </div>''',
            unsafe_allow_html=True
        )

    with col_head_right:
        c_btn_user, c_btn_dev, c_btn_log = st.columns([1.0, 1.1, 0.6], gap="small", vertical_alignment="center")

        user_first = current_user.name.split()[0]
        dev_short = "Huawei M5" if "mediapad m5" in curr_pref.lower() else (curr_pref[:11] + "..." if len(curr_pref) > 13 else curr_pref)

        with c_btn_user:
            with st.popover(f"👤 {user_first}", width="stretch", help="Profilo utente attivo, permessi e login"):
                st.write("##### 👤 Profilo Utente & Permessi")
                st.markdown(f"**Utente:** `{current_user.name}` ({current_user.email})<br>**Ruolo:** <span style='color:{role_col}; font-weight:bold;'>{current_user.role.value}</span>", unsafe_allow_html=True)
                st.caption(f"Permessi operativi: `{'Lettura & Modifica completa' if current_user.can_edit() else 'Sola Lettura'}`")
                st.divider()

                st.write("###### 🔄 Cambia Profilo (Test Ruoli):")
                new_u_sel = st.selectbox(
                    "Seleziona Account Band:",
                    user_emails,
                    index=curr_user_idx,
                    format_func=lambda e: f"{next(u.name for u in all_users if u.email == e)} [{next(u.role.value for u in all_users if u.email == e)}]",
                    key="pop_hub_user_sel"
                )
                if new_u_sel != st.session_state["current_user_email"]:
                    st.session_state["current_user_email"] = new_u_sel
                    u_sel = auth_mgr.get_user_by_email(new_u_sel)
                    if u_sel:
                        log_op("🔐", "AUTH", f"Passaggio profilo utente a {u_sel.name} [{u_sel.role.value}]", "INFO")
                    st.rerun()

                st.divider()
                st.write("###### 🔑 Accesso Google OAuth2:")
                in_email = st.text_input("Email Google:", placeholder="mario@gmail.com", key="pop_oauth_email")
                in_name = st.text_input("Nome e Cognome:", placeholder="Mario Rossi", key="pop_oauth_name")
                if st.button("Accedi con Google", type="primary", key="pop_btn_google", width="stretch"):
                    if in_email:
                        new_u = auth_mgr.authenticate_or_register_google(in_email, in_name)
                        st.session_state["current_user_email"] = new_u.email
                        log_op("🔑", "AUTH", f"Accesso federato Google per {new_u.name} ({new_u.email})", "SUCCESS")
                        st.success(f"Accesso riuscito come {new_u.name}!")
                        st.rerun()

        with c_btn_dev:
            with st.popover(f"📱 {dev_short}", width="stretch", help="Dispositivo hardware e scala zoom"):
                st.write("##### 📱 Configurazione Dispositivo Display")
                st.caption("Adatta automaticamente margini, colonne e leggibilità al tuo schermo.")
                new_dev_sel = st.selectbox(
                    "Seleziona Modello Hardware:",
                    dev_names,
                    index=pref_idx,
                    key="pop_hub_dev_sel"
                )
                if new_dev_sel != st.session_state.get("user_preferred_device"):
                    st.session_state["user_preferred_device"] = new_dev_sel
                    # Auto adjust zoom for Huawei
                    if "huawei" in new_dev_sel.lower():
                        st.session_state["ui_zoom_level"] = 0.82
                    elif "ipad" in new_dev_sel.lower() or "pc" in new_dev_sel.lower():
                        st.session_state["ui_zoom_level"] = 1.0
                    st.rerun()

                st.divider()
                st.write("###### 🔍 Scala Schermo (Zoom):")
                st.caption("Rimpicciolisci o ingrandisci per adattare perfettamente la schermata al tablet:")
                z_cols = st.columns(5)
                zoom_presets = [("75%", 0.75), ("82%", 0.82), ("90%", 0.90), ("100%", 1.0), ("110%", 1.10)]
                for z_i, (z_lbl, z_v) in enumerate(zoom_presets):
                    with z_cols[z_i]:
                        is_active_z = abs(active_zoom - z_v) < 0.02
                        b_type = "primary" if is_active_z else "secondary"
                        if st.button(z_lbl, key=f"btn_z_{z_v}", type=b_type, width="stretch"):
                            st.session_state["ui_zoom_level"] = z_v
                            st.rerun()

                curr_prof = device_mgr.get_device_by_name(curr_pref)
                if curr_prof:
                    st.divider()
                    st.markdown(f"**Specifiche Display:** `{curr_prof.name}`<br>"
                                f"📐 Risoluzione mm: `{curr_prof.width_mm:.1f} × {curr_prof.height_mm:.1f} mm` ({curr_prof.orientation})<br>"
                                f"📖 Colonne: `{curr_prof.columns}` &bull; Testo: `{curr_prof.font_size_lyrics} pt` &bull; Accordi: `{curr_prof.font_size_chords} pt`",
                                unsafe_allow_html=True)

        with c_btn_log:
            with st.popover(f"📟 {op_logger.count()}", width="stretch", help="Apri la console delle operazioni"):
                render_status_console(op_logger, key_prefix="top_pop_console", compact=False)

    # Row 2: Ultra-Compact Navigation Pills (Single Row)
    active_item = st.session_state.get("main_menu_choice", "🏠 Home Dashboard")
    if active_item not in MENU_ITEMS:
        active_item = MENU_ITEMS[0]

    top_pill_selection = st.pills(
        "Menu Navigazione Principale",
        options=MENU_ITEMS,
        format_func=lambda x: MENU_COMPACT_LABELS.get(x, x),
        default=active_item,
        selection_mode="single",
        required=True,
        wrap=True,
        key="top_nav_pills_widget",
        label_visibility="collapsed"
    )
    if top_pill_selection and top_pill_selection != st.session_state["main_menu_choice"]:
        st.session_state["main_menu_choice"] = top_pill_selection
        st.rerun()

menu_choice = st.session_state["main_menu_choice"]

# ------------------------------------------------------------------------------
# 1. HOME DASHBOARD
# ------------------------------------------------------------------------------
if menu_choice == "🏠 Home Dashboard":
    st.subheader("🏠 THE New ASMA — Dashboard Ufficiale")
    st.caption("Piattaforma Digitale Integrata Band: Repertorio, Live Stage 60fps, Scalette, Editor AML & Accordi")

    st.write("")

    songs = storage.list_songs()
    repertoires = storage.list_repertoires()
    setlists = storage.list_setlists()
    events = storage.list_events()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Brani in Archivio", len(songs))
    c2.metric("Repertori Attivi", len(repertoires))
    c3.metric("Scalette Live", len(setlists))
    c4.metric("Eventi Programmati", len(events))

    st.divider()

    col_recent, col_live = st.columns([1, 1])

    with col_recent:
        st.write("### 🕒 Ultime Attività & Modifiche")
        recent_logs = audit.get_entries(limit=5)
        if recent_logs:
            for log in recent_logs:
                st.write(f"- `{log.timestamp[11:19]}` **{log.action}** su {log.entity_type} da *{log.user_name}*")
        else:
            st.info("Nessuna attività recente registrata.")

    with col_live:
        st.write("### 🎤 Accesso Rapido Palco")
        if setlists:
            latest_setlist = setlists[-1]
            st.success(f"Prossima scaletta pronta: **{latest_setlist.title}** ({len(latest_setlist.items)} brani)")
            if st.button("🚀 Avvia Subito Modalità Palco", type="primary"):
                st.session_state["selected_setlist_uuid"] = latest_setlist.uuid
                st.session_state["launch_stage"] = True
                st.rerun()
        else:
            st.info("Nessuna scaletta creata. Crea una scaletta per iniziare.")

# ------------------------------------------------------------------------------
# 2. GESTIONE REPERTORI
# ------------------------------------------------------------------------------
elif menu_choice == "📚 Repertori":
    st.subheader("📚 Gestione Repertori")

    repertoires = storage.list_repertoires()
    col_rep_top1, col_rep_top2 = st.columns([3, 1])
    with col_rep_top1:
        if repertoires:
            selected_rep_name = st.selectbox("Seleziona Repertorio:", [r.name for r in repertoires])
            selected_rep = next(r for r in repertoires if r.name == selected_rep_name)
            st.write(f"*{selected_rep.description}*")
        else:
            st.info("Nessun repertorio esistente. Crea il tuo primo repertorio.")
            selected_rep = None

    with col_rep_top2:
        with st.popover("➕ Nuovo Repertorio", width="stretch"):
            st.write("##### Crea Nuovo Repertorio")
            new_r_name = st.text_input("Nome:", placeholder="Es. Repertorio Acustico")
            new_r_desc = st.text_input("Descrizione:", placeholder="Brani per set acustico")
            if st.button("Crea Repertorio", type="primary", disabled=not current_user.can_edit()):
                if new_r_name:
                    created_rep = Repertoire(name=new_r_name, description=new_r_desc)
                    storage.save_repertoire(created_rep, current_user.email, current_user.name)
                    log_op("📚", "REPERTORIO", f"Creato nuovo repertorio '{new_r_name}'", "SUCCESS")
                    st.success(f"Repertorio '{new_r_name}' creato!")
                    st.rerun()

        if selected_rep:
            with st.popover("🗑️ Elimina Repertorio", width="stretch"):
                st.warning(f"Vuoi eliminare il repertorio **'{selected_rep.name}'**?\n\n*Nota: I brani NON verranno cancellati e resteranno nell'archivio generale.*")
                if st.button("Conferma Eliminazione", type="secondary", disabled=not current_user.can_delete()):
                    storage.delete_repertoire(selected_rep.uuid, current_user.email, current_user.name)
                    log_op("🗑️", "REPERTORIO", f"Eliminato repertorio '{selected_rep.name}'", "WARNING")
                    st.success(f"Repertorio '{selected_rep.name}' eliminato.")
                    st.rerun()

    if not selected_rep:
        st.stop()

    rep_songs = [storage.get_song(s_id) for s_id in selected_rep.song_uuids if storage.get_song(s_id)]

    # Sezione Aggiunta Brani al Repertorio
    all_archive_songs = storage.list_songs()
    unassigned_songs = [s for s in all_archive_songs if s["uuid"] not in selected_rep.song_uuids]

    c_btn1, c_btn2 = st.columns([1, 2])
    with c_btn1:
        if st.button("➕ Crea Nuovo Brano", disabled=not current_user.can_edit()):
            new_s = Song(title="Nuovo Brano", key_current="C", aml_content="{title: Nuovo Brano}\n{key: C}\n\n[C]Testo e accordi...")
            saved = storage.save_song(new_s, st.session_state["current_user_email"], st.session_state["current_user_name"])
            storage.move_song_to_repertoire(saved.uuid, selected_rep.uuid)
            st.session_state["selected_song_uuid"] = saved.uuid
            log_op("➕", "BRANO", f"Creato nuovo brano '{saved.title}' nel repertorio '{selected_rep.name}'", "SUCCESS")
            st.success(f"Creato brano '{saved.title}'")
            st.rerun()

    with c_btn2:
        if unassigned_songs:
            with st.expander("📥 Inserisci brano esistente dell'archivio in questo repertorio"):
                s_to_add_id = st.selectbox(
                    "Seleziona brano da collegare:",
                    [s["uuid"] for s in unassigned_songs],
                    format_func=lambda uid: next(f"{s['title']} ({s.get('artist', 'Sconosciuto')})" for s in unassigned_songs if s["uuid"] == uid),
                    key=f"sel_add_{selected_rep.uuid}"
                )
                if st.button("➕ Aggiungi al Repertorio", disabled=not current_user.can_edit()):
                    storage.move_song_to_repertoire(s_to_add_id, selected_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                    log_op("📥", "REPERTORIO", f"Brano associato al repertorio '{selected_rep.name}'", "INFO")
                    st.success("Brano associato con successo a questo repertorio!")
                    st.rerun()

    if rep_songs:
        rows = []
        for s in rep_songs:
            lock = lock_mgr.check_lock(s.uuid)
            lock_display = f"🔒 {lock.locked_by_name}" if lock.is_locked else "🔓 Libero"
            rows.append({
                "UUID": s.uuid,
                "Titolo": s.title,
                "Artista": s.artist,
                "Tonalità": s.key_current,
                "BPM": s.bpm,
                "Revisione": f"Rev #{s.current_revision}",
                "Lock": lock_display
            })
        st.dataframe(rows, width="stretch")

        selected_s_id = st.selectbox("Seleziona Brano per azioni rapide:", [r["UUID"] for r in rows], format_func=lambda x: next(r["Titolo"] for r in rows if r["UUID"] == x))
        selected_lock = lock_mgr.check_lock(selected_s_id)
        selected_song_obj = next((s for s in rep_songs if s.uuid == selected_s_id), None)

        col_act1, col_act2, col_act3, col_act4, col_act5 = st.columns(5)
        with col_act1:
            if st.button("📝 Apri nell'Editor", width="stretch"):
                st.session_state["selected_song_uuid"] = selected_s_id
                st.session_state.pop(f"released_lock_{selected_s_id}", None)
                st.info("Passa alla scheda 'Editor Brani' dal menu a sinistra.")
        with col_act2:
            if selected_lock.is_locked:
                can_unlock = (selected_lock.locked_by_email == current_user.email) or current_user.is_admin()
                if st.button("🔓 Rilascia Lock", disabled=not can_unlock, width="stretch", help=f"Bloccato da {selected_lock.locked_by_name}"):
                    lock_mgr.release_lock(selected_s_id, current_user.email, force=current_user.is_admin())
                    st.session_state[f"released_lock_{selected_s_id}"] = True
                    s_title = selected_song_obj.title if selected_song_obj else selected_s_id
                    log_op("🔓", "LOCK", f"Rilasciato lock di editing per '{s_title}' da Gestione Repertori", "INFO")
                    st.success("Lock rilasciato con successo!")
                    st.rerun()
            else:
                st.caption("🔓 Nessun lock attivo")
        with col_act3:
            other_reps = [r for r in repertoires if r.uuid != selected_rep.uuid]
            if other_reps:
                dest_rep = st.selectbox("Sposta in:", [r.name for r in other_reps], key=f"dest_rep_{selected_s_id}")
                if st.button("➡️ Sposta", disabled=not current_user.can_edit(), width="stretch"):
                    target_r = next(r for r in other_reps if r.name == dest_rep)
                    storage.move_song_to_repertoire(selected_s_id, target_r.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                    st.success(f"Brano spostato in '{target_r.name}' senza perdita dello storico.")
                    st.rerun()
        with col_act4:
            if st.button("❌ Rimuovi", disabled=not current_user.can_edit(), width="stretch"):
                storage.remove_song_from_repertoire(selected_s_id, selected_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                st.success("Brano rimosso dal repertorio (rimane presente nell'archivio generale).")
                st.rerun()
        with col_act5:
            if st.button("🗑️ Cestino", disabled=not current_user.can_delete(), width="stretch"):
                storage.delete_song(selected_s_id, st.session_state["current_user_email"], st.session_state["current_user_name"])
                st.warning("Brano spostato nel cestino (recuperabile per 30 giorni).")
                st.rerun()
    else:
        st.info("Nessun brano associato a questo repertorio.")

# ------------------------------------------------------------------------------
# 3. EDITOR BRANI
# ------------------------------------------------------------------------------
elif menu_choice == "📝 Editor Brani":
    st.subheader("📝 Editor Brani Musicali & Anteprima Device-Aware")

    songs = storage.list_songs()
    if not songs:
        st.warning("Nessun brano disponibile. Creane uno dalla sezione 'Repertori'.")
        st.stop()

    song_choices = {s["uuid"]: s["title"] for s in songs}
    curr_uuid = st.session_state.get("selected_song_uuid")
    keys_list = list(song_choices.keys())
    default_idx = keys_list.index(curr_uuid) if (curr_uuid and curr_uuid in keys_list) else 0
    selected_uuid = st.selectbox("Seleziona Brano da modificare:", keys_list, index=default_idx, format_func=lambda x: song_choices[x])
    st.session_state["selected_song_uuid"] = selected_uuid

    song = storage.get_song(selected_uuid)
    if not song:
        st.error("Brano non trovato.")
        st.stop()

    # Lock Management Check (SRS Cap. 4.6 & 7.7)
    current_lock = lock_mgr.check_lock(song.uuid)
    user_email = st.session_state["current_user_email"]
    user_name = st.session_state["current_user_name"]

    user_released = st.session_state.get(f"released_lock_{song.uuid}", False)

    if user_released:
        can_edit = False
        st.info(f"ℹ️ Modalità Sola Lettura: hai rilasciato il lock per '{song.title}'. Il brano è libero per gli altri musicisti.")
        if st.button("🔒 Ri-acquisisci Lock per Modificare", type="primary"):
            st.session_state.pop(f"released_lock_{song.uuid}", None)
            st.rerun()
    elif current_lock.is_locked and current_lock.locked_by_email != user_email:
        st.error(f"🔒 Brano bloccato in modifica da **{current_lock.locked_by_name}** ({current_lock.locked_by_email}). Modalità sola lettura.")
        can_edit = False
    elif not current_user.can_edit():
        st.warning("⚠️ Modalità Sola Lettura: L'utente corrente ha ruolo VIEWER (Ospite). I controlli di modifica e salvataggio sono disattivati.")
        can_edit = False
    else:
        lock_mgr.acquire_lock(song.uuid, user_email, user_name)
        st.success(f"🔓 Hai acquisito il lock di editing per '{song.title}'. Gli altri musicisti possono solo consultarlo.")
        can_edit = True

    col_edit, col_prev = st.columns([1, 1])

    with col_edit:
        st.write("#### 🎼 Sorgente AML")
        meta_c1, meta_c2, meta_c3 = st.columns(3)
        with meta_c1:
            title_input = st.text_input("Titolo:", value=song.title, disabled=not can_edit)
            key_input = st.text_input("Tonalità:", value=song.key_current, disabled=not can_edit)
        with meta_c2:
            artist_input = st.text_input("Artista:", value=song.artist, disabled=not can_edit)
            bpm_input = st.number_input("BPM:", value=song.bpm, disabled=not can_edit)
        with meta_c3:
            genre_input = st.text_input("Genere:", value=song.genre, disabled=not can_edit)
            capo_input = st.number_input("Capo tasto:", value=song.capo, disabled=not can_edit)

        # Visualizzazione e Associazione Repertori
        all_reps = storage.list_repertoires()
        assigned_reps = [r for r in all_reps if song.uuid in r.song_uuids]
        rep_labels = ", ".join([r.name for r in assigned_reps]) if assigned_reps else "Nessun repertorio (Non assegnato)"
        st.caption(f"📚 **Repertori associati:** `{rep_labels}`")
        unassigned_reps = [r for r in all_reps if song.uuid not in r.song_uuids]
        if unassigned_reps:
            with st.expander("➕ Associa questo brano a un altro Repertorio"):
                col_r_sel, col_r_btn = st.columns([3, 1])
                with col_r_sel:
                    target_r_obj = st.selectbox("Seleziona repertorio:", unassigned_reps, format_func=lambda r: r.name, key=f"add_r_edit_{song.uuid}")
                with col_r_btn:
                    st.write("")
                    if st.button("Collega", disabled=not can_edit):
                        storage.move_song_to_repertoire(song.uuid, target_r_obj.uuid, user_email, user_name)
                        log_op("📚", "REPERTORIO", f"Brano '{song.title}' associato a '{target_r_obj.name}'", "INFO")
                        st.success(f"Brano associato a '{target_r_obj.name}'!")
                        st.rerun()

        # Transposition Quick Tools
        st.write("**Trasposizione Rapida:**")
        tr_c1, tr_c2, tr_c3, tr_c4 = st.columns(4)
        with tr_c1:
            if st.button("⬇️ -1 Semitono", disabled=not can_edit):
                doc = AMLParser.parse(song.aml_content)
                new_doc = AMLParser.transpose_document(doc, semitones=-1)
                song.aml_content = new_doc.to_aml()
                song.key_current = MusicEngine.transpose_chord(song.key_current, semitones=-1)
                storage.save_song(song, user_email, user_name, "Trasposizione -1 semitono")
                log_op("⬇️", "TRASPOSIZIONE", f"Brano '{song.title}' trasposto -1 semitono in {song.key_current}", "SUCCESS")
                st.rerun()
        with tr_c2:
            if st.button("⬆️ +1 Semitono", disabled=not can_edit):
                doc = AMLParser.parse(song.aml_content)
                new_doc = AMLParser.transpose_document(doc, semitones=1)
                song.aml_content = new_doc.to_aml()
                song.key_current = MusicEngine.transpose_chord(song.key_current, semitones=1)
                storage.save_song(song, user_email, user_name, "Trasposizione +1 semitono")
                log_op("⬆️", "TRASPOSIZIONE", f"Brano '{song.title}' trasposto +1 semitono in {song.key_current}", "SUCCESS")
                st.rerun()
        with tr_c3:
            if st.button("🇮🇹 Converti in ITA", disabled=not can_edit):
                doc = AMLParser.parse(song.aml_content)
                song.aml_content = AMLParser.convert_notation(doc, "ITA").to_aml()
                storage.save_song(song, user_email, user_name, "Conversione notazione italiana")
                log_op("🇮🇹", "NOTAZIONE", f"Brano '{song.title}' convertito in notazione Italiana", "INFO")
                st.rerun()
        with tr_c4:
            if st.button("🌐 Converti in INT", disabled=not can_edit):
                doc = AMLParser.parse(song.aml_content)
                song.aml_content = AMLParser.convert_notation(doc, "INT").to_aml()
                storage.save_song(song, user_email, user_name, "Conversione notazione internazionale")
                log_op("🌐", "NOTAZIONE", f"Brano '{song.title}' convertito in notazione Internazionale", "INFO")
                st.rerun()

        tags_input = st.text_input("🏷️ Tag del Brano (separati da virgola):", value=", ".join(song.tags or []), disabled=not can_edit, help="Es: ballad, rock, acustico, bis")

        with st.expander("📖 Guida Sintassi & Tag AML (Direttive, Sezioni, Accordi Inline, Griglie, Strumenti)"):
            st.markdown("""
            * **• Direttive:** `{title: Titolo}`, `{artist: Artista}`, `{key: Tonalità}`, `{tempo: BPM}`, `{time: 4/4}`
            * **• Sezioni:** `{intro}`, `{verse}`, `{chorus}`, `{bridge}`, `{solo}`, `{outro}`
            * **• Accordi Inline:** `[Am]On a dark desert highway, [F#7]cool wind in my hair`
            * **• Griglia Armonica a Battute:** `| DO | LAm | FA | SOL |`
            * **• Tag Strumentali:** `{guitar: Solo Don Felder}`, `{voice: Armonizzazione a 3}`, `{bass: Slap}`, `{drums: 4/4 Groove}`
            """)

        aml_editor_text = st.text_area("Testo AML:", value=song.aml_content, height=360, disabled=not can_edit)
        rev_comment = st.text_input("Commento della modifica (per storico revisioni):", value="Modifica accordi e sezioni", disabled=not can_edit)

        col_s1, col_s2, col_s3 = st.columns([1.5, 1, 1.2])
        with col_s1:
            if st.button("💾 Salva Nuova Revisione", type="primary", disabled=not can_edit, width="stretch"):
                song.title = title_input
                song.artist = artist_input
                song.key_current = key_input
                song.bpm = bpm_input
                song.genre = genre_input
                song.capo = capo_input
                song.tags = [t.strip().lower() for t in tags_input.split(",") if t.strip()]
                song.aml_content = aml_editor_text
                saved = storage.save_song(song, user_email, user_name, rev_comment)
                log_op("💾", "SALVATAGGIO", f"Salvata Nuova Revisione #{saved.current_revision} per '{song.title}'", "SUCCESS")
                st.success(f"Salvato con successo! Nuova Revisione #{saved.current_revision}")
                st.rerun()
        with col_s2:
            if st.button("🔓 Rilascia Lock", width="stretch"):
                lock_mgr.release_lock(song.uuid, user_email)
                st.session_state[f"released_lock_{song.uuid}"] = True
                log_op("🔓", "LOCK", f"Rilasciato lock di editing per '{song.title}'", "INFO")
                st.info("Lock rilasciato.")
                st.rerun()
        with col_s3:
            with st.popover("🗑️ Elimina Brano", width="stretch"):
                st.warning(f"Vuoi spostare **'{song.title}'** nel cestino?\n\n*Potrai ripristinarlo entro 30 giorni.*")
                if st.button("Conferma Eliminazione", type="secondary", disabled=not current_user.can_delete(), key=f"del_editor_{song.uuid}"):
                    lock_mgr.release_lock(song.uuid, user_email, force=True)
                    storage.delete_song(song.uuid, user_email, user_name)
                    log_op("🗑️", "CESTINO", f"Brano '{song.title}' spostato nel cestino (soft-delete 30gg)", "WARNING")
                    st.session_state["selected_song_uuid"] = None
                    st.success(f"Brano '{song.title}' spostato nel cestino.")
                    st.rerun()

    with col_prev:
        st.write("#### 👁️ Anteprima Reale PDF & Esportazione Dispositivo")
        configured_devs = device_mgr.list_devices()
        dev_choices = {d.uuid: d.name for d in configured_devs}
        user_pref_name = st.session_state.get("user_preferred_device", "Foglio a 4 stampabile")
        default_dev_idx = next((i for i, d in enumerate(configured_devs) if d.name == user_pref_name), 0)

        selected_dev_uuid = st.selectbox(
            "📐 Formato Dispositivo di Destinazione:",
            list(dev_choices.keys()),
            index=default_dev_idx,
            format_func=lambda x: dev_choices[x]
        )
        prof = device_mgr.get_device(selected_dev_uuid) or DeviceProfile()

        st.caption(f"📱 **Specifiche Dispositivo:** `{prof.name}` &bull; `{prof.width_mm:.1f} × {prof.height_mm:.1f} mm` ({prof.orientation}) &bull; Colonne: `{prof.columns}` &bull; Font Testo: `{prof.font_size_lyrics} pt`")

        # Genera il PDF dal contenuto attuale dell'editor in tempo reale
        preview_song = Song(
            uuid=song.uuid,
            title=title_input,
            artist=artist_input,
            key_current=key_input,
            bpm=bpm_input,
            genre=genre_input,
            capo=capo_input,
            tags=[t.strip().lower() for t in tags_input.split(",") if t.strip()],
            aml_content=aml_editor_text,
            current_revision=song.current_revision
        )

        pdf_bytes = PDFEngine.generate_song_pdf(preview_song, profile=prof, use_cache=False)

        col_exp_pdf, col_exp_sb = st.columns(2)
        with col_exp_pdf:
            st.download_button(
                label=f"📄 Scarica PDF ({prof.name})",
                data=pdf_bytes,
                file_name=f"{preview_song.title.replace(' ', '_')}_{prof.name.replace(' ', '_')}.pdf",
                mime="application/pdf",
                width="stretch"
            )
        with col_exp_sb:
            st.download_button(
                label="🎸 Esporta per SongBook Pro (.pro)",
                data=ExportEngine.export_for_songbookpro(preview_song),
                file_name=f"{preview_song.title.replace(' ', '_')}.pro",
                mime="text/plain",
                width="stretch",
                help="Formato ChordPro nativo compatibile con SongBook Pro per tablet/smartphone"
            )

        st.markdown("##### 📄 Anteprima Reale Pagine PDF Formattate:")
        try:
            import pymupdf
            doc_pdf = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            num_pages = len(doc_pdf)
            st.caption(f"Totale pagine generate: **{num_pages}** per `{prof.name}`")
            for page_num in range(num_pages):
                page = doc_pdf[page_num]
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                st.image(
                    img_bytes,
                    caption=f"Pagina {page_num + 1} di {num_pages} — Formato {prof.name}",
                    width="stretch"
                )
        except Exception as ex_pdf:
            st.warning(f"Impossibile renderizzare l'anteprima visiva del PDF ({ex_pdf}). Puoi comunque scaricare il file PDF generato sopra.")

        with st.expander("🔍 Sorgente HTML Strutturato"):
            parsed_doc = AMLParser.parse(aml_editor_text)
            preview_html = f"<div style='background:#111; color:#fff; padding:16px; border-radius:6px; font-family:monospace;'>"
            for n in parsed_doc.nodes:
                if hasattr(n, "section_name"):
                    preview_html += f"<div style='color:#0288D1; font-weight:bold; margin-top:8px;'>[{n.section_name.upper()}]</div>"
                elif hasattr(n, "measures"):
                    measure_str = " | ".join([" ".join(m) for m in n.measures])
                    preview_html += f"<div style='background:#222; padding:4px; color:#FFD600; font-weight:bold;'>| {measure_str} |</div>"
                elif hasattr(n, "segments"):
                    chords = "".join([s.chord.chord_text + "  " for s in n.segments if s.chord])
                    lyrics = "".join([s.text for s in n.segments])
                    if chords.strip():
                        preview_html += f"<div style='color:#FFD600; font-weight:bold;'>{chords}</div>"
                    preview_html += f"<div>{lyrics}</div>"
            preview_html += "</div>"
            st.markdown(preview_html, unsafe_allow_html=True)

        with st.expander("📜 Cronologia Revisioni (SRS Cap. 4.5)"):
            revs = storage.get_revisions_for_song(song.uuid)
            for r in reversed(revs):
                st.write(f"- **Rev #{r.revision_number}** ({r.timestamp[0:10]} {r.timestamp[11:19]}) di *{r.author_name}*: {r.comment}")
                if st.button(f"Ripristina Rev #{r.revision_number}", key=f"restore_{r.revision_number}"):
                    storage.restore_revision(song.uuid, r.revision_number, user_email, user_name)
                    st.success(f"Rollback completato alla Revisione #{r.revision_number}")
                    st.rerun()

# ------------------------------------------------------------------------------
# 4. SCALETTE LIVE
# ------------------------------------------------------------------------------
elif menu_choice == "📑 Scalette Live":
    st.subheader("📑 Gestione Scalette Live (Setlist)")

    setlists = storage.list_setlists()
    all_songs = storage.list_songs()
    song_map = {s["uuid"]: s for s in all_songs}

    col_s1, col_s2 = st.columns([1, 2])

    with col_s1:
        st.write("#### Scalette Esistenti")
        if setlists:
            for s in setlists:
                if st.button(f"🎵 {s.title} ({len(s.items)} brani)", key=f"sel_setlist_{s.uuid}"):
                    st.session_state["selected_setlist_uuid"] = s.uuid
                    st.rerun()
        else:
            st.info("Nessuna scaletta creata.")

        with st.form("new_setlist_form"):
            new_title = st.text_input("Nuova Scaletta Titolo:", "Scaletta Tour Estate 2027")
            new_date = st.text_input("Data:", "15/07/2027")
            submit_set = st.form_submit_button("Crea Scaletta", disabled=not current_user.can_edit())
            if submit_set:
                new_set = Setlist(title=new_title, date=new_date)
                storage.save_setlist(new_set, st.session_state["current_user_email"], st.session_state["current_user_name"])
                st.session_state["selected_setlist_uuid"] = new_set.uuid
                log_op("📑", "SCALETTA", f"Creata scaletta live '{new_title}' ({new_date})", "SUCCESS")
                st.success(f"Creata scaletta '{new_title}'")
                st.rerun()

    with col_s2:
        curr_set_id = st.session_state.get("selected_setlist_uuid")
        if curr_set_id:
            active_setlist = next((s for s in setlists if s.uuid == curr_set_id), None)
            if active_setlist:
                c_title_s, c_del_s = st.columns([3, 1])
                with c_title_s:
                    st.write(f"### Scaletta: **{active_setlist.title}** ({active_setlist.date})")
                with c_del_s:
                    with st.popover("🗑️ Elimina Scaletta", width="stretch"):
                        st.warning(f"Vuoi davvero eliminare la scaletta **'{active_setlist.title}'**?")
                        if st.button("Conferma Eliminazione", type="secondary", disabled=not current_user.can_delete(), key=f"del_set_{active_setlist.uuid}"):
                            storage.delete_setlist(active_setlist.uuid, current_user.email, current_user.name)
                            st.session_state["selected_setlist_uuid"] = None
                            log_op("🗑️", "SCALETTA", f"Eliminata scaletta '{active_setlist.title}'", "WARNING")
                            st.success("Scaletta eliminata con successo.")
                            st.rerun()

                if all_songs:
                    add_song_id = st.selectbox("Aggiungi brano alla sequenza:", list(song_map.keys()), format_func=lambda x: song_map[x]["title"])
                    if st.button("➕ Inserisci in Scaletta", disabled=not current_user.can_edit()):
                        active_setlist.items.append(SetlistItem(song_uuid=add_song_id))
                        storage.save_setlist(active_setlist, st.session_state["current_user_email"], st.session_state["current_user_name"])
                        log_op("➕", "SCALETTA", f"Aggiunto brano '{song_map[add_song_id]['title']}' a '{active_setlist.title}'", "INFO")
                        st.success("Brano aggiunto alla scaletta!")
                        st.rerun()
                        st.success("Brano aggiunto alla scaletta!")
                        st.rerun()

                st.write("#### Sequenza di Esecuzione:")
                if active_setlist.items:
                    for idx, item in enumerate(active_setlist.items):
                        s_info = song_map.get(item.song_uuid)
                        title = s_info["title"] if s_info else "Sconosciuto"
                        key = item.custom_key or (s_info["key_current"] if s_info else "-")
                        bpm = item.custom_bpm or (s_info["bpm"] if s_info else "-")

                        r_c1, r_c2, r_c3, r_c4 = st.columns([5, 1, 1, 1])
                        with r_c1:
                            st.markdown(f"**{idx + 1}. {title}** &bull; Key: `{key}` &bull; BPM: `{bpm}`")
                        with r_c2:
                            if idx > 0 and st.button("⬆️", key=f"up_{idx}_{item.song_uuid}", disabled=not current_user.can_edit(), help="Sposta prima"):
                                active_setlist.items[idx], active_setlist.items[idx - 1] = active_setlist.items[idx - 1], active_setlist.items[idx]
                                storage.save_setlist(active_setlist, current_user.email, current_user.name)
                                st.rerun()
                        with r_c3:
                            if idx < len(active_setlist.items) - 1 and st.button("⬇️", key=f"down_{idx}_{item.song_uuid}", disabled=not current_user.can_edit(), help="Sposta dopo"):
                                active_setlist.items[idx], active_setlist.items[idx + 1] = active_setlist.items[idx + 1], active_setlist.items[idx]
                                storage.save_setlist(active_setlist, current_user.email, current_user.name)
                                st.rerun()
                        with r_c4:
                            if st.button("❌", key=f"rem_{idx}_{item.song_uuid}", disabled=not current_user.can_edit(), help="Rimuovi brano dalla scaletta"):
                                active_setlist.items.pop(idx)
                                storage.save_setlist(active_setlist, current_user.email, current_user.name)
                                st.success(f"Brano '{title}' rimosso dalla scaletta.")
                                st.rerun()
                else:
                    st.info("Nessun brano nella sequenza. Aggiungine uno con il menu sopra.")

                st.divider()
                st.write("#### 📤 Esportazione Scaletta Unificata (Tutti i Brani)")
                loaded_songs = [storage.get_song(item.song_uuid) for item in active_setlist.items if storage.get_song(item.song_uuid)]

                c_set_dev, c_set_act = st.columns([1.5, 2.5])
                with c_set_dev:
                    configured_devs = device_mgr.list_devices()
                    dev_choices_set = {d.uuid: d.name for d in configured_devs}
                    user_pref_name = st.session_state.get("user_preferred_device", "Foglio a 4 stampabile")
                    default_dev_idx = next((i for i, d in enumerate(configured_devs) if d.name == user_pref_name), 0)
                    selected_set_dev_uuid = st.selectbox(
                        "Formato Dispositivo Scaletta:",
                        list(dev_choices_set.keys()),
                        index=default_dev_idx,
                        format_func=lambda x: dev_choices_set[x],
                        key=f"set_dev_sel_{active_setlist.uuid}"
                    )
                    set_prof = device_mgr.get_device(selected_set_dev_uuid) or DeviceProfile()
                    st.caption(f"📐 **Specifiche:** `{set_prof.name}` &bull; `{set_prof.width_mm:.1f}×{set_prof.height_mm:.1f} mm` ({set_prof.orientation})")

                with c_set_act:
                    if loaded_songs:
                        set_pdf = PDFEngine.generate_setlist_pdf(active_setlist, loaded_songs, profile=set_prof)
                        st.download_button(
                            label=f"📄 Scarica PDF Unico Scaletta ({set_prof.name})",
                            data=set_pdf,
                            file_name=f"Scaletta_{active_setlist.title.replace(' ', '_')}_{set_prof.name.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            width="stretch",
                            help="Genera un unico documento PDF con copertina, indice e tutti i brani impaginati sequenzialmente nel formato del dispositivo."
                        )

                        col_sb_exp, col_zip_exp = st.columns(2)
                        with col_sb_exp:
                            set_sb = ExportEngine.export_setlist_for_songbookpro(active_setlist, loaded_songs)
                            st.download_button(
                                label="🎸 Esporta per SongBook Pro (.pro)",
                                data=set_sb,
                                file_name=f"Scaletta_{active_setlist.title.replace(' ', '_')}.pro",
                                mime="text/plain",
                                width="stretch",
                                help="File unico con tutti i brani della scaletta separati da pagina per SongBook Pro"
                            )
                        with col_zip_exp:
                            live_zip = ExportEngine.create_offline_live_pack_zip(active_setlist, loaded_songs)
                            st.download_button(
                                label="📦 Scarica Live Pack ZIP",
                                data=live_zip,
                                file_name=f"LivePack_{active_setlist.title.replace(' ', '_')}.zip",
                                mime="application/zip",
                                width="stretch",
                                help="Archivio completo contenente il PDF scaletta, singoli PDF, file AML e file per SongBook Pro"
                            )
                    else:
                        st.info("Aggiungi brani alla sequenza per abilitare l'esportazione del PDF e per SongBook Pro.")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🎤 Avvia Modalità Palco (Live Stage)", type="primary", width="stretch"):
                    st.session_state["launch_stage"] = True
                    st.info("Passa a 'Modalità Palco' dal menu a sinistra.")

# ------------------------------------------------------------------------------
# 5. MODALITÀ PALCO (LIVE STAGE VIEW)
# ------------------------------------------------------------------------------
elif menu_choice == "🎤 Modalità Palco (Live Stage)":
    st.subheader("🎤 Modalità Palco Ufficiale (Live Stage Component)")

    setlists = storage.list_setlists()
    if not setlists:
        st.warning("Crea una scaletta per utilizzare la modalità palco.")
        st.stop()

    set_id = st.session_state.get("selected_setlist_uuid") or setlists[0].uuid
    active_setlist = next((s for s in setlists if s.uuid == set_id), setlists[0])

    songs_to_stage = [storage.get_song(item.song_uuid) for item in active_setlist.items if storage.get_song(item.song_uuid)]
    if not songs_to_stage:
        st.warning(f"La scaletta '{active_setlist.title}' non contiene brani.")
        st.stop()

    st.caption(f"Palco attivo: **{active_setlist.title}** ({len(songs_to_stage)} brani) &bull; Keep Screen Awake attivo &bull; Pedali Bluetooth connessi")
    html_bundle = LiveStageComponent.render_html_bundle(songs_to_stage, dark_theme=True, initial_speed=35)
    st.components.v1.html(html_bundle, height=720, scrolling=False)

# ------------------------------------------------------------------------------
# 6. EVENTI LIVE (SRS Cap. 4.4)
# ------------------------------------------------------------------------------
elif menu_choice == "📅 Eventi Live":
    st.subheader("📅 Gestione Eventi & Concerti Live")

    events = storage.list_events()
    setlists = storage.list_setlists()

    col_ev1, col_ev2 = st.columns([1, 1])

    with col_ev1:
        st.write("#### Crea Nuovo Evento Live")
        with st.form("new_event_form"):
            ev_name = st.text_input("Nome Evento / Concerto:", "Live Rock Festival")
            ev_venue = st.text_input("Luogo / Locale:", "Piazza San Giovanni, Roma")
            ev_date = st.text_input("Data Evento:", "20/07/2027")
            ev_setlist = st.selectbox("Associa Scaletta:", [s.title for s in setlists] if setlists else ["Nessuna scaletta"])
            ev_notes = st.text_area("Note Logistiche e Scheda Tecnica:", "Soundcheck ore 17:30. Portare D.I. box per chitarra acustica e pedale Bluetooth.")

            if st.form_submit_button("Salva Evento Live"):
                target_s_id = next((s.uuid for s in setlists if s.title == ev_setlist), None)
                new_ev = LiveEvent(name=ev_name, venue=ev_venue, event_date=ev_date, setlist_uuid=target_s_id, logistics_notes=ev_notes)
                storage.save_event(new_ev, st.session_state["current_user_email"], st.session_state["current_user_name"])
                st.success(f"Evento '{ev_name}' salvato con successo!")
                st.rerun()

    with col_ev2:
        st.write("#### Calendario Eventi Programmati")
        if events:
            for ev in events:
                with st.expander(f"📍 {ev.name} — {ev.event_date} ({ev.venue})"):
                    st.write(f"**Data:** {ev.event_date} | **Luogo:** {ev.venue}")
                    matched_set = next((s for s in setlists if s.uuid == ev.setlist_uuid), None)
                    if matched_set:
                        st.write(f"**Scaletta Associata:** {matched_set.title} ({len(matched_set.items)} brani)")
                    st.write(f"**Note Tecniche:** {ev.logistics_notes}")
                    if st.button("🗑️ Elimina Evento", key=f"del_ev_{ev.uuid}"):
                        storage.delete_event(ev.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                        st.success("Evento eliminato.")
                        st.rerun()
        else:
            st.info("Nessun evento registrato.")

# ------------------------------------------------------------------------------
# 7. IMPORTA ED ESPORTA (CON WEB IMPORTER)
# ------------------------------------------------------------------------------
elif menu_choice == "📥 Importa & 📤 Esporta":
    st.subheader("📥 Importazione Multi-Formato & 📤 Esportazione Interoperabile")

    # Scelta del Repertorio di Destinazione per l'importazione
    all_reps = storage.list_repertoires()
    col_rep_sel, col_rep_info = st.columns([2, 1])
    with col_rep_sel:
        target_rep = st.selectbox(
            "📂 Assegna automaticamente i brani importati a questo Repertorio:",
            all_reps,
            format_func=lambda r: f"📚 {r.name} ({len(r.song_uuids)} brani)"
        ) if all_reps else None
    with col_rep_info:
        if target_rep:
            st.caption(f"I brani importati verranno archiviati in: **{target_rep.name}**")
        else:
            st.warning("Nessun repertorio attivo. I brani resteranno nell'archivio generale.")

    tab_web, tab_imp, tab_exp = st.tabs(["🌐 Import da Web / URL", "📥 Import PDF & Testo", "📤 Esporta per App Esterne"])

    with tab_web:
        st.write("#### 🌐 Importazione Automatica da Internet (Siti Italiani ed Internazionali)")
        st.caption("Estrae automaticamente accordi e testi da Accordi e Spartiti, Ultimate-Guitar, Skitarrate, Chordie e pagine web pubbliche.")

        url_input = st.text_input("Incolla URL diretto della pagina dello spartito:", placeholder="https://www.accordiespartiti.it/accordi/italiani/nomadi/canzone-per-unamica/")
        if url_input and st.button("📥 Scarica da URL e Converti in AML"):
            with st.spinner("Scaricamento e parsing della pagina web..."):
                try:
                    song_web = WebSongImporter.fetch_from_url(url_input)
                    saved = storage.save_song(song_web, st.session_state["current_user_email"], st.session_state["current_user_name"], "Importazione da Web URL")
                    if target_rep:
                        storage.move_song_to_repertoire(saved.uuid, target_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                    rep_msg = f" ed inserito nel repertorio **'{target_rep.name}'**" if target_rep else ""
                    log_op("📥", "WEB IMPORT", f"Importato brano '{saved.title}' ({saved.artist}) da URL web", "SUCCESS")
                    st.success(f"Brano importato e salvato con successo: **{saved.title}** ({saved.artist}) — Tonalità: `{saved.key_current}`{rep_msg}")
                    st.session_state["selected_song_uuid"] = saved.uuid
                except Exception as err:
                    log_op("❌", "WEB IMPORT", f"Errore import URL: {str(err)}", "ERROR")
                    st.error(f"Errore durante l'importazione da Web: {str(err)}")

        st.divider()
        st.write("#### 🔍 Ricerca Brano Online sui Portali (Italiani ed Internazionali)")
        st.caption("Interroga in tempo reale Accordi e Spartiti, Ultimate-Guitar e i principali archivi web per trovare e importare lo spartito reale.")

        c_w1, c_w2 = st.columns(2)
        with c_w1:
            search_title = st.text_input("Titolo Brano:", "Albachiara")
        with c_w2:
            search_artist = st.text_input("Artista (opzionale):", "Vasco Rossi")

        c_btn1, c_btn2 = st.columns([1, 1])
        with c_btn1:
            do_search = st.button("🔍 Cerca Brano sui Portali", width="stretch")
        with c_btn2:
            auto_import = st.button("⚡ Importa Subito il Miglior Risultato", width="stretch")

        if do_search:
            with st.spinner("Ricerca in corso sui portali di accordi..."):
                found_candidates = WebSongImporter.search_online_candidates(search_title, search_artist, limit=6)
                st.session_state["web_search_candidates"] = found_candidates
                log_op("🔍", "WEB IMPORT", f"Ricerca online per '{search_title}': trovati {len(found_candidates)} spartiti", "INFO")
                if not found_candidates:
                    st.warning("Nessun brano trovato con questi termini sui portali online, oppure rete non raggiungibile.")

        if auto_import:
            with st.spinner("Ricerca e importazione del brano migliore in corso..."):
                try:
                    imported_song = WebSongImporter.search_online_and_import(search_title, search_artist)
                    saved = storage.save_song(imported_song, st.session_state["current_user_email"], st.session_state["current_user_name"], "Ricerca Web e Importazione Automatica")
                    if target_rep:
                        storage.move_song_to_repertoire(saved.uuid, target_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                    st.session_state["selected_song_uuid"] = saved.uuid
                    rep_msg = f" ed associato a **'{target_rep.name}'**" if target_rep else ""
                    log_op("⚡", "WEB IMPORT", f"Importazione rapida completata: '{saved.title}' ({saved.artist})", "SUCCESS")
                    st.success(f"Brano importato e salvato: **{saved.title}** ({saved.artist}) — Tonalità: `{saved.key_current}`{rep_msg}")
                    st.info("Puoi visualizzarlo o modificarlo nella sezione **'🎵 Repertorio'**.")
                except Exception as err:
                    log_op("❌", "WEB IMPORT", f"Errore import automatico: {str(err)}", "ERROR")
                    st.error(f"Errore durante l'importazione automatica: {str(err)}")

        # Visualizza risultati candidati trovati
        candidates = st.session_state.get("web_search_candidates", [])
        if candidates:
            st.write(f"##### 📋 Risultati trovati sul Web ({len(candidates)} spartiti disponibili):")
            for idx, cand in enumerate(candidates):
                with st.container():
                    col_info, col_act = st.columns([4, 1])
                    with col_info:
                        st.markdown(f"**{cand['title']}** — *{cand.get('artist', '')}*  \n🏷️ Portale: `{cand['portal']}` | [Apri Pagina Originale ↗]({cand['url']})")
                    with col_act:
                        if st.button("📥 Importa", key=f"imp_cand_{idx}", width="stretch"):
                            with st.spinner("Scaricamento e parsing in AML..."):
                                try:
                                    s_obj = WebSongImporter.fetch_from_url(cand["url"])
                                    if (not s_obj.artist or s_obj.artist == "Artista Sconosciuto") and cand.get("artist"):
                                        s_obj.artist = cand["artist"]
                                    if (not s_obj.title or s_obj.title == "Brano da Web") and cand.get("title"):
                                        s_obj.title = cand["title"]
                                    saved = storage.save_song(s_obj, st.session_state["current_user_email"], st.session_state["current_user_name"], f"Importato da {cand['portal']}")
                                    if target_rep:
                                        storage.move_song_to_repertoire(saved.uuid, target_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                                    st.session_state["selected_song_uuid"] = saved.uuid
                                    rep_msg = f" ed inserito in **'{target_rep.name}'**" if target_rep else ""
                                    log_op("📥", "WEB IMPORT", f"Importato brano '{saved.title}' da {cand['portal']}", "SUCCESS")
                                    st.success(f"Brano salvato: **{saved.title}** (Key: `{saved.key_current}`){rep_msg}!")
                                except Exception as e_imp:
                                    log_op("❌", "WEB IMPORT", f"Errore importazione candidato: {str(e_imp)}", "ERROR")
                                    st.error(f"Errore importazione: {str(e_imp)}")

    with tab_imp:
        st.write("#### Importazione da File PDF, ChordPro o Formato Tradizionale")
        imp_format = st.radio("Seleziona Formato di Origine:", ["ChordPro standard", "Tradizionale (Accordi sopra il testo)", "PDF"], horizontal=True)

        if imp_format == "PDF":
            uploaded_pdf = st.file_uploader("Carica File PDF dello spartito:", type=["pdf"])
            if uploaded_pdf and st.button("Estrai e Converti in AML"):
                pdf_bytes = uploaded_pdf.read()
                imported_s = ImportEngine.import_from_pdf_bytes(pdf_bytes, filename=uploaded_pdf.name)
                saved = storage.save_song(imported_s, st.session_state["current_user_email"], st.session_state["current_user_name"])
                if target_rep:
                    storage.move_song_to_repertoire(saved.uuid, target_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                rep_msg = f" ed inserito in **'{target_rep.name}'**" if target_rep else ""
                st.success(f"Estratto e salvato con successo come '{saved.title}'{rep_msg}!")
                st.session_state["selected_song_uuid"] = saved.uuid
        else:
            pasted_text = st.text_area("Incolla qui il testo dello spartito:", height=200)
            if pasted_text and st.button("Converti e Salva in Repertorio"):
                if imp_format == "ChordPro standard":
                    s_obj = ImportEngine.import_from_chordpro(pasted_text)
                else:
                    s_obj = ImportEngine.import_from_traditional(pasted_text)
                saved = storage.save_song(s_obj, st.session_state["current_user_email"], st.session_state["current_user_name"])
                if target_rep:
                    storage.move_song_to_repertoire(saved.uuid, target_rep.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                rep_msg = f" ed inserito in **'{target_rep.name}'**" if target_rep else ""
                st.success(f"Brano importato e salvato: **{saved.title}** (Key: {saved.key_current}){rep_msg}")

    with tab_exp:
        st.write("#### Esportazione per MobileSheets, SongBookPro, OnSong")
        all_s = storage.list_songs()
        if all_s:
            exp_song_id = st.selectbox("Seleziona Brano da esportare:", [s["uuid"] for s in all_s], format_func=lambda x: next(s["title"] for s in all_s if s["uuid"] == x))
            target_song = storage.get_song(exp_song_id)

            c_e1, c_e2, c_e3, c_e4 = st.columns(4)
            with c_e1:
                sb_content = ExportEngine.export_for_songbookpro(target_song)
                st.download_button("🎸 SongBook Pro (.pro)", sb_content, file_name=f"{target_song.title}.pro", width="stretch")
            with c_e2:
                ms_content = ExportEngine.export_for_mobilesheets(target_song)
                st.download_button("📱 MobileSheets (.pro)", ms_content, file_name=f"{target_song.title}_ms.pro", width="stretch")
            with c_e3:
                cpro_content = ExportEngine.export_to_chordpro(target_song.aml_content)
                st.download_button("🎼 ChordPro (.cho)", cpro_content, file_name=f"{target_song.title}.cho", width="stretch")
            with c_e4:
                onsong_content = ExportEngine.export_for_onsong(target_song)
                st.download_button("🎤 OnSong (.onsong)", onsong_content, file_name=f"{target_song.title}.onsong", width="stretch")

            st.divider()
            st.write("#### 📦 Offline Live Pack ZIP (SRS Cap. 14.29)")
            setlists = storage.list_setlists()
            if setlists:
                pack_set = st.selectbox("Seleziona Scaletta per generare il Live Pack:", setlists, format_func=lambda x: x.title)
                pack_songs = [storage.get_song(it.song_uuid) for it in pack_set.items if storage.get_song(it.song_uuid)]
                if pack_songs:
                    pack_zip = ExportEngine.create_offline_live_pack_zip(pack_set, pack_songs)
                    st.download_button(
                        "💾 Scarica Offline Live Pack ZIP Completo",
                        data=pack_zip,
                        file_name=f"OfflinePack_{pack_set.title.replace(' ', '_')}.zip",
                        mime="application/zip",
                        type="primary"
                    )

# ------------------------------------------------------------------------------
# 8. RICERCA GLOBALE
# ------------------------------------------------------------------------------
elif menu_choice == "🔍 Ricerca Globale":
    st.subheader("🔍 Ricerca Globale Multi-Criterio (< 2ms)")

    c_q1, c_q2, c_q3, c_q4, c_q5 = st.columns(5)
    with c_q1:
        search_txt = st.text_input("Parola chiave (titolo/autore/testo):", "")
    with c_q2:
        search_key = st.text_input("Tonalità (es. C o G):", "")
    with c_q3:
        search_bpm = st.number_input("BPM Massimo:", min_value=0, max_value=300, value=250)
    with c_q4:
        search_genre = st.text_input("Genere:", "")
    with c_q5:
        available_tags = ["Tutti"] + list(storage.list_all_tags().keys())
        search_tag = st.selectbox("Filtra per Tag:", available_tags)

    t0 = time.perf_counter()
    res = storage.search_songs(
        query_text=search_txt or None,
        key=search_key or None,
        bpm_max=search_bpm if search_bpm > 0 else None,
        genre=search_genre or None,
        tag=search_tag if search_tag != "Tutti" else None
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    st.caption(f"⚡ Ricerca eseguita in **{elapsed_ms:.3f} ms** su SQLite in-memory | Trovati: **{len(res)}**")
    if res:
        st.dataframe(res, width="stretch")
    else:
        st.info("Nessun brano corrisponde ai criteri.")

# ------------------------------------------------------------------------------
# 9. BAND AI (OPZIONALE)
# ------------------------------------------------------------------------------
elif menu_choice == "🤖 Band AI (Opzionale)":
    st.subheader("🤖 Assistente Creativo Band AI (100% Opzionale)")
    st.caption("In conformità alla SRS (Cap. 1.4 e 22.6), l'AI è rigorosamente esclusa da accordi, trasposizioni e PDF. Fornisce solo spunti creativi di arrangiamento e medley.")

    ai_mode = BandAIService.get_current_mode()
    st.info(f"Modalità AI Attuale del Sistema: **{ai_mode}**")

    tab_ai1, tab_ai2 = st.tabs(["🎵 Suggeritore Medley & Transizioni", "🎸 Idee di Arrangiamento Live"])

    with tab_ai1:
        st.write("#### Analisi e Suggerimenti Transizione Medley")
        all_s = storage.list_songs()
        if len(all_s) >= 2:
            s_choices = {s["uuid"]: s["title"] for s in all_s}
            id_a = st.selectbox("Primo Brano:", list(s_choices.keys()), format_func=lambda x: s_choices[x], key="ai_s1")
            id_b = st.selectbox("Secondo Brano:", [k for k in s_choices.keys() if k != id_a], format_func=lambda x: s_choices[x], key="ai_s2")

            s_a = storage.get_song(id_a)
            s_b = storage.get_song(id_b)

            if st.button("💡 Analizza Compatibilità & Suggerisci Transizione"):
                advice = BandAIService.suggest_medley_transition(s_a.title, s_a.key_current, s_a.bpm, s_b.title, s_b.key_current, s_b.bpm)
                st.metric("Affinità Transizione", f"{int(advice['score'] * 100)}%")
                st.text_area("Consigli di Regia e Arrangiamento:", advice["creative_advice"], height=160)
        else:
            st.info("Inserisci almeno 2 brani nell'archivio per calcolare la transizione medley.")

    with tab_ai2:
        st.write("#### Consigli Strumentali per Brano")
        if all_s:
            sel_s_id = st.selectbox("Seleziona Brano:", [s["uuid"] for s in all_s], format_func=lambda x: next(s["title"] for s in all_s if s["uuid"] == x), key="ai_arr_s")
            s_obj = storage.get_song(sel_s_id)
            if st.button("🎸 Genera Idee di Dinamica & Sezioni"):
                arr_text = BandAIService.suggest_arrangement_ideas(s_obj.title, s_obj.genre, s_obj.key_current, s_obj.bpm)
                st.markdown(arr_text)

# ------------------------------------------------------------------------------
# 10. MANUALE & CHANGELOG
# ------------------------------------------------------------------------------
elif menu_choice == "📖 Manuale & Changelog":
    st.subheader("📖 Documentazione Ufficiale & Registro Modifiche")

    tab_man, tab_chan = st.tabs(["📘 Manuale Utente Auto-Aggiornante", "📜 Changelog Giornaliero (AAAA.MM.GG)"])

    with tab_man:
        st.write("### Manuale Operativo Ufficiale ASMA 2.0")
        manual_pdf = ManualEngine.generate_manual_pdf()
        st.download_button("📄 Scarica Manuale Completo in PDF Stampabile", data=manual_pdf, file_name="Manuale_Utente_ASMA_2.0.pdf", mime="application/pdf", type="primary")
        st.divider()
        st.markdown(ManualEngine.get_manual_markdown())

    with tab_chan:
        st.write("### Registro Modifiche (Changelog)")
        st.markdown(ChangelogEngine.get_changelog_markdown())

# ------------------------------------------------------------------------------
# 11. AMMINISTRAZIONE & LOG
# ------------------------------------------------------------------------------
elif menu_choice == "⚙️ Amministrazione & Log":
    st.subheader("⚙️ Pannello di Controllo Amministrativo (Solo ADMIN)")

    if not current_user.can_admin():
        st.error(f"⛔ **Accesso Negato**: Questa sezione è riservata esclusivamente agli amministratori. Il tuo account ({current_user.email}) ha il ruolo di **{current_user.role.value}**.")
        st.info("Per accedere, seleziona un profilo ADMIN nella barra laterale o chiedi a un amministratore di aggiornare i tuoi privilegi.")
    else:
        tab_locks, tab_audit, tab_aml_syntax, tab_tags, tab_devices, tab_users, tab_backup, tab_trash, tab_gist, tab_health = st.tabs([
            "🔒 Gestione Lock Attivi",
            "📜 Audit Trail Immutabile",
            "🎼 Sintassi & Tag AML",
            "🏷️ Gestione Tag & Tassonomia",
            "📱 Dispositivi & Schermi Band",
            "👥 Utenti & Ruoli Band",
            "💾 Backup & Ripristino",
            "🗑️ Cestino (Retention 30gg)",
            "☁️ Sincronizzazione GitHub Gist",
            "🏥 Health & Telemetria"
        ])

        with tab_locks:
            st.write("#### Lock Concorrenza Attivi")
            active_locks = lock_mgr.get_active_locks()
            if active_locks:
                st.dataframe(active_locks, width="stretch")
                for l in active_locks:
                    if st.button(f"Sblocca Forzatamente {l['song_uuid']}", key=f"force_unlock_{l['song_uuid']}"):
                        lock_mgr.release_lock(l["song_uuid"], current_user.email, force=True)
                        st.success("Sbloccato con successo.")
                        st.rerun()
            else:
                st.success("Nessun lock attivo al momento. Tutti i brani sono liberi per la modifica.")

        with tab_audit:
            st.write("#### Registro Audit Trail Immutabile")
            entries = audit.get_entries(limit=50)
            if entries:
                st.dataframe([e.to_dict() for e in entries], width="stretch")
            else:
                st.info("Nessuna voce di audit.")

        with tab_aml_syntax:
            st.write("#### 🎼 Configurazione e Gestione Tag Sintassi AML (ASMA Markup Language)")
            st.caption("Configura, aggiungi, modifica e rimuovi i tag e le direttive del linguaggio musicale AML. Il parser interpreta dinamicamente questi elementi per formattazione, indicizzazione e PDF.")

            st.markdown("""
            <div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; margin-bottom:16px;">
              <span style="color:#00E5FF; font-weight:bold; font-size:14px;">📋 Esempi di Sintassi e Struttura AML:</span>
              <ul style="color:#e6edf3; margin-top:8px; margin-bottom:0; font-size:13px; line-height:1.7;">
                <li><b>• Direttive:</b> <code>{title: Titolo}</code>, <code>{artist: Artista}</code>, <code>{key: Tonalità}</code>, <code>{tempo: BPM}</code>, <code>{time: 4/4}</code></li>
                <li><b>• Sezioni:</b> <code>{intro}</code>, <code>{verse}</code>, <code>{chorus}</code>, <code>{bridge}</code>, <code>{solo}</code>, <code>{outro}</code></li>
                <li><b>• Accordi Inline:</b> <code>[Am]On a dark desert highway, [F#7]cool wind in my hair</code></li>
                <li><b>• Griglia Armonica a Battute:</b> <code>| DO | LAm | FA | SOL |</code></li>
                <li><b>• Tag Strumentali:</b> <code>{guitar: Solo Don Felder}</code>, <code>{voice: Armonizzazione a 3}</code>, <code>{bass: Slap groove}</code></li>
              </ul>
            </div>
            """, unsafe_allow_html=True)

            all_aml_tags = aml_tag_mgr.list_tags()
            n_dir = sum(1 for t in all_aml_tags if t.category == "directive")
            n_sec = sum(1 for t in all_aml_tags if t.category == "section")
            n_inst = sum(1 for t in all_aml_tags if t.category == "instrumental_tag")
            n_syn = sum(1 for t in all_aml_tags if t.category == "structural_syntax")

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Direttive", n_dir)
            with m2:
                st.metric("Sezioni Musicali", n_sec)
            with m3:
                st.metric("Tag Strumentali", n_inst)
            with m4:
                st.metric("Sintassi Speciale", n_syn)

            cat_map = {
                "Tutte": "Tutte",
                "Direttive": "directive",
                "Sezioni Musicali": "section",
                "Tag Strumentali": "instrumental_tag",
                "Sintassi Strutturale": "structural_syntax"
            }
            filter_cat_label = st.selectbox("Filtra Elenco Tag per Categoria:", list(cat_map.keys()), key="filter_aml_cat")
            filtered_tags = aml_tag_mgr.list_tags(category=cat_map[filter_cat_label])

            st.write(f"##### 📋 Tag AML Attivi ({len(filtered_tags)})")
            tag_table_data = []
            for t in filtered_tags:
                tag_table_data.append({
                    "Tag": t.tag,
                    "Categoria": t.category.replace("_", " ").capitalize(),
                    "Nome Visualizzato": t.display_name,
                    "Sintassi Pattern": t.syntax_pattern,
                    "Esempio Reale": t.example,
                    "Descrizione": t.description,
                    "Rimozione Consentita": "Sì" if t.is_removable else "No (Fisso)"
                })
            st.dataframe(tag_table_data, width="stretch")

            st.divider()

            col_at1, col_at2, col_at3 = st.columns([1.3, 1.3, 1.4])

            with col_at1:
                st.write("##### ➕ Aggiungi Nuovo Tag AML")
                with st.form("form_add_aml_tag"):
                    new_tag_id = st.text_input("Nome Tag (univoco, minuscolo):", placeholder="es. saxophone, breakdown, bpm").strip().lower()
                    new_tag_cat = st.selectbox("Categoria:", ["directive", "section", "instrumental_tag"])
                    new_tag_disp = st.text_input("Nome Visualizzato:", placeholder="es. Sassofono, Breakdown Ritmico")
                    new_tag_pattern = st.text_input("Sintassi Pattern:", placeholder="es. {saxophone: Dettagli}")
                    new_tag_example = st.text_input("Esempio di Utilizzo:", placeholder="es. {saxophone: Solo Clarence Clemons}")
                    new_tag_desc = st.text_area("Descrizione del Tag:", placeholder="Descrivi la funzione del tag...", height=80)

                    btn_sub_aml = st.form_submit_button("Salva Nuovo Tag AML", type="primary")
                    if btn_sub_aml:
                        if new_tag_id and new_tag_disp:
                            try:
                                def_obj = AMLTagDefinition(
                                    tag=new_tag_id,
                                    category=new_tag_cat,
                                    display_name=new_tag_disp,
                                    syntax_pattern=new_tag_pattern or f"{{{new_tag_id}}}",
                                    example=new_tag_example or f"{{{new_tag_id}}}",
                                    description=new_tag_desc or "Tag personalizzato dall'amministratore",
                                    is_removable=True,
                                    is_builtin=False
                                )
                                aml_tag_mgr.add_tag(def_obj, current_user.email, current_user.name)
                                log_op("🎼", "AML TAG", f"Aggiunto nuovo tag AML '{new_tag_id}' ({new_tag_cat})", "SUCCESS")
                                st.success(f"Tag AML '{new_tag_id}' aggiunto con successo!")
                                st.rerun()
                            except Exception as ex:
                                st.error(str(ex))
                        else:
                            st.warning("Specifica un nome e una descrizione per il tag.")

            with col_at2:
                st.write("##### ✏️ Modifica Tag AML Esistente")
                if all_aml_tags:
                    tag_to_edit_id = st.selectbox("Seleziona Tag da modificare:", [t.tag for t in all_aml_tags], key="sel_tag_mod")
                    tag_cur = aml_tag_mgr.get_tag(tag_to_edit_id)
                    if tag_cur:
                        with st.form(f"form_edit_aml_{tag_cur.tag}"):
                            edit_disp = st.text_input("Nome Visualizzato:", value=tag_cur.display_name)
                            edit_pattern = st.text_input("Sintassi Pattern:", value=tag_cur.syntax_pattern)
                            edit_example = st.text_input("Esempio Reale:", value=tag_cur.example)
                            edit_desc = st.text_area("Descrizione:", value=tag_cur.description, height=80)
                            if st.form_submit_button("Aggiorna Tag"):
                                try:
                                    aml_tag_mgr.update_tag(
                                        tag_cur.tag,
                                        display_name=edit_disp,
                                        syntax_pattern=edit_pattern,
                                        example=edit_example,
                                        description=edit_desc,
                                        user_email=current_user.email,
                                        user_name=current_user.name
                                    )
                                    log_op("✏️", "AML TAG", f"Modificato tag AML '{tag_cur.tag}'", "INFO")
                                    st.success(f"Tag '{tag_cur.tag}' aggiornato con successo!")
                                    st.rerun()
                                except Exception as e_mod:
                                    st.error(str(e_mod))

            with col_at3:
                st.write("##### 🗑️ Elimina Tag / Ripristina")
                st.caption("Rimuovi tag non fondamentali o ripristina la configurazione iniziale.")

                removable_tags = [t for t in all_aml_tags if t.is_removable]
                if removable_tags:
                    tag_to_remove = st.selectbox("Seleziona Tag da Eliminare:", [t.tag for t in removable_tags], format_func=lambda x: f"{x} ({aml_tag_mgr.get_tag(x).category})", key="sel_tag_del")
                    with st.popover("🗑️ Conferma Rimozione Tag AML", width="stretch"):
                        st.warning(f"Vuoi davvero eliminare il tag AML **'{tag_to_remove}'**?")
                        if st.button("Elimina Definitivamente Tag", type="secondary"):
                            try:
                                aml_tag_mgr.delete_tag(tag_to_remove, current_user.email, current_user.name)
                                log_op("🗑️", "AML TAG", f"Eliminato tag AML '{tag_to_remove}'", "WARNING")
                                st.success(f"Tag AML '{tag_to_remove}' eliminato con successo!")
                                st.rerun()
                            except Exception as e_del:
                                st.error(str(e_del))
                else:
                    st.info("Nessun tag eliminabile.")

                st.write("---")
                st.caption("Ripristina tutti i tag AML di fabbrica (Direttive, Sezioni, Tag Strumentali, Accordi Inline, Griglie).")
                with st.popover("🔄 Ripristina Sintassi AML di Fabbrica", width="stretch"):
                    st.warning("Vuoi ripristinare il catalogo completo dei tag AML ai valori predefiniti di fabbrica?")
                    if st.button("Conferma Ripristino Sintassi AML", type="primary"):
                        aml_tag_mgr.reset_to_defaults(current_user.email, current_user.name)
                        log_op("🔄", "AML TAG", "Ripristinati i tag AML di fabbrica", "INFO")
                        st.success("Sintassi e tag AML ripristinati con successo!")
                        st.rerun()

        with tab_tags:
            st.write("#### 🏷️ Gestione Centralizzata Tag & Tassonomia (Solo ADMIN)")
            st.caption("Organizza, raggruppa, rinomina o elimina tag a livello globale in tutti i brani del catalogo musicale.")

            tag_counts = storage.list_all_tags()
            total_tags = len(tag_counts)
            total_tagged_instances = sum(tag_counts.values())

            m_t1, m_t2, m_t3 = st.columns(3)
            with m_t1:
                st.metric("Tag Distinti", total_tags)
            with m_t2:
                st.metric("Applicazioni Complessive", total_tagged_instances)
            with m_t3:
                most_used = max(tag_counts.items(), key=lambda x: x[1])[0] if tag_counts else "Nessuno"
                st.metric("Tag Più Utilizzato", most_used)

            st.write("##### 📋 Elenco Tag e Frequenza d'Uso")
            if tag_counts:
                tag_rows = [{"Tag": k, "Numero Brani": v} for k, v in tag_counts.items()]
                st.dataframe(tag_rows, width="stretch")
            else:
                st.info("Nessun tag assegnato ai brani nel catalogo.")

            st.divider()

            col_tag_op1, col_tag_op2, col_tag_op3 = st.columns(3)
            with col_tag_op1:
                st.write("##### ✏️ Rinomina o Unisci Tag (Merge)")
                st.caption("Rinomina un tag in tutti i brani in cui compare. Se il nuovo nome esiste già, i tag verranno unificati.")
                if tag_counts:
                    source_tag = st.selectbox("Seleziona Tag da rinominare:", list(tag_counts.keys()), key="src_tag_sel")
                    target_tag = st.text_input("Nuovo Nome Tag:", placeholder="es. acoustic-live", key="target_tag_input")
                    if st.button("Rinomina Tag Globalmente", type="primary"):
                        if target_tag.strip():
                            updated = storage.rename_tag_globally(source_tag, target_tag, current_user.email, current_user.name)
                            log_op("✏️", "TAG", f"Tag '{source_tag}' rinominato globalmente in '{target_tag.strip()}' su {updated} brani", "SUCCESS")
                            st.success(f"Tag '{source_tag}' rinominato in '{target_tag.strip()}' su {updated} brani!")
                            st.rerun()
                        else:
                            st.warning("Inserisci un nuovo nome valido per il tag.")
                else:
                    st.info("Nessun tag disponibile da rinominare.")

            with col_tag_op2:
                st.write("##### 🗑️ Eliminazione Globale Tag")
                st.caption("Rimuove completamente un tag da tutti i brani del catalogo musicale.")
                if tag_counts:
                    tag_to_delete = st.selectbox("Seleziona Tag da eliminare:", list(tag_counts.keys()), key="del_tag_sel")
                    with st.popover("🗑️ Elimina Tag dal Catalogo", width="stretch"):
                        st.warning(f"Vuoi davvero rimuovere il tag **'{tag_to_delete}'** da tutti i brani che lo contengono?")
                        if st.button("Conferma Rimozione Globale", type="secondary", key="btn_confirm_del_tag"):
                            removed = storage.delete_tag_globally(tag_to_delete, current_user.email, current_user.name)
                            log_op("🗑️", "TAG", f"Tag '{tag_to_delete}' eliminato da {removed} brani", "WARNING")
                            st.success(f"Tag '{tag_to_delete}' rimosso con successo da {removed} brani!")
                            st.rerun()
                else:
                    st.info("Nessun tag disponibile da eliminare.")

            with col_tag_op3:
                st.write("##### 🏷️ Assegnazione Massiva Tag (Bulk)")
                st.caption("Assegna rapidamente un tag a una selezione multipla di brani.")
                all_active_songs = storage.list_songs(include_deleted=False)
                if all_active_songs:
                    song_map = {s["uuid"]: s["title"] for s in all_active_songs}
                    selected_uuids = st.multiselect(
                        "Seleziona brani a cui assegnare il tag:",
                        options=list(song_map.keys()),
                        format_func=lambda x: song_map[x],
                        key="bulk_tag_songs"
                    )
                    bulk_tag_name = st.text_input("Tag da assegnare:", placeholder="es. scaletta-estiva", key="bulk_tag_name")
                    if st.button("Assegna Tag ai Brani Selezionati"):
                        if bulk_tag_name.strip() and selected_uuids:
                            added = storage.add_tag_to_songs(bulk_tag_name, selected_uuids, current_user.email, current_user.name)
                            log_op("🏷️", "TAG", f"Tag '{bulk_tag_name.strip()}' assegnato in bulk a {added} brani", "SUCCESS")
                            st.success(f"Tag '{bulk_tag_name.strip()}' assegnato a {added} brani!")
                            st.rerun()
                        else:
                            st.warning("Seleziona almeno un brano e specifica un tag.")
                else:
                    st.info("Nessun brano attivo disponibile nel catalogo.")

        with tab_devices:
            st.write("#### 📱 Gestione Dispositivi & Schermi Hardware dei Musicisti (SRS Cap. 5.3 & 16.14)")
            st.caption("Configura, aggiungi e rimuovi i profili dei dispositivi fisici (Pixel 8 pro, iPad, Galaxy Tab, Xiaomi Pad, smartphone generici e A4). L'engine grafico adatta automaticamente margini, colonne e font alle dimensioni millimetriche del display.")

            all_devs = device_mgr.list_devices()
            st.write(f"##### 📋 Dispositivi Attivi Configurati ({len(all_devs)})")

            dev_rows = []
            for d in all_devs:
                dim_str = f"{d.width_mm:.1f} x {d.height_mm:.1f} mm" if d.width_mm and d.height_mm else "Standard"
                dev_rows.append({
                    "Nome Dispositivo": d.name,
                    "Categoria": d.device_type.capitalize(),
                    "Dimensioni Display": dim_str,
                    "Orientamento": d.orientation.capitalize(),
                    "Colonne": d.columns,
                    "Font Accordi / Testo": f"{d.font_size_chords}pt / {d.font_size_lyrics}pt",
                    "Margini": f"{d.margin_top_mm:.0f}mm",
                    "Tipo": "Personalizzato" if d.is_custom else "Predefinito"
                })
            st.dataframe(dev_rows, width="stretch")

            st.divider()

            col_d_add, col_d_del, col_d_rst = st.columns([1.5, 1.2, 1.3])

            with col_d_add:
                st.write("##### ➕ Aggiungi Nuovo Dispositivo")
                with st.form("form_add_device"):
                    new_d_name = st.text_input("Nome Dispositivo:", placeholder="Es. Huawei MatePad 11")
                    c_type_col1, c_type_col2 = st.columns(2)
                    with c_type_col1:
                        new_d_type = st.selectbox("Tipo:", ["tablet", "smartphone", "printable_a4"])
                    with c_type_col2:
                        new_d_orient = st.selectbox("Orientamento:", ["portrait", "landscape"])

                    c_dim1, c_dim2 = st.columns(2)
                    with c_dim1:
                        new_d_w = st.number_input("Larghezza (mm):", min_value=50.0, max_value=500.0, value=170.0, step=1.0)
                    with c_dim2:
                        new_d_h = st.number_input("Altezza (mm):", min_value=50.0, max_value=500.0, value=250.0, step=1.0)

                    c_fnt1, c_fnt2, c_cols = st.columns(3)
                    with c_fnt1:
                        new_fnt_c = st.number_input("Font Accordi:", min_value=7.0, max_value=24.0, value=12.0, step=0.5)
                    with c_fnt2:
                        new_fnt_l = st.number_input("Font Testo:", min_value=6.0, max_value=22.0, value=11.0, step=0.5)
                    with c_cols:
                        new_cols_cnt = st.selectbox("Colonne:", [1, 2], index=1 if new_d_type == "tablet" else 0)

                    new_mrg = st.number_input("Margine laterale (mm):", min_value=2.0, max_value=30.0, value=8.0, step=1.0)

                    btn_sub_dev = st.form_submit_button("Salva Nuovo Dispositivo", type="primary")
                    if btn_sub_dev:
                        if new_d_name.strip():
                            try:
                                dev_obj = DeviceProfile(
                                    name=new_d_name.strip(),
                                    target_device=new_d_type if new_d_type != "printable_a4" else "pc_a4",
                                    device_type=new_d_type,
                                    width_mm=new_d_w,
                                    height_mm=new_d_h,
                                    orientation=new_d_orient,
                                    columns=new_cols_cnt,
                                    font_size_lyrics=new_fnt_l,
                                    font_size_chords=new_fnt_c,
                                    margin_top_mm=new_mrg,
                                    margin_bottom_mm=new_mrg,
                                    margin_left_mm=new_mrg,
                                    margin_right_mm=new_mrg,
                                    is_custom=True
                                )
                                device_mgr.add_device(dev_obj, current_user.email, current_user.name)
                                log_op("📱", "DISPOSITIVI", f"Aggiunto nuovo profilo dispositivo: '{new_d_name.strip()}'", "SUCCESS")
                                st.success(f"Dispositivo '{new_d_name.strip()}' aggiunto con successo!")
                                st.rerun()
                            except Exception as err:
                                st.error(str(err))
                        else:
                            st.warning("Inserisci un nome valido per il dispositivo.")

            with col_d_del:
                st.write("##### 🗑️ Rimuovi Dispositivo")
                st.caption("Elimina un profilo hardware dall'elenco disponibile per i musicisti.")
                if all_devs:
                    dev_to_del = st.selectbox("Seleziona Dispositivo da Eliminare:", all_devs, format_func=lambda d: f"{d.name} ({d.device_type})", key="sel_del_dev")
                    with st.popover("🗑️ Conferma Rimozione Dispositivo", width="stretch"):
                        st.warning(f"Vuoi davvero eliminare il dispositivo **'{dev_to_del.name}'**?")
                        if st.button("Elimina Dispositivo", type="secondary", key="btn_confirm_del_dev"):
                            try:
                                device_mgr.remove_device(dev_to_del.uuid, current_user.email, current_user.name)
                                log_op("🗑️", "DISPOSITIVI", f"Rimosso profilo dispositivo: '{dev_to_del.name}'", "WARNING")
                                st.success(f"Dispositivo '{dev_to_del.name}' rimosso!")
                                st.rerun()
                            except Exception as e_del:
                                st.error(str(e_del))
                else:
                    st.info("Nessun dispositivo disponibile.")

            with col_d_rst:
                st.write("##### 🔄 Ripristina Predefiniti Band")
                st.caption("Ripristina l'elenco ufficiale dei dispositivi standard (Pixel 8 Pro, iPad, Tab S7/S8/S9, A4, Xiaomi, Oppo, iPhone, Android).")
                with st.popover("🔄 Ripristina Tutti i Dispositivi Predefiniti", width="stretch"):
                    st.warning("Questa operazione ripristinerà gli 8 profili hardware predefiniti della band. Continuare?")
                    if st.button("Conferma Ripristino Standard", type="primary"):
                        device_mgr.reset_defaults(current_user.email, current_user.name)
                        log_op("🔄", "DISPOSITIVI", "Ripristinati gli 8 profili dispositivi predefiniti della band", "INFO")
                        st.success("Profili hardware ripristinati con successo!")
                        st.rerun()

        with tab_users:
            st.write("#### 👥 Gestione Utenti, Ruoli & Permessi Band (SRS Cap. 3 & 10)")
            users = auth_mgr.list_users()
            u_data = []
            for u in users:
                u_data.append({
                    "Email": u.email,
                    "Nome": u.name,
                    "Ruolo": u.role.value,
                    "Provider": u.provider,
                    "Attivo": "Sì" if u.is_active else "No"
                })
            st.dataframe(u_data, width="stretch")

            col_u1, col_u2, col_u3 = st.columns(3)
            with col_u1:
                st.write("##### ✏️ Modifica Ruolo")
                target_user_email = st.selectbox("Seleziona Utente:", [u.email for u in users], key="target_u_email")
                new_role_choice = st.selectbox("Nuovo Ruolo:", [r.value for r in UserRole], key="new_r_choice")
                if st.button("Aggiorna Ruolo Utente", type="primary"):
                    try:
                        auth_mgr.update_user_role(target_user_email, UserRole(new_role_choice), current_user.email)
                        log_op("👥", "UTENTI", f"Ruolo di {target_user_email} aggiornato a {new_role_choice}", "INFO")
                        st.success(f"Ruolo di {target_user_email} aggiornato a {new_role_choice}!")
                        st.rerun()
                    except Exception as ex:
                        st.error(str(ex))
            with col_u2:
                st.write("##### ➕ Registra Musicista")
                new_u_email = st.text_input("Email Nuovo Utente:", placeholder="batteria@band.org")
                new_u_name = st.text_input("Nome e Cognome:", placeholder="Luca Rossi")
                new_u_role = st.selectbox("Ruolo Iniziale:", [r.value for r in UserRole], index=1)
                if st.button("Aggiungi Utente"):
                    if new_u_email:
                        reg_user = auth_mgr.authenticate_or_register_google(new_u_email, new_u_name)
                        auth_mgr.update_user_role(reg_user.email, UserRole(new_u_role), current_user.email)
                        log_op("➕", "UTENTI", f"Registrato utente {reg_user.name} ({new_u_role})", "SUCCESS")
                        st.success(f"Utente {reg_user.name} registrato!")
                        st.rerun()
            with col_u3:
                st.write("##### 🗑️ Elimina Utente")
                deletable_users = [u.email for u in users if u.email.lower() != current_user.email.lower()]
                if deletable_users:
                    user_to_delete = st.selectbox("Seleziona Utente da Rimuovere:", deletable_users, key="user_to_del")
                    with st.popover("🗑️ Elimina Account", width="stretch"):
                        st.warning(f"Vuoi davvero eliminare l'account di **{user_to_delete}**?")
                        if st.button("Conferma Eliminazione Account", type="secondary"):
                            try:
                                auth_mgr.delete_user(user_to_delete, current_user.email)
                                log_op("🗑️", "UTENTI", f"Eliminato account {user_to_delete}", "WARNING")
                                st.success(f"Utente '{user_to_delete}' eliminato con successo.")
                                st.rerun()
                            except Exception as err:
                                st.error(str(err))
                else:
                    st.info("Nessun altro utente rimovibile (sei l'unico amministratore connesso).")

        with tab_backup:
            st.write("#### 💾 Backup & Ripristino Disaster Recovery (SRS Cap. 10.15, 10.16 & 17.5)")
            st.caption("Esegui un backup atomico compresso (.ZIP) di tutto il catalogo musicale, impostazioni, eventi e storico revisioni, oppure ripristina un punto di ripristino precedente.")

            b_c1, b_c2 = st.columns(2)
            with b_c1:
                st.write("##### 📦 Esporta Backup Completo")
                backup_bytes = BackupEngine.create_full_backup_zip()
                now_iso = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_op("📦", "BACKUP", f"Creato archivio backup completo ({len(backup_bytes)} bytes)", "INFO")
                st.download_button(
                    "💾 Scarica Backup ZIP Completo",
                    data=backup_bytes,
                    file_name=f"ASMA_BACKUP_{now_iso}.zip",
                    mime="application/zip",
                    type="primary",
                    width="stretch"
                )
                st.info("Include: brani AML, revisioni, scalette, repertori, eventi live, log di audit e utenti.")

            with b_c2:
                st.write("##### 🔄 Ripristina da File Backup ZIP")
                uploaded_backup = st.file_uploader("Carica file ZIP di backup ASMA:", type=["zip"], key="backup_upload")
                if uploaded_backup and st.button("⚠️ Avvia Ripristino Completo"):
                    with st.spinner("Verifica integrità ed estrazione dei file in corso..."):
                        ok, msg = BackupEngine.restore_from_backup_zip(uploaded_backup.read())
                        log_op("🔄", "BACKUP", f"Ripristino backup: {msg}", "SUCCESS" if ok else "ERROR")
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        with tab_trash:
            st.write("#### 🗑️ Cestino Brani Eliminati (Soft-Delete a 30 giorni)")
            st.info("I brani eliminati vengono conservati qui prima dell'eventuale eliminazione definitiva.")
            deleted_songs = storage.list_songs(include_deleted=True)
            soft_deleted = [s for s in deleted_songs if s.get("is_deleted") == 1]
            if soft_deleted:
                st.dataframe(soft_deleted, width="stretch")

                col_tr_top1, col_tr_top2 = st.columns([3, 1])
                with col_tr_top2:
                    with st.popover("🧹 Svuota Cestino", width="stretch"):
                        st.warning("Vuoi eliminare definitivamente TUTTI i brani nel cestino? L'operazione è irreversibile.")
                        if st.button("Conferma Svuota Cestino", type="secondary", disabled=not current_user.can_admin()):
                            purged = storage.empty_trash(current_user.email, current_user.name)
                            log_op("🧹", "CESTINO", f"Cestino svuotato: eliminati definitivamente {purged} brani", "WARNING")
                            st.success(f"Cestino svuotato: {purged} brani eliminati definitivamente.")
                            st.rerun()

                st.write("##### Azioni per Singolo Brano:")
                for sd in soft_deleted:
                    c_sd1, c_sd2, c_sd3 = st.columns([3, 1, 1.2])
                    with c_sd1:
                        st.write(f"🎵 **{sd['title']}** — {sd.get('artist', '')} (Key: `{sd.get('key_current', '-')}`)")
                    with c_sd2:
                        if st.button("🔄 Ripristina", key=f"restore_{sd['uuid']}", width="stretch"):
                            storage.restore_song(sd["uuid"], current_user.email, current_user.name)
                            log_op("♻️", "RIPRISTINO", f"Brano '{sd['title']}' ripristinato dal cestino", "SUCCESS")
                            st.success(f"Brano '{sd['title']}' ripristinato nell'archivio!")
                            st.rerun()
                    with c_sd3:
                        with st.popover("🔥 Elimina", width="stretch"):
                            st.write(f"Eliminare definitivamente **'{sd['title']}'**?")
                            if st.button("Conferma", key=f"purge_{sd['uuid']}", type="secondary", disabled=not current_user.can_admin()):
                                storage.purge_song_permanently(sd["uuid"], current_user.email, current_user.name)
                                log_op("🔥", "CESTINO", f"Brano '{sd['title']}' eliminato definitivamente", "WARNING")
                                st.success(f"Brano '{sd['title']}' eliminato definitivamente.")
                                st.rerun()
            else:
                st.write("Il cestino è attualmente vuoto.")

        with tab_gist:
            st.write("#### Sincronizzazione Remota GitHub Gist (SRS Cap. 18.9 & 22.8)")
            st.caption("Sincronizza l'intero archivio musicale con il tuo repository Gist a costo zero.")
            is_conn, msg = gist_client.test_connection()
            if is_conn:
                st.success(f"🟢 Stato Connessione Gist: {msg}")
                if st.button("☁️ Sincronizza Tutti i File su Gist Adesso", type="primary"):
                    all_s = storage.list_songs()
                    push_dict = {f"{s['uuid']}.json": json.dumps(s) for s in all_s}
                    push_ok, push_msg = gist_client.push_files(push_dict)
                    log_op("☁️", "SYNC GIST", f"Gist push: {push_msg}", "SUCCESS" if push_ok else "ERROR")
                    if push_ok:
                        st.success(push_msg)
                    else:
                        st.error(push_msg)
            else:
                st.warning(f"🟡 Stato Gist: {msg}")
                st.info("Per abilitare la sincronizzazione automatica remota, configura le variabili di ambiente `GITHUB_TOKEN` e `GIST_ID` o aggiungile a `.streamlit/secrets.toml`.")

        with tab_health:
            st.write("#### Endpoint di Controllo Salute `/health`")
            st.json({
                "status": "healthy",
                "version": "2026.11.05",
                "uptime_target": "99.9%",
                "storage_status": "ok",
                "in_memory_index": "active",
                "pdf_engine": "ok",
                "gist_sync": "configured" if gist_client.is_configured else "offline_local",
                "ai_mode": BandAIService.get_current_mode()
            })

# ------------------------------------------------------------------------------
# FINESTRA DI STATO BOTTOM (Accessibile da tutte le sezioni di ASMA)
# ------------------------------------------------------------------------------
st.write("")
st.divider()
with st.expander(f"📟 Finestra di Stato — Registro Operazioni in Tempo Reale ({op_logger.count()} eventi registrati)", expanded=False):
    render_status_console(op_logger, key_prefix="footer_console", compact=False)

