"""
Gibberish Clipboard Handler
=============================
Cross-platform clipboard access with fallback chains.

Priority:
    Windows  → win32clipboard (ctypes) → pyperclip fallback
    macOS    → pbcopy/pbpaste → pyperclip fallback
    Linux    → xclip / xsel / wl-copy → pyperclip fallback
"""

import platform
import subprocess
import time
from typing import Optional

_SYSTEM = platform.system()


# ── Windows native clipboard via ctypes ──────────────────────────────

def _win_get_clipboard() -> Optional[str]:
    """Read clipboard text on Windows using ctypes."""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        CF_UNICODETEXT = 13

        if not user32.OpenClipboard(0):
            return None

        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return None

            kernel32.GlobalLock.restype = ctypes.c_void_p
            ptr = kernel32.GlobalLock(handle)
            if not ptr:
                return None

            try:
                text = ctypes.wstring_at(ptr)
                return text
            finally:
                kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()

    except Exception:
        return None


def _win_set_clipboard(text: str) -> bool:
    """Write text to clipboard on Windows using ctypes."""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        CF_UNICODETEXT = 13
        GMEM_MOVEABLE = 0x0002

        # Encode to UTF-16-LE with null terminator
        data = text.encode("utf-16-le") + b"\x00\x00"
        size = len(data)

        if not user32.OpenClipboard(0):
            return False

        try:
            user32.EmptyClipboard()

            handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
            if not handle:
                return False

            kernel32.GlobalLock.restype = ctypes.c_void_p
            ptr = kernel32.GlobalLock(handle)
            if not ptr:
                kernel32.GlobalFree(handle)
                return False

            ctypes.memmove(ptr, data, size)
            kernel32.GlobalUnlock(handle)

            user32.SetClipboardData(CF_UNICODETEXT, handle)
            return True
        finally:
            user32.CloseClipboard()

    except Exception:
        return False


# ── macOS clipboard ──────────────────────────────────────────────────

def _mac_get_clipboard() -> Optional[str]:
    """Read clipboard on macOS using pbpaste."""
    try:
        result = subprocess.run(
            ["pbpaste"], capture_output=True, text=True, timeout=2
        )
        return result.stdout if result.returncode == 0 else None
    except Exception:
        return None


def _mac_set_clipboard(text: str) -> bool:
    """Write to clipboard on macOS using pbcopy."""
    try:
        process = subprocess.Popen(
            ["pbcopy"], stdin=subprocess.PIPE
        )
        process.communicate(text.encode("utf-8"), timeout=2)
        return process.returncode == 0
    except Exception:
        return False


# ── Linux clipboard ──────────────────────────────────────────────────

def _find_linux_clipboard_tool() -> Optional[str]:
    """Detect available clipboard tool on Linux."""
    # Check for Wayland first
    import os
    if os.environ.get("WAYLAND_DISPLAY"):
        for tool in ("wl-copy", "wl-paste"):
            try:
                subprocess.run(["which", tool], capture_output=True, check=True)
                return "wl-clipboard"
            except Exception:
                pass

    # X11 tools
    for tool in ("xclip", "xsel"):
        try:
            subprocess.run(["which", tool], capture_output=True, check=True)
            return tool
        except Exception:
            pass

    return None


def _linux_get_clipboard() -> Optional[str]:
    """Read clipboard on Linux."""
    try:
        tool = _find_linux_clipboard_tool()
        if tool == "wl-clipboard":
            result = subprocess.run(
                ["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=2
            )
        elif tool == "xclip":
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"],
                capture_output=True, text=True, timeout=2
            )
        elif tool == "xsel":
            result = subprocess.run(
                ["xsel", "--clipboard", "--output"],
                capture_output=True, text=True, timeout=2
            )
        else:
            return None

        return result.stdout if result.returncode == 0 else None
    except Exception:
        return None


def _linux_set_clipboard(text: str) -> bool:
    """Write to clipboard on Linux."""
    try:
        tool = _find_linux_clipboard_tool()
        if tool == "wl-clipboard":
            process = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
        elif tool == "xclip":
            process = subprocess.Popen(
                ["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE
            )
        elif tool == "xsel":
            process = subprocess.Popen(
                ["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE
            )
        else:
            return False

        process.communicate(text.encode("utf-8"), timeout=2)
        return process.returncode == 0
    except Exception:
        return False


# ── Pyperclip fallback ───────────────────────────────────────────────

def _pyperclip_get() -> Optional[str]:
    """Fallback: read clipboard via pyperclip."""
    try:
        import pyperclip
        return pyperclip.paste()
    except Exception:
        return None


def _pyperclip_set(text: str) -> bool:
    """Fallback: write clipboard via pyperclip."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        return False


# ── Public API ───────────────────────────────────────────────────────

def get_clipboard() -> Optional[str]:
    """
    Read text from system clipboard.
    Uses platform-native API first, falls back to pyperclip.
    """
    if _SYSTEM == "Windows":
        result = _win_get_clipboard()
        if result is not None:
            return result
    elif _SYSTEM == "Darwin":
        result = _mac_get_clipboard()
        if result is not None:
            return result
    elif _SYSTEM == "Linux":
        result = _linux_get_clipboard()
        if result is not None:
            return result

    return _pyperclip_get()


def set_clipboard(text: str) -> bool:
    """
    Write text to system clipboard.
    Uses platform-native API first, falls back to pyperclip.
    """
    if _SYSTEM == "Windows":
        if _win_set_clipboard(text):
            return True
    elif _SYSTEM == "Darwin":
        if _mac_set_clipboard(text):
            return True
    elif _SYSTEM == "Linux":
        if _linux_set_clipboard(text):
            return True

    return _pyperclip_set(text)


def save_clipboard() -> Optional[str]:
    """Save current clipboard content for later restoration."""
    return get_clipboard()


def restore_clipboard(content: Optional[str]) -> None:
    """Restore previously saved clipboard content."""
    if content is not None:
        set_clipboard(content)
