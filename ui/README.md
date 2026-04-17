# UI

This folder contains the Streamlit tab helpers used by the repo-level app.

`app.py` remains the main entry point for the interface. It handles:

- page setup
- upload validation
- shared session-state management
- parsing the uploaded document once
- passing the shared parsed assessment into the tab helpers

The modules in this folder are responsible for rendering the individual tabs
and keeping the tab-specific UI logic out of `app.py`.

The repository root is the parent folder of this `ui/` subfolder.

## Imports

The modules in this folder are imported by `app.py` using paths such as:

- `from ui.app_rules_tab import render_rules_tab`
- `from ui.app_llm_tab import render_llm_tab`

Inside the tab modules themselves, imports from the rest of the codebase still
use absolute repo-root package paths such as:

- `from iucn_rules_checker.assessment_parser import AssessmentParser`
- `from llm_rag.iv_inference.rag_runtime import answer_rag_question`
- `from simplified_llm_api_script.llm_checker_v2 import review_document`

Those imports do not need to become relative just because the tab modules live
inside `ui/`. The modules are still executed as part of the repo-root app, not
as standalone scripts launched directly from the `ui/` folder.

## Files In This Folder

- `app_rules_tab.py`
  Renders the rules-based feedback tab and groups reviewer violations for
  display and JSON download.
- `app_llm_tab.py`
  Renders the LLM feedback tab and handles model selection plus LLM-review
  output display.
- `app_rag_tab.py`
  Renders the prototype RAG chat tab and manages the chat UI around the RAG
  runtime helpers.
- `app_download_tab.py`
  Renders the feedback-download tab and builds the Excel export from available
  rules-based and LLM outputs.
- `README.md`
  This document.
