"""
Gibberish Global Hotkey Handler
================================
Uses `keyboard` library for global hotkey registration on Windows.
The suppress=True flag intercepts keys at OS level BEFORE any
application sees them — no conflicts with VS Code, volume keys, etc.

Note: Requires Administrator privileges on Windows.
"""

import threading
from typing import Callable, Optional


class HotkeyManager:
    """
    Global hotkey manager using the keyboard library.
    Suppresses the hotkey so no other app receives it.
    """

    def __init__(self):
        self._hotkey_handle = None
        self._callback: Optional[Callable] = None
        self._current_shortcut: Optional[str] = None

    def register(self, shortcut: str, callback: Callable) -> None:
        """
        Register a global hotkey combination.
        The hotkey is suppressed — it won't reach any application.
        """
        import keyboard

        self._callback = callback
        self._current_shortcut = shortcut

        print(f"[Gibberish] Registering hotkey: {shortcut} (suppressed)")

        self._hotkey_handle = keyboard.add_hotkey(
            shortcut,
            lambda: threading.Thread(target=self._safe_callback, daemon=True).start(),
            suppress=True,
            trigger_on_release=False,
        )

        print("[Gibberish] Hotkey listener started")

    def _safe_callback(self):
        """Wrapper to catch exceptions in callback."""
        try:
            if self._callback:
                self._callback()
        except Exception as e:
            print(f"[Gibberish] Hotkey callback error: {e}")
            import traceback
            traceback.print_exc()

    def unregister(self) -> None:
        """Remove current hotkey registration."""
        if self._hotkey_handle is not None:
            try:
                import keyboard
                keyboard.remove_hotkey(self._hotkey_handle)
            except Exception:
                pass
            self._hotkey_handle = None

    def update_shortcut(self, new_shortcut: str) -> None:
        """Change the hotkey at runtime."""
        if self._callback:
            self.unregister()
            self.register(new_shortcut, self._callback)

    def wait(self) -> None:
        """Block until interrupted."""
        import keyboard
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            pass

    def shutdown(self) -> None:
        """Clean shutdown."""
        self.unregister()
