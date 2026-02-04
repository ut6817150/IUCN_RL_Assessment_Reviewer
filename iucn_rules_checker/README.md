# IUCN Checker

A Python-based linting tool that validates text against IUCN Red List assessment formatting, style, and terminology rules.

## Overview

IUCN Checker enforces standardized conventions for scientific assessments, including UK spelling, number formatting, date conventions, IUCN-specific terminology, and more. It can be used as a command-line tool or imported as a Python library.

## Features

- **11 specialized checkers** covering 50+ distinct rules
- **Accurate position tracking** with line/column information for each violation
- **Suggested fixes** for most violations
- **Flexible filtering** by category, severity, or specific rules
- **Multiple output formats** including JSON and pretty-printed summaries
- **No external dependencies** - uses only Python standard library
- **Dual interface** - CLI tool and importable Python library

## Installation

No installation required beyond Python 3.7+. Clone the repository and run directly:

```bash
git clone <repository-url>
cd code
```

## Usage

### Command Line

```bash
# Check a file
python -m iucn_checker input.txt

# Check from stdin
echo "The color of the species is grey." | python -m iucn_checker

# Pretty-print violations
python -m iucn_checker input.txt --pretty

# Show summary only
python -m iucn_checker input.txt --summary

# Output to JSON file
python -m iucn_checker input.txt -o report.json

# Filter by categories
python -m iucn_checker input.txt --categories Language Numbers

# Filter by minimum severity (error, warning, info)
python -m iucn_checker input.txt --severity warning

# Check plain text (skip formatting checks that require HTML tags)
python -m iucn_checker input.txt --plain-text

# List available categories
python -m iucn_checker --list-categories
```

### As a Python Library

```python
from iucn_checker import IUCNRuleChecker, check_text, Severity

# Quick check
report = check_text("Your assessment text here...")
print(report.to_json())

# Check with filtering options
checker = IUCNRuleChecker(
    enabled_categories={'Language', 'Numbers'},
    min_severity=Severity.WARNING
)
report = checker.check("Your assessment text here...")

# Iterate through violations
for violation in report.violations:
    print(f"Line {violation.position.line}: {violation.message}")
    if violation.suggested_fix:
        print(f"  Suggestion: {violation.suggested_fix}")
```

## Categories

The checker includes the following rule categories:

| Category | Description |
|----------|-------------|
| **Language** | UK spelling enforcement (colour, centre, grey, -ise endings) |
| **Numbers** | Number formatting (1-9 as words, commas for thousands) |
| **Dates** | Date conventions (no ordinals, numeric centuries) |
| **Abbreviations** | Abbreviation rules (et al., etc., Latin terms) |
| **Symbols** | Units and symbols (km², °, %) |
| **Punctuation** | Punctuation standards (en-dashes for ranges) |
| **IUCN Terms** | IUCN-specific terminology (no "the IUCN", category capitalization) |
| **Geography** | Geographic naming (ISO 3166 country names) |
| **Scientific Names** | Species name formatting (spp., sp., italics) |
| **References** | Citation formatting (author separators, et al.) |
| **Formatting** | Text formatting rules (italics usage — requires HTML-tagged input) |

> **Note:** The Formatting category checks for correct use of italics via HTML tags (`<i>`, `<em>`). If your input is plain text without HTML markup, use the `--plain-text` flag to skip these checks and avoid false positives.

## Output Format

Reports are output in JSON format with the following structure:

```json
{
  "summary": {
    "text_length": 1234,
    "total_violations": 5,
    "by_severity": {
      "error": 1,
      "warning": 3,
      "info": 1
    },
    "by_category": {
      "Language": 2,
      "Numbers": 3
    }
  },
  "violations": [
    {
      "rule_id": "spelling_uk",
      "rule_name": "UK English spelling required",
      "category": "Language",
      "matched_text": "color",
      "position": {
        "start": 42,
        "end": 47,
        "line": 2,
        "column": 15
      },
      "severity": "warning",
      "message": "Use UK spelling 'colour' instead of 'color'",
      "suggested_fix": "colour",
      "context": "...the color of the..."
    }
  ]
}
```

## Exit Codes

When used as a CLI tool:

| Code | Meaning |
|------|---------|
| 0 | No violations found |
| 1 | Warnings or info-level violations found |
| 2 | Errors found |

## Project Structure

```
code/
├── iucn_checker/
│   ├── __init__.py          # Package exports
│   ├── __main__.py          # CLI entry point
│   ├── main.py              # CLI argument parsing
│   ├── engine.py            # Core checking orchestration
│   ├── models.py            # Data models (Violation, Report)
│   └── checkers/            # Rule implementations
│       ├── base.py          # Abstract base classes
│       ├── spelling.py      # UK spelling rules
│       ├── numbers.py       # Number formatting
│       ├── dates.py         # Date formatting
│       ├── abbreviations.py # Abbreviation rules
│       ├── symbols.py       # Symbols and units
│       ├── punctuation.py   # Punctuation rules
│       ├── iucn_terms.py    # IUCN terminology
│       ├── geography.py     # Geographic naming
│       ├── scientific.py    # Scientific names
│       ├── references.py    # Citation formatting
│       └── formatting.py    # Text formatting
├── IUCN_Assessment_Rules.json
└── IUCN_Assessment_Rules.xlsx
```

## Examples

### Checking an Assessment

```bash
python -m iucn_checker assessment.txt --pretty
```

Sample output:

```
IUCN Rule Checker Report
========================

Violations Found: 3

[WARNING] Line 5, Col 12 (Language)
  Rule: UK English spelling required
  Found: "color"
  Message: Use UK spelling 'colour' instead of 'color'
  Suggestion: colour

[WARNING] Line 8, Col 1 (Numbers)
  Rule: Numbers at sentence start
  Found: "5 species"
  Message: Spell out numbers at the start of a sentence
  Suggestion: Five species

[INFO] Line 12, Col 23 (IUCN Terms)
  Rule: IUCN without article
  Found: "the IUCN"
  Message: Use 'IUCN' without 'the'
  Suggestion: IUCN
```

### CI/CD Integration

```bash
# Exit with non-zero status if errors found
python -m iucn_checker assessment.txt --severity error
if [ $? -eq 2 ]; then
    echo "Assessment contains errors"
    exit 1
fi
```

## Requirements

- Python 3.7 or higher
- No external dependencies

## License

This project was developed as part of an academic group project at Imperial College London.
