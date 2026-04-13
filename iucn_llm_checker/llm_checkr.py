import json
import sys
from pathlib import Path
from datetime import datetime
from rag_retriever import retrieve_context
from ollama import chat
import time
# from json_loader import load_assessment_from_json

SCRIPT_DIR = Path(__file__).parent
RULES_PATH = SCRIPT_DIR.parent / "IUCN_Assessment_Threats.json"
PROMPT_TEMPLATE_PATH = SCRIPT_DIR / "llm_check.md"


def load_rules(rules_path: Path) -> list[dict]:
    with open(rules_path, encoding="utf-8") as f:
        data = json.load(f)
    return data["IUCN Assessment Rules"]


def load_prompt_template(template_path: Path) -> str:
    return template_path.read_text(encoding="utf-8")


def load_assessment_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_single_rule(assessment_json: dict, rule: dict, system_prompt: str) -> dict:
    rule_text = rule["Rule/Standard"]

    rag_ctx = retrieve_context(rule_text, top_k=3)

    assessment_data = json.dumps(assessment_json, ensure_ascii=False, separators=(",", ":"))

    response = chat(
        model="deepseek-r1:1.5b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"RULE TO CHECK:\n{rule_text}"},
            {"role": "user", "content": f"RETRIEVED CONTEXT (Standards):\n{rag_ctx}"},
            {"role": "user", "content": f"ASSESSMENT FILE:\n{assessment_data}"},
        ],
        think=False
    )

    # feedback = response.message.content.strip()

    # if feedback.lower() == "good":
    #     feedback = "Good"

    # is_good = (feedback == "Good")

    # Base fields always returned
    result = {
        "document_source": rule["Document Source"],
        "section_category": rule["Section/Category"],
        "rule": rule_text,
        "assessment_section": rule["Assessment Section"],
        "rationale": rule["Rationale"],
        "feedback": response.message.content,
        # Optional: easier post-analysis
        # "violation_status": "good" if is_good else "breach",
    }

    # IMPORTANT: only include debug fields when breach
    # if not is_good:
        # keep these only for breaches (debugging / audit)
        # result["retrieved_context"] = rag_ctx
    
    return result


def run_llm_checks(assessment_file: str, output_file: str = "llm_check_results.json") -> None:
    start_time = time.perf_counter()
    assessment_path = Path(assessment_file)
    if not assessment_path.exists():
        print(f"Error: Assessment file not found: {assessment_file}", file=sys.stderr)
        sys.exit(1)

    # Load JSON directly (dict)
    if assessment_path.suffix.lower() != ".json":
        raise ValueError("Option 1 expects a .json assessment file as input.")
    
    assessment_data = load_assessment_json(assessment_path)

    rules = load_rules(RULES_PATH)
    system_prompt = load_prompt_template(PROMPT_TEMPLATE_PATH)
    total_rules = len(rules)
    results = []

    print(f"Checking assessment against {total_rules} LLM-judged rules...")
    print(f"Model: deepseek-r1")
    print(f"Assessment file: {assessment_file}")
    print("-" * 60)

    for i, rule in enumerate(rules, 1):
        rule_text = rule["Rule/Standard"]
        section = rule["Section/Category"]
        print(f"[{i}/{total_rules}] Checking: {section} - {rule_text}...", end=" ", flush=True)

        try:
            result = check_single_rule(assessment_data, rule, system_prompt)
            result["status"] = "completed"
            print("Done.")
        except Exception as e:
            result = {
                "document_source": rule["Document Source"],
                "section_category": rule["Section/Category"],
                "rule": rule_text,
                "assessment_section": rule["Assessment Section"],
                "rationale": rule["Rationale"],
                "feedback": None,
                # "thinking": None,
                "status": "error",
                "error_message": str(e),
            }
            print(f"ERROR: {e}")

        results.append(result)

    total_seconds = time.perf_counter() - start_time

    output = {
        "metadata": {
            "assessment_file": str(assessment_path.resolve()),
            "timestamp": datetime.now().isoformat(),
            "model": "deepseek-r1",
            "total_rules_checked": total_rules,
            "total_seconds": round(total_seconds, 4),
            "successful": sum(1 for r in results if r["status"] == "completed"),
            "errors": sum(1 for r in results if r["status"] == "error"),
        },
        "results": results,
    }

    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("-" * 60)
    print(f"Results saved to: {output_path.resolve()}")
    print(f"Completed: {output['metadata']['successful']}/{total_rules}")
    if output["metadata"]["errors"] > 0:
        print(f"Errors: {output['metadata']['errors']}")
    print(f"Total runtime: {total_seconds:.2f} seconds")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py llm_checkr.py <assessment_file.json> [output_file.json]")
        sys.exit(1)

    assessment_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "llm_check_results.json"
    run_llm_checks(assessment_file, output_file)
