#!/usr/bin/env python3
"""
main.py — CLI entrypoint for the Foreign Language Identifier.

Works both as a normal Python script AND as a PyInstaller-bundled executable.

Usage:
  python3 main.py                          # all 11 built-in samples
  python3 main.py --sample 4              # one sample
  python3 main.py --text "..."            # inline text
  python3 main.py --input FILE.txt        # plain-text file (sample format)
  python3 main.py --input FILE.docx       # Word document → writes FILE_annotated.docx
  python3 main.py --input FILE.docx -o OUT.docx  # specify output path
  python3 main.py --json                  # output as JSON instead of plain annotated text
  python3 main.py --json --sample 1       # JSON output for a specific sample
"""

import argparse
import sys
import os
from pathlib import Path

# --- Resolve project root correctly whether running as script or PyInstaller exe ---
if getattr(sys, "frozen", False):
    # PyInstaller one-file bundle: _MEIPASS is the temp extraction dir
    _BASE = Path(sys._MEIPASS)
else:
    _BASE = Path(__file__).parent

sys.path.insert(0, str(_BASE))

from annotator.tagger import annotate, annotate_html
from annotator.json_output import annotate_json

SAMPLES_FILE = _BASE / "samples" / "input_samples.txt"


def load_samples(path: Path) -> dict[str, str]:
    samples: dict[str, str] = {}
    label: str | None = None
    lines: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.rstrip("\n")
            if s.startswith("Sample "):
                if label and lines:
                    samples[label] = "\n".join(lines).strip()
                label = s.rstrip(":")
                lines = []
            else:
                lines.append(s)
    if label and lines:
        samples[label] = "\n".join(lines).strip()
    return samples


def process(label: str, text: str, json_mode: bool = False) -> tuple[str, str]:
    sep = "=" * 70
    text_out = ""
    html_out = ""
    if json_mode:
        import json
        raw = annotate_json(text)
        data = json.loads(raw)
        data["sample"] = label
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        print(json_str)
        return json_str, f"<pre>{json_str}</pre>"
    else:
        text_out = f"\n{sep}\n  {label}\n{sep}\n[INPUT]\n{text}\n\n[OUTPUT]\n{annotate(text)}\n"
        print(text_out)
        html_out = f"<h3>{label}</h3><div style='white-space: pre-wrap; font-family: monospace;'>{annotate_html(text)}</div>"
        return text_out, html_out


def save_execution_report(results: list[tuple[str, str]]) -> None:
    """Consolidates results and saves to lang/_html/."""
    out_dir = Path("lang/_html")
    out_dir.mkdir(parents=True, exist_ok=True)

    full_text = "\n".join([r[0] for r in results])
    with open(out_dir / "execution_output.txt", "w", encoding="utf-8") as f:
        f.write(full_text)

    # Basic HTML wrapper with styles from the web UI
    styles = """
    <style>
        body { font-family: sans-serif; background: #0d1117; color: #e6edf3; padding: 2rem; }
        h3 { color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 0.5rem; }
        .lang-span { border-radius: 4px; padding: 1px 3px; position: relative; }
        .lang-span[data-lang="es"] { background: rgba(239,68,68,.20); color: #fca5a5; }
        .lang-span[data-lang="fr"] { background: rgba(59,130,246,.20); color: #93c5fd; }
        .lang-span[data-lang="de"] { background: rgba(234,179,8,.20);  color: #fde047; }
        .lang-span[data-lang="it"] { background: rgba(34,197,94,.20);  color: #86efac; }
        .lang-span[data-lang="zh"] { background: rgba(236,72,153,.20); color: #f9a8d4; }
        .lang-span[data-lang="ar"] { background: rgba(99,102,241,.20); color: #c7d2fe; }
        .lang-span[data-lang="ta"] { background: rgba(163,230,53,.20); color: #bef264; }
        .lang-span[data-lang="hi"] { background: rgba(251,146,60,.20); color: #fed7aa; }
        /* Add more as needed, or a catch-all */
        .lang-span { background: rgba(148,163,184,.15); color: #94a3b8; }
    </style>
    """
    full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'>{styles}</head><body>"
    full_html += "\n<hr>\n".join([r[1] for r in results])
    full_html += "</body></html>"

    with open(out_dir / "execution_output.html", "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"\n[info] Saved consolidated results to: {out_dir}/")


def _process_docx(input_path: Path, output_path: Path | None) -> None:
    """Run language annotation on an entire Word document."""
    try:
        from docx_io import process_docx
    except ImportError:
        print(
            "Error: python-docx is required for .docx processing.\n"
            "Install it with:  pip install python-docx",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[lang_detect] Reading: {input_path}")
    out = process_docx(input_path, output_path)
    print(f"[lang_detect] Wrote annotated document: {out}")
    print(
        "[lang_detect] Open the output file in Word / LibreOffice to see\n"
        "              inline <lang xml:lang=\"xx\"> annotations."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Identify foreign languages in a manuscript and annotate with <lang> tags.\n"
            "Supports plain-text files and Word documents (.docx)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  lang_detect                              Process all 11 built-in samples
  lang_detect --sample 4                  Process sample 4 only
  lang_detect --text "Merci, Gracias"     Annotate inline text
  lang_detect --input myfile.txt          Plain-text file (sample format)
  lang_detect --input myfile.docx         Word doc → myfile_annotated.docx
  lang_detect --input myfile.docx -o out.docx  Specify output path
        """,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text", "-t", help="Inline text to annotate")
    group.add_argument("--input", "-i", help="Path to an input file (.txt or .docx)")
    group.add_argument(
        "--sample", "-s", type=int, metavar="N",
        help="Process one of the 11 built-in samples (1-11)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output .docx path (only used when --input is a .docx file)",
    )
    parser.add_argument(
        "--json", "-j", action="store_true",
        help="Output in JSON format instead of plain annotated text",
    )
    args = parser.parse_args()

    results = []
    if args.text:
        if args.json:
            print(annotate_json(args.text))
        else:
            print(annotate(args.text))

    elif args.input:
        path = Path(args.input)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)

        if path.suffix.lower() == ".docx":
            out_path = Path(args.output) if args.output else None
            _process_docx(path, out_path)
        else:
            # Plain-text sample format
            if args.output:
                print(
                    "Warning: --output is only used with .docx input; ignoring.",
                    file=sys.stderr,
                )
            samples = load_samples(path)
            for label, text in samples.items():
                results.append(process(label, text, json_mode=args.json))
            save_execution_report(results)

    elif args.sample:
        samples = load_samples(SAMPLES_FILE)
        key = f"Sample {args.sample}"
        if key not in samples:
            print(f"Error: '{key}' not found.", file=sys.stderr)
            sys.exit(1)
        results.append(process(key, samples[key], json_mode=args.json))
        save_execution_report(results)

    else:
        samples = load_samples(SAMPLES_FILE)
        for label, text in samples.items():
            results.append(process(label, text, json_mode=args.json))
        save_execution_report(results)


if __name__ == "__main__":
    main()
