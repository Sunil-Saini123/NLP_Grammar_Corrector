"""
Logic tests for the desktop app that run on ANY OS (Win32 calls are mocked).

    python -m tests.test_desktop_logic
"""
import os
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from desktop_app import hotkey_listener as hl
from desktop_app import winapi


class FakeSystem:
    """A scriptable stand-in for the clipboard + keyboard."""
    def __init__(self, selection="", clipboard="old clipboard", copy_delay=0.0,
                 ignore_first_copy=False, exe="notepad.exe"):
        self.selection, self.clipboard, self.copy_delay = selection, clipboard, copy_delay
        self.ignore_first_copy, self.exe = ignore_first_copy, exe
        self.seq, self.copies, self.pastes, self.methods = 1, 0, [], []

    def install(self):
        winapi.process_name_of_window = lambda h: self.exe
        winapi.wait_keys_released = lambda *a, **k: True
        winapi.clipboard_sequence = lambda: self.seq
        winapi.send_copy = self._send_copy
        winapi.send_paste = lambda: self.pastes.append(self.clipboard)
        winapi.get_foreground_window = lambda: 42
        hl.clip_get = lambda: self.clipboard
        hl.clip_set = self._clip_set
        hl.COPY_TIMEOUTS = (0.3, 0.3)

    def _clip_set(self, text):
        self.clipboard = text
        self.seq += 1
        return True

    def _send_copy(self, method="ctrl+c"):
        self.methods.append(method)
        self.copies += 1
        if self.ignore_first_copy and self.copies == 1:
            return True
        if not self.selection:
            return True            # nothing selected: apps leave the clipboard alone

        def later():
            time.sleep(self.copy_delay)
            self.clipboard = self.selection
            self.seq += 1
        threading.Thread(target=later, daemon=True).start()
        return True


def check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    return cond


def run():
    ok = True

    # 1. normal copy
    s = FakeSystem(selection="He go home."); s.install()
    c = hl.capture_selection(1, [])
    ok &= check("normal copy returns the selection", c.text == "He go home." and c.error is None)
    ok &= check("user's clipboard is restored afterwards", s.clipboard == "old clipboard")

    # 2. THE BUG: selection identical to what is already on the clipboard
    s = FakeSystem(selection="same text", clipboard="same text"); s.install()
    c = hl.capture_selection(1, [])
    ok &= check("selection equal to clipboard still works (old code said 'nothing copied')",
                c.text == "same text")

    # 3. slow application (copy lands 0.5s later, old code waited 0.15s)
    s = FakeSystem(selection="slow app text", copy_delay=0.5); s.install()
    hl.COPY_TIMEOUTS = (0.9, 0.5)
    c = hl.capture_selection(1, [])
    ok &= check("slow app (0.5s copy) is captured", c.text == "slow app text")

    # 4. app ignores the first Ctrl+C
    s = FakeSystem(selection="retry text", ignore_first_copy=True); s.install()
    c = hl.capture_selection(1, [])
    ok &= check("retry with Ctrl+Insert after an ignored copy",
                c.text == "retry text" and s.methods == ["ctrl+c", "ctrl+insert"])

    # 5. nothing selected
    s = FakeSystem(selection=""); s.install()
    c = hl.capture_selection(1, [])
    ok &= check("no selection -> explicit 'no_selection' result", c.error == "no_selection")
    ok &= check("clipboard untouched when nothing was selected", s.clipboard == "old clipboard")

    # 6. terminal window: never inject Ctrl+C (would send SIGINT)
    s = FakeSystem(selection="x", exe="windowsterminal.exe"); s.install()
    c = hl.capture_selection(1, [])
    ok &= check("terminal windows are refused and no Ctrl+C is sent", c.error == "terminal" and s.copies == 0)

    # 7. too long
    s = FakeSystem(selection="a" * (hl.MAX_CHARS + 1)); s.install()
    ok &= check("oversized selection is rejected", hl.capture_selection(1, []).error == "too_long")

    # 8. accept -> paste + clipboard restore
    s = FakeSystem(clipboard="mine"); s.install()
    job = {"corrected": "He goes home.", "backup": "mine", "hwnd": 42}
    good = hl.paste_replace(job)
    ok &= check("accept pastes the corrected text", good and s.pastes == ["He goes home."])
    ok &= check("accept restores the previous clipboard", s.clipboard == "mine")

    # 9. hotkey parsing / diff
    ok &= check("parse ctrl+alt+h", winapi.parse_hotkey("ctrl+alt+h") == (winapi.MOD_CONTROL | winapi.MOD_ALT, 0x48))
    b, a, n = hl.diff_segments("She dont like it", "She doesn't like it")
    ok &= check("diff finds exactly 1 change", n == 1 and ("dont", "del") in b and ("doesn't", "ins") in a)
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
