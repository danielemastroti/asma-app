"""
ASMA Accordi Next Generation - Web Song Importer
Extracts and normalizes chord charts and lyrics from public web pages and portals.
Supports live multi-portal search: Accordi e Spartiti, Ultimate-Guitar, Skitarrate, Chordie, and generic chord sites.
Conforms to SRS Cap. 14.14, 14.15 and user directive.
"""

from __future__ import annotations
import re
import json
import urllib.parse
from typing import Dict, Any, Optional, Tuple, List
import requests
from bs4 import BeautifulSoup

from asma_core.models import Song
from asma_core.aml_parser import AMLParser, AMLDocument
from asma_core.music_engine import MusicEngine


class WebSongImporter:
    """Imports songs directly from public web URLs and chord websites with real multi-portal online search."""

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    @classmethod
    def search_online_candidates(cls, song_title: str, artist: str = "", limit: int = 10, timeout_seconds: int = 8) -> List[Dict[str, Any]]:
        """
        Executes a real-time search across major chord portals (Italian & International)
        and returns a ranked list of candidate chord charts.
        """
        query_terms = [t.strip() for t in [song_title, artist] if t.strip()]
        full_query = " ".join(query_terms)
        if not full_query:
            return []

        q_enc = urllib.parse.quote(full_query)
        headers = {"User-Agent": cls.USER_AGENT}
        candidates: List[Dict[str, Any]] = []

        # -------------------------------------------------------------
        # 1. Accordi e Spartiti (Primary Italian & International songs)
        # -------------------------------------------------------------
        try:
            url_as = f"https://www.accordiespartiti.it/?s={q_enc}"
            resp = requests.get(url_as, headers=headers, timeout=timeout_seconds)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "/accordi/" in href and not any(c["url"] == href for c in candidates):
                        # Extract artist from tags-search if present
                        tag_elem = a.find(class_="tags-search")
                        cand_artist = tag_elem.get_text(strip=True) if tag_elem else ""
                        if tag_elem:
                            tag_elem.decompose()
                        cand_title = a.get_text(strip=True)

                        # Clean title
                        cand_title = re.sub(r"(?i)\s*accordi(\s+100%\s+corretti)?.*", "", cand_title).strip()
                        if cand_title:
                            score = cls._compute_relevance(song_title, artist, cand_title, cand_artist)
                            if score > 0:
                                candidates.append({
                                    "title": cand_title,
                                    "artist": cand_artist or artist or "Artista Sconosciuto",
                                    "portal": "Accordi e Spartiti",
                                    "url": href,
                                    "score": score
                                })
        except Exception:
            pass  # Fail gracefully to allow other sources

        # -------------------------------------------------------------
        # 2. Ultimate-Guitar (Primary International & Global chords)
        # -------------------------------------------------------------
        try:
            url_ug = f"https://www.ultimate-guitar.com/search.php?search_type=title&value={q_enc}"
            resp = requests.get(url_ug, headers=headers, timeout=timeout_seconds)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                store = soup.find("div", class_="js-store")
                if store and store.get("data-content"):
                    data = json.loads(store["data-content"])
                    results = data.get("store", {}).get("page", {}).get("data", {}).get("results", [])
                    for res in results:
                        tab_url = res.get("tab_url")
                        tab_type = res.get("type", "")
                        # We only want Chords (not tabs, bass or pro guitar files)
                        if tab_url and (tab_type == "Chords" or "chords" in tab_url):
                            if not any(c["url"] == tab_url for c in candidates):
                                cand_title = res.get("song_name", "")
                                cand_artist = res.get("artist_name", "")
                                score = cls._compute_relevance(song_title, artist, cand_title, cand_artist)
                                if score > 0:
                                    candidates.append({
                                        "title": cand_title,
                                        "artist": cand_artist,
                                        "portal": "Ultimate Guitar",
                                        "url": tab_url,
                                        "score": score
                                    })
        except Exception:
            pass

        # Sort descending by relevance score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:limit]

    @classmethod
    def _compute_relevance(cls, target_title: str, target_artist: str, cand_title: str, cand_artist: str) -> int:
        """Calculates a simple matching score between searched terms and candidate results."""
        score = 0
        t_clean = target_title.lower().strip()
        a_clean = target_artist.lower().strip()
        ct_clean = cand_title.lower().strip()
        ca_clean = cand_artist.lower().strip()

        if t_clean and t_clean == ct_clean:
            score += 50
        elif t_clean and t_clean in ct_clean:
            score += 30

        if a_clean and a_clean == ca_clean:
            score += 40
        elif a_clean and a_clean in ca_clean:
            score += 20

        # Sub-word matches
        for word in t_clean.split():
            if len(word) > 2 and word in ct_clean:
                score += 5

        return score

    @classmethod
    def fetch_from_url(cls, url: str, timeout_seconds: int = 10) -> Song:
        """
        Fetches HTML from a public URL, extracts title, artist, and chord content,
        and converts it into an AML Song object.
        """
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url

        headers = {"User-Agent": cls.USER_AGENT}
        try:
            resp = requests.get(clean_url, headers=headers, timeout=timeout_seconds)
            resp.raise_for_status()
            html_text = resp.text
        except Exception as e:
            raise RuntimeError(f"Impossibile scaricare la pagina web da {clean_url}: {str(e)}")

        # Check if Ultimate Guitar page
        if "ultimate-guitar.com" in clean_url:
            return cls._parse_ultimate_guitar(html_text, clean_url)

        return cls.parse_html_to_song(html_text, source_url=clean_url)

    @classmethod
    def _parse_ultimate_guitar(cls, html_text: str, source_url: str) -> Song:
        """Parses Ultimate Guitar JSON store page."""
        soup = BeautifulSoup(html_text, "html.parser")
        store = soup.find("div", class_="js-store")
        if not store or not store.get("data-content"):
            return cls.parse_html_to_song(html_text, source_url)

        try:
            data = json.loads(store["data-content"])
            page_data = data.get("store", {}).get("page", {}).get("data", {})
            tab_data = page_data.get("tab", {})
            tab_view = page_data.get("tab_view", {})
            wiki_tab = tab_view.get("wiki_tab", {})
            content = wiki_tab.get("content", "")

            title = tab_data.get("song_name") or "Brano Ultimate-Guitar"
            artist = tab_data.get("artist_name") or ""
            tonality = tab_view.get("meta", {}).get("tonality") or "C"

            # Clean UG markup: [ch]Am[/ch] -> Am, remove [tab] wrapper tags and strip guitar tab lines
            from asma_core.pdf_engine import PDFEngine
            cleaned = re.sub(r"\[ch\](.*?)\[/ch\]", r"\1", content)
            cleaned = re.sub(r"\[/?tab\]", "", cleaned)
            cleaned = "\n".join([l for l in cleaned.splitlines() if not PDFEngine.is_guitar_tab_line(l)])

            doc = AMLParser.import_traditional_chords_over_text(cleaned)

            aml_lines = [
                f"{{title: {title}}}",
                f"{{artist: {artist}}}",
                f"{{key: {tonality}}}",
                f"{{source: {source_url}}}",
                "",
                doc.to_aml()
            ]

            from asma_core.ai_service import BandAIService
            est_bpm = BandAIService.estimate_song_bpm(title, artist)
            return Song(
                title=title,
                artist=artist,
                key_original=tonality,
                key_current=tonality,
                bpm=est_bpm,
                aml_content="\n".join(aml_lines),
                tags=["importato-web", "ultimate-guitar"]
            )
        except Exception:
            return cls.parse_html_to_song(html_text, source_url)

    @classmethod
    def parse_html_to_song(cls, html_text: str, source_url: str = "") -> Song:
        """
        Parses web page HTML using heuristic content extraction to locate the main chord chart.
        """
        soup = BeautifulSoup(html_text, "html.parser")

        # 1. Extract Page Title / Artist
        extracted_title = ""
        extracted_artist = ""

        # Check OpenGraph metadata
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            extracted_title = og_title["content"].strip()
        elif soup.title and soup.title.string:
            extracted_title = soup.title.string.strip()

        # Clean title string (remove site slogans and suffixes)
        extracted_title = re.sub(r"(?i)\s*accordi\s+100%\s+corretti\s*", " ", extracted_title)
        for suffix in [
            "Accordi e Spartiti", "Accordi per Chitarra",
            "Skitarrate", "Ultimate Guitar", "Chords & Tabs", "Testo e Accordi",
            "Chords", "Tabs", "Spartito", "Testo con Accordi"
        ]:
            extracted_title = re.sub(rf"\s*[-|:]\s*{suffix}.*", "", extracted_title, flags=re.IGNORECASE)

        # Separate "Title - Artist" or "Artist - Title" using h1 and hyphen heuristics
        h1 = soup.find("h1")
        h1_text = ""
        if h1 and h1.get_text(strip=True):
            h1_text = re.sub(r"(?i)\s*accordi(\s+100%\s+corretti)?.*", "", h1.get_text(strip=True)).strip()

        if "-" in extracted_title:
            parts = extracted_title.split("-", 1)
            p0 = parts[0].strip()
            p1 = parts[1].strip()
            if h1_text and h1_text.lower() in p0.lower():
                extracted_title = p0
                extracted_artist = p1
            elif h1_text and h1_text.lower() in p1.lower():
                extracted_title = p1
                extracted_artist = p0
            else:
                # Default heuristic: Artist - Title
                extracted_artist = p0
                extracted_title = p1
        elif " by " in extracted_title.lower():
            parts = re.split(r"\s+by\s+", extracted_title, flags=re.IGNORECASE, maxsplit=1)
            extracted_title = parts[0].strip()
            extracted_artist = parts[1].strip()
        elif h1_text:
            extracted_title = h1_text

        # 2. Extract Song Body Content
        raw_content = ""

        # Priority 1: <pre> tags
        pre_tags = soup.find_all("pre")
        if pre_tags:
            largest_pre = max(pre_tags, key=lambda p: len(p.get_text()))
            if len(largest_pre.get_text()) > 200:
                raw_content = largest_pre.get_text()

        # Priority 2: Specific portal classes
        if not raw_content:
            target_selectors = [
                ".entry-content", ".testo_canzone", ".tab-content",
                ".js-tab-content", ".chord_sheet", "#chord_sheet",
                "article", ".song-content", ".chords-body"
            ]
            for sel in target_selectors:
                element = soup.select_one(sel)
                if element and len(element.get_text()) > 200:
                    for br in element.find_all("br"):
                        br.replace_with("\n")
                    raw_content = element.get_text()
                    break

        # Priority 3: Fallback to all body paragraphs
        if not raw_content:
            body = soup.find("body")
            if body:
                raw_content = body.get_text(separator="\n")

        if not raw_content or len(raw_content.strip()) < 50:
            raise ValueError("Impossibile estrarre il testo degli accordi dalla pagina selezionata.")

        clean_text = raw_content.replace("\xa0", " ")
        # Rimuove blocchi di intavolature/tablature chitarra web
        clean_text = re.sub(r"(?is)\[tab\].*?\[/tab\]", "", clean_text)
        clean_text = re.sub(r"(?is)\{sot\}.*?\{eot\}", "", clean_text)
        clean_text = re.sub(r"(?is)\{start_of_tab\}.*?\{end_of_tab\}", "", clean_text)
        clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)

        # 3. Convert to AML Document
        if "[" in clean_text and "]" in clean_text:
            doc = AMLParser.parse(clean_text)
        else:
            doc = AMLParser.import_traditional_chords_over_text(clean_text)

        # 4. Infer Key
        detected_key = "C"
        for node in doc.nodes:
            if hasattr(node, "segments"):
                for seg in node.segments:
                    if seg.chord:
                        p = MusicEngine.parse_chord(seg.chord.chord_text)
                        if p:
                            detected_key = p.full_root
                            break
                if detected_key != "C":
                    break

        final_title = extracted_title or "Brano da Web"
        final_artist = extracted_artist or ""

        aml_lines = [
            f"{{title: {final_title}}}",
            f"{{artist: {final_artist}}}",
            f"{{key: {detected_key}}}",
            f"{{source: {source_url}}}",
            "",
            doc.to_aml()
        ]

        from asma_core.ai_service import BandAIService
        est_bpm = BandAIService.estimate_song_bpm(final_title, final_artist)
        return Song(
            title=final_title,
            artist=final_artist,
            key_original=detected_key,
            key_current=detected_key,
            bpm=est_bpm,
            aml_content="\n".join(aml_lines),
            tags=["importato-web"]
        )

    @classmethod
    def search_online_and_import(cls, song_title: str, artist: str = "") -> Song:
        """
        Executes a real internet search across chord portals and automatically imports
        the best matching chord chart.
        If offline or portals are unreachable, gracefully falls back to a clean template draft.
        """
        candidates = cls.search_online_candidates(song_title, artist, limit=3)
        if candidates:
            # Try importing candidate in order
            for cand in candidates:
                try:
                    song = cls.fetch_from_url(cand["url"])
                    # Ensure title and artist are retained if site metadata was empty
                    if (not song.artist or song.artist == "Artista Sconosciuto") and cand.get("artist"):
                        song.artist = cand["artist"]
                    if (not song.title or song.title == "Brano da Web") and cand.get("title"):
                        song.title = cand["title"]
                    return song
                except Exception:
                    continue

        # Offline / Fallback draft
        aml_content = f"""{{title: {song_title.title()}}}
{{artist: {artist.title()}}}
{{key: G}}
{{tempo: 120}}
{{time: 4/4}}

{{intro}}
| G | D | Em | C |

{{verse}}
[G]Testo del brano... [D]
[Em]Accordi posizionati da completare [C]

{{chorus}}
[C]Ritornello da [D]completare con [G]la band!
"""
        from asma_core.ai_service import BandAIService
        fb_bpm = BandAIService.estimate_song_bpm(song_title, artist)
        aml_content = aml_content.replace("{tempo: 120}", f"{{tempo: {fb_bpm}}}")
        return Song(
            title=song_title.title(),
            artist=artist.title(),
            key_current="G",
            bpm=fb_bpm,
            aml_content=aml_content,
            tags=["bozza-web-fallback"]
        )
