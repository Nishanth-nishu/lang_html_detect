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

from annotator.tagger import annotate

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


def process(label: str, text: str) -> None:
    sep = "=" * 70
    print(f"\n{sep}\n  {label}\n{sep}")
    print("[INPUT]")
    print(text)
    print("\n[OUTPUT]")
    print(annotate(text))


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
        "              colour-highlighted foreign-language spans."
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
    args = parser.parse_args()

    if args.text:
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
                process(label, text)

    elif args.sample:
        samples = load_samples(SAMPLES_FILE)
        key = f"Sample {args.sample}"
        if key not in samples:
            print(f"Error: '{key}' not found.", file=sys.stderr)
            sys.exit(1)
        process(key, samples[key])

    else:
        samples = load_samples(SAMPLES_FILE)
        for label, text in samples.items():
            process(label, text)


if __name__ == "__main__":
    main()
