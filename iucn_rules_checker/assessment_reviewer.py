"""Parse an assessment and apply configured checkers to every parsed section."""

import re
from typing import Any, Dict, List, Tuple, Type

try:
    from .assessment_parser import AssessmentParser
    from .checkers.abbreviations import AbbreviationChecker
    from .checkers.base import BaseChecker
    from .checkers.dates import DateChecker
    from .checkers.formatting import FormattingChecker
    from .checkers.geography import GeographyChecker
    from .checkers.iucn_terms import IUCNTermsChecker
    from .checkers.numbers import NumberChecker
    from .checkers.punctuation import PunctuationChecker
    from .checkers.references import ReferenceChecker
    from .checkers.scientific import ScientificNameChecker
    from .checkers.spelling import SpellingChecker
    from .violation import Violation
except ImportError:  # pragma: no cover - direct script execution fallback
    from assessment_parser import AssessmentParser
    from checkers.abbreviations import AbbreviationChecker
    from checkers.base import BaseChecker
    from checkers.dates import DateChecker
    from checkers.formatting import FormattingChecker
    from checkers.geography import GeographyChecker
    from checkers.iucn_terms import IUCNTermsChecker
    from checkers.numbers import NumberChecker
    from checkers.punctuation import PunctuationChecker
    from checkers.references import ReferenceChecker
    from checkers.scientific import ScientificNameChecker
    from checkers.spelling import SpellingChecker
    from violation import Violation


class IUCNAssessmentReviewer:
    """Review parsed assessment sections and return rule violations."""

    CHECKER_CLASSES: Tuple[Type[BaseChecker], ...] = (
        AbbreviationChecker,
        DateChecker,
        FormattingChecker,
        GeographyChecker,
        IUCNTermsChecker,
        NumberChecker,
        PunctuationChecker,
        ReferenceChecker,
        ScientificNameChecker,
        SpellingChecker,
    )

    def __init__(self):
        self.assessment_parser = AssessmentParser()
        self.checkers = self.create_checkers()

    def create_checkers(self) -> List[BaseChecker]:
        """Create the configured text checkers."""
        return [checker_class() for checker_class in self.CHECKER_CLASSES]

    def review_assessment(self, assessment: Dict[str, Any]) -> List[Violation]:
        """Parse an assessment tree dict and return all violations."""
        full_report = self.assessment_parser.parse(assessment)
        return self.review_full_report(full_report)

    def is_table_section(self, section_name: str) -> bool:
        """Return True when a parsed section key represents table-derived content."""
        return re.search(r"\[table\s+\d+\]", section_name, re.IGNORECASE) is not None

    def review_full_report(self, full_report: Dict[str, str]) -> List[Violation]:
        """Apply each rule to each ``section -> text`` pair in the parsed report."""
        if not isinstance(full_report, dict):
            raise TypeError("review_full_report() expects a dict of section paths to text.")

        violations: List[Violation] = []
        for checker in self.checkers:
            checker.begin_sweep()

        try:
            for section_name, section_text in full_report.items():
                if not section_text.strip():
                    continue
                if self.is_table_section(section_name):
                    continue

                section_item = (section_name, section_text)
                for checker in self.checkers:
                    violations.extend(checker.check(section_item))
        finally:
            for checker in self.checkers:
                checker.end_sweep()

        return violations
