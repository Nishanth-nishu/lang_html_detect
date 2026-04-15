import string

def tag_spans(spans):
    """
    Wraps language spans in <lang xml:lang="...">...</lang> tags.
    """
    return _tag_spans_generic(spans, lambda lang, text: f"<lang xml:lang=\"{lang}\">{text}</lang>")

def tag_spans_html(spans):
    """
    Wraps language spans in <span class="lang-span" data-lang="...">...</span> tags.
    """
    return _tag_spans_generic(spans, lambda lang, text: f"<span class=\"lang-span\" data-lang=\"{lang}\">{text}</span>")

def _tag_spans_generic(spans, tag_func):
    output = []
    # Western scripts where final punctuation often goes outside
    WESTERN_TAGS = {"en", "es", "de", "fr", "it", "pt", "sv", "fi", "ru", "tr", "pl", "cs", "hu", "hr", "sr", "sl", "lt", "lv", "et", "sq", "ro", "bg", "uk", "be", "mk", "el", "cy", "ga", "eu", "la"}
    
    for span in spans:
        if span.lang:
            text = span.text
            # Identify surrounding punctuation for Western languages
            if span.lang in WESTERN_TAGS:
                l_pun = ""
                r_pun = ""
                
                # Strip leading punctuation/whitespace
                while text and text[0] in (string.whitespace + string.punctuation + "“”‘’"):
                     l_pun += text[0]
                     text = text[1:]
                
                # Strip trailing punctuation/whitespace
                while text and text[-1] in (string.whitespace + string.punctuation + "“”‘’"):
                     r_pun = text[-1] + r_pun
                     text = text[:-1]
                
                if text:
                    output.append(f"{l_pun}{tag_func(span.lang, text)}{r_pun}")
                else:
                    output.append(l_pun + r_pun)
            else:
                # For non-Western (CJK, Indic, Arabic, Hebrew), keep internal punctuation
                # But remove extra surrounding spaces
                l_space = ""
                r_space = ""
                while text and text[0].isspace():
                    l_space += text[0]
                    text = text[1:]
                while text and text[-1].isspace():
                    r_space = text[-1] + r_space
                    text = text[:-1]
                
                if text:
                    output.append(f"{l_space}{tag_func(span.lang, text)}{r_space}")
                else:
                    output.append(l_space + r_space)
        else:
            output.append(span.text)
    return "".join(output)

from detector.segmenter import segment

def annotate(text):
    """
    Convenience function for CLI: segments then tags.
    """
    spans = segment(text)
    return tag_spans(spans)

def annotate_html(text):
    """
    Convenience function for Web/HTML: segments then tags with HTML spans.
    """
    spans = segment(text)
    return tag_spans_html(spans)

