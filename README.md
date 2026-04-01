Small utility scripts for converting assessment files into structured JSON.

## Python files:

### `convert_doc_to_docx.py`

Batch converts legacy `.doc` files into `.docx` files using `doc2docx`. Requires MS Word to be installed on the machine.

- Default input folder: `assessments_doc/`
- Default output folder: `converted/`
- Run:

```bash
python3.12 convert_doc_to_docx.py
```

- What it does:
  - Reads all `.doc` files in the input folder
  - Saves converted `.docx` files in the output folder
  - Skips files that were already converted
  - Writes `_conversion_errors.json` to the output folder

To change the folders, edit these constants in [`convert_doc_to_docx.py`]:

```python
INPUT_FOLDER = Path("assessments_doc")
OUTPUT_FOLDER = Path("converted")
```

### `assessment_processor.py`

Main parser. Converts `.docx` or `.html` assessment files into a JSON dictionary with:

- heading structure
- paragraphs
- list items
- tables
- comments and comment anchors
- rich-text fields for superscript and subscript where available

Default folders are defined in [`assessment_processor.py`]:

```python
DEFAULT_INPUT_FOLDER = "converted"
DEFAULT_OUTPUT_FOLDER = "json_converted"
```

To use different folders, change those two values in the file.

### `parse_docx_to_dict.py`

Very small helper script for quick testing. It imports `parse_docx_to_dict()` from `assessment_processor.py`, parses one hard-coded `.docx` file, and prints the result.

Edit the filename in [`parse_docx_to_dict.py`](/Users/Khalid/Desktop/University/SWP/IUCN_Reviewer/parse_docx_to_dict.py#L1) before running it.

Run:

```bash
python3.12 parse_docx_to_dict.py
```

## How to run `assessment_processor.py`

### Batch mode

Use batch mode when you want the script to automatically save JSON files.

```bash
python3.12 assessment_processor.py
```

Behavior:

- Reads every `.docx`, `.html`, and `.htm` file in `DEFAULT_INPUT_FOLDER`
- Saves one `.json` file per input file in `DEFAULT_OUTPUT_FOLDER`
- Writes `_errors.json` in `json_converted/`

Example workflow:

1. Put files in `converted/`
2. Run `python3.12 assessment_processor.py`
3. Open the generated files in `json_converted/`

### Single-file mode

Use single-file mode when you want to inspect one file quickly.

```bash
python3.12 assessment_processor.py "converted/My Assessment.docx"
```

Behavior:

- Parses only the file you pass in
- Prints the JSON to the terminal
- Does not save a `.json` file automatically

If you want to save the output from single-file mode, redirect it:

```bash
python3.12 assessment_processor.py "converted/My Assessment.docx" > "json_converted/My Assessment.json"
```

## Recommended workflow

If your source files are `.doc`:

1. Put the `.doc` files in `DEFAULT_INPUT_FOLDER`
2. Run `python3.12 convert_doc_to_docx.py`
3. Run `python3.12 assessment_processor.py`

If your source files are already `.docx`:

1. Put the files in `DEFAULT_INPUT_FOLDER`
2. Run `python3.12 assessment_processor.py`

## Notes

- `assessment_processor.py` supports `.docx`, `.html`, and `.htm`
- Batch mode saves files automatically
- Single-file mode prints to stdout unless you use `>` followed by output file name
- If you change default folders in the code, keep the workflow consistent across both scripts
