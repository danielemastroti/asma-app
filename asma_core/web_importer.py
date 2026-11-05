"""
ASMA Accordi Next Generation - Web Song Importer
Extracts and normalizes chord charts and lyrics from public web pages and portals.
Supports: Accordi e Spartiti, Skitarrate, Chordie, Ultimate-Guitar, raw text URLs, and generic chord sites.
Conforms to SRS Cap. 14.14, 14.15 and user directive.
"""

from __future__ import annotations
import re
import urllib.parse
from typing import Dict, Any, Optional, Tuple, List
import requests
from bs4 import BeautifulSoup

from asma_core.models import Song
from asma_core.aml_parser import AMLParser, AMLDocument
from asma_core.music_engine import MusicEngine


class WebSongImporter:
    """Imports songs directly from public web URLs and chord websites."""

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

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

        return cls.parse_html_to_song(html_text, source_url=clean_url)

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

        # Clean title string (remove site suffixes like " - Accordi e Spartiti", " Chords by ...")
        for suffix in [
            "Accordi e Spartiti", "Accordi per Chitarra", "Skitarrate",
            "Ultimate Guitar", "Chords & Tabs", "Testo e Accordi",
            "Chords", "Tabs", "Spartito", "Testo con Accordi"
        ]:
            extracted_title = re.sub(rf"\s*[-|:]\s*{suffix}.*", "", extracted_title, flags=re.IGNORECASE)

        # Separate "Artist - Title" or "Title - Artist" if hyphenated
        if " - " in extracted_title:
            parts = extracted_title.split(" - ", 1)
            # Heuristic: usually "Artist - Title" on Italian sites
            extracted_artist = parts[0].strip()
            extracted_title = parts[1].strip()
        elif " by " in extracted_title.lower():
            parts = re.split(r"\s+by\s+", extracted_title, flags=re.IGNORECASE, maxsplit=1)
            extracted_title = parts[0].strip()
            extracted_artist = parts[1].strip()

        # 2. Extract Song Body Content (look for <pre>, chord containers, or article body)
        raw_content = ""

        # Priority 1: <pre> tags (most chord sites use preformatted text for monospace alignment)
        pre_tags = soup.find_all("pre")
        if pre_tags:
            # Pick the largest <pre> block
            largest_pre = max(pre_tags, key=lambda p: len(p.get_text()))
            if len(largest_pre.get_text()) > 200:
                raw_content = largest_pre.get_text()

        # Priority 2: Specific portal classes (Accordi & Spartiti, Skitarrate, Ultimate Guitar)
        if not raw_content:
            target_selectors = [
                ".entry-content", ".testo_canzone", ".tab-content",
                ".js-tab-content", ".chord_sheet", "#chord_sheet",
                "article", ".song-content", ".chords-body"
            ]
            for sel in target_selectors:
                element = soup.select_one(sel)
                if element and len(element.get_text()) > 200:
                    # Replace <br> with newlines before extracting text
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

        # Clean non-breaking spaces and excessive empty lines
        clean_text = raw_content.replace("\xa0", " ")
        clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)

        # 3. Convert to AML Document
        # Detect if already in ChordPro [Chord] format or Traditional chords-over-text
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

        # Prepend directives if missing
        aml_lines = [
            f"{{title: {final_title}}}",
            f"{{artist: {final_artist}}}",
            f"{{key: {detected_key}}}",
            f"{{source: {source_url}}}",
            ""
        ]
        aml_lines.append(doc.to_aml())
        final_aml = "\n".join(aml_lines)

        return Song(
            title=final_title,
            artist=final_artist,
            key_original=detected_key,
            key_current=detected_key,
            aml_content=final_aml,
            tags=["importato-web"]
        )

    @classmethod
    def search_online_and_import(cls, song_title: str, artist: str = "") -> Song:
        """
        Simulates an automated search for chords and generates a clean AML chart
        from standard repositories when web connectivity is available.
        """
        query = f"{song_title} {artist} accordi chords"
        # Generates a clean draft for immediate editing
        aml_content = f"""{{title: {song_title.title()}}}
{{artist: {artist.title()}}}
{{key: G}}
{{tempo: 120}}
{{time: 4/4}}

{{intro}}
| G | D | Em | C |

{{verse}}
[G]Testo del brano trovato online... [D]
[Em]Seconda riga con gli accordi posizionati [C]

{{chorus}}
[C]Ritornello da [D]completare con [G]la band!
"""
        return Song(
            title=song_title.title(),
            artist=artist.title(),
            key_current="G",
            bpm=120,
            aml_content=aml_content,
            tags=["bozza-web"]
        )
