"""
Gibberish Session Initializer
===============================
Manages the one-time session initializer prompt that gets
prepended to the first compressed output per session.
"""

from typing import Optional
from core.session import SessionManager


class SessionInitializer:
    """
    Handles the session initializer prompt injection.

    The initializer is a system-level instruction prepended to the
    FIRST compressed prompt in a session, designed to set the tone
    for AI responses (e.g., "Respond minimal. No fluff.").

    Rules:
        - Injected ONLY once per session
        - Always placed at the beginning of output
        - Never repeated until session is reset
        - Can be toggled on/off via config
    """

    # Separator between initializer and compressed prompt
    SEPARATOR = "\n---\n"

    def __init__(self, session: SessionManager, enabled: bool = True,
                 text: str = "Respond minimal. No fluff. Direct answers only."):
        self._session = session
        self._enabled = enabled
        self._text = text.strip()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value.strip()

    def process(self, compressed_text: str) -> str:
        """
        Conditionally prepend the initializer to compressed text.

        Returns:
            The final output string, with or without initializer.
        """
        if not self._enabled:
            return compressed_text

        if self._session.is_initializer_injected:
            # Already injected this session — return as-is
            return compressed_text

        # First compression this session — inject initializer
        self._session.mark_initializer_injected()
        return f"{self._text}{self.SEPARATOR}{compressed_text}"

    def force_reinject(self) -> None:
        """
        Force the initializer to be injected again on next compression.
        Useful for session resets without full session reset.
        """
        self._session.reset_session()
