# IUCN Rules Checker

The rules checker is the deterministic review component of this project. It is
meant to take a parsed IUCN assessment, run a fixed set of rule-based checks
over the content, and return structured violations for issues such as
formatting, terminology, references, spelling, dates, numbers, and related
review concerns.

It does this by parsing an assessment tree into a flat report and running the
package's rules-based review flow on the parsed content.

This package also powers the repo-level Streamlit interface in `app.py`.

For rule-by-rule checker behavior, see:

- `checkers/README.md`

## Files And Project Structure

```text
iucn_rules_checker/
|- assessment_parser.py
|- assessment_reviewer.py
|- violation.py
|- checkers/
|- unittests/
|- evaluation/
|- test_word_document/
`- README.md
```

Quick guide to the contents of this folder:

| Path | Purpose |
| --- | --- |
| `assessment_parser.py` | Flattens a structured assessment dictionary into the `section_name -> text` mapping used by the reviewer. |
| `assessment_reviewer.py` | Runs the rules-based review flow over a parsed report and returns `Violation` objects. |
| `violation.py` | Defines the shared `Violation` dataclass used across the package. |
| `checkers/` | Checker implementations plus shared checker utilities. See `checkers/README.md` for rule-level documentation. |
| `unittests/` | Standard-library regression tests for the parser, reviewer, and checker modules. |
| `evaluation/` | Notebook and supporting assets used to inspect and refine rules-based behaviour. |
| `test_word_document/` | Notebook workflow for running the reviewer on a user-supplied `.docx` assessment. |
| `README.md` | Package-level overview and usage notes. |

## Testing And Evaluation

Testing material for the rules checker is grouped into three folders:

- `unittests/`
  Standard-library `unittest` suite for parser, reviewer, and checker
  regressions.
- `evaluation/`
  Contains `evaluation.ipynb`, `test_doc_rules_based.docx`, and
  `IUCN_submissions_evaluation.xlsx` for notebook-based inspection and
  evaluation of rule behaviour.
- `test_word_document/`
  Contains `test_word_document.ipynb`, a notebook for running the reviewer on
  your own `.docx` assessment file. The original Kew sample document is not
  included in this repository for confidentiality reasons.

Run the full unit-test suite from the repository root:

```bash
python -m unittest discover -s iucn_rules_checker/unittests -p "test_*.py"
```

Run selected test modules:

```bash
python -m unittest iucn_rules_checker.unittests.test_assessment_parser
python -m unittest iucn_rules_checker.unittests.test_assessment_reviewer
```

The notebook workflows in `evaluation/` and `test_word_document/` first
convert a Word document to a Python dictionary using
`preprocessing/assessment_processor.py`, then run the parser and reviewer on
that structured data.

To test your own `.docx` assessment, open
`test_word_document/test_word_document.ipynb`, set `CUSTOM_DOCX_PATH` to your
file path, and run the notebook cells.

## Requirements

### Runtime Dependencies

The core Python code in `iucn_rules_checker/` uses only the Python standard library.

### Optional Tooling

- Jupyter
  Needed only if you want to run the notebooks in:
  - `evaluation/evaluation.ipynb`
  - `test_word_document/test_word_document.ipynb`
- `python-docx`
  Needed for workflows that first convert Word documents to a Python dict
  using the `parse_to_dict` function from `repo root > preprocessing > assessment_processor.py`
- `beautifulsoup4`
  Also needed for that Word-document conversion step

## Core Workflow And Classes

The core rules-checker flow has two main stages:

1. `AssessmentParser` converts a structured assessment dictionary into a flat
   report.
2. `IUCNAssessmentReviewer` runs the configured checkers over that flat report
   and returns `Violation` objects.

The sections below describe the main classes and helper abstractions involved
in that workflow.

## AssessmentParser

`AssessmentParser` expects a Python `dict` representing the structured
assessment tree used in this project.

Expected structure:

- each node has a `title`
- each node has a `blocks` list
- each node has a `children` list

Current parser behavior:

- walks the tree recursively
- builds keys like:
  - `Title [paragraph 1]`
  - `Title > Section > Subsection [paragraph 2]`
  - `Title > Section [table 1] [row 3]`
- uses `text_rich` only for paragraph blocks
- uses `rows_rich` only for table blocks
- emits one output entry per table row, not one per table
- preserves Unicode characters and normalizes non-breaking spaces to regular
  spaces
- ignores `style` blocks entirely

Parser input:

- hierarchical assessment `dict`

Parser output:

- `dict[str, str]`
  - keys are parsed section/block paths
  - values are the corresponding paragraph or table-row strings

Example:

```python
from iucn_rules_checker.assessment_parser import AssessmentParser

assessment = {
    "title": "Root",
    "blocks": [
        {"type": "paragraph", "text_rich": "Draft"},
        {"type": "table", "rows_rich": [["Status"], ["LC - Least Concern"]]},
    ],
    "children": [],
}

full_report = AssessmentParser().parse(assessment)
print(len(full_report))
print(next(iter(full_report.items())))
```

## IUCNAssessmentReviewer

`IUCNAssessmentReviewer` reviews an already parsed report.

The intended workflow is explicitly two-step:

1. run `AssessmentParser.parse(assessment)` to build a flat `full_report`
2. pass that `full_report` into
   `IUCNAssessmentReviewer.review_full_report(...)`

Current reviewer behavior:

- skips empty sections
- routes parsed table sections to a dedicated `TableChecker`
- routes bibliography sections to a dedicated `BibliographyChecker`
- runs all other non-table, non-bibliography sections through the normal checker list
- calls `begin_sweep()` on every checker before a review pass
- calls `end_sweep()` on every checker after the pass finishes

### Section Routing

Parsed table sections are routed to `self.table_checker` only:

- `TableChecker`

Current `TableChecker` behavior combines:

- `AbbreviationChecker.check_et_al(...)`

Normal non-bibliography sections are checked by `self.checkers`:

- `AbbreviationChecker`
- `DateChecker`
- `FormattingChecker`
- `GeographyChecker`
- `IUCNTermsChecker`
- `NumberChecker`
- `PunctuationChecker`
- `ReferenceChecker`
- `ScientificNameChecker`
- `SpellingChecker`
- `SymbolChecker`

Bibliography sections are routed to `self.bibliography_checker` only:

- `BibliographyChecker`

Current `BibliographyChecker` behavior combines:

- `check_ampersand_usage(...)`
- `AbbreviationChecker.check_et_al(...)`
- `PunctuationChecker.check_range_dashes(...)`

Example:

```python
from iucn_rules_checker.assessment_reviewer import IUCNAssessmentReviewer

full_report = {
    "Assessment > Notes [paragraph 1]": "Examples occur e.g. in text.",
    "Assessment > Notes [table 1] [row 1]": "Smith et al. 2020",
    "Assessment > Bibliography [paragraph 1]": "Smith & Jones 2020. Journal 10-20.",
}

reviewer = IUCNAssessmentReviewer()
violations = reviewer.review_full_report(full_report)
cleaned_violations = reviewer.clean_up_violations(list(violations))

print(f"Violations: {len(cleaned_violations)}")
print(cleaned_violations[0].to_dict())
```

### `clean_up_violations(...)`

`clean_up_violations(...)` is a helper on `IUCNAssessmentReviewer` that strips
simple inline markup from:

- `matched_text`
- `matched_snippet`
- `message`

It removes these tags only:

- italic tags: `<i>`, `<em>`
- bold tags: `<b>`, `<strong>`
- superscript tags: `<sup>`
- subscript tags: `<sub>`

## Violation Objects

Each rule hit is returned as a `Violation` object.

Current fields:

- `rule_class`
- `rule_method`
- `matched_text`
- `matched_snippet`
- `message`
- `suggested_fix`
- `section_name`

Meaning of the text-related fields:

- `matched_text`
  The exact span that triggered the rule.
- `matched_snippet`
  A short nearby context snippet.
- `section_name`
  The display section name. Paragraph suffixes such as `[paragraph 2]` are
  normalized away when violations are created.

Example `to_dict()` output:

```json
{
  "rule_class": "SpellingChecker",
  "rule_method": "SpellingChecker.check_text",
  "section_name": "Assessment > Geographic Range",
  "matched_text": "color",
  "matched_snippet": "the color of the species",
  "message": "Use UK spelling 'colour' instead of 'color'",
  "suggested_fix": "colour"
}
```

## Checker Framework

All checker classes inherit from `checkers/base.py`.

Shared methods include:

- `begin_sweep()`
- `end_sweep()`
- `check_text(section_name, text)`
- `strip_style_markers(...)`
- `create_violation(...)`
- `normalize_section_name(...)`
- `get_rule_method_name()`

`strip_style_markers(...)` can selectively remove:

- italic tags: `<i>`, `<em>`
- bold tags: `<b>`, `<strong>`
- superscript tags: `<sup>`
- subscript tags: `<sub>`

It returns:

- cleaned text
- an index map from cleaned positions back to original-text positions

That lets a checker match against normalized text but still create violations
against the original rich-text source.

## Checker Modules

Checker modules currently present in `checkers/`:

- `abbreviations.py`
- `bibliography.py`
- `dates.py`
- `formatting.py`
- `geography.py`
- `iucn_terms.py`
- `numbers.py`
- `punctuation.py`
- `references.py`
- `scientific.py`
- `spelling.py`
- `symbols.py`

See `checkers/README.md` for the method-by-method rule documentation.

## Adding Or Updating Rules

### Add A Rule To An Existing Checker

1. Open the relevant checker module under `checkers/`.
2. Add the logic inside `check_text(...)` or a helper method it calls.
3. Create violations with `self.create_violation(...)`.
4. Add regression coverage in the matching file under `unittests/`.

Example:

```python
violations.append(
    self.create_violation(
        section_name=section_name,
        text=text,
        span=match.span(),
        message="Describe the problem here",
        suggested_fix="corrected text",
    )
)
```

### Add A New Checker

1. Create a new checker under `checkers/` as a `BaseChecker` subclass.
2. Implement `check_text(...)`.
3. Wire it into `IUCNAssessmentReviewer.__init__`:
   add it to `self.checkers` for normal sections, or compose it into
   `self.bibliography_checker` if it should only run on bibliography content.
4. Add tests under `unittests/`.

Minimal skeleton:

```python
from typing import List

from .base import BaseChecker
from ..violation import Violation


class MyChecker(BaseChecker):
    def check_text(self, section_name: str, text: str) -> List[Violation]:
        violations: List[Violation] = []
        return violations
```

## Related Documentation

- `checkers/README.md`
  Detailed checker and rule documentation.
- `evaluation/README.md`
  Notes on the rules-based evaluation workflow.
- `test_word_document/README.md`
  Notes on the sample Word-document testing workflow.

## License

Developed as part of an academic group project at Imperial College London.
