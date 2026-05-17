# WOACC EVO Tracker 🚀

**WOACC EVO Tracker** is a local/community tracker for **Assetto Corsa EVO** dedicated server JSON results.

It imports EVO result files automatically, builds web leaderboards and session pages, provides diagnostic import logs, and can optionally send Discord notifications or expose a WOACC Bridge API for external collectors.

> Community-made project. Not official Kunos software.

---

## Main features

- Automatic import of Assetto Corsa EVO result JSON files
- Practice / Qualifying / Race session archive
- Server, track and session detail pages
- Filtered leaderboards with shareable links
- Driver statistics and lap history
- Import logs with **Retry** and full traceback diagnostics
- Manual re-import of failed JSON files
- WOACC Bridge API for external/global collectors
- Remote/LAN access without requiring Caddy
- Reverse proxy / Caddy support with configurable base path
- Custom web theme: colors and fonts
- Multi-language interface

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
4. enable the source
5. press **Import now** or start the tracker

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

If a build script is included in the repository, use it from the project root.

Typical command:

```bat
build_exe.bat
```

The compiled executable should be published in **GitHub Releases**, not committed directly to the source repository.

---

## GitHub release suggestion

Suggested tag:

```text
v13.2.2
```

Suggested release title:

```text
WOACC EVO Tracker v13.2.2 Social Update
```

Short release summary:

```text
This release adds the new Discord Setup panel, weekly recaps, session notifications, license mode, license web page, improved import diagnostics, and better public URL handling for Caddy/reverse proxy setups.
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
