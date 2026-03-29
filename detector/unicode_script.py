"""
Unicode script heuristics for instant language pre-classification.

Maps Unicode block ranges to ISO 639-1 language codes.
This avoids invoking ML models for clearly non-Latin scripts.
"""
import unicodedata
import re

# Map (start, end) codepoint ranges to ISO 639-1 codes.
# When multiple languages share a script we return the most common one
# and let the downstream detector disambiguate.
SCRIPT_RANGES = [
    # CJK Unified Ideographs + extensions → Chinese (zh)
    (0x4E00,  0x9FFF,  "zh"),
    (0x3400,  0x4DBF,  "zh"),
    (0x20000, 0x2A6DF, "zh"),
    (0x2A700, 0x2B73F, "zh"),
    (0x2B740, 0x2B81F, "zh"),
    (0x2B820, 0x2CEAF, "zh"),
    (0xF900,  0xFAFF,  "zh"),
    # Hiragana / Katakana → Japanese (ja)
    (0x3040,  0x309F,  "ja"),
    (0x30A0,  0x30FF,  "ja"),
    (0x31F0,  0x31FF,  "ja"),
    # CJK Compatibility / Katakana phonetic ext
    (0x3200,  0x32FF,  "ja"),
    # Hangul → Korean (ko)
    (0xAC00,  0xD7AF,  "ko"),
    (0x1100,  0x11FF,  "ko"),
    (0x3130,  0x318F,  "ko"),
    (0xA960,  0xA97F,  "ko"),
    (0xD7B0,  0xD7FF,  "ko"),
    # Arabic → ar (Arabic, Persian, Urdu share; use ar as default)
    (0x0600,  0x06FF,  "ar"),
    (0x0750,  0x077F,  "ar"),
    (0xFB50,  0xFDFF,  "ar"),
    (0xFE70,  0xFEFF,  "ar"),
    # Hebrew → he
    (0x0590,  0x05FF,  "he"),
    (0xFB1D,  0xFB4F,  "he"),
    # Devanagari → hi (also Marathi, Nepali; hi is default)
    (0x0900,  0x097F,  "hi"),
    # Tamil → ta
    (0x0B80,  0x0BFF,  "ta"),
    # Telugu → te
    (0x0C00,  0x0C7F,  "te"),
    # Kannada → kn
    (0x0C80,  0x0CFF,  "kn"),
    # Malayalam → ml
    (0x0D00,  0x0D7F,  "ml"),
    # Bengali → bn
    (0x0980,  0x09FF,  "bn"),
    # Gujarati → gu
    (0x0A80,  0x0AFF,  "gu"),
    # Gurmukhi (Punjabi) → pa
    (0x0A00,  0x0A7F,  "pa"),
    # Oriya → or
    (0x0B00,  0x0B7F,  "or"),
    # Sinhala → si
    (0x0D80,  0x0DFF,  "si"),
    # Thai → th
    (0x0E00,  0x0E7F,  "th"),
    # Lao → lo
    (0x0E80,  0x0EFF,  "lo"),
    # Myanmar → my
    (0x1000,  0x109F,  "my"),
    # Khmer → km
    (0x1780,  0x17FF,  "km"),
    # Cyrillic → ru (default; disambiguation done later)
    (0x0400,  0x04FF,  "ru"),
    (0x0500,  0x052F,  "ru"),
    # Greek → el
    (0x0370,  0x03FF,  "el"),
    (0x1F00,  0x1FFF,  "el"),
    # Georgian → ka
    (0x10A0,  0x10FF,  "ka"),
    # Armenian → hy
    (0x0530,  0x058F,  "hy"),
    # Ethiopic → am (Amharic default)
    (0x1200,  0x137F,  "am"),
]


def _codepoint_script(cp: int) -> str | None:
    """Return a language code if codepoint belongs to a known non-Latin script."""
    for start, end, lang in SCRIPT_RANGES:
        if start <= cp <= end:
            return lang
    return None


def dominant_script(text: str) -> str | None:
    """
    Return the dominant non-Latin script language code for the text,
    or None if the text is predominantly Latin / ASCII.
    
    Uses majority vote over all codepoints.
    """
    if not text.strip():
        return None
    counts: dict[str, int] = {}
    latin_count = 0
    for ch in text:
        cp = ord(ch)
        lang = _codepoint_script(cp)
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
        elif ch.isalpha():
            latin_count += 1

    if not counts:
        return None
    best_lang = max(counts, key=lambda k: counts[k])
    best_count = counts[best_lang]
    total_alpha = best_count + latin_count
    if total_alpha == 0:
        return None
    # Only claim non-Latin if it's clearly dominant (> 40% of alpha chars)
    if best_count / total_alpha >= 0.40:
        return best_lang
    return None


def is_rtl_script(lang_code: str) -> bool:
    """True if the language is written right-to-left."""
    return lang_code in {"ar", "he", "fa", "ur", "ps", "yi", "dv"}


def split_by_script(text: str) -> list[tuple[str, str | None]]:
    """
    Split *text* into contiguous runs that share the same Unicode script class.
    Returns list of (token_text, lang_or_None) where lang_or_None is set only
    for clearly non-Latin tokens; Latin/ASCII tokens get None.
    """
    if not text:
        return []

    runs: list[tuple[str, str | None]] = []
    current_chars: list[str] = []
    current_lang: str | None = None

    for ch in text:
        cp = ord(ch)
        ch_lang = _codepoint_script(cp)

        # Non-alpha (spaces, punctuation, digits) — keep with current run
        if not ch.isalpha():
            current_chars.append(ch)
            continue

        if ch_lang != current_lang:
            # Flush current run
            if current_chars:
                runs.append(("".join(current_chars), current_lang))
            current_chars = [ch]
            current_lang = ch_lang
        else:
            current_chars.append(ch)

    if current_chars:
        runs.append(("".join(current_chars), current_lang))

    return runs
