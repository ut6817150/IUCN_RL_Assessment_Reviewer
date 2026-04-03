# IUCN Reviewer

This repository contains the Streamlit app and the rule-based checking package
used for reviewing IUCN assessment JSON files.

Main entry points:

- `app.py`
  Streamlit interface for uploading an assessment and viewing checker output.
- `iucn_rules_checker/assessment_parser.py`
  Converts a hierarchical assessment JSON tree into a flat `full_report`.
- `iucn_rules_checker/assessment_reviewer.py`
  Runs the configured checker classes over that parsed `full_report`.

Documentation:

- `iucn_rules_checker/README.md`
  Package-level usage, parser/reviewer flow, project structure, and unit-test commands.
- `iucn_rules_checker/checkers/README.md`
  Method-by-method checker behavior, including what each rule catches and misses.

Typical flow:

1. Parse the assessment JSON with `AssessmentParser.parse(...)`.
2. Review the parsed `full_report` with `IUCNAssessmentReviewer.review_full_report(...)`.
3. Inspect the returned `Violation` objects in the app, notebook, or tests.

Tests are designed to be run from the repository root:

```bash
python -m unittest discover -s iucn_rules_checker/unittests -p "test_*.py"
```
