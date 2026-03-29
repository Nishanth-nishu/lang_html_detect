"""
Language detector wrapping Lingua (primary) and fastText (fallback).

Priority:
  1. Unicode script heuristics (instant, no ML)
  2. Lingua — high accuracy on Latin-script short text
  3. fastText lid.176.bin — broad 176-language fallback

All models are free / open-source and run fully locally.
"""

from __future__ import annotations
import os
import re
import threading
import urllib.request
from pathlib import Path
from typing import Optional

from detector.unicode_script import dominant_script

# ---------------------------------------------------------------------------
# Lingua setup
# ---------------------------------------------------------------------------
try:
    from lingua import Language, LanguageDetectorBuilder
    _LINGUA_AVAILABLE = True
except ImportError:
    _LINGUA_AVAILABLE = False
    print("[warn] lingua not available; Latin detection quality will be reduced.")

# ---------------------------------------------------------------------------
# fastText setup — download model to persistent cache on first use
# ---------------------------------------------------------------------------
_FT_MODEL_URL = (
    "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
)

# Use a persistent cache directory to avoid re-downloading in bundled EXE
_CACHE_DIR = Path.home() / ".cache" / "lang_detect"
_FT_MODEL_PATH = _CACHE_DIR / "models" / "lid.176.bin"

_ft_model = None
_ft_lock = threading.Lock()

try:
    import fasttext as _ft_lib
    _FT_LIB_AVAILABLE = True
except ImportError:
    _FT_LIB_AVAILABLE = False
    print("[warn] fasttext not available; falling back to lingua only.")


def _get_fasttext_model():
    global _ft_model
    if _ft_model is not None:
        return _ft_model
    with _ft_lock:
        if _ft_model is not None:
            return _ft_model
        if not _FT_LIB_AVAILABLE:
            return None
        
        # Ensure persistent cache directory exists
        if not _FT_MODEL_PATH.exists():
            _FT_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            print(f"[info] Downloading fastText model to {_FT_MODEL_PATH} …")
            urllib.request.urlretrieve(_FT_MODEL_URL, str(_FT_MODEL_PATH))
            print("[info] fastText model downloaded.")
            
        try:
            _ft_model = _ft_lib.load_model(str(_FT_MODEL_PATH))
        except Exception as e:
            print(f"[err] Failed to load fastText model: {e}")
            return None
    return _ft_model


# ---------------------------------------------------------------------------
# Lingua detector — built lazily
# ---------------------------------------------------------------------------
_lingua_detector = None
_lingua_lock = threading.Lock()

def _get_lingua_detector():
    global _lingua_detector
    if _lingua_detector is not None or not _LINGUA_AVAILABLE:
        return _lingua_detector
    with _lingua_lock:
        if _lingua_detector is not None:
            return _lingua_detector
        _lingua_detector = (
            LanguageDetectorBuilder.from_all_languages()
            .build()
        )
    return _lingua_detector


# ---------------------------------------------------------------------------
# BCP-47 / ISO 639-1 normalisation
# ---------------------------------------------------------------------------
_LINGUA_TO_ISO: dict[str, str] = {}

def _lingua_lang_to_iso(lang) -> str:
    """Convert a Lingua Language enum value to ISO 639-1 code."""
    name = lang.name.lower()          # e.g. "SPANISH" → "spanish"
    # Special cases where Lingua name doesn't map to iso cleanly
    _OVERRIDES = {
        "chinese": "zh",
        "japanese": "ja",
        "korean": "ko",
        "arabic": "ar",
        "hebrew": "he",
        "hindi": "hi",
        "tamil": "ta",
        "telugu": "te",
        "kannada": "kn",
        "malayalam": "ml",
        "bengali": "bn",
        "gujarati": "gu",
        "punjabi": "pa",
        "urdu": "ur",
        "persian": "fa",
        "turkish": "tr",
        "russian": "ru",
        "ukrainian": "uk",
        "greek": "el",
        "thai": "th",
        "vietnamese": "vi",
        "indonesian": "id",
        "malay": "ms",
        "english": "en",
        "spanish": "es",
        "french": "fr",
        "german": "de",
        "italian": "it",
        "portuguese": "pt",
        "dutch": "nl",
        "swedish": "sv",
        "norwegian": "no",
        "danish": "da",
        "finnish": "fi",
        "polish": "pl",
        "czech": "cs",
        "slovak": "sk",
        "hungarian": "hu",
        "romanian": "ro",
        "catalan": "ca",
        "latin": "la",
        "afrikaans": "af",
        "basque": "eu",
        "welsh": "cy",
        "irish": "ga",
        "icelandic": "is",
        "albanian": "sq",
        "macedonian": "mk",
        "serbian": "sr",
        "croatian": "hr",
        "bosnian": "bs",
        "slovenian": "sl",
        "bulgarian": "bg",
        "belarusian": "be",
        "georgian": "ka",
        "armenian": "hy",
        "azerbaijani": "az",
        "kazakh": "kk",
        "uzbek": "uz",
        "latvian": "lv",
        "lithuanian": "lt",
        "estonian": "et",
        "maltese": "mt",
        "swahili": "sw",
        "yoruba": "yo",
        "zulu": "zu",
        "xhosa": "xh",
        "shona": "sn",
        "somali": "so",
        "hausa": "ha",
        "igbo": "ig",
        "amharic": "am",
        "maori": "mi",
        "esperanto": "eo",
        "nynorsk": "nn",
        "marathi": "mr",
        "nepali": "ne",
        "sinhala": "si",
    }
    return _OVERRIDES.get(name, lang.iso_code_639_1.name.lower() if hasattr(lang, 'iso_code_639_1') else name[:2])


_FT_LABEL_RE = re.compile(r"__label__(.+)")

def _fasttext_detect(text: str) -> tuple[str | None, float]:
    """Return (iso_lang_code, confidence) using fastText."""
    model = _get_fasttext_model()
    if model is None:
        return None, 0.0
    clean = text.replace("\n", " ").strip()
    if not clean:
        return None, 0.0
    try:
        labels, probs = model.predict(clean, k=1)
        if not labels:
            return None, 0.0
        m = _FT_LABEL_RE.match(labels[0])
        if not m:
            return None, 0.0
        code = m.group(1).split("_")[0]
        return code, float(probs[0])
    except (ValueError, Exception):
        # NumPy 2.x compatibility workaround: use predict with string output
        try:
            import numpy as np
            result = model.predict(clean, k=1, threshold=0.0)
            labels = result[0]
            probs = np.asarray(result[1])
            if not labels:
                return None, 0.0
            m = _FT_LABEL_RE.match(labels[0])
            if not m:
                return None, 0.0
            code = m.group(1).split("_")[0]
            return code, float(probs[0])
        except Exception:
            return None, 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class LanguageDetector:
    """Three-layer language detector: unicode → lingua → fasttext."""

    # Only applied to fastText (Lingua's scores are calibrated differently)
    FT_MIN_CONFIDENCE = 0.50

    def __init__(self):
        self._lingua = _get_lingua_detector()
        self.lang_enum = Language if _LINGUA_AVAILABLE else None

    def detect(self, text: str) -> tuple[str | None, float]:
        """
        Return (iso_639_1_code, confidence) for the given text.
        Returns None lang for English / undetectable text.
        """
        text = text.strip()
        if not text or not any(c.isalpha() for c in text):
            return None, 0.0

        # Layer 1: Unicode script heuristics (instant)
        script_lang = dominant_script(text)
        if script_lang:
            return script_lang, 1.0

        # Layer 2: Lingua
        if self._lingua:
            try:
                # Get all confidence values to see the gap between top and English
                conf_values = self._lingua.compute_language_confidence_values(text)
                if not conf_values:
                    return None, 0.0
                
                top = conf_values[0]
                if top.language == self.lang_enum.ENGLISH:
                    return None, top.value
                
                # Find English confidence for comparison
                en_conf = next((c.value for c in conf_values if c.language == self.lang_enum.ENGLISH), 0.0)
                
                # If it's a very short piece of text, require a margin
                # Lingua confidences are very small (e.g. 0.05), so we use a relative ratio
                if len(text) < 20:
                    # Require top lang to be significantly more likely than English
                    if top.value < 0.01: # Extremely low confidence
                        return None, 0.0
                    if top.value < en_conf * 2.0:
                        return None, top.value
                
                iso = _lingua_lang_to_iso(top.language)
                return iso, 0.85 # We map Lingua's top pick to a "trust" value
            except Exception:
                pass

        # Layer 3: fastText fallback
        ft_lang, ft_conf = _fasttext_detect(text)
        if ft_lang and ft_lang != "en" and ft_conf >= self.FT_MIN_CONFIDENCE:
            return ft_lang, ft_conf

        return None, 0.0

    def detect_spans(self, text: str) -> list[tuple[int, int, str]]:
        """
        Use Lingua's multi-language detection to get character-level spans.
        Returns list of (start, end, iso_code) for non-English spans.
        Only works if Lingua is available.
        """
        detector = _get_lingua_detector()
        if not detector or not _LINGUA_AVAILABLE:
            return []
        try:
            results = detector.detect_multiple_languages_of(text)
            spans = []
            for r in results:
                iso = _lingua_lang_to_iso(r.language)
                spans.append((r.start_index, r.end_index, iso))
            return spans
        except Exception:
            return []


# Singleton
_detector_instance: LanguageDetector | None = None

def get_detector() -> LanguageDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = LanguageDetector()
    return _detector_instance
