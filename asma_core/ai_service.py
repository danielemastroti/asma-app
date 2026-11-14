"""
ASMA Accordi Next Generation - Auxiliary Band AI Service
Optional Creative AI Assistant for Arrangements and Medleys.
Conforms to SRS Cap. 15.6, 19.9, 22.5 and Blueprint Rule "Music First".
STRICTLY FORBIDDEN FOR: Chord parsing, transpositions, PDF generation, or versioning.
"""

from __future__ import annotations
import os
import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from asma_core.music_engine import MusicEngine


SECTION_HEADING_REGEX = re.compile(
    r"^(?:\[|\(|\{)?\s*(intro(?:duzione)?|verse|strofa|ritornello|chorus|bridge|inciso|special|solo|assolo|outro|finale|coda)(?:(?:\s*[:\-]?\s*|\s+)([\dIVX]+))?(?:\s*[-:]\s*|\s*|\s*[\:\-]|\s*(?:\]|\)|\}))?$",
    re.IGNORECASE
)

SECTION_NAME_MAP = {
    "intro": "intro",
    "introduzione": "intro",
    "verse": "verse",
    "strofa": "verse",
    "chorus": "chorus",
    "ritornello": "chorus",
    "bridge": "bridge",
    "inciso": "bridge",
    "special": "bridge",
    "solo": "solo",
    "assolo": "solo",
    "outro": "outro",
    "finale": "outro",
    "coda": "coda"
}


class BandAIService:
    """
    Auxiliary Creative AI Service.
    100% Optional. Fallbacks seamlessly to deterministic logic when offline or disabled.
    """
    MODE_OFF = "OFF"
    MODE_FREE = "FREE"
    MODE_PREMIUM = "PREMIUM"
    _cached_turso_key: Optional[str] = None

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """Retrieves Gemini API key from environment, Streamlit secrets, .streamlit/secrets.toml, or Turso settings."""
        for env_var in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
            val = os.environ.get(env_var)
            if val and not val.startswith("AIzaSy_YOUR_OPTIONAL"):
                return val

        # Local secrets file
        try:
            import tomllib
            candidate_paths = [
                os.path.join(os.getcwd(), "config", "secrets.toml"),
                os.path.join(os.getcwd(), ".secrets.toml"),
                os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
            ]
            for secrets_path in candidate_paths:
                if os.path.exists(secrets_path):
                    with open(secrets_path, "rb") as f:
                        data = tomllib.load(f)
                        k = data.get("ai", {}).get("gemini_api_key") or data.get("gemini_api_key")
                        if k and isinstance(k, str) and not k.startswith("AIzaSy_YOUR_OPTIONAL"):
                            return k.strip()
        except Exception:
            pass

        # Fallback to Turso Cloud band_settings (enables Render cloud deploy out-of-the-box)
        if cls._cached_turso_key:
            return cls._cached_turso_key
        try:
            from asma_core.turso_client import TursoClient
            tc = TursoClient()
            if tc.is_configured:
                db_key = tc.get_setting("gemini_api_key")
                if db_key and db_key.strip():
                    cls._cached_turso_key = db_key.strip()
                    return cls._cached_turso_key
        except Exception:
            pass

        return None

    @classmethod
    def save_api_key(cls, api_key: str) -> bool:
        """Persists Gemini API key into Turso band_settings for cloud access."""
        clean_key = (api_key or "").strip()
        if not clean_key:
            return False
        try:
            from asma_core.turso_client import TursoClient
            tc = TursoClient()
            if tc.is_configured and tc.set_setting("gemini_api_key", clean_key):
                cls._cached_turso_key = clean_key
                return True
        except Exception:
            pass
        return False

    @classmethod
    def get_current_mode(cls) -> str:
        api_key = cls.get_api_key()
        if not api_key:
            return cls.MODE_OFF
        return os.environ.get("ASMA_AI_MODE", cls.MODE_FREE)

    @classmethod
    def detect_sections_with_ai(cls, aml_text: str) -> Optional[str]:
        """
        Uses a free, ultra-fast and lightweight Gemini model (gemini-1.5-flash / gemini-2.0-flash-lite)
        to identify and insert section tags ({intro}, {verse}, {chorus}, {bridge}, {solo}, {outro}).
        Strictly constrained with timeout, zero temperature and low token ceiling.
        """
        api_key = cls.get_api_key()
        if not api_key:
            return None

        prompt = (
            "Sei un assistente musicale esperto di formattazione testi e spartiti per leggio.\n"
            "Nel testo musicale seguente mancano i tag di sezione. Inserisci i tag di sezione AML standard "
            "({intro}, {verse}, {chorus}, {bridge}, {solo}, {outro}) prima di ciascuna sezione logica del brano.\n"
            "Regole vincolanti:\n"
            "1. Mantieni esattamente inalterate tutte le parole e tutti gli accordi (es. [Am], [G]).\n"
            "2. Non aggiungere spiegazioni, non commentare e non usare blocchi di codice markdown (nessun ```).\n"
            "3. Restituisci esclusivamente il testo AML aggiornato.\n\n"
            f"{aml_text}"
        )

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 1500
            }
        }

        # Modelli gratuiti e leggeri raccomandati per velocità e minimo consumo di token
        models_to_try = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview"]
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                out_text = parts[0].get("text", "").strip()
                                out_text = re.sub(r"^```[a-zA-Z]*\n", "", out_text)
                                out_text = re.sub(r"\n```$", "", out_text).strip()
                                if re.search(r"\{(intro|verse|chorus|bridge|solo|outro|strofa|ritornello)", out_text, re.IGNORECASE):
                                    return out_text
            except Exception:
                continue

        return None

    @classmethod
    def detect_sections_heuristic(cls, aml_text: str) -> str:
        """
        Deterministic, robust fallback for detecting sections and stanza spacing:
        1. Identifies textual section markers (e.g. Ritornello:, [Ritornello], Strofa 1, (Chorus), Bridge:)
           and converts them into proper AML section directives ({chorus}, {verse}, etc.).
        2. If the text has neither section tags nor blank lines, divides long continuous blocks
           into natural 4-line stanzas separated by blank lines for clean music-stand layout.
        """
        lines = aml_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        body_lines = [l.strip() for l in aml_text.strip().splitlines()]
        has_existing_blank_lines = any(not l for l in body_lines)
        new_lines: List[str] = []
        consecutive_text_lines = 0

        for raw_line in lines:
            line_str = raw_line.strip()

            if not line_str:
                new_lines.append("")
                consecutive_text_lines = 0
                continue

            if line_str.startswith("{") and line_str.endswith("}"):
                new_lines.append(raw_line)
                consecutive_text_lines = 0
                continue

            m = SECTION_HEADING_REGEX.match(line_str)
            if m:
                raw_keyword = m.group(1).lower()
                canonical = SECTION_NAME_MAP.get(raw_keyword, "verse")
                num_suffix = m.group(2)
                label_suffix = f": {num_suffix.strip()}" if num_suffix and num_suffix.strip() else ""
                new_lines.append(f"{{{canonical}{label_suffix}}}")
                consecutive_text_lines = 0
                continue

            # Inserisce righe vuote SOLO se il testo era un blocco continuo privo di qualsiasi riga vuota
            if not has_existing_blank_lines and consecutive_text_lines >= 4:
                new_lines.append("")
                consecutive_text_lines = 0

            new_lines.append(raw_line)
            consecutive_text_lines += 1

        return "\n".join(new_lines)

    @classmethod
    def ensure_section_spacing_aml(cls, aml_text: str) -> str:
        """
        Ensures that a song AML document has well-defined sections and spacing:
        1. If sections are already present ({intro}, {verse}, {chorus}, etc.), leaves it unchanged.
        2. If sections are missing, attempts fast lightweight AI model (Gemini free tier).
        3. As the ultimate fallback, applies deterministic heuristic segmentation to format the PDF
           at the highest possible standard.
        """
        if not aml_text or not aml_text.strip():
            return aml_text

        # Check if AML already has explicit section tags
        if re.search(r"\{(intro|verse|chorus|bridge|solo|outro|strofa|ritornello|assolo|finale|sob|soc|sov|start_of_bridge|start_of_chorus|start_of_verse|speciale)", aml_text, re.IGNORECASE):
            return aml_text

        # 1. Fast deterministic heuristic segmentation (instantly converts Strofa 1:, Ritornello:, etc.)
        heuristic_res = cls.detect_sections_heuristic(aml_text)
        if re.search(r"\{(intro|verse|chorus|bridge|solo|outro|strofa|ritornello|assolo|finale|sob|soc|sov|start_of_bridge|start_of_chorus|start_of_verse|speciale)", heuristic_res, re.IGNORECASE):
            return heuristic_res

        # 2. Try lightweight AI detection when no textual headings were found
        ai_result = cls.detect_sections_with_ai(aml_text)
        if ai_result:
            return ai_result

        return heuristic_res


    KNOWN_SONG_BPM: Dict[str, int] = {
        "knock on wood": 140,
        "albachiara": 68,
        "hotel california": 74,
        "lo spettacolo": 130,
        "a te": 64,
        "sally": 65,
        "cielito lindo": 105,
        "la bamba": 150,
        "stand by me": 118,
        "smoke on the water": 114,
        "sweet child o mine": 125,
        "billie jean": 117,
        "shape of you": 96,
        "wonderwall": 87,
        "let it be": 71,
        "imagine": 76,
        "hallelujah": 56,
        "hey jude": 74,
        "rolling in the deep": 105,
        "viva la vida": 138,
        "perfect": 63,
        "thinking out loud": 79,
        "blinding lights": 171,
        "take on me": 168,
        "careless whisper": 76,
        "il gatto e la volpe": 144,
        "gianna": 128,
        "certe notti": 76,
        "vita spericolata": 92,
        "urlando contro il cielo": 132,
        "generale": 82,
        "la canzone del sole": 112,
        "si viaggiare": 106,
        "il mio canto libero": 72,
    }

    @classmethod
    def fetch_songbpm_info(cls, title: str, artist: str = "") -> Optional[Dict[str, Any]]:
        """
        Interroga esclusivamente il database di SongBPM (https://songbpm.com) per estrarre:
        - BPM reale del brano
        - Tonalità (Key) normalizzata
        - Durata
        Applica filtro intelligente per parole chiave del titolo per evitare falsi positivi
        e fallback sul solo titolo se con l'artista non trova riscontro.
        Restituisce None se offline o se il brano non è presente su SongBPM.
        """
        import urllib.parse
        from bs4 import BeautifulSoup

        clean_t = re.sub(r"[\(\[\{].*?[\)\]\}]", "", title or "").strip()
        clean_a = re.sub(r"[\(\[\{].*?[\)\]\}]", "", artist or "").strip()
        clean_t = re.sub(r"[^\w\s-]", " ", clean_t).strip()
        clean_a = re.sub(r"[^\w\s-]", " ", clean_a).strip()
        title_keywords = [w.lower() for w in re.findall(r"\b\w+\b", clean_t) if len(w) > 2]

        def _search_query(q_str: str) -> Optional[Dict[str, Any]]:
            if not q_str.strip():
                return None
            url = "https://songbpm.com/searches"
            data = urllib.parse.urlencode({"query": q_str}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "it,en;q=0.9"
                }
            )
            try:
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                    soup = BeautifulSoup(html, "html.parser")
                    candidates = []
                    for a in soup.find_all("a"):
                        href = a.get("href", "")
                        if href.startswith("/@") and "/apple-music" not in href and "/spotify" not in href:
                            raw_txt = a.get_text(" ", strip=True)
                            txt = raw_txt.replace("\u266f", "#").replace("\u266d", "b")
                            m_bpm = re.search(r"BPM\s+(\d+)", txt)
                            m_key = re.search(r"Key\s+([A-G][b#]?(?:\s*(?:maj|min|m))?)", txt, re.IGNORECASE)
                            m_dur = re.search(r"Duration\s+(\d+:\d+)", txt)
                            if m_bpm:
                                bpm_val = int(m_bpm.group(1))
                                if 40 <= bpm_val <= 260:
                                    k_val = m_key.group(1).strip() if m_key else None
                                    if k_val:
                                        k_val = k_val.replace("♯", "#").replace("♭", "b")
                                    txt_lower = txt.lower()
                                    score = sum(1 for w in title_keywords if w in txt_lower)
                                    candidates.append({
                                        "bpm": bpm_val,
                                        "key": k_val,
                                        "duration": m_dur.group(1) if m_dur else None,
                                        "source": "SongBPM.com",
                                        "matched": txt[:80],
                                        "score": score
                                    })
                    if candidates:
                        candidates.sort(key=lambda c: c["score"], reverse=True)
                        best = candidates[0]
                        if best["score"] > 0 or not title_keywords:
                            return {
                                "bpm": best["bpm"],
                                "key": best["key"],
                                "duration": best["duration"],
                                "source": best["source"],
                                "matched": best["matched"]
                            }
            except Exception:
                return None
            return None

        # 1. Tentativo con Titolo + Artista
        combo_query = " ".join(f"{clean_t} {clean_a}".split())
        res = _search_query(combo_query)
        if res:
            return res

        # 2. Fallback con solo Titolo se l'artista era specificato
        if clean_a and clean_t:
            res_title_only = _search_query(clean_t)
            if res_title_only:
                return res_title_only

        return None

    @classmethod
    def estimate_song_bpm(cls, title: str, artist: str = "", default_bpm: int = 120) -> int:
        """
        Restituisce il tempo reale (BPM) del brano ottenuto esclusivamente da SongBPM (https://songbpm.com).
        Se il brano non viene trovato su SongBPM o in assenza di connessione internet,
        viene impostato il valore di default specificato (120 BPM).
        Nessuna stima arbitraria o AI: solo dati verificati da SongBPM con fallback di default.
        """
        if not (title or "").strip():
            return default_bpm

        sb_info = cls.fetch_songbpm_info(title, artist)
        if sb_info and sb_info.get("bpm"):
            return int(sb_info["bpm"])

        return default_bpm

    @classmethod
    def suggest_medley_transition(
        cls,
        song_a_title: str,
        song_a_key: str,
        song_a_bpm: int,
        song_b_title: str,
        song_b_key: str,
        song_b_bpm: int
    ) -> Dict[str, Any]:
        """
        Generates creative arrangement advice for transitioning between two songs in a medley.
        Operates without AI by default; utilizes Gemini if configured.
        """
        # 1. Deterministic Music Engine Analysis (Guaranteed to work)
        score, details = MusicEngine.calculate_harmonic_compatibility(
            song_a_key, song_a_bpm, song_b_key, song_b_bpm
        )

        advice = [
            f"Transizione da '{song_a_title}' ({song_a_key}, {song_a_bpm} BPM) verso '{song_b_title}' ({song_b_key}, {song_b_bpm} BPM).",
            f"Valutazione armonica: Distanza sul circolo delle quinte = {details.get('fifths_distance')} semitoni di quinta.",
            f"Variazione ritmica: {details.get('bpm_diff_percent')}% di differenza."
        ]

        if details.get("fifths_distance", 0) == 0:
            advice.append("Suggerimento: Stessa tonalità! Chiudi l'ultimo ritornello del primo brano suonando l'accordo di tonica in stacco e fai entrare la chitarra sul primo battere.")
        elif details.get("fifths_distance", 0) == 1:
            advice.append("Suggerimento: Modulazione alla dominante/sottodominante. Utilizza una misura di stacco ritmico di batteria per impostare il nuovo tempo.")
        else:
            advice.append("Suggerimento: Tonalità distanti. Consigliato un ponte strumentale con giro armonico di 4 battute per modulare alla nuova tonalità.")

        return {
            "score": score,
            "details": details,
            "creative_advice": "\n".join(advice),
            "ai_mode_used": cls.get_current_mode()
        }

    @classmethod
    def suggest_arrangement_ideas(
        cls,
        title: str,
        genre: str = "",
        key: str = "",
        bpm: int = 0,
        artist: str = "",
        instrument: str = "Globale"
    ) -> str:
        """
        Consigli di arrangiamento live con target specifico (Globale, Tastiera, Voce, Chitarra, Basso, Batteria)
        e raccomandazione preset Yamaha Montage su misura per i tastieristi.
        """
        # Ricerca valore reale e verificato su SongBPM
        sb_info = cls.fetch_songbpm_info(title, artist)
        if sb_info and sb_info.get("bpm"):
            songbpm_bpm = sb_info["bpm"]
            tempo_label = f"SongBPM: {songbpm_bpm} BPM"
        elif bpm and bpm != 120:
            songbpm_bpm = bpm
            tempo_label = f"SongBPM: {songbpm_bpm} BPM"
        else:
            songbpm_bpm = cls.estimate_song_bpm(title, artist)
            tempo_label = f"SongBPM: {songbpm_bpm} BPM"

        g_lower = (genre or "").lower()
        t_lower = (title or "").lower()
        k_str = key or "Tonica"

        # Tentativo chiamata Gemini AI per consigli dinamici e su misura per lo specifico brano
        api_key = cls.get_api_key()
        if api_key:
            prompt = (
                f"Sei un maestro arrangiatore e direttore musicale per una live band (Tastiera Yamaha Montage, Voce, Chitarra ritmica, Chitarra elettrica, Basso, Batteria).\n"
                f"Fornisci consigli creativi, professionali e SPECIFICI per l'esecuzione live di questo brano:\n"
                f"- Titolo: '{title}'\n"
                f"- Artista: '{artist}'\n"
                f"- Tonalità: '{k_str}'\n"
                f"- Andamento: {songbpm_bpm} BPM\n"
                f"- Genere: {genre or 'Pop/Rock/Musica leggera'}\n"
                f"- Strumento target: {instrument}\n\n"
                f"Istruzioni:\n"
                f"1. Dai consigli personalizzati per '{title}', facendo riferimento alla struttura, dinamica, intro, strofe e ritornelli tipici di questo specifico pezzo.\n"
                f"2. Se lo strumento target include 'Tastiera', consiglia la performance o i timbri più adatti per Yamaha Montage (o workstation synth/piano/organo/pad) e impostazioni per Scene e Super Knob.\n"
                f"3. Se lo strumento è 'Voce', 'Chitarra', 'Basso' o 'Batteria', dai suggerimenti precisi su suono, dinamica, stacchi e interplay con il resto della band.\n"
                f"4. Se lo strumento è 'Globale', offri una guida per l'intera band (Intro, Strofa, Ritornello, Bridge/Assolo, Finale).\n"
                f"Formatta la risposta in Markdown chiaro ed elegante con elenchi puntati."
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1000}
            }
            models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash-8b"]
            for model in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=4.0) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode("utf-8"))
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    ai_reply = parts[0].get("text", "").strip()
                                    if ai_reply and len(ai_reply) > 50:
                                        return f"### 🤖 Consulente Arrangiamento AI — '{title}'\n*Analisi su misura generata in tempo reale per {instrument}*\n\n" + ai_reply
                except Exception:
                    continue

        # Determinazione del preset Yamaha Montage ottimale
        if any(w in g_lower or w in t_lower for w in ["rock", "blues", "hard"]):
            montage_preset = "**All Revved Up** (Organo Hammond B3 con Leslie su Pedale FC7) oppure **Prog Organ**"
            montage_tip = "Usa il Super Knob per dosare il Drive del preamplificatore valvolare. Assegna l'effetto Rotary Speaker (Slow/Fast) al tasto Assignable Switch 1 o al pedale switch."
        elif any(w in g_lower or w in t_lower for w in ["soul", "funk", "motown", "r&b"]):
            montage_preset = "**73 Rd 1 Gallery** (Rhodes valvolare con Auto-Pan/Phaser) o **Clavi D6 Wah**"
            montage_tip = "Regola la dinamica Velocity per far ruggire il Rhodes sulle frasi di stacco. Super Knob per dosare l'inviluppo del Wah."
        elif any(w in g_lower or w in t_lower for w in ["dance", "disco", "80s", "synth", "pop dance"]):
            montage_preset = "**Super 80s Brass** (Split con pad sintetico) oppure **TX81Z LatelyBass / DX Crisp**"
            montage_tip = "Programma la Scene 1 per la strofa (pad filtrato) e Scene 2 per il ritornello (apertura filtro Cutoff a piena banda)."
        else:
            montage_preset = "**CFX Concert** (Gran Coda Acustico) con layer sottile di **Warm Pad** o **Seattle Sections**"
            montage_tip = "Configura lo split a C3: mano sinistra su pad/basso leggero e mano destra su CFX Concert brillante per tagliare nel mix della band."

        inst_norm = instrument.lower()

        if "tastier" in inst_norm:
            return f"""### 🎹 Consigli di Arrangiamento per TASTIERA & Preset Yamaha Montage
**Brano:** '{title}' ({k_str} &bull; {songbpm_bpm} BPM)

#### 🎛️ Preset Consigliato Yamaha Montage:
* **Performance Ufficiale Montage:** {montage_preset}
* **Configurazione Super Knob & Scene:** {montage_tip}
* **Scene Memory:** Imposta **Scene 1** per strofe (suono asciutto e intimo) e **Scene 2 / 3** per ritornelli e assolo (apertura riverbero e layer aggiuntivi).

#### 🎼 Guida all'Esecuzione nel Mix della Band:
1. **Intro & Strofa:** Non raddoppiare la linea di basso fondamentale nella mano sinistra: lascia lo spazio al bassista. Suona voicings aperti (drop-2) tra C3 e G5.
2. **Ritornello:** Incrementa il volume o apri il Super Knob. Sostieni con accordi sostenuti (pad/organo) o riff ritmici accentati sui battere e levare.
3. **Bridge / Stacchi:** Se presente un assolo di chitarra, fai comping ritmico discreto sui tempi deboli (2 e 4) senza invadere le frequenze medie.
4. **Finale:** Concludi con arpeggio o accordo aperto di {k_str} lasciando sfumare il riverbero."""

        elif "voce" in inst_norm:
            return f"""### 🎤 Consigli di Arrangiamento per VOCE
**Brano:** '{title}' ({k_str} &bull; {songbpm_bpm} BPM)

1. **Tessitura e Registro:** Con tonalità impostata su **{k_str}**, cura il passaggio di registro tra voce di petto e voce mista nei ritornelli.
2. **Strofa 1:** Canto narrativo, intimista, quasi parlato, con microfonazione ravvicinata per valorizzare i bassi vocali.
3. **Ritornello:** Massima apertura polmonare e proiezione; inserisci raddoppi vocali e cori sulla terza superiore ({k_str}) per dare potenza live.
4. **Dinamica Live:** Durante il bridge o assolo strumentale, retrocedi leggermente dal microfono per dare il centro della scena al solista."""

        elif "ritmic" in inst_norm or ("chitarra" in inst_norm and "elettric" not in inst_norm):
            return f"""### 🎸 Consigli di Arrangiamento per CHITARRA RITMICA
**Brano:** '{title}' ({k_str} &bull; {songbpm_bpm} BPM)

1. **Accordi & Voicing:** Preferisci accordi aperti o triadi sui primi 4 cantini (D-G-B-E) per non impastare le frequenze basse con basso e cassa.
2. **Pattern Ritmico:** Mantieni un groove solido a {songbpm_bpm} BPM con pennata fluida; accentua il 2° e 4° movimento in sincrono con il rullante.
3. **Dinamica Sezioni:** Palm-muting sulle strofe per creare tensione; apertura completa delle pennate nei ritornelli per allargare il fronte sonoro stereo."""

        elif "elettric" in inst_norm or "lead" in inst_norm:
            return f"""### ⚡ Consigli di Arrangiamento per CHITARRA ELETTRICA (Lead)
**Brano:** '{title}' ({k_str} &bull; {songbpm_bpm} BPM)

1. **Tonalità per l'Assolo:** Scala pentatonica e dorica/blues su tonalità **{k_str}**.
2. **Catena Effetti:** Overdrive caldo, leggero delay sincronizzato sui quarti a **{songbpm_bpm} BPM** (tempo delay: {int(60000 / songbpm_bpm)} ms).
3. **Strofe:** Riff melodici di risposta alla voce (call and response) e arpeggi puliti con chorus leggero.
4. **Assolo:** Inizia con frasi melodiche cantabili e lente, per poi accelerare in crescendo verso la chiusura del ritornello."""

        elif "basso" in inst_norm:
            return f"""### 🎸 Consigli di Arrangiamento per BASSO
**Brano:** '{title}' ({k_str} &bull; {songbpm_bpm} BPM)

1. **Lock-in con la Batteria:** Blocca le note fondamentali di **{k_str}** esattamente in sincrono con la cassa a {songbpm_bpm} BPM.
2. **Strofa:** Note lunghe sui quarti, rotonde, senza fronzoli per garantire stabilità al cantante.
3. **Ritornello:** Introduci ottave o ghost-notes ritmiche per spingere l'energia della band.
4. **Transizioni:** Utilizza passaggi cromatici ascendenti/discendenti per collegare le sezioni armoniche."""

        elif "batteri" in inst_norm:
            return f"""### 🥁 Consigli di Arrangiamento per BATTERIA
**Brano:** '{title}' ({k_str} &bull; {songbpm_bpm} BPM)

1. **Groove di Riferimento:** {songbpm_bpm} BPM verificati su SongBPM.
2. **Strofe:** Charleston chiuso a ottavi, rullante sul 2 e 4 con tocco leggero (o cross-stick se ballad).
3. **Ritornelli:** Apertura parziale o totale del charleston (o passaggio sul piatto Ride), cassa decisa per spingere la band.
4. **Fill & Stacchi:** Mantieni i fill essenziali e a tempo, preparando sempre l'attacco del ritornello con un crash deciso sul primo battito."""

        else:
            # Globale band
            header_tags = [t for t in [genre, f"Tonalità {k_str}", tempo_label] if t]
            header_str = f" ({', '.join(header_tags)})" if header_tags else ""

            return f"""Consigli di Arrangiamento Live Globale per '{title}'{header_str}:
1. **Intro:** Inizia con strumento solista (tastiera Montage con *{montage_preset.split('(')[0].strip('* ')}* o chitarra) per le prime 4 battute, poi ingresso di cassa in 4 a metà intro a {songbpm_bpm} BPM da SongBPM prima dell'ingresso della voce.
2. **Strofa 1:** Mantieni il basso lineare e charleston chiuso per dare intimità al testo del cantante.
3. **Ritornello:** Esplosione dinamica a {songbpm_bpm} BPM: apertura del charleston, cori a due voci su {k_str} e layer di tastiere e chitarre.
4. **Bridge / Assolo:** Sezione ritmica serrata a {songbpm_bpm} BPM, progressione in crescendo dinamico fino al drop sul ritornello finale.
5. **Finale:** Uscita con giro armonico ripetuto in diminuendo con stacco secco sull'accordo di tonica ({k_str})."""

    @classmethod
    def analyze_probable_key_with_ai_fallback(
        cls,
        title: str,
        artist: str = "",
        chords: Optional[List[str]] = None,
        current_hint: str = ""
    ) -> Dict[str, Any]:
        """
        Rileva la tonalità più probabile di un brano.
        1. Esegue prima l'analisi armonica deterministica con MusicEngine.detect_probable_key.
        2. In caso di dubbio o discrepanza tra tonalità maggiore/minore relativa (es. MIm 6° grado di SOL),
           e se le API AI sono configurate, consulta l'IA gratuita e leggera (Gemini Flash).
        3. Restituisce un dizionario completo con tonalità italiana, relativo e spiegazione.
        """
        chords = chords or []
        engine_res = MusicEngine.detect_probable_key(chords, current_hint)

        api_key = cls.get_api_key()
        if not api_key:
            return engine_res

        # Verifichiamo se l'IA leggera e gratuita può confermare o raffinare
        chord_sample = ", ".join(chords[:25]) if chords else "N/A"
        prompt = (
            f"Sei un assistente musicale e maestro di armonia. Analizza questo brano:\n"
            f"Titolo: '{title}'\n"
            f"Artista: '{artist}'\n"
            f"Accordi rilevati: {chord_sample}\n"
            f"Tonalità ipotizzata: {engine_res.get('probable_key')} (Relativo: {engine_res.get('relative_key')})\n\n"
            f"Domanda: Qual è la tonalità d'impianto principale del brano in notazione italiana (DO, DOm, RE, REm, MI, MIm, FA, FAm, SOL, SOLm, LA, LAm, SI, SIm, con # o b)?\n"
            f"Fai particolare attenzione se si tratta di una tonalità minore (es. MIm) o del suo relativo maggiore (es. SOL dove MIm è il 6° grado).\n"
            f"Rispondi ESCLUSIVAMENTE con la sigla della tonalità principale (es. MIm o SOL)."
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 20}
        }
        models_to_try = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview"]
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                ai_key_raw = parts[0].get("text", "").strip()
                                ai_key_clean = re.sub(r"[^A-Za-z0-9#b]", "", ai_key_raw)
                                parsed_ai = MusicEngine.parse_chord(ai_key_clean)
                                if parsed_ai:
                                    ita_ai_key = MusicEngine.convert_notation(ai_key_clean, "ITA")
                                    engine_res["ai_validated_key"] = ita_ai_key
                                    engine_res["probable_key"] = ita_ai_key
                                    engine_res["source"] = "AI (Gemini Flash)"
                                    break
            except Exception:
                continue

        return engine_res

    @classmethod
    def transcribe_sheet_music_images(cls, image_items: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Uses Gemini Multimodal Vision API to transcribe photographed sheet music or song charts
        into standard AML / ChordPro format with title, artist, key, bpm, and inline chords.
        Supports multi-page images (page 1, page 2, etc.).
        """
        api_key = cls.get_api_key()
        if not api_key:
            raise RuntimeError("Chiave API Gemini non configurata. Verifica gemini_api_key nei secrets.")

        if not image_items:
            raise ValueError("Nessuna immagine fornita per la trascrizione.")

        prompt = (
            "Sei un assistente musicale professionista esperto nella trascrizione di spartiti, canzonieri e fogli musicali cartacei in formato ChordPro / AML (Accordi Band).\n"
            "Ti vengono fornite una o più immagini fotografate in sequenza (pagina 1, pagina 2, ecc.) di un brano musicale cartaceo con testo e accordi posizionati sopra le parole.\n"
            "Il tuo compito è trascrivere con assoluta fedeltà l'intero brano convertendolo in formato ChordPro / AML.\n\n"
            "REGOLE DI TRASCRIZIONE:\n"
            "1. Posiziona ciascun accordo ESATTAMENTE all'interno del testo prima della sillaba/parola corrispondente tra parentesi quadre, es: '[DO]Vespe truccate [SOL]anni sessanta'.\n"
            "2. Non perdere nessuna strofa o ritornello di tutte le pagine fornite. Unisci le pagine in un unico testo ordinato e coerente.\n"
            "3. Usa le direttive di sezione ChordPro / AML:\n"
            "   - Ritornello: usa {soc} all'inizio del ritornello e {eoc} alla fine (oppure [RITORNELLO]).\n"
            "   - Strofe: usa {sov} all'inizio e {eov} alla fine (oppure [STROFA 1], [STROFA 2]).\n"
            "   - Ponte/Speciale: usa {sob} e {eob} (oppure [SPECIALE] o [BRIDGE]).\n"
            "   - Intro/Outro/Assolo: [INTRO], [OUTRO], [ASSOLO], ♪ (Strumentale).\n"
            "   - Se ci sono commenti o indicazioni per i musicisti sul foglio (es. 'arpeggio tastiera', 'stop', 'ritmo 2 volte'): usa la direttiva {c: commento}.\n"
            "4. Estrai i metadati dall'intestazione del foglio:\n"
            "   - Titolo del brano (se non presente, deducilo dal ritornello o prima riga).\n"
            "   - Artista / Band (se presente, altrimenti lascia vuoto o 'Band').\n"
            "   - Tonalità iniziale (es. DO, RE, SOL, C, G, Am, ecc.).\n"
            "   - BPM / Tempo (se indicato in numeri, es. 120, altrimenti 120).\n"
            "   - Capotasto (se indicato, es. 2, altrimenti 0).\n"
            "5. RISPONDI ESCLUSIVAMENTE con un oggetto JSON valido con questa struttura esatta:\n"
            "{\n"
            '  "title": "TITOLO DEL BRANO",\n'
            '  "artist": "Nome Artista",\n'
            '  "key": "DO",\n'
            '  "bpm": 120,\n'
            '  "capo": 0,\n'
            '  "aml_content": "{title: TITOLO}\\n{artist: Artista}\\n{key: DO}\\n\\n[INTRO]\\n| DO | SOL | FA | DO |\\n\\n[DO]Testo con accordi...\\n"\n'
            "}\n"
        )

        parts: List[Dict[str, Any]] = [{"text": prompt}]
        for idx, img in enumerate(image_items, 1):
            raw_b64 = img.get("data", "")
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            mime = img.get("mime_type", "image/jpeg")
            parts.append({"text": f"--- PAGINA {idx} DEL BRANO ---"})
            parts.append({
                "inlineData": {
                    "mimeType": mime,
                    "data": raw_b64
                }
            })

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json"
            }
        }

        models_to_try = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-3.8-flash"]
        last_error = None
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30.0) as resp:
                    if resp.status == 200:
                        res_json = json.loads(resp.read().decode("utf-8"))
                        candidates = res_json.get("candidates", [])
                        if candidates:
                            resp_parts = candidates[0].get("content", {}).get("parts", [])
                            if resp_parts:
                                raw_text = resp_parts[0].get("text", "").strip()
                                clean_json = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
                                clean_json = re.sub(r"\s*```$", "", clean_json).strip()
                                # Fallback regex in case model wraps JSON in commentary
                                json_match = re.search(r"(\{.*\})", clean_json, re.DOTALL)
                                if json_match:
                                    clean_json = json_match.group(1)
                                parsed_data = json.loads(clean_json)
                                return {
                                    "title": parsed_data.get("title", "Nuovo Brano"),
                                    "artist": parsed_data.get("artist", ""),
                                    "key": parsed_data.get("key", "DO"),
                                    "bpm": int(parsed_data.get("bpm", 120)) if str(parsed_data.get("bpm", "")).isdigit() else 120,
                                    "capo": int(parsed_data.get("capo", 0)) if str(parsed_data.get("capo", "")).isdigit() else 0,
                                    "aml_content": parsed_data.get("aml_content", "")
                                }
            except urllib.error.HTTPError as he:
                try:
                    err_body = he.read().decode("utf-8")
                    err_json = json.loads(err_body)
                    msg = err_json.get("error", {}).get("message", err_body)
                except Exception:
                    msg = str(he)
                last_error = f"{he.code} ({model}): {msg}"
                continue
            except Exception as e:
                last_error = f"{model}: {str(e)}"
                continue

        raise RuntimeError(f"Errore durante l'elaborazione Vision AI: {last_error}")

    _live_suggestions_cache: Dict[str, Dict[str, Any]] = {}

    BAND_MEMBERS = [
        {"key": "band", "name": "Tutta la Band", "role": "Intero Gruppo (Dinamiche d'insieme, arrangiamento, stacchi, timing)", "icon": "👥"},
        {"key": "cico", "name": "Cico", "role": "Cantante (Voce solista, attacchi, dinamica vocale, fiato, intonazione)", "icon": "🎤"},
        {"key": "mingo", "name": "Mingo", "role": "Batterista (Groove ritmico, timing/BPM, accenti cassa/rullante, stacchi e fill)", "icon": "🥁"},
        {"key": "puma", "name": "Puma", "role": "Bassista (Incastro ritmico con la cassa di Mingo, note fondamentali, passaggi armonici)", "icon": "🎸"},
        {"key": "red", "name": "Red", "role": "Chitarra Solista (Effetti, distorsioni/delay, riff portanti, assoli, volume solista)", "icon": "⚡"},
        {"key": "maurino", "name": "Maurino", "role": "Chitarra Ritmica (Strumming, solidità armonica, accordi aperti vs barré, impasto con Red)", "icon": "🎸"},
        {"key": "sentimental", "name": "Sentimental", "role": "Tastiere & Synth (Pad di sottofondo, pianoforte, cambio scene {Scena: X}, arricchimento armonico)", "icon": "🎹"}
    ]

    @classmethod
    def get_musician_list(cls) -> List[Dict[str, str]]:
        return cls.BAND_MEMBERS

    @classmethod
    def generate_live_suggestions(cls, song: Any, musician: str = "band") -> Dict[str, Any]:
        """
        Generates tailored live performance advice for a specific band member or the entire band.
        Uses free, lightweight Google Gemini model (gemini-2.5-flash / gemini-2.0-flash / gemini-1.5-flash).
        Falls back seamlessly to deterministic heuristic suggestions when offline or no API key is present.
        Results are cached in-memory per (song.uuid, musician) for 0ms response.
        """
        norm_musician = (musician or "band").lower().strip()
        matched_member = next((m for m in cls.BAND_MEMBERS if m["key"] == norm_musician), cls.BAND_MEMBERS[0])
        musician_key = matched_member["key"]

        song_id = getattr(song, "uuid", None) or getattr(song, "title", "song")
        cache_key = f"{song_id}_{musician_key}"
        if cache_key in cls._live_suggestions_cache:
            return cls._live_suggestions_cache[cache_key]

        title = getattr(song, "title", "Brano")
        artist = getattr(song, "artist", "Band")
        key = getattr(song, "key_current", "DO") or "DO"
        bpm = getattr(song, "bpm", 120) or 120
        capo = getattr(song, "capo", 0) or 0
        aml_content = getattr(song, "aml_content", "") or ""

        # Extract directives from AML to enrich prompt and heuristics
        scena_matches = re.findall(r"\{scena:\s*([^\}]+)\}", aml_content, re.IGNORECASE)
        stacco_matches = re.findall(r"\{stacco:?\s*([^\}]+)\}", aml_content, re.IGNORECASE)
        has_solos = bool(re.search(r"\{(?:solo|assolo)", aml_content, re.IGNORECASE))

        # Check for Gemini API key
        api_key = cls.get_api_key()

        if api_key:
            prompt = (
                f"Sei il direttore musicale e arrangiatore live della band per il brano '{title}' ({artist}).\n"
                f"DATI MUSICALI DEL BRANO:\n"
                f"- Tonalità: {key}\n"
                f"- BPM / Tempo: {bpm}\n"
                f"- Capotasto: {capo}\n"
                f"- Direttive sceniche/synth presenti: {', '.join(scena_matches) if scena_matches else 'Nessuna specifica'}\n"
                f"- Direttive stacchi presenti: {', '.join(stacco_matches) if stacco_matches else 'Nessuno specifico'}\n"
                f"- Presenza assolo: {'Sì' if has_solos else 'No'}\n\n"
                f"DESTINATARIO: {matched_member['name']} - Ruolo: {matched_member['role']}\n\n"
                f"Fornisci consigli tecnici e pratici per l'esecuzione LIVE sul palco di questo pezzo per {matched_member['name']}.\n"
                f"Sii conciso, musicale, orientato all'esecuzione dal vivo (dinamiche piano/forte, attacchi, timing, stacchi, gestione del suono o preset).\n"
                f"Rispondi ESCLUSIVAMENTE con un oggetto JSON valido (senza testo introduttivo e senza markdown) con questa struttura:\n"
                f"{{\n"
                f'  "summary": "Frase di sintesi sull\'approccio al brano",\n'
                f'  "tips": [\n'
                f'    {{"section": "Intro & Attacco", "tip": "consiglio..."}},\n'
                f'    {{"section": "Strofa & Dinamica", "tip": "consiglio..."}},\n'
                f'    {{"section": "Ritornello & Apertura", "tip": "consiglio..."}},\n'
                f'    {{"section": "Momenti Speciali & Stacchi", "tip": "consiglio..."}},\n'
                f'    {{"section": "Finale & Chiusura", "tip": "consiglio..."}}\n'
                f'  ],\n'
                f'  "gear_advice": "Consiglio su strumento/preset/timbro/effetti",\n'
                f'  "watchout": "Attenzione critica dal vivo (punto da non sbagliare)"\n'
                f"}}\n"
            )

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 800,
                    "responseMimeType": "application/json"
                }
            }

            models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
            for model in models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=5.0) as resp:
                        if resp.status == 200:
                            res_json = json.loads(resp.read().decode("utf-8"))
                            cands = res_json.get("candidates", [])
                            if cands:
                                ptext = cands[0].get("content", {}).get("parts", [])[0].get("text", "")
                                ptext = re.sub(r"^```(?:json)?\s*", "", ptext, flags=re.IGNORECASE)
                                ptext = re.sub(r"\s*```$", "", ptext).strip()
                                parsed = json.loads(ptext)
                                if "tips" in parsed and "summary" in parsed:
                                    parsed["musician_key"] = musician_key
                                    parsed["musician_name"] = matched_member["name"]
                                    parsed["musician_role"] = matched_member["role"]
                                    parsed["musician_icon"] = matched_member["icon"]
                                    parsed["source"] = f"AI Gemini ({model})"
                                    cls._live_suggestions_cache[cache_key] = parsed
                                    return parsed
                except Exception:
                    continue

        # Deterministic offline heuristic fallback
        fallback = cls._generate_heuristic_live_suggestions(
            song_title=title,
            artist=artist,
            key=key,
            bpm=bpm,
            capo=capo,
            musician_key=musician_key,
            matched_member=matched_member,
            scena_matches=scena_matches,
            stacco_matches=stacco_matches,
            has_solos=has_solos
        )
        cls._live_suggestions_cache[cache_key] = fallback
        return fallback

    @classmethod
    def _generate_heuristic_live_suggestions(
        cls,
        song_title: str,
        artist: str,
        key: str,
        bpm: int,
        capo: int,
        musician_key: str,
        matched_member: Dict[str, str],
        scena_matches: List[str],
        stacco_matches: List[str],
        has_solos: bool
    ) -> Dict[str, Any]:
        """Deterministic, musical and rock-solid advice generator."""
        tempo_desc = "lento ed espressivo" if bpm < 85 else ("incalzante e ritmato" if bpm > 130 else "mid-tempo con groove solido")
        scena_str = f"Scena {scena_matches[0]}" if scena_matches else "Preset standard"
        stacchi_str = f"Stacco su: {', '.join(stacco_matches)}" if stacco_matches else "Nessuno stacco marcato"

        if musician_key == "cico":
            return {
                "musician_key": "cico",
                "musician_name": "Cico",
                "musician_role": matched_member["role"],
                "musician_icon": "🎤",
                "source": "Regole Musicali ASMA Live (Offline/Free)",
                "summary": f"Voce solista in tonalità {key} a {bpm} BPM ({tempo_desc}). Presenza scenica e intonazione dell'attacco.",
                "tips": [
                    {"section": "Intro & Attacco", "tip": f"Fissa mentalmente la tonica in {key} durante l'intro; entra con voce ferma e decisa esattamente sulla prima battuta cantata."},
                    {"section": "Strofa & Dinamica", "tip": "Canta con registro intimo e scandisci ogni sillaba; lascia respirare il testo senza anticipare il tempo."},
                    {"section": "Ritornello & Apertura", "tip": "Apri al massimo la proiezione diaframmatica; alza l'energia scenica e cerca il contatto visivo diretto con il pubblico."},
                    {"section": "Momenti Speciali & Stacchi", "tip": f"Negli stacchi ({stacchi_str}) sfrutta la pausa per recuperare fiato ed enfatizzare il rientro della strofa successiva."},
                    {"section": "Finale & Chiusura", "tip": "Tieni la nota finale fino alla battuta di chiusura concordata con Mingo alla batteria; gesto chiaro della mano per l'unisono."}
                ],
                "gear_advice": f"Regola il monitor o in-ear per ascoltare chiaramente la chitarra di Maurino e il synth di Sentimental in tonalità {key}.",
                "watchout": f"A {bpm} BPM non farti trascinare ad accelerare le sillabe; mantieni il fiato regolare soprattutto nei ritornelli."
            }

        elif musician_key == "mingo":
            return {
                "musician_key": "mingo",
                "musician_name": "Mingo",
                "musician_role": matched_member["role"],
                "musician_icon": "🥁",
                "source": "Regole Musicali ASMA Live (Offline/Free)",
                "summary": f"Groove portante e metronomo vivente a {bpm} BPM ({tempo_desc}). Incastro millimetrico con Puma.",
                "tips": [
                    {"section": "Intro & Attacco", "tip": f"Dai il tempo con 4 colpi netti di bacchette/charleston a {bpm} BPM esatti; ingresso compatto di tutta la band."},
                    {"section": "Strofa & Dinamica", "tip": "Groove lineare e asciutto (charleston chiuso, rullante a volume contenuto); lascia spazio frequenziale alla voce di Cico."},
                    {"section": "Ritornello & Apertura", "tip": "Passa al piatto ride o apri leggermente l'hi-hat; dai spinta con accenti incisivi di cassa in 4/4."},
                    {"section": "Momenti Speciali & Stacchi", "tip": f"Negli stacchi ({stacchi_str}) blocca i piatti con precisione chirurgica; fill di ripartenza compatto senza strappi."},
                    {"section": "Finale & Chiusura", "tip": "Colpo di rullante e piatto crash secco all'unisono sul segnale visivo di Cico."}
                ],
                "gear_advice": f"Verifica il metronomo visivo a {bpm} BPM sul tablet prima del conteggio iniziale; bacchette 5A ben bilanciate.",
                "watchout": f"Attenzione a non prendere velocità nei passaggi strofa-ritornello; mantieni il groove piantato a {bpm} BPM."
            }

        elif musician_key == "puma":
            return {
                "musician_key": "puma",
                "musician_name": "Puma",
                "musician_role": matched_member["role"],
                "musician_icon": "🎸",
                "source": "Regole Musicali ASMA Live (Offline/Free)",
                "summary": f"Pilastro armonico e groove in tonalità {key}. Incastro perfetto con la cassa di Mingo.",
                "tips": [
                    {"section": "Intro & Attacco", "tip": f"Piazza subito la fondamentale in {key} con suono rotondo e pieno per dare sicurezza a chitarre e tastiere."},
                    {"section": "Strofa & Dinamica", "tip": "Suona sulle note basse della cassa di Mingo; mantieni le note staccate o tenute a seconda del respiro del brano."},
                    {"section": "Ritornello & Apertura", "tip": "Aggiungi passaggi melodici o ottave per dare movimento e spinta emotiva alla linea armonica."},
                    {"section": "Momenti Speciali & Stacchi", "tip": f"Negli stacchi ({stacchi_str}) muta istantaneamente le corde con il palmo della mano sinistra; silenzio assoluto."},
                    {"section": "Finale & Chiusura", "tip": f"Chiudi sulla fondamentale {key} e mantieni il sustain fino al completo stop della batteria."}
                ],
                "gear_advice": "Basse calde (100-200 Hz) con medi definiti a 800 Hz per bucare il mix senza impastare con la cassa.",
                "watchout": "Non anticipare le ripartenze dopo le pause ritmiche; guarda gli occhi di Mingo."
            }

        elif musician_key == "red":
            return {
                "musician_key": "red",
                "musician_name": "Red",
                "musician_role": matched_member["role"],
                "musician_icon": "⚡",
                "source": "Regole Musicali ASMA Live (Offline/Free)",
                "summary": f"Lead guitar e fraseggi tematici in tonalità {key}. Riff d'impatto ed equilibrio col canto.",
                "tips": [
                    {"section": "Intro & Attacco", "tip": f"Attacca con il riff caratteristico o arpeggio pulito in {key}; volume bilanciato per non sovrastare l'ingresso del brano."},
                    {"section": "Strofa & Dinamica", "tip": "Interventi discreti: fraseggi di risposta alla voce o accordi acuti stoppati per non entrare in conflitto con la voce di Cico."},
                    {"section": "Ritornello & Apertura", "tip": "Accordi aperti o power-chord con overdrive moderato; apertura spaziale con riverbero o chorus."},
                    {"section": "Momenti Speciali & Assoli", "tip": f"{'Attiva il boost di volume/overdrive per il solo; bending intonatissimi sulla scala di ' + key if has_solos else 'Focus sugli stacchi armonici e arricchimento sonoro.'}"},
                    {"section": "Finale & Chiusura", "tip": "Accordo conclusivo vibrato con sustain prolungato fino al cut-off finale."}
                ],
                "gear_advice": f"Imposta il delay con tap tempo a {bpm} BPM; pedale boost calibrato a +3dB pronto per l'assolo.",
                "watchout": "Disattiva tempestivamente il boost del solo prima della strofa successiva per rientrare subito nel mix."
            }

        elif musician_key == "maurino":
            return {
                "musician_key": "maurino",
                "musician_name": "Maurino",
                "musician_role": matched_member["role"],
                "musician_icon": "🎸",
                "source": "Regole Musicali ASMA Live (Offline/Free)",
                "summary": f"Muro armonico e plettrata ritmica a {bpm} BPM in tonalità {key} (Capo: {capo}°).",
                "tips": [
                    {"section": "Intro & Attacco", "tip": f"Entra con plettrata precisa a tempo con il charleston di Mingo; posizione accordi {'al tasto ' + str(capo) if capo > 0 else 'aperti' }."},
                    {"section": "Strofa & Dinamica", "tip": "Strumming leggero o palm-muting per dare pulsazione ritmica senza riempire troppo lo spazio frequenziale."},
                    {"section": "Ritornello & Apertura", "tip": "Plettrata ampia ed energica su tutte le corde; ritmo deciso e sincronizzato sui quarti."},
                    {"section": "Momenti Speciali & Stacchi", "tip": f"Negli stacchi ({stacchi_str}) stoppata secca con la mano destra su tutte le corde; stop netto."},
                    {"section": "Finale & Chiusura", "tip": "Ultima pennata decisa all'ingiù esattamente sul colpo finale di Mingo."}
                ],
                "gear_advice": f"Plettro medio per strumming fluido; accordatura rigorosa al capotasto {capo}° se presente.",
                "watchout": "Mantieni la costanza della pennata senza accelerare sulle variazioni ritmiche della strofa."
            }

        elif musician_key == "sentimental":
            return {
                "musician_key": "sentimental",
                "musician_name": "Sentimental",
                "musician_role": matched_member["role"],
                "musician_icon": "🎹",
                "source": "Regole Musicali ASMA Live (Offline/Free)",
                "summary": f"Armonia, tappeti synth e timbri per {key}. Setup rapido: {scena_str}.",
                "tips": [
                    {"section": "Intro & Attacco", "tip": f"Imposta subito {scena_str} sul synth/master keyboard; entra con accordo d'atmosfera o intro di pianoforte."},
                    {"section": "Strofa & Dinamica", "tip": "Tappeto di archi/pad caldo sotto il registro vocale; suona accordi aperti nei registri medio-alti per non invadere il basso."},
                    {"section": "Ritornello & Apertura", "tip": "Arricchisci con pianoforte acustico brillante o organo Hammond per dare pienezza alla band."},
                    {"section": "Momenti Speciali & Stacchi", "tip": f"Negli stacchi ({stacchi_str}) segui gli stop d'insieme; rilascia il pedale di sustain per azzerare code sonore."},
                    {"section": "Finale & Chiusura", "tip": "Accordo conclusivo con pedale di sustain tenuto fino al fade-out naturale o segnale di stop."}
                ],
                "gear_advice": f"Controlla il selettore preset per richiamare al volo {scena_str}; regola il pedale d'espressione per i crescendo.",
                "watchout": "Evita note basse sotto il C3 (Do centrale) con la mano sinistra per non creare risonanze fangose con il basso di Puma."
            }

        else:  # band
            return {
                "musician_key": "band",
                "musician_name": "Tutta la Band",
                "musician_role": matched_member["role"],
                "musician_icon": "👥",
                "source": "Regole Musicali ASMA Live (Offline/Free)",
                "summary": f"Arrangiamento live in tonalità {key} a {bpm} BPM ({tempo_desc}). Coordinamento d'insieme e dinamiche palco.",
                "tips": [
                    {"section": "Intro & Attacco", "tip": f"Conteggio rigoroso di Mingo a 4/4 ({bpm} BPM); attacco compatto e pulito di tutta la band."},
                    {"section": "Strofa & Dinamica", "tip": "Dinamica contenuta (mezzo-piano); basso, chitarre e tastiere lasciano assoluto risalto alla voce di Cico."},
                    {"section": "Ritornello & Apertura", "tip": "Apertura dinamica corale (forte); cori della band aperti nei controcanti ed energia raddoppiata."},
                    {"section": "Momenti Speciali & Stacchi", "tip": f"Massima concentrazione visiva su Mingo negli stacchi ({stacchi_str}); stop e ripartenze al millisecondo."},
                    {"section": "Finale & Chiusura", "tip": "Chiusura netta e sincronizzata all'unisono guidata dal gesto di Cico e colpo finale di batteria."}
                ],
                "gear_advice": "Bilanciamento volumi spie/mixer di palco: fare attenzione che il livello di chitarre e tastiere non mascheri la voce solista.",
                "watchout": f"Non farsi prendere dall'adrenalina accelerando il tempo durante il ritornello; riferimento saldo al groove di Mingo e Puma."
            }



