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
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
python -m venv .venv
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

The `ui/` folder contains the Streamlit UI helper modules imported by
repo-root `app.py`.

Main responsibilities:

- sidebar upload, API-key, and model selection
- rules-based feedback tab rendering
- LLM feedback tab rendering and result triage display
- RAG chat tab rendering
- downloadable feedback workbook creation

Important files:

- `ui/app_sidebar.py`
- `ui/app_config.py`
- `ui/app_rules_tab.py`
- `ui/app_llm_tab.py`
- `ui/app_rag_tab.py`
- `ui/app_download_tab.py`

For more detail, see:

```text
ui/README.md
```

### `preprocessing/`

The `preprocessing/` folder contains the assessment parser used to convert
uploaded `.docx`, `.html`, and `.htm` files into the structured dictionary used
by the rest of the app.

Main responsibilities:

- parse heading structure
- extract paragraphs, lists, tables, comments, and rich-text fields
- expose `parse_to_dict(...)` for app and notebook use
- provide notebooks for parser inspection, unit-style checks, and batch
  evaluation over fixture documents

Important files and folders:

- `preprocessing/assessment_processor.py`
- `preprocessing/test_preprocessing/`
  Parser notebooks and DOCX fixtures.

For more detail, see:

```text
preprocessing/README.md
preprocessing/test_preprocessing/README.md
```

### `iucn_rules_checker/`

The `iucn_rules_checker/` package contains the deterministic rules-based
review system.

Main responsibilities:

- flatten parsed assessment trees into section text
- route normal sections, table rows, and bibliography sections to the right
  checker classes
- return structured `Violation` objects
- provide unit tests and notebook-based evaluation assets

Important files and folders:

- `iucn_rules_checker/assessment_parser.py`
- `iucn_rules_checker/assessment_reviewer.py`
- `iucn_rules_checker/violation.py`
- `iucn_rules_checker/checkers/`
- `iucn_rules_checker/unittests/`
- `iucn_rules_checker/evaluation/`
- `iucn_rules_checker/test_word_document/`

For more detail, see:

```text
iucn_rules_checker/README.md
iucn_rules_checker/checkers/README.md
iucn_rules_checker/unittests/README.md
iucn_rules_checker/evaluation/README.md
iucn_rules_checker/test_word_document/README.md
```

### `simplified_llm_api_script/`

The `simplified_llm_api_script/` folder contains the structured LLM review
engine used by the LLM feedback tab.

Main responsibilities:

- load Markdown rule files from `prompt_library/rules/`
- select relevant assessment sections for each rule
- call OpenRouter-compatible, Anthropic, or Hugging Face providers through
  provider abstractions
- parse structured JSON findings
- expose `review_document(...)` and `provider_from_config(...)` for the app

Important files and folders:

- `simplified_llm_api_script/llm_checker_v2.py`
- `simplified_llm_api_script/grid_test.py`
- `simplified_llm_api_script/IUCN_LLM_checks.md`
- `simplified_llm_api_script/json_converted/`
  Example parsed assessment JSON files used by the CLI and evaluation runner.
- `simplified_llm_api_script/grid_outputs/`
  Generated grid-evaluation outputs. These are not read by the app runtime.
- `simplified_llm_api_script/evaluation/`
  Evaluation spreadsheets and test files, when present.
- `simplified_llm_api_script/prompt_library/system_prompt.md`
- `simplified_llm_api_script/prompt_library/rules/`
- `simplified_llm_api_script/unit_tests/`
- `simplified_llm_api_script/docs/review_assessment_integration.md`

The optional `simplified_llm_api_script/converted/` folder is only a local
input folder for regenerating parsed JSON with `assessment_processor.py`; the
reviewer itself consumes parsed dictionaries or JSON files.

The prompt library currently includes rules for category justification,
geographic range, population, habitats, use and trade, threats, conservation,
bibliography, reference formatting, acronym explanation, argument coherence,
and scientific/common-name formatting.

For more detail, see:

```text
simplified_llm_api_script/README.md
simplified_llm_api_script/IUCN_LLM_checks.md
simplified_llm_api_script/docs/review_assessment_integration.md
simplified_llm_api_script/prompt_library/system_prompt.md
simplified_llm_api_script/prompt_library/rules/
```

### `llm_rag/`

The `llm_rag/` folder contains the retrieval-augmented generation pipeline used
by the RAG chat tab.

Main responsibilities:

- store the raw IUCN reference PDFs
- preprocess PDFs into retrieval-ready JSONL records
- build dense and sparse reference retrieval assets
- provide deterministic lookup for stable Red List threshold facts
- retrieve evidence from the uploaded draft assessment
- assemble grounded prompts that keep reference evidence and draft evidence
  separate
- expose debug payloads for the Streamlit UI and evaluation notebooks
- provide unit tests, smoke notebooks, retrieval judging prompts, and
  development-history documentation

Important folders:

- `llm_rag/i_raw_documents/`
  Raw IUCN reference PDFs.
- `llm_rag/ii_preprocessed_documents/`
  Generated retrieval blocks, manifests, tables, and preprocessing script.
- `llm_rag/iii_vector_db/`
  Reference retrieval code, Chroma assets, sparse corpus files, and threshold
  lookup.
- `llm_rag/iv_inference/`
  Uploaded-draft retrieval, prompt assembly, OpenRouter-compatible calls, and
  RAG runtime helpers.
- `llm_rag/evaluation/`
  Notebook-based retrieval inspection, smoke tests, and retrieval-judging
  prompts.
- `llm_rag/unit_tests/`
  Unit tests grouped by preprocessing, vector-db, and inference stages.

For the full RAG architecture, design decisions, rebuild commands, evaluation
notes, and future work, start with:

```text
llm_rag/README.md
llm_rag/DEVELOPMENT_HISTORY.md
```

Stage-specific documentation:

```text
llm_rag/i_raw_documents/README.md
llm_rag/ii_preprocessed_documents/README.md
llm_rag/iii_vector_db/README.md
llm_rag/iv_inference/README.md
llm_rag/evaluation/README.md
llm_rag/unit_tests/README.md
```

### `assets/`

The `assets/` folder stores static files used by the project, currently
including:

```text
assets/IUCN_Kew_header.png
```

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

The main future-work themes below are synthesized from the detailed README
files and development notes across the project subfolders.

### Improve hosted-app user management

The Streamlit interface currently supports shared preset OpenRouter keys and
session-only user-provided keys. A future deployed version could add
authentication and per-user API-key management so reviewers can sign in, save
their own key, and reuse it across sessions. If implemented, API keys should be
stored in an encrypted external backend rather than in Streamlit session state,
plain files, or logs.

The UI could also benefit from richer progress states for long LLM/RAG runs,
clearer partial-result handling, optional run history, and named review
sessions. Those features would need to be designed carefully around privacy,
document sensitivity, and credential handling.

### Strengthen RAG document preprocessing

The current preprocessing layer preserves headings, paragraphs, tables,
comments, rich text, and other structure needed by the reviewer. Future work
could test newer document-conversion tools such as Microsoft's
[MarkItDown](https://github.com/microsoft/markitdown) as either a companion
parser or a replacement for parts of the current pipeline.

Any preprocessing change should be evaluated against the existing parser
notebooks and RAG retrieval outputs. The important question is not just whether
the extracted text looks cleaner, but whether section provenance, table rows,
supporting-information records, comments, and Red List criteria evidence remain
stable enough for rules, LLM feedback, retrieval, and unit tests.

### Improve RAG retrieval quality

The RAG system already combines reference-document retrieval, uploaded-draft
retrieval, deterministic threshold lookup, and debug payloads. The next major
improvement would be to make relationships between chunks explicit. A
GraphRAG-style layer could link consecutive chunks, table rows to parent
tables, cross-referenced sections, threshold facts to their source criteria,
and draft rationale sections to related fields such as AOO, EOO, locations,
threats, habitat decline, and population trend.

This would address a known retrieval issue: the system can retrieve a broadly
relevant chunk but miss the nearby row, subsection, annex, or draft field needed
for complete evidence coverage. Connected chat context is another useful
extension, allowing reviewers to ask follow-up questions without forcing each
RAG turn to behave like a disconnected prompt.

### Expand evaluation coverage

The repository already includes unit tests, parser evaluation notebooks,
rules-checker evaluation notebooks, RAG smoke notebooks, and retrieval-judging
prompts for external LLM review. Future evaluation work should broaden those
checks across more uploaded assessments, more Red List categories and criteria,
and more question types.

Useful additions include structured retrieval-evaluation datasets, regression
checks for retrieval failures found during qualitative notebook review,
expanded deterministic threshold tests, and clearer comparison of retrieval
quality before and after preprocessing, chunking, reranking, or GraphRAG
changes. The notebook evaluations should continue to complement unit tests by
showing whether outputs are useful, grounded, and complete in realistic review
scenarios.

### Extend review rules and LLM feedback

The deterministic checker and LLM prompt-library systems are intentionally
modular. Future work can add new checker classes, expand existing checker
coverage, and refine LLM rule prompts based on reviewer feedback and evaluation
results. Priority areas include reducing false positives, improving
section-specific behavior, making severity/report-section metadata more
consistent, and aligning rule outputs with the way assessors triage review
comments in practice.

## Where To Go Next

For app flow and Streamlit UI details:

```text
ui/README.md
```

For deterministic checker logic:

```text
iucn_rules_checker/README.md
iucn_rules_checker/checkers/README.md
```

For LLM prompt-library review logic:

```text
simplified_llm_api_script/README.md
simplified_llm_api_script/IUCN_LLM_checks.md
```

For RAG architecture, retrieval design, evaluation, and future work:

```text
llm_rag/README.md
llm_rag/DEVELOPMENT_HISTORY.md
llm_rag/evaluation/README.md
```

For document parsing:

```text
preprocessing/README.md
```
