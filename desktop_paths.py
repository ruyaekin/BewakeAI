"""Read Comfy Desktop configuration without modifying its files or model folders."""
import json, os, shlex
from pathlib import Path
from core import SUBDIRS, import_paths

MODEL_DIRS={cat:Path(sub).name for cat,sub in SUBDIRS.items() if cat!='Workflow'}

def read_json(path,fallback):
    try:
        path=Path(path)
        if path.stat().st_size>8*1024*1024: return fallback
        return json.loads(path.read_text('utf-8-sig'))
    except (OSError,ValueError): return fallback

def absolute(value,base):
    if not isinstance(value,str) or not value.strip(): return None
    path=Path(os.path.expandvars(value)).expanduser()
    return (path if path.is_absolute() else Path(base)/path).resolve()

def unique(values): return list(dict.fromkeys(str(p) for p in values if p is not None))

def args(text):
    if not isinstance(text,str) or not text.strip(): return []
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        api=ctypes.windll.shell32
        api.CommandLineToArgvW.argtypes=[wintypes.LPCWSTR,ctypes.POINTER(ctypes.c_int)]
        api.CommandLineToArgvW.restype=ctypes.POINTER(wintypes.LPWSTR)
        count=ctypes.c_int(); pointer=api.CommandLineToArgvW('app.exe '+text,ctypes.byref(count))
        if not pointer: return []
        try: return [pointer[i] for i in range(1,count.value)]
        finally:
            ctypes.windll.kernel32.LocalFree.argtypes=[ctypes.c_void_p]
            ctypes.windll.kernel32.LocalFree(pointer)
    return shlex.split(text)

def flag(tokens,name):
    value=None
    for index,token in enumerate(tokens):
        if token==name and index+1<len(tokens): value=tokens[index+1]
        elif token.startswith(name+'='): value=token.split('=',1)[1]
    return value

def append_yaml(targets,file):
    import yaml
    try:
        for _,(category,path) in import_paths(file).items():
            targets[category]=unique([*targets.get(category,[]),path])
    except (OSError,ValueError,TypeError,yaml.YAMLError): pass

def comfy_root(path):
    for candidate in (path/'ComfyUI',path):
        if (candidate/'main.py').is_file() or (candidate/'models').is_dir(): return candidate
    return None

def find_desktop(roaming=None,local=None,home=None):
    roaming=Path(roaming or os.getenv('APPDATA',Path.home()/'AppData'/'Roaming'))
    local=Path(local or os.getenv('LOCALAPPDATA',Path.home()/'AppData'/'Local'))
    home=Path(home or Path.home()); result={}
    # Current official Comfy Desktop supports several installs and shared model roots.
    config_dir=roaming/'Comfy Desktop'
    settings=read_json(config_dir/'settings.json',{})
    if not isinstance(settings,dict): settings={}
    records=read_json(config_dir/'installations.json',[])
    if not isinstance(records,list): records=[]
    shared=[absolute(p,config_dir) for p in settings.get('modelsDirs',[]) if isinstance(p,str)] if isinstance(settings.get('modelsDirs',[]),list) else []
    for record in records:
        if not isinstance(record,dict) or record.get('sourceId')=='cloud' or record.get('status') in ('installing','failed'): continue
        install=absolute(record.get('installPath'),config_dir)
        if install is None: continue
        root=comfy_root(install)
        if root is None: continue
        tokens=args(record.get('launchArgs',''))
        base=absolute(flag(tokens,'--base-directory') or record.get('adoptedBaseDir'),install) or root
        user=absolute(flag(tokens,'--user-directory'),install) or base/'user'
        own=base/'models'
        # Downloads belong to this installation's own model library, never Shared.
        targets={cat:[str(own/sub)] for cat,sub in MODEL_DIRS.items()}
        targets['Workflow']=[str(user/'default'/'workflows')]
        name=record.get('name') or install.name
        result[f'Comfy Desktop · {name} | {root}']=targets
    # Older Electron Desktop uses a separate data basePath rather than its program folder.
    legacy_dir=roaming/'ComfyUI'; config=read_json(legacy_dir/'config.json',{})
    if isinstance(config,dict):
        base=absolute(config.get('basePath'),legacy_dir)
        if base is not None and base.is_dir():
            targets={cat:[str(base/sub)] for cat,sub in SUBDIRS.items()}
            result[f'Comfy Desktop (ältere Version) | {base}']=targets
    return result
