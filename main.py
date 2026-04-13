"""
╔═══════════════════════════════════════════════════════════════╗
║                       GIBBERISH                               ║
║              Global Prompt Compression Tool                   ║
║                                                               ║
║   Select chaos. Press shortcut. Get clarity.                  ║
╚═══════════════════════════════════════════════════════════════╝

Usage:
    python main.py              → Start Gibberish (background daemon)
    python main.py --test       → Run compression on a sample prompt
    python main.py --reset      → Reset session state
    python main.py --status     → Show session status
"""

import json
import os
import sys
import time
import threading
import argparse
import io
from pathlib import Path

# Force UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Resolve project root for imports ─────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from core.compressor import PromptCompressor
from core.session import SessionManager
from core.initializer import SessionInitializer
from system.hotkey import HotkeyManager
from system.selection import capture_selection, replace_selection


# ── Config loader ────────────────────────────────────────────────────

CONFIG_PATH = PROJECT_ROOT / "config" / "settings.json"


def load_config() -> dict:
    """Load configuration from settings.json."""
    if not CONFIG_PATH.exists():
        print(f"[!] Config not found at {CONFIG_PATH}, using defaults.")
        return {
            "shortcut": ["ctrl", "6", "7"],
            "initializer_enabled": True,
            "initializer_text": "Respond minimal. No fluff. Direct answers only.",
            "compression_level": "ultra",
            "simulate_copy_delay_ms": 50,
            "simulate_paste_delay_ms": 50,
            "notification_enabled": True,
            "log_enabled": False,
            "log_file": "gibberish.log",
            "custom_filler_words": [],
            "custom_removals": [],
        }

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Notification (lightweight, optional) ─────────────────────────────

def notify(title: str, message: str) -> None:
    """Send a system notification (best-effort, non-blocking)."""
    import platform
    system = platform.system()

    try:
        if system == "Windows":
            # Use Windows toast notification via PowerShell
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $textNodes = $template.GetElementsByTagName("text")
            $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null
            $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Gibberish").Show($toast)
            '''
            import subprocess
            subprocess.Popen(
                ["powershell", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=0x08000000,  # CREATE_NO_WINDOW
            )
        elif system == "Darwin":
            import subprocess
            subprocess.Popen([
                "osascript", "-e",
                f'display notification "{message}" with title "{title}"'
            ])
        elif system == "Linux":
            import subprocess
            subprocess.Popen(["notify-send", title, message])
    except Exception:
        pass  # Notifications are best-effort


# ── Logger ───────────────────────────────────────────────────────────

class GibberishLogger:
    """Simple lightweight logger."""

    def __init__(self, enabled: bool = False, log_file: str = "gibberish.log"):
        self.enabled = enabled
        self.log_path = PROJECT_ROOT / log_file

    def log(self, message: str) -> None:
        """Log a message with timestamp."""
        if not self.enabled:
            return
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

    def info(self, msg: str) -> None:
        self.log(f"INFO  | {msg}")

    def error(self, msg: str) -> None:
        self.log(f"ERROR | {msg}")


# ── Main Application ────────────────────────────────────────────────

class Gibberish:
    """
    Main Gibberish application.
    Orchestrates compression, session management, and system integration.
    """

    def __init__(self):
        self.config = load_config()
        self.logger = GibberishLogger(
            enabled=self.config.get("log_enabled", False),
            log_file=self.config.get("log_file", "gibberish.log"),
        )

        # Initialize core engines
        self.compressor = PromptCompressor(
            level=self.config.get("compression_level", "ultra"),
            custom_fillers=self.config.get("custom_filler_words", []),
            custom_removals=self.config.get("custom_removals", []),
        )
        self.session = SessionManager()
        self.initializer = SessionInitializer(
            session=self.session,
            enabled=self.config.get("initializer_enabled", True),
            text=self.config.get("initializer_text", "Respond minimal. No fluff."),
        )

        # System integration
        self.hotkey = HotkeyManager()
        self._lock = threading.Lock()

        self.logger.info("Gibberish initialized")

    def process_selection(self) -> None:
        """
        Main workflow — triggered by global hotkey.

        1. Capture selected text (via clipboard trick)
        2. Compress the prompt
        3. Prepend initializer (if first time in session)
        4. Replace the original selection with compressed output
        """
        with self._lock:  # Prevent re-entrant calls
            try:
                print("\n[Gibberish] === HOTKEY TRIGGERED ===")

                # Step 1: Capture selected text
                copy_delay = self.config.get("simulate_copy_delay_ms", 150)
                selected = capture_selection(delay_ms=copy_delay)

                if not selected:
                    print("[Gibberish] No text selected — aborting")
                    return

                print(f"[Gibberish] CAPTURED: \"{selected}\"")

                # Step 2: Compress
                compressed = self.compressor.compress(selected)
                print(f"[Gibberish] COMPRESSED: \"{compressed}\"")

                # Step 3: Apply session initializer
                final = self.initializer.process(compressed)
                print(f"[Gibberish] FINAL OUTPUT: \"{final}\"")

                # Step 4: Track session
                self.session.increment_compression()

                # Step 5: Replace selection
                paste_delay = self.config.get("simulate_paste_delay_ms", 150)
                replace_selection(final, delay_ms=paste_delay)

                print(f"[Gibberish] Done! (compression #{self.session.compression_count})")

            except Exception as e:
                print(f"[Gibberish] ERROR: {e}")
                import traceback
                traceback.print_exc()

    def start(self) -> None:
        """Start Gibberish in background mode."""
        shortcut_keys = self.config.get("shortcut", ["ctrl", "6", "7"])

        # Convert list to keyboard shortcut string
        if isinstance(shortcut_keys, list):
            shortcut_str = "+".join(shortcut_keys)
        else:
            shortcut_str = shortcut_keys

        print()
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║                     GIBBERISH v1.0                       ║")
        print("║             Global Prompt Compression Tool               ║")
        print("╠═══════════════════════════════════════════════════════════╣")
        print(f"║  Shortcut     : {shortcut_str:<41}║")
        print(f"║  Compression  : {self.config.get('compression_level', 'ultra'):<41}║")
        print(f"║  Initializer  : {'ON' if self.config.get('initializer_enabled') else 'OFF':<41}║")
        print("╠═══════════════════════════════════════════════════════════╣")
        print("║  Select text → Press shortcut → Get compressed prompt    ║")
        print("║  Press Ctrl+C to exit                                    ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print()

        self.logger.info(f"Starting with shortcut: {shortcut_str}")

        # Register hotkey
        self.hotkey.register(shortcut_str, self.process_selection)

        try:
            # Block main thread
            self.hotkey.wait()
        except KeyboardInterrupt:
            print("\n[Gibberish] Shutting down...")
            self.shutdown()

    def shutdown(self) -> None:
        """Clean shutdown."""
        self.hotkey.shutdown()
        self.logger.info("Gibberish shut down")
        print("[Gibberish] Goodbye.")

    def reset_session(self) -> None:
        """Reset session — initializer will be re-injected."""
        self.session.reset_session()
        self.logger.info("Session reset")
        print("[Gibberish] Session reset. Initializer will re-inject on next use.")

    def get_status(self) -> dict:
        """Get current session status."""
        return self.session.get_status()


# ── CLI Interface ────────────────────────────────────────────────────

def run_test():
    """Run a quick compression test without hotkey registration."""
    config = load_config()
    compressor = PromptCompressor(
        level=config.get("compression_level", "ultra"),
        custom_fillers=config.get("custom_filler_words", []),
    )
    session = SessionManager()
    initializer = SessionInitializer(
        session=session,
        enabled=config.get("initializer_enabled", True),
        text=config.get("initializer_text", "Respond minimal. No fluff."),
    )

    test_prompts = [
        "hey bro can you explain recursion in python simply with examples pls",
        "Hi there, I was wondering if you could possibly help me understand how "
        "neural networks work? I'd really appreciate it if you could explain the "
        "basics with some simple examples. Thanks in advance!",
        "ok so basically I need you to write a function that takes a list of numbers "
        "and returns the sorted list but like without using the built-in sort method "
        "please and thank you, also maybe add some comments to explain what's happening",
        "Could you kindly help me debug this error? I'm getting a TypeError when I try "
        "to concatenate a string and an integer in Python. I think it might be a type "
        "conversion issue but I'm not really sure honestly.",
    ]

    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║              GIBBERISH COMPRESSION TEST                   ║")
    print(f"║  Level: {config.get('compression_level', 'ultra'):<49}║")
    print("╚═══════════════════════════════════════════════════════════╝\n")

    for i, prompt in enumerate(test_prompts, 1):
        compressed = compressor.compress(prompt)
        final = initializer.process(compressed)

        input_len = len(prompt)
        output_len = len(final)
        ratio = int((1 - output_len / max(input_len, 1)) * 100)

        print(f"── Test {i} ──────────────────────────────────────────")
        print(f"  INPUT  ({input_len} chars):")
        print(f"    \"{prompt}\"")
        print(f"  OUTPUT ({output_len} chars, -{ratio}%):")
        for line in final.split("\n"):
            print(f"    {line}")
        print()

    session_status = session.get_status()
    print(f"── Session Status ─────────────────────────────────────")
    print(f"  Session ID          : {session_status['session_id']}")
    print(f"  Initializer injected: {session_status['initializer_injected']}")
    print(f"  Compressions        : {session_status['compression_count']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Gibberish — Global Prompt Compression Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py          Start Gibberish daemon
  python main.py --test   Run compression test
  python main.py --reset  Reset session state
  python main.py --status Show session info
        """,
    )
    parser.add_argument("--test", action="store_true", help="Run compression test")
    parser.add_argument("--reset", action="store_true", help="Reset current session")
    parser.add_argument("--status", action="store_true", help="Show session status")

    args = parser.parse_args()

    if args.test:
        run_test()
        return

    app = Gibberish()

    if args.reset:
        app.reset_session()
        return

    if args.status:
        status = app.get_status()
        print("\n[Gibberish] Session Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        print()
        return

    # Default: start daemon
    app.start()


if __name__ == "__main__":
    main()
