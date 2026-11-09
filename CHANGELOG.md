# Registro delle Modifiche (Changelog Ufficiale)

## Versione 2026.11.09 (09/11/2026) — Persistenza Totale Preferenze Utente su Turso Cloud, Palco Start On-Demand, Header Compatto e Clean UI

### 🚀 Nuove Funzionalità (New Features)
- Persistenza Cloud Turso DB per Preferenze Utente & Dispositivo: memorizzazione sincrona e permanente a database per ogni singola coppia (utente, dispositivo). Vengono salvate le dimensioni dei font (testo e accordi), colonne PDF, margini laterali, colori personalizzati (testo, accordi, AML) e zoom dell'interfaccia, garantendo la disponibilità immediata a ogni nuovo login o riavvio dell'applicazione.
- Autoscroll Palco On-Demand: in Modalità Palco (Live Stage), lo scorrimento automatico non si avvia più da solo all'apertura del brano, ma parte unicamente quando il musicista tocca il pulsante 'AVVIO' o attiva il pedale Bluetooth.
- Feedback Visivo Inserimento Brani in Scaletta: notifica immediata (toast a scomparsa) e aggiornamento dinamico del conteggio brani quando si preme il grande tasto 'Inserisci' in scaletta.

### ⚡ Miglioramenti (Improvements)
- Sorgente AML Compatta nei Brani: ristrutturazione completa dei metadati in una griglia orizzontale su 6 colonne (Titolo, Tonalità, Artista, BPM, Genere, Capotasto), eliminando lo spreco di spazio verticale e migliorando la leggibilità immediata.
- Layout Brand Header e Stato Connessione: riposizionato il badge '● ONLINE' al di sotto del titolo 'THE New ASMA' con colonne a larghezza fissa per evitare qualsiasi sovrapposizione con il pulsante profilo utente ('👤 Cico').
- Sincronizzazione Navigazione a Doppia Riga: sincronizzati i menu a pills di primo e secondo livello con callback reattivi, eliminando il loop di refresh e lo sfarfallio della pagina.
- Ottimizzazione Zoom Tablet (Huawei): zoom dell'interfaccia applicato esclusivamente al contenitore primario ([data-testid='stAppViewContainer']), eliminando la riduzione cubica a cascata e preservando la larghezza intera del display.

### 🛡️ Sicurezza (Security)
- Pulizia definitiva credenziali e account dummy predefiniti (daniele@band.org, marco.chitarra@band.org, ospite@band.org) dal registro utenti e dal database cloud.
- Sincronizzazione bidirezionale protetta con Turso Cloud DB per le scalette live (compresa la 'Scaletta Live Band 2026' con 46 brani), al sicuro da reset del container effimero di Streamlit Cloud.

### 🐛 Correzioni di Bug (Bug Fixes)
- Correzione errore critico di avvio su Streamlit Cloud: rimosso parametro incompatibile 'toolbarMode' in .streamlit/config.toml che causava il blocco del container e la schermata 'Oh no. Error running app.'.
- Correzione AttributeError su MusicEngine.detect_notation_system: aggiunto il metodo di rilevamento notazione italiana/internazionale durante la modifica degli attributi di tonalità e capotasto.
- Eliminazione continua e forzata dei badge fluttuanti di Streamlit Cloud e GitHub (identicon e tasto 'Manage app' con corona rossa): iniettato watchdog JavaScript continuo (300ms) e fogli di stile anti-badge applicati a livello di root, parent e top DOM.
- Risolto disallineamento durante il ripristino di scalette live con tombstone pruning.

## Versione 2026.11.08 (08/11/2026) — Sincronizzazione Cloud Persistente, Spaziatura Accordi, Controlli Palco e Unicità Repertori

### 🚀 Nuove Funzionalità (New Features)
- Sincronizzazione Cloud Persistente bidirezionale (GitHub Gist) per scalette, brani e repertori: garanzia assoluta contro la perdita di dati dopo riavvii o nuovi deploy su Streamlit Cloud.
- Idratazione automatica all'avvio: il server recupera istantaneamente le 12 scalette della band e tutti i 41 brani ufficiali con schema dual-compatible.
- Controlli completi Modalità Palco (Live Stage): aggiunti pulsanti touch e scorciatoie pedali Bluetooth per cambio pagina (Pag Giù / Pag Su), navigazione brani (Prec / Succ), play/pausa e regolatore velocità autoscroll a 60fps.
- Toolbar persistente sezione Brani: header con titolo attivo e pulsanti compatti ('Nuovo brano', 'Salva nuova revisione', 'Rilascia lock', 'Elimina brano').
- Consulente arrangiamento AI multi-strumento con suggerimenti specifici per Tastiera, Voce, Chitarra ritmica, Chitarra elettrica, Basso, Batteria e Globale.
- Suggerimenti preset, scene memory e super knob Yamaha Montage dedicati ai tastieristi.

### ⚡ Miglioramenti (Improvements)
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
- Motore PDF: rimossa la tabella a celle colorate per le sequenze di accordi (griglie armoniche); ora renderizzate in linea con separatore '|' pulito (es. 'LA | DO | FA | SOL') conforme alla specifica utente.
- Parser AML e Motore Musicale: aggiunto riconoscimento nativo dell'accordo 'SOL4+' e suffissi '4+', con trasposizione corretta e unione automatica delle righe di accordi tradizionali posizionate sopra il testo (es. 'SOL'/'Vespe', 'SOL4+'/'anni').
- Anteprima PDF: risolto disallineamento della cache di sessione del preview e bug sintattico in app.py con aggiornamento istantaneo del ridimensionamento font degli accordi.
- Mobile UX: soppressione totale della tastiera virtuale all'apertura degli elenchi a discesa dei brani (selectbox) su smartphone e tablet (Android/iOS). I menu con opzioni precompilate non richiedono digitazione e non aprono più la tastiera su schermo, lasciando tutta la visuale libera per scorrere e selezionare il brano.
- Persistenza Dispositivo su Cookie di Sessione e LocalStorage: isolamento totale dell'accoppiamento utente-dispositivo tramite cookie locali nel browser. Il PC rimane impostato stabilmente su A4 Desktop e lo Smartphone su Pixel 8, prevenendo qualsiasi sovrascrittura incrociata anche dopo riavvii o nuovi deploy.
- Deduplicazione e Unicità Repertori: rimossi tutti i brani doppi dai repertori, unificati i codici brano canonici e imposto il controllo rigoroso anti-duplicato (case-insensitive) sullo stesso repertorio.
- Titoli Brani in UPPERCASE: formattati tutti i titoli dei brani ufficiali in lettere maiuscole per una leggibilità perfetta su display di palco e repertorio.
- Protezione Cestino e Persistenza post-Deploy: rimosso data/trash/ dal .gitignore e implementato il registro Tombstone permanente. Gli elementi cancellati (scalette, brani, repertori) non riappaiono mai più nei menu a discesa né dopo un deploy né dopo un riavvio, rimanendo recuperabili esclusivamente dall'Admin nel Cestino.

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
