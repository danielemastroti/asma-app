"""
ASMA Accordi Next Generation - Song Completeness Checker & LLM Autocompletion
Verifies song integrity against LRCLIB API and autocompletes truncated chord sheets using LLM.
Conforms to SRS Cap. 14, 15 and Task Directive.
"""

from __future__ import annotations
import re
import json
import urllib.parse
import urllib.request
import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)


class CompletenessChecker:
    """Checks song lyric completeness using LRCLIB API and manages AI autocompletion and snapshots."""

    USER_AGENT = "ASMA-App/1.0 (https://github.com/danielemastroti/asma-app)"
    DEFAULT_THRESHOLD = 0.80

    # Common chord tokens regex for stripping chord lines from traditional chord sheets
    CHORD_TOKENS_REGEX = re.compile(
        r"^(?:[A-G]|DO|RE|MI|FA|SOL|LA|SI)(?:b|#)?(?:m|min|maj|dim|aug|sus|add)?\d*(?:/[A-G](?:b|#)?)?$",
        re.IGNORECASE
    )

    @classmethod
    def is_medley(cls, title: str, aml_content: str = "") -> bool:
        """
        Rule: Any song whose title contains the word 'MEDLEY' (case-insensitive)
        must NEVER be verified by LRCLIB nor modified by LLM.
        Also checks medley directives in aml_content.
        """
        if not title:
            return False
        clean_title = title.strip().lower()
        if "medley" in clean_title:
            return True
        if aml_content:
            low_aml = aml_content.lower()
            if any(tag in low_aml for tag in ["{medley:", "{start_of_medley:", "{sos:", "{soms:", "{start_of_medley_song:"]):
                return True
        return False

    @classmethod
    def fetch_official_lyrics_lrclib(cls, title: str, artist: str = "", timeout: float = 6.0) -> Optional[str]:
        """
        Fetches official lyrics from free LRCLIB API.
        Attempts exact match via /api/get, then falls back to /api/search.
        """
        clean_title = re.sub(r"(?i)\s*\(.*?\)", "", title).strip()
        clean_artist = (artist or "").strip()
        if not clean_title:
            return None

        headers = {"User-Agent": cls.USER_AGENT}

        # 1. Exact match attempt
        try:
            params = {"track_name": clean_title}
            if clean_artist and clean_artist.lower() not in ["band", "artista sconosciuto", "autore sconosciuto"]:
                params["artist_name"] = clean_artist
            qs = urllib.parse.urlencode(params)
            url_get = f"https://lrclib.net/api/get?{qs}"

            req = urllib.request.Request(url_get, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    plain = data.get("plainLyrics")
                    if plain and len(plain.strip()) > 30:
                        return plain.strip()
        except Exception:
            pass

        # 2. Search fallback
        try:
            search_query = f"{clean_artist} {clean_title}".strip() if clean_artist else clean_title
            url_search = f"https://lrclib.net/api/search?q={urllib.parse.quote(search_query)}"
            req = urllib.request.Request(url_search, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    results = json.loads(resp.read().decode("utf-8"))
                    if isinstance(results, list):
                        for item in results:
                            plain = item.get("plainLyrics")
                            if plain and len(plain.strip()) > 30:
                                return plain.strip()
        except Exception:
            pass

        return None

    @classmethod
    def extract_sung_lyrics(cls, text: str) -> str:
        """
        Extracts only sung lyrics from an AML or traditional chord sheet text:
        - Removes metadata directives {title: ...}, {key: ...}, {np}, etc.
        - Removes section badges [STROFA], [RITORNELLO], [INTRO], [BRIDGE], [FINALE], etc.
        - Removes inline bracketed chords [DO], [G#m7], etc.
        - Removes standalone lines consisting solely of chords (Do, Re, Mi, C, D, Em, etc.).
        - Removes autocompletion tags [AUTO-COMPLETATO] and [/AUTO-COMPLETATO].
        """
        if not text:
            return ""

        lines = text.splitlines()
        sung_lines: List[str] = []

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            # Skip metadata directives
            if trimmed.startswith("{") and trimmed.endswith("}"):
                continue

            # Remove autocompletion markers
            trimmed = trimmed.replace("[AUTO-COMPLETATO]", "").replace("[/AUTO-COMPLETATO]", "").strip()
            if not trimmed:
                continue

            # Check for section badges like [INTRO], [STROFA], [RITORNELLO], [SOLO], etc.
            if re.match(r"^\[(?:INTRO|STROFA|RITORNELLO|RIT|CHORUS|VERSE|BRIDGE|PONTE|INCISO|SPECIAL|SOLO|ASSOLO|STACCO|STRUMENTALE|OUTRO|FINALE|CODA|END|SOV|SOC|SOB)[^\]]*\]$", trimmed, re.IGNORECASE):
                continue

            # Check if this line is a traditional chord line (spaces separated chords)
            tokens = [tok for tok in re.split(r"[\s\|\:\-]+", trimmed) if tok]
            if tokens and all(cls.is_chord_token(tok) for tok in tokens):
                continue

            # Remove inline bracketed chords [Am], [DO7], [SOL/SI]
            without_inline_chords = re.sub(r"\[[A-Za-z0-9#b/\+]+\]", "", trimmed)
            cleaned_line = without_inline_chords.strip()

            # Ignore residual noise lines (e.g. guitar tabs |---3---| or purely punctuation)
            if cleaned_line and re.search(r"[a-zA-Z\u00C0-\u017F]", cleaned_line):
                sung_lines.append(cleaned_line)

        return "\n".join(sung_lines)

    @classmethod
    def is_chord_token(cls, token: str) -> bool:
        """Determines if a standalone token is a musical chord."""
        clean = token.strip("()[]{}|,:.-")
        if not clean:
            return False
        # Italian and Anglo-Saxon chord roots
        pattern = r"^(?:DO|RE|MI|FA|SOL|LA|SI|[A-G])(?:#|b)?(?:m|min|maj|dim|aug|sus|add)?\d*(?:/(?:DO|RE|MI|FA|SOL|LA|SI|[A-G])(?:#|b)?)?$"
        return bool(re.match(pattern, clean, re.IGNORECASE))

    @classmethod
    def check_completeness(
        cls,
        title: str,
        artist: str = "",
        aml_or_chords: str = "",
        threshold: float = DEFAULT_THRESHOLD,
        prefetched_official: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates song completeness:
        1. If medley -> returns status 'MEDLEY'.
        2. Queries LRCLIB -> returns 'NON_VERIFICATO' if not found.
        3. Computes ratio = sung_text_length / official_text_length.
        4. If ratio < threshold -> 'INCOMPLETO', else 'COMPLETO'.
        """
        if cls.is_medley(title, aml_or_chords):
            return {
                "status": "MEDLEY",
                "completeness_ratio": 1.0,
                "official_lyrics": "",
                "is_medley": True,
                "reason": "Brano Medley escluso da verifiche di completezza e modifiche AI."
            }

        official_lyrics = prefetched_official if prefetched_official is not None else cls.fetch_official_lyrics_lrclib(title, artist)
        if not official_lyrics:
            return {
                "status": "NON_VERIFICATO",
                "completeness_ratio": None,
                "official_lyrics": "",
                "is_medley": False,
                "reason": "Testo ufficiale non trovato su LRCLIB."
            }

        sung_text = cls.extract_sung_lyrics(aml_or_chords)

        # Normalize strings to count meaningful sung characters (letters and digits)
        sung_chars = re.sub(r"[\W_]+", "", sung_text.lower())
        off_chars = re.sub(r"[\W_]+", "", official_lyrics.lower())

        sung_len = len(sung_chars)
        off_len = max(1, len(off_chars))

        ratio = round(min(1.5, sung_len / off_len), 2)

        if ratio < threshold:
            status = "INCOMPLETO"
            reason = f"Testo al {int(ratio * 100)}% rispetto al testo ufficiale LRCLIB (mancano strofe, bridge o outro)."
        else:
            status = "COMPLETO"
            reason = f"Testo completo ({int(ratio * 100)}% del testo ufficiale)."

        return {
            "status": status,
            "completeness_ratio": ratio,
            "official_lyrics": official_lyrics,
            "is_medley": False,
            "reason": reason
        }

    @classmethod
    def complete_song_with_llm(
        cls,
        title: str,
        artist: str,
        key: str,
        aml_content: str,
        official_lyrics: str
    ) -> Tuple[str, bool]:
        """
        Calls the LLM (Gemini) to complete missing verses/outro of a truncated song.
        Constraints:
        - Must NOT alter existing lines and chords.
        - Adds ONLY missing parts, wrapping them in [AUTO-COMPLETATO] ... [/AUTO-COMPLETATO].
        - Uses song's tonality (key) for harmonically coherent chords.
        - Temperature = 0.1.
        """
        if cls.is_medley(title, aml_content):
            raise ValueError("I brani Medley sono protetti e non possono essere modificati dall'AI.")

        from asma_core.ai_service import BandAIService
        api_key = BandAIService.get_api_key()
        if not api_key:
            raise RuntimeError("Chiave API Gemini non configurata. Configura GEMINI_API_KEY per abilitare il completamento AI.")

        if official_lyrics and official_lyrics.strip():
            ref_block = f"""TESTO UFFICIALE DI RIFERIMENTO (COMPLETO):
---
{official_lyrics.strip()}
---"""
        else:
            ref_block = f"""TESTO UFFICIALE DI RIFERIMENTO:
Non disponibile nell'archivio esterno LRCLIB. Utilizza la tua conoscenza del brano discografico '{title}' dell'artista '{artist}' per identificare strofe, bridge, ritornelli o outro mancanti nello spartito attuale. Se il brano è già completo o non conosci il testo di questo brano, restituisci lo spartito inalterato senza marcatori."""

        prompt = f"""Sei un assistente musicale professionista per una band live.
Il seguente brano con accordi in formato AML/ChordPro risulta TRONCATO rispetto al testo originale.

DATI DEL BRANO:
Titolo: {title}
Artista: {artist}
Tonalità: {key or 'C'}

{ref_block}

SPARTITO ACCORDI ATTUALE (TRONCATO O INCOMPLETO IN FORMATO AML):
---
{aml_content}
---

REGOLE TASSATIVE:
1. NON modificare, NON cancellare e NON alterare nessuna riga né gli accordi già presenti nello SPARTITO ATTUALE.
2. Identifica esclusivamente le parti (strofe, bridge, ritornelli finali, outro o code) presenti nel brano originale ma MANCANTI nello SPARTITO ATTUALE.
3. Genera e aggiungi in fondo allo spartito (o nel punto corretto in cui il testo si interrompe) le sezioni mancanti nel corretto formato AML (es. [STROFA], [RITORNELLO], [BRIDGE], [FINALE]).
4. Assegna gli accordi corretti tra parentesi quadre (es. [DO], [SOL], [LAm], [FA] o notazione anglosassone [C], [G], [Am], [F] coerente con lo spartito attuale):
   - Se il testo mancante è una ripetizione di strofe o ritornelli precedenti, copia fedelmente la medesima sequenza di accordi.
   - Se è una coda/outro nuova, deduci accordi armonici perfettamente coerenti con la tonalità {key or 'C'}.
5. RACCHIUDI OBBLIGATORIAMENTE TUTTO IL BLOCCO DI RIGHE AGGIUNTE DALL'AI TRA I TAG DI MARCAZIONE:
   [AUTO-COMPLETATO]
   ... righe aggiunte con sezioni, testo e accordi ...
   [/AUTO-COMPLETATO]
6. Restituisci l'INTERO spartito AML finale (lo spartito originale inalterato seguito dal blocco completato [AUTO-COMPLETATO]...[/AUTO-COMPLETATO]).
7. Non aggiungere commenti introduttivi né conclusivi, rispondi ESCLUSIVAMENTE con il testo AML completo.
"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 3000
            }
        }

        models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro"]
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
                with urllib.request.urlopen(req, timeout=25.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                out_text = parts[0].get("text", "").strip()
                                # Clean markdown code fences if present
                                out_text = re.sub(r"^```[a-zA-Z]*\n", "", out_text)
                                out_text = re.sub(r"\n```$", "", out_text).strip()
                                if "[AUTO-COMPLETATO]" in out_text:
                                    return out_text, True
                                # If LLM forgot the tag but added content, append the tag around the newly added tail
                                if len(out_text.strip()) > len(aml_content.strip()) + 20:
                                    tail = out_text[len(aml_content):].strip()
                                    wrapped = aml_content.rstrip() + "\n\n[AUTO-COMPLETATO]\n" + tail + "\n[/AUTO-COMPLETATO]\n"
                                    return wrapped, True
                                # If output matches or has no new sections, no modification needed
                                return aml_content, False
            except urllib.error.HTTPError as he:
                err_body = ""
                try:
                    err_body = he.read().decode("utf-8")
                except Exception:
                    pass
                last_error = f"HTTP {he.code} ({model}): {err_body[:100]}"
                logger.warning(f"Gemini API HTTPError {he.code} for model {model}: {err_body}")
                continue
            except Exception as e:
                last_error = f"{type(e).__name__} ({model}): {str(e)}"
                logger.warning(f"Gemini API Error for model {model}: {e}")
                continue

        if last_error:
            raise RuntimeError(f"Errore chiamata AI Gemini: {last_error}")

        return aml_content, False

    @classmethod
    def clean_autocompleted_tags(cls, text: str) -> str:
        """Removes [AUTO-COMPLETATO] and [/AUTO-COMPLETATO] tags from text, making it definitive."""
        if not text:
            return ""
        cleaned = text.replace("[AUTO-COMPLETATO]", "").replace("[/AUTO-COMPLETATO]", "")
        # Clean extra redundant blank lines caused by tag removals
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip() + "\n"
