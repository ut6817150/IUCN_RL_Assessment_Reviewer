"""
convert_doc_folder.py

Batch convert legacy .doc files into .docx files
using doc2docx.

Run:
    python3.12 convert_doc_folder.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

from doc2docx import convert


# Default folders
INPUT_FOLDER = Path("assessments_doc")
OUTPUT_FOLDER = Path("converted")


def main():
    if not INPUT_FOLDER.exists():
        print(f"Input folder not found: {INPUT_FOLDER.resolve()}")
        return 1

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    doc_files = sorted(INPUT_FOLDER.glob("*.doc"))
    if not doc_files:
        print(f"No .doc files found in {INPUT_FOLDER}")
        return 0

    converted = 0
    skipped = 0
    errors: List[Dict[str, str]] = []

    for doc_path in doc_files:
        out_path = OUTPUT_FOLDER / f"{doc_path.stem}.docx"

        if out_path.exists():
            skipped += 1
            print(f"Skip: {doc_path.name} (already converted)")
            continue

        try:
            convert(str(doc_path), str(out_path))
            converted += 1
            print(f"Done: {doc_path.name} -> {out_path.name}")

        except Exception as e:
            errors.append({"file": doc_path.name, "error": repr(e)})
            print(f"Failed: {doc_path.name} ({e!r})")

    # Save error report
    error_file = OUTPUT_FOLDER / "_conversion_errors.json"
    with open(error_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total": len(doc_files),
                "converted": converted,
                "skipped": skipped,
                "failed": len(errors),
                "errors": errors,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\n===============================")
    print(f"Converted: {converted}")
    print(f"Skipped:   {skipped}")
    print(f"Failed:    {len(errors)}")
    print(f"Error log saved to: {error_file.name}")
    print("===============================")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
