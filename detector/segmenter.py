"""
Text segmenter: splits mixed-language text into labelled spans.

Strategy:
  1. Walk the text character-by-character, grouping into Unicode-script runs.
  2. For Latin segments, further split by sentence boundaries.
  3. Detect language of each span.
  4. Merge adjacent spans that share the same detected language.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from detector.unicode_script import split_by_script, dominant_script
from detector.lang_detector import get_detector


@dataclass
class LangSpan:
    text: str
    lang: str | None          # ISO 639-1, or None for English / unknown
    start: int = 0
    end: int = 0


# Sentence-ending punctuation (greedy split for Latin blocks)
_SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')

# A "word" token — for inline word-level detection
_WORD_RE = re.compile(r'\S+')


def _detect_latin_block(text: str) -> list[LangSpan]:
    """
    Detect language in a Latin-script text block.
    First tries Lingua's multi-language span detection;
    falls back to sentence-level then word-level detection.
    """
    detector = get_detector()

    # Try Lingua multi-language span detection directly
    spans = detector.detect_spans(text)
    if spans:
        result: list[LangSpan] = []
        prev = 0
        for start, end, iso in spans:
            if start > prev:
                gap = text[prev:start]
                if gap.strip():
                    result.append(LangSpan(text=gap, lang=None))
                else:
                    result.append(LangSpan(text=gap, lang=None))
            chunk = text[start:end]
            result.append(LangSpan(text=chunk, lang=iso if iso != "en" else None))
            prev = end
        if prev < len(text):
            tail = text[prev:]
            result.append(LangSpan(text=tail, lang=None))
        return result

    # Fallback: sentence-level detection
    sentences = _SENT_SPLIT_RE.split(text)
    if len(sentences) > 1:
        result = []
        remaining = text
        for sent in sentences:
            lang, conf = detector.detect(sent)
            result.append(LangSpan(text=sent, lang=lang if lang != "en" else None))
            # Append the separator that was consumed
            after = len(sent)
            if remaining[after:after+1] in (' ', '\n', '\t'):
                result.append(LangSpan(text=remaining[after:after+1], lang=None))
                remaining = remaining[after+1:]
            else:
                remaining = remaining[after:]
        return result

    # Single-sentence block: whole-block detection
    lang, conf = detector.detect(text)
    return [LangSpan(text=text, lang=lang if lang != "en" else None)]


def _detect_word_level(text: str) -> list[LangSpan]:
    """
    Word-level detection for a mixed inline block.
    Used when the block contains both script-classified and Latin tokens.
    """
    result: list[LangSpan] = []
    pos = 0
    detector = get_detector()
    for m in _WORD_RE.finditer(text):
        # Add any whitespace before this word
        if m.start() > pos:
            result.append(LangSpan(text=text[pos:m.start()], lang=None))
        word = m.group()
        # Script check first
        script_lang = dominant_script(word)
        if script_lang:
            result.append(LangSpan(text=word, lang=script_lang))
        else:
            lang, conf = detector.detect(word)
            result.append(LangSpan(text=word, lang=lang if lang != "en" else None))
        pos = m.end()
    if pos < len(text):
        result.append(LangSpan(text=text[pos:], lang=None))
    return result


def _merge_adjacent(spans: list[LangSpan]) -> list[LangSpan]:
    """Merge consecutive spans that share the same language code."""
    if not spans:
        return []
    merged = [LangSpan(text=spans[0].text, lang=spans[0].lang)]
    for sp in spans[1:]:
        last = merged[-1]
        if sp.lang == last.lang:
            last.text += sp.text
        else:
            merged.append(LangSpan(text=sp.text, lang=sp.lang))
    return merged


def segment(text: str) -> list[LangSpan]:
    """
    Main entry point. Split *text* into language-labelled spans.
    Returns a list of LangSpan objects whose .text fields concatenate
    to exactly reproduce the original text.
    """
    if not text:
        return []

    # 1. Split by Unicode script
    script_runs = split_by_script(text)

    result: list[LangSpan] = []
    for (chunk, base_lang) in script_runs:
        if not chunk:
            continue
        if base_lang is not None:
            # Non-Latin script — script heuristic already gave us the language.
            # But if the chunk has mixed word characters, do word-level.
            result.append(LangSpan(text=chunk, lang=base_lang))
        else:
            # Latin or ASCII — needs linguistic detection
            # Heuristic: if chunk contains non-ASCII Latin chars mixed with pure ASCII,
            # try word-level detection for inline words; otherwise sentence-level.
            has_mixed_scripts = any(ord(c) > 0x024F for c in chunk if c.isalpha())
            if has_mixed_scripts:
                result.extend(_detect_word_level(chunk))
            else:
                result.extend(_detect_latin_block(chunk))

    # 2. Merge adjacent same-language spans
    merged = _merge_adjacent(result)

    # 3. Assign character offsets
    pos = 0
    for sp in merged:
        sp.start = pos
        sp.end = pos + len(sp.text)
        pos = sp.end

    return merged
