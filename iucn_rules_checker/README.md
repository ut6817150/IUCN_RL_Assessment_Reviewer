# IUCN Rules Checker

A Python-based linting tool that validates text against IUCN Red List assessment formatting, style, and terminology rules.

## Overview

IUCN Rules Checker enforces standardized conventions for scientific assessments, including UK spelling, number formatting, date conventions, IUCN-specific terminology, and more. It can be used as a command-line tool, imported as a Python library, or integrated with a Streamlit frontend via JSON input.

## Features

- **12 specialized checkers** covering 50+ distinct rules
- **Accurate position tracking** with line/column information for each violation
- **Suggested fixes** for most violations
- **Flexible filtering** by category, severity, or specific rules
- **Multiple output formats** including JSON and pretty-printed summaries
- **Dual input modes** - plain text or Streamlit hierarchical JSON
- **Dual interface** - CLI tool and importable Python library
- **Comprehensive test suite** covering all major checkers

## Installation

Requires Python 3.7+. Clone the repository and run directly:

```bash
git clone <repository-url>
cd iucn_rules_checker
```

### Dependencies

```
beautifulsoup4  # for HTML processing
pytest>=7.0.0  # for running tests
```

### Development Setup (Recommended)

For development and testing, set up a virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install in editable mode with dependencies
pip install -e .

# Install testing dependencies
pip install pytest pytest-cov beautifulsoup4
```


## Usage

### Command Line

```bash
# Check a file
python -m iucn_rules_checker input.txt

# Check from stdin
echo "The color of the species is grey." | python -m iucn_rules_checker

# Pretty-print violations
python -m iucn_rules_checker input.txt --pretty

# Show summary only
python -m iucn_rules_checker input.txt --summary

# Output to JSON file
python -m iucn_rules_checker input.txt -o report.json

# Filter by categories
python -m iucn_rules_checker input.txt --categories Language Numbers

# Filter by minimum severity (error, warning, info)
python -m iucn_rules_checker input.txt --severity warning

# Check plain text (skip formatting checks that require HTML tags)
python -m iucn_rules_checker input.txt --plain-text

# List available categories
python -m iucn_rules_checker --list-categories
```

### As a Python Library

```python
from iucn_rules_checker import IUCNRuleChecker, check_text, Severity

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

### Checking Streamlit JSON Input

The checker supports the hierarchical JSON format produced by the Streamlit frontend, where sections appear as `children` and text content lives in `blocks`:

```python
import json
from iucn_rules_checker import IUCNRuleChecker

with open('assessment.json', 'r') as f:
    assessment_json = json.load(f)

checker = IUCNRuleChecker()
report = checker.check_json(assessment_json)

print(f"Total violations: {report.total_violations}")
for violation in report.violations:
    print(f"[{violation.severity.value.upper()}] {violation.message}")
```

You can also use the standalone script for quick inspection:

```bash
python show_json_violations.py assessment.json
```

### Demo and Examples

```bash
# Run the quick demo
python demo.py

# See full usage examples including JSON workflow
python usage_examples.py
```

## Testing

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_formatting.py -v

# Run tests with coverage report
python -m pytest tests/ --cov=checkers --cov-report=html

# Run tests with detailed output
python -m pytest tests/ -v -s
```

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures
├── test_checkers.py         # General checker tests
├── test_formatting.py       # Scientific name and italics tests
├── test_numbers.py          # Number formatting tests
├── test_punctuation.py      # En-dash and punctuation tests
├── test_spelling.py         # UK/US spelling tests
├── test_integration.py      # End-to-end tests
├── test_edge_cases.py       # Edge cases and performance
├── test_cli.py              # Command-line interface tests
├── test_family_names.py     # Taxonomic family name tests
└── test_new_rules.py        # Tests for recently added rules
```

## Categories

The checker includes the following rule categories:

| Category | Description |
|----------|-------------|
| **Language** | Language and style issues (passive voice, vague wording) |
| **Spelling** | UK spelling enforcement (colour, centre, grey, -ise endings) |
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
iucn_rules_checker/
├── checkers/
│   ├── __init__.py          # Package exports
│   ├── base.py              # Abstract base classes
│   ├── spelling.py          # UK spelling rules
│   ├── language.py          # Language and style rules
│   ├── numbers.py           # Number formatting
│   ├── dates.py             # Date formatting
│   ├── abbreviations.py     # Abbreviation rules
│   ├── symbols.py           # Symbols and units
│   ├── punctuation.py       # Punctuation rules
│   ├── iucn_terms.py        # IUCN terminology
│   ├── geography.py         # Geographic naming
│   ├── scientific.py        # Scientific names
│   ├── references.py        # Citation formatting
│   └── formatting.py        # Text formatting (requires HTML input)
├── tests/                   # Comprehensive test suite
│   ├── conftest.py
│   ├── test_checkers.py
│   ├── test_formatting.py
│   ├── test_numbers.py
│   ├── test_punctuation.py
│   ├── test_spelling.py
│   ├── test_integration.py
│   ├── test_edge_cases.py
│   ├── test_cli.py
│   ├── test_family_names.py
│   └── test_new_rules.py
├── engine.py                # Core checking orchestration
├── models.py                # Data models (Violation, Report, Severity)
├── html_processor.py        # HTML parsing utilities (uses BeautifulSoup)
├── streamlit_json_validator.py  # Validator for Streamlit JSON format
├── main.py                  # CLI entry point
├── __main__.py              # Allows `python -m iucn_rules_checker`
├── __init__.py              # Public API exports
├── demo.py                  # Quick demo script
├── usage_examples.py        # Extended usage examples
├── show_json_violations.py  # CLI script for JSON violation inspection
├── setup.py                 # Package configuration
└── sample.json              # Example Streamlit JSON assessment
```

## Examples

### Checking an Assessment

```bash
python -m iucn_rules_checker assessment.txt --pretty
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
python -m iucn_rules_checker assessment.txt --severity error
if [ $? -eq 2 ]; then
    echo "Assessment contains errors"
    exit 1
fi
```

## Requirements

- Python 3.7 or higher
- `beautifulsoup4` (for HTML processing)
- `pytest 7.0+` (for running tests)

## License

This project was developed as part of an academic group project at Imperial College London.
