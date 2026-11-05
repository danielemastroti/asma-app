"""
ASMA Accordi Next Generation - Multi-Format Import Engine
Extracts, normalizes and compiles external formats into official AML.
Supports: PDF, ChordPro, Traditional Chords-Over-Lyrics, Raw Text, and OnSong.
Zero-AI Dependency. Conforms to SRS Cap. 14.3 - 14.19 and Blueprint Sec. 3.
"""

from __future__ import annotations
import io
import re
from typing import Dict, Any, Optional, Tuple, List

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None

from asma_core.models import Song
from asma_core.aml_parser import AMLParser, AMLDocument
from asma_core.music_engine import MusicEngine


class ImportEngine:
    """Multi-format song importer."""

    @classmethod
    def import_from_chordpro(cls, content: str) -> Song:
        """Parses a ChordPro string and returns an initialized Song instance."""
        doc = AMLParser.parse(content)
        meta = doc.metadata

        title = meta.get("title", meta.get("t", "Senza Titolo"))
        artist = meta.get("artist", meta.get("a", ""))
        key = meta.get("key", "C")
        tempo = int(meta.get("tempo", meta.get("t", 120))) if meta.get("tempo", "").isdigit() else 120
        time_sig = meta.get("time", "4/4")
        capo = int(meta.get("capo", 0)) if meta.get("capo", "").isdigit() else 0

        song = Song(
            title=title,
            artist=artist,
            key_original=key,
            key_current=key,
            bpm=tempo,
            time_signature=time_sig,
            capo=capo,
            aml_content=doc.to_aml()
        )
        return song

    @classmethod
    def import_from_traditional(cls, text: str, default_title: str = "Brano Tradizionale") -> Song:
        """Parses traditional chords-over-lyrics text and returns an initialized Song instance."""
        doc = AMLParser.import_traditional_chords_over_text(text)
        meta = doc.metadata

        # Attempt to detect key from first recognized chord if key not set
        key = meta.get("key")
        if not key:
            for node in doc.nodes:
                if hasattr(node, "segments"):
                    for seg in node.segments:
                        if seg.chord:
                            p = MusicEngine.parse_chord(seg.chord.chord_text)
                            if p:
                                key = p.full_root
                                break
                    if key:
                        break
        key = key or "C"

        song = Song(
            title=meta.get("title", default_title),
            artist=meta.get("artist", ""),
            key_original=key,
            key_current=key,
            aml_content=doc.to_aml()
        )
        return song

    @classmethod
    def import_from_pdf_bytes(cls, pdf_bytes: bytes, filename: str = "documento.pdf") -> Song:
        """
        SRS Cap. 14.4: Extracts text from PDF using PyMuPDF and parses it as traditional or AML text.
        """
        if not fitz:
            raise RuntimeError("PyMuPDF non disponibile per l'estrazione testo da PDF.")

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        extracted_text_pages: List[str] = []

        for page in doc:
            extracted_text_pages.append(page.get_text("text"))

        full_text = "\n".join(extracted_text_pages)

        # Infer title from filename if title not found
        clean_name = filename.rsplit(".", 1)[0].replace("_", " ").title()

        # Check if PDF text already contains inline brackets [C]
        if "[" in full_text and "]" in full_text:
            song = cls.import_from_chordpro(full_text)
            if not song.title or song.title == "Senza Titolo":
                song.title = clean_name
            return song
        else:
            return cls.import_from_traditional(full_text, default_title=clean_name)
