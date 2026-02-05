import json

# 1. Read data
with open("IUCN_Assessment_Rules.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rules = data["IUCN Assessment Rules"]

# 2. Filter LLM-judged and Hybrid checks
llm_related_rules = [
    rule for rule in rules
    if rule.get("Judgment Type") in {"LLM-judged", "Hybrid"}
]

# 3. Check
print(f"Total rules: {len(rules)}")
print(f"LLM / Hybrid rules: {len(llm_related_rules)}")

# 4. Save as new file
with open("llm_hybrid_rules.json", "w", encoding="utf-8") as f:
    json.dump(
        {"IUCN Assessment Rules": llm_related_rules},
        f,
        ensure_ascii=False,
        indent=2
    )
