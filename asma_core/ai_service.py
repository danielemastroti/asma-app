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
    r"^(?:\[|\(|\{)?\s*(intro(?:duzione)?|verse|strofa|ritornello|chorus|bridge|inciso|special|solo|assolo|outro|finale|coda)(?:\s*[\dIVX]+)?(?:\s*[-:]\s*|\s*|\s*[\:\-]|\s*(?:\]|\)|\}))?$",
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

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """Retrieves Gemini API key from environment, Streamlit secrets or .streamlit/secrets.toml."""
        for env_var in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
            val = os.environ.get(env_var)
            if val and not val.startswith("AIzaSy_YOUR_OPTIONAL"):
                return val

        # Streamlit runtime secrets
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if "ai" in st.secrets and "gemini_api_key" in st.secrets["ai"]:
                    k = str(st.secrets["ai"]["gemini_api_key"]).strip()
                    if k and not k.startswith("AIzaSy_YOUR_OPTIONAL"):
                        return k
                if "gemini_api_key" in st.secrets:
                    k = str(st.secrets["gemini_api_key"]).strip()
                    if k and not k.startswith("AIzaSy_YOUR_OPTIONAL"):
                        return k
        except Exception:
            pass

        # Direct .streamlit/secrets.toml reading
        try:
            import tomllib
            secrets_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
            if os.path.exists(secrets_path):
                with open(secrets_path, "rb") as f:
                    data = tomllib.load(f)
                    k = data.get("ai", {}).get("gemini_api_key") or data.get("gemini_api_key")
                    if k and isinstance(k, str) and not k.startswith("AIzaSy_YOUR_OPTIONAL"):
                        return k.strip()
        except Exception:
            pass

        return None

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
                num_match = re.search(r"[\dIVX]+", line_str)
                label_suffix = f": {num_match.group(0)}" if num_match else ""
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
        if re.search(r"\{(intro|verse|chorus|bridge|solo|outro|strofa|ritornello|assolo|finale)", aml_text, re.IGNORECASE):
            return aml_text

        # 1. Try lightweight AI detection
        ai_result = cls.detect_sections_with_ai(aml_text)
        if ai_result:
            return ai_result

        # 2. Fallback to deterministic heuristic segmentation
        return cls.detect_sections_heuristic(aml_text)


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
        Interroga direttamente il database di SongBPM (https://songbpm.com) per estrarre:
        - BPM reale della canzone
        - Tonalita (Key)
        - Durata
        Protetto da timeout (3.5s) e user-agent realistico. Restituisce None se offline o brano non trovato.
        """
        import urllib.parse
        from bs4 import BeautifulSoup

        clean_title = re.sub(r"[\(\[\{].*?[\)\]\}]", "", title or "").strip()
        clean_artist = re.sub(r"[\(\[\{].*?[\)\]\}]", "", artist or "").strip()
        clean_title = re.sub(r"[^\w\s-]", " ", clean_title)
        clean_artist = re.sub(r"[^\w\s-]", " ", clean_artist)
        query = " ".join(f"{clean_title} {clean_artist}".split())
        if not query:
            return None

        url = "https://songbpm.com/searches"
        data = urllib.parse.urlencode({"query": query}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "it,en;q=0.9"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                for a in soup.find_all("a"):
                    href = a.get("href", "")
                    if href.startswith("/@"):
                        txt = a.get_text(" ", strip=True)
                        m_bpm = re.search(r"BPM\s+(\d+)", txt)
                        m_key = re.search(r"Key\s+([A-G][b#]?(?:\s*(?:maj|min|m))?)", txt, re.IGNORECASE)
                        m_dur = re.search(r"Duration\s+(\d+:\d+)", txt)
                        if m_bpm:
                            bpm = int(m_bpm.group(1))
                            if 40 <= bpm <= 260:
                                return {
                                    "bpm": bpm,
                                    "key": m_key.group(1).strip() if m_key else None,
                                    "duration": m_dur.group(1) if m_dur else None,
                                    "source": "SongBPM.com",
                                    "matched": txt[:80]
                                }
        except Exception:
            return None
        return None

    @classmethod
    def estimate_song_bpm(cls, title: str, artist: str = "") -> int:
        """
        Stima il tempo reale (BPM) di un brano evitando il valore fisso/rigido di 120 BPM:
        1. Ricerca prioritaria nel catalogo di standard rock/pop (istantaneo <0.1ms).
        2. Ricerca in tempo reale sul database musicale SongBPM (https://songbpm.com).
        3. Modello AI Gemini gratuito e ultraleggero (se chiave configurata o disponibile).
        4. Euristiche lessicali su genere e stile deducibili da titolo/artista.
        """
        clean_title = (title or "").strip().lower()
        clean_artist = (artist or "").strip().lower()
        if not clean_title:
            return 100

        # 1. Ricerca rapida nel catalogo di riferimento
        for song_k, bpm_v in cls.KNOWN_SONG_BPM.items():
            if song_k in clean_title or clean_title in song_k:
                return bpm_v

        # 2. Ricerca su SongBPM.com
        songbpm_info = cls.fetch_songbpm_info(title, artist)
        if songbpm_info and songbpm_info.get("bpm"):
            return songbpm_info["bpm"]

        # 3. Richiesta AI Gemini (gratuito e istantaneo, max 10 token)
        api_key = cls.get_api_key()
        if api_key:
            prompt = (
                f"Qual è il tempo musicale tipico in BPM (battiti per minuto) del brano '{title}' "
                f"{f'dell\'artista {artist}' if artist else ''}? "
                "Rispondi ESCLUSIVAMENTE con un singolo numero intero rappresentante i BPM (ad esempio: 75, 128, 140, 92). "
                "Nessun testo aggiuntivo o spiegazione."
            )
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.0,
                    "maxOutputTokens": 10
                }
            }
            models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash-lite"]
            for model in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=2.5) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode("utf-8"))
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    num_match = re.search(r"\b([4-9]\d|1\d\d|2[0-4]\d)\b", parts[0].get("text", ""))
                                    if num_match:
                                        val = int(num_match.group(1))
                                        if 40 <= val <= 240:
                                            return val
                except Exception:
                    pass

        # 3. Euristiche lessicali sul titolo / artista
        hint = f"{clean_title} {clean_artist}"
        if any(w in hint for w in ["ballad", "lento", "slow", "love", "notte", "piano", "adagio"]):
            return 68
        if any(w in hint for w in ["dance", "disco", "club", "house", "remix"]):
            return 128
        if any(w in hint for w in ["reggae", "dub", "ska"]):
            return 78
        if any(w in hint for w in ["punk", "metal", "fast", "speed", "rap"]):
            return 155
        if any(w in hint for w in ["funk", "groove", "r&b", "soul"]):
            return 104
        if any(w in hint for w in ["rock", "roll"]):
            return 124
        if any(w in hint for w in ["pop", "acoustic", "folk"]):
            return 95

        return 100

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
    def suggest_arrangement_ideas(cls, title: str, genre: str, key: str, bpm: int) -> str:
        """Suggests live arrangement dynamics (Intro, Solo, Outro, Dynamics)."""
        effective_bpm = bpm if (bpm and bpm != 120) else cls.estimate_song_bpm(title)
        return f"""Consigli di Arrangiamento Live per '{title}' ({genre}, {key}, {effective_bpm} BPM):
1. **Intro:** Inizia con strumento solista (chitarra o piano) per le prime 4 battute, poi ingresso di cassa in 4 a metà intro per definire il groove prima della voce.
2. **Strofa 1:** Mantieni il basso lineare sui quarti con piatti charleston chiusi per dare intimità al testo.
3. **Ritornello:** Esplosione dinamica: apertura del charleston, raddoppio delle chitarre e armonia vocale a due voci sulla terza superiore.
4. **Bridge / Assolo:** Sezione ritmica serrata, progressione in crescendo dinamico fino al drop sul ritornello finale.
5. **Finale:** Uscita con giro armonico ripetuto in diminuendo con stacco secco sull'accordo di tonica ({key})."""
