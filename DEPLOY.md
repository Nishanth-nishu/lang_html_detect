# Production Deployment Guide

**Tool: `lang_detect`** — Foreign Language Identifier  
Single-file executable. No Python, no Docker, no pip needed on the target server.

---

## Quick Start

```
bash build.sh          # one-time build (needs Python 3.10+ on build machine)
scp dist/lang_detect user@server:/usr/local/bin/
ssh user@server "lang_detect --input manuscript.docx"
```

---

## Step-by-Step

### 1 — Build machine requirements (one-time setup)

| Requirement | Minimum version |
|---|---|
| Python | 3.10+ |
| pip | 22+ |

No special OS — any modern Linux (glibc 2.28+), macOS 12+, or Windows 10+ works.

```bash
# Clone / unzip the project
cd lang_html_detect

# Install build dependencies (NOT needed on target server)
pip install -r requirements.txt pyinstaller

# Build the binary
bash build.sh
```

The output is a single file: `dist/lang_detect` (~150 MB, self-contained).

---

### 2 — Pre-download the fastText model (important for offline / air-gapped servers)

The binary auto-downloads the fastText language model (~130 MB) on first run to:
```
~/.cache/lang_detect/models/lid.176.bin
```

**Option A — Let it download automatically** (server needs internet on first run):
```bash
lang_detect --text "test"   # triggers download once; subsequent runs use cache
```

**Option B — Pre-download and ship the model with the binary** (air-gapped):
```bash
# On any machine with internet:
mkdir -p ~/.cache/lang_detect/models
wget -O ~/.cache/lang_detect/models/lid.176.bin \
  https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin

# Copy to the server's cache directory:
scp ~/.cache/lang_detect/models/lid.176.bin \
  user@server:~/.cache/lang_detect/models/lid.176.bin
```

---

### 3 — Copy binary to server

```bash
# Option A: scp
scp dist/lang_detect user@server:/usr/local/bin/lang_detect
ssh user@server "chmod +x /usr/local/bin/lang_detect"

# Option B: shared NFS / mounted drive — just copy the file

# Option C: just run it in-place
./dist/lang_detect --input document.docx
```

The binary is statically linked to its Python runtime and all libraries.  
**No pip install, no virtualenv, no Docker needed on the server.**

---

### 4 — Usage on the server

```bash
# Annotate a Word document → produces document_annotated.docx
lang_detect --input manuscript.docx

# Specify a custom output path
lang_detect --input manuscript.docx --output manuscript_tagged.docx

# Annotate inline text
lang_detect --text "Merci beaucoup! Danke schön."

# Process a plain-text multi-sample file
lang_detect --input samples.txt

# Process built-in sample 4
lang_detect --sample 4
```

---

## Output Format

### Word document (`.docx`) input
The output `.docx` preserves all original formatting (fonts, bold, italic, tables, images).  
Foreign-language runs are **colour-highlighted**:

| Language | Colour |
|---|---|
| French | Blue `#1E90FF` |
| Spanish | Tomato `#FF6347` |
| German | Forest Green `#228B22` |
| Italian | Dark Orange `#FF8C00` |
| Russian / Ukrainian | Dark Violet `#9400D3` |
| Arabic / Hebrew / Persian | Crimson `#DC143C` |
| Chinese | Deep Pink `#FF1493` |
| Japanese | Saddle Brown `#8B4513` |
| Korean | Dark Turquoise `#00CED1` |
| Hindi / Devanagari | Dark Goldenrod `#B8860B` |
| Tamil / Dravidian | Sea Green `#2E8B57` |
| Portuguese | Purple `#6A0DAD` |
| Other foreign | Slate Gray `#708090` |

Each annotated paragraph is followed by a small grey annotation line:
```
↳ Hello <lang xml:lang="fr">Bonjour</lang> world
```

### Plain text input
Outputs the XML-annotated string to stdout:
```
Hello <lang xml:lang="fr">Bonjour</lang> world
```

---

## Building for Multiple Platforms

PyInstaller binaries are **platform-specific** (Linux EXE won't run on Windows and vice versa).  
Build on the same OS family as your target server.

| Target | Build on |
|---|---|
| Linux (glibc ≥ 2.28) | Ubuntu 20.04 / Debian 10 or higher |
| macOS | macOS 12+ |
| Windows | Windows 10 |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Permission denied` | `chmod +x lang_detect` |
| `GLIBC_2.xx not found` | Build on an older Linux (e.g. Ubuntu 20.04) |
| `[info] Downloading fastText model` appears on first run | Expected — model downloads once; use Option B above to pre-cache |
| Output docx looks wrong | Open in LibreOffice 7.3+ or Word 2019+ for best colour support |
| `python-docx` import error in script mode | `pip install python-docx` on the build machine |
