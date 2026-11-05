# 18. Deployment e Infrastruttura

## 18.1 Obiettivo

L'infrastruttura deve garantire:

- Alta disponibilità
- Facilità di gestione
- Costi contenuti
- Affidabilità durante eventi live
- Semplicità di manutenzione
- Facilità di rollback

L'intera architettura deve essere progettata per essere gestita da una band musicale senza necessità di personale DevOps dedicato.

---

# 18.2 Architettura Generale

## Stack Applicativo

Frontend e Backend:

```text
Python
Streamlit
```

Hosting:

```text
Streamlit Community Cloud
```

Storage:

```text
GitHub Gist
```

Autenticazione:

```text
Google Authentication
```

Monitoraggio:

```text
UptimeRobot
```

---

# 18.3 Filosofia Infrastrutturale

Principio fondamentale:

```text
Keep It Simple
```

Evitare:

- Kubernetes
- Cluster complessi
- Database gestiti costosi
- Servizi non necessari

Prediligere:

- Componenti semplici
- Costi bassi
- Facilità di recupero

---

# 18.4 Repository GitHub

Tutto il progetto deve essere ospitato su GitHub.

---

## Contenuti Repository

```text
Codice Applicazione
Documentazione
Release Notes
Manuale
Test
Configurazioni
```

---

## Branching Strategy

Supportare:

```text
main
develop
feature/*
hotfix/*
```

---

# 18.5 Streamlit Cloud

Deployment principale tramite:

```text
Streamlit Community Cloud
```

---

## Deploy Automatico

Ogni aggiornamento del branch:

```text
main
```

può attivare il deploy automatico.

---

# 18.6 Startup Container

Durante l'avvio del container registrare:

- Timestamp startup
- Versione Python
- Versione Streamlit
- Versione applicazione
- Pacchetti caricati

---

## Esempio

```text
05/11/2026 10:15:10

Application Startup

Python 3.13
Streamlit 1.xx
ASMA 2026.11.05
```

---

# 18.7 Logging Startup

Registrare:

- Installazione pacchetti
- Verifiche iniziali
- Connessioni storage
- Inizializzazione AI

---

# 18.8 Versione Applicazione

Ogni deploy deve esporre:

```text
Versione Applicazione
```

Esempio:

```text
ASMA 2026.11.05
```

---

## Informazioni Addizionali

Visualizzare:

- Commit Git
- Data rilascio
- Autore rilascio

---

# 18.9 Storage Strategy

Lo storage principale è basato su:

```text
GitHub Gist
```

---

## Vantaggi

- Versionamento
- Facilità backup
- Ridotto costo
- Alta disponibilità

---

## Contenuti Memorizzati

- Repertori
- Brani
- Scalette
- Eventi
- Configurazioni
- Log applicativi

---

# 18.10 Organizzazione Dati

Separare logicamente:

```text
Configurazioni
```

```text
Dati Musicali
```

```text
Backup
```

```text
Log
```

---

# 18.11 Cache Locale

Utilizzare cache locale per:

- PDF
- Query frequenti
- Anteprime
- Modalità palco

---

## Obiettivo

Ridurre:

- Tempi di risposta
- Accessi GitHub
- Consumo rete

---

# 18.12 Persistenza Offline

Supportare:

```text
Offline Cache
```

per:

- Ultimi repertori
- Ultime scalette
- Ultimi PDF

---

# 18.13 UptimeRobot

L'applicazione sarà monitorata tramite:

```text
UptimeRobot
```

---

## Polling

Intervallo:

```text
5 minuti
```

---

## Obiettivo

Evitare:

```text
Sleep Mode
```

del container.

---

# 18.14 Health Endpoint

Esporre:

```text
/health
```

---

## Output

```json
{
  "status":"healthy",
  "version":"2026.11.05",
  "github":"ok",
  "authentication":"ok",
  "pdf":"ok",
  "ai":"ok"
}
```

---

# 18.15 Health Dashboard

Visualizzare:

- Stato Applicazione
- Stato GitHub
- Stato Authentication
- Stato PDF Engine
- Stato AI

---

# 18.16 Monitoraggio Disponibilità

Calcolare:

- Ultime 24 ore
- Ultimi 7 giorni
- Ultimi 30 giorni

---

## KPI

```text
Uptime %
```

---

# 18.17 Scalabilità

La piattaforma deve poter crescere fino ad almeno:

```text
100 utenti
```

senza modifiche architetturali sostanziali.

---

## Obiettivo

Supportare:

- Crescita band
- Collaboratori
- Musicisti ospiti

---

# 18.18 Gestione Aggiornamenti

Ogni aggiornamento deve:

1. Eseguire backup
2. Deploy nuova versione
3. Verificare test automatici
4. Aggiornare changelog
5. Aggiornare manuale

---

# 18.19 Rollback

In caso di problemi deve essere possibile:

```text
Rollback della Release
```

---

## Obiettivi

Tempo massimo:

```text
< 10 minuti
```

---

# 18.20 Configurazioni Applicative

Le configurazioni non devono essere hardcoded.

Utilizzare:

- Config File
- Variabili ambiente

---

# 18.21 Gestione Dipendenze

Definire:

```text
requirements.txt
```

completo e versionato.

---

## Controlli

Verificare:

- Dipendenze mancanti
- Versioni incompatibili

---

# 18.22 Moduli Applicativi

Separare logicamente:

```text
Authentication
```

```text
Music Engine
```

```text
PDF Engine
```

```text
AI Engine
```

```text
Administration
```

```text
Monitoring
```

```text
Imports
```

```text
Exports
```

---

# 18.23 Sistema Log

Registrare:

- Startup
- Shutdown
- Errori
- Warning
- Sync
- Backup

---

## Livelli Log

Supportare:

```text
INFO
SUCCESS
WARNING
ERROR
CRITICAL
```

---

# 18.24 Retention Log

Configurabile.

Valore consigliato:

```text
180 giorni
```

---

# 18.25 Centralizzazione Log

Tutti i log devono essere consultabili da UI.

L'amministratore non deve avere bisogno di accedere direttamente a:

- Streamlit
- Container
- Console Python

---

# 18.26 Exception Tracking

Registrare automaticamente:

- Exception Python
- Stack Trace
- Modulo Coinvolto
- Timestamp

---

## Visualizzazione

Supportare:

```text
Mostra Dettagli
```

per espandere il traceback.

---

# 18.27 System Diagnostics

Dashboard dedicata al troubleshooting.

Visualizzare:

- Memoria utilizzata
- Cache
- Stato servizi
- Errori recenti

---

# 18.28 Test Infrastrutturali

Verificare automaticamente:

- Storage
- Authentication
- PDF Engine
- AI Engine
- Cache

---

# 18.29 Disaster Recovery

Definire procedure per:

- Perdita GitHub Gist
- Corruzione dati
- Deploy errati
- Restore completi

---

## Obiettivi

Massimizzare:

- Recuperabilità
- Integrità
- Disponibilità

---

# 18.30 Availability Target

Disponibilità obiettivo:

```text
99%
```

o superiore.

---

# 18.31 Recovery Target

Ripristino sistema:

```text
< 30 minuti
```

in caso di guasto applicativo.

---

# 18.32 Tecnical Dashboard

Visibile solo agli Admin.

Mostrare:

- Versioni software
- Librerie installate
- Stato dipendenze
- Ambiente runtime

---

# 18.33 Modalità Diagnostica

Supportare:

```text
Diagnostic Mode
```

per troubleshooting avanzato.

---

# 18.34 Continuous Monitoring

Controllare continuamente:

- Storage
- PDF
- AI
- Authentication
- Cache

---

# 18.35 Continuous Quality Verification

Dopo ogni deploy eseguire:

- Health Check
- Smoke Test
- Regression Test Critici

---

# 18.36 Obiettivo Finale

L'infrastruttura deve risultare:

- Semplice
- Economica
- Affidabile
- Facile da gestire

garantendo disponibilità continua alla band e permettendo all'amministratore di monitorare e mantenere l'intero sistema direttamente dall'interfaccia web senza dipendere da strumenti esterni.
