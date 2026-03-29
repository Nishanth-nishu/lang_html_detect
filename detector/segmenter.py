"""
Text segmenter: splits mixed-language text into labelled LangSpan objects.

Strategy per Latin block:
  1. Sentence-split, then detect each sentence.
  2. Skip short all-ASCII words without diacritics in word-level mode
     (prevents romanised transliterations like 'Pahaad', 'Jabal' from being
     falsely tagged as foreign languages).
  3. Never call detect_multiple_languages_of() — too many false spans.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from detector.unicode_script import split_by_script, dominant_script
from detector.lang_detector import get_detector

# Sentence boundary — split after . ! ? ; : followed by whitespace
_SENT_RE = re.compile(r'(?<=[.!?\\;:])\s+')
# Word token
_WORD_RE = re.compile(r'\S+')
# Has at least one non-ASCII alphabetic char (diacritic, etc.)
_HAS_DIACRITIC = re.compile(r'[^\x00-\x7F]')


@dataclass
class LangSpan:
    text: str
    lang: str | None
    start: int = 0
    end: int = 0


# Common English words/language names that should not be tagged as foreign
_LANG_NAMES_EN = {
    "hindi", "spanish", "arabic", "japanese", "chinese", "tamil", "french", 
    "german", "italian", "portuguese", "russian", "korean", "english"
}


def _is_likely_transliteration(word: str) -> bool:
    """
    Revised heuristic: all-ASCII, short, and NO diacritics.
    We also skip words that are common language names in English.
    """
    w = word.lower().strip(",.()\"'")
    if w in _LANG_NAMES_EN:
        return True
    
    if not word.isascii() or _HAS_DIACRITIC.search(word):
        return False
    
    # Short ASCII word → likely transliteration or English
    if len(word) <= 7:
        return True
    return False


# Regex to match leading "Language Name: " or "Script Name (Transliteration): " headers
_HEADER_RE = re.compile(r'^([A-Z][a-z]+(\s+[A-Z][a-z]+)*[:\s(]+(\([A-Z][a-z/]+\):\s+)?)+', re.UNICODE)

def _detect_block(text: str) -> list[LangSpan]:
    detector = get_detector()
    text_stripped = text.strip()
    if not text_stripped or not any(c.isalpha() for c in text_stripped):
        return [LangSpan(text=text, lang=None)]

    # ALWAYS split by sentence first for Latin blocks to handle mixed-language blocks correctly
    sentences = _SENT_RE.split(text)
    result = []
    remaining = text
    
    for sent in sentences:
        if not sent.strip():
            continue
        idx = remaining.find(sent)
        if idx > 0:
            result.append(LangSpan(text=remaining[:idx], lang=None))
        
        s_lang, s_conf = detector.detect(sent)
        
        # Heuristic: if sentence is strongly detected as foreign, label it.
        # But skip if it's just a common English word or very short.
        if s_lang and s_lang != "en" and s_conf > 0.4:
            # Check for English headers like "Spanish: "
            m = _HEADER_RE.match(sent)
            if m:
                header = m.group()
                content = sent[len(header):]
                if header.strip():
                    result.append(LangSpan(text=header, lang=None))
                if content.strip():
                    # Recurse on content or just detect
                    c_lang, c_conf = detector.detect(content)
                    result.append(LangSpan(text=content, lang=c_lang if (c_lang and c_lang != "en" and c_conf > 0.5) else None))
            else:
                result.append(LangSpan(text=sent, lang=s_lang))
        else:
            result.append(LangSpan(text=sent, lang=None))
            
        remaining = remaining[idx + len(sent):]
    
    if remaining:
        result.append(LangSpan(text=remaining, lang=None))
    return result


def _detect_word_level(text: str) -> list[LangSpan]:
    detector = get_detector()
    result: list[LangSpan] = []
    pos = 0

    for m in _WORD_RE.finditer(text):
        word = m.group()
        if m.start() > pos:
            result.append(LangSpan(text=text[pos:m.start()], lang=None))

        script_lang = dominant_script(word)
        if script_lang:
            # Words in non-Latin scripts are ALWAYS tagged
            result.append(LangSpan(text=word, lang=script_lang))
        elif _is_likely_transliteration(word):
            result.append(LangSpan(text=word, lang=None))
        else:
            lang, conf = detector.detect(word)
            # Be extremely conservative for single words in mixed blocks
            result.append(LangSpan(text=word, lang=lang if (lang and lang != "en" and conf > 0.8) else None))

        pos = m.end()

    if pos < len(text):
        result.append(LangSpan(text=text[pos:], lang=None))
    return result


def _merge_adjacent(spans: list[LangSpan]) -> list[LangSpan]:
    """
    Greedily merge spans of the same language, absorbing all intermediate
    neutral characters. Prevents fragmented tags.
    """
    if not spans:
        return []
    
    current = spans
    while True:
        changed = False
        new_spans = []
        i = 0
        while i < len(current):
            c = current[i]
            # Greedy lookahead for Lang(A) + (Neutral)* + Lang(A)
            if c.lang is not None:
                j = i + 1
                neutral_acc = ""
                while j < len(current):
                    mid = current[j]
                    if mid.lang is None and not any(ch.isalpha() for ch in mid.text):
                        neutral_acc += mid.text
                        j += 1
                    elif mid.lang == c.lang:
                        # Found same language! Merge everything from i to j.
                        merged_text = c.text + neutral_acc + mid.text
                        c = LangSpan(text=merged_text, lang=c.lang)
                        i = j
                        changed = True
                        # Reset greedy search from new end
                        j = i + 1
                        neutral_acc = ""
                    else:
                        break
            
            # Simple identity merge for adjacent identical labels
            if i + 1 < len(current) and c.lang == current[i+1].lang:
                c = LangSpan(text=c.text + current[i+1].text, lang=c.lang)
                i += 1
                changed = True

            new_spans.append(c)
            i += 1
        
        current = new_spans
        if not changed:
            break
            
    return current


def segment(text: str) -> list[LangSpan]:
    """
    Main entry point. Split *text* into language-labelled LangSpan objects.
    The .text fields of all returned spans concatenate to exactly reproduce
    the original text.
    """
    if not text:
        return []

    script_runs = split_by_script(text)
    result: list[LangSpan] = []

    for chunk, base_lang in script_runs:
        if not chunk:
            continue

        if base_lang is not None:
            # Non-Latin script — Unicode heuristic already classified it
            result.append(LangSpan(text=chunk, lang=base_lang))
        else:
            # Latin or neutral (punctuation / spaces)
            if not any(c.isalpha() for c in chunk):
                # Pure whitespace/punctuation — always neutral
                result.append(LangSpan(text=chunk, lang=None))
            elif any(ord(c) > 0x024F for c in chunk if c.isalpha()):
                # Has non-basic-Latin alpha chars — word-level detection
                result.extend(_detect_word_level(chunk))
            else:
                # Pure Latin — sentence-level detection
                result.extend(_detect_block(chunk))

    merged = _merge_adjacent(result)

    # Assign character offsets
    pos = 0
    for sp in merged:
        sp.start = pos
        sp.end = pos + len(sp.text)
        pos = sp.end

    return merged
