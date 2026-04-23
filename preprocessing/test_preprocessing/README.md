# Test Preprocessing

This folder contains notebooks and DOCX fixtures for testing `../assessment_processor.py`.

## Contents

### `test_output_format.ipynb`

Manual output inspection notebook.

- Parses one `.docx`, `.html`, or `.htm` file using `parse_to_dict`
- Prints the parsed dictionary as formatted JSON
- Uses `word assessment files/Myrcia neosmithii_draft_status_Apr2022_v2.docx` by default

### `unit_tests.ipynb`

Unit-level and fixture-based parser tests.

- Runs 17 tests that print `PASS` or `FAIL`
- Uses generated DOCX and HTML fixtures for controlled parser behavior
- Uses selected real DOCX fixtures for regression checks
- Includes deterministic-output and structural-invariant checks

Coverage includes:

- rich-text wrapping and paragraph rich-text rendering
- style bucket merging
- heading detection
- table extraction
- full DOCX parsing
- DOCX files without comments
- HTML and `.htm` parsing
- HTML style extraction
- `parse_to_dict`
- raw XML run rendering
- unsupported file extensions
- DOCX edge structures
- output invariants
- real DOCX fixture regressions
- deterministic parser output

### `evaluation_tests_batch.ipynb`

Batch parser evaluation notebook.

- Evaluates all DOCX files in `word assessment files/`
- Reports metric-level scores and aggregate scores
- Includes both parser-output checks and raw DOCX/XML-derived checks

Metrics include:

- text bigram similarity
- schema completeness
- heading tree recall
- rich-text tag coverage
- style block presence
- comment output structure
- raw DOCX/XML text bigram similarity
- raw DOCX/XML heading tree recall
- raw DOCX/XML structure count consistency
- raw DOCX/XML comment ID coverage
- raw DOCX/XML rich-text feature recall

### `word assessment files/`

DOCX fixture folder used by the notebooks.

- Contains the batch assessment files used by `evaluation_tests_batch.ipynb`
- Contains selected real DOCX fixtures used by `unit_tests.ipynb`
- Contains the default inspection document used by `test_output_format.ipynb`

## Testing Setup

The notebooks locate `assessment_processor.py` by searching the current directory and parent directories. They can be run from the repository root or from this folder.

Required Python packages:

- `python-docx`
- `beautifulsoup4`
- `IPython`
- Jupyter or a compatible notebook environment

## How To Run

### Manual Output Inspection

1. Open `test_output_format.ipynb`
2. Set `DOCUMENT_PATH` if a different input document is required
3. Run all cells
4. Inspect the printed JSON dictionary

### Unit Tests

1. Open `unit_tests.ipynb`
2. Run all cells
3. Confirm every test prints `PASS`

### Batch Evaluation

1. Open `evaluation_tests_batch.ipynb`
2. Run all cells
3. Review each metric score and the aggregate scores

## Interpreting Results

- `PASS` means the test or metric matched its expected condition.
- `FAIL` means the parser output or metric result needs review.
- Unit tests focus on controlled behavior, invariants, and selected real-document regressions.
- Batch evaluation provides broader parser-output and raw DOCX/XML consistency checks across the assessment fixture set.
