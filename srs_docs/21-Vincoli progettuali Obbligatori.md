# 21. Vincoli Progettuali Obbligatori

## 21.1 Obiettivo

Questa sezione definisce i vincoli architetturali, metodologici e operativi che devono essere rispettati durante l'intero ciclo di vita del progetto.

Tali vincoli hanno priorità superiore rispetto a qualsiasi decisione implementativa.

---

# 21.2 Compatibilità Retroattiva

## Principio

Tutti i dati salvati devono rimanere utilizzabili dalle versioni future del sistema.

---

## Regole

È vietato:

- Rompere la compatibilità AML
- Rompere la compatibilità dei JSON
- Rendere inutilizzabili vecchi repertori
- Rendere inutilizzabili vecchie scalette

---

## Migrazioni

Qualsiasi modifica strutturale deve prevedere:

- Migrazione automatica
- Backup preventivo
- Possibilità di rollback

---

# 21.3 Modifiche Incrementali

Ogni nuova funzionalità deve essere introdotta in modo incrementale.

---

## Obblighi

Ogni modifica deve:

- Preservare le funzionalità esistenti
- Aggiornare i test
- Aggiornare il manuale
- Aggiornare il changelog

---

## Divieti

È vietato:

- Rimuovere funzionalità senza approvazione esplicita
- Modificare workflow consolidati senza documentazione
- Alterare strutture dati senza migrazione

---

# 21.4 Nessuna Regressione

Prima del rilascio ogni modifica deve superare:

- Unit Test
- Functional Test
- Musical Regression Test
- PDF Test
- Export Test
- Security Test

---

## Regola

Se un test critico fallisce:

```text
Release Bloccata
```

---

# 21.5 Architettura Modulare

L'applicazione deve essere organizzata in moduli indipendenti.

---

## Moduli Minimi

```text
Authentication
Music Engine
AML Engine
PDF Engine
Import Engine
Export Engine
Live Mode
Administration
Monitoring
AI Services
```

---

## Obiettivo

Favorire:

- Manutenzione
- Riutilizzo
- Testing
- Evoluzione futura

---

# 21.6 Single Source Of Truth

Tutte le funzionalità devono utilizzare AML come sorgente ufficiale.

---

## Regola

Non devono esistere:

- Copie divergenti
- Formati paralleli
- Duplicazioni permanenti

---

## Flusso

```text
AML
 ↓
Rendering
 ↓
PDF
 ↓
Export
```

---

# 21.7 Git First

Il progetto deve seguire una filosofia Git-centric.

---

## Obblighi

Ogni modifica deve essere associata ad un commit descrittivo.

---

## Formato Commit

Esempio:

```text
feat: aggiunta export MobileSheets
```

```text
fix: correzione trasposizione accordi bemolle
```

---

# 21.8 Logging Obbligatorio

Ogni funzione significativa deve produrre eventi di log.

---

## Livelli

```text
INFO
SUCCESS
WARNING
ERROR
CRITICAL
```

---

## Eventi da Registrare

- Login
- Logout
- Import
- Export
- Salvataggio
- Restore
- Errori

---

# 21.9 Documentazione Continua

Ogni modifica deve aggiornare:

- Changelog
- Manuale
- Test

---

## Divieto

È vietato rilasciare funzionalità non documentate.

---

# 21.10 Automazione Prima della Manualità

Qualsiasi attività ripetitiva deve essere automatizzata quando possibile.

---

## Esempi

- Aggiornamento changelog
- Aggiornamento manuale
- Verifiche pre-release
- Backup

---

# 21.11 Osservabilità Completa

L'amministratore deve poter comprendere cosa sta accadendo nel sistema tramite la sola interfaccia web.

---

## Obiettivo

Ridurre al minimo la necessità di accesso diretto a:

- Streamlit Cloud
- GitHub
- Container
- Console Python

---

# 21.12 Data Preservation

La perdita dati deve essere considerata un evento critico.

---

## Regole

Ogni operazione distruttiva deve prevedere:

- Backup
- Audit Trail
- Possibilità di recupero

---

# 21.13 User Experience First

In caso di conflitto tra:

```text
Eleganza tecnica
```

e

```text
Usabilità
```

deve prevalere l'usabilità.

---

# 21.14 Mobile First

La progettazione UX deve avere come riferimento principale:

- Smartphone Android
- Tablet Android
- iPad

---

## Desktop

Ottimizzato successivamente.

---

# 21.15 Live First

Quando esistono scelte alternative, deve essere favorita la soluzione più affidabile in contesto live.

---

## Priorità

1. Affidabilità
2. Velocità
3. Funzionalità avanzate

---

# 21.16 Indipendenza dall'AI

L'AI deve essere considerata un servizio accessorio.

---

## Divieto

Funzioni critiche non devono dipendere dall'AI.

---

# 21.17 Qualità Minima Accettabile

Una release è considerata valida solo se:

```text
Tutti i test critici = PASS
```

---

# 21.18 Obiettivo Finale

Garantire che il progetto mantenga:

- Coerenza
- Affidabilità
- Evolvibilità
- Manutenibilità

per l'intero ciclo di vita applicativo.

---

# 22. Gestione Costi e Sostenibilità Operativa

## 22.1 Obiettivo

L'infrastruttura deve mantenere costi estremamente contenuti.

La piattaforma deve poter essere utilizzata dalla band senza dipendere da servizi costosi o abbonamenti obbligatori.

---

# 22.2 Filosofia Economica

Principio guida:

```text
Free First
Open Source First
Low Cost Always
```

---

# 22.3 Priorità Tecnologiche

Preferire:

1. Open Source
2. Servizi Gratuiti
3. Servizi Freemium
4. Servizi Premium opzionali

---

# 22.4 Costi Ricorrenti

Qualsiasi funzionalità che comporti costi ricorrenti deve essere:

- Facoltativa
- Disattivabile
- Chiaramente identificata

---

# 22.5 Servizi AI

La configurazione predefinita deve essere:

```text
AI FREE
```

---

## Obiettivo

Evitare dipendenza da:

- Abbonamenti
- Token a consumo
- Servizi a pagamento obbligatori

---

# 22.6 Utilizzo Intelligente dell'AI

L'AI deve essere utilizzata solo quando realmente necessaria.

---

## Evitare AI per

- Trasposizioni
- Parsing accordi
- PDF
- Ricerca tonalità
- Conversioni musicali
- Validazioni

---

## Consentire AI per

- Suggerimenti medley
- Suggerimenti arrangiamento
- Ricerca web
- Supporto documentale

---

# 22.7 Ottimizzazione Chiamate Esterne

Minimizzare:

- API Call
- Token Usage
- Query duplicate

---

## Strategie

- Caching
- Riutilizzo risultati
- Elaborazione locale

---

# 22.8 GitHub Gist

Utilizzare GitHub Gist come storage principale per:

- Ridurre costi
- Semplificare backup
- Evitare database dedicati

---

# 22.9 Streamlit Cloud

Utilizzare Streamlit Community Cloud come piattaforma primaria.

---

## Obiettivo

Massimizzare:

- Gratuità
- Semplicità
- Affidabilità

---

# 22.10 Risorse Computazionali

Ridurre:

- Utilizzo CPU
- Utilizzo RAM
- Tempo elaborazione

---

## Priorità

Favorire algoritmi semplici e deterministici.

---

# 22.11 Caching

Implementare caching per:

- PDF
- Anteprime
- Query
- Render

---

## Benefici

- Riduzione tempi
- Riduzione costi
- Riduzione traffico

---

# 22.12 Monitoraggio Costi

Dashboard amministrativa con stima di:

- Chiamate AI
- Utilizzo storage
- Generazione PDF
- Attività utenti

---

# 22.13 Modalità Emergenza

In caso di indisponibilità di servizi esterni:

Il sistema deve continuare a funzionare senza costi aggiuntivi.

---

# 22.14 Nessun Vendor Lock-In

I dati devono essere sempre esportabili.

---

## Formati Minimi

- AML
- JSON
- PDF
- ChordPro

---

# 22.15 Sostenibilità a Lungo Termine

La piattaforma deve poter rimanere operativa anche nel caso in cui:

- Cambino le quote gratuite AI
- Cambino le politiche Streamlit
- Cambino le API di terze parti

---

## Strategia

Ridurre la dipendenza da servizi esterni.

---

# 22.16 ROI Tecnico

Ogni nuova funzionalità deve essere valutata considerando:

- Complessità
- Beneficio reale
- Costo manutentivo
- Costo operativo

---

# 22.17 Regola Finale

L'applicazione deve poter garantire tutte le funzionalità fondamentali della band con costo operativo prossimo a zero.

I servizi premium devono essere considerati soltanto estensioni facoltative e non prerequisiti per il corretto funzionamento della piattaforma.