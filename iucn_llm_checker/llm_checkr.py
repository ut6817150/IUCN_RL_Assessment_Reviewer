import json
import sys
from pathlib import Path
from datetime import datetime
from ollama import chat

SCRIPT_DIR = Path(__file__).parent
RULES_PATH = SCRIPT_DIR.parent / "IUCN_Assessment_Rules.json"
PROMPT_TEMPLATE_PATH = SCRIPT_DIR / "llm_check.md"


def load_rules(rules_path: Path) -> list[dict]:
    with open(rules_path, encoding="utf-8") as f:
        data = json.load(f)
    return [r for r in data["IUCN Assessment Rules"] if r["Judgment Type"] == "LLM-judged"]


def load_prompt_template(template_path: Path) -> str:
    return template_path.read_text(encoding="utf-8")


def check_single_rule(assessment_text: str, rule: dict, system_prompt: str) -> dict:
    rule_text = rule["Rule/Standard"]

    response = chat(
        model="deepseek-r1:1.5b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": assessment_text},
            {"role": "system", "content": f"RULE TO CHECK: {rule_text}"},
        ],
        think=True,
    )

    return {
        "document_source": rule["Document Source"],
        "section_category": rule["Section/Category"],
        "rule": rule_text,
        "assessment_section": rule["Assessment Section"],
        "rationale": rule["Rationale"],
        "feedback": response.message.content,
        "thinking": response.message.thinking,
    }


def run_llm_checks(assessment_file: str, output_file: str = "llm_check_results.json") -> None:
    assessment_path = Path(assessment_file)
    if not assessment_path.exists():
        print(f"Error: Assessment file not found: {assessment_file}", file=sys.stderr)
        sys.exit(1)

    assessment_text = assessment_path.read_text(encoding="utf-8")
    rules = load_rules(RULES_PATH)
    system_prompt = load_prompt_template(PROMPT_TEMPLATE_PATH)
    total_rules = len(rules)
    results = []

    print(f"Checking assessment against {total_rules} LLM-judged rules...")
    print(f"Model: deepseek-r1 (thinking enabled)")
    print(f"Assessment file: {assessment_file}")
    print("-" * 60)

    for i, rule in enumerate(rules, 1):
        rule_text = rule["Rule/Standard"]
        section = rule["Section/Category"]
        print(f"[{i}/{total_rules}] Checking: {section} - {rule_text}...", end=" ", flush=True)

        try:
            result = check_single_rule(assessment_text, rule, system_prompt)
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
                "thinking": None,
                "status": "error",
                "error_message": str(e),
            }
            print(f"ERROR: {e}")

        results.append(result)

    output = {
        "metadata": {
            "assessment_file": str(assessment_path.resolve()),
            "timestamp": datetime.now().isoformat(),
            "model": "deepseek-r1",
            "total_rules_checked": total_rules,
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python llm_checkr.py <assessment_file.txt> [output_file.json]")
        sys.exit(1)

    assessment_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "llm_check_results.json"
    run_llm_checks(assessment_file, output_file)
