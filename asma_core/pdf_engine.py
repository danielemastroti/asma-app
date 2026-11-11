"""
ASMA Accordi Next Generation - Device-Aware PDF Engine
High-Performance PDF Generation Engine powered by ReportLab.
Zero-AI Dependency. Conforms to SRS Cap. 13 and Blueprint Sec. 7.
"""

from __future__ import annotations
import os
import re
import io
from html import escape
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
    CustomTagNode, ChordLyricLineNode, ChordGridLineNode, CommentNode,
    EmptyLineNode
)
from asma_core.ai_service import BandAIService


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

        # 3. Footer line and page numbering (proportional to page width and safe from content overlap)
        foot_m_side = min(12.0 * mm, page_w * 0.08)
        foot_line_y = 9.5 * mm
        foot_text_y = 6.0 * mm

        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#777777"))
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(foot_m_side, foot_line_y, page_w - foot_m_side, foot_line_y)

        # Left footer: metadata
        date_str = datetime.now().strftime("%d/%m/%Y")
        footer_left = f"Generato: {date_str} {self.version_str}"
        self.drawString(foot_m_side, foot_text_y, footer_left)

        # Right footer: Page X of Y
        footer_right = f"Pagina {self._pageNumber} di {total_pages}"
        self.drawRightString(page_w - foot_m_side, foot_text_y, footer_right)

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
        include_chords: bool = True,
        user_name: Optional[str] = None
    ) -> bytes:
        """
        Generates a device-aware PDF for a single song.
        Implements memory buffer caching and smart page break protection.
        """
        prof = profile or DeviceProfile()
        cache_key = (
            f"{song.uuid}_{song.updated_at}_{prof.name}_{prof.target_device}_{prof.orientation}_"
            f"{getattr(prof, 'columns', 1)}_{getattr(prof, 'font_size_lyrics', 12)}_"
            f"{getattr(prof, 'font_size_chords', 13)}_"
            f"{getattr(prof, 'margin_left_mm', 10)}_{getattr(prof, 'margin_top_mm', 10)}_{getattr(prof, 'color_lyrics', '')}_"
            f"{getattr(prof, 'color_chords', '')}_{getattr(prof, 'color_aml_markup', '')}_"
            f"{template_name}_{watermark}_{include_chords}_{user_name}"
        )

        if use_cache and cache_key in cls._cache:
            return cls._cache[cache_key]

        buffer = io.BytesIO()
        pagesize = cls.get_page_size(prof)

        # Top margin: exactly 58 pt (px) default for single songs, lateral margins from profile
        top_m = max(float(getattr(prof, "margin_top_mm", 10.0)), 0.0) * mm
        # Bottom margin: at least 15.0 mm to guarantee no overlap with the footer line (which sits at 9.5 mm)
        bot_m = max(prof.margin_bottom_mm, 15.0) * mm
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
        header_table = cls._create_song_header_table(song, styles, prof, content_w, include_chords=include_chords, user_name=user_name)
        story.append(header_table)
        story.append(Spacer(1, 3 * mm))

        # 2. Parse AML Document and Render Flowables
        aml_text = BandAIService.ensure_section_spacing_aml(song.aml_content)
        aml_doc = AMLParser.parse(aml_text)
        content_flowables = cls._render_aml_nodes_to_flowables(aml_doc, styles, content_w, include_chords=include_chords, profile=prof)
        story.extend(content_flowables)

        # Custom Canvas Factory for page numbering and watermark
        def canvas_maker(*args, **kwargs):
            c = NumberedCanvas(*args, **kwargs)
            c.watermark_text = watermark
            c.document_title = song.title
            c.version_str = f"| Rev #{song.current_revision}"
            if user_name:
                c.version_str += f" | {user_name}"
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
        include_chords: bool = True,
        user_name: Optional[str] = None
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
            date_raw = str(setlist.date).strip()
            date_parts = date_raw.split("T")[0].split("-")
            if len(date_parts) == 3 and len(date_parts[0]) == 4:
                date_display = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
            else:
                date_display = date_raw
            story.append(Paragraph(f"Data Esecuzione: <b>{date_display}</b>", styles["SectionText"]))
        if user_name:
            story.append(Paragraph(f"Musicista: <b>{user_name}</b>", styles["SectionText"]))
        if setlist.description:
            story.append(Paragraph(f"<i>{setlist.description}</i>", styles["SectionText"]))

        story.append(Spacer(1, 10 * mm))

        # Index Table of Songs (responsive to device usable_w)
        song_map = {s.uuid: s for s in songs}
        from asma_core.music_engine import MusicEngine

        if usable_w < 110 * mm:
            # Layout ultra-compatto per smartphone (senza BPM o Metro)
            index_data = [["#", "Titolo", "Tonalità"]]
            for idx, item in enumerate(setlist.items, start=1):
                s = song_map.get(item.song_uuid)
                title = s.title if s else "Sconosciuto"
                raw_k = item.custom_key or (s.key_current if s else "-")
                key = MusicEngine.convert_notation(raw_k, "ITA") if raw_k and raw_k != "-" else "-"
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
                raw_k = item.custom_key or (s.key_current if s else "-")
                key = MusicEngine.convert_notation(raw_k, "ITA") if raw_k and raw_k != "-" else "-"
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

            header_t = cls._create_song_header_table(
                s,
                styles,
                prof,
                usable_w,
                setlist_pos=f"{i+1} di {len(setlist.items)}",
                include_chords=include_chords,
                custom_key=item.custom_key,
                user_name=user_name
            )
            story.append(header_t)
            story.append(Spacer(1, 4 * mm))

            aml_text = BandAIService.ensure_section_spacing_aml(s.aml_content)
            aml_doc = AMLParser.parse(aml_text)
            # If item has custom transposition key, transpose document
            if item.custom_key and item.custom_key != s.key_current:
                from asma_core.music_engine import MusicEngine
                delta = MusicEngine.calculate_semitone_delta(s.key_current, item.custom_key)
                aml_doc = AMLParser.transpose_document(aml_doc, semitones=delta)

            flowables = cls._render_aml_nodes_to_flowables(aml_doc, styles, usable_w, include_chords=include_chords, profile=prof)
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

    TAB_STRING_PREFIX = re.compile(
        r"^\s*([A-Ga-g1-6][#b]?|[hH]igh\s*[eE]|[lL]ow\s*[eE])\s*[:|]\s*[-0-9hpbrx/~\\|\s]{3,}"
    )
    TAB_HEADER = re.compile(
        r"(?i)^\s*(\[|\()?(\b(intro|solo|riff|assolo|chitarra|guitar|verse|chorus|strofa|ritornello|outro)\b\s+)*"
        r"\b(tab|tablatura|tablature|tabs)\b"
        r"(\s+\b(intro|solo|riff|assolo|chitarra|guitar|verse|chorus|strofa|ritornello|outro|1|2|3)\b)*"
        r"(\]|\))?\s*[:\-]?\s*$"
    )

    @classmethod
    def _format_lyric_spaces(cls, text: str) -> str:
        """Preserves indentation and multi-space alignment while keeping breakable single spaces between words."""
        if not text:
            return ""
        lead_len = len(text) - len(text.lstrip(" "))
        content = text.lstrip(" ")
        content = re.sub(r" {2,}", lambda m: "&nbsp;" * (len(m.group(0)) - 1) + " ", content)
        return ("&nbsp;" * lead_len) + content

    @classmethod
    def _format_chord_spaces(cls, text: str) -> str:
        """Preserves chord horizontal alignment while allowing line breaks between distant chord groups."""
        if not text:
            return ""
        lead_len = len(text) - len(text.lstrip(" "))
        content = text.lstrip(" ")
        content = re.sub(r" {2,}", lambda m: "&nbsp;" * (len(m.group(0)) - 1) + " ", content)
        return ("&nbsp;" * lead_len) + content

    @classmethod
    def is_guitar_tab_line(cls, line: str) -> bool:
        """Rileva se una riga di testo appartiene a una tablatura di chitarra/basso o staff tab."""
        s = line.strip()
        if not s:
            return False
        if cls.TAB_HEADER.match(s):
            return True
        if cls.TAB_STRING_PREFIX.match(s):
            return True
        # Riga tab racchiusa tra pipe con trattini e simboli di tab
        if s.startswith("|") and s.endswith("|") and len(s) >= 6:
            dashes = s.count("-")
            if dashes >= 4 and not re.search(r"[A-Za-z]{3,}", s):
                return True
        # Riga composta prevalentemente da trattini e cifre tipica di intavolature
        if s.count("-") >= 5:
            non_ws = len(re.sub(r"\s+", "", s))
            if non_ws > 0 and (s.count("-") / non_ws) >= 0.4:
                if not re.search(r"[a-zA-Z]{4,}", s):
                    return True
        return False

    @classmethod
    def _create_song_header_table(
        cls,
        song: Song,
        styles: Dict[str, ParagraphStyle],
        profile: DeviceProfile,
        usable_width: float,
        setlist_pos: Optional[str] = None,
        include_chords: bool = True,
        custom_key: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> Table:
        """Constructs an elegant header box containing metadata (Tonalità latina, BPM, Time Signature, Capo)."""
        title_p = Paragraph(f"<b>{song.title}</b>", styles["DocTitle"])
        pos_str = f" [{setlist_pos}]" if setlist_pos else ""

        parts = []
        if song.artist and song.artist.strip():
            parts.append(f"<b>{song.artist.strip()}</b>{pos_str}")
        elif pos_str:
            parts.append(f"<b>{pos_str.strip()}</b>")

        if song.author and song.author.strip() and song.author.strip().lower() != (song.artist or "").strip().lower():
            parts.append(f"<i>{song.author.strip()}</i>")

        from asma_core.music_engine import MusicEngine
        raw_key = custom_key or song.key_current or "-"
        ita_key = MusicEngine.convert_notation(raw_key, "ITA") if raw_key and raw_key != "-" else "-"

        if user_name and user_name.strip():
            clean_pseudo = re.sub(r'\(.*?\)', '', user_name).strip()
            if clean_pseudo:
                parts.append(f"<b>{clean_pseudo}</b>")

        if include_chords:
            meta_info = f"<b>Tonalità:</b> {ita_key}"
            if song.capo > 0:
                meta_info += f" | <b>Capo:</b> {song.capo}° tasto"
            parts.append(meta_info)
        else:
            parts.append(f"<b>Solo Testo</b> &bull; <b>Tonalità:</b> {ita_key}")

        sub_text = " &bull; ".join(parts)
        subtitle_p = Paragraph(sub_text, styles["DocSubtitle"])

        logo_flowable = None
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "band_logo.png")
        if not os.path.exists(logo_path):
            logo_path = "assets/band_logo.png"
        if os.path.exists(logo_path):
            try:
                from reportlab.platypus import Image as RLImage
                # Logo in proporzione nativa 2.79:1 (30mm x 10.7mm), elegante e ben visibile
                logo_flowable = RLImage(logo_path, width=30 * mm, height=10.7 * mm)
            except Exception:
                pass

        if logo_flowable:
            col2_w = min(34 * mm, usable_width * 0.25)
            col1_w = usable_width - col2_w

            table_data = [
                [title_p, logo_flowable],
                [subtitle_p, ""]
            ]
            t = Table(table_data, colWidths=[col1_w, col2_w])
            t.setStyle(TableStyle([
                ('SPAN', (1, 0), (1, 1)),
                ('ALIGN', (1, 0), (1, 1), 'RIGHT'),
                ('VALIGN', (1, 0), (1, 1), 'MIDDLE'),
                ('VALIGN', (0, 0), (0, 1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('LINEBELOW', (0, 1), (-1, 1), 1.0, colors.HexColor("#333333"))
            ]))
            return t

        table_data = [
            [title_p],
            [subtitle_p]
        ]
        t = Table(table_data, colWidths=[usable_width])
        t.setStyle(TableStyle([
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
        base_chords_size = getattr(prof_obj, "font_size_chords", 13.0) or 13.0
        base_lyrics_size = getattr(prof_obj, "font_size_lyrics", 12.0) or 12.0
        """
        Converts AML AST nodes into ReportLab Flowables.
        Groups section items into KeepTogether blocks to prevent orphan lines.
        """
        flowables: List[Flowable] = []
        pending_badge: Optional[Flowable] = None
        last_was_inst_marker = False
        in_tab_block = False

        def add_flowable(item: Flowable):
            nonlocal pending_badge
            if pending_badge:
                # Mantiene il badge di sezione unito alla prima riga evitando KeepTogether annidati (che forzano salti pagina indebiti)
                content = item._content if isinstance(item, KeepTogether) else [item]
                flowables.append(KeepTogether([pending_badge, Spacer(1, 1.5 * mm)] + content))
                pending_badge = None
            else:
                flowables.append(item)

        for node in doc.nodes:
            if isinstance(node, DirectiveNode):
                d_name = node.name.strip().lower()
                d_val = (node.value or "").strip()
                if d_name in ["sot", "start_of_tab", "tab", "tablatura"]:
                    in_tab_block = True
                    continue
                elif d_name in ["eot", "end_of_tab"]:
                    in_tab_block = False
                    continue

                if in_tab_block:
                    continue

                # Header metadata directives (already rendered in PDF title header)
                if d_name in ["title", "t", "artist", "a", "key", "tempo", "bpm", "capo", "time"]:
                    continue

                # Band notes and comments: {c: ...} or {comment: ...}
                if d_name in ["c", "comment", "ci", "cb"]:
                    if pending_badge:
                        flowables.append(pending_badge)
                        pending_badge = None
                    note_text = d_val or "Nota"
                    comm_p = Paragraph(f"<font color='{c_aml_hex}'><b><i>&#9835; [NOTA]: {escape(note_text)}</i></b></font>", styles["DocSubtitle"])
                    add_flowable(KeepTogether([comm_p, Spacer(1, 1.2 * mm)]))
                    last_was_inst_marker = False
                    continue

                # Section directives: {soc}, {start_of_chorus}, {sov}, {start_of_verse}, {sob}, {start_of_bridge}
                if d_name in ["soc", "start_of_chorus", "chorus", "ritornello"]:
                    if pending_badge:
                        flowables.append(pending_badge)
                        pending_badge = None
                    if flowables and not isinstance(flowables[-1], Spacer):
                        flowables.append(Spacer(1, 3.5 * mm))
                    badge_title = d_val.upper() if d_val else "RITORNELLO"
                    badge_text = f"&nbsp;&nbsp;<b>[{badge_title}]</b>&nbsp;&nbsp;"
                    p = Paragraph(badge_text, styles["SectionBadge"])
                    badge_table = Table([[p]], colWidths=[usable_width])
                    badge_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(c_aml_hex)),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ]))
                    pending_badge = badge_table
                    last_was_inst_marker = False
                    continue

                if d_name in ["sov", "start_of_verse", "verse", "strofa"]:
                    if pending_badge:
                        flowables.append(pending_badge)
                        pending_badge = None
                    if flowables and not isinstance(flowables[-1], Spacer):
                        flowables.append(Spacer(1, 3.5 * mm))
                    badge_title = d_val.upper() if d_val else "STROFA"
                    badge_text = f"&nbsp;&nbsp;<b>[{badge_title}]</b>&nbsp;&nbsp;"
                    p = Paragraph(badge_text, styles["SectionBadge"])
                    badge_table = Table([[p]], colWidths=[usable_width])
                    badge_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(c_aml_hex)),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ]))
                    pending_badge = badge_table
                    last_was_inst_marker = False
                    continue

                if d_name in ["sob", "start_of_bridge", "bridge", "speciale"]:
                    if pending_badge:
                        flowables.append(pending_badge)
                        pending_badge = None
                    if flowables and not isinstance(flowables[-1], Spacer):
                        flowables.append(Spacer(1, 3.5 * mm))
                    badge_title = d_val.upper() if d_val else "SPECIALE"
                    badge_text = f"&nbsp;&nbsp;<b>[{badge_title}]</b>&nbsp;&nbsp;"
                    p = Paragraph(badge_text, styles["SectionBadge"])
                    badge_table = Table([[p]], colWidths=[usable_width])
                    badge_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(c_aml_hex)),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ]))
                    pending_badge = badge_table
                    last_was_inst_marker = False
                    continue

                if d_name in ["eoc", "end_of_chorus", "eov", "end_of_verse", "eob", "end_of_bridge"]:
                    if pending_badge:
                        flowables.append(pending_badge)
                        pending_badge = None
                    if flowables and not isinstance(flowables[-1], Spacer):
                        flowables.append(Spacer(1, 2.0 * mm))
                    continue

                # Column break: {colb} or {column_break}
                if d_name in ["colb", "column_break", "col_break"]:
                    if pending_badge:
                        flowables.append(pending_badge)
                        pending_badge = None
                    if cols == 2:
                        flowables.append(FrameBreak())
                    else:
                        flowables.append(Spacer(1, 4.0 * mm))
                    continue

                # Any other directive with value (e.g. custom tag)
                if d_val:
                    comm_p = Paragraph(f"<font color='{c_aml_hex}'><b>[{d_name.upper()}]:</b> {escape(d_val)}</font>", styles["DocSubtitle"])
                    add_flowable(KeepTogether([comm_p, Spacer(1, 1.0 * mm)]))
                    last_was_inst_marker = False
                continue

            elif isinstance(node, SectionNode):
                sec_name = node.section_name.strip().lower()
                sec_label = (node.label or "").strip().lower()
                # Elimina sempre le sezioni e i badge dedicati a tablature
                if any(k in sec_name for k in ["tab", "tablatura", "tabs", "riff_tab", "guitar_tab"]) or "tab" in sec_label:
                    in_tab_block = True
                    continue
                else:
                    in_tab_block = False

                if pending_badge:
                    flowables.append(pending_badge)
                    pending_badge = None

                # Separazione spaziale elegante e proporzionata prima di ogni nuova sezione
                if flowables and not isinstance(flowables[-1], Spacer):
                    flowables.append(Spacer(1, 3.5 * mm))

                # Section badge
                badge_text = f"&nbsp;&nbsp;<b>[{node.section_name.upper()}]</b>&nbsp;&nbsp;"
                p = Paragraph(badge_text, styles["SectionBadge"])
                badge_table = Table([[p]], colWidths=[usable_width])
                badge_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(c_aml_hex)),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                pending_badge = badge_table
                last_was_inst_marker = False

            elif isinstance(node, ChordGridLineNode):
                if in_tab_block or cls.is_guitar_tab_line(node.to_aml()):
                    continue
                # Measure grid line senza tabelle: accordi divisi dal simbolo |
                if include_chords:
                    grid_tokens = []
                    for measure in node.measures:
                        m_txt = " ".join(measure).strip()
                        if m_txt:
                            grid_tokens.append(m_txt)
                    grid_line_text = " | ".join(grid_tokens)
                    if grid_line_text:
                        p_grid = Paragraph(f"<font color='{c_chord_hex}' size='{base_chords_size}pt'><b>{grid_line_text}</b></font>", styles["ChordText"])
                        add_flowable(KeepTogether([Spacer(1, 1.0 * mm), p_grid, Spacer(1, 1.2 * mm)]))
                        last_was_inst_marker = False
                else:
                    # Nel PDF solo testo per il cantante, le sequenze di accordi/battute sono segnalate come (Strumentale)
                    if not last_was_inst_marker:
                        p_inst = Paragraph(f"<font color='{c_aml_hex}'><b><i>&#9835; (Strumentale)</i></b></font>", styles["DocSubtitle"])
                        add_flowable(KeepTogether([p_inst, Spacer(1, 1.2 * mm)]))
                        last_was_inst_marker = True

            elif isinstance(node, ChordLyricLineNode):
                if in_tab_block:
                    continue
                raw_aml = node.to_aml()
                # Interleaved chord-lyric line
                chord_line_parts = []
                lyric_line_parts = []

                for idx, seg in enumerate(node.segments):
                    c_text = seg.chord.chord_text if seg.chord else ""
                    l_text = seg.text or ""

                    has_following_chord = any(s.chord for s in node.segments[idx + 1:])
                    if c_text and has_following_chord and (len(l_text) <= len(c_text)):
                        gap = 2
                        max_len = len(c_text) + gap
                        chord_line_parts.append(c_text + " " * gap)
                        lyric_line_parts.append(l_text.ljust(max_len))
                    else:
                        max_len = max(len(c_text), len(l_text))
                        if c_text:
                            chord_line_parts.append(c_text.ljust(max_len))
                        else:
                            chord_line_parts.append(" " * max_len)
                        lyric_line_parts.append(l_text.ljust(max_len))

                chords_str = "".join(chord_line_parts).rstrip()
                lyrics_str = "".join(lyric_line_parts).rstrip()

                # Elimina sempre qualsiasi riga di tablatura per chitarra/basso
                if cls.is_guitar_tab_line(lyrics_str) or cls.is_guitar_tab_line(raw_aml):
                    continue

                if include_chords and chords_str.strip():
                    # Atomic 2-row table for chord line over lyric line: mai separati tra pagine
                    p_chords = Paragraph(f"<font color='{c_chord_hex}' size='{base_chords_size}pt'><b>{cls._format_chord_spaces(chords_str)}</b></font>", styles["ChordText"])
                    p_lyrics = Paragraph(cls._format_lyric_spaces(lyrics_str), styles["LyricText"]) if lyrics_str.strip() else Paragraph("&nbsp;", styles["LyricText"])
                    
                    pair_table = Table([[p_chords], [p_lyrics]], colWidths=[usable_width])
                    pair_table.setStyle(TableStyle([
                        ('TOPPADDING', (0, 0), (-1, -1), 0),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ]))
                    add_flowable(KeepTogether([pair_table, Spacer(1, 0.8 * mm)]))
                    last_was_inst_marker = False
                else:
                    # Check if lyrics_str actually contains pure chords (es. SIb/FA  DO/MI   RE7/9+)
                    l_tokens = [t.strip("[](),|") for t in lyrics_str.split() if t.strip("[](),|")]
                    is_pure_chords = False
                    if l_tokens and not re.search(r"\b\w+'\w+\b|[.,!?;:]", lyrics_str):
                        from asma_core.music_engine import ITALIAN_LOWERCASE_WORDS, MusicEngine
                        if not any(t.lower() in ITALIAN_LOWERCASE_WORDS for t in l_tokens):
                            valid_cnt = sum(1 for t in l_tokens if MusicEngine.parse_chord(t))
                            if valid_cnt > 0 and (valid_cnt == len(l_tokens) or (valid_cnt / len(l_tokens)) >= 0.75):
                                is_pure_chords = True

                    if is_pure_chords:
                        if not include_chords:
                            # Nel PDF cantante solo testo, una sequenza di accordi va SEMPRE segnalata come (Strumentale)
                            if not last_was_inst_marker:
                                p_inst = Paragraph(f"<font color='{c_aml_hex}'><b><i>&#9835; (Strumentale)</i></b></font>", styles["DocSubtitle"])
                                add_flowable(KeepTogether([p_inst, Spacer(1, 1.2 * mm)]))
                                last_was_inst_marker = True
                        else:
                            # Nel PDF con accordi, renderizzali in evidenza come riga di accordi con stile ChordText
                            p_chords = Paragraph(f"<font color='{c_chord_hex}' size='{base_chords_size}pt'><b>{cls._format_chord_spaces(lyrics_str)}</b></font>", styles["ChordText"])
                            add_flowable(KeepTogether([Spacer(1, 1.2 * mm), p_chords, Spacer(1, 1.5 * mm)]))
                            last_was_inst_marker = False
                    elif lyrics_str.strip():
                        # Singer lyrics-only (or line with only lyrics)
                        p_lyrics = Paragraph(cls._format_lyric_spaces(lyrics_str), styles["LyricText"])
                        add_flowable(KeepTogether([p_lyrics, Spacer(1, 0.8 * mm)]))
                        last_was_inst_marker = False
                    elif chords_str.strip():
                        # Sequenza di soli accordi senza testo (es. MI | DO | LA) -> segnalato come (Strumentale)
                        if not last_was_inst_marker:
                            p_inst = Paragraph(f"<font color='{c_aml_hex}'><b><i>&#9835; (Strumentale)</i></b></font>", styles["DocSubtitle"])
                            add_flowable(KeepTogether([p_inst, Spacer(1, 1.2 * mm)]))
                            last_was_inst_marker = True

            elif isinstance(node, CustomTagNode):
                tag_label = node.tag_type.strip().lower()
                if in_tab_block or tag_label in ["tab", "tablatura", "sot", "eot"] or cls.is_guitar_tab_line(node.content or ""):
                    continue
                # Tag strumentale o assolo (es. {guitar: solo}, {assolo}, ecc.)
                tag_label = node.tag_type.strip().lower()
                is_solo = any(k in tag_label for k in ["solo", "assolo", "instrumental", "guitar", "chitarra", "piano", "sax", "stacco"])
                if not include_chords and is_solo:
                    content_str = f" — {node.content}" if node.content and node.content.strip() else ""
                    tag_p = Paragraph(f"<font color='{c_aml_hex}'><b><i>&#9835; (Strumentale{content_str})</i></b></font>", styles["CustomTagText"])
                else:
                    tag_p = Paragraph(f"&#9835; <b>[{node.tag_type.upper()}]:</b> {node.content}", styles["CustomTagText"])

                tag_t = Table([[tag_p]], colWidths=[usable_width])
                tag_t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDE7F6")),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(c_aml_hex)),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                add_flowable(KeepTogether([tag_t, Spacer(1, 0.8 * mm)]))
                last_was_inst_marker = True

            elif isinstance(node, CommentNode):
                if in_tab_block or cls.is_guitar_tab_line(node.text):
                    continue
                comm_p = Paragraph(f"<i># {node.text}</i>", styles["DocSubtitle"])
                add_flowable(KeepTogether([comm_p, Spacer(1, 0.8 * mm)]))
                last_was_inst_marker = False

            elif isinstance(node, EmptyLineNode):
                if in_tab_block:
                    continue
                if pending_badge:
                    flowables.append(pending_badge)
                    pending_badge = None
                # Spaziatura contenuta tra strofe/paragrafi (senza creare vuoti enormi)
                if flowables and not isinstance(flowables[-1], Spacer):
                    flowables.append(Spacer(1, 2.0 * mm))
                last_was_inst_marker = False

        if pending_badge:
            flowables.append(pending_badge)

        return flowables

    @classmethod
    def clear_cache(cls) -> None:
        """Empties the in-memory PDF buffer cache."""
        cls._cache.clear()
