# WOACC EVO Tracker - Guida completa di installazione e configurazione

Questa guida raccoglie installazione, configurazione e uso delle funzioni storiche e delle ultime novita di WOACC EVO Tracker.

WOACC EVO Tracker e' un tracker locale/community per i risultati JSON generati dai server dedicati di Assetto Corsa EVO. Importa le sessioni, costruisce pagine web consultabili dalla community, gestisce record, notifiche Discord, recap, condizioni server, API Bridge e leaderboard live basata sui log del dedicated server.

> Progetto community-made. Non e' software ufficiale Kunos.

---

## 1. Requisiti

- Windows.
- Assetto Corsa EVO Dedicated Server.
- Una cartella server con i JSON risultati, ad esempio:

```text
servers/server_1/result
```

- Facoltativo ma consigliato: il file log del dedicated server:

```text
servers/server_1/serverConfig/Assetto Corsa EVO Server.txt
```

- Per la versione da sorgente: Python 3.10 o superiore.
- Per la versione EXE: non serve installare Python.
- Browser web per aprire l'interfaccia del tracker.
- Facoltativo: webhook Discord.
- Facoltativo: Caddy o altro reverse proxy se si vuole pubblicare il tracker con un dominio e un base path tipo `/tracker`.

---

## 2. Installazione da EXE

1. Scarica lo ZIP della release.
2. Estrai lo ZIP in una cartella scrivibile, per esempio:

```text
C:\WOACC_Tracker
```

3. Avvia:

```text
WOACC Tracker.exe
```

4. Se Windows mostra SmartScreen, conferma l'avvio solo se il file arriva dalla release ufficiale che hai scaricato.
5. Alla prima apertura configura la scheda `Generale`, poi aggiungi almeno una cartella monitorata.

Consiglio: evita di avviare il programma dentro lo ZIP. Estrai sempre tutto prima.

---

## 3. Installazione da sorgente

Apri un terminale nella cartella del progetto e installa le dipendenze:

```powershell
python -m pip install -r requirements.txt
python run_tracker.py
```

Se Windows non riconosce `python`, installa Python dal sito ufficiale e abilita l'opzione `Add Python to PATH`, oppure usa il percorso completo dell'eseguibile Python.

---

## 4. Prima configurazione desktop

Nella scheda `Generale` trovi le impostazioni principali.

### Nome community

Nome mostrato nel tracker web e usato come contesto generale.

### Porta web app

Porta locale su cui gira il tracker, per esempio:

```text
5055
```

L'indirizzo locale sara':

```text
http://127.0.0.1:5055
```

### Intervallo scansione

Ogni quanti secondi il tracker controlla le cartelle dei JSON risultati.

Esempio consigliato:

```text
60
```

### Public URL

Indirizzo pubblico usato per creare link condivisibili e link Discord.

Esempi:

```text
https://woacc.zapto.org/
http://TUO_IP_PUBBLICO:5055
```

### Base path reverse proxy

Usalo se il tracker e' pubblicato sotto un percorso, ad esempio:

```text
/tracker
```

Con:

```text
Public URL: https://woacc.zapto.org/
Base path: /tracker
```

i link diventano:

```text
https://woacc.zapto.org/tracker/session/123
```

### Lingua

Lingue disponibili:

- Italiano
- English
- Francais
- Espanol

### Accesso remoto / LAN

Se attivo, il tracker ascolta anche sulla rete locale con bind `0.0.0.0`.

Usalo se vuoi raggiungerlo da altri PC in LAN o dietro reverse proxy.

### Share data with WOACC

Abilita la WOACC Bridge API per strumenti esterni o collector globali.

Il JSON originale della sessione resta invariato.

### Protezione con password

Puoi proteggere la web app con password. Lascia vuoto il campo nuova password se non vuoi cambiarla.

---

## 5. Aggiungere un server monitorato

Apri la scheda `Cartelle monitorate`.

Per ogni server:

1. Premi `Aggiungi`.
2. Seleziona la cartella dei JSON risultati:

```text
...\servers\server_1\result
```

3. Dai un nome riconoscibile al server/sorgente.
4. Quando richiesto, seleziona anche il file log del server:

```text
...\servers\server_1\serverConfig\Assetto Corsa EVO Server.txt
```

Il file log e' facoltativo. Se non lo configuri, il tracker continua a importare i JSON come prima, ma non puo' leggere condizioni server e leaderboard live.

---

## 6. Dove trovare cartella result e file log

Ogni server dedicato di Assetto Corsa EVO ha una propria cartella. Il punto di partenza piu semplice e' cercare la cartella dove si trova l'eseguibile:

```text
AssettoCorsaEVOServer.exe
```

Esempio:

```text
C:\Users\TUO_UTENTE\Desktop\server_1\AssettoCorsaEVOServer.exe
```

Oppure, se usi una struttura con piu server:

```text
C:\Users\TUO_UTENTE\Desktop\woacc_server_manager\servers\server_1\AssettoCorsaEVOServer.exe
C:\Users\TUO_UTENTE\Desktop\woacc_server_manager\servers\server_2\AssettoCorsaEVOServer.exe
```

Dentro la stessa cartella dell'eseguibile, o nelle sue sottocartelle, trovi normalmente le cartelle importanti per il tracker.

### Cartella dei risultati JSON

La cartella da monitorare per i risultati e':

```text
result
```

Percorso tipico:

```text
...\server_1\result
```

Esempio completo:

```text
C:\Users\TUO_UTENTE\Desktop\woacc_server_manager\servers\server_1\result
```

Dentro questa cartella il dedicated server crea file simili a:

```text
results_20260607_150733_practice.json
results_20260607_160416_qualifying.json
results_20260607_170205_race.json
```

Questa e' la cartella che devi selezionare quando WOACC Tracker chiede il percorso dei JSON risultati.

### File log del server

Il file log da selezionare e':

```text
Assetto Corsa EVO Server.txt
```

Percorso tipico:

```text
...\server_1\serverConfig\Assetto Corsa EVO Server.txt
```

Esempio completo:

```text
C:\Users\TUO_UTENTE\Desktop\woacc_server_manager\servers\server_1\serverConfig\Assetto Corsa EVO Server.txt
```

Questo file contiene le righe scritte dal dedicated server durante l'avvio e durante la sessione. WOACC Tracker lo usa per leggere condizioni, stato server, player online e leaderboard live.

### Regola pratica

Per ogni server EVO devi associare:

```text
server_1\result
server_1\serverConfig\Assetto Corsa EVO Server.txt
```

Per il server successivo:

```text
server_2\result
server_2\serverConfig\Assetto Corsa EVO Server.txt
```

Non usare il log di un server diverso dalla cartella `result` selezionata, altrimenti condizioni e leaderboard live potrebbero riferirsi al server sbagliato.

### Se il file log non si vede

Se non trovi `Assetto Corsa EVO Server.txt`:

- avvia almeno una volta il dedicated server;
- controlla la cartella `serverConfig`;
- verifica di essere nella cartella del server corretto, cioe' quella vicina a `AssettoCorsaEVOServer.exe`;
- se il server manager usa cartelle separate, entra nella cartella del singolo server, non nella cartella principale del manager.

---

## 7. Selezione e sincronizzazione del log server

Ogni sorgente puo' avere associato il file:

```text
Assetto Corsa EVO Server.txt
```

Questo file viene letto per:

- condizioni meteo/sessione;
- server online/offline;
- numero player online;
- tipo sessione live;
- leaderboard live;
- settori live.

### Seleziona log server

Il pulsante serve a impostare o cambiare il percorso del file log.

### Sincronizza log server

Questa funzione va usata a server dedicato spento.

Quando premi `Sincronizza log server`, il tracker:

1. mostra un avviso per ricordare di spegnere il dedicated server;
2. rinomina il log attuale con un numero progressivo, ad esempio:

```text
Assetto Corsa EVO Server_001.txt
```

3. crea un nuovo `Assetto Corsa EVO Server.txt` vuoto.

Questo evita blocchi o rallentamenti quando un log vecchio e' diventato molto grande.

Se il server e' acceso, il file potrebbe essere bloccato da Windows e l'operazione potrebbe fallire.

---

## 8. Import dei JSON risultati

Il tracker controlla automaticamente le cartelle monitorate e importa i nuovi file:

```text
results_YYYYMMDD_HHMMSS_practice.json
results_YYYYMMDD_HHMMSS_qualifying.json
results_YYYYMMDD_HHMMSS_race.json
```

Puoi anche premere `Importa ora` per forzare un controllo manuale.

I JSON originali generati dal dedicated server non vengono modificati. Il tracker salva i dati nel proprio database e mantiene compatibilita con applicazioni esterne che leggono i file originali.

Se un import fallisce, nella pagina/log diagnostici puoi vedere l'errore e usare `Retry`.

---

## 9. Condizioni server

Se il file `Assetto Corsa EVO Server.txt` e' configurato, quando viene importato un nuovo JSON il tracker cerca nel log la `Season Definition` corretta e associa alla sessione:

- meteo;
- temperatura aria;
- pioggia/precipitazione;
- bagnato pista;
- vento;
- umidita;
- grip pista;
- gomma/rubber;
- marbles.

Le condizioni vengono mostrate in forma compatta:

```text
DRY | 23.4C | G 1.00 | WET 0.00 | WIND 0.0
WET | 18.2C | G 0.72 | WET 0.40 | WIND 1.2
WET | RAIN 0.25 | 18.2C | G 0.65 | WET 0.60 | WIND 2.5
```

Significato:

- `DRY`: pista asciutta.
- `WET`: pista bagnata.
- `RAIN`: pioggia attiva.
- `C`: temperatura aria.
- `G`: grip pista.
- `WET`: valore bagnato pista.
- `WIND`: vento.

Nota importante: se il log e' stato svuotato mentre il server era gia acceso, potrebbe mancare la `Season Definition`. In quel caso le condizioni possono restare vuote fino al riavvio del server o alla prossima definizione scritta nel log.

---

## 10. Pagine web principali

### Home

Mostra riepilogo community, server disponibili e ultime sessioni rilevate.

### Server

Mostra:

- server monitorati;
- server online;
- tipo sessione live;
- pista;
- condizioni;
- player online;
- link alla leaderboard live.

### Sessioni

Archivio di tutte le sessioni importate, con filtri per server, pista, tipo sessione e condizioni asciutto/bagnato.

### Dettaglio sessione

Mostra classifica della sessione, piloti, categorie, auto, tempi, giri e condizioni associate.

### Classifica

Classifica filtrata per server, pista e condizioni.

### Record

Record storici della community, filtrabili anche per asciutto/bagnato quando il dato e' disponibile.

### Licenze

Pagina dedicata al sistema licenze piloti.

### WOACC

Pagina dedicata a condivisione/API/bridge quando abilitate.

---

## 11. Server online e leaderboard live

La lettura live e' opzionale per ogni server.

Per abilitarla:

1. apri `Cartelle monitorate`;
2. seleziona il server;
3. imposta il file `Assetto Corsa EVO Server.txt`;
4. attiva la spunta `Leaderboard live`.

Se la spunta e' disattivata, il tracker non genera la leaderboard live per quel server.

### Cosa viene aggiornato

Il tracker aggiorna periodicamente:

- quanti server sono attivi;
- quanti player sono online;
- schede server online;
- leaderboard live quando la pagina viene consultata.

La pagina leaderboard live si aggiorna automaticamente ogni 5 secondi.

### Ottimizzazione lettura log

Per ridurre il carico:

- i dati leggeri di stato server vengono letti per mostrare online/player;
- i dati pesanti della leaderboard vengono letti solo quando la pagina/API live viene richiesta;
- la leaderboard usa cache temporanea;
- la frequenza della pagina live e' 5 secondi;
- la lettura e' attiva solo sui server con leaderboard live abilitata.

Questo e' importante per community con molti server online.

### Prove libere e qualifica

In sessioni Practice e Qualifying la leaderboard live ordina i piloti per miglior tempo sul giro rilevato nel log.

Mostra:

- posizione;
- pilota;
- auto;
- miglior giro;
- distacco;
- giri totali;
- ultimo giro;
- settori S1, S2, S3;
- stato pilota.

Premendo il nome del pilota si puo' consultare la lista dei giri rilevati.

### Gara

Per le sessioni Race la logica live resta in attesa di dati piu sicuri sui log gara.

L'obiettivo e' ordinare per posizione live, ma va implementato solo quando il formato dei log gara sara' verificato con certezza.

### Piloti online, offline e non confermati

La leaderboard distingue:

- `Online`: pilota confermato presente o con attivita recente.
- `Offline`: pilota uscito nella sessione corrente quando il log contiene una riga di disconnessione.
- `Non confermato`: il log non contiene abbastanza informazioni per sapere con certezza se il pilota e' ancora dentro.

Il filtro della leaderboard permette di vedere tutti, solo online o solo offline.

### Cambio sessione

Quando il log indica un cambio sessione, la leaderboard viene riavviata e considera solo i dati della sessione attuale.

Il log del dedicated server puo' restare nello stesso file per giorni; per questo il tracker usa marker di sessione per evitare di mostrare piloti e giri di sessioni vecchie.

### Validita dei giri live

La leaderboard live e' provvisoria.

Il log non espone sempre in modo affidabile i track limits o tutte le cause di giro invalidato. Il JSON finale resta la fonte piu sicura per validi/non validi.

Per questo i tempi live vanno considerati candidati fino all'arrivo del JSON ufficiale della sessione.

---

## 12. Discord

La configurazione Discord e' nella scheda dedicata.

Prima di premere `Setup Discord` seleziona un server/sorgente. Se non selezioni un server, l'app mostra un avviso.

Moduli disponibili:

- Record;
- Sessioni;
- Licenze;
- Recap settimanale.

Ogni modulo puo' essere attivato o disattivato.

### Record Discord

Invia un messaggio quando viene rilevato un nuovo record.

Quando disponibili, i messaggi includono anche le condizioni della sessione.

### Sessioni Discord

Invia notifiche quando viene importata una nuova sessione.

Modalita:

- semplice: link alla sessione;
- dettagliata: puo' includere Top 3 per Qualifying e Race.

### Licenze Discord

Invia una notifica quando un pilota raggiunge una nuova licenza.

---

## 13. Recap settimanale community

Il recap settimanale non e' piu legato al singolo server.

La logica attuale e':

- usa tutti i record rilevati dal tracker;
- considera tutti i server monitorati, attuali e passati;
- raggruppa per pista;
- mostra lo storico record community per ogni pista;
- usa un webhook dedicato al recap.

Il recap si configura dalla scheda `Cartelle monitorate` con il pulsante dedicato al webhook recap.

La desktop app mostra uno stato visivo ON/OFF per capire subito se il recap e' attivo.

---

## 14. Sistema licenze

Il sistema licenze assegna livelli ai piloti in base alle soglie tempo configurate.

Esempio:

```text
AM       1:50.000
SILVER   1:47.000
PRO      1:44.000
```

Regole:

- lo SteamID viene usato internamente per riconoscere il pilota;
- lo SteamID non viene mostrato sul web;
- un pilota viene notificato una sola volta per livello;
- se raggiunge un livello migliore, viene inviata una nuova notifica.

La pagina `/licenses` mostra ranking, ricerca pilota e sessioni collegate.

---

## 15. WOACC Bridge API

Se abiliti `Share data with WOACC`, il tracker espone endpoint API per strumenti esterni.

Il JSON originale resta invariato:

```text
GET /api/woacc/session/<session_id>/original.json
```

L'indice API puo' includere metadata aggiuntivi, come condizioni server, senza rompere la compatibilita con chi legge il JSON originale.

Esempio:

```json
{
  "session_id": 111,
  "download_url": "https://example.com/api/woacc/session/111/original.json",
  "conditions": {
    "ambient_temperature_c": 23.4,
    "precipitation": 0,
    "initial_global_wetness": 0,
    "wind_speed_m_s": 0,
    "track_grip": 1.0
  }
}
```

---

## 16. Reverse proxy e Caddy

Se pubblichi il tracker dietro Caddy o altro reverse proxy:

1. abilita `Accesso remoto / LAN`;
2. imposta `Public URL`;
3. imposta `Base path reverse proxy` se usi un percorso tipo `/tracker`;
4. verifica i link Discord e i link condivisi.

Esempio:

```text
Public URL: https://woacc.zapto.org/
Base path: /tracker
```

Risultato:

```text
https://woacc.zapto.org/tracker/
```

Nel progetto e' presente anche un esempio:

```text
caddy_tracker_example.caddyfile
```

---

## 17. Tema web e lingua

Dal desktop puoi personalizzare:

- colori principali;
- font;
- tema web;
- lingua interfaccia.

Le lingue incluse sono:

- `it`
- `en`
- `fr`
- `es`

---

## 18. Manutenzione e backup

Consigli:

- fai backup del file di configurazione prima di aggiornare;
- fai backup del database se contiene storico importante;
- non cancellare il database se vuoi mantenere sessioni, record e licenze;
- se i log del dedicated diventano enormi, usa `Sincronizza log server` a server spento;
- non includere nella release file temporanei, vecchi ZIP, log, database locali o risultati JSON privati.

---

## 19. Aggiornamento a una nuova versione

1. Chiudi WOACC Tracker.
2. Fai backup di configurazione e database se necessario.
3. Sostituisci i file della vecchia versione con quelli della nuova release.
4. Riavvia il tracker.
5. Controlla che le cartelle monitorate siano ancora presenti.
6. Controlla che ogni server abbia il log corretto se usi condizioni/live.
7. Premi `Importa ora` per verificare che tutto sia letto correttamente.

---

## 20. Problemi comuni

### L'app si blocca quando aggiungo un server

Possibile causa: il file `Assetto Corsa EVO Server.txt` e' molto grande.

Soluzione consigliata:

1. spegni il dedicated server;
2. usa `Sincronizza log server`;
3. riaccendi il dedicated server;
4. abilita la leaderboard live solo sui server in cui ti serve.

### Le condizioni mostrano `--`

Controlla:

- il percorso del file `Assetto Corsa EVO Server.txt`;
- che il log contenga una `Season Definition`;
- che il server sia stato riavviato dopo un reset del log;
- che il log corrisponda al server giusto;
- che la sessione sia stata importata dopo aver configurato il log.

### La leaderboard live mostra piloti vecchi

Aggiorna all'ultima versione.

La logica recente usa marker di cambio sessione per considerare solo la sessione attuale. Se il log non contiene marker sufficienti, alcuni piloti possono restare `Non confermato` fino a nuova attivita o riavvio sessione/server.

### La validita dei giri live non coincide col gioco

Il log del dedicated server non espone sempre un segnale certo per track limits e invalidazioni.

Il JSON finale resta la fonte ufficiale per giri validi/non validi.

### Discord non invia messaggi

Controlla:

- webhook corretto;
- modulo attivo;
- server selezionato nel setup;
- Public URL configurato;
- Base path configurato se usi reverse proxy.

### La porta web e' occupata

Cambia `Porta web app`, salva e riavvia il tracker.

### Python non viene riconosciuto

Installa Python abilitando `Add Python to PATH`, oppure usa il percorso completo di Python.

---

## 21. Creazione EXE per release

Comando consigliato per build completa con template, static e lingue incluse:

```powershell
python -m PyInstaller --noconfirm --onefile --windowed --name "WOACC Tracker" --add-data "woacc_tracker\web\templates;woacc_tracker\web\templates" --add-data "woacc_tracker\web\static;woacc_tracker\web\static" --add-data "woacc_tracker\i18n;woacc_tracker\i18n" --hidden-import=jinja2 --hidden-import=werkzeug --hidden-import=flask run_tracker.py
```

Per la release ZIP includi solo i file necessari all'utente finale, ad esempio:

- `WOACC Tracker.exe`;
- `README.md`;
- questa guida;
- `LICENSE`;
- eventuale `config.example.json`;
- eventuale esempio Caddy.

Non includere:

- database locale;
- config personale;
- log;
- JSON risultati privati;
- cartelle `build`;
- file temporanei;
- vecchi ZIP.

---

## 22. Note sulle ultime novita

Ultime funzioni incluse:

- condizioni server da log;
- filtri asciutto/bagnato;
- recap settimanale globale community;
- webhook recap dedicato;
- stato visivo recap ON/OFF;
- traduzione spagnola;
- categoria pilota da `cupCategory`;
- motivi invalid lap quando disponibili;
- API Bridge con metadata condizioni senza modificare il JSON originale;
- selezione file `Assetto Corsa EVO Server.txt` per ogni server;
- sincronizzazione log server a server spento;
- leaderboard live opzionale per singolo server;
- server online e player online nel menu;
- schede server online con pista, sessione, condizioni e link live;
- aggiornamento automatico leaderboard live ogni 5 secondi;
- settori giro live S1/S2/S3;
- dettaglio giri per pilota;
- filtro piloti online/offline;
- pulizia nomi auto live rimuovendo prefisso `ks_`;
- cache lettura log per ridurre carico su community con molti server.
