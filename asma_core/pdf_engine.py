"""
ASMA Accordi Next Generation - Device-Aware PDF Engine
High-Performance PDF Generation Engine powered by ReportLab.
Zero-AI Dependency. Conforms to SRS Cap. 13 and Blueprint Sec. 7.
"""

from __future__ import annotations
import os
import io
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, PageBreak, Flowable
)
from reportlab.pdfgen import canvas

from asma_core.models import Song, DeviceProfile, Setlist, Repertoire
from asma_core.aml_parser import (
    AMLParser, AMLDocument, DirectiveNode, SectionNode,
    CustomTagNode, ChordLyricLineNode, ChordGridLineNode, CommentNode
)


# Standard custom page sizes (in points, 1 point = 1/72 inch)
PAGE_SIZES: Dict[str, Tuple[float, float]] = {
    "pc_a4": A4,
    "pc_a4_landscape": landscape(A4),
    "tablet": landscape(A4),
    "ipad": portrait(A4),
    "smartphone": (100 * mm, 210 * mm)  # Tall vertical smartphone form-factor
}


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to calculate total page count dynamically
    and render professional headers, footers and optional watermarks.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.watermark_text: Optional[str] = None
        self.document_title: str = ""
        self.version_str: str = ""

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        page_w, page_h = self._pagesize

        # 1. Watermark if present
        if self.watermark_text:
            self.setFont("Helvetica-Bold", 45)
            self.setFillColor(colors.Color(0.85, 0.85, 0.85, alpha=0.35))
            self.translate(page_w / 2.0, page_h / 2.0)
            self.rotate(45)
            self.drawCentredString(0, 0, self.watermark_text.upper())
            self.restoreState()
            self.saveState()

        # 2. Header line (on page 2 onwards)
        if self._pageNumber > 1:
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#666666"))
            self.drawString(15 * mm, page_h - 10 * mm, f"ASMA Accordi — {self.document_title}")
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(15 * mm, page_h - 11 * mm, page_w - 15 * mm, page_h - 11 * mm)

        # 3. Footer line and page numbering
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#777777"))
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(15 * mm, 12 * mm, page_w - 15 * mm, 12 * mm)

        # Left footer: metadata
        date_str = datetime.now().strftime("%d/%m/%Y")
        footer_left = f"Generato: {date_str} {self.version_str}"
        self.drawString(15 * mm, 8 * mm, footer_left)

        # Right footer: Page X of Y
        footer_right = f"Pagina {self._pageNumber} di {total_pages}"
        self.drawRightString(page_w - 15 * mm, 8 * mm, footer_right)

        self.restoreState()


class PDFEngine:
    """
    Device-Aware Publication Engine for ASMA 2.0.
    Transforms AML documents into publication-ready PDFs.
    """
    _cache: Dict[str, bytes] = {}

    @classmethod
    def get_page_size(cls, profile: DeviceProfile) -> Tuple[float, float]:
        target = profile.target_device.lower()
        if target == "smartphone":
            return PAGE_SIZES["smartphone"]
        elif target == "tablet":
            return PAGE_SIZES["tablet"]
        elif target == "ipad":
            return PAGE_SIZES["ipad"]
        else:
            return PAGE_SIZES["pc_a4_landscape"] if profile.orientation == "landscape" else PAGE_SIZES["pc_a4"]

    @classmethod
    def generate_song_pdf(
        cls,
        song: Song,
        profile: Optional[DeviceProfile] = None,
        template_name: str = "standard",
        watermark: Optional[str] = None,
        use_cache: bool = True
    ) -> bytes:
        """
        Generates a device-aware PDF for a single song.
        Implements memory buffer caching and smart page break protection.
        """
        prof = profile or DeviceProfile()
        cache_key = f"{song.uuid}_{song.updated_at}_{prof.target_device}_{prof.orientation}_{template_name}_{watermark}"

        if use_cache and cache_key in cls._cache:
            return cls._cache[cache_key]

        buffer = io.BytesIO()
        pagesize = cls.get_page_size(prof)

        # Margins converted from mm to points
        top_m = prof.margin_top_mm * mm
        bot_m = prof.margin_bottom_mm * mm
        left_m = prof.margin_left_mm * mm
        right_m = prof.margin_right_mm * mm

        doc = SimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            leftMargin=left_m,
            rightMargin=right_m,
            topMargin=top_m,
            bottomMargin=bot_m
        )

        styles = cls._build_style_sheet(prof, template_name)
        story: List[Flowable] = []

        # 1. Song Header Banner
        header_table = cls._create_song_header_table(song, styles, prof, pagesize[0] - left_m - right_m)
        story.append(header_table)
        story.append(Spacer(1, 4 * mm))

        # 2. Parse AML Document and Render Flowables
        aml_doc = AMLParser.parse(song.aml_content)
        content_flowables = cls._render_aml_nodes_to_flowables(aml_doc, styles, pagesize[0] - left_m - right_m)
        story.extend(content_flowables)

        # Custom Canvas Factory for page numbering and watermark
        def canvas_maker(*args, **kwargs):
            c = NumberedCanvas(*args, **kwargs)
            c.watermark_text = watermark
            c.document_title = song.title
            c.version_str = f"| Rev #{song.current_revision}"
            return c

        doc.build(story, canvasmaker=canvas_maker)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        if use_cache:
            cls._cache[cache_key] = pdf_bytes

        return pdf_bytes

    @classmethod
    def generate_setlist_pdf(
        cls,
        setlist: Setlist,
        songs: List[Song],
        profile: Optional[DeviceProfile] = None,
        template_name: str = "standard",
        watermark: Optional[str] = None
    ) -> bytes:
        """
        Generates a consolidated multi-song PDF document for an entire setlist,
        including a cover page, structured index, and smart song-level page breaks.
        """
        prof = profile or DeviceProfile()
        buffer = io.BytesIO()
        pagesize = cls.get_page_size(prof)

        left_m = prof.margin_left_mm * mm
        right_m = prof.margin_right_mm * mm
        usable_w = pagesize[0] - left_m - right_m

        doc = SimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            leftMargin=left_m,
            rightMargin=right_m,
            topMargin=prof.margin_top_mm * mm,
            bottomMargin=prof.margin_bottom_mm * mm
        )

        styles = cls._build_style_sheet(prof, template_name)
        story: List[Flowable] = []

        # Cover Page
        story.append(Spacer(1, 10 * mm))
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "band_logo.png")
        if not os.path.exists(logo_path):
            logo_path = "assets/band_logo.png"
        if os.path.exists(logo_path):
            try:
                from reportlab.platypus import Image as RLImage
                story.append(RLImage(logo_path, width=50 * mm, height=20 * mm))
                story.append(Spacer(1, 6 * mm))
            except Exception:
                pass

        story.append(Paragraph(f"<b>SCALETTA LIVE: {setlist.title.upper()}</b>", styles["DocTitle"]))
        if setlist.date:
            story.append(Paragraph(f"Data Esecuzione: <b>{setlist.date}</b>", styles["SectionText"]))
        if setlist.description:
            story.append(Paragraph(f"<i>{setlist.description}</i>", styles["SectionText"]))

        story.append(Spacer(1, 10 * mm))

        # Index Table of Songs
        index_data = [["#", "Titolo Brano", "Artista", "Tonalità", "BPM", "Note"]]
        song_map = {s.uuid: s for s in songs}

        for idx, item in enumerate(setlist.items, start=1):
            s = song_map.get(item.song_uuid)
            title = s.title if s else "Brano sconosciuto"
            artist = s.artist if s else ""
            key = item.custom_key or (s.key_current if s else "-")
            bpm = str(item.custom_bpm or (s.bpm if s else "-"))
            notes = item.notes or ("(Medley)" if item.is_medley else "")
            index_data.append([str(idx), title, artist, key, bpm, notes])

        idx_table = Table(index_data, colWidths=[10 * mm, 60 * mm, 40 * mm, 20 * mm, 18 * mm, 40 * mm])
        idx_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#212121")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
            ('FONTSIZE', (0, 1), (-1, -1), 8.5)
        ]))
        story.append(idx_table)
        story.append(PageBreak())

        # Render each song with smart page break between songs
        for i, item in enumerate(setlist.items):
            s = song_map.get(item.song_uuid)
            if not s:
                continue

            header_t = cls._create_song_header_table(s, styles, prof, usable_w, setlist_pos=f"{i+1} di {len(setlist.items)}")
            story.append(header_t)
            story.append(Spacer(1, 4 * mm))

            aml_doc = AMLParser.parse(s.aml_content)
            # If item has custom transposition key, transpose document
            if item.custom_key and item.custom_key != s.key_current:
                from asma_core.music_engine import MusicEngine
                delta = MusicEngine.calculate_semitone_delta(s.key_current, item.custom_key)
                aml_doc = AMLParser.transpose_document(aml_doc, semitones=delta)

            flowables = cls._render_aml_nodes_to_flowables(aml_doc, styles, usable_w)
            story.extend(flowables)

            # Insert page break between songs
            if i < len(setlist.items) - 1:
                story.append(PageBreak())

        def canvas_maker(*args, **kwargs):
            c = NumberedCanvas(*args, **kwargs)
            c.watermark_text = watermark
            c.document_title = setlist.title
            c.version_str = "| Scaletta Ufficiale"
            return c

        doc.build(story, canvasmaker=canvas_maker)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @classmethod
    def _build_style_sheet(cls, profile: DeviceProfile, template_name: str) -> Dict[str, ParagraphStyle]:
        """Constructs typography styles conforming to the device profile and template."""
        base_lyrics_size = profile.font_size_lyrics
        base_chords_size = profile.font_size_chords

        # Color schemes based on template
        if template_name.lower() == "stage":
            chord_color = colors.HexColor("#D32F2F")  # High contrast bright red
            bg_badge = colors.HexColor("#1A237E")    # Deep navy blue
        else:
            chord_color = colors.HexColor("#B71C1C")  # Professional dark crimson
            bg_badge = colors.HexColor("#0D47A1")

        styles = {
            "DocTitle": ParagraphStyle(
                "DocTitle",
                fontName="Helvetica-Bold",
                fontSize=base_lyrics_size * 1.5,
                leading=base_lyrics_size * 1.8,
                textColor=colors.HexColor("#111111")
            ),
            "DocSubtitle": ParagraphStyle(
                "DocSubtitle",
                fontName="Helvetica",
                fontSize=base_lyrics_size * 1.0,
                leading=base_lyrics_size * 1.2,
                textColor=colors.HexColor("#555555")
            ),
            "SectionBadge": ParagraphStyle(
                "SectionBadge",
                fontName="Helvetica-Bold",
                fontSize=base_lyrics_size * 0.9,
                leading=base_lyrics_size * 1.2,
                textColor=colors.white
            ),
            "SectionText": ParagraphStyle(
                "SectionText",
                fontName="Helvetica",
                fontSize=base_lyrics_size,
                leading=base_lyrics_size * 1.3,
                textColor=colors.black
            ),
            "ChordText": ParagraphStyle(
                "ChordText",
                fontName="Helvetica-Bold",
                fontSize=base_chords_size,
                leading=base_chords_size * 1.1,
                textColor=chord_color
            ),
            "LyricText": ParagraphStyle(
                "LyricText",
                fontName="Courier",
                fontSize=base_lyrics_size,
                leading=base_lyrics_size * 1.2,
                textColor=colors.HexColor("#111111")
            ),
            "CustomTagText": ParagraphStyle(
                "CustomTagText",
                fontName="Helvetica-Oblique",
                fontSize=base_lyrics_size * 0.9,
                leading=base_lyrics_size * 1.1,
                textColor=colors.HexColor("#4A148C")
            )
        }
        return styles

    @classmethod
    def _create_song_header_table(
        cls,
        song: Song,
        styles: Dict[str, ParagraphStyle],
        profile: DeviceProfile,
        usable_width: float,
        setlist_pos: Optional[str] = None
    ) -> Table:
        """Constructs an elegant header box containing metadata (Key, BPM, Time Signature, Capo)."""
        title_p = Paragraph(f"<b>{song.title}</b>", styles["DocTitle"])
        pos_str = f" [{setlist_pos}]" if setlist_pos else ""
        artist_p = Paragraph(f"<b>{song.artist}</b>{pos_str} &bull; <i>{song.author}</i>", styles["DocSubtitle"])

        meta_str = f"<b>Key:</b> {song.key_current} | <b>BPM:</b> {song.bpm} | <b>Metro:</b> {song.time_signature}"
        if song.capo > 0:
            meta_str += f" | <b>Capo:</b> {song.capo}° tasto"
        meta_p = Paragraph(meta_str, styles["SectionText"])

        logo_flowable = None
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "band_logo.png")
        if not os.path.exists(logo_path):
            logo_path = "assets/band_logo.png"
        if os.path.exists(logo_path):
            try:
                from reportlab.platypus import Image as RLImage
                logo_flowable = RLImage(logo_path, width=28 * mm, height=11 * mm)
            except Exception:
                pass

        if logo_flowable:
            table_data = [
                [title_p, logo_flowable],
                [artist_p, meta_p]
            ]
            col1_w = usable_width * 0.65
            col2_w = usable_width * 0.35
            t = Table(table_data, colWidths=[col1_w, col2_w])
            t.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('ALIGN', (1, 1), (1, 1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('LINEBELOW', (0, 1), (-1, 1), 1.0, colors.HexColor("#333333"))
            ]))
            return t

        table_data = [
            [title_p, meta_p],
            [artist_p, ""]
        ]

        col1_w = usable_width * 0.55
        col2_w = usable_width * 0.45

        t = Table(table_data, colWidths=[col1_w, col2_w])
        t.setStyle(TableStyle([
            ('SPAN', (1, 0), (1, 1)),
            ('ALIGN', (1, 0), (1, 1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('LINEBELOW', (0, 1), (-1, 1), 1.0, colors.HexColor("#333333"))
        ]))
        return t

    @classmethod
    def _render_aml_nodes_to_flowables(
        cls,
        doc: AMLDocument,
        styles: Dict[str, ParagraphStyle],
        usable_width: float
    ) -> List[Flowable]:
        """
        Converts AML AST nodes into ReportLab Flowables.
        Groups section items into KeepTogether blocks to prevent orphan lines.
        """
        flowables: List[Flowable] = []
        current_section_block: List[Flowable] = []

        def flush_section():
            if current_section_block:
                # If section block is compact (under 8 elements), keep together
                if len(current_section_block) <= 8:
                    flowables.append(KeepTogether(current_section_block[:]))
                else:
                    flowables.extend(current_section_block[:])
                current_section_block.clear()

        for node in doc.nodes:
            if isinstance(node, DirectiveNode):
                # Header directives are already represented in top banner
                continue

            elif isinstance(node, SectionNode):
                flush_section()
                # Section badge
                badge_text = f"&nbsp;&nbsp;<b>[{node.section_name.upper()}]</b>&nbsp;&nbsp;"
                p = Paragraph(badge_text, styles["SectionBadge"])
                badge_table = Table([[p]], colWidths=[usable_width])
                badge_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#263238")),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                current_section_block.append(Spacer(1, 2 * mm))
                current_section_block.append(badge_table)
                current_section_block.append(Spacer(1, 1.5 * mm))

            elif isinstance(node, ChordGridLineNode):
                # Measure grid line: | Bm | F#7 | A | E |
                grid_cells = []
                for measure in node.measures:
                    grid_cells.append(Paragraph(f"<b>{' '.join(measure)}</b>", styles["ChordText"]))

                num_cells = len(grid_cells)
                cell_w = usable_width / max(num_cells, 1)
                grid_table = Table([grid_cells], colWidths=[cell_w] * num_cells)
                grid_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0F4F8")),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 1.0, colors.HexColor("#90A4AE")),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                current_section_block.append(KeepTogether([grid_table, Spacer(1, 1.5 * mm)]))

            elif isinstance(node, ChordLyricLineNode):
                # Interleaved chord-lyric line
                chord_line_parts = []
                lyric_line_parts = []

                for seg in node.segments:
                    c_text = seg.chord.chord_text if seg.chord else ""
                    l_text = seg.text or ""

                    # Space padding to align monospace visually
                    max_len = max(len(c_text), len(l_text))
                    if c_text:
                        chord_line_parts.append(c_text.ljust(max_len))
                    else:
                        chord_line_parts.append(" " * max_len)
                    lyric_line_parts.append(l_text.ljust(max_len))

                chords_str = "".join(chord_line_parts).rstrip()
                lyrics_str = "".join(lyric_line_parts).rstrip()

                unit_flowables = []
                if chords_str.strip():
                    unit_flowables.append(Paragraph(f"<font color='#B71C1C'><b>{chords_str.replace(' ', '&nbsp;')}</b></font>", styles["LyricText"]))
                if lyrics_str.strip():
                    unit_flowables.append(Paragraph(lyrics_str.replace(' ', '&nbsp;'), styles["LyricText"]))
                unit_flowables.append(Spacer(1, 1 * mm))

                # Keep chord line and lyric line strictly atomic (never break apart)
                current_section_block.append(KeepTogether(unit_flowables))

            elif isinstance(node, CustomTagNode):
                # Instrumental tag
                tag_p = Paragraph(f"&#9835; <b>[{node.tag_type.upper()}]:</b> {node.content}", styles["CustomTagText"])
                tag_t = Table([[tag_p]], colWidths=[usable_width])
                tag_t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDE7F6")),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#7E57C2")),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                current_section_block.append(KeepTogether([tag_t, Spacer(1, 1 * mm)]))

            elif isinstance(node, CommentNode):
                comm_p = Paragraph(f"<i># {node.text}</i>", styles["DocSubtitle"])
                current_section_block.append(comm_p)

        flush_section()
        return flowables

    @classmethod
    def clear_cache(cls) -> None:
        """Empties the in-memory PDF buffer cache."""
        cls._cache.clear()
