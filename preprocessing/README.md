# Preprocessing

This folder contains the preprocessing parser used to convert assessment files into structured JSON.

## Current Contents

### `assessment_processor.py`

This is the main preprocessing script.

- Purpose: parse assessment documents into a structured Python dictionary / JSON output
- Supported input file types: `.docx`, `.html`, `.htm`
- Output:
  - batch mode: one `.json` file per input document
  - single-document mode: JSON printed to stdout
- Default input folder variable: `DEFAULT_INPUT_FOLDER`
- Default output folder variable: `DEFAULT_OUTPUT_FOLDER`

What it extracts:

- heading structure
- paragraphs
- list blocks
- tables
- comments and comment anchor context for DOCX files
- rich-text fields where available

## How To Run

Run from inside `preprocessing/`:

```bash
python3.12 assessment_processor.py
```

### Batch Mode

Batch mode runs when you call the script with no arguments.

```bash
python3.12 assessment_processor.py
```

Behavior:

- reads every `.docx`, `.html`, and `.htm` file in the folder pointed to by `DEFAULT_INPUT_FOLDER`
- creates the folder pointed to by `DEFAULT_OUTPUT_FOLDER` if it does not already exist
- saves one JSON file per input document into the folder pointed to by `DEFAULT_OUTPUT_FOLDER`
- writes `_errors.json` into the folder pointed to by `DEFAULT_OUTPUT_FOLDER`

Use batch mode when you want to process a whole folder at once.

Batch workflow:

1. Put your `.docx`, `.html`, or `.htm` files in the folder pointed to by `DEFAULT_INPUT_FOLDER`
2. Run `python3.12 assessment_processor.py`
3. Open the generated JSON files in the folder pointed to by `DEFAULT_OUTPUT_FOLDER`
4. If anything fails, inspect `_errors.json` in the folder pointed to by `DEFAULT_OUTPUT_FOLDER`

### Single-Document Mode

Single-document mode runs when you pass one supported file path to the script.

```bash
python3.12 assessment_processor.py "<path-to-file>.docx"
```

You can also pass HTML:

```bash
python3.12 assessment_processor.py "<path-to-file>.html"
```

Behavior:

- parses only the one file you pass in
- prints the JSON to stdout
- does not automatically save a `.json` file

If you want to save the result manually:

```bash
python3.12 assessment_processor.py "<path-to-file>.docx" > "output.json"
```

## `parse_to_dict()` Helper

`assessment_processor.py` also exposes a helper function:

```python
from assessment_processor import parse_to_dict
```

This function accepts a single `.docx`, `.html`, or `.htm` path and returns the parsed dictionary directly.

## Test Notebook

The folder [test_preprocessing] contains a notebook for quick manual testing:

- notebook: [test_preprocessing.ipynb]
- purpose: choose a document path, run `parse_to_dict`, and inspect the parsed JSON output interactively

## Recommended Process

### If your source files are already `.docx` or `HTML`

1. Put the files in the folder pointed to by `DEFAULT_INPUT_FOLDER`
2. Run `python3.12 assessment_processor.py` for batch parsing

### If you want to inspect just one file

1. Keep the document wherever you want
2. Run `python3.12 assessment_processor.py "<path-to-file>"`
3. Review the printed JSON directly in the terminal

### If you want to test interactively

1. Open [test_preprocessing.ipynb]
2. Set `DOCUMENT_PATH`
3. Run the notebook cells


