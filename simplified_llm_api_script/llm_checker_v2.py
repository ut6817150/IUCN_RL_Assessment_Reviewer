import asyncio
import json
from pathlib import Path
from typing import Literal

import anthropic
import frontmatter
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

BASE_DIR = Path(__file__).parent
RULES_DIR = BASE_DIR / "prompt_library" / "rules"
SYSTEM_PROMPT_PATH = BASE_DIR / "prompt_library" / "system_prompt.md"
MODEL = "claude-sonnet-4-20250514"


# ── Pydantic models ──────────────────────────────────────────────────────────

class Finding(BaseModel):
    section_path: str
    issue: str
    severity: Literal["high", "medium", "low"]
    suggestion: str


class RuleResult(BaseModel):
    rule_name: str
    findings: list[Finding]


# ── Rule loading ──────────────────────────────────────────────────────────────

REQUIRED_FRONTMATTER = {"scope", "severity", "category"}


def load_rules() -> list[dict]:
    """Load and validate all rule markdown files from the rules directory."""
    rules = []
    for path in sorted(RULES_DIR.glob("*.md")):
        post = frontmatter.load(str(path))
        missing = REQUIRED_FRONTMATTER - set(post.metadata.keys())
        if missing:
            raise ValueError(f"Rule {path.name} missing frontmatter fields: {missing}")
        rules.append({
            "name": path.stem,
            "scope": post.metadata["scope"],
            "severity": post.metadata["severity"],
            "category": post.metadata["category"],
            "body": post.content,
        })
    return rules


def load_system_prompt() -> str:
    """Load the shared system prompt."""
    return SYSTEM_PROMPT_PATH.read_text()


# ── Section selection ─────────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    """Normalize a string for fuzzy matching: lowercase, strip whitespace."""
    return s.replace(" ", "").lower().strip()


def select_sections(document_tree: dict, scope: str) -> list[dict]:
    """
    Extract the relevant parts of the document tree based on a rule's scope.

    Returns a list of section dicts. For 'section_type:*', each element is a
    single section (the rule will be called once per section).
    """
    scope_stripped = scope.strip()

    if scope_stripped == "full_document":
        return [document_tree]

    if scope_stripped.startswith("relevant_sections:"):
        names_raw = scope_stripped.split(":", 1)[1]
        target_names = {_normalize(n) for n in names_raw.split(",")}
        matched = [
            child for child in document_tree.get("children", [])
            if _normalize(child.get("title", "")) in target_names
        ]
        return matched

    if scope_stripped == "section_type:*":
        return document_tree.get("children", [])

    raise ValueError(f"Unknown scope format: {scope}")


# ── Prompt assembly & LLM call ───────────────────────────────────────────────

def _build_user_message(rule_body: str, sections: list[dict]) -> str:
    """Assemble the user message with rule instructions and document content."""
    doc_json = json.dumps(sections, indent=2, ensure_ascii=False)
    return (
        f"<rule>\n{rule_body}\n</rule>\n\n"
        f"<document>\n{doc_json}\n</document>"
    )

## CHANGE TO GET FREE LLMs
async def evaluate_rule(
    client: anthropic.AsyncAnthropic,
    system_prompt: str,
    rule: dict,
    sections: list[dict],
) -> RuleResult:
    """Make a single-turn LLM call to evaluate one rule against document sections."""
    response = await client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": _build_user_message(rule["body"], sections),
            }
        ],
    )

    raw_text = response.content[0].text

    # Strip markdown code fences if the model wraps the JSON
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]  # remove opening fence line
        cleaned = cleaned.rsplit("```", 1)[0]  # remove closing fence
        cleaned = cleaned.strip()

    data = json.loads(cleaned)
    return RuleResult(**data)


# ── Orchestration ─────────────────────────────────────────────────────────────

async def review_document(document_tree: dict) -> list[RuleResult]:
    """
    Evaluate a document tree against all rules concurrently.

    This is the main entry point, designed to be called from other scripts
    with a dict (not a file path).
    """
    rules = load_rules()
    system_prompt = load_system_prompt()
    client = anthropic.AsyncAnthropic()

    tasks = []
    for rule in rules:
        sections = select_sections(document_tree, rule["scope"])

        if rule["scope"].strip() == "section_type:*":
            # Run the rule independently against each section
            for section in sections:
                tasks.append(evaluate_rule(client, system_prompt, rule, [section]))
        else:
            tasks.append(evaluate_rule(client, system_prompt, rule, sections))

    results = await asyncio.gather(*tasks)
    return list(results)


def results_to_json(results: list[RuleResult]) -> list[dict]:
    """Convert results to a JSON-serialisable structure."""
    return [r.model_dump() for r in results]


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Default to the example JSON if no argument is provided
    json_path = sys.argv[1] if len(sys.argv) > 1 else str(
        BASE_DIR / "Myrcia almasensis_draft_status_Apr2022.json"
    )

    with open(json_path, "r", encoding="utf-8") as f:
        document_tree = json.load(f)

    results = asyncio.run(review_document(document_tree))
    print(json.dumps(results_to_json(results), indent=2, ensure_ascii=False))
