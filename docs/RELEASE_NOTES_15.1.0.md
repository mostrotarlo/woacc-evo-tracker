# WOACC EVO & ACC Tracker 15.1.0

![WOACC EVO & ACC Tracker](https://raw.githubusercontent.com/mostrotarlo/woacc-evo-tracker/v15.1.0/docs/assets/woacc-evo-acc-tracker-15.1.0.png)

## Unified ACC and EVO tracker

- Select EVO, ACC or both; separate simulator archives and initial web view.
- Automatically discover server folders from EVO Web Server Manager and ACCweb, and keep managed sources synchronized.
- Add standalone result folders from the appropriate simulator tab. Logs are detected automatically; a file picker opens when detection fails.
- Import ACC results with official lap validity, driver identifiers and wet-session status. Read configured ACC temperatures from matching server settings when available; missing historical values stay unknown.
- Share ACC and EVO sessions through the Bridge API. Existing EVO clients retain the default EVO filter; updated clients can request `sim=all`.
- Run the tracker as an optional Windows service with delayed automatic startup, without requiring a Windows login or an open desktop window.
- More visible desktop tabs, source log maintenance and preserved per-source notification options.
- Include a complete 63-page installation and user manual in Italian, English, French and Spanish, with local/LAN access, Caddy HTTPS examples and alternatives without Caddy.
- Correct static asset paths behind a stripping reverse proxy using `X-Forwarded-Prefix`.

## Installation and upgrade

Download **WOACC_Tracker_v15.1.0_Windows_x64.zip** and extract the entire archive. Start **WOACC Tracker.exe**. Keep `_internal` and the complete **WOACC Tracker Engine** directory together with it; this is not a single-file executable release. Python is not required.

Before upgrading, stop the tracker/service and back up the existing configuration and database. A service installed from a moved application folder must be removed and reinstalled. Read the included manual before changing network or service settings.

## Important limitations

- EVO live lap validity remains provisional where the log does not report track-limit invalidation reliably. Archived JSON results are the authoritative source.
- Live race-position standings remain pending; no unsupported position is invented.
- ACC live status and weather depend on available log events and configuration. Configured temperatures are not real-time track measurements; absent grip and historical values remain unknown.
- Public deployment requires your own DNS/network/firewall configuration. The app does not install Caddy or create router forwarding.
- ACC JSON Monitor Plus is a separate application and is not included. Use an updated dual-simulator version and a private API key per tracker.

Demo: https://woacc.zapto.org/tracker/

