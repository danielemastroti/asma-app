# ASMA Accordi Next Generation (v2.0)
> **Piattaforma Web Professionale per la Gestione Collaborativa delle Attività Musicali della Band**

Conforme alle specifiche **SRS v1.0 (Capitoli 1 - 22)**.

---

## 🎵 Principi Guida

1. **La Musica Prima dell'AI**: Il 100% delle funzioni critiche (accordi, trasposizioni, PDF, ricerca, scalette, live) è implementato con algoritmi matematici deterministici in Python puro senza dipendenza da servizi AI esterni.
2. **AML come Single Source of Truth**: L'intero archivio musicale è memorizzato nel formato standard **ASMA Markup Language (AML)**, compatibile con ChordPro ed esteso per griglie ritmiche e tag strumentali.
3. **Live First & Mobile First**: La Modalità Palco è progettata per operare a 60 fps con pedaliere Bluetooth, blocco dello standby dello schermo e resilienza offline garantita.
4. **Costi Operativi Prossimi a Zero**: Funziona su Streamlit Community Cloud e GitHub Gist senza database a pagamento.

---

## 🚀 Avvio Rapido

### 1. Requisiti di Sistema
- Python 3.10+
- Streamlit, ReportLab, PyMuPDF

### 2. Installazione Dipendenze
```powershell
pip install -r requirements.txt
```

### 3. Avvio dell'Applicazione
```powershell
streamlit run app.py
```

### 4. Esecuzione Test Automatici
```powershell
python -m unittest discover tests
```

---

## 🏗️ Architettura dei Moduli (`asma_core/`)

- [`models.py`](asma_core/models.py): Modelli di dominio con UUIDv4 e timestamp ISO 8601 (`Song`, `Repertoire`, `Setlist`, `Revision`, `LockStatus`, `AuditEntry`).
- [`music_engine.py`](asma_core/music_engine.py): Motore musicale deterministico (Pitch Class $[0, 11]$, trasposizioni $[-12, +12]$, circolo delle quinte, notazione ITA/INT, calcolo compatibilità Medley).
- [`aml_parser.py`](asma_core/aml_parser.py): Parser formale AST, serializzatore bidirezionale, importatore da spartiti tradizionali.
- [`lock_manager.py`](asma_core/lock_manager.py): Gestione dei lock concorrenti in memoria con heartbeat di sessione e rilascio forzato.
- [`storage_manager.py`](asma_core/storage_manager.py): Storage a doppio livello: indice SQLite in RAM ($< 2\text{ ms}$) + persistenza file JSON con cestino e retention a 30 giorni.
- [`pdf_engine.py`](asma_core/pdf_engine.py): Motore di pubblicazione PDF ReportLab device-aware (smartphone, tablet, iPad, A4) con impaginazione intelligente anti-orfanità (*Smart Page Break*).
- [`live_stage_component.py`](asma_core/live_stage_component.py): Componente Web Standalone per il palco (scorrimento continuo a 60 fps, pedali Bluetooth HID, metronomo Web Audio a latenza zero, Keep Screen Awake, cache locale).
- [`export_engine.py`](asma_core/export_engine.py): Esportazione verso MobileSheets, SongBookPro, OnSong, ChordPro e Offline Live Pack ZIP.
- [`import_engine.py`](asma_core/import_engine.py): Ingestione multi-formato da PDF, ChordPro e testi tradizionali.

---

## 🏥 Monitoraggio & Health Endpoint
L'endpoint per UptimeRobot / Pingdom è attivo all'indirizzo:
```text
https://[app-url]/?endpoint=health
```
Restituisce lo stato dei sottosistemi in formato JSON con codice HTTP 200.
