"""
Layer 2 - Windows desktop app for the Grammar Corrector.

Select text in ANY application, press the hotkey (default Ctrl+Alt+H) and a
small floating card shows exactly what would change. Accept to replace the
selection in place, Copy to keep the result on the clipboard, or ignore it.
The card can be dragged anywhere and pinned.

    pip install nltk symspellpy pyperclip
    python build_models.py                  # once
    python desktop_app/hotkey_listener.py   # no Administrator rights needed

    --hotkey ctrl+alt+h             change the trigger
    --accept-hotkey ctrl+alt+enter  accept the visible suggestion from the keyboard
    --demo                          show a sample card (UI preview, any OS)

Why the old version was inconsistent ("sometimes nothing happens")
-------------------------------------------------------------------
 1. The hotkey callback ran inside a low-level keyboard HOOK and slept /
    polled the clipboard there. Windows silently unhooks slow hooks, so after
    a slow press the hotkey could stay dead. Now: RegisterHotKey + a worker
    thread (see winapi.py).
 2. The copy step slept a fixed 0.15 s and then compared the clipboard text
    with what was there before. A slow app (Word, Chrome, Docs) missed the
    window, and re-selecting text that was already on the clipboard looked
    like "nothing was copied". Now: the clipboard SEQUENCE NUMBER is polled
    (it changes on every copy, even of identical text) with a retry.
 3. Ctrl+C was injected while Alt was still physically held. Now we wait for
    the keys to be released and inject the whole combo with one SendInput.
 4. Every failure only printed to a console nobody was looking at. Now each
    outcome has its own on-screen message: "No text selected", "Clipboard
    busy", "No issues found", ...
"""
import argparse
import difflib
import os
import queue
import re
import sys
import threading
import time
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import tkinter as tk
import tkinter.font as tkfont

from desktop_app import winapi

try:
    import pyperclip
except ImportError:  # pragma: no cover
    pyperclip = None

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
HOTKEY = "ctrl+alt+h"
ACCEPT_HOTKEY = "ctrl+alt+enter"
MAX_CHARS = 20000            # refuse absurdly large selections
AUTO_DISMISS_MS = 45000      # card closes by itself (not while hovered / pinned)
COPY_TIMEOUTS = (0.7, 0.6)   # seconds to wait for the 1st (Ctrl+C) / 2nd (Ctrl+Insert) copy
USER_DICTIONARY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "user_dictionary.txt")

THEME = dict(
    bg="#16181d", card="#1f2229", border="#343947", text="#e8eaf0", muted="#8a90a0",
    accent="#6c8cff", accent_hi="#8aa3ff", btn="#2a2e38", btn_hi="#363b49",
    ok="#4ade80", ok_bg="#12331f", bad="#f87171", bad_bg="#3d1d20",
    warn="#fbbf24", info="#60a5fa",
)

LABELS = {
    "subject_verb_agreement": "Subject-verb agreement", "article_error": "Article",
    "spelling": "Spelling", "confused_word": "Word choice", "punctuation": "Punctuation",
    "capitalization": "Capitalization", "comma_splice": "Comma splice",
    "sentence_fragment": "Sentence fragment", "preposition_error": "Preposition",
}


def _label(kind):
    return LABELS.get(kind, str(kind).replace("_", " ").capitalize())


# ---------------------------------------------------------------------------
# Clipboard helpers (the Windows clipboard is a shared, lockable resource)
# ---------------------------------------------------------------------------
def clip_get():
    for _ in range(8):
        try:
            return pyperclip.paste()
        except Exception:
            time.sleep(0.03)
    return None


def clip_set(text):
    for _ in range(8):
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            time.sleep(0.03)
    return False


def wait_for_sequence_change(seq0, timeout):
    """True as soon as the clipboard sequence number differs from seq0."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if winapi.clipboard_sequence() != seq0:
            return True
        time.sleep(0.01)
    return winapi.clipboard_sequence() != seq0


class Capture:
    """Outcome of trying to read the user's selection."""
    def __init__(self, text=None, error=None, backup=None):
        self.text, self.error, self.backup = text, error, backup


def capture_selection(hwnd, release_vks):
    """Copy the current selection of the foreground app and return it.

    error is one of: 'terminal', 'no_selection', 'clipboard_busy', 'too_long'.
    """
    exe = winapi.process_name_of_window(hwnd)
    if exe in winapi.TERMINAL_PROCESSES:
        return Capture(error="terminal")

    winapi.wait_keys_released(release_vks, timeout=1.5)
    backup = clip_get()
    seq0 = winapi.clipboard_sequence()      # ONE snapshot: a slow first copy still counts

    copied = False
    for method, timeout in zip(("ctrl+c", "ctrl+insert"), COPY_TIMEOUTS):
        winapi.send_copy(method)
        if wait_for_sequence_change(seq0, timeout):
            copied = True
            break
    if not copied:
        return Capture(error="no_selection", backup=backup)

    time.sleep(0.03)          # let the source app finish writing all formats
    text = clip_get()
    if text is None:
        return Capture(error="clipboard_busy", backup=backup)
    if backup:                # put the user's own clipboard text back right away
        clip_set(backup)
    if not text.strip():
        return Capture(error="no_selection")
    if len(text) > MAX_CHARS:
        return Capture(error="too_long")
    return Capture(text=text, backup=backup)


def paste_replace(job):
    """Replace the (still selected) text in the source window with the correction."""
    if job.get("hwnd") and winapi.get_foreground_window() != job["hwnd"]:
        winapi.set_foreground_window(job["hwnd"])
        time.sleep(0.12)
    winapi.wait_keys_released([winapi.VK_CONTROL, winapi.VK_MENU, winapi.VK_SHIFT], timeout=1.0)
    if not clip_set(job["corrected"]):
        return False
    time.sleep(0.05)
    winapi.send_paste()
    time.sleep(0.45)          # Word / browsers read the clipboard lazily
    if job.get("backup"):
        clip_set(job["backup"])
    return True


# ---------------------------------------------------------------------------
# Word-level diff for the before/after view
# ---------------------------------------------------------------------------
_TOKEN_RE = re.compile(r"\s+|\w+(?:['\u2019]\w+)*|[^\w\s]", re.UNICODE)


def diff_segments(original, corrected):
    """Returns (before, after, n_changes); each side is [(text, tag|None)]."""
    a, b = _TOKEN_RE.findall(original), _TOKEN_RE.findall(corrected)
    before, after, changes = [], [], 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        left, right = "".join(a[i1:i2]), "".join(b[j1:j2])
        if op == "equal":
            before.append((left, None))
            after.append((right, None))
            continue
        changes += 1
        if left:
            before.append((left, "del"))
        if right:
            after.append((right, "ins"))
    return before, after, changes


def wrapped_lines(text, font, width_px):
    """Number of display lines `text` needs when word-wrapped at width_px.
    Measured with the real font, so it does not depend on window layout timing."""
    total = 0
    space = font.measure(" ")
    for line in text.split("\n"):
        count, cur = 1, 0
        for word in line.split(" "):
            w = font.measure(word)
            if cur and cur + space + w > width_px:
                count += 1
                cur = w
                while cur > width_px:          # a single over-long token wraps by character
                    count += 1
                    cur -= width_px
            else:
                cur = cur + space + w if cur else w
        total += count
    return total


# ---------------------------------------------------------------------------
# Small widgets
# ---------------------------------------------------------------------------
class Btn(tk.Label):
    """Flat label-button with hover state (tk.Button looks dated on Windows)."""
    KINDS = {
        "primary": (THEME["accent"], THEME["accent_hi"], "#ffffff"),
        "secondary": (THEME["btn"], THEME["btn_hi"], THEME["text"]),
        "ghost": (THEME["card"], THEME["btn"], THEME["muted"]),
    }

    def __init__(self, parent, text, command, kind="secondary", font=None, padx=14, pady=6):
        self._bg, self._hi, fg = self.KINDS[kind]
        super().__init__(parent, text=text, bg=self._bg, fg=fg, font=font,
                         padx=padx, pady=pady, cursor="hand2")
        self._command = command
        self.bind("<Enter>", lambda e: self.configure(bg=self._hi))
        self.bind("<Leave>", lambda e: self.configure(bg=self._bg))
        self.bind("<ButtonRelease-1>", self._release)

    def _release(self, e):
        if 0 <= e.x < self.winfo_width() and 0 <= e.y < self.winfo_height():
            self._command()

    def set_text(self, text):
        self.configure(text=text)

    def set_kind(self, kind):
        self._bg, self._hi, fg = self.KINDS[kind]
        self.configure(bg=self._bg, fg=fg)


def _screen_bounds(win, x, y):
    wa = winapi.work_area_at(x, y)
    if wa:
        return wa
    return 0, 0, win.winfo_screenwidth(), win.winfo_screenheight()


def _clamp_position(win, x, y, w, h, keep_visible=True):
    left, top, right, bottom = _screen_bounds(win, x, y)
    if keep_visible:     # allow dragging partly off-screen, but never lose the header
        x = max(left - w + 80, min(x, right - 80))
        y = max(top, min(y, bottom - 40))
    else:
        x = max(left, min(x, right - w))
        y = max(top, min(y, bottom - h))
    return int(x), int(y)


# ---------------------------------------------------------------------------
# Toast (tiny, non-interactive status message)
# ---------------------------------------------------------------------------
class Toast:
    ICONS = {"ok": ("\u2713", THEME["ok"]), "info": ("\u2139", THEME["info"]),
             "warn": ("!", THEME["warn"]), "err": ("\u2715", THEME["bad"])}

    def __init__(self, app, text, kind="info", pos=None, ms=2600):
        self.win = win = tk.Toplevel(app.root)
        win.withdraw()
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=THEME["border"])
        icon, color = self.ICONS.get(kind, self.ICONS["info"])
        body = tk.Frame(win, bg=THEME["card"])
        body.pack(padx=1, pady=1)
        tk.Frame(body, bg=color, width=4).pack(side="left", fill="y")
        tk.Label(body, text=icon, bg=THEME["card"], fg=color, font=app.font(11, True),
                 padx=10).pack(side="left")
        tk.Label(body, text=text, bg=THEME["card"], fg=THEME["text"], font=app.font(10),
                 wraplength=360, justify="left", pady=9).pack(side="left", padx=(0, 14))
        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        if pos is None:
            pos = winapi.get_cursor_pos() or (win.winfo_screenwidth() // 2, win.winfo_screenheight() // 2)
        x, y = _clamp_position(win, pos[0] + 14, pos[1] + 18, w, h, keep_visible=False)
        win.geometry(f"+{x}+{y}")
        win.deiconify()
        winapi.style_popup_window(win)
        win.after(ms, self.close)

    def close(self):
        try:
            self.win.destroy()
        except tk.TclError:
            pass


# ---------------------------------------------------------------------------
# The suggestion card
# ---------------------------------------------------------------------------
class SuggestionPopup:
    WIDTH_CHARS = 54
    MAX_LINES = 7

    def __init__(self, app, job):
        self.app, self.job = app, job
        self.pinned = app.pin_pos is not None
        self.hover = False
        self.timer = None
        self._drag = None
        self.closed = False
        self.details_frame = None
        self.details_toggle = None

        t = THEME
        self.win = win = tk.Toplevel(app.root)
        win.withdraw()
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=t["border"])

        outer = tk.Frame(win, bg=t["bg"])
        outer.pack(padx=1, pady=1)

        # ---- header (drag handle) -------------------------------------
        header = tk.Frame(outer, bg=t["card"], padx=12, pady=7, cursor="fleur")
        header.pack(fill="x")
        tk.Label(header, text="\u283f", bg=t["card"], fg=t["muted"], font=app.font(12),
                 cursor="fleur").pack(side="left", padx=(0, 8))
        tk.Label(header, text="Grammar suggestion", bg=t["card"], fg=t["text"],
                 font=app.font(10, True), cursor="fleur").pack(side="left")
        before, after, n = diff_segments(job["original"], job["corrected"])
        tk.Label(header, text=f"{n} change" + ("" if n == 1 else "s"), bg=t["btn"], fg=t["accent_hi"],
                 font=app.font(8, True), padx=8, pady=1, cursor="fleur").pack(side="left", padx=10)
        Btn(header, "\u2715", self.dismiss, kind="ghost", font=app.font(10), padx=8, pady=2).pack(side="right")
        self.pin_btn = Btn(header, "Pinned" if self.pinned else "Pin", self.toggle_pin,
                           kind="primary" if self.pinned else "ghost", font=app.font(9), padx=8, pady=2)
        self.pin_btn.pack(side="right", padx=(0, 2))

        # ---- body -----------------------------------------------------
        body = tk.Frame(outer, bg=t["bg"], padx=12, pady=10)
        body.pack(fill="x")
        self._section(body, "ORIGINAL")
        self._text_box(body, before)
        self._section(body, "SUGGESTED", top=8)
        self._text_box(body, after)

        self.details_items = self._build_details(job.get("errors", []))
        if self.details_items:
            self.details_toggle = tk.Label(body, text=self._toggle_text(False), bg=t["bg"], fg=t["muted"],
                                           font=app.font(9), cursor="hand2")
            self.details_toggle.pack(anchor="w", pady=(10, 0))
            self.details_toggle.bind("<Button-1>", lambda e: self.toggle_details(body))

        # ---- footer ---------------------------------------------------
        footer = tk.Frame(outer, bg=t["card"], padx=12, pady=9)
        footer.pack(fill="x")
        Btn(footer, "Accept", self.accept, kind="primary", font=app.font(10, True)).pack(side="left")
        Btn(footer, "Copy", self.copy, font=app.font(10)).pack(side="left", padx=(6, 0))
        Btn(footer, "Dismiss", self.dismiss, kind="ghost", font=app.font(10)).pack(side="left", padx=(6, 0))
        if app.accept_hotkey_label:
            tk.Label(footer, text=app.accept_hotkey_label, bg=t["card"], fg=t["muted"],
                     font=app.font(8), cursor="fleur").pack(side="right")

        self._make_draggable(win)
        win.bind("<Enter>", self._on_enter)
        win.bind("<Leave>", self._on_leave)
        self._place()
        win.deiconify()
        winapi.style_popup_window(win)
        self._fade_in()
        self._arm_timer()

    # -- building blocks ---------------------------------------------------
    def _section(self, parent, text, top=0):
        tk.Label(parent, text=text, bg=THEME["bg"], fg=THEME["muted"],
                 font=self.app.font(8, True)).pack(anchor="w", pady=(top, 3))

    def _text_box(self, parent, segments):
        t = THEME
        box = tk.Text(parent, width=self.WIDTH_CHARS, height=2, wrap="word", bd=0, relief="flat",
                      bg=t["card"], fg=t["text"], font=self.app.font(10), padx=10, pady=8,
                      highlightthickness=1, highlightbackground=t["border"], cursor="arrow",
                      insertwidth=0, spacing3=2)
        box.tag_configure("del", foreground=t["bad"], background=t["bad_bg"], overstrike=True)
        box.tag_configure("ins", foreground=t["ok"], background=t["ok_bg"], font=self.app.font(10, True))
        for text, tg in segments:
            if tg:
                box.insert("end", text, tg)
            else:
                box.insert("end", text)
        plain = "".join(s for s, _ in segments)
        measure_font = tkfont.Font(root=self.app.root, font=self.app.font(10, True))  # bold = worst case
        inner_px = measure_font.measure("0") * self.WIDTH_CHARS - 6
        box.configure(height=max(1, min(wrapped_lines(plain, measure_font, inner_px), self.MAX_LINES)))
        box.bind("<Key>", lambda e: "break")
        box.bind("<MouseWheel>", lambda e: box.yview_scroll(-1 * (e.delta // 120 or 1), "units"))
        box.bind("<Button-4>", lambda e: box.yview_scroll(-1, "units"))
        box.bind("<Button-5>", lambda e: box.yview_scroll(1, "units"))
        box.pack(fill="x")
        return box

    @staticmethod
    def _build_details(errors):
        seen, items = set(), []
        for e in errors:
            msg = (e.get("message") or "").strip()
            if not msg or msg in seen:
                continue
            seen.add(msg)
            items.append((_label(e.get("type")), msg, e.get("suggestion") is None))
        return items

    def _toggle_text(self, open_):
        arrow = "\u25be" if open_ else "\u25b8"
        return arrow + "  Why? (" + str(len(self.details_items)) + ")"

    def toggle_details(self, body):
        t = THEME
        if self.details_frame is None:
            f = self.details_frame = tk.Frame(body, bg=t["bg"])
            for kind, msg, advisory in self.details_items[:6]:
                row = tk.Frame(f, bg=t["bg"])
                row.pack(fill="x", pady=1)
                tk.Label(row, text=("Heads-up" if advisory else kind), bg=t["btn"],
                         fg=(t["warn"] if advisory else t["accent_hi"]), font=self.app.font(8, True),
                         padx=6, pady=1).pack(side="left", anchor="n")
                tk.Label(row, text=msg, bg=t["bg"], fg=t["muted"], font=self.app.font(9),
                         wraplength=340, justify="left").pack(side="left", padx=8, anchor="w")
            if len(self.details_items) > 6:
                tk.Label(f, text=f"+ {len(self.details_items) - 6} more", bg=t["bg"], fg=t["muted"],
                         font=self.app.font(8)).pack(anchor="w", pady=(2, 0))
            f.pack(fill="x", pady=(6, 0), after=self.details_toggle)
            self.details_toggle.configure(text=self._toggle_text(True))
            self._make_draggable(f)
        else:
            self.details_frame.destroy()
            self.details_frame = None
            self.details_toggle.configure(text=self._toggle_text(False))
        self.win.update_idletasks()
        self._reclamp()

    # -- placement / drag ---------------------------------------------------
    def _place(self):
        win = self.win
        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        if self.app.pin_pos:
            x, y = self.app.pin_pos
        else:
            cx, cy = self.job["x"], self.job["y"]
            x, y = cx + 14, cy + 18
            _, _, _, bottom = _screen_bounds(win, cx, cy)
            if y + h > bottom - 8:      # not enough room below the cursor -> open above it
                y = cy - h - 14
        x, y = _clamp_position(win, x, y, w, h, keep_visible=False)
        win.geometry(f"+{x}+{y}")

    def _reclamp(self):
        win = self.win
        x, y = _clamp_position(win, win.winfo_x(), win.winfo_y(), win.winfo_reqwidth(),
                               win.winfo_reqheight(), keep_visible=False)
        win.geometry(f"+{x}+{y}")

    def _make_draggable(self, widget):
        """Drag the card by any non-interactive area (header, labels, padding)."""
        if isinstance(widget, (Btn, tk.Text)) or widget is self.details_toggle:
            return
        widget.bind("<ButtonPress-1>", self._drag_start, add="+")
        widget.bind("<B1-Motion>", self._drag_move, add="+")
        widget.bind("<ButtonRelease-1>", self._drag_end, add="+")
        for child in widget.winfo_children():
            self._make_draggable(child)

    def _drag_start(self, e):
        self._drag = (e.x_root - self.win.winfo_x(), e.y_root - self.win.winfo_y())
        self._cancel_timer()

    def _drag_move(self, e):
        if not self._drag:
            return
        win = self.win
        x, y = _clamp_position(win, e.x_root - self._drag[0], e.y_root - self._drag[1],
                               win.winfo_width(), win.winfo_height(), keep_visible=True)
        win.geometry(f"+{x}+{y}")

    def _drag_end(self, e):
        if not self._drag:
            return
        self._drag = None
        if self.pinned:
            self.app.pin_pos = (self.win.winfo_x(), self.win.winfo_y())
        self._arm_timer()

    # -- lifetime ---------------------------------------------------------------
    def _fade_in(self, step=0):
        if self.closed:
            return
        try:
            self.win.attributes("-alpha", min(1.0, 0.25 + step * 0.15))
        except tk.TclError:
            return
        if step < 5:
            self.win.after(14, self._fade_in, step + 1)

    def _arm_timer(self):
        self._cancel_timer()
        if not self.pinned and not self.hover and not self.closed:
            self.timer = self.win.after(AUTO_DISMISS_MS, self.dismiss)

    def _cancel_timer(self):
        if self.timer:
            try:
                self.win.after_cancel(self.timer)
            except tk.TclError:
                pass
            self.timer = None

    def _on_enter(self, e):
        self.hover = True
        self._cancel_timer()

    def _on_leave(self, e):
        # <Leave> also fires when the pointer moves onto a child widget; check the real position
        x, y = self.win.winfo_pointerxy()
        w = self.win
        if w.winfo_rootx() <= x < w.winfo_rootx() + w.winfo_width() and \
                w.winfo_rooty() <= y < w.winfo_rooty() + w.winfo_height():
            return
        self.hover = False
        self._arm_timer()

    def toggle_pin(self):
        self.pinned = not self.pinned
        self.pin_btn.set_text("Pinned" if self.pinned else "Pin")
        self.pin_btn.set_kind("primary" if self.pinned else "ghost")
        if self.pinned:
            self.app.pin_pos = (self.win.winfo_x(), self.win.winfo_y())
            self._cancel_timer()
        else:
            self.app.pin_pos = None
            self._arm_timer()

    def accept(self):
        self.app.submit("accept", self.job)
        self.close()

    def copy(self):
        self.app.submit("copy", self.job)
        self.close()

    def dismiss(self):
        self.close()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self._cancel_timer()
        try:
            self.win.destroy()
        except tk.TclError:
            pass
        self.app.popup_closed(self)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class App:
    def __init__(self, hotkey=HOTKEY, accept_hotkey=ACCEPT_HOTKEY):
        self.hotkey, self.accept_hotkey = hotkey, accept_hotkey
        self.accept_hotkey_label = winapi.pretty_hotkey(accept_hotkey) if accept_hotkey else ""
        self.root = None
        self.ui_q, self.work_q = queue.Queue(), queue.Queue()
        self.engine = None
        self.engine_ready = threading.Event()
        self.popup = None
        self.toast = None
        self.pin_pos = None
        self.busy = threading.Event()
        self._font_family = None
        self.hk = None
        self.main_vk = None

    # -- fonts ------------------------------------------------------------
    def font(self, size, bold=False):
        if self._font_family is None:
            fams = set(tkfont.families(self.root))
            self._font_family = next((f for f in ("Segoe UI Variable Text", "Segoe UI", "SF Pro Text",
                                                  "Helvetica Neue", "DejaVu Sans", "Arial") if f in fams),
                                     "TkDefaultFont")
        return (self._font_family, size, "bold") if bold else (self._font_family, size)

    # -- engine -------------------------------------------------------------
    def _load_engine(self):
        try:
            from engine.corrector import GrammarCorrector
            self.engine = GrammarCorrector()
            if os.path.exists(USER_DICTIONARY):
                with open(USER_DICTIONARY, encoding="utf-8") as fh:
                    words = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
                self.engine.spell.add_words(words)
            print("Engine ready.")
        except Exception as exc:
            print("FAILED TO LOAD THE GRAMMAR ENGINE:", exc)
            print("Run `python build_models.py` once and make sure the NLTK data is downloaded.")
            traceback.print_exc()
        finally:
            self.engine_ready.set()

    # -- thread entry points -------------------------------------------------
    def request_correction(self):
        """Called on the hotkey thread: must return immediately."""
        if self.busy.is_set():
            return
        self.busy.set()
        self.work_q.put(("correct", {"hwnd": winapi.get_foreground_window(),
                                     "pos": winapi.get_cursor_pos()}))

    def request_accept_current(self):
        popup = self.popup
        if popup and not popup.closed:
            self.work_q.put(("accept", popup.job))
            self.ui_q.put(("close_popup",))

    def submit(self, kind, job):
        self.work_q.put((kind, job))

    # -- worker ---------------------------------------------------------------
    def _worker(self):
        while True:
            kind, payload = self.work_q.get()
            try:
                if kind == "correct":
                    self._do_correct(payload)
                elif kind == "accept":
                    ok = paste_replace(payload)
                    if not ok:
                        clip_set(payload["corrected"])
                    self._toast("Replaced with the corrected text" if ok
                                else "Couldn't paste - the correction is on your clipboard",
                                "ok" if ok else "err")
                elif kind == "copy":
                    ok = clip_set(payload["corrected"])
                    self._toast("Copied corrected text" if ok else "Couldn't access the clipboard",
                                "ok" if ok else "err")
            except Exception:
                traceback.print_exc()
                self._toast("Something went wrong - see the console", "err")
            finally:
                if kind == "correct":
                    self.busy.clear()

    def _toast(self, text, kind, pos=None, ms=2600):
        self.ui_q.put(("toast", text, kind, pos, ms))

    def _release_vks(self):
        vks = [winapi.VK_CONTROL, winapi.VK_MENU, winapi.VK_SHIFT, 0x5B, 0x5C]
        if self.main_vk:
            vks.append(self.main_vk)
        return vks

    def _do_correct(self, req):
        pos = req.get("pos")
        if not self.engine_ready.is_set():
            self._toast("Loading the grammar engine - one moment...", "info", pos)
            self.engine_ready.wait(60)
        if self.engine is None:
            self._toast("Grammar engine failed to load - run build_models.py", "err", pos, 6000)
            return

        cap = capture_selection(req.get("hwnd"), self._release_vks())
        messages = {
            "terminal": ("Select text in a regular app - terminals use Ctrl+C to interrupt", "warn"),
            "no_selection": ("No text selected - highlight some text first", "warn"),
            "clipboard_busy": ("The clipboard was busy - please try again", "warn"),
            "too_long": (f"Selection is too long (max {MAX_CHARS:,} characters)", "warn"),
        }
        if cap.error:
            text, kind = messages[cap.error]
            self._toast(text, kind, pos)
            return

        result = self.engine.correct_document(cap.text)
        if not result["changed"]:
            hints = [e["message"] for e in result["errors"] if e.get("suggestion") is None]
            if hints:
                self._toast("No automatic fixes. Heads-up: " + hints[0], "info", pos, 6000)
            else:
                self._toast("No issues found", "ok", pos)
            return

        self.ui_q.put(("popup", {
            "original": cap.text, "corrected": result["corrected"], "errors": result["errors"],
            "backup": cap.backup, "hwnd": req.get("hwnd"),
            "x": (pos or (0, 0))[0], "y": (pos or (0, 0))[1],
        }))

    # -- UI thread -------------------------------------------------------------
    def _pump(self):
        try:
            while True:
                msg = self.ui_q.get_nowait()
                if msg[0] == "toast":
                    self.show_toast(msg[1], msg[2], msg[3] if len(msg) > 3 else None,
                                    msg[4] if len(msg) > 4 else 2600)
                elif msg[0] == "popup":
                    self.show_popup(msg[1])
                elif msg[0] == "close_popup" and self.popup:
                    self.popup.close()
        except queue.Empty:
            pass
        self.root.after(30, self._pump)

    def show_toast(self, text, kind="info", pos=None, ms=2600):
        if self.toast:
            self.toast.close()
        self.toast = Toast(self, text, kind, pos, ms)

    def show_popup(self, job):
        if self.toast:
            self.toast.close()
            self.toast = None
        if self.popup:
            self.popup.close()
        self.popup = SuggestionPopup(self, job)
        if self.hk:
            self.hk.set_accept_hotkey(True)

    def popup_closed(self, popup):
        if self.popup is popup:
            self.popup = None
            if self.hk:
                self.hk.set_accept_hotkey(False)

    # -- lifecycle ----------------------------------------------------------------
    def run(self, demo=False):
        winapi.set_dpi_aware()
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.after(30, self._pump)

        if demo:
            self.root.after(200, lambda: self.show_popup(DEMO_JOB(self.root)))
            self.root.mainloop()
            return 0

        if not winapi.IS_WINDOWS:
            print("The global hotkey is implemented for Windows only. Use --demo to preview the UI.")
            return 1
        if pyperclip is None:
            print("pyperclip is missing: pip install pyperclip")
            return 1
        if not winapi.acquire_single_instance():
            print("Grammar Corrector is already running.")
            return 0

        threading.Thread(target=self._load_engine, daemon=True, name="engine").start()
        threading.Thread(target=self._worker, daemon=True, name="worker").start()

        self.hk = winapi.HotkeyThread(self.hotkey, self.request_correction,
                                      self.accept_hotkey, self.request_accept_current)
        self.main_vk = self.hk.main_vk
        self.hk.start()
        self.hk.ready.wait(3)
        if self.hk.error:
            print("=" * 70)
            print(f"Could not register {winapi.pretty_hotkey(self.hotkey)}: {self.hk.error}")
            print("Another program already uses this shortcut. Pick another with --hotkey")
            print("(for example --hotkey ctrl+alt+g).")
            print("=" * 70)
            return 1

        print(f"Grammar Corrector is running. Select text anywhere and press "
              f"{winapi.pretty_hotkey(self.hotkey)}.  Quit with Ctrl+C in this window.")
        self.show_toast(f"Grammar Corrector ready - select text and press "
                        f"{winapi.pretty_hotkey(self.hotkey)}", "ok",
                        (self.root.winfo_screenwidth() - 420, self.root.winfo_screenheight() - 130), 4000)
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.hk.stop()
        return 0


def DEMO_JOB(root):
    return {
        "original": "She dont like apples and he go to school everyday.",
        "corrected": "She doesn't like apples and he goes to school everyday.",
        "errors": [
            {"type": "spelling", "message": '"dont" is missing an apostrophe - should be "don\'t".',
             "suggestion": "don't"},
            {"type": "subject_verb_agreement", "message": '"he go" - subject-verb agreement error.',
             "suggestion": "goes"},
            {"type": "comma_splice", "message": "Possible comma splice.", "suggestion": None},
        ],
        "backup": None, "hwnd": 0,
        "x": root.winfo_screenwidth() // 3, "y": root.winfo_screenheight() // 3,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Grammar Corrector desktop app")
    ap.add_argument("--hotkey", default=HOTKEY)
    ap.add_argument("--accept-hotkey", default=ACCEPT_HOTKEY)
    ap.add_argument("--demo", action="store_true", help="show a sample suggestion card")
    args = ap.parse_args(argv)
    try:
        winapi.parse_hotkey(args.hotkey)
        if args.accept_hotkey:
            winapi.parse_hotkey(args.accept_hotkey)
    except ValueError as exc:
        ap.error(str(exc))
    return App(args.hotkey, args.accept_hotkey).run(demo=args.demo)


if __name__ == "__main__":
    sys.exit(main())
