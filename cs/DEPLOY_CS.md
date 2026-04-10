# Deploying Language Detector (C# .NET)

This version is a high-performance C# port of the language detection system, designed for .NET 8.0 environments.

## Prerequisites
- .NET 8.0 SDK installed on the build machine.

## Setup & Build

1. **Navigate to the C# project directory**:
   ```bash
   cd /scratch/nishanth.r/tn/lang_html_detect_cs
   ```

2. **Restore dependencies**:
   ```bash
   dotnet restore
   ```

3. **Build the single-file executable**:
   ```bash
   # For Linux
   dotnet publish -c Release -r linux-x64 --self-contained true /p:PublishSingleFile=true

   # For Windows
   dotnet publish -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true
   ```

## Usage

Run the generated executable:

```bash
# General text
./lang_detect --text "Hello world. Bonjour tout le monde."

# Docx file
./lang_detect --input my_manuscript.docx --output result.docx

# Run benchmark sample
./lang_detect --sample 1
```

## Features
- **Lingua.NET**: High-precision detection for 75+ languages.
- **OpenXML**: Native Word document processing without requiring Microsoft Word installed.
- **Zero Runtime Dependencies**: The `self-contained` publish include everything needed to run on a machine without .NET installed.
