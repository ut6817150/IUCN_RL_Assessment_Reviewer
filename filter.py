import json
from pathlib import Path
from typing import Dict, List


def filter_non_rule_based_rules(input_path: Path, output_path: Path) -> None:
    """
    Load the IUCN rules JSON file,
    remove rules where 'Judgment Type' == 'Rule-based',
    and save the remaining rules in the same JSON schema.
    """

    # Load original file
    with open(input_path, "r", encoding="utf-8") as f:
        data: Dict = json.load(f)

    rules: List[Dict] = data.get("IUCN Assessment Rules", [])

    # Filter out Rule-based rules (case-insensitive safe)
    filtered_rules = [
        r for r in rules
        if (r.get("Judgment Type") or "").strip().lower() != "rule-based"
    ]

    # Keep same schema
    output_data = {
        "IUCN Assessment Rules": filtered_rules
    }

    # Save to new file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Original rules: {len(rules)}")
    print(f"Filtered rules (LLM + Hybrid): {len(filtered_rules)}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    input_file = Path("IUCN_Assessment_Rules.json")
    output_file = Path("IUCN_Assessment_Rules_LLM_Hybrid.json")

    filter_non_rule_based_rules(input_file, output_file)