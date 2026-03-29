"""
Annotator: wraps non-English language spans with <lang xml:lang="XX"> tags.

Fixes applied:
- Leading/trailing whitespace stripped from tag content and emitted outside
- Punctuation-only spans are never wrapped
"""

from __future__ import annotations
import re
from detector.segmenter import segment, LangSpan

# Matches leading whitespace
_LEAD_WS = re.compile(r'^(\s*)')
# Matches trailing whitespace
_TRAIL_WS = re.compile(r'(\s*)$')


def _wrap(text: str, lang: str) -> str:
    """
    Wrap *text* with <lang xml:lang="lang"> ... </lang>.
    Leading and trailing whitespace are moved OUTSIDE the tag.
    """
    lead = _LEAD_WS.match(text).group(1)
    tail = _TRAIL_WS.search(text).group(1)
    content = text[len(lead): len(text) - len(tail) if tail else len(text)]
    if not content or not any(c.isalpha() for c in content):
        return text          # nothing to wrap
    return f'{lead}<lang xml:lang="{lang}">{content}</lang>{tail}'


def annotate(text: str) -> str:
    """
    Detect all non-English language spans in *text* and wrap them with
    <lang xml:lang="XX">…</lang> tags.
    Adjacent same-language spans are merged into one tag.
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
    Same as annotate() but returns HTML with colour-coded <span> elements
    for browser display.
    """
    spans = segment(text)
    parts: list[str] = []
    for sp in spans:
        escaped = _html_escape(sp.text)
        if sp.lang and sp.lang != "en":
            lead = _LEAD_WS.match(escaped).group(1)
            tail = _TRAIL_WS.search(escaped).group(1)
            content = escaped[len(lead): len(escaped) - len(tail) if tail else len(escaped)]
            if content and any(c.isalpha() for c in sp.text):
                parts.append(
                    f'{lead}<span class="lang-span" data-lang="{sp.lang}" '
                    f'title="{sp.lang}">{content}</span>{tail}'
                )
            else:
                parts.append(escaped)
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
