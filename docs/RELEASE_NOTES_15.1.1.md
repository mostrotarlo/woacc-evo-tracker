# WOACC EVO & ACC Tracker 15.1.1

## Desktop freeze fixes

- Fix the interface freeze when pressing **Stop tracker** or closing the desktop application.
- Fix the freeze when switching from the desktop tracker to the Windows service.
- Stop the folder monitor and web server in the background, keeping the interface responsive until shutdown completes.
- Prevent another start or service operation during local shutdown.
- Wait for local shutdown before closing the interface. Closing the control panel does not stop a separately running Windows service.
- Report shutdown errors without discarding the runtime or silently closing the application.
- Limit the wait for Windows service commands to two minutes. A pending command is not treated as a completed installation and does not automatically restart the local tracker.
- Correct service-engine discovery when running from source.

## Download and upgrade

Download **WOACC_Tracker_v15.1.1_Windows_x64.zip** and extract the complete archive.
Start **WOACC Tracker.exe**. Keep both `_internal` directories and the complete
**WOACC Tracker Engine** folder. Python is not required.

Stop the previous tracker/service and back up the configuration and database
before upgrading. The default configuration remains in
`%APPDATA%\WOACC_Tracker\config.json`; existing source paths, database settings,
web settings and API keys are preserved when using the same Windows account.
Do not run old and new versions simultaneously against the same database.
Update startup shortcuts if the application folder changes. Remove and reinstall
an existing Windows service if its executable path changes.

Includes the complete installation and configuration manual in Italian, English,
French and Spanish. ACC/EVO support and existing live-timing limitations are
unchanged from 15.1.0.

Validation: 35 automated tests passed before the version bump, including shutdown,
service handoff, close-after-stop and error-path regression tests.

Demo: https://woacc.zapto.org/tracker/
