#!/usr/bin/env python3
"""
main.py — CLI entrypoint for the Foreign Language Identifier.

Works both as a normal Python script AND as a PyInstaller-bundled executable.

Usage:
  python3 main.py                 # all 11 built-in samples
  python3 main.py --sample 4     # one sample
  python3 main.py --text "..."   # inline text
  python3 main.py --input FILE   # your own file
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Identify foreign languages in a manuscript and annotate with <lang> tags.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  lang_detect                          Process all 11 built-in samples
  lang_detect --sample 4              Process sample 4 only
  lang_detect --text "Merci, Gracias" Annotate inline text
  lang_detect --input myfile.txt      Process your own file
        """,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text", "-t", help="Inline text to annotate")
    group.add_argument("--input", "-i", help="Path to an input text file")
    group.add_argument("--sample", "-s", type=int, metavar="N",
                       help="Process one of the 11 built-in samples (1-11)")
    args = parser.parse_args()

    if args.text:
        print(annotate(args.text))
    elif args.input:
        path = Path(args.input)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
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
