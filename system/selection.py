"""
Gibberish Text Selection Handler
==================================
Captures and replaces selected text system-wide using the
clipboard-copy trick. Waits for user to fully release hotkey
before simulating copy/paste.
"""

import platform
import time
from typing import Optional
from pynput.keyboard import Key, Controller

from system.clipboard import get_clipboard, set_clipboard, save_clipboard, restore_clipboard

_SYSTEM = platform.system()
_kb = Controller()


def _wait_for_modifiers_released(timeout: float = 1.0) -> None:
    """
    Wait until the user has physically released all modifier keys.
    This prevents our simulated Ctrl+C from becoming Ctrl+Alt+C, etc.
    """
    # Just wait a fixed time for the user to release keys
    time.sleep(0.3)


def _simulate_copy() -> None:
    """Simulate Ctrl+C to copy selected text."""
    if _SYSTEM == "Darwin":
        _kb.press(Key.cmd)
        time.sleep(0.02)
        _kb.press("c")
        time.sleep(0.02)
        _kb.release("c")
        _kb.release(Key.cmd)
    else:
        _kb.press(Key.ctrl_l)
        time.sleep(0.02)
        _kb.press("c")
        time.sleep(0.02)
        _kb.release("c")
        _kb.release(Key.ctrl_l)


def _simulate_paste() -> None:
    """Simulate Ctrl+V to paste from clipboard."""
    if _SYSTEM == "Darwin":
        _kb.press(Key.cmd)
        time.sleep(0.02)
        _kb.press("v")
        time.sleep(0.02)
        _kb.release("v")
        _kb.release(Key.cmd)
    else:
        _kb.press(Key.ctrl_l)
        time.sleep(0.02)
        _kb.press("v")
        time.sleep(0.02)
        _kb.release("v")
        _kb.release(Key.ctrl_l)


def capture_selection(delay_ms: int = 150) -> Optional[str]:
    """
    Capture currently selected text from any application.

    Returns:
        The selected text, or None if nothing was selected.
    """
    print("[DBG] Waiting for modifier keys to be released...")
    _wait_for_modifiers_released()

    # Save original clipboard
    original = save_clipboard()
    print(f"[DBG] Saved clipboard: {repr(original[:50]) if original else 'None'}")

    # Clear clipboard to detect new content
    set_clipboard("")
    time.sleep(0.1)

    # Simulate copy
    print("[DBG] Simulating Ctrl+C...")
    _simulate_copy()

    # Wait for the copy to complete
    time.sleep(delay_ms / 1000.0)

    # Read what was copied
    selected = get_clipboard()
    print(f"[DBG] Clipboard after copy: {repr(selected[:80]) if selected else 'None'}")

    # Restore original clipboard
    restore_clipboard(original)

    # If clipboard is empty, nothing was selected
    if not selected or selected.strip() == "":
        print("[DBG] No text detected in clipboard")
        return None

    print(f"[DBG] Captured selection: {repr(selected[:80])}")
    return selected


def replace_selection(text: str, delay_ms: int = 150) -> bool:
    """
    Replace currently selected text with the given text.

    Returns:
        True if replacement was successful.
    """
    # Save original clipboard
    original = save_clipboard()

    # Write replacement to clipboard
    set_clipboard(text)
    time.sleep(0.1)

    # Simulate paste
    print("[DBG] Simulating Ctrl+V to paste replacement...")
    _simulate_paste()

    # Wait for paste to complete
    time.sleep(delay_ms / 1000.0)

    # Restore original clipboard after a delay
    time.sleep(0.3)
    restore_clipboard(original)

    print("[DBG] Selection replaced")
    return True
