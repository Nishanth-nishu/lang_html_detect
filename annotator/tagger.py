"""
Tagger: wraps identified foreign ranges in <lang xml:lang="..."> tags.
Handles punctuation stripping to ensure tags wrap only the core text.
"""

from __future__ import annotations
from detector.segmenter import segment, LangSpan

def annotate(text: str) -> str:
    """
    Main entry point for tagging text.
    """
    spans = segment(text)
    result = []
    
    # We strip these characters from the edges of INLINE tags.
    # We include smart quotes and standard quotes.
    STRIP_CHARS = " ,.!?;:()\"'“”‘’"

    for span in spans:
        if span.lang:
            content = span.text
            
            if not span.is_block:
                # Strip leading/trailing punctuation and whitespace
                stripped = content.strip(STRIP_CHARS + " \n\r\t")
                if not stripped:
                    result.append(content)
                    continue
                
                idx = content.find(stripped)
                leading = content[:idx]
                trailing = content[idx + len(stripped):]
                
                result.append(f'{leading}<lang xml:lang="{span.lang}">{stripped}</lang>{trailing}')
            else:
                # For blocks (Chinese, Arabic, full sentences), we wrap the whole thing.
                # But we still want to strip OUTER whitespace.
                stripped = content.strip(" \n\r\t")
                leading = content[:content.find(stripped)]
                trailing = content[content.find(stripped) + len(stripped):]
                
                result.append(f'{leading}<lang xml:lang="{span.lang}">{stripped}</lang>{trailing}')
        else:
            result.append(span.text)
            
    return "".join(result)
