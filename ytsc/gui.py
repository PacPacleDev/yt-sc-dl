"""Interface graphique — téléchargement uniquement.

Le téléchargement tourne dans un thread séparé pour que la fenêtre reste
réactive ; toute mise à jour de widget repasse par `after()` car Tk n'est
pas sûr à utiliser depuis un autre thread.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from . import config
from .downloader import download, detect_source, DownloadError

# ── Thème ────────────────────────────────────────────────────────────────────
BG, BG2, BG3 = "#0d0b14", "#151222", "#1e1a30"
NEON_G, NEON_V, NEON_P = "#39ff88", "#a855f7", "#e040fb"
TEXT, MUTED, BORDER, ERR = "#eae6f5", "#7a7391", "#2d2745", "#ff4d6d"

FONT = ("SF Pro Display", 12)
FONT_BOLD = ("SF Pro Display", 12, "bold")
FONT_TITLE = ("SF Pro Display", 22, "bold")
FONT_SMALL = ("SF Pro Display", 10)
FONT_LABEL = ("SF Pro Display", 10, "bold")
FONT_MONO = ("Menlo", 10)

QUALITY_LABELS = {"320": "320 kbps (max)", "256": "256 kbps", "192": "192 kbps",
                  "128": "128 kbps", "0": "meilleur disponible"}


class NeonButton(tk.Canvas):
    """Bouton arrondi dessiné à la main — Tk n'en propose pas nativement."""

    def __init__(self, parent, text, color, command, width=200, height=42,
                 radius=21, bg=BG, fg="#0d0b14", font=FONT_BOLD, glow=True):
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0)
        self.color, self.command = color, command
        self.w, self.h, self.r = width, height, radius
        self.fg, self._font, self.glow = fg, font, glow
        self._enabled, self._text = True, text
        self._draw(color)
        self.bind("<Button-1>", lambda _e: self._click())
        self.bind("<Enter>", lambda _e: self._hover(True))
        self.bind("<Leave>", lambda _e: self._hover(False))
        self.config(cursor="hand2")

    def _rounded(self, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.create_polygon(pts, smooth=True, **kw)

    def _draw(self, color, glow=None):
        self.delete("all")
        if self.glow and self._enabled:
            self._rounded(1, 1, self.w - 1, self.h - 1, self.r,
                          fill="", outline=glow or color, width=2)
            self._rounded(3, 3, self.w - 3, self.h - 3, self.r - 2,
                          fill=color, outline="")
        else:
            self._rounded(3, 3, self.w - 3, self.h - 3, self.r - 2,
                          fill=color, outline="")
        self.create_text(self.w / 2, self.h / 2, text=self._text,
                         fill=self.fg if self._enabled else MUTED, font=self._font)

    def _click(self):
        if self._enabled and self.command:
            self.command()

    def _hover(self, on):
        if self._enabled:
            self._draw(self.color, glow="#ffffff" if on else None)

    def set_color(self, color, fg=None):
        self.color = color
        if fg:
            self.fg = fg
        self._draw(color)

    def set_state(self, enabled):
        self._enabled = enabled
        self._draw(self.color if enabled else BG3)
        self.config(cursor="hand2" if enabled else "arrow")


def entry(parent, var, accent=NEON_V):
    return tk.Entry(parent, textvariable=var, font=FONT, bg=BG3, fg=TEXT,
                    insertbackground=NEON_G, bd=0, relief="flat",
                    highlightthickness=1, highlightbackground=BORDER,
                    highlightcolor=accent)


def section(parent, title, accent=NEON_V):
    outer = tk.Frame(parent, bg=BG)
    outer.pack(fill="x", pady=(0, 10))
    tk.Label(outer, text=title.upper(), font=FONT_LABEL,
             bg=BG, fg=accent).pack(anchor="w", pady=(0, 4))
    inner = tk.Frame(outer, bg=BG2, highlightthickness=1,
                     highlightbackground=BORDER, padx=14, pady=12)
    inner.pack(fill="x")
    return inner


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Yt-Sc DL")
        self.geometry("820x720")
        self.minsize(760, 620)
        self.configure(bg=BG)
        self.cfg = config.load()
        self._cancel = threading.Event()
        self._build()

    # ── Construction ──────────────────────────────────────────────────────────
    def _build(self):
        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=28, pady=(18, 12))
        tk.Label(head, text="YT", font=FONT_TITLE, bg=BG, fg=ERR).pack(side="left")
        tk.Label(head, text="·SC", font=FONT_TITLE, bg=BG, fg=NEON_V).pack(side="left")
        tk.Label(head, text="DL", font=FONT_TITLE, bg=BG, fg=NEON_G).pack(side="left")
        tk.Label(head, text="playlists → audio → Rekordbox", font=FONT_SMALL,
                 bg=BG, fg=MUTED).pack(side="left", padx=14, pady=10)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=28)

        # Playlists mémorisées
        saved = section(body, "Playlists mémorisées", NEON_V)
        self.yt_url = tk.StringVar(value=self.cfg["youtube_url"])
        self.yt_dir = tk.StringVar(value=self.cfg["youtube_dir"])
        self.sc_url = tk.StringVar(value=self.cfg["soundcloud_url"])
        self.sc_dir = tk.StringVar(value=self.cfg["soundcloud_dir"])
        self._source_block(saved, "YouTube", self.yt_url, self.yt_dir, NEON_P)
        tk.Frame(saved, bg=BORDER, height=1).pack(fill="x", pady=10)
        self._source_block(saved, "SoundCloud", self.sc_url, self.sc_dir, NEON_V)

        row = tk.Frame(saved, bg=BG2)
        row.pack(fill="x", pady=(12, 0))
        self.yt_btn = NeonButton(row, "▶  YOUTUBE", NEON_G,
                                 lambda: self._start(self.yt_url.get(),
                                                     self.yt_dir.get(), "YouTube"),
                                 width=160, bg=BG2)
        self.yt_btn.pack(side="left", padx=(0, 10))
        self.sc_btn = NeonButton(row, "▶  SOUNDCLOUD", NEON_V,
                                 lambda: self._start(self.sc_url.get(),
                                                     self.sc_dir.get(), "SoundCloud"),
                                 width=180, bg=BG2, fg="#ffffff")
        self.sc_btn.pack(side="left")
        self.stop_btn = NeonButton(row, "⏹  STOP", BG3, self._stop, width=110,
                                   bg=BG2, fg=ERR, glow=False)
        self.stop_btn.pack(side="right")
        self.stop_btn.set_state(False)

        # Téléchargement ponctuel
        one = section(body, "Télécharger une playlist", NEON_G)
        r = tk.Frame(one, bg=BG2)
        r.pack(fill="x")
        self.url = tk.StringVar()
        self.url.trace_add("write", self._on_url)
        entry(r, self.url, NEON_G).pack(side="left", fill="x", expand=True,
                                        ipady=9, padx=(0, 10))
        self.detect = tk.Label(r, text="—", font=FONT_SMALL, bg=BG2,
                               fg=MUTED, width=13)
        self.detect.pack(side="left", padx=(0, 10))
        self.go_btn = NeonButton(r, "▶  LANCER", BG3,
                                 lambda: self._start(self.url.get(),
                                                     self.out_dir.get(), "Téléchargement"),
                                 width=130, bg=BG2, fg=MUTED, glow=False)
        self.go_btn.pack(side="left")
        self.go_btn.set_state(False)

        r2 = tk.Frame(one, bg=BG2)
        r2.pack(fill="x", pady=(10, 0))
        tk.Label(r2, text="Dossier", font=FONT_SMALL, bg=BG2, fg=MUTED,
                 width=8, anchor="w").pack(side="left")
        self.out_dir = tk.StringVar(value=self.cfg["output_dir"])
        entry(r2, self.out_dir, NEON_G).pack(side="left", fill="x", expand=True,
                                             ipady=7, padx=(0, 8))
        NeonButton(r2, "📁", NEON_G, lambda: self._browse(self.out_dir),
                   width=52, height=32, radius=16, bg=BG2).pack(side="left")

        # Options
        opt = section(body, "Options", NEON_P)
        o = tk.Frame(opt, bg=BG2)
        o.pack(fill="x", pady=(0, 10))
        tk.Label(o, text="Format", font=FONT_SMALL, bg=BG2, fg=MUTED,
                 width=8, anchor="w").pack(side="left")
        self.fmt = tk.StringVar(value=self.cfg["format"])
        self.fmt.trace_add("write", self._on_format)
        m = tk.OptionMenu(o, self.fmt, *config.FORMATS)
        self._menu(m, NEON_G)
        m.pack(side="left", padx=(0, 22))
        tk.Label(o, text="Débit", font=FONT_SMALL, bg=BG2,
                 fg=MUTED).pack(side="left", padx=(0, 8))
        self.qual = tk.StringVar(value=self.cfg["quality"])
        self.qual.trace_add("write", self._on_format)
        self.qmenu = tk.OptionMenu(o, self.qual, *config.QUALITIES)
        self._menu(self.qmenu, NEON_V)
        self.qmenu.pack(side="left")
        self.qhint = tk.Label(o, text="", font=FONT_SMALL, bg=BG2, fg=MUTED)
        self.qhint.pack(side="left", padx=12)

        c = tk.Frame(opt, bg=BG2)
        c.pack(fill="x")
        self.thumb = tk.IntVar(value=int(self.cfg["embed_thumbnail"]))
        self.meta = tk.IntVar(value=int(self.cfg["embed_metadata"]))
        self.sub = tk.IntVar(value=int(self.cfg["subfolder_per_playlist"]))
        for text, var in (("Pochette", self.thumb), ("Métadonnées", self.meta),
                          ("Sous-dossier par playlist", self.sub)):
            tk.Checkbutton(c, text=text, variable=var, font=FONT_SMALL, bg=BG2,
                           fg=TEXT, selectcolor=BG3, activebackground=BG2,
                           activeforeground=NEON_G, bd=0,
                           highlightthickness=0, cursor="hand2").pack(
                side="left", padx=(0, 16))
        NeonButton(c, "💾  ENREGISTRER", NEON_G, self._save,
                   width=155, height=34, radius=17, bg=BG2).pack(side="right")
        self._on_format()

        # Statut
        st = tk.Frame(self, bg=BG2, highlightthickness=1, highlightbackground=BORDER)
        st.pack(fill="x", padx=28, pady=(4, 8))
        self.dot = tk.Label(st, text="●", font=FONT, bg=BG2, fg=NEON_G)
        self.dot.pack(side="left", padx=(14, 8), pady=8)
        self.status = tk.StringVar(value="Prêt")
        tk.Label(st, textvariable=self.status, font=FONT, bg=BG2,
                 fg=TEXT).pack(side="left")

        # Log
        lf = tk.Frame(self, bg=BG)
        lf.pack(fill="both", expand=True, padx=28, pady=(0, 14))
        lh = tk.Frame(lf, bg=BG)
        lh.pack(fill="x")
        tk.Label(lh, text="LOG", font=FONT_LABEL, bg=BG, fg=NEON_G).pack(side="left")
        tk.Button(lh, text="effacer", font=FONT_SMALL, bg=BG, fg=MUTED, bd=0,
                  activebackground=BG, activeforeground=NEON_P, cursor="hand2",
                  command=self._clear).pack(side="right")
        self.log = scrolledtext.ScrolledText(
            lf, bg="#0a0812", fg="#b9b3cc", font=FONT_MONO, height=9, bd=0,
            relief="flat", wrap="word", insertbackground=NEON_G, state="disabled",
            highlightthickness=1, highlightbackground=BORDER)
        self.log.pack(fill="both", expand=True, pady=(4, 0))
        for tag, col in (("ok", NEON_G), ("err", ERR), ("info", TEXT)):
            self.log.tag_config(tag, foreground=col)

    def _source_block(self, parent, label, url_var, dir_var, accent):
        r1 = tk.Frame(parent, bg=BG2)
        r1.pack(fill="x", pady=(0, 6))
        tk.Label(r1, text=label, font=FONT_BOLD, bg=BG2, fg=accent,
                 width=11, anchor="w").pack(side="left")
        entry(r1, url_var, accent).pack(side="left", fill="x", expand=True, ipady=7)
        r2 = tk.Frame(parent, bg=BG2)
        r2.pack(fill="x")
        tk.Label(r2, text="↳ dossier", font=FONT_SMALL, bg=BG2, fg=MUTED,
                 width=11, anchor="w").pack(side="left")
        entry(r2, dir_var, accent).pack(side="left", fill="x", expand=True,
                                        ipady=6, padx=(0, 8))
        NeonButton(r2, "📁", accent, lambda: self._browse(dir_var), width=52,
                   height=30, radius=15, bg=BG2,
                   fg="#ffffff" if accent != NEON_G else BG).pack(side="left")

    def _menu(self, menu, accent):
        menu.config(bg=BG3, fg=TEXT, font=FONT_SMALL, bd=0, width=8,
                    highlightthickness=1, highlightbackground=BORDER,
                    activebackground=accent, activeforeground=BG, relief="flat",
                    cursor="hand2", indicatoron=0, padx=10, pady=6)
        menu["menu"].config(bg=BG3, fg=TEXT, font=FONT_SMALL,
                            activebackground=accent, activeforeground=BG, bd=0)

    # ── Réactions ─────────────────────────────────────────────────────────────
    def _browse(self, var):
        d = filedialog.askdirectory(initialdir=var.get() or os.path.expanduser("~"),
                                    title="Choisir un dossier")
        if d:
            var.set(d)
            self._save(silent=True)

    def _on_format(self, *_):
        if self.fmt.get() in config.LOSSLESS:
            self.qmenu.config(state="disabled")
            self.qhint.config(text="sans perte — débit ignoré", fg=NEON_G)
        else:
            self.qmenu.config(state="normal")
            self.qhint.config(text=QUALITY_LABELS.get(self.qual.get(), ""), fg=MUTED)

    def _on_url(self, *_):
        src = detect_source(self.url.get())
        if src == "youtube":
            self.detect.config(text="▶ YOUTUBE", fg=NEON_P)
            self.go_btn.set_color(NEON_G, fg=BG)
            self.go_btn.set_state(True)
        elif src == "soundcloud":
            self.detect.config(text="☁ SOUNDCLOUD", fg=NEON_V)
            self.go_btn.set_color(NEON_V, fg="#ffffff")
            self.go_btn.set_state(True)
        else:
            self.detect.config(text="—", fg=MUTED)
            self.go_btn.set_color(BG3, fg=MUTED)
            self.go_btn.set_state(False)

    def _say(self, msg):
        self.log.config(state="normal")
        low = msg.lower()
        tag = "ok" if "✓" in msg else ("err" if "✗" in msg or "erreur" in low else "info")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")

    def _clear(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    def _save(self, silent=False):
        self.cfg.update({
            "youtube_url": self.yt_url.get().strip(),
            "youtube_dir": self.yt_dir.get().strip(),
            "soundcloud_url": self.sc_url.get().strip(),
            "soundcloud_dir": self.sc_dir.get().strip(),
            "output_dir": self.out_dir.get().strip(),
            "format": self.fmt.get(),
            "quality": self.qual.get(),
            "embed_thumbnail": bool(self.thumb.get()),
            "embed_metadata": bool(self.meta.get()),
            "subfolder_per_playlist": bool(self.sub.get()),
        })
        err = config.save(self.cfg)
        if err:
            messagebox.showerror("Erreur", f"Configuration non enregistrée :\n{err}")
        elif not silent:
            self._say("✓ Réglages enregistrés.")

    # ── Téléchargement ────────────────────────────────────────────────────────
    def _running(self, on, label=""):
        for b in (self.yt_btn, self.sc_btn):
            b.set_state(not on)
        self.go_btn.set_state((not on) and detect_source(self.url.get()) is not None)
        self.stop_btn.set_state(on)
        self.dot.config(fg=NEON_V if on else NEON_G)
        self.status.set(f"{label} en cours…" if on else "Prêt")

    def _start(self, url, out, label):
        url = (url or "").strip()
        out = os.path.expanduser((out or "").strip())
        if not detect_source(url):
            messagebox.showwarning(
                "URL manquante",
                "Renseigne une URL YouTube ou SoundCloud valide.")
            return
        if not os.path.isdir(out):
            messagebox.showerror("Dossier introuvable",
                                 f"Ce dossier n'existe pas :\n{out}")
            return

        self._save(silent=True)
        self._cancel.clear()
        self._running(True, label)
        self._say("\n" + "─" * 60)

        def work():
            try:
                download(url, out,
                         fmt=self.fmt.get(), quality=self.qual.get(),
                         embed_thumbnail=bool(self.thumb.get()),
                         embed_metadata=bool(self.meta.get()),
                         subfolder_per_playlist=bool(self.sub.get()),
                         on_message=lambda m: self.after(0, self._say, m),
                         on_progress=self._check_cancel)
            except DownloadError as e:
                self.after(0, self._say, f"✗ {e}")
            except Exception as e:                      # filet de sécurité
                self.after(0, self._say, f"✗ Erreur inattendue : {e}")
            finally:
                self.after(0, self._running, False)

        threading.Thread(target=work, daemon=True).start()

    def _check_cancel(self, _d):
        """Appelé par yt-dlp à chaque étape : lève pour interrompre proprement."""
        if self._cancel.is_set():
            raise KeyboardInterrupt("Interrompu par l'utilisateur")

    def _stop(self):
        self._cancel.set()
        self._say("⏹ Arrêt demandé — fin du morceau en cours…")
