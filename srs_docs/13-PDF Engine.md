# 13. PDF Engine

## 13.1 Obiettivo

Il PDF Engine rappresenta il motore di pubblicazione ufficiale della piattaforma.

Deve consentire la generazione di documenti professionali ottimizzati per:

- Smartphone Android
- Tablet Android
- iPad
- iPad Pro
- Formato A4 stampabile
- MobileSheets
- SongBookPro
- OnSong
- Archiviazione digitale

L'obiettivo è garantire che la visualizzazione e la stampa siano coerenti con il profilo dispositivo selezionato.

---

## 13.2 Filosofia

L'intero sistema PDF deve basarsi sul principio:

```text
Unica sorgente dati
Molteplici formati di uscita
```

Il PDF non deve mai essere modificato direttamente.

Ogni PDF deve essere generato a partire dal contenuto sorgente AML.

---

## 13.3 Tipologie di PDF

Supportare almeno:

### PDF Brano

Generazione di un singolo brano.

---

### PDF Scaletta

Generazione dell'intera scaletta.

---

### PDF Repertorio

Generazione di tutti i brani appartenenti a un repertorio.

---

### PDF Evento Live

Generazione completa di:

- Evento
- Scaletta
- Note organizzative
- Informazioni logistiche

---

## 13.4 PDF Device-Aware

Ogni PDF deve essere generato in base al profilo dispositivo selezionato.

Esempi:

### Smartphone

Caratteri molto leggibili.

Massima ottimizzazione verticale.

---

### Tablet

Equilibrio tra informazioni visibili e numero pagine.

---

### iPad

Layout ottimizzato per utilizzo live.

---

### PC

Formato:

```text
A4 Stampabile
```

---

## 13.5 Impostazioni Device

Ogni profilo può definire:

- Dimensione testo
- Dimensione accordi
- Margini
- Orientamento
- Interlinea
- Spaziatura accordi
- Gestione page break

---

## 13.6 Orientamento

Supportare:

### Portrait

```text
Verticale
```

### Landscape

```text
Orizzontale
```

---

## 13.7 Anteprima PDF

Ogni modifica deve essere visualizzabile tramite:

```text
Anteprima PDF Live
```

aggiornata senza rigenerazione manuale.

---

## 13.8 Split View

Modalità consigliata:

```text
Editor | Anteprima PDF
```

specialmente da desktop e tablet.

---

## 13.9 Contenuti PDF

Il PDF può contenere:

- Titolo
- Autore
- Artista
- Accordi
- Testo
- BPM
- Tonalità
- Time Signature
- Tag musicali
- Note condivise

---

## 13.10 Contenuti Facoltativi

Configurabili:

- Data generazione
- Numero revisione
- Repertorio
- Nome evento
- Autore ultima modifica

---

## 13.11 Header PDF

Configurabile.

Esempio:

```text
Hotel California
Eagles
Original Key: Bm
Current Key: Am
```

---

## 13.12 Footer PDF

Configurabile.

Possibili informazioni:

```text
Pagina 4 di 12
```

```text
Versione Documento
```

```text
Data Generazione
```

---

## 13.13 Numerazione Pagine

Supportata per tutti i PDF multipagina.

---

## 13.14 Indice Automatico

Disponibile per:

### Repertori

### Scalette

### Eventi

Generato automaticamente.

---

## 13.15 Gestione Note Musicali

Visualizzare correttamente:

```text
{note:}
```

```text
{voice:}
```

```text
{solo:}
```

```text
{guitar:}
```

```text
{drums:}
```

---

## 13.16 Rendering Tag

Esempio:

Input:

```text
{note:Tutti insieme}
```

Output PDF:

```text
Tutti insieme
```

senza mostrare il markup.

---

## 13.17 Evidenziazione Tag

Configurabile.

Possibili rendering:

- Box colorato
- Grassetto
- Corsivo
- Evidenziato

---

## 13.18 Sezioni Musicali

Riconoscere automaticamente:

```text
{intro}
```

```text
{verse}
```

```text
{chorus}
```

```text
{bridge}
```

```text
{solo}
```

```text
{outro}
```

---

## 13.19 Progressioni Armoniche

Riconoscere e formattare:

```text
C | Am | F | G
```

come blocco armonico.

---

## 13.20 Gestione Medley

Supportare:

- Separazione visiva
- Cambio titolo
- Cambio tonalità
- Cambio BPM

all'interno dello stesso PDF.

---

## 13.21 Cambio Pagina Intelligente

Evitare:

- Spezzatura accordi
- Taglio righe
- Spezzatura sezioni

quando possibile.

---

## 13.22 Controllo Allineamento

Prima della generazione verificare:

- Allineamento accordi
- Spaziatura
- Margini
- Overflow

---

## 13.23 Validazione PDF

Bloccare la generazione se vengono rilevati:

- Accordi non riconosciuti
- Tag invalidi
- Errori strutturali AML

---

## 13.24 Template PDF

Supportare almeno:

### Standard

Uso generale.

---

### Stage

Ottimizzato per palco.

---

### Studio

Ottimizzato per stampa.

---

### Rehearsal

Ottimizzato per prove.

---

## 13.25 Watermark

Opzionale.

Esempio:

```text
Versione Provvisoria
```

---

## 13.26 Filigrana Personalizzata

Configurabile dall'amministratore.

---

## 13.27 PDF Protetti

Opzione futura:

- Blocco copia
- Password
- Lettura sola visualizzazione

---

## 13.28 PDF per MobileSheets

Esportazione dedicata.

Obiettivo:

miglior compatibilità possibile con MobileSheets.

Includere:

- Metadati
- Titolo
- Tonalità
- Tag

---

## 13.29 PDF per SongBookPro

Ottimizzare:

- Layout
- Metadati
- Compatibilità importazione

---

## 13.30 PDF per OnSong

Ottimizzare:

- Riconoscimento sezioni
- Accordi
- Tag AML convertiti

---

## 13.31 PDF Batch

Supportare generazione massiva.

Esempio:

```text
Genera PDF per tutti i brani del repertorio
```

---

## 13.32 Gestione Copertina

Supportare copertine personalizzate per:

- Repertori
- Scalette
- Eventi

---

## 13.33 Statistiche PDF

Registrare:

- Numero generazioni
- Utente
- Data
- Device utilizzato

---

## 13.34 Cronologia PDF

Memorizzare:

- Ultimi PDF generati
- Ultime impostazioni
- Ultimo profilo utilizzato

---

## 13.35 Caching PDF

Se nessuna modifica è intervenuta:

- Riutilizzare PDF già generato

per aumentare velocità.

---

## 13.36 Prestazioni

Obiettivi:

### Brano singolo

```text
< 2 secondi
```

---

### Scaletta

```text
< 5 secondi
```

---

### Repertorio completo

```text
< 15 secondi
```

---

## 13.37 Affidabilità

La generazione PDF deve funzionare anche in assenza di:

- Gemini
- OpenAI
- Claude
- Servizi AI esterni

---

## 13.38 Test Automatici PDF

Ad ogni rilascio eseguire:

- Test smartphone
- Test tablet
- Test iPad
- Test A4
- Test medley
- Test tag
- Test progressioni armoniche

---

## 13.39 Obiettivo Finale

Il PDF Engine deve produrre documenti professionali che possano essere:

- Stampati
- Archiviati
- Utilizzati dal vivo
- Condivisi con altri musicisti
- Importati in software esterni

senza richiedere modifiche manuali successive.