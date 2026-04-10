using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using LangDetect.Annotator;

namespace LangDetect.IO;

public class DocxProcessor
{
    private readonly Annotator.Annotator _annotator;

    public DocxProcessor(Annotator.Annotator annotator)
    {
        _annotator = annotator;
    }

    public void Process(string inputPath, string? outputPath = null)
    {
        outputPath ??= Path.Combine(
            Path.GetDirectoryName(inputPath) ?? "",
            Path.GetFileNameWithoutExtension(inputPath) + "_annotated" + Path.GetExtension(inputPath)
        );

        // Copy input to output to preserve headers/footers/styles
        File.Copy(inputPath, outputPath, true);

        using (WordprocessingDocument doc = WordprocessingDocument.Open(outputPath, true))
        {
            var body = doc.MainDocumentPart?.Document.Body;
            if (body == null) return;

            var paragraphs = body.Elements<Paragraph>().ToList();

            foreach (var para in paragraphs)
            {
                string text = para.InnerText;
                if (string.IsNullOrWhiteSpace(text)) continue;

                string annotatedText = _annotator.Annotate(text);

                // Preserve the first run's properties (font size, etc.) if possible
                var firstRun = para.Elements<Run>().FirstOrDefault();
                RunProperties? baseRpr = firstRun?.RunProperties != null 
                    ? (RunProperties)firstRun.RunProperties.CloneNode(true) 
                    : null;

                // Clear existing runs
                para.RemoveAllChildren<Run>();

                // Add new run with annotated text
                var newRun = new Run();
                if (baseRpr != null)
                {
                    newRun.AppendChild(baseRpr);
                }

                var t = new Text(annotatedText) { Space = SpaceProcessingModeValues.Preserve };
                newRun.AppendChild(t);

                para.AppendChild(newRun);
            }

            doc.MainDocumentPart?.Document.Save();
        }

        Console.WriteLine($"[lang_detect] Wrote annotated document: {outputPath}");
    }
}
