# WOACC Tracker v1.1

Tracker risultati per Assetto Corsa EVO basato sui JSON generati dal dedicated server.

## Novità v1.1

- Supporto reverse proxy sotto sottocartella, es. `https://woacc.zapto.org/tracker/`.
- Dettaglio pilota con:
  - best lap;
  - giro potenziale, calcolato con migliori S1+S2+S3 validi;
  - media giri validi;
  - media di tutti i giri.
- Annuncio record evento su Discord per singola cartella monitorata:
  - non retroattivo;
  - la finestra record parte quando attivi la spunta;
  - il primo giro valido diventa record iniziale;
  - i successivi miglioramenti vengono annunciati via webhook Discord.
- Pagina web `Record`.
- Tema personalizzabile da launcher:
  - font;
  - colori principali;
  - accento;
  - sfondo/card/testi.
- Database aggiornato con migrazioni automatiche.

## Avvio rapido

```bash
pip install -r requirements.txt
python run_tracker.py
```

## Caddy sotto /tracker

Esempio Caddyfile:

```caddyfile
woacc.zapto.org {
    redir /tracker /tracker/

    handle_path /tracker/* {
        reverse_proxy 127.0.0.1:5055 {
            header_up X-Forwarded-Prefix /tracker
        }
    }

    handle_path /accweb/* {
        reverse_proxy 127.0.0.1:8090
    }

    handle {
        reverse_proxy 127.0.0.1:9001
    }
}
```

Nel launcher imposta `Base path reverse proxy` a:

```txt
/tracker
```

## Regole dati

- Server logico = `server_name + track_name`.
- Piloti accorpati via `player_id` Steam, se presente.
- Nome pilota aggiornato con l'ultimo nome rilevato.
- Classifiche e statistiche separate per `pilota + auto`.
- Sessioni senza giri non importate nel DB operativo.
- FP/Q = classifica tempi.
- Race = ordine arrivo da standings JSON.
- Condizioni wet/dry e storico penalità dettagliato non risultano esportati nei JSON testati.

## Discord record

Per ogni cartella monitorata puoi attivare `Configura record Discord`.
Quando attivi la spunta parte una nuova finestra record evento. Non vengono annunciati record storici già presenti.


## WOACC Bridge API

Il Tracker può funzionare come collector remoto per WOACC.
WOACC può leggere l'indice delle sessioni e scaricare i JSON originali completi.

Endpoint principali:

- `GET /api/woacc/ping`
- `GET /api/woacc/sessions`
- `GET /api/woacc/session/<session_id>/original.json`

Se il Tracker gira sotto Caddy con `base_path` `/tracker`, gli endpoint pubblici diventano:

- `https://tuodominio.it/tracker/api/woacc/ping`
- `https://tuodominio.it/tracker/api/woacc/sessions`

Parametri utili per `/api/woacc/sessions`:

- `status=imported` default, mostra solo sessioni importate correttamente
- `status=all` mostra anche skipped/error
- `after=YYYY-MM-DDTHH:MM:SS` mostra solo file importati dopo quella data
- `limit=1000` limite risultati, massimo 5000

Sicurezza opzionale in `config.json`:

```json
"woacc_api_enabled": true,
"woacc_api_key": "metti-una-chiave-lunga"
```

Se `woacc_api_key` è valorizzata, WOACC deve chiamare gli endpoint con header:

```http
X-WOACC-API-Key: metti-una-chiave-lunga
```

## v12.1 - WOACC branch / bridge improvements

### Multilingua
- Aggiunto supporto lingua italiano/inglese nella web UI.
- Le traduzioni sono file esterni in `woacc_tracker/i18n/`.
- Per aggiungere una lingua basta copiare `it.json` o `en.json`, rinominarlo ad esempio `fr.json`, tradurre i valori e riavviare il Tracker.
- La lingua predefinita può essere impostata in `config.json` con:

```json
"language": "it"
```

### Classifica filtrata
Nuova pagina web:

```text
/leaderboard
```

Permette di generare una classifica aggregata filtrando:
- nome server/campionato, ad esempio `season IV`;
- pista tramite menu a tendina, popolato in base ai server filtrati;
- tipo sessione opzionale.

Esempio:

```text
/leaderboard?server_q=season%20IV&track=COTA
```

La classifica prende il miglior giro valido per ogni coppia pilota/auto nelle sessioni filtrate.

### Categoria pilota
Se il JSON originale contiene una categoria pilota, viene mostrata accanto al nome/risultato come badge:
- AM
- SILVER
- PRO
- PRO-AM

Il parser prova a rilevarla da chiavi comuni come `category`, `driver_category`, `cupCategory`, `license`, `class`, `rating`.

### WOACC Bridge API
Restano disponibili gli endpoint per fare importare a WOACC i JSON originali completi:

```text
GET /api/woacc/ping
GET /api/woacc/sessions
GET /api/woacc/session/<session_id>/original.json
```


## Fix v12.1.1

- Corretto il cambio lingua sotto Caddy/subpath (`/tracker`): il redirect resta dentro il Tracker e non torna più alla root WOACC.

## Lingua desktop e web

La lingua è ora una preferenza globale del Tracker:

- dalla Web App puoi cambiarla dal selettore in alto;
- dalla Desktop App puoi cambiarla nella scheda **Generale / General**;
- il valore viene salvato in `config.json` con la chiave `language`;
- i testi sono caricati da vocabolari esterni in `woacc_tracker/i18n/`.

Per aggiungere una nuova lingua:

1. copia `woacc_tracker/i18n/en.json`;
2. rinominalo, per esempio `fr.json`;
3. traduci i valori lasciando invariate le chiavi;
4. riavvia il Tracker.

## v12.1.3 - Share links

All web pages now include a shared **Share** button. The generated link keeps the full current URL, including query parameters.

This is especially useful for pre-qualifying leaderboards. Example:

```text
/tracker/leaderboard?server_q=season%20IV&track=COTA
```

When this URL is shared, users open the same filtered leaderboard directly without setting filters manually.


## v12.1.4

- Allargata la pagina Leaderboard a tutta la larghezza disponibile.
- Tabella classifica più compatta, con colonne ottimizzate e scroll orizzontale solo come fallback.
- Tooltip con valore completo per campi lunghi come server, pista, auto e pilota.

---

## WOACC Tracker v13 - WOACC Bridge API

Version 13 enables the WOACC Bridge API by default so ACC_JSON_Monitor_Plus 2 can import EVO tracker data into a central WOACC installation.

Default behavior:

- Bridge API: enabled by default
- Shared bridge key: `WOACC-EVO-BRIDGE-V13-ACCJSONMONITORPLUS2`
- API endpoints:
  - `/api/woacc/ping`
  - `/api/woacc/sessions`
  - `/api/woacc/session/<id>/original.json`

The desktop app includes a checkbox:

**Share data with WOACC (Bridge API enabled)**

Disable it if you do not want ACC_JSON_Monitor_Plus 2 to read this tracker.

ACC_JSON_Monitor_Plus 2 must send the shared key using:

```http
X-WOACC-API-Key: WOACC-EVO-BRIDGE-V13-ACCJSONMONITORPLUS2
```



## WOACC community integration

The desktop app includes a **Join the WOACC community** button. It opens a local information page explaining the WOACC philosophy and how a community can request inclusion in the global WOACC ecosystem.

The WOACC Bridge API is enabled by default and protected with the shared ACC_JSON_Monitor_Plus 2 key. Users can disable data sharing from the desktop app by unchecking **Share data with WOACC**.

Config fields you may customize before publishing your build:

```json
"woacc_main_url": "https://woacc.zapto.org/",
"woacc_discord_url": "https://discord.com/channels/@me",
"woacc_discord_contact": "Fabio / WOACC",
"woacc_request_message": "Ciao Fabio, vorrei collegare il mio WOACC Tracker EVO al WOACC globale. Indirizzo tracker da aggiungere: "
```
