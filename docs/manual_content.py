"""Reviewed manual content. Each language has the same fourteen chapters."""

LANGUAGES = {
"it": ("Italiano", "Manuale di installazione e utilizzo", [
("Installazione e primo avvio", """
## A chi serve
WOACC Tracker importa i risultati dei dedicated server Assetto Corsa EVO e Assetto Corsa Competizione (ACC). Non avvia i dedicated server e non sostituisce ACCweb o EVO Web Server Manager. La pagina web, il monitoraggio e la Bridge API sono gestiti dal tracker.
## Installazione passo per passo
1. Scaricare la release Windows x64 da GitHub o OverTake e controllare versione e checksum. Python non serve per il pacchetto eseguibile.
2. Estrarre TUTTO lo ZIP in una cartella permanente, ad esempio C:\\WOACC\\Tracker. Non avviare l'app dentro lo ZIP.
3. Conservare WOACC Tracker.exe, la cartella _internal e l'intera sottocartella WOACC Tracker Engine. I file interni sono necessari: questa release non è un singolo eseguibile portatile.
4. Aprire WOACC Tracker.exe. In Generale scegliere evo, acc oppure both, salvare e configurare le sorgenti nelle rispettive schede.
5. Premere Avvia Tracker, poi Apri Web App. Verificare http://127.0.0.1:5055/ prima di configurare la rete.
## Cosa viene salvato
Configurazione e database sono normalmente in %APPDATA%\\WOACC_Tracker\\config.json e woacc_tracker.db. Ogni utente Windows ha il proprio profilo. Gli aggiornamenti non richiedono di cancellare questi file. I JSON originali del dedicated restano invariati.
! Se Windows segnala un'app non riconosciuta, verificare prima provenienza e hash. Non disattivare antivirus o firewall per aggirare il controllo. Questa release è per Windows x64.
"""),
("Scheda Generale: tutte le impostazioni", """
::Modalità tracker|evo importa EVO; acc importa ACC; both abilita entrambi e mostra il selettore sul sito. Una sorgente dell'altro simulatore non viene importata in modalità singola.
::Vista iniziale|EVO o ACC determina la prima vista web in both. Una scelta già memorizzata nel browser può prevalere; usare il selettore del sito per cambiarla.
::Nome community|Intestazione del sito. Non rinomina i server presenti nei JSON.
::Porta web|Predefinita 5055. Cambiarla se occupata; aggiornare anche firewall, proxy e URL.
::Intervallo scansione|Secondi tra i cicli di importazione; predefinito 10, minimo effettivo 2. Non è la frequenza di aggiornamento live del browser.
::URL pubblico|Indirizzo completo raggiungibile dagli utenti, ad esempio https://tracker.example.com. Serve ai link condivisi e alle notifiche: non configura DNS o router.
::Percorso base|Vuoto per accesso diretto o dominio dedicato; /tracker se pubblicato sotto quel prefisso tramite proxy.
::Accesso remoto / LAN|Abilitato: ascolta su 0.0.0.0; disabilitato: solo 127.0.0.1. Non apre da solo firewall o porte del router.
::Condivisione WOACC|Abilita la Bridge API. Autenticazione API separata dalla password del sito.
::Avvio automatico|Avvia app e tracker all'accesso dell'utente Windows. Per funzionare prima dell'accesso usare il servizio.
::Password web|Abilitare e inserire una nuova password. Lasciare il campo vuoto conserva quella esistente. Usare HTTPS o VPN: HTTP non cifra la password.
## Pulsanti
Salva impostazioni registra i valori. Avvia/Ferma Tracker avviano o fermano sito e monitoraggio, oppure il servizio installato. Apri Web App e Apri Log aprono il browser locale. Importa ora avvia una scansione manuale; Aggiorna stato rilegge i conteggi del database. WOACC apre la richiesta di collegamento alla community.
! Dopo modifiche in modalità servizio premere Riavvia servizio. In modalità tradizionale fermare e riavviare il tracker per applicare porta, rete e altre impostazioni del motore.
"""),
("Servizio Windows", """
## Attivazione
1. Sistemare prima sorgenti, porta e URL; provare il sito in modalità normale.
2. In Generale > Servizio Windows premere Installa e avvia. Accettare la conferma e l'autorizzazione amministratore di Windows.
3. Il tracker locale viene fermato e il motore separato viene registrato come WOACCTracker. Il servizio usa la configurazione esistente tramite un percorso assoluto.
4. Controllare stato ATTIVO e aprire il sito. Chiudere la finestra desktop non ferma il servizio.
## Comandi e comportamento
Il servizio parte automaticamente, con avvio ritardato, prima dell'accesso dell'utente. Riavvia servizio applica le modifiche salvate. Avvia/Ferma Tracker controllano il servizio quando installato. Rimuovi servizio lo arresta e lo disinstalla, conservando configurazione, risultati e database. L'avvio tradizionale torna disponibile.
L'avvio tramite registro dell'utente viene disabilitato durante l'uso del servizio per evitare doppie istanze. Una protezione aggiuntiva impedisce due motori sulla stessa configurazione. Un servizio associato a una configurazione diversa non viene controllato da questa finestra.
## Permessi e percorsi
Il servizio usa LocalSystem. Deve poter leggere risultati e log e scrivere nella cartella del database. Unità di rete mappate come Z: potrebbero non esistere per il servizio: usare percorsi UNC e un account del servizio con i permessi necessari. Non spostare l'eseguibile Engine dopo l'installazione; rimuovere prima il servizio e reinstallarlo dopo lo spostamento.
! Il servizio non riavvia automaticamente Caddy o i dedicated server. Configurare separatamente il loro avvio. service.log, accanto a config.json, contiene il log del motore con rotazione; service-control.log registra errori di installazione e gestione.
"""),
("Scheda EVO: automatico o manuale", """
## Se usi EVO Web Server Manager
1. In EVO premere Sfoglia e scegliere la cartella principale del manager, quella che contiene servers. Si può indicare anche il suo eseguibile.
2. Premere Sincronizza server e Salva impostazioni. Il tracker riconosce le sottocartelle con server.json, la cartella result e il log del relativo server.
3. Controllare Cartelle monitorate. Non aggiungere di nuovo le stesse cartelle manualmente: non servono altri percorsi se la struttura standard è integra.
Il monitoraggio aggiorna le sorgenti gestite quando il manager aggiunge o rimuove server. Una sorgente rimossa dalla configurazione non cancella le sessioni già archiviate nel database.
## Senza manager
1. Premere Aggiungi cartella risultati nella scheda EVO.
2. Scegliere la cartella result del singolo server e dare un nome riconoscibile.
3. L'app cerca serverConfig\\Assetto Corsa EVO Server.txt accanto a result. Se manca, chiede di selezionare manualmente il log. Annullare lascia funzionante l'importazione JSON, ma senza live da quel log.
4. Per la classifica live abilitarla nella lista delle cartelle monitorate.
```tree_evo
```
! Il percorso è relativo alla directory di AssettoCorsaEVOServer.exe di QUEL server, non alla cartella del gioco client. Il log deve essere aggiornato dal dedicated. La proposta di sincronizzazione del log va accettata solo a dedicated spento; se sta girando, rifiutarla.
"""),
("Scheda ACC: ACCweb e configurazione meteo", """
## Se usi ACCweb
1. In ACC scegliere la cartella principale ACCweb, che contiene config.
2. Premere Sincronizza server e salvare. Il tracker trova config\\ID_SERVER\\accwebConfig.json, legge il nome da settings.json e associa results e log\\server.log.
3. Verificare le righe in Cartelle monitorate. Nella struttura standard non occorre aggiungere altri percorsi. Se i file non sono ancora stati creati, avviare il dedicated e sincronizzare di nuovo.
## Aggiunta manuale
Premere Aggiungi cartella risultati nella scheda ACC e scegliere results del singolo server. Il tracker cerca log\\server.log nella cartella superiore; se non lo trova apre la selezione manuale. Annullare non impedisce di importare i risultati. Modifica percorso log permette di correggere l'associazione in seguito.
```tree_acc
```
## Temperatura, pioggia e identità
Le temperature configurate si leggono da event.json accanto a results: ambientTemp per l'aria e trackTemp quando presente. Non sono una misura continua della pista. La pioggia configurata e la casualità non dimostrano che la sessione sia stata bagnata: per le sessioni archiviate prevale isWetSession nel risultato.
Il grip non viene inventato se assente. Dati mancanti sono ND. Le vecchie temperature si recuperano soltanto se la configurazione non è successiva alla sessione e la pista coincide; altrimenti restano ND. Gli Steam ID presenti nei risultati vengono conservati per identificazione e API, non esposti come nome pubblico.
! Non usare il nome del server (per esempio WET) come prova delle condizioni effettive.
"""),
("Cartelle monitorate: ogni funzione", """
Selezionare una riga prima di usare i comandi. Sim, nome, percorso e Log server aiutano a verificare l'associazione; Impostato indica un percorso salvato, non garantisce che il file sia aggiornato.
::Attiva/Disattiva|Controlla l'importazione automatica della sorgente. Record, Sessioni e Licenze indicano le rispettive funzioni Discord, non il numero di dati nel database.
::Modifica nome|Cambia l'etichetta della sorgente; i nomi originali dei risultati possono rimanere diversi sul sito.
::Rimuovi|Elimina l'associazione di monitoraggio, non i file originali o lo storico già importato. Le sorgenti gestite possono ricomparire alla sincronizzazione se il server esiste ancora nel manager.
::Leaderboard live ON/OFF|Abilita o disabilita il live per la sorgente selezionata. Richiede un log associato; per EVO non è attivo per default nelle aggiunte manuali.
::Modifica percorso log|Seleziona un altro log del server. Controllare sempre che appartenga allo stesso server della cartella risultati.
::Manutenzione > Sincronizza log server|Solo EVO: archivia il log con un numero progressivo, ad esempio _001, e crea un file vuoto. Non importa JSON e non sincronizza impostazioni. Fermare PRIMA il dedicated, confermare e poi riavviarlo.
::Setup Discord|Apre tre schede per record, nuove sessioni e licenze. Le funzioni sono indipendenti e hanno webhook separati.
::Recap settimanale / Webhook Recap|Gestiscono il riepilogo globale della community. Non sono impostazioni del solo server selezionato.
! Non duplicare la stessa cartella con due simulazioni diverse. Usare una cartella per dedicated e non mischiare manualmente file ACC ed EVO in una sorgente configurata per un solo formato.
"""),
("Discord, record, licenze e recap", """
## Preparare i webhook
In Discord creare un webhook nel canale desiderato dalle impostazioni delle integrazioni e copiarne l'URL. Trattarlo come una credenziale. In Cartelle monitorate selezionare il server e aprire Setup Discord; salvare prima di chiudere.
::Record|Abilitare annuncio record, scegliere il nome evento/server e il webhook record. Il tracker notifica i miglioramenti riconosciuti nell'importazione. Cancella record salvati elimina lo storico record/recap della sorgente, non i JSON o tutte le sessioni.
::Sessioni|Abilitare notifica nuove sessioni e inserire il webhook dedicato. Semplice invia disponibilità e link; Dettagliata aggiunge Top 3 per qualifica/gara, mantenendo semplice la pratica.
::Licenze|Abilitare, impostare webhook e da 1 a 3 soglie con nome e tempo, ad esempio Gold e 1:45.000. È accettato anche 105.000 secondi. Scegliere soglie coerenti con pista, auto e condizioni. Cancella storico licenze azzera risultati/notifiche della funzione per quella sorgente.
## Recap della community
Configurare Webhook Recap e poi abilitare Recap settimanale. È un riepilogo globale con il proprio webhook; richiede che il tracker rimanga in funzione. Lo stato indica se la funzione è attiva e il webhook configurato. Non garantisce una pubblicazione se il PC è spento.
! Le finestre di attivazione evitano di annunciare indiscriminatamente tutto lo storico. Un nuovo import non equivale sempre a una nuova notifica; controllare il Log in caso di invii mancanti. Non includere webhook o chiavi private negli screenshot pubblici.
"""),
("Sito web, Tema Web e Log", """
::Home|Riepilogo del simulatore selezionato, server e ultime sessioni. In both usare EVO/ACC nella barra per cambiare archivio.
::Server|Ricerca dei server archiviati; riquadri online con pista, sessione, condizioni disponibili, piloti e accesso alla classifica live. Aprire un server per storico e migliori tempi.
::Sessioni|Filtrare e aprire un risultato; il dettaglio mostra partecipanti, tempi e giri disponibili. Pratica, qualifica e gara sono sessioni diverse; una gara archiviata usa i dati del risultato finale, non il live provvisorio.
::Classifica|Confronto dei migliori tempi con filtri disponibili per pista/layout, auto, sessione e condizioni. I layout GP e altri layout vengono separati se identificati nei risultati.
::Record|Storico dei record registrati. Non confonderlo con tutti i giri del live o con la lista dei migliori tempi.
::Licenze|Risultati della funzione a soglie configurata per le sorgenti.
::WOACC / Condividi / Lingua|Richiesta di integrazione, link alla pagina attuale e selezione della lingua web. La lingua desktop si sceglie in Generale.
## Tema Web
Font e dimensione testo controllano la tipografia; sfondo, card, card secondaria e linee la struttura; testo, testo secondario, accento, errore e avviso i colori. Usare valori HEX come #17613e oppure le scelte disponibili e premere Salva tema. Non modifica i colori delle schede desktop. Verificare contrasto anche sul telefono.
## Log
La scheda desktop registra avvio, scansioni ed errori della finestra. Apri Log mostra le importazioni web con errori, diagnostica e Retry quando disponibile. In servizio consultare anche service.log. Retry ritenta l'importazione del file, non ripara un JSON incompleto nel dedicated.
"""),
("Classifica live e limiti dei dati", """
## Utilizzo
Abilitare il live sulla sorgente, aprire Server e premere Live leaderboard. La pagina e i conteggi si aggiornano automaticamente ogni 5 secondi; JavaScript deve essere attivo. Non occorre aggiornare manualmente il browser per ogni giro.
In pratica e qualifica i piloti sono ordinati per miglior tempo rilevato; sono mostrati distacco, giri, ultimo giro e settori disponibili. Premere il nome del pilota per aprire i giri registrati. Usare Tutti/Online/Offline per filtrare; l'aspetto delle righe distingue lo stato dei piloti.
## La sessione corrente
La classifica deve riferirsi al segmento di sessione riconosciuto nel log, non all'intero archivio. Il cambio sessione e l'uscita di tutti i giocatori sono eventi di azzeramento per EVO. Chi esce durante una sessione può restare nello storico di quella sessione come offline.
## Dati provvisori
I log non garantiscono sempre la validità del giro: un taglio può non avere una segnalazione riconoscibile. Il risultato JSON di fine sessione è la fonte per lo storico definitivo. Non usare un tempo live candidato come prova certa di validità.
La classifica di gara live è ancora sospesa: non viene inventata una posizione attuale senza dati affidabili. Il live ACC ha limiti aggiuntivi dovuti alla porzione di log letta e agli eventi disponibili; una pagina vuota può indicare che manca il cambio sessione o l'identità della connessione nel segmento letto.
! Stato online, numero piloti e meteo live sono ricostruzioni da log/configurazione, non interrogazioni dirette del gioco. File vecchi, log non aggiornati e meteo casuale possono produrre indicazioni incomplete. Per molti server abilitare solo il live necessario; non c'è un numero di server garantito per ogni PC.
"""),
("Accesso locale e LAN senza Caddy", """
## Prima sullo stesso PC
Avviare il tracker e aprire http://127.0.0.1:5055/. Se non risponde, controllare stato e porta occupata. 127.0.0.1 indica sempre il dispositivo su cui si apre il browser, non il PC del tracker da un telefono.
## Poi su un altro dispositivo della stessa rete
1. In Generale abilitare Accesso remoto / LAN, porta 5055 e percorso base vuoto. Salvare e riavviare il motore.
2. Sul PC usare ipconfig e leggere l'IPv4 della scheda realmente collegata, ad esempio 192.168.1.50. Prenotare quell'indirizzo nel DHCP del router per mantenerlo stabile.
3. In Windows Firewall avanzato creare una regola in ingresso per TCP 5055 sul profilo della rete privata, limitata alla sottorete locale. Non spegnere il firewall.
4. Dal telefono/computer collegato alla stessa rete aprire http://192.168.1.50:5055/.
## Regola PowerShell opzionale
Aprire PowerShell come amministratore; copiare soltanto il comando del riquadro. Sostituire 5055 se si usa un'altra porta. La regola seguente è SOLO per LAN privata, non per Internet.
```firewall_lan
```
! Wi-Fi ospiti, isolamento client, VLAN e firewall di rete possono bloccare la connessione pur essendo nello stesso edificio. Impostare l'URL pubblico non apre la rete. Per un accesso remoto privato senza esporre porte pubbliche usare una VPN già configurata.
"""),
("Pubblicazione HTTPS con Caddy", """
## Dominio dedicato: soluzione più semplice
1. Configurare il DNS di tracker.example.com verso l'IP pubblico. Se dinamico, usare un servizio DDNS aggiornato.
2. Con Caddy sullo stesso PC lasciare Accesso remoto disabilitato, porta tracker 5055, base vuota e URL pubblico https://tracker.example.com.
3. Inserire nel Caddyfile il riquadro domain. Caddy riceve HTTPS e inoltra al tracker locale.
```caddy_domain
```
## Sotto /tracker su un dominio esistente
Impostare base /tracker e URL https://community.example.com/tracker. Inserire il riquadro prefix nel blocco del dominio già esistente; mantenere le altre route senza sostituire l'intero file. handle_path rimuove il prefisso dalla richiesta; X-Forwarded-Prefix permette al tracker di generare correttamente i link pubblici.
```caddy_prefix
```
## Apertura e verifica
Nel caso standard aprire TCP 80 e 443 sul firewall del PC Caddy e inoltrarli dal router a quel PC. Non esporre 5055 se Caddy è locale. Il DNS deve essere corretto e la cartella dati Caddy deve essere persistente e scrivibile. Validare il Caddyfile e ricaricare Caddy; vedi i comandi nell'appendice comune.
Provare il dominio da un telefono in rete mobile, poi aprire CSS, una sessione, la classifica live e l'API. Se Caddy è su un altro PC, abilitare LAN nel tracker e limitare 5055 al solo IP del proxy. HTTPS richiede anche che Caddy resti acceso.
"""),
("Internet senza Caddy", """
## Due opzioni distinte
Una VPN offre accesso privato senza pubblicare il tracker. Per un sito pubblico senza Caddy si può usare un altro reverse proxy HTTPS, oppure l'accesso HTTP diretto descritto qui con i relativi rischi.
## Accesso diretto HTTP
1. Abilitare Accesso remoto, scegliere porta 5055 e lasciare percorso base vuoto. Salvare e riavviare il tracker.
2. Assegnare al PC un IPv4 LAN stabile. Nel router inoltrare una porta TCP esterna, per esempio 5055, alla porta 5055 di quel PC.
3. Creare una regola firewall in ingresso coerente con il profilo reale della scheda. Aprire solo la porta necessaria; limitare gli IP remoti quando possibile.
4. Impostare URL pubblico http://IP_PUBBLICO:5055 oppure http://nome-ddns.example:5055. Se la porta esterna è diversa, nell'URL usare quella esterna.
5. Verificare da rete mobile. Un test dalla propria LAN può fallire per assenza di NAT loopback anche se il sito è raggiungibile dall'esterno.
## Se non funziona
Con CGNAT o doppio NAT il port forwarding sul solo router domestico può non bastare. Verificare con il provider se si dispone di un IP pubblico raggiungibile. Il tracker non risolve queste limitazioni e non crea tunnel automaticamente.
! HTTP diretto non cifra password, chiave API o traffico. Non inviare credenziali via HTTP pubblico. Per accesso protetto usare HTTPS tramite un altro proxy o VPN. La password web non sostituisce TLS. Non esporre i servizi di gestione dei dedicated per rendere visibile il tracker.
"""),
("Bridge API e monitor esterni", """
## Attivazione sicura
Condivisione WOACC in Generale abilita la Bridge API. I client devono usare la stessa chiave API del tracker: la password del sito non è quella dell'API. Per cambiarla, fermare il tracker, fare backup di config.json, modificare woacc_api_key con una chiave privata forte e riavviare. Non pubblicare la chiave predefinita o i webhook.
## Collegamento del monitor
Nel monitor impostare la radice completa del tracker (incluso /tracker se presente), non un link a una sessione. Usare una versione aggiornata del monitor capace di ACC ed EVO; ogni tracker deve conservare la propria chiave. Il monitor non è incluso in questo ZIP.
```api_routes
```
L'elenco sessioni supporta sim=evo, acc o all. Il valore predefinito resta evo per compatibilità con vecchi client. L'API può condividere originali ACC e JSON compatibili per i collettori: i client devono scegliere il formato corretto.
Le condizioni disponibili includono temperature, grip e bagnato; i campi mancanti restano null/ND. Lo Steam ID è disponibile solo se la sorgente lo contiene: non viene creato da un nome pilota. Le temperature ACC configurate sono incluse quando recuperabili.
! 401 significa chiave mancante o errata; 403 può indicare API disabilitata; 502 dal proxy richiede di verificare che il motore sia acceso e la porta corretta. Non mettere chiavi nei link pubblici o negli screenshot. Preferire l'header X-WOACC-API-Key e HTTPS.
"""),
("Aggiornamenti, backup e risoluzione problemi", """
## Aggiornare senza perdere dati
1. Salvare una copia di %APPDATA%\\WOACC_Tracker e della vecchia cartella applicazione. Fare il backup SQLite a tracker fermo, oppure con strumenti di backup SQLite coerenti.
2. Fermare il tracker. Se il servizio è installato e si cambia cartella, rimuoverlo PRIMA dello spostamento. Anche aggiornando nello stesso percorso fermare il servizio prima di sostituire i file.
3. Estrarre tutta la nuova release; conservare configurazione e database, non copiarci una configurazione di esempio sopra.
4. Avviare, controllare versione/sorgenti e reinstallare il servizio se necessario. Verificare sito, API e import di una nuova sessione.
::Nessuna sessione|Verificare modalità ACC/EVO, cartella giusta, sorgente attiva e presenza di un JSON completo. Il dedicated può creare il risultato solo a fine sessione.
::Nessun live|Verificare log del medesimo server, file aggiornato, live abilitato e limiti documentati. Non eliminare un log mentre il dedicated lo scrive.
::Porta occupata|Fermare un'altra istanza o cambiare porta e aggiornare proxy/firewall. Non avviare app e servizio come due motori indipendenti.
::Caddy 502 / pagina senza stile|Controllare motore e porta; per /tracker verificare base e blocco Caddy dell'appendice. Provare prima in locale.
::Temperatura o grip ND|Non tutti i risultati/configurazioni li contengono. Non è un motivo per inventare valori o usare il nome WET del server.
::Servizio non parte|Controllare percorso Engine, permessi LocalSystem, config e service.log; usare anche Visualizzatore eventi Windows.
::Notifiche assenti|Controllare webhook, funzione attiva, finestra di attivazione, connessione Internet e Log.
! L'app non garantisce capacità illimitata. Ridurre sorgenti/live superflui e misurare carico e dimensioni log sul proprio PC. Non pubblicare backup, database, config personali o risultati con dati privati nella release.
"""),
]),
"en": ("English", "Installation and user manual", [
("Installation and first launch", """
## Purpose
WOACC Tracker imports dedicated-server results from Assetto Corsa EVO and Assetto Corsa Competizione (ACC). It does not start dedicated servers or replace ACCweb/EVO Web Server Manager. The tracker runs the website, monitoring and Bridge API.
## Step by step
1. Download the Windows x64 release from GitHub or OverTake and verify its version and checksum. The executable package does not require Python.
2. Extract the ENTIRE ZIP into a permanent folder, such as C:\\WOACC\\Tracker. Do not run the application from inside the ZIP.
3. Keep WOACC Tracker.exe, _internal and the complete WOACC Tracker Engine subfolder. Internal files are required: this release is not a single portable executable.
4. Open WOACC Tracker.exe. In General select evo, acc or both, save settings, then configure sources in the matching tabs.
5. Select Start Tracker and Open Web App. Test http://127.0.0.1:5055/ before setting up remote access.
## Stored data
Configuration and database normally live in %APPDATA%\\WOACC_Tracker\\config.json and woacc_tracker.db. Each Windows user has a separate profile. Updates do not require deleting these files. Original dedicated-server JSON files remain unchanged.
! If Windows reports an unrecognized application, verify its origin and hash first. Do not disable antivirus or the firewall to bypass verification. This package targets Windows x64.
"""),
("General tab: every setting", """
::Tracker mode|evo imports EVO; acc imports ACC; both enables both simulators and the website switch. Sources for the other simulator are ignored in single-simulator mode.
::Opening view|EVO or ACC chooses the initial website view in both mode. A browser selection already stored can take precedence; use the website switch to change it.
::Community name|Website heading. It does not rename servers in original results.
::Web port|Default 5055. Change it if occupied, and update firewall, proxy and URLs.
::Scan interval|Seconds between import cycles; default 10, effective minimum 2. Separate from live browser refresh frequency.
::Public URL|Complete reachable address, such as https://tracker.example.com. Used for shared links/notifications; it does not configure DNS or the router.
::Base path|Empty for direct access or a dedicated domain; /tracker when using that prefix behind a proxy.
::Remote / LAN access|Enabled listens on 0.0.0.0; disabled binds to 127.0.0.1. Does not automatically open firewall/router ports.
::Share with WOACC|Enables the Bridge API. API authentication is separate from the website password.
::Automatic startup|Starts the app and tracker at Windows user sign-in. Use the service to run before sign-in.
::Website password|Enable protection and enter a new password. Leaving the field blank retains the existing password. Use HTTPS or a VPN; HTTP does not encrypt passwords.
## Buttons
Save Settings stores values. Start/Stop Tracker controls website and monitoring, or the installed service. Open Web App/Open Logs opens the local browser. Import Now starts a manual scan; Refresh Status reloads database counts. WOACC opens the community integration request.
! In service mode restart the service after saving changes. In traditional mode stop and restart the tracker to apply port, network and other engine settings.
"""),
("Windows service", """
## Activation
1. Configure sources, port and URL; test the website in normal mode first.
2. In General > Windows service choose Install and start. Accept the confirmation and Windows administrator request.
3. The local tracker stops and the separate engine is registered as WOACCTracker. The service uses the existing configuration through its absolute path.
4. Check ACTIVE status and open the website. Closing the desktop window does not stop the service.
## Controls and behavior
The service starts automatically with a delayed start, before user sign-in. Restart Service applies saved changes. Start/Stop Tracker controls the installed service. Remove Service stops and uninstalls it while retaining configuration, results and database. Traditional startup becomes available again.
User-registry startup is disabled while the service is installed to avoid duplicate instances. An additional guard blocks two engines for the same configuration. The desktop does not control a service registered for another configuration.
## Permissions and paths
The service uses LocalSystem, which must read results/logs and write to the database folder. User-mapped network drives such as Z: may be unavailable: use UNC paths and a service account with appropriate permissions. Do not move Engine after installation; remove the service first and reinstall after moving it.
! The service does not automatically start Caddy or dedicated servers. Configure their startup separately. service.log beside config.json records engine activity with rotation; service-control.log records installation/control errors.
"""),
("EVO tab: automatic or manual", """
## With EVO Web Server Manager
1. In EVO choose Browse and select the manager's main folder containing servers; its executable can also be selected.
2. Select Sync Servers and Save Settings. The tracker detects server.json subfolders, result directories and the matching server logs.
3. Check Monitored Folders. Do not manually add the same folders again: no extra paths are needed when the standard structure is intact.
Monitoring updates managed sources as the manager adds/removes servers. Removing a source from configuration does not delete previously archived sessions from the database.
## Without the manager
1. Choose Add Results Folder in the EVO tab.
2. Select the individual server's result folder and enter a recognizable name.
3. The app looks for serverConfig\\Assetto Corsa EVO Server.txt beside result. If missing, it asks you to select a log manually. Canceling still allows JSON imports but not live timing from that log.
4. Enable Live Leaderboard in Monitored Folders if wanted.
```tree_evo
```
! These paths refer to the folder containing THAT server's AssettoCorsaEVOServer.exe, not the game client's folder. The dedicated server must update the log. Accept the optional log synchronization only with the dedicated server stopped; decline while it is running.
"""),
("ACC tab: ACCweb and weather configuration", """
## With ACCweb
1. In ACC select the main ACCweb folder containing config.
2. Choose Sync Servers and save. The tracker detects config\\SERVER_ID\\accwebConfig.json, reads the name from settings.json and associates results and log\\server.log.
3. Check Monitored Folders. No other paths are needed in the standard layout. If files have not been created yet, start the dedicated server and synchronize again.
## Manual setup
Choose Add Results Folder in the ACC tab and select the individual server's results folder. The tracker searches for log\\server.log in its parent folder; if missing, it opens manual selection. Canceling does not prevent results imports. Edit Log Path can correct the association later.
```tree_acc
```
## Temperature, rain and identity
Configured temperatures come from event.json beside results: ambientTemp for air and trackTemp when present. These are not continuous measurements of the track. Configured rain and randomness do not prove a session was wet: archived sessions use isWetSession from the result.
Missing grip is not invented. Unavailable data is ND. Historical temperature recovery requires configuration no newer than the session and a matching track; otherwise values stay ND. Steam IDs in results are retained for identification/API, not displayed as public driver names.
! A server name containing WET is not evidence of actual session conditions.
"""),
("Monitored Folders: every function", """
Select a row before using commands. Sim, Name, Path and Server Log help verify associations; Set means a saved path, not proof that a log is current.
::Enable/Disable|Controls automatic source import. Records, Sessions and Licenses indicate Discord features, not database record counts.
::Edit Name|Changes the source label. Names from original results can still differ on the website.
::Remove|Removes monitoring association, not original files or imported history. Managed sources can reappear during sync if the server still exists in the manager.
::Live Leaderboard ON/OFF|Enables live timing for the selected source. Requires an associated log. Manual EVO sources do not enable it by default.
::Edit Log Path|Selects another server log. Make sure it belongs to the same server as the results folder.
::Maintenance > Sync Server Log|EVO only: archives the log with a progressive suffix such as _001 and creates an empty file. Does not import JSON or synchronize settings. Stop the dedicated server FIRST, confirm, then restart it.
::Setup Discord|Opens independent tabs for records, new sessions and licenses, each with a separate webhook.
::Weekly Recap / Recap Webhook|Controls the global community summary, not just the selected server.
! Do not add the same folder twice under different simulators. Use one results folder per dedicated server and do not manually mix ACC/EVO files in a source configured for a single format.
"""),
("Discord, records, licenses and recap", """
## Prepare webhooks
Create a webhook in the target Discord channel's integration settings and copy its URL. Treat it as a credential. Select a server in Monitored Folders and open Setup Discord; save before closing.
::Records|Enable record announcements, enter event/server name and record webhook. Recognized improvements during import are announced. Clear Saved Records removes that source's record/recap history, not its JSON files or all sessions.
::Sessions|Enable new-session notifications and enter their webhook. Simple sends availability and a tracker link; Detailed adds Top 3 for qualifying/races, keeping practice simple.
::Licenses|Enable, enter webhook and 1 to 3 named time thresholds, for example Gold and 1:45.000. 105.000 seconds is also accepted. Match thresholds to track, car and conditions. Clear License History resets this source's license achievements/notifications.
## Community recap
Configure Recap Webhook, then enable Weekly Recap. This global summary has its own webhook and requires the tracker to stay running. Status shows whether the feature is enabled and a webhook is configured; it cannot publish while the PC is off.
! Activation windows prevent indiscriminate notifications for all historical data. A new import does not always trigger a new notification. Check Logs if delivery is missing. Never include webhook URLs or private keys in public screenshots.
"""),
("Website, Web Theme and Logs", """
::Home|Selected simulator overview, servers and latest sessions. In both mode use the EVO/ACC switch to change archives.
::Servers|Search archived servers; online cards show available track/session/conditions/player information and Live Leaderboard access. Open a server for history and best times.
::Sessions|Filter/open a result; details show participants, times and available laps. Practice, qualifying and race are separate sessions. Archived races use final result data, not provisional live timing.
::Leaderboard|Compare best times using available track/layout, car, session and condition filters. GP and other layouts are separated when identified in results.
::Records|Recorded improvement history; not all live laps and not merely the best-time list.
::Licenses|Achievements from the threshold feature configured for sources.
::WOACC / Share / Language|Integration request, current-page sharing and website language. Set desktop language in General.
## Web Theme
Font and font size control typography. Background, Card, Secondary Card and Lines control structure; Text, Secondary Text, Accent, Error and Warning set colors. Use HEX values such as #17613e or available presets, then Save Theme. Does not change desktop tab colors. Check contrast on mobile too.
## Logs
The desktop Log tab records window startup/scans/errors. Open Logs shows website imports, errors, diagnostics and Retry when available. In service mode also inspect service.log. Retry attempts another import; it cannot repair an incomplete dedicated-server JSON.
"""),
("Live leaderboard and data limitations", """
## Usage
Enable live timing for the source, open Servers and choose Live Leaderboard. The page and counters refresh automatically every 5 seconds with JavaScript enabled; no manual reload is needed for each lap.
Practice/qualifying entries are ordered by detected best time with gap, laps, last lap and available sectors. Select a driver's name to expand recorded laps. All/Online/Offline filters limit entries; row appearance distinguishes driver state.
## Current session
The board should represent the session segment recognized in the log, not the whole archive. Session change and all players leaving reset EVO timing. Drivers who leave partway through can remain offline in that session's history.
## Provisional data
Logs cannot always prove lap validity: a track cut may have no recognizable signal. The completed-session JSON is the source for definitive archived results. Do not treat a candidate live time as proof of a valid lap.
Live race classification remains pending; current positions are not invented without reliable data. ACC live has additional limitations from the bounded log portion and available events. An empty page can mean the session-change or connection identity is missing in the portion read.
! Online status, player counts and live weather are inferred from logs/configuration, not direct game queries. Old/unupdated logs and random weather can give incomplete indications. Enable only necessary live sources for many servers; there is no universal server-count capacity guarantee.
"""),
("Local and LAN access without Caddy", """
## On the tracker PC first
Start the tracker and open http://127.0.0.1:5055/. If unreachable, check running state and port conflicts. On a phone, 127.0.0.1 means the phone itself, not your tracker computer.
## Another device on the same network
1. In General enable Remote / LAN Access, use port 5055 and an empty base path. Save and restart the engine.
2. Run ipconfig on the PC and read the IPv4 for its active network adapter, for example 192.168.1.50. Reserve it in the router's DHCP settings for a stable address.
3. In Windows Firewall Advanced Security create an inbound TCP 5055 rule for the private-network profile, restricted to the local subnet. Do not disable the firewall.
4. On a phone/computer connected to that network open http://192.168.1.50:5055/.
## Optional PowerShell rule
Run PowerShell as administrator and copy only the command. Replace 5055 if using another port. This rule is for a private LAN ONLY, not public Internet access.
```firewall_lan
```
! Guest Wi-Fi, client isolation, VLANs and network firewalls can block access even within one building. A Public URL does not open the network. For private remote access without public ports, use an already configured VPN.
"""),
("HTTPS publication with Caddy", """
## Dedicated domain: simplest setup
1. Point tracker.example.com's DNS to the public IP; use updated DDNS for a dynamic IP.
2. With Caddy on the same PC, leave Remote Access disabled; set tracker port 5055, empty base and Public URL https://tracker.example.com.
3. Use the domain Caddyfile block. Caddy accepts HTTPS and forwards to the local tracker.
```caddy_domain
```
## /tracker on an existing domain
Set base /tracker and URL https://community.example.com/tracker. Insert the prefix block into the existing domain block, preserving other routes instead of replacing the whole Caddyfile. handle_path strips the request prefix; X-Forwarded-Prefix lets the tracker generate correct public links.
```caddy_prefix
```
## Open ports and verify
For the standard setup, allow inbound TCP 80/443 on the Caddy PC and forward these router ports to it. Do not expose 5055 with local Caddy. DNS must be correct and Caddy's data folder persistent/writable. Validate and reload the Caddyfile using the shared appendix commands.
Test from a phone on mobile data, then check CSS, a session, live timing and API. If Caddy runs on another PC, enable tracker LAN access and restrict 5055 to the proxy's IP. Caddy must remain running for HTTPS access.
"""),
("Internet access without Caddy", """
## Different choices
A VPN provides private access without publishing the tracker. For a public website without Caddy, another HTTPS reverse proxy is an option; direct HTTP access below has important risks.
## Direct HTTP
1. Enable Remote Access, choose port 5055 and leave Base Path empty. Save and restart the tracker.
2. Give the PC a stable LAN IPv4. Forward an external TCP port, for example 5055, to that PC's port 5055 in the router.
3. Create an inbound firewall rule matching the adapter's actual profile. Open only the required port and restrict remote IPs where possible.
4. Set Public URL to http://PUBLIC_IP:5055 or http://ddns-name.example:5055. If the external port differs, use the external port in the URL.
5. Test from mobile data. Testing from your LAN can fail due to missing NAT loopback even if external access works.
## If unreachable
With CGNAT or double NAT, port forwarding on just the home router may not suffice. Ask your provider whether you have a reachable public IP. The tracker does not fix these restrictions or create tunnels automatically.
! Public HTTP does not encrypt passwords, API keys or traffic. Do not send credentials over public HTTP. Use another HTTPS proxy or a VPN for protected access. A website password is not a TLS replacement. Do not expose dedicated-server administration services just to publish the tracker.
"""),
("Bridge API and external monitors", """
## Secure activation
Share with WOACC in General enables the Bridge API. Clients need the tracker API key; the website password is different. To change it, stop the tracker, back up config.json, set woacc_api_key to a strong private key and restart. Do not publish the default key or webhook URLs.
## Connect a monitor
Enter the complete tracker root in the monitor, including /tracker if used, not a session page URL. Use an updated monitor supporting ACC and EVO; each tracker needs its own stored key. The monitor is not included in this ZIP.
```api_routes
```
The session list supports sim=evo, acc or all; default remains evo for old-client compatibility. The API can share original ACC files and collector-compatible JSON: clients must choose the correct format.
Available conditions include temperatures, grip and wetness; missing fields remain null/ND. A Steam ID is available only if the source includes it, never invented from a driver's name. Recoverable configured ACC temperatures are included.
! 401 means missing/wrong key; 403 can indicate a disabled API; a proxy 502 requires checking that the engine and correct port are running. Do not place keys in public URLs/screenshots. Prefer X-WOACC-API-Key headers and HTTPS.
"""),
("Updates, backups and troubleshooting", """
## Update without losing data
1. Back up %APPDATA%\\WOACC_Tracker and the previous application folder. Copy SQLite with the tracker stopped or use a consistent SQLite backup tool.
2. Stop the tracker. If moving an installed service, remove it BEFORE changing folders. Even when updating in place, stop the service before replacing files.
3. Extract the whole new release. Retain configuration/database; never overwrite personal settings with an example configuration.
4. Start, verify version/sources and reinstall the service if needed. Test the website, API and a newly imported session.
::No sessions|Check simulator mode, correct folder, enabled source and complete JSON. Dedicated servers may create results only when sessions end.
::No live data|Check matching/current log, live enabled and documented limits. Never delete a log while the dedicated server is writing it.
::Port occupied|Stop the other instance or change port and adjust proxy/firewall. Do not run app/service as independent engines.
::Caddy 502 / unstyled page|Check engine/port; for /tracker check base and the appendix Caddy block. Test locally first.
::Temperature/grip ND|Not every result/config contains these values. Do not fabricate values or infer weather from WET in a server name.
::Service fails|Check Engine location, LocalSystem permissions, config and service.log; also use Windows Event Viewer.
::Missing notifications|Check webhook, enabled feature, activation window, Internet connection and Logs.
! Capacity is not unlimited. Disable unnecessary live/sources and measure actual load/log sizes on your PC. Do not publish backups, databases, personal configs or private results in releases.
"""),
]),
}
