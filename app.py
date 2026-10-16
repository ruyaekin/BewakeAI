import os, sys, json, threading, queue, tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from core import *
import theme
from theme import messagebox, simpledialog
import onboarding
from branding import NAME, VERSION, default_state
import background
import routing
from routes_ui import open_routes
import updater

class App(tk.Tk):
    def __init__(self,data=None,first_run=True,enable_tray=True,start_hidden=False,instance=None):
        super().__init__(); self.title(NAME+' · '+VERSION); self.geometry('1180x820'); self.minsize(1000,720)
        self.start_hidden=start_hidden and enable_tray
        if self.start_hidden: self.withdraw()
        self.store=Store(data or default_state())
        self.mover=Mover(self.store); self.stability=Stability(); self.pending={}; self.done=set(); self.q=queue.Queue(); self.busy=False; self.paused=False
        self.done_versions={}; self.routing_window=None
        self.available_update=None
        self.progress=queue.Queue(); self.setup_open=False; self.setup_window=None
        self.events=queue.Queue(); self.tray=None; self.instance=instance; self.in_tray=False; self._minimize_pending=False; self._hidden_windows=[]; self._destroying=False
        theme.apply(self)
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.bind('<Unmap>',self.minimized,add='+')
        ttk.Label(self,text=NAME,font=('Segoe UI',24,'bold')).pack(anchor='w',padx=20,pady=(15,0))
        ttk.Label(self,text='Downloads prüfen · Ziel auswählen · sicher verschieben',font=('Segoe UI',11)).pack(anchor='w',padx=22,pady=(0,10))
        bar=ttk.Frame(self); bar.pack(fill='x',padx=20)
        for label,fn in [('Einrichtung',self.setup),('Download-Ordner',self.downloads),('Comfy Desktop erkennen',self.desktop_detect),('Zielordner & Automatik',self.routing_setup),('Zielpfad setzen',self.target),('Einstellungen',self.settings),('Pause / Fortsetzen',self.pause)]: ttk.Button(bar,text=label,command=fn).pack(side='left',padx=2)
        self.info=tk.StringVar(); ttk.Label(self,textvariable=self.info).pack(anchor='w',padx=22,pady=10)
        self.tree=ttk.Treeview(self,columns=('category','reason','size'),show='tree headings',selectmode='browse'); self.tree.heading('#0',text='Datei'); self.tree.column('#0',width=330)
        for c,t,w in [('category','Vorschlag',100),('reason','Erkennung',380),('size','MB',70)]: self.tree.heading(c,text=t); self.tree.column(c,width=w)
        self.tree.pack(fill='both',expand=True,padx=20); self.tree.bind('<<TreeviewSelect>>',self.select)
        install_row=ttk.Frame(self); install_row.pack(fill='x',padx=20,pady=(12,0))
        ttk.Label(install_row,text='Installation / Modellbibliothek').pack(side='left',padx=(0,12))
        self.installation=tk.StringVar(); self.install_combo=ttk.Combobox(install_row,textvariable=self.installation,state='readonly'); self.install_combo.pack(side='left',fill='x',expand=True)
        self.install_combo.bind('<<ComboboxSelected>>',lambda e:self.refresh_targets())
        ttk.Button(install_row,text='Ordner manuell hinzufügen',command=self.install).pack(side='left',padx=(8,0))
        panel=ttk.Frame(self); panel.pack(fill='x',padx=20,pady=10)
        self.category=tk.StringVar(value='Unbekannt'); ttk.Combobox(panel,textvariable=self.category,values=CATEGORIES,state='readonly',width=15).pack(side='left'); self.category.trace_add('write',lambda *_:self.refresh_targets())
        self.destination=tk.StringVar(); self.combo=ttk.Combobox(panel,textvariable=self.destination,width=35); self.combo.pack(side='left',padx=8,fill='x',expand=True)
        ttk.Button(panel,text='Ordner wählen',command=self.browse).pack(side='left'); ttk.Button(panel,text='Verschieben',style='Accent.TButton',command=self.move).pack(side='left',padx=8)
        actions=ttk.Frame(self); actions.pack(fill='x',padx=20)
        for label,fn in [('Vorschau / Details',self.preview),('Lokale KI fragen',self.ai),('Regel merken',self.remember),('Regeln',self.rules),('Ignorieren',self.ignore),('Undo',self.undo),('Protokoll',self.log),('Updates',lambda:self.check_updates(True))]: ttk.Button(actions,text=label,command=fn).pack(side='left',padx=3)
        self.status=tk.StringVar(value='Bereit. Automatik ist standardmäßig aus. Dateien müssen mindestens 10 Sekunden stabil sein.')
        ttk.Label(self,textvariable=self.status,wraplength=1050).pack(anchor='w',padx=22,pady=15)
        self.refresh_targets()
        self._scan_after=self.after(500,self.tick)
        self._tray_after=self.after(100,self.poll_events)
        if first_run: self._update_after=self.after(15000,self.scheduled_update)
        if enable_tray:
            try:
                self.tray=background.Tray(self.events); self.tray.start()
                self.after(4000,self.verify_tray)
            except Exception as e:
                self.store.log('tray_error',message=str(e)); self.status.set('Tray nicht verfügbar; das Programm bleibt über die Taskleiste erreichbar.'); self.deiconify()
        if first_run and not self.store.config.get('setup_complete'):
            self.start_hidden=False; self.deiconify()
            self.setup_open=True
            self.after(200,self.setup)
    def close(self):
        if self.store.config['close_to_tray'] and self.tray is not None and self.tray.ready:
            self.hide_to_tray(); return
        self.quit_app()
    def quit_app(self):
        if self.busy:
            self.show_window(); messagebox.showinfo('Vorgang läuft','Bitte den laufenden Vorgang abwarten, bevor Bewake AI Download Manager beendet wird.'); return
        self.destroy()
    def destroy(self):
        if self._destroying: return
        self._destroying=True
        for name in ('_scan_after','_tray_after','_update_after'):
            value=getattr(self,name,None)
            if value is not None:
                try: self.after_cancel(value)
                except tk.TclError: pass
        if self.tray is not None:
            try: self.tray.stop()
            except Exception: pass
        super().destroy()
    def minimized(self,event):
        if event.widget is self and not self._destroying and self.state()=='iconic':
            self._minimize_pending=True
            if self.tray is not None and self.tray.ready: self.hide_to_tray()
    def verify_tray(self):
        if not self._destroying and self.tray is not None and not self.tray.ready:
            self.show_window(); self.status.set('Tray nicht verfügbar. Das Fenster bleibt geöffnet und erreichbar.')
    def hide_to_tray(self):
        if self.tray is None or not self.tray.ready: return False
        if self.grab_current() is not None:
            self.deiconify(); self.status.set('Bitte zuerst den geöffneten Dialog abschließen.'); return False
        self._hidden_windows=[]
        for child in self.winfo_children():
            if isinstance(child,tk.Toplevel) and child.state() in ('normal','iconic'):
                self._hidden_windows.append(child); child.withdraw()
        self.withdraw(); self.in_tray=True; self._minimize_pending=False
        return True
    def show_window(self):
        self.start_hidden=False; self._minimize_pending=False; self.in_tray=False
        self.deiconify(); self.lift(); self.focus_force()
        for child in self._hidden_windows:
            if child.winfo_exists(): child.deiconify()
        self._hidden_windows=[]
    def poll_events(self):
        if self._destroying: return
        if self.instance is not None and self.instance.requested(): self.show_window()
        try:
            while True:
                event,value=self.events.get_nowait()
                if event=='show': self.show_window()
                elif event=='pause': self.pause()
                elif event=='settings': self.show_window(); self.settings()
                elif event=='quit': self.quit_app()
                elif event=='tray_ready':
                    self.tray.update(self.paused)
                    if self.start_hidden or self._minimize_pending: self.hide_to_tray()
                elif event=='tray_error':
                    self.store.log('tray_error',message=value); self.show_window(); self.status.set('Tray konnte nicht gestartet werden: '+str(value))
                if self._destroying: return
        except queue.Empty: pass
        self._tray_after=self.after(100,self.poll_events)
    def selected(self):
        ids=self.tree.selection(); return self.pending.get(ids[0]) if ids else None
    def error(self,e):
        self.status.set(str(e)); self.store.log('error',message=str(e))
        if self.in_tray: self.notify('Aktion erforderlich',str(e))
        else: messagebox.showerror('Bewake AI Download Manager',str(e))
    def notify(self,title,message):
        if not self.store.config['notifications']: return
        try:
            from windows_toasts import WindowsToaster, Toast
            toast=Toast(); toast.text_fields=[title,message,'Bewake AI über das Symbol neben der Uhr öffnen.']
            toast.on_activated=lambda _:self.events.put(('show',None))
            WindowsToaster(NAME).show_toast(toast)
        except Exception as e: self.store.log('notification_error',message=str(e))
    def background(self,fn,callback):
        if self.busy: return
        self.busy=True; self.status.set('Wird geprüft … große Modelle können etwas dauern.')
        def run():
            try: self.q.put((callback,fn(),None))
            except Exception as e: self.q.put((callback,None,e))
        threading.Thread(target=run,daemon=True).start()
    def tick(self):
        try:
            while True: self.status.set(self.progress.get_nowait())
        except queue.Empty: pass
        try:
            while True:
                cb,result,err=self.q.get_nowait(); self.busy=False
                if err: self.error(err)
                else: cb(result)
                if self._destroying: return
        except queue.Empty: pass
        mode=' · Neue Downloads automatisch' if self.store.config.get('auto_new') else ' · Regelautomatik AN' if self.store.config['auto'] else ' · Bestätigung erforderlich'
        self.info.set(('PAUSIERT · ' if self.paused else 'Überwachung · ')+self.store.config['downloads']+mode)
        if not self.paused and not self.busy and not self.setup_open:
            try:
                for p in Path(self.store.config['downloads']).iterdir():
                    key=str(p)
                    if key in self.done:
                        if self.done_versions.get(key)==routing.identity(p): continue
                        self.done.discard(key)
                    if any(v['path']==key for v in self.pending.values()): continue
                    if self.stability.ready(p):
                        self.background(lambda p=p:(str(p),classify(p)),self.add); break
            except OSError as e: self.status.set('Überwachung: '+str(e))
        self._scan_after=self.after(1500,self.tick)
    def add(self,result):
        path,(cat,reason)=result; p=Path(path)
        if not p.exists(): return
        rule=self.store.rule(p)
        if rule: cat=rule['category']; reason='Bestätigte Regel: '+rule['pattern']
        iid=self.tree.insert('', 'end',text=p.name,values=(cat,reason,round(p.stat().st_size/1048576,2)))
        self.pending[iid]={'path':path,'category':cat,'reason':reason,'identity':routing.identity(p)}; self.status.set('Neuer Vorschlag: '+p.name)
        auto_target=''
        if self.store.config.get('auto_new'):
            if routing.eligible(self.store.config,p): auto_target=routing.destination(self.store.config,cat)
        elif rule and rule.get('auto') and self.store.config['auto']: auto_target=rule['target']
        if auto_target:
            def moved(dst):
                self.removed(iid,'Automatisch verschoben: '+str(dst)); self.notify('Bewake AI: Automatisch abgelegt',p.name+' → '+str(dst.parent))
            self.background(lambda:self.mover.move(path,auto_target),moved)
        else: self.notify('Bewake AI: Download bereit',p.name+' · '+cat)
    def select(self,*_):
        item=self.selected()
        if item: self.category.set(item['category']); self.refresh_targets()
    def refresh_targets(self):
        cat=self.category.get(); values=[]
        names=list(self.store.config['installations'])
        self.install_combo['values']=names
        if self.installation.get() not in names:
            preferred=next((name for name in names if name.startswith('Comfy Desktop')),names[0] if names else '')
            self.installation.set(preferred)
        for name,paths in self.store.config['installations'].items():
            if name!=self.installation.get(): continue
            if cat in paths: values.extend(paths[cat] if isinstance(paths[cat],list) else [paths[cat]])
        if cat in self.store.config['targets']: values.append(self.store.config['targets'][cat])
        self.combo['values']=values; self.destination.set(values[0] if values else '')
    def desktop_detect(self):
        if self.busy: return
        def found(paths):
            if not paths:
                messagebox.showinfo('Comfy Desktop','Keine lokale Desktop-Installation gefunden. Starte Comfy Desktop einmal oder wähle den Datenordner manuell.'); return
            self.store.config['installations'].update(paths); self.store.save()
            self.installation.set(next(iter(paths))); self.refresh_targets()
            self.status.set(f'{len(paths)} Desktop-Installation(en) erkannt. Modellziele und Workflows sind pro Installation auswählbar.')
        self.background(onboarding.find_desktop,found)
    def browse(self):
        p=filedialog.askdirectory()
        if p: self.destination.set(p)
    def downloads(self):
        p=filedialog.askdirectory(title='Zu überwachenden Download-Ordner wählen')
        if p:
            self.store.config['downloads']=p
            if self.store.config.get('auto_new'): routing.activate(self.store.config,p)
            self.store.save(); self.stability=Stability(); self.done.clear()
    def routing_setup(self):
        if self.routing_window is not None and self.routing_window.winfo_exists(): self.routing_window.lift(); return
        if self.busy: return messagebox.showinfo('Vorgang läuft','Bitte den laufenden Vorgang abwarten.')
        detected=onboarding.find_desktop()
        self.routing_window=open_routes(self,detected,onboarding.defaults()['targets'])
        return self.routing_window
    def install(self):
        root=filedialog.askdirectory(title='ComfyUI oder Portable-Ordner wählen')
        if not root: return
        found=discover(root)
        if not found: return messagebox.showinfo('ComfyUI','Keine Installation mit models-Ordner gefunden. Zielpfade können einzeln gesetzt werden.')
        for p in found: self.store.config['installations'][str(p)]={c:str(p/sub) for c,sub in SUBDIRS.items()}
        self.store.save(); self.refresh_targets(); self.status.set(f'{len(found)} Installation(en) hinzugefügt. Zielpfade vor dem Verschieben prüfen.')
    def yaml(self):
        p=filedialog.askopenfilename(filetypes=[('ComfyUI-Pfade','*.yaml *.yml')])
        if not p: return
        try:
            for name,(cat,path) in import_paths(p).items(): self.store.config['installations'][name]={cat:path}
            self.store.save(); self.refresh_targets()
        except Exception as e: self.error(e)
    def target(self):
        self.browse()
        if self.destination.get(): self.store.config['targets'][self.category.get()]=self.destination.get(); self.store.save()
    def pause(self):
        self.paused=not self.paused
        if self.tray is not None: self.tray.update(self.paused)
    def setup(self):
        if self.setup_window is not None and self.setup_window.winfo_exists(): self.setup_window.lift(); return
        if self.busy: return messagebox.showinfo('Vorgang läuft','Bitte den laufenden Vorgang abwarten.')
        win=tk.Toplevel(self); self.setup_window=win; self.setup_open=True; win.title('Bewake AI Download Manager einrichten'); win.geometry('820x740'); win.minsize(760,700); win.transient(self)
        buttons=ttk.Frame(win,padding=(24,8,24,20)); buttons.pack(side='bottom',fill='x')
        frame=ttk.Frame(win,padding=24); frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Startklar in wenigen Schritten',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(frame,text='Ordner prüfen, Comfy Desktop verbinden und auf Wunsch lokale KI einrichten.',style='Muted.TLabel').pack(anchor='w',pady=(6,20))
        default=onboarding.defaults(); paths=dict(self.store.config['installations'])
        download=tk.StringVar(value=self.store.config['downloads'] if self.store.file.exists() else default['downloads'])
        ttk.Label(frame,text='1  ·  Downloads überwachen',font=('Segoe UI',12,'bold')).pack(anchor='w')
        row=ttk.Frame(frame); row.pack(fill='x',pady=(8,16)); ttk.Entry(row,textvariable=download).pack(side='left',fill='x',expand=True)
        def choose():
            p=filedialog.askdirectory(parent=win,title='Download-Ordner wählen')
            if p: download.set(p)
        ttk.Button(row,text='Ändern',command=choose).pack(side='left',padx=(8,0))
        ttk.Label(frame,text='2  ·  Comfy Desktop und Zielordner',font=('Segoe UI',12,'bold')).pack(anchor='w')
        details=tk.Text(frame,height=6,wrap='word',relief='flat',padx=10,pady=10); details.pack(fill='both',expand=True,pady=8)
        def refresh():
            details.config(state='normal'); details.delete('1.0','end')
            details.insert('end','Desktop-Installationen / weitere ComfyUI-Ordner:\n')
            if not paths: details.insert('end','Noch keine Installation gefunden. Comfy Desktop einmal starten oder Datenordner hinzufügen.\n')
            for name,targets in paths.items():
                details.insert('end',name+'\n')
                for category in ('LoRA','Workflow'):
                    value=targets.get(category,[]); value=value[0] if isinstance(value,list) and value else value
                    if value: details.insert('end',f'  {category}: {value}\n')
            details.insert('end','\nWeitere Ziele (jederzeit änderbar):\n')
            for cat,path in {**default['targets'],**self.store.config['targets']}.items(): details.insert('end',f'{cat}: {path}\n')
            details.config(state='disabled')
        row=ttk.Frame(frame); row.pack(fill='x')
        def add_root():
            root=filedialog.askdirectory(parent=win,title='ComfyUI oder Portable-Ordner wählen')
            if root:
                found=onboarding.find_installations([Path(root)])
                if not found: messagebox.showinfo('ComfyUI','Kein ComfyUI-models-Ordner gefunden. Du kannst Ziele später einzeln festlegen.',parent=win)
                paths.update(found); refresh()
        def detected(result):
            found,available=result; paths.update(found); refresh(); model_box['values']=['',*available]
            self.status.set(f'{len(found)} ComfyUI-Installation(en) und {len(available)} lokale KI-Modell(e) gefunden.')
        def scan():
            def work():
                found=onboarding.find_installations()
                try: available=onboarding.models()
                except Exception: available=[]
                return found,available
            self.background(work,detected)
        ttk.Button(row,text='Desktop automatisch erkennen',command=scan).pack(side='left')
        ttk.Button(row,text='Datenordner manuell hinzufügen',command=add_root).pack(side='left',padx=8)
        ttk.Label(frame,text='3  ·  Lokale KI (optional)',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(18,8))
        model=tk.StringVar(value=self.store.config['model']); model_box=ttk.Combobox(frame,textvariable=model,values=[''],width=45); model_box.pack(anchor='w')
        ttk.Label(frame,text='Leer lassen: sofort ohne KI nutzbar. Automatisches KI-Setup benötigt Internet\nund mehrere GB Speicherplatz; das Modell allein ist ca. 2,5 GB groß.',style='Muted.TLabel').pack(anchor='w',pady=8)
        ttk.Button(frame,text='Ollama + lokales Modell automatisch einrichten',command=lambda:self.ai_setup(model)).pack(anchor='w')
        ttk.Label(frame,textvariable=self.status,wraplength=750,style='Muted.TLabel').pack(anchor='w',pady=(12,0))
        def finish():
            if self.busy: return messagebox.showinfo('Einrichtung läuft','Bitte die laufende Suche oder KI-Einrichtung abwarten.',parent=win)
            p=Path(download.get())
            if not p.is_absolute() or not p.is_dir(): return messagebox.showerror('Download-Ordner','Bitte einen vorhandenen absoluten Ordner auswählen.',parent=win)
            self.store.config.update(downloads=str(p),installations=paths,targets={**default['targets'],**self.store.config['targets']},model=model.get().strip(),setup_complete=True)
            if self.store.config.get('auto_new') and self.store.config.get('auto_folder')!=routing.key(p): routing.activate(self.store.config,p)
            self.store.save(); self.stability=Stability(); self.refresh_targets(); self.setup_open=False; self.paused=False; win.destroy(); self.status.set('Einrichtung abgeschlossen. Bitte jetzt die Zielordner prüfen und die neue Automatik wählen.')
            self.after(50,self.routing_setup)
        def later():
            if self.busy: return
            self.setup_open=False; self.paused=True; win.destroy(); self.status.set('Überwachung pausiert. Einrichtung über die Schaltfläche fortsetzen.')
        ttk.Button(buttons,text='Einrichtung abschließen',style='Accent.TButton',command=finish).pack(side='right')
        ttk.Button(buttons,text='Später',command=later).pack(side='right',padx=8)
        win.protocol('WM_DELETE_WINDOW',later); refresh(); win.grab_set(); scan()
    def ai_setup(self,model_var=None):
        if self.busy: return
        if not messagebox.askyesno('Lokale KI einrichten','Ollama wird bei Bedarf über Windows installiert. Danach wird qwen3:4b heruntergeladen (ca. 2,5 GB).\n\nPlane mindestens 8 GB freien Speicher ein. Der Download kann einige Minuten dauern.\n\nJetzt einrichten?'): return
        def done(model):
            self.store.config['model']=model; self.store.save()
            if model_var is not None: model_var.set(model)
            self.status.set('Lokale KI bereit: '+model)
        self.background(lambda:onboarding.setup_ai(self.store.folder,self.progress.put),done)
    def removed(self,iid,text):
        if iid in self.pending:
            item=self.pending.pop(iid); self.done.add(item['path']); self.done_versions[item['path']]=item['identity']; self.tree.delete(iid)
        self.status.set(text)
    def move(self):
        item=self.selected(); dest=self.destination.get()
        if not item or not dest: return messagebox.showinfo('Ziel fehlt','Datei und Zielordner auswählen.')
        if not Path(dest).is_absolute(): return self.error(ValueError('Bitte absoluten Zielpfad wählen'))
        if not messagebox.askyesno('Verschieben bestätigen',item['path']+'\n\n→ '+dest+'\n\nKategorie: '+self.category.get()): return
        iid=self.tree.selection()[0]; self.background(lambda:self.mover.move(item['path'],dest),lambda dst:self.removed(iid,'Verschoben: '+str(dst)))
    def ignore(self):
        if self.selected(): self.removed(self.tree.selection()[0],'Für diese Sitzung ignoriert.')
    def undo(self):
        def restored(p):
            self.done.add(str(p)); self.done_versions[str(p)]=routing.identity(p); self.store.config.setdefault('auto_baseline',{})[routing.key(p)]=routing.identity(p); self.store.save(); self.status.set('Wiederhergestellt; diese Datei bleibt von der Automatik ausgenommen: '+str(p))
        self.background(self.mover.undo,restored)
    def preview(self):
        item=self.selected()
        if not item: return
        def display(data):
            win=tk.Toplevel(self); win.title('Vorschau – keine Datei wird ausgeführt'); text=tk.Text(win,width=100,height=30,wrap='word'); text.pack(fill='both',expand=True); text.insert('1.0',data); text.config(state='disabled')
        def load():
            p=Path(item['path']); data=f'{p}\n{p.stat().st_size:,} Bytes\n{item["reason"]}\n\n'
            if p.suffix.lower() in ('.txt','.json','.csv','.yaml','.yml'):
                with p.open('r',encoding='utf-8',errors='replace') as f: data+=f.read(24000)
            else: data+=json.dumps(metadata(p),ensure_ascii=False,indent=2)[:24000]
            return data
        self.background(load,display)
    def ai(self):
        item=self.selected()
        if not item: return
        model=self.store.config['model']
        if not model: return messagebox.showinfo('Lokale KI','Unter Einstellungen den Namen eines bereits lokal installierten Ollama-Modells eintragen.')
        self.background(lambda:local_ai(item['path'],model),lambda cat:(self.category.set(cat),self.status.set('KI-Vorschlag: '+cat+' – manuell prüfen.')))
    def remember(self):
        item=self.selected(); target=self.destination.get()
        if not item or not Path(target).is_absolute(): return messagebox.showinfo('Regel','Datei und absoluten Zielpfad auswählen.')
        pattern=simpledialog.askstring('Regel','Dateimuster (z. B. *lora*.safetensors):',initialvalue=Path(item['path']).name)
        if not pattern: return
        auto=messagebox.askyesno('Regelautomatik','Diese Regel künftig automatisch anwenden, wenn zusätzlich die globale Automatik eingeschaltet ist?\n\nMuster: '+pattern+'\nZiel: '+target)
        self.store.config['rules'].append(dict(pattern=pattern,category=self.category.get(),target=target,auto=auto)); self.store.save()
    def rules(self):
        win=tk.Toplevel(self); win.title('Regeln verwalten'); box=tk.Listbox(win,width=120,height=15); box.pack()
        for r in self.store.config['rules']: box.insert('end',f'{r["pattern"]} → {r["target"]} | Automatik: {r["auto"]}')
        def delete():
            if box.curselection(): i=box.curselection()[0]; self.store.config['rules'].pop(i); box.delete(i); self.store.save()
        ttk.Button(win,text='Ausgewählte Regel löschen',command=delete).pack()
    def scheduled_update(self):
        if self._destroying: return
        if self.busy or self.setup_open or self.grab_current() is not None:
            self._update_after=self.after(60000,self.scheduled_update); return
        if self.store.config.get('check_updates') and self.store.config.get('update_repo'): self.check_updates(False)
        self._update_after=self.after(2*60*60*1000,self.scheduled_update)
    def check_updates(self,manual=False):
        if self.busy: return self.status.set('Bitte den laufenden Vorgang abwarten und danach Updates öffnen.')
        repo=self.store.config.get('update_repo','').strip()
        if not repo:
            if manual: messagebox.showinfo('GitHub-Updates','Unter Einstellungen das GitHub-Repository eintragen, z. B. ruyaekin/BewakeAI.')
            return
        def work():
            try: return updater.check(repo,VERSION)
            except Exception as error:
                if manual: raise
                self.store.log('update_check_error',message=str(error)); return None
        def checked(update):
            self.available_update=update
            if update is None:
                if manual: messagebox.showinfo('Updates','Keine neuere veröffentlichte Version mit Windows-Setup gefunden. Ist das Repository öffentlich und der Release-Build abgeschlossen?')
                return
            self.status.set('Neue Version '+update['version']+' verfügbar. Über Updates herunterladen.')
            if self.store.config.get('install_updates_automatically'): self.download_update(update)
            elif manual:
                if messagebox.askyesno('Update verfügbar','Version '+update['version']+' herunterladen und installieren?\nDie App wird dafür kurz beendet und danach wieder gestartet. Einstellungen bleiben erhalten.'): self.download_update(update)
            else: self.notify('Bewake AI: Update verfügbar','Version '+update['version']+' · App öffnen und auf Updates klicken.')
        self.background(work,checked)
    def download_update(self,update):
        def ready(path):
            if self.grab_current() is not None:
                self.status.set('Update heruntergeladen. Bitte Dialog schließen und Updates erneut öffnen.'); return
            try:
                self.store.save(); updater.launch(update,path,self.store.folder)
            except Exception as error: return self.error(error)
            self.destroy()
        self.background(lambda:updater.download(update,self.store.folder),ready)
    def settings(self):
        win=tk.Toplevel(self); win.title('Einstellungen'); auto=tk.BooleanVar(value=self.store.config['auto']); notify=tk.BooleanVar(value=self.store.config['notifications'])
        win.transient(self)
        ttk.Label(win,text='Start und Hintergrundbetrieb',font=('Segoe UI',14,'bold')).pack(anchor='w',padx=15,pady=(15,8))
        try: current_startup=background.startup_enabled()
        except OSError as e: current_startup=False; self.store.log('startup_error',message=str(e))
        startup=tk.BooleanVar(value=current_startup); close_tray=tk.BooleanVar(value=self.store.config['close_to_tray'])
        ttk.Checkbutton(win,text='Mit Windows starten (direkt im Systemtray)',variable=startup).pack(anchor='w',padx=15)
        ttk.Checkbutton(win,text='Beim Schließen im Systemtray weiterlaufen',variable=close_tray).pack(anchor='w',padx=15)
        ttk.Label(win,text='Minimieren legt die App neben der Uhr ab. Vollständig beenden:\nRechtsklick auf das Tray-Symbol → Beenden.',style='Muted.TLabel').pack(anchor='w',padx=20,pady=8)
        ttk.Label(win,text='Downloads und Benachrichtigungen',font=('Segoe UI',12,'bold')).pack(anchor='w',padx=15,pady=(12,0))
        ttk.Checkbutton(win,text='Bestätigte automatische Regeln aktivieren',variable=auto).pack(anchor='w',padx=15,pady=10)
        ttk.Checkbutton(win,text='Windows-Benachrichtigungen',variable=notify).pack(anchor='w',padx=15)
        ttk.Label(win,text='Optional: lokaler Ollama-Modellname (leer = keine KI)').pack(padx=15,pady=10)
        entry=ttk.Entry(win,width=45); entry.insert(0,self.store.config['model']); entry.pack(padx=15)
        def installed():
            self.ai_setup()
            def sync():
                if not win.winfo_exists(): return
                if self.busy: win.after(500,sync)
                else: entry.delete(0,'end'); entry.insert(0,self.store.config['model'])
            win.after(500,sync)
        ttk.Button(win,text='KI automatisch einrichten (Download)',command=installed).pack(pady=10)
        ttk.Label(win,text='GitHub-Updates',font=('Segoe UI',12,'bold')).pack(anchor='w',padx=15,pady=(8,4))
        repo=tk.StringVar(value=self.store.config['update_repo']); ttk.Entry(win,textvariable=repo,width=55).pack(padx=15)
        update_checks=tk.BooleanVar(value=self.store.config['check_updates']); update_install=tk.BooleanVar(value=self.store.config['install_updates_automatically'])
        ttk.Checkbutton(win,text='Beim Start und alle 2 Stunden nach Updates suchen',variable=update_checks).pack(anchor='w',padx=15)
        ttk.Checkbutton(win,text='Neue Versionen automatisch herunterladen und installieren',variable=update_install).pack(anchor='w',padx=15)
        ttk.Label(win,text='Öffentliches Repository, z. B. ruyaekin/BewakeAI.\nOhne automatische Installation erscheint nur ein Update-Hinweis.',style='Muted.TLabel').pack(anchor='w',padx=20,pady=4)
        def save():
            try:
                update_repo=updater.repository(repo.get()) if repo.get().strip() else ''
                if startup.get()!=current_startup: background.set_startup(startup.get())
            except (OSError,ValueError) as e: return self.error(e)
            self.store.config.update(auto=auto.get(),notifications=notify.get(),model=entry.get().strip(),close_to_tray=close_tray.get(),update_repo=update_repo,check_updates=update_checks.get(),install_updates_automatically=update_install.get()); self.store.save(); win.destroy()
        ttk.Button(win,text='Speichern',command=save).pack(pady=15)
    def log(self):
        win=tk.Toplevel(self); win.title('Protokoll'); t=tk.Text(win,width=120,height=30); t.pack(); t.insert('1.0','\n'.join(json.dumps(e,ensure_ascii=False) for e in self.store.events()[-250:])); t.config(state='disabled')

if __name__=='__main__':
    data=sys.argv[sys.argv.index('--data-dir')+1] if '--data-dir' in sys.argv else None
    instance=background.SingleInstance()
    if instance.existing:
        if '--tray' not in sys.argv: instance.show_existing()
        instance.close(); sys.exit(0)
    try:
        app=App(data,first_run='--smoke-test' not in sys.argv,start_hidden='--tray' in sys.argv,instance=instance)
        if '--smoke-test' in sys.argv: app.after(1500,app.destroy)
        app.mainloop()
    finally: instance.close()
