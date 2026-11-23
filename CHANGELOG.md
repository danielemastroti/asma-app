# Registro delle Modifiche (Changelog Ufficiale)

## Versione 2026.11.23 (23/11/2026) — Barre Superiori Fisse durante Scorrimento Lista Brani (Sticky UI), Persistenza Offline Completa PWA con Snapshot Locale, Risoluzione Modalità Palco Offline & Cache Anteprime PDF, Gestione Modifiche Offline (Caso B) & Fix Medley

### Nuove Funzionalità (New Features)
- Barra Superiore Fissa & Strumenti Pinned durante lo Scorrimento Lista Brani (Sticky Navigation & Toolbar): fissata l'intera area superiore della schermata (Header con Logo e Palco, Barra di Navigazione schede, Barra dei Filtri Repertorio con chip Band/Personale, tasto rapido '💾 Salva PDF', '📑 Lista PDF' e barra di ricerca istantanea) in modo che rimanga costantemente visibile e agganciata in cima allo schermo su tablet, iPad, smartphone e computer durante lo scorrimento della griglia dei brani. In questo modo, qualunque sia la posizione assunta nella lista (anche scorrendo verso il 40° o 50° brano), il musicista può sempre accedere con un tocco ai tasti di salvataggio PDF, al cambio repertorio, alla ricerca e al passaggio rapido alla Modalità Palco, senza dover risalire in cima alla pagina. Gestito inoltre l'offset automatico (scroll-margin-top) sul visualizzatore dello spartito e sul modulo di inserimento per un allineamento fluido sotto le barre fisse.
- Tasto Supplementare '💾 Salva PDF' in Cima alla Lista Brani (Accesso Rapido): introdotto un pulsante rapido di salvataggio/esportazione PDF nella barra superiore accanto ai chip del Repertorio Personale e prima di '📑 Lista PDF'. In questo modo, quando un musicista seleziona un brano all'inizio della lista col solo scopo di salvarlo, può scaricarlo immediatamente senza essere costretto a scorrere l'intero elenco fino a fondo pagina: il tasto '💾 Salva PDF' è ora comodamente disponibile sia in cima che in fondo alla lista.
- Persistenza Offline Completa PWA con Snapshot Locale: l'applicazione memorizza automaticamente in cache locale protetta (IndexedDB / localStorage) l'intero archivio musicale (tutti i 92 brani con testi AML completi, accordi, sezioni, metadati, repertori e scalette). In assenza di connessione Internet o segnale mobile (seminterrati, sale prove o palchi all'aperto), l'applicazione si avvia a 0ms, permettendo la consultazione, ricerca istantanea, trasposizione cromatica, vista Testo Web e Modalità Palco (Teleprompter a 60 fps con pedaliere Bluetooth) senza alcuna dipendenza da rete.
- Cache Intelligente Anteprime PDF per il Palco & Visualizzatore: introdotta la memorizzazione locale delle anteprime PDF renderizzate per il profilo hardware attivo (es. tablet Huawei MediaPad M5, iPad o A4). Se un musicista ha visualizzato uno spartito online prima del concerto o delle prove, lo spartito PDF rimane consultabile e fruibile al 100% in Modalità Palco anche in modalità aereo o con Wi-Fi disattivato, contrassegnato dal badge '📄 Spartito PDF da Cache Offline'.
- Fallback Iper-Resiliente Teleprompter per Palco Offline: se durante un live offline viene selezionata la vista PDF su un brano non ancora pre-caricato in cache, l'applicazione evita categoricamente schermate vuote o errori: attiva immediatamente la visualizzazione Teleprompter notturno (con testo, accordi, sezioni, autoscroll e trasposizione al volo intatti) e mostra un pill informativo '📡 Modalità Palco Offline: Teleprompter notturno attivo con accordi e testo completi'.
- Gestione Sicura delle Modifiche Offline (Caso B) & Bozze Locali: introdotta la gestione avanzata per la modifica dei brani in assenza di connessione. Se un musicista lavora su un proprio brano personale o ne crea uno nuovo mentre è offline, le modifiche vengono preservate localmente come 'Bozza Locale Offline' (con contrassegno visivo '💾 Bozza Offline' sulla card del brano). Non appena il dispositivo torna online, ASMA esegue la sincronizzazione automatica in background con il database centrale Turso Cloud, eliminando il rischio di perdere note o modifiche. I brani del Repertorio Ufficiale Band rimangono categoricamente protetti da alterazioni non connesse.
- Indicatore di Stato Connessione & Modale Dettagli Snapshot: inserito nella testata dell'applicazione un pill dinamico '🟡 Offline' / '🟢 Online' con modale informativa interattiva che riepiloga il numero di brani nello snapshot locale, la data dell'ultimo salvataggio e lo stato delle eventuali bozze offline in attesa di sincronizzazione.

### Miglioramenti (Improvements)
- Inclusione aml_content nell'Indice SQLite & API: la tabella in-memory `songs_index` del backend e l'endpoint `/api/songs` includono ora nativamente il corpo AML completo (`aml_content`) di ciascun brano. Lo snapshot locale scaricato dai tablet include pertanto l'intero patrimonio testuale e armonico senza dover effettuare singole chiamate di dettaglio.
- Supporto Scalette 100% Offline in Modalità Palco: `loadAndPlaySetlist` e `loadSetlists` recuperano ora scalette e brani dallo snapshot locale se il server non è raggiungibile, garantendo la continuità dello show dal vivo anche in caso di caduta totale della connessione durante il concerto.
- Risoluzione Prima Pagina Vuota sui Medley per Tablet e Smartphone (Fix ReportLab KeepTogether): eliminata l'anomalia che provocava la comparsa di una prima pagina vuota sul MEDLEY BATTISTI e su brani concatenati visualizzati su Huawei MediaPad M5, iPad 10.2" e smartphone. Rimosso l'involucro indivisibile outer KeepTogether che inglobava l'intero spezzone iniziale, mantenendo le protezioni atomiche delle singole sezioni ([INTRO], [STROFA], [RITORNELLO]) e la proprietà keepWithNext sui banner di titolo. La prima pagina viene ora popolata densamente a partire dalla prima riga utile su qualsiasi schermo.
- Bypass Autenticazione Offline per Sessioni Pregresse: abilitato il ripristino trasparente dell'identità musicista da memoria locale in caso di assenza di rete all'avvio dell'app, evitando il blocco accidentale sulla schermata di login Google quando ci si trova in sale prove o palchi offline.

### Sicurezza (Security)
- Protezione del Repertorio Ufficiale da Conflitti Offline: impedita la forzatura o clonazione disconnessa del catalogo ufficiale della band, preservando l'integrità del database condiviso e garantendo che le modifiche passino unicamente dal flusso validato online.

### Correzioni di Bug (Bug Fixes)
- Fix errore Teleprompter `renderAmlSectionBadge is not a function` & Switch Testo/Accordi: spostata la dichiarazione della funzione di formattazione badge di sezione all'esterno del ciclo di parsing a livello di modulo; ripristinato il corretto funzionamento immediato del pulsante di switch '🎤 Solo Testo' / '🎸 Accordi: ON' in Modalità Palco sia online che offline.
- Fix Modalità Palco Offline 'Nessun testo inserito' e PDF non visibile: eliminata l'assenza del testo e il messaggio 'Nessun testo inserito' quando si attiva la Modalità Palco con il tablet disconnesso, grazie all'inclusione di `aml_content` nello snapshot e al fallback resiliente.
- Fix selezione brano offline: il visualizzatore e la selezione brano (selectSong) utilizzano il fallback immediato sullo snapshot locale in caso di errore di rete delle API, eliminando blocchi dell'interfaccia.

## Versione 2026.11.22 (22/11/2026) — Formattazione Pagine Medley su Base Dispositivo nell'Editor, Prompt Guidato Post-Salvataggio nel Personale & Paginazione Smart

### Nuove Funzionalità (New Features)
- Formattazione Pagine Medley su Base Dispositivo nell'Editor (📐 Impagina Medley): nuova funzionalità integrata nell'editor AML e nel visualizzatore che permette al musicista di formattare e impaginare automaticamente gli spezzoni di un Medley su misura per il proprio dispositivo hardware (es. Tablet Huawei MediaPad M5 / MatePad, iPad, smartphone o foglio A4). Il sistema calcola il peso in righe di ciascuno spezzone e inserisce con precisione i salti pagina forzati ({np}) per garantire che ogni transizione live ricada nel punto ideale dello schermo o della stampa, senza spezzamenti accidentali di accordi o sezioni a fondo pagina.
- Prompt Guidato Post-Salvataggio nel Repertorio Personale: al completamento del salvataggio di un Medley nel Repertorio Personale (sia da nuovo brano che da modifica esistente), l'applicazione mostra un prompt modale dedicato che invita il musicista a procedere subito con l'impaginazione guidata su base dispositivo prima di tornare alla lista brani o al palco, garantendo che lo spartito sia immediatamente pronto e ottimizzato per il leggio digitale.
- Strategie di Impaginazione Multiple (Smart Fit, 1 Spezzone per Pagina, Personalizzata): la modale di impaginazione offre tre strategie flessibili: Compattazione Ottimizzata (Smart Fit) che raggruppa dinamicamente gli spezzoni in base alla capienza dello schermo target (52 righe per tablet a 2 colonne, 40 per foglio A4, 22 per smartphone); 1 Spezzone per Pagina che posiziona ciascun brano su una schermata/pagina indipendente; Personalizzata con toggle interattivi per ciascuno spezzone con stima pagine in tempo reale; e Rimuovi Salti Pagina per visualizzazione continua.
- Piena Parità Formattazione Dispositivo & Stampa A4 Tradizionale: il musicista mantiene come sempre la possibilità sia di visualizzare il medley ottimizzato per il dispositivo attualmente selezionato (sia a video che in Stage Mode o download PDF dispositivo), sia di generare, condividere su WhatsApp o stampare in qualsiasi momento la copia in formato A4 standard (con accordi o solo testo) identica a tutti gli altri brani del repertorio.

### Miglioramenti (Improvements)
- Nuovi Quick-Chip nell'Editor AML: aggiunti nella barra dei quick-chip i pulsanti ad inserimento rapido '📐 Impagina Medley', '␣ {riga_bianca}' e '📄 {np} Salto Pagina'.
- Rendering Web e Visualizzatore per Salto Pagina {np}: il parser web visualizza una barra tratteggiata elegante di demarcazione pagina con etichetta '--- Salto Pagina (Nuova Pagina PDF) ---', permettendo di verificare a colpo d'occhio dove cadrà il cambio pagina.
- Soppressione Separatori Medley Ridondanti in Testa a Nuova Pagina: nel generatore PDF (pdf_engine.py), se uno spezzone inizia in cima a una nuova pagina generata da un salto forzato {np}, la linea separatrice orizzontale superiore viene soppressa per non sovrapporsi o sporcare l'intestazione.
- Eliminazione Pagine Bianche su Esportazione e Condivisione WhatsApp A4 per Medley (Fix Pagina Bianca dopo With Or Without You): risolta l'anomalia che provocava la comparsa di una pagina bianca subito dopo lo spezzone With Or Without You nell'invio del MEDLEY ROCK in formato A4 alla band via WhatsApp o nella stampa diretta. Il sistema ora ri-ottimizza automaticamente la capienza per il foglio A4 (40 righe in colonna singola, 52 a due colonne) indipendentemente dal dispositivo per cui il medley era stato salvato nel repertorio personale, normalizza la sintassi dei frammenti e ripulisce distanziatori e salti ridondanti a inizio frame tramite SmartDocTemplate, garantendo documenti A4 continui, densi e impeccabili per tutti i musicisti.
- Risoluzione Taglio Piè di Pagina su iPad 7ª/8ª/9ª Generazione & Regolazione Margine Inferiore (14mm): ricalibrate le proporzioni geometriche del profilo hardware per iPad 10.2" (altezza utile 224.0 mm, ratio ~1.28) allineandole all'area attiva reale del display Retina 4:3 sotto le barre di navigazione delle app leggio (es. MobileSheets). Introdotto il parametro regolabile di 'Margine Inferiore PDF' (da 4 a 50 mm, default 14 mm) sia nelle impostazioni profilo che nei PDF scaricati, anteprime live e teleprompter palco. Il piè di pagina (NumberedCanvas) è ora posizionato dinamicamente in relazione al margine inferiore con margini laterali protetti, eliminando categoricamente qualsiasi troncamento o scomparsa di data di generazione, revisione e numero di pagina ('Pagina X di Y') sul bordo inferiore e sulla cornice del dispositivo.
- Deduplicazione Globale Indicazioni 'Strumentale' Consecutive tra Testo ed Accordi (Tutti i Brani & Visualizzazione Solo Testo): garantito che nella visualizzazione solo testo (sia sui PDF generati per Cico che su Web e Teleprompter Palco) non compaia mai 'Strumentale' ripetuto consecutivamente. Quando una riga di testo/commento esplicito (es. ♪ (Strumentale)) precede una battuta o sequenza di accordi (es. in Hanno ucciso l'Uomo Ragno, I'm a Believer, Medley Rock), il motore unifica l'indicazione emettendone una sola. Tutti gli accordi e le battute del catalogo rimangono al 100% inalterati e perfettamente intatti per chi suona con gli accordi.
- Standardizzazione Sezione [STROFA] su Tutto il Catalogo (con Avanzamento Revisioni): convertite tutte le strofe numerate ([STROFA 1], [STROFA 2], ecc.) e direttive ChordPro residue nella notazione pulita unificata [STROFA], migliorando la leggibilità live sul leggio per Cico e per la band. Ogni brano aggiornato ha avanzato la propria revisione con snapshot storici e tracciamento audit.
- Motore di Importazione ed Auto-Segmentazione allineato a [STROFA]: il motore centrale di segmentazione (BandAIService / WebImporter) assegna ora categoricamente il badge standard [STROFA] senza suffissi numerici sia su importazioni da ricerca web, testi tradizionali, ChordPro che scansione fotocamera.
- Quick-Chip Accordi in Notazione Anglosassone nell'Editor AML: aggiunta nella toolbar dell'editor una serie dedicata di chip rapidi per gli accordi anglosassoni ([C], [D], [E], [F], [G], [A], [B]) con evidenziazione azzurra ciano, utilizzabili in combinazione diretta con i tasti modificatori (m, 7, maj7, sus, dim, b, #, /).
- Strutturazione Musicale Sezioni AML su UNCHAIN MY HEART, A LUCA e JUMPIN JACK FLASH: UNCHAIN MY HEART (Joe Cocker) integrato con i badge standard [BRIDGE], [STROFA], [SOLO: Sax] e [FINALE], con correzione dell'accavallamento sintattico post-assolo; A LUCA (PICCOLA BAND) ripulito dall'intestazione duplicata e aggiornato con [RITORNELLO] e [SOLO: Chitarra]; JUMPIN JACK FLASH (The Rolling Stones) arricchito con la separazione netta del [RITORNELLO] da ciascuna strofa, [STRUMENTALE] centrale e [FINALE] per l'outro.

## Versione 2026.11.19 (19/11/2026) — Badge '⭐ Migliore' su Ricerca Web per Sezioni & Accordi, Standardizzazione Sezioni Repertorio Ufficiale & Pulizia Elenchi PDF

### Nuove Funzionalità (New Features)
- Badge '⭐ Migliore' su Ricerca Web per Sezioni & Accordi: nella modale di importazione web (Cerca sul Web), il motore di crawling interroga simultaneamente molteplici portali e calcola un punteggio combinato di qualità musicale. Il brano più completo, accurato e affidabile viene evidenziato a colpo d'occhio con il badge visivo verde smeraldo '⭐ Migliore', contorno in rilievo e pulsante '⭐ Importa Consigliato'. Il calcolo valorizza l'accuratezza armonica, le recensioni della community (rating fino a 5 stelle), il volume di voti verificati e la completezza delle sezioni ([INTRO], [STROFA], [RITORNELLO], [BRIDGE], [SOLO], [FINALE]), mostrando inoltre il dettaglio di stelle e voti.
- Standardizzazione Strutturale delle Sezioni sui 10 Brani del Repertorio Band: completata l'analisi e la correzione musicale approfondita di 10 brani cardine del Repertorio Ufficiale Band: Fortunate Son, Knock on Wood, Madre Dolcissima, Mustang Sally, Per Colpa Di Chi, Spirito, Venus, Vieni Qui, What a Wonderful World, Wicked Game. Tutti presentano ora la sequenza standard di badge ad alta visibilità ([INTRO], [STROFA 1], [RITORNELLO], [STROFA 2], [BRIDGE], [SOLO], [STRUMENTALE], [FINALE], [END]) preservando al 100% accordi, testi e tonalità.
- Pulizia e Normalizzazione Catalogo Ufficiale (47 Brani Unici): eliminata la copia duplicata di Hanno Ucciso L'Uomo Ragno con apostrofo tipografico; l'elenco ufficiale della band conta ora esattamente 47 brani unici, con titoli rigorosamente in MAIUSCOLO e formattazione pronta per la stampa e il leggio digitale.
- Isolamento Rigoroso Importazioni & Destinazione Esclusiva nel Repertorio Personale: qualsiasi brano creato o importato (da ricerca web, scansione fotocamera OCR Vision, incolla testo tradizionale, link URL diretto o editor manuale AML) viene indirizzato e salvato categoricamente nel Repertorio Personale del musicista connesso e MAI direttamente nel Repertorio Ufficiale Band. Il selettore del repertorio di destinazione mostra esclusivamente i repertori personali e un promemoria con lucchetto protettivo. L'accesso al Repertorio Ufficiale Band avviene unicamente a seguito dell'esplicita promozione ('⭐ Promuovi a Ufficiale'), proteggendo il catalogo concerti da importazioni grezze o bozze provvisorie.

### Miglioramenti (Improvements)
- Risoluzione Errori Sintattici e Tab Invasivi nei Brani Ufficiali: rimosso l'errore di parentesi annidate [LAm[LA]] in Venus, ripulite le tablature ASCII non allineate da Venus e Wicked Game, eliminati i badge duplicati a ripetizione consecutiva ([RITORNELLO] ripetuto su ogni riga in Madre Dolcissima e Vieni Qui), corretti i badge accavallati ([STROFA 1]\n[STROFA 3] in Wicked Game, [BRIDGE]\n[FINALE] in Per Colpa Di Chi) e riordinata la strofa 3 orfana in What a Wonderful World.
- Ottimizzazione Spaziatura Verticale Mustang Sally: eliminate le interlinee doppie superflue che gonfiavano lo spartito a dismisura, compattando la struttura in una visualizzazione armoniosa e perfettamente bilanciata su pagina singola.

## Versione 2026.11.18 (18/11/2026) — Download PDF Elenco Brani in Repertorio, Nuova Direttiva {riga_bianca}, Badge Sezioni Evidenziati, Icona Tastiera {scena: }, Paginazione Intelligente & Autorefresh Audit Log

### Nuove Funzionalità (New Features)
- Download PDF Elenco Brani in Repertorio: introdotta la possibilità di scaricare e stampare un documento PDF professionale con la lista completa e ordinata dei brani presenti in repertorio (sia per il Repertorio Ufficiale Band, per i repertori personali dei musicisti, o per il catalogo generale 'Tutti i Brani'). Il PDF include logo della band, conteggio totale dei brani, data di generazione, pseudonimo del musicista e una tabella ordinata alfabeticamente con numerazione progressiva (#), Titolo Brano, Artista, Tonalità in notazione italiana (DO, REm, ecc.), BPM e Durata, con intestazioni di colonna ripetute su tutte le pagine (repeatRows=1) e impaginazione reattiva ottimizzata sia per tablet (Huawei MediaPad M5) che per foglio A4. Pulsante '📑 Lista PDF' accessibile con un solo tocco direttamente accanto ai chip dei repertori e nella modale di gestione amministratore.
- Nuova Direttiva Riga Bianca {riga_bianca} / {blank_line}: consente di inserire una riga bianca vuota (o N righe / altezza personalizzata es. {riga_bianca: 2} o {riga_bianca: 15mm}) in qualsiasi posizione dello spartito (tra sezioni, tra versi o all'interno di una strofa/ritornello) sia nei PDF generati che nella visualizzazione web e teleprompter palco. Aggiunto anche il quick chip rapido '␣ {riga_bianca}' nella toolbar dell'editor AML.
- Nuova Direttiva Salto Pagina Forzato {np} / {new_page} / {salto_pagina}: forza l'interruzione immediata e il passaggio alla pagina successiva nella compilazione del PDF.
- Autorefresh Audit Log per Admin (5 Min): visualizzazione del registro di audit con aggiornamento automatico ciclico ogni 5 minuti (300.000 ms) per l'amministratore autenticato, corredata da indicatore verde di stato attivo nella testata della modale.
- Icona Grafica Tasti Live per {scena: }: la direttiva {scena: } elimina completamente la parola testuale 'scena' nei PDF e nel visualizzatore live, mostrando l'icona grafica della tastiera seguita dal preset/valore del musicista in un pill badge ciano dedicato.
- Badge Sezioni ad Alta Visibilità (simili a STACCO): tutti i badge musicali ([INTRO], [STROFA], [RITORNELLO], [RIT], [BRIDGE], [SOLO], [OUTRO]) sono ora evidenziati con sfondi pill compatti e colori dedicati vivaci ad alto contrasto sia su PDF che su Web/Palco.

### Miglioramenti (Improvements)
- Risoluzione Sezioni e Direttive nei PDF Scaricati (Rotolando verso sud) & Segmentazione Euristica: corretto e strutturato il brano Rotolando verso sud dei Negrita con tutte le sezioni AML standard ([INTRO], [STROFA 1], [RITORNELLO], [STROFA 2], [STROFA 3], [SPECIAL], [STROFA 4], [END]) sincronizzandolo su database locale e cloud Turso. Potenziato il motore di segmentazione euristica in BandAIService che rileva automaticamente strofe e ritornelli ripetuti anche per brani privi di tag espliciti, evitando la generazione di PDF con muri di testo non formattati.
- Sincronizzazione Parametro Trasposizione su Download PDF Brano: esteso l'endpoint /api/songs/{uuid}/pdf con il parametro transpose (semitoni al volo) sincronizzato con il visualizzatore e l'anteprima PDF.
- Formattazione e Paginazione Ottimale di Burning Love per Cico (Huawei MediaPad M5): risolta la formattazione anomala del brano Burning Love per il profilo tablet a 2 colonne di Cico con sezioni AML standard e griglia armonica bilanciata ripartita su esattamente 2 pagine piene ed equilibrate.
- Supporto Sezione [STRUMENTALE] / [INTERMEZZO] in AML Parser & PDF Engine: estesa la sintassi riconosciuta a livello di AST per includere le sezioni strumentali ([STRUMENTALE], STRUMENTALE:, [INTERMEZZO]) con rendering a badge pill dedicato in ocra/oro.
- Eliminazione Pagine Orfane per Badge [END]: il badge di chiusura [END] viene compattato e armonizzato per rimanere sempre all'interno dell'ultima pagina di musica.
- Paginazione Sezioni Lunghe (>6 righe) e Ottimizzazione Riempimento Pagine PDF: se una sezione è molto lunga, il blocco di testa (badge, direttive preliminari e prime 6 righe di testo) rimane unito contro gli orfani, mentre le righe successive scorrono sulla pagina successiva.
- Compattazione Spezzoni Medley: gli spezzoni di brani medley che possono rientrare in una singola pagina vengono preservati come unità compatta.
- Protezione Anti-Orfano Sezioni nei PDF: prevenzione dello spezzamento prematuro di intestazioni o versi isolati a fondo pagina.

## Versione 2026.11.14 (14/11/2026) — Medley Multi-Brano, Nuove Direttive Scena & Stacco, Ripristino Teleprompter Palco e Persistenza Dispositivo

### Nuove Funzionalità (New Features)
- Nuova Modalità MEDLEY nell'Editor: supporto a composizioni con molteplici spezzoni di brani indipendenti ({start_of_song: Titolo | Artista | Tonalità} e {end_of_song}), ciascuno con tonalità, introduzione e sezioni proprie, gestione fino a 20 brani, palette a colori alternati vivaci e separatore visivo.
- Nuova Direttiva Editor {Scena: } (es. {scena: 3}): setup rapido live per il tastierista con numero o nome preset/tasto synth, disponibile sia per brani singoli che Medley, visualizzato come badge in PDF, Web e Teleprompter Palco con quick chip dedicato.
- Nuova Direttiva Editor {Stacco: } (es. {stacco: guitar}, {stacco organo}, {stacco: Tutti}): break/stab strumentale d'insieme o per strumento, reso con badge dedicato e quick chip nell'editor.
- Persistenza Cloud Dispositivo Utente: la selezione del dispositivo hardware (iPad, Huawei MediaPad M5, ecc.) viene sincronizzata su database cloud Turso e ripristinata automaticamente ad ogni accesso.

### Miglioramenti (Improvements)
- Ottimizzazione Barra Superiore su Tablet Huawei (16:10): layout fluido che previene lo sbordo orizzontale su schermi da 800px.
- Pulizia Pulsanti Duplicati nella Home Dashboard: rimozione di controlli ridondanti per brani e scalette.
- Ottimizzazione RAM Anteprime PDF: rendering JPEG compresso 96 DPI e gestione rigorosa memoria PyMuPDF/GC per prevenire saturazione 512MB su Render
- Cache Pagine PDF Alleggerita: limite memoria dinamica a 6 voci massime con rilascio immediato buffer

### Correzioni di Bug (Bug Fixes)
- Ripristino Teleprompter in Modalità Palco: risolto il problema per cui il teleprompter non era più accessibile ed era visibile solo il PDF; reimpostata la vista live a Teleprompter Notte ad alto contrasto con autoscroll 60fps, scala font A+/A- e doppio switcher [Teleprompter / PDF] in alto e in basso.
- Persistenza Layout e Dispositivo: garantita conservazione di 1 colonna e font 13.0 per iPad e dispositivi hardware anche dopo nuovi deploy e login
- Ripristino Visualizzatore Brani & Anteprima PDF: eliminato il controllo restrittivo che svuotava il visualizzatore e annullava il brano selezionato; garantita la selezione automatica del primo brano al cambio repertorio e aggiornato il Service Worker a v77 per invalidare cache browser stale
- Risolto Teleprompter Nero in Modalità Palco: corretto errore ReferenceError amlText in parseAmlForWeb che interrompeva il rendering del testo notturno ad alto contrasto lasciando la schermata nera
- Fallback Resiliente Testo Palco: inserito blocco protettivo try/catch con visualizzazione immediata del testo anche in caso di anomalie formattazione

## Versione 2026.11.12 (12/11/2026) — Release Test

### Nuove Funzionalità (New Features)
- Protezione Rigorosa Repertorio Ufficiale: vietata la modifica diretta dei brani del repertorio ufficiale a tutti gli utenti (incluso l'amministratore). I musicisti creano la propria copia personale nel loro repertorio, apportano le modifiche, le salvano e poi le promuovono a Ufficiale (rimuovendo la copia personale).
- Condivisione A4 su WhatsApp per Scalette e Brani: invio del file PDF A4 pronto per la stampa direttamente su WhatsApp tramite Web Share API nativa (con allegato PDF reale per smartphone e tablet, e fallback web per desktop).
- Selettore Rapido Versione A4 (Con Accordi vs Solo Testo): pulsanti dedicati nella modale A4 per scegliere tra versione completa '🎸 Con Accordi' e versione '🎤 Solo Testo' (ideale per cantanti e leggii vocali), con regolazione separata dei font.
- Modifica Data di Esecuzione Scalette: campo data interattivo (gg/mm/aaaa) modificabile direttamente dall'editor scaletta con salvataggio automatico e sincronizzazione immediata nel database cloud Turso.
- Badge Fine Brano [END] Standard: inserito badge automatico [END] al termine di ogni spartito per i musicisti sul palco (sia nell'anteprima web che nei PDF generati).
- Registro Modifiche Dinamico (Changelog): consultabile liberamente da tutti i componenti della band con raggruppamento rigoroso a singola versione giornaliera e persistenza permanente su database cloud.
- Pannello Backup & Restore DB (Solo Admin): maschera esclusiva per gli amministratori per esportare il dump JSON integrale dell'intero database e changelog o ripristinarlo con un click.
- Feature Alfa
- Feature Beta
- Selettore Rapido Versione A4 (Con Accordi vs Solo Testo): pulsanti dedicati nella modale A4 per scegliere tra versione completa 'Con Accordi' e versione 'Solo Testo' (ideale per cantanti e leggii vocali), con regolazione separata dei font.

### Miglioramenti (Improvements)
- Prefetch PDF & Tocco Diretto iOS/iPadOS: precaricamento automatico in memoria dei PDF multi-pagina delle scalette per eliminare l'errore di scadenza del gesto utente di Safari ('user denied permission'), affiancato dal pulsante verde di invio istantaneo.
- Consolidamento Tag di Rollback Git: registrato e protetto su repository remoto il punto di ripristino rollback-point-997c1f5 per garantire rollback istantaneo e sicuro.

### Sicurezza (Security)
- Controllo Accessi & Backup Riservato Admin: gli endpoint di backup e restore del database sono protetti da verifica del ruolo amministratore con audit trail di ogni operazione.

### Correzioni di Bug (Bug Fixes)
- Risolto Bug Sezioni [INTRO: 1] / [INTRO: I]: corretta l'espressione regolare che scambiava la lettera 'I' di 'Intro:' per un numero romano 'I', garantendo la stampa dell'intestazione pulita [INTRO].
- Fix Alfa
- Fix Beta

## Versione 2026.11.09 (09/11/2026) — Doppia Modalità di Accesso (Semplificata vs Editing), Persistenza Cloud Turso e Clean UI

### Nuove Funzionalità (New Features)
- Doppia Modalità di Accesso (Editing vs Semplificata): selezione diretta alla pagina di login tra 'Modalità Semplificata' (live e concerto) e 'Modalità Editing' (gestione completa). I permessi del profilo utente (ADMIN, BAND_MEMBER, VIEWER) rimangono rigorosamente inalterati.
- Nuovo Menu Semplificato su Singola Riga: menu essenziale con funzioni base: Home, Brani, Scalette, Palco, Guida e Logout. Niente menu contestuali o schermate di configurazione inutilizzate prima di un concerto.
- Menu Brani Semplificato (NO EDIT): interfaccia pulita e immediata priva di tasti, controlli o elenchi a discesa di editing. Include la consultazione del brano, l'anteprima reale delle pagine PDF formattate per il dispositivo, il salvataggio PDF (con accordi / solo testo), l'invio diretto alla stampante A4, l'avvio della Modalità Palco e l'esportazione.
- Modalità Editing Brani 100% Inalterata: l'accesso completo in modalità Editing preserva inalterate tutte le funzionalità preesistenti di editor AML, trasposizione, gestione lock e cronologia revisioni.
- Preferenza Spartito Personale (Solo Testo vs Testo+Accordi): ogni musicista può configurare nel proprio profilo il formato predefinito di visualizzazione spartito, salvato su Turso Cloud DB e applicato come default.
- Persistenza Cloud Turso DB per Preferenze Utente & Dispositivo: memorizzazione sincrona e permanente a database per ogni singola coppia (utente, dispositivo).
- Autoscroll Palco On-Demand: in Modalità Palco (Live Stage), lo scorrimento automatico non si avvia più da solo all'apertura del brano, ma parte unicamente quando il musicista tocca il pulsante 'AVVIO' o attiva il pedale Bluetooth.

### Miglioramenti (Improvements)
- Fix Glitch Tag Script: rimosso il frammento di codice watchdog che appariva come testo grezzo in cima allo schermo su alcuni tablet Android / Huawei.
- Switcher rapido di modalità nel Profilo Musicista: possibilità di passare istantaneamente tra Modalità Semplificata e Modalità Editing in qualsiasi momento senza dover ripetere il login.
- Brand Header Pulito e Senza Sovrapposizioni: rimosso qualsiasi elemento superfluo o badge dall'header del brand, garantendo che il logo, 'THE New ASMA' e il LED di stato online abbiano spaziatura perfetta.

### Sicurezza (Security)
- Pulizia definitiva credenziali e account dummy predefiniti dal registro utenti e dal database cloud.
- Sincronizzazione bidirezionale protetta con Turso Cloud DB per le scalette live, al sicuro da reset del container effimero di Streamlit Cloud.

### Correzioni di Bug (Bug Fixes)
- Blindatura Anti-Crash React 18 su Tablet Huawei ('Node.removeChild'): integrato scudo di riconciliazione DOM per Node.prototype.removeChild e insertBefore unito al tag notranslate, eliminando alla radice l'errore 'The node to be removed is not a child of this node' durante il passaggio alla Modalità Palco o cambio vista.
- Priorità Tablet al Login e Unificazione Preferenze Utente nel DB: eliminata definitivamente la tabella client_preferences. Tutte le 9 preferenze utente (Modalità, Visualizzazione Predefinita, Dispositivo, Testo, Accordi, Colonne 1/2, Margini, Colori, Zoom) sono ora sincronizzate in user_device_preferences. Ad ogni login viene data priorità rigorosa al tablet del musicista.
- Risolto difetto click triplo sui tasti di navigazione: eliminata la sovrascrittura automatica delle chiavi di sessione dei widget di navigazione ad ogni ciclo di render. Ora ogni tocco su tablet e click su PC risponde all'istante al primo click senza richiedere pressioni ripetute.
- Risolto bug generazione PDF a 2 colonne quando impostata 1 colonna: integrata l'invalidazione istantanea della cache dei PDF e chiavi univoche versionate per i pulsanti di download, garantendo la rigenerazione immediata con il numero corretto di colonne.
- Ottimizzazione CPU mobile ed eliminazione polling JS continuo: rimosso il setInterval a 300ms che rallentava i tablet Android/Huawei e protetta la patch di index.html contro vecchi residui di manipolazione DOM.
- Risolto Crash Bianco in Modalità Palco ('Node.removeChild'): rimossa la rimozione diretta di nodi DOM gestiti da React nei watchdog di stile, garantendo la transizione fluida e sicura alla Modalità Palco senza interruzioni di rendering.
- Correzione Dispositivo Cico e Priorità Profili Turso DB: corretto il riconoscimento hardware dei tablet Huawei e blindata la priorità assoluta ai profili registrati nel database cloud (Foglio A4 da PC, Huawei MatePad da tablet), eliminando alla radice l'assegnazione accidentale di Pixel 8 pro.
- Ottimizzazione Prestazioni 'Brani' e Anteprima PDF: introdotto caching istantaneo (@st.cache_data) per rendering pagine PDF, pulsanti di stampa A4 e compilazione documenti musicali, abbattendo il tempo di apertura e selezione brano a meno di 150ms.
- Unico Tasto Logout e Correzione Flusso di Disconnessione: rimosso il pulsante duplicato di logout (eliminato da menu secondari e popover); mantenuto un unico tasto '🚪 Logout' nella barra superiore con callback on_click dedicato, eliminando il ricaricamento forzato errato e garantendo la disconnessione immediata ed effettiva.
- Risoluzione Sovrapposizione Header Brand: rimossa la badge di modalità (LIVE/EDIT) dall'header ed eliminata la larghezza massima fissa (180px), azzerando qualsiasi collisione o sovrapposizione con il profilo musicista ('👤 Cico') su tablet e smartphone.
- Ottimizzazione Velocità Logon e Logout: rimossa la chiamata di sincronizzazione cloud remota bloccante all'accesso sessione (lo storage è già istantaneo in-memory e SQLite), velocizzando il login e la navigazione ad apertura immediata (<100ms).
- Risolto bug dispositivo attivo e preferenze incrociate tra PC e Tablet: memorizzazione e ripristino indipendenti dell'ultimo dispositivo per categoria hardware (desktop PC, tablet, smartphone). Se l'utente imposta 'Foglio a 4 stampabile' da PC, al nuovo login dallo stesso PC ritrova 'Foglio a 4 stampabile' con tutti i settaggi (font, accordi, margini, colonne, colori), senza sovrapporsi al tablet (es. Huawei). La selezione genera un inserimento/aggiornamento immediato su Turso Cloud DB (ON CONFLICT DO UPDATE).
- Risolto glitch visivo di tag JS grezzo iniettato via markdown nella parte superiore della vista principale.
- Risolto bug di sovrascrittura preferenze utente su reload: sincronizzati i widget slider e radio con le chiavi di sessione e callback on_change dedicati, impedendo a valori di fallback di azzerare i valori a database.
- Correzione sparizione editor e anteprima nei Brani: aggiunta sincronizzazione esplicita delle chiavi univoche (UUID) per l'area di testo AML e pulsanti di sblocco/salvataggio.
- Correzione AttributeError su MusicEngine.detect_notation_system durante la modifica degli attributi di tonalità e capotasto.
- Unico Tasto Logout e Correzione Flusso di Disconnessione: rimosso il pulsante duplicato di logout (eliminato da menu secondari e popover); mantenuto un unico tasto 'Logout' nella barra superiore con callback on_click dedicato, eliminando il ricaricamento forzato errato e garantendo la disconnessione immediata ed effettiva.
- Risoluzione Sovrapposizione Header Brand: rimossa la badge di modalità (LIVE/EDIT) dall'header ed eliminata la larghezza massima fissa (180px), azzerando qualsiasi collisione o sovrapposizione con il profilo musicista ('Cico') su tablet e smartphone.

## Versione 2026.11.08 (08/11/2026) — Sincronizzazione Cloud Persistente, Spaziatura Accordi, Controlli Palco e Unicità Repertori

### Nuove Funzionalità (New Features)
- Sincronizzazione Cloud Persistente bidirezionale (GitHub Gist) per scalette, brani e repertori: garanzia assoluta contro la perdita di dati dopo riavvii o nuovi deploy su Streamlit Cloud.
- Idratazione automatica all'avvio: il server recupera istantaneamente le 12 scalette della band e tutti i 41 brani ufficiali con schema dual-compatible.
- Controlli completi Modalità Palco (Live Stage): aggiunti pulsanti touch e scorciatoie pedali Bluetooth per cambio pagina (Pag Giù / Pag Su), navigazione brani (Prec / Succ), play/pausa e regolatore velocità autoscroll a 60fps.
- Toolbar persistente sezione Brani: header con titolo attivo e pulsanti compatti ('Nuovo brano', 'Salva nuova revisione', 'Rilascia lock', 'Elimina brano').
- Consulente arrangiamento AI multi-strumento con suggerimenti specifici per Tastiera, Voce, Chitarra ritmica, Chitarra elettrica, Basso, Batteria e Globale.
- Suggerimenti preset, scene memory e super knob Yamaha Montage dedicati ai tastieristi.

### Miglioramenti (Improvements)
- Layout scalette ottimizzato: pulsanti sposta brano ('⬆️', '⬇️') ed elimina ('❌') disposti su un'unica riga orizzontale compatta su tutti i dispositivi mobili.
- Unicità rigorosa dei repertori: divieto assoluto di creare o rinominare repertori con nomi duplicati (case-insensitive), con notifica immediata d'errore.
- Cancellazione repertori fittizi o vuoti duplicati dal database.
- Selettore profili utente e simulazione ruoli riservato esclusivamente agli utenti Admin.
- Rimozione voce ridondante 'Logout' dai sottomenu orizzontali.
- Layout scalette ottimizzato: pulsanti sposta brano ('Su', 'Giu') ed elimina ('Elimina') disposti su un'unica riga orizzontale compatta su tutti i dispositivi mobili.

### Sicurezza (Security)
- Autenticazione Google OAuth reale e obbligatoria per tutti gli accessi: digitazione email autorizzata con login_hint e reindirizzamento diretto a Google per la verifica di sicurezza dell'identità (nessun bypass consentito).
- Risoluzione errore 400 redirect_uri_mismatch: allineamento e normalizzazione automatica dell'URI di reindirizzamento su '/oauth2callback' in perfetta corrispondenza con la configurazione di Google Cloud Console.
- Protezione area riservata band: solo gli account autenticati con successo dai server Google e registrati nella lista ufficiale musicisti possono accedere.

### Correzioni di Bug (Bug Fixes)
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
- Allineamento Autenticazione alla Prima Versione (Accordi): ripristinato il flusso di autenticazione nativo Streamlit OIDC con pulsante 'Accedi con Google' (on_click=st.login), verifica st.user/headers e supporto Authlib per eliminare definitivamente qualsiasi blocco di navigazione o modulo manuale.

## Versione 2026.11.05 (05/11/2026) — Rilascio Ufficiale ASMA Accordi 2.0 (Next Generation)

### Nuove Funzionalità (New Features)
- Architettura a due livelli: SQLite in-memory (< 2ms) e storage partizionato JSON.
- Formato ufficiale AML (ASMA Markup Language) come Single Source of Truth.
- Motore musicale deterministico (Zero-AI) con trasposizioni cromatiche -12/+12 semitoni e circolo delle quinte.
- Supporto nativo bilingue: notazione Italiana (DO, RE, MI...) e Internazionale (C, D, E...).
- Generatore PDF ReportLab Device-Aware con algoritmo Smart Page Break anti-orfanità per smartphone, tablet, iPad e A4.
- Modalità Palco (Live Stage) con scorrimento fluido a 60 fps, metronomo Web Audio API, Keep Screen Awake e pedaliere Bluetooth HID.
- Esportatore ed importatore per MobileSheets, SongBookPro, OnSong, ChordPro e Offline Live Pack ZIP.
- Web Importer per estrazione automatica di spartiti da portali italiani e internazionali.

### Miglioramenti (Improvements)
- Sistema di lock editing concorrente con heartbeat di sessione a 60 minuti e sblocco forzato Admin.
- Cestino con conservazione per 30 giorni e ripristino istantaneo di brani, repertori e scalette.
- Endpoint di salute /health per prevenire lo sleep mode del cloud tramite UptimeRobot.
- Manuale utente auto-aggiornante online e PDF stampabile.

### Sicurezza (Security)
- Registro Audit Trail immutabile append-only per il tracciamento di tutte le modifiche critiche.
- Protezione contro l'inattività di sessione e isolamento dei dati sensibili.

### Correzioni di Bug (Bug Fixes)
- Risolto disallineamento sillabico durante l'importazione da spartiti tradizionali con accordi sopra il testo.
- Risolta ambiguità interpretativa per accordi italiani complessi (DO7+, LA-, DO+).
