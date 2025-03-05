# LaTeX to PDF Converter

## Overview
This Python script converts LaTeX code into a PDF file using `pdflatex`. It takes a `.tex` file as input, compiles it, and generates a corresponding `.pdf` file.

## Features
- Converts LaTeX files to PDF
- Handles LaTeX compilation errors gracefully
- Works with any `.tex` file containing valid LaTeX code

## Prerequisites
Ensure you have the following installed:

- Python 3.x
- `pdflatex` (part of TeX Live, MiKTeX, or MacTeX distributions)

To install TeX Live on Linux:
```sh
sudo apt install texlive-latex-base
```

To install MiKTeX on Windows, download it from [MiKTeX website](https://miktex.org/download).

## Installation
Clone the repository and navigate to the script's directory:
```sh
git clone https://github.com/aushin19/LaTex2PDF.git
cd LaTex2PDF
```

Install required Python packages (if any):
```sh
pip install -r requirements.txt
```

## Usage
Run the script with the LaTeX file as an argument:
```sh
python app.py
```

```sh
curl --location --request POST 'http://localhost:5678/convert-file' \
--header 'Content-Type: application/json' \
--data ''
```

This will generate PDF in the `temp` directory.

## Error Handling
If the script encounters an error during compilation, it will display the error log. Ensure your LaTeX syntax is correct.
