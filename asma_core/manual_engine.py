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
        "title": "4. Gestione Repertori, Brani & Scalette Live",
        "content": """I repertori raggruppano logicamente i brani (es. Working In Progress, Definitivo, Acustico).
<br/>&bull; <b>Editor Brani & Sorgente AML Compatta:</b> I metadati del brano sono organizzati in una barra compatta a 6 colonne (Titolo, Tonalità, Artista, BPM, Genere e Capotasto) che azzera lo spreco di spazio verticale e lascia massima visibilità al testo e agli accordi.
<br/>&bull; <b>Composizione Scalette & Feedback Visivo:</b> Quando aggiungi un brano con il pulsante 'Inserisci', l'interfaccia mostra immediatamente una notifica visiva verde (toast) di conferma e aggiorna all'istante il contatore dei brani in scaletta.
<br/>&bull; <b>Compatibilità Armonica & Ritmica:</b> Per ogni coppia di brani consecutivi viene calcolata la transizione armonica (distanza sul circolo delle quinte) e la variazione di BPM. Tutte le scalette sono sincronizzate in modo permanente sul database cloud Turso."""
    },
    {
        "title": "5. Modalità Palco (Live Stage Mode)",
        "content": """Progettata per l'esecuzione live su smartphone Android, tablet (es. Huawei MatePad) e iPad:
<br/>&bull; <b>Avvio On-Demand dell'Autoscroll:</b> All'apertura di un brano o scaletta, lo scorrimento automatico NON parte mai da solo. Il musicista ha tutto il tempo di posizionarsi e avviare lo scorrimento toccando il grande pulsante 'AVVIO' o premendo il pedale Bluetooth.
<br/>&bull; <b>Scorrimento Fluido a 60 fps & Tap-to-Pause:</b> Regolabile da 10 a 120 px/secondo. Toccando lo spartito in qualsiasi punto lo scorrimento si mette istantaneamente in pausa per consentire modifiche o annotazioni al volo.
<br/>&bull; <b>Pedaliere Bluetooth HID:</b> Supporto nativo per AirTurn, PageFlip e BlueTurn (PageUp/Down, frecce su/giù, tasti 1 e 2).
<br/>&bull; <b>Interfaccia Clean Palco:</b> Tutti i loghi fluttuanti esterni e barre di servizio (Streamlit/GitHub) vengono soppressi per garantire una schermata pulita a pieno schermo.
<br/>&bull; <b>Keep Screen Awake:</b> Impedisce lo spegnimento o il blocco dello schermo del dispositivo durante l'esibizione.
<br/>&bull; <b>Metronomo Web Audio API:</b> Click audio ad alta precisione e latenza zero (< 1 ms) con lampeggio visivo del quarto."""
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
<br/>&bull; <b>Cestino con Retention 30gg:</b> Nessuna cancellazione accidentale è definitiva. Brani, scalette e repertori eliminati restano protetti nel Cestino.
<br/>&bull; <b>Audit Trail:</b> Tracciamento immutabile di ogni login, salvataggio e ripristino.
<br/>&bull; <b>Health Endpoint:</b> Monitoraggio `/health` compatibile con UptimeRobot per prevenire lo sleep mode del cloud."""
    },
    {
        "title": "8. Profilo Utente, Dispositivi & Cloud Database (Turso)",
        "content": """Personalizzazione indipendente per ogni musicista e hardware:
<br/>&bull; <b>Default Spartito (Solo Testo vs Testo+Accordi):</b> Ogni musicista (ad es. cantanti, coristi o musicisti) può selezionare nel proprio profilo popover la modalità predefinita di spartito ('Solo Testo' o 'Testo + Accordi'). La scelta viene salvata a database su Turso Cloud e imposta automaticamente il formato iniziale dell'anteprima PDF.
<br/>&bull; <b>Stampa e Download Sempre Completi:</b> A prescindere dalla preferenza di default, tutti i componenti della band mantengono sempre la possibilità di stampare su carta A4 o scaricare il PDF sia con accordi che in versione solo testo.
<br/>&bull; <b>Persistenza Utente/Dispositivo:</b> Le preferenze grafiche sono salvate nel database cloud Turso e associate alla coppia <code>(email_musicista, tipo_dispositivo)</code>.
<br/>&bull; <b>Parametri Personalizzabili:</b> Dimensione testo (8-30px), dimensione accordi (8-32px), colonne PDF (1 o 2 colonne), margini laterali (4-30mm), palette colori (testo, accordi, markup AML) e zoom dell'interfaccia (75%-110%).
<br/>&bull; <b>Resistenza a Riavvii e Deploy:</b> Al riavvio dell'applicazione o al login successivo da qualsiasi tablet, smartphone o PC, le impostazioni personalizzate vengono ripristinate automaticamente all'istante."""
    },
    {
        "title": "9. Modalità di Accesso: Editing vs Semplificata",
        "content": """L'applicazione mette a disposizione due modalità operative selezionabili alla pagina del login:
<br/>&bull; <b>Modalità Semplificata (Live & Concerto):</b> Dedicata al musicista prima e durante i live. Offre un menu essenziale su singola riga (Home, Brani, Scalette, Palco, Guida, Logout). Nella sezione Brani sono rimosse tutte le funzionalità di editing (nessun campo testo, dropdown o tasto di modifica): il musicista trova subito i brani per visualizzare l'anteprima PDF formattata per il proprio leggio, salvare il file PDF o inviarlo direttamente alla stampante A4, consultare la scaletta e avviare la Modalità Palco.
<br/>&bull; <b>Modalità Editing (Completa):</b> Offre l'accesso integrale a tutto il sito, compresi l'editor sorgente AML, la gestione avanzata dei repertori, import/export da file e web, amministrazione e Band AI.
<br/>&bull; <b>Permessi Inalterati:</b> I ruoli di sicurezza (ADMIN, BAND_MEMBER, VIEWER) restano rigorosamente invariati in entrambe le modalità.
<br/>&bull; <b>Passaggio Rapido:</b> È possibile commutare tra le due modalità in qualsiasi momento dal popover del Profilo Musicista ('👤')."""
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
