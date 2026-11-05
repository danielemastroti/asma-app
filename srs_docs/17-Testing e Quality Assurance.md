# 17. Testing e Quality Assurance

## 17.1 Obiettivo

La qualità del software è un requisito fondamentale della piattaforma.

L'obiettivo è garantire che:

- Nessuna funzionalità musicale venga compromessa dai rilasci
- I dati non vengano corrotti
- I PDF continuino a essere generati correttamente
- Le esportazioni rimangano compatibili
- La modalità palco resti affidabile durante eventi live

Ogni modifica applicativa deve essere verificata prima del rilascio.

---

# 17.2 Filosofia QA

La piattaforma deve adottare il principio:

```text
Test First
Release Later
```

Nessuna release deve essere pubblicata senza aver completato i controlli automatici previsti.

---

# 17.3 Livelli di Test

Supportare:

- Unit Test
- Integration Test
- Functional Test
- Regression Test
- UX Test
- Performance Test
- Compatibility Test
- Security Test

---

# 17.4 Continuous Verification

Ogni modifica deve essere verificata automaticamente.

Eventi che avviano i test:

- Deploy
- Merge
- Aggiornamento dipendenze
- Release candidata

---

# 17.5 Test di Regressione Musicale

Funzionalità fondamentale della piattaforma.

Ogni rilascio deve verificare la compatibilità musicale completa.

---

## Controlli Obbligatori

Verificare:

- Accordi
- Trasposizioni
- PDF
- Tag
- Modalità palco
- Import
- Export

---

# 17.6 Test Parser Musicale

Verificare il riconoscimento corretto di:

## Accordi Semplici

```text
C
D
E
F
G
A
B
```

---

## Accordi Italiani

```text
DO
RE
MI
FA
SOL
LA
SI
```

---

## Accordi Complessi

```text
Cmaj7
Cm7
Csus4
C7+
Bbmaj7
C#m7b5
```

---

## Equivalenti Italiani

```text
DO+
LA-
REsus4
```

---

# 17.7 Test Trasposizione

Verificare:

```text
DO → RE
```

```text
SOL → LA
```

```text
Am → Bm
```

---

## Controlli

Verificare:

- Accuratezza
- Armature
- Conversioni
- Stabilità parser

---

# 17.8 Test Armature

Verificare:

### Modalità Diesis

```text
C#
D#
F#
```

---

### Modalità Bemolle

```text
Db
Eb
Gb
```

---

### Override Utente

Forzatura:

```text
Preferisci #
```

oppure

```text
Preferisci b
```

---

# 17.9 Test Progressioni Armoniche

Verificare il corretto riconoscimento di:

```text
DO LA SOL RE FA
```

---

e

```text
C Am G D F
```

---

## Validare

- Parsing
- Rendering
- PDF
- Modalità palco

---

# 17.10 Test AML

Verificare:

- Parsing AML
- Salvataggio AML
- Ricaricamento AML

---

## Controlli

Confermare che non vi siano perdite di dati.

---

# 17.11 Test ChordPro

Verificare:

- Import
- Export
- Conversione AML

---

# 17.12 Test Formato Tradizionale

Verificare:

```text
Accordi sopra testo
```

---

## Controlli

- Allineamento
- Conversione
- PDF

---

# 17.13 Test Tag Musicali

Verificare:

```text
{intro}
{verse}
{chorus}
{bridge}
{solo}
{outro}
```

---

## Verificare

- Editor
- PDF
- Modalità palco

---

# 17.14 Test Tag Personalizzati

Verificare:

```text
{note:}
{voice:}
{guitar:}
```

---

## Controlli

- Parsing
- Rendering
- Salvataggio

---

# 17.15 Test Annotazioni

Verificare separatamente:

### Annotazioni Condivise

### Annotazioni Private

---

## Controllare

- Visibilità
- Permessi
- Persistenza

---

# 17.16 Test Repertori

Verificare:

- Creazione
- Modifica
- Rinomina
- Eliminazione
- Ripristino

---

# 17.17 Test Brani

Verificare:

- Creazione
- Modifica
- Salvataggio
- Versionamento

---

# 17.18 Test Scalette

Verificare:

- Creazione
- Ordinamento
- Medley
- Durata totale

---

# 17.19 Test Eventi Live

Verificare:

- Creazione
- Associazione scaletta
- Modifica
- Export

---

# 17.20 Test Device Profiles

Supportare test per:

- Smartphone Android
- Tablet Android
- iPad
- iPad Pro
- PC A4

---

## Verificare

- Font
- PDF
- Modalità palco

---

# 17.21 Test Responsive

Verificare:

### Smartphone

320px+

---

### Tablet

768px+

---

### Desktop

1024px+

---

# 17.22 Test PDF

Funzione critica.

---

## PDF Brano

Verificare:

- Layout
- Impaginazione

---

## PDF Scaletta

Verificare:

- Ordine
- Numerazione

---

## PDF Repertorio

Verificare:

- Copertina
- Indice
- Navigazione

---

# 17.23 Test Split View

Verificare:

```text
Editor | Anteprima
```

---

## Compatibilità

- Desktop
- Tablet

---

# 17.24 Test Modalità Palco

Funzione critica.

---

## Verificare

- Caricamento
- Scrolling
- Stop
- Resume

---

## Cambio Brano

Tempo massimo:

```text
1 secondo
```

---

# 17.25 Test Cache Offline

Verificare funzionamento senza rete.

---

## Simulare

- Assenza internet
- Timeout storage
- Timeout GitHub

---

# 17.26 Test MobileSheets

Verificare:

- Export
- Import
- Metadati

---

# 17.27 Test SongBookPro

Verificare:

- Import
- Export
- Compatibilità

---

# 17.28 Test OnSong

Verificare:

- ChordPro compatibile
- Metadati
- Sezioni

---

# 17.29 Test Import PDF

Verificare:

- Parsing
- Accordi
- Titolo
- Metadati

---

# 17.30 Test Ricerca

Verificare:

- Titolo
- Autore
- Tonalità
- BPM
- Tag

---

# 17.31 Test Ricerca Armonica

Verificare:

- Tonalità compatibili
- Progressioni simili
- Suggerimenti medley

---

# 17.32 Test Versionamento

Verificare:

- Creazione revisioni
- Diff
- Restore

---

# 17.33 Test Lock Editing

Verificare:

- Lock automatico
- Timeout
- Sblocco

---

# 17.34 Test Backup

Verificare:

- Creazione
- Integrità
- Restore

---

# 17.35 Test Changelog

Verificare:

- Generazione automatica
- Versione giornaliera

---

# 17.36 Test Manuale

Verificare:

- Aggiornamento automatico
- PDF

---

# 17.37 Test Authentication

Verificare:

- Login Google
- Logout
- Scadenza sessione

---

# 17.38 Test Permessi

Verificare:

### Admin

Accesso completo.

### Editor

Accesso limitato.

---

# 17.39 Test Security

Verificare:

- Input validation
- Upload validation
- Protezione API

---

# 17.40 Test Performance

Obiettivi:

### Apertura Brano

```text
< 2 secondi
```

---

### Apertura Scaletta

```text
< 3 secondi
```

---

### Generazione PDF

```text
< 5 secondi
```

---

# 17.41 Test Monitoring

Verificare:

- Health endpoint
- Dashboard
- Log

---

# 17.42 Test UptimeRobot

Verificare:

- Risposta /health
- Status healthy

---

# 17.43 Test Deploy

Dopo ogni deploy verificare:

- Startup
- Connessioni
- Storage
- PDF Engine

---

# 17.44 Test Automatici Notturni

Eseguire suite completa giornaliera.

---

## Report

Produrre:

- Successi
- Warning
- Errori

---

# 17.45 KPI Qualità

Monitorare:

- Error Rate
- Uptime
- PDF Success Rate
- Export Success Rate
- Restore Success Rate

---

# 17.46 Criteri di Blocco Release

La release deve essere bloccata se:

- Fallisce un test musicale
- Fallisce un test PDF
- Fallisce un test export
- Fallisce un test di sicurezza
- Fallisce un test di restore

---

# 17.47 Definizione di Release Valida

Una release è valida soltanto se:

```text
Tutti i test critici =
PASS
```

---

# 17.48 Obiettivo Finale

Garantire che ogni nuova versione dell'applicazione sia affidabile per l'utilizzo reale durante:

- Studio
- Prove
- Eventi
- Concerti Live

senza introdurre regressioni funzionali, musicali o operative.