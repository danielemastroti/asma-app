# 19. Roadmap e Sviluppi Futuri

## 19.1 Obiettivo

La roadmap definisce l'evoluzione progressiva della piattaforma ASMA Accordi Next Generation.

Lo sviluppo deve seguire una strategia incrementale:

```text
MVP
↓
Versione Operativa
↓
Versione Collaborativa
↓
Versione Professionale
↓
Versione Enterprise Band
```

Ogni fase deve produrre una versione stabile e utilizzabile.

---

# 19.2 Principi di Evoluzione

Ogni nuova funzionalità deve rispettare:

- Compatibilità con i dati esistenti
- Nessuna regressione musicale
- Nessuna perdita di informazioni
- Mantenimento delle performance
- Aggiornamento automatico di Changelog e Manuale

---

# 19.3 Fase 1 - MVP

## Obiettivo

Rendere disponibile una prima versione completamente utilizzabile dalla band.

---

## Funzionalità Incluse

### Autenticazione

- Login Google
- Gestione utenti autorizzati
- Ruoli Admin ed Editor

---

### Repertori

- Creazione repertori
- Modifica repertori
- Eliminazione repertori
- Ricerca repertori

---

### Brani

- Creazione
- Modifica
- Salvataggio
- Versionamento base

---

### Editor Musicale

Supporto:

- ITA
- INT
- ChordPro
- Tradizionale

---

### PDF

Generazione:

- Brano singolo
- Repertorio

---

### Modalità Palco

Versione iniziale.

---

### GitHub Gist

Sincronizzazione dati.

---

## Obiettivo di Rilascio

Versione interna utilizzabile dalla band.

---

# 19.4 Fase 2 - Collaborazione

## Obiettivo

Abilitare lavoro multiutente avanzato.

---

## Funzionalità

### Lock Editing

- Check-out brani
- Timeout
- Sblocco

---

### Review

- Versionamento completo
- Diff revisioni
- Restore

---

### Audit Trail

Storico attività utenti.

---

### Notifiche

Visualizzazione modifiche recenti.

---

## Obiettivo

Ridurre conflitti durante il lavoro simultaneo.

---

# 19.5 Fase 3 - Modalità Live Professionale

## Obiettivo

Ottimizzare l'utilizzo durante concerti e prove.

---

## Funzionalità

### Modalità Palco Avanzata

- Fullscreen
- Scroll automatico
- Scroll manuale
- Cache offline

---

### Metronomo

Integrato.

---

### Device Profiles

- Smartphone
- Tablet
- iPad
- A4

---

### Eventi Live

Nuova entità.

---

## Obiettivo

Utilizzo reale durante eventi.

---

# 19.6 Fase 4 - Motore Musicale Avanzato

## Obiettivo

Trasformare la piattaforma in uno strumento musicale intelligente.

---

## Funzionalità

### Trasposizione Avanzata

- Armature automatiche
- # e b automatici
- Override utente

---

### Progressioni Armoniche

Riconoscimento automatico.

---

### Ricerca Musicale

Per:

- Tonalità
- BPM
- Compatibilità armonica

---

### Motore Medley

Generazione assistita.

---

## Obiettivo

Supportare il lavoro musicale della band.

---

# 19.7 Fase 5 - Ecosistema PDF Professionale

## Obiettivo

Portare il PDF Engine a livello professionale.

---

## Funzionalità

### Template PDF

- Studio
- Stage
- Rehearsal

---

### Copertine

Personalizzabili.

---

### PDF Batch

Generazione massiva.

---

### Caching PDF

Automatico.

---

## Obiettivo

Ridurre drasticamente il lavoro di preparazione dei materiali.

---

# 19.8 Fase 6 - Interoperabilità

## Obiettivo

Ridurre il lock-in dei dati.

---

## Integrazioni

### MobileSheets

Import ed export.

---

### SongBookPro

Import ed export.

---

### OnSong

Import ed export.

---

### ChordPro

Supporto completo.

---

### AML

Formato nativo definitivo.

---

## Obiettivo

Massima portabilità dei contenuti.

---

# 19.9 Fase 7 - AI Assistita

## Principio

L'AI deve essere sempre opzionale.

---

## AI OFF

Nessuna AI.

---

## AI FREE

Modalità predefinita.

---

## AI PREMIUM

Facoltativa.

---

## Funzioni AI

Consentite esclusivamente per:

- Suggerimento medley
- Suggerimento arrangiamenti
- Ricerca web assistita
- Riassunti
- Produzione documentazione

---

## Funzioni NON gestite da AI

- Trasposizioni
- Parsing accordi
- Generazione PDF
- Calcoli musicali

---

# 19.10 Fase 8 - Mobile Companion

## Obiettivo

Preparare una futura app companion.

---

## Potenziali Funzioni

- Consultazione repertori
- Modalità palco
- Sincronizzazione cloud
- Download offline

---

## Nota

L'app non è prevista nella prima versione ma l'architettura deve essere predisposta.

---

# 19.11 Fase 9 - Statistiche Musicali

## Obiettivo

Analizzare l'attività della band.

---

## Indicatori

### Brani più utilizzati

### Brani mai eseguiti

### BPM più frequenti

### Tonalità più utilizzate

### Medley più utilizzati

### Attività utenti

---

## Dashboard

Interfaccia dedicata.

---

# 19.12 Fase 10 - Knowledge Base Musicale

## Obiettivo

Creare una base dati musicale condivisa.

---

## Contenuti

- Accordi
- Tecniche
- Guide
- Regole band

---

## Integrazione

Ricerca globale.

---

# 19.13 Evoluzioni PDF Future

Supportare:

### PDF Annotabili

### PDF Interattivi

### Indici Navigabili

### QR Code

---

# 19.14 Evoluzioni Live Future

Supportare:

### Pedali Bluetooth

- AirTurn
- PageFlip
- BlueTurn

---

### MIDI

Possibili integrazioni future.

---

### Cambio Brano Remoto

Sincronizzazione tra musicisti.

---

# 19.15 Evoluzioni Collaborative Future

Possibilità di introdurre:

### Commenti

### Discussioni

### Workflow Approvazione

### Revisione Brani

---

# 19.16 Evoluzioni Cloud Future

Possibile migrazione futura da GitHub Gist verso:

- Azure Storage
- PostgreSQL
- Supabase
- Firebase

senza modificare AML.

---

# 19.17 Compatibilità Retroattiva

Ogni nuova versione deve mantenere:

- Compatibilità AML
- Compatibilità PDF
- Compatibilità revisioni

---

# 19.18 Strategia Rilasci

Versionamento:

```text
AAAA.MM.GG
```

Esempio:

```text
2026.11.05
```

---

## Regola

Massimo una release ufficiale al giorno.

---

# 19.19 Criteri di Accettazione

Una nuova funzionalità può essere rilasciata solo se:

- Test superati
- Regressioni assenti
- Manuale aggiornato
- Changelog aggiornato
- Backup generato

---

# 19.20 Visione Finale

ASMA Accordi Next Generation dovrà evolvere da semplice archivio di accordi a:

```text
Piattaforma Collaborativa Musicale Completa
```

capace di supportare:

- Studio
- Prove
- Arrangiamento
- Gestione repertori
- Gestione eventi
- Performance live
- Produzione PDF
- Interoperabilità con software musicali

mantenendo come principi guida:

- Semplicità
- Affidabilità
- Portabilità dei dati
- Collaborazione
- Indipendenza dall'AI
- Centralità del musicista