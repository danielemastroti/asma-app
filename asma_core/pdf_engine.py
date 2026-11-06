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
    SimpleDocTemplate, BaseDocTemplate, PageTemplate, Frame, FrameBreak,
    Paragraph, Spacer, Table, TableStyle,
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
    "pc_a4": portrait(A4),
    "pc_a4_landscape": portrait(A4),
    "tablet": portrait(A4),
    "ipad": portrait(A4),
    "smartphone": (100 * mm, 210 * mm)  # Layout PDF sempre verticale
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
        """Returns page dimensions in points. Enforces ALWAYS vertical (portrait) layout, never landscape."""
        if getattr(profile, "width_mm", 0) > 0 and getattr(profile, "height_mm", 0) > 0:
            w = min(profile.width_mm, profile.height_mm) * mm
            h = max(profile.width_mm, profile.height_mm) * mm
            return (w, h)

        target = profile.target_device.lower()
        if target == "smartphone":
            sz = PAGE_SIZES["smartphone"]
        elif target == "tablet":
            sz = PAGE_SIZES["tablet"]
        elif target == "ipad":
            sz = PAGE_SIZES["ipad"]
        else:
            sz = PAGE_SIZES["pc_a4"]
        return (min(sz[0], sz[1]), max(sz[0], sz[1]))

    @classmethod
    def generate_song_pdf(
        cls,
        song: Song,
        profile: Optional[DeviceProfile] = None,
        template_name: str = "standard",
        watermark: Optional[str] = None,
        use_cache: bool = True,
        include_chords: bool = True
    ) -> bytes:
        """
        Generates a device-aware PDF for a single song.
        Implements memory buffer caching and smart page break protection.
        """
        prof = profile or DeviceProfile()
        cache_key = (
            f"{song.uuid}_{song.updated_at}_{prof.name}_{prof.target_device}_{prof.orientation}_"
            f"{getattr(prof, 'columns', 1)}_{getattr(prof, 'font_size_lyrics', 12)}_"
            f"{getattr(prof, 'margin_left_mm', 10)}_{getattr(prof, 'color_lyrics', '')}_"
            f"{getattr(prof, 'color_chords', '')}_{getattr(prof, 'color_aml_markup', '')}_"
            f"{template_name}_{watermark}_{include_chords}"
        )

        if use_cache and cache_key in cls._cache:
            return cls._cache[cache_key]

        buffer = io.BytesIO()
        pagesize = cls.get_page_size(prof)

        # Top margin: exactly 58 pt (px) default for single songs, lateral margins from profile
        top_m = 58.0
        bot_m = prof.margin_bottom_mm * mm
        left_m = prof.margin_left_mm * mm
        right_m = prof.margin_right_mm * mm
        usable_w = pagesize[0] - left_m - right_m
        usable_h = pagesize[1] - top_m - bot_m

        cols = getattr(prof, "columns", 1) or 1
        if cols == 2:
            col_gap = 4.0 * mm
            col_w = (usable_w - col_gap) / 2.0
            content_w = col_w
            f1 = Frame(left_m, bot_m, col_w, usable_h, id='c1', topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
            f2 = Frame(left_m + col_w + col_gap, bot_m, col_w, usable_h, id='c2', topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
            doc = BaseDocTemplate(buffer, pagesize=pagesize, leftMargin=left_m, rightMargin=right_m, topMargin=top_m, bottomMargin=bot_m)
            doc.addPageTemplates([PageTemplate(id='TwoCol', frames=[f1, f2])])
        else:
            content_w = usable_w
            f1 = Frame(left_m, bot_m, usable_w, usable_h, id='c1', topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
            doc = BaseDocTemplate(buffer, pagesize=pagesize, leftMargin=left_m, rightMargin=right_m, topMargin=top_m, bottomMargin=bot_m)
            doc.addPageTemplates([PageTemplate(id='OneCol', frames=[f1])])

        styles = cls._build_style_sheet(prof, template_name)
        story: List[Flowable] = []

        # 1. Song Header Banner
        header_table = cls._create_song_header_table(song, styles, prof, content_w, include_chords=include_chords)
        story.append(header_table)
        story.append(Spacer(1, 3 * mm))

        # 2. Parse AML Document and Render Flowables
        aml_doc = AMLParser.parse(song.aml_content)
        content_flowables = cls._render_aml_nodes_to_flowables(aml_doc, styles, content_w, include_chords=include_chords, profile=prof)
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
        watermark: Optional[str] = None,
        include_chords: bool = True
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

        # Index Table of Songs (responsive to device usable_w)
        song_map = {s.uuid: s for s in songs}

        if usable_w < 110 * mm:
            # Layout ultra-compatto per smartphone (senza BPM o Metro)
            index_data = [["#", "Titolo", "Key"]]
            for idx, item in enumerate(setlist.items, start=1):
                s = song_map.get(item.song_uuid)
                title = s.title if s else "Sconosciuto"
                key = item.custom_key or (s.key_current if s else "-")
                index_data.append([str(idx), title, key])

            col_widths = [usable_w * 0.14, usable_w * 0.62, usable_w * 0.24]
            idx_table = Table(index_data, colWidths=col_widths)
            idx_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#212121")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
                ('FONTSIZE', (0, 1), (-1, -1), 7.5)
            ]))
        else:
            index_data = [["#", "Titolo Brano", "Artista", "Tonalità", "Note"]]
            for idx, item in enumerate(setlist.items, start=1):
                s = song_map.get(item.song_uuid)
                title = s.title if s else "Brano sconosciuto"
                artist = s.artist if s else ""
                key = item.custom_key or (s.key_current if s else "-")
                notes = item.notes or ("(Medley)" if item.is_medley else "")
                index_data.append([str(idx), title, artist, key, notes])

            col_widths = [
                usable_w * 0.07,
                usable_w * 0.40,
                usable_w * 0.28,
                usable_w * 0.12,
                usable_w * 0.13
            ]
            idx_table = Table(index_data, colWidths=col_widths)
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

            header_t = cls._create_song_header_table(s, styles, prof, usable_w, setlist_pos=f"{i+1} di {len(setlist.items)}", include_chords=include_chords)
            story.append(header_t)
            story.append(Spacer(1, 4 * mm))

            aml_doc = AMLParser.parse(s.aml_content)
            # If item has custom transposition key, transpose document
            if item.custom_key and item.custom_key != s.key_current:
                from asma_core.music_engine import MusicEngine
                delta = MusicEngine.calculate_semitone_delta(s.key_current, item.custom_key)
                aml_doc = AMLParser.transpose_document(aml_doc, semitones=delta)

            flowables = cls._render_aml_nodes_to_flowables(aml_doc, styles, usable_w, include_chords=include_chords)
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
        """Constructs typography styles conforming to the device profile, custom layout and template."""
        base_lyrics_size = profile.font_size_lyrics
        base_chords_size = profile.font_size_chords

        # Profile custom colors
        c_chord_hex = getattr(profile, "color_chords", "#B71C1C") or "#B71C1C"
        c_lyric_hex = getattr(profile, "color_lyrics", "#111111") or "#111111"
        c_aml_hex = getattr(profile, "color_aml_markup", "#4A148C") or "#4A148C"

        chord_color = colors.HexColor(c_chord_hex)
        lyric_color = colors.HexColor(c_lyric_hex)
        aml_color = colors.HexColor(c_aml_hex)

        styles = {
            "DocTitle": ParagraphStyle(
                "DocTitle",
                fontName="Helvetica-Bold",
                fontSize=base_lyrics_size * 1.3,
                leading=base_lyrics_size * 1.5,
                textColor=lyric_color
            ),
            "DocSubtitle": ParagraphStyle(
                "DocSubtitle",
                fontName="Helvetica",
                fontSize=base_lyrics_size * 0.9,
                leading=base_lyrics_size * 1.1,
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
                textColor=lyric_color
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
                textColor=lyric_color
            ),
            "CustomTagText": ParagraphStyle(
                "CustomTagText",
                fontName="Helvetica-Oblique",
                fontSize=base_lyrics_size * 0.9,
                leading=base_lyrics_size * 1.1,
                textColor=aml_color
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
        setlist_pos: Optional[str] = None,
        include_chords: bool = True
    ) -> Table:
        """Constructs an elegant header box containing metadata (Key, BPM, Time Signature, Capo)."""
        title_p = Paragraph(f"<b>{song.title}</b>", styles["DocTitle"])
        pos_str = f" [{setlist_pos}]" if setlist_pos else ""
        artist_p = Paragraph(f"<b>{song.artist}</b>{pos_str} &bull; <i>{song.author}</i>", styles["DocSubtitle"])

        if include_chords:
            meta_str = f"<b>Key:</b> {song.key_current}"
            if song.capo > 0:
                meta_str += f" | <b>Capo:</b> {song.capo}° tasto"
        else:
            meta_str = "🎤 <b>Solo Testo (Cantante)</b>"
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
        usable_width: float,
        include_chords: bool = True,
        profile: Optional[DeviceProfile] = None
    ) -> List[Flowable]:
        prof_obj = profile or DeviceProfile()
        c_chord_hex = getattr(prof_obj, "color_chords", "#B71C1C") or "#B71C1C"
        c_aml_hex = getattr(prof_obj, "color_aml_markup", "#4A148C") or "#4A148C"
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
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(c_aml_hex)),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                current_section_block.append(Spacer(1, 2 * mm))
                current_section_block.append(badge_table)
                current_section_block.append(Spacer(1, 1.5 * mm))

            elif isinstance(node, ChordGridLineNode):
                # Measure grid line: | Bm | F#7 | A | E |
                if include_chords:
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
                else:
                    # In singer's lyrics-only mode, chord grids are omitted to keep the sheet clean
                    pass

            elif isinstance(node, ChordLyricLineNode):
                # Interleaved chord-lyric line
                chord_line_parts = []
                lyric_line_parts = []

                for seg in node.segments:
                    c_text = seg.chord.chord_text if seg.chord else ""
                    l_text = seg.text or ""

                    max_len = max(len(c_text), len(l_text))
                    if c_text:
                        chord_line_parts.append(c_text.ljust(max_len))
                    else:
                        chord_line_parts.append(" " * max_len)
                    lyric_line_parts.append(l_text.ljust(max_len))

                chords_str = "".join(chord_line_parts).rstrip()
                lyrics_str = "".join(lyric_line_parts).rstrip()

                if include_chords and chords_str.strip():
                    # Atomic 2-row table for chord line over lyric line: GUARANTEES THEY NEVER SEPARATE ACROSS PAGES
                    p_chords = Paragraph(f"<font color='{c_chord_hex}'><b>{chords_str.replace(' ', '&nbsp;')}</b></font>", styles["LyricText"])
                    p_lyrics = Paragraph(lyrics_str.replace(' ', '&nbsp;'), styles["LyricText"]) if lyrics_str.strip() else Paragraph("&nbsp;", styles["LyricText"])
                    
                    pair_table = Table([[p_chords], [p_lyrics]], colWidths=[usable_width])
                    pair_table.setStyle(TableStyle([
                        ('TOPPADDING', (0, 0), (-1, -1), 0),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ]))
                    current_section_block.append(KeepTogether([pair_table, Spacer(1, 1 * mm)]))
                else:
                    # Singer lyrics-only (or line with only lyrics)
                    if lyrics_str.strip():
                        p_lyrics = Paragraph(lyrics_str.replace(' ', '&nbsp;'), styles["LyricText"])
                        current_section_block.append(KeepTogether([p_lyrics, Spacer(1, 1 * mm)]))

            elif isinstance(node, CustomTagNode):
                # Instrumental tag
                tag_p = Paragraph(f"&#9835; <b>[{node.tag_type.upper()}]:</b> {node.content}", styles["CustomTagText"])
                tag_t = Table([[tag_p]], colWidths=[usable_width])
                tag_t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDE7F6")),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(c_aml_hex)),
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
