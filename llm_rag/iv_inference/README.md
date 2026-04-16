# iv_inference

## Purpose

This folder contains the inference-time RAG logic used by the app in the repo root.

It covers:

- parsing the uploaded draft assessment into section-level HTML
- building and ranking draft-side retrieval chunks
- orchestrating threshold lookup, reference retrieval, prompt assembly, and external LLM calls
- small UI-facing helpers for section labels

## Main files

- `inference_assessment_parser.py`: converts the uploaded assessment tree into a flat `section_path -> html` report
- `draft_retrieval.py`: builds the draft retrieval store and ranks draft sections against the user query
- `rag_runtime.py`: coordinates the full inference flow and debug payload generation
- `ui_helpers.py`: normalizes section names for display

## Unit tests

The main unit-test files in this folder are:

- `test_inference_assessment_parser_unit.py`: validates the uploaded-draft parser. It checks input validation, recursive section-path construction, fallback section naming, paragraph and table HTML rendering, merging multiple supported blocks into one section, ignoring unsupported block types, and rich-cell coercion for values such as `None` and `bytes`.
- `test_draft_retrieval_unit.py`: validates draft-side retrieval behavior. It checks text normalization, HTML stripping, token normalization and expansion, block-marker removal from section paths, phrase matching, supporting-information query detection, draft-store construction, empty-input handling, deduplication, hit formatting, empty-query fallback behavior, and heuristic ranking for population, Red List status, and supporting-information questions.
- `test_rag_runtime_unit.py`: validates the inference orchestrator. It checks OpenAI-compatible base-URL normalization, LLM request payload construction, completion-response normalization across common SDK shapes, reasoning extraction, normalized error payloads, Streamlit session-state initialization and upload-triggered cache resets, report-to-draft-store caching, retrieved-reference formatting, grounded prompt assembly, external-LLM configuration checks, external-LLM call behavior, end-to-end answer assembly, and debug-payload serialization.
- `test_ui_helpers_unit.py`: validates UI section-name cleanup. It checks removal of parser-added `[paragraph n]`, `[table n]`, and `[row n]` suffixes, case-insensitive matching, preserving already clean names, and avoiding removal of unsupported suffix patterns such as `[figure 1]`.

Together these tests cover the full inference pipeline:

1. assessment tree -> section-level HTML report
2. report -> normalized draft retrieval store
3. query -> retrieved reference evidence + retrieved draft evidence + grounded prompt
4. final response -> debug payload + UI-friendly section labels

## Running the tests

Run the tests from the repo root:

```bash
python -m pytest -q llm_rag/iv_inference/test_inference_assessment_parser_unit.py
python -m pytest -q llm_rag/iv_inference/test_draft_retrieval_unit.py
python -m pytest -q llm_rag/iv_inference/test_rag_runtime_unit.py
python -m pytest -q llm_rag/iv_inference/test_ui_helpers_unit.py
```

Run all `iv_inference` unit tests together:

```bash
python -m pytest -q llm_rag/iv_inference/test_inference_assessment_parser_unit.py llm_rag/iv_inference/test_draft_retrieval_unit.py llm_rag/iv_inference/test_rag_runtime_unit.py llm_rag/iv_inference/test_ui_helpers_unit.py
```

Or run every test file in the folder:

```bash
python -m pytest -q llm_rag/iv_inference
```
