# WOACC Tracker - servizio Windows

La distribuzione servizio comprende la finestra `WOACC Tracker.exe` e il motore
nella sottocartella `WOACC Tracker Engine`. Conservare entrambe le cartelle e tutti
i file `_internal`. Non spostare il motore dopo l'installazione del servizio.

## Attivazione

Nella scheda Generale, sezione Servizio Windows, scegliere **Installa e avvia** e
accettare la richiesta amministratore. Il tracker locale viene fermato prima
dell'installazione. Il servizio parte automaticamente con Windows, anche senza
accesso dell'utente. Chiudere la finestra non ferma il servizio.

La registrazione del servizio conserva il percorso assoluto della configurazione
esistente. Database, cartelle monitorate, porta, URL e chiave API rimangono quelli
attuali. L'avvio all'accesso dell'utente viene disattivato mentre il servizio e
installato, per evitare doppie istanze.

**Avvia Tracker** e **Ferma Tracker** controllano il servizio quando installato.
Dopo aver salvato modifiche alle impostazioni o alle cartelle, scegliere
**Riavvia servizio**. Lo stato viene aggiornato dopo ogni operazione.

**Rimuovi servizio** arresta e rimuove il servizio senza cancellare dati o
impostazioni. L'avvio tradizionale torna disponibile.

## Permessi e diagnosi

Il servizio usa LocalSystem. Le cartelle locali devono essere leggibili e la
cartella della configurazione/database scrivibile da questo account. Le unita di
rete mappate dall'utente non sono disponibili: usare percorsi UNC e configurare
un account del servizio autorizzato nelle proprieta del servizio Windows.

`service.log` si trova accanto a `config.json`, con rotazione automatica.
`service-control.log` contiene gli errori di installazione o gestione.
Un'altra configurazione non puo controllare questo servizio dall'interfaccia.

## Build

Installare i requisiti e PyInstaller, poi eseguire `build_service.ps1`.
Distribuire tutta la cartella `dist_service/WOACC Tracker`.
