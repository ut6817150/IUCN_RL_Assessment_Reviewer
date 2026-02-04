"""Abbreviation checker for IUCN assessments."""

import re
from typing import List, Tuple

from .base import BaseChecker
from ..models import Violation, Severity


class AbbreviationChecker(BaseChecker):
    """Checker for abbreviation rules."""

    def __init__(self):
        super().__init__(
            rule_id="abbreviations_format",
            rule_name="Abbreviation formatting rules",
            category="Abbreviations",
            severity=Severity.WARNING,
            assessment_section="Whole Document"
        )

    def check(self, text: str) -> List[Violation]:
        """Check for abbreviation violations."""
        violations = []

        # e.g. and i.e. should be avoided in body text
        violations.extend(self._check_latin_abbreviations(text))

        # Correct format for common abbreviations
        violations.extend(self._check_abbreviation_formats(text))

        # Latin terms without periods
        violations.extend(self._check_latin_terms(text))

        # Title abbreviations
        violations.extend(self._check_title_abbreviations(text))

        return violations

    def _check_latin_abbreviations(self, text: str) -> List[Violation]:
        """Check for e.g. and i.e. which should be avoided in body text."""
        violations = []

        # e.g. - should use "for example"
        eg_pattern = re.compile(r'\be\.g\.(?:\s|,)', re.IGNORECASE)
        for match in eg_pattern.finditer(text):
            # Check if it's in brackets (more acceptable)
            before = text[max(0, match.start()-5):match.start()]
            if '(' in before:
                continue  # Skip if in brackets

            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0).strip(),
                start=match.start(),
                end=match.end()-1,
                message="Avoid 'e.g.' in body text; use 'for example' instead",
                suggested_fix="for example,"
            ))

        # i.e. - should use "that is"
        ie_pattern = re.compile(r'\bi\.e\.(?:\s|,)', re.IGNORECASE)
        for match in ie_pattern.finditer(text):
            before = text[max(0, match.start()-5):match.start()]
            if '(' in before:
                continue

            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0).strip(),
                start=match.start(),
                end=match.end()-1,
                message="Avoid 'i.e.' in body text; use 'that is' instead",
                suggested_fix="that is,"
            ))

        return violations

    def _check_abbreviation_formats(self, text: str) -> List[Violation]:
        """Check correct format for common abbreviations."""
        violations = []

        # etc without period
        etc_pattern = re.compile(r'\betc\b(?!\.)')
        for match in etc_pattern.finditer(text):
            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                message="Use 'etc.' with period",
                suggested_fix="etc."
            ))

        # et al without period
        etal_pattern = re.compile(r'\bet al\b(?!\.)')
        for match in etal_pattern.finditer(text):
            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                message="Use 'et al.' with period",
                suggested_fix="et al."
            ))

        # in lit instead of in litt.
        inlit_pattern = re.compile(r'\bin lit\b(?!t)')
        for match in inlit_pattern.finditer(text):
            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                message="Use 'in litt.' not 'in lit'",
                suggested_fix="in litt."
            ))

        # pers. comm without period after comm
        perscomm_pattern = re.compile(r'\bpers\.\s*comm\b(?!\.)')
        for match in perscomm_pattern.finditer(text):
            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                message="Use 'pers. comm.' format",
                suggested_fix="pers. comm."
            ))

        # pers. obs without period
        persobs_pattern = re.compile(r'\bpers\.\s*obs\b(?!\.)')
        for match in persobs_pattern.finditer(text):
            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                message="Use 'pers. obs.' format",
                suggested_fix="pers. obs."
            ))

        # Prof without period
        prof_pattern = re.compile(r'\bProf\b(?!\.)')
        for match in prof_pattern.finditer(text):
            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                message="Use 'Prof.' with period",
                suggested_fix="Prof."
            ))

        return violations

    def _check_latin_terms(self, text: str) -> List[Violation]:
        """Check Latin terms that should NOT have periods."""
        violations = []

        # in situ. -> in situ (no period)
        insitu_pattern = re.compile(r'\bin\s*situ\.')
        for match in insitu_pattern.finditer(text):
            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                message="Use 'in situ' without period",
                suggested_fix="in situ"
            ))

        # ex situ. -> ex situ (no period)
        exsitu_pattern = re.compile(r'\bex\s*situ\.')
        for match in exsitu_pattern.finditer(text):
            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                message="Use 'ex situ' without period",
                suggested_fix="ex situ"
            ))

        # ad hoc. -> ad hoc (no period)
        adhoc_pattern = re.compile(r'\bad\s*hoc\.')
        for match in adhoc_pattern.finditer(text):
            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                message="Use 'ad hoc' without periods",
                suggested_fix="ad hoc"
            ))

        return violations

    def _check_title_abbreviations(self, text: str) -> List[Violation]:
        """Check title abbreviation formats."""
        violations = []

        # Dr. should be Dr (UK style - no period)
        dr_pattern = re.compile(r'\bDr\.(?=\s)')
        for match in dr_pattern.finditer(text):
            violations.append(self._create_violation(
                text=text,
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                message="Use 'Dr' without period (UK style)",
                suggested_fix="Dr"
            ))

        return violations
