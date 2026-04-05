"""
docx_io.py — Word Document I/O for the Foreign Language Identifier.

Read paragraphs from a .docx file, annotate them with language detection,
and write a new .docx where each paragraph's text is replaced with
the full annotated XML string (e.g. <lang xml:lang="fr">Bonjour</lang>).

The output preserves the original document structure, headers, footers, etc.
Font size is preserved from the input (default 11pt).
No color highlighting — just the plain annotated text.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Word-namespace helpers
# ---------------------------------------------------------------------------
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = "{%s}" % _W_NS


# ---------------------------------------------------------------------------
# Public API: read_docx
# ---------------------------------------------------------------------------

def read_docx(path: str | Path) -> List[Tuple[int, str]]:
    """
    Read all paragraphs from a Word document.
    Returns list of (paragraph_index, paragraph_text).
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
    Copy the input .docx and replace each paragraph's text content
    with its annotated version (full text with inline <lang> tags).

    Font size and paragraph styles are preserved from the original.
    """
    from docx import Document
    from docx.oxml import OxmlElement
    import copy

    doc = Document(str(input_path))
    annotation_map: dict[int, str] = {idx: xml for idx, xml in annotated_paragraphs}
    body = doc.element.body
    para_elems = [child for child in body if child.tag == _W + "p"]

    for para_idx, para_elem in enumerate(para_elems):
        if para_idx not in annotation_map:
            continue

        annotated_text = annotation_map[para_idx]

        # --- Extract formatting from first existing run (if any) ---
        first_run = para_elem.find(_W + "r")
        base_rpr = None
        if first_run is not None:
            rpr_elem = first_run.find(_W + "rPr")
            if rpr_elem is not None:
                base_rpr = copy.deepcopy(rpr_elem)

        # --- Clear all existing runs (keep pPr paragraph properties) ---
        for child in list(para_elem):
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag not in ("pPr",):
                para_elem.remove(child)

        # --- Create a single new run with the full annotated text ---
        run_elem = OxmlElement("w:r")

        # Preserve original run properties (font, size, etc.)
        if base_rpr is not None:
            run_elem.append(copy.deepcopy(base_rpr))

        t_elem = OxmlElement("w:t")
        t_elem.text = annotated_text
        # Preserve leading/trailing whitespace
        t_elem.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        run_elem.append(t_elem)

        para_elem.append(run_elem)

    doc.save(str(output_path))


# ---------------------------------------------------------------------------
# Convenience: process an entire .docx end-to-end
# ---------------------------------------------------------------------------

def process_docx(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    """
    High-level function: read input_path, annotate every paragraph,
    write output_path with full annotated text.
    """
    from annotator.tagger import annotate

    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_name(
            input_path.stem + "_annotated" + input_path.suffix
        )
    output_path = Path(output_path)

    paragraphs = read_docx(input_path)
    annotated = [(idx, annotate(text)) for idx, text in paragraphs]
    write_annotated_docx(input_path, output_path, annotated)
    return output_path
