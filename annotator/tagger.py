"""
Annotator: wraps non-English language spans with <lang xml:lang="XX"> tags.
"""

from __future__ import annotations
import re
from detector.segmenter import segment, LangSpan


def _wrap(text: str, lang: str) -> str:
    return f'<lang xml:lang="{lang}">{text}</lang>'


def annotate(text: str) -> str:
    """
    Detect all non-English language spans in *text* and wrap them with
    <lang xml:lang="XX">…</lang> tags.

    - English and unknown spans are left untouched.
    - Adjacent spans of the same non-English language are merged into one tag.
    - Whitespace and punctuation outside language spans are preserved exactly.
    """
    spans = segment(text)
    parts: list[str] = []
    for sp in spans:
        if sp.lang and sp.lang != "en":
            parts.append(_wrap(sp.text, sp.lang))
        else:
            parts.append(sp.text)
    return "".join(parts)


def annotate_html(text: str) -> str:
    """
    Same as annotate() but returns an HTML string with colour-coded spans
    for browser display (uses <span> with data-lang attribute instead of
    <lang> so browsers render it correctly).
    """
    spans = segment(text)
    parts: list[str] = []
    for sp in spans:
        escaped = _html_escape(sp.text)
        if sp.lang and sp.lang != "en":
            parts.append(
                f'<span class="lang-span" data-lang="{sp.lang}" '
                f'title="{sp.lang}">{escaped}</span>'
            )
        else:
            parts.append(escaped)
    return "".join(parts)


def _html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
    )
