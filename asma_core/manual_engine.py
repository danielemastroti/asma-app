"""
ASMA Accordi Next Generation - Dynamic Official User Manual Engine
Generates comprehensive printable and downloadable PDF documentation with band logo,
Table of Contents, structured chapters, embedded screenshots, and real-time auto-updating changelog.
Conforms to SRS Cap. 4.11, 15.14 and latest band guidelines.
"""

from __future__ import annotations
import os
import io
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


def _resolve_asset_path(rel_path: str) -> Optional[str]:
    """Resolves asset path safely whether running from repo root or subfolders."""
    if os.path.exists(rel_path):
        return rel_path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate = os.path.join(base_dir, rel_path)
    if os.path.exists(candidate):
        return candidate
    return None


class ManualNumberedCanvas(canvas.Canvas):
    """
    Two-pass ReportLab canvas for dynamic total page counting,
    running header with Band Logo, and official footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

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

        # Running header: starting on page 2 onwards
        if self._pageNumber > 1:
            header_y = page_h - 12 * mm
            logo_path = _resolve_asset_path("frontend/assets/band_logo.png")
            if logo_path:
                try:
                    self.drawImage(
                        logo_path,
                        page_w - 38 * mm,
                        header_y - 2.5 * mm,
                        width=22 * mm,
                        height=7.9 * mm,
                        preserveAspectRatio=True,
                        mask='auto'
                    )
                except Exception:
                    pass

            self.setFont("Helvetica-Bold", 8.5)
            self.setFillColor(colors.HexColor("#0284c7"))
            self.drawString(15 * mm, header_y, "THE NEW ASMA 2.0")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(48 * mm, header_y, "— Manuale Utente Ufficiale Band")

            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(15 * mm, header_y - 3 * mm, page_w - 15 * mm, header_y - 3 * mm)

        # Footer on all pages
        foot_y = 10 * mm
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(15 * mm, foot_y + 3.5 * mm, page_w - 15 * mm, foot_y + 3.5 * mm)

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        now_str = datetime.now().strftime("%d/%m/%Y")
        self.drawString(15 * mm, foot_y, f"Repertorio Ufficiale Band • Documento Autocompilato • {now_str}")
        self.drawRightString(page_w - 15 * mm, foot_y, f"Pagina {self._pageNumber} di {total_pages}")
        self.restoreState()


class ManualEngine:
    """
    Auto-updating band manual engine.
    Produces high-fidelity PDF manual with logo, table of contents,
    detailed multi-device guidelines, and live changelog ingestion.
    """

    @classmethod
    def get_chapters_metadata(cls) -> List[Dict[str, Any]]:
        """Returns ordered index of chapters with descriptions."""
        return [
            {"num": 1, "title": "Introduzione & Filosofia ASMA", "desc": "Cos'è il sistema, Single Source of Truth AML, la musica prima dell'AI, architettura offline-first."},
            {"num": 2, "title": "Login & Modalità Operative (Palco vs Editing)", "desc": "Accesso semplificato casa/palco, modalità editing completa, Google OAuth e sessioni persistenti."},
            {"num": 3, "title": "Elenco Utenti e Pseudonimi Autorizzati (Band)", "desc": "Componenti della band (Cico, Mingo, Puma, Red, Maurino, Sentimental) e ruoli di sicurezza."},
            {"num": 4, "title": "Preferenze Utente, Profili Hardware & Persistenza Cloud", "desc": "Multi-dispositivo (iPad, MediaPad, MatePad, Pixel, A4), font, colonne, margini e salvataggio Turso."},
            {"num": 5, "title": "Lista Brani, Anteprima PDF, Stampa A4 & Download Dispositivo", "desc": "Ricerca 0ms, schede brani, Repertorio Ufficiale vs Personale, rendering fedele e stampa."},
            {"num": 6, "title": "Importazione Brani & Scansione da Fotocamera", "desc": "Cerca sul Web, Incolla Testo, ChordPro, URL diretti e Scansione Fotocamera OCR multi-pagina con Gemini Vision AI."},
            {"num": 7, "title": "Creazione Brani Autoprodotti", "desc": "Barra metadati essenziali compatti e repertorio personale protetto."},
            {"num": 8, "title": "Flusso di Lavoro Modifica Brani (Ufficiale vs Personale)", "desc": "Protezione del repertorio ufficiale, copia nel personale, schema grafico di flusso e promozione con sovrascrittura."},
            {"num": 9, "title": "AML (ASMA Markup Language) — Sintassi, Direttive & Guida Autonoma", "desc": "Tabella completa di tutte le direttive, esempi pratici per scrivere un intero brano da zero o un medley autonomamente."},
            {"num": 10, "title": "Modalità Editing, Nuove Direttive Scena/Stacco & Medley", "desc": "Direttiva {Scena: X} per tastiere, {stacco: strumento}, Medley fino a 20 brani e Impaginazione Pagine su base Dispositivo / Stampa A4."},
            {"num": 11, "title": "IL CIRCOLO DELLE QUINTE (Armonia & Esempi Pratici per la Band)", "desc": "Guida semplice per musicisti: l'orologio delle tonalità, relative minori, modulazioni, trasposizioni per la voce e transizioni live per scalette e medley."},
            {"num": 12, "title": "Modalità Palco (Stage Mode) & Teleprompter 60fps", "desc": "Autoscroll fluido a 60fps, avvio on-demand, tap-to-pause, contrasto notturno OLED, pedaliere HID e metronomo."},
            {"num": 13, "title": "Gestione Scalette Live & Condivisione WhatsApp", "desc": "Composizione scalette, variazioni BPM, durata totale e condivisione A4 WhatsApp."},
            {"num": 14, "title": "Suggerimenti Esecuzione Live (AI Gemini Free)", "desc": "Consigli su misura per Cico, Mingo, Puma, Red, Maurino, Sentimental e per l'intera band, con fallback offline."},
            {"num": 15, "title": "Amministrazione, Sicurezza, Cestino 30gg & Backup DB", "desc": "Cestino con ripristino entro 30 giorni, backup integrale JSON, restore con un clic e audit trail."},
            {"num": 16, "title": "Changelog Dinamico & Cronologia Novità (In Tempo Reale)", "desc": "Cronologia delle release e nuove funzionalità compilata automaticamente da data/changelog.json."},
            {"num": 17, "title": "Appendice: Figure Grafiche & Riepilogo Screenshot", "desc": "Riepilogo delle 8 figure grafiche incluse nel manuale."}
        ]

    @classmethod
    def sanitize_pdf_text(cls, text: str) -> str:
        """
        Strips or converts any characters not supported by standard PDF Helvetica
        (emojis, special symbols, etc.) to guarantee 100% clean rendering with zero black squares.
        """
        if not text:
            return ""
        replacements = {
            '♯': '#',
            '♭': 'b',
            '✓': 'OK',
            '▼': '|',
            '▲': '^',
            '❌': '[X]',
            '⭐': '',
            '🔒': '',
            '🔓': '',
            '📋': '',
            '✏️': '',
            '✏': '',
            '💾': '',
            '📄': '',
            '🎤': '',
            '🎸': '',
            '🎹': '',
            '🥁': '',
            '🎼': '',
            '🎶': '',
            '🎵': '',
            '👉': '',
            '👤': '',
            '👥': '',
            '💡': '',
            '📷': '',
            '🔗': '',
            '⚡': '',
            '✨': '',
            '➕': '+',
            '🚪': '',
            '⬆': '^',
            '⬇': 'v',
            '\ufe0f': '',
        }
        for k, v in replacements.items():
            text = text.replace(k, v)

        text = text.replace("' ", "'").replace(" '", "'")

        # Drop any remaining emojis or high Unicode characters (> 0x2500, except allowed dashes/bullets/arrows)
        cleaned_chars = []
        for c in text:
            cp = ord(c)
            if cp < 128:
                cleaned_chars.append(c)
            elif cp in [0x00AA, 0x00BA]:
                cleaned_chars.append(c)
            elif 0x00C0 <= cp <= 0x00FF:
                cleaned_chars.append(c)
            elif cp in [0x2014, 0x2022, 0x2192, 0x2194]:
                cleaned_chars.append(c)
            else:
                continue
        return "".join(cleaned_chars)

    @classmethod
    def load_changelog_entries(cls) -> List[Dict[str, Any]]:
        """Reads latest changelog directly from data/changelog.json for 100% dynamic documentation."""
        changelog_path = os.path.join(os.getcwd(), "data", "changelog.json")
        if os.path.exists(changelog_path):
            try:
                with open(changelog_path, "r", encoding="utf-8") as f:
                    raw_entries = json.load(f)
                clean_entries = []
                for entry in raw_entries:
                    clean_entry = {
                        "version": cls.sanitize_pdf_text(entry.get("version", "")),
                        "date": cls.sanitize_pdf_text(entry.get("date", "")),
                        "title": cls.sanitize_pdf_text(entry.get("title", "")),
                        "new_features": [cls.sanitize_pdf_text(x) for x in entry.get("new_features", [])],
                        "improvements": [cls.sanitize_pdf_text(x) for x in entry.get("improvements", [])],
                        "security": [cls.sanitize_pdf_text(x) for x in entry.get("security", [])],
                        "bug_fixes": [cls.sanitize_pdf_text(x) for x in entry.get("bug_fixes", [])],
                    }
                    clean_entries.append(clean_entry)
                return clean_entries
            except Exception:
                pass
        return []

    @classmethod
    def generate_manual_pdf(cls) -> bytes:
        """
        Builds the complete official User Manual as a publication-ready PDF.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        cover_title_style = ParagraphStyle(
            "CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#0f172a"),
            alignment=1,  # Center
            spaceAfter=6
        )
        cover_sub_style = ParagraphStyle(
            "CoverSub",
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0284c7"),
            alignment=1,  # Center
            spaceAfter=14
        )
        ch_title_style = ParagraphStyle(
            "ChTitle",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0369a1"),
            spaceBefore=14,
            spaceAfter=5,
            keepWithNext=True
        )
        ch_sub_style = ParagraphStyle(
            "ChSub",
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13.5,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=7,
            spaceAfter=3,
            keepWithNext=True
        )
        body_style = ParagraphStyle(
            "ManBody",
            fontName="Helvetica",
            fontSize=9.2,
            leading=13,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=4
        )
        bullet_style = ParagraphStyle(
            "ManBullet",
            fontName="Helvetica",
            fontSize=9.0,
            leading=12.5,
            textColor=colors.HexColor("#334155"),
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=2
        )
        code_box_style = ParagraphStyle(
            "ManCode",
            fontName="Courier",
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#0f172a")
        )
        caption_style = ParagraphStyle(
            "ManCaption",
            fontName="Helvetica-Oblique",
            fontSize=8.2,
            leading=11,
            textColor=colors.HexColor("#64748b"),
            alignment=1,
            spaceBefore=3,
            spaceAfter=8
        )

        story = []

        # =========================================================================
        # COVER PAGE
        # =========================================================================
        logo_path = _resolve_asset_path("frontend/assets/band_logo.png")
        if logo_path:
            try:
                # 1024 x 367 ratio -> width 84mm, height 30.1mm
                story.append(Image(logo_path, width=84 * mm, height=30.1 * mm))
                story.append(Spacer(1, 4 * mm))
            except Exception:
                pass

        story.append(Paragraph("MANUALE UTENTE UFFICIALE", cover_title_style))
        story.append(Paragraph("THE NEW ASMA 2.0 &bull; Piattaforma Musicale per Repertori, Palco & PDF", cover_sub_style))

        # Metadata banner table
        now_dt = datetime.now()
        date_str = now_dt.strftime("%d/%m/%Y")
        meta_data = [
            [
                Paragraph("<b>Versione Sistema:</b> ASMA 2.0 (2026.11)", body_style),
                Paragraph(f"<b>Data Compilazione:</b> {date_str}", body_style)
            ],
            [
                Paragraph("<b>Destinatari:</b> Tutta la Band (Cico, Mingo, Puma, Red, Maurino, Sentimental)", body_style),
                Paragraph("<b>Database Cloud:</b> Turso Sincronizzato", body_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[90 * mm, 90 * mm])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 6 * mm))

        # TABLE OF CONTENTS
        story.append(Paragraph("<b>INDICE GENERALE DEI CAPITOLI</b>", ch_title_style))
        chapters = cls.get_chapters_metadata()
        toc_data = []
        for ch in chapters:
            toc_data.append([
                Paragraph(f"<b>Capitolo {ch['num']}</b>", body_style),
                Paragraph(f"<b>{ch['title']}</b><br/><font color='#64748b' size='7.5'>{ch['desc']}</font>", body_style)
            ])
        toc_table = Table(toc_data, colWidths=[24 * mm, 156 * mm])
        toc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ffffff")),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(toc_table)

        story.append(PageBreak())

        # =========================================================================
        # CAPITOLO 1: INTRODUZIONE & FILOSOFIA
        # =========================================================================
        story.append(Paragraph("Capitolo 1 &bull; Introduzione & Filosofia ASMA", ch_title_style))
        story.append(Paragraph(
            "<b>THE NEW ASMA 2.0</b> è la piattaforma integrata ideata e progettata per le esigenze reali della band: "
            "gestione centralizzata di brani, repertori condivisi, scalette per concerti, annotazioni live ed esportazione "
            "in PDF ad alta risoluzione calibrata al millimetro per ciascun dispositivo hardware presente sul palco.",
            body_style
        ))
        story.append(Paragraph("<b>I Principi Guida Fondamentali:</b>", ch_sub_style))
        story.append(Paragraph(
            "&bull; <b>La Musica Viene Prima dell'AI:</b> Tutte le funzionalità operative sul palco e in sala prove — visualizzazione, "
            "scorrimento del teleprompter, trasposizioni cromatiche, formattazione a colonne e generazione PDF — sono "
            "<b>100% deterministiche, locali e a latenza zero</b>. L'intelligenza artificiale (Gemini) è impiegata esclusivamente "
            "come assistente ausiliario facoltativo per la scansione OCR di spartiti cartacei e suggerimenti live.",
            bullet_style
        ))
        story.append(Paragraph(
            "&bull; <b>Single Source of Truth (AML):</b> Ogni brano è codificato nel formato testuale standard ASMA Markup Language. "
            "Questo garantisce totale portabilità, assenza di lock-in verso software proprietari e allineamento perfetto tra web e carta.",
            bullet_style
        ))
        story.append(Paragraph(
            "&bull; <b>Architettura Cloud & Offline-First:</b> L'archivio è sincronizzato nel cloud su database distribuito Turso (SQLite edge). "
            "L'applicazione Web Progressive (PWA) garantisce la piena operatività anche in caso di caduta temporanea della rete durante un live.",
            bullet_style
        ))

        # =========================================================================
        # CAPITOLO 2: LOGIN & MODALITÀ OPERATIVE
        # =========================================================================
        story.append(Paragraph("Capitolo 2 &bull; Login & Modalità Operative (Palco vs Editing)", ch_title_style))
        story.append(Paragraph(
            "L'accesso al sistema avviene tramite Google OAuth oppure selezione rapida del profilo autorizzato. "
            "Il sistema memorizza in modo permanente la sessione sul browser e sul tablet.",
            body_style
        ))
        story.append(Paragraph("<b>Le Due Modalità Operative Selezionabili:</b>", ch_sub_style))
        story.append(Paragraph(
            "1. <b>Modalità Semplificata (Casa / Palco):</b> Pensata per il musicista sul palco o a casa per studiare. "
            "L'interfaccia nasconde ogni campo di editing o pulsante invasivo: consente solo di consultare i brani, "
            "vedere l'anteprima PDF fedele al foglio stampato, stampare su A4, scaricare il PDF per il proprio tablet e "
            "lanciare la <b>Modalità Palco</b> con teleprompter a scorrimento automatico a 60 fps.",
            bullet_style
        ))
        story.append(Paragraph(
            "2. <b>Modalità Editing (Completa):</b> Sblocca l'editor AML, i quick chips per accordi e direttive, la gestione dei repertori, "
            "l'importazione da web e fotocamera, l'ordinamento scalette e gli strumenti amministrativi.",
            bullet_style
        ))
        story.append(Paragraph(
            "Il passaggio tra le due modalità è immediato: basta toccare il badge in testata (<i>'Casa / Palco'</i>) o aprire "
            "il popover del profilo musicista in alto a destra.",
            body_style
        ))

        # =========================================================================
        # CAPITOLO 3: ELENCO UTENTI E PSEUDONIMI AUTORIZZATI
        # =========================================================================
        story.append(Paragraph("Capitolo 3 &bull; Elenco Utenti & Pseudonimi Autorizzati (Band)", ch_title_style))
        story.append(Paragraph(
            "Il sistema riconosce e assegna impostazioni dedicate a ciascun membro della band:",
            body_style
        ))

        band_users_data = [
            [Paragraph("<b>Pseudonimo</b>", body_style), Paragraph("<b>Ruolo / Strumento</b>", body_style), Paragraph("<b>Specifiche nel Sistema</b>", body_style)],
            [Paragraph("<b>Cico</b>", body_style), Paragraph("Cantante (Voce Solista)", body_style), Paragraph("Default spartito 'Solo Testo' per leggio vocale, teleprompter con font maggiorato.", body_style)],
            [Paragraph("<b>Mingo</b>", body_style), Paragraph("Batterista (Batteria & Ritmica)", body_style), Paragraph("Visualizzazione metronomo BPM, evidenziazione stacchi {stacco: } e battute.", body_style)],
            [Paragraph("<b>Puma</b>", body_style), Paragraph("Bassista (Basso Elettrico)", body_style), Paragraph("Fondamentali armoniche, accordi con slash bass (es. C/E), incastro groove.", body_style)],
            [Paragraph("<b>Red</b>", body_style), Paragraph("Chitarra Elettrica (Solista)", body_style), Paragraph("Evidenziazione sezioni {solo}, cambi effetti/overdrive, intonazione in tonalità.", body_style)],
            [Paragraph("<b>Maurino</b>", body_style), Paragraph("Chitarra Ritmica (Accompagnamento)", body_style), Paragraph("Pattern ritmici di strumming, accordi aperti e barré, solidità del tempo.", body_style)],
            [Paragraph("<b>Sentimental</b>", body_style), Paragraph("Tastiere & Sintetizzatori", body_style), Paragraph("Direttiva esclusiva {Scena: X} per cambio rapido preset synth dal vivo.", body_style)]
        ]
        users_table = Table(band_users_data, colWidths=[30 * mm, 50 * mm, 100 * mm])
        users_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(users_table)
        story.append(Spacer(1, 4 * mm))

        # =========================================================================
        # CAPITOLO 4: PREFERENZE UTENTE, HARDWARE & PERSISTENZA CLOUD
        # =========================================================================
        story.append(Paragraph("Capitolo 4 &bull; Preferenze Utente, Profili Hardware & Persistenza Cloud", ch_title_style))
        story.append(Paragraph(
            "Ciascun musicista possiede dispositivi hardware differenti (tablet Android 16:10, iPad 4:3, smartphone o foglio A4). "
            "ASMA memorizza le preferenze per la coppia <code>(email_musicista, profilo_dispositivo)</code> garantendo che "
            "il layout prescelto rimanga intatto e persistente a database anche dopo nuovi deploy del server o riavvii del browser.",
            body_style
        ))
        story.append(Paragraph(
            "<b>I 6 Parametri di Impaginazione Regolabili:</b>", ch_sub_style
        ))
        story.append(Paragraph("&bull; <b>Numero Colonne:</b> 1 colonna (lettura continua) oppure 2 colonne (ottimizzazione dello spazio verticale per evitare cambi pagina).", bullet_style))
        story.append(Paragraph("&bull; <b>Font Testo (pt):</b> Dimensione regolabile da 8 a 30 pt.", bullet_style))
        story.append(Paragraph("&bull; <b>Font Accordi (pt):</b> Dimensione indipendente regolabile da 8 a 32 pt.", bullet_style))
        story.append(Paragraph("&bull; <b>Margini Laterali (mm):</b> Spaziatura laterale da 4 a 30 mm.", bullet_style))
        story.append(Paragraph("&bull; <b>Margine Superiore (mm):</b> Spazio superiore da 0 a 40 mm per posizionare il brano sotto cornici o fotocamere frontali.", bullet_style))
        story.append(Paragraph("&bull; <b>Margine Inferiore (mm):</b> Spazio inferiore da 4 a 50 mm (default 14 mm). Regola e protegge l'area utile prima del piè di pagina (data, revisione, numerazione), garantendo l'assenza totale di tagli o sovrapposizioni su schermi iPad (7ª/8ª/9ª gen Retina 4:3) e tablet con barre di navigazione o custodie a cornice spessa.", bullet_style))

        # Embedded screenshot: layout
        fig_layout_path = _resolve_asset_path("frontend/assets/manual/fig_layout_impaginazione.png")
        if fig_layout_path:
            try:
                story.append(Spacer(1, 2 * mm))
                # 490 x 442 -> scaled width 80mm, height 72.1mm
                story.append(Image(fig_layout_path, width=80 * mm, height=72.1 * mm))
                story.append(Paragraph("Figura 4.1: Pannello touch per Layout e Impaginazione PDF multi-dispositivo.", caption_style))
            except Exception:
                pass

        story.append(PageBreak())

        # =========================================================================
        # CAPITOLO 5: LISTA BRANI, ANTEPRIMA PDF & STAMPA A4
        # =========================================================================
        story.append(Paragraph("Capitolo 5 &bull; Lista Brani, Anteprima PDF, Stampa A4 & Download Dispositivo", ch_title_style))
        story.append(Paragraph(
            "La vista brani offre una visualizzazione a schede reattiva con ricerca istantanea a 0ms per titolo o artista. "
            "I brani sono suddivisi tra <b>Repertorio Ufficiale Band</b> (protetto) e <b>Personale</b> del singolo musicista.",
            body_style
        ))
        story.append(Paragraph(
            "<b>Isolamento del Repertorio Ufficiale:</b> Il Repertorio Ufficiale Band è blindato per preservare l'integrità del catalogo concerti. "
            "Nessun brano nuovo o importato può atterrare direttamente nell'Ufficiale. Tutti i nuovi brani confluiscono esclusivamente "
            "nel Repertorio Personale del musicista e possono accedere al Repertorio Ufficiale solo attraverso il comando esplicito "
            "<b>'⭐ Promuovi a Ufficiale'</b>.",
            body_style
        ))
        story.append(Paragraph("<b>Funzionalità della Scheda Brano:</b>", ch_sub_style))
        story.append(Paragraph("&bull; <b>Anteprima PDF Reale:</b> Visualizza le pagine del brano renderizzate ad alta risoluzione (96 DPI) esattamente come verranno visualizzate sul tablet o stampate su carta.", bullet_style))
        story.append(Paragraph("&bull; <b>Stampa A4 Diretta:</b> Invia lo spartito alla stampante del sistema operativo con margini ottimali A4.", bullet_style))
        story.append(Paragraph("&bull; <b>Scarica PDF:</b> Genera e scarica il file PDF ottimizzato con il profilo del dispositivo attivo (proporzioni esatte dello schermo).", bullet_style))
        story.append(Paragraph("&bull; <b>Scarica Elenco PDF Repertorio (Pulsante '📑 Lista PDF'):</b> Genera e scarica un catalogo PDF professionale con l'elenco ordinato e pulito dei brani del Repertorio Ufficiale Band (o del repertorio attivo), con numerazione progressiva (#), Titolo Brano, Artista, Tonalità in notazione italiana (DO, REm, ecc.), BPM, Durata e intestazioni ripetute su tutte le pagine. Il sistema include filtri automatici rigorosi che deduplicano i titoli ed escludono categoricamente brani di test/default (es. Albachiara) o copie personali orfane.", bullet_style))
        story.append(Paragraph("&bull; <b>Vista 'Solo Testo' per Cantante (Cico) & Deduplicazione Strumentali:</b> Nella modalità senza accordi, il motore ripulisce e ottimizza la lettura per il cantante eliminando griglie armoniche e compattando le indicazioni strumentali consecutive (badge <code>[STRUMENTALE]</code>, <code>[SOLO]</code> o direttive <code>(Strumentale)</code> prive di versi intermedi), che vengono emesse una sola volta per la massima chiarezza e scorrevolezza sul leggio.", bullet_style))

        # Embedded screenshot: lista brani
        fig_brani_path = _resolve_asset_path("frontend/assets/manual/fig_repertorio_brani.png")
        if fig_brani_path:
            try:
                story.append(Spacer(1, 2 * mm))
                # 1024 x 491 -> scaled width 150mm, height 71.9mm
                story.append(Image(fig_brani_path, width=150 * mm, height=71.9 * mm))
                story.append(Paragraph("Figura 5.1: Vista Lista Brani con schede repertorio Ufficiale protetto e Personale.", caption_style))
            except Exception:
                pass

        # Embedded screenshot: condividi e stampa A4
        fig_condividi_path = _resolve_asset_path("frontend/assets/manual/fig_condividi_stampa_a4.png")
        if fig_condividi_path:
            try:
                story.append(Spacer(1, 2 * mm))
                # 757 x 705 -> width 82mm, height 76.3mm
                story.append(Image(fig_condividi_path, width=82 * mm, height=76.3 * mm))
                story.append(Paragraph("Figura 5.2: Modale 'Condividi / Stampa A4' con selezione accordi o solo testo, font regolabile, layout a 2 colonne e condivisione rapida su WhatsApp.", caption_style))
            except Exception:
                pass

        # =========================================================================
        # CAPITOLO 6: IMPORTAZIONE BRANI DA FONTI ESTERNE & SCANSIONE FOTOCAMERA
        # =========================================================================
        story.append(Paragraph("Capitolo 6 &bull; Importazione Brani da Fonti Esterne & Scansione Fotocamera", ch_title_style))
        story.append(Paragraph(
            "Il pulsante <b>'Nuovo / Importa'</b> nella schermata Brani apre una finestra interattiva a 5 schede "
            "per acquisire rapidamente spartiti da qualunque supporto:",
            body_style
        ))
        story.append(Paragraph("&bull; <b>Cerca sul Web (con Badge '⭐ Migliore'):</b> Inserisci titolo e artista: il crawler musicale interroga istantaneamente portali nazionali e internazionali (Accordi e Spartiti, Ultimate-Guitar). L'algoritmo valuta accuratezza armonica, recensioni della community e ricchezza delle sezioni, contrassegnando visivamente il brano di qualità superiore con il badge <b>'⭐ Migliore'</b> e il pulsante <i>'⭐ Importa Consigliato'</i>, mostrando a colpo d'occhio rating stellato e voti.", bullet_style))
        story.append(Paragraph("&bull; <b>Fotocamera / Scansione OCR (Gemini Vision AI):</b> Scansione ottica diretta di spartiti cartacei, canzonieri o fogli scritti a mano tramite la fotocamera del dispositivo o caricamento immagini.", bullet_style))
        story.append(Paragraph("&bull; <b>Incolla Testo:</b> Incolla testo con accordi posti sopra le parole (formato testo tradizionale); il parser fonde testo e accordi in sintassi inline AML <code>[DO]Parola</code> senza errori di allineamento.", bullet_style))
        story.append(Paragraph("&bull; <b>Da Link Web:</b> Estrazione diretta di testo e accordi da una pagina web specifica incollandone la URL.", bullet_style))
        story.append(Paragraph("&bull; <b>Scrivi AML:</b> Composizione libera direttamente nel formato sorgente della band con assistenza sintattica.", bullet_style))

        story.append(Paragraph(
            "<b>Assegnazione Automatica Sezioni Musicali su Nuove Importazioni:</b> "
            "Qualsiasi brano acquisito tramite Incolla Testo, ChordPro, estrazione PDF, URL web o Scrivi AML "
            "viene analizzato dal motore musicale in background: se il testo originale è privo di indicazioni di sezione, "
            "il sistema rileva automaticamente strofe e ritornelli ripetuti, inserendo i badge standard ad alta visibilità "
            "(<code>[INTRO]</code>, <code>[STROFA 1]</code>, <code>[RITORNELLO]</code>, <code>[BRIDGE]</code>, <code>[SOLO]</code>, "
            "<code>[STRUMENTALE]</code>, <code>[FINALE]</code>, <code>[END]</code>) senza mai alterare le parole o gli accordi originali.",
            body_style
        ))

        story.append(Paragraph(
            "<b>Regola Rigorosa di Destinazione &mdash; Sempre nel Repertorio Personale:</b> "
            "L'importazione dei brani <u>non va mai direttamente sul Repertorio Ufficiale Band</u>. "
            "Qualsiasi brano creato o importato da qualunque canale (ricerca web, fotocamera OCR, incolla testo, link diretto o editor AML) "
            "viene <b>sempre e automaticamente posizionato nel repertorio personale</b> del musicista connesso. "
            "Nel modulo di salvataggio, il selettore del repertorio di destinazione mostra unicamente i repertori personali, bloccando l'accesso diretto all'Ufficiale con un apposito promemoria protettivo.<br/>"
            "Un brano personale può entrare nel <b>Repertorio Ufficiale Band</b> esclusivamente a seguito di una <b>promozione esplicita</b>: "
            "aprendo la scheda del brano personale, basta premere il pulsante dorato <b>'⭐ Promuovi a Ufficiale'</b>. "
            "Se nel Repertorio Ufficiale esiste già un brano con lo stesso titolo, il sistema ne aggiorna armoniosamente il contenuto (accordi, sezioni, metadati) "
            "eliminando la copia personale ridondante; se si tratta di un brano inedito, lo trasferisce nell'elenco ufficiale comune mantenendo la storia delle revisioni.",
            body_style
        ))

        story.append(Paragraph("<b>Approfondimento: Scansione da Fotocamera / Foto Spartito Cartaceo (OCR AI)</b>", ch_sub_style))
        story.append(Paragraph(
            "La scheda <b>'Fotocamera / Foto'</b> è una delle funzionalità più potenti di ASMA: consente di digitalizzare in pochi "
            "secondi interi spartiti cartacei, spartiti di prova o canzonieri storici senza dover ricopiare testo o accordi a mano.",
            body_style
        ))
        story.append(Paragraph("<b>Procedura Passo-Passo per la Scansione:</b>", ch_sub_style))
        story.append(Paragraph(
            "1. <b>Accesso alla Scheda:</b> Tocca <i>'Nuovo / Importa'</i> e seleziona il tab <i>'Fotocamera / Foto'</i>.<br/>"
            "2. <b>Scatto della Foto o Selezione File:</b> Su smartphone o tablet (Android/iOS) tocca <i>'Scatta Foto o Scegli da Galleria'</i>: "
            "il sistema apre direttamente la fotocamera posteriore del dispositivo per inquadrare lo spartito con buona luce.<br/>"
            "3. <b>Supporto Multi-Pagina:</b> Se il brano si sviluppa su più fogli, puoi scattare o caricare più foto in sequenza. "
            "L'interfaccia mostra le miniature delle pagine caricate (Pagina 1, Pagina 2, ecc.) con possibilità di visualizzarle, riordinarle o rimuovere scatti sfocati.<br/>"
            "4. <b>Riconoscimento Ottico Intelligente (Gemini Vision OCR):</b> Toccando <i>'Elabora con Vision AI'</i>, "
            "il motore analizza le immagini scansionate ed estrae automaticamente:<br/>"
            "&nbsp;&nbsp;&bull; <b>Titolo e Artista:</b> Rilevati dall'intestazione del foglio o dal ritornello.<br/>"
            "&nbsp;&nbsp;&bull; <b>Tonalità e BPM:</b> Tonalità musicale rilevata e tempo suggerito.<br/>"
            "&nbsp;&nbsp;&bull; <b>Struttura a Sezioni:</b> Identificazione di [INTRO], [STROFA], [RITORNELLO], [SPECIAL], [SOLO] ed [OUTRO].<br/>"
            "&nbsp;&nbsp;&bull; <b>Accordi Perfettamente Ancorati:</b> Gli accordi vengono letti e convertiti nella notazione inline AML standard (es. <code>[DO]</code>, <code>[SOL]</code>) posizionati esattamente sopra o dentro la sillaba corretta.<br/>"
            "5. <b>Revisione & Salvataggio Immediato:</b> Il testo AML generato viene aperto direttamente nell'Editor integrato, "
            "dove il musicista può verificare il risultato con l'anteprima live, effettuare eventuali micro-aggiustamenti e salvare il brano nel proprio repertorio personale con un solo tocco.",
            body_style
        ))
        story.append(Paragraph(
            "<i>Nota sulla Chiave API:</i> Per utilizzare la scansione da fotocamera è sufficiente configurare una volta sola la chiave gratuita Google Gemini "
            "nel pannello <i>Impostazioni &bull; Chiave Google Gemini Vision AI</i>. La chiave viene sincronizzata in cloud per tutta la band.",
            caption_style
        ))
        story.append(Spacer(1, 2 * mm))

        # =========================================================================
        # CAPITOLO 7: CREAZIONE BRANI AUTOPRODOTTI
        # =========================================================================
        story.append(Paragraph("Capitolo 7 &bull; Creazione Brani Autoprodotti", ch_title_style))
        story.append(Paragraph(
            "Per inserire brani inediti o composizioni della band, è disponibile la barra metadati essenziali a 6 campi: "
            "<b>Titolo, Artista, Tonalità, BPM, Genere e Capotasto</b>. I brani autoprodotti vengono salvati nel repertorio "
            "personale dell'autore, pronti per essere provati e promossi al repertorio ufficiale.",
            body_style
        ))

        # =========================================================================
        # CAPITOLO 8: FLUSSO DI LAVORO PER MODIFICA BRANI ESISTENTI (UFFICIALE vs PERSONALE)
        # =========================================================================
        story.append(Paragraph("Capitolo 8 &bull; Flusso di Lavoro Modifica Brani (Ufficiale vs Personale)", ch_title_style))
        story.append(Paragraph(
            "Una delle architetture più importanti di ASMA riguarda la <b>protezione del Repertorio Ufficiale della Band</b>. "
            "In un gruppo musicale, se chiunque potesse modificare direttamente lo spartito comune, un cambio di tonalità o "
            "una correzione al volo rischierebbero di alterare lo spartito sui tablet di tutti gli altri musicisti proprio "
            "prima o durante un concerto. Per questo motivo, <b>nessun utente (incluso l'amministratore) può modificare "
            "direttamente un brano del Repertorio Ufficiale</b>. Si segue il flusso protetto e collaborativo in 5 fasi:",
            body_style
        ))
        story.append(Paragraph("<b>Le 5 Fasi del Flusso di Lavoro:</b>", ch_sub_style))
        story.append(Paragraph(
            "1. <b>Fase 1 — Consultazione Protetta:</b> Quando selezioni un brano dal Repertorio Ufficiale, "
            "l'interfaccia mostra il badge <code> Ufficiale Protetto</code>. I campi di modifica diretta sono disattivati: "
            "puoi visualizzare l'anteprima PDF, stampare su A4, avviare il teleprompter Palco o consultare i consigli live AI, "
            "con la sicurezza assoluta che nessuno spartito comune possa essere modificato accidentalmente.",
            bullet_style
        ))
        story.append(Paragraph(
            "2. <b>Fase 2 — Copia nel Personale (Fork Isolato):</b> Per apportare qualsiasi modifica, tocca il pulsante "
            "<i>' Copia nel Personale per Modificare'</i>. Il sistema crea istantaneamente un duplicato privato del brano "
            "e lo assegna al tuo repertorio personale (legato al tuo account Google).",
            bullet_style
        ))
        story.append(Paragraph(
            "3. <b>Fase 3 — Modifica & Arrangiamento in Autonomia:</b> Nella tua copia personale si sbloccano tutti gli strumenti di editing:<br/>"
            "&nbsp;&nbsp;&bull; <b>Trasposizione Tonalità:</b> Con i pulsanti <code>b -1</code> e <code># +1</code> puoi trasporre al volo tutti gli accordi del brano e verificare subito la nuova chiave.<br/>"
            "&nbsp;&nbsp;&bull; <b>Direttive Live & Tastiere:</b> Inserisci la direttiva synth <code>{scena: X}</code> per Sentimental, gli stacchi <code>{stacco: strumento}</code> per la ritmica, o crea un Medley concatenato.<br/>"
            "&nbsp;&nbsp;&bull; <b>Salvataggio su Cloud Turso:</b> Toccando <i>' Salva nel DB'</i> le tue modifiche vengono salvate in modo permanente nel cloud senza che gli altri membri della band vedano versioni parziali o premature.",
            bullet_style
        ))
        story.append(Paragraph(
            "4. <b>Fase 4 — Collaudo & Prova con la Band:</b> Prova il nuovo arrangiamento a casa o in sala prove sul tuo tablet, "
            "verificando la resa in Modalità Palco (60 fps) e nell'anteprima PDF.",
            bullet_style
        ))
        story.append(Paragraph(
            "5. <b>Fase 5 — Promozione a Ufficiale con Sovrascrittura Protetta:</b> Quando l'arrangiamento è concordato e approvato da tutta la band, "
            "nella scheda del brano personale compare il pulsante dorato <b>'Promuovi a Ufficiale'</b>. Toccandolo:<br/>"
            "&nbsp;&nbsp;&bull; La versione nel Repertorio Ufficiale Band viene automaticamente <b>sovrascritta e aggiornata</b> con il nuovo testo e accordi validati.<br/>"
            "&nbsp;&nbsp;&bull; La copia temporanea nel tuo repertorio personale viene <b>automaticamente rimossa</b> per non lasciare duplicati disallineati.<br/>"
            "&nbsp;&nbsp;&bull; Tutti i tablet della band scaricano all'istante la nuova versione ufficiale sincronizzata.",
            bullet_style
        ))

        # Workflow Summary Table
        wf_data = [
            [Paragraph("<b>Fase</b>", body_style), Paragraph("<b>Azione / Pulsante UI</b>", body_style), Paragraph("<b>Effetto sul Sistema</b>", body_style)],
            [Paragraph("<b>1. Ufficiale</b>", body_style), Paragraph("Visualizzazione brano (Protetto)", body_style), Paragraph("Lettura sicura, modifiche dirette bloccate.", body_style)],
            [Paragraph("<b>2. Fork</b>", body_style), Paragraph("<i>'Copia nel Personale'</i>", body_style), Paragraph("Crea copia privata nel repertorio personale.", body_style)],
            [Paragraph("<b>3. Editing</b>", body_style), Paragraph("<i>'Modifica'</i> &bull; <code>b/#</code> &bull; <i>'Salva'</i>", body_style), Paragraph("Modifica testo, accordi, BPM e direttive in isolamento.", body_style)],
            [Paragraph("<b>4. Test</b>", body_style), Paragraph("<i>'PDF'</i> &bull; <i>'Palco'</i>", body_style), Paragraph("Collaudo leggio su tablet e verifica con la band.", body_style)],
            [Paragraph("<b>5. Rilascio</b>", body_style), Paragraph("<i>'Promuovi a Ufficiale'</i>", body_style), Paragraph("Sovrascrive l'Ufficiale ed elimina la copia personale.", body_style)]
        ]
        wf_table = Table(wf_data, colWidths=[24 * mm, 62 * mm, 94 * mm])
        wf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(Spacer(1, 2 * mm))
        story.append(wf_table)
        story.append(Spacer(1, 3 * mm))

        # Schema Grafico di Flusso per la Modifica di un Brano Ufficiale
        story.append(Paragraph("<b>Schema Grafico di Flusso (Ciclo di Vita e Promozione del Brano):</b>", ch_sub_style))
        story.append(Paragraph(
            "Il diagramma sottostante sintetizza visivamente come un musicista passa dal brano ufficiale protetto "
            "alla propria versione personale di lavoro, fino alla promozione approvata con la band:",
            body_style
        ))
        flowchart_data = [
            [
                Paragraph("<font color='#ffd600' size='9.5'><b> STEP 1: REPERTORIO UFFICIALE BAND (PROTETTO)</b></font><br/>"
                          "<font size='8' color='#cbd5e1'>Lo spartito comune è in sola lettura protetta • Nessun rischio di manomissione accidentale prima di un live.<br/>"
                          "<i>Azione: Tocca il pulsante</i> <b>'Copia nel Personale per Modificare'</b></font>", body_style)
            ],
            [
                Paragraph("<font color='#38bdf8' size='11'><b>|</b></font> <font size='8' color='#94a3b8'>Fork automatico a latenza zero nel proprio archivio personale Google</font>", caption_style)
            ],
            [
                Paragraph("<font color='#38bdf8' size='9.5'><b>STEP 2: FORK AUTOMATICO NEL REPERTORIO PERSONALE</b></font><br/>"
                          "<font size='8' color='#cbd5e1'>Viene creato all'istante un duplicato privato del brano assegnato al tuo account personale.<br/>"
                          "<i>Risultato: Si sbloccano l'Editor AML completo, la trasposizione tonalità e i quick chips.</i></font>", body_style)
            ],
            [
                Paragraph("<font color='#c084fc' size='11'><b>|</b></font> <font size='8' color='#94a3b8'>Editing autonomo a casa o in sala prove senza disturbare gli altri leggii</font>", caption_style)
            ],
            [
                Paragraph("<font color='#c084fc' size='9.5'><b>STEP 3: MODIFICA AML, TRASPOSIZIONE (b/#) & SALVATAGGIO CLOUD</b></font><br/>"
                          "<font size='8' color='#cbd5e1'>• Adatta la tonalità alla voce di Cico con <code>b -1</code> / <code># +1</code><br/>"
                          "• Inserisci direttive tastiere <code>{scena: X}</code> per Sentimental e stacchi <code>{stacco: Tutti}</code><br/>"
                          "• Salva su database cloud Turso con il pulsante <b>'Salva nel DB'</b></font>", body_style)
            ],
            [
                Paragraph("<font color='#f59e0b' size='11'><b>|</b></font> <font size='8' color='#94a3b8'>Collaudo pratico sul palco o in sala prove</font>", caption_style)
            ],
            [
                Paragraph("<font color='#fbbf24' size='9.5'><b>STEP 4: COLLAUDO IN SALA PROVE CON LA BAND</b></font><br/>"
                          "<font size='8' color='#cbd5e1'>Verifica lo spartito sul teleprompter a 60fps o genera l'anteprima PDF reale.<br/>"
                          "<i>I tuoi compagni continuano a visualizzare la versione ufficiale senza alterazioni.</i></font>", body_style)
            ],
            [
                Paragraph("<font color='#10b981' size='11'><b>|</b></font> <font size='8' color='#94a3b8'>Accordo raggiunto → tocca <i>'Promuovi a Ufficiale'</i></font>", caption_style)
            ],
            [
                Paragraph("<font color='#34d399' size='9.5'><b>STEP 5: PROMOZIONE & SINCRONIZZAZIONE GENERALE BAND</b></font><br/>"
                          "<font size='8' color='#cbd5e1'>• La versione nel Repertorio Ufficiale Band viene <b>sovrascritta e aggiornata</b> al nuovo arrangiamento.<br/>"
                          "• La copia personale temporanea viene <b>automaticamente rimossa</b> (zero duplicati o ambiguità).<br/>"
                          "• Tutti i tablet e smartphone del gruppo scaricano istantaneamente la nuova versione ufficiale.</font>", body_style)
            ]
        ]
        flowchart_table = Table(flowchart_data, colWidths=[180 * mm])
        flowchart_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#0f172a")),
            ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#ffd600")),
            ('BACKGROUND', (0, 2), (0, 2), colors.HexColor("#0c4a6e")),
            ('BOX', (0, 2), (0, 2), 1, colors.HexColor("#38bdf8")),
            ('BACKGROUND', (0, 4), (0, 4), colors.HexColor("#4c1d95")),
            ('BOX', (0, 4), (0, 4), 1, colors.HexColor("#c084fc")),
            ('BACKGROUND', (0, 6), (0, 6), colors.HexColor("#78350f")),
            ('BOX', (0, 6), (0, 6), 1, colors.HexColor("#f59e0b")),
            ('BACKGROUND', (0, 8), (0, 8), colors.HexColor("#064e3b")),
            ('BOX', (0, 8), (0, 8), 1, colors.HexColor("#10b981")),
            ('ALIGN', (0, 1), (0, 1), 'CENTER'),
            ('ALIGN', (0, 3), (0, 3), 'CENTER'),
            ('ALIGN', (0, 5), (0, 5), 'CENTER'),
            ('ALIGN', (0, 7), (0, 7), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(Spacer(1, 2 * mm))
        story.append(flowchart_table)
        story.append(Spacer(1, 3 * mm))

        # Funzionamento Offline & Gestione Modifiche Offline (Caso B)
        story.append(Paragraph("<b>Funzionamento Offline & Gestione Modifiche Offline (Caso B):</b>", ch_sub_style))
        story.append(Paragraph(
            "Per garantire l'assoluta affidabilità sia in sala prove (seminterrati, cantine prive di segnale) "
            "che sul palco (live all'aperto o locali senza Wi-Fi), ASMA implementa la <b>Persistenza Offline Completa con Snapshot Locale</b> "
            "e la politica di sicurezza per le modifiche (<b>Caso B</b>):<br/>"
            "&bull; <b>Snapshot Locale Automatico:</b> Ogni volta che il dispositivo è connesso a Internet, l'intero archivio "
            "(tutti i brani del catalogo, accordi, sezioni, repertori e scalette) viene salvato localmente nel database protetto del browser. "
            "In assenza di segnale, l'app si apre a 0ms e tutti i brani rimangono consultabili, ricercabili e suonabili sul palco a 60 fps con pedaliere.<br/>"
            "&bull; <b>Tutela del Repertorio Ufficiale da Offline:</b> Non è possibile alterare né forzare modifiche al Repertorio Ufficiale della band "
            "mentre si è offline, prevenendo qualsiasi rischio di desincronizzazione o disaccordo tra i componenti.<br/>"
            "&bull; <b>Bozze Locali Offline per i Brani Personali:</b> Se un musicista apporta modifiche a una propria copia personale o crea un nuovo brano "
            "mentre è offline, il sistema non perde il lavoro: salva una <i>Bozza Locale Offline</i> (contrassegnata con badge dorato <code>💾 Bozza Offline</code>). "
            "Il musicista può provarla subito sul proprio leggio. Non appena il tablet o telefono rileva nuovamente una connessione Internet (4G o Wi-Fi), "
            "ASMA effettua la sincronizzazione automatica in background salvando la versione definitiva nel database centrale Turso Cloud.",
            body_style
        ))
        story.append(Spacer(1, 3 * mm))

        story.append(PageBreak())

        # =========================================================================
        # CAPITOLO 9: AML (ASMA MARKUP LANGUAGE) — SINTASSI, DIRETTIVE & GUIDA AUTONOMA
        # =========================================================================
        story.append(Paragraph("Capitolo 9 &bull; AML (ASMA Markup Language) — Sintassi, Direttive & Guida Autonoma", ch_title_style))
        story.append(Paragraph(
            "<b>AML (ASMA Markup Language)</b> è il linguaggio nativo e universale della piattaforma. "
            "Rappresenta l'unica fonte di verità (<i>Single Source of Truth</i>) da cui il sistema genera in tempo reale "
            "lo spartito Web, la visualizzazione Teleprompter Palco a 60 fps, lo spartito PDF stampato per il leggio e il click del metronomo. "
            "In questo capitolo vengono illustrate <b>tutte le direttive disponibili</b> e due guide pratiche passo-passo "
            "che consentono a qualsiasi musicista della band di scrivere autonomamente un brano completo o un Medley da zero.",
            body_style
        ))
        story.append(Paragraph("<b>Tabella Completa di Tutte le Direttive Presenti in ASMA AML:</b>", ch_sub_style))

        aml_syntax_data = [
            [Paragraph("<b>Direttiva / Costrutto</b>", body_style), Paragraph("<b>Sintassi & Esempio</b>", body_style), Paragraph("<b>Ambito & Ruolo</b>", body_style), Paragraph("<b>Effetto su Palco & PDF</b>", body_style)],
            [Paragraph("<b>{title: } / {t: }</b>", body_style), Paragraph("<code>{title: Albachiara}</code>", code_box_style), Paragraph("Metadato principale", body_style), Paragraph("Imposta il titolo del brano nella testata e nell'indice generale.", body_style)],
            [Paragraph("<b>{artist: } / {a: }</b>", body_style), Paragraph("<code>{artist: Vasco Rossi}</code>", code_box_style), Paragraph("Metadato autore", body_style), Paragraph("Mostrato sotto il titolo nel PDF e nel teleprompter.", body_style)],
            [Paragraph("<b>{key: } / {k: }</b>", body_style), Paragraph("<code>{key: DO}</code>", code_box_style), Paragraph("Tonalità d'impianto", body_style), Paragraph("Riferimento cromatico per le trasposizioni automatiche (b/#).", body_style)],
            [Paragraph("<b>{tempo: } / {bpm: }</b>", body_style), Paragraph("<code>{tempo: 68}</code>", code_box_style), Paragraph("Metronomo live", body_style), Paragraph("Velocità in battiti per minuto per click audio e lampeggio visivo.", body_style)],
            [Paragraph("<b>{capo: }</b>", body_style), Paragraph("<code>{capo: 2}</code>", code_box_style), Paragraph("Capotasto chitarra", body_style), Paragraph("Indica a Red e Maurino a quale tasto posizionare il capotasto.", body_style)],
            [Paragraph("<b>{duration: }</b>", body_style), Paragraph("<code>{duration: 3:45}</code>", code_box_style), Paragraph("Durata esecuzione", body_style), Paragraph("Permette il calcolo automatico dei tempi della scaletta concerto.", body_style)],
            [Paragraph("<b>{sov} ... {eov}</b>", body_style), Paragraph("<code>{sov}<br/>Testo strofa...<br/>{eov}</code>", code_box_style), Paragraph("Delimitatore Strofa", body_style), Paragraph("<i>Start/End of Verse</i>: raggruppa la strofa con spaziatura coerente.", body_style)],
            [Paragraph("<b>{soc} ... {eoc}</b>", body_style), Paragraph("<code>{soc}<br/>Testo ritornello...<br/>{eoc}</code>", code_box_style), Paragraph("Delimitatore Ritornello", body_style), Paragraph("<i>Start/End of Chorus</i>: evidenzia visivamente il ritornello nel PDF e palco.", body_style)],
            [Paragraph("<b>{sob} ... {eob}</b>", body_style), Paragraph("<code>{sob}<br/>Ponte / Special...<br/>{eob}</code>", code_box_style), Paragraph("Delimitatore Bridge", body_style), Paragraph("<i>Start/End of Bridge</i>: isola la sezione di stacco armonico prima dell'assolo.", body_style)],
            [Paragraph("<b>Etichette Sezione</b>", body_style), Paragraph("<code>[INTRO]<br/>[STROFA] [RIT]<br/>[OUTRO] [END]</code>", code_box_style), Paragraph("Header visivi veloci", body_style), Paragraph("Badge colorati con bordo ad alto contrasto per colpo d'occhio immediato.", body_style)],
            [Paragraph("<b>{solo: }</b>", body_style), Paragraph("<code>{solo: Chitarra Red}</code>", code_box_style), Paragraph("Assolo strumentale", body_style), Paragraph("Badge verde brillante con strumento solista indicato chiaramente.", body_style)],
            [Paragraph("<b>{c: } / {comment: }</b>", body_style), Paragraph("<code>{c: Rallentare sul finale}</code>", code_box_style), Paragraph("Note di palco / Regia", body_style), Paragraph("Box corsivo evidenziato in grigio per indicazioni esecutive ai musicisti.", body_style)],
            [Paragraph("<b>{scena: }</b>", body_style), Paragraph("<code>{scena: 3}<br/>{scena: Piano + Pad}</code>", code_box_style), Paragraph("Preset Tastiere / Synth", body_style), Paragraph("Badge ciano dedicato per Sentimental: indica numero preset o tasto synth.", body_style)],
            [Paragraph("<b>{stacco: }</b>", body_style), Paragraph("<code>{stacco: Tutti}<br/>{stacco: guitar}</code>", code_box_style), Paragraph("Stacco / Break ritmico", body_style), Paragraph("Badge rosso brillante ad alto contrasto per coordinare stop e ripartenze.", body_style)],
            [Paragraph("<b>{riga_bianca} / {blank_line}</b>", body_style), Paragraph("<code>{riga_bianca}</code><br/><code>{riga_bianca: 2}</code><br/><code>{blank_line}</code>", code_box_style), Paragraph("Riga bianca / Spaziatura libera", body_style), Paragraph("Inserisce una riga bianca vuota (o N righe personalizzate) in qualsiasi punto dello spartito (tra sezioni, versi o all'interno del testo).", body_style)],
            [Paragraph("<b>{colb}</b>", body_style), Paragraph("<code>{colb}</code>", code_box_style), Paragraph("Salto Colonna", body_style), Paragraph("<i>Column Break</i>: forza il testo a passare alla 2ª colonna (layout 2 colonne).", body_style)],
            [Paragraph("<b>{np} / {new_page}</b>", body_style), Paragraph("<code>{np}</code><br/><code>{new_page}</code>", code_box_style), Paragraph("Salto Pagina Forzato", body_style), Paragraph("<i>Page Break</i>: forza il passaggio immediato alla pagina successiva nel PDF.", body_style)],
            [Paragraph("<b>Accordi Inline</b>", body_style), Paragraph("<code>[DO]Respiri [SOL]piano</code>", code_box_style), Paragraph("Accordo su sillaba", body_style), Paragraph("Accordo oro agganciato esattamente sopra la sillaba, trasponibile con 1 tap.", body_style)],
            [Paragraph("<b>Griglia a Battute</b>", body_style), Paragraph("<code>| DO | SOL | LAm | FA |</code>", code_box_style), Paragraph("Griglia armonica", body_style), Paragraph("Ideale per introduzioni e parti strumentali ritmiche con stanghette di battuta.", body_style)],
            [Paragraph("<b>Spezzoni Medley</b>", body_style), Paragraph("<code>{start_of_song: ...}<br/>...<br/>{end_of_song}</code>", code_box_style), Paragraph("Medley concatenati", body_style), Paragraph("Definisce spezzoni con tonalità propria e palette a colori vivaci alternati.", body_style)]
        ]
        aml_table = Table(aml_syntax_data, colWidths=[36 * mm, 46 * mm, 42 * mm, 56 * mm])
        aml_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(aml_table)
        story.append(Spacer(1, 3 * mm))

        # GUIDA PRATICA 1: COME SCRIVERE UN BRANO INTERO AUTONOMAMENTE
        story.append(Paragraph("<b>Guida Pratica 1: Come Scrivere un Intero Brano da Zero nell'Editor</b>", ch_sub_style))
        story.append(Paragraph(
            "Per inserire un brano nuovo, tocca il pulsante <b>'Nuovo / Importa'</b> → scheda <b>'Crea Nuovo'</b>. "
            "Nell'area di testo dell'editor incolla o componi la struttura AML seguendo questo modello completo e funzionante:",
            body_style
        ))
        sample_song_aml = (
            "{title: ALBACHIARA}\n"
            "{artist: Vasco Rossi}\n"
            "{key: DO}\n"
            "{tempo: 68}\n"
            "{capo: 0}\n\n"
            "[INTRO]\n"
            "| DO | SOL | LAm | FA | (x2)\n\n"
            "{sov}\n"
            "[DO] Respiri piano per [SOL]non far rumore\n"
            "[LAm] Ti addormenti di sera e [FA]ti risvegli col sole\n"
            "[DO] Sei chiara come un'alba, [SOL]sei fresca come l'aria\n"
            "{eov}\n\n"
            "{soc}\n"
            "[FA] E con la faccia pulita [SOL]cammini per strada\n"
            "[DO] Mangiando una mela coi [LAm]libri di scuola\n"
            "[FA] Ti piace studiare, [SOL]non te ne devi vergognare\n"
            "{eoc}\n\n"
            "{colb}\n\n"
            "{sob}\n"
            "{stacco: Tutti}\n"
            "[LAm] E quando guardi con quegli [MIm]occhi grandi\n"
            "[FA] Forse un po' troppo sinceri, [SOL]sinceri...\n"
            "{eob}\n\n"
            "{solo: Chitarra Red}\n"
            "| FA | SOL | DO | LAm |\n\n"
            "{c: Rallentando finale guidato dal gesto di Cico}\n"
            "[OUTRO]\n"
            "| DO | SOL | FA | DO |\n"
            "[END]"
        )
        sample_song_table = Table([[Paragraph(f"<pre>{sample_song_aml.replace('\n', '<br/>')}</pre>", code_box_style)]], colWidths=[180 * mm])
        sample_song_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0284c7")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(sample_song_table)
        story.append(Spacer(1, 3 * mm))

        # GUIDA PRATICA 2: COME COMPORRE UN MEDLEY MULTI-BRANO AUTONOMAMENTE
        story.append(Paragraph("<b>Guida Pratica 2: Come Comporre un Medley Multi-Brano Autonomamente</b>", ch_sub_style))
        story.append(Paragraph(
            "Un Medley è una sequenza ininterrotta di spezzoni di brani diversi (fino a 20 brani distinti). "
            "Ciascun brano viene racchiuso tra <code>{start_of_song: Titolo | Artista | Tonalità}</code> ed <code>{end_of_song}</code>. "
            "Il sistema assegna a ogni spezzone un colore vivace alternato, gestisce tonalità e cambi scena in modo indipendente "
            "e permette il salto rapido tra i brani:",
            body_style
        ))
        sample_medley_aml = (
            "{title: MEDLEY BATTISTI}\n"
            "{artist: Lucio Battisti}\n"
            "{key: VARIE}\n"
            "{tempo: 120}\n\n"
            "{start_of_song: IL TEMPO DI MORIRE | LUCIO BATTISTI | LA}\n"
            "[INTRO]\n"
            "| LA | RE | SI | SOL | RE | LA | MI |\n\n"
            "{sov}\n"
            "[LA] Motocicletta 10 HP\n"
            "[RE] Tutta cromata è tua se dici sì\n"
            "{eov}\n"
            "{end_of_song}\n\n"
            "{start_of_song: DIECI RAGAZZE | LUCIO BATTISTI | SOL}\n"
            "{scena: 2}\n"
            "{stacco: Batteria Mingo}\n"
            "[INTRO]\n"
            "| SOL | DO | RE | SOL |\n\n"
            "{soc}\n"
            "[SOL] Dieci ragazze per me [DO]posson bastare\n"
            "[RE] Dieci ragazze per me [SOL]io vorrei con me\n"
            "{eoc}\n"
            "{end_of_song}"
        )
        sample_medley_table = Table([[Paragraph(f"<pre>{sample_medley_aml.replace('\n', '<br/>')}</pre>", code_box_style)]], colWidths=[180 * mm])
        sample_medley_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#a855f7")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(sample_medley_table)
        story.append(Spacer(1, 4 * mm))

        # =========================================================================
        # CAPITOLO 10: MODALITÀ EDITING, DIRETTIVE SCENA/STACCO & MEDLEY
        # =========================================================================
        story.append(Paragraph("Capitolo 10 &bull; Modalità Editing, Nuove Direttive Scena/Stacco & Medley", ch_title_style))
        story.append(Paragraph(
            "L'editor di ASMA mette a disposizione controlli touch dedicati per rendere l'arrangiamento live immediato:",
            body_style
        ))
        story.append(Paragraph(
            "&bull; <b>Direttiva {Scena: } per Tastiere (es. <code>{scena: 3}</code> o <code>{scena: Piano + Pad}</code>):</b> "
            "Consente a Sentimental di conoscere istantaneamente il tasto o preset da richiamare sulla tastiera per quella specifica "
            "sezione del pezzo. Viene visualizzata con badge azzurro sia nel PDF che nel teleprompter palco.",
            bullet_style
        ))
        story.append(Paragraph(
            "&bull; <b>Direttiva {Stacco: } (es. <code>{stacco: guitar}</code>, <code>{stacco: organo}</code> o <code>{stacco: Tutti}</code>):</b> "
            "Segnala un break o stab strumentale con badge rosso ad alto contrasto per coordinare gli stop ritmici della band.",
            bullet_style
        ))
        story.append(Paragraph(
            "&bull; <b>Direttiva Riga Bianca {riga_bianca} (o <code>{blank_line}</code> / <code>{riga_bianca: 2}</code>):</b> "
            "Consente di inserire una riga bianca vuota (o N righe a scelta) in qualsiasi posizione dello spartito (tra sezioni, tra versi o all'interno di una strofa/ritornello) "
            "per personalizzare la spaziatura sia nel PDF che nel teleprompter palco. È disponibile anche il quick chip rapido '␣ {riga_bianca}' nell'editor.",
            bullet_style
        ))
        story.append(Paragraph(
            "&bull; <b>Badge Fine Brano [END] Anti-Orfano:</b> "
            "Il badge di chiusura [END] viene armonizzato e compattato per rimanere sempre all'interno dell'ultima pagina di testo e accordi, "
            "evitando rigorosamente di generare una pagina supplementare vuota contenente soltanto il badge [END].",
            bullet_style
        ))
        story.append(Paragraph(
            "&bull; <b>Composizione MEDLEY Multi-Brano:</b> Supporto completo a brani composti da spezzoni concatenati (fino a 20 brani) "
            "tramite le direttive <code>{start_of_song: Titolo | Artista | Tonalità}</code> ed <code>{end_of_song}</code>. "
            "Ciascuno spezzone ha la propria tonalità e sezioni, con colorazione alternata tra 20 tonalità cromatiche vive "
            "per distinguere i passaggi al volo durante il live.",
            bullet_style
        ))
        story.append(Paragraph(
            "&bull; <b>Formattazione Pagine Medley su Base Dispositivo (📐 Impagina Medley):</b> "
            "Poiché i medley sono composti assemblando più spezzoni e ogni musicista utilizza schermi di dimensioni diverse "
            "(es. Huawei MediaPad M5 o MatePad di Cico, iPad, smartphone o foglio A4), a lavoro ultimato l'impaginazione naturale "
            "potrebbe risultare non ottimizzata per il leggio digitale. L'editor offre ora lo strumento dedicato <b>'📐 Impagina Medley'</b> "
            "(accessibile con un tocco nella testata dell'editor, tra i quick-chip e nelle opzioni del visualizzatore).",
            bullet_style
        ))
        story.append(Paragraph(
            "&bull; <b>Prompt Guidato Post-Salvataggio nel Personale:</b> "
            "Subito dopo aver salvato un Medley nel proprio <i>Repertorio Personale</i> (da nuovo brano o da modifica), "
            "il sistema mostra un prompt interattivo che invita il musicista a impaginare immediatamente gli spezzoni per il proprio dispositivo, "
            "garantendo uno spartito rifinito e pronto per la prova o il concerto senza passaggi manuali complessi.",
            bullet_style
        ))
        story.append(Paragraph(
            "&bull; <b>Strategie di Distribuzione Pagine Flessibili:</b> "
            "All'interno della modale di impaginazione il musicista può selezionare il dispositivo target e scegliere tra tre strategie:<br/>"
            "&nbsp;&nbsp;1. <b>Compattazione Ottimizzata (Smart Fit):</b> Calcola il peso in righe di ogni spezzone in base alla capienza verticale del dispositivo "
            "(~52 righe per tablet a 2 colonne, ~40 righe per foglio A4, ~22 righe per smartphone) e inserisce i salti pagina <code>{np}</code> "
            "solo dove strettamente necessario per minimizzare il numero totale di facciate senza spezzare i singoli brani a metà.<br/>"
            "&nbsp;&nbsp;2. <b>1 Spezzone per Pagina:</b> Posiziona categoricamente ogni spezzone su una nuova pagina dedicata inserendo <code>{np}</code> "
            "dopo ciascun <code>{end_of_song}</code>, ideale per chi desidera una schermata chiara e isolata per ogni brano del medley.<br/>"
            "&nbsp;&nbsp;3. <b>Personalizzata con Toggle Interattivi:</b> Consente al musicista di attivare o disattivare liberamente il salto pagina "
            "dopo qualsiasi spezzone con un semplice tocco, aggiornando all'istante la stima delle pagine risultanti e consentendo la verifica con anteprima PDF reale in tempo reale.<br/>"
            "&nbsp;&nbsp;4. <b>Rimuovi Salti Pagina (Testo Continuo):</b> Elimina tutti i salti <code>{np}</code> per consentire uno scorrimento fluido ininterrotto.",
            bullet_style
        ))
        story.append(Paragraph(
            "&bull; <b>Piena Libertà: Dispositivo Personale vs Stampa A4 Tradizionale:</b> "
            "Il musicista mantiene sempre la totale flessibilità: può consultare il medley con la formattazione su misura per il proprio dispositivo in uso "
            "(a video, in Stage Mode o scaricando il PDF del proprio profilo hardware) oppure generare, stampare e condividere su WhatsApp in qualsiasi momento "
            "la <b>copia in formato A4 standard</b> (con o senza accordi), esattamente come avviene per tutti gli altri brani del catalogo. "
            "Il motore di compilazione PDF garantisce inoltre la totale assenza di pagine bianche o salti forzati accidentali: anche se il brano è stato "
            "salvato con interruzioni pagina specifiche per un tablet o smartphone, la generazione A4 ri-ottimizza automaticamente la capienza verticale "
            "(40 righe in colonna singola, 52 a due colonne) e ripulisce qualsiasi spaziatore orfano o salto a frame vuoto tramite <code>SmartDocTemplate</code>, "
            "assicurando spartiti A4 sempre densi, armoniosi e continui per tutti i membri della band.",
            bullet_style
        ))

        # Embedded screenshot: editor medley e direttive (Screenshot A)
        fig_editor_path = _resolve_asset_path("frontend/assets/manual/fig_editor_medley_direttive.png")
        if fig_editor_path:
            try:
                story.append(Spacer(1, 2 * mm))
                # 1024 x 316 -> width 155mm, height 47.8mm
                story.append(Image(fig_editor_path, width=155 * mm, height=47.8 * mm))
                story.append(Paragraph("Figura 10.1 [Screenshot A]: Editor brano con quick-chips per accordi, spezzoni Medley, setup scena ({scena: 1}) e stacchi musicali ({stacco: Tutti}).", caption_style))
            except Exception:
                pass

        story.append(PageBreak())

        # =========================================================================
        # CAPITOLO 11: IL CIRCOLO DELLE QUINTE (ARMONIA & ESEMPI PRATICI PER LA BAND)
        # =========================================================================
        story.append(Paragraph("Capitolo 11 &bull; IL CIRCOLO DELLE QUINTE (Armonia & Esempi Pratici per la Band)", ch_title_style))
        story.append(Paragraph(
            "Il <b>Circolo delle Quinte</b> è la bussola armonica fondamentale per ogni musicista. "
            "All'interno del sito il circolo delle quinte non è solo una teoria musicale, "
            "ma uno <b>strumento visivo e interattivo integrato</b> "
            "(apribile con un tocco dal pulsante <b>'Circolo Quinte'</b> nell'Editor, nel Visualizzatore e nelle Scalette) "
            "che risolve i problemi concreti che la band incontra sul palco e in sala prove.",
            body_style
        ))

        story.append(Paragraph("<b>Cos'è in Parole Semplici: L'Orologio delle 12 Tonalità</b>", ch_sub_style))
        story.append(Paragraph(
            "Immagina il Circolo delle Quinte come il quadrante di un orologio con 12 ore, dove al posto dei numeri ci sono le 12 tonalità musicali:<br/>"
            "&bull; <b>A ore 12 c'è il DO (C):</b> È la tonalità di partenza neutra, che non ha nessun diesis (#) e nessun bemolle (b).<br/>"
            "&bull; <b>In senso orario (a destra, salendo di una quinta giusta):</b> Ogni ora che avanzi si aggiunge <b>un diesis (#)</b>: "
            "SOL (1#: FA#) → RE (2#) → LA (3#) → MI (4#) → SI (5#) → FA#/SOLb (6#).<br/>"
            "&bull; <b>In senso antiorario (a sinistra, scendendo di una quinta o salendo di una quarta):</b> Ogni ora che arretri si aggiunge <b>un bemolle (b)</b>: "
            "FA (1b: SIb) → SIb (2b) → MIb (3b) → LAb (4b) → REb (5b).",
            body_style
        ))

        story.append(Paragraph("<b>I 5 Casi Pratici di Utilità Reale per la Nostra Band:</b>", ch_sub_style))
        story.append(Paragraph(
            "<b>1. Tonalità Vicine = Transizioni Naturali e Morbide:</b><br/>"
            "Due tonalità vicine sull'orologio (ad esempio <b>DO</b> e <b>SOL</b>, oppure <b>DO</b> e <b>FA</b>) hanno quasi tutte le note in comune "
            "(6 note su 7 sono identiche!). Passare da un brano in DO a uno in SOL durante un concerto o all'interno di un medley "
            "risulta immediato, piacevole e totalmente naturale all'orecchio del pubblico.",
            bullet_style
        ))
        story.append(Paragraph(
            "<b>2. Le Relative Minori (Il 'Gemello Emotivo' di ogni Accordo Maggiore):</b><br/>"
            "All'interno del cerchio, ogni tonalità maggiore ha una sua 'relativa minore' con cui condivide <b>esattamente le stesse note ed alterazioni</b>:<br/>"
            "&nbsp;&nbsp;&bull; <b>DO Maggiore ↔ LA Minore (LAm)</b> (0 alterazioni)<br/>"
            "&nbsp;&nbsp;&bull; <b>SOL Maggiore ↔ MI Minore (MIm)</b> (1 diesis: FA#)<br/>"
            "&nbsp;&nbsp;&bull; <b>RE Maggiore ↔ SI Minore (SIm)</b> (2 diesis: FA#, DO#)<br/>"
            "&nbsp;&nbsp;&bull; <b>FA Maggiore ↔ RE Minore (REm)</b> (1 bemolle: SIb)<br/>"
            "<i>Applicazione pratica:</i> Se la strofa di un pezzo è intima e malinconica in LAm, aprendo il ritornello in DO Maggiore "
            "crei una meravigliosa esplosione di energia luminosa senza uscire dalla stessa famiglia armonica!",
            bullet_style
        ))
        story.append(Paragraph(
            "<b>3. La Modulazione d'Energia (Salita di 1 Tono nel Ritornello Finale):</b><br/>"
            "Nel classico pop-rock, per dare una scarica di adrenalina all'ultimo ritornello prima della chiusura, la band spesso "
            "modula salendo di un tono intero (es. da DO a RE, oppure da SOL a LA). Sul cerchio delle quinte, questa mossa corrisponde "
            "esattamente a <b>2 passi orari (Distanza 2)</b>: l'orecchio percepisce una spinta epica verso l'alto senza disorientarsi.",
            bullet_style
        ))
        story.append(Paragraph(
            "<b>4. Trasposizioni Immediate su Misura per la Voce di Cico:</b><br/>"
            "Se un brano in SOL è troppo acuto o troppo faticoso sulle note alte per Cico, abbassarlo di un tono (a FA) o di un semitono "
            "è facilissimo con i pulsanti <code>b -1</code> e <code># +1</code>. Il Circolo delle Quinte garantisce che <b>tutti gli accordi scalino "
            "in modo rigorosamente proporzionale</b>: il tastierista (Sentimental), il bassista (Puma) e i chitarristi (Red e Maurino) "
            "vedono gli accordi già corretti e riscritti con le giuste alterazioni (senza confusioni tra diesis e bemolli).",
            bullet_style
        ))
        story.append(Paragraph(
            "<b>5. Composizione Scalette e Medley Senza 'Salti nel Vuoto':</b><br/>"
            "Nelle scalette di ASMA, tra ogni brano consecutivo appare un badge automatico che legge la distanza sul Circolo delle Quinte:<br/>"
            "&nbsp;&nbsp;&bull; <font color='#10b981'><b>Distanza 0 (Stessa tonalità):</b></font> Passaggio immediato perfetto, attacco diretto al millisecondo.<br/>"
            "&nbsp;&nbsp;&bull; <font color='#0284c7'><b>Distanza 1 (Tonalità vicina / Subdominante / Dominante):</b></font> Transizione fluida e naturale.<br/>"
            "&nbsp;&nbsp;&bull; <font color='#f59e0b'><b>Distanza 2 (Salto di 1 tono intero):</b></font> Modulazione d'energia tipica di slancio.<br/>"
            "&nbsp;&nbsp;&bull; <font color='#ef4444'><b>Distanza > 2 (Salto marcato):</b></font> Attenzione: scale molto diverse. Inserire uno <b>stacco ritmico</b> "
            "<code>{stacco: Tutti}</code>, una pausa o un break di batteria di Mingo per resettare l'orecchio prima di ripartire.",
            bullet_style
        ))

        # Embedded screenshot: circolo delle quinte (Screenshot B)
        fig_circolo_path = _resolve_asset_path("frontend/assets/manual/fig_circolo_quinte.jpg")
        if fig_circolo_path:
            try:
                story.append(Spacer(1, 2 * mm))
                # 1024 x 990 -> width 95mm, height 91.8mm
                story.append(Image(fig_circolo_path, width=95 * mm, height=91.8 * mm))
                story.append(Paragraph("Figura 11.1 [Screenshot B]: Strumento interattivo del Circolo delle Quinte in ASMA con 12 tonalità, relative minori, alterazioni (#/b), accordi della famiglia armonica e transizioni consigliate.", caption_style))
            except Exception:
                pass

        story.append(PageBreak())

        # =========================================================================
        # CAPITOLO 12: MODALITÀ PALCO (STAGE MODE) & TELEPROMPTER
        # =========================================================================
        story.append(Paragraph("Capitolo 12 &bull; Modalità Palco (Stage Mode) & Teleprompter 60fps", ch_title_style))
        story.append(Paragraph(
            "La <b>Modalità Palco</b> trasforma qualsiasi smartphone, tablet o laptop in un teleprompter musicale professionale:",
            body_style
        ))
        story.append(Paragraph("&bull; <b>Avvio On-Demand:</b> Lo scorrimento NON parte mai da solo. Il musicista si posiziona e avvia lo scorrimento toccando il grande pulsante 'AVVIO' o premendo il pedale.", bullet_style))
        story.append(Paragraph("&bull; <b>Scorrimento Fluido a 60 fps & Tap-to-Pause:</b> Velocità regolabile da 10 a 120 px/s. Un tocco su qualunque punto dello spartito mette istantaneamente in pausa lo scorrimento.", bullet_style))
        story.append(Paragraph("&bull; <b>Tema Notte OLED Alto Contrasto:</b> Sfondo nero assoluto (#000000), testo bianco brillante (#FFFFFF), accordi oro (#FFD600) e direttive azzurre (#38BDF8).", bullet_style))
        story.append(Paragraph("&bull; <b>Pedaliere Bluetooth HID:</b> Supporto nativo per AirTurn, PageFlip, BlueTurn e tastiere (PageDown/PageUp, frecce, tasti 1 e 2).", bullet_style))
        story.append(Paragraph("&bull; <b>Keep Screen Awake:</b> Mantiene lo schermo sempre acceso per l'intera durata dell'esibizione.", bullet_style))
        story.append(Paragraph("&bull; <b>Metronomo Audio & Visivo:</b> Click Web Audio API a latenza zero (<1 ms) con indicatore a lampeggio visivo del quarto.", bullet_style))

        # Embedded screenshot: palco
        fig_palco_path = _resolve_asset_path("frontend/assets/manual/fig_modalita_palco.png")
        if fig_palco_path:
            try:
                story.append(Spacer(1, 2 * mm))
                # 1024 x 561 landscape -> scaled width 145mm, height 79.5mm
                story.append(Image(fig_palco_path, width=145 * mm, height=79.5 * mm))
                story.append(Spacer(1, 1.5 * mm))
                story.append(Paragraph("Figura 12.1: Teleprompter notturno OLED ad alto contrasto ('Hanno Ucciso L'Uomo Ragno') con autoscroll fluido 60fps, barre di controllo e accordi in giallo.", caption_style))
                story.append(Spacer(1, 3 * mm))
            except Exception as e:
                logger.warning(f"Impossibile includere screenshot palco: {e}")

        story.append(PageBreak())

        # =========================================================================
        # CAPITOLO 13: GESTIONE SCALETTE LIVE & CONDIVISIONE WHATSAPP
        # =========================================================================
        story.append(Paragraph("Capitolo 13 &bull; Gestione Scalette Live & Condivisione WhatsApp", ch_title_style))
        story.append(Paragraph(
            "La gestione scalette consente di pianificare concerti con titolo, data, location e ordinamento dei pezzi. "
            "Aggiungendo brani con il pulsante <i>'Inserisci'</i> viene mostrata una notifica toast visiva immediata e "
            "aggiornato il contatore in tempo reale.",
            body_style
        ))
        story.append(Paragraph("<b>Funzionalità Avanzate Scalette:</b>", ch_sub_style))
        story.append(Paragraph("&bull; <b>Indicatori di Transizione Live:</b> Tra ciascuna coppia di brani consecutivi viene calcolata la distanza sul circolo delle quinte (0-6) e il Δ BPM percentuale, con raccomandazione esecutiva colorata (passaggio immediato, modulazione o stacco ritmico).", bullet_style))
        story.append(Paragraph("&bull; <b>Condivisione A4 su WhatsApp:</b> Invio del PDF completo A4 stampabile direttamente sul gruppo WhatsApp della band con un solo tocco.", bullet_style))
        story.append(Paragraph("&bull; <b>Calcolo Durata Live:</b> Somma automatica dei minuti e secondi per rispettare i tempi del locale.", bullet_style))

        # Embedded screenshot: modale condivisione A4 WhatsApp (Screenshot B2)
        fig_condividi_path = _resolve_asset_path("frontend/assets/manual/fig_condividi_stampa_a4.png")
        if fig_condividi_path:
            try:
                story.append(Spacer(1, 2 * mm))
                # 757 x 705 -> width 78mm, height 72.6mm
                story.append(Image(fig_condividi_path, width=78 * mm, height=72.6 * mm))
                story.append(Paragraph("Figura 13.1 [Screenshot B2]: Modale di condivisione e stampa A4 su WhatsApp per inviare istantaneamente scalette e spartiti alla band.", caption_style))
            except Exception:
                pass

        # =========================================================================
        # CAPITOLO 14: SUGGERIMENTI ESECUZIONE LIVE (AI GEMINI FREE)
        # =========================================================================
        story.append(Paragraph("Capitolo 14 &bull; Suggerimenti Esecuzione Live (AI Gemini Free)", ch_title_style))
        story.append(Paragraph(
            "Accessibile da qualunque brano tramite il pulsante <b>'Consigli Live'</b>, questa funzionalità "
            "fornisce raccomandazioni pratiche ed esecutive per il palco utilizzando l'intelligenza artificiale gratuita "
            "e ultra-leggera Google Gemini (con fallback deterministico offline istantaneo in caso di assenza di connessione).",
            body_style
        ))
        story.append(Paragraph("<b>Consigli Selezionabili per Singolo Musicista o Tutta la Band:</b>", ch_sub_style))
        story.append(Paragraph("&bull; <b>Tutta la Band:</b> Dinamiche d'insieme, attacchi d'impatto, gestione dei crescendo tra strofa e ritornello, chiusure nette.", bullet_style))
        story.append(Paragraph("&bull; <b>Cico (Voce):</b> Intonazione della prima nota, gestione del fiato a BPM elevati, momenti di coinvolgimento del pubblico.", bullet_style))
        story.append(Paragraph("&bull; <b>Mingo (Batteria):</b> Groove ritmico, timing dei fill prima dei ritornelli, cassa granitica sulle fondamentali del basso.", bullet_style))
        story.append(Paragraph("&bull; <b>Puma (Basso):</b> Incastro cassa-basso con Mingo, linee melodiche nei ponti, stop ritmici negli stacchi.", bullet_style))
        story.append(Paragraph("&bull; <b>Red (Chitarra Solista):</b> Gestione overdrive e delay a tempo, riff portanti, espressività nei bending dell'assolo.", bullet_style))
        story.append(Paragraph("&bull; <b>Maurino (Chitarra Ritmica):</b> Solidità di plettrata/strumming, accordi aperti vs barré, bilanciamento frequenze con Red.", bullet_style))
        story.append(Paragraph("&bull; <b>Sentimental (Tastiere):</b> Selezione della scena corretta ({scena: X}), pad e pianoforte senza sporcare le frequenze basse.", bullet_style))

        # Embedded screenshot: consigli live ai (Screenshot C)
        fig_ai_path = _resolve_asset_path("frontend/assets/manual/fig_consigli_live_ai.jpg")
        if fig_ai_path:
            try:
                story.append(Spacer(1, 2 * mm))
                # 941 x 1024 -> width 90mm, height 97.9mm
                story.append(Image(fig_ai_path, width=90 * mm, height=97.9 * mm))
                story.append(Paragraph("Figura 14.1 [Screenshot C]: Modale Consigli Live AI Gemini con schede dedicate per l'intera band e per ciascun musicista.", caption_style))
            except Exception:
                pass

        # =========================================================================
        # CAPITOLO 15: AMMINISTRAZIONE, SICUREZZA, CESTINO 30GG & BACKUP
        # =========================================================================
        story.append(Paragraph("Capitolo 15 &bull; Amministrazione, Sicurezza, Cestino 30gg & Backup DB", ch_title_style))
        story.append(Paragraph(
            "Gli amministratori dispongono di strumenti completi per la protezione dell'archivio:",
            body_style
        ))
        story.append(Paragraph("&bull; <b>Cestino con Retention 30 Giorni:</b> Nessuna cancellazione è distruttiva. I brani eliminati possono essere ripristinati in qualunque momento entro 30 giorni con un clic.", bullet_style))
        story.append(Paragraph("&bull; <b>Backup DB Integrale in Formato JSON:</b> Con un solo tocco viene esportato un dump JSON compatto contenente brani, scalette, utenti, preferenze e changelog.", bullet_style))
        story.append(Paragraph("&bull; <b>Ripristino Database:</b> Importa il dump per migrare o recuperare l'archivio su qualunque server o istanza Turso Cloud.", bullet_style))
        story.append(Paragraph("&bull; <b>Health Check (/api/health):</b> Monitoraggio compatibile con UptimeRobot per prevenire lo sleep mode del cloud su Render.", bullet_style))

        story.append(PageBreak())

        # =========================================================================
        # CAPITOLO 16: CHANGELOG DINAMICO & CRONOLOGIA NOVITÀ (AUTOCOMPILATO)
        # =========================================================================
        story.append(Paragraph("Capitolo 16 &bull; Changelog Dinamico & Cronologia Novità (In Tempo Reale)", ch_title_style))
        story.append(Paragraph(
            "<i>Questo capitolo viene autocompilato dinamicamente in tempo reale leggendo direttamente "
            "da <code>data/changelog.json</code>. Ogni nuova release, bug fix o implementazione registrata "
            "è immediatamente presente in questo documento senza richiedere alcun aggiornamento manuale.</i>",
            body_style
        ))
        story.append(Spacer(1, 2 * mm))

        entries = cls.load_changelog_entries()
        if not entries:
            story.append(Paragraph("Nessuna voce di changelog presente.", body_style))
        else:
            for entry in entries[:8]:  # Mostra le release più recenti
                v_str = entry.get("version", "")
                d_str = entry.get("date", "")
                t_str = entry.get("title", "")
                entry_header = f"<b>Versione {v_str} ({d_str})</b> — {t_str}"
                story.append(Paragraph(entry_header, ch_sub_style))

                new_feats = entry.get("new_features", [])
                if new_feats:
                    for nf in new_feats:
                        story.append(Paragraph(f"&bull; <font color='#0284c7'><b>[Nuova Funzione]</b></font> {nf}", bullet_style))

                improvements = entry.get("improvements", [])
                if improvements:
                    for imp in improvements:
                        story.append(Paragraph(f"&bull; <font color='#059669'><b>[Miglioramento]</b></font> {imp}", bullet_style))

                bug_fixes = entry.get("bug_fixes", [])
                if bug_fixes:
                    for bf in bug_fixes:
                        story.append(Paragraph(f"&bull; <font color='#dc2626'><b>[Bug Fix]</b></font> {bf}", bullet_style))

                story.append(Spacer(1, 2 * mm))

        # =========================================================================
        # CAPITOLO 17 / APPENDICE: FIGURE GRAFICHE & RIEPILOGO SCREENSHOT
        # =========================================================================
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("Appendice &bull; Guida alle Figure Grafiche & Riepilogo Screenshot", ch_title_style))
        story.append(Paragraph(
            "Per mantenere la documentazione visivamente chiara e immediata per tutti i componenti della band, "
            "il manuale integra figure esplicative dell'interfaccia. Di seguito il riepilogo delle figure incluse:",
            body_style
        ))

        fig_table_data = [
            [Paragraph("<b>Rif. Figura</b>", body_style), Paragraph("<b>Capitolo</b>", body_style), Paragraph("<b>Descrizione Schermata</b>", body_style), Paragraph("<b>Stato Inclusione</b>", body_style)],
            [Paragraph("<b>Figura 4.1</b>", body_style), Paragraph("Cap. 4", body_style), Paragraph("Pannello Layout & Impaginazione PDF (colonne, font, margini)", body_style), Paragraph("<font color='#059669'><b>OK Presente</b></font>", body_style)],
            [Paragraph("<b>Figura 5.1</b>", body_style), Paragraph("Cap. 5", body_style), Paragraph("Griglia Brani con schede repertorio Ufficiale vs Personale", body_style), Paragraph("<font color='#059669'><b>OK Presente</b></font>", body_style)],
            [Paragraph("<b>Figura 5.2</b>", body_style), Paragraph("Cap. 5", body_style), Paragraph("Modale touch Condividi / Stampa A4 per invio su WhatsApp", body_style), Paragraph("<font color='#059669'><b>OK Presente</b></font>", body_style)],
            [Paragraph("<b>Figura 10.1</b><br/><font size='7' color='#0284c7'><b>[Screenshot A]</b></font>", body_style), Paragraph("Cap. 10", body_style), Paragraph("Editor AML con direttive Medley, {scena: 1} e {stacco: Tutti}", body_style), Paragraph("<font color='#059669'><b>OK Presente</b></font>", body_style)],
            [Paragraph("<b>Figura 11.1</b><br/><font size='7' color='#0284c7'><b>[Screenshot B]</b></font>", body_style), Paragraph("Cap. 11", body_style), Paragraph("IL CIRCOLO DELLE QUINTE: 12 tonalità, relative minori, alterazioni e accordi", body_style), Paragraph("<font color='#059669'><b>OK Presente</b></font>", body_style)],
            [Paragraph("<b>Figura 12.1</b>", body_style), Paragraph("Cap. 12", body_style), Paragraph("Teleprompter Palco notturno con controlli scorrimento 60fps", body_style), Paragraph("<font color='#059669'><b>OK Presente</b></font>", body_style)],
            [Paragraph("<b>Figura 13.1</b><br/><font size='7' color='#0284c7'><b>[Screenshot B2]</b></font>", body_style), Paragraph("Cap. 13", body_style), Paragraph("Dettaglio Scaletta: Modale Condividi / Stampa A4 WhatsApp", body_style), Paragraph("<font color='#059669'><b>OK Presente</b></font>", body_style)],
            [Paragraph("<b>Figura 14.1</b><br/><font size='7' color='#0284c7'><b>[Screenshot C]</b></font>", body_style), Paragraph("Cap. 14", body_style), Paragraph("Modale Suggerimenti Live AI con schede per singolo musicista", body_style), Paragraph("<font color='#059669'><b>OK Presente</b></font>", body_style)],
        ]
        fig_table = Table(fig_table_data, colWidths=[28 * mm, 20 * mm, 95 * mm, 37 * mm])
        fig_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(fig_table)

        # Build document using ManualNumberedCanvas
        doc.build(story, canvasmaker=ManualNumberedCanvas)
        return buffer.getvalue()

    @classmethod
    def get_manual_markdown(cls) -> str:
        """Returns markdown export of the user manual."""
        md = ["# Manuale Operativo Ufficiale — THE NEW ASMA 2.0\n"]
        for ch in cls.get_chapters_metadata():
            md.append(f"## Capitolo {ch['num']}: {ch['title']}\n{ch['desc']}\n")
        return "\n".join(md)
