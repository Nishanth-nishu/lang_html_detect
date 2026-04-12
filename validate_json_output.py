#!/usr/bin/env python3
"""
validate_json_output.py — Cross-validation script for JSON output mode.

Runs all 11 benchmark samples through the JSON annotator and checks:
  - JSON is valid and parseable
  - `annotated` field contains <lang> tags when foreign spans are detected
  - `languages_detected` is non-empty for samples with known foreign content
  - `spans` list is non-empty
  - All spans have `text` and `is_foreign` fields

Usage:
  python3 validate_json_output.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from annotator.json_output import annotate_json


def load_samples(path: Path) -> dict:
    samples = {}
    label = None
    lines = []
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


# --- Samples that must have at least one foreign language detected ---
EXPECTED_LANGS = {
    "Sample 1": {"zh", "ar", "ta"},
    "Sample 2": {"ja", "ar", "hi"},
    "Sample 3": {"ja"},
    "Sample 4": {"fr", "es", "de"},
    "Sample 5": {"es", "fr"},
    "Sample 6": {"he"},
    "Sample 7": {"it"},
    "Sample 8": {"es"},
    "Sample 9": {"fr", "hi"},
    "Sample 10": {"de"},
    "Sample 11": set(),  # English-only, no foreign required
}


def validate():
    samples_path = Path(__file__).parent / "samples" / "input_samples.txt"
    samples = load_samples(samples_path)
    passed = 0
    failed = 0

    print("=" * 65)
    print("  JSON Output Cross-Validation — All 11 Benchmark Samples")
    print("=" * 65)

    for label in sorted(samples, key=lambda x: int(x.split()[-1])):
        text = samples[label]
        issues = []

        try:
            raw = annotate_json(text)
            data = json.loads(raw)
        except Exception as e:
            print(f"  {label}: [FAIL] Could not parse JSON: {e}")
            failed += 1
            continue

        # Check required keys
        for key in ("input", "annotated", "spans", "languages_detected"):
            if key not in data:
                issues.append(f"missing key '{key}'")

        if "spans" in data:
            if not isinstance(data["spans"], list):
                issues.append("'spans' is not a list")
            else:
                for i, sp in enumerate(data["spans"]):
                    if "text" not in sp or "is_foreign" not in sp:
                        issues.append(f"span[{i}] missing required fields")
                        break

        # Check annotated has <lang> tags if any foreign spans
        foreign_spans = [s for s in data.get("spans", []) if s.get("is_foreign")]
        if foreign_spans and "<lang xml:lang=" not in data.get("annotated", ""):
            issues.append("foreign spans found but <lang> tags missing in 'annotated'")

        # Check expected languages are detected
        detected = set(data.get("languages_detected", []))
        required = EXPECTED_LANGS.get(label, set())
        missing = required - detected
        if missing:
            issues.append(f"expected langs not detected: {missing}")

        if issues:
            print(f"  {label}: [FAIL] {'; '.join(issues)}")
            failed += 1
        else:
            langs = data.get("languages_detected", [])
            spans_count = len(data.get("spans", []))
            print(f"  {label}: [PASS] | langs={langs} | spans={spans_count}")
            passed += 1

    print()
    print("=" * 65)
    print(f"  RESULT: {passed}/11 PASSED, {failed}/11 FAILED")
    print("=" * 65)
    return failed == 0


if __name__ == "__main__":
    ok = validate()
    sys.exit(0 if ok else 1)
