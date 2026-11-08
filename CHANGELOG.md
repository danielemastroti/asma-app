# Registro delle Modifiche (Changelog Ufficiale)

## Versione 2026.11.08 (08/11/2026) — Sincronizzazione Cloud Persistente, Spaziatura Accordi, Controlli Palco e Unicità Repertori

### 🚀 Nuove Funzionalità (New Features)
- Permanenza Profili Display Utente/Dispositivo: memorizzazione indipendente del profilo hardware basata sull'accoppiamento utente e tipo dispositivo (smartphone es. Pixel 8, desktop PC es. A4 stampabile, tablet), evitando sovrascritture incrociate tra login successivi da device diversi.
- Dimensione Carattere Accordi Indipendente: aggiunto slider dedicato nel popover 'Formato & Testo' per regolare in modo autonomo la dimensione degli accordi (8-32 px) rispetto a quella del testo/testi.
- Scalette Mobile-Friendly: riorganizzazione dell'area di lavoro in schede 'Ordine di Palco' e 'Aggiungi Brani dai Repertori' a tutta larghezza, eliminando il restringimento su mobile e rendendo le colonne perfettamente fruibili.
- Gestione Repertori Potenziata: aggiunta funzione 'Rinomina Repertorio' con validazione di univocità del nome (case-insensitive).
- Clonazione Brani tra Repertori: pulsante 'Clona per Altro Repertorio' per creare versioni indipendenti (nuovo UUID) con diverso arrangiamento (es. versione acustica vs elettrica).
- Cestino Amministrativo Completo: suddivisione chiara del cestino in 3 sezioni ('Brani', 'Scalette', 'Repertori') con metadati completi e ripristino istantaneo con singolo click.
- Suggerimenti AI Arrangiamento Dinamici: integrazione avanzata Gemini per produrre analisi armonica e arrangiamento personalizzati e unici per ciascun brano con fallback contestuale.
- Sincronizzazione Cloud Persistente bidirezionale (GitHub Gist) per scalette, brani e repertori: garanzia assoluta contro la perdita di dati dopo riavvii o nuovi deploy su Streamlit Cloud.
- Idratazione automatica all'avvio: il server recupera istantaneamente le 12 scalette della band e tutti i 41 brani ufficiali con schema dual-compatible.
- Controlli completi Modalità Palco (Live Stage): aggiunti pulsanti touch e scorciatoie pedali Bluetooth per cambio pagina (Pag Giù / Pag Su), navigazione brani (Prec / Succ), play/pausa e regolatore velocità autoscroll a 60fps.
- Toolbar persistente sezione Brani: header con titolo attivo e pulsanti compatti ('Nuovo brano', 'Salva nuova revisione', 'Rilascia lock', 'Elimina brano').
- Consulente arrangiamento AI multi-strumento con suggerimenti specifici per Tastiera, Voce, Chitarra ritmica, Chitarra elettrica, Basso, Batteria e Globale.
- Suggerimenti preset, scene memory e super knob Yamaha Montage dedicati ai tastieristi.

### ⚡ Miglioramenti (Improvements)
- Evidenza Repertorio Attivo in Editing: banner dedicato che mostra chiaramente il repertorio di lavoro attivo durante la modifica dei brani.
- Regola Obbligatoria Unicità Brani nei Repertori: consentite due versioni diverse dello stesso brano in due repertori differenti, ma vietati duplicati con lo stesso titolo all'interno dello stesso repertorio.
- Pulizia Schermata Import/Export: eliminato qualsiasi richiamo o visualizzazione della modalità palco con autoscroll dalla schermata di Import/Export.
- Design & Look and Feel: gerarchia visiva con colori di sfondo ben distinti tra parti fisse/strutturali (deep slate #0B0F19 / #111827) e parti modificabili/editor (#1E293B con accento cyan #38BDF8).
- Layout scalette ottimizzato: pulsanti sposta brano ('⬆️', '⬇️') ed elimina ('❌') disposti su un'unica riga orizzontale compatta su tutti i dispositivi mobili.
- Unicità rigorosa dei repertori: divieto assoluto di creare o rinominare repertori con nomi duplicati (case-insensitive), con notifica immediata d'errore.
- Cancellazione repertori fittizi o vuoti duplicati dal database.
- Selettore profili utente e simulazione ruoli riservato esclusivamente agli utenti Admin.
- Rimozione voce ridondante 'Logout' dai sottomenu orizzontali.

### 🛡️ Sicurezza (Security)
- Autenticazione Google OAuth reale e obbligatoria per tutti gli accessi: digitazione email autorizzata con login_hint e reindirizzamento diretto a Google per la verifica di sicurezza dell'identità (nessun bypass consentito).
- Risoluzione errore 400 redirect_uri_mismatch: allineamento e normalizzazione automatica dell'URI di reindirizzamento su '/oauth2callback' in perfetta corrispondenza con la configurazione di Google Cloud Console.
- Protezione area riservata band: solo gli account autenticati con successo dai server Google e registrati nella lista ufficiale musicisti possono accedere.

### 🐛 Correzioni di Bug (Bug Fixes)
- Motore PDF Griglie Armoniche: resa delle sequenze di soli accordi senza tabelle, separate semplicemente dal simbolo ' | ' come da specifica.
- Motore PDF Dimensioni Logo: rimpicciolito il logo band nell'intestazione per prevenire qualsiasi sovrapposizione con i titoli dei brani lunghi.
- Motore PDF: risolto incollamento accordi consecutivi (anti-gluing es. 'FADO' -> 'FA  DO', 'SIb/FADO/MI' -> 'SIb/FA  DO/MI  RE7/9+') con spaziatura minima garantita.
- Motore PDF: rimossa sillabazione accidentale a metà parola nei testi dei brani.
- Motore PDF: garantito margine inferiore di sicurezza anti-sovrapposizione (minimo 15 mm) rispetto al piè di pagina.
- Eliminazione permanente di brani dummy non caricati dall'utente (es. 'Sultans of Swing', 'Hotel California', 'Canzone per un'amica') dal repository e dai seeder di test.
- Live Stage: risolto blocco dell'autoscroll automatico causato da misurazione prematura dell'altezza del DOM.
- Schermata di Login minimale: form essenziale con solo inserimento email musicista e pulsante 'Accedi' (nessun pulsante superfluo); reindirizzamento istantaneo su Google OAuth con login_hint.
- Risolto AttributeError all'avvio: eliminato importlib.reload legacy in app.py con ripristino dell'importazione nativa e pulita di StorageManager.
- Accesso diretto automatico: se l'utente ha già effettuato l'autenticazione Google sul browser, accede direttamente all'applicazione senza passare dalla schermata di login.
- Risoluzione Errore Google 403 (Robottino 'Non disponi dell'autorizzazione necessaria'): rimossa navigazione iframe tramite meta-refresh e implementato reindirizzamento top-level (window.top) con pulsante diretto target='_top' per consentire a Google Accounts di aprirsi all'esterno del frame di Streamlit.
- Allineamento Autenticazione alla Prima Versione (Accordi): ripristinato il flusso di autenticazione nativo Streamlit OIDC con pulsante '🎸 Accedi con Google' (on_click=st.login), verifica st.user/headers e supporto Authlib per eliminare definitivamente qualsiasi blocco di navigazione o modulo manuale.

## Versione 2026.11.05 (05/11/2026) — Rilascio Ufficiale ASMA Accordi 2.0 (Next Generation)

### 🚀 Nuove Funzionalità (New Features)
- Architettura a due livelli: SQLite in-memory (< 2ms) e storage partizionato JSON.
- Formato ufficiale AML (ASMA Markup Language) come Single Source of Truth.
- Motore musicale deterministico (Zero-AI) con trasposizioni cromatiche -12/+12 semitoni e circolo delle quinte.
- Supporto nativo bilingue: notazione Italiana (DO, RE, MI...) e Internazionale (C, D, E...).
- Generatore PDF ReportLab Device-Aware con algoritmo Smart Page Break anti-orfanità per smartphone, tablet, iPad e A4.
- Modalità Palco (Live Stage) con scorrimento fluido a 60 fps, metronomo Web Audio API, Keep Screen Awake e pedaliere Bluetooth HID.
- Esportatore ed importatore per MobileSheets, SongBookPro, OnSong, ChordPro e Offline Live Pack ZIP.
- Web Importer per estrazione automatica di spartiti da portali italiani e internazionali.

### ⚡ Miglioramenti (Improvements)
- Sistema di lock editing concorrente con heartbeat di sessione a 60 minuti e sblocco forzato Admin.
- Cestino con conservazione per 30 giorni e ripristino istantaneo di brani, repertori e scalette.
- Endpoint di salute /health per prevenire lo sleep mode del cloud tramite UptimeRobot.
- Manuale utente auto-aggiornante online e PDF stampabile.

### 🛡️ Sicurezza (Security)
- Registro Audit Trail immutabile append-only per il tracciamento di tutte le modifiche critiche.
- Protezione contro l'inattività di sessione e isolamento dei dati sensibili.

### 🐛 Correzioni di Bug (Bug Fixes)
- Risolto disallineamento sillabico durante l'importazione da spartiti tradizionali con accordi sopra il testo.
- Risolta ambiguità interpretativa per accordi italiani complessi (DO7+, LA-, DO+).
