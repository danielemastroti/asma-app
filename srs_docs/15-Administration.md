# 15. Administration

## 15.1 Obiettivo

La sezione Administration rappresenta il centro di controllo dell'intera piattaforma.

Deve consentire all'amministratore di:

- Gestire utenti
- Gestire configurazioni
- Monitorare il sistema
- Eseguire backup
- Effettuare restore
- Amministrare integrazioni
- Consultare log tecnici
- Gestire rilasci applicativi

Tutte le funzioni descritte in questa sezione devono essere accessibili esclusivamente agli utenti con ruolo:

```text
ADMIN
```

---

# 15.2 Dashboard Amministrativa

La dashboard amministrativa deve fornire una vista globale dello stato del sistema.

Mostrare:

- Utenti attivi
- Brani totali
- Repertori totali
- Scalette totali
- Eventi live
- Stato GitHub Gist
- Stato Google Authentication
- Stato AI
- Stato PDF Engine

---

## Indicatori Rapidi

Visualizzare:

```text
ONLINE
```

oppure

```text
WARNING
```

oppure

```text
ERROR
```

per ogni componente principale.

---

# 15.3 Gestione Utenti

## Funzioni Disponibili

- Aggiungi utente
- Disabilita utente
- Elimina utente
- Promuovi ad Admin
- Revoca privilegi Admin

---

## Informazioni Utente

Per ogni utente visualizzare:

- Nome
- Email Google
- Ruolo
- Data registrazione
- Ultimo accesso
- Ultimo device utilizzato

---

## Utenti Attivi

Visualizzare:

```text
Connessi Ora
```

con:

- Nome
- Data login
- Device

---

# 15.4 Ruoli

## Admin

Accesso totale.

---

## Editor

Accesso operativo.

---

## Futuri Ruoli

Architettura predisposta per:

- Read Only
- Guest
- Live Performer

---

# 15.5 Configurazione Sistema

Area dedicata alle impostazioni generali.

---

## Parametri Applicativi

Configurabili:

- Timeout lock editing
- Timeout sessione
- Numero revisioni
- Frequenza backup
- Dimensione cache

---

## Parametri Musicali

Configurabili:

- Armatura preferita
- Notazione default
- Font PDF
- Font modalità palco

---

# 15.6 Gestione AI

L'amministratore può configurare:

## AI OFF

Disabilitata.

---

## AI FREE

Predefinita.

Utilizza esclusivamente servizi gratuiti.

---

## AI PREMIUM

Configurabile.

Richiede credenziali dedicate.

---

## Regola Fondamentale

L'applicazione deve continuare a funzionare senza AI.

---

# 15.7 Configurazione API

Area dedicata alla gestione chiavi.

Supportare:

- Gemini
- Google
- GitHub
- Streamlit Cloud

---

## Sicurezza

Le chiavi:

- Non devono mai essere mostrate in chiaro
- Devono essere cifrate
- Devono essere mascherate

Esempio:

```text
AIza*****************
```

---

# 15.8 Gestione GitHub Gist

Visualizzare:

- Stato connessione
- Ultima sincronizzazione
- Ultimo errore

---

## Operazioni

- Test connessione
- Sincronizzazione forzata
- Verifica consistenza dati

---

# 15.9 Backup

## Backup Manuale

Consentire la creazione immediata di snapshot.

---

## Backup Automatico

Supportare:

- Giornaliero
- Settimanale
- Prima dei restore
- Prima degli aggiornamenti

---

## Contenuti Inclusi

- Repertori
- Brani
- Scalette
- Eventi
- Configurazioni
- Utenti

---

# 15.10 Restore

Supportare:

- Restore completo
- Restore selettivo

---

## Restore Selettivo

Esempi:

- Singolo repertorio
- Singolo brano
- Singola scaletta

---

## Sicurezza Restore

Creare sempre un backup prima del restore.

---

# 15.11 Gestione Cestino

Visualizzare elementi eliminati.

Supportare:

- Ripristino
- Eliminazione definitiva

---

## Conservazione

Periodo minimo:

```text
30 giorni
```

---

# 15.12 Gestione Tag Personalizzati

Funzione esclusiva Admin.

---

## Creazione Tag

Esempio:

```text
{note:}
```

```text
{voice:}
```

```text
{guitar:}
```

```text
{drums:}
```

---

## Proprietà Tag

Configurabili:

- Nome
- Colore
- Stile
- Comportamento PDF
- Comportamento Modalità Palco

---

## Esempio

Input:

```text
{note:Tutti insieme}
```

Output:

```text
Tutti insieme
```

---

# 15.13 Changelog Management

Il changelog deve essere aggiornato automaticamente.

---

## Regola

Massimo una versione al giorno.

Formato:

```text
AAAA.MM.GG
```

---

## Sezioni

- New Features
- Bug Fixes
- Improvements
- Security

---

# 15.14 Manuale Applicativo

Generato automaticamente.

---

## Aggiornamento Automatico

Ogni nuova funzionalità deve produrre aggiornamento del manuale.

---

## Export

Supportare:

- PDF
- HTML

---

# 15.15 Monitoring Dashboard

Visualizzare:

- Stato applicazione
- Stato storage
- Stato autenticazione
- Stato AI
- Stato PDF Engine

---

# 15.16 Health Check

Endpoint:

```text
/health
```

Output:

```json
{
  "status":"healthy"
}
```

---

## Compatibilità

Supportare:

- UptimeRobot
- Pingdom
- StatusCake

---

# 15.17 Uptime

Visualizzare:

- Ultime 24 ore
- Ultimi 7 giorni
- Ultimi 30 giorni

---

## Percentuale Disponibilità

Esempio:

```text
99.98%
```

---

# 15.18 Modalità Manutenzione

Consentire:

```text
Maintenance Mode
```

---

## Funzioni

- Blocca accessi utenti
- Consenti accesso Admin
- Mostra messaggio manutenzione

---

# 15.19 Audit Trail

Registrare:

- Login
- Logout
- Modifiche
- Restore
- Eliminazioni
- Backup

---

## Audit Immutabile

Gli eventi non devono essere modificabili.

---

# 15.20 Versione Applicazione

Sempre visibile.

Esempio:

```text
ASMA 2026.11.05
```

---

## Informazioni Tecniche

Visualizzare:

- Commit Git
- Data Deploy
- Python Version
- Streamlit Version

---

# 15.21 Modalità Sviluppatore

Visibile solo agli Admin.

---

## Informazioni Disponibili

- Dipendenze installate
- Dipendenze mancanti
- Versioni librerie
- Variabili ambiente validate

---

# 15.22 Gestione Cache

Permettere:

- Svuota Cache
- Rigenera Cache
- Verifica Integrità Cache

---

# 15.23 Gestione PDF

Operazioni disponibili:

- Rigenera PDF
- Pulisci Cache PDF
- Verifica Integrità PDF

---

# 15.24 Gestione Lock

Visualizzare:

- Brani bloccati
- Utente
- Ora blocco

---

## Funzioni

- Rimozione lock manuale
- Sblocco forzato

---

# 15.25 Scheduler

Visualizzare attività pianificate.

Esempi:

- Backup
- Pulizie cache
- Rigenerazioni PDF
- Controlli integrità

---

# 15.26 Gestione Errori

Visualizzare:

- Errori aperti
- Warning
- Errori risolti

---

## Filtri

- Data
- Utente
- Modulo
- Gravità

---

# 15.27 Configurazione Device

L'Admin può definire:

- Profili di default
- Profili consigliati
- Parametri PDF

---

# 15.28 Sicurezza

Visualizzare:

- Login falliti
- Attività sospette
- Tentativi non autorizzati

---

# 15.29 Obiettivo Finale

L'Amministratore deve essere in grado di gestire e diagnosticare il 95% dei problemi dell'applicazione direttamente dalla UI, senza necessità di accedere a:

- Streamlit Cloud
- Console Python
- GitHub
- Log del Container

garantendo operatività, monitoraggio e manutenzione centralizzati.
