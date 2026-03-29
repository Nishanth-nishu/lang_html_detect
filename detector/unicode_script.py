"""
Unicode script detection utilities.
Determines script of a character or string to separate non-Latin blocks.
"""

from __future__ import annotations
import unicodedata

# Map major script names (from Unicode data) to likely ISO 639-1 languages.
SCRIPT_TO_LANG = {
    "ARABIC": "ar",
    "HEBREW": "he",
    "CYRILLIC": "ru",
    "HAN": "zh",
    "HIRAGANA": "ja",
    "KATAKANA": "ja",
    "HANGUL": "ko",
    "DEVANAGARI": "hi",
    "TAMIL": "ta",
    "BENGALI": "bn",
    "GURMUKHI": "pa",
    "TELUGU": "te",
    "KANNADA": "kn",
    "MALAYALAM": "ml",
    "GUJARATI": "gu",
    "ORIYA": "or",
    "SINHALA": "si",
    "THAI": "th",
    "MYANMAR": "my",
    "KHMER": "km",
    "LAO": "lo",
    "GEORGIAN": "ka",
    "ARMENIAN": "hy",
    "GREEK": "el",
}

def get_script(char: str) -> str:
    """
    Returns the Unicode script name for a character.
    """
    try:
        name = unicodedata.name(char)
        if unicodedata.category(char).startswith('M'):
            return "COMBINING"
        
        for s in SCRIPT_TO_LANG:
            if s in name:
                return s
        
        if "LATIN" in name:
            return "LATIN"
        
        return "NEUTRAL"
    except ValueError:
        return "NEUTRAL"

def dominant_script(text: str) -> str | None:
    """
    Returns the ISO lang code for the dominant non-Latin script in the text.
    """
    counts: dict[str, int] = {}
    for char in text:
        script = get_script(char)
        if script not in ["LATIN", "NEUTRAL", "COMBINING"]:
            counts[script] = counts.get(script, 0) + 1
    
    if not counts:
        return None
    
    best_script = max(counts, key=counts.get)
    return SCRIPT_TO_LANG.get(best_script)

def split_by_script(text: str) -> list[tuple[str, str | None]]:
    """
    Splits text into spans of consistent script.
    Continuous NON-LATIN scripts are grouped as "NON_LATIN".
    """
    if not text:
        return []
        
    spans: list[tuple[str, str | None]] = []
    current_chunk = []
    current_is_latin = None
    
    for char in text:
        script = get_script(char)
        
        if script == "COMBINING":
            current_chunk.append(char)
            continue
            
        is_latin = (script in ["LATIN", "NEUTRAL"])

        if script == "NEUTRAL":
             # Neutral stays with current block type
             current_chunk.append(char)
        elif is_latin == current_is_latin:
             current_chunk.append(char)
        else:
            if current_chunk:
                spans.append(("".join(current_chunk), "LATIN" if current_is_latin else "NON_LATIN"))
            current_chunk = [char]
            current_is_latin = is_latin
            
    if current_chunk:
        spans.append(("".join(current_chunk), "LATIN" if current_is_latin else "NON_LATIN"))
        
    # Mapping back to likely lang for NON_LATIN blocks
    result = []
    for chunk_text, block_type in spans:
        if block_type == "NON_LATIN":
             result.append((chunk_text, dominant_script(chunk_text)))
        else:
             result.append((chunk_text, None))
             
    return _merge_adjacent_scripts(result)

def _merge_adjacent_scripts(spans: list[tuple[str, str | None]]) -> list[tuple[str, str | None]]:
    if not spans: return []
    merged = []
    i = 0
    while i < len(spans):
        text, lang = spans[i]
        if lang is not None:
            j = i + 1
            while j < len(spans):
                next_text, next_lang = spans[j]
                # Merge if next is Neutral-only OR if next is SAME lang
                if next_lang is None and all(get_script(c) == "NEUTRAL" for c in next_text):
                    if j + 1 < len(spans) and spans[j+1][1] == lang:
                        text += next_text + spans[j+1][0]
                        j += 2
                    else:
                        break
                elif next_lang == lang:
                    text += next_text
                    j += 1
                else:
                    break
            merged.append((text, lang))
            i = j
        else:
            merged.append((text, lang))
            i += 1
    return merged
