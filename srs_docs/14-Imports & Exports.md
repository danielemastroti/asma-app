# 14. Imports & Exports

## 14.1 Obiettivo

Il sistema deve consentire l'interoperabilità completa con le principali applicazioni musicali e con i formati maggiormente utilizzati dai musicisti.

Principi fondamentali:

- Nessun lock-in proprietario
- Importazione semplice
- Esportazione semplice
- Conservazione dei metadati
- Conservazione degli accordi
- Conservazione delle revisioni quando possibile
- Compatibilità multi-piattaforma

---

## 14.2 Filosofia

Tutti i contenuti devono essere memorizzati internamente nel formato:

```text
AML
ASMA Markup Language
```

Il formato AML rappresenta la sorgente unica di verità.

Tutti gli import e gli export devono transitare attraverso AML.

Schema:

```text
Formato Esterno
        ↓
      AML
        ↓
Formato Esterno
```

---

# 14.3 Formati Importati

Supportare almeno:

- PDF
- ChordPro
- Formato Tradizionale
- Testo Libero
- OnSong
- MobileSheets
- SongBookPro
- File AML

---

# 14.4 Import PDF

## Obiettivo

Permettere l'importazione di PDF provenienti da:

- Internet
- MobileSheets
- SongBookPro
- Raccolte personali
- Documenti cartacei digitalizzati

---

## Riconoscimento Automatico

Identificare automaticamente:

- Titolo
- Autore
- Artista
- Accordi
- Testo
- Sezioni musicali

---

## Parsing PDF

Il sistema deve tentare il riconoscimento di:

```text
Accordi sopra il testo
```

oppure

```text
Accordi inline
```

---

## Correzione Assistita

Qualora vengano rilevate anomalie:

Mostrare editor di conferma.

---

# 14.5 Import ChordPro

Supportare:

```text
{title:Hotel California}
{artist:Eagles}

[Am]On a dark desert highway
```

---

## Elementi ChordPro Supportati

```text
title
artist
album
key
tempo
comment
soc
eoc
start_of_chorus
end_of_chorus
```

---

## Conversione

Convertire automaticamente in AML.

---

# 14.6 Import Formato Tradizionale

Supportare:

```text
       C
Hello darkness my old friend
```

---

## Riconoscimento Automatico

Identificare:

- Riga accordi
- Riga testo
- Sezioni

---

## Conversione

Trasformare in AML.

---

# 14.7 Import Testo Libero

Consentire la creazione di nuovi brani partendo da:

```text
Testo semplice
```

oppure

```text
Accordi e testo misti
```

---

# 14.8 Creazione Rapida Brano

Caso d'uso:

Brani originali.

Brani inediti.

Bozze.

Medley.

---

## Editor Guidato

Possibilità di:

- Inserire testo
- Inserire accordi
- Inserire tag
- Inserire BPM
- Inserire tonalità

---

# 14.9 Import SongBookPro

Supportare:

- File esportati
- Metadati
- Accordi
- Sezioni

quando disponibili.

---

# 14.10 Import MobileSheets

Supportare:

- PDF
- Metadati
- Playlist
- Strutture compatibili

quando disponibili.

---

# 14.11 Import OnSong

Supportare:

- File compatibili OnSong
- ChordPro esteso
- Metadati

---

# 14.12 Import Repertorio

Possibilità di importare:

- Singolo brano
- Intero repertorio
- Librerie complete

---

# 14.13 Import Batch

Consentire importazione multipla.

Esempi:

```text
10 PDF
```

```text
50 ChordPro
```

```text
Intera cartella
```

---

# 14.14 Import da URL

Supportare:

```text
URL pubblico
```

contenente:

- PDF
- ChordPro
- Testi

---

# 14.15 Ricerca Web

Possibilità di cercare:

- Testi
- Accordi
- PDF

da sorgenti configurabili.

---

# 14.16 Import da Clipboard

Supportare:

```text
Copia e Incolla
```

direttamente nell'editor.

---

# 14.17 Controlli Import

Verificare sempre:

- Accordi validi
- Tonalità valide
- Tag validi
- Formato coerente

---

# 14.18 Gestione Errori

In presenza di errori:

- Mostrare dettaglio
- Evidenziare righe coinvolte
- Consentire correzione manuale

---

# 14.19 Modalità Preview

Ogni importazione deve consentire:

```text
Anteprima prima del salvataggio
```

---

# 14.20 Export PDF

Supportare:

- Brano
- Scaletta
- Repertorio
- Evento

---

# 14.21 Export ChordPro

Generare file ChordPro standard.

Esempio:

```text
{title:Hotel California}
```

---

# 14.22 Export AML

Consentire esportazione del formato nativo.

Utilizzato per:

- Backup
- Migrazione
- Restore

---

# 14.23 Export MobileSheets

## Obiettivo

Massima compatibilità possibile.

---

## Contenuti

Esportare:

- PDF
- Metadati
- Tonalità
- BPM
- Tag

quando supportati.

---

## Profilo Dedicato

Aggiungere:

```text
Esporta per MobileSheets
```

---

# 14.24 Export SongBookPro

Esportare:

- Testo
- Accordi
- Metadati
- Sezioni

quando supportati.

---

## Profilo Dedicato

```text
Esporta per SongBookPro
```

---

# 14.25 Export OnSong

Esportare:

- ChordPro compatibile
- Metadati
- Sezioni musicali

---

## Profilo Dedicato

```text
Esporta per OnSong
```

---

# 14.26 Export Repertorio

Supportare:

```text
ZIP completo
```

contenente:

- Brani
- PDF
- Metadati

---

# 14.27 Export Scaletta

Supportare:

- PDF unico
- PDF separati
- ZIP completo

---

# 14.28 Export Evento Live

Generare:

```text
Pacchetto Evento
```

contenente:

- Scaletta
- PDF
- Informazioni evento
- Note

---

# 14.29 Export Offline Pack

Funzione dedicata ai live.

Generare pacchetto contenente:

- PDF
- Scaletta
- Metadati

consultabile senza rete.

---

# 14.30 Conservazione Metadati

Durante import/export preservare ove possibile:

- Titolo
- Autore
- Artista
- Tonalità
- BPM
- Time Signature
- Tags
- Revisione

---

# 14.31 Conversione Automatizzata

Supportare:

```text
AML → ChordPro
```

```text
AML → PDF
```

```text
AML → MobileSheets
```

```text
AML → SongBookPro
```

```text
AML → OnSong
```

---

# 14.32 Compatibilità Futura

Architettura predisposta per:

- BandHelper
- Setlist Maker
- ForScore
- UnrealBook
- MobileSheets Pro

---

# 14.33 Log Operazioni

Registrare:

- Import eseguito
- Export eseguito
- Utente
- Data
- Formato

---

# 14.34 Statistiche

Mostrare:

- Formati più utilizzati
- Import più frequenti
- Export più frequenti

---

# 14.35 Test Automatici

Ad ogni rilascio eseguire:

## Import

- PDF
- ChordPro
- Tradizionale

---

## Export

- PDF
- MobileSheets
- SongBookPro
- OnSong
- AML

---

# 14.36 Obiettivo Finale

Un musicista deve poter:

1. Importare materiale esistente.
2. Modificarlo.
3. Organizzarlo in repertori.
4. Inserirlo in scalette.
5. Utilizzarlo dal vivo.
6. Esportarlo verso altre applicazioni.

senza perdita significativa di:

- Accordi
- Testo
- Tag musicali
- Metadati
- Informazioni esecutive.