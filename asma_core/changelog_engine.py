"""
ASMA Accordi Next Generation - Automated Changelog Engine
Conforms to SRS Cap. 4.10, 15.13.
Rule: Single version per day in format AAAA.MM.GG.
"""

from __future__ import annotations
import os
from datetime import datetime

CHANGELOG_ENTRIES = [
    {
        "version": "2026.11.08",
        "date": "08/11/2026",
        "title": "Sincronizzazione Cloud Persistente, Spaziatura Accordi, Controlli Palco e Unicità Repertori",
        "new_features": [
            "Sincronizzazione Cloud Persistente bidirezionale (GitHub Gist) per scalette, brani e repertori: garanzia assoluta contro la perdita di dati dopo riavvii o nuovi deploy su Streamlit Cloud.",
            "Idratazione automatica all'avvio: il server recupera istantaneamente le 12 scalette della band e tutti i 41 brani ufficiali con schema dual-compatible.",
            "Controlli completi Modalità Palco (Live Stage): aggiunti pulsanti touch e scorciatoie pedali Bluetooth per cambio pagina (Pag Giù / Pag Su), navigazione brani (Prec / Succ), play/pausa e regolatore velocità autoscroll a 60fps.",
            "Toolbar persistente sezione Brani: header con titolo attivo e pulsanti compatti ('Nuovo brano', 'Salva nuova revisione', 'Rilascia lock', 'Elimina brano').",
            "Consulente arrangiamento AI multi-strumento con suggerimenti specifici per Tastiera, Voce, Chitarra ritmica, Chitarra elettrica, Basso, Batteria e Globale.",
            "Suggerimenti preset, scene memory e super knob Yamaha Montage dedicati ai tastieristi."
        ],
        "improvements": [
            "Layout scalette ottimizzato: pulsanti sposta brano ('⬆️', '⬇️') ed elimina ('❌') disposti su un'unica riga orizzontale compatta su tutti i dispositivi mobili.",
            "Unicità rigorosa dei repertori: divieto assoluto di creare o rinominare repertori con nomi duplicati (case-insensitive), con notifica immediata d'errore.",
            "Cancellazione repertori fittizi o vuoti duplicati dal database.",
            "Selettore profili utente e simulazione ruoli riservato esclusivamente agli utenti Admin.",
            "Rimozione voce ridondante 'Logout' dai sottomenu orizzontali."
        ],
        "security": [
            "Verifica autenticazione Google OAuth reale: reindirizzamento effettivo ad accounts.google.com ed eliminazione del bypass fittizio su ambienti cloud per proteggere l'area riservata della band."
        ],
        "bug_fixes": [
            "Motore PDF: risolto incollamento accordi consecutivi (anti-gluing es. 'FADO' -> 'FA  DO', 'SIb/FADO/MI' -> 'SIb/FA  DO/MI  RE7/9+') con spaziatura minima garantita.",
            "Motore PDF: rimossa sillabazione accidentale a metà parola nei testi dei brani.",
            "Motore PDF: garantito margine inferiore di sicurezza anti-sovrapposizione (minimo 15 mm) rispetto al piè di pagina.",
            "Eliminazione permanente di brani dummy non caricati dall'utente (es. 'Sultans of Swing', 'Hotel California', 'Canzone per un'amica') dal repository e dai seeder di test.",
            "Live Stage: risolto blocco dell'autoscroll automatico causato da misurazione prematura dell'altezza del DOM.",
            "Schermata di Login: ripristinato form di accesso primario per email autorizzata band-only per garantire ingresso immediato anche in navigazione in incognito in caso di mancata registrazione degli URI di reindirizzamento nella Google Cloud Console."
        ]
    },
    {
        "version": "2026.11.05",
        "date": "05/11/2026",
        "title": "Rilascio Ufficiale ASMA Accordi 2.0 (Next Generation)",
        "new_features": [
            "Architettura a due livelli: SQLite in-memory (< 2ms) e storage partizionato JSON.",
            "Formato ufficiale AML (ASMA Markup Language) come Single Source of Truth.",
            "Motore musicale deterministico (Zero-AI) con trasposizioni cromatiche -12/+12 semitoni e circolo delle quinte.",
            "Supporto nativo bilingue: notazione Italiana (DO, RE, MI...) e Internazionale (C, D, E...).",
            "Generatore PDF ReportLab Device-Aware con algoritmo Smart Page Break anti-orfanità per smartphone, tablet, iPad e A4.",
            "Modalità Palco (Live Stage) con scorrimento fluido a 60 fps, metronomo Web Audio API, Keep Screen Awake e pedaliere Bluetooth HID.",
            "Esportatore ed importatore per MobileSheets, SongBookPro, OnSong, ChordPro e Offline Live Pack ZIP.",
            "Web Importer per estrazione automatica di spartiti da portali italiani e internazionali."
        ],
        "improvements": [
            "Sistema di lock editing concorrente con heartbeat di sessione a 60 minuti e sblocco forzato Admin.",
            "Cestino con conservazione per 30 giorni e ripristino istantaneo di brani, repertori e scalette.",
            "Endpoint di salute /health per prevenire lo sleep mode del cloud tramite UptimeRobot.",
            "Manuale utente auto-aggiornante online e PDF stampabile."
        ],
        "security": [
            "Registro Audit Trail immutabile append-only per il tracciamento di tutte le modifiche critiche.",
            "Protezione contro l'inattività di sessione e isolamento dei dati sensibili."
        ],
        "bug_fixes": [
            "Risolto disallineamento sillabico durante l'importazione da spartiti tradizionali con accordi sopra il testo.",
            "Risolta ambiguità interpretativa per accordi italiani complessi (DO7+, LA-, DO+)."
        ]
    }
]


class ChangelogEngine:
    """Manages application version history and automated changelog generation."""

    @classmethod
    def get_latest_version(cls) -> str:
        return CHANGELOG_ENTRIES[0]["version"]

    @classmethod
    def get_changelog_markdown(cls) -> str:
        md = ["# Registro delle Modifiche (Changelog Ufficiale)\n"]
        for entry in CHANGELOG_ENTRIES:
            md.append(f"## Versione {entry['version']} ({entry['date']}) — {entry['title']}\n")
            if entry.get("new_features"):
                md.append("### 🚀 Nuove Funzionalità (New Features)")
                for item in entry["new_features"]:
                    md.append(f"- {item}")
                md.append("")
            if entry.get("improvements"):
                md.append("### ⚡ Miglioramenti (Improvements)")
                for item in entry["improvements"]:
                    md.append(f"- {item}")
                md.append("")
            if entry.get("security"):
                md.append("### 🛡️ Sicurezza (Security)")
                for item in entry["security"]:
                    md.append(f"- {item}")
                md.append("")
            if entry.get("bug_fixes"):
                md.append("### 🐛 Correzioni di Bug (Bug Fixes)")
                for item in entry["bug_fixes"]:
                    md.append(f"- {item}")
                md.append("")
        return "\n".join(md)

    @classmethod
    def export_to_file(cls, filepath: str = "CHANGELOG.md") -> None:
        content = cls.get_changelog_markdown()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
