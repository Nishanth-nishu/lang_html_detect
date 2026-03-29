"""
Unicode script heuristics for instant language pre-classification.

Key improvements:
- Non-alpha chars (spaces, punctuation) emitted as SEPARATE neutral runs
  so they never end up inside <lang> tags
- CJK (zh) runs adjacent to Hiragana/Katakana (ja) runs are reclassified as ja
"""
import unicodedata
import re

SCRIPT_RANGES = [
    (0x4E00,  0x9FFF,  "zh"), (0x3400,  0x4DBF,  "zh"),
    (0x20000, 0x2A6DF, "zh"), (0x2A700, 0x2B73F, "zh"),
    (0x2B740, 0x2B81F, "zh"), (0x2B820, 0x2CEAF, "zh"),
    (0xF900,  0xFAFF,  "zh"),
    # Hiragana / Katakana → Japanese (ja)
    (0x3040,  0x309F,  "ja"), (0x30A0,  0x30FF,  "ja"),
    (0x31F0,  0x31FF,  "ja"), (0x3200,  0x32FF,  "ja"),
    # Hangul → Korean (ko)
    (0xAC00,  0xD7AF,  "ko"), (0x1100,  0x11FF,  "ko"),
    (0x3130,  0x318F,  "ko"), (0xA960,  0xA97F,  "ko"),
    (0xD7B0,  0xD7FF,  "ko"),
    # Arabic (ar)
    (0x0600,  0x06FF,  "ar"), (0x0750,  0x077F,  "ar"),
    (0xFB50,  0xFDFF,  "ar"), (0xFE70,  0xFEFF,  "ar"),
    # Hebrew (he)
    (0x0590,  0x05FF,  "he"), (0xFB1D,  0xFB4F,  "he"),
    # Devanagari (hi)
    (0x0900,  0x097F,  "hi"),
    # Tamil (ta)
    (0x0B80,  0x0BFF,  "ta"),
    # Telugu (te)
    (0x0C00,  0x0C7F,  "te"),
    # Kannada (kn)
    (0x0C80,  0x0CFF,  "kn"),
    # Malayalam (ml)
    (0x0D00,  0x0D7F,  "ml"),
    # Bengali (bn)
    (0x0980,  0x09FF,  "bn"),
    # Gujarati (gu)
    (0x0A80,  0x0AFF,  "gu"),
    # Gurmukhi / Punjabi (pa)
    (0x0A00,  0x0A7F,  "pa"),
    # Oriya (or)
    (0x0B00,  0x0B7F,  "or"),
    # Sinhala (si)
    (0x0D80,  0x0DFF,  "si"),
    # Thai (th)
    (0x0E00,  0x0E7F,  "th"),
    # Lao (lo)
    (0x0E80,  0x0EFF,  "lo"),
    # Myanmar (my)
    (0x1000,  0x109F,  "my"),
    # Khmer (km)
    (0x1780,  0x17FF,  "km"),
    # Cyrillic (ru default)
    (0x0400,  0x04FF,  "ru"), (0x0500,  0x052F,  "ru"),
    # Greek (el)
    (0x0370,  0x03FF,  "el"), (0x1F00,  0x1FFF,  "el"),
    # Georgian (ka)
    (0x10A0,  0x10FF,  "ka"),
    # Armenian (hy)
    (0x0530,  0x058F,  "hy"),
    # Ethiopic (am)
    (0x1200,  0x137F,  "am"),
]


def _codepoint_script(cp: int) -> str | None:
    for start, end, lang in SCRIPT_RANGES:
        if start <= cp <= end:
            return lang
    return None


def dominant_script(text: str) -> str | None:
    """
    Return the dominant non-Latin script language code for the text,
    or None if the text is predominantly Latin/ASCII.
    Japanese phonetic (Hiragana/Katakana) causes all CJK in the text to be
    reclassified as 'ja' rather than 'zh'.
    """
    if not text.strip():
        return None
    counts: dict[str, int] = {}
    latin_count = 0
    has_ja_phonetic = False

    for ch in text:
        cp = ord(ch)
        lang = _codepoint_script(cp)
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
            if lang == "ja":
                has_ja_phonetic = True
        elif ch.isalpha():
            latin_count += 1

    if not counts:
        return None

    # If Japanese phonetic characters exist, absorb all CJK into Japanese
    if has_ja_phonetic and "zh" in counts:
        counts["ja"] = counts.get("ja", 0) + counts.pop("zh")

    best_lang = max(counts, key=lambda k: counts[k])
    best_count = counts[best_lang]
    total_alpha = sum(counts.values()) + latin_count
    if total_alpha == 0:
        return None
    if best_count / total_alpha >= 0.40:
        return best_lang
    return None


def split_by_script(text: str) -> list[tuple[str, str | None]]:
    """
    Split *text* into contiguous runs sharing the same Unicode script class.
    Ensures strict boundaries between different scripts while keeping
    intra-script punctuation/marks together.
    """
    if not text:
        return []

    runs: list[tuple[str, str | None]] = []
    buf: list[str] = []
    current_lang: str | None = None

    def _flush():
        if buf:
            runs.append(("".join(buf), current_lang))
            buf.clear()

    for ch in text:
        cp = ord(ch)
        cat = unicodedata.category(ch)
        is_mark = cat.startswith('M')
        # Digits and symbols are also neutral
        is_neutral = not ch.isalpha() and not is_mark
        ch_lang = _codepoint_script(cp) if not is_neutral else None

        # Key logic: flush if script changes
        # (None is treated as its own 'Latin/Neutral' script run)
        if ch_lang != current_lang:
            # If changing from None to a script, or script to None, or script A to script B
            _flush()
            current_lang = ch_lang
        
        buf.append(ch)

    _flush()
    return _resolve_cjk_japanese(runs)


def _resolve_cjk_japanese(runs: list[tuple[str, str | None]]) -> list[tuple[str, str | None]]:
    """
    Japanese text often contains Kanji (zh script). If 'ja' (Hiragana/Katakana)
    is present nearby, the Kanji is almost certainly Japanese.
    """
    ja_indices = {i for i, (_, l) in enumerate(runs) if l == "ja"}
    if not ja_indices:
        return runs
    
    result = list(runs)
    # Check 10 positions around each zh run
    for i, (text, lang) in enumerate(runs):
        if lang == "zh":
            for ja_idx in ja_indices:
                if abs(i - ja_idx) <= 10:
                    result[i] = (text, "ja")
                    break
    return result


def is_rtl_script(lang_code: str) -> bool:
    return lang_code in {"ar", "he", "fa", "ur", "ps", "yi", "dv"}
