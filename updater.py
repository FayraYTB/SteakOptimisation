"""
updater.py — Système de mise à jour automatique
Vérifie GitHub, télécharge et remplace le .exe si une nouvelle version existe.
"""

import urllib.request
import urllib.error
import json
import os
import sys
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import ttk
from packaging import version as pkg_version

# ── Configuration ──────────────────────────────────────────────────────────────
CURRENT_VERSION = "2.0"

# URL du fichier version.json sur GitHub (branche main, dossier racine)
# Remplace SteakOptimisation par ton vrai nom d'utilisateur GitHub
VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "SteakOptimisation/pc-optimizer/main/version.json"
)

# ── Couleurs (cohérentes avec l'app) ──────────────────────────────────────────
BG      = "#050510"
PANEL   = "#0a0a1e"
CARD    = "#0f0f2a"
BORDER  = "#0d2a6e"
ACCENT  = "#0d6efd"
SUCCESS = "#00e5a0"
WARN    = "#ffa500"
DANGER  = "#ff4444"
TEXT    = "#e8f0ff"
SUBTEXT = "#5570a0"


def _compare_versions(v1: str, v2: str) -> bool:
    """Retourne True si v2 est plus récente que v1."""
    try:
        return pkg_version.parse(v2) > pkg_version.parse(v1)
    except Exception:
        # Fallback simple si packaging n'est pas disponible
        return v2 != v1


def check_for_update(timeout: int = 5) -> dict | None:
    """
    Vérifie si une mise à jour est disponible.
    Retourne le dict du version.json distant si maj dispo, sinon None.
    """
    try:
        req = urllib.request.Request(
            VERSION_URL,
            headers={"User-Agent": "PCOptimizerPro-Updater/2.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        remote_ver = data.get("version", "0.0")
        if _compare_versions(CURRENT_VERSION, remote_ver):
            return data          # nouvelle version disponible
        return None              # déjà à jour
    except Exception:
        return None              # pas de réseau ou erreur → silencieux


# ── Fenêtre de mise à jour ────────────────────────────────────────────────────
class UpdateWindow(tk.Toplevel):
    def __init__(self, parent, update_info: dict):
        super().__init__(parent)
        self.title("Mise à jour disponible")
        self.geometry("480x360")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.grab_set()                    # fenêtre modale
        self.transient(parent)

        self._info   = update_info
        self._parent = parent
        self._build_ui()

    def _build_ui(self):
        # ── En-tête ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=ACCENT, height=56)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⬆️  Mise à jour disponible !",
                 font=("Segoe UI", 13, "bold"),
                 bg=ACCENT, fg="white").pack(padx=16, pady=12)

        body = tk.Frame(self, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=14)

        # ── Versions ───────────────────────────────────────────────────────────
        ver_frame = tk.Frame(body, bg=CARD,
                             highlightbackground=BORDER,
                             highlightthickness=1)
        ver_frame.pack(fill=tk.X, pady=(0, 12))

        row = tk.Frame(ver_frame, bg=CARD)
        row.pack(fill=tk.X, padx=14, pady=10)
        tk.Label(row, text=f"Version actuelle :  {CURRENT_VERSION}",
                 font=("Segoe UI", 9), bg=CARD, fg=SUBTEXT).pack(side=tk.LEFT)
        tk.Label(row, text=f"  →  {self._info.get('version','?')}  ✨",
                 font=("Segoe UI", 9, "bold"), bg=CARD, fg=SUCCESS).pack(side=tk.LEFT)

        # ── Changelog ──────────────────────────────────────────────────────────
        tk.Label(body, text="Nouveautés :",
                 font=("Segoe UI", 9, "bold"),
                 bg=BG, fg=ACCENT).pack(anchor=tk.W)

        log_frame = tk.Frame(body, bg=CARD,
                             highlightbackground=BORDER,
                             highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 12))

        changelog = self._info.get("changelog", [])
        for item in changelog:
            tk.Label(log_frame, text=f"  ✓  {item}",
                     font=("Segoe UI", 9),
                     bg=CARD, fg=TEXT,
                     anchor=tk.W).pack(fill=tk.X, padx=8, pady=2)

        # ── Barre de progression ───────────────────────────────────────────────
        self.prog_label = tk.Label(body, text="",
                                   font=("Segoe UI", 8),
                                   bg=BG, fg=SUBTEXT)
        self.prog_label.pack(anchor=tk.W)

        style = ttk.Style()
        style.configure("Update.Horizontal.TProgressbar",
                        troughcolor=PANEL, background=ACCENT, thickness=8)
        self.prog_bar = ttk.Progressbar(body,
                                        style="Update.Horizontal.TProgressbar",
                                        mode="determinate", length=440)
        self.prog_bar.pack(fill=tk.X, pady=(2, 10))

        # ── Boutons ────────────────────────────────────────────────────────────
        btn_frame = tk.Frame(body, bg=BG)
        btn_frame.pack(fill=tk.X)

        self.btn_update = tk.Button(
            btn_frame,
            text="⬇️  Télécharger et installer",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT, fg="white",
            activebackground="#1a7fff",
            activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            padx=14, pady=6,
            command=self._start_download,
        )
        self.btn_update.pack(side=tk.LEFT)

        tk.Button(
            btn_frame,
            text="Plus tard",
            font=("Segoe UI", 9),
            bg=PANEL, fg=SUBTEXT,
            activebackground=CARD,
            activeforeground=TEXT,
            relief=tk.FLAT, cursor="hand2",
            padx=12, pady=6,
            command=self.destroy,
        ).pack(side=tk.RIGHT)

    # ── Téléchargement ────────────────────────────────────────────────────────
    def _start_download(self):
        self.btn_update.configure(state=tk.DISABLED, text="⏳  Téléchargement...")
        self.prog_bar.configure(mode="indeterminate")
        self.prog_bar.start(10)
        self.prog_label.configure(text="Connexion au serveur...")
        threading.Thread(target=self._download, daemon=True).start()

    def _download(self):
        url = self._info.get("download_url", "")
        if not url:
            self.after(0, lambda: self.prog_label.configure(
                text="❌ URL de téléchargement manquante.", fg=DANGER))
            return

        try:
            # Téléchargement dans un fichier temporaire
            tmp_dir  = tempfile.gettempdir()
            tmp_path = os.path.join(tmp_dir, "PC_Optimizer_Pro_update.exe")

            self.after(0, lambda: self.prog_label.configure(
                text="Téléchargement en cours..."))

            req = urllib.request.Request(
                url, headers={"User-Agent": "PCOptimizerPro-Updater/2.0"})

            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk = 8192

                self.after(0, lambda: self.prog_bar.configure(
                    mode="determinate", maximum=max(total, 1)))
                self.prog_bar.stop()

                with open(tmp_path, "wb") as f:
                    while True:
                        data = resp.read(chunk)
                        if not data:
                            break
                        f.write(data)
                        downloaded += len(data)
                        pct = int(downloaded / max(total, 1) * 100)
                        self.after(0, self._update_progress,
                                   downloaded, pct)

            # Lance le script de remplacement et quitte
            self.after(0, self._install_update, tmp_path)

        except Exception as e:
            self.after(0, lambda: self.prog_label.configure(
                text=f"❌ Erreur : {e}", fg=DANGER))
            self.after(0, lambda: self.btn_update.configure(
                state=tk.NORMAL, text="🔄 Réessayer"))

    def _update_progress(self, downloaded: int, pct: int):
        self.prog_bar["value"] = downloaded
        self.prog_label.configure(
            text=f"Téléchargement... {pct}%  ({downloaded // 1024} Ko)",
            fg=TEXT)

    def _install_update(self, tmp_path: str):
        """Remplace l'exe actuel et redémarre."""
        current_exe = sys.executable if getattr(sys, "frozen", False) \
            else os.path.abspath(sys.argv[0])

        # Script batch pour remplacer le .exe après fermeture
        bat = os.path.join(tempfile.gettempdir(), "pc_optimizer_update.bat")
        with open(bat, "w") as f:
            f.write(f"""@echo off
ping 127.0.0.1 -n 3 >nul
move /Y "{tmp_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
""")
        subprocess.Popen(["cmd", "/c", bat],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        self._parent.destroy()   # ferme l'app → le bat remplace et relance


# ── Fonction principale appelée au démarrage de l'app ─────────────────────────
def check_and_prompt(parent: tk.Tk):
    """
    Lance la vérification en arrière-plan.
    Si une maj est dispo, affiche UpdateWindow.
    """
    def _check():
        info = check_for_update()
        if info:
            parent.after(0, lambda: UpdateWindow(parent, info))

    threading.Thread(target=_check, daemon=True).start()
