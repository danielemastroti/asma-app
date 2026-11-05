# 12. Live Mode

## 12.1 Obiettivo

La Modalità Palco rappresenta una delle funzionalità più importanti dell'intera piattaforma.

Deve consentire ai musicisti di eseguire brani durante prove e concerti minimizzando:

- Interazioni manuali
- Errori di lettura
- Perdita di tempo
- Distrazioni

La modalità deve essere ottimizzata per:

- Smartphone Android
- Tablet Android
- iPad
- iPad Pro

---

## 12.2 Accesso

La modalità palco deve poter essere attivata da:

- Scaletta
- Brano singolo
- Medley
- Evento Live

Accesso rapido disponibile dalla Home Dashboard.

---

## 12.3 Modalità Full Screen

All'attivazione:

- Nascondere menu
- Nascondere elementi amministrativi
- Nascondere toolbar non necessarie

Massimizzare l'area disponibile per:

- Accordi
- Testo
- Indicazioni musicali

---

## 12.4 Theme Stage

Supportare almeno:

### Dark Theme

```text
Sfondo Nero
Testo Bianco
Accordi Giallo Chiaro
```

---

### Light Theme

```text
Sfondo Bianco
Testo Nero
```

---

### Custom Theme

Configurabile dall'utente.

---

## 12.5 Font

Configurabili per:

- Testo
- Accordi
- Tag
- Annotazioni

Dimensioni indipendenti.

---

## 12.6 Scroll Automatico

Funzione principale della modalità palco.

L'utente deve poter:

- Avviare
- Fermare
- Riprendere
- Accelerare
- Rallentare

lo scrolling.

---

## 12.7 Velocità Scroll

Configurabile:

```text
Molto Lenta
Lenta
Media
Veloce
Molto Veloce
```

oppure tramite slider.

---

## 12.8 Profili Scroll

Salvabili nel profilo utente.

Esempio:

```text
Prove
```

```text
Live
```

```text
Acustico
```

---

## 12.9 Scorrimento Manuale

Sempre disponibile.

Supportare:

- Touch
- Swipe
- Mouse
- Tastiera
- Pedali Bluetooth compatibili

---

## 12.10 Supporto Pedali Bluetooth

Architettura predisposta per:

- AirTurn
- PageFlip
- IK Multimedia BlueTurn
- Dispositivi equivalenti

Funzioni:

- Pagina successiva
- Pagina precedente
- Avvio scroll
- Pausa scroll

---

## 12.11 Visualizzazione Scaletta

Visualizzare in alto:

```text
Posizione brano corrente
```

Esempio:

```text
Brano 4 di 18
```

---

## 12.12 Navigazione Rapida

Consentire:

```text
Brano precedente
```

```text
Brano successivo
```

senza uscire dalla modalità palco.

---

## 12.13 Indicazione Tonalità

Sempre visibile.

Esempio:

```text
Tonalità: SOL
```

oppure

```text
Tonalità: G
```

---

## 12.14 Indicazione BPM

Sempre visibile.

Esempio:

```text
92 BPM
```

---

## 12.15 Indicazione Metro

Visualizzare:

```text
4/4
```

```text
3/4
```

```text
6/8
```

---

## 12.16 Metronomo Integrato

Opzionale.

Funzioni:

- On/Off
- Volume
- BPM automatico
- BPM personalizzato

---

## 12.17 Modalità Medley

Supportare medley continui.

Visualizzare:

```text
Inizio Medley
```

e

```text
Cambio Brano
```

in modo evidente.

---

## 12.18 Modalità Assolo

Le sezioni riconosciute come:

```text
Progressioni Armoniche
```

devono essere evidenziate.

Esempio:

```text
C | Am | F | G
```

renderizzate come giro armonico.

---

## 12.19 Evidenziazione Sezioni

Renderizzare in modo differente:

- Intro
- Strofa
- Ritornello
- Bridge
- Solo
- Outro

---

## 12.20 Modalità Contrasto Elevato

Per utilizzo sotto illuminazione intensa.

Ottimizzata per:

- Luce solare
- Palchi all'aperto
- Tablet luminosi

---

## 12.21 Modalità Notturna

Ottimizzata per:

- Palchi scuri
- Club
- Locali

Ridurre l'abbagliamento.

---

## 12.22 Annotazioni Condivise

Visualizzabili in modalità palco.

Esempio:

```text
Entrare tutti insieme
```

---

## 12.23 Annotazioni Private

Visualizzare solo al proprietario.

Esempio:

```text
Ricordati il chorus
```

---

## 12.24 Gestione TAG

Interpretare automaticamente:

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

## 12.25 Cambio Tonalità Live

Consentire trasposizione immediata.

Esempio:

```text
-1 tono
```

```text
+1 tono
```

senza uscire dalla modalità palco.

---

## 12.26 Cambio Notazione Live

Supportare:

```text
ITA
```

```text
INT
```

in tempo reale.

Esempio:

```text
DO -> C
```

```text
LA- -> Am
```

---

## 12.27 Stato Connessione

Visualizzare sempre:

```text
ONLINE
```

oppure

```text
OFFLINE
```

---

## 12.28 Cache Offline

In assenza di rete deve essere possibile accedere a:

- Ultime scalette
- Ultimi repertori
- Ultimi PDF
- Ultimi brani sincronizzati

---

## 12.29 Protezione Sleep

Prevedere modalità:

```text
Keep Screen Awake
```

durante la modalità palco.

---

## 12.30 Sicurezza Live

Le funzioni amministrative non devono essere visibili durante la modalità palco.

---

## 12.31 Statistiche Utilizzo

Registrare:

- Brani eseguiti
- Durata utilizzo
- Numero aperture
- Eventi associati

---

## 12.32 Salvataggio Stato

In caso di chiusura accidentale:

- Ripristinare posizione
- Ripristinare brano corrente
- Ripristinare scaletta

all'accesso successivo.

---

## 12.33 Requisiti Prestazionali

Tempo massimo apertura modalità palco:

```text
< 2 secondi
```

Tempo massimo cambio brano:

```text
< 1 secondo
```

---

## 12.34 Obiettivo Finale

La modalità palco deve sostituire completamente:

- Fogli cartacei
- PDF statici
- Raccolte manuali

fornendo un'esperienza stabile, leggibile e affidabile durante qualsiasi esibizione live.