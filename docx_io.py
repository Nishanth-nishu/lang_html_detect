"""
docx_io.py — Word Document I/O for the Foreign Language Identifier.

Read paragraphs from a .docx file, annotate them with language detection,
and write a new .docx containing ONLY the foreign-language snippets.

Non-foreign text is removed. 
Output font size is set to 8pt (regardless of input size).
No color highlighting is used.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import List, Tuple

# Output font size in half-points (16 = 8pt)
_OUTPUT_FONT_SIZE_HP = 16 

# ---------------------------------------------------------------------------
# Word-namespace helpers (python-docx internals)
# ---------------------------------------------------------------------------
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = "{%s}" % _W_NS

# ---------------------------------------------------------------------------
# XML tag parser — turns annotate() output into (text, lang|None) spans
# ---------------------------------------------------------------------------
_TAG_RE = re.compile(r'<lang xml:lang="([^"]+)">(.*?)</lang>', re.DOTALL)


def _parse_annotated(annotated: str) -> List[Tuple[str, str | None]]:
    """
    Parse the XML-annotated string from annotate() into a flat list of
    (text_fragment, lang_or_None) tuples.
    """
    result: List[Tuple[str, str | None]] = []
    pos = 0
    for m in _TAG_RE.finditer(annotated):
        if m.start() > pos:
            result.append((annotated[pos:m.start()], None))
        result.append((m.group(2), m.group(1)))
        pos = m.end()
    if pos < len(annotated):
        result.append((annotated[pos:], None))
    return result


# ---------------------------------------------------------------------------
# Public API: read_docx
# ---------------------------------------------------------------------------

def read_docx(path: str | Path) -> List[Tuple[int, str]]:
    """
    Read all paragraphs from a Word document.
    """
    from docx import Document 

    doc = Document(str(path))
    return [(i, para.text) for i, para in enumerate(doc.paragraphs)]


# ---------------------------------------------------------------------------
# Public API: write_annotated_docx
# ---------------------------------------------------------------------------

def write_annotated_docx(
    input_path: str | Path,
    output_path: str | Path,
    annotated_paragraphs: List[Tuple[int, str]],
) -> None:
    """
    Copy the input .docx structure but rewrite the body so it contains
    ONLY the language-tagged snippets at 8pt font, with no colors.
    """
    from docx import Document
    from docx.oxml import OxmlElement
    import lxml.etree as etree

    doc = Document(str(input_path))
    annotation_map: dict[int, str] = {idx: xml for idx, xml in annotated_paragraphs}
    body = doc.element.body
    para_elems = [child for child in body if child.tag == _W + "p"]

    # Process paragraphs
    for para_idx, para_elem in enumerate(para_elems):
        if para_idx not in annotation_map:
            # If not in map (skipped), clear it or leave it? 
            # "Only tagged contains will be retained" suggests clearing untagged paras.
            for child in list(para_elem):
                if child.tag.split("}")[-1] != "pPr":
                    para_elem.remove(child)
            continue

        annotated = annotation_map[para_idx]
        spans = _parse_annotated(annotated)
        
        # Filter: only keep foreign (tagged) spans
        foreign_spans = [(t, l) for t, l in spans if l is not None]

        # Clear existing runs
        for child in list(para_elem):
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag not in ("pPr",):
                para_elem.remove(child)

        if not foreign_spans:
            # Paragraph has no foreign content -> effectively becomes empty
            continue

        # Re-add ONLY foreign runs
        # We need to keep some spacing between them if they were separate? 
        # But user said "only tagged contains will be retained".
        for i, (text_frag, lang) in enumerate(foreign_spans):
            if not text_frag:
                continue

            run_elem = OxmlElement("w:r")
            rpr = OxmlElement("w:rPr")

            # Set font size to 8pt (half-points = 16)
            sz = OxmlElement("w:sz")
            sz.set(_W + "val", str(_OUTPUT_FONT_SIZE_HP))
            rpr.append(sz)
            szCs = OxmlElement("w:szCs")
            szCs.set(_W + "val", str(_OUTPUT_FONT_SIZE_HP))
            rpr.append(szCs)

            # Ensure color is black or automatic (remove any existing color)
            # Actually, by creating new rPr we are clean.

            run_elem.append(rpr)

            t_elem = OxmlElement("w:t")
            t_elem.text = text_frag
            t_elem.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            run_elem.append(t_elem)
            
            para_elem.append(run_elem)
            
            # Add a separator if multiple spans
            if i < len(foreign_spans) - 1:
                sep_run = OxmlElement("w:r")
                sep_t = OxmlElement("w:t")
                sep_t.text = " | "
                sep_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                sep_run.append(sep_t)
                para_elem.append(sep_run)

    # Note: We are NOT adding the annotation note paragraph as it was unrequested 
    # and might clutter the "tagged contents only" output.

    doc.save(str(output_path))


def process_docx(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    """
    High-level function: read input_path, annotate every paragraph,
    write annotated output_path.
    """
    from annotator.tagger import annotate 

    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_name(
            input_path.stem + "_extracted" + input_path.suffix
        )
    output_path = Path(output_path)

    paragraphs = read_docx(input_path)
    annotated = [(idx, annotate(text)) for idx, text in paragraphs]
    write_annotated_docx(input_path, output_path, annotated)
    return output_path
