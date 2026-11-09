# Registro delle Modifiche (Changelog Ufficiale)

## Versione 2026.11.09 (09/11/2026) — Doppia Modalità di Accesso (Semplificata vs Editing), Persistenza Cloud Turso e Clean UI

### 🚀 Nuove Funzionalità (New Features)
- Doppia Modalità di Accesso (Editing vs Semplificata): selezione diretta alla pagina di login tra 'Modalità Semplificata' (live e concerto) e 'Modalità Editing' (gestione completa). I permessi del profilo utente (ADMIN, BAND_MEMBER, VIEWER) rimangono rigorosamente inalterati.
- Nuovo Menu Semplificato su Singola Riga: menu essenziale con funzioni base: Home, Brani, Scalette, Palco, Guida e Logout. Niente menu contestuali o schermate di configurazione inutilizzate prima di un concerto.
- Menu Brani Semplificato (NO EDIT): interfaccia pulita e immediata priva di tasti, controlli o elenchi a discesa di editing. Include la consultazione del brano, l'anteprima reale delle pagine PDF formattate per il dispositivo, il salvataggio PDF (con accordi / solo testo), l'invio diretto alla stampante A4, l'avvio della Modalità Palco e l'esportazione nei formati musicali (MobileSheets, SongBook Pro, ChordPro, OnSong).
- Modalità Editing Brani 100% Inalterata: l'accesso completo in modalità Editing preserva inalterate tutte le funzionalità preesistenti di editor AML, trasposizione, gestione lock e cronologia revisioni.

- Preferenza Spartito Personale (Solo Testo vs Testo+Accordi): ogni musicista può configurare nel proprio profilo il formato predefinito di visualizzazione spartito. La preferenza viene memorizzata permanentemente su Turso Cloud DB, caricata ad ogni login e applicata automaticamente come default nell'anteprima PDF. Rimane sempre garantita per tutti i componenti della band la possibilità di stampare o salvare in qualsiasi momento sia la versione con accordi che la versione solo testo.
- Persistenza Cloud Turso DB per Preferenze Utente & Dispositivo: memorizzazione sincrona e permanente a database per ogni singola coppia (utente, dispositivo). Vengono salvate le dimensioni dei font (testo e accordi), colonne PDF, margini laterali, colori personalizzati (testo, accordi, AML) e zoom dell'interfaccia, garantendo la disponibilità immediata a ogni nuovo login o riavvio dell'applicazione.
- Autoscroll Palco On-Demand: in Modalità Palco (Live Stage), lo scorrimento automatico non si avvia più da solo all'apertura del brano, ma parte unicamente quando il musicista tocca il pulsante 'AVVIO' o attiva il pedale Bluetooth.
- Feedback Visivo Inserimento Brani in Scaletta: notifica immediata (toast a scomparsa) e aggiornamento dinamico del conteggio brani quando si preme il grande tasto 'Inserisci' in scaletta.

### ⚡ Miglioramenti (Improvements)
- Sorgente AML Compatta nei Brani: ristrutturazione completa dei metadati in una griglia orizzontale su 6 colonne (Titolo, Tonalità, Artista, BPM, Genere, Capotasto), eliminando lo spreco di spazio verticale e migliorando la leggibilità immediata.
- Brand Header Pulito con LED Online Inline: sostituito il badge esteso 'ONLINE' con un discreto punto LED verde a 6px inline accanto al titolo 'THE New ASMA', eliminando alla radice qualsiasi rischio di sovrapposizione con il pulsante profilo utente ('👤 Cico') su ogni schermo tablet e smartphone.
- Sincronizzazione Navigazione a Doppia Riga: sincronizzati i menu a pills di primo e secondo livello con callback reattivi, eliminando il loop di refresh e lo sfarfallio della pagina.
- Ottimizzazione Zoom Tablet (Huawei): zoom dell'interfaccia applicato esclusivamente al contenitore primario ([data-testid='stAppViewContainer']), eliminando la riduzione cubica a cascata e preservando la larghezza intera del display.

### 🛡️ Sicurezza (Security)
- Pulizia definitiva credenziali e account dummy predefiniti (daniele@band.org, marco.chitarra@band.org, ospite@band.org) dal registro utenti e dal database cloud.
- Sincronizzazione bidirezionale protetta con Turso Cloud DB per le scalette live (compresa la 'Scaletta Live Band 2026' con 46 brani), al sicuro da reset del container effimero di Streamlit Cloud.

### 🐛 Correzioni di Bug (Bug Fixes)
- Risolto difetto click triplo sui pulsanti e pills di navigazione ("devi schiacciare i tasti tre volte"): rimosso l'azzeramento forzato incondizionato delle chiavi di sessione (`top_nav_pills_simp`, `top_nav_pills_r1`, `top_nav_pills_r2`) immediatamente prima delle chiamate `st.pills`, che sovrascriveva l'interazione touch dell'utente ripristinando il vecchio valore. Introdotta sincronizzazione selettiva che scatta unicamente in caso di cambio menu esterno, garantendo che ogni tocco sul display del tablet o click da mouse risponda al primo colpo istantaneamente.
- Risolto bug generazione PDF a 2 colonne con selezione a 1 colonna: corretta la mancata invalidazione della cache nei callback del popover di layout (`_on_columns_change`, `_on_font_size_change`, ecc.), aggiunta la pulizia immediata di `PDFEngine._cache` e dei buffer `buf_`, invocazione di `st.rerun()` ed estensione delle chiavi dei pulsanti di download (`key=dl_..._{columns}_{fl}_{fc}`) per forzare il refresh immediato del payload PDF scaricabile su Streamlit.
- Ottimizzazione reattività touch e pulizia thread JS mobile: eliminato il timer periodico `setInterval(..., 300)` da `browser_polyfill.py` che saturava la CPU sui tablet Android/Huawei provocando touch lenti o mancati, e protetta l'iniezione in `index.html` con versione blindata contro vecchi residui di manipolazione DOM.
- Risolto Crash Bianco in Modalità Palco ('Node.removeChild'): rimossa la rimozione diretta di nodi DOM gestiti da React nei watchdog di stile, garantendo la transizione fluida e sicura alla Modalità Palco senza interruzioni di rendering.
- Correzione Dispositivo Cico e Priorità Profili Turso DB: corretto il riconoscimento hardware dei tablet Huawei (in precedenza scambiati per smartphone a causa della dicitura 'Mobile Safari' nell'user-agent) e blindata la priorità assoluta ai profili registrati nel database cloud (Foglio A4 da PC, Huawei MatePad da tablet), eliminando alla radice l'assegnazione accidentale di Pixel 8 pro.
- Ottimizzazione Prestazioni 'Brani' e Anteprima PDF: introdotto caching istantaneo (@st.cache_data) per rendering pagine PDF, pulsanti di stampa A4 e compilazione documenti musicali, abbattendo il tempo di apertura e selezione brano da 5 secondi a meno di 150ms.
- Unico Tasto Logout e Correzione Flusso di Disconnessione: eliminato qualsiasi tasto duplicato di logout (rimosso dai menu secondari e dal profilo popover); mantenuto un unico tasto '🚪 Logout' nella barra superiore con callback on_click dedicato e flag di disconnessione di sessione, garantendo logout immediato e funzionante.
- Risoluzione Sovrapposizione Header Brand: rimossa la badge di modalità (LIVE/EDIT) dall'header brand ed eliminata la larghezza massima fissa (180px), azzerando qualsiasi collisione o sovrapposizione con il profilo musicista ('👤 Cico') su tablet e smartphone.
- Ottimizzazione Velocità Logon e Logout: rimossa la chiamata di sincronizzazione cloud remota bloccante all'accesso sessione (lo storage è già istantaneo in-memory e SQLite), velocizzando il login e la navigazione ad apertura immediata (<100ms).
- Risolto bug dispositivo attivo e preferenze incrociate tra PC e Tablet: memorizzazione e ripristino indipendenti dell'ultimo dispositivo per categoria hardware (desktop PC, tablet, smartphone). Se l'utente imposta "Foglio a 4 stampabile" da PC, al nuovo login dallo stesso PC ritrova fedelmente "Foglio a 4 stampabile" con tutti i settaggi di testo, accordi, margini, colonne e colori, senza sovrapporsi al tablet (es. Huawei). La selezione genera un inserimento/aggiornamento immediato su Turso Cloud DB (ON CONFLICT DO UPDATE).
- Eliminazione residuo script visualizzato su tablet Huawei: rimossa chiamata deprecata a st.markdown contenente codice di polyfill, garantendo schermate perfettamente pulite senza testi grezzi sotto la barra di navigazione.
- Risolto bug di sovrascrittura preferenze utente su reload: sincronizzati i widget slider e radio con le chiavi di sessione e callback on_change dedicati, impedendo a valori di fallback o widget non inizializzati di azzerare i valori salvati a database.
- Correzione sparizione editor e anteprima nei Brani: aggiunta sincronizzazione esplicita delle chiavi univoche (UUID) per l'area di testo AML, i commenti di revisione e i pulsanti di sblocco/salvataggio, garantendo rendering stabile su ogni cambio brano.
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
