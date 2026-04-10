using System.Text;
using LangDetect.Detector;

namespace LangDetect.Annotator;

public static class Tagger
{
    private static readonly HashSet<string> WESTERN_TAGS = new()
    {
        "en", "es", "de", "fr", "it", "pt", "sv", "fi", "ru", "tr", "pl", "cs", "hu", "hr", "sr", "sl", "lt", "lv", "et", "sq", "ro", "bg", "uk", "be", "mk", "el", "cy", "ga", "eu", "la"
    };

    public static string TagSpans(List<LangSpan> spans)
    {
        var output = new StringBuilder();

        foreach (var span in spans)
        {
            if (span.Lang != null)
            {
                string text = span.Text;
                if (WESTERN_TAGS.Contains(span.Lang))
                {
                    string lPun = "";
                    string rPun = "";

                    while (text.Length > 0 && (char.IsWhiteSpace(text[0]) || char.IsPunctuation(text[0]) || "“”‘’".Contains(text[0])))
                    {
                        lPun += text[0];
                        text = text.Substring(1);
                    }

                    while (text.Length > 0 && (char.IsWhiteSpace(text[text.Length - 1]) || char.IsPunctuation(text[text.Length - 1]) || "“”‘’".Contains(text[text.Length - 1])))
                    {
                        rPun = text[text.Length - 1] + rPun;
                        text = text.Substring(0, text.Length - 1);
                    }

                    if (text.Length > 0)
                    {
                        output.Append($"{lPun}<lang xml:lang=\"{span.Lang}\">{text}</lang>{rPun}");
                    }
                    else
                    {
                        output.Append(lPun + rPun);
                    }
                }
                else
                {
                    // Non-Western
                    string lSpace = "";
                    string rSpace = "";

                    while (text.Length > 0 && char.IsWhiteSpace(text[0]))
                    {
                        lSpace += text[0];
                        text = text.Substring(1);
                    }

                    while (text.Length > 0 && char.IsWhiteSpace(text[text.Length - 1]))
                    {
                        rSpace = text[text.Length - 1] + rSpace;
                        text = text.Substring(0, text.Length - 1);
                    }

                    if (text.Length > 0)
                    {
                        output.Append($"{lSpace}<lang xml:lang=\"{span.Lang}\">{text}</lang>{rSpace}");
                    }
                    else
                    {
                        output.Append(lSpace + rSpace);
                    }
                }
            }
            else
            {
                output.Append(span.Text);
            }
        }

        return output.ToString();
    }
}

public class Annotator
{
    private readonly Segmenter _segmenter;

    public Annotator(Segmenter segmenter)
    {
        _segmenter = segmenter;
    }

    public string Annotate(string text)
    {
        var spans = _segmenter.Segment(text);
        return Tagger.TagSpans(spans);
    }
}
