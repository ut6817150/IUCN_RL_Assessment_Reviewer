# llm_rag

## Overview

`llm_rag` contains the retrieval-augmented generation pipeline used by `app.py` in the repo root.

The pipeline has four stages:

1. Raw IUCN reference PDFs are stored in `1_raw_documents/`.
2. `2_preprocessed_documents/preprocess_pdfs.py` converts those PDFs into retrieval-ready blocks, including table rows and synthetic fallback tables for difficult PDFs.
3. `3_vector_db/build_reference_db.py` turns those blocks into a hybrid retrieval store made up of:
   - a Chroma dense index
   - a sparse JSONL corpus
   - parent table contexts
   - deterministic threshold lookup data
4. `4_inference/rag_runtime.py` combines reference retrieval with uploaded-draft retrieval and sends a grounded prompt to the external LLM configured in `app.py` in the repo root.

## Folder structure

```text
llm_rag/
|- 1_raw_documents/
|- 2_preprocessed_documents/
|- 3_vector_db/
|- 4_inference/
|- README.md
`- RAG_updates.md
```

## What each folder does

### `1_raw_documents/`

Stores the source PDFs used to build the reference corpus.

### `2_preprocessed_documents/`

Stores intermediate retrieval assets produced from the PDFs:

- `raw_page_blocks.jsonl`
- `retrieval_blocks.jsonl`
- per-document `manifest.json`
- extracted CSV tables where available
- `summary.json` across the whole corpus

### `3_vector_db/`

Stores the reference retrieval layer:

- `reference_corpus.jsonl`
- `parent_contexts.jsonl`
- `thresholds.json`
- `build_summary.json`
- `chroma_db/reference_docs/`
- the runtime retrieval code

### `4_inference/`

Stores the inference-time logic used by the app:

- `inference_assessment_parser.py` flattens the uploaded draft into section-level HTML
- `draft_retrieval.py` scores uploaded-draft sections against the user query
- `rag_runtime.py` orchestrates threshold lookup, reference retrieval, draft retrieval, prompt assembly, external LLM calls, and debug payloads
- `ui_helpers.py` contains small UI-facing helpers

## Importing the inference helpers into `app.py`

The app currently loads the inference helpers dynamically from the repo root.

The key pattern is:

```python
import importlib.util
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
INFERENCE_DIR = APP_DIR / "llm_rag" / "4_inference"

def load_local_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

ui_helpers_module = load_local_module("ui_helpers_local", INFERENCE_DIR / "ui_helpers.py")
rag_runtime_module = load_local_module("rag_runtime_local", INFERENCE_DIR / "rag_runtime.py")
```

After loading those modules, `app.py` can bind the main helpers it needs:

```python
normalize_display_section_name = ui_helpers_module.normalize_display_section_name

answer_rag_question = rag_runtime_module.answer_rag_question
build_rag_debug_payload = rag_runtime_module.build_rag_debug_payload
build_report_from_assessment = rag_runtime_module.build_report_from_assessment
ensure_draft_store_from_report = rag_runtime_module.ensure_draft_store_from_report
init_rag_session_state = rag_runtime_module.init_rag_session_state
sync_rag_state_with_upload = rag_runtime_module.sync_rag_state_with_upload
```

These are the main inference-side functions used by the app:

- `init_rag_session_state(...)`: creates the RAG session-state keys
- `sync_rag_state_with_upload(...)`: resets cached RAG state when the uploaded file changes
- `build_report_from_assessment(...)`: converts the parsed assessment tree into the section-level report dictionary
- `ensure_draft_store_from_report(...)`: builds or reuses the cached draft retrieval store
- `answer_rag_question(...)`: runs the end-to-end RAG pipeline for one prompt
- `build_rag_debug_payload(...)`: formats the debug information shown in the UI

## Current runtime flow

When a user uploads a draft in the RAG app from the repo root:

1. The uploaded assessment is parsed with `parse_dict(...)`.
2. `InferenceAssessmentParser` converts the parsed tree into a `section_path -> html` report dictionary.
3. A draft retrieval store is built from those sections and cached in Streamlit session state.
4. For each prompt:
   - threshold facts are looked up deterministically when relevant
   - reference evidence is retrieved with hybrid dense + sparse search
   - top draft sections are retrieved from the uploaded assessment
   - a grounded prompt is assembled
   - the external LLM is called through the OpenAI client against OpenRouter
   - debug output is prepared, including prompt, reference excerpts, draft hits, and request errors

## Key design decisions

- Table rows are preserved because many IUCN requirements live in tables rather than prose.
- Parent table contexts are stored separately so row-level hits can be expanded with larger context.
- Threshold questions are answered deterministically where possible instead of relying fully on free-form generation.
- Uploaded drafts are retrieved separately from the reference corpus so the system can distinguish:
  - what the IUCN reference documents require
  - what the uploaded draft appears to contain

## Typical commands

From the repo root:

```bash
python llm_rag/2_preprocessed_documents/preprocess_pdfs.py
python llm_rag/3_vector_db/build_reference_db.py --reset
streamlit run app.py
```

## When to rebuild

Re-run preprocessing or rebuild the vector DB when:

- the PDFs in `1_raw_documents/` change
- preprocessing logic changes
- chunking, embeddings, or retrieval-build logic changes

You do not need to rebuild the vector DB for UI-only changes or most inference-layer changes.
