"""Persistent boundary between old files and downloads created after activation."""
import os,time
from pathlib import Path
from core import SUBDIRS

GENERAL=['Bild','Video','Audio','Dokument','Archiv','Programm','Sonstiges']

def identity(path):
    stat=Path(path).stat()
    return getattr(stat,'st_birthtime_ns',stat.st_ctime_ns)

def key(path): return os.path.normcase(str(Path(path).resolve()))

def activate(config,folder):
    folder=Path(folder)
    if not folder.is_absolute() or not folder.is_dir(): raise ValueError('Bitte einen vorhandenen Download-Ordner wählen.')
    since=time.time_ns(); baseline={}
    for path in folder.iterdir():
        if path.is_file():
            try: baseline[key(path)]=identity(path)
            except OSError: continue
    config.update(auto_new=True,auto_since_ns=since,auto_baseline=baseline,auto_folder=key(folder))

def eligible(config,path):
    if not config.get('auto_new') or not config.get('auto_since_ns'): return False
    path=Path(path)
    if key(path.parent)!=config.get('auto_folder'): return False
    try: birth=identity(path)
    except OSError: return False
    return birth>=config['auto_since_ns'] and config.get('auto_baseline',{}).get(key(path))!=birth

def destination(config,category):
    if category in SUBDIRS:
        paths=config.get('installations',{}).get(config.get('routing_installation',''),{})
        value=paths.get(category,[])
        return value[0] if isinstance(value,list) and value else value if isinstance(value,str) else ''
    return config.get('targets',{}).get(category,'') if category in GENERAL else ''
