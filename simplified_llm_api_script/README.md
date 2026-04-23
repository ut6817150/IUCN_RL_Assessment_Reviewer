# IUCN LLM Assessment Checker

Runs structured LLM-based quality checks against parsed IUCN Red List species
assessment documents. Each check is defined as a markdown rule file; the engine
selects the relevant sections of the assessment, calls the configured LLM, and
returns structured findings.

---

## Directory Structure

```
simplified_llm_api_script/
├── llm_checker_v2.py          # Main module: LLM providers, rule evaluation, entry points
├── assessment_processor.py    # Converts DOCX/HTML assessment documents → structured JSON
├── grid_test.py               # Evaluation runner: tests a matrix of providers × models
├── IUCN_LLM_checks.md         # Source notes for the rule set
│
├── prompt_library/
│   ├── system_prompt.md       # Base system prompt sent to the LLM on every call
│   └── rules/
│       ├── rule_01_justification_category.md
│       ├── rule_02_consistency_geographic_range.md
│       ├── rule_03_consistency_population.md
│       ├── rule_04_consistency_habitats.md
│       ├── rule_05_consistency_use_and_trade.md
│       ├── rule_06_consistency_threats.md
│       ├── rule_07_consistency_conservation.md
│       ├── rule_08_consistency_bibliography.md
│       ├── rule_09_formatting_references.md
│       ├── rule_10_minor_check_acronyms.md
│       ├── rule_11_minor_check_argument_coherence.md
│       └── rule_12_formatting_scientific_common_name.md
│
├── json_converted/            # Example assessment inputs (JSON trees)
├── grid_outputs/              # Generated results from grid_test.py runs
├── unit_tests/                # Unit tests for rule selection/orchestration helpers
├── docs/                      # Integration notes for calling review_assessment
└── evaluation/                # Evaluation spreadsheets and test files, when present
```

---

## Setup

Install dependencies from the repository root:

```bash
python3 -m pip install -r requirements.txt
```

The root `requirements.txt` covers the dependencies used by this folder.
If you are already inside `simplified_llm_api_script/`, use
`python3 -m pip install -r ../requirements.txt`.

For command-line use, provide the API key for the provider you intend to call.
You can place these in a `.env` file in the repository root or export them in
your shell:

```
OPENROUTER_KEY=your_openrouter_key
ANTHROPIC_API_KEY=your_anthropic_key
HUGGINGFACE_TOKEN=your_huggingface_token
```

Only the key for the provider you intend to use is required.

---

## CLI Usage

Run from `simplified_llm_api_script/`:

```bash
python3 llm_checker_v2.py json_converted/Test1_Bulbostylis\ atracuminata\ IUCN\ Draft2_JP.json --provider openrouter --mode sequential
```

| Argument | Default | Description |
|---|---|---|
| `json_file` | legacy fallback path | Path to an assessment JSON file. Pass this explicitly. |
| `--provider` | `openrouter` | LLM provider |
| `--model` | provider default | Model name override |
| `--mode` | `sequential` | `sequential`: one rule at a time (rate-limit safe); `concurrent`: all rules in parallel |

**Default models per provider:**

| Provider | Default model |
|---|---|
| `anthropic` | `claude-sonnet-4.6` |
| `openrouter` | `google/gemma-4-31b-it` |
| `huggingface` | `deepseek-ai/DeepSeek-R1:novita` |

**Example:**

```bash
python3 llm_checker_v2.py json_converted/Test2_Calamus_heatubunii_JPComms.json --provider openrouter --model google/gemma-4-31b-it --mode sequential
```

Output is a JSON array of rule results printed to stdout.

---

## Prompt Library

Each rule file in `prompt_library/rules/` has two parts:

**Frontmatter** (YAML) — controls how the engine uses the rule:

```yaml
---
scope: "relevant_sections: Threats, Redlist Assessment"
severity: high
category: section_consistency
---
```

- `scope`: Determines which parts of the assessment document are passed to the LLM:
  - `full_document` — entire tree
  - `relevant_sections: Section A, Section B` — named sections only
  - `section_type:*` — evaluates the rule once per top-level child section
- `severity`: Default severity label attached to findings from this rule
- `category`: Grouping label (e.g. `section_consistency`, `minor_check`, `formatting`)

**Body** — the markdown prompt text sent to the LLM describing what to check and how to report it.

The `system_prompt.md` instructs the LLM to respond only in JSON:
```json
{"rule_name": "rule_name_here", "findings": [...]}
```

---

## Assessment Input Format

Assessments are represented as a hierarchical JSON tree. This is the format produced by `assessment_processor.py` when parsing a DOCX or HTML file.

```json
{
  "title": "species_name",
  "level": 0,
  "path": [],
  "blocks": [
    {"type": "paragraph", "text": "..."},
    {"type": "table", "rows": [[...]]}
  ],
  "children": [
    {
      "title": "Threats",
      "level": 1,
      "path": ["Threats"],
      "blocks": [...],
      "children": [...]
    }
  ]
}
```

To convert DOCX/HTML files in batch mode, create a local `converted/` folder in
this directory, put the source files there, and run:

```bash
python3 assessment_processor.py
```

Batch mode reads from `converted/` and writes parsed JSON files to
`json_converted/`. To parse a single file and print JSON to stdout:

```bash
python3 assessment_processor.py path/to/assessment.docx
```

---

## Output Format

`review_assessment()` returns:

```json
{
  "rule_06_consistency_threats": [
    {
      "section_path": "Threats > Classification Scheme",
      "issue": "Threat X is listed here but absent from the Redlist Assessment narrative.",
      "severity": "high",
      "suggestion": "Add threat X to the Redlist Assessment or remove it from the threats table."
    }
  ],
  "rule_04_consistency_habitats": []
}
```

Rules with no findings return an empty list. Rules that failed due to an LLM error also return an empty list.

---

## Grid Testing

`grid_test.py` runs all assessments in `json_converted/` against a configurable
matrix of `(provider, model)` pairs. The matrix is defined in the `GRID` list at
the top of the file. This is an evaluation workflow; the main reviewer does not
read `grid_outputs/`.

```bash
python3 grid_test.py [--docs STEM ...] [--delay SECONDS]
```

| Argument | Default | Description |
|---|---|---|
| `--docs STEM ...` | all documents | Filter documents by filename stem substring. E.g. `--docs Test1 Test2` runs only files whose stem contains "Test1" or "Test2" |
| `--delay SECONDS` | `2.0` | Seconds to wait between each `(doc, model)` run |

Rules within a single run fire concurrently for normal models, and sequentially for OpenRouter `:free` models (which have tight rate limits).

Results are written to `grid_outputs/` as:

- `{doc_stem}/{provider}__{model_slug}.json` — findings only
- `{doc_stem}/{provider}__{model_slug}_meta.json` — full metadata (token usage, timing, errors)
- `_grid_summary.json` — aggregate across all runs

---

## Programmatic Use

The main handover function is `review_assessment(...)` in `llm_checker_v2.py`.
It accepts a parsed assessment dictionary and returns a dictionary keyed by rule
name:

```python
import asyncio
import json

from llm_checker_v2 import review_assessment

with open("json_converted/Test2_Calamus_heatubunii_JPComms.json", encoding="utf-8") as f:
    assessment = json.load(f)

results = asyncio.run(review_assessment(assessment))
```

See `docs/review_assessment_integration.md` for provider configuration examples.

---

## Tests

From the repository root:

```bash
python3 -m pytest simplified_llm_api_script/unit_tests
```
