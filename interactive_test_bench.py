"""
ASMA Accordi Next Generation - Interactive Test Bench (Streamlit UI)
Interactive playground to test and validate Music Engine, AML Parser,
In-memory SQL Storage, and Lock Manager before moving to Phase 3.
"""

import streamlit as st
import time
from asma_core.music_engine import MusicEngine
from asma_core.aml_parser import AMLParser
from asma_core.models import Song
from asma_core.storage_manager import StorageManager
from asma_core.lock_manager import LockManager

st.set_page_config(
    page_title="ASMA 2.0 - Core Test Bench",
    page_icon="🎸",
    layout="wide"
)

st.title("🎸 ASMA Accordi 2.0 — Banco di Test Interattivo dei Moduli Core")
st.caption("Piattaforma di collaudo e validazione: Music Engine, AML Parser, Storage In-Memory SQLite e Lock Manager.")

tab_music, tab_aml, tab_storage, tab_lock = st.tabs([
    "🎵 1. Motore Musicale & Trasposizioni",
    "📝 2. AML Parser & Import Tradizionale",
    "⚡ 3. Storage & Ricerca SQL (< 2ms)",
    "🔒 4. Lock Concorrenza Multiutente"
])

# ==============================================================================
# TAB 1: MUSIC ENGINE
# ==============================================================================
with tab_music:
    st.header("Collaudo del Music Engine Deterministico (Zero-AI)")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Trasposizione Singolo Accordo / Giro")
        input_chord = st.text_input("Accordo o sequenza:", value="DO7+ D/F# LA- SOLm")
        semitones = st.slider("Intervallo semitoni (Δ):", min_value=-12, max_value=12, value=2)
        notation = st.radio("Sistema di notazione:", ["Preserva", "Italiana (ITA)", "Internazionale (INT)"], horizontal=True)
        target_sys = "ITA" if "Italiana" in notation else ("INT" if "Internazionale" in notation else None)

        if input_chord:
            tokens = input_chord.split()
            transposed_tokens = [MusicEngine.transpose_chord(t, semitones=semitones, target_system=target_sys) for t in tokens]
            st.success(f"Risultato trasposto: **{' '.join(transposed_tokens)}**")

            # Check progression
            prog_info = MusicEngine.identify_progression(tokens)
            if prog_info["is_progression"]:
                st.info(f"Riconoscimento giro armonico: **{prog_info['description']}**")

    with col2:
        st.subheader("Calcolo Affinità Medley")
        c_k1, c_b1 = st.columns(2)
        with c_k1:
            key1 = st.text_input("Tonalità Brano 1:", value="DO")
            bpm1 = st.number_input("BPM Brano 1:", value=120, min_value=30, max_value=250)
        with c_b1:
            key2 = st.text_input("Tonalità Brano 2:", value="SOL")
            bpm2 = st.number_input("BPM Brano 2:", value=125, min_value=30, max_value=250)

        score, details = MusicEngine.calculate_harmonic_compatibility(key1, bpm1, key2, bpm2)
        st.metric("Punteggio Compatibilità Medley", f"{int(score * 100)}%", f"Distanza quinte: {details.get('fifths_distance', 0)}")
        st.write(f"**Delta BPM:** {details.get('bpm_diff_percent', 0)}%")
        st.write(f"**Raccomandazione Regia:** `{details.get('recommended_transition', '')}`")

# ==============================================================================
# TAB 2: AML PARSER & IMPORT
# ==============================================================================
with tab_aml:
    st.header("Collaudo AML Parser & Conversione Tradizionale")
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Importatore Formato Tradizionale (Accordi sopra il testo)")
        default_trad = """        C             G
Hello darkness my old friend
        Am            F
I've come to talk with you again"""
        trad_input = st.text_area("Incolla testo tradizionale:", value=default_trad, height=140)
        if st.button("Converti in AML Puro"):
            doc_imported = AMLParser.import_traditional_chords_over_text(trad_input)
            st.session_state["aml_live"] = doc_imported.to_aml()
            st.success("Convertito con successo in AML!")

    with col_b:
        st.subheader("Editor AML & Manipolazione AST")
        default_aml = st.session_state.get("aml_live", """{title: Hotel California}
{artist: Eagles}
{key: Bm}
{tempo: 74}
{time: 4/4}

{intro}
| Bm | F#7 | A | E |

{verse}
[Bm]On a dark desert highway, [F#7]cool wind in my hair
[A]Warm smell of colitas, [E]rising up through the air

{chorus}
[G]Welcome to the Hotel Cali[D]fornia
{guitar: Don Felder intro riff}
Such a [Em]lovely place, such a [F#7]lovely face""")

        aml_editor = st.text_area("Sorgente AML:", value=default_aml, height=220)

        c_tr1, c_tr2, c_tr3 = st.columns(3)
        with c_tr1:
            if st.button("Trasponi +1 semitono"):
                doc = AMLParser.parse(aml_editor)
                st.session_state["aml_live"] = AMLParser.transpose_document(doc, semitones=1).to_aml()
                st.rerun()
        with c_tr2:
            if st.button("Trasponi -1 semitono"):
                doc = AMLParser.parse(aml_editor)
                st.session_state["aml_live"] = AMLParser.transpose_document(doc, semitones=-1).to_aml()
                st.rerun()
        with c_tr3:
            if st.button("Converti in ITA"):
                doc = AMLParser.parse(aml_editor)
                st.session_state["aml_live"] = AMLParser.convert_notation(doc, to_system="ITA").to_aml()
                st.rerun()

    # Document Validation
    doc_val = AMLParser.parse(aml_editor)
    issues = AMLParser.validate(doc_val)
    if issues:
        st.warning(f"Rilevati {len(issues)} avvisi di validazione AML:")
        for iss in issues:
            st.write(f"- `{iss['level']}`: {iss['message']}")
    else:
        st.success("Documento AML valido al 100% (Zero errori o warning)")

# ==============================================================================
# TAB 3: STORAGE & SQL SEARCH
# ==============================================================================
with tab_storage:
    st.header("Collaudo Storage & Ricerca SQL in RAM (< 2ms)")
    storage = StorageManager()

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        q_text = st.text_input("Cerca testo / titolo:", "")
    with col_s2:
        q_key = st.text_input("Filtro Tonalità (es. Bm o G):", "")
    with col_s3:
        q_bpm_max = st.number_input("BPM Massimo:", min_value=0, max_value=300, value=200)
    with col_s4:
        q_genre = st.text_input("Genere (es. Rock):", "")

    t0 = time.perf_counter()
    search_results = storage.search_songs(
        query_text=q_text or None,
        key=q_key or None,
        bpm_max=q_bpm_max if q_bpm_max > 0 else None,
        genre=q_genre or None
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    st.caption(f"⚡ Ricerca completata su SQLite in-memory in **{elapsed_ms:.3f} ms** | Risultati: **{len(search_results)}**")

    if search_results:
        st.dataframe(
            search_results,
            column_order=["title", "artist", "key_current", "bpm", "genre", "current_revision"],
            use_container_width=True
        )
    else:
        st.info("Nessun brano corrisponde ai criteri.")

    with st.expander("Aggiungi rapidamente un nuovo brano per testare l'indice SQL"):
        with st.form("new_song_form"):
            new_title = st.text_input("Titolo:", "Nuovo Brano di Prova")
            new_artist = st.text_input("Artista:", "Band ASMA")
            new_key = st.text_input("Tonalità:", "C")
            new_bpm = st.number_input("BPM:", value=110)
            new_genre = st.text_input("Genere:", "Rock")
            submit = st.form_submit_button("Salva Brano")
            if submit:
                new_s = Song(title=new_title, artist=new_artist, key_current=new_key, bpm=new_bpm, genre=new_genre)
                storage.save_song(new_s, user_name="Tester", revision_comment="Test manuale da UI")
                st.success(f"Brano '{new_title}' salvato e indicizzato in SQLite!")
                st.rerun()

# ==============================================================================
# TAB 4: LOCK CONCURRENCY
# ==============================================================================
with tab_lock:
    st.header("Simulatore Concorrenza & Locking Editing (Cap. 4.6)")
    lock_mgr = LockManager()

    st.write("Simula due musicisti che tentano di modificare contemporaneamente lo stesso brano per verificare che il lock esclusivo prevenga i conflitti:")

    test_song_uuid = "hotel-california-demo-uuid"
    c_u1, c_u2 = st.columns(2)

    with c_u1:
        st.subheader("Musicista A: Roberto")
        if st.button("Roberto apre il brano in modifica"):
            ok, stt, msg = lock_mgr.acquire_lock(test_song_uuid, "roberto@band.org", "Roberto")
            if ok:
                st.success(msg)
            else:
                st.error(msg)

        if st.button("Roberto termina e rilascia il lock"):
            rel_ok, rel_msg = lock_mgr.release_lock(test_song_uuid, "roberto@band.org")
            st.info(rel_msg)

    with c_u2:
        st.subheader("Musicista B: Daniele")
        if st.button("Daniele prova ad aprire lo stesso brano"):
            ok, stt, msg = lock_mgr.acquire_lock(test_song_uuid, "daniele@band.org", "Daniele")
            if ok:
                st.success(msg)
            else:
                st.error(f"ACCESSO NEGATO: {msg}")

        if st.button("Daniele termina e rilascia il lock"):
            rel_ok, rel_msg = lock_mgr.release_lock(test_song_uuid, "daniele@band.org")
            st.info(rel_msg)

    st.divider()
    cur_lock = lock_mgr.check_lock(test_song_uuid)
    if cur_lock.is_locked:
        st.warning(f"Stato Attuale del Brano: 🔒 Bloccato da **{cur_lock.locked_by_name}** ({cur_lock.locked_by_email}) - alle ore {cur_lock.locked_at}")
    else:
        st.success("Stato Attuale del Brano: 🔓 Libero per l'editing")

    if st.button("Sblocco Forzato Amministrativo (Admin Force Unlock)"):
        lock_mgr.release_lock(test_song_uuid, "admin@band.org", force=True)
        st.success("Lock rilasciato forzatamente dall'amministratore.")
        st.rerun()
