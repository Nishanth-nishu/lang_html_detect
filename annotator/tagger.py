import string

def tag_spans(spans):
    """
    Wraps language spans in <lang xml:lang="...">...</lang> tags.
    """
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
                    output.append(f"{l_pun}<lang xml:lang=\"{span.lang}\">{text}</lang>{r_pun}")
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
                    output.append(f"{l_space}<lang xml:lang=\"{span.lang}\">{text}</lang>{r_space}")
                else:
                    output.append(l_space + r_space)
        else:
            output.append(span.text)
    return "".join(output)
