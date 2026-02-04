"""Punctuation checker for IUCN assessments."""

import re
from typing import List

from .base import BaseChecker
from ..models import Violation, Severity


class PunctuationChecker(BaseChecker):
    """Checker for punctuation rules."""

    def __init__(self):
        super().__init__(
            rule_id="punctuation_format",
            rule_name="Punctuation formatting rules",
            category="Punctuation",
            severity=Severity.WARNING,
            assessment_section="Whole Document"
        )

    def check(self, text: str) -> List[Violation]:
        """Check for punctuation violations."""
        violations = []

        # En dash for ranges
        violations.extend(self._check_range_dashes(text))

        # Commas around "for example"
        violations.extend(self._check_for_example_commas(text))

        return violations

    def _check_range_dashes(self, text: str) -> List[Violation]:
        """Check that ranges use en dash (–) not hyphen (-)."""
        violations = []

        # Pattern: number-number or year-year ranges with hyphen
        # Should be en dash (–)
        range_pattern = re.compile(r'(\d+)\s*-\s*(\d+)')

        for match in range_pattern.finditer(text):
            # Skip if it's already an en dash
            if '–' in match.group(0) or '—' in match.group(0):
                continue

            # Skip negative numbers (e.g., "-5")
            before = text[max(0, match.start()-1):match.start()]
            if before in ['', ' ', '\n', '(', '[']:
                num1, num2 = match.group(1), match.group(2)
                # This looks like a range
                fix = f"{num1}–{num2}"  # En dash
                violations.append(self._create_violation(
                    text=text,
                    matched_text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    message="Use en dash (–) for ranges, not hyphen (-)",
                    suggested_fix=fix
                ))

        return violations

    def _check_for_example_commas(self, text: str) -> List[Violation]:
        """Check that 'for example' is surrounded by commas."""
        violations = []

        # "for example" without preceding comma
        pattern_no_before = re.compile(r'(?<![,])\s+for example\b', re.IGNORECASE)
        for match in pattern_no_before.finditer(text):
            # Check if it's at the start of a sentence
            before = text[max(0, match.start()-2):match.start()]
            if not before.strip() or before.strip()[-1] in '.!?':
                continue  # OK at sentence start

            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0).strip(),
                start=match.start(),
                end=match.end(),
                message="'for example' should be preceded by a comma",
                suggested_fix=None
            ))

        # "for example" without following comma
        pattern_no_after = re.compile(r'\bfor example(?![,])\s+\w', re.IGNORECASE)
        for match in pattern_no_after.finditer(text):
            violations.append(self._create_violation(
                text=text,
                matched_text="for example",
                start=match.start(),
                end=match.start() + 11,
                message="'for example' should be followed by a comma",
                suggested_fix="for example,"
            ))

        return violations
