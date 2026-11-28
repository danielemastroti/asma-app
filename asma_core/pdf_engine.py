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
from reportlab.pdfbase import pdfmetrics

from asma_core.models import Song, DeviceProfile, Setlist, Repertoire
from asma_core.aml_parser import (
    AMLParser, AMLDocument, DirectiveNode, SectionNode,
    CustomTagNode, ChordLyricLineNode, ChordGridLineNode, CommentNode,
    EmptyLineNode, MedleySongStartNode, MedleySongEndNode
)
from asma_core.ai_service import BandAIService


# Palette elegante di 20 colori ad alto contrasto per i titoli degli spezzoni Medley
MEDLEY_COLORS = [
    "#0284c7",  # 1. Sky Blue
    "#d97706",  # 2. Warm Amber
    "#059669",  # 3. Emerald Green
    "#7c3aed",  # 4. Deep Violet
    "#e11d48",  # 5. Vivid Rose
    "#0891b2",  # 6. Deep Cyan
    "#ea580c",  # 7. Bright Orange
    "#4f46e5",  # 8. Royal Indigo
    "#16a34a",  # 9. Grass Green
    "#db2777",  # 10. Magenta Pink
    "#2563eb",  # 11. Cobalt Blue
    "#ca8a04",  # 12. Goldenrod
    "#0d9488",  # 13. Dark Teal
    "#9333ea",  # 14. Violet
    "#dc2626",  # 15. Crimson
    "#1d4ed8",  # 16. Sapphire
    "#b45309",  # 17. Ochre
    "#047857",  # 18. Forest
    "#6d28d9",  # 19. Iris
    "#be123c",  # 20. Ruby
]


class SmartDocTemplate(BaseDocTemplate):
    """
    Subclass of BaseDocTemplate that prevents blank pages by suppressing
    redundant PageBreak calls when the current frame has no drawn content.
    """
    def handle_pageBreak(self, slow=None):
        flowable_count = getattr(self, '_curPageFlowableCount', 0)
        at_top = getattr(getattr(self, 'frame', None), '_atTop', 0)
        if flowable_count == 0 or at_top:
            return
        super().handle_pageBreak(slow=slow)


class SmartSimpleDocTemplate(SimpleDocTemplate):
    """
    Subclass of SimpleDocTemplate that prevents blank pages by suppressing
    redundant PageBreak calls when the current frame has no drawn content.
    """
    def handle_pageBreak(self, slow=None):
        flowable_count = getattr(self, '_curPageFlowableCount', 0)
        at_top = getattr(getattr(self, 'frame', None), '_atTop', 0)
        if flowable_count == 0 or at_top:
            return
        super().handle_pageBreak(slow=slow)



# Standard custom page sizes (in points, 1 point = 1/72 inch)
PAGE_SIZES: Dict[str, Tuple[float, float]] = {
    "pc_a4": portrait(A4),
    "pc_a4_landscape": portrait(A4),
    "tablet": portrait(A4),
    "ipad": (174.1 * mm, 224.0 * mm),
    "smartphone": (100 * mm, 210 * mm)  # Layout PDF sempre verticale
}


class AtomicTable(Table):
    """
    Tabella atomica che non si spezza MAI a meta' tra pagine o colonne in ReportLab.
    Se lo spazio disponibile nel frame non e' sufficiente a contenerla interamente,
    l'intera tabella viene spostata integralmente all'inizio del frame/pagina successiva.
    """
    def split(self, availWidth, availHeight):
        return []


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
        self.margin_bottom_mm: Optional[float] = None
        self.margin_side_mm: Optional[float] = None

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
            self.drawString(15 * mm, page_h - 10 * mm, f"ASMA — {self.document_title}")
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(15 * mm, page_h - 11 * mm, page_w - 15 * mm, page_h - 11 * mm)

        # 3. Footer line and page numbering (proportional to page width and safe from content overlap/bezel cutoff)
        side_m = getattr(self, "margin_side_mm", None)
        if side_m is not None and side_m > 0:
            foot_m_side = max(side_m * mm, 14.0 * mm)
        else:
            foot_m_side = max(14.0 * mm, page_w * 0.08)

        bot_margin = float(getattr(self, "margin_bottom_mm", 12.0) or 12.0)
        foot_line_y = max(6.0, bot_margin - 3.5) * mm
        foot_text_y = max(3.5, bot_margin - 7.5) * mm

        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#777777"))
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(foot_m_side, foot_line_y, page_w - foot_m_side, foot_line_y)

        # Left footer: metadata (preserves the actual song modification date instead of application restart date)
        if getattr(self, "song_updated_date", None):
            date_str = f"Modificato: {self.song_updated_date}"
        else:
            date_str = f"Data: {datetime.now().strftime('%d/%m/%Y')}"
        footer_left = f"{date_str} {self.version_str}"
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
            f"v3_{song.uuid}_{song.updated_at}_{prof.name}_{prof.target_device}_{prof.orientation}_"
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
        bot_m = max(float(getattr(prof, "margin_bottom_mm", 12.0) or 12.0), 12.0) * mm
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
            doc = SmartDocTemplate(buffer, pagesize=pagesize, leftMargin=left_m, rightMargin=right_m, topMargin=top_m, bottomMargin=bot_m)
            doc.addPageTemplates([PageTemplate(id='TwoCol', frames=[f1, f2])])
        else:
            content_w = usable_w
            f1 = Frame(left_m, bot_m, usable_w, usable_h, id='c1', topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0)
            doc = SmartDocTemplate(buffer, pagesize=pagesize, leftMargin=left_m, rightMargin=right_m, topMargin=top_m, bottomMargin=bot_m)
            doc.addPageTemplates([PageTemplate(id='OneCol', frames=[f1])])

        styles = cls._build_style_sheet(prof, template_name)
        story: List[Flowable] = []

        # 1. Song Header Banner
        header_table = cls._create_song_header_table(song, styles, prof, content_w, include_chords=include_chords, user_name=user_name)
        story.append(header_table)
        story.append(Spacer(1, 3 * mm))

        # 2. Parse AML Document and Render Flowables
        aml_source = song.aml_content or ""
        aml_source = re.sub(r'\[/?AUTO-COMPLETATO\]\n?', '', aml_source, flags=re.IGNORECASE)
        is_a4 = (
            getattr(prof, "target_device", "") == "pc_a4"
            or getattr(prof, "device_type", "") == "printable_a4"
            or "foglio" in (getattr(prof, "name", "") or "").lower()
        )
        if is_a4 and aml_source:
            # Se il brano ha già direttive esplicite di salto pagina ({np}), rispetta l'impaginazione manuale dell'autore
            has_manual_np = bool(re.search(r'\{(?:np|new_page|page_break|salto_pagina)\}', aml_source, re.IGNORECASE))
            if not has_manual_np:
                _, fragments = AMLParser.split_medley_fragments(aml_source)
                if len(fragments) > 1:
                    # Re-pack fragments intelligently for A4 capacity: 1 col = 40 lines, 2 cols = 52 lines
                    target_dev_name = "Foglio a 4 stampabile" if cols == 1 else "Tablet"
                    aml_source, _ = AMLParser.format_medley_pages(
                        aml_source,
                        strategy="smart_fit",
                        target_device=target_dev_name
                    )

        aml_text = BandAIService.ensure_section_spacing_aml(aml_source)
        aml_doc = AMLParser.parse(aml_text)
        content_flowables = cls._render_aml_nodes_to_flowables(aml_doc, styles, content_w, include_chords=include_chords, profile=prof)
        story.extend(content_flowables)

        # Custom Canvas Factory for page numbering and watermark
        def canvas_maker(*args, **kwargs):
            c = NumberedCanvas(*args, **kwargs)
            c.watermark_text = watermark
            c.document_title = song.title
            c.version_str = f"| Rev #{song.current_revision}"
            updated_raw = getattr(song, "updated_at", None) or getattr(song, "created_at", None)
            if updated_raw:
                try:
                    dt = datetime.fromisoformat(str(updated_raw).replace("Z", "+00:00"))
                    c.song_updated_date = dt.strftime("%d/%m/%Y")
                except Exception:
                    c.song_updated_date = None
            else:
                c.song_updated_date = None
            c.margin_bottom_mm = float(getattr(prof, "margin_bottom_mm", 12.0) or 12.0)
            c.margin_side_mm = max(float(getattr(prof, "margin_left_mm", 10.0) or 10.0), float(getattr(prof, "margin_right_mm", 10.0) or 10.0))
            if user_name:
                clean_foot = re.sub(r'\(.*?\)', '', user_name).strip()
                if clean_foot:
                    c.version_str += f" | ({clean_foot})"
            return c

        doc.build(story, canvasmaker=canvas_maker)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        if use_cache:
            if len(cls._cache) >= 25:
                # Evict oldest keys to keep memory tightly controlled
                for k in list(cls._cache.keys())[:10]:
                    cls._cache.pop(k, None)
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

        doc = SmartSimpleDocTemplate(
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
            clean_cover = re.sub(r'\(.*?\)', '', user_name).strip()
            if clean_cover:
                story.append(Paragraph(f"Musicista: <b>({clean_cover})</b>", styles["SectionText"]))
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
            aml_text = re.sub(r'\[/?AUTO-COMPLETATO\]\n?', '', aml_text, flags=re.IGNORECASE)
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
            c.margin_bottom_mm = float(getattr(prof, "margin_bottom_mm", 12.0) or 12.0)
            c.margin_side_mm = max(float(getattr(prof, "margin_left_mm", 10.0) or 10.0), float(getattr(prof, "margin_right_mm", 10.0) or 10.0))
            return c

        doc.build(story, canvasmaker=canvas_maker)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @classmethod
    def generate_repertoire_pdf(
        cls,
        repertoire_name: str,
        songs: List[Song],
        profile: Optional[DeviceProfile] = None,
        template_name: str = "standard",
        watermark: Optional[str] = None,
        user_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> bytes:
        """
        Generates a clean, beautifully formatted PDF catalog/list of all songs in a repertoire.
        Includes band logo, summary metadata, and a responsive table with:
        #, Titolo Brano, Artista, Tonalità (ITA), BPM, Durata.
        """
        from asma_core.music_engine import MusicEngine
        prof = profile or DeviceProfile()
        buffer = io.BytesIO()
        pagesize = cls.get_page_size(prof)

        left_m = prof.margin_left_mm * mm
        right_m = prof.margin_right_mm * mm
        top_m = max(float(getattr(prof, "margin_top_mm", 10.0) or 10.0), 10.0) * mm
        bot_m = max(float(getattr(prof, "margin_bottom_mm", 12.0) or 12.0), 12.0) * mm
        usable_w = pagesize[0] - left_m - right_m

        doc = SmartSimpleDocTemplate(
            buffer,
            pagesize=pagesize,
            leftMargin=left_m,
            rightMargin=right_m,
            topMargin=top_m,
            bottomMargin=bot_m
        )

        styles = cls._build_style_sheet(prof, template_name)
        story: List[Flowable] = []

        # 1. Band Logo
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "band_logo.png")
        if not os.path.exists(logo_path):
            logo_path = "assets/band_logo.png"
        if os.path.exists(logo_path):
            try:
                from reportlab.platypus import Image as RLImage
                story.append(RLImage(logo_path, width=42 * mm, height=16.8 * mm))
                story.append(Spacer(1, 4 * mm))
            except Exception:
                pass

        # 2. Header Title & Subtitle
        rep_clean = repertoire_name.strip() if repertoire_name else "Repertorio Band"
        story.append(Paragraph(f"<b>ELENCO BRANI — {rep_clean.upper()}</b>", styles["DocTitle"]))

        date_str = datetime.now().strftime("%d/%m/%Y")
        meta_parts = [f"Totale Brani: <b>{len(songs)}</b>", f"Data: <b>{date_str}</b>"]
        if user_name:
            clean_pseudo = re.sub(r'\(.*?\)', '', user_name).strip()
            if clean_pseudo:
                meta_parts.append(f"Musicista: <b>({clean_pseudo})</b>")
        if description and description.strip():
            meta_parts.append(f"<i>{description.strip()}</i>")

        story.append(Paragraph(" &bull; ".join(meta_parts), styles["SectionText"]))
        story.append(Spacer(1, 5 * mm))

        # 3. Helper to extract song attributes whether Song model or dict
        def _get_val(obj: Any, key: str, default: Any = "") -> Any:
            if hasattr(obj, key):
                v = getattr(obj, key)
                return v if v is not None else default
            if isinstance(obj, dict):
                v = obj.get(key)
                return v if v is not None else default
            return default

        # Sort songs alphabetically by title
        sorted_songs = sorted(songs, key=lambda s: str(_get_val(s, "title", "")).strip().lower())

        # 4. Table Construction
        if usable_w < 115 * mm:
            # Phone / ultra-compact layout: #, Titolo, Tonalità, BPM
            table_data = [["#", "Titolo Brano", "Tonalità", "BPM"]]
            for idx, s in enumerate(sorted_songs, start=1):
                raw_k = _get_val(s, "key_current", "") or _get_val(s, "key_original", "") or "-"
                key_ita = MusicEngine.convert_notation(raw_k, "ITA") if raw_k and raw_k != "-" else "-"
                bpm_val = _get_val(s, "bpm", 0)
                bpm_str = f"{bpm_val}" if bpm_val else "-"
                s_title = _get_val(s, "title", "Brano")
                title_p = Paragraph(f"<b>{escape(s_title)}</b>", styles["TableCellBold"])
                table_data.append([str(idx), title_p, key_ita, bpm_str])

            col_widths = [usable_w * 0.12, usable_w * 0.54, usable_w * 0.20, usable_w * 0.14]
        else:
            # Tablet / A4 layout: #, Titolo, Artista, Tonalità, BPM, Durata
            table_data = [["#", "Titolo Brano", "Artista", "Tonalità", "BPM", "Durata"]]
            for idx, s in enumerate(sorted_songs, start=1):
                raw_k = _get_val(s, "key_current", "") or _get_val(s, "key_original", "") or "-"
                key_ita = MusicEngine.convert_notation(raw_k, "ITA") if raw_k and raw_k != "-" else "-"
                bpm_val = _get_val(s, "bpm", 0)
                bpm_str = f"{bpm_val} BPM" if bpm_val else "-"
                dur_val = _get_val(s, "duration_seconds", 0)
                dur_str = f"{int(dur_val) // 60}:{int(dur_val) % 60:02d}" if (dur_val and int(dur_val) > 0) else "-"
                s_title = _get_val(s, "title", "Brano")
                s_artist = _get_val(s, "artist", "-")
                title_p = Paragraph(f"<b>{escape(s_title)}</b>", styles["TableCellBold"])
                artist_p = Paragraph(escape(s_artist), styles["TableCell"])
                table_data.append([str(idx), title_p, artist_p, key_ita, bpm_str, dur_str])

            col_widths = [
                usable_w * 0.06,
                usable_w * 0.38,
                usable_w * 0.26,
                usable_w * 0.12,
                usable_w * 0.10,
                usable_w * 0.08
            ]

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ('FONTSIZE', (0, 1), (-1, -1), 8.5)
        ]))

        story.append(tbl)

        def canvas_maker(*args, **kwargs):
            c = NumberedCanvas(*args, **kwargs)
            c.watermark_text = watermark
            c.document_title = rep_clean
            c.version_str = "| Elenco Repertorio"
            c.margin_bottom_mm = float(getattr(prof, "margin_bottom_mm", 12.0) or 12.0)
            c.margin_side_mm = max(float(getattr(prof, "margin_left_mm", 10.0) or 10.0), float(getattr(prof, "margin_right_mm", 10.0) or 10.0))
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
                fontName="Courier-Bold",
                fontSize=base_lyrics_size,
                leading=max(base_chords_size, base_lyrics_size) * 1.1,
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
            ),
            "TableCell": ParagraphStyle(
                "TableCell",
                fontName="Helvetica",
                fontSize=8.5,
                leading=11.0,
                textColor=colors.HexColor("#1e293b")
            ),
            "TableCellBold": ParagraphStyle(
                "TableCellBold",
                fontName="Helvetica-Bold",
                fontSize=8.5,
                leading=11.0,
                textColor=colors.HexColor("#0f172a")
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
    def _format_aligned_chord_line(cls, chords_str: str, chord_color_hex: str, chord_size: float, lyric_size: float) -> str:
        """Formats a chord line in Courier-Bold using lyric-sized spaces so every chord aligns with its exact lyric column."""
        if not chords_str:
            return ""
        l_size = lyric_size if lyric_size and lyric_size > 0 else 12.0
        c_size = chord_size if chord_size and chord_size > 0 else l_size
        ratio = c_size / l_size
        parts: List[str] = []
        cursor_cols = 0.0
        for idx, match in enumerate(re.finditer(r"\S+", chords_str)):
            start_col = match.start()
            chord_txt = match.group(0)
            min_gap = 0 if idx == 0 else 1
            spaces_needed = max(min_gap, round(start_col - cursor_cols))
            if spaces_needed > 0:
                if idx == 0 or spaces_needed == 1:
                    parts.append("&nbsp;" * spaces_needed)
                else:
                    parts.append("&nbsp;" * (spaces_needed - 1) + " ")
            parts.append(f"<font color='{chord_color_hex}' size='{c_size}pt'><b>{escape(chord_txt)}</b></font>")
            cursor_cols += spaces_needed + (len(chord_txt) * ratio)
        return "".join(parts)

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
                parts.append(f"<b>({clean_pseudo})</b>")

        meta_info = f"<b>Tonalità:</b> {ita_key}"
        if include_chords and song.capo > 0:
            meta_info += f" | <b>Capo:</b> {song.capo}° tasto"
        parts.append(meta_info)

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
        fragment_flowables: List[Flowable] = []
        current_section_items: List[Flowable] = []
        current_section_is_intro: bool = False
        current_section_has_content: bool = False
        section_text_lines: int = 0
        section_split_index: Optional[int] = None
        last_was_inst_marker = False
        in_tab_block = False
        medley_fragment_count = 0
        in_medley_fragment = False

        def target_list() -> List[Flowable]:
            return fragment_flowables if in_medley_fragment else flowables

        def append_item(it: Flowable):
            target_list().append(it)

        def flush_section(force: bool = False):
            nonlocal current_section_items, current_section_is_intro, current_section_has_content, section_text_lines, section_split_index
            if not current_section_items:
                current_section_is_intro = False
                current_section_has_content = False
                return
            if not current_section_has_content and not force:
                return
            if current_section_is_intro and not force:
                current_section_is_intro = False
                return
            current_section_is_intro = False
            current_section_has_content = False
            dest = target_list()
            # Remove trailing spacers
            while current_section_items and isinstance(current_section_items[-1], Spacer):
                current_section_items.pop()
            if not current_section_items:
                return

            # Se la sezione è molto lunga (> 6 righe di testo), può spezzarsi su più pagine;
            # l'importante è che il blocco di testa (badge di sezione, direttive, griglie armoniche, commenti
            # e le prime 6 righe di testo) rimanga unito e non venga spezzato prematuramente!
            if section_split_index is not None and section_split_index < len(current_section_items):
                head = current_section_items[:section_split_index]
                tail = current_section_items[section_split_index:]
                dest.append(KeepTogether(head))
                dest.extend(tail)
            else:
                dest.append(KeepTogether(list(current_section_items)))
            current_section_items = []
            section_text_lines = 0
            section_split_index = None

        def finalize_medley_fragment():
            nonlocal fragment_flowables, in_medley_fragment
            flush_section(force=True)
            if fragment_flowables:
                while fragment_flowables and isinstance(fragment_flowables[0], Spacer):
                    fragment_flowables.pop(0)
                while fragment_flowables and isinstance(fragment_flowables[-1], Spacer):
                    fragment_flowables.pop()
                flowables.extend(fragment_flowables)
                fragment_flowables = []
            in_medley_fragment = False

        def add_flowable(item: Flowable, spacer_after: Optional[Spacer] = None, is_content: bool = True, is_text_line: bool = False):
            nonlocal current_section_items, current_section_has_content, section_text_lines, section_split_index
            if is_content:
                current_section_has_content = True
            # Estrai flowable e spacer se incapsulati in KeepTogether
            core_flowables: List[Flowable] = []
            extracted_spacer = spacer_after
            if isinstance(item, KeepTogether):
                for sub in item._content:
                    if isinstance(sub, Spacer):
                        if extracted_spacer is None:
                            extracted_spacer = sub
                    else:
                        core_flowables.append(sub)
            else:
                core_flowables.append(item)

            if not core_flowables:
                if extracted_spacer:
                    current_section_items.append(extracted_spacer)
                return

            main_item = core_flowables[0] if len(core_flowables) == 1 else AtomicTable([[f] for f in core_flowables], colWidths=[usable_width])
            if isinstance(main_item, Table):
                main_item.setStyle(TableStyle([('NOSPLIT', (0, 0), (-1, -1))]))

            current_section_items.append(main_item)
            if extracted_spacer:
                current_section_items.append(extracted_spacer)
            if is_text_line:
                section_text_lines += 1
                if section_text_lines == 6:
                    section_split_index = len(current_section_items)

        def create_section_badge_table(sec_name: str, sec_label: Optional[str] = None) -> Flowable:
            label_clean = (sec_label or "").strip()
            s = sec_name.strip().lower()

            # Normalizzazione etichette badge in nomenclatura standard
            if s in ["verse", "sov", "start_of_verse"]:
                italian_name = "STROFA"
            elif s in ["chorus", "soc", "start_of_chorus", "rit"]:
                italian_name = "RITORNELLO"
            elif s in ["bridge", "sob", "start_of_bridge"]:
                italian_name = "BRIDGE"
            elif s in ["ponte", "special", "inciso"]:
                italian_name = "SPECIAL"
            elif s in ["outro", "coda"]:
                italian_name = "OUTRO"
            elif s in ["solo", "assolo"]:
                italian_name = "SOLO"
            elif s in ["intro", "introduzione"]:
                italian_name = "INTRO"
            elif s in ["strumentale", "intermezzo", "interlude"]:
                italian_name = "STRUMENTALE"
            elif s in ["stacco"]:
                italian_name = "STACCO"
            elif s in ["end", "fine"]:
                italian_name = "END"
            else:
                italian_name = sec_name.upper()

            badge_title = f"{italian_name}: {label_clean.upper()}" if label_clean else italian_name
            badge_text = f"[{badge_title}]"
            sb = styles["SectionBadge"]

            # Distinctive background color similar to STACCO:
            if any(k in s for k in ["stacco"]):
                bg_col = colors.HexColor("#DC2626")  # Vibrant Red
            elif any(k in s for k in ["intro"]):
                bg_col = colors.HexColor("#059669")  # Emerald Green
            elif any(k in s for k in ["strofa", "verse", "sov"]):
                bg_col = colors.HexColor("#2563EB")  # Royal Blue
            elif any(k in s for k in ["ritornello", "rit", "chorus", "soc"]):
                bg_col = colors.HexColor("#7C3AED")  # Vibrant Purple
            elif any(k in s for k in ["bridge", "ponte", "special", "inciso", "sob"]):
                bg_col = colors.HexColor("#D97706")  # Amber / Orange
            elif any(k in s for k in ["solo", "assolo", "strumentale", "intermezzo", "interlude"]):
                bg_col = colors.HexColor("#B45309")  # Ochre / Gold
            elif any(k in s for k in ["outro", "finale", "coda", "end", "fine"]):
                bg_col = colors.HexColor("#475569")  # Slate Dark
            else:
                bg_col = colors.HexColor(c_aml_hex) if c_aml_hex else colors.HexColor("#4F46E5")

            p_badge = Paragraph(
                f"<b>{escape(badge_text)}</b>",
                ParagraphStyle(f'Badge_{s}', parent=sb, textColor=colors.HexColor("#FFFFFF"), fontSize=base_lyrics_size * 0.85)
            )
            text_w = pdfmetrics.stringWidth(badge_text, sb.fontName, base_lyrics_size * 0.85)
            badge_w = min(usable_width, text_w + 16.0)
            t = AtomicTable([[p_badge]], colWidths=[badge_w], hAlign="LEFT")
            t.keepWithNext = True
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), bg_col),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('NOSPLIT', (0, 0), (-1, -1)),
            ]))
            return t

        for node in doc.nodes:
            if isinstance(node, (DirectiveNode, MedleySongStartNode, MedleySongEndNode)):
                d_name = node.name.strip().lower()
                d_val = (node.value or "").strip()

                # Spezzone Medley: Inizio brano
                if isinstance(node, MedleySongStartNode) or d_name in ["start_of_song", "sos", "start_of_medley", "start_of_medley_song", "soms"]:
                    if in_medley_fragment:
                        finalize_medley_fragment()

                    flush_section(force=True)

                    medley_fragment_count += 1
                    in_medley_fragment = True

                    # Riga di separazione visibile tra spezzoni di brano differenti (dal 2° brano in poi o dopo contenuti)
                    # Non disegnare la riga se lo spezzone inizia in cima a una nuova pagina (dopo PageBreak)
                    last_flowable = None
                    check_target = fragment_flowables if fragment_flowables else flowables
                    for it in reversed(check_target):
                        if isinstance(it, Spacer):
                            continue
                        last_flowable = it
                        break

                    is_after_page_break = isinstance(last_flowable, PageBreak)

                    if not is_after_page_break and (medley_fragment_count > 1 or flowables or fragment_flowables):
                        divider_table = Table([[""]], colWidths=[usable_width], rowHeights=[1.5 * mm])
                        divider_table.keepWithNext = True
                        divider_table.setStyle(TableStyle([
                            ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor("#475569")),
                            ('TOPPADDING', (0, 0), (-1, -1), 0),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                        ]))
                        curr_target = target_list()
                        if curr_target and not isinstance(curr_target[-1], Spacer):
                            sp_div1 = Spacer(1, 4.0 * mm)
                            sp_div1.keepWithNext = True
                            append_item(sp_div1)
                        current_section_items.append(divider_table)
                        sp_div2 = Spacer(1, 3.0 * mm)
                        sp_div2.keepWithNext = True
                        current_section_items.append(sp_div2)

                    # Estrazione metadati spezzone (Titolo, Artista, Tonalità)
                    if isinstance(node, MedleySongStartNode):
                        frag_title = node.title
                        frag_artist = node.artist
                        frag_key = node.key
                    else:
                        frag_title, frag_artist, frag_key = AMLParser.parse_medley_start_value(d_val)

                    frag_title = frag_title or f"Brano {medley_fragment_count}"
                    color_hex = MEDLEY_COLORS[(medley_fragment_count - 1) % len(MEDLEY_COLORS)]
                    from asma_core.music_engine import MusicEngine
                    ita_key = MusicEngine.convert_notation(frag_key, "ITA") if frag_key else ""

                    meta_parts = []
                    if frag_artist:
                        meta_parts.append(escape(frag_artist))
                    if ita_key:
                        meta_parts.append(f"Ton: {escape(ita_key)}")
                    meta_str = " &bull; ".join(meta_parts)

                    title_str = f"<b>{medley_fragment_count}. {escape(frag_title.upper())}</b>"
                    if meta_str:
                        col2_w = min(usable_width * 0.45, 80 * mm)
                        col1_w = usable_width - col2_w
                        title_p = Paragraph(f"<font color='#FFFFFF' size='{base_lyrics_size * 1.05}'>{title_str}</font>", styles["DocSubtitle"])
                        meta_p = Paragraph(f"<font color='#F1F5F9' size='{base_lyrics_size * 0.88}'><b>{meta_str}</b></font>", ParagraphStyle('RMeta', parent=styles["DocSubtitle"], alignment=2))
                        banner = Table([[title_p, meta_p]], colWidths=[col1_w, col2_w])
                    else:
                        title_p = Paragraph(f"<font color='#FFFFFF' size='{base_lyrics_size * 1.05}'>{title_str}</font>", styles["DocSubtitle"])
                        banner = Table([[title_p]], colWidths=[usable_width])

                    banner.keepWithNext = True
                    banner.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(color_hex)),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ]))
                    current_section_items.append(banner)
                    sp_ban = Spacer(1, 2.5 * mm)
                    sp_ban.keepWithNext = True
                    current_section_items.append(sp_ban)
                    last_was_inst_marker = False
                    continue

                # Spezzone Medley: Fine brano (direttiva invisibile sul PDF)
                if isinstance(node, MedleySongEndNode) or d_name in ["end_of_song", "eos", "end_of_medley", "end_of_medley_song", "eoms"]:
                    flush_section()
                    finalize_medley_fragment()
                    continue

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
                    if in_medley_fragment and d_name in ["key", "tonalita"] and d_val:
                        from asma_core.music_engine import MusicEngine
                        ita_k = MusicEngine.convert_notation(d_val, "ITA")
                        comm_p = Paragraph(f"<font color='{c_chord_hex}'><b>[CAMBIO TONALITÀ: {escape(ita_k)}]</b></font>", styles["DocSubtitle"])
                        add_flowable(KeepTogether([comm_p, Spacer(1, 1.2 * mm)]), is_content=False)
                    continue

                # Band notes and comments: {c: ...} or {comment: ...}
                if d_name in ["c", "comment", "ci", "cb"]:
                    note_text = d_val or "Nota"
                    clean_note = re.sub(r"^[♪\u266a\u266b\u25a0■\*\-\#\s]+", "", note_text).strip()
                    clean_note_no_parens = clean_note.strip("()[]{}").strip().lower()
                    is_note_inst = bool(re.match(r"^(?:strumentale|instrumental|solo|assolo|intermezzo|interlude)(?:\s*[:\-–—]?\s*.*)?$", clean_note_no_parens))
                    if not include_chords and is_note_inst:
                        if last_was_inst_marker:
                            continue
                        last_was_inst_marker = True
                    else:
                        last_was_inst_marker = False
                    comm_p = Paragraph(f"<font color='{c_aml_hex}'><b><i>{escape(note_text)}</i></b></font>", styles["DocSubtitle"])
                    add_flowable(KeepTogether([comm_p, Spacer(1, 1.2 * mm)]), is_content=False)
                    continue

                # Section directives: {soc}, {start_of_chorus}, {sov}, {start_of_verse}, {sob}, {start_of_bridge}
                if d_name in ["soc", "start_of_chorus", "chorus", "ritornello"]:
                    flush_section()
                    curr_target = target_list()
                    if curr_target and not isinstance(curr_target[-1], Spacer):
                        curr_target.append(Spacer(1, 3.5 * mm))
                    badge_table = create_section_badge_table("RITORNELLO", d_val or None)
                    current_section_items.append(badge_table)
                    sp = Spacer(1, 1.8 * mm)
                    sp.keepWithNext = True
                    current_section_items.append(sp)
                    last_was_inst_marker = False
                    continue

                if d_name in ["sov", "start_of_verse", "verse", "strofa"]:
                    flush_section()
                    curr_target = target_list()
                    if curr_target and not isinstance(curr_target[-1], Spacer):
                        curr_target.append(Spacer(1, 3.5 * mm))
                    badge_table = create_section_badge_table("STROFA", d_val or None)
                    current_section_items.append(badge_table)
                    sp = Spacer(1, 1.8 * mm)
                    sp.keepWithNext = True
                    current_section_items.append(sp)
                    last_was_inst_marker = False
                    continue

                if d_name in ["sob", "start_of_bridge", "bridge", "speciale"]:
                    flush_section()
                    curr_target = target_list()
                    if curr_target and not isinstance(curr_target[-1], Spacer):
                        curr_target.append(Spacer(1, 3.5 * mm))
                    badge_table = create_section_badge_table("BRIDGE", d_val or None)
                    current_section_items.append(badge_table)
                    sp = Spacer(1, 1.8 * mm)
                    sp.keepWithNext = True
                    current_section_items.append(sp)
                    last_was_inst_marker = False
                    continue

                if d_name in ["eoc", "end_of_chorus", "eov", "end_of_verse", "eob", "end_of_bridge"]:
                    flush_section(force=True)
                    curr_target = target_list()
                    if curr_target and not isinstance(curr_target[-1], Spacer):
                        append_item(Spacer(1, 2.0 * mm))
                    continue

                # Column break: {colb} or {column_break}
                if d_name in ["colb", "column_break", "col_break"]:
                    flush_section(force=True)
                    if cols == 2:
                        append_item(FrameBreak())
                    else:
                        append_item(Spacer(1, 4.0 * mm))
                    continue

                # Page break: {np}, {new_page}, {page_break}, {salto_pagina}
                if d_name in ["np", "new_page", "page_break", "salto_pagina", "salto_di_pagina"]:
                    flush_section(force=True)
                    if in_medley_fragment:
                        finalize_medley_fragment()
                    curr_t = target_list()
                    while curr_t and isinstance(curr_t[-1], Spacer):
                        curr_t.pop()
                    if curr_t and not isinstance(curr_t[-1], PageBreak):
                        append_item(PageBreak())
                    continue

                # Riga bianca / Spazio verticale personalizzato: {riga_bianca}, {blank_line}, {spazio}, ecc.
                if d_name in [
                    "riga_bianca", "rigabianca", "riga-bianca",
                    "riga_vuota", "rigavuota", "riga-vuota",
                    "blank_line", "blankline", "blank-line",
                    "empty_line", "emptyline", "empty-line",
                    "spazio", "space"
                ]:
                    line_count = 1
                    custom_height_pt = None
                    if d_val:
                        val_str = d_val.strip().lower()
                        if val_str.endswith("mm"):
                            try:
                                custom_height_pt = float(val_str[:-2].strip()) * mm
                            except ValueError:
                                pass
                        elif val_str.endswith("pt"):
                            try:
                                custom_height_pt = float(val_str[:-2].strip())
                            except ValueError:
                                pass
                        else:
                            try:
                                line_count = max(1, int(val_str))
                            except ValueError:
                                line_count = 1

                    if custom_height_pt is not None:
                        blank_h = max(1.0, custom_height_pt)
                    else:
                        blank_h = base_lyrics_size * 1.3 * line_count

                    add_flowable(Spacer(1, blank_h), is_content=False, is_text_line=False)
                    if include_chords:
                        last_was_inst_marker = False
                    continue

                # Direttiva Scena Live Tastiere: {scena: ...}
                if d_name in ["scena", "scene"]:
                    scena_val = (d_val or "").strip()
                    badge_title = scena_val.upper() if scena_val else ""
                    sb = styles["SectionBadge"]
                    icon_path = os.path.join(os.path.dirname(__file__), "assets", "keyboard_icon.png")
                    img_w, img_h = 13.0, 12.0
                    if os.path.exists(icon_path):
                        clean_icon_path = icon_path.replace("\\", "/")
                        img_markup = f'<img src="{clean_icon_path}" width="{img_w}" height="{img_h}" valign="middle"/>'
                    else:
                        img_markup = "&#9836;"

                    content_markup = f"{img_markup} &nbsp;<b>{escape(badge_title)}</b>" if badge_title else img_markup
                    p_scena = Paragraph(content_markup, ParagraphStyle('ScenaBadgeDir', parent=sb, textColor=colors.HexColor("#FFFFFF"), fontSize=base_lyrics_size * 0.85))
                    text_w = pdfmetrics.stringWidth(badge_title, sb.fontName, base_lyrics_size * 0.85) if badge_title else 0
                    badge_w = min(usable_width, text_w + img_w + 24.0)
                    badge_table = AtomicTable([[p_scena]], colWidths=[badge_w], hAlign="LEFT")
                    badge_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0891B2")),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('NOSPLIT', (0, 0), (-1, -1)),
                    ]))
                    add_flowable(KeepTogether([badge_table, Spacer(1, 1.8 * mm)]), is_content=False)
                    last_was_inst_marker = False
                    continue

                # Direttiva Stacco Strumentale / d'insieme: {stacco: ...}
                if d_name in ["stacco"]:
                    if not include_chords and last_was_inst_marker:
                        continue
                    stacco_val = (d_val or "").strip()
                    badge_title = f"[STACCO: {stacco_val.upper()}]" if stacco_val else "[STACCO]"
                    sb = styles["SectionBadge"]
                    p_stacco = Paragraph(f"<b>{escape(badge_title)}</b>", ParagraphStyle('StaccoBadgeDir', parent=sb, textColor=colors.HexColor("#FFFFFF"), fontSize=base_lyrics_size * 0.85))
                    text_w = pdfmetrics.stringWidth(badge_title, sb.fontName, base_lyrics_size * 0.85)
                    badge_w = min(usable_width, text_w + 16.0)
                    badge_table = AtomicTable([[p_stacco]], colWidths=[badge_w], hAlign="LEFT")
                    badge_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#DC2626")),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('NOSPLIT', (0, 0), (-1, -1)),
                    ]))
                    add_flowable(KeepTogether([badge_table, Spacer(1, 1.8 * mm)]), is_content=False)
                    last_was_inst_marker = True
                    continue

                # Any other directive with value (e.g. custom tag)
                if d_val:
                    comm_p = Paragraph(f"<font color='{c_aml_hex}'><b>[{d_name.upper()}]:</b> {escape(d_val)}</font>", styles["DocSubtitle"])
                    add_flowable(KeepTogether([comm_p, Spacer(1, 1.0 * mm)]), is_content=False)
                    last_was_inst_marker = False
                continue

            elif isinstance(node, SectionNode):
                sec_name = node.section_name.strip().lower()
                sec_label = (node.label or "").strip().lower()
                sec_full = f"{sec_name} {sec_label}".strip()
                is_inst_section = any(k in sec_full for k in ["solo", "assolo", "strumentale", "intermezzo", "interlude"])

                # Elimina sempre le sezioni e i badge dedicati a tablature
                if any(k in sec_name for k in ["tab", "tablatura", "tabs", "riff_tab", "guitar_tab"]) or "tab" in sec_label:
                    in_tab_block = True
                    continue
                else:
                    in_tab_block = False

                if not include_chords and is_inst_section:
                    if last_was_inst_marker:
                        # Marcatore/badge strumentale già emesso in sequenza immediata: scrivi una sola volta
                        continue
                    flush_section(force=True)
                    curr_target = target_list()
                    if curr_target and not isinstance(curr_target[-1], Spacer):
                        curr_target.append(Spacer(1, 3.5 * mm))
                    badge_table = create_section_badge_table(node.section_name, node.label)
                    current_section_items.append(badge_table)
                    sp = Spacer(1, 1.8 * mm)
                    sp.keepWithNext = True
                    current_section_items.append(sp)
                    current_section_has_content = True
                    last_was_inst_marker = True
                    continue

                flush_section()

                if sec_name in ["end", "fine"]:
                    flush_section(force=True)
                    curr_target = target_list()
                    while curr_target and isinstance(curr_target[-1], Spacer):
                        curr_target.pop()
                    curr_target.append(Spacer(1, 1.0 * mm))
                    sb = styles["SectionBadge"]
                    end_text = "[END]"
                    end_font_size = min(10.5, sb.fontSize)
                    p_end = Paragraph(f"<b>{escape(end_text)}</b>", ParagraphStyle('EndBadgeP', parent=sb, fontSize=end_font_size, leading=end_font_size * 1.1))
                    text_w = pdfmetrics.stringWidth(end_text, sb.fontName, end_font_size)
                    badge_w = min(usable_width, text_w + 12.0)
                    end_table = AtomicTable([[p_end]], colWidths=[badge_w], hAlign="LEFT")
                    end_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(c_aml_hex)),
                        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
                        ('LEFTPADDING', (0, 0), (-1, -1), 5),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                        ('NOSPLIT', (0, 0), (-1, -1)),
                    ]))
                    curr_target.append(end_table)
                    last_was_inst_marker = False
                    continue

                # Separazione spaziale elegante e proporzionata prima di ogni nuova sezione
                curr_target = target_list()
                if curr_target and not isinstance(curr_target[-1], Spacer):
                    curr_target.append(Spacer(1, 3.5 * mm))

                if any(k in sec_name for k in ["intro", "introduzione"]):
                    current_section_is_intro = True
                badge_table = create_section_badge_table(node.section_name, node.label)
                current_section_items.append(badge_table)
                sp = Spacer(1, 1.8 * mm)
                sp.keepWithNext = True
                current_section_items.append(sp)
                last_was_inst_marker = False
                continue

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
                    inline_comm = getattr(node, "inline_comment", None)
                    inline_comm_html = f" <font color='{c_aml_hex}'><b><i>({escape(inline_comm)})</i></b></font>" if inline_comm else ""
                    if grid_line_text:
                        p_grid = Paragraph(f"<font color='{c_chord_hex}' size='{base_chords_size}pt'><b>{grid_line_text}</b></font>{inline_comm_html}", styles["ChordText"])
                        add_flowable(KeepTogether([Spacer(1, 1.0 * mm), p_grid, Spacer(1, 1.2 * mm)]), is_text_line=True)
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
                    inline_comm = getattr(node, "inline_comment", None)
                    inline_comm_html = f" <font color='{c_aml_hex}'><b><i>({escape(inline_comm)})</i></b></font>" if inline_comm else ""
                    on_chords = getattr(node, "comment_on_chords", False)
                    if lyrics_str.strip():
                        # Atomic 2-row table for chord line over lyric line: mai separati tra pagine
                        chords_html = cls._format_aligned_chord_line(chords_str, c_chord_hex, base_chords_size, base_lyrics_size)
                        p_chords = Paragraph(f"{chords_html}{inline_comm_html if on_chords else ''}", styles["ChordText"])
                        p_lyrics = Paragraph(f"{cls._format_lyric_spaces(lyrics_str)}{'' if on_chords else inline_comm_html}", styles["LyricText"])
                        pair_table = AtomicTable([[p_chords], [p_lyrics]], colWidths=[usable_width])
                        pair_table.setStyle(TableStyle([
                            ('TOPPADDING', (0, 0), (-1, -1), 0),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                            ('LEFTPADDING', (0, 0), (-1, -1), 0),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                            ('NOSPLIT', (0, 0), (-1, -1)),
                        ]))
                        add_flowable(pair_table, spacer_after=Spacer(1, 0.6 * mm), is_text_line=True)
                    else:
                        # Pure chord line (e.g. SOL SOL# LA {c: brass} -> SOL SOL# LA (brass))
                        chords_html = cls._format_aligned_chord_line(chords_str, c_chord_hex, base_chords_size, base_lyrics_size)
                        p_chords = Paragraph(f"{chords_html}{inline_comm_html}", styles["ChordText"])
                        add_flowable(KeepTogether([Spacer(1, 1.0 * mm), p_chords, Spacer(1, 1.2 * mm)]), is_text_line=True)
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
                            add_flowable(KeepTogether([Spacer(1, 1.2 * mm), p_chords, Spacer(1, 1.5 * mm)]), is_text_line=True)
                            last_was_inst_marker = False
                    elif lyrics_str.strip():
                        clean_lyr = re.sub(r"^[♪\u266a\u266b\u25a0■\*\-\#\s]+", "", lyrics_str).strip()
                        clean_lyr_no_parens = clean_lyr.strip("()[]{}").strip().lower()
                        is_lyric_inst = bool(re.match(r"^(?:strumentale|instrumental|solo|assolo|intermezzo|interlude)(?:\s*[:\-–—]?\s*.*)?$", clean_lyr_no_parens))
                        if is_lyric_inst:
                            if not include_chords:
                                if last_was_inst_marker:
                                    continue
                                p_inst = Paragraph(f"<font color='{c_aml_hex}'><b><i>&#9835; (Strumentale)</i></b></font>", styles["DocSubtitle"])
                                add_flowable(KeepTogether([p_inst, Spacer(1, 1.2 * mm)]))
                                last_was_inst_marker = True
                            else:
                                disp_title = clean_lyr_no_parens.capitalize() if clean_lyr_no_parens else "Strumentale"
                                p_inst = Paragraph(f"<font color='{c_aml_hex}'><b><i>&#9835; ({disp_title})</i></b></font>", styles["DocSubtitle"])
                                add_flowable(KeepTogether([p_inst, Spacer(1, 1.2 * mm)]))
                                last_was_inst_marker = True
                        else:
                            # Singer lyrics-only (or line with only lyrics)
                            inline_comm = getattr(node, "inline_comment", None)
                            inline_comm_html = f" <font color='{c_aml_hex}'><b><i>({escape(inline_comm)})</i></b></font>" if inline_comm else ""
                            p_lyrics = Paragraph(f"{cls._format_lyric_spaces(lyrics_str)}{inline_comm_html}", styles["LyricText"])
                            add_flowable(KeepTogether([p_lyrics, Spacer(1, 0.6 * mm)]), is_text_line=True)
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

                # Direttiva Scena Live Tastiere in CustomTag
                if tag_label in ["scena", "scene"]:
                    scena_val = (node.content or "").strip()
                    badge_title = scena_val.upper() if scena_val else ""
                    sb = styles["SectionBadge"]
                    icon_path = os.path.join(os.path.dirname(__file__), "assets", "keyboard_icon.png")
                    img_w, img_h = 13.0, 12.0
                    if os.path.exists(icon_path):
                        clean_icon_path = icon_path.replace("\\", "/")
                        img_markup = f'<img src="{clean_icon_path}" width="{img_w}" height="{img_h}" valign="middle"/>'
                    else:
                        img_markup = "&#9836;"

                    content_markup = f"{img_markup} &nbsp;<b>{escape(badge_title)}</b>" if badge_title else img_markup
                    p_scena = Paragraph(content_markup, ParagraphStyle('ScenaBadgeCust', parent=sb, textColor=colors.HexColor("#FFFFFF"), fontSize=base_lyrics_size * 0.85))
                    text_w = pdfmetrics.stringWidth(badge_title, sb.fontName, base_lyrics_size * 0.85) if badge_title else 0
                    badge_w = min(usable_width, text_w + img_w + 24.0)
                    badge_table = AtomicTable([[p_scena]], colWidths=[badge_w], hAlign="LEFT")
                    badge_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#0891B2")),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('NOSPLIT', (0, 0), (-1, -1)),
                    ]))
                    add_flowable(KeepTogether([badge_table, Spacer(1, 1.8 * mm)]), is_content=False)
                    last_was_inst_marker = False
                    continue

                # Direttiva Stacco in CustomTag
                if tag_label in ["stacco"]:
                    stacco_val = (node.content or "").strip()
                    badge_title = f"[STACCO: {stacco_val.upper()}]" if stacco_val else "[STACCO]"
                    sb = styles["SectionBadge"]
                    p_stacco = Paragraph(f"<b>{escape(badge_title)}</b>", ParagraphStyle('StaccoBadgeCust', parent=sb, textColor=colors.HexColor("#FFFFFF"), fontSize=base_lyrics_size * 0.85))
                    text_w = pdfmetrics.stringWidth(badge_title, sb.fontName, base_lyrics_size * 0.85)
                    badge_w = min(usable_width, text_w + 16.0)
                    badge_table = AtomicTable([[p_stacco]], colWidths=[badge_w], hAlign="LEFT")
                    badge_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#DC2626")),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('NOSPLIT', (0, 0), (-1, -1)),
                    ]))
                    add_flowable(KeepTogether([badge_table, Spacer(1, 1.8 * mm)]), is_content=False)
                    last_was_inst_marker = True
                    continue

                # Riga bianca / Spazio verticale in CustomTag
                if tag_label in [
                    "riga_bianca", "rigabianca", "riga-bianca",
                    "riga_vuota", "rigavuota", "riga-vuota",
                    "blank_line", "blankline", "blank-line",
                    "empty_line", "emptyline", "empty-line",
                    "spazio", "space"
                ]:
                    line_count = 1
                    custom_height_pt = None
                    raw_val = (node.content or "").strip().lower()
                    if raw_val:
                        if raw_val.endswith("mm"):
                            try:
                                custom_height_pt = float(raw_val[:-2].strip()) * mm
                            except ValueError:
                                pass
                        elif raw_val.endswith("pt"):
                            try:
                                custom_height_pt = float(raw_val[:-2].strip())
                            except ValueError:
                                pass
                        else:
                            try:
                                line_count = max(1, int(raw_val))
                            except ValueError:
                                line_count = 1

                    if custom_height_pt is not None:
                        blank_h = max(1.0, custom_height_pt)
                    else:
                        blank_h = base_lyrics_size * 1.3 * line_count

                    add_flowable(Spacer(1, blank_h), is_content=False, is_text_line=False)
                    if include_chords:
                        last_was_inst_marker = False
                    continue

                # Tag strumentale o assolo (es. {guitar: solo}, {assolo}, ecc.)
                tag_label = node.tag_type.strip().lower()
                is_solo = any(k in tag_label for k in ["solo", "assolo", "instrumental", "guitar", "chitarra", "piano", "sax", "stacco"])
                if not include_chords and is_solo:
                    if last_was_inst_marker:
                        # Non duplicare marcatori strumentali consecutivi
                        continue
                    content_str = f" — {node.content}" if node.content and node.content.strip() else ""
                    tag_p = Paragraph(f"<font color='{c_aml_hex}'><b><i>&#9835; (Strumentale{content_str})</i></b></font>", styles["CustomTagText"])
                    tag_t = Table([[tag_p]], colWidths=[usable_width])
                    tag_t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDE7F6")),
                        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(c_aml_hex)),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ]))
                    add_flowable(KeepTogether([tag_t, Spacer(1, 0.8 * mm)]))
                    last_was_inst_marker = True
                    continue
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
                comm_text = (node.text or "").strip().lower()
                if not include_chords and any(w in comm_text for w in ["strumentale", "solo", "assolo"]):
                    if last_was_inst_marker:
                        continue
                    last_was_inst_marker = True
                comm_p = Paragraph(f"<i># {node.text}</i>", styles["DocSubtitle"])
                add_flowable(KeepTogether([comm_p, Spacer(1, 0.8 * mm)]), is_content=False)

            elif isinstance(node, EmptyLineNode):
                if in_tab_block:
                    continue
                flush_section()
                # Spaziatura contenuta tra strofe/paragrafi (senza creare vuoti enormi)
                curr_target = target_list()
                if curr_target and not isinstance(curr_target[-1], (Spacer, PageBreak)):
                    append_item(Spacer(1, 2.0 * mm))
                # Preserva last_was_inst_marker: le righe vuote non devono azzerare la protezione anti-duplicati strumentali

        flush_section(force=True)
        if in_medley_fragment:
            finalize_medley_fragment()
        flush_section(force=True)

        # Inserisci un badge [END] di default alla fine del brano se non gia' presente
        has_end_badge = False
        for node in reversed(doc.nodes):
            if isinstance(node, EmptyLineNode):
                continue
            if isinstance(node, SectionNode) and node.section_name in ["end", "fine"]:
                has_end_badge = True
                break
            if isinstance(node, DirectiveNode) and node.name in ["end", "fine"]:
                has_end_badge = True
                break
            break

        if not has_end_badge and flowables:
            # Rimuovi eventuali spaziatori vuoti multipli prima di [END] per compattare
            while len(flowables) > 1 and isinstance(flowables[-1], Spacer):
                flowables.pop()
            flowables.append(Spacer(1, 1.0 * mm))
            sb = styles["SectionBadge"]
            end_text = "[END]"
            end_font_size = min(10.5, sb.fontSize)
            p_end = Paragraph(f"<b>{escape(end_text)}</b>", ParagraphStyle('EndBadgeP', parent=sb, fontSize=end_font_size, leading=end_font_size * 1.1))
            text_w = pdfmetrics.stringWidth(end_text, sb.fontName, end_font_size)
            badge_w = min(usable_width, text_w + 12.0)
            end_table = AtomicTable([[p_end]], colWidths=[badge_w], hAlign="LEFT")
            end_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(c_aml_hex)),
                ('TOPPADDING', (0, 0), (-1, -1), 1.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('NOSPLIT', (0, 0), (-1, -1)),
            ]))
            flowables.append(end_table)

        # Post-process: sanitize flowables list to guarantee no redundant or orphan page breaks
        cleaned_flowables: List[Flowable] = []
        for it in flowables:
            if isinstance(it, PageBreak):
                while cleaned_flowables and isinstance(cleaned_flowables[-1], Spacer):
                    cleaned_flowables.pop()
                if cleaned_flowables and not isinstance(cleaned_flowables[-1], PageBreak):
                    cleaned_flowables.append(it)
            elif isinstance(it, Spacer):
                if cleaned_flowables and not isinstance(cleaned_flowables[-1], (Spacer, PageBreak)):
                    cleaned_flowables.append(it)
            else:
                cleaned_flowables.append(it)

        while cleaned_flowables and isinstance(cleaned_flowables[-1], (Spacer, PageBreak)):
            cleaned_flowables.pop()

        return cleaned_flowables

    @classmethod
    def clear_cache(cls) -> None:
        """Empties the in-memory PDF buffer cache."""
        cls._cache.clear()
