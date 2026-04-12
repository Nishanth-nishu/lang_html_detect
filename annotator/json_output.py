"""
annotator/json_output.py

Converts LangSpan lists into structured JSON output.

JSON format:
{
  "input": "...",
  "annotated": "...",         # Same as XML-tagged string
  "spans": [
    {
      "text": "...",
      "lang": "es" | null,
      "is_foreign": true | false
    },
    ...
  ],
  "languages_detected": ["es", "de", "fr", ...]
}
"""

import json
from detector.segmenter import segment


def annotate_json(text: str) -> str:
    """
    Segment text and return a JSON string with full annotation detail.
    """
    spans = segment(text)
    
    span_list = []
    langs_seen = set()

    for span in spans:
        is_foreign = span.lang is not None and span.lang != "en"
        entry = {
            "text": span.text,
            "lang": span.lang,
            "is_foreign": is_foreign
        }
        span_list.append(entry)
        if span.lang and span.lang != "en":
            langs_seen.add(span.lang)

    # Build the XML-annotated string for reference
    from annotator.tagger import tag_spans
    annotated_str = tag_spans(spans)

    result = {
        "input": text,
        "annotated": annotated_str,
        "spans": span_list,
        "languages_detected": sorted(langs_seen)
    }

    return json.dumps(result, ensure_ascii=False, indent=2)
