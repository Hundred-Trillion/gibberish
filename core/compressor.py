"""
Gibberish Prompt Compression Engine
====================================
Transforms verbose, messy prompts into minimal structured form.
Zero-dependency NLP — pure regex + heuristic pipeline.
"""

import re
from typing import List


# ── Filler / politeness tokens to strip ──────────────────────────────

FILLER_WORDS = {
    # greetings & pleasantries
    "hey", "hi", "hello", "yo", "sup", "hiya", "howdy",
    "please", "pls", "plz", "kindly", "thanks", "thank", "thx",
    "bro", "dude", "mate", "man", "buddy", "fam", "bruh",
    "sir", "madam",

    # hedging / softeners
    "just", "maybe", "perhaps", "possibly", "actually", "basically",
    "literally", "honestly", "frankly", "really", "very", "quite",
    "simply", "merely", "kind", "kinda", "sorta", "sort",

    # filler phrases (single-word components)
    "um", "uh", "hmm", "well", "so", "like", "okay", "ok", "right",
    "anyway", "anyways", "alright",

    # redundant modals
    "would", "could", "should", "might",

    # question softeners
    "wondering", "wonder", "curious",

    # misc noise
    "also", "some", "probably", "guess", "suppose",
    "sure", "appreciate", "getting",
}

# Ultra-mode only: strip articles/prepositions for maximum density
ULTRA_STRIP_WORDS = {
    "the", "a", "an", "of", "to", "in", "on", "at", "by",
    "it", "its", "i", "my", "me", "you", "your",
    "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "this", "that", "these", "those",
    "not",
}

FILLER_PHRASES = [
    # multi-word patterns to strip (order: longest first)
    r"\bcan you\b",
    r"\bcould you\b",
    r"\bwould you\b",
    r"\bwould you mind\b",
    r"\bdo you think\b",
    r"\bI was wondering\b",
    r"\bI wanted to\b",
    r"\bI want to\b",
    r"\bI need to\b",
    r"\bI'd like to\b",
    r"\bI would like to\b",
    r"\bif you don'?t mind\b",
    r"\bif possible\b",
    r"\bwhen you get a chance\b",
    r"\bwhen you have time\b",
    r"\bat your earliest convenience\b",
    r"\bfor me\b",
    r"\bit would be great if\b",
    r"\bit'd be great if\b",
    r"\bit would be nice if\b",
    r"\bno worries if not\b",
    r"\bno pressure\b",
    r"\bthanks in advance\b",
    r"\bthank you in advance\b",
    r"\bI appreciate\b",
    r"\bmuch appreciated\b",
    r"\bthanks a lot\b",
    r"\bthanks so much\b",
    r"\bhey there\b",
    r"\bhi there\b",
    r"\bcan you help me\b",
    r"\bhelp me\b",
    r"\bwith examples?\b",
    r"\bwith an example\b",
    r"\bwith some\b",
    r"\bI'd\b",
    r"\bI'm\b",
    r"\bit might be\b",
    r"\bin detail\b",
    r"\bin simple terms\b",
    r"\bin a nutshell\b",
    r"\bas soon as possible\b",
    r"\basap\b",
    r"\bif you can\b",
    r"\bif you could\b",
    r"\ba bit\b",
    r"\ba little\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\byou know\b",
    r"\bI mean\b",
    r"\bI think\b",
    r"\bI guess\b",
    r"\bI believe\b",
    r"\bI suppose\b",
    r"\bto be honest\b",
    r"\bto be fair\b",
    r"\bat the end of the day\b",
    r"\bat this point\b",
    r"\bfor what it'?s worth\b",
    r"\bin my opinion\b",
    r"\bin any case\b",
]

# Precompile patterns for speed
_PHRASE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in FILLER_PHRASES]

# Punctuation noise
_PUNCTUATION_NOISE = re.compile(r"[!?.…,;:]+")
_MULTI_SPACE = re.compile(r"\s{2,}")
_LEADING_CONJUNCTIONS = re.compile(r"^(and|but|or|so|then|also|yet)\s+", re.IGNORECASE)


class PromptCompressor:
    """
    Multi-pass prompt compression engine.

    Compression levels:
        - light   → remove greetings + politeness only
        - medium  → + filler words + phrase patterns
        - ultra   → + structural restructuring into bullet points
    """

    def __init__(self, level: str = "ultra", custom_fillers: List[str] = None,
                 custom_removals: List[str] = None):
        self.level = level.lower()
        self.filler_words = FILLER_WORDS.copy()
        if custom_fillers:
            self.filler_words.update(w.lower() for w in custom_fillers)
        self.extra_patterns = []
        if custom_removals:
            self.extra_patterns = [
                re.compile(re.escape(r), re.IGNORECASE) for r in custom_removals
            ]

    def compress(self, text: str) -> str:
        """Main entry point. Returns compressed prompt."""
        if not text or not text.strip():
            return text

        result = text.strip()

        # Pass 1: Strip multi-word filler phrases
        result = self._strip_phrases(result)

        # Pass 2: Strip custom removal patterns
        result = self._strip_custom(result)

        if self.level in ("medium", "ultra"):
            # Pass 3: Strip individual filler words
            result = self._strip_filler_words(result)

        if self.level == "ultra":
            # Pass 3.5: Ultra-aggressive article/preposition strip
            result = self._strip_ultra_words(result)

        # Pass 4: Clean punctuation noise
        result = self._clean_punctuation(result)

        # Pass 5: Normalize whitespace
        result = _MULTI_SPACE.sub(" ", result).strip()

        if self.level == "ultra":
            # Pass 6: Structural restructuring
            result = self._restructure(result)

        # Final cleanup
        result = self._final_clean(result)

        return result

    def _strip_phrases(self, text: str) -> str:
        """Remove multi-word filler phrases."""
        for pattern in _PHRASE_PATTERNS:
            text = pattern.sub(" ", text)
        return text

    def _strip_custom(self, text: str) -> str:
        """Remove user-defined custom patterns."""
        for pattern in self.extra_patterns:
            text = pattern.sub(" ", text)
        return text

    def _strip_filler_words(self, text: str) -> str:
        """Remove individual filler/hedge words while preserving structure."""
        words = text.split()
        filtered = []
        for word in words:
            clean = word.strip(".,!?;:'\"").lower()
            if clean not in self.filler_words:
                filtered.append(word)
        return " ".join(filtered)

    def _strip_ultra_words(self, text: str) -> str:
        """Ultra mode: strip articles, prepositions, pronouns for max density."""
        words = text.split()
        filtered = []
        for word in words:
            clean = word.strip(".,!?;:'\"").lower()
            if clean not in ULTRA_STRIP_WORDS:
                filtered.append(word)
        return " ".join(filtered)

    def _clean_punctuation(self, text: str) -> str:
        """Collapse repeated punctuation, strip trailing noise."""
        # Collapse runs of punctuation into single period
        text = _PUNCTUATION_NOISE.sub(".", text)
        # Remove leading/trailing dots
        text = text.strip(".")
        return text

    def _restructure(self, text: str) -> str:
        """
        Ultra mode: split into semantic lines.
        Splits on natural boundaries and capitalizes each line.
        """
        # Split on periods, commas, 'and', 'but', newlines
        parts = re.split(r"[.\n]+|,\s*|\band\b|\bbut\b", text, flags=re.IGNORECASE)
        lines = []
        for part in parts:
            cleaned = part.strip()
            cleaned = _LEADING_CONJUNCTIONS.sub("", cleaned).strip()
            cleaned = _MULTI_SPACE.sub(" ", cleaned)
            if cleaned and len(cleaned) > 1:
                # Capitalize first letter
                cleaned = cleaned[0].upper() + cleaned[1:]
                lines.append(cleaned)

        if not lines:
            return text

        return "\n".join(lines)

    def _final_clean(self, text: str) -> str:
        """Final pass: remove noise lines, merge fragments, strip whitespace."""
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]

        # Remove lines that are too short to be useful (single filler words)
        cleaned = []
        for line in lines:
            # Skip single-word lines that are just noise
            words = line.split()
            if len(words) == 1 and words[0].lower().strip(".,!?") in (
                self.filler_words | ULTRA_STRIP_WORDS
                if self.level == "ultra" else self.filler_words
            ):
                continue
            # Skip very short fragment lines (1-3 chars)
            if len(line) <= 3:
                continue
            cleaned.append(line)

        # Merge very short lines into previous line
        merged = []
        for line in cleaned:
            if merged and len(line.split()) <= 2 and len(merged[-1].split()) <= 4:
                merged[-1] = f"{merged[-1]} {line}"
            else:
                merged.append(line)

        return "\n".join(merged)
