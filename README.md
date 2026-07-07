# 🏔️ Mountain Passport – GiraRifugi

**GiraRifugi** è un'applicazione web sviluppata in **Django** che permette agli escursionisti di scoprire rifugi di montagna, prenotare soggiorni, effettuare il check-in tramite codice, raccogliere "timbri" nel proprio passaporto digitale, lasciare recensioni e iscriversi a itinerari guidati organizzati da guide alpine.

Progetto realizzato per l'esame di **Progettazione e Sviluppo Web** — Università di Genova.

---

## 📋 Indice

- [Funzionalità](#-funzionalità)
- [Ruoli utente](#-ruoli-utente)
- [Stack tecnologico](#-stack-tecnologico)
- [Struttura del progetto](#-struttura-del-progetto)
- [Modello dati](#-modello-dati)
- [Installazione e avvio](#-installazione-e-avvio)
- [Note di configurazione](#-note-di-configurazione)
- [Licenza](#-licenza)

---

## ✨ Funzionalità

- **Home dinamica per ruolo**: contenuti, filtri e dashboard diversi a seconda del gruppo dell'utente autenticato
- **Ricerca e filtraggio server-side** dei rifugi per nome, regione e fascia di altitudine, con **paginazione** dei risultati
- **Passaporto digitale**: storico visite, timbri raccolti, punteggio totale (basato sull'altitudine dei rifugi visitati) e attività recenti
- **Check-in tramite codice**: registrazione automatica della visita e assegnazione del timbro
- **Prenotazioni** dei soggiorni presso i rifugi, con validazione delle date e workflow di approvazione/rifiuto da parte del gestore
- **Recensioni e voti** (1–5) lasciabili solo dopo aver effettivamente visitato un rifugio
- **Itinerari guidati**: creazione da parte delle guide alpine e iscrizione da parte degli escursionisti, con gestione dei posti disponibili
- **Eventi** organizzati dai rifugi, filtrabili per titolo, regione e data
- **Preferiti**: possibilità di salvare i rifugi di interesse
- **Pannello amministrativo dedicato** per l'approvazione dei nuovi rifugi inseriti dai gestori e per la creazione di nuovi utenti/ruoli
- **Sessione persistente**: gli ultimi filtri di ricerca utilizzati vengono salvati in sessione
- **Django Admin personalizzata** con liste, filtri, ricerca e azioni custom per ogni modello

## 👥 Ruoli utente

L'accesso alle viste è protetto tramite un decorator custom (`gruppo_richiesto`) basato sui **gruppi Django**, con pagina 403 dedicata in caso di accesso non autorizzato.

| Ruolo | Descrizione |
|---|---|
| **Escursionista** | Naviga i rifugi, prenota, fa check-in, scrive recensioni, si iscrive agli itinerari, gestisce preferiti e profilo |
| **GestoreRifugio** | Gestisce i propri rifugi (creazione/modifica), gli eventi collegati e approva/rifiuta le prenotazioni ricevute |
| **GuidaAlpina** | Crea, modifica ed elimina i propri itinerari guidati |
| **Admin** | Approva i rifugi in attesa, modifica dati sensibili (es. altitudine), crea nuovi utenti e assegna i ruoli |

> I gruppi `Escursionista`, `GestoreRifugio`, `GuidaAlpina` e `Admin` devono esistere nel database (vedi [Note di configurazione](#-note-di-configurazione)).

## 🛠️ Stack tecnologico

- **Backend**: Python, Django
- **Frontend**: HTML, CSS (custom, senza framework), JavaScript
- **Database**: SQLite
- **Autenticazione**: sistema built-in di Django (`django.contrib.auth`)

## 📁 Struttura del progetto

```
girarifugi/
├── girarifugi/           # Configurazione del progetto (settings, urls, wsgi/asgi)
├── rifugi/                # App principale
│   ├── models.py          # Entità del dominio
│   ├── views.py            # Viste pubbliche, ristrette e dashboard per ruolo
│   ├── urls.py
│   ├── admin.py            # Personalizzazione Django Admin
│   └── migrations/
├── templates/              # Template HTML organizzati per sezione
│   ├── base.html
│   ├── home.html
│   ├── registration/       # Login e registrazione
│   └── rifugi/              # Dettaglio rifugio, dashboard, passaporto, pannello admin...
├── static/
│   ├── css/                 # Fogli di stile custom per pagina
│   └── banner.jpg
├── media/                   # Immagini caricate (rifugi, eventi)
└── manage.py
```

## 🗃️ Modello dati

- **Rifugio**: struttura ricettiva (nome, località, coordinate, altitudine, tipo, stato di approvazione, gestore associato)
- **Visita** / **Timbro**: registrano il check-in di un escursionista presso un rifugio
- **Prenotazione**: richiesta di soggiorno con date, numero ospiti e stato (in attesa/approvata/rifiutata)
- **Recensione**: voto e commento di un escursionista su un rifugio visitato
- **Preferito**: relazione tra escursionista e rifugio salvato
- **Itinerario** / **IscrizioneItinerario**: percorso guidato creato da una guida alpina e relative iscrizioni
- **Evento** / **IscrizioneEvento**: evento organizzato da un rifugio e relative iscrizioni

## 📄 Licenza

Distribuito con licenza **MIT**. Vedi [LICENSE](./LICENSE) per maggiori dettagli.
