"""Streamlit entry point for the combined IUCN review app.

This app exposes three parallel review workflows over the same uploaded
assessment:

- a deterministic rules-based checker
- an LLM-based reviewer that runs the simplified assessment prompts
- a RAG chat prototype grounded in both the uploaded draft and the reference
  IUCN documents

The script keeps the control flow inline so the tab behaviour is easy to trace
from top to bottom during development.
"""

import asyncio
import json
import tempfile
from collections import defaultdict
from pathlib import Path
import os

import pandas as pd
import streamlit as st

from preprocessing.assessment_processor import parse_dict

from iucn_rules_checker.assessment_parser import AssessmentParser
from iucn_rules_checker.assessment_reviewer import IUCNAssessmentReviewer

from llm_rag.iv_inference.rag_runtime import answer_rag_question
from llm_rag.iv_inference.rag_runtime import build_rag_debug_payload
from llm_rag.iv_inference.rag_runtime import build_report_from_assessment
from llm_rag.iv_inference.rag_runtime import ensure_draft_store_from_report
from llm_rag.iv_inference.rag_runtime import init_rag_session_state
from llm_rag.iv_inference.rag_runtime import sync_rag_state_with_upload
from llm_rag.iv_inference.ui_helpers import normalize_display_section_name

from simplified_llm_api_script.llm_checker_v2 import ReviewDocumentError
from simplified_llm_api_script.llm_checker_v2 import provider_from_config
from simplified_llm_api_script.llm_checker_v2 import review_document


OPENROUTER_API_KEY = os.getenv("OR_TOKEN")

RAG_LLM_CONFIG = {
    "base_url": "https://openrouter.ai/api/v1",
    "model": "openai/gpt-oss-120b:free",
    "api_key": OPENROUTER_API_KEY,
    "reasoning_enabled": True,
}

LLM_TAB_CONFIGS = {
    "GPT OSS 120b (free and zero data retention)": {
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "openai/gpt-oss-120b:free",
        "api_key": OPENROUTER_API_KEY,
        "reasoning_enabled": True,
    },
}

st.set_page_config(page_title="IUCN Assessment Feedback Tool", layout="wide")
st.title("IUCN Assessment Feedback Tool")
st.caption(
    "Upload one assessment, then run the rules-based, LLM, and RAG systems separately "
    "from the tabs below."
)

if "uploaded_file_signature" not in st.session_state:
    st.session_state["uploaded_file_signature"] = None
if "rules_feedback" not in st.session_state:
    st.session_state["rules_feedback"] = None
if "llm_feedback" not in st.session_state:
    st.session_state["llm_feedback"] = None

# The RAG helper manages a larger set of session-state keys used by the chat UI.
init_rag_session_state(st.session_state)

uploaded = st.file_uploader(
    "Upload a .docx, .html or .htm file",
    type=["docx", "html", "doc"],
)

tmp_path: Path | None = None
uploaded_ext: str | None = None
uploaded_name = ""
file_signature = None
input_ready = False

if uploaded:
    uploaded_name = uploaded.name
    uploaded_ext = Path(uploaded.name).suffix.lower()
    file_signature = f"{uploaded.name}:{len(uploaded.getbuffer())}"

    if uploaded_ext == ".doc":
        st.error(
            "The feedback tool only supports .docx files. Please convert .doc to .docx and re-upload. Or, upload a HTML file."
        )
    elif uploaded_ext not in [".docx", ".html"]:
        st.error("The feedback tool only supports .docx or HTML files.")
    elif uploaded_ext == ".docx" or uploaded_ext == ".html":
        tmp_dir = Path(tempfile.mkdtemp(prefix="upload_"))
        safe_name = Path(uploaded.name).name
        tmp_path = tmp_dir / safe_name
        tmp_path.write_bytes(uploaded.getbuffer())

        st.success(f"Uploaded: {uploaded.name}")
        st.caption(f"Temp file: {tmp_path}")

# Reset cached tab outputs whenever the uploaded file changes.
if st.session_state["uploaded_file_signature"] != file_signature:
    st.session_state["uploaded_file_signature"] = file_signature
    st.session_state["rules_feedback"] = None
    st.session_state["llm_feedback"] = None

sync_rag_state_with_upload(st.session_state, file_signature)

if uploaded is None:
    st.info("Upload a file to enable both feedback systems.")
elif tmp_path is not None:
    input_ready = True

rules_tab, llm_tab, rag_tab = st.tabs(
    ["Rules-based feedback", "LLM feedback", "RAG chat (prototype)"]
)

with rules_tab:
    st.subheader("Rules-based feedback")
    st.write("Run the deterministic checker suite on the uploaded assessment.")

    if st.button(
        "Generate feedback",
        key="generate_rules_feedback",
        type="primary",
        disabled=not input_ready,
    ):
        with st.spinner("Generating rules-based feedback..."):
            assessment = parse_dict(str(tmp_path))
            parser = AssessmentParser()
            reviewer = IUCNAssessmentReviewer()
            full_report = parser.parse(assessment)
            violations = [
                violation.to_dict()
                for violation in reviewer.review_full_report(full_report)
            ]

            # Preserve the document's original section order rather than sorting
            # headings alphabetically in the UI.
            grouped_violations = defaultdict(list)
            for violation in violations:
                section_name = normalize_display_section_name(
                    violation.get("section_name") or "Whole document"
                )
                grouped_violations[section_name].append(violation)

            ordered_grouped_violations = {}
            seen_sections = set()
            for section_name in full_report:
                normalized_name = normalize_display_section_name(section_name)
                if normalized_name in seen_sections:
                    continue
                seen_sections.add(normalized_name)
                if normalized_name in grouped_violations:
                    ordered_grouped_violations[normalized_name] = grouped_violations[normalized_name]

            for section_name, rows in grouped_violations.items():
                if section_name not in ordered_grouped_violations:
                    ordered_grouped_violations[section_name] = rows

            st.session_state["rules_feedback"] = {
                "violations": violations,
                "grouped_violations": ordered_grouped_violations,
            }

    if st.session_state["rules_feedback"] is None:
        st.info("Click `Generate feedback` in this tab to run the rules-based reviewer.")
    else:
        feedback = st.session_state["rules_feedback"]
        violations = feedback["violations"]
        grouped_violations = feedback["grouped_violations"]

        if not violations:
            st.success("No rules-based violations were found for this document.")
        else:
            st.metric("Violations found", len(violations))

            for section_name, rows in grouped_violations.items():
                table = pd.DataFrame(
                    [
                        {
                            "Rule": row.get("rule_class", ""),
                            "Method": row.get("rule_method", ""),
                            "Matched text": row.get("matched_text", ""),
                            "Context": row.get("matched_snippet", ""),
                            "Message": row.get("message", ""),
                            "Suggested fix": row.get("suggested_fix", ""),
                        }
                        for row in rows
                    ]
                )
                table = table[
                    [
                        "Rule",
                        "Method",
                        "Matched text",
                        "Context",
                        "Message",
                        "Suggested fix",
                    ]
                ]

                error_label = "error" if len(rows) == 1 else "errors"
                with st.expander(f"{section_name} ({len(rows)} {error_label})", expanded=False):
                    st.dataframe(table, use_container_width=True, hide_index=True)

            st.download_button(
                label="Download rules feedback (JSON)",
                data=json.dumps(grouped_violations, indent=2, ensure_ascii=False).encode("utf-8"),
                file_name=f"{Path(uploaded_name).stem}_rules_feedback.json",
                mime="application/json",
            )

with llm_tab:
    st.subheader("LLM feedback")
    st.write("Run the simplified LLM reviewer separately from the rules-based checks.")
    selected_llm_label = st.selectbox(
        "Choose LLM",
        options=list(LLM_TAB_CONFIGS.keys()),
        index=0,
        key="llm_tab_model_choice",
    )
    selected_llm_config = LLM_TAB_CONFIGS[selected_llm_label]
    st.caption(
        f"Selected config: OpenRouter model `{selected_llm_config['model']}` "
        f"with reasoning `{'on' if selected_llm_config['reasoning_enabled'] else 'off'}`."
    )

    if st.button(
        "Generate feedback",
        key="generate_llm_feedback",
        type="primary",
        disabled=not input_ready,
    ):
        with st.spinner("Generating LLM feedback..."):
            assessment = parse_dict(str(tmp_path))
            llm_results = []
            llm_error = None

            try:
                provider = provider_from_config(selected_llm_config)
                llm_results = asyncio.run(
                    review_document(assessment, provider=provider, mode="sequential")
                )
            except ReviewDocumentError as exc:
                llm_error = str(exc)
                llm_results = exc.results
            except Exception as exc:
                llm_error = str(exc)

            st.session_state["llm_feedback"] = {
                "status": "success" if llm_error is None else "error",
                "model_label": selected_llm_label,
                "model_slug": selected_llm_config["model"],
                "error": llm_error,
                # Persist the raw rule results for download and direct rendering.
                "llm_results": [result.model_dump() for result in llm_results],
            }

    if st.session_state["llm_feedback"] is None:
        st.info("Click `Generate feedback` in this tab to run the LLM workflow.")
    else:
        feedback = st.session_state["llm_feedback"]
        st.caption(
            f"Generated with `{feedback.get('model_label', 'Unknown')}` "
            f"using model `{feedback.get('model_slug', 'Unknown')}`."
        )
        if feedback.get("error"):
            st.warning(
                "The LLM review returned partial or empty results. "
                f"Last error: {feedback['error']}"
            )

        if not feedback.get("llm_results"):
            st.info("No LLM rule results were returned.")

        for llm_result in feedback.get("llm_results", []):
            rule_name = llm_result.get("rule_name") or "unknown_rule"
            findings = llm_result.get("findings") or []
            with st.expander(
                f"{rule_name} ({len(findings)} findings)",
                expanded=False,
            ):
                if not findings:
                    st.write("No findings or external LLM failed")
                else:
                    for index, finding in enumerate(findings, start=1):
                        section_path = finding.get("section_path") or "Whole document"
                        severity = finding.get("severity") or "unknown"
                        st.markdown(
                            f"**{section_path} clause (Severity: {severity})**"
                        )
                        st.write(finding.get("issue") or "No issue provided.")
                        st.caption(
                            "Suggested fix: "
                            + (finding.get("suggestion") or "No suggestion provided.")
                        )
                        if index < len(findings):
                            st.divider()

        st.download_button(
            label="Download LLM feedback (JSON)",
            data=json.dumps(
                feedback.get("llm_results", []),
                indent=2,
                ensure_ascii=False,
            ).encode("utf-8"),
            file_name=f"{Path(uploaded_name).stem}_llm_feedback.json",
            mime="application/json",
        )

with rag_tab:
    st.subheader("RAG chat")
    st.write("Ask grounded questions about the uploaded assessment and the IUCN reference documents.")
    st.caption(
        "For each question, the app fetches deterministic threshold facts, retrieves reference evidence, "
        "retrieves the top draft chunks, and sends that combined prompt to the external LLM when configured."
    )
    show_debug = st.checkbox(
        "Show retrieval debug output",
        value=False,
        key="rag_show_debug",
    )

    if not input_ready:
        st.info("Upload a file to enable the RAG chat.")
    else:
        # Parse and cache the uploaded assessment once per file so the chat can
        # reuse the same draft store across multiple prompts.
        if st.session_state.get("rag_assessment_input_signature") != file_signature:
            assessment_for_rag = parse_dict(str(tmp_path))
            st.session_state["rag_assessment_input_dict"] = assessment_for_rag
            st.session_state["rag_assessment_input_signature"] = file_signature
            st.session_state["rag_report_dict"] = build_report_from_assessment(assessment_for_rag)
            ensure_draft_store_from_report(
                st.session_state,
                st.session_state.get("rag_report_dict"),
                file_signature,
            )

        if st.button(
            "Clear RAG chat",
            key="clear_rag_chat",
            disabled=not st.session_state["rag_messages"],
            use_container_width=True,
        ):
            st.session_state["rag_messages"] = []
            st.rerun()

        if RAG_LLM_CONFIG["base_url"].strip() and RAG_LLM_CONFIG["model"].strip():
            st.caption(
                f"External LLM config is hard-coded in `app.py` using model `{RAG_LLM_CONFIG['model']}`."
            )
        else:
            st.caption(
                "External LLM config is hard-coded in `app.py` and is currently not fully set."
            )

        if st.session_state.get("rag_draft_store") is None:
            st.caption("RAG context is prepared automatically when a new file is uploaded.")
        else:
            st.caption(
                f"Draft store ready: {len(st.session_state['rag_draft_store'])} chunks "
                f"from {len(st.session_state.get('rag_report_dict', {}))} parsed report blocks"
            )

        chat_history = st.container(height=520, border=True)
        with chat_history:
            if not st.session_state["rag_messages"]:
                st.caption(
                    "Start the conversation below. The chat history stays in this pane so the input box remains in place."
                )

            for message in st.session_state["rag_messages"]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if message["role"] == "assistant":
                        route = message.get("route", "unknown")
                        used_external_llm = "yes" if message.get("used_external_llm") else "no"
                        deterministic_used = "yes" if message.get("deterministic_answer") else "no"
                        reference_count = message.get("reference_count", 0)
                        draft_count = message.get("draft_count", 0)
                        st.caption(
                            f"Route: `{route}` | External LLM: `{used_external_llm}` | "
                            f"Deterministic facts: `{deterministic_used}` | "
                            f"Reference chunks: `{reference_count}` | Draft chunks: `{draft_count}`"
                        )
                    if show_debug and message["role"] == "assistant" and message.get("debug"):
                        with st.expander("Debug details", expanded=False):
                            if message.get("debug_error"):
                                st.error(message["debug_error"])
                            st.code(message["debug"], language="json")

        user_prompt = st.chat_input(
            "Ask about the uploaded assessment or the IUCN requirements.",
            key="rag_chat_input",
        )

        if user_prompt:
            st.session_state["rag_messages"].append({"role": "user", "content": user_prompt})

            with chat_history:
                with st.chat_message("user"):
                    st.markdown(user_prompt)

                with st.chat_message("assistant"):
                    # Keep the retrieval, prompt assembly, and external LLM call
                    # visible to the user as one staged status block.
                    with st.status("Running RAG inference...", expanded=True) as status:
                        status.write("Loading the uploaded draft context.")
                        draft_store = ensure_draft_store_from_report(
                            st.session_state,
                            st.session_state.get("rag_report_dict"),
                            file_signature,
                        )

                        status.write("Fetching deterministic facts, reference evidence, and draft evidence.")
                        response = answer_rag_question(
                            query=user_prompt,
                            draft_store=draft_store,
                            llm_config=RAG_LLM_CONFIG,
                        )

                        if response.get("llm_configured"):
                            status.write("Sending the combined prompt to the external LLM.")
                        else:
                            status.write("No external LLM is configured, so the chat returns a configuration message.")
                        status.update(label="RAG inference complete", state="complete", expanded=False)

                    st.markdown(response["answer"])
                    st.caption(
                        f"Route: `{response.get('route', 'unknown')}` | "
                        f"LLM configured: `{'yes' if response.get('llm_configured') else 'no'}` | "
                        f"External LLM: `{'yes' if response.get('used_external_llm') else 'no'}` | "
                        f"Deterministic facts: `{'yes' if response.get('deterministic_answer') else 'no'}` | "
                        f"Reference chunks: `{len(response.get('reference_payload', {}).get('results') or [])}` | "
                        f"Draft chunks: `{len(response.get('draft_hits') or [])}`"
                    )

                    debug_data = build_rag_debug_payload(response)
                    debug_payload = json.dumps(debug_data, ensure_ascii=False, indent=2)
                    if show_debug:
                        with st.expander("Debug details", expanded=False):
                            if debug_data.get("request_error"):
                                st.error(debug_data["request_error"])
                            st.code(debug_payload, language="json")

            st.session_state["rag_messages"].append(
                {
                    "role": "assistant",
                    "content": response["answer"],
                    "debug": debug_payload,
                    "debug_error": debug_data.get("request_error"),
                    "route": response.get("route"),
                    "llm_configured": response.get("llm_configured"),
                    "used_external_llm": response.get("used_external_llm"),
                    "deterministic_answer": response.get("deterministic_answer"),
                    "reference_count": len(response.get("reference_payload", {}).get("results") or []),
                    "draft_count": len(response.get("draft_hits") or []),
                }
            )
            st.rerun()
