import json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from app import App
from core import Store,classify,SUBDIRS
from routing import activate,eligible,destination

class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name); self.downloads=self.root/'downloads'; self.downloads.mkdir(); self.store=Store(self.root/'state')
        self.store.config['downloads']=str(self.downloads)
    def tearDown(self): self.temp.cleanup()
    def test_existing_excluded_even_after_restart(self):
        old=self.downloads/'old.pdf'; old.write_bytes(b'old'); activate(self.store.config,self.downloads); self.store.save()
        self.assertFalse(eligible(Store(self.store.folder).config,old))
        old.write_bytes(b'changed'); self.assertFalse(eligible(self.store.config,old))
    def test_new_file_eligible_and_persistent(self):
        activate(self.store.config,self.downloads); time.sleep(.015); new=self.downloads/'new.pdf'; new.write_bytes(b'new'); self.store.save()
        self.assertTrue(eligible(Store(self.store.folder).config,new))
    def test_partial_download_started_before_activation_stays_excluded(self):
        part=self.downloads/'old.pdf.crdownload'; part.write_bytes(b'old'); activate(self.store.config,self.downloads); ready=part.with_suffix(''); part.rename(ready)
        self.assertFalse(eligible(self.store.config,ready))
    def test_wrong_folder_not_eligible(self):
        activate(self.store.config,self.downloads); other=self.root/'new.pdf'; other.write_bytes(b'new'); self.assertFalse(eligible(self.store.config,other))
    def test_routes_use_selected_install(self):
        c=self.store.config; c.update(routing_installation='A',installations={'A':{'LoRA':['C:/A/models/loras']},'B':{'LoRA':['D:/B/models/loras']}},targets={'Bild':'E:/images'})
        self.assertEqual(destination(c,'LoRA'),'C:/A/models/loras'); self.assertEqual(destination(c,'Bild'),'E:/images'); self.assertEqual(destination(c,'Unbekannt'),'')
    def test_ordinary_unknown_files_and_programs(self):
        for name,category in [('setup.exe','Programm'),('file.weird','Sonstiges'),('notes.json','Dokument'),('unknown.safetensors','Unbekannt')]:
            p=self.downloads/name; p.write_bytes(b'example'); self.assertEqual(classify(p)[0],category)
    def test_gui_only_new_download_auto_moves(self):
        app=App(self.root/'gui-state',first_run=False,enable_tray=False); app.withdraw(); app.paused=True; app.store.config['notifications']=False
        app.store.config.update(downloads=str(self.downloads),targets={'Dokument':str(self.root/'documents')})
        old=self.downloads/'old.pdf'; old.write_bytes(b'old'); activate(app.store.config,self.downloads)
        try:
            app.add((str(old),('Dokument','Dateiendung'))); self.assertFalse(app.busy); self.assertTrue(old.exists())
            time.sleep(.015); new=self.downloads/'new.pdf'; new.write_bytes(b'new'); app.add((str(new),('Dokument','Dateiendung')))
            self.drain(app); self.assertFalse(new.exists()); self.assertTrue((self.root/'documents'/'new.pdf').exists()); self.assertTrue(old.exists())
            app.undo(); self.drain(app); self.assertTrue(new.exists()); self.assertFalse(eligible(app.store.config,new)); self.assertIn(str(new),app.done)
        finally: app.destroy()
    def test_routing_dialog_saves_all_targets_and_boundary(self):
        from routes_ui import open_routes
        from tkinter import ttk
        from routing import GENERAL
        app=App(self.root/'gui-state',first_run=False,enable_tray=False); app.withdraw(); app.paused=True; app.store.config['downloads']=str(self.downloads)
        old=self.downloads/'old.pdf'; old.write_bytes(b'old')
        targets={cat:str(self.root/cat) for cat in GENERAL}; models={'Desktop A':{cat:[str(self.root/'ComfyUI'/sub)] for cat,sub in SUBDIRS.items()}}
        try:
            win=open_routes(app,models,targets)
            footer=next(w for w in win.winfo_children() if isinstance(w,ttk.Frame) and any(isinstance(b,ttk.Button) for b in w.winfo_children())); next(w for w in footer.winfo_children() if isinstance(w,ttk.Button) and w.cget('text')=='Speichern und starten').invoke()
            self.assertTrue(app.store.config['auto_new']); self.assertEqual(app.store.config['routing_installation'],'Desktop A'); self.assertEqual(app.store.config['targets'],targets)
            self.assertFalse(eligible(app.store.config,old)); self.assertFalse(app.setup_open)
        finally: app.destroy()
    def drain(self,app):
        cb,result,error=app.q.get(timeout=5); app.busy=False
        if error: raise error
        cb(result)

if __name__=='__main__': unittest.main()
