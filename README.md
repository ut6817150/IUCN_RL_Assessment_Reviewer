# IUCN Assessment Reviewer

![IUCN Kew header](assets/IUCN_Kew_header.png)

This repository contains the IUCN Assessment Reviewer developed for Kew
Gardens as part of the Imperial College London SWE group project. The tool is
a Streamlit web app for reviewing draft IUCN Red List assessments with three
complementary workflows:

- deterministic rules-based feedback
- LLM-based feedback driven by a structured prompt library
- retrieval-augmented generation (RAG) chat over IUCN reference documents and
  the uploaded draft assessment

The deployed web app is available on Hugging Face Spaces:

```text
https://huggingface.co/spaces/SWE-Group-Project/IUCN_Assessment_reviewer
```

The deployed app has been stress tested for Kew Gardens and can support 10
concurrent users on the same OpenRouter API key.

## What The App Does

The app accepts a draft assessment file, parses it once into a structured
assessment dictionary, and shares that parsed input across the main review
workflows.

Current supported upload formats:

- `.docx`
- `.html`
- `.htm`

The app then exposes four tabs:

- `Rules-based feedback`
  Runs deterministic Python checkers for formatting, punctuation,
  bibliography, numbers, dates, IUCN terminology, scientific names, spelling,
  symbols, tables, and related issues.
- `LLM feedback`
  Runs a fixed set of LLM review rules from
  `simplified_llm_api_script/prompt_library/rules/` and displays structured
  findings in a sortable triage table.
- `RAG chat (prototype)`
  Retrieves official IUCN reference evidence and relevant uploaded-draft
  sections, then uses the selected OpenRouter model to answer grounded review
  questions.
- `Download feedback`
  Exports available rules-based and/or LLM feedback to an Excel workbook.

## Run The Deployed App

Open the Hugging Face Space:

```text
https://huggingface.co/spaces/SWE-Group-Project/IUCN_Assessment_reviewer
```

The Space has been stress tested and can support 10 concurrent users sharing
the same OpenRouter API key.

Use the sidebar to:

1. upload an assessment document
2. enter or select an OpenRouter API key
3. choose an OpenRouter model
4. run the desired workflow from the main tabs

## Run Locally

### 1. Clone The Repository

Clone the GitHub source repository:

```bash
git clone https://github.com/ut6817150/IUCN_RL_Assessment_Reviewer.git
cd IUCN_RL_Assessment_Reviewer
```

SSH alternative:

```bash
git clone git@github.com:ut6817150/IUCN_RL_Assessment_Reviewer.git
cd IUCN_RL_Assessment_Reviewer
```

### 2. Create A Python Environment

Python 3.12 is recommended because the project has been developed and tested
against that environment.

```powershell
# Windows PowerShell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

From the repository root:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` includes the Streamlit runtime dependencies, document
parsing dependencies, RAG dependencies, unit-test dependencies, and lightweight
notebook support used by the evaluation notebooks.

### 4. Prepare An OpenRouter API Key

When running locally, users must provide their own OpenRouter API key:

```text
https://openrouter.ai/
```

The app assumes OpenRouter-backed model access for the LLM feedback and RAG
chat workflows.

The preconfigured API-key options are deployment-specific and will not work
after cloning the repository locally unless you also configure matching local
environment variables. For local development, use the sidebar option to enter
your own OpenRouter API key. The rules-based feedback tab does not require an
API key.

### 5. Start The App

From the repository root:

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## Repository Structure

```text
.
├── app.py                         Streamlit app entry point
├── requirements.txt               Runtime, test, and notebook dependencies
├── assets/                        Static images and app assets
├── ui/                            Streamlit sidebar and tab renderers
├── preprocessing/                 DOCX/HTML assessment parser
├── iucn_rules_checker/            Deterministic rules-based reviewer
├── simplified_llm_api_script/     LLM prompt-library reviewer
└── llm_rag/                       RAG reference retrieval and inference
```

## Top-Level Files

- `app.py`
  Main Streamlit entry point. It configures the page, renders the sidebar,
  caches the parsed upload, resets upload-scoped state when the file changes,
  and passes shared state into the rules-based, LLM, RAG, and download tabs.
- `requirements.txt`
  Python dependencies for running the app, tests, and notebook evaluation
  workflows.
- `.gitignore`
  Excludes Python caches, notebook checkpoints, OS files, local environments,
  and other non-source artifacts.
- `README.md`
  This repository-level guide.

## Subfolders

### `ui/`

The `ui/` folder contains the Streamlit presentation layer: sidebar setup, tab
rendering, result display, and download/export helpers used by `app.py`.

Start here:

```text
ui/README.md
```

### `preprocessing/`

The `preprocessing/` folder contains the document-ingestion pipeline that turns
uploaded `.docx`, `.html`, and `.htm` assessments into the structured
dictionary shared by the rules, LLM, and RAG workflows. It also includes the
fixtures and notebooks used to inspect and evaluate parser behaviour.

Start here:

```text
preprocessing/README.md
preprocessing/test_preprocessing/README.md
```

### `iucn_rules_checker/`

The `iucn_rules_checker/` package contains the deterministic review pipeline:
parsed-assessment normalisation, checker classes for different error types,
structured violations, and the supporting unit-test and notebook evaluation
workflows.

Start here:

```text
iucn_rules_checker/README.md
iucn_rules_checker/checkers/README.md
iucn_rules_checker/unittests/README.md
iucn_rules_checker/evaluation/README.md
iucn_rules_checker/test_word_document/README.md
```

### `simplified_llm_api_script/`

The `simplified_llm_api_script/` folder contains the LLM-based review engine:
prompt-library rules, section selection, model-provider integration,
structured-finding parsing, and the unit-test and evaluation material used to
refine prompt behaviour.

The prompt library currently covers category justification, geographic range,
population, habitats, use and trade, threats, conservation, bibliography,
reference formatting, acronym explanation, argument coherence, and
scientific/common-name formatting.

Start here:

```text
simplified_llm_api_script/README.md
simplified_llm_api_script/IUCN_LLM_checks.md
simplified_llm_api_script/docs/review_assessment_integration.md
simplified_llm_api_script/prompt_library/system_prompt.md
simplified_llm_api_script/prompt_library/rules/
```

### `llm_rag/`

The `llm_rag/` folder contains the retrieval-augmented generation system used
by the chat tab, including the reference-document corpus, preprocessing
outputs, retrieval/indexing code, inference-time prompt assembly, and
evaluation assets.

For the full RAG architecture, design decisions, rebuild commands, evaluation
notes, and future work, start with:

```text
llm_rag/README.md
llm_rag/DEVELOPMENT_HISTORY.md
llm_rag/evaluation/README.md
llm_rag/unit_tests/README.md
```

### `assets/`

The `assets/` folder stores static images and other lightweight visual assets
used by the app UI.

## Testing

The repository contains several test and evaluation layers. Install the root
dependencies first:

```bash
python -m pip install -r requirements.txt
```

### Rules-Based Unit Tests

From the repository root:

```bash
python -m unittest discover -s iucn_rules_checker/unittests -p "test_*.py"
```

More detail:

```text
iucn_rules_checker/unittests/README.md
```

### Assessment Parser Tests

The uploaded-assessment parser in `preprocessing/assessment_processor.py` is
tested through notebooks rather than a conventional pytest file. The notebooks
can be run from the repository root or from `preprocessing/test_preprocessing/`.

Unit-style parser checks:

```text
preprocessing/test_preprocessing/unit_tests.ipynb
```

This notebook contains focused parser checks for rich-text rendering, table
extraction, heading detection, DOCX parsing, HTML parsing, and error handling.
It uses generated DOCX/HTML fixtures plus selected real DOCX fixtures, and
prints `PASS` or `FAIL` for each test section.

Manual output inspection:

```text
preprocessing/test_preprocessing/test_output_format.ipynb
```

Batch parser evaluation:

```text
preprocessing/test_preprocessing/evaluation_tests_batch.ipynb
```

The batch evaluation notebook evaluates the DOCX fixture set in
`preprocessing/test_preprocessing/word assessment files/` and reports parser
quality metrics such as text similarity, schema completeness, heading recall,
rich-text coverage, and comment-structure checks.

### RAG Unit Tests

From the repository root:

```bash
python -m pytest -q llm_rag/unit_tests
```

More detail:

```text
llm_rag/unit_tests/README.md
```

### LLM Review Unit Tests

From the repository root:

```bash
python -m pytest -q simplified_llm_api_script/unit_tests
```

These tests use mock providers and do not require live LLM calls.

The `simplified_llm_api_script/grid_test.py` script is an evaluation runner
that makes live provider calls and writes to `simplified_llm_api_script/grid_outputs/`;
it is not part of the unit-test suite.

### Notebook Evaluation

Notebook-based inspection and evaluation workflows provide qualitative and
diagnostic assessment of the code. They are not just pass/fail unit tests; they
help reviewers inspect whether the generated outputs look useful, complete,
and faithful to the source material.

Notebook workflows live in:

```text
preprocessing/test_preprocessing/
iucn_rules_checker/evaluation/
iucn_rules_checker/test_word_document/
llm_rag/evaluation/
```

Examples of what the notebooks evaluate:

- `preprocessing/test_preprocessing/test_output_format.ipynb`
  Parses one selected `.docx`, `.html`, or `.htm` file and prints the parsed
  dictionary as formatted JSON for manual inspection.
- `preprocessing/test_preprocessing/unit_tests.ipynb`
  Runs controlled parser checks and selected real-document regressions for
  rich text, headings, tables, DOCX/HTML parsing, error handling, output
  invariants, and deterministic output.
- `preprocessing/test_preprocessing/evaluation_tests_batch.ipynb`
  Qualitatively and quantitatively checks parser output, including heading
  recall, text preservation, rich-text preservation, table-cell extraction,
  comments, raw DOCX/XML consistency checks, and overall parser quality across
  the fixture batch.
- `iucn_rules_checker/evaluation/evaluation.ipynb`
  Runs targeted checker sections from a purpose-built Word document so rule
  behavior can be inspected checker by checker.
- `iucn_rules_checker/test_word_document/test_word_document.ipynb`
  Runs the rules-based reviewer on a user-provided Word assessment and displays
  the resulting violations for manual inspection. During development, this
  workflow was used to spot check real IUCN assessment documents provided by
  Kew Gardens; those documents are not included in the repository for
  confidentiality reasons.
- `llm_rag/evaluation/smoke_and_inspection/`
  Contains notebooks for inspecting preprocessed reference assets, vector-db
  build outputs, deterministic threshold lookup, and broad retrieval behavior.
- `llm_rag/evaluation/retrieval_judging/`
  Generates retrieval-only prompts for external LLM judging so the team can
  assess whether the RAG system retrieved relevant, focused, and complete
  evidence before testing final answer quality.

## Reference And Generated Assets

Some folders contain generated or semi-generated assets that are part of the
RAG workflow:

- `llm_rag/ii_preprocessed_documents/`
  Preprocessed JSONL, manifests, and extracted table CSVs.
- `llm_rag/iii_vector_db/`
  Reference retrieval corpus files, build summaries, deterministic thresholds,
  and Chroma vector-db assets.

The Chroma database is a runtime database. If it is opened, queried, rebuilt,
or migrated by local tools, its files may be marked as modified by Git. See:

```text
llm_rag/iii_vector_db/chroma_db/README.md
llm_rag/iii_vector_db/chroma_db/reference_docs/README.md
```

for details on how those assets are generated and used.

## Development Notes

- The app is designed around the repository root as the working directory.
- UI modules import other project modules using repo-root package paths.
- The rules-based feedback tab can run without an API key.
- The LLM feedback and RAG chat tabs require an OpenRouter-compatible model
  configuration and API key.
- The RAG system separates official reference evidence from uploaded-draft
  evidence so users can distinguish guidance requirements from draft content.
- The RAG debug output is intended to make retrieval behavior inspectable
  during development and evaluation.

## Future Work

Likely next steps for the project are:

- improve deployment UX with authentication, safer per-user API-key storage,
  and better handling of long-running review sessions
- evaluate alternative document-conversion tooling such as
  [MarkItDown](https://github.com/microsoft/markitdown) without losing the
  structure needed by rules, LLM review, and RAG
- improve RAG retrieval by linking related chunks more explicitly and
  supporting better follow-up context across turns
- expand evaluation coverage with more assessments, more retrieval regression
  cases, and clearer before/after comparisons for retrieval changes
- extend the deterministic and LLM rule sets while reducing false positives
  and improving reviewer-facing triage metadata
