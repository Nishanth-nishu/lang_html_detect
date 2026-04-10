# lang_html_detect

AI-powered language identifier for manuscripts. Detects non-English language spans and annotates them with `<lang xml:lang="XX">…</lang>` tags — 100% free, local, no paid APIs.

Now available in both **Python** and **C# (.NET 8.0)**.

## Features
- Identifies 176+ languages in mixed-language text
- Word-level, phrase-level, and sentence-level detection
- Produces `<lang xml:lang="XX">…</lang>` XML annotations
- Supports `.docx` and `.txt` files
- Web UI (Python version) with highlight previews

## Architecture (Three-Layer Pipeline)

| Layer | Tool | Purpose |
|---|---|---|
| 1 | Unicode script heuristics | Instant: CJK→zh, Arabic→ar, Tamil→ta, Hebrew→he… |
| 2 | Lingua | High-accuracy detection for Latin scripts (Spanish, French, etc.) |
| 3 | fastText (Python) / Fallback | 176-language broad identification |

---

## 🐍 Python Version

### Installation
```bash
pip install -r requirements.txt
```

### Usage
```bash
# Process Word document
python3 main.py --input manuscript.docx --output result.docx

# Process all 11 benchmark samples
python3 main.py

# Direct text input
python3 main.py --text "C'est la vie"
```

---

## 📘 C# (.NET 8.0) Version

Located in the `cs/` directory.

### Build
Requires .NET 8.0 SDK.
```bash
cd cs
dotnet build
# Or build as a standalone EXE
./build_cs.sh
```

### Usage
```bash
# Process Word document
dotnet run -- --input manuscript.docx --output result.docx

# Run a specific benchmark sample (1-11)
dotnet run -- --sample 1

# Direct text input
dotnet run -- --text "Bonjour tout le monde"
```

---

## Project Structure
```
lang_html_detect/
├── cs/                     # C# .NET 8.0 Port
│   ├── Detector/           # Logic (Unicode, Lingua)
│   ├── IO/                 # DocxProcessor (OpenXML)
│   └── Program.cs          # CLI Entrypoint
├── detector/               # Python Detector Logic
├── annotator/              # Tagging & Annotation Logic
├── samples/                # Benchmark Samples (input_samples.txt)
├── main.py                 # Python CLI Entrypoint
├── app.py                  # Flask Web UI
└── docs/                   # Full Documentation (DEPLOY.md)
```

## Supported Languages (Sample)
Chinese (zh), Japanese (ja), Korean (ko), Arabic (ar), Hebrew (he), Hindi (hi), Tamil (ta), Telugu (te), Kannada (kn), Malayalam (ml), Bengali (bn), Punjabi (pa), Gujarati (gu), Russian (ru), Greek (el), Thai (th), Vietnamese (vi), Spanish (es), French (fr), German (de), Italian (it), Portuguese (pt), and 150+ more.

## License
MIT
