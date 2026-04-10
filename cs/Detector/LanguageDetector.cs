using Lingua.NET;
using System.Collections.Concurrent;

namespace LangDetect.Detector;

public class LanguageDetector
{
    private readonly Lingua.NET.LanguageDetector _lingua;
    private static readonly ConcurrentDictionary<Language, string> _isoCache = new();

    public LanguageDetector()
    {
        _lingua = LanguageDetectorBuilder.FromAllLanguages().Build();
    }

    public (string? lang, double confidence) Detect(string text)
    {
        text = text.Trim();
        if (string.IsNullOrEmpty(text) || !text.Any(char.IsLetter))
        {
            return (null, 0.0);
        }

        // Layer 1: Unicode script heuristics (instant)
        string? scriptLang = UnicodeScript.DominantScript(text);
        if (scriptLang != null)
        {
            return (scriptLang, 1.0);
        }

        // Layer 2: Lingua
        try
        {
            var confidences = _lingua.ComputeLanguageConfidenceValues(text);
            if (confidences.Count == 0) return (null, 0.0);

            var top = confidences.OrderByDescending(c => c.Value).First();
            if (top.Language == Language.English)
            {
                return (null, top.Value);
            }

            // Find English confidence for margin check
            double enConf = confidences.FirstOrDefault(c => c.Language == Language.English)?.Value ?? 0.0;

            if (text.Length < 20)
            {
                if (top.Value < 0.01) return (null, 0.0);
                if (top.Value < enConf * 2.0) return (null, top.Value);
            }

            return (GetIsoCode(top.Language), 0.85);
        }
        catch
        {
            return (null, 0.0);
        }
    }

    private string GetIsoCode(Language lang)
    {
        return _isoCache.GetOrAdd(lang, l =>
        {
            string name = l.ToString().ToLower();
            return name switch
            {
                "chinese" => "zh",
                "japanese" => "ja",
                "korean" => "ko",
                "arabic" => "ar",
                "hebrew" => "he",
                "hindi" => "hi",
                "tamil" => "ta",
                "telugu" => "te",
                "kannada" => "kn",
                "malayalam" => "ml",
                "bengali" => "bn",
                "gujarati" => "gu",
                "punjabi" => "pa",
                "urdu" => "ur",
                "persian" => "fa",
                "turkish" => "tr",
                "russian" => "ru",
                "ukrainian" => "uk",
                "greek" => "el",
                "thai" => "th",
                "vietnamese" => "vi",
                "indonesian" => "id",
                "malay" => "ms",
                "english" => "en",
                "spanish" => "es",
                "french" => "fr",
                "german" => "de",
                "italian" => "it",
                "portuguese" => "pt",
                "dutch" => "nl",
                "swedish" => "sv",
                "norwegian" => "no",
                "danish" => "da",
                "finnish" => "fi",
                "polish" => "pl",
                "czech" => "cs",
                "slovak" => "sk",
                "hungarian" => "hu",
                "romanian" => "ro",
                "catalan" => "ca",
                "latin" => "la",
                "afrikaans" => "af",
                "basque" => "eu",
                "welsh" => "cy",
                "irish" => "ga",
                "icelandic" => "is",
                "albanian" => "sq",
                "macedonian" => "mk",
                "serbian" => "sr",
                "croatian" => "hr",
                "bosnian" => "bs",
                "slovenian" => "sl",
                "bulgarian" => "bg",
                "belarusian" => "be",
                "georgian" => "ka",
                "armenian" => "hy",
                "azerbaijani" => "az",
                "kazakh" => "kk",
                "uzbek" => "uz",
                "latvian" => "lv",
                "lithuanian" => "lt",
                "estonian" => "et",
                "maltese" => "mt",
                "swahili" => "sw",
                "yoruba" => "yo",
                "zulu" => "zu",
                "xhosa" => "xh",
                "shona" => "sn",
                "somali" => "so",
                "hausa" => "ha",
                "igbo" => "ig",
                "amharic" => "am",
                "maori" => "mi",
                "esperanto" => "eo",
                "marathi" => "mr",
                "nepali" => "ne",
                "sinhala" => "si",
                _ => name.Length >= 2 ? name.Substring(0, 2) : name
            };
        });
    }
}
