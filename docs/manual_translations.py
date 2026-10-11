TRANSLATIONS = {
"fr": ("Français", "Manuel d'installation et d'utilisation", [
("Installation et premier démarrage", """
## Rôle de l'application
WOACC Tracker importe les résultats des serveurs dédiés Assetto Corsa EVO et Assetto Corsa Competizione (ACC). Il ne lance pas les serveurs dédiés et ne remplace ni ACCweb ni EVO Web Server Manager. Il gère le site, la surveillance et la Bridge API.
## Installation
1. Télécharger la version Windows x64 sur GitHub ou OverTake et vérifier version et empreinte. Le paquet exécutable ne nécessite pas Python.
2. Extraire TOUT le ZIP dans un dossier permanent, par exemple C:\\WOACC\\Tracker. Ne pas lancer depuis le ZIP.
3. Garder WOACC Tracker.exe, _internal et tout le sous-dossier WOACC Tracker Engine. Cette version n'est pas un exécutable autonome unique.
4. Ouvrir l'application, choisir evo, acc ou both dans Général, enregistrer puis configurer les sources dans les onglets correspondants.
5. Démarrer le tracker et ouvrir le site. Tester http://127.0.0.1:5055/ avant de configurer le réseau.
## Données conservées
La configuration et la base sont normalement dans %APPDATA%\\WOACC_Tracker\\config.json et woacc_tracker.db. Chaque utilisateur Windows dispose de son profil. Une mise à jour ne nécessite pas leur suppression. Les JSON originaux restent inchangés.
! Si Windows signale une application inconnue, vérifier provenance et empreinte avant d'accepter. Ne pas désactiver antivirus ou pare-feu pour contourner le contrôle. Paquet Windows x64.
"""),
("Général : tous les réglages", """
::Mode tracker|evo importe EVO ; acc importe ACC ; both active les deux et le sélecteur du site. Le mode simple ignore les sources de l'autre simulateur.
::Vue initiale|EVO ou ACC définit la première vue en mode both. Un choix déjà mémorisé dans le navigateur peut être prioritaire.
::Nom communauté|Titre du site, sans renommer les serveurs des résultats originaux.
::Port web|5055 par défaut. Si occupé, changer le port et adapter pare-feu, proxy et URL.
::Intervalle analyse|Secondes entre importations : 10 par défaut, minimum effectif 2. Ce n'est pas la fréquence du live dans le navigateur.
::URL publique|Adresse complète accessible, par exemple https://tracker.example.com ; sert aux liens et notifications, sans configurer DNS ou routeur.
::Chemin de base|Vide en accès direct ou domaine dédié ; /tracker avec ce préfixe derrière un proxy.
::Accès distant / LAN|Activé : écoute 0.0.0.0 ; désactivé : 127.0.0.1 uniquement. N'ouvre pas automatiquement les ports.
::Partage WOACC|Active la Bridge API, dont l'authentification est indépendante du mot de passe web.
::Démarrage automatique|Lance l'application à l'ouverture de session Windows. Utiliser le service avant connexion de l'utilisateur.
::Mot de passe web|Activer et saisir un nouveau mot de passe. Champ vide : conserver l'ancien. Utiliser HTTPS ou VPN, pas HTTP pour les identifiants.
## Commandes
Enregistrer conserve les réglages. Démarrer/Arrêter contrôle le site et la surveillance, ou le service installé. Ouvrir Web/Logs ouvre le navigateur local. Importer maintenant analyse manuellement ; Actualiser relit les compteurs de la base. WOACC ouvre la demande d'intégration.
! Après modifications, redémarrer le service. En mode classique, arrêter puis démarrer le tracker pour appliquer les réglages du moteur.
"""),
("Service Windows", """
## Activer
1. Configurer sources, port et URL ; tester le site en mode classique.
2. Dans Général > Service Windows, choisir Installer et démarrer ; accepter la confirmation et l'autorisation administrateur.
3. Le tracker local s'arrête et le moteur séparé est enregistré sous WOACCTracker avec le chemin absolu de la configuration existante.
4. Vérifier ACTIF et le site. Fermer la fenêtre ne ferme pas le service.
## Fonctionnement
Le démarrage automatique est retardé et ne dépend pas de la connexion d'un utilisateur. Redémarrer le service applique les modifications enregistrées. Démarrer/Arrêter Tracker contrôle le service installé. Supprimer le service l'arrête et le désinstalle sans effacer configuration, résultats ou base ; le mode classique redevient disponible.
Le démarrage dans le registre utilisateur est désactivé pendant l'installation du service. Une protection supplémentaire bloque deux moteurs sur la même configuration. L'interface ne contrôle pas un service associé à une autre configuration.
## Permissions
LocalSystem doit lire résultats/logs et écrire dans le dossier de la base. Les lecteurs réseau utilisateur comme Z: peuvent être absents : utiliser UNC et un compte de service autorisé. Ne pas déplacer Engine après installation ; retirer le service avant déplacement, puis le réinstaller.
! Le service ne démarre pas automatiquement Caddy ou les serveurs dédiés. Régler leur démarrage séparément. service.log, près de config.json, est rotatif ; service-control.log contient les erreurs de gestion.
"""),
("Onglet EVO : automatique ou manuel", """
## Avec EVO Web Server Manager
1. Parcourir vers le dossier principal du manager contenant servers, ou son exécutable.
2. Synchroniser les serveurs puis enregistrer. Le tracker reconnaît les dossiers contenant server.json, les résultats et le log correspondant.
3. Vérifier Dossiers surveillés. Aucun autre chemin n'est nécessaire dans la structure standard ; ne pas ajouter les mêmes sources manuellement.
La surveillance adapte les sources gérées aux ajouts/suppressions du manager. Retirer une source n'efface pas les sessions déjà archivées.
## Sans manager
1. Choisir Ajouter dossier résultats dans EVO.
2. Sélectionner result du serveur concerné et donner un nom reconnaissable.
3. Le tracker cherche serverConfig\\Assetto Corsa EVO Server.txt à côté de result. Si absent, la sélection manuelle est proposée. Annuler permet encore l'import JSON, mais pas le live de ce log.
4. Activer Live leaderboard dans Dossiers surveillés si nécessaire.
```tree_evo
```
! Les chemins sont relatifs à AssettoCorsaEVOServer.exe de CE serveur, pas au jeu client. Le serveur dédié doit actualiser le log. N'accepter la synchronisation proposée que serveur dédié arrêté ; refuser pendant son fonctionnement.
"""),
("Onglet ACC : ACCweb et météo", """
## Avec ACCweb
1. Choisir le dossier principal ACCweb contenant config.
2. Synchroniser et enregistrer : reconnaissance de config\\ID_SERVEUR\\accwebConfig.json, nom dans settings.json, association de results et log\\server.log.
3. Vérifier Dossiers surveillés. Aucun autre chemin n'est requis dans la structure standard. Si les fichiers n'existent pas encore, démarrer le dédié puis synchroniser de nouveau.
## Configuration manuelle
Ajouter dossier résultats dans ACC puis sélectionner results du serveur. Le tracker cherche log\\server.log dans le dossier parent ; si absent, il ouvre la sélection manuelle. Annuler n'empêche pas les imports. Modifier chemin log permet une correction ultérieure.
```tree_acc
```
## Températures et identité
event.json, à côté de results, fournit ambientTemp pour l'air et trackTemp si présent. Il s'agit de valeurs configurées, pas de mesures continues. Pluie configurée et aléatoire ne prouvent pas une session mouillée : les archives utilisent isWetSession du résultat.
Le grip absent n'est pas inventé ; les données indisponibles restent ND. Pour récupérer d'anciennes températures, la configuration doit être antérieure ou égale à la session et la piste identique. Les Steam ID présents sont conservés pour identification/API, pas comme noms publics.
! WET dans le nom du serveur ne démontre pas la météo réelle.
"""),
("Dossiers surveillés : chaque fonction", """
Sélectionner une ligne. Sim, nom, chemin et log permettent de vérifier l'association. Défini signifie chemin enregistré, pas log actuel.
::Activer/Désactiver|Contrôle l'import automatique. Record, Sessions, Licences représentent les fonctions Discord, pas des compteurs.
::Modifier nom|Change le nom de la source ; les noms des JSON peuvent rester différents sur le site.
::Supprimer|Retire l'association, pas les originaux ni l'historique importé. Une source gérée peut revenir lors d'une synchronisation si le serveur existe toujours.
::Live ON/OFF|Active le live de la source sélectionnée ; nécessite un log. Les ajouts manuels EVO ne l'activent pas par défaut.
::Modifier chemin log|Choisit un autre log ; il doit appartenir au même serveur que le dossier résultats.
::Maintenance > Synchroniser log|EVO uniquement : archive le log avec suffixe progressif _001 et crée un fichier vide. Ne synchronise pas les paramètres et n'importe pas les JSON. Arrêter D'ABORD le dédié, confirmer puis redémarrer.
::Setup Discord|Trois fonctions indépendantes : records, nouvelles sessions et licences, chacune avec son webhook.
::Récap hebdomadaire / Webhook|Gère le résumé global de la communauté, pas seulement le serveur sélectionné.
! Ne pas dupliquer une source sous deux simulateurs. Utiliser un dossier par dédié ; ne pas mélanger manuellement ACC/EVO dans une source configurée pour un seul format.
"""),
("Discord, records, licences et récap", """
## Webhooks
Créer un webhook dans les intégrations du canal Discord souhaité et copier l'URL. Le traiter comme un secret. Sélectionner le serveur dans Dossiers surveillés, ouvrir Setup Discord puis enregistrer.
::Records|Activer l'annonce, saisir nom événement/serveur et webhook. Les améliorations reconnues à l'import sont annoncées. Effacer records supprime l'historique records/récap de la source, pas les JSON ou toutes les sessions.
::Sessions|Activer les notifications et définir le webhook. Simple : disponibilité et lien ; Détaillé : Top 3 pour qualifications/courses, entraînement simple.
::Licences|Activer, définir webhook et 1 à 3 seuils nommés, par exemple Gold et 1:45.000 ; 105.000 secondes est aussi accepté. Adapter à piste, voiture et conditions. Effacer historique licences réinitialise acquis/notifications de cette source.
## Récap communauté
Définir Webhook Récap, puis activer Récap hebdomadaire. Résumé global, webhook distinct, tracker devant rester actif. Le statut indique activation et configuration ; aucune publication n'est garantie PC éteint.
! Les fenêtres d'activation évitent de notifier indistinctement tout l'historique. Un import n'entraîne pas toujours une notification. Consulter les logs si nécessaire. Ne jamais publier les webhooks ou clés dans des captures.
"""),
("Site, Thème Web et Logs", """
::Accueil|Résumé du simulateur sélectionné, serveurs et dernières sessions ; EVO/ACC change d'archive en mode both.
::Serveurs|Recherche d'archives et cartes en ligne avec piste/session/conditions/joueurs disponibles et lien live. Ouvrir un serveur pour historique et meilleurs temps.
::Sessions|Filtrer puis ouvrir un résultat : participants, temps et tours disponibles. Pratique, qualification et course sont séparées. Les courses archivées utilisent le résultat final, pas le live provisoire.
::Classement|Meilleurs temps avec filtres piste/layout, voiture, session et conditions. Les variantes GP/autres sont séparées si identifiées dans les résultats.
::Records|Historique des améliorations enregistrées, différent de tous les tours live ou des seuls meilleurs temps.
::Licences|Résultats des seuils configurés sur les sources.
::WOACC / Partager / Langue|Demande d'intégration, lien de la page courante et langue web. La langue desktop se règle dans Général.
## Thème Web
Police/taille définissent la typographie ; fond, cartes et lignes la structure ; texte, texte secondaire, accent, erreur et avertissement les couleurs. Choisir un HEX comme #17613e ou un préréglage et enregistrer. N'affecte pas les onglets desktop. Vérifier le contraste sur mobile.
## Logs
L'onglet desktop montre démarrage, analyses et erreurs. Ouvrir Logs présente imports web, diagnostics et Retry si disponible. En service, lire aussi service.log. Retry retente l'import, sans réparer un JSON incomplet du dédié.
"""),
("Classement live et limites", """
## Consulter
Activer le live de la source, ouvrir Serveurs puis Live leaderboard. Page et compteurs s'actualisent toutes les 5 secondes si JavaScript est actif.
En pratique/qualification : ordre par meilleur temps détecté, écart, tours, dernier tour et secteurs disponibles. Cliquer le nom ouvre les tours enregistrés. Tous/En ligne/Hors ligne filtre les pilotes ; l'apparence indique leur état.
## Session courante
Le classement doit concerner le segment de session reconnu, pas tout le fichier historique. Pour EVO, changement de session ou départ de tous les joueurs réinitialisent les temps. Un pilote parti peut rester hors ligne dans l'historique de cette session.
## Provisoire
Un log ne prouve pas toujours la validité : une coupure peut ne laisser aucun indice exploitable. Le JSON de fin de session constitue l'archive définitive. Ne pas considérer un temps candidat live comme sûrement valide.
Le classement course live reste en attente de données fiables, sans inventer les positions. ACC présente des limites liées à la portion de log lue et aux événements ; une page vide peut signifier qu'il manque le changement de session ou l'identité de connexion.
! Statut, joueurs et météo live sont déduits des logs/configuration, pas interrogés directement dans le jeu. Logs anciens/non actualisés et météo aléatoire peuvent induire des indications incomplètes. Activer seulement le live utile ; aucune capacité universelle en nombre de serveurs n'est garantie.
"""),
("Accès local et LAN sans Caddy", """
## D'abord sur le PC
Démarrer et ouvrir http://127.0.0.1:5055/. Vérifier statut et conflits de port si inaccessible. Sur un téléphone, 127.0.0.1 désigne le téléphone, pas le PC tracker.
## Puis sur le même réseau
1. Activer Accès distant/LAN, port 5055, base vide ; enregistrer et redémarrer.
2. Exécuter ipconfig sur le PC ; lire l'IPv4 de l'adaptateur actif, par exemple 192.168.1.50. Réserver cette adresse dans le DHCP du routeur.
3. Dans Pare-feu Windows avancé, autoriser TCP 5055 en entrée sur profil privé, limité au sous-réseau local. Ne pas désactiver le pare-feu.
4. Ouvrir http://192.168.1.50:5055/ depuis un appareil du même réseau.
## Commande facultative
PowerShell administrateur ; copier seulement la commande. Adapter 5055 si nécessaire. Cette règle est réservée au LAN privé, pas à Internet.
```firewall_lan
```
! Wi-Fi invité, isolation clients, VLAN ou pare-feu réseau peuvent bloquer l'accès. L'URL publique n'ouvre pas le réseau. Pour un accès distant privé sans ports publics, utiliser un VPN déjà configuré.
"""),
("Publication HTTPS avec Caddy", """
## Domaine dédié
1. Faire pointer tracker.example.com vers l'IP publique ; utiliser DDNS si dynamique.
2. Caddy sur le même PC : accès distant désactivé, tracker 5055, base vide, URL https://tracker.example.com.
3. Utiliser le bloc domain : Caddy reçoit HTTPS et transmet au tracker local.
```caddy_domain
```
## Préfixe /tracker
Base /tracker et URL https://community.example.com/tracker. Insérer le bloc prefix dans le domaine existant en conservant ses autres routes. handle_path retire le préfixe ; X-Forwarded-Prefix permet au tracker de générer les liens publics corrects.
```caddy_prefix
```
## Vérifier
En configuration standard, autoriser TCP 80/443 sur le PC Caddy et rediriger ces ports du routeur vers lui. Ne pas exposer 5055 avec Caddy local. DNS correct et dossier de données Caddy persistant/accessible en écriture sont nécessaires. Valider et recharger le Caddyfile avec les commandes de l'annexe.
Tester sur réseau mobile : styles, session, live et API. Si Caddy est sur un autre PC, activer LAN dans le tracker et limiter 5055 à l'IP du proxy. Caddy doit rester actif pour HTTPS.
"""),
("Internet sans Caddy", """
## Choix
Un VPN donne un accès privé sans publication. Pour un site public sans Caddy, utiliser un autre proxy HTTPS ; l'accès HTTP direct ci-dessous comporte des risques.
## HTTP direct
1. Activer accès distant, port 5055 et base vide ; enregistrer/redémarrer.
2. IPv4 LAN stable pour le PC. Dans le routeur, rediriger un port TCP externe, par exemple 5055, vers 5055 de ce PC.
3. Ajouter une règle pare-feu entrante adaptée au profil réel de l'adaptateur. N'ouvrir que le port nécessaire et limiter les IP distantes si possible.
4. URL http://IP_PUBLIQUE:5055 ou http://nom-ddns.example:5055. Si le port externe diffère, l'utiliser dans l'URL.
5. Tester en données mobiles ; un test LAN peut échouer sans NAT loopback malgré un accès externe fonctionnel.
## Obstacles
CGNAT ou double NAT peut rendre insuffisante la redirection du seul routeur domestique. Vérifier l'IP publique accessible auprès du fournisseur. Le tracker ne contourne pas ces contraintes et ne crée pas de tunnel.
! HTTP public ne chiffre ni mot de passe, ni clé API, ni trafic. Ne pas y transmettre de secrets. Utiliser un proxy HTTPS ou VPN pour l'accès protégé. Un mot de passe web ne remplace pas TLS. Ne pas exposer les outils d'administration des dédiés pour publier le tracker.
"""),
("Bridge API et moniteurs externes", """
## Sécurité
Partage WOACC active l'API dans Général. Les clients utilisent la clé API, distincte du mot de passe web. Pour changer la clé, arrêter le tracker, sauvegarder config.json, modifier woacc_api_key avec une clé privée forte puis redémarrer. Ne pas publier la clé par défaut ou les webhooks.
## Moniteur
Indiquer la racine complète du tracker, /tracker compris si présent, pas une page session. Utiliser un moniteur mis à jour pour ACC/EVO et une clé enregistrée séparément pour chaque tracker. Le moniteur n'est pas inclus dans ce ZIP.
```api_routes
```
La liste accepte sim=evo, acc ou all ; evo reste le défaut pour les anciens clients. Originaux ACC et JSON compatibles collecteurs peuvent être partagés ; choisir le bon format côté client.
Températures, grip et humidité sont partagés si disponibles ; sinon null/ND. Steam ID seulement si présent à la source, jamais créé à partir d'un nom. Les températures ACC configurées récupérables sont incluses.
! 401 : clé absente/incorrecte ; 403 : API éventuellement désactivée ; 502 du proxy : moteur/port à vérifier. Préférer HTTPS et l'en-tête X-WOACC-API-Key ; ne pas mettre les clés dans liens publics ou captures.
"""),
("Mises à jour, sauvegardes et dépannage", """
## Mise à jour
1. Sauvegarder %APPDATA%\\WOACC_Tracker et l'ancien dossier application. Copier SQLite à tracker arrêté ou avec un outil de sauvegarde cohérent.
2. Arrêter le tracker/service. Retirer le service AVANT de déplacer son dossier ; arrêter aussi le service avant remplacement sur place.
3. Extraire la nouvelle version complète sans écraser la configuration personnelle par un exemple.
4. Vérifier version/sources, réinstaller le service si nécessaire et tester site, API et un nouvel import.
::Aucune session|Vérifier mode, dossier, source active et JSON complet ; parfois créé uniquement en fin de session.
::Aucun live|Vérifier log actuel du bon serveur, activation et limites. Ne pas supprimer un log en cours d'écriture.
::Port occupé|Arrêter l'autre instance ou changer port/proxy/pare-feu. Ne pas lancer deux moteurs app/service.
::Caddy 502 / sans styles|Vérifier moteur, port, base /tracker et bloc Caddy ; tester localement d'abord.
::Température/grip ND|Données parfois absentes : ne pas inventer ou déduire WET du nom.
::Service en panne|Vérifier Engine, droits LocalSystem, config, service.log et Observateur d'événements.
::Notifications absentes|Vérifier webhook, activation, fenêtre d'activation, Internet et Logs.
! Réduire live/sources inutiles et mesurer charge/taille des logs. Ne pas publier sauvegardes, bases, configurations personnelles ou résultats privés dans une release.
"""),
]),
"es": ("Español", "Manual de instalación y uso", [
("Instalación y primer inicio", """
## Finalidad
WOACC Tracker importa resultados de servidores dedicados Assetto Corsa EVO y Assetto Corsa Competizione (ACC). No inicia servidores dedicados ni sustituye ACCweb/EVO Web Server Manager. Gestiona la web, la supervisión y la Bridge API.
## Instalación
1. Descargar la versión Windows x64 de GitHub u OverTake y comprobar versión y hash. El paquete ejecutable no necesita Python.
2. Extraer TODO el ZIP en una carpeta permanente, por ejemplo C:\\WOACC\\Tracker. No ejecutar dentro del ZIP.
3. Conservar WOACC Tracker.exe, _internal y toda la subcarpeta WOACC Tracker Engine. No es un único ejecutable portátil.
4. Abrir la aplicación, elegir evo, acc o both en General, guardar y configurar las fuentes en sus pestañas.
5. Iniciar Tracker y Abrir Web App. Probar http://127.0.0.1:5055/ antes de configurar la red.
## Datos guardados
Configuración y base normalmente están en %APPDATA%\\WOACC_Tracker\\config.json y woacc_tracker.db. Cada usuario Windows tiene su perfil. Actualizar no requiere borrarlos. Los JSON originales permanecen intactos.
! Si Windows avisa de una aplicación desconocida, verificar procedencia y hash antes de aceptarla. No desactivar antivirus o firewall para evitar la comprobación. Paquete Windows x64.
"""),
("General: todos los ajustes", """
::Modo Tracker|evo importa EVO; acc importa ACC; both habilita ambos y el selector web. El modo único ignora las fuentes del otro simulador.
::Vista inicial|EVO o ACC elige la primera vista en both. Una elección ya guardada por el navegador puede prevalecer.
::Nombre comunidad|Título web; no renombra servidores en los resultados originales.
::Puerto web|5055 por defecto. Si está ocupado, cambiarlo y ajustar firewall, proxy y URL.
::Intervalo escaneo|Segundos entre ciclos de importación: 10 por defecto, mínimo efectivo 2. Es distinto del refresco live del navegador.
::URL pública|Dirección completa accesible, por ejemplo https://tracker.example.com. Sirve para enlaces/notificaciones, no configura DNS o router.
::Ruta base|Vacía para acceso directo o dominio dedicado; /tracker con ese prefijo detrás de proxy.
::Acceso remoto / LAN|Activado escucha 0.0.0.0; desactivado solo 127.0.0.1. No abre puertos automáticamente.
::Compartir WOACC|Activa Bridge API; su autenticación es independiente de la contraseña web.
::Inicio automático|Inicia app y tracker al iniciar sesión Windows. Usar servicio para funcionar antes de iniciar sesión.
::Contraseña web|Activar y escribir una nueva. Campo vacío conserva la actual. Usar HTTPS o VPN; HTTP no cifra contraseñas.
## Botones
Guardar ajustes registra los valores. Iniciar/Detener Tracker controla web y supervisión, o el servicio instalado. Abrir Web/Logs abre el navegador local. Importar ahora escanea manualmente; Actualizar estado relee contadores. WOACC abre la solicitud de integración.
! Tras guardar cambios reiniciar el servicio. En modo tradicional detener y reiniciar el tracker para aplicar puerto, red y ajustes del motor.
"""),
("Servicio Windows", """
## Activación
1. Configurar fuentes, puerto y URL; probar primero en modo normal.
2. General > Servicio Windows > Instalar e iniciar. Aceptar confirmación y permiso de administrador Windows.
3. El tracker local se detiene y el motor separado se registra como WOACCTracker, usando la ruta absoluta de la configuración existente.
4. Verificar ACTIVO y abrir la web. Cerrar la ventana no detiene el servicio.
## Funcionamiento
Inicio automático retardado, antes del inicio de sesión del usuario. Reiniciar servicio aplica cambios guardados. Iniciar/Detener Tracker controla el servicio instalado. Eliminar servicio lo detiene y desinstala conservando configuración, resultados y base; vuelve a estar disponible el inicio tradicional.
El inicio del registro del usuario se desactiva mientras el servicio está instalado. Una protección adicional evita dos motores para la misma configuración. La ventana no controla un servicio asociado a otra configuración.
## Permisos
LocalSystem debe leer resultados/logs y escribir en la carpeta de la base. Unidades de red como Z: pueden no existir para ese usuario: usar UNC y una cuenta de servicio autorizada. No mover Engine después de instalar; eliminar primero el servicio y reinstalar tras moverlo.
! No inicia automáticamente Caddy ni los servidores dedicados: configurar su inicio aparte. service.log junto a config.json tiene rotación; service-control.log registra errores de instalación/control.
"""),
("Pestaña EVO: automático o manual", """
## Con EVO Web Server Manager
1. Examinar y elegir la carpeta principal del manager que contiene servers, o su ejecutable.
2. Sincronizar servidores y guardar. Detecta subcarpetas con server.json, resultados y log correspondiente.
3. Revisar Carpetas supervisadas. No hacen falta más rutas en la estructura estándar; no duplicar las fuentes manualmente.
La supervisión adapta las fuentes gestionadas a los servidores añadidos/eliminados. Eliminar una fuente no borra las sesiones ya archivadas.
## Sin manager
1. Añadir carpeta resultados en EVO.
2. Elegir result del servidor y asignar un nombre reconocible.
3. Busca serverConfig\\Assetto Corsa EVO Server.txt junto a result. Si falta, solicita selección manual. Cancelar permite importar JSON pero no live desde ese log.
4. Activar Live leaderboard en Carpetas supervisadas si se desea.
```tree_evo
```
! Las rutas pertenecen a la carpeta de AssettoCorsaEVOServer.exe de ESE servidor, no al juego cliente. El dedicado debe actualizar el log. Aceptar la sincronización opcional solo con el servidor parado; rechazarla mientras está funcionando.
"""),
("Pestaña ACC: ACCweb y meteorología", """
## Con ACCweb
1. Seleccionar la carpeta principal ACCweb que contiene config.
2. Sincronizar y guardar: detecta config\\ID_SERVIDOR\\accwebConfig.json, obtiene nombre de settings.json y asocia results y log\\server.log.
3. Revisar Carpetas supervisadas. No hace falta añadir otras rutas en la estructura estándar. Si aún faltan archivos, iniciar el dedicado y volver a sincronizar.
## Manualmente
Añadir carpeta resultados en ACC y seleccionar results del servidor. Busca log\\server.log en la carpeta superior; si no existe, abre la selección manual. Cancelar no impide importar resultados. Modificar ruta del log permite corregirla después.
```tree_acc
```
## Temperatura e identidad
event.json junto a results proporciona ambientTemp para aire y trackTemp si existe. Son valores configurados, no mediciones continuas. La lluvia configurada y aleatoria no demuestra sesión mojada: las archivadas usan isWetSession del resultado.
No se inventa grip ausente; datos no disponibles quedan ND. Temperaturas históricas requieren configuración no posterior a la sesión y circuito coincidente. Steam ID presente se conserva para identificación/API, no como nombre público.
! WET en el nombre del servidor no demuestra las condiciones reales.
"""),
("Carpetas supervisadas: cada función", """
Seleccionar una fila. Sim, nombre, ruta y log ayudan a comprobar asociación. Configurado indica ruta guardada, no archivo actualizado.
::Activar/Desactivar|Controla importación automática. Record, Sesiones y Licencias indican funciones Discord, no cantidades de registros.
::Modificar nombre|Cambia etiqueta de la fuente; los nombres de los resultados pueden diferir en la web.
::Eliminar|Quita asociación, no originales ni historial importado. Una fuente gestionada puede reaparecer al sincronizar si sigue en el manager.
::Live ON/OFF|Activa live de la fuente elegida; necesita log asociado. EVO manual no lo activa por defecto.
::Modificar ruta del log|Selecciona otro archivo; debe pertenecer al mismo servidor que los resultados.
::Mantenimiento > Sincronizar log|Solo EVO: archiva con sufijo progresivo _001 y crea archivo vacío. No importa JSON ni sincroniza ajustes. Detener PRIMERO el dedicado, confirmar y reiniciarlo.
::Setup Discord|Tres funciones independientes: records, nuevas sesiones y licencias, con webhooks separados.
::Resumen semanal / Webhook|Controla el resumen global de la comunidad, no solo el servidor seleccionado.
! No duplicar carpetas bajo simuladores distintos. Una carpeta por dedicado; no mezclar manualmente ACC/EVO en una fuente configurada para un único formato.
"""),
("Discord, records, licencias y resumen", """
## Webhooks
Crear un webhook en las integraciones del canal Discord y copiar su URL. Tratarla como credencial. Elegir servidor en Carpetas supervisadas, abrir Setup Discord y guardar antes de cerrar.
::Records|Activar anuncios, indicar nombre evento/servidor y webhook. Anuncia mejoras reconocidas al importar. Borrar records elimina historial records/resumen de esa fuente, no JSON ni todas las sesiones.
::Sesiones|Activar y definir webhook. Simple: disponibilidad y enlace; Detallada: Top 3 en clasificación/carrera, práctica simple.
::Licencias|Activar, introducir webhook y 1 a 3 umbrales con nombre y tiempo, por ejemplo Gold y 1:45.000; también acepta 105.000 segundos. Adaptar a pista, coche y condiciones. Borrar historial licencias reinicia logros/notificaciones de la fuente.
## Resumen comunidad
Configurar Webhook Resumen y activar Resumen semanal. Es global, con webhook propio; requiere tracker funcionando. El estado indica activación/configuración, no garantiza publicaciones con PC apagado.
! Las ventanas de activación evitan anunciar todo el historial indiscriminadamente. Un import no siempre produce notificación. Consultar Logs si falta un envío. No publicar webhooks ni claves en capturas.
"""),
("Web, Tema Web y Logs", """
::Inicio|Resumen del simulador elegido, servidores y últimas sesiones. EVO/ACC cambia de archivo en modo both.
::Servidores|Búsqueda de historial y tarjetas online con pista/sesión/condiciones/jugadores disponibles y acceso live. Abrir servidor para historial/mejores tiempos.
::Sesiones|Filtrar y abrir resultados: participantes, tiempos y vueltas. Práctica, clasificación y carrera son distintas. Carreras archivadas usan resultado final, no live provisional.
::Clasificación|Mejores tiempos con filtros pista/layout, coche, sesión y condiciones. GP y otras variantes se separan si están identificadas.
::Records|Historial de mejoras registradas, no todas las vueltas live o únicamente mejores tiempos.
::Licencias|Resultados de los umbrales configurados por fuente.
::WOACC / Compartir / Idioma|Solicitud de integración, enlace actual e idioma web. Idioma desktop en General.
## Tema Web
Fuente/tamaño controlan tipografía; fondo, tarjetas y líneas la estructura; texto, texto secundario, acento, error y aviso los colores. Usar HEX como #17613e o opciones disponibles y guardar. No cambia pestañas desktop. Comprobar contraste en móvil.
## Logs
Desktop registra inicio, escaneos y errores. Abrir Logs muestra imports web, diagnóstico y Retry cuando exista. En servicio consultar también service.log. Retry reintenta importar, sin reparar un JSON incompleto del dedicado.
"""),
("Clasificación live y limitaciones", """
## Uso
Activar live, abrir Servidores y Live leaderboard. Página y contadores se actualizan cada 5 segundos con JavaScript activo, sin recarga manual por vuelta.
En práctica/clasificación se ordena por mejor tiempo detectado, mostrando diferencia, vueltas, última vuelta y sectores disponibles. Pulsar nombre para expandir vueltas. Todos/Online/Offline filtra; la apariencia indica estado del piloto.
## Sesión actual
Debe reflejar el segmento reconocido en el log, no todo el archivo. En EVO cambian los tiempos al cambiar sesión o salir todos los jugadores. Un piloto que sale puede seguir como offline en el historial de esa sesión.
## Datos provisionales
El log no garantiza validez: un recorte puede no dejar señal reconocible. El JSON final es la fuente definitiva del historial. No considerar un tiempo live candidato como prueba de vuelta válida.
Clasificación live de carrera pendiente de datos fiables; no se inventan posiciones. ACC tiene límites por la porción de log leída y eventos disponibles: una página vacía puede indicar cambio de sesión o identidad de conexión ausentes.
! Estado online, jugadores y clima live son inferidos de logs/configuración, no consultas directas al juego. Logs viejos/no actualizados y clima aleatorio pueden dar indicaciones incompletas. Activar solo el live necesario; no existe capacidad garantizada universal de servidores.
"""),
("Acceso local y LAN sin Caddy", """
## Primero en el PC
Iniciar y abrir http://127.0.0.1:5055/. Si falla, revisar estado y puerto ocupado. En un teléfono, 127.0.0.1 es el teléfono, no el PC tracker.
## Después en la misma red
1. Activar acceso Remoto/LAN, puerto 5055 y base vacía; guardar/reiniciar.
2. Ejecutar ipconfig y leer IPv4 del adaptador activo, por ejemplo 192.168.1.50. Reservarla en DHCP del router.
3. En Firewall Windows avanzado autorizar entrada TCP 5055 con perfil privado y subred local. No desactivar el firewall.
4. Abrir http://192.168.1.50:5055/ desde otro dispositivo de esa red.
## Comando opcional
PowerShell administrador; copiar solo el comando. Adaptar puerto si hace falta. Esta regla es SOLO para LAN privada, no Internet.
```firewall_lan
```
! Wi-Fi invitados, aislamiento, VLAN o firewall de red pueden bloquear. URL pública no abre la red. Para acceso remoto privado sin puertos públicos usar VPN ya configurada.
"""),
("Publicación HTTPS con Caddy", """
## Dominio dedicado
1. DNS de tracker.example.com hacia IP pública; DDNS actualizado si cambia.
2. Caddy en mismo PC: remoto desactivado, tracker 5055, base vacía y URL https://tracker.example.com.
3. Usar bloque domain del Caddyfile: recibe HTTPS y lo envía al tracker local.
```caddy_domain
```
## Prefijo /tracker
Base /tracker y URL https://community.example.com/tracker. Insertar bloque prefix en el dominio existente, conservando otras rutas. handle_path elimina el prefijo y X-Forwarded-Prefix permite generar enlaces públicos correctos.
```caddy_prefix
```
## Comprobar
En configuración estándar abrir entrada TCP 80/443 en PC Caddy y redirigir puertos del router hacia ese PC. No exponer 5055 con Caddy local. DNS correcto y carpeta de datos Caddy persistente/escribible. Validar y recargar usando comandos del apéndice.
Probar con datos móviles: estilos, sesión, live y API. Si Caddy está en otro PC, activar LAN en tracker y limitar 5055 a IP del proxy. Caddy debe permanecer funcionando para HTTPS.
"""),
("Internet sin Caddy", """
## Opciones
VPN ofrece acceso privado sin publicar. Para una web pública sin Caddy puede usarse otro proxy HTTPS; el HTTP directo siguiente tiene riesgos.
## HTTP directo
1. Activar remoto, puerto 5055 y base vacía; guardar/reiniciar.
2. IPv4 LAN estable. Router: redirigir un puerto TCP externo, por ejemplo 5055, al 5055 de ese PC.
3. Crear regla entrante adecuada al perfil real del adaptador. Abrir solo puerto necesario y limitar IP remotas si es posible.
4. URL http://IP_PUBLICA:5055 o http://nombre-ddns.example:5055. Si puerto externo distinto, usar ese en URL.
5. Probar con red móvil. Un test LAN puede fallar por falta de NAT loopback aunque funcione desde fuera.
## Problemas
CGNAT/doble NAT puede impedir que baste redirigir el router doméstico. Consultar al proveedor por IP pública accesible. El tracker no resuelve restricciones ni crea túneles automáticamente.
! HTTP público no cifra contraseñas, claves API o tráfico. No enviar credenciales así. Usar otro proxy HTTPS o VPN para acceso protegido. Contraseña web no sustituye TLS. No exponer administración del dedicado para publicar el tracker.
"""),
("Bridge API y monitores externos", """
## Seguridad
Compartir WOACC activa API en General. Clientes necesitan clave API, distinta de contraseña web. Cambiarla: detener, respaldar config.json, modificar woacc_api_key con clave privada fuerte y reiniciar. No publicar clave por defecto o webhooks.
## Conectar monitor
Indicar raíz completa del tracker, incluyendo /tracker si existe, no página sesión. Usar monitor actualizado para ACC/EVO y clave separada por tracker. El monitor no está incluido en este ZIP.
```api_routes
```
Listado admite sim=evo, acc o all; evo sigue por defecto para clientes antiguos. Puede compartir originales ACC y JSON compatibles con colectores; elegir formato correcto en cliente.
Condiciones disponibles incluyen temperatura, grip y mojado; ausentes quedan null/ND. Steam ID solo si viene de la fuente, nunca inventado desde el nombre. Incluye temperaturas ACC configuradas recuperables.
! 401: clave ausente/incorrecta; 403: API posiblemente desactivada; 502 proxy: revisar motor y puerto. Preferir HTTPS y cabecera X-WOACC-API-Key, nunca claves en URL pública o capturas.
"""),
("Actualizaciones, copias y solución de problemas", """
## Actualización
1. Respaldar %APPDATA%\\WOACC_Tracker y carpeta anterior. Copiar SQLite con tracker detenido o con herramienta de respaldo coherente.
2. Detener tracker/servicio. Eliminar servicio ANTES de mover su carpeta; incluso actualizando allí detenerlo antes de reemplazar archivos.
3. Extraer release completa sin sobrescribir configuración personal con ejemplos.
4. Comprobar versión/fuentes, reinstalar servicio si procede y probar web, API y nueva sesión.
::Sin sesiones|Revisar modo, carpeta, fuente activa y JSON completo; dedicado puede generarlo solo al final.
::Sin live|Revisar log actualizado del servidor correcto, activación y límites. No borrar mientras se escribe.
::Puerto ocupado|Detener otra instancia o cambiar puerto/proxy/firewall. No ejecutar app/servicio como motores separados.
::Caddy 502 / sin estilos|Revisar motor, puerto, base /tracker y bloque Caddy; probar local primero.
::Temperatura/grip ND|Datos pueden faltar: no inventar o deducir WET del nombre.
::Falla servicio|Revisar Engine, permisos LocalSystem, configuración, service.log y Visor de eventos Windows.
::Sin notificaciones|Revisar webhook, función activa, ventana de activación, Internet y Logs.
! Reducir live/fuentes innecesarios y medir carga/tamaño logs. No publicar backups, bases, configuraciones personales ni resultados privados en releases.
"""),
]),
}
