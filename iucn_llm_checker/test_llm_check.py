"""
Test script for running the LLM checker against a sample assessment
that intentionally violates multiple LLM-judged IUCN rules.

Usage:
    python test_llm_check.py
    python test_llm_check.py --output results.json
"""

import argparse
from pathlib import Path
from llm_checkr import run_llm_checks

SCRIPT_DIR = Path(__file__).parent
DEFAULT_INPUT = SCRIPT_DIR / "test_assessment.txt"
DEFAULT_OUTPUT = SCRIPT_DIR / "test_llm_check_results.json"


def main():
    parser = argparse.ArgumentParser(description="Run LLM checks on the test assessment file")
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT),
        help="Path to the assessment text file (default: test_assessment.txt)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help="Path for the output JSON file (default: test_llm_check_results.json)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("IUCN LLM Checker - Test Run")
    print("=" * 60)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print("=" * 60)

    run_llm_checks(args.input, args.output)

    print()
    print("=" * 60)
    print(f"Feedback JSON written to: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
