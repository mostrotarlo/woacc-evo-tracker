# WOACC EVO Tracker - Complete Installation and Configuration Guide

This guide covers installation, configuration, and usage of both existing features and the latest additions in WOACC EVO Tracker.

WOACC EVO Tracker is a local/community tracker for Assetto Corsa EVO dedicated server result JSON files. It imports sessions, builds web pages for the community, manages records, Discord notifications, weekly recap, server conditions, Bridge API, and live leaderboard data based on the dedicated server log.

> Community-made project. Not official Kunos software.

---

## 1. Requirements

- Windows.
- Assetto Corsa EVO Dedicated Server.
- A server result folder, for example:

```text
servers/server_1/result
```

- Optional but recommended: the dedicated server log file:

```text
servers/server_1/serverConfig/Assetto Corsa EVO Server.txt
```

- For the source version: Python 3.10 or newer.
- For the EXE version: Python is not required.
- A web browser to open the tracker interface.
- Optional: Discord webhook.
- Optional: Caddy or another reverse proxy if you want to publish the tracker through a domain and a base path such as `/tracker`.

---

## 2. Installation from EXE

1. Download the release ZIP.
2. Extract the ZIP into a writable folder, for example:

```text
C:\WOACC_Tracker
```

3. Start:

```text
WOACC Tracker.exe
```

4. If Windows SmartScreen appears, confirm the launch only if the file comes from the official release you downloaded.
5. On first launch, configure the `General` tab, then add at least one monitored folder.

Tip: do not run the program directly inside the ZIP. Always extract it first.

---

## 3. Installation from Source

Open a terminal inside the project folder and install the dependencies:

```powershell
python -m pip install -r requirements.txt
python run_tracker.py
```

If Windows does not recognize `python`, install Python and enable `Add Python to PATH`, or use the full path to the Python executable.

---

## 4. First Desktop Configuration

The `General` tab contains the main settings.

### Community Name

Name shown in the web tracker and used as the general community context.

### Web App Port

Local port used by the tracker, for example:

```text
5055
```

The local address will be:

```text
http://127.0.0.1:5055
```

### Scan Interval

How often the tracker checks the result JSON folders.

Recommended example:

```text
60
```

### Public URL

Public address used to build shareable links and Discord links.

Examples:

```text
https://woacc.zapto.org/
http://YOUR_PUBLIC_IP:5055
```

### Reverse Proxy Base Path

Use this if the tracker is published under a path, for example:

```text
/tracker
```

With:

```text
Public URL: https://woacc.zapto.org/
Base path: /tracker
```

links become:

```text
https://woacc.zapto.org/tracker/session/123
```

### Language

Available languages:

- Italiano
- English
- Francais
- Espanol

### Remote / LAN Access

When enabled, the tracker also listens on the local network using bind `0.0.0.0`.

Use this if you want to reach it from other PCs on the LAN or through a reverse proxy.

### Share Data with WOACC

Enables the WOACC Bridge API for external tools or global collectors.

The original session JSON remains unchanged.

### Password Protection

You can protect the web app with a password. Leave the new password field empty if you do not want to change it.

---

## 5. Adding a Monitored Server

Open the `Monitored folders` tab.

For each server:

1. Click `Add`.
2. Select the result JSON folder:

```text
...\servers\server_1\result
```

3. Give the source/server a recognizable name.
4. When requested, also select the server log file:

```text
...\servers\server_1\serverConfig\Assetto Corsa EVO Server.txt
```

The log file is optional. If you do not configure it, the tracker will continue importing JSON files as before, but it will not be able to read server conditions or live leaderboard data.

---

## 6. Where to Find the result Folder and Log File

Each Assetto Corsa EVO dedicated server has its own folder. The easiest starting point is the folder containing:

```text
AssettoCorsaEVOServer.exe
```

Example:

```text
C:\Users\YOUR_USER\Desktop\server_1\AssettoCorsaEVOServer.exe
```

Or, if you use a multi-server manager structure:

```text
C:\Users\YOUR_USER\Desktop\woacc_server_manager\servers\server_1\AssettoCorsaEVOServer.exe
C:\Users\YOUR_USER\Desktop\woacc_server_manager\servers\server_2\AssettoCorsaEVOServer.exe
```

Inside the same executable folder, or in its subfolders, you normally find the folders needed by the tracker.

### Result JSON Folder

The folder to monitor for results is:

```text
result
```

Typical path:

```text
...\server_1\result
```

Full example:

```text
C:\Users\YOUR_USER\Desktop\woacc_server_manager\servers\server_1\result
```

Inside this folder, the dedicated server creates files similar to:

```text
results_20260607_150733_practice.json
results_20260607_160416_qualifying.json
results_20260607_170205_race.json
```

This is the folder you must select when WOACC Tracker asks for the result JSON path.

### Server Log File

The log file to select is:

```text
Assetto Corsa EVO Server.txt
```

Typical path:

```text
...\server_1\serverConfig\Assetto Corsa EVO Server.txt
```

Full example:

```text
C:\Users\YOUR_USER\Desktop\woacc_server_manager\servers\server_1\serverConfig\Assetto Corsa EVO Server.txt
```

This file contains the lines written by the dedicated server during startup and during live sessions. WOACC Tracker uses it to read conditions, server status, online players, and live leaderboard data.

### Practical Rule

For each EVO server, associate:

```text
server_1\result
server_1\serverConfig\Assetto Corsa EVO Server.txt
```

For the next server:

```text
server_2\result
server_2\serverConfig\Assetto Corsa EVO Server.txt
```

Do not use the log from a different server than the selected `result` folder. Otherwise, conditions and live leaderboard data may refer to the wrong server.

### If the Log File Is Missing

If you cannot find `Assetto Corsa EVO Server.txt`:

- start the dedicated server at least once;
- check the `serverConfig` folder;
- make sure you are inside the correct server folder, close to `AssettoCorsaEVOServer.exe`;
- if your server manager uses separate folders, open the single server folder, not only the main manager folder.

---

## 7. Selecting and Syncing the Server Log

Each source can have an associated file:

```text
Assetto Corsa EVO Server.txt
```

This file is used for:

- server conditions;
- online/offline server status;
- online player count;
- live session type;
- live leaderboard;
- live sectors.

### Select Server Log

This button is used to set or change the log file path.

### Sync Server Log

This function must be used while the dedicated server is stopped.

When you click `Sync server log`, the tracker:

1. shows a warning reminding you to stop the dedicated server;
2. renames the current log with a progressive number, for example:

```text
Assetto Corsa EVO Server_001.txt
```

3. creates a new empty `Assetto Corsa EVO Server.txt`.

This helps prevent freezes or slowdowns when an old log file has become very large.

If the server is running, Windows may lock the file and the operation may fail.

---

## 8. Result JSON Import

The tracker automatically checks monitored folders and imports new files:

```text
results_YYYYMMDD_HHMMSS_practice.json
results_YYYYMMDD_HHMMSS_qualifying.json
results_YYYYMMDD_HHMMSS_race.json
```

You can also click `Import now` to force a manual check.

Original JSON files generated by the dedicated server are never modified. The tracker stores data in its own database and keeps compatibility with external applications that read the original files.

If an import fails, the diagnostic log page shows the error and allows you to use `Retry`.

---

## 9. Server Conditions

If `Assetto Corsa EVO Server.txt` is configured, when a new JSON is imported the tracker searches the log for the matching `Season Definition` and associates the following data with the session:

- weather;
- air temperature;
- rain/precipitation;
- track wetness;
- wind;
- humidity;
- track grip;
- rubber;
- marbles.

Conditions are displayed in compact form:

```text
DRY | 23.4C | G 1.00 | WET 0.00 | WIND 0.0
WET | 18.2C | G 0.72 | WET 0.40 | WIND 1.2
WET | RAIN 0.25 | 18.2C | G 0.65 | WET 0.60 | WIND 2.5
```

Meaning:

- `DRY`: dry track.
- `WET`: wet track.
- `RAIN`: active rain.
- `C`: air temperature.
- `G`: track grip.
- `WET`: track wetness value.
- `WIND`: wind.

Important note: if the log was emptied while the server was already running, the `Season Definition` may be missing. In that case, conditions may remain empty until the server restarts or writes a new definition.

---

## 10. Main Web Pages

### Home

Shows community summary, available servers, and latest detected sessions.

### Servers

Shows:

- monitored servers;
- online servers;
- live session type;
- track;
- conditions;
- online players;
- live leaderboard link.

### Sessions

Archive of all imported sessions, with filters for server, track, session type, and dry/wet conditions.

### Session Detail

Shows the session leaderboard, drivers, categories, cars, times, laps, and associated conditions.

### Leaderboard

Filtered leaderboard by server, track, and conditions.

### Records

Community historical records, filterable by dry/wet conditions when data is available.

### Licenses

Page dedicated to the driver license system.

### WOACC

Page dedicated to sharing/API/bridge features when enabled.

---

## 11. Online Servers and Live Leaderboard

Live reading is optional for each server.

To enable it:

1. open `Monitored folders`;
2. select the server;
3. set the `Assetto Corsa EVO Server.txt` file;
4. enable the `Live leaderboard` checkbox.

If the checkbox is disabled, the tracker will not generate a live leaderboard for that server.

### What Gets Updated

The tracker periodically updates:

- how many servers are active;
- how many players are online;
- online server cards;
- live leaderboard when the page is opened.

The live leaderboard page updates automatically every 5 seconds.

### Log Reading Optimization

To reduce load:

- light server status data is read to show online/player information;
- heavier leaderboard data is read only when the live page/API is requested;
- the leaderboard uses a short cache;
- the live page refresh frequency is 5 seconds;
- reading is active only for servers with live leaderboard enabled.

This is important for communities with many online servers.

### Practice and Qualifying

In Practice and Qualifying sessions, the live leaderboard sorts drivers by best lap detected in the log.

It shows:

- position;
- driver;
- car;
- best lap;
- gap;
- total laps;
- last lap;
- sectors S1, S2, S3;
- driver state.

Clicking the driver name opens the detected lap list.

### Race

Race live logic is still pending more reliable race log data.

The target is to sort by live position, but this should only be implemented once race log format is confirmed.

### Online, Offline, and Unconfirmed Drivers

The leaderboard distinguishes:

- `Online`: driver confirmed as present or recently active.
- `Offline`: driver left during the current session and the log contains a disconnect line.
- `Unconfirmed`: the log does not contain enough information to know for sure whether the driver is still connected.

The leaderboard filter can show all drivers, only online drivers, or only offline drivers.

### Session Change

When the log indicates a session change, the leaderboard restarts and considers only the current session data.

The dedicated server log may stay in the same file for days; for this reason, the tracker uses session markers to avoid showing drivers and laps from old sessions.

### Live Lap Validity

The live leaderboard is provisional.

The log does not always expose a reliable signal for track limits or every invalidation reason. The final JSON remains the safest source for valid/invalid laps.

For this reason, live times should be treated as candidates until the official session JSON is generated.

---

## 12. Discord

Discord configuration is available in the dedicated setup panel.

Before clicking `Setup Discord`, select a server/source. If no server is selected, the app shows a warning.

Available modules:

- Records;
- Sessions;
- Licenses;
- Weekly recap.

Each module can be enabled or disabled.

### Discord Records

Sends a message when a new record is detected.

When available, messages also include session conditions.

### Discord Sessions

Sends notifications when a new session is imported.

Modes:

- simple: session link only;
- detailed: can include Top 3 for Qualifying and Race.

### Discord Licenses

Sends a notification when a driver reaches a new license level.

---

## 13. Community Weekly Recap

The weekly recap is no longer tied to a single server.

Current logic:

- uses all records detected by the tracker;
- considers all monitored servers, current and past;
- groups by track;
- shows the community historical record for each track;
- uses a dedicated recap webhook.

The recap is configured from the `Monitored folders` tab using the dedicated recap webhook button.

The desktop app shows a visual ON/OFF status so you can immediately see whether the recap is active.

---

## 14. License System

The license system assigns levels to drivers based on configured lap-time thresholds.

Example:

```text
AM       1:50.000
SILVER   1:47.000
PRO      1:44.000
```

Rules:

- SteamID is used internally to recognize the driver;
- SteamID is not shown on the web interface;
- a driver is notified only once per level;
- if a driver reaches a better level, a new notification is sent.

The `/licenses` page shows ranking, driver search, and related sessions.

---

## 15. WOACC Bridge API

If you enable `Share data with WOACC`, the tracker exposes API endpoints for external tools.

The original JSON remains unchanged:

```text
GET /api/woacc/session/<session_id>/original.json
```

The API index can include extra metadata, such as server conditions, without breaking compatibility with tools that read the original JSON.

Example:

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

## 16. Reverse Proxy and Caddy

If you publish the tracker behind Caddy or another reverse proxy:

1. enable `Remote / LAN access`;
2. set `Public URL`;
3. set `Reverse proxy base path` if you use a path such as `/tracker`;
4. verify Discord links and share links.

Example:

```text
Public URL: https://woacc.zapto.org/
Base path: /tracker
```

Result:

```text
https://woacc.zapto.org/tracker/
```

The project also includes an example:

```text
caddy_tracker_example.caddyfile
```

---

## 17. Web Theme and Language

From the desktop app you can customize:

- main colors;
- fonts;
- web theme;
- interface language.

Included languages:

- `it`
- `en`
- `fr`
- `es`

---

## 18. Maintenance and Backup

Recommendations:

- back up the configuration file before updating;
- back up the database if it contains important history;
- do not delete the database if you want to keep sessions, records, and licenses;
- if dedicated server logs become huge, use `Sync server log` while the server is stopped;
- do not include temporary files, old ZIP files, logs, local databases, or private result JSON files in a release package.

---

## 19. Updating to a New Version

1. Close WOACC Tracker.
2. Back up configuration and database if needed.
3. Replace the old version files with the new release files.
4. Restart the tracker.
5. Check that monitored folders are still present.
6. Check that each server has the correct log path if you use conditions/live features.
7. Click `Import now` to verify that everything is read correctly.

---

## 20. Common Issues

### The App Freezes When Adding a Server

Possible cause: `Assetto Corsa EVO Server.txt` is very large.

Recommended solution:

1. stop the dedicated server;
2. use `Sync server log`;
3. restart the dedicated server;
4. enable live leaderboard only on the servers where you need it.

### Conditions Show `--`

Check:

- the `Assetto Corsa EVO Server.txt` path;
- that the log contains a `Season Definition`;
- that the server was restarted after a log reset;
- that the log belongs to the correct server;
- that the session was imported after configuring the log.

### The Live Leaderboard Shows Old Drivers

Update to the latest version.

The recent logic uses session change markers to consider only the current session. If the log does not contain enough markers, some drivers may remain `Unconfirmed` until new activity or a session/server restart.

### Live Lap Validity Does Not Match the Game

The dedicated server log does not always expose a certain signal for track limits and invalidations.

The final JSON remains the official source for valid/invalid laps.

### Discord Does Not Send Messages

Check:

- correct webhook;
- module enabled;
- selected server in setup;
- configured Public URL;
- configured Base path if using a reverse proxy.

### The Web Port Is Busy

Change `Web app port`, save, and restart the tracker.

### Python Is Not Recognized

Install Python with `Add Python to PATH` enabled, or use the full Python executable path.

---

## 21. Creating the EXE for Release

Recommended command for a complete build with templates, static files, and languages included:

```powershell
python -m PyInstaller --noconfirm --onefile --windowed --name "WOACC Tracker" --add-data "woacc_tracker\web\templates;woacc_tracker\web\templates" --add-data "woacc_tracker\web\static;woacc_tracker\web\static" --add-data "woacc_tracker\i18n;woacc_tracker\i18n" --hidden-import=jinja2 --hidden-import=werkzeug --hidden-import=flask run_tracker.py
```

For the release ZIP, include only the files needed by end users, for example:

- `WOACC Tracker.exe`;
- `README.md`;
- this guide;
- `LICENSE`;
- optional `config.example.json`;
- optional Caddy example.

Do not include:

- local database;
- personal config;
- logs;
- private result JSON files;
- `build` folders;
- temporary files;
- old ZIP files.

---

## 22. Latest Additions

Latest included features:

- server conditions from log;
- dry/wet filters;
- global community weekly recap;
- dedicated recap webhook;
- visual recap ON/OFF status;
- Spanish translation;
- driver category from `cupCategory`;
- invalid lap reasons when available;
- Bridge API condition metadata without modifying the original JSON;
- `Assetto Corsa EVO Server.txt` selection for each server;
- server log sync/reset while the server is stopped;
- optional live leaderboard per server;
- online servers and online players in the menu;
- online server cards with track, session, conditions, and live link;
- automatic live leaderboard refresh every 5 seconds;
- live sectors S1/S2/S3;
- driver lap detail;
- online/offline driver filter;
- live car name cleanup by removing the `ks_` prefix;
- log reading cache to reduce load on communities with many servers.
