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
            logo_path = "frontend/assets/band_logo.png"
            if os.path.exists(logo_path):
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
            {"num": 8, "title": "Flusso di Lavoro Modifica Brani (Ufficiale vs Personale)", "desc": "Protezione del repertorio ufficiale, copia nel personale, modifiche e promozione con sovrascrittura."},
            {"num": 9, "title": "AML (ASMA Markup Language) — Sintassi & Specifiche", "desc": "Direttive, sezioni, accordi inline tra parentesi quadre e griglie armoniche a battute."},
            {"num": 10, "title": "Modalità Editing, Nuove Direttive Scena/Stacco & Medley", "desc": "Direttiva {Scena: X} per tastiere, {stacco: strumento}, e Medley continui fino a 20 brani con colori alternati."},
            {"num": 11, "title": "Modalità Palco (Stage Mode) & Teleprompter 60fps", "desc": "Autoscroll fluido a 60fps, avvio on-demand, tap-to-pause, contrasto notturno OLED, pedaliere HID e metronomo."},
            {"num": 12, "title": "Gestione Scalette Live & Compatibilità Armonica", "desc": "Composizione scalette, Circolo delle Quinte, variazioni BPM, durata totale e condivisione A4 WhatsApp."},
            {"num": 13, "title": "Suggerimenti Esecuzione Live (AI Gemini Free)", "desc": "Consigli su misura per Cico, Mingo, Puma, Red, Maurino, Sentimental e per l'intera band, con fallback offline."},
            {"num": 14, "title": "Amministrazione, Sicurezza, Cestino 30gg & Backup DB", "desc": "Cestino con ripristino entro 30 giorni, backup integrale JSON, restore con un clic e audit trail."},
            {"num": 15, "title": "Changelog Dinamico & Cronologia Novità (In Tempo Reale)", "desc": "Cronologia delle release e nuove funzionalità compilata automaticamente da data/changelog.json."},
            {"num": 16, "title": "Appendice: Figure Grafiche & Richiesta Screenshot", "desc": "Riepilogo figure incluse e lista degli screenshot d'interfaccia consigliati per le future edizioni."}
        ]

    @classmethod
    def load_changelog_entries(cls) -> List[Dict[str, Any]]:
        """Reads latest changelog directly from data/changelog.json for 100% dynamic documentation."""
        changelog_path = os.path.join(os.getcwd(), "data", "changelog.json")
        if os.path.exists(changelog_path):
            try:
                with open(changelog_path, "r", encoding="utf-8") as f:
                    return json.load(f)
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
        logo_path = "frontend/assets/band_logo.png"
        if os.path.exists(logo_path):
            try:
                # 1024 x 367 ratio -> width 84mm, height 30.1mm
                story.append(Image(logo_path, width=84 * mm, height=30.1 * mm, preserveAspectRatio=True))
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
            "Il passaggio tra le due modalità è immediato: basta toccare il badge in testata (<i>'🎤 Casa / Palco'</i>) o aprire "
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
            "<b>I 5 Parametri di Impaginazione Regolabili:</b>", ch_sub_style
        ))
        story.append(Paragraph("&bull; <b>Numero Colonne:</b> 1 colonna (lettura continua) oppure 2 colonne (ottimizzazione dello spazio verticale per evitare cambi pagina).", bullet_style))
        story.append(Paragraph("&bull; <b>Font Testo (pt):</b> Dimensione regolabile da 8 a 30 pt.", bullet_style))
        story.append(Paragraph("&bull; <b>Font Accordi (pt):</b> Dimensione indipendente regolabile da 8 a 32 pt.", bullet_style))
        story.append(Paragraph("&bull; <b>Margini Laterali (mm):</b> Spaziatura laterale da 4 a 30 mm.", bullet_style))
        story.append(Paragraph("&bull; <b>Margine Superiore (mm):</b> Spazio superiore da 0 a 40 mm per posizionare il brano sotto cornici o fotocamere frontali.", bullet_style))

        # Embedded screenshot: layout
        fig_layout_path = "frontend/assets/manual/fig_layout_impaginazione.png"
        if os.path.exists(fig_layout_path):
            try:
                story.append(Spacer(1, 2 * mm))
                # 490 x 442 -> scaled width 80mm, height 72.1mm
                story.append(Image(fig_layout_path, width=80 * mm, height=72.1 * mm, preserveAspectRatio=True))
                story.append(Paragraph("Figura 4.1: Pannello touch di configurazione Layout & Impaginazione PDF con sincronizzazione cloud immediata.", caption_style))
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
        story.append(Paragraph("<b>Funzionalità della Scheda Brano:</b>", ch_sub_style))
        story.append(Paragraph("&bull; <b>Anteprima PDF Reale:</b> Visualizza le pagine del brano renderizzate ad alta risoluzione (96 DPI) esattamente come verranno visualizzate sul tablet o stampate su carta.", bullet_style))
        story.append(Paragraph("&bull; <b>Stampa A4 Diretta:</b> Invia lo spartito alla stampante del sistema operativo con margini ottimali A4.", bullet_style))
        story.append(Paragraph("&bull; <b>Scarica PDF:</b> Genera e scarica il file PDF ottimizzato con il profilo del dispositivo attivo (proporzioni esatte dello schermo).", bullet_style))

        # Embedded screenshot: lista brani
        fig_brani_path = "frontend/assets/manual/fig_repertorio_brani.png"
        if os.path.exists(fig_brani_path):
            try:
                story.append(Spacer(1, 2 * mm))
                # 1024 x 491 -> scaled width 150mm, height 71.9mm
                story.append(Image(fig_brani_path, width=150 * mm, height=71.9 * mm, preserveAspectRatio=True))
                story.append(Paragraph("Figura 5.1: Schermata Principale con schede di filtro (Tutti, Repertorio Ufficiale, Personale) e griglia brani.", caption_style))
            except Exception:
                pass

        # =========================================================================
        # CAPITOLO 6: IMPORTAZIONE BRANI DA FONTI ESTERNE & SCANSIONE FOTOCAMERA
        # =========================================================================
        story.append(Paragraph("Capitolo 6 &bull; Importazione Brani da Fonti Esterne & Scansione Fotocamera", ch_title_style))
        story.append(Paragraph(
            "Il pulsante <b>'➕ Nuovo / Importa'</b> nella schermata Brani apre una finestra interattiva a 5 schede "
            "per acquisire rapidamente spartiti da qualunque supporto:",
            body_style
        ))
        story.append(Paragraph("&bull; <b>🌐 Cerca sul Web:</b> Inserisci titolo e artista: il crawler musicale cerca su portali pubblici di accordi e converte il brano in formato AML strutturato.", bullet_style))
        story.append(Paragraph("&bull; <b>📷 Fotocamera / Scansione OCR (Gemini Vision AI):</b> Scansione ottica diretta di spartiti cartacei, canzonieri o fogli scritti a mano tramite la fotocamera del dispositivo o caricamento immagini.", bullet_style))
        story.append(Paragraph("&bull; <b>📋 Incolla Testo:</b> Incolla testo con accordi posti sopra le parole (formato testo tradizionale); il parser fonde testo e accordi in sintassi inline AML <code>[DO]Parola</code> senza errori di allineamento.", bullet_style))
        story.append(Paragraph("&bull; <b>🔗 Da Link Web:</b> Estrazione diretta di testo e accordi da una pagina web specifica incollandone la URL.", bullet_style))
        story.append(Paragraph("&bull; <b>✍️ Scrivi AML:</b> Composizione libera direttamente nel formato sorgente della band con assistenza sintattica.", bullet_style))

        story.append(Paragraph("<b>Approfondimento: Scansione da Fotocamera / Foto Spartito Cartaceo (OCR AI)</b>", ch_sub_style))
        story.append(Paragraph(
            "La scheda <b>'📷 Fotocamera / Foto'</b> è una delle funzionalità più potenti di ASMA: consente di digitalizzare in pochi "
            "secondi interi spartiti cartacei, spartiti di prova o canzonieri storici senza dover ricopiare testo o accordi a mano.",
            body_style
        ))
        story.append(Paragraph("<b>Procedura Passo-Passo per la Scansione:</b>", ch_sub_style))
        story.append(Paragraph(
            "1. <b>Accesso alla Scheda:</b> Tocca <i>'➕ Nuovo / Importa'</i> e seleziona il tab <i>'📷 Fotocamera / Foto'</i>.<br/>"
            "2. <b>Scatto della Foto o Selezione File:</b> Su smartphone o tablet (Android/iOS) tocca <i>'📷 Scatta Foto o Scegli da Galleria'</i>: "
            "il sistema apre direttamente la fotocamera posteriore del dispositivo per inquadrare lo spartito con buona luce.<br/>"
            "3. <b>Supporto Multi-Pagina:</b> Se il brano si sviluppa su più fogli, puoi scattare o caricare più foto in sequenza. "
            "L'interfaccia mostra le miniature delle pagine caricate (Pagina 1, Pagina 2, ecc.) con possibilità di visualizzarle, riordinarle o rimuovere scatti sfocati.<br/>"
            "4. <b>Riconoscimento Ottico Intelligente (Gemini Vision OCR):</b> Toccando <i>'✨ Elabora con Vision AI'</i>, "
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
        # CAPITOLO 8: FLUSSO DI LAVORO PER MODIFICA BRANI ESISTENTI
        # =========================================================================
        story.append(Paragraph("Capitolo 8 &bull; Flusso di Lavoro Modifica Brani (Ufficiale vs Personale)", ch_title_style))
        story.append(Paragraph(
            "Per tutelare l'integrità del repertorio condiviso, <b>nessun utente (incluso l'amministratore) può modificare "
            "direttamente i brani del Repertorio Ufficiale</b>. Si applica la procedura protetta in 3 fasi:",
            body_style
        ))
        story.append(Paragraph("1. <b>Copia nel Personale:</b> Il musicista tocca <i>'📋 Copia nel Personale per Modificare'</i>. Il sistema crea un fork privato.", bullet_style))
        story.append(Paragraph("2. <b>Modifica Autonoma:</b> L'utente modifica testo, tonalità, direttive synth o stacchi nel proprio editor senza intaccare la versione comune.", bullet_style))
        story.append(Paragraph("3. <b>Promozione a Ufficiale:</b> Concordato l'arrangiamento, il tasto <i>'⭐ Promuovi a Ufficiale'</i> sovrascrive la versione comune ed elimina automaticamente la copia personale ridondante.", bullet_style))

        story.append(PageBreak())

        # =========================================================================
        # CAPITOLO 9: AML (ASMA MARKUP LANGUAGE) — SINTASSI & SPECIFICHE
        # =========================================================================
        story.append(Paragraph("Capitolo 9 &bull; AML (ASMA Markup Language) — Sintassi & Specifiche", ch_title_style))
        story.append(Paragraph(
            "AML è il linguaggio nativo del sistema. Sintassi riassuntiva dei costrutti standard:",
            body_style
        ))

        aml_syntax_data = [
            [Paragraph("<b>Costrutto AML</b>", body_style), Paragraph("<b>Esempio Pratico</b>", body_style), Paragraph("<b>Effetto su Spartito & Palco</b>", body_style)],
            [Paragraph("<b>Direttive Metadati</b>", body_style), Paragraph("<code>{title: Albachiara}<br/>{key: DO}<br/>{tempo: 68}</code>", code_box_style), Paragraph("Imposta titolo, tonalità e tempo BPM per il metronomo.", body_style)],
            [Paragraph("<b>Sezioni Brano</b>", body_style), Paragraph("<code>{intro}<br/>{verse}<br/>{chorus}<br/>{bridge}<br/>{outro}</code>", code_box_style), Paragraph("Crea intestazioni visive con stacco grafico pulito e spaziatura.", body_style)],
            [Paragraph("<b>Accordi Inline</b>", body_style), Paragraph("<code>[DO]Respiri piano per [SOL]non far rumore</code>", code_box_style), Paragraph("Accordo ancorato alla sillaba esatta, trasponibile automaticamente.", body_style)],
            [Paragraph("<b>Griglia a Battute</b>", body_style), Paragraph("<code>| DO | SOL | LAm | FA |</code>", code_box_style), Paragraph("Griglia armonica tabellare per introduzioni e parti strumentali.", body_style)],
            [Paragraph("<b>Interruzione Colonna</b>", body_style), Paragraph("<code>{colb}</code>", code_box_style), Paragraph("Forza il testo a passare alla seconda colonna nel layout a 2 colonne.", body_style)]
        ]
        aml_table = Table(aml_syntax_data, colWidths=[40 * mm, 65 * mm, 75 * mm])
        aml_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(aml_table)
        story.append(Spacer(1, 4 * mm))

        # =========================================================================
        # CAPITOLO 10: MODALITÀ EDITING, DIRETTIVE SCENA/STACCO & MEDLEY
        # =========================================================================
        story.append(Paragraph("Capitolo 10 &bull; Nuove Direttive Scena/Stacco & Modalità Medley", ch_title_style))
        story.append(Paragraph(
            "L'editor mette a disposizione nuove direttive avanzate per la massima efficacia live:",
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
            "&bull; <b>Composizione MEDLEY Multi-Brano:</b> Supporto completo a brani composti da spezzoni concatenati (fino a 20 brani) "
            "tramite le direttive <code>{start_of_song: Titolo | Artista | Tonalità}</code> ed <code>{end_of_song}</code>. "
            "Ciascuno spezzone ha la propria tonalità e sezioni, con colorazione alternata tra 20 tonalità cromatiche vive "
            "per distinguere i passaggi al volo durante il live.",
            bullet_style
        ))

        # =========================================================================
        # CAPITOLO 11: MODALITÀ PALCO (STAGE MODE) & TELEPROMPTER
        # =========================================================================
        story.append(Paragraph("Capitolo 11 &bull; Modalità Palco (Stage Mode) & Teleprompter 60fps", ch_title_style))
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
        fig_palco_path = "frontend/assets/manual/fig_modalita_palco.png"
        if os.path.exists(fig_palco_path):
            try:
                story.append(Spacer(1, 2 * mm))
                # 459 x 1024 -> scaled width 52mm, height 116mm
                story.append(Image(fig_palco_path, width=52 * mm, height=116 * mm, preserveAspectRatio=True))
                story.append(Paragraph("Figura 11.1: Visualizzazione Teleprompter su dispositivo mobile con controlli di velocità e trasposizione.", caption_style))
            except Exception:
                pass

        story.append(PageBreak())

        # =========================================================================
        # CAPITOLO 12: GESTIONE SCALETTE LIVE & CIRCOLO DELLE QUINTE
        # =========================================================================
        story.append(Paragraph("Capitolo 12 &bull; Gestione Scalette Live & Compatibilità Armonica", ch_title_style))
        story.append(Paragraph(
            "La gestione scalette consente di pianificare concerti con titolo, data, location e ordinamento dei pezzi. "
            "Aggiungendo brani con il pulsante <i>'Inserisci'</i> viene mostrata una notifica toast visiva immediata e "
            "aggiornato il contatore in tempo reale.",
            body_style
        ))
        story.append(Paragraph("<b>Funzionalità Avanzate Scalette:</b>", ch_sub_style))
        story.append(Paragraph("&bull; <b>Compatibilità Armonica sul Circolo delle Quinte:</b> Tra ciascuna coppia di brani consecutivi viene calcolata la distanza tonale e la variazione di BPM per garantire transizioni fluide.", bullet_style))
        story.append(Paragraph("&bull; <b>Condivisione A4 su WhatsApp:</b> Invio del PDF completo A4 stampabile direttamente sul gruppo WhatsApp della band con un solo tocco.", bullet_style))
        story.append(Paragraph("&bull; <b>Calcolo Durata Live:</b> Somma automatica dei minuti e secondi per rispettare i tempi del locale.", bullet_style))

        # =========================================================================
        # CAPITOLO 13: SUGGERIMENTI ESECUZIONE LIVE (AI GEMINI FREE)
        # =========================================================================
        story.append(Paragraph("Capitolo 13 &bull; Suggerimenti Esecuzione Live (AI Gemini Free)", ch_title_style))
        story.append(Paragraph(
            "Accessibile da qualunque brano tramite il pulsante <b>'💡 Consigli Live'</b>, questa funzionalità "
            "fornisce raccomandazioni pratiche ed esecutive per il palco utilizzando l'intelligenza artificiale gratuita "
            "e ultra-leggera Google Gemini (con fallback deterministico offline istantaneo in caso di assenza di connessione).",
            body_style
        ))
        story.append(Paragraph("<b>Consigli Selezionabili per Singolo Musicista o Tutta la Band:</b>", ch_sub_style))
        story.append(Paragraph("&bull; <b>👥 Tutta la Band:</b> Dinamiche d'insieme, attacchi d'impatto, gestione dei crescendo tra strofa e ritornello, chiusure nette.", bullet_style))
        story.append(Paragraph("&bull; <b>🎤 Cico (Voce):</b> Intonazione della prima nota, gestione del fiato a BPM elevati, momenti di coinvolgimento del pubblico.", bullet_style))
        story.append(Paragraph("&bull; <b>🥁 Mingo (Batteria):</b> Groove ritmico, timing dei fill prima dei ritornelli, cassa granitica sulle fondamentali del basso.", bullet_style))
        story.append(Paragraph("&bull; <b>🎸 Puma (Basso):</b> Incastro cassa-basso con Mingo, linee melodiche nei ponti, stop ritmici negli stacchi.", bullet_style))
        story.append(Paragraph("&bull; <b>⚡ Red (Chitarra Solista):</b> Gestione overdrive e delay a tempo, riff portanti, espressività nei bending dell'assolo.", bullet_style))
        story.append(Paragraph("&bull; <b>🎸 Maurino (Chitarra Ritmica):</b> Solidità di plettrata/strumming, accordi aperti vs barré, bilanciamento frequenze con Red.", bullet_style))
        story.append(Paragraph("&bull; <b>🎹 Sentimental (Tastiere):</b> Selezione della scena corretta ({scena: X}), pad e pianoforte senza sporcare le frequenze basse.", bullet_style))

        # =========================================================================
        # CAPITOLO 14: AMMINISTRAZIONE, SICUREZZA, CESTINO 30GG & BACKUP
        # =========================================================================
        story.append(Paragraph("Capitolo 14 &bull; Amministrazione, Sicurezza, Cestino 30gg & Backup DB", ch_title_style))
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
        # CAPITOLO 15: CHANGELOG DINAMICO & CRONOLOGIA NOVITÀ (AUTOCOMPILATO)
        # =========================================================================
        story.append(Paragraph("Capitolo 15 &bull; Changelog Dinamico & Cronologia Novità (In Tempo Reale)", ch_title_style))
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
        # CAPITOLO 16 / APPENDICE: FIGURE GRAFICHE & RICHIESTA SCREENSHOT
        # =========================================================================
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("Appendice &bull; Guida alle Figure Grafiche & Screenshot Consigliati", ch_title_style))
        story.append(Paragraph(
            "Per mantenere la documentazione visivamente chiara e immediata per tutti i componenti della band, "
            "il manuale integra figure esplicative dell'interfaccia. Di seguito il riepilogo delle figure incluse e "
            "l'elenco degli screenshot consigliati da catturare dall'applicazione:",
            body_style
        ))

        fig_table_data = [
            [Paragraph("<b>Rif. Figura</b>", body_style), Paragraph("<b>Capitolo</b>", body_style), Paragraph("<b>Descrizione Schermata</b>", body_style), Paragraph("<b>Stato Inclusione</b>", body_style)],
            [Paragraph("<b>Figura 4.1</b>", body_style), Paragraph("Cap. 4", body_style), Paragraph("Pannello Layout & Impaginazione PDF (colonne, font, margini)", body_style), Paragraph("<font color='#059669'><b>✓ Presente</b></font>", body_style)],
            [Paragraph("<b>Figura 5.1</b>", body_style), Paragraph("Cap. 5", body_style), Paragraph("Griglia Brani con schede repertorio Ufficiale vs Personale", body_style), Paragraph("<font color='#059669'><b>✓ Presente</b></font>", body_style)],
            [Paragraph("<b>Figura 11.1</b>", body_style), Paragraph("Cap. 11", body_style), Paragraph("Teleprompter Palco notturno con controlli scorrimento", body_style), Paragraph("<font color='#059669'><b>✓ Presente</b></font>", body_style)],
            [Paragraph("<b>Screenshot A</b>", body_style), Paragraph("Cap. 10", body_style), Paragraph("Editor AML con direttive Medley, {scena: 3} e {stacco: }", body_style), Paragraph("<font color='#d97706'><b>Suggerito</b></font>", body_style)],
            [Paragraph("<b>Screenshot B</b>", body_style), Paragraph("Cap. 12", body_style), Paragraph("Dettaglio Scaletta con Circolo Quinte e tasto WhatsApp", body_style), Paragraph("<font color='#d97706'><b>Suggerito</b></font>", body_style)],
            [Paragraph("<b>Screenshot C</b>", body_style), Paragraph("Cap. 13", body_style), Paragraph("Modale Suggerimenti Live AI con schede per musicista", body_style), Paragraph("<font color='#d97706'><b>Suggerito</b></font>", body_style)],
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
