using System.Text.RegularExpressions;
using LangDetect.Detector;
using LangDetect.Annotator;
using LangDetect.IO;

namespace LangDetect;

class Program
{
    static void Main(string[] args)
    {
        if (args.Length == 0)
        {
            PrintUsage();
            return;
        }

        string? input = null;
        string? output = null;
        string? text = null;
        int? sampleIdx = null;

        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "--input":
                case "-i":
                    if (i + 1 < args.Length) input = args[++i];
                    break;
                case "--output":
                case "-o":
                    if (i + 1 < args.Length) output = args[++i];
                    break;
                case "--text":
                case "-t":
                    if (i + 1 < args.Length) text = args[++i];
                    break;
                case "--sample":
                case "-s":
                    if (i + 1 < args.Length && int.TryParse(args[++i], out int s)) sampleIdx = s;
                    break;
                case "--help":
                case "-h":
                    PrintUsage();
                    return;
            }
        }

        var detector = new LanguageDetector();
        var segmenter = new Segmenter(detector);
        var annotator = new Annotator.Annotator(segmenter);

        if (sampleIdx.HasValue)
        {
            RunSample(sampleIdx.Value, annotator);
        }
        else if (text != null)
        {
            Console.WriteLine(annotator.Annotate(text));
        }
        else if (input != null)
        {
            if (input.EndsWith(".docx", StringComparison.OrdinalIgnoreCase))
            {
                var processor = new DocxProcessor(annotator);
                processor.Process(input, output);
            }
            else
            {
                string content = File.ReadAllText(input);
                Console.WriteLine(annotator.Annotate(content));
            }
        }
        else
        {
            PrintUsage();
        }
    }

    static void RunSample(int idx, Annotator.Annotator annotator)
    {
        string samplePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "samples", "input_samples.txt");
        if (!File.Exists(samplePath))
        {
            // Fallback to searching relative to project
            samplePath = "samples/input_samples.txt";
        }

        if (!File.Exists(samplePath))
        {
            Console.WriteLine($"Error: samples/input_samples.txt not found at {Path.GetFullPath(samplePath)}");
            return;
        }

        string fullText = File.ReadAllText(samplePath);
        var samples = Regex.Split(fullText, @"Sample \d+:");
        
        // samples[0] is usually empty or header. samples[1] is Sample 1.
        if (idx < 1 || idx >= samples.Length)
        {
            Console.WriteLine($"Error: Sample {idx} not found. Range: 1 to {samples.Length - 1}");
            return;
        }

        string sampleContent = samples[idx].Trim();
        Console.WriteLine($"--- Sample {idx} ---");
        Console.WriteLine(annotator.Annotate(sampleContent));
    }

    static void PrintUsage()
    {
        Console.WriteLine("Multilingual Manuscript Tagger (C# Port)");
        Console.WriteLine("Usage:");
        Console.WriteLine("  lang_detect --text \"Your text here\"");
        Console.WriteLine("  lang_detect --input document.docx [--output annotated.docx]");
        Console.WriteLine("  lang_detect --sample 1");
        Console.WriteLine();
        Console.WriteLine("Options:");
        Console.WriteLine("  -i, --input <file>    Path to .docx or .txt file");
        Console.WriteLine("  -o, --output <file>   Path for annotated .docx output");
        Console.WriteLine("  -t, --text <string>   Direct text input for annotation");
        Console.WriteLine("  -s, --sample <num>    Run a benchmark sample (1-11)");
    }
}
