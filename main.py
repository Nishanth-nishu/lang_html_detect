#!/usr/bin/env python3
"""
main.py — CLI entrypoint for the Foreign Language Identifier.

Usage:
  python main.py                          # Process all 11 bundled samples
  python main.py --input FILE             # Process a file (one sample per line)
  python main.py --text "Hello, Merci"    # Process a single text string
  python main.py --sample 4              # Process one of the 11 built-in samples
"""

import argparse
import sys
from pathlib import Path

# Make sure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from annotator.tagger import annotate


SAMPLES_FILE = Path(__file__).parent / "samples" / "input_samples.txt"


def load_samples(path: Path) -> dict[str, str]:
    """Parse a samples file into {label: text} dict."""
    samples: dict[str, str] = {}
    current_label: str | None = None
    current_lines: list[str] = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip("\n")
            # Detect "Sample N:" header lines
            if stripped.startswith("Sample "):
                if current_label and current_lines:
                    samples[current_label] = "\n".join(current_lines).strip()
                current_label = stripped.rstrip(":")
                current_lines = []
            else:
                current_lines.append(stripped)

    if current_label and current_lines:
        samples[current_label] = "\n".join(current_lines).strip()

    return samples


def process_and_print(label: str, text: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    print("[INPUT]")
    print(text)
    print("\n[OUTPUT]")
    result = annotate(text)
    print(result)


def main():
    parser = argparse.ArgumentParser(
        description="Identify foreign languages in a manuscript and annotate with <lang> tags."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text", "-t", type=str, help="Inline text to annotate")
    group.add_argument("--input", "-i", type=str, help="Path to input file (one sample per line)")
    group.add_argument("--sample", "-s", type=int, help="Process only sample N (1-11)")
    args = parser.parse_args()

    if args.text:
        result = annotate(args.text)
        print(result)

    elif args.input:
        path = Path(args.input)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        samples = load_samples(path)
        for label, text in samples.items():
            process_and_print(label, text)

    elif args.sample:
        samples = load_samples(SAMPLES_FILE)
        key = f"Sample {args.sample}"
        if key not in samples:
            print(f"Error: '{key}' not found. Available: {list(samples.keys())}", file=sys.stderr)
            sys.exit(1)
        process_and_print(key, samples[key])

    else:
        # Default: process all 11 built-in samples
        samples = load_samples(SAMPLES_FILE)
        for label, text in samples.items():
            process_and_print(label, text)


if __name__ == "__main__":
    main()
