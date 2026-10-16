"""Dark theme shared by the app, onboarding and all application dialogs."""
import os
import tkinter as tk
from tkinter import ttk

BG='#10151e'
SURFACE='#1b2432'
FIELD='#121b28'
FG='#e8edf5'
MUTED='#a2b1c6'
ACCENT='#397df4'

def apply(root):
    root.configure(background=BG)
    for key,value in {'*background':BG,'*foreground':FG,'*insertBackground':FG,
                      '*selectBackground':ACCENT,'*selectForeground':'white',
                      '*highlightBackground':SURFACE,'*highlightColor':ACCENT,
                      '*font':'{Segoe UI} 10','*Listbox.background':FIELD,
                      '*Text.background':FIELD,'*Entry.background':FIELD,
                      '*Button.background':SURFACE,'*activeBackground':SURFACE,
                      '*activeForeground':FG}.items(): root.option_add(key,value)
    style=ttk.Style(root); style.theme_use('clam')
    style.configure('.',background=BG,foreground=FG,bordercolor=SURFACE,
                    lightcolor=SURFACE,darkcolor=SURFACE,troughcolor=FIELD,
                    selectbackground=ACCENT,selectforeground='white')
    style.configure('TButton',background=SURFACE,padding=(11,8),borderwidth=0)
    style.map('TButton',background=[('active','#2b3b51'),('pressed',ACCENT)],foreground=[('disabled','#65758b')])
    style.configure('Accent.TButton',background=ACCENT,foreground='white')
    style.map('Accent.TButton',background=[('active','#5592ff')])
    style.configure('TEntry',fieldbackground=FIELD,foreground=FG,insertcolor=FG,padding=7)
    style.configure('TCombobox',fieldbackground=FIELD,background=SURFACE,foreground=FG,arrowcolor=FG,padding=6)
    style.map('TCombobox',fieldbackground=[('readonly',FIELD)],foreground=[('readonly',FG)],selectbackground=[('readonly',FIELD)])
    style.configure('TCheckbutton',background=BG,indicatorbackground=FIELD,indicatorforeground=FG,padding=5)
    style.map('TCheckbutton',background=[('active',BG)],indicatorbackground=[('selected',ACCENT),('active',SURFACE)])
    style.configure('Treeview',background=FIELD,fieldbackground=FIELD,foreground=FG,rowheight=34,borderwidth=0)
    style.map('Treeview',background=[('selected','#244b80')],foreground=[('selected','white')])
    style.configure('Treeview.Heading',background=SURFACE,foreground=MUTED,padding=9,relief='flat')
    style.map('Treeview.Heading',background=[('active','#2b3b51')])
    style.configure('Muted.TLabel',foreground=MUTED)
    style.configure('TProgressbar',background=ACCENT,troughcolor=FIELD,borderwidth=0)
    style.configure('TLabelframe',background=BG,bordercolor=SURFACE)
    style.configure('TLabelframe.Label',background=BG,foreground=MUTED)
    style.configure('TNotebook',background=BG,borderwidth=0)
    style.configure('TNotebook.Tab',background=SURFACE,foreground=FG,padding=(16,10))
    style.map('TNotebook.Tab',background=[('selected',ACCENT)],foreground=[('selected','white')])
    root.bind_all('<Map>',_titlebar,add='+')

def _titlebar(event):
    widget=event.widget
    if os.name!='nt' or not isinstance(widget,(tk.Tk,tk.Toplevel)): return
    try:
        import ctypes
        from ctypes import wintypes
        user=ctypes.windll.user32; user.GetParent.argtypes=[wintypes.HWND]; user.GetParent.restype=wintypes.HWND
        hwnd=user.GetParent(widget.winfo_id()) or widget.winfo_id()
        dwm=ctypes.windll.dwmapi; dwm.DwmSetWindowAttribute.argtypes=[wintypes.HWND,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
        enabled=ctypes.c_int(1); dwm.DwmSetWindowAttribute(hwnd,20,ctypes.byref(enabled),4)
    except (OSError,AttributeError): pass

def dialog(title,text,question=False,initial=None,parent=None):
    parent=parent or tk._default_root
    win=tk.Toplevel(parent); win.title(title); win.configure(bg=BG); win.transient(parent); win.resizable(False,False)
    ttk.Label(win,text=title,font=('Segoe UI',16,'bold')).pack(anchor='w',padx=24,pady=(22,10))
    ttk.Label(win,text=text,wraplength=560,justify='left').pack(anchor='w',padx=24,pady=(0,18))
    value=None; entry=None; result=[None if initial is not None else False]
    if initial is not None:
        value=tk.StringVar(value=initial); entry=ttk.Entry(win,textvariable=value,width=65); entry.pack(padx=24,pady=(0,16)); entry.focus_set()
    def finish(ok): result[0]=value.get() if ok and value is not None else (ok if value is None else None); win.destroy()
    row=ttk.Frame(win); row.pack(fill='x',padx=24,pady=(0,22))
    if question or value is not None: ttk.Button(row,text='Abbrechen',command=lambda:finish(False)).pack(side='right',padx=(8,0))
    ttk.Button(row,text='Bestätigen' if question else 'OK',style='Accent.TButton',command=lambda:finish(True)).pack(side='right')
    win.bind('<Escape>',lambda e:finish(False)); win.bind('<Return>',lambda e:finish(True)); win.protocol('WM_DELETE_WINDOW',lambda:finish(False))
    win.update_idletasks(); win.geometry(f'+{max(0,parent.winfo_rootx()+90)}+{max(0,parent.winfo_rooty()+90)}')
    previous=parent.grab_current(); win.grab_set(); parent.wait_window(win)
    if previous is not None and previous.winfo_exists(): previous.grab_set()
    return result[0]

class messagebox:
    @staticmethod
    def showinfo(title,message,**kw): return dialog(title,message,**kw)
    showerror=showinfo
    @staticmethod
    def askyesno(title,message,**kw): return dialog(title,message,question=True,**kw)

class simpledialog:
    @staticmethod
    def askstring(title,prompt,initialvalue='',**kw): return dialog(title,prompt,initial=initialvalue,**kw)
