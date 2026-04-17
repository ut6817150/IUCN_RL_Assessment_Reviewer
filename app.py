"""Streamlit entry point for the combined IUCN review app.

Purpose:
    This module owns the shared Streamlit page shell for the feedback tool.
    It handles upload validation, caches the parsed assessment input once per
    uploaded file, and passes that shared dictionary into the rules-based, LLM,
    and RAG tabs so each workflow can focus on its own UI and processing.
"""

import os
import tempfile
from pathlib import Path

import streamlit as st
from preprocessing.assessment_processor import parse_to_dict
from llm_rag.iv_inference.rag_runtime import init_rag_session_state
from llm_rag.iv_inference.rag_runtime import sync_rag_state_with_upload

from ui.app_download_tab import render_download_tab
from ui.app_llm_tab import render_llm_tab
from ui.app_rag_tab import render_rag_tab
from ui.app_rules_tab import render_rules_tab

# Keep the selectable OpenRouter credentials centralised at the app entry point.
OPENROUTER_KEY_OPTIONS = {
    "Steve Bachman's Key": "Openrouter_API_key_Steve_Bachman",
    "Jack Plummer's Key": "JackAPIKey",
    "Khalid Alahmadi's Key": "OR_TOKEN",
}

# Expose the preset model metadata once, then inject the selected key at runtime.
LLM_TAB_MODEL_SPECS = {
    "GPT OSS 120b (free and zero data retention)": {
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "openai/gpt-oss-120b:free",
        "reasoning_enabled": True,
    },
    "Qwen 3.5 Plus 02-15 (Paid and retains data)": {
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "qwen/qwen3.5-plus-02-15",
        "reasoning_enabled": True,
    },
}
CUSTOM_LLM_OPTION = "configure your own LLM"

# Configure the shared page shell before any widgets are created.
st.set_page_config(
    page_title="IUCN Assessment Feedback Tool",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("IUCN Assessment Feedback Tool")

st.caption(
    "Use the arrow on the top left of the screen to access the sidebar for "
    "document upload and API key selection. Upload one assessment, then run "
    "the rules-based, LLM, and RAG systems separately from the tabs below."
)

# Track upload-scoped outputs and the shared parsed assessment in session state.
if "uploaded_file_signature" not in st.session_state:
    st.session_state["uploaded_file_signature"] = None
if "rules_feedback" not in st.session_state:
    st.session_state["rules_feedback"] = None
if "llm_feedback" not in st.session_state:
    st.session_state["llm_feedback"] = None
if "assessment_input_dict" not in st.session_state:
    st.session_state["assessment_input_dict"] = None
if "assessment_input_signature" not in st.session_state:
    st.session_state["assessment_input_signature"] = None

# The RAG runtime manages its own larger chat/session state payload.
init_rag_session_state(st.session_state)

# Place the global app inputs back in the sidebar so the main page stays
# focused on the workflow tabs.
with st.sidebar:
    st.subheader("Inputs")
    st.caption(
        "Choose a document and OpenRouter key here, then run each workflow "
        "from the tabs in the main workspace."
    )
    uploaded = st.file_uploader(
        "Assessment file",
        type=["docx", "html", "doc"],
    )
    # Keep upload validation and readiness messaging anchored directly under
    # the uploader instead of letting it fall below the API-key selector.
    upload_feedback_placeholder = st.empty()
    selected_key_label = st.selectbox(
        "OpenRouter API key",
        options=list(OPENROUTER_KEY_OPTIONS.keys()),
        index=2,
        key="openrouter_api_key_choice",
    )

selected_key_env_var = OPENROUTER_KEY_OPTIONS[selected_key_label]
selected_openrouter_api_key = os.getenv(selected_key_env_var)

if selected_openrouter_api_key:
    st.sidebar.success(f"Using `{selected_key_label}`")

# Keep the runtime model configs derived from the currently selected key.
RAG_LLM_CONFIG = {
    "base_url": "https://openrouter.ai/api/v1",
    "model": "openai/gpt-oss-120b:free",
    "api_key": selected_openrouter_api_key,
    "reasoning_enabled": True,
}
LLM_TAB_CONFIGS = {
    label: {
        **config,
        "api_key": selected_openrouter_api_key,
    }
    for label, config in LLM_TAB_MODEL_SPECS.items()
}

tmp_path: Path | None = None
uploaded_ext: str | None = None
uploaded_name = ""
file_signature = None
input_ready = False

# Validate the upload and materialise a temporary file for the parser.
if uploaded:
    uploaded_name = uploaded.name
    uploaded_ext = Path(uploaded.name).suffix.lower()
    file_signature = f"{uploaded.name}:{len(uploaded.getbuffer())}"

    # Legacy `.doc` uploads must be converted before they can be parsed safely.
    if uploaded_ext == ".doc":
        upload_feedback_placeholder.error(
            "The feedback tool only supports .docx files. Please convert .doc to .docx and re-upload. Or, upload a HTML file."
        )
    # Reject any other unsupported extension early so the tabs stay disabled.
    elif uploaded_ext not in [".docx", ".html"]:
        upload_feedback_placeholder.error(
            "The feedback tool only supports .docx or HTML files."
        )

    # Persist the supported upload to a temporary path because the parser
    # expects a filesystem location rather than an in-memory upload object.
    elif uploaded_ext == ".docx" or uploaded_ext == ".html":
        tmp_dir = Path(tempfile.mkdtemp(prefix="upload_"))
        safe_name = Path(uploaded.name).name
        tmp_path = tmp_dir / safe_name
        tmp_path.write_bytes(uploaded.getbuffer())
        upload_feedback_placeholder.caption(f"Uploaded file: `{uploaded.name}`")

# Clear all upload-scoped cached outputs when the user switches documents.
if st.session_state["uploaded_file_signature"] != file_signature:
    st.session_state["uploaded_file_signature"] = file_signature
    st.session_state["rules_feedback"] = None
    st.session_state["llm_feedback"] = None
    st.session_state["assessment_input_dict"] = None
    st.session_state["assessment_input_signature"] = None

# Keep the RAG runtime's upload-specific caches aligned with the current file.
sync_rag_state_with_upload(st.session_state, file_signature)

# Enable the downstream tabs only when a supported upload has been staged.
if uploaded is None:
    upload_feedback_placeholder.caption(
        "Upload a file to enable the rules-based, LLM, and RAG workflows."
    )
elif tmp_path is not None:
    input_ready = True

assessment_input = None
if input_ready:
    # Parse the uploaded document once per file signature and share the
    # resulting assessment dictionary across the tab render helpers.
    if st.session_state.get("assessment_input_signature") != file_signature:
        st.session_state["assessment_input_dict"] = parse_to_dict(str(tmp_path))
        st.session_state["assessment_input_signature"] = file_signature
    assessment_input = st.session_state.get("assessment_input_dict")

# Build the four top-level workflows from the shared page shell.
rules_tab, llm_tab, rag_tab, download_tab = st.tabs(
    ["Rules-based feedback", "LLM feedback", "RAG chat (prototype)", "Download feedback"]
)

# Render the deterministic rules-based review workflow.
with rules_tab:
    render_rules_tab(
        input_ready=input_ready,
        assessment=assessment_input,
        uploaded_name=uploaded_name,
    )

# Render the separate LLM review workflow.
with llm_tab:
    render_llm_tab(
        input_ready=input_ready,
        assessment=assessment_input,
        uploaded_name=uploaded_name,
        llm_tab_configs=LLM_TAB_CONFIGS,
        custom_llm_option=CUSTOM_LLM_OPTION,
        openrouter_api_key=selected_openrouter_api_key,
    )

# Render the prototype RAG chat workflow over the same parsed assessment.
with rag_tab:
    render_rag_tab(
        input_ready=input_ready,
        assessment=assessment_input,
        file_signature=file_signature,
        rag_llm_config=RAG_LLM_CONFIG,
    )

# Render the export tab for whichever feedback outputs are currently available.
with download_tab:
    render_download_tab(uploaded_name=uploaded_name)
