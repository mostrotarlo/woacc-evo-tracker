# WOACC EVO & ACC Tracker 15.1.0

![WOACC EVO & ACC Tracker](docs/assets/woacc-evo-acc-tracker-15.1.0.png)

## v15.1.0 Unified ACC/EVO and Windows service

This Windows release supports ACC, EVO or both, automatic server discovery from
ACCweb and EVO Web Server Manager, per-source live timing controls, and a separate
Windows service engine. Manual additions detect the expected log location for
both simulators and ask for a log when detection fails. Desktop tabs are colored.

Extract the complete release archive before opening `WOACC Tracker.exe`. Keep
both `_internal` directories and the `WOACC Tracker Engine` folder. The included
multilingual PDF manual covers all settings, service installation, LAN access,
public access with and without Caddy, Discord and the Bridge API.

**WOACC Tracker** is a local/community tracker for Assetto Corsa EVO and Assetto Corsa Competizione dedicated servers.

It imports result files automatically, builds separate web leaderboards and session pages for each simulator, provides diagnostic import logs, and can optionally send Discord notifications or expose an EVO-compatible WOACC Bridge API for external collectors.

> Community-made project. Not official Kunos software.

---

## v15.0.5 ACC configured temperatures

ACC sessions import `ambientTemp` and optional `trackTemp` from the server's `event.json`, next to its `results` folder. These are configured temperatures. Explicit result conditions take priority. Archived sessions can recover missing temperatures only when the configuration predates the session and matches its track. Values are stored with the session and shared through the Bridge API; missing track temperature and grip remain unavailable. Dry/wet status follows the result's `isWetSession`, independently of configured random rain.

## v15.0.4 ACC data and opening view

In the Windows settings, choose the initial EVO or ACC view when both simulators are enabled. Older ACC sessions keep missing air/track temperature and grip as unavailable; their existing `playerId` values remain available as Steam IDs. The tracker stores explicit `conditions` values from a result JSON when present, without modifying the original file. A newly generated standard ACC result is not guaranteed to contain temperatures or grip.

## v15.0.3 Performance

Unchanged result files are skipped during subsequent folder scans. Each imported session is committed in one database transaction instead of writing every lap separately. The web pages use indexed session lookups, and the server list reuses its live status data during rendering.

## v15.0.1 Bridge API for both simulators

The authenticated WOACC Bridge API can now share original ACC and EVO JSON files without changing their contents:

```text
GET /api/woacc/sessions             EVO only (legacy default)
GET /api/woacc/sessions?sim=acc     ACC only
GET /api/woacc/sessions?sim=all     Both simulators
GET /api/woacc/session/<id>/original.json
```

Each index item includes `sim` (`evo` or `acc`). The existing `X-WOACC-API-Key` remains valid. The default stays EVO-only so older ACC JSON Monitor Plus installations do not accidentally interpret ACC results as EVO results. Update the monitor before switching it to `sim=all`.

---

## New in v15.0.0: EVO and ACC in one tracker

- Choose EVO, ACC or Both in the desktop General tab. The web interface keeps the simulators separate via an EVO/ACC switch.
- In the EVO tab, select the EVO Web Server Manager installation folder. Servers are discovered under `servers/<server>/`, with results in `result/` and live log in `serverConfig/Assetto Corsa EVO Server.txt`.
- In the ACC tab, select the ACCweb installation folder. Servers are discovered under `config/<server>/`, with results in `results/` and the live log in `log/server.log`.
- Manager sync adds and removes server sources as their folders change, while preserving per-server options such as monitoring and Discord settings. A temporarily unavailable manager folder does not erase its sources.
- ACC archived sessions use the official `isValidForBest` lap flag and final race order from the ACC result JSON. `isWetSession` supplies the historical dry/wet indicator.
- ACC live Practice/Qualifying timing is provisional. Race position is not shown live until a reliable position signal is verified; official race classification appears after the session JSON is imported.
- ACCweb's current `event.json` can provide configured track, air and track temperature for live server status. It is not used to invent historical temperatures absent from result JSON.
- The existing Bridge API defaults to EVO sessions for current external consumers; the existing configuration, key and database are reused on upgrade.
- Repeated scans skip result files whose size and modification time have not changed, avoiding repeated hashing of large ACC archives.

For a safe upgrade, back up `%APPDATA%\WOACC_Tracker\config.json` and `woacc_tracker.db` before replacing the running application. Keep the old executable as a rollback copy.

---

## Main features

- Automatic import of Assetto Corsa EVO result JSON files
- Optional import of server conditions from `Assetto Corsa EVO Server.txt`
- Optional live leaderboard generated from the dedicated server log
- Online server cards with live session type, track, conditions and player count
- Weather, air temperature, rain, wet track, wind, grip, rubber and marbles stored per session
- Compact DRY/WET/RAIN condition labels in web tables and Discord messages
- Dry/wet filters for sessions, records and leaderboards
- Practice / Qualifying / Race session archive
- Server, track and session detail pages
- Filtered leaderboards with shareable links
- Track records by circuit, car and driver
- Driver statistics and lap history
- Import logs with **Retry** and full traceback diagnostics
- Manual re-import of failed JSON files
- WOACC Bridge API for external/global collectors
- Remote/LAN access without requiring Caddy
- Reverse proxy / Caddy support with configurable base path
- Custom web theme: colors and fonts
- Multi-language interface

---

## New in v14.1.2 Windows Autostart Fix

### Automatic tracker startup

When the automatic-start option is enabled, WOACC Tracker registers itself to start with Windows. The tracker service, web app and folder monitor then start on their own, without requiring the **Start Tracker** button.

The desktop app includes this option:

```text
Start tracker automatically when the app opens
```

The setting is applied immediately when the checkbox changes. Disabling it removes the Windows startup registration.

### Conditions fallback

Server log condition parsing now also accepts fallback fields for ambient temperature and sky coverage when the dedicated server writes them with alternate names.

---

## New in v14.1.0 Track Layout Fix

### Separate track layouts

WOACC Tracker now uses `track_layout_name` from the Assetto Corsa EVO result JSON to distinguish different layouts of the same track.

Examples:

```text
Monza / GP
Monza / Mini
```

These are now treated as separate tracks in:

- server grouping
- sessions
- filtered leaderboard
- records
- licenses
- live leaderboard labels
- Discord session notifications
- WOACC Bridge API metadata

### Historical data migration

On first start after updating, WOACC Tracker tries to fix already imported sessions by reading the original JSON files still stored in their saved paths.

If the original JSON files are still available, old sessions are moved into the correct `track / layout` grouping automatically.

If the original JSON files were deleted or moved, those old sessions cannot be corrected with certainty and remain as previously imported.

---

## New in v14.0.0 Live Server Monitoring

### Live leaderboard from server logs

Each monitored source can enable a live leaderboard based on:

```text
Assetto Corsa EVO Server.txt
```

For Practice and Qualifying sessions, WOACC Tracker builds a provisional live leaderboard ordered by best lap and shows:

- driver
- car
- best lap
- gap
- lap count
- last lap
- sectors S1, S2 and S3
- online / offline / unconfirmed driver state

The live leaderboard refreshes automatically every 5 seconds.

Race live ordering is intentionally left pending until enough reliable race log data is available.

### Per-server live toggle

Live leaderboard reading can be enabled or disabled for each monitored server from the desktop app.

This avoids unnecessary log parsing on communities with many servers.

### Online server overview

The Servers page now includes online server cards with:

- server name
- track
- session type
- conditions
- online player count
- live leaderboard link

The top navigation also shows active servers and total online players.

### Log reading optimization

WOACC Tracker now keeps live log reading lighter:

- server/player status uses lightweight reads;
- detailed leaderboard parsing runs only when the live page/API is requested;
- live leaderboard data uses short cache;
- automatic refresh is reduced to 5 seconds.

### Current-session handling

The live leaderboard resets when the log indicates a new session, so old laps and offline drivers from previous sessions are not mixed with the current session.

Driver states are shown as online, offline or unconfirmed depending on what the log can prove.

### Log sync/reset tool

The desktop app includes a server log sync/reset tool.

Use it while the dedicated server is stopped. It renames the existing log with a progressive backup name and creates a new empty:

```text
Assetto Corsa EVO Server.txt
```

This is useful when old logs have become very large.

### Complete setup guides

Two complete installation and configuration guides are included:

```text
GUIDA_INSTALLAZIONE_CONFIGURAZIONE.md
INSTALLATION_AND_CONFIGURATION.md
```

They explain where to find each server `result` folder and the matching `Assetto Corsa EVO Server.txt` log file.

---

## New in v13.3.0 Conditions and Community Recap

### Server conditions from logs

Each monitored source can now be linked to the dedicated server log:

```text
Assetto Corsa EVO Server.txt
```

When a new result JSON is imported, WOACC Tracker reads the matching `Season Definition` from the log and stores the server conditions with the session.

Imported condition fields include:

- weather type
- air temperature
- precipitation
- track wetness
- wind speed
- humidity
- initial grip
- dynamic track grip
- rubber
- marbles

The original EVO result JSON is never modified.

### Local time handling

Some result filenames use UTC while the server log uses local Windows time.

WOACC Tracker now falls back to the real file write time when needed, so the web interface can show the local session time and still match the correct log conditions.

### DRY / WET / RAIN labels

Conditions are shown in compact form:

```text
DRY | 23.4C | G 1.00 | WET 0.00 | WIND 0.0
WET | 18.2C | G 0.72 | WET 0.40 | WIND 1.2
WET | RAIN 0.25 | 18.2C | G 0.65 | WET 0.60 | WIND 2.5
```

Meaning:

- **DRY**: dry track
- **WET**: wet track
- **RAIN**: active rain
- **C**: air temperature
- **G**: track grip
- **WIND**: wind speed

### Web filters

The web interface now supports filtering by conditions:

- all conditions
- dry
- wet

Available on:

- Sessions
- Filtered leaderboard
- Records

### Discord and recap updates

- Discord record messages include session conditions when available.
- Weekly recap is now global for the community instead of being tied to a single monitored server.
- Weekly recap uses its own dedicated webhook.
- The desktop app shows a visual ON/OFF recap status.

### Bridge API conditions metadata

The WOACC Bridge API keeps serving the original JSON unchanged:

```text
GET /api/woacc/session/<session_id>/original.json
```

The session index includes extra metadata under `conditions`:

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

External tools can keep reading the original JSON as before and optionally consume the extra `conditions` block from the index.

### Other improvements

- Invalid laps now show a reason when available.
- Pit return flag `129` marks the next lap as an outlap.
- Driver category extraction supports `cupCategory`.
- Spanish translation file added.
- Record monitoring operational details are no longer exposed on the public web pages.

---

## New in v13.2.2 Social

### Discord Setup

The old Discord record button has been replaced by a complete **Setup Discord** panel.

Available modules:

- **Records**
- **Weekly recap**
- **Sessions**
- **Licenses**

Each module can be enabled independently and can use its own webhook where applicable.

### Record announcements

Send Discord announcements when a new record is achieved.

Options:

- enable / disable record announcements
- dedicated Discord webhook
- custom event/server name
- reset saved record history

### Weekly recap

Send a weekly recap of records.

The recap contains:

- driver
- track
- record time

### Session notifications

Notify Discord when new sessions are available.

Available modes:

- **Simple**: sends only a new-session notification and tracker link
- **Detailed**: for Qualifying and Race, can include the Top 3 drivers; Practice remains a simple notification

### License system

WOACC Tracker can assign licenses based on lap-time thresholds.

You can configure from 1 to 3 custom levels, for example:

```text
AM       1:50.000
SILVER   1:47.000
PRO      1:44.000
```

Rules:

- SteamID is used internally for stable driver matching
- SteamID is never shown in the web interface
- a driver is notified only once per achieved level
- a new notification is sent only if the driver reaches a higher level

The web page:

```text
/licenses
```

shows:

- latest licenses achieved
- license ranking ordered by level and best time
- driver search by name
- click on a row to open the related session

### Discord session URL fix

Discord embed links now support both:

```text
https://yourdomain/tracker/session/<id>
```

and:

```text
http://PUBLIC_IP:5055/session/<id>
```

The link is built from:

- **Public URL**
- **Reverse proxy base path**

Example with Caddy:

```text
Public URL: https://woacc.zapto.org/
Base path: /tracker
Result: https://woacc.zapto.org/tracker/session/68
```

Example without Caddy:

```text
Public URL: http://PUBLIC_IP:5055
Base path: empty
Result: http://PUBLIC_IP:5055/session/68
```

---

## Installation from source

```bash
pip install -r requirements.txt
python run_tracker.py
```

Then open:

```text
http://127.0.0.1:5055
```

Recommended desktop settings:

```text
Web App Port: 5055
Remote / LAN Access: enabled if you want access from other devices
Password: optional
```

---

## Monitored folders

The tracker must know where the EVO Dedicated Server stores the result JSON files.

In the desktop app:

1. open the **Monitored folders** tab
2. press **Add folder**
3. select the EVO Dedicated Server `results` folder
4. optionally select `Assetto Corsa EVO Server.txt` to import server conditions
5. enable the source
6. press **Import now** or start the tracker

Supported session types:

```text
Practice
Qualifying
Race
```

---

## Discord setup

1. Open Discord
2. Open the settings of the channel where notifications should be posted
3. Open:

```text
Integrations → Webhooks
```

4. Create a new webhook
5. Copy the webhook URL
6. In WOACC Tracker, select a monitored folder
7. Press **Setup Discord**
8. Configure the modules you want to use
9. Save

---

## Public access

### Local

```text
http://127.0.0.1:5055
```

### LAN

```text
http://192.168.x.x:5055
```

### Internet without Caddy

To expose the tracker directly:

1. enable **Remote / LAN Access**
2. open port `5055` in Windows Firewall
3. forward port `5055` in your router
4. use your public IP or a Dynamic DNS service

Example:

```text
http://PUBLIC_IP:5055
```

Dynamic DNS examples:

- No-IP
- DuckDNS
- Zapto

### Internet with Caddy / reverse proxy

Example configuration:

```text
Public URL: https://yourdomain.com/
Base path: /tracker
```

The public tracker URL becomes:

```text
https://yourdomain.com/tracker
```

---

## WOACC Bridge API

The Bridge API allows external tools or a global WOACC collector to query the tracker.

Endpoints:

```text
GET /api/woacc/ping
GET /api/woacc/sessions
GET /api/woacc/session/<session_id>/original.json
```

`/api/woacc/ping` advertises `supported_sims`. `/api/woacc/sessions` defaults to EVO for older clients and accepts `?sim=evo`, `?sim=acc`, or `?sim=all`. Each item includes its `sim` and, when known, a `conditions` object.

`/api/woacc/session/<session_id>/original.json` returns the original EVO or ACC result JSON unchanged. EVO air temperature, grip and wetness in the index come from the matching server log, not from the original result JSON. ACC results can supply `isWetSession`; air/track temperature and grip are not inferred when absent.

The WOACC Unified Monitor copies available index conditions into its converted JSON as `conditions` with `__conditions_source`, while keeping the downloaded raw file unchanged. It preserves ACC `playerId` as `steamId`/`playerId` for drivers and laps. Existing converted files are not rewritten automatically.

When served under `/tracker`:

```text
GET /tracker/api/woacc/ping
GET /tracker/api/woacc/sessions
GET /tracker/api/woacc/session/<session_id>/original.json
```

---

## Data and settings location

On Windows, settings and database are stored in:

```text
C:\Users\<USER>\AppData\Roaming\WOACC_Tracker
```

Typical files:

```text
config.json
woacc_tracker.db
```

Do not commit private runtime files to GitHub.

---

## Files that should not be committed

Keep these out of the repository:

```text
config.json
woacc_tracker.db
*.db
*.db-journal
__pycache__/
build/
dist/
*.pyc
```

---

## Build executable

Recommended Windows command from the project root:

```powershell
python -m PyInstaller --noconfirm --onefile --windowed --name "WOACC Tracker" --add-data "woacc_tracker\web\templates;woacc_tracker\web\templates" --add-data "woacc_tracker\web\static;woacc_tracker\web\static" --add-data "woacc_tracker\i18n;woacc_tracker\i18n" --hidden-import=jinja2 --hidden-import=werkzeug --hidden-import=flask run_tracker.py
```

The compiled executable should be published in **GitHub Releases**, not committed directly to the source repository.

---

## GitHub release suggestion

Suggested tag:

```text
v14.1.2
```

Suggested release title:

```text
WOACC EVO Tracker v14.1.2 Windows Autostart Fix
```

Short release summary:

```text
This release makes the automatic-start checkbox register WOACC Tracker directly in Windows startup. When enabled, the desktop app, web server and folder monitor start automatically after Windows login. Disabling the checkbox removes the registration.
```

---

## Support

PayPal donation:

```text
https://www.paypal.com/donate/?business=7AVK9RRTQHSNJ&no_recurring=1&currency_code=EUR
```

Live demo:

```text
https://woacc.zapto.org/tracker
```

GitHub:

```text
https://github.com/mostrotarlo/woacc-evo-tracker
```

---

## License

MIT License
