"""
Conference-Sharker: Academic Conference Deadline Countdown Widget

Lightweight floating desktop widget for tracking academic conference deadlines.
- Zero external dependencies (pure tkinter)
- Rounded-corner translucent floating window
- Embedded calendar picker for deadline selection
- Auto-start via Windows Registry
"""

import tkinter as tk
from tkinter import messagebox
import json
import os
import sys
import calendar as cal_mod
from datetime import datetime, date
from uuid import uuid4

try:
    import winreg
except ImportError:
    winreg = None

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.abspath(sys.argv[0]))

DATA_FILE = os.path.join(_BASE, "deadlines.json")
APP_NAME = "Conference-Sharker"
W = 380
CORNER_R = 16

# Catppuccin Mocha
BG       = "#1e1e2e"
CARD     = "#313244"
TITLE_BG = "#181825"
TEXT     = "#cdd6f4"
SUB      = "#a6adc8"
GREEN    = "#a6e3a1"
YELLOW   = "#f9e2af"
ORANGE   = "#fab387"
RED      = "#f38ba8"
BLUE     = "#89b4fa"
LAVENDER = "#b4befe"
SURFACE  = "#45475a"
SURFACE2 = "#585b70"
OVERLAY  = "#6c7086"
CRUST    = "#11111b"

FONT = "Segoe UI"
MONO = "Consolas"

MONTHS = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _round_region(win):
    """Clip window to a rounded rectangle (Windows GDI)."""
    try:
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        w, h = win.winfo_width(), win.winfo_height()
        if w < 10 or h < 10:
            return
        rgn = ctypes.windll.gdi32.CreateRoundRectRgn(
            0, 0, w + 1, h + 1, CORNER_R, CORNER_R,
        )
        ctypes.windll.user32.SetWindowRgn(hwnd, rgn, True)
    except Exception:
        pass


# ===================================================================
# CalendarFrame – embedded month calendar
# ===================================================================
class CalendarFrame(tk.Frame):
    def __init__(self, parent, selected=None, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._sel = selected or date.today()
        self._vy = self._sel.year
        self._vm = self._sel.month
        self._build()

    def _build(self):
        nav = tk.Frame(self, bg=BG)
        nav.pack(fill="x", pady=(0, 4))

        abtn = dict(
            bg=SURFACE, fg=TEXT, bd=0, font=(FONT, 10),
            activebackground=BLUE, activeforeground=CRUST,
            cursor="hand2", width=3, pady=1,
        )
        tk.Button(nav, text="\u25c0", command=self._prev, **abtn).pack(side="left")
        self._title = tk.Label(nav, bg=BG, fg=TEXT, font=(FONT, 10, "bold"))
        self._title.pack(side="left", expand=True)
        tk.Button(nav, text="\u25b6", command=self._next, **abtn).pack(side="right")

        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x")
        for i, d in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            fg = RED if i == 6 else ORANGE if i == 5 else SUB
            tk.Label(hdr, text=d, bg=BG, fg=fg, font=(FONT, 9), width=4).pack(
                side="left", expand=True,
            )

        tk.Frame(self, bg=SURFACE, height=1).pack(fill="x", pady=3)
        self._grid = tk.Frame(self, bg=BG)
        self._grid.pack(fill="x")
        self._render()

    def _render(self):
        for w in self._grid.winfo_children():
            w.destroy()
        self._title.config(text=f"{MONTHS[self._vm]} {self._vy}")

        today = date.today()
        for week in cal_mod.monthcalendar(self._vy, self._vm):
            row = tk.Frame(self._grid, bg=BG)
            row.pack(fill="x", pady=1)
            for day in week:
                if day == 0:
                    tk.Label(row, text="", bg=BG, width=4, font=(FONT, 9)).pack(
                        side="left", expand=True,
                    )
                    continue
                d = date(self._vy, self._vm, day)
                is_sel = d == self._sel
                is_today = d == today
                bg_c = BLUE if is_sel else SURFACE if is_today else BG
                fg_c = CRUST if is_sel else LAVENDER if is_today else TEXT
                lbl = tk.Label(
                    row, text=str(day), bg=bg_c, fg=fg_c,
                    font=(FONT, 9, "bold" if is_sel or is_today else ""),
                    width=4, cursor="hand2",
                )
                lbl.pack(side="left", expand=True, padx=1, pady=1)
                lbl.bind("<Button-1>", lambda _, dd=day: self._pick(dd))
                _bg = bg_c
                lbl.bind(
                    "<Enter>",
                    lambda _, l=lbl, s=is_sel: l.configure(bg=BLUE if s else SURFACE2),
                )
                lbl.bind("<Leave>", lambda _, l=lbl, b=_bg: l.configure(bg=b))

    def _pick(self, day):
        self._sel = date(self._vy, self._vm, day)
        self._render()

    def _prev(self):
        self._vm -= 1
        if self._vm < 1:
            self._vm, self._vy = 12, self._vy - 1
        self._render()

    def _next(self):
        self._vm += 1
        if self._vm > 12:
            self._vm, self._vy = 1, self._vy + 1
        self._render()

    @property
    def selected(self):
        return self._sel


# ===================================================================
# App – main floating widget
# ===================================================================
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.data = self._load()
        self.cards = []
        self._dx = self._dy = 0
        self._collapsed = False
        self._last_sz = (0, 0)

        self._init_window()
        self._init_ui()
        self._refresh()
        self.root.update_idletasks()
        _round_region(self.root)
        self._ensure_autostart()
        self._tick()

    # ---- Data ----

    def _load(self):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"deadlines": [], "pos": [100, 100]}

    def _save(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ---- Window ----

    def _init_window(self):
        r = self.root
        r.title(APP_NAME)
        r.overrideredirect(True)
        r.attributes("-topmost", True)
        r.attributes("-alpha", 0.88)
        r.configure(bg=BG)
        r.minsize(W, 34)

        sw, sh = r.winfo_screenwidth(), r.winfo_screenheight()
        x, y = self.data.get("pos", [100, 100])
        x, y = max(0, min(int(x), sw - 120)), max(0, min(int(y), sh - 60))
        r.geometry(f"+{x}+{y}")
        r.bind("<Configure>", self._on_cfg)

    def _on_cfg(self, event):
        if event.widget is not self.root:
            return
        sz = (event.width, event.height)
        if sz != self._last_sz:
            self._last_sz = sz
            _round_region(self.root)

    # ---- UI ----

    def _init_ui(self):
        tb = tk.Frame(self.root, bg=TITLE_BG, height=34)
        tb.pack(fill="x")
        tb.pack_propagate(False)

        title = tk.Label(
            tb, text="  Conference-Sharker", bg=TITLE_BG, fg=LAVENDER,
            font=(FONT, 10, "bold"),
        )
        title.pack(side="left", padx=6)

        for w in (tb, title):
            w.bind("<Button-1>", self._press)
            w.bind("<B1-Motion>", self._drag)
            w.bind("<ButtonRelease-1>", self._release)

        bkw = dict(
            bg=TITLE_BG, fg=OVERLAY, bd=0, font=(MONO, 12),
            activebackground=SURFACE, activeforeground=TEXT,
            cursor="hand2", width=3,
        )
        tk.Button(tb, text="\u00d7", command=self._quit, **bkw).pack(side="right")
        tk.Button(tb, text="\u2500", command=self._collapse, **bkw).pack(side="right")
        tk.Button(tb, text="\u2261", command=self._open_mgr, **bkw).pack(side="right")

        self.body = tk.Frame(self.root, bg=BG)
        self.body.pack(fill="both", expand=True, padx=6, pady=(2, 0))

        foot = tk.Frame(self.root, bg=BG)
        foot.pack(fill="x", padx=6, pady=(4, 6))
        foot.columnconfigure(0, weight=1)
        foot.columnconfigure(1, weight=1)
        tk.Button(
            foot, text="+ Add Conference", command=self._add,
            bg=SURFACE, fg=TEXT, font=(FONT, 9),
            activebackground=BLUE, activeforeground=CRUST,
            bd=0, pady=6, cursor="hand2",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        tk.Button(
            foot, text="\u2261 Manage", command=self._open_mgr,
            bg=SURFACE, fg=TEXT, font=(FONT, 9),
            activebackground=BLUE, activeforeground=CRUST,
            bd=0, pady=6, cursor="hand2",
        ).grid(row=0, column=1, sticky="ew", padx=(2, 0))
        self._foot = foot

        mkw = dict(
            tearoff=0, bg=CARD, fg=TEXT,
            activebackground=BLUE, activeforeground=CRUST,
            font=(FONT, 9), relief="flat", bd=0,
        )
        self.ctx = tk.Menu(self.root, **mkw)
        self.ctx.add_command(label="  Add Conference", command=self._add)
        self.ctx.add_command(label="  Manage", command=self._open_mgr)
        self.ctx.add_separator()
        self.ctx.add_command(label="  Toggle Auto-start", command=self._autostart)
        self.ctx.add_separator()
        self.ctx.add_command(label="  Quit", command=self._quit)
        self.root.bind("<Button-3>", lambda e: self.ctx.post(e.x_root, e.y_root))

        self._cctx = tk.Menu(self.root, **mkw)

    # ---- Cards ----

    def _refresh(self):
        for c in self.cards:
            c["f"].destroy()
        self.cards.clear()

        dls = sorted(
            self.data.get("deadlines", []), key=lambda d: d.get("deadline", ""),
        )

        if not dls:
            f = tk.Frame(self.body, bg=CARD, padx=14, pady=14)
            f.pack(fill="x", pady=3)
            tk.Label(
                f, text="Click below to add a conference",
                bg=CARD, fg=SUB, font=(FONT, 10),
            ).pack()
            self.cards.append({"f": f, "cd": None})
            return

        for dl in dls:
            f = tk.Frame(self.body, bg=CARD, padx=14, pady=8)
            f.pack(fill="x", pady=3)

            l_name = tk.Label(
                f, text=dl["paper"], bg=CARD, fg=TEXT,
                font=(FONT, 10, "bold"), anchor="w",
            )
            l_name.pack(fill="x")

            sub_text = f"{dl['conference']}  \u00b7  {dl['deadline'][:10]}"
            l_sub = tk.Label(
                f, text=sub_text, bg=CARD, fg=SUB,
                font=(FONT, 9), anchor="w",
            )
            l_sub.pack(fill="x")

            cd = tk.Label(
                f, text="", bg=CARD, fg=GREEN,
                font=(MONO, 22, "bold"), anchor="w",
            )
            cd.pack(fill="x")

            did = dl["id"]
            ws = [f, l_name, l_sub, cd]
            for w in ws:
                w.bind("<Enter>", lambda _, ws=ws: [x.config(bg=SURFACE) for x in ws])
                w.bind("<Leave>", lambda _, ws=ws: [x.config(bg=CARD) for x in ws])
                w.bind("<Button-3>", lambda e, d=did: self._card_ctx(e, d))

            self.cards.append({"f": f, "cd": cd, "dl": dl["deadline"]})

    def _card_ctx(self, event, did):
        m = self._cctx
        m.delete(0, "end")
        m.add_command(label="  Edit", command=lambda: self._edit(did))
        m.add_command(label="  Delete", command=lambda: self._delete(did))
        m.post(event.x_root, event.y_root)

    # ---- Countdown (1 s tick) ----

    def _tick(self):
        now = datetime.now()
        for c in self.cards:
            lbl = c.get("cd")
            if lbl is None:
                continue
            try:
                target = datetime.strptime(c["dl"], "%Y-%m-%d %H:%M:%S")
                secs = int((target - now).total_seconds())
                if secs <= 0:
                    lbl.config(text="EXPIRED", fg=OVERLAY)
                else:
                    d, rem = divmod(secs, 86400)
                    h, rem = divmod(rem, 3600)
                    mi, s = divmod(rem, 60)
                    txt = (
                        f"{d}d {h:02d}:{mi:02d}:{s:02d}"
                        if d else f"{h:02d}:{mi:02d}:{s:02d}"
                    )
                    color = (
                        GREEN if secs > 30 * 86400
                        else YELLOW if secs > 7 * 86400
                        else ORANGE if secs > 86400
                        else RED
                    )
                    lbl.config(text=txt, fg=color)
            except (ValueError, KeyError, tk.TclError):
                continue
        self.root.after(1000, self._tick)

    # ---- Drag ----

    def _press(self, e):
        self._dx, self._dy = e.x, e.y

    def _drag(self, e):
        self.root.geometry(
            f"+{self.root.winfo_x() + e.x - self._dx}"
            f"+{self.root.winfo_y() + e.y - self._dy}"
        )

    def _release(self, _):
        self.data["pos"] = [self.root.winfo_x(), self.root.winfo_y()]
        self._save()

    # ---- Actions ----

    def _collapse(self):
        if self._collapsed:
            self.body.pack(fill="both", expand=True, padx=6, pady=(2, 0))
            self._foot.pack(fill="x", padx=6, pady=(4, 6))
        else:
            self.body.pack_forget()
            self._foot.pack_forget()
        self._collapsed = not self._collapsed

    def _add(self):
        DlgDeadline(self.root, cb=self._on_saved)

    def _edit(self, did):
        dl = next((d for d in self.data["deadlines"] if d["id"] == did), None)
        if dl:
            DlgDeadline(self.root, data=dl, cb=self._on_saved)

    def _delete(self, did, parent=None):
        if messagebox.askyesno(
            "Confirm", "Delete this entry?", parent=parent or self.root,
        ):
            self.data["deadlines"] = [
                d for d in self.data["deadlines"] if d["id"] != did
            ]
            self._save()
            self._refresh()

    def _on_saved(self, dl):
        idx = next(
            (i for i, d in enumerate(self.data["deadlines"]) if d["id"] == dl["id"]),
            None,
        )
        if idx is not None:
            self.data["deadlines"][idx] = dl
        else:
            self.data["deadlines"].append(dl)
        self._save()
        self._refresh()

    def _open_mgr(self):
        ManagerWin(self.root, self)

    def _ensure_autostart(self):
        """Register auto-start on first launch (silent, no dialog)."""
        if not winreg:
            return
        kp = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, kp, 0, winreg.KEY_ALL_ACCESS,
            ) as key:
                try:
                    winreg.QueryValueEx(key, APP_NAME)
                except FileNotFoundError:
                    if getattr(sys, "frozen", False):
                        val = f'"{sys.executable}"'
                    else:
                        val = f'pythonw "{os.path.abspath(sys.argv[0])}"'
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, val)
        except Exception:
            pass

    def _autostart(self):
        if not winreg:
            return
        kp = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, kp, 0, winreg.KEY_ALL_ACCESS,
            ) as key:
                try:
                    winreg.QueryValueEx(key, APP_NAME)
                    winreg.DeleteValue(key, APP_NAME)
                    messagebox.showinfo(
                        "Auto-start", "Auto-start disabled.", parent=self.root,
                    )
                except FileNotFoundError:
                    if getattr(sys, "frozen", False):
                        val = f'"{sys.executable}"'
                    else:
                        val = f'pythonw "{os.path.abspath(sys.argv[0])}"'
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, val)
                    messagebox.showinfo(
                        "Auto-start", "Auto-start enabled.", parent=self.root,
                    )
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.root)

    def _quit(self):
        self.data["pos"] = [self.root.winfo_x(), self.root.winfo_y()]
        self._save()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ===================================================================
# DlgDeadline – add / edit with embedded calendar + time picker
# ===================================================================
class DlgDeadline:
    def __init__(self, parent, data=None, cb=None):
        self.cb, self.data = cb, data

        if data:
            try:
                dt = datetime.strptime(data["deadline"], "%Y-%m-%d %H:%M:%S")
                init_d, init_t = dt.date(), (dt.hour, dt.minute, dt.second)
            except (ValueError, KeyError):
                init_d, init_t = date.today(), (20, 0, 0)
        else:
            init_d, init_t = date.today(), (20, 0, 0)

        w = tk.Toplevel(parent)
        self.win = w
        w.title("Edit Conference" if data else "Add Conference")
        w.configure(bg=BG)
        w.attributes("-topmost", True)
        w.transient(parent)
        w.grab_set()

        # -- Paper --
        tk.Label(
            w, text="Paper Title", bg=BG, fg=TEXT, font=(FONT, 9),
        ).pack(anchor="w", padx=24, pady=(16, 0))
        self.e_paper = self._entry(w)
        self.e_paper.insert(0, (data or {}).get("paper", ""))

        # -- Conference --
        tk.Label(
            w, text="Conference", bg=BG, fg=TEXT, font=(FONT, 9),
        ).pack(anchor="w", padx=24, pady=(10, 0))
        self.e_conf = self._entry(w)
        self.e_conf.insert(0, (data or {}).get("conference", ""))

        # -- Calendar --
        tk.Label(
            w, text="Deadline Date", bg=BG, fg=TEXT, font=(FONT, 9),
        ).pack(anchor="w", padx=24, pady=(10, 0))
        self.cal = CalendarFrame(w, selected=init_d)
        self.cal.pack(fill="x", padx=24, pady=(4, 0))

        # -- Time --
        tk.Frame(w, bg=SURFACE, height=1).pack(fill="x", padx=24, pady=(10, 0))
        tf = tk.Frame(w, bg=BG)
        tf.pack(fill="x", padx=24, pady=(8, 0))

        tk.Label(tf, text="Time", bg=BG, fg=TEXT, font=(FONT, 10)).pack(side="left")

        skw = dict(
            width=3, font=(MONO, 13), bg=CARD, fg=TEXT,
            insertbackground=TEXT, selectbackground=BLUE,
            selectforeground=CRUST, buttonbackground=SURFACE,
            bd=0, relief="flat", wrap=True, justify="center",
        )
        self.sp_h = tk.Spinbox(tf, from_=0, to=23, format="%02.0f", **skw)
        self.sp_h.pack(side="left", padx=(12, 0))
        self.sp_h.delete(0, "end")
        self.sp_h.insert(0, f"{init_t[0]:02d}")

        tk.Label(tf, text=":", bg=BG, fg=OVERLAY, font=(MONO, 14, "bold")).pack(
            side="left",
        )
        self.sp_m = tk.Spinbox(tf, from_=0, to=59, format="%02.0f", **skw)
        self.sp_m.pack(side="left")
        self.sp_m.delete(0, "end")
        self.sp_m.insert(0, f"{init_t[1]:02d}")

        tk.Label(tf, text=":", bg=BG, fg=OVERLAY, font=(MONO, 14, "bold")).pack(
            side="left",
        )
        self.sp_s = tk.Spinbox(tf, from_=0, to=59, format="%02.0f", **skw)
        self.sp_s.pack(side="left")
        self.sp_s.delete(0, "end")
        self.sp_s.insert(0, f"{init_t[2]:02d}")

        # -- Buttons --
        bf = tk.Frame(w, bg=BG)
        bf.pack(fill="x", padx=24, pady=(14, 16))
        tk.Button(
            bf, text="Save", command=self._save, bg=BLUE, fg=CRUST,
            font=(FONT, 10, "bold"), bd=0, padx=24, pady=5, cursor="hand2",
        ).pack(side="right")
        tk.Button(
            bf, text="Cancel", command=w.destroy, bg=SURFACE, fg=TEXT,
            font=(FONT, 10), bd=0, padx=24, pady=5, cursor="hand2",
        ).pack(side="right", padx=(0, 10))

        w.update_idletasks()
        rw = max(420, w.winfo_reqwidth())
        rh = w.winfo_reqheight()
        px = parent.winfo_x() + parent.winfo_width() // 2 - rw // 2
        py = max(parent.winfo_y() - 80, 20)
        w.geometry(f"{rw}x{rh}+{px}+{py}")
        w.resizable(False, False)

        self.e_paper.focus_set()
        w.bind("<Return>", lambda _: self._save())
        w.bind("<Escape>", lambda _: w.destroy())

    @staticmethod
    def _entry(parent):
        e = tk.Entry(
            parent, font=(FONT, 11), bg=CARD, fg=TEXT,
            insertbackground=TEXT, bd=0, relief="flat",
            selectbackground=BLUE, selectforeground=CRUST,
        )
        e.pack(fill="x", padx=24, pady=(4, 0), ipady=6)
        return e

    def _save(self):
        paper = self.e_paper.get().strip()
        conf = self.e_conf.get().strip()
        if not paper or not conf:
            messagebox.showwarning(
                "Missing Fields", "Please fill in both Paper Title and Conference.",
                parent=self.win,
            )
            return
        try:
            h, m, s = int(self.sp_h.get()), int(self.sp_m.get()), int(self.sp_s.get())
            if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Invalid Time", "Please enter a valid time.", parent=self.win,
            )
            return

        d = self.cal.selected
        deadline = f"{d.year:04d}-{d.month:02d}-{d.day:02d} {h:02d}:{m:02d}:{s:02d}"
        if self.cb:
            self.cb({
                "id": (self.data or {}).get("id", uuid4().hex[:8]),
                "paper": paper,
                "conference": conf,
                "deadline": deadline,
            })
        self.win.destroy()


# ===================================================================
# ManagerWin – backend management panel
# ===================================================================
class ManagerWin:
    def __init__(self, parent, app):
        self.app = app

        w = tk.Toplevel(parent)
        self.win = w
        w.title("Manage \u2014 Conference-Sharker")
        w.geometry("540x460")
        w.configure(bg=BG)
        w.attributes("-topmost", True)
        w.transient(parent)

        w.update_idletasks()
        sw, sh = w.winfo_screenwidth(), w.winfo_screenheight()
        w.geometry(f"+{sw // 2 - 270}+{sh // 2 - 230}")

        hdr = tk.Frame(w, bg=TITLE_BG, height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr, text="  Deadline Manager", bg=TITLE_BG, fg=TEXT,
            font=(FONT, 12, "bold"),
        ).pack(side="left")
        tk.Button(
            hdr, text="+ Add Conference", command=self._add, bg=BLUE, fg=CRUST,
            font=(FONT, 9, "bold"), bd=0, padx=14, pady=3, cursor="hand2",
        ).pack(side="right", padx=12)

        box = tk.Frame(w, bg=BG)
        box.pack(fill="both", expand=True, padx=8, pady=8)

        self.canvas = tk.Canvas(box, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(box, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=BG)

        self.inner.bind(
            "<Configure>",
            lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw", tags="inn")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig("inn", width=e.width),
        )
        self.canvas.bind(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(-e.delta // 120, "units"),
        )
        w.bind("<Escape>", lambda _: w.destroy())
        self._refresh()

    def _refresh(self):
        for ch in self.inner.winfo_children():
            ch.destroy()

        dls = sorted(
            self.app.data.get("deadlines", []), key=lambda d: d.get("deadline", ""),
        )

        if not dls:
            tk.Label(
                self.inner,
                text='No conferences yet.\nClick "+ Add Conference" to get started.',
                bg=BG, fg=SUB, font=(FONT, 11), pady=80,
            ).pack(fill="x")
            return

        for dl in dls:
            row = tk.Frame(self.inner, bg=CARD, padx=14, pady=10)
            row.pack(fill="x", pady=3)

            info = tk.Frame(row, bg=CARD)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(
                info, text=dl["paper"], bg=CARD, fg=TEXT,
                font=(FONT, 10, "bold"), anchor="w",
            ).pack(fill="x")
            tk.Label(
                info,
                text=f"{dl['conference']}  \u00b7  {dl['deadline']}",
                bg=CARD, fg=SUB, font=(FONT, 9), anchor="w",
            ).pack(fill="x")

            btns = tk.Frame(row, bg=CARD)
            btns.pack(side="right", padx=(8, 0))
            did = dl["id"]
            tk.Button(
                btns, text="Edit", command=lambda d=did: self._edit(d),
                bg=SURFACE, fg=TEXT, font=(FONT, 9),
                bd=0, padx=10, pady=2, cursor="hand2",
            ).pack(side="left", padx=2)
            tk.Button(
                btns, text="Del", command=lambda d=did: self._del(d),
                bg=RED, fg=CRUST, font=(FONT, 9),
                bd=0, padx=10, pady=2, cursor="hand2",
            ).pack(side="left", padx=2)

    def _add(self):
        DlgDeadline(self.win, cb=self._on_saved)

    def _edit(self, did):
        dl = next((d for d in self.app.data["deadlines"] if d["id"] == did), None)
        if dl:
            DlgDeadline(self.win, data=dl, cb=self._on_saved)

    def _del(self, did):
        if messagebox.askyesno("Confirm", "Delete this entry?", parent=self.win):
            self.app.data["deadlines"] = [
                d for d in self.app.data["deadlines"] if d["id"] != did
            ]
            self.app._save()
            self.app._refresh()
            self._refresh()

    def _on_saved(self, dl):
        self.app._on_saved(dl)
        self._refresh()


# ===================================================================
if __name__ == "__main__":
    App().run()
