import copy
import tkinter as tk
from tkinter import ttk,filedialog
from pathlib import Path
from core import SUBDIRS
from routing import GENERAL,activate,key
from theme import messagebox

def open_routes(app,detected,defaults):
    win=tk.Toplevel(app); win.title('Zielordner und neue Downloads'); win.geometry('900x780'); win.minsize(820,760); win.transient(app)
    previous_setup=app.setup_open; app.setup_open=True
    win.bind('<Destroy>',lambda event:setattr(app,'setup_open',previous_setup) if event.widget is win else None,add='+')
    config=copy.deepcopy(app.store.config)
    config['installations'].update(detected)
    targets={**defaults,**config['targets']}
    ttk.Label(win,text='Einmal einrichten, neue Downloads automatisch ablegen',font=('Segoe UI',17,'bold')).pack(anchor='w',padx=20,pady=(20,8))
    ttk.Label(win,text='Vorhandene Dateien bleiben liegen. Comfy-Dateien gehen direkt in die gewählte Installation.',style='Muted.TLabel').pack(anchor='w',padx=20,pady=(0,15))
    footer=ttk.Frame(win,padding=20); footer.pack(side='bottom',fill='x')
    tabs=ttk.Notebook(win); tabs.pack(fill='both',expand=True,padx=20)
    general=ttk.Frame(tabs,padding=15); comfy=ttk.Frame(tabs,padding=15); behavior=ttk.Frame(tabs,padding=15)
    tabs.add(general,text='Dateitypen'); tabs.add(comfy,text='Comfy Desktop'); tabs.add(behavior,text='Automatik')
    def folder_row(parent,label,variable):
        row=ttk.Frame(parent); row.pack(fill='x',pady=4)
        ttk.Label(row,text=label,width=16).pack(side='left')
        ttk.Entry(row,textvariable=variable).pack(side='left',fill='x',expand=True)
        def browse():
            selected=filedialog.askdirectory(parent=win,title=label+' – Zielordner')
            if selected: variable.set(selected)
        ttk.Button(row,text='Ordner wählen',command=browse).pack(side='left',padx=(8,0))
    ordinary={cat:tk.StringVar(value=targets.get(cat,'')) for cat in GENERAL}
    for cat,var in ordinary.items(): folder_row(general,cat,var)
    ttk.Label(general,text='Programme werden nur verschoben. Archive werden nicht entpackt.',style='Muted.TLabel').pack(anchor='w',pady=16)
    names=list(config['installations']); selected=tk.StringVar(value=config.get('routing_installation',''))
    if selected.get() not in names: selected.set(next((n for n in names if n.startswith('Comfy Desktop')),names[0] if names else ''))
    ttk.Label(comfy,text='Diese Installation für automatische Comfy-Downloads verwenden:').pack(anchor='w',pady=(0,8))
    combo=ttk.Combobox(comfy,textvariable=selected,values=names,state='readonly'); combo.pack(fill='x',pady=(0,10))
    model_vars={cat:tk.StringVar() for cat in SUBDIRS}; current=[None]
    for cat,var in model_vars.items(): folder_row(comfy,cat,var)
    def flush():
        if current[0] is not None:
            config['installations'][current[0]].update({cat:[var.get().strip()] if var.get().strip() else [] for cat,var in model_vars.items()})
    def load(*_):
        flush(); current[0]=selected.get() if selected.get() in names else None
        paths=config['installations'].get(selected.get(),{})
        for cat,var in model_vars.items():
            value=paths.get(cat,[]); var.set(value[0] if isinstance(value,list) and value else value if isinstance(value,str) else '')
    combo.bind('<<ComboboxSelected>>',load); load()
    ttk.Label(comfy,text='Modelle gehören in models/… der Installation, Workflows in user/default/workflows.\nShared ist dafür nicht erforderlich. Leere oder unklare Modellziele benötigen eine manuelle Zuordnung.',style='Muted.TLabel',wraplength=790).pack(anchor='w',pady=10)
    automatic=tk.BooleanVar(value=config['auto_new'] if config.get('routing_configured') else True)
    ttk.Checkbutton(behavior,text='Neue Downloads ab jetzt automatisch in diese Zielordner verschieben',variable=automatic).pack(anchor='w',pady=12)
    ttk.Label(behavior,text='• Nur Dateien, die nach Aktivierung neu im Download-Ordner entstehen.\n• Bereits vorhandene Dateien und laufende Downloads werden ausgenommen.\n• Der Startzeitpunkt bleibt über Neustarts erhalten.\n• Unklare Modelltypen, fehlende Ziele und Duplikate bleiben zur Prüfung liegen.\n• KI-Vorschläge allein lösen keine automatische Verschiebung aus.',wraplength=760,justify='left').pack(anchor='w',pady=10)
    ttk.Label(behavior,text='Erneutes Aus- und Einschalten setzt den Startzeitpunkt neu.\nAutostart mit Windows wird unabhängig davon in den Einstellungen gewählt.',style='Muted.TLabel').pack(anchor='w',pady=20)
    def save():
        flush()
        try:
            values=[var.get().strip() for var in ordinary.values()]+[v.get().strip() for v in model_vars.values() if v.get().strip()]
            for value in values:
                if not value or not Path(value).is_absolute(): raise ValueError('Bitte absolute Zielordner für alle allgemeinen Dateitypen angeben.')
                if key(value)==key(config['downloads']): raise ValueError('Ein Zielordner darf nicht der überwachte Download-Ordner sein.')
            previous=app.store.config
            if automatic.get() and (not previous.get('auto_new') or previous.get('auto_folder')!=key(config['downloads'])): activate(config,config['downloads'])
            config.update(auto=False,auto_new=automatic.get(),routing_configured=True,routing_installation=selected.get(),targets={cat:var.get().strip() for cat,var in ordinary.items()})
            app.store.config=config; app.store.save(); app.refresh_targets()
            app.status.set('Nur neue Downloads werden automatisch einsortiert.' if automatic.get() else 'Automatische Ablage ausgeschaltet. Downloads werden zur Prüfung vorgeschlagen.')
            win.destroy()
        except (OSError,ValueError) as error: messagebox.showerror('Zielordner prüfen',str(error),parent=win)
    ttk.Button(footer,text='Speichern und starten',style='Accent.TButton',command=save).pack(side='right')
    ttk.Button(footer,text='Abbrechen',command=win.destroy).pack(side='right',padx=8)
    win.grab_set()
    return win
