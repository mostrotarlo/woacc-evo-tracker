# WOACC Tracker API: EVO e ACC

Il tab AC Evo di WOACC Unified Monitor legge anche le sessioni ACC quando il tracker annuncia `supported_sims: ["evo", "acc"]`. La chiave API resta associata al singolo URL del tracker.

- Originali: `results/EVO_<tracker>/raw` e `results/ACC_<tracker>/raw`.
- Convertiti: la cartella `session_jsons` configurata per WOACC; EVO puo usare `session_json_evo` se l'opzione di output comune e disattivata.
- Identita ACC: `steamId` e `playerId` nei piloti e nei giri, ricavati dal `playerId` originale.
- Condizioni: blocco `conditions` copiato dall'indice API. `__conditions_source` indica la provenienza. Per EVO temperatura aria, grip e bagnato arrivano dal log del server; nell'originale non ci sono. ACC espone `isWetSession` e le temperature configurate disponibili in `event.json` (`ambientTemp`, `trackTemp`). Il grip rimane ND quando manca una fonte.

Al primo collegamento a un tracker che espone ACC, le sessioni ACC gia presenti nell'indice vengono segnate come storico e non riscaricate. Le nuove vengono importate normalmente. I file ACC identici gia scaricati dal lettore hosting condividono la stessa chiave SHA-256 e non vengono convertiti due volte. Per recuperare lo storico dall'API, impostare `evo.acc_backfill_existing` a `true` in `config/app_config.json` **prima del primo collegamento ACC**. Risultati equivalenti provenienti da sistemi diversi (per esempio un sito ACCTracker e il JSON raw ACC) non vengono fusi automaticamente senza un identificatore comune affidabile.
