"""
ASMA Accordi Next Generation - Export Engine
Multi-Platform Export Engine for MobileSheets, SongBookPro, OnSong, ChordPro, and AML.
Zero-AI Dependency. Conforms to SRS Cap. 14 and Blueprint Sec. 3.
"""

from __future__ import annotations
import zipfile
import io
import os
from typing import List, Dict, Any, Optional

from asma_core.models import Song, Setlist, Repertoire
from asma_core.aml_parser import (
    AMLParser, AMLDocument, DirectiveNode, SectionNode,
    CustomTagNode, ChordLyricLineNode, ChordGridLineNode
)
from asma_core.pdf_engine import PDFEngine


class ExportEngine:
    """Multi-format interoperability export engine."""

    @classmethod
    def export_to_chordpro(cls, aml_content: str) -> str:
        """
        Translates AML AST to 100% standard ChordPro syntax.
        Converts custom tags to standard comments and maps sections.
        """
        doc = AMLParser.parse(aml_content)
        lines: List[str] = []

        for node in doc.nodes:
            if isinstance(node, DirectiveNode):
                lines.append(f"{{{node.name}: {node.value}}}")
            elif isinstance(node, SectionNode):
                name = node.section_name.lower()
                if name == "chorus":
                    lines.append("{start_of_chorus}")
                elif name == "verse":
                    lines.append("{start_of_verse}")
                elif name == "bridge":
                    lines.append("{start_of_bridge}")
                else:
                    lines.append(f"{{comment: [{name.upper()}]}}")
            elif isinstance(node, CustomTagNode):
                lines.append(f"{{comment: [{node.tag_type.upper()}]: {node.content}}}")
            elif isinstance(node, ChordGridLineNode):
                measure_strs = [" ".join(m) for m in node.measures]
                lines.append(f"| {' | '.join(measure_strs)} |")
            elif isinstance(node, ChordLyricLineNode):
                lines.append(node.to_aml())
            else:
                lines.append(node.to_aml())

        return "\n".join(lines)

    @classmethod
    def export_for_mobilesheets(cls, song: Song) -> str:
        """
        SRS Cap. 14.23: Dedicated export for MobileSheets.
        Includes MobileSheets specific header directives (key, tempo, time, custom tags).
        """
        chordpro = cls.export_to_chordpro(song.aml_content)
        header_lines = [
            f"{{title: {song.title}}}",
            f"{{artist: {song.artist}}}",
            f"{{key: {song.key_current}}}",
            f"{{tempo: {song.bpm}}}",
            f"{{time: {song.time_signature}}}"
        ]
        if song.tags:
            header_lines.append(f"{{keywords: {', '.join(song.tags)}}}")
        if song.genre:
            header_lines.append(f"{{genre: {song.genre}}}")
        if song.duration_seconds > 0:
            header_lines.append(f"{{duration: {song.duration_seconds}}}")

        return "\n".join(header_lines) + "\n\n" + chordpro

    @classmethod
    def export_for_songbookpro(cls, song: Song) -> str:
        """SRS Cap. 14.24: Dedicated export optimized for SongBookPro."""
        return cls.export_for_mobilesheets(song)

    @classmethod
    def export_setlist_for_songbookpro(cls, setlist: Setlist, songs: List[Song]) -> str:
        """Esporta l'intera scaletta come documento consolidato SongBook Pro (.pro)."""
        song_map = {s.uuid: s for s in songs}
        sections: List[str] = [
            f"{{title: SCALETTA - {setlist.title}}}",
            f"{{comment: Data: {setlist.date or 'N/D'}}}",
            f"{{comment: Brani totali: {len(setlist.items)}}}",
            ""
        ]
        for idx, item in enumerate(setlist.items, start=1):
            s = song_map.get(item.song_uuid)
            if s:
                sections.append(f"{{new_page}}\n{{comment: [SCALETTA #{idx}] {s.title}}}\n" + cls.export_for_songbookpro(s))
        return "\n\n".join(sections)

    @classmethod
    def export_for_onsong(cls, song: Song) -> str:
        """SRS Cap. 14.25: Dedicated export optimized for OnSong."""
        doc = AMLParser.parse(song.aml_content)
        lines: List[str] = [
            f"Title: {song.title}",
            f"Artist: {song.artist}",
            f"Key: {song.key_current}",
            f"Tempo: {song.bpm}",
            f"Time: {song.time_signature}",
            ""
        ]
        for node in doc.nodes:
            if isinstance(node, SectionNode):
                lines.append(f"{node.section_name.title()}:")
            elif isinstance(node, DirectiveNode):
                continue
            else:
                lines.append(node.to_aml())
        return "\n".join(lines)

    @classmethod
    def create_offline_live_pack_zip(
        cls,
        setlist: Setlist,
        songs: List[Song]
    ) -> bytes:
        """
        SRS Cap. 14.29: Generates an Offline Live Pack ZIP containing:
        - Master consolidated Setlist PDF
        - Individual Song PDFs
        - Native AML source files
        - MobileSheets files
        - Setlist JSON metadata
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. Consolidated Setlist PDF
            master_pdf = PDFEngine.generate_setlist_pdf(setlist, songs)
            clean_title = setlist.title.replace(" ", "_")
            zf.writestr(f"00_SCALETTA_{clean_title}.pdf", master_pdf)

            # 2. Individual Songs (PDF, AML, MobileSheets)
            for idx, s in enumerate(songs, start=1):
                safe_name = f"{idx:02d}_{s.title.replace(' ', '_')}"
                # PDF
                song_pdf = PDFEngine.generate_song_pdf(s)
                zf.writestr(f"pdf/{safe_name}.pdf", song_pdf)
                # AML
                zf.writestr(f"aml/{safe_name}.aml", s.aml_content)
                # MobileSheets
                ms_text = cls.export_for_mobilesheets(s)
                zf.writestr(f"mobilesheets/{safe_name}.pro", ms_text)

            # 3. Metadata JSON
            zf.writestr("metadata.json", str(setlist.to_dict()))

        zip_bytes = zip_buffer.getvalue()
        zip_buffer.close()
        return zip_bytes

    @classmethod
    def get_default_local_export_dir(cls) -> str:
        """Returns standard local PDF exports directory."""
        return os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports", "pdf"))

    @classmethod
    def get_default_gdrive_export_dir(cls) -> str:
        """Detects or returns standard Google Drive synchronized directory."""
        candidates = [
            "G:\\Il mio Drive\\ASMA_PDF",
            "G:\\My Drive\\ASMA_PDF",
            os.path.expanduser("~/Google Drive/ASMA_PDF"),
            os.path.expanduser("~/GoogleDrive/ASMA_PDF"),
        ]
        for c in candidates:
            if os.path.exists(os.path.dirname(c)) or os.path.exists(c):
                return c
        return os.path.expanduser("~/Google Drive/ASMA_PDF")

    @classmethod
    def save_file_to_destination(cls, file_bytes: bytes, target_dir: str, file_name: str) -> str:
        """
        Saves binary file (e.g. PDF) to designated directory (local or Google Drive).
        Creates directory structure if missing and returns absolute file path.
        """
        cleaned_dir = os.path.abspath(os.path.expanduser(target_dir.strip()))
        os.makedirs(cleaned_dir, exist_ok=True)
        target_path = os.path.join(cleaned_dir, file_name)
        with open(target_path, "wb") as f:
            f.write(file_bytes)
        return target_path
