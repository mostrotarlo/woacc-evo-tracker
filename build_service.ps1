$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python -m PyInstaller --noconfirm --onedir --windowed --name 'WOACC Tracker' --distpath dist_service --workpath build_service_desktop --add-data 'woacc_tracker\web\templates;woacc_tracker\web\templates' --add-data 'woacc_tracker\web\static;woacc_tracker\web\static' --add-data 'woacc_tracker\i18n;woacc_tracker\i18n' run_tracker.py
if ($LASTEXITCODE -ne 0) { throw 'Desktop build failed' }
python -m PyInstaller --noconfirm --onedir --name 'WOACC Tracker Engine' --distpath dist_service_engine --workpath build_service_engine --hidden-import win32timezone --add-data 'woacc_tracker\web\templates;woacc_tracker\web\templates' --add-data 'woacc_tracker\web\static;woacc_tracker\web\static' --add-data 'woacc_tracker\i18n;woacc_tracker\i18n' run_tracker_service.py
if ($LASTEXITCODE -ne 0) { throw 'Engine build failed' }
# Keep the complete engine distribution alongside the desktop executable.
Copy-Item -LiteralPath 'dist_service_engine\WOACC Tracker Engine' -Destination 'dist_service\WOACC Tracker' -Recurse -Force
Copy-Item -LiteralPath 'WINDOWS_SERVICE.md' -Destination 'dist_service\WOACC Tracker\WINDOWS_SERVICE.md' -Force
