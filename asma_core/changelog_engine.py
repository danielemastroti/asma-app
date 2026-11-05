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
