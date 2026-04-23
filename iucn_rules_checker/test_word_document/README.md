# Test Word Document

This folder contains a simple notebook-based workflow for testing the
rules-based system on a Word document.

## Files In This Folder

- `test_word_document.ipynb`
  Notebook that loads a user-provided Word document, converts it to a Python
  dict, parses the resulting dictionary with `AssessmentParser`, and then
  generates violations with `IUCNAssessmentReviewer`.
- `README.md`
  This document.

## Confidential Test Document

During development, this workflow was used to spot check real IUCN assessment
documents provided by Kew Gardens. Those assessment documents are not included
in this repository because they are confidential.

## How It Works

The notebook uses the same two-stage rules-based flow as the rest of the
package:

1. The `.docx` file is first converted to a Python dict using the
   `parse_to_dict` function from `repo root > preprocessing > assessment_processor.py`.
2. `AssessmentParser.parse(...)` converts that assessment dictionary into the
   flat `full_report` mapping used by the reviewer.
3. `IUCNAssessmentReviewer.review_full_report(...)` generates the rule
   violations.
4. `clean_up_violations(...)` is applied before the results are displayed so
   the printed output is easier to read.

## Test Your Own Word Document

Open:

- `test_word_document/test_word_document.ipynb`

and change the path cell so that `CUSTOM_DOCX_PATH` points to your own `.docx`
file.

If `CUSTOM_DOCX_PATH` is left as `None`, the notebook will stop with a reminder
to provide a local file path.

Example:

```python
CUSTOM_DOCX_PATH = "path/to/your_assessment.docx"
```

Then run the notebook cells again. The notebook will:

- load your Word document
- convert it to a Python dict
- build the parsed `full_report`
- generate the rules-based violations
- print the results

## Notes

- The notebook expects the `parse_to_dict` function from
  `repo root > preprocessing > assessment_processor.py` to be available for
  the Word-document conversion step.
- The notebook is written to locate the repository root automatically, so it
  can still work if it is launched from the notebook folder or from the repo
  root.
