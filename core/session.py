"""
Gibberish Session Manager
==========================
Tracks session state to ensure the initializer prompt
is injected exactly ONCE per session.
"""

import time
from typing import Optional


class SessionManager:
    """
    Manages session lifecycle for Gibberish.

    A 'session' begins when the first compression is triggered
    and ends when explicitly reset or the app restarts.

    Tracks:
        - Whether the initializer has been injected
        - Compression count in current session
        - Session start time
    """

    def __init__(self):
        self._initializer_injected: bool = False
        self._compression_count: int = 0
        self._session_start: float = time.time()
        self._session_id: int = 1

    @property
    def is_initializer_injected(self) -> bool:
        """Check if the initializer has already been sent this session."""
        return self._initializer_injected

    @property
    def compression_count(self) -> int:
        """Number of compressions performed in this session."""
        return self._compression_count

    @property
    def session_id(self) -> int:
        """Current session ID (increments on reset)."""
        return self._session_id

    @property
    def session_duration(self) -> float:
        """Seconds since session started."""
        return time.time() - self._session_start

    def mark_initializer_injected(self) -> None:
        """Mark the initializer as injected for this session."""
        self._initializer_injected = True

    def increment_compression(self) -> None:
        """Track another compression event."""
        self._compression_count += 1

    def reset_session(self) -> None:
        """
        Reset the session state entirely.
        Initializer will be re-injected on next compression.
        """
        self._initializer_injected = False
        self._compression_count = 0
        self._session_start = time.time()
        self._session_id += 1

    def get_status(self) -> dict:
        """Return a snapshot of current session state."""
        return {
            "session_id": self._session_id,
            "initializer_injected": self._initializer_injected,
            "compression_count": self._compression_count,
            "duration_seconds": round(self.session_duration, 1),
        }
