# -*- coding: utf-8 -*-
"""
KAT - haelt die Windows-Sitzung "aktiv", ohne dass etwas kaputt geht.

Verhalten:
  * Solange du den PC benutzt (echte Maus-/Tastatureingabe), tut KAT NICHTS.
  * Erst nach einer einstellbaren Leerlaufzeit (IDLE_THRESHOLD) ohne echte Eingabe
    wird KAT aktiv und bewegt die Maus alle ~30 Sekunden ein paar Pixel (und zuckt
    sie sofort zurueck), tippt gelegentlich die unschaedliche F15-Taste, scrollt minimal.
  * Sobald wieder echte Eingabe kommt, pausiert KAT automatisch und wartet erneut
    die Leerlaufzeit ab.

Kein Fenster. Steuerung nur ueber das Tray-Icon (ggf. unter "ausgeblendete Symbole"):
Rechtsklick -> Pausieren / Fortsetzen / Beenden.

KEIN Logging, keine automatischen Meldungen: KAT haelt nirgends fest, wann es lief.
Nur Python-Standardbibliothek (ctypes) -> keine zusaetzlichen Pakete noetig.
"""

import ctypes
import ctypes.wintypes as wt
import os
import random
import threading
import time

# ----------------------------- Konfiguration ------------------------------
IDLE_THRESHOLD = 120       # Sek. ohne echte Eingabe, bevor KAT aktiv wird (2 Min)
ACTION_MIN     = 25        # min. Sekunden zwischen zwei Aktionen
ACTION_MAX     = 35        # max. Sekunden zwischen zwei Aktionen
JIGGLE_PIXELS  = 3         # wie weit die Maus zuckt (Pixel)
KEY_CHANCE     = 0.30      # Wahrscheinlichkeit pro Aktion fuer F15-Tastendruck
SCROLL_CHANCE  = 0.15      # Wahrscheinlichkeit pro Aktion fuer Mini-Scroll
ENABLE_CLICK   = False     # ECHTE Linksklicks. ACHTUNG: kann anklicken was gerade
                           # unter dem Cursor liegt -> Default AUS. Auf True setzen
                           # falls gewuenscht.
CLICK_CHANCE   = 0.10      # nur wirksam wenn ENABLE_CLICK = True
TRAY_TOOLTIP   = "KAT"     # Hover-Text am Tray-Icon (beliebig aenderbar)
NOTIFY_ON_ACTIVE = False   # KEINE Sprechblase beim automatischen Aktivwerden (Abwesenheit)
NOTIFY_ON_START  = False   # kein Start-/Klick-Hinweisfenster (lautlos). Nur zum Testen auf True.
MAGIC          = 0x4B415431  # Signatur der eigenen Eingaben ("KAT1")
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH  = os.path.join(SCRIPT_DIR, "kat.ico")

# Bewusst KEIN Logging: KAT schreibt nirgends mit, wann es lief oder aktiv war.

user32   = ctypes.WinDLL("user32",   use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
shell32  = ctypes.WinDLL("shell32",  use_last_error=True)

ULONG_PTR = ctypes.c_size_t
LRESULT   = ctypes.c_ssize_t
HHOOK     = ctypes.c_void_p

# ----------------------------- SendInput-Typen -----------------------------
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wt.DWORD), ("wParamL", wt.WORD), ("wParamH", wt.WORD)]

class _INPUTunion(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("u", _INPUTunion)]

user32.SendInput.argtypes = [wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype  = wt.UINT

INPUT_MOUSE          = 0
INPUT_KEYBOARD       = 1
MOUSEEVENTF_MOVE     = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
MOUSEEVENTF_WHEEL    = 0x0800
KEYEVENTF_KEYUP      = 0x0002
VK_F15               = 0x7E


def _send(*inputs):
    n = len(inputs)
    arr = (INPUT * n)(*inputs)
    user32.SendInput(n, arr, ctypes.sizeof(INPUT))


def _mouse(dx=0, dy=0, flags=MOUSEEVENTF_MOVE, data=0):
    return INPUT(type=INPUT_MOUSE,
                 u=_INPUTunion(mi=MOUSEINPUT(dx, dy, data, flags, 0, MAGIC)))


def _key(vk, up=False):
    flags = KEYEVENTF_KEYUP if up else 0
    return INPUT(type=INPUT_KEYBOARD,
                 u=_INPUTunion(ki=KEYBDINPUT(vk, 0, flags, 0, MAGIC)))


def do_action():
    """Eine unauffaellige, unschaedliche Aktivitaet ausfuehren."""
    p0 = wt.POINT()
    user32.GetCursorPos(ctypes.byref(p0))
    dx = random.choice((-1, 1)) * random.randint(2, JIGGLE_PIXELS)
    dy = random.choice((-1, 1)) * random.randint(2, JIGGLE_PIXELS)
    _send(_mouse(dx, dy))                 # ein paar Pixel...
    time.sleep(0.04)
    p1 = wt.POINT()
    user32.GetCursorPos(ctypes.byref(p1))
    _send(_mouse(p0.x - p1.x, p0.y - p1.y))   # exakt zuruecksetzen (kein Drift, auch am Bildschirmrand)

    if random.random() < KEY_CHANCE:      # harmlose Taste, tippt nirgends Zeichen
        _send(_key(VK_F15), _key(VK_F15, up=True))

    if random.random() < SCROLL_CHANCE:   # Mini-Scroll, netto null
        _send(_mouse(flags=MOUSEEVENTF_WHEEL, data=120))
        time.sleep(0.02)
        _send(_mouse(flags=MOUSEEVENTF_WHEEL, data=(-120) & 0xFFFFFFFF))

    if ENABLE_CLICK and random.random() < CLICK_CHANCE:
        _send(_mouse(flags=MOUSEEVENTF_LEFTDOWN))
        _send(_mouse(flags=MOUSEEVENTF_LEFTUP))


# ----------------------- Erkennung echter Eingabe --------------------------
_lock          = threading.Lock()
_last_activity = time.monotonic()
_paused        = False
_running       = True

WH_KEYBOARD_LL          = 13
WH_MOUSE_LL             = 14
HC_ACTION               = 0
LLKHF_INJECTED          = 0x10
LLMHF_INJECTED          = 0x01
LLMHF_LOWER_IL_INJECTED = 0x02


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wt.DWORD), ("scanCode", wt.DWORD), ("flags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("pt", wt.POINT), ("mouseData", wt.DWORD), ("flags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]


HOOKPROC = ctypes.CFUNCTYPE(LRESULT, ctypes.c_int, wt.WPARAM, wt.LPARAM)

user32.SetWindowsHookExW.argtypes   = [ctypes.c_int, HOOKPROC, wt.HINSTANCE, wt.DWORD]
user32.SetWindowsHookExW.restype    = HHOOK
user32.CallNextHookEx.argtypes      = [HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM]
user32.CallNextHookEx.restype       = LRESULT
user32.UnhookWindowsHookEx.argtypes = [HHOOK]
user32.UnhookWindowsHookEx.restype  = wt.BOOL


def _mark_user_activity():
    global _last_activity
    with _lock:
        _last_activity = time.monotonic()


@HOOKPROC
def _kbd_proc(nCode, wParam, lParam):
    if nCode == HC_ACTION:
        st = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        if not (st.flags & LLKHF_INJECTED) and st.dwExtraInfo != MAGIC:
            _mark_user_activity()
    return user32.CallNextHookEx(None, nCode, wParam, lParam)


@HOOKPROC
def _mouse_proc(nCode, wParam, lParam):
    if nCode == HC_ACTION:
        st = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
        if not (st.flags & (LLMHF_INJECTED | LLMHF_LOWER_IL_INJECTED)) \
                and st.dwExtraInfo != MAGIC:
            _mark_user_activity()
    return user32.CallNextHookEx(None, nCode, wParam, lParam)


def _worker():
    global _action_count, _last_action_str, _active_session, _want_balloon
    last_action = 0.0
    interval = random.uniform(ACTION_MIN, ACTION_MAX)
    while _running:
        with _lock:
            idle = time.monotonic() - _last_activity
        active = (not _paused) and idle >= IDLE_THRESHOLD
        if active:
            now = time.monotonic()
            if now - last_action >= interval:
                try:
                    do_action()
                except Exception:
                    pass
                last_action = now
                interval = random.uniform(ACTION_MIN, ACTION_MAX)
                _action_count += 1
                _last_action_str = time.strftime("%H:%M:%S")
                if not _active_session:
                    _active_session = True
                    if NOTIFY_ON_ACTIVE:
                        _want_balloon = True
                _post_refresh()
        elif _active_session:
            _active_session = False
            _post_refresh()
        time.sleep(1)


# ------------------------------- Tray-Icon ---------------------------------
WNDPROC = ctypes.CFUNCTYPE(LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [("cbSize", wt.UINT), ("style", wt.UINT), ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                ("hInstance", wt.HINSTANCE), ("hIcon", wt.HICON), ("hCursor", wt.HANDLE),
                ("hbrBackground", wt.HBRUSH), ("lpszMenuName", wt.LPCWSTR),
                ("lpszClassName", wt.LPCWSTR), ("hIconSm", wt.HICON)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("hWnd", wt.HWND), ("uID", wt.UINT),
                ("uFlags", wt.UINT), ("uCallbackMessage", wt.UINT), ("hIcon", wt.HICON),
                ("szTip", wt.WCHAR * 128), ("dwState", wt.DWORD), ("dwStateMask", wt.DWORD),
                ("szInfo", wt.WCHAR * 256), ("uVersion", wt.UINT),
                ("szInfoTitle", wt.WCHAR * 64), ("dwInfoFlags", wt.DWORD),
                ("guidItem", ctypes.c_byte * 16), ("hBalloonIcon", wt.HICON)]


class MSG(ctypes.Structure):
    _fields_ = [("hwnd", wt.HWND), ("message", wt.UINT), ("wParam", wt.WPARAM),
                ("lParam", wt.LPARAM), ("time", wt.DWORD), ("pt", wt.POINT)]


WM_DESTROY      = 0x0002
WM_APP          = 0x8000
WM_TRAY         = WM_APP + 1
WM_RBUTTONUP    = 0x0205
WM_LBUTTONUP    = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_NULL         = 0x0000
NIM_ADD         = 0
NIM_DELETE      = 2
NIF_MESSAGE     = 0x01
NIF_ICON        = 0x02
NIF_TIP         = 0x04
IDI_APPLICATION = 32512
MF_STRING       = 0x0000
MF_SEPARATOR    = 0x0800
MF_GRAYED       = 0x0001
TPM_RIGHTBUTTON = 0x0002
TPM_NONOTIFY    = 0x0080
TPM_RETURNCMD   = 0x0100
ID_TOGGLE       = 1001
ID_EXIT         = 1002
ID_TEST         = 1003
ID_STATUS       = 1004
WM_REFRESH      = WM_APP + 2
WM_PING         = WM_APP + 3
MB_OK              = 0x0
MB_ICONINFORMATION = 0x40
MB_SETFOREGROUND   = 0x10000
MB_TOPMOST         = 0x40000
NIM_MODIFY      = 1
NIF_INFO        = 0x10
NIIF_INFO       = 0x01
IMAGE_ICON      = 1
LR_LOADFROMFILE = 0x0010
LR_DEFAULTSIZE  = 0x0040

user32.DefWindowProcW.argtypes   = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.DefWindowProcW.restype    = LRESULT
user32.RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
user32.RegisterClassExW.restype  = wt.ATOM
user32.CreateWindowExW.argtypes  = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD,
                                    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                    wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID]
user32.CreateWindowExW.restype   = wt.HWND
user32.DestroyWindow.argtypes    = [wt.HWND]
user32.DestroyWindow.restype     = wt.BOOL
user32.LoadIconW.argtypes        = [wt.HINSTANCE, wt.LPCWSTR]
user32.LoadIconW.restype         = wt.HICON
user32.LoadImageW.argtypes       = [wt.HINSTANCE, wt.LPCWSTR, wt.UINT,
                                    ctypes.c_int, ctypes.c_int, wt.UINT]
user32.LoadImageW.restype        = wt.HANDLE
user32.PostQuitMessage.argtypes  = [ctypes.c_int]
user32.GetMessageW.argtypes      = [ctypes.POINTER(MSG), wt.HWND, wt.UINT, wt.UINT]
user32.GetMessageW.restype       = ctypes.c_int
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype  = LRESULT
user32.SetForegroundWindow.argtypes = [wt.HWND]
user32.SetForegroundWindow.restype  = wt.BOOL
user32.PostMessageW.argtypes     = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.PostMessageW.restype      = wt.BOOL
user32.CreatePopupMenu.argtypes  = []
user32.CreatePopupMenu.restype   = wt.HMENU
user32.AppendMenuW.argtypes      = [wt.HMENU, wt.UINT, ctypes.c_size_t, wt.LPCWSTR]
user32.AppendMenuW.restype       = wt.BOOL
user32.TrackPopupMenu.argtypes   = [wt.HMENU, wt.UINT, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_int, wt.HWND, wt.LPVOID]
user32.TrackPopupMenu.restype    = ctypes.c_int
user32.DestroyMenu.argtypes      = [wt.HMENU]
user32.DestroyMenu.restype       = wt.BOOL
user32.GetCursorPos.argtypes     = [ctypes.POINTER(wt.POINT)]
user32.GetCursorPos.restype      = wt.BOOL
user32.RegisterWindowMessageW.argtypes = [wt.LPCWSTR]
user32.RegisterWindowMessageW.restype  = wt.UINT
user32.FindWindowW.argtypes = [wt.LPCWSTR, wt.LPCWSTR]
user32.FindWindowW.restype  = wt.HWND
user32.MessageBoxW.argtypes = [wt.HWND, wt.LPCWSTR, wt.LPCWSTR, wt.UINT]
user32.MessageBoxW.restype  = ctypes.c_int
shell32.Shell_NotifyIconW.argtypes = [wt.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
shell32.Shell_NotifyIconW.restype  = wt.BOOL
kernel32.GetModuleHandleW.argtypes = [wt.LPCWSTR]
kernel32.GetModuleHandleW.restype  = wt.HMODULE
kernel32.CreateMutexW.argtypes     = [wt.LPVOID, wt.BOOL, wt.LPCWSTR]
kernel32.CreateMutexW.restype      = wt.HANDLE

hmod = kernel32.GetModuleHandleW(None)

CLASS_NAME = "SettingsHostWindow"
_nid = NOTIFYICONDATAW()
_mouse_hook = None
_kbd_hook = None
_mutex = None
_taskbar_created = 0
_hwnd = None
_action_count = 0
_last_action_str = "-"
_active_session = False
_want_balloon = False


def MAKEINTRESOURCEW(x):
    return ctypes.cast(ctypes.c_void_p(x), wt.LPCWSTR)


def _load_icon():
    h = user32.LoadImageW(None, ICON_PATH, IMAGE_ICON, 0, 0,
                          LR_LOADFROMFILE | LR_DEFAULTSIZE)
    if not h:
        h = user32.LoadIconW(None, MAKEINTRESOURCEW(IDI_APPLICATION))
    return h


def add_icon(hwnd):
    _nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
    _nid.hWnd = hwnd
    _nid.uID = 1
    _nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
    _nid.uCallbackMessage = WM_TRAY
    _nid.hIcon = _load_icon()
    _nid.hBalloonIcon = _nid.hIcon
    _nid.szTip = TRAY_TOOLTIP
    shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(_nid))


def remove_icon():
    shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(_nid))


def status_text():
    if _paused:
        return "angehalten"
    with _lock:
        idle = time.monotonic() - _last_activity
    if idle >= IDLE_THRESHOLD:
        return "aktiv - haelt wach (letzte Aktion %s, %dx)" % (_last_action_str, _action_count)
    rest = int(IDLE_THRESHOLD - idle)
    return "wartet auf Leerlauf (noch %d:%02d, gesamt %dx)" % (rest // 60, rest % 60, _action_count)


def update_tooltip():
    _nid.uFlags = NIF_TIP
    _nid.szTip = ("%s - %s" % (TRAY_TOOLTIP, status_text()))[:127]
    shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(_nid))


def show_balloon(title, text):
    _nid.uFlags = NIF_INFO
    _nid.dwInfoFlags = NIIF_INFO
    _nid.szInfoTitle = title[:63]
    _nid.szInfo = text[:255]
    shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(_nid))


def _post_refresh():
    if _hwnd:
        user32.PostMessageW(_hwnd, WM_REFRESH, 0, 0)


def _notice(text):
    # Unuebersehbare Kontroll-Meldung nur bei DEINEM Start/Klick (nicht waehrend Abwesenheit).
    # Laeuft in eigenem Thread, damit die Nachrichtenschleife nicht blockiert.
    if not NOTIFY_ON_START:
        return
    def _show():
        user32.MessageBoxW(None, text, "Diagnostics",
                           MB_OK | MB_ICONINFORMATION | MB_SETFOREGROUND | MB_TOPMOST)
    threading.Thread(target=_show, daemon=True).start()


def show_menu(hwnd):
    global _paused, _action_count, _last_action_str
    menu = user32.CreatePopupMenu()
    user32.AppendMenuW(menu, MF_STRING | MF_GRAYED, 0, ("KAT - %s" % status_text())[:127])
    user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
    user32.AppendMenuW(menu, MF_STRING, ID_TEST, "Jetzt testen (Aktion ausfuehren)")
    user32.AppendMenuW(menu, MF_STRING, ID_STATUS, "Status anzeigen")
    user32.AppendMenuW(menu, MF_STRING, ID_TOGGLE,
                       "Fortsetzen" if _paused else "Pausieren")
    user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
    user32.AppendMenuW(menu, MF_STRING, ID_EXIT, "Beenden")
    pt = wt.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    user32.SetForegroundWindow(hwnd)
    cmd = user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON | TPM_RETURNCMD | TPM_NONOTIFY,
                                pt.x, pt.y, 0, hwnd, None)
    user32.PostMessageW(hwnd, WM_NULL, 0, 0)
    user32.DestroyMenu(menu)
    if cmd == ID_TOGGLE:
        _paused = not _paused
        if not _paused:
            _mark_user_activity()   # nach Fortsetzen erst wieder Ruhephase abwarten
        update_tooltip()
    elif cmd == ID_TEST:
        do_action()
        _action_count += 1
        _last_action_str = time.strftime("%H:%M:%S")
        update_tooltip()
        show_balloon("KAT - Test",
                     "Aktion ausgefuehrt: die Maus hat sich kurz bewegt. KAT funktioniert.")
    elif cmd == ID_STATUS:
        show_balloon("KAT - Status", status_text())
    elif cmd == ID_EXIT:
        user32.DestroyWindow(hwnd)


def py_wndproc(hwnd, msg, wparam, lparam):
    global _want_balloon
    if msg == WM_TRAY:
        if lparam in (WM_RBUTTONUP, WM_LBUTTONUP, WM_LBUTTONDBLCLK):
            show_menu(hwnd)
        return 0
    if msg == WM_REFRESH:
        update_tooltip()
        if _want_balloon:
            _want_balloon = False
            show_balloon("KAT", "haelt deinen Status jetzt aktiv.")
        return 0
    if msg == WM_PING:
        _notice("Trace-Host laeuft bereits.")
        return 0
    if _taskbar_created and msg == _taskbar_created:
        add_icon(hwnd)
        return 0
    if msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


WNDPROC_REF = WNDPROC(py_wndproc)


def create_window():
    wc = WNDCLASSEXW()
    wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
    wc.lpfnWndProc = WNDPROC_REF
    wc.hInstance = hmod
    wc.lpszClassName = CLASS_NAME
    user32.RegisterClassExW(ctypes.byref(wc))
    return user32.CreateWindowExW(0, CLASS_NAME, "", 0, 0, 0, 0, 0,
                                  None, None, hmod, None)


def main():
    global _mutex, _mouse_hook, _kbd_hook, _taskbar_created, _running, _hwnd

    # Nur eine Instanz zulassen
    _mutex = kernel32.CreateMutexW(None, False, "SettingsHostSingleton")
    if ctypes.get_last_error() == 183:   # ERROR_ALREADY_EXISTS
        # Laeuft schon -> der laufenden Instanz Bescheid geben (Feedback beim Doppelklick)
        existing = user32.FindWindowW(CLASS_NAME, None)
        if existing:
            user32.PostMessageW(existing, WM_PING, 0, 0)
        return

    _taskbar_created = user32.RegisterWindowMessageW("TaskbarCreated")
    hwnd = create_window()
    _hwnd = hwnd
    add_icon(hwnd)
    update_tooltip()

    # Low-Level-Hooks auf diesem (pumpenden) Thread installieren
    _mouse_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, _mouse_proc, hmod, 0)
    _kbd_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, _kbd_proc, hmod, 0)
    if not _mouse_hook or not _kbd_hook:
        # Eingabeerkennung fehlgeschlagen -> lieber gar nicht laufen, sonst
        # koennte KAT aktiv werden waehrend der Nutzer arbeitet.
        if _mouse_hook:
            user32.UnhookWindowsHookEx(_mouse_hook)
        if _kbd_hook:
            user32.UnhookWindowsHookEx(_kbd_hook)
        remove_icon()
        return

    _notice("Trace-Host laeuft.")
    threading.Thread(target=_worker, daemon=True).start()

    try:
        msg = MSG()
        while True:
            r = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if r == 0 or r == -1:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        _running = False
        if _mouse_hook:
            user32.UnhookWindowsHookEx(_mouse_hook)
        if _kbd_hook:
            user32.UnhookWindowsHookEx(_kbd_hook)
        remove_icon()


if __name__ == "__main__":
    main()
