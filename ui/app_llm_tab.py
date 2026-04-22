"""LLM-tab UI helpers for the Streamlit app.

Purpose:
    This module renders the model-driven feedback tab. It receives the shared
    parsed assessment dictionary from ``app.py``, uses the shared sidebar
    model and API-key configuration, runs the simplified LLM reviewer, and
    formats the returned findings for display and JSON export. It also gates
    the primary action when the sidebar model configuration is incomplete.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from simplified_llm_api_script.llm_checker_v2 import ReviewDocumentError
from simplified_llm_api_script.llm_checker_v2 import provider_from_config
from simplified_llm_api_script.llm_checker_v2 import review_document


SEVERITY_ORDER = {"high": 1, "medium": 2, "low": 3, "unknown": 4, "none": 5}
LLM_SORT_OPTIONS = ("Preset rule order", "Report section", "Severity")
SECTION_ORDER_FALLBACK = 10**9


def _format_llm_error_message(error_text: str | None) -> str | None:
    """
    Convert raw provider errors into clearer user-facing messages.

    Args:
        error_text (str | None): Raw exception text captured from the LLM
            provider flow.

    Returns:
        str | None: Friendly message to display in the UI, or ``None`` when
            there is no error text.
    """

    if not error_text:
        return None

    lowered = error_text.lower()
    if "503" in lowered or "502" in lowered:
        return (
            "The selected OpenRouter model is temporarily unavailable or overloaded. "
            "Please try again later, or switch to a different model."
        )
    if "429" in lowered:
        return (
            "OpenRouter rate limit reached or quota exceeded for this model or API key. "
            "Please wait and try again, or switch model or API key."
        )
    return error_text


def _rule_order_from_name(rule_name: str, fallback: int) -> int:
    """
    Extract the numeric rule prefix used by the LLM rule files.

    Args:
        rule_name (str): Rule identifier returned by the LLM workflow.
        fallback (int): Position to use if the name does not contain a
            numeric prefix.

    Returns:
        int: Rule order used for stable default sorting.
    """

    for part in rule_name.split("_"):
        if part.isdigit():
            return int(part)
    return fallback


def _preview_text(value: Any, limit: int = 160) -> str:
    """
    Return a single-line preview for long LLM issue and suggestion text.

    Args:
        value (Any): Raw text-like value from an LLM finding.
        limit (int): Maximum number of characters to show before truncation.

    Returns:
        str: Compact preview suitable for table display.
    """

    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}..."


def _normalize_section_key(value: Any) -> str:
    """
    Normalize a report-section label for loose, whitespace-insensitive matching.

    Args:
        value (Any): Section label or path-like value.

    Returns:
        str: Lowercase lookup key with spacing differences removed.
    """

    normalized = " ".join(str(value or "").replace(">", " ").split()).lower()
    return normalized.replace(" ", "")


def _build_section_order_map(assessment: dict[str, Any] | None) -> dict[str, int]:
    """
    Build a lookup from section labels to their order in the assessment.

    Args:
        assessment (dict[str, Any] | None): Parsed assessment dictionary from
            the uploaded report.

    Returns:
        dict[str, int]: Normalized section labels mapped to document-order
            positions.
    """

    section_order: dict[str, int] = {}
    position = 0
    ignored_keys = {
        "children",
        "content",
        "level",
        "metadata",
        "paragraphs",
        "section_type",
        "tables",
        "text",
        "title",
        "type",
    }

    def register(labels: list[str]) -> None:
        nonlocal position

        normalized_labels = [
            _normalize_section_key(label)
            for label in labels
            if _normalize_section_key(label)
        ]
        if not normalized_labels:
            return

        position += 1
        for label in normalized_labels:
            section_order.setdefault(label, position)

    def walk(node: Any, path: tuple[str, ...] = ()) -> None:
        if isinstance(node, dict):
            title = next(
                (
                    str(node[key])
                    for key in ("title", "section", "heading", "name")
                    if isinstance(node.get(key), str) and node.get(key).strip()
                ),
                "",
            )
            current_path = path
            if title:
                current_path = (*path, title)
                register([title, " > ".join(current_path)])

            children = node.get("children")
            if isinstance(children, list):
                for child in children:
                    walk(child, current_path)

            # Some parsed dictionaries are keyed directly by section name
            # rather than only by a nested children list, so handle both forms.
            for key, value in node.items():
                if key in ignored_keys or not isinstance(value, (dict, list)):
                    continue
                keyed_path = (*current_path, str(key))
                register([str(key), " > ".join(keyed_path)])
                walk(value, keyed_path)

        elif isinstance(node, list):
            for item in node:
                walk(item, path)

    walk(assessment or {})
    return section_order


def _section_order_for_path(section_path: str, section_order: dict[str, int]) -> int:
    """
    Resolve an LLM-returned section path to assessment document order.

    Args:
        section_path (str): Section path returned in an LLM finding.
        section_order (dict[str, int]): Lookup built from the parsed
            assessment dictionary.

    Returns:
        int: Document-order position, or a large fallback value when unmatched.
    """

    normalized_path = _normalize_section_key(section_path)
    if normalized_path in section_order:
        return section_order[normalized_path]

    path_parts = [
        part.strip()
        for part in str(section_path or "")
        .replace("/", ">")
        .replace(",", ">")
        .split(">")
        if part.strip()
    ]
    for part in reversed(path_parts):
        normalized_part = _normalize_section_key(part)
        if normalized_part in section_order:
            return section_order[normalized_part]

    for label, order in section_order.items():
        if label and (label in normalized_path or normalized_path in label):
            return order

    return SECTION_ORDER_FALLBACK


def _flatten_llm_findings(
    llm_results: list[dict[str, Any]],
    section_order: dict[str, int],
) -> list[dict[str, Any]]:
    """
    Flatten nested rule results into finding rows for sortable display.

    Args:
        llm_results (list[dict[str, Any]]): Stored LLM result payload from
            Streamlit session state.
        section_order (dict[str, int]): Report-section order lookup built from
            the parsed assessment dictionary.

    Returns:
        list[dict[str, Any]]: Finding rows for the triage table.
    """

    finding_rows = []

    for rule_index, llm_result in enumerate(llm_results, start=1):
        rule_name = llm_result.get("rule_name") or "unknown_rule"
        rule_order = _rule_order_from_name(rule_name, fallback=rule_index)
        findings = llm_result.get("findings") or []

        if not findings:
            finding_rows.append(
                {
                    "_rule_order": rule_order,
                    "_finding_order": 1,
                    "_section_order": SECTION_ORDER_FALLBACK,
                    "_severity_order": SEVERITY_ORDER["none"],
                    "_finding_id": f"{rule_order}:1:{rule_name}",
                    "_has_finding": False,
                    "Rule": rule_name,
                    "Section": "No findings",
                    "Severity": "none",
                    "Issue preview": "No findings",
                    "Suggestion preview": "No action suggested",
                    "Issue": "No findings were returned for this rule.",
                    "Suggestion": "No action suggested.",
                }
            )
            continue

        for finding_index, finding in enumerate(findings, start=1):
            section_path = finding.get("section_path") or "Whole document"
            severity = str(finding.get("severity") or "unknown").lower()
            issue = finding.get("issue") or "No issue provided."
            suggestion = finding.get("suggestion") or "No suggestion provided."

            finding_rows.append(
                {
                    "_rule_order": rule_order,
                    "_finding_order": finding_index,
                    "_section_order": _section_order_for_path(
                        section_path,
                        section_order,
                    ),
                    "_severity_order": SEVERITY_ORDER.get(
                        severity,
                        SEVERITY_ORDER["unknown"],
                    ),
                    "_finding_id": f"{rule_order}:{finding_index}:{rule_name}",
                    "_has_finding": True,
                    "Rule": rule_name,
                    "Section": section_path,
                    "Severity": severity,
                    "Issue preview": _preview_text(issue),
                    "Suggestion preview": _preview_text(suggestion),
                    "Issue": issue,
                    "Suggestion": suggestion,
                }
            )

    return finding_rows


def _sort_llm_finding_rows(
    finding_rows: list[dict[str, Any]],
    sort_by: str,
) -> list[dict[str, Any]]:
    """
    Sort LLM findings while preserving deterministic tie-breakers.

    Args:
        finding_rows (list[dict[str, Any]]): Flattened finding rows.
        sort_by (str): User-selected sort mode.

    Returns:
        list[dict[str, Any]]: Sorted copy of the finding rows.
    """

    if sort_by == "Report section":
        return sorted(
            finding_rows,
            key=lambda row: (
                row["_section_order"],
                row["_rule_order"],
                row["_finding_order"],
                row["Section"].lower(),
            ),
        )

    if sort_by == "Severity":
        return sorted(
            finding_rows,
            key=lambda row: (
                row["_severity_order"],
                row["_rule_order"],
                row["_finding_order"],
            ),
        )

    return sorted(
        finding_rows,
        key=lambda row: (
            row["_rule_order"],
            row["_finding_order"],
        ),
    )


def _render_llm_feedback_table(
    feedback: dict[str, Any],
    assessment: dict[str, Any] | None,
) -> None:
    """
    Render LLM findings as a compact sortable triage table.

    Args:
        feedback (dict[str, Any]): LLM feedback payload stored in Streamlit
            session state.
        assessment (dict[str, Any] | None): Parsed assessment dictionary used
            to sort report sections in document order.

    Returns:
        None: Value produced by this method.
    """

    finding_rows = _flatten_llm_findings(
        feedback.get("llm_results", []),
        _build_section_order_map(assessment),
    )

    if not finding_rows:
        st.info("No LLM findings were returned.")
        return

    real_finding_count = sum(1 for row in finding_rows if row["_has_finding"])
    finding_label = "finding" if real_finding_count == 1 else "findings"
    st.write(f"{real_finding_count} {finding_label} returned.")

    sort_by = st.selectbox(
        "Sort findings by",
        LLM_SORT_OPTIONS,
        help=(
            "The default keeps the numbered LLM rule order. "
            "Alternative views sort the same findings by report section or severity."
        ),
    )
    sorted_rows = _sort_llm_finding_rows(finding_rows, sort_by)
    sorted_rows_by_id = {row["_finding_id"]: row for row in sorted_rows}

    st.caption(
        "The table shows short previews to keep the page compact. "
        "Select one or more rows to read the full issue and suggestion below. "
        "Report-section sorting follows the uploaded assessment order where a section match is found."
    )

    display_columns = [
        "Rule",
        "Section",
        "Severity",
        "Issue preview",
        "Suggestion preview",
    ]
    display_df = pd.DataFrame(sorted_rows)[display_columns]
    table_event = st.dataframe(
        display_df,
        hide_index=True,
        width="stretch",
        height=360,
        row_height=62,
        on_select="rerun",
        selection_mode="multi-row",
        key="llm_findings_table",
        column_config={
            "Rule": st.column_config.TextColumn(width="medium"),
            "Section": st.column_config.TextColumn(width="medium"),
            "Severity": st.column_config.TextColumn(width="small"),
            "Issue preview": st.column_config.TextColumn(width="large"),
            "Suggestion preview": st.column_config.TextColumn(width="large"),
        },
    )

    selected_rows = table_event.selection.rows
    selected_ids = [
        sorted_rows[index]["_finding_id"]
        for index in selected_rows
        if index < len(sorted_rows)
    ]

    previous_sort_by = st.session_state.get("llm_findings_previous_sort_by")
    sort_changed = previous_sort_by is not None and previous_sort_by != sort_by
    if sort_changed:
        # Dataframe row indexes can shift when sorting reruns the page, so
        # preserve stable IDs instead of trusting stale row indexes.
        selected_ids = [
            finding_id
            for finding_id in st.session_state.get("llm_selected_finding_ids", [])
            if finding_id in sorted_rows_by_id
        ]
        st.session_state["llm_selected_finding_ids"] = selected_ids
    elif selected_ids:
        st.session_state["llm_selected_finding_ids"] = selected_ids
    else:
        st.session_state["llm_selected_finding_ids"] = []
    st.session_state["llm_findings_previous_sort_by"] = sort_by

    selected_findings = [
        sorted_rows_by_id[finding_id]
        for finding_id in st.session_state.get("llm_selected_finding_ids", [])
        if finding_id in sorted_rows_by_id
    ]

    st.markdown("#### Selected findings")
    if not selected_findings:
        st.info("No finding selected. Select one or more rows in the table to inspect the full issue and suggestion.")
        return

    for index, selected_finding in enumerate(selected_findings, start=1):
        with st.container(border=True):
            st.markdown(f"**Selected finding {index} of {len(selected_findings)}**")
            first_col, second_col, third_col = st.columns([1.3, 1.7, 0.8])
            first_col.markdown(f"**Rule**  \n{selected_finding['Rule']}")
            second_col.markdown(f"**Section**  \n{selected_finding['Section']}")
            third_col.markdown(f"**Severity**  \n{selected_finding['Severity']}")

            st.markdown("**Issue**")
            st.write(selected_finding["Issue"])

            st.markdown("**Suggested fix**")
            st.write(selected_finding["Suggestion"])


def render_llm_tab(
    *,
    input_ready: bool,
    assessment: dict[str, Any] | None,
    uploaded_name: str,
    selected_llm_label: str,
    selected_llm_config: dict[str, Any],
    custom_model_missing: bool,
) -> None:
    """
    Render the LLM feedback tab.

    Args:
        input_ready (bool): Whether the uploaded file is in a supported format
            and ready for processing.
        assessment (dict[str, Any] | None): Parsed assessment dictionary shared
            by ``app.py``, or ``None`` when no supported upload is ready.
        uploaded_name (str): Original uploaded filename used for downloads.
        selected_llm_label (str): Sidebar-selected LLM label used for the
            current tab run.
        selected_llm_config (dict[str, Any]): Fully resolved LLM config chosen
            in the shared sidebar.
        custom_model_missing (bool): Whether the custom-model branch is active
            but still missing a model slug.

    Returns:
        None: Value produced by this method.
    """

    llm_config_ready = bool(
        selected_llm_config.get("api_key") and selected_llm_config.get("model")
    )

    st.subheader("LLM feedback")
    st.write("Run the simplified LLM reviewer separately from the rules-based checks.")

    if custom_model_missing:
        st.info("Enter an OpenRouter model slug in the sidebar to enable the custom LLM option.")
    elif not llm_config_ready:
        st.info("Configure a valid API key and model in the sidebar to use this tab.")

    if st.button(
        "Generate feedback",
        key="generate_llm_feedback",
        type="primary",
        disabled=not input_ready or custom_model_missing or not llm_config_ready,
    ):
        with st.spinner("Generating LLM feedback..."):
            if assessment is None:
                raise ValueError("LLM feedback requires a parsed assessment dictionary.")

            llm_results = []
            llm_error = None

            try:
                # Build the provider from the shared sidebar config and run the
                # existing sequential review workflow over the shared input dict.
                provider = provider_from_config(selected_llm_config)
                llm_results = asyncio.run(
                    review_document(assessment, provider=provider, mode="sequential")
                )
            except ReviewDocumentError as exc:
                llm_error = str(exc)
                llm_results = exc.results
            except Exception as exc:
                llm_error = str(exc)

            # Preserve both the results and the execution metadata so the tab
            # can survive reruns and the download tab can export the output.
            st.session_state["llm_feedback"] = {
                "status": "success" if llm_error is None else "error",
                "model_label": selected_llm_label,
                "model_slug": selected_llm_config["model"],
                "error": llm_error,
                "display_error": _format_llm_error_message(llm_error),
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
                f"Last error: {feedback.get('display_error') or feedback['error']}"
            )

        if not feedback.get("llm_results"):
            st.info("No LLM rule results were returned.")
        else:
            _render_llm_feedback_table(feedback, assessment)

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
