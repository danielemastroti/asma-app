"""
ASMA Accordi Next Generation - Automatic User Manual Engine
Generates dynamic documentation both as online Interactive Web view and as printable PDF.
Conforms to SRS Cap. 4.11 and 15.14.
"""

from __future__ import annotations
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from asma_core.pdf_engine import NumberedCanvas


MANUAL_SECTIONS = [
    {
        "title": "1. Introduzione & Visione del Prodotto",
        "content": """ASMA Accordi Next Generation è la piattaforma collaborativa musicale della band per gestire repertori, brani, accordi, scalette live, eventi e pubblicazione PDF.
Tutte le funzionalità operano secondo il principio vincolante: <b>La musica viene prima dell'AI</b>. Tutte le funzionalità essenziali sono deterministiche, veloci e affidabili anche sul palco in assenza di rete internet."""
    },
    {
        "title": "2. Formato Ufficiale AML (ASMA Markup Language)",
        "content": """AML è la <b>Single Source of Truth</b> del sistema. Sintassi principale:
<br/>&bull; <b>Direttive:</b> <code>{title: Titolo}</code>, <code>{artist: Artista}</code>, <code>{key: Tonalità}</code>, <code>{tempo: BPM}</code>, <code>{time: 4/4}</code>
<br/>&bull; <b>Sezioni:</b> <code>{intro}</code>, <code>{verse}</code>, <code>{chorus}</code>, <code>{bridge}</code>, <code>{solo}</code>, <code>{outro}</code>
<br/>&bull; <b>Accordi Inline:</b> <code>[Am]On a dark desert highway, [F#7]cool wind in my hair</code>
<br/>&bull; <b>Griglia Armonica a Battute:</b> <code>| DO | LAm | FA | SOL |</code>
<br/>&bull; <b>Tag Strumentali:</b> <code>{guitar: Solo Don Felder}</code>, <code>{voice: Armonizzazione a 3}</code>"""
    },
    {
        "title": "3. Motore Musicale & Trasposizioni",
        "content": """Il Music Engine supporta nativamente la notazione Italiana (DO, RE, MI, FA, SOL, LA, SI) e Internazionale (C, D, E, F, G, A, B).
Le trasposizioni coprono l'intero spettro cromatico da <b>-12 a +12 semitoni</b> con gestione automatica delle armature di chiave (# e b) sul circolo delle quinte o forzatura manuale della preferenza utente."""
    },
    {
        "title": "4. Gestione Repertori & Scalette Live",
        "content": """I repertori raggruppano logicamente i brani (es. Working In Progress, Definitivo, Acustico).
Le scalette definiscono la sequenza di esecuzione live. È possibile combinare brani singoli e <b>Medley continui</b>. Il sistema calcola automaticamente la compatibilità armonica (distanza sul circolo delle quinte) e ritmica (delta BPM) tra brani contigui."""
    },
    {
        "title": "5. Modalità Palco (Live Stage Mode)",
        "content": """Progettata per smartphone Android, tablet e iPad:
<br/>&bull; <b>Scorrimento Fluido a 60 fps:</b> Regolabile da 10 a 120 px/secondo.
<br/>&bull; <b>Pedaliere Bluetooth HID:</b> Supporto integrato per AirTurn, PageFlip e BlueTurn (tasti PageUp/Down, frecce, tasti 1 e 2).
<br/>&bull; <b>Keep Screen Awake:</b> Impedisce lo spegnimento o il blocco dello schermo del tablet durante il concerto.
<br/>&bull; <b>Metronomo Web Audio API:</b> Click acustico a latenza zero ($< 1$ ms) con flash visivo del quarto.
<br/>&bull; <b>Resilienza Offline:</b> Salvataggio automatico in cache locale per funzionare anche se cade il Wi-Fi del locale."""
    },
    {
        "title": "6. Importazione & Esportazione Interoperabile",
        "content": """Nessun lock-in dei dati:
<br/>&bull; <b>Import:</b> Da file PDF, ChordPro standard, formato tradizionale (accordi sopra il testo) e direttamente da URL web di spartiti.
<br/>&bull; <b>Export:</b> Verso MobileSheets (.pro), SongBookPro, OnSong, ChordPro e Offline Live Pack ZIP con tutti i PDF e sorgenti AML."""
    },
    {
        "title": "7. Amministrazione, Sicurezza & Cestino",
        "content": """Riservato al ruolo ADMIN:
<br/>&bull; <b>Lock Editing:</b> Prevenzione dei conflitti concorrenti quando un musicista modifica un brano.
<br/>&bull; <b>Cestino con Retention 30gg:</b> Nessuna cancellazione accidentale è definitiva.
<br/>&bull; <b>Audit Trail:</b> Tracciamento immutabile di ogni login, salvataggio e ripristino.
<br/>&bull; <b>Health Endpoint:</b> Monitoraggio `/health` compatibile con UptimeRobot per prevenire lo sleep mode del cloud."""
    }
]


class ManualEngine:
    """Auto-updating application manual engine."""

    @classmethod
    def get_manual_markdown(cls) -> str:
        """Returns full markdown text of the user manual."""
        md = ["# Manuale Operativo Ufficiale — ASMA Accordi 2.0\n"]
        for sec in MANUAL_SECTIONS:
            md.append(f"## {sec['title']}\n")
            # Clean HTML tags for markdown
            clean_c = sec["content"].replace("<br/>", "\n").replace("<b>", "**").replace("</b>", "**").replace("<code>", "`").replace("</code>", "`")
            md.append(f"{clean_c}\n")
        return "\n".join(md)

    @classmethod
    def generate_manual_pdf(cls) -> bytes:
        """Generates a professional printable PDF document of the complete User Manual."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ManTitle",
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0D47A1")
        )
        sec_title_style = ParagraphStyle(
            "ManSecTitle",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#212121"),
            spaceBefore=12,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "ManBody",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#263238")
        )

        story = []
        # Title
        story.append(Paragraph("<b>MANUALE UTENTE UFFICIALE</b>", title_style))
        story.append(Paragraph("ASMA Accordi Next Generation &bull; Edizione 2026.11.05", styles["Italic"]))
        story.append(Spacer(1, 6 * mm))

        # Sections
        for sec in MANUAL_SECTIONS:
            story.append(Paragraph(sec["title"], sec_title_style))
            story.append(Paragraph(sec["content"], body_style))
            story.append(Spacer(1, 3 * mm))

        def canvas_maker(*args, **kwargs):
            c = NumberedCanvas(*args, **kwargs)
            c.document_title = "Manuale Utente ASMA 2.0"
            c.version_str = "| Edizione Ufficiale"
            return c

        doc.build(story, canvasmaker=canvas_maker)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
