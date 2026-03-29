#!/usr/bin/env python3
"""
app.py — Flask web UI for the Foreign Language Identifier.

Run:  python app.py
Open: http://localhost:5000
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, request, jsonify
from annotator.tagger import annotate, annotate_html

app = Flask(__name__)

# Pre-load all 11 samples for the frontend sample loader
SAMPLES_FILE = Path(__file__).parent / "samples" / "input_samples.txt"


def _load_samples() -> dict[str, str]:
    samples: dict[str, str] = {}
    current_label: str | None = None
    current_lines: list[str] = []
    with open(SAMPLES_FILE, encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip("\n")
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


SAMPLES = _load_samples()


@app.route("/")
def index():
    return render_template("index.html", samples=SAMPLES)


@app.route("/annotate", methods=["POST"])
def annotate_endpoint():
    data = request.get_json(force=True)
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"xml": "", "html": "", "error": "No text provided."})
    xml_out = annotate(text)
    html_out = annotate_html(text)
    return jsonify({"xml": xml_out, "html": html_out})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
