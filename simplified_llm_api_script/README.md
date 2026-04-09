# IUCN LLM Assessment Checker

Runs structured LLM-based quality checks against IUCN Red List species assessment documents. Each check is defined as a markdown rule file; the engine selects the relevant sections of the assessment, calls the configured LLM, and returns structured findings.

---

## Directory Structure

```
simplified_llm_api_script/
├── llm_checker_v2.py          # Main module: LLM providers, rule evaluation, entry points
├── assessment_processor.py    # Converts DOCX/HTML assessment documents → structured JSON
├── grid_test.py               # Grid search runner: tests a matrix of providers × models
│
├── prompt_library/
│   ├── system_prompt.md       # Base system prompt sent to the LLM on every call
│   └── rules/
│       ├── rule_01_consistency_threats.md
│       ├── rule_02_consistency_habitats.md
│       ├── rule_03_consistency_bibliography.md
│       ├── rule_04_consistency_geographic_range.md
│       ├── rule_05_consistency_population.md
│       ├── rule_06_consistency_conservation.md
│       ├── rule_07_justification_category.md
│       ├── rule_08_formatting_references.md
│       ├── rule_09_formatting_scientific_common_name.md
│       ├── rule_10_minor_check_acronyms.md
│       └── rule_11_minor_check_argument_coherence.md
│
├── json_converted/            # Example assessment inputs (JSON trees)
├── converted/                 # Source DOCX/HTML files for assessment_processor
├── grid_outputs/              # Results from grid_test.py runs
│
├── requirements.txt
└── .env                       # API keys (not committed)
```

---

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in this directory:

```
OPENROUTER_KEY=your_openrouter_key
ANTHROPIC_API_KEY=your_anthropic_key
HUGGINGFACE_TOKEN=your_huggingface_token
```

Only the key for the provider you intend to use is required.

---

## CLI Usage

```bash
python llm_checker_v2.py [json_file] --provider [anthropic|openrouter|huggingface] --model [model_name] --mode [sequential|concurrent]
```

| Argument | Default | Description |
|---|---|---|
| `json_file` | bundled example | Path to an assessment JSON file |
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
python llm_checker_v2.py json_converted/my_assessment.json --provider anthropic --mode sequential
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

To convert a DOCX file: run `assessment_processor.py` (it reads from `converted/`, writes to `json_converted/`).

---

## Output Format

`review_assessment()` returns:

```json
{
  "rule_01_consistency_threats": [
    {
      "section_path": "Threats > Classification Scheme",
      "issue": "Threat X is listed here but absent from the Redlist Assessment narrative.",
      "severity": "high",
      "suggestion": "Add threat X to the Redlist Assessment or remove it from the threats table."
    }
  ],
  "rule_02_consistency_habitats": []
}
```

Rules with no findings return an empty list. Rules that failed due to an LLM error also return an empty list.

---

## Grid Testing

`grid_test.py` runs all assessments in `json_converted/` against a configurable matrix of `(provider, model)` pairs. Results are written to `grid_outputs/` as:

- `{provider}__{model_slug}.json` — findings only
- `{provider}__{model_slug}_meta.json` — full metadata (token usage, timing, errors)
- `_grid_summary.json` — aggregate across all runs
