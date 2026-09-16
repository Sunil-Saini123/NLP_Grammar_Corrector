

"""
Layer 2 — OS Integration.

Runs in the background. When you select text in ANY application (Word,
Gmail in browser, Notepad, Google Docs, etc.) and press the hotkey,
this script:
  1. Simulates Ctrl+C to copy the current selection
  2. Reads the clipboard
  3. Sends the text to the Layer-1 GrammarCorrector engine
  4. Shows a small popup at your cursor with the suggested correction
     (inspired by Ayush's "LookUp" app) — you choose Accept or Dismiss
  5. On Accept, pastes the corrected text back, replacing the selection

This file NEVER contains grammar logic itself — it only calls
`engine.corrector.GrammarCorrector.correct()`. That separation means Layer 1
can be re-tuned/retested without touching this file at all, and vice versa.

--------------------------------------------------------------------------
SETUP (run on your own laptop, not in a sandbox):
    pip install keyboard pyperclip nltk symspellpy pynput
    python build_models.py      # one-time: builds the LM + spellcheck data
                                 # (skip this and the app will silently look
                                 #  "dead" — see PLATFORM NOTES below)

RUN (Windows: an elevated/admin terminal is recommended — see below):
    python desktop_app/hotkey_listener.py

DEFAULT HOTKEY: Ctrl+Alt+H

WHY THE PREVIOUS VERSION TYPED "ḥ" INTO YOUR DOCUMENT (fixed here):
  On many Windows keyboard layouts — including most Indic/Sanskrit/Arabic
  transliteration layouts — Ctrl+Alt is treated as AltGr, and AltGr+H is
  bound to a special character ("ḥ", h with a dot below). The previous
  version used `pynput.keyboard.Listener`, which can only WATCH keystrokes,
  not block them. So the instant you pressed Ctrl+Alt+H, Windows' own input
  layer converted it into "ḥ" and typed it into whatever field had focus —
  in parallel with, and before, our script could do anything about it.

  This version uses the `keyboard` library instead, which can register a
  hotkey with `suppress=True`. That tells Windows "swallow this exact key
  combo, don't deliver it to the focused app at all" — so Ctrl+Alt+H no
  longer leaks a character anywhere, on any layout.

  It also explicitly releases Ctrl/Alt (via synthetic key-up events)
  before simulating Ctrl+C, because sending copy while your physical Alt
  key is still held down would itself send Ctrl+Alt+C to the app — the
  same class of bug, one step later in the pipeline.

OTHER FIXES FROM THE ORIGINAL:
  - Case sensitivity: matching used to break if Shift/Caps Lock was on.
    The `keyboard` library normalizes this for you.
  - Silent crash on startup: main() used to load the grammar engine
    *before* starting the listener, so a missing data/*.pkl or missing
    NLTK data would crash the whole process with no listener ever
    running. This version prints a clear diagnostic instead and keeps
    the hotkey registered so you get feedback instead of dead silence.
  - Holding the keys down used to fire the correction repeatedly on OS
    key-repeat. This version debounces so one press = one action.

PLATFORM NOTES:
  - Windows: `keyboard`'s suppress=True generally needs the terminal to
    be running as Administrator to reliably hook and swallow global keys
    system-wide. Right-click your terminal/PowerShell -> "Run as
    administrator" before running this script. Without admin, the hotkey
    may still work but suppression (blocking the leaked character) may
    silently fail on some setups.
  - Some antivirus/Windows Defender configs flag global keyboard hooks
    (which is what makes any hotkey listener work) as keylogger-like
    behavior. If the script exits immediately or the hotkey never
    registers, check Defender/AV logs and allow the Python process.
  - The `keyboard` library is Windows/Linux only (no macOS support);
    that's fine here since you're targeting Windows.
--------------------------------------------------------------------------
"""
import sys
import os
import time
import queue
import threading
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pyperclip
import keyboard
from pynput import mouse

from engine.corrector import GrammarCorrector

# ---------------------------------------------------------------------------
# Hotkey configuration
# ---------------------------------------------------------------------------
HOTKEY = "ctrl+alt+h"

CLIPBOARD_WAIT = 0.15   # seconds to let the OS clipboard settle after a simulated copy/paste
MODIFIER_RELEASE_WAIT = 0.05  # seconds to let the OS register the forced modifier release
DEBOUNCE_SECONDS = 0.5  # ignore repeat triggers within this window

mouse_controller = mouse.Controller()

last_trigger_time = 0.0
trigger_lock = threading.Lock()

corrector = None              # lazy-loaded so the listener starts instantly
corrector_load_error = None

ui_queue = queue.Queue()      # jobs handed from the hotkey thread to the Tk main thread


# ---------------------------------------------------------------------------
# Engine loading
# ---------------------------------------------------------------------------
def _load_engine():
    """Load the grammar engine, capturing any failure instead of crashing
    the whole process (which is what silently killed the old hotkey)."""
    global corrector, corrector_load_error
    if corrector is not None or corrector_load_error is not None:
        return corrector
    try:
        print("Loading grammar engine (first use only)...")
        corrector = GrammarCorrector()
        print("Engine ready.")
    except Exception as e:
        corrector_load_error = e
        print("=" * 70)
        print("FAILED TO LOAD THE GRAMMAR ENGINE.")
        print("This is almost certainly why nothing seemed to happen when")
        print("you pressed the hotkey — the app never finished starting.")
        print(f"Error: {e}")
        print("Most common fix: run `python build_models.py` once from the")
        print("project root to generate data/ngram_model.pkl and")
        print("data/spell_freq.pkl, and make sure NLTK data is downloaded.")
        print("=" * 70)
        traceback.print_exc()
    return corrector


# ---------------------------------------------------------------------------
# Clipboard-based selection capture / replace
# ---------------------------------------------------------------------------
def _release_hotkey_modifiers():
    """Force Ctrl and Alt to a 'released' state at the OS level before we
    inject our own Ctrl+C/Ctrl+V. If we don't do this, your physically-held
    Alt (from Ctrl+Alt+H) combines with our synthetic Ctrl+C into
    Ctrl+Alt+C, which is itself a layout-dependent shortcut / character on
    many keyboards — the exact same bug class that produced "ḥ"."""
    keyboard.release("ctrl")
    keyboard.release("alt")
    time.sleep(MODIFIER_RELEASE_WAIT)


def _simulate_copy():
    _release_hotkey_modifiers()
    keyboard.send("ctrl+c")
    time.sleep(CLIPBOARD_WAIT)


def _simulate_paste():
    _release_hotkey_modifiers()
    keyboard.send("ctrl+v")
    time.sleep(CLIPBOARD_WAIT)


def paste_text(corrected, previous_clipboard):
    """Runs on accept: pastes the corrected text, then restores whatever
    was on the clipboard before we touched it."""
    pyperclip.copy(corrected)
    _simulate_paste()
    time.sleep(CLIPBOARD_WAIT)
    pyperclip.copy(previous_clipboard)


def handle_hotkey():
    """Fired by the `keyboard` library when Ctrl+Alt+H is pressed (and
    suppressed, so it never reaches the focused app). Does the clipboard/
    engine work, then hands the result to the Tk main thread to show the
    popup — Tk must only ever be touched from the main thread."""
    global last_trigger_time

    with trigger_lock:
        now = time.time()
        if now - last_trigger_time < DEBOUNCE_SECONDS:
            return
        last_trigger_time = now

    engine = _load_engine()
    if engine is None:
        return  # error already printed by _load_engine

    previous_clipboard = pyperclip.paste()
    _simulate_copy()
    selected_text = pyperclip.paste()

    if not selected_text or not selected_text.strip():
        print("No text selected — nothing to correct.")
        return
    if selected_text == previous_clipboard:
        print("Nothing new was copied — make sure text is selected before pressing the hotkey.")
        return

    print(f"Selected: {selected_text!r}")
    try:
        result = engine.correct(selected_text)
    except Exception as e:
        print(f"Error during correction: {e}")
        traceback.print_exc()
        return
    corrected = result["corrected"]
    print(f"Corrected: {corrected!r}")

    if corrected.strip() == selected_text.strip():
        print("No changes needed.")
        return

    cursor_x, cursor_y = mouse_controller.position
    ui_queue.put({
        "original": selected_text,
        "corrected": corrected,
        "previous_clipboard": previous_clipboard,
        "x": cursor_x,
        "y": cursor_y,
    })


# ---------------------------------------------------------------------------
# Popup UI (LookUp-style: small, borderless, appears at the cursor)
# ---------------------------------------------------------------------------
def show_popup(root, job):
    import tkinter as tk

    popup = tk.Toplevel(root)
    popup.overrideredirect(True)   # no title bar, like LookUp's popup
    popup.attributes("-topmost", True)
    popup.configure(bg="#1e1e1e", padx=1, pady=1)

    # Position near the cursor, nudged so it doesn't sit under the pointer.
    x, y = job["x"] + 16, job["y"] + 16
    popup.geometry(f"+{x}+{y}")

    frame = tk.Frame(popup, bg="#252526", padx=12, pady=10)
    frame.pack()

    tk.Label(
        frame, text="Grammar suggestion", fg="#9cdcfe", bg="#252526",
        font=("Segoe UI", 9, "bold"), anchor="w",
    ).pack(fill="x")

    tk.Label(
        frame, text=job["original"], fg="#d4a5a5", bg="#252526",
        font=("Segoe UI", 10), wraplength=340, justify="left", anchor="w",
    ).pack(fill="x", pady=(6, 2))

    tk.Label(
        frame, text=job["corrected"], fg="#b5e8b5", bg="#252526",
        font=("Segoe UI", 10, "bold"), wraplength=340, justify="left", anchor="w",
    ).pack(fill="x", pady=(0, 8))

    btn_row = tk.Frame(frame, bg="#252526")
    btn_row.pack(fill="x")

    def accept():
        popup.destroy()
        threading.Thread(
            target=paste_text,
            args=(job["corrected"], job["previous_clipboard"]),
            daemon=True,
        ).start()

    def dismiss():
        popup.destroy()

    tk.Button(
        btn_row, text="Accept (paste)", command=accept,
        bg="#0e639c", fg="white", relief="flat", padx=8, pady=3,
    ).pack(side="left")
    tk.Button(
        btn_row, text="Dismiss", command=dismiss,
        bg="#3c3c3c", fg="white", relief="flat", padx=8, pady=3,
    ).pack(side="left", padx=(6, 0))

    popup.bind("<Escape>", lambda e: dismiss())
    popup.focus_force()

    # Auto-dismiss so stray popups don't pile up if you get distracted.
    popup.after(15000, lambda: popup.winfo_exists() and popup.destroy())


def ui_loop(root):
    try:
        while True:
            job = ui_queue.get_nowait()
            show_popup(root, job)
    except queue.Empty:
        pass
    root.after(50, ui_loop, root)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Grammar Corrector is running in the background.")
    print("Select text anywhere and press Ctrl+Alt+H to detect & correct it.")
    print("Press Ctrl+C in this terminal to quit.")

    _load_engine()  # pre-load so the first real use isn't slow (errors are printed, not fatal)

    try:
        # suppress=True: swallow the combo at the OS level so it never
        # leaks a character (e.g. "ḥ") into whatever app has focus.
        keyboard.add_hotkey(HOTKEY, handle_hotkey, suppress=True, trigger_on_release=False)
    except Exception as e:
        print("=" * 70)
        print(f"Could not register the global hotkey ({e}).")
        print("On Windows, `suppress=True` usually needs the terminal to be")
        print("running as Administrator. Right-click PowerShell/cmd ->")
        print("'Run as administrator', then run this script again.")
        print("=" * 70)
        return

    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # no visible main window — only the popups it spawns
    root.after(50, ui_loop, root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()