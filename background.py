"""Windows startup registration and a thread-safe system tray bridge."""
import os, subprocess, sys
from pathlib import Path
from branding import NAME

RUN_KEY=r'Software\Microsoft\Windows\CurrentVersion\Run'
STARTUP_NAME='BewakeAI'

def startup_command():
    if getattr(sys,'frozen',False): command=[sys.executable]
    else:
        executable=Path(sys.executable)
        windowless=executable.with_name('pythonw.exe')
        command=[str(windowless if windowless.exists() else executable),str(Path(__file__).with_name('app.py').resolve())]
    return subprocess.list2cmdline([*command,'--tray'])

def startup_enabled():
    if os.name!='nt': return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,RUN_KEY) as key:
            value,_=winreg.QueryValueEx(key,STARTUP_NAME)
            return bool(value)
    except FileNotFoundError: return False

def set_startup(enabled):
    if os.name!='nt': raise OSError('Autostart ist nur unter Windows verfügbar.')
    import winreg
    if enabled:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,RUN_KEY,0,winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key,STARTUP_NAME,0,winreg.REG_SZ,startup_command())
    else:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,RUN_KEY,0,winreg.KEY_SET_VALUE) as key: winreg.DeleteValue(key,STARTUP_NAME)
        except FileNotFoundError: pass

def tray_image():
    from PIL import Image, ImageDraw
    image=Image.new('RGBA',(64,64),(0,0,0,0)); draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((2,2,62,62),radius=16,fill='#1b2432',outline='#397df4',width=3)
    draw.line([(19,16),(19,48)],fill='#e8edf5',width=6)
    draw.arc((18,15,44,34),-90,90,fill='#e8edf5',width=5)
    draw.arc((18,31,46,49),-90,90,fill='#e8edf5',width=5)
    draw.ellipse((43,43,56,56),fill='#397df4')
    return image

class Tray:
    def __init__(self,events):
        self.events=events; self.ready=False; self.stopped=False; self.paused=False
        self.icon=None
    def start(self):
        import pystray
        menu=pystray.Menu(
            pystray.MenuItem('Öffnen',lambda:self.events.put(('show',None)),default=True),
            pystray.MenuItem('Überwachung pausieren',lambda:self.events.put(('pause',None)),checked=lambda item:self.paused),
            pystray.MenuItem('Einstellungen',lambda:self.events.put(('settings',None))),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Beenden',lambda:self.events.put(('quit',None))))
        self.icon=pystray.Icon('BewakeAI',tray_image(),NAME,menu)
        def ready(icon):
            try:
                if self.stopped: return
                icon.visible=True; self.ready=True; self.events.put(('tray_ready',None))
            except Exception as error: self.events.put(('tray_error',str(error)))
        self.icon.run_detached(ready)
    def update(self,paused):
        self.paused=paused
        if self.ready and self.icon is not None:
            self.icon.title=NAME+(' · Pausiert' if paused else ' · Überwachung aktiv')
            self.icon.update_menu()
    def stop(self):
        self.stopped=True; self.ready=False
        if self.icon is not None: self.icon.stop()

class SingleInstance:
    """A second launch signals the existing GUI instead of creating another watcher."""
    def __init__(self):
        self.mutex=None; self.event=None; self.existing=False
        if os.name!='nt': return
        import ctypes
        from ctypes import wintypes
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.CreateMutexW.argtypes=[wintypes.LPVOID,wintypes.BOOL,wintypes.LPCWSTR]; self.api.CreateMutexW.restype=wintypes.HANDLE
        self.api.CreateEventW.argtypes=[wintypes.LPVOID,wintypes.BOOL,wintypes.BOOL,wintypes.LPCWSTR]; self.api.CreateEventW.restype=wintypes.HANDLE
        self.api.SetEvent.argtypes=[wintypes.HANDLE]
        self.api.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
        self.api.CloseHandle.argtypes=[wintypes.HANDLE]
        self.mutex=self.api.CreateMutexW(None,False,'Local\\DownloadPilotPrototype')
        if not self.mutex: raise ctypes.WinError(ctypes.get_last_error())
        self.existing=ctypes.get_last_error()==183
        self.event=self.api.CreateEventW(None,False,False,'Local\\BewakeAI.ShowWindow')
        if not self.event: raise ctypes.WinError(ctypes.get_last_error())
    def show_existing(self):
        if self.event: self.api.SetEvent(self.event)
    def requested(self): return self.event is not None and self.api.WaitForSingleObject(self.event,0)==0
    def close(self):
        for handle in (self.event,self.mutex):
            if handle: self.api.CloseHandle(handle)
        self.event=None; self.mutex=None
