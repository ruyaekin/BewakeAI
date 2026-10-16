"""Public GitHub Releases updater. Only verified installer assets can be launched."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request,urlopen

SETUP='Bewake-AI-Download-Manager-Setup.exe'
HEADERS={'User-Agent':'BewakeAI-Updater','Accept':'application/vnd.github+json'}

def repository(value):
    value=value.strip().removeprefix('https://github.com/').rstrip('/')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',value) or any(x in ('.','..') for x in value.split('/')): raise ValueError('GitHub-Repository als NAME/REPOSITORY angeben.')
    return value

def version(value):
    match=re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)',value)
    if not match: raise ValueError('Version muss wie 0.6.0 aussehen.')
    return tuple(map(int,match.groups()))

def asset_url(value,repo):
    if not value.startswith('https://github.com/'+repo+'/releases/download/'): raise ValueError('Update-Datei stammt nicht aus dem gewählten GitHub-Repository.')
    return value

def read(url,limit=2*1024*1024):
    with urlopen(Request(url,headers=HEADERS),timeout=20) as response:
        data=response.read(limit+1)
        if len(data)>limit: raise ValueError('Update-Antwort ist zu groß.')
        return data

def check(repo,current):
    repo=repository(repo)
    try: release=json.loads(read('https://api.github.com/repos/'+repo+'/releases/latest'))
    except HTTPError as error:
        if error.code==404: return None
        raise
    if release.get('draft') or release.get('prerelease'): return None
    tag=release.get('tag_name','')
    if version(tag)<=version(current): return None
    assets=release.get('assets',[]); setup=next((a for a in assets if a.get('name')==SETUP),None)
    if not setup: return None # A build may still be attaching the installer.
    url=asset_url(setup.get('browser_download_url',''),repo)
    sha=setup.get('digest') or ''
    if sha.startswith('sha256:'): sha=sha[7:]
    if not re.fullmatch('[0-9a-fA-F]{64}',sha):
        checksums=next((a for a in assets if a.get('name')=='SHA256SUMS.txt'),None)
        if not checksums: raise ValueError('Für dieses Release fehlt die SHA-256-Prüfsumme.')
        contents=read(asset_url(checksums.get('browser_download_url',''),repo),65536).decode('utf-8-sig')
        sha=next((line.split()[0] for line in contents.splitlines() if len(line.split())==2 and line.split()[1].lstrip('*')==SETUP),'')
    if not re.fullmatch('[0-9a-fA-F]{64}',sha): raise ValueError('Ungültige Update-Prüfsumme.')
    size=setup.get('size',0)
    if not isinstance(size,int) or not 0<size<=256*1024*1024: raise ValueError('Ungültige Update-Dateigröße.')
    return {'version':tag.removeprefix('v'),'url':url,'sha256':sha.lower(),'size':size}

def download(update,folder):
    folder=Path(folder)/'updates'; folder.mkdir(parents=True,exist_ok=True)
    version(update['version']); target=folder/('BewakeAI-'+update['version']+'-Setup.exe'); partial=target.with_suffix('.partial')
    expected=update['sha256']; sha=hashlib.sha256(); size=0
    try:
        with urlopen(Request(update['url'],headers={'User-Agent':'BewakeAI-Updater'}),timeout=45) as response,partial.open('wb') as output:
            parsed=urlparse(response.url)
            if parsed.scheme!='https' or parsed.hostname not in ('github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'): raise ValueError('Unzulässige Download-Weiterleitung.')
            while True:
                block=response.read(1024*1024)
                if not block: break
                size+=len(block)
                if size>update['size']: raise ValueError('Update-Dateigröße stimmt nicht überein.')
                sha.update(block); output.write(block)
            output.flush(); os.fsync(output.fileno())
        if size!=update['size'] or sha.hexdigest()!=expected: raise ValueError('Update-Prüfsumme stimmt nicht. Installation abgebrochen.')
        os.replace(partial,target); return target
    finally:
        if partial.exists(): partial.unlink()

def launch(update,path,state_folder):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=update['sha256']: raise ValueError('Update-Datei wurde nach dem Download verändert.')
    if not getattr(sys,'frozen',False):
        raise ValueError('Update ist heruntergeladen. Automatische Installation nur in der installierten Windows-App verfügbar: '+str(path))
    script=Path(state_folder)/'install-update.ps1'
    script.write_text('''param([int]$AppProcessId,[string]$Setup,[string]$InstallDir,[string]$PreviousExe)
$ErrorActionPreference = 'Stop'
Wait-Process -Id $AppProcessId -ErrorAction SilentlyContinue
try {
    $installer = Start-Process -FilePath $Setup -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/DIR="' + $InstallDir + '"')) -WindowStyle Hidden -Wait -PassThru
    if ($installer.ExitCode -ne 0) { throw ('Setup exit: ' + $installer.ExitCode) }
    Start-Process -FilePath (Join-Path $InstallDir 'BewakeAIDownloadManager.exe') -ArgumentList '--tray' -WindowStyle Hidden
} catch {
    $_ | Out-File -FilePath (Join-Path $PSScriptRoot 'update-install.log') -Append
    Start-Process -FilePath $PreviousExe -WindowStyle Hidden
}
''',encoding='utf-8-sig')
    subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',str(script),'-AppProcessId',str(os.getpid()),'-Setup',str(path),'-InstallDir',str(Path(sys.executable).parent),'-PreviousExe',sys.executable],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
