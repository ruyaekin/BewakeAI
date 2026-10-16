import tempfile, unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tkinter as tk
from tkinter import ttk
import background
from app import App

class BackgroundTests(unittest.TestCase):
    def test_autostart_command_quotes_executable_and_uses_tray(self):
        with patch('background.sys.frozen',True,create=True),patch('background.sys.executable',r'C:\Program Files\Bewake AI\app.exe'):
            self.assertEqual(background.startup_command(),'"C:\\Program Files\\Bewake AI\\app.exe" --tray')
    def test_registry_switch_only_touches_own_value(self):
        with patch('winreg.CreateKeyEx') as create,patch('winreg.OpenKey') as open_key,patch('winreg.SetValueEx') as put,patch('winreg.DeleteValue') as delete:
            background.set_startup(True); self.assertEqual(put.call_args.args[1],background.STARTUP_NAME); self.assertTrue(put.call_args.args[4].endswith('--tray'))
            background.set_startup(False); self.assertEqual(delete.call_args.args[1],background.STARTUP_NAME)
    def app(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        app=App(Path(self.temp.name)/'state',first_run=False,enable_tray=False); app.paused=True; app.store.config['notifications']=False
        self.addCleanup(lambda:None if app._destroying else app.destroy()); return app
    def test_hide_restore_close_and_exit(self):
        app=self.app(); tray=MagicMock(); tray.ready=True; app.tray=tray
        self.assertTrue(app.hide_to_tray()); self.assertEqual(app.state(),'withdrawn'); self.assertTrue(app.in_tray)
        app.show_window(); self.assertEqual(app.state(),'normal'); self.assertFalse(app.in_tray)
        app.close(); self.assertTrue(app.in_tray); self.assertFalse(app._destroying)
        app.quit_app(); self.assertTrue(app._destroying); tray.stop.assert_called_once()
    def test_missing_tray_does_not_hide_window(self):
        app=self.app(); self.assertFalse(app.hide_to_tray()); self.assertFalse(app.in_tray)
    def test_close_can_really_exit_when_disabled(self):
        app=self.app(); app.tray=MagicMock(); app.tray.ready=True; app.store.config['close_to_tray']=False
        app.close(); self.assertTrue(app._destroying)
    def test_background_watcher_still_processes_download(self):
        app=self.app(); app.tray=MagicMock(); app.tray.ready=True; app.hide_to_tray()
        source=Path(self.temp.name)/'image.png'; source.write_bytes(b'example')
        app.add((str(source),('Bild','Dateiendung'))); self.assertEqual(len(app.tree.get_children()),1); self.assertFalse(app.store.config['auto'])
    def test_startup_setting_does_not_enable_sorting(self):
        app=self.app()
        with patch('background.startup_enabled',return_value=False),patch('background.set_startup') as startup:
            app.settings(); win=next(w for w in app.winfo_children() if isinstance(w,tk.Toplevel))
            for w in win.winfo_children():
                if isinstance(w,ttk.Checkbutton) and w.cget('text').startswith('Mit Windows starten'): w.invoke()
            next(w for w in win.winfo_children() if isinstance(w,ttk.Button) and w.cget('text')=='Speichern').invoke()
            startup.assert_called_once_with(True)
            self.assertFalse(app.store.config['auto'])

if __name__=='__main__': unittest.main()
