"""
Utilities for loading and flattening tree-structured IUCN assessment JSON
into plain text suitable for LLM input.
"""

import json
from pathlib import Path
from typing import List


def _format_table(rows: List[List[str]]) -> str:
    """
    Convert a JSON table block into markdown-style text.
    Keeps structure readable for LLM reasoning.
    """
    if not rows:
        return ""

    # Convert all cells to strings and strip whitespace
    rows = [[("" if c is None else str(c)).strip() for c in r] for r in rows]

    # If single-column rows → bullet list
    if all(len(r) == 1 for r in rows):
        return "\n".join(f"- {r[0]}" for r in rows if r and r[0])

    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []

    lines = []
    lines.append(" | ".join(header))
    lines.append(" | ".join(["---"] * len(header)))

    for r in body:
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
        elif len(r) > len(header):
            r = r[: len(header)]
        lines.append(" | ".join(r))

    return "\n".join(lines)


def _flatten_node(node: dict, lines: List[str]) -> None:
    """
    Recursively traverse JSON assessment tree and append text to lines.
    """

    title = node.get("title")
    level = node.get("level", 1)

    if title:
        heading_level = max(1, min(6, int(level)))
        lines.append("#" * heading_level + " " + title)

    # Process content blocks
    for block in node.get("blocks", []):
        btype = block.get("type")

        if btype == "paragraph":
            text = (block.get("text") or "").strip()
            if text:
                lines.append(text)

        elif btype == "table":
            table_text = _format_table(block.get("rows", []))
            if table_text:
                lines.append(table_text)

    # Recurse into children
    for child in node.get("children", []):
        _flatten_node(child, lines)


def load_assessment_from_json(path: Path) -> str:
    """
    Load a tree-structured IUCN assessment JSON file
    and return flattened plain text.
    """

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    lines: List[str] = []
    _flatten_node(data, lines)

    # Clean excessive blank lines
    cleaned = []
    last_blank = False
    for line in lines:
        line = line.strip()
        if not line:
            if not last_blank:
                cleaned.append("")
            last_blank = True
        else:
            cleaned.append(line)
            last_blank = False

    text = "\n".join(cleaned).strip()

    txt_path = path.with_suffix(".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    return text

if __name__ == "__main__":
    load_assessment_from_json(Path("Habropetalum dawei_draft_status_Apr2023.json"))