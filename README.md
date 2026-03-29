# lang_html_detect

AI-powered foreign language identifier for manuscripts. Detects non-English language spans and annotates them with `<lang xml:lang="XX">…</lang>` tags — 100% free, local, no paid APIs.

## Features
- Identifies 176+ languages in mixed-language text
- Word-level, phrase-level, and sentence-level detection
- Produces `<lang xml:lang="XX">…</lang>` XML annotations
- Flask web UI with color-coded language highlighting
- CLI tool for batch processing

## Architecture (Three-Layer Pipeline)

| Layer | Tool | Purpose |
|---|---|---|
| 1 | Unicode script heuristics | Instant: CJK→zh, Arabic→ar, Tamil→ta, Hebrew→he, Devanagari→hi… |
| 2 | [Lingua-py](https://github.com/pemistahl/lingua-py) (Apache 2.0) | Latin-script accuracy: Spanish, French, German, Italian, etc. |
| 3 | [fastText lid.176](https://fasttext.cc/docs/en/language-identification.html) (CC BY-SA 3.0) | 176-language fallback, auto-downloaded on first use |

## Installation

```bash
pip install lingua-language-detector fasttext-wheel flask
```

## Usage

### CLI

```bash
# Process all 11 built-in samples
python3 main.py

# Process a specific sample
python3 main.py --sample 4

# Process inline text
python3 main.py --text "Hello, Merci, Gracias, 谢谢, شكرا"

# Process your own file
python3 main.py --input mymanuscript.txt
```

### Web UI

```bash
python3 app.py
# Open http://localhost:5000
```

## Example Output

**Input:**
```
The methods section includes Merci, Gracias, Danke, 谢谢, شكرا, நன்றி.
El resultado es estable. Le résultat est stable.
```

**Output:**
```xml
The methods section includes <lang xml:lang="zh">谢谢</lang>,
<lang xml:lang="ar">شكرا</lang>, <lang xml:lang="ta">நன்றி</lang>.
<lang xml:lang="es">El resultado es estable.</lang>
<lang xml:lang="fr">Le résultat est stable.</lang>
```

## Project Structure

```
lang-identifier/
├── detector/
│   ├── unicode_script.py   # Unicode block → lang code heuristics
│   ├── lang_detector.py    # 3-layer detector (Lingua + fastText)
│   └── segmenter.py        # Text → LangSpan[] pipeline
├── annotator/
│   └── tagger.py           # annotate() + annotate_html()
├── templates/
│   └── index.html          # Flask web UI (dark mode, color-coded)
├── samples/
│   └── input_samples.txt   # 11 test samples
├── main.py                 # CLI entrypoint
├── app.py                  # Flask web server
└── requirements.txt
```

## Supported Languages (Sample)

Chinese (zh), Japanese (ja), Korean (ko), Arabic (ar), Hebrew (he), Hindi (hi), Tamil (ta), Telugu (te), Kannada (kn), Malayalam (ml), Bengali (bn), Punjabi (pa), Gujarati (gu), Russian (ru), Greek (el), Thai (th), Vietnamese (vi), Spanish (es), French (fr), German (de), Italian (it), Portuguese (pt), and 150+ more.

## License

MIT
