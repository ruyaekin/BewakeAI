"""Local first-run defaults and optional Ollama bootstrap."""
import json, os, shutil, subprocess, time
from pathlib import Path
from urllib.request import Request, urlopen
from core import discover, SUBDIRS
from desktop_paths import find_desktop

MODEL='qwen3:4b'

def windows_folder(name,fallback):
    if os.name=='nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
                return Path(os.path.expandvars(winreg.QueryValueEx(key,name)[0]))
        except OSError: pass
    return Path.home()/fallback

def defaults():
    return {'downloads':str(windows_folder('{374DE290-123F-4565-9164-39C4925E467B}','Downloads')),
            'targets':{'Bild':str(windows_folder('My Pictures','Pictures')/'Bewake AI'),
                       'Video':str(windows_folder('My Video','Videos')/'Bewake AI'),
                       'Audio':str(windows_folder('My Music','Music')/'Bewake AI'),
                       'Dokument':str(windows_folder('Personal','Documents')/'Bewake AI'),
                       'Archiv':str(windows_folder('Personal','Documents')/'Bewake AI'/'Archive'),
                       'Programm':str(windows_folder('Personal','Documents')/'Bewake AI'/'Programme'),
                       'Sonstiges':str(windows_folder('Personal','Documents')/'Bewake AI'/'Sonstiges')}}

def find_installations(roots=None):
    result=find_desktop() if roots is None else {}
    if roots is None:
        roots=[Path.home(),windows_folder('Desktop','Desktop'),windows_folder('Personal','Documents'),Path(defaults()['downloads'])]
        roots += [Path(f'{drive}:/')/suffix for drive in ('C','D','E','F') for suffix in ('AI','ComfyUI','ComfyUI_windows_portable')]
    desktop_roots={key.split(' | ',1)[1] for key in result if ' | ' in key}
    for root in roots:
        try:
            for path in discover(root):
                if str(path) not in desktop_roots: result[str(path)]={cat:str(path/sub) for cat,sub in SUBDIRS.items()}
        except OSError: continue
    return result

def models():
    with urlopen('http://127.0.0.1:11434/api/tags',timeout=3) as response: data=json.load(response)
    return [m['name'] for m in data.get('models',[]) if ':cloud' not in m['name'] and not m.get('remote_host')]

def ollama_exe():
    path=shutil.which('ollama')
    if path: return path
    path=Path(os.getenv('LOCALAPPDATA',''))/'Programs'/'Ollama'/'ollama.exe'
    return str(path) if path.is_file() else None

def setup_ai(state_folder,progress):
    """Only invoked after the user selects the explicit install/download button."""
    state_folder=Path(state_folder); state_folder.mkdir(parents=True,exist_ok=True)
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    with (state_folder/'ki-setup.log').open('a',encoding='utf-8') as log:
        try: available=models()
        except Exception: available=None
        if available is None:
            exe=ollama_exe()
            if not exe:
                winget=shutil.which('winget')
                if not winget: raise RuntimeError('Windows-App-Installer (winget) fehlt. Bitte Ollama von ollama.com/download/windows installieren und erneut versuchen.')
                progress('Ollama wird installiert … das kann einige Minuten dauern.')
                result=subprocess.run([winget,'install','--id','Ollama.Ollama','--exact','--source','winget','--silent','--accept-package-agreements','--accept-source-agreements','--disable-interactivity'],stdout=log,stderr=log,creationflags=flags,timeout=1800)
                exe=ollama_exe()
                if result.returncode!=0 or not exe: raise RuntimeError('Ollama-Installation nicht abgeschlossen. Details: '+str(state_folder/'ki-setup.log'))
            progress('Lokaler KI-Dienst wird gestartet …')
            try: available=models()
            except Exception:
                env=os.environ.copy(); env['OLLAMA_HOST']='127.0.0.1:11434'
                subprocess.Popen([exe,'serve'],stdout=log,stderr=log,creationflags=flags,env=env)
                for _ in range(60):
                    try: available=models(); break
                    except Exception: time.sleep(1)
                else: raise RuntimeError('Ollama-Dienst startet nicht. Details im KI-Setup-Protokoll.')
        if MODEL not in available:
            progress('Lokales Modell wird geladen (ca. 2,5 GB) …')
            request=Request('http://127.0.0.1:11434/api/pull',data=json.dumps({'model':MODEL,'stream':True}).encode(),headers={'Content-Type':'application/json'})
            with urlopen(request,timeout=180) as response:
                success=False
                for raw in response:
                    item=json.loads(raw)
                    if item.get('error'): raise RuntimeError(item['error'])
                    total=item.get('total',0); completed=item.get('completed',0)
                    progress(f'Modell-Download: {completed/total:.0%}' if total else item.get('status','Modell wird eingerichtet …'))
                    success=item.get('status')=='success'
                if not success: raise RuntimeError('Modell-Download wurde nicht abgeschlossen. Erneutes Einrichten setzt den Download fort.')
        progress('Lokale KI ist eingerichtet.')
        return MODEL
