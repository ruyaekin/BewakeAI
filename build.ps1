$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
py -m pip install -r requirements.txt
py -m unittest -v
if ($LASTEXITCODE -ne 0) { throw 'Tests fehlgeschlagen' }
py -m PyInstaller --noconfirm --clean --windowed --onedir --hidden-import pystray._win32 --add-data 'release-config.json;.' --name BewakeAIDownloadManager --distpath release --workpath build app.py
if ($LASTEXITCODE -ne 0) { throw 'App-Build fehlgeschlagen' }
Copy-Item README.txt release\BewakeAIDownloadManager\README.txt
$compiler = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if ($compiler) { & $compiler.Source installer.iss }
else { Write-Output 'Portable App gebaut. Für Setup.exe: Inno Setup 6.6+ installieren und installer.iss kompilieren.' }
