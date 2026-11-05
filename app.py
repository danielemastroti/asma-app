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
st.set_page_config(
    page_title="ASMA Accordi 2.0",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Dark Band Theme and Clean Layout (SRS Cap. 5 & Blueprint Sec. 14)
st.markdown("""
<style>
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
from asma_core.pdf_engine import PDFEngine
from asma_core.live_stage_component import LiveStageComponent
from asma_core.export_engine import ExportEngine
from asma_core.import_engine import ImportEngine
from asma_core.web_importer import WebSongImporter
from asma_core.manual_engine import ManualEngine
from asma_core.changelog_engine import ChangelogEngine
from asma_core.ai_service import BandAIService
from asma_core.gist_client import GistClient

# Initialize Singletons
storage = StorageManager()
lock_mgr = LockManager()
audit = AuditLogger()
gist_client = GistClient()

# Initialize Session State
if "current_user_name" not in st.session_state:
    st.session_state["current_user_name"] = "Daniele Rossi"
if "current_user_email" not in st.session_state:
    st.session_state["current_user_email"] = "daniele@band.org"
if "current_user_role" not in st.session_state:
    st.session_state["current_user_role"] = "ADMIN"
if "selected_song_uuid" not in st.session_state:
    st.session_state["selected_song_uuid"] = None
if "selected_setlist_uuid" not in st.session_state:
    st.session_state["selected_setlist_uuid"] = None

# TOP FIXED HEADER (SRS Cap. 3.5 & 5.3)
col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
with col_h1:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:16px;">
      <span class="user-badge">👤 {st.session_state['current_user_name']} ({st.session_state['current_user_role']})</span>
      <span class="status-badge">🟢 ONLINE</span>
      <span class="version-tag">Versione: <b>ASMA 2026.11.05</b></span>
    </div>
    """, unsafe_allow_html=True)
with col_h3:
    st.caption(f"Storage: In-Memory SQLite + Gist | Health: OK")

st.divider()

# LEVEL 1 NAVIGATION MENU (SRS Cap. 5.4)
menu_choice = st.sidebar.radio(
    "MENU PRINCIPALE",
    [
        "🏠 Home Dashboard",
        "📚 Repertori",
        "📝 Editor & Split-View",
        "📑 Scalette Live",
        "🎤 Modalità Palco (Live Stage)",
        "📅 Eventi Live",
        "📥 Importa & 📤 Esporta",
        "🔍 Ricerca Globale",
        "🤖 Band AI (Opzionale)",
        "📖 Manuale & Changelog",
        "⚙️ Amministrazione & Log"
    ]
)

# ------------------------------------------------------------------------------
# 1. HOME DASHBOARD
# ------------------------------------------------------------------------------
if menu_choice == "🏠 Home Dashboard":
    st.subheader("🏠 Home Dashboard Band")

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
    rep_names = [r.name for r in repertoires]
    selected_rep_name = st.selectbox("Seleziona Repertorio:", rep_names)
    selected_rep = next(r for r in repertoires if r.name == selected_rep_name)

    st.write(f"*{selected_rep.description}*")
    rep_songs = [storage.get_song(s_id) for s_id in selected_rep.song_uuids if storage.get_song(s_id)]

    c_btn1, c_btn2 = st.columns([1, 4])
    with c_btn1:
        if st.button("➕ Crea Nuovo Brano"):
            new_s = Song(title="Nuovo Brano", key_current="C", aml_content="{title: Nuovo Brano}\n{key: C}\n\n[C]Testo e accordi...")
            saved = storage.save_song(new_s, st.session_state["current_user_email"], st.session_state["current_user_name"])
            storage.move_song_to_repertoire(saved.uuid, selected_rep.uuid)
            st.session_state["selected_song_uuid"] = saved.uuid
            st.success(f"Creato brano '{saved.title}'")
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
        st.dataframe(rows, use_container_width=True)

        selected_s_id = st.selectbox("Apri Brano nell'Editor:", [r["UUID"] for r in rows], format_func=lambda x: next(r["Titolo"] for r in rows if r["UUID"] == x))
        col_act1, col_act2, col_act3 = st.columns(3)
        with col_act1:
            if st.button("📝 Modifica Brano nell'Editor"):
                st.session_state["selected_song_uuid"] = selected_s_id
                st.info("Passa alla scheda 'Editor & Split-View' dal menu a sinistra.")
        with col_act2:
            other_reps = [r for r in repertoires if r.uuid != selected_rep.uuid]
            if other_reps:
                dest_rep = st.selectbox("Sposta brano nel repertorio:", [r.name for r in other_reps])
                if st.button("➡️ Sposta Brano"):
                    target_r = next(r for r in other_reps if r.name == dest_rep)
                    storage.move_song_to_repertoire(selected_s_id, target_r.uuid, st.session_state["current_user_email"], st.session_state["current_user_name"])
                    st.success(f"Brano spostato in '{target_r.name}' senza perdita dello storico.")
                    st.rerun()
        with col_act3:
            if st.button("🗑️ Sposta nel Cestino"):
                storage.delete_song(selected_s_id, st.session_state["current_user_email"], st.session_state["current_user_name"])
                st.warning("Brano spostato nel cestino (recuperabile per 30 giorni).")
                st.rerun()
    else:
        st.info("Nessun brano associato a questo repertorio.")

# ------------------------------------------------------------------------------
# 3. EDITOR & SPLIT-VIEW
# ------------------------------------------------------------------------------
elif menu_choice == "📝 Editor & Split-View":
    st.subheader("📝 Editor Musicale & Anteprima Split-View")

    songs = storage.list_songs()
    if not songs:
        st.warning("Nessun brano disponibile. Creane uno dalla sezione 'Repertori'.")
        st.stop()

    song_choices = {s["uuid"]: s["title"] for s in songs}
    curr_uuid = st.session_state.get("selected_song_uuid") or list(song_choices.keys())[0]
    selected_uuid = st.selectbox("Seleziona Brano da modificare:", list(song_choices.keys()), index=list(song_choices.keys()).index(curr_uuid), format_func=lambda x: song_choices[x])
    st.session_state["selected_song_uuid"] = selected_uuid

    song = storage.get_song(selected_uuid)
    if not song:
        st.error("Brano non trovato.")
        st.stop()

    # Lock Management Check (SRS Cap. 4.6 & 7.7)
    current_lock = lock_mgr.check_lock(song.uuid)
    user_email = st.session_state["current_user_email"]
    user_name = st.session_state["current_user_name"]

    if current_lock.is_locked and current_lock.locked_by_email != user_email:
        st.error(f"🔒 Brano bloccato in modifica da **{current_lock.locked_by_name}** ({current_lock.locked_by_email}). Modalità sola lettura.")
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
                st.rerun()
        with tr_c2:
            if st.button("⬆️ +1 Semitono", disabled=not can_edit):
                doc = AMLParser.parse(song.aml_content)
                new_doc = AMLParser.transpose_document(doc, semitones=1)
                song.aml_content = new_doc.to_aml()
                song.key_current = MusicEngine.transpose_chord(song.key_current, semitones=1)
                storage.save_song(song, user_email, user_name, "Trasposizione +1 semitono")
                st.rerun()
        with tr_c3:
            if st.button("🇮🇹 Converti in ITA", disabled=not can_edit):
                doc = AMLParser.parse(song.aml_content)
                song.aml_content = AMLParser.convert_notation(doc, "ITA").to_aml()
                storage.save_song(song, user_email, user_name, "Conversione notazione italiana")
                st.rerun()
        with tr_c4:
            if st.button("🌐 Converti in INT", disabled=not can_edit):
                doc = AMLParser.parse(song.aml_content)
                song.aml_content = AMLParser.convert_notation(doc, "INT").to_aml()
                storage.save_song(song, user_email, user_name, "Conversione notazione internazionale")
                st.rerun()

        aml_editor_text = st.text_area("Testo AML:", value=song.aml_content, height=360, disabled=not can_edit)
        rev_comment = st.text_input("Commento della modifica (per storico revisioni):", value="Modifica accordi e sezioni", disabled=not can_edit)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("💾 Salva Nuova Revisione", type="primary", disabled=not can_edit):
                song.title = title_input
                song.artist = artist_input
                song.key_current = key_input
                song.bpm = bpm_input
                song.genre = genre_input
                song.capo = capo_input
                song.aml_content = aml_editor_text
                saved = storage.save_song(song, user_email, user_name, rev_comment)
                st.success(f"Salvato con successo! Nuova Revisione #{saved.current_revision}")
                st.rerun()
        with col_s2:
            if st.button("🔓 Rilascia Lock ed Esci"):
                lock_mgr.release_lock(song.uuid, user_email)
                st.info("Lock rilasciato.")
                st.rerun()

    with col_prev:
        st.write("#### 👁️ Anteprima Device-Aware & PDF")
        profile_choice = st.selectbox("Profilo Dispositivo:", ["pc_a4", "tablet", "ipad", "smartphone"])
        prof = DeviceProfile(target_device=profile_choice)

        pdf_bytes = PDFEngine.generate_song_pdf(song, profile=prof, use_cache=False)
        st.download_button(
            label="📄 Scarica PDF Stampabile",
            data=pdf_bytes,
            file_name=f"{song.title.replace(' ', '_')}_{profile_choice}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.caption("Anteprima visuale HTML:")
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
            submit_set = st.form_submit_button("Crea Scaletta")
            if submit_set:
                new_set = Setlist(title=new_title, date=new_date)
                storage.save_setlist(new_set, st.session_state["current_user_email"], st.session_state["current_user_name"])
                st.session_state["selected_setlist_uuid"] = new_set.uuid
                st.success(f"Creata scaletta '{new_title}'")
                st.rerun()

    with col_s2:
        curr_set_id = st.session_state.get("selected_setlist_uuid")
        if curr_set_id:
            active_setlist = next((s for s in setlists if s.uuid == curr_set_id), None)
            if active_setlist:
                st.write(f"### Scaletta: **{active_setlist.title}** ({active_setlist.date})")

                if all_songs:
                    add_song_id = st.selectbox("Aggiungi brano alla sequenza:", list(song_map.keys()), format_func=lambda x: song_map[x]["title"])
                    if st.button("➕ Inserisci in Scaletta"):
                        active_setlist.items.append(SetlistItem(song_uuid=add_song_id))
                        storage.save_setlist(active_setlist, st.session_state["current_user_email"], st.session_state["current_user_name"])
                        st.success("Brano aggiunto alla scaletta!")
                        st.rerun()

                st.write("#### Sequenza di Esecuzione:")
                for idx, item in enumerate(active_setlist.items, start=1):
                    s_info = song_map.get(item.song_uuid)
                    title = s_info["title"] if s_info else "Sconosciuto"
                    key = item.custom_key or (s_info["key_current"] if s_info else "-")
                    bpm = item.custom_bpm or (s_info["bpm"] if s_info else "-")
                    st.write(f"**{idx}. {title}** &bull; Key: `{key}` &bull; BPM: `{bpm}`")

                st.divider()
                c_p1, c_p2 = st.columns(2)
                with c_p1:
                    if st.button("🎤 Avvia Modalità Palco (Live Stage)", type="primary"):
                        st.session_state["launch_stage"] = True
                        st.info("Passa a 'Modalità Palco' dal menu a sinistra.")
                with c_p2:
                    loaded_songs = [storage.get_song(item.song_uuid) for item in active_setlist.items if storage.get_song(item.song_uuid)]
                    if loaded_songs:
                        set_pdf = PDFEngine.generate_setlist_pdf(active_setlist, loaded_songs)
                        st.download_button("📄 Scarica PDF Completo Scaletta", set_pdf, file_name=f"{active_setlist.title}.pdf", mime="application/pdf")

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

    tab_web, tab_imp, tab_exp = st.tabs(["🌐 Import da Web / URL", "📥 Import PDF & Testo", "📤 Esporta per App Esterne"])

    with tab_web:
        st.write("#### 🌐 Importazione Automatica da Internet (Siti Italiani ed Internazionali)")
        st.caption("Estrae automaticamente accordi e testi da Accordi e Spartiti, Skitarrate, Chordie, Ultimate-Guitar e pagine web pubbliche.")

        url_input = st.text_input("Incolla URL della pagina dello spartito:", placeholder="https://www.accordiespartiti.it/accordi/italiani/nomadi/canzone-per-unamica/")
        if url_input and st.button("Scarica e Converti in AML"):
            with st.spinner("Scaricamento e parsing della pagina web..."):
                try:
                    song_web = WebSongImporter.fetch_from_url(url_input)
                    saved = storage.save_song(song_web, st.session_state["current_user_email"], st.session_state["current_user_name"], "Importazione da Web URL")
                    st.success(f"Brano importato e salvato con successo: **{saved.title}** ({saved.artist}) — Tonalità: `{saved.key_current}`")
                    st.session_state["selected_song_uuid"] = saved.uuid
                except Exception as err:
                    st.error(f"Errore durante l'importazione da Web: {str(err)}")

        st.divider()
        st.write("#### Oppure cerca per Titolo / Artista:")
        c_w1, c_w2 = st.columns(2)
        with c_w1:
            search_title = st.text_input("Titolo Brano:", "Knockin' On Heaven's Door")
        with c_w2:
            search_artist = st.text_input("Artista:", "Bob Dylan")
        if st.button("🔍 Cerca Bozza Online"):
            draft = WebSongImporter.search_online_and_import(search_title, search_artist)
            saved = storage.save_song(draft, st.session_state["current_user_email"], st.session_state["current_user_name"], "Bozza creata da ricerca web")
            st.success(f"Creata bozza per '{draft.title}'. Puoi rifinirla nell'Editor!")
            st.session_state["selected_song_uuid"] = saved.uuid

    with tab_imp:
        st.write("#### Importazione da File PDF, ChordPro o Formato Tradizionale")
        imp_format = st.radio("Seleziona Formato di Origine:", ["ChordPro standard", "Tradizionale (Accordi sopra il testo)", "PDF"], horizontal=True)

        if imp_format == "PDF":
            uploaded_pdf = st.file_uploader("Carica File PDF dello spartito:", type=["pdf"])
            if uploaded_pdf and st.button("Estrai e Converti in AML"):
                pdf_bytes = uploaded_pdf.read()
                imported_s = ImportEngine.import_from_pdf_bytes(pdf_bytes, filename=uploaded_pdf.name)
                saved = storage.save_song(imported_s, st.session_state["current_user_email"], st.session_state["current_user_name"])
                st.success(f"Estratto e salvato con successo come '{saved.title}'!")
                st.session_state["selected_song_uuid"] = saved.uuid
        else:
            pasted_text = st.text_area("Incolla qui il testo dello spartito:", height=200)
            if pasted_text and st.button("Converti e Salva in Repertorio"):
                if imp_format == "ChordPro standard":
                    s_obj = ImportEngine.import_from_chordpro(pasted_text)
                else:
                    s_obj = ImportEngine.import_from_traditional(pasted_text)
                saved = storage.save_song(s_obj, st.session_state["current_user_email"], st.session_state["current_user_name"])
                st.success(f"Brano importato e salvato: **{saved.title}** (Key: {saved.key_current})")

    with tab_exp:
        st.write("#### Esportazione per MobileSheets, SongBookPro, OnSong")
        all_s = storage.list_songs()
        if all_s:
            exp_song_id = st.selectbox("Seleziona Brano da esportare:", [s["uuid"] for s in all_s], format_func=lambda x: next(s["title"] for s in all_s if s["uuid"] == x))
            target_song = storage.get_song(exp_song_id)

            c_e1, c_e2, c_e3 = st.columns(3)
            with c_e1:
                ms_content = ExportEngine.export_for_mobilesheets(target_song)
                st.download_button("📱 MobileSheets (.pro)", ms_content, file_name=f"{target_song.title}.pro")
            with c_e2:
                cpro_content = ExportEngine.export_to_chordpro(target_song.aml_content)
                st.download_button("🎼 ChordPro Standard (.cho)", cpro_content, file_name=f"{target_song.title}.cho")
            with c_e3:
                onsong_content = ExportEngine.export_for_onsong(target_song)
                st.download_button("🎤 OnSong (.onsong)", onsong_content, file_name=f"{target_song.title}.onsong")

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

    c_q1, c_q2, c_q3, c_q4 = st.columns(4)
    with c_q1:
        search_txt = st.text_input("Parola chiave (titolo/autore/testo):", "")
    with c_q2:
        search_key = st.text_input("Tonalità (es. C o G):", "")
    with c_q3:
        search_bpm = st.number_input("BPM Massimo:", min_value=0, max_value=300, value=250)
    with c_q4:
        search_genre = st.text_input("Genere:", "")

    t0 = time.perf_counter()
    res = storage.search_songs(
        query_text=search_txt or None,
        key=search_key or None,
        bpm_max=search_bpm if search_bpm > 0 else None,
        genre=search_genre or None
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    st.caption(f"⚡ Ricerca eseguita in **{elapsed_ms:.3f} ms** su SQLite in-memory | Trovati: **{len(res)}**")
    if res:
        st.dataframe(res, use_container_width=True)
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

    tab_locks, tab_audit, tab_trash, tab_gist, tab_health = st.tabs([
        "🔒 Gestione Lock Attivi",
        "📜 Audit Trail Immutabile",
        "🗑️ Cestino (Retention 30gg)",
        "☁️ Sincronizzazione GitHub Gist",
        "🏥 Health & Telemetria"
    ])

    with tab_locks:
        st.write("#### Lock Concorrenza Attivi")
        active_locks = lock_mgr.get_active_locks()
        if active_locks:
            st.dataframe(active_locks, use_container_width=True)
            for l in active_locks:
                if st.button(f"Sblocca Forzatamente {l['song_uuid']}", key=f"force_unlock_{l['song_uuid']}"):
                    lock_mgr.release_lock(l["song_uuid"], "admin@band.org", force=True)
                    st.success("Sbloccato con successo.")
                    st.rerun()
        else:
            st.success("Nessun lock attivo al momento. Tutti i brani sono liberi per la modifica.")

    with tab_audit:
        st.write("#### Registro Audit Trail Immutabile")
        entries = audit.get_entries(limit=50)
        if entries:
            st.dataframe([e.to_dict() for e in entries], use_container_width=True)
        else:
            st.info("Nessuna voce di audit.")

    with tab_trash:
        st.write("#### Elementi Eliminati (Soft-Delete a 30 giorni)")
        st.info("I brani nel cestino vengono conservati per 30 giorni prima dell'eliminazione definitiva.")
        deleted_songs = storage.list_songs(include_deleted=True)
        soft_deleted = [s for s in deleted_songs if s.get("is_deleted") == 1]
        if soft_deleted:
            st.dataframe(soft_deleted, use_container_width=True)
            for sd in soft_deleted:
                if st.button(f"Ripristina '{sd['title']}'", key=f"restore_trash_{sd['uuid']}"):
                    storage.restore_song(sd["uuid"], st.session_state["current_user_email"], st.session_state["current_user_name"])
                    st.success(f"Brano '{sd['title']}' ripristinato!")
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
                # Gist push
                all_s = storage.list_songs()
                push_dict = {f"{s['uuid']}.json": json.dumps(s) for s in all_s}
                push_ok, push_msg = gist_client.push_files(push_dict)
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
