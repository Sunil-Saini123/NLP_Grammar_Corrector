"""
Thin Win32 layer for the Grammar Corrector desktop app (pure ctypes, no
third-party dependencies).

Why this exists
---------------
The previous version used the `keyboard` library (a low-level keyboard HOOK)
plus `pynput`. A hook has two nasty failure modes that match the symptom
"sometimes it corrects, sometimes nothing happens":

  * Windows silently REMOVES a low-level hook whose callback is slow
    (LowLevelHooksTimeout, ~300 ms). The old callback slept, polled the
    clipboard and loaded the NLP engine *inside* the hook thread, so after
    one slow press the hotkey could stop working until restart.
  * It usually needs an elevated (Administrator) terminal to be reliable.

This module instead uses `RegisterHotKey`, the OS-supported way to own a
global shortcut: the OS delivers a WM_HOTKEY message to a normal message
loop, nothing can time out, no admin rights are needed, and the key combo is
swallowed by the OS (so Ctrl+Alt+H can never type "ḥ" on AltGr layouts).

Everything here degrades to harmless no-ops on non-Windows systems so the UI
can still be developed/tested on Linux/macOS.
"""
import ctypes
import os
import sys
import threading
import time
from ctypes import wintypes

IS_WINDOWS = sys.platform == "win32"

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x0001, 0x0002, 0x0004, 0x0008, 0x4000

VK_SHIFT, VK_CONTROL, VK_MENU = 0x10, 0x11, 0x12
VK_LBUTTON, VK_RBUTTON = 0x01, 0x02
VK_ESCAPE, VK_RETURN, VK_INSERT = 0x1B, 0x0D, 0x2D
VK_C, VK_V = 0x43, 0x56

WM_QUIT, WM_HOTKEY, WM_APP = 0x0012, 0x0312, 0x8000
_MSG_REG_ACCEPT = WM_APP + 1
_MSG_UNREG_ACCEPT = WM_APP + 2

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP = 0x0001, 0x0002

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE = 0x00000080, 0x08000000
GCL_STYLE, CS_DROPSHADOW = -26, 0x00020000

# Windows that must never receive a synthetic Ctrl+C (it would send SIGINT).
TERMINAL_PROCESSES = {
    "cmd.exe", "powershell.exe", "pwsh.exe", "conhost.exe", "windowsterminal.exe",
    "wt.exe", "mintty.exe", "bash.exe", "wsl.exe", "alacritty.exe", "wezterm-gui.exe",
}

_NAMED_KEYS = {
    "enter": VK_RETURN, "return": VK_RETURN, "space": 0x20, "tab": 0x09, "esc": VK_ESCAPE,
    "escape": VK_ESCAPE, "insert": VK_INSERT, "delete": 0x2E, "home": 0x24, "end": 0x23,
    "pageup": 0x21, "pagedown": 0x22, "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
}
_MOD_NAMES = {"ctrl": MOD_CONTROL, "control": MOD_CONTROL, "alt": MOD_ALT,
              "shift": MOD_SHIFT, "win": MOD_WIN, "windows": MOD_WIN}


# --------------------------------------------------------------------------
# Structures (sizes matter: sizeof(INPUT) must be 40 on 64-bit Windows)
# --------------------------------------------------------------------------
ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_int32), ("dy", ctypes.c_int32), ("mouseData", ctypes.c_uint32),
                ("dwFlags", ctypes.c_uint32), ("time", ctypes.c_uint32), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_uint16), ("wScan", ctypes.c_uint16), ("dwFlags", ctypes.c_uint32),
                ("time", ctypes.c_uint32), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_uint32), ("wParamL", ctypes.c_uint16), ("wParamH", ctypes.c_uint16)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_uint32), ("u", _INPUTUNION)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint32), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", ctypes.c_uint32)]


# --------------------------------------------------------------------------
# DLL handles + prototypes (argtypes are REQUIRED on 64-bit so handles aren't truncated)
# --------------------------------------------------------------------------
if IS_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
    user32.RegisterHotKey.restype = wintypes.BOOL
    user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.UnregisterHotKey.restype = wintypes.BOOL
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.GetMessageW.restype = ctypes.c_int
    user32.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT,
                                    wintypes.UINT, wintypes.UINT]
    user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostThreadMessageW.restype = wintypes.BOOL
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short
    user32.GetClipboardSequenceNumber.restype = wintypes.DWORD
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    user32.GetParent.argtypes = [wintypes.HWND]
    user32.GetParent.restype = wintypes.HWND
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = ctypes.c_long
    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
    user32.SetWindowLongW.restype = ctypes.c_long
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
    user32.MonitorFromPoint.restype = wintypes.HANDLE
    user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFO)]
    user32.GetMonitorInfoW.restype = wintypes.BOOL
    try:  # 64-bit only name; 32-bit Windows exposes the non-Ptr variants
        _get_class_long = user32.GetClassLongPtrW
        _set_class_long = user32.SetClassLongPtrW
    except AttributeError:  # pragma: no cover
        _get_class_long = user32.GetClassLongW
        _set_class_long = user32.SetClassLongW
    _get_class_long.argtypes = [wintypes.HWND, ctypes.c_int]
    _get_class_long.restype = ctypes.c_size_t
    _set_class_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_size_t]
    _set_class_long.restype = ctypes.c_size_t

    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                    wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE


# --------------------------------------------------------------------------
# Process / environment helpers
# --------------------------------------------------------------------------
def set_dpi_aware():
    """Must run BEFORE Tk creates its first window: makes the popup crisp on
    125%/150% laptop screens and makes GetCursorPos coordinates match Tk's."""
    if not IS_WINDOWS:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)   # system DPI aware
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass


def acquire_single_instance(name="Local\\GrammarCorrectorHotkey"):
    """True if we are the only running copy."""
    if not IS_WINDOWS:
        return True
    handle = kernel32.CreateMutexW(None, False, name)
    already = ctypes.get_last_error() == 183  # ERROR_ALREADY_EXISTS
    acquire_single_instance._handle = handle   # keep alive for process lifetime
    return not already


# --------------------------------------------------------------------------
# Hotkey string parsing
# --------------------------------------------------------------------------
def parse_hotkey(text):
    """'ctrl+alt+h' -> (MOD_CONTROL | MOD_ALT, 0x48). Raises ValueError."""
    mods, key = 0, None
    for part in [p.strip().lower() for p in text.split("+") if p.strip()]:
        if part in _MOD_NAMES:
            mods |= _MOD_NAMES[part]
        elif key is not None:
            raise ValueError(f"more than one non-modifier key in {text!r}")
        elif len(part) == 1 and part.isalnum():
            key = ord(part.upper())
        elif part in _NAMED_KEYS:
            key = _NAMED_KEYS[part]
        elif part.startswith("f") and part[1:].isdigit() and 1 <= int(part[1:]) <= 24:
            key = 0x70 + int(part[1:]) - 1
        else:
            raise ValueError(f"unknown key {part!r} in {text!r}")
    if key is None:
        raise ValueError(f"no key in {text!r}")
    if not mods:
        raise ValueError(f"{text!r} needs at least one modifier (ctrl/alt/shift/win)")
    return mods, key


def pretty_hotkey(text):
    names = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift", "win": "Win", "enter": "Enter",
             "esc": "Esc", "space": "Space"}
    return "+".join(names.get(p.strip().lower(), p.strip().upper() if len(p.strip()) == 1
                              else p.strip().capitalize()) for p in text.split("+"))


# --------------------------------------------------------------------------
# Keyboard injection / state
# --------------------------------------------------------------------------
def _key_input(vk, up=False):
    flags = KEYEVENTF_KEYUP if up else 0
    if vk in (VK_INSERT, 0x2E, 0x24, 0x23, 0x21, 0x22, 0x25, 0x26, 0x27, 0x28):
        flags |= KEYEVENTF_EXTENDEDKEY
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)
    return inp


def send_combo(modifiers, key):
    """Press modifiers+key and release them, atomically in ONE SendInput call
    so nothing the user types can interleave with it."""
    if not IS_WINDOWS:
        return False
    seq = [_key_input(m) for m in modifiers] + [_key_input(key), _key_input(key, up=True)] \
        + [_key_input(m, up=True) for m in reversed(modifiers)]
    arr = (INPUT * len(seq))(*seq)
    sent = user32.SendInput(len(seq), arr, ctypes.sizeof(INPUT))
    return sent == len(seq)


def release_keys(*vks):
    """Synthetic key-up for keys that might still be held (belt and braces)."""
    if not IS_WINDOWS:
        return
    seq = [_key_input(v, up=True) for v in vks]
    arr = (INPUT * len(seq))(*seq)
    user32.SendInput(len(seq), arr, ctypes.sizeof(INPUT))


def key_down(vk):
    if not IS_WINDOWS:
        return False
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def wait_keys_released(vks, timeout=1.5, poll=0.01):
    """Block until none of `vks` are physically down (or timeout). Sending
    Ctrl+C while the user's Alt is still held would deliver Ctrl+Alt+C."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not any(key_down(v) for v in vks):
            return True
        time.sleep(poll)
    return False


def send_copy(method="ctrl+c"):
    if method == "ctrl+insert":
        return send_combo([VK_CONTROL], VK_INSERT)
    return send_combo([VK_CONTROL], VK_C)


def send_paste():
    return send_combo([VK_CONTROL], VK_V)


# --------------------------------------------------------------------------
# Clipboard sequence number (changes on EVERY clipboard write, even same text)
# --------------------------------------------------------------------------
def clipboard_sequence():
    if not IS_WINDOWS:
        return None
    return int(user32.GetClipboardSequenceNumber())


# --------------------------------------------------------------------------
# Windows / monitors / process
# --------------------------------------------------------------------------
def get_cursor_pos():
    if IS_WINDOWS:
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
    return None


def get_foreground_window():
    return int(user32.GetForegroundWindow() or 0) if IS_WINDOWS else 0


def set_foreground_window(hwnd):
    if IS_WINDOWS and hwnd:
        try:
            return bool(user32.SetForegroundWindow(hwnd))
        except Exception:
            return False
    return False


def process_name_of_window(hwnd):
    """Lower-case exe name owning `hwnd`, or '' if unknown."""
    if not (IS_WINDOWS and hwnd):
        return ""
    try:
        pid = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buf))
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                return os.path.basename(buf.value).lower()
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        pass
    return ""


def work_area_at(x, y):
    """(left, top, right, bottom) of the monitor work area containing the point."""
    if IS_WINDOWS:
        try:
            mon = user32.MonitorFromPoint(wintypes.POINT(int(x), int(y)), 2)  # NEAREST
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            if user32.GetMonitorInfoW(mon, ctypes.byref(info)):
                r = info.rcWork
                return r.left, r.top, r.right, r.bottom
        except Exception:
            pass
    return None


def style_popup_window(tk_window, rounded=True):
    """Make a borderless Tk window behave like a tool-tip: it never steals
    focus (so the app you were typing in stays active and Ctrl+V lands there),
    stays out of the taskbar/Alt-Tab, and gets a soft shadow / rounded
    corners where Windows supports it. Call while the window is withdrawn or
    right after it is first shown."""
    if not IS_WINDOWS:
        return
    try:
        tk_window.update_idletasks()
        hwnd = user32.GetParent(tk_window.winfo_id()) or tk_window.winfo_id()
        ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
        try:
            cls = _get_class_long(hwnd, GCL_STYLE)
            _set_class_long(hwnd, GCL_STYLE, cls | CS_DROPSHADOW)
        except Exception:
            pass
        if rounded:
            try:  # Windows 11: DWMWA_WINDOW_CORNER_PREFERENCE = DWMWCP_ROUND
                pref = ctypes.c_int(2)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    wintypes.HWND(hwnd), 33, ctypes.byref(pref), ctypes.sizeof(pref))
            except Exception:
                pass
    except Exception:
        pass


# --------------------------------------------------------------------------
# Global hotkey thread
# --------------------------------------------------------------------------
class HotkeyThread(threading.Thread):
    """Owns a message loop and the global hotkeys.

    on_trigger() is called on THIS thread, so it must only enqueue work and
    return immediately (never sleep, never touch the clipboard).
    """

    ID_MAIN, ID_ACCEPT = 1, 2

    def __init__(self, hotkey, on_trigger, accept_hotkey=None, on_accept=None):
        super().__init__(name="hotkey-loop", daemon=True)
        self.main_mods, self.main_vk = parse_hotkey(hotkey)
        self.accept = parse_hotkey(accept_hotkey) if accept_hotkey else None
        self.on_trigger = on_trigger
        self.on_accept = on_accept
        self.ready = threading.Event()
        self.error = None
        self._tid = None

    def run(self):
        if not IS_WINDOWS:
            self.error = "global hotkeys are only implemented for Windows"
            self.ready.set()
            return
        msg = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, WM_APP, WM_APP, 0)  # create the thread's queue
        self._tid = kernel32.GetCurrentThreadId()
        if not user32.RegisterHotKey(None, self.ID_MAIN, self.main_mods | MOD_NOREPEAT, self.main_vk):
            self.error = ctypes.WinError(ctypes.get_last_error())
            self.ready.set()
            return
        self.ready.set()
        while True:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret in (0, -1):
                break
            if msg.message == WM_HOTKEY:
                if msg.wParam == self.ID_MAIN:
                    self._safe(self.on_trigger)
                elif msg.wParam == self.ID_ACCEPT and self.on_accept:
                    self._safe(self.on_accept)
            elif msg.message == _MSG_REG_ACCEPT and self.accept:
                user32.RegisterHotKey(None, self.ID_ACCEPT, self.accept[0] | MOD_NOREPEAT, self.accept[1])
            elif msg.message == _MSG_UNREG_ACCEPT:
                user32.UnregisterHotKey(None, self.ID_ACCEPT)
        user32.UnregisterHotKey(None, self.ID_MAIN)
        user32.UnregisterHotKey(None, self.ID_ACCEPT)

    @staticmethod
    def _safe(fn):
        try:
            fn()
        except Exception:  # never let a callback kill the message loop
            import traceback
            traceback.print_exc()

    def set_accept_hotkey(self, enabled):
        """Register/unregister the 'accept suggestion' shortcut (only while a
        popup is visible, so it never steals a combo the rest of the time)."""
        if IS_WINDOWS and self._tid and self.accept:
            user32.PostThreadMessageW(self._tid, _MSG_REG_ACCEPT if enabled else _MSG_UNREG_ACCEPT, 0, 0)

    def stop(self):
        if IS_WINDOWS and self._tid:
            user32.PostThreadMessageW(self._tid, WM_QUIT, 0, 0)
