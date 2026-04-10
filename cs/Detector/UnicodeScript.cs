using System.Globalization;
using System.Text;

namespace LangDetect.Detector;

public static class UnicodeScript
{
    private static readonly Dictionary<string, string> SCRIPT_TO_LANG = new()
    {
        { "Arabic", "ar" },
        { "Hebrew", "he" },
        { "Cyrillic", "ru" },
        { "Han", "zh" },
        { "Hiragana", "ja" },
        { "Katakana", "ja" },
        { "Hangul", "ko" },
        { "Devanagari", "hi" },
        { "Tamil", "ta" },
        { "Bengali", "bn" },
        { "Gurmukhi", "pa" },
        { "Telugu", "te" },
        { "Kannada", "kn" },
        { "Malayalam", "ml" },
        { "Gujarati", "gu" },
        { "Oriya", "or" },
        { "Sinhala", "si" },
        { "Thai", "th" },
        { "Myanmar", "my" },
        { "Khmer", "km" },
        { "Lao", "lo" },
        { "Georgian", "ka" },
        { "Armenian", "hy" },
        { "Greek", "el" }
    };

    public static string GetScript(char c)
    {
        UnicodeCategory category = CharUnicodeInfo.GetUnicodeCategory(c);
        
        if (category == UnicodeCategory.NonSpacingMark || 
            category == UnicodeCategory.SpacingCombiningMark || 
            category == UnicodeCategory.EnclosingMark)
        {
            return "COMBINING";
        }

        int code = (int)c;

        // Order matters: Specific scripts first, then broad ranges like Han (CJK)
        if (code >= 0x0600 && code <= 0x06FF) return "Arabic";
        if (code >= 0x0750 && code <= 0x077F) return "Arabic";
        if (code >= 0x0590 && code <= 0x05FF) return "Hebrew";
        if (code >= 0x0400 && code <= 0x04FF) return "Cyrillic";
        
        // Japanese
        if (code >= 0x3040 && code <= 0x309F) return "Hiragana";
        if (code >= 0x30A0 && code <= 0x30FF) return "Katakana";
        
        // Korean
        if (code >= 0xAC00 && code <= 0xD7AF) return "Hangul";
        
        // Chinese / CJK Unified Ideographs
        if (code >= 0x4E00 && code <= 0x9FFF) return "Han";
        if (code >= 0x3400 && code <= 0x4DBF) return "Han";
        if (code >= 0x2E80 && code <= 0x2EFF) return "Han";

        if (code >= 0x0900 && code <= 0x097F) return "Devanagari";
        if (code >= 0x0B80 && code <= 0x0BFF) return "Tamil";
        if (code >= 0x0980 && code <= 0x09FF) return "Bengali";
        if (code >= 0x0A00 && code <= 0x0A7F) return "Gurmukhi";
        if (code >= 0x0C00 && code <= 0x0C7F) return "Telugu";
        if (code >= 0x0C80 && code <= 0x0CFF) return "Kannada";
        if (code >= 0x0D00 && code <= 0x0D7F) return "Malayalam";
        if (code >= 0x0A80 && code <= 0x0AFF) return "Gujarati";
        if (code >= 0x0B00 && code <= 0x0B7F) return "Oriya";
        if (code >= 0x0D80 && code <= 0x0DFF) return "Sinhala";
        if (code >= 0x0E00 && code <= 0x0E7F) return "Thai";
        if (code >= 0x1000 && code <= 0x109F) return "Myanmar";
        if (code >= 0x1780 && code <= 0x17FF) return "Khmer";
        if (code >= 0x0E80 && code <= 0x0EFF) return "Lao";
        if (code >= 0x10A0 && code <= 0x10FF) return "Georgian";
        if (code >= 0x0530 && code <= 0x058F) return "Armenian";
        if (code >= 0x0370 && code <= 0x03FF) return "Greek";

        if ((code >= 0x0041 && code <= 0x005A) || (code >= 0x0061 && code <= 0x007A)) return "Latin";
        if (code >= 0x00C0 && code <= 0x00FF) return "Latin"; // Latin-1 Supplement

        return "NEUTRAL";
    }

    public static string? DominantScript(string text)
    {
        var counts = new Dictionary<string, int>();
        foreach (char c in text)
        {
            string script = GetScript(c);
            if (script != "Latin" && script != "NEUTRAL" && script != "COMBINING")
            {
                counts[script] = counts.GetValueOrDefault(script, 0) + 1;
            }
        }

        if (counts.Count == 0) return null;

        string bestScript = counts.OrderByDescending(x => x.Value).First().Key;
        return SCRIPT_TO_LANG.GetValueOrDefault(bestScript);
    }

    public static List<(string text, string? lang)> SplitByScript(string text)
    {
        if (string.IsNullOrEmpty(text)) return new List<(string, string?)>();

        var spans = new List<(string text, string type)>();
        var currentChunk = new StringBuilder();
        bool? currentIsLatin = null;

        foreach (char c in text)
        {
            string script = GetScript(c);
            if (script == "COMBINING")
            {
                currentChunk.Append(c);
                continue;
            }

            bool isLatin = (script == "Latin" || script == "NEUTRAL");

            if (script == "NEUTRAL")
            {
                currentChunk.Append(c);
            }
            else if (currentIsLatin == null || isLatin == currentIsLatin)
            {
                currentChunk.Append(c);
                currentIsLatin = isLatin;
            }
            else
            {
                if (currentChunk.Length > 0)
                {
                    spans.Add((currentChunk.ToString(), currentIsLatin.Value ? "LATIN" : "NON_LATIN"));
                }
                currentChunk.Clear();
                currentChunk.Append(c);
                currentIsLatin = isLatin;
            }
        }

        if (currentChunk.Length > 0)
        {
            spans.Add((currentChunk.ToString(), (currentIsLatin ?? true) ? "LATIN" : "NON_LATIN"));
        }

        var result = new List<(string text, string? lang)>();
        foreach (var span in spans)
        {
            if (span.type == "NON_LATIN")
            {
                result.Add((span.text, DominantScript(span.text)));
            }
            else
            {
                result.Add((span.text, null));
            }
        }

        return MergeAdjacentScripts(result);
    }

    private static List<(string text, string? lang)> MergeAdjacentScripts(List<(string text, string? lang)> spans)
    {
        if (spans.Count == 0) return spans;

        var merged = new List<(string text, string? lang)>();
        int i = 0;
        while (i < spans.Count)
        {
            string text = spans[i].text;
            string? lang = spans[i].lang;

            if (lang != null)
            {
                int j = i + 1;
                while (j < spans.Count)
                {
                    string nextText = spans[j].text;
                    string? nextLang = spans[j].lang;

                    if (nextLang == null && nextText.All(c => GetScript(c) == "NEUTRAL"))
                    {
                        if (j + 1 < spans.Count && spans[j + 1].lang == lang)
                        {
                            text += nextText + spans[j + 1].text;
                            j += 2;
                        }
                        else
                        {
                            break;
                        }
                    }
                    else if (nextLang == lang)
                    {
                        text += nextText;
                        j += 1;
                    }
                    else
                    {
                        break;
                    }
                }
                merged.Add((text, lang));
                i = j;
            }
            else
            {
                merged.Add((text, lang));
                i++;
            }
        }
        return merged;
    }
}
