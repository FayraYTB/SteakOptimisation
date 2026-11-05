import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import shutil
import subprocess
import threading
import ctypes
import sys
from pathlib import Path
import time
import json
import updater

# ── Droits admin ───────────────────────────────────────────────────────────────
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

# ── Utilitaires ────────────────────────────────────────────────────────────────
def get_size(path):
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_size(entry.path)
            except (PermissionError, OSError):
                pass
    except (PermissionError, OSError):
        pass
    return total

def format_size(size_bytes):
    for unit in ["o", "Ko", "Mo", "Go"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} To"

def clean_folder(path, log_func):
    freed = 0
    if not os.path.exists(path):
        return freed
    for item in Path(path).iterdir():
        try:
            size = get_size(str(item)) if item.is_dir() else item.stat().st_size
            if item.is_dir():
                shutil.rmtree(str(item), ignore_errors=True)
            else:
                item.unlink()
            freed += size
            log_func(f"  ✓ {item.name}", "success")
        except (PermissionError, OSError):
            log_func(f"  ✗ {item.name}", "warn")
    return freed

# ── Historique ─────────────────────────────────────────────────────────────────
HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".pc_optimizer_history.json")

def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_history(entry: dict):
    history = load_history()
    history.insert(0, entry)
    history = history[:20]   # garde les 20 dernières entrées
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass

# ── Palette ────────────────────────────────────────────────────────────────────
BG      = "#050510"
PANEL   = "#0a0a1e"
CARD    = "#0f0f2a"
BORDER  = "#0d2a6e"
ACCENT  = "#0d6efd"
ACCENT2 = "#1a7fff"
SUCCESS = "#00e5a0"
WARN    = "#ffa500"
DANGER  = "#ff4444"
TEXT    = "#e8f0ff"
SUBTEXT = "#5570a0"

# ── Splash screen ──────────────────────────────────────────────────────────────
class SplashScreen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        w, h = 420, 240
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.configure(bg=PANEL)
        self.attributes("-topmost", True)

        # Bordure bleue
        border = tk.Frame(self, bg=ACCENT, bd=0)
        border.place(x=0, y=0, relwidth=1, height=3)

        tk.Label(self, text="⚡", font=("Segoe UI", 48),
                 bg=PANEL, fg=ACCENT).pack(pady=(30, 0))
        tk.Label(self, text="PC Optimizer Pro",
                 font=("Segoe UI", 18, "bold"),
                 bg=PANEL, fg=TEXT).pack()
        tk.Label(self, text="Chargement...",
                 font=("Segoe UI", 9),
                 bg=PANEL, fg=SUBTEXT).pack(pady=(4, 16))

        style = ttk.Style()
        style.configure("Splash.Horizontal.TProgressbar",
                        troughcolor=BG, background=ACCENT, thickness=4)
        self.bar = ttk.Progressbar(self, style="Splash.Horizontal.TProgressbar",
                                   mode="indeterminate", length=300)
        self.bar.pack()
        self.bar.start(8)

        tk.Label(self, text="v2.0  —  Gratuit & Open Source",
                 font=("Segoe UI", 8),
                 bg=PANEL, fg=SUBTEXT).pack(pady=(10, 0))

# ── ModernButton ───────────────────────────────────────────────────────────────
class ModernButton(tk.Frame):
    def __init__(self, parent, text, command=None,
                 width=200, height=42,
                 bg=ACCENT, hover=ACCENT2, fg="white",
                 font=("Segoe UI", 10, "bold"), **kwargs):
        super().__init__(parent, bg=parent["bg"],
                         width=width, height=height, **kwargs)
        self.pack_propagate(False)
        self._bg = bg; self._hover = hover
        self._fg = fg; self._font = font
        self._cmd = command; self._enabled = True

        self._lbl = tk.Label(self, text=text, font=font, fg=fg, bg=bg,
                             cursor="hand2", relief=tk.FLAT)
        self._lbl.place(relx=0.5, rely=0.5, anchor="center")
        self.configure(bg=bg, relief=tk.FLAT)

        for w in (self, self._lbl):
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)
            w.bind("<Button-1>", self._on_click)

    def _on_enter(self, _=None):
        if self._enabled:
            self.configure(bg=self._hover)
            self._lbl.configure(bg=self._hover)

    def _on_leave(self, _=None):
        if self._enabled:
            self.configure(bg=self._bg)
            self._lbl.configure(bg=self._bg)

    def _on_click(self, _=None):
        if self._enabled and self._cmd:
            self._cmd()

    def set_state(self, enabled: bool):
        self._enabled = enabled
        color = self._bg if enabled else "#1a1a3a"
        self.configure(bg=color)
        self._lbl.configure(bg=color,
                            fg=self._fg if enabled else SUBTEXT,
                            cursor="hand2" if enabled else "arrow")

    def set_text(self, text):
        self._lbl.configure(text=text)

# ── ModernCheck ────────────────────────────────────────────────────────────────
class ModernCheck(tk.Frame):
    def __init__(self, parent, text, variable, **kwargs):
        super().__init__(parent, bg=parent["bg"], **kwargs)
        self._var = variable
        self._box = tk.Label(self, width=2, font=("Segoe UI", 9, "bold"),
                             bg=ACCENT if variable.get() else CARD,
                             fg="white",
                             text="✓" if variable.get() else " ",
                             relief=tk.FLAT, cursor="hand2", padx=2)
        self._box.pack(side=tk.LEFT, padx=(0, 8))
        self._lbl = tk.Label(self, text=text, font=("Segoe UI", 9),
                             bg=parent["bg"], fg="#c8d8f0", cursor="hand2")
        self._lbl.pack(side=tk.LEFT)
        self._box.bind("<Button-1>", self._toggle)
        self._lbl.bind("<Button-1>", self._toggle)

    def _toggle(self, _=None):
        self._var.set(not self._var.get())
        self._box.configure(bg=ACCENT if self._var.get() else CARD,
                            text="✓" if self._var.get() else " ")

# ── Application ────────────────────────────────────────────────────────────────
class PCOptimizerApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.withdraw()                     # cachée pendant le splash
        self.title("PC Optimizer Pro")
        self.geometry("980x680")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._running = False
        self._scan_running = False
        self._configure_styles()

        # Splash 2s
        splash = SplashScreen(self)
        self.after(2000, lambda: self._finish_init(splash))

    def _finish_init(self, splash):
        splash.destroy()
        self._build_ui()
        self.deiconify()
        self.after(300, self._refresh_disk_info)
        self.after(4000, lambda: updater.check_and_prompt(self))

    # ── Styles ────────────────────────────────────────────────────────────────
    def _configure_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        for name, color in [("Blue", ACCENT), ("Green", SUCCESS),
                             ("Orange", WARN), ("Red", DANGER)]:
            s.configure(f"{name}.Horizontal.TProgressbar",
                        troughcolor=PANEL, background=color,
                        darkcolor=color, lightcolor=color,
                        bordercolor=BORDER, thickness=10)
        s.configure("Disk.Horizontal.TProgressbar",
                    troughcolor=PANEL, background=ACCENT, thickness=10)
        s.configure("Tabs.TNotebook", background=BG, borderwidth=0)
        s.configure("Tabs.TNotebook.Tab",
                    background=PANEL, foreground=SUBTEXT,
                    padding=[16, 8], font=("Segoe UI", 9, "bold"),
                    borderwidth=0)
        s.map("Tabs.TNotebook.Tab",
              background=[("selected", CARD)],
              foreground=[("selected", ACCENT)])

    # ── UI principale ─────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()

        # Notebook (onglets)
        self.notebook = ttk.Notebook(self, style="Tabs.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Onglet 1 — Optimisation
        tab1 = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab1, text="🚀  Optimisation")
        self._build_tab_optimize(tab1)

        # Onglet 2 — Analyse
        tab2 = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab2, text="🔍  Analyse PC")
        self._build_tab_analyze(tab2)

        # Onglet 3 — Historique
        tab3 = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab3, text="📋  Historique")
        self._build_tab_history(tab3)

        # Onglet 4 — Paramètres
        tab4 = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(tab4, text="⚙️  Paramètres")
        self._build_tab_settings(tab4)

        self._build_footer()

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=PANEL, height=68)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=ACCENT, width=5).pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(hdr, text="⚡", font=("Segoe UI", 24),
                 bg=PANEL, fg=ACCENT).pack(side=tk.LEFT, padx=(14, 8))
        tf = tk.Frame(hdr, bg=PANEL)
        tf.pack(side=tk.LEFT)
        tk.Label(tf, text="PC Optimizer Pro",
                 font=("Segoe UI", 17, "bold"),
                 bg=PANEL, fg=TEXT).pack(anchor=tk.W)
        tk.Label(tf, text="Nettoyage & Optimisation Windows",
                 font=("Segoe UI", 8), bg=PANEL, fg=SUBTEXT).pack(anchor=tk.W)

        # Infos RAM rapides dans le header
        self.lbl_header_ram = tk.Label(hdr, text="",
                                       font=("Segoe UI", 8),
                                       bg=PANEL, fg=SUBTEXT)
        self.lbl_header_ram.pack(side=tk.RIGHT, padx=(0, 8))
        tk.Label(hdr, text=" v2.0 ", font=("Segoe UI", 8, "bold"),
                 bg=ACCENT, fg="white", padx=6, pady=2).pack(
            side=tk.RIGHT, padx=20)
        self.after(500, self._update_header_stats)

    def _update_header_stats(self):
        try:
            import ctypes as ct
            class MEMSTATUS(ct.Structure):
                _fields_ = [
                    ("dwLength",                ct.c_ulong),
                    ("dwMemoryLoad",            ct.c_ulong),
                    ("ullTotalPhys",            ct.c_ulonglong),
                    ("ullAvailPhys",            ct.c_ulonglong),
                    ("ullTotalPageFile",        ct.c_ulonglong),
                    ("ullAvailPageFile",        ct.c_ulonglong),
                    ("ullTotalVirtual",         ct.c_ulonglong),
                    ("ullAvailVirtual",         ct.c_ulonglong),
                    ("ullAvailExtendedVirtual", ct.c_ulonglong),
                ]
            ms = MEMSTATUS()
            ms.dwLength = ct.sizeof(ms)
            ct.windll.kernel32.GlobalMemoryStatusEx(ct.byref(ms))
            used  = ms.ullTotalPhys - ms.ullAvailPhys
            total = ms.ullTotalPhys
            pct   = int(used / total * 100)
            self.lbl_header_ram.config(
                text=f"RAM  {format_size(used)} / {format_size(total)}  ({pct}%)")
        except Exception:
            pass
        self.after(5000, self._update_header_stats)

    # ── Section label helper ──────────────────────────────────────────────────
    def _section_label(self, parent, text, bg=None):
        bg = bg or BG
        f = tk.Frame(parent, bg=bg)
        f.pack(fill=tk.X, pady=(12, 4))
        tk.Label(f, text=text, font=("Segoe UI", 8, "bold"),
                 bg=bg, fg=ACCENT).pack(side=tk.LEFT)
        tk.Frame(f, bg=BORDER, height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0), pady=5)

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 1 — OPTIMISATION
    # ══════════════════════════════════════════════════════════════════════════
    def _build_tab_optimize(self, parent):
        body = tk.Frame(parent, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=18, pady=12)

        # Colonne gauche
        left = tk.Frame(body, bg=BG, width=300)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)
        self._build_options_panel(left)

        tk.Frame(body, bg=BORDER, width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=12)

        # Colonne droite
        right = tk.Frame(body, bg=BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_log_panel(right)

    def _build_options_panel(self, parent):
        # En-tête avec boutons tout cocher / décocher
        top = tk.Frame(parent, bg=BG)
        top.pack(fill=tk.X, pady=(0, 8))
        tk.Label(top, text="OPTIONS DE NETTOYAGE",
                 font=("Segoe UI", 8, "bold"),
                 bg=BG, fg=SUBTEXT).pack(side=tk.LEFT)

        btn_all  = tk.Label(top, text="Tout", font=("Segoe UI", 8),
                            bg=BG, fg=ACCENT, cursor="hand2")
        btn_none = tk.Label(top, text="Aucun", font=("Segoe UI", 8),
                            bg=BG, fg=SUBTEXT, cursor="hand2")
        btn_none.pack(side=tk.RIGHT, padx=(4, 0))
        tk.Label(top, text="|", font=("Segoe UI", 8),
                 bg=BG, fg=SUBTEXT).pack(side=tk.RIGHT)
        btn_all.pack(side=tk.RIGHT, padx=(0, 4))

        self.vars = {}
        options = [
            ("temp_windows", "🗑️  Temp Windows",          True),
            ("temp_user",    "👤  Temp Utilisateur",       True),
            ("prefetch",     "⚡  Prefetch Windows",       True),
            ("recycle_bin",  "♻️  Vider la Corbeille",     True),
            ("dns_cache",    "🌐  Cache DNS",              True),
            ("event_logs",   "📋  Journaux d'événements",  False),
            ("thumbnail",    "🖼️  Cache Miniatures",       False),
        ]
        self._check_widgets = []

        self._section_label(parent, "SYSTÈME")
        for key, label, default in options[:5]:
            var = tk.BooleanVar(value=default)
            self.vars[key] = var
            c = ModernCheck(parent, label, var)
            c.pack(anchor=tk.W, pady=3)
            self._check_widgets.append(c)

        self._section_label(parent, "AVANCÉ")
        for key, label, default in options[5:]:
            var = tk.BooleanVar(value=default)
            self.vars[key] = var
            c = ModernCheck(parent, label, var)
            c.pack(anchor=tk.W, pady=3)
            self._check_widgets.append(c)

        btn_all.bind("<Button-1>",  lambda _: self._select_all(True))
        btn_none.bind("<Button-1>", lambda _: self._select_all(False))

        # Espace disque
        self._section_label(parent, "DISQUE C:")
        disk_frame = tk.Frame(parent, bg=CARD,
                              highlightbackground=BORDER, highlightthickness=1)
        disk_frame.pack(fill=tk.X, pady=4)
        self.lbl_disk = tk.Label(disk_frame, text="Chargement...",
                                 font=("Segoe UI", 8),
                                 bg=CARD, fg=TEXT, justify=tk.LEFT)
        self.lbl_disk.pack(padx=12, pady=(10, 6), anchor=tk.W)
        self.disk_bar = ttk.Progressbar(disk_frame, length=260,
                                        style="Disk.Horizontal.TProgressbar",
                                        mode="determinate")
        self.disk_bar.pack(padx=12, pady=(0, 10), fill=tk.X)

    def _select_all(self, value: bool):
        for v in self.vars.values():
            v.set(value)
        for c in self._check_widgets:
            c._box.configure(bg=ACCENT if value else CARD,
                             text="✓" if value else " ")

    def _build_log_panel(self, parent):
        tk.Label(parent, text="JOURNAL D'ACTIVITÉ",
                 font=("Segoe UI", 8, "bold"),
                 bg=BG, fg=SUBTEXT).pack(anchor=tk.W, pady=(0, 8))

        log_frame = tk.Frame(parent, bg=CARD,
                             highlightbackground=BORDER, highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(
            log_frame, font=("Consolas", 9),
            bg="#03030f", fg=TEXT,
            insertbackground=ACCENT, relief=tk.FLAT,
            state=tk.DISABLED, wrap=tk.WORD,
            padx=10, pady=8, selectbackground=ACCENT)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.tag_configure("title",   foreground=ACCENT,
                                               font=("Consolas", 9, "bold"))
        self.log_area.tag_configure("success", foreground=SUCCESS)
        self.log_area.tag_configure("warn",    foreground=WARN)
        self.log_area.tag_configure("error",   foreground=DANGER)
        self.log_area.tag_configure("info",    foreground="#5580cc")

        prog_frame = tk.Frame(parent, bg=BG)
        prog_frame.pack(fill=tk.X, pady=(8, 0))
        self.lbl_progress = tk.Label(prog_frame, text="",
                                     font=("Segoe UI", 8), bg=BG, fg=SUBTEXT)
        self.lbl_progress.pack(anchor=tk.W)
        self.progress = ttk.Progressbar(prog_frame,
                                        style="Blue.Horizontal.TProgressbar",
                                        mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(2, 0))

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 2 — ANALYSE PC
    # ══════════════════════════════════════════════════════════════════════════
    def _build_tab_analyze(self, parent):
        top = tk.Frame(parent, bg=BG)
        top.pack(fill=tk.X, padx=18, pady=(14, 6))
        tk.Label(top, text="ANALYSE DU SYSTÈME",
                 font=("Segoe UI", 10, "bold"),
                 bg=BG, fg=TEXT).pack(side=tk.LEFT)

        self.btn_scan = ModernButton(top, text="🔍  Lancer l'analyse",
                                     command=self._start_scan,
                                     width=180, height=34,
                                     bg=ACCENT, hover=ACCENT2,
                                     font=("Segoe UI", 9, "bold"))
        self.btn_scan.pack(side=tk.RIGHT)

        # Cartes de stats
        cards_frame = tk.Frame(parent, bg=BG)
        cards_frame.pack(fill=tk.X, padx=18, pady=(0, 12))

        self._stat_cards = {}
        stats = [
            ("ram",  "💾 RAM",        "–"),
            ("disk", "💿 Disque C:",  "–"),
            ("temp", "📁 Temp totaux", "–"),
            ("cpu",  "🖥️ Processeur",  "–"),
        ]
        for i, (key, title, val) in enumerate(stats):
            card = tk.Frame(cards_frame, bg=CARD,
                            highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="ew")
            cards_frame.columnconfigure(i, weight=1)
            tk.Label(card, text=title, font=("Segoe UI", 8, "bold"),
                     bg=CARD, fg=SUBTEXT).pack(anchor=tk.W, padx=12, pady=(10, 2))
            lbl = tk.Label(card, text=val, font=("Segoe UI", 14, "bold"),
                           bg=CARD, fg=ACCENT)
            lbl.pack(anchor=tk.W, padx=12, pady=(0, 10))
            self._stat_cards[key] = lbl

        # Tableau des gros fichiers
        self._section_label(parent, "GROS FICHIERS (> 100 Mo)", bg=BG)

        table_frame = tk.Frame(parent, bg=CARD,
                               highlightbackground=BORDER, highlightthickness=1)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))

        cols = ("Fichier", "Taille", "Chemin")
        self.tree = ttk.Treeview(table_frame, columns=cols,
                                 show="headings", height=10)
        style = ttk.Style()
        style.configure("Treeview",
                        background="#03030f", foreground=TEXT,
                        rowheight=24, fieldbackground="#03030f",
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background=PANEL, foreground=ACCENT,
                        font=("Segoe UI", 8, "bold"), borderwidth=0)
        style.map("Treeview", background=[("selected", BORDER)])

        self.tree.heading("Fichier", text="Fichier")
        self.tree.heading("Taille",  text="Taille")
        self.tree.heading("Chemin",  text="Chemin")
        self.tree.column("Fichier", width=200)
        self.tree.column("Taille",  width=80,  anchor="e")
        self.tree.column("Chemin",  width=400)

        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.lbl_scan_status = tk.Label(parent, text="",
                                        font=("Segoe UI", 8),
                                        bg=BG, fg=SUBTEXT)
        self.lbl_scan_status.pack(padx=18, anchor=tk.W)

    def _start_scan(self):
        if self._scan_running:
            return
        self._scan_running = True
        self.btn_scan.set_state(False)
        self.btn_scan.set_text("⏳  Analyse...")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.lbl_scan_status.config(text="Analyse en cours...", fg=WARN)
        threading.Thread(target=self._run_scan, daemon=True).start()

    def _run_scan(self):
        results = []

        # RAM
        try:
            import ctypes as ct
            class MEM(ct.Structure):
                _fields_ = [("dwLength", ct.c_ulong),
                             ("dwMemoryLoad", ct.c_ulong),
                             ("ullTotalPhys", ct.c_ulonglong),
                             ("ullAvailPhys", ct.c_ulonglong),
                             ("ullTotalPageFile", ct.c_ulonglong),
                             ("ullAvailPageFile", ct.c_ulonglong),
                             ("ullTotalVirtual", ct.c_ulonglong),
                             ("ullAvailVirtual", ct.c_ulonglong),
                             ("ullAvailExtendedVirtual", ct.c_ulonglong)]
            ms = MEM(); ms.dwLength = ct.sizeof(ms)
            ct.windll.kernel32.GlobalMemoryStatusEx(ct.byref(ms))
            used  = ms.ullTotalPhys - ms.ullAvailPhys
            total = ms.ullTotalPhys
            pct   = int(used / total * 100)
            self.after(0, self._stat_cards["ram"].config,
                       {"text": f"{pct}%  ({format_size(used)})",
                        "fg": DANGER if pct > 85 else WARN if pct > 65 else SUCCESS})
        except Exception:
            pass

        # Disque
        try:
            u = shutil.disk_usage("C:\\")
            pct = int(u.used / u.total * 100)
            self.after(0, self._stat_cards["disk"].config,
                       {"text": f"{pct}%  libre: {format_size(u.free)}",
                        "fg": DANGER if pct > 85 else WARN if pct > 65 else SUCCESS})
        except Exception:
            pass

        # Taille dossiers temp
        temp_total = 0
        for p in [
            os.environ.get("SystemRoot", "C:\\Windows") + "\\Temp",
            os.environ.get("TEMP", os.path.expanduser("~\\AppData\\Local\\Temp")),
            os.environ.get("SystemRoot", "C:\\Windows") + "\\Prefetch",
        ]:
            temp_total += get_size(p)
        color = DANGER if temp_total > 500_000_000 else WARN if temp_total > 100_000_000 else SUCCESS
        self.after(0, self._stat_cards["temp"].config,
                   {"text": format_size(temp_total), "fg": color})

        # CPU (approximatif via compteur Windows)
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "loadpercentage"],
                capture_output=True, text=True, timeout=5)
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip().isdigit()]
            if lines:
                cpu = int(lines[0])
                self.after(0, self._stat_cards["cpu"].config,
                           {"text": f"{cpu}%",
                            "fg": DANGER if cpu > 85 else WARN if cpu > 60 else SUCCESS})
        except Exception:
            self.after(0, self._stat_cards["cpu"].config,
                       {"text": "N/A", "fg": SUBTEXT})

        # Scan gros fichiers dans le profil utilisateur
        scan_paths = [
            os.path.expanduser("~\\Downloads"),
            os.path.expanduser("~\\Documents"),
            os.path.expanduser("~\\Desktop"),
            os.environ.get("TEMP", ""),
        ]
        LIMIT = 100 * 1024 * 1024   # 100 Mo
        found = 0
        for base in scan_paths:
            if not base or not os.path.exists(base):
                continue
            self.after(0, self.lbl_scan_status.config,
                       {"text": f"Scan : {base}", "fg": SUBTEXT})
            try:
                for root, dirs, files in os.walk(base):
                    dirs[:] = [d for d in dirs
                               if not d.startswith(".")]
                    for fname in files:
                        try:
                            fp   = os.path.join(root, fname)
                            size = os.path.getsize(fp)
                            if size >= LIMIT:
                                results.append((fname, size, fp))
                                found += 1
                                if found >= 200:
                                    break
                        except (PermissionError, OSError):
                            pass
                    if found >= 200:
                        break
            except (PermissionError, OSError):
                pass

        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:50]

        def _populate():
            for fname, size, path in results:
                tag = "big" if size > 1_000_000_000 else ""
                self.tree.insert("", tk.END,
                                 values=(fname, format_size(size), path),
                                 tags=(tag,))
            self.tree.tag_configure("big", foreground=WARN)
            total_size = sum(s for _, s, _ in results)
            self.lbl_scan_status.config(
                text=f"{len(results)} fichier(s) trouvé(s)  —  "
                     f"Total : {format_size(total_size)}",
                fg=SUCCESS)
            self._scan_running = False
            self.btn_scan.set_state(True)
            self.btn_scan.set_text("🔍  Lancer l'analyse")

        self.after(0, _populate)

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 3 — HISTORIQUE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_tab_history(self, parent):
        top = tk.Frame(parent, bg=BG)
        top.pack(fill=tk.X, padx=18, pady=(14, 6))
        tk.Label(top, text="HISTORIQUE DES OPTIMISATIONS",
                 font=("Segoe UI", 10, "bold"),
                 bg=BG, fg=TEXT).pack(side=tk.LEFT)
        tk.Label(top, text="Effacer",
                 font=("Segoe UI", 8), bg=BG, fg=DANGER,
                 cursor="hand2").pack(side=tk.RIGHT,
                 pady=4).bind("<Button-1>", self._clear_history)

        # Liste
        hist_frame = tk.Frame(parent, bg=CARD,
                              highlightbackground=BORDER, highlightthickness=1)
        hist_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=8)

        self.hist_canvas = tk.Canvas(hist_frame, bg=CARD,
                                     highlightthickness=0)
        vsb = ttk.Scrollbar(hist_frame, orient="vertical",
                            command=self.hist_canvas.yview)
        self.hist_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.hist_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hist_inner = tk.Frame(self.hist_canvas, bg=CARD)
        self.hist_canvas.create_window((0, 0), window=self.hist_inner,
                                       anchor="nw")
        self.hist_inner.bind("<Configure>",
            lambda e: self.hist_canvas.configure(
                scrollregion=self.hist_canvas.bbox("all")))

        self._refresh_history()

        # Résumé total
        self.lbl_hist_total = tk.Label(parent, text="",
                                       font=("Segoe UI", 9, "bold"),
                                       bg=BG, fg=SUCCESS)
        self.lbl_hist_total.pack(padx=18, pady=(4, 8), anchor=tk.W)
        self._update_hist_total()

    def _refresh_history(self):
        for w in self.hist_inner.winfo_children():
            w.destroy()
        history = load_history()
        if not history:
            tk.Label(self.hist_inner, text="Aucune optimisation effectuée.",
                     font=("Segoe UI", 9), bg=CARD, fg=SUBTEXT,
                     pady=20).pack()
            return
        for entry in history:
            row = tk.Frame(self.hist_inner, bg=PANEL,
                           highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill=tk.X, padx=8, pady=4)
            tk.Label(row, text=entry.get("date", "–"),
                     font=("Consolas", 8), bg=PANEL, fg=SUBTEXT,
                     width=18).pack(side=tk.LEFT, padx=10, pady=8)
            tasks_str = ", ".join(entry.get("tasks", []))
            tk.Label(row, text=tasks_str,
                     font=("Segoe UI", 8), bg=PANEL, fg=TEXT).pack(
                side=tk.LEFT, padx=8)
            tk.Label(row, text=format_size(entry.get("freed", 0)),
                     font=("Segoe UI", 9, "bold"),
                     bg=PANEL, fg=SUCCESS).pack(side=tk.RIGHT, padx=14)

    def _update_hist_total(self):
        history = load_history()
        total = sum(e.get("freed", 0) for e in history)
        count = len(history)
        self.lbl_hist_total.config(
            text=f"Total : {count} optimisation(s)  —  {format_size(total)} libérés au total")

    def _clear_history(self, _=None):
        if messagebox.askyesno("Effacer", "Effacer tout l'historique ?"):
            try:
                os.remove(HISTORY_FILE)
            except Exception:
                pass
            self._refresh_history()
            self._update_hist_total()

    # ══════════════════════════════════════════════════════════════════════════
    # ONGLET 4 — PARAMÈTRES
    # ══════════════════════════════════════════════════════════════════════════
    def _build_tab_settings(self, parent):
        body = tk.Frame(parent, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        self._section_label(body, "DÉMARRAGE", bg=BG)

        self._auto_update_var = tk.BooleanVar(value=True)
        ModernCheck(body, "Vérifier les mises à jour au démarrage",
                    self._auto_update_var).pack(anchor=tk.W, pady=4)

        self._auto_scan_var = tk.BooleanVar(value=False)
        ModernCheck(body, "Lancer l'analyse automatiquement au démarrage",
                    self._auto_scan_var).pack(anchor=tk.W, pady=4)

        self._section_label(body, "À PROPOS", bg=BG)
        about = tk.Frame(body, bg=CARD,
                         highlightbackground=BORDER, highlightthickness=1)
        about.pack(fill=tk.X, pady=4)

        infos = [
            ("Application",   "PC Optimizer Pro"),
            ("Version",       "2.0"),
            ("Développeur",   "TON_USERNAME"),
            ("Licence",       "Open Source — Gratuit"),
            ("Site web",      "https://TON_USERNAME.github.io/pc-optimizer"),
        ]
        for label, val in infos:
            row = tk.Frame(about, bg=CARD)
            row.pack(fill=tk.X, padx=14, pady=4)
            tk.Label(row, text=f"{label} :", width=16, anchor=tk.W,
                     font=("Segoe UI", 9), bg=CARD, fg=SUBTEXT).pack(side=tk.LEFT)
            tk.Label(row, text=val,
                     font=("Segoe UI", 9, "bold"), bg=CARD, fg=TEXT).pack(
                side=tk.LEFT)

        # Bouton vérifier MAJ manuellement
        self._section_label(body, "MISES À JOUR", bg=BG)
        ModernButton(body, text="🔄  Vérifier maintenant",
                     command=lambda: updater.check_and_prompt(self),
                     width=200, height=36, bg=ACCENT, hover=ACCENT2,
                     font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=4)

    # ── Footer ────────────────────────────────────────────────────────────────
    def _build_footer(self):
        footer = tk.Frame(self, bg=PANEL, height=58)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Frame(footer, bg=BORDER, height=1).pack(fill=tk.X)

        btn_frame = tk.Frame(footer, bg=PANEL)
        btn_frame.pack(side=tk.LEFT, padx=18, pady=8)

        self.btn_start = ModernButton(
            btn_frame, text="▶  LANCER L'OPTIMISATION",
            command=self._start_optimization,
            width=230, height=40, bg=ACCENT, hover=ACCENT2,
            font=("Segoe UI", 10, "bold"))
        self.btn_start.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_clear = ModernButton(
            btn_frame, text="🧹  Effacer",
            command=self._clear_log,
            width=110, height=40, bg="#0a0a2e", hover="#101048",
            font=("Segoe UI", 9))
        self.btn_clear.pack(side=tk.LEFT)

        self.lbl_status = tk.Label(
            footer, text="● Prêt",
            font=("Segoe UI", 9, "bold"), bg=PANEL, fg=SUCCESS)
        self.lbl_status.pack(side=tk.RIGHT, padx=20)

    # ── Log ───────────────────────────────────────────────────────────────────
    def _log(self, message, tag=None):
        self.log_area.configure(state=tk.NORMAL)
        ts = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{ts}] {message}\n", tag or "")
        self.log_area.configure(state=tk.DISABLED)
        self.log_area.see(tk.END)

    def _clear_log(self):
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.delete("1.0", tk.END)
        self.log_area.configure(state=tk.DISABLED)

    # ── Disque ────────────────────────────────────────────────────────────────
    def _refresh_disk_info(self):
        try:
            u = shutil.disk_usage("C:\\")
            pct = u.used / u.total * 100
            color = DANGER if pct > 85 else WARN if pct > 65 else SUCCESS
            self.lbl_disk.config(
                text=(f"Utilisé  : {format_size(u.used)}\n"
                      f"Libre    : {format_size(u.free)}\n"
                      f"Total    : {format_size(u.total)}  ({pct:.1f}%)"),
                fg=color)
            self.disk_bar["value"] = pct
            ttk.Style().configure("Disk.Horizontal.TProgressbar",
                                  background=color)
        except Exception as e:
            self.lbl_disk.config(text=f"Erreur : {e}", fg=DANGER)

    # ── Optimisation ──────────────────────────────────────────────────────────
    def _start_optimization(self):
        if self._running:
            return
        selected = [k for k, v in self.vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Aucune option",
                                   "Sélectionne au moins une option.")
            return
        # Basculer sur l'onglet Optimisation
        self.notebook.select(0)
        self._running = True
        self.btn_start.set_state(False)
        self.btn_start.set_text("⏳  EN COURS...")
        self.progress.start(10)
        self.lbl_status.config(text="● Optimisation...", fg=WARN)
        self.lbl_progress.config(text="Nettoyage en cours...")
        threading.Thread(target=self._run_tasks,
                         args=(selected,), daemon=True).start()

    def _run_tasks(self, tasks):
        total = 0
        self._log("━" * 50, "title")
        self._log("  ⚡ DÉMARRAGE DE L'OPTIMISATION", "title")
        self._log("━" * 50, "title")

        steps = {
            "temp_windows": ("Fichiers temp Windows",
                lambda: clean_folder(
                    os.environ.get("SystemRoot", "C:\\Windows") + "\\Temp",
                    self._log)),
            "temp_user": ("Fichiers temp Utilisateur",
                lambda: clean_folder(
                    os.environ.get("TEMP",
                        os.path.expanduser("~\\AppData\\Local\\Temp")),
                    self._log)),
            "prefetch": ("Prefetch Windows",
                lambda: clean_folder(
                    os.environ.get("SystemRoot", "C:\\Windows") + "\\Prefetch",
                    self._log)),
            "recycle_bin":  ("Corbeille",              self._empty_recycle),
            "dns_cache":    ("Cache DNS",               self._flush_dns),
            "event_logs":   ("Journaux d'événements",   self._clean_event_logs),
            "thumbnail":    ("Cache Miniatures",         self._clean_thumbnails),
        }
        task_names = []
        for key in tasks:
            label, func = steps[key]
            task_names.append(label)
            self._log(f"\n▶  {label}", "title")
            result = func()
            if isinstance(result, int):
                total += result
                self._log(f"  → Libéré : {format_size(result)}", "info")

        self._log("\n" + "━" * 50, "title")
        self._log(f"  ✅ TERMINÉ  —  {format_size(total)} libérés", "success")
        self._log("━" * 50, "title")

        # Sauvegarde dans l'historique
        save_history({
            "date":  time.strftime("%Y-%m-%d %H:%M:%S"),
            "tasks": task_names,
            "freed": total,
        })
        self.after(0, self._on_done, total)

    def _empty_recycle(self):
        try:
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0007)
            self._log("  ✓ Corbeille vidée.", "success")
        except Exception as e:
            self._log(f"  ✗ {e}", "error")

    def _flush_dns(self):
        try:
            subprocess.run(["ipconfig", "/flushdns"],
                           capture_output=True, text=True, check=True)
            self._log("  ✓ Cache DNS vidé.", "success")
        except Exception as e:
            self._log(f"  ✗ {e}", "error")

    def _clean_event_logs(self):
        for name in ["Application", "System", "Security"]:
            try:
                subprocess.run(["wevtutil", "cl", name],
                               capture_output=True, text=True)
                self._log(f"  ✓ Journal '{name}' nettoyé.", "success")
            except Exception as e:
                self._log(f"  ✗ {name} : {e}", "error")

    def _clean_thumbnails(self):
        path = os.path.expanduser(
            "~\\AppData\\Local\\Microsoft\\Windows\\Explorer")
        freed = 0
        try:
            for f in Path(path).glob("thumbcache_*.db"):
                try:
                    freed += f.stat().st_size
                    f.unlink()
                    self._log(f"  ✓ {f.name}", "success")
                except Exception as e:
                    self._log(f"  ✗ {f.name} : {e}", "error")
        except Exception as e:
            self._log(f"  ✗ {e}", "error")
        return freed

    def _on_done(self, freed):
        self._running = False
        self.progress.stop()
        self.btn_start.set_state(True)
        self.btn_start.set_text("▶  LANCER L'OPTIMISATION")
        self.lbl_status.config(text="● Terminé ✅", fg=SUCCESS)
        self.lbl_progress.config(
            text=f"Dernière optimisation : {format_size(freed)} libérés")
        self._refresh_disk_info()
        self._refresh_history()
        self._update_hist_total()
        messagebox.showinfo("PC Optimizer Pro",
                            f"Optimisation terminée !\n{format_size(freed)} libérés.")

# ── Lancement ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_as_admin()
    app = PCOptimizerApp()
    app.mainloop()
