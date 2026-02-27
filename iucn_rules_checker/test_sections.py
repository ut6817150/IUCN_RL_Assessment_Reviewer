import json
from collections import defaultdict
from iucn_rules_checker.engine import IUCNRuleChecker

# Load your sample JSON
with open("Acianthera odontotepala_draft_status_Jun2025 (1).json") as f:
    assessment = json.load(f)

checker = IUCNRuleChecker()
report = checker.check_json(assessment)

# Group by section
grouped = defaultdict(list)
for v in report.violations:
    section = v.assessment_section or "Whole Document"
    grouped[section].append(v)

# Print results
print(f"\nTotal violations: {report.total_violations}")
print(f"Sections found: {len(grouped)}\n")
print("=" * 60)

for section, violations in sorted(grouped.items()):
    print(f"\n[{section}]  ({len(violations)} violations)")
    for v in violations:
        print(f"  [{v.severity.value.upper()}] {v.category}: {v.message}")
        if v.matched_text:
            print(f"    Found: '{v.matched_text[:60]}'")