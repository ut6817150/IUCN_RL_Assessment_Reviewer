"""Regression tests for reviewer checker configuration."""

import unittest

from iucn_rules_checker.assessment_reviewer import IUCNAssessmentReviewer


class AssessmentReviewerTests(unittest.TestCase):
    """Check which checker classes the reviewer wires in."""

    def test_reviewer_includes_all_checkers_except_symbols(self) -> None:
        reviewer = IUCNAssessmentReviewer()
        configured_checkers = [type(checker).__name__ for checker in reviewer.checkers]

        self.assertEqual(
            configured_checkers,
            [
                "AbbreviationChecker",
                "DateChecker",
                "FormattingChecker",
                "GeographyChecker",
                "IUCNTermsChecker",
                "NumberChecker",
                "PunctuationChecker",
                "ReferenceChecker",
                "ScientificNameChecker",
                "SpellingChecker",
            ],
        )
        self.assertNotIn("SymbolChecker", configured_checkers)
        self.assertNotIn("LanguageChecker", configured_checkers)

    def test_reviewer_skips_table_sections_but_checks_paragraph_sections(self) -> None:
        reviewer = IUCNAssessmentReviewer()
        full_report = {
            "Assessment > Notes [paragraph 1]": "Examples occur e.g. in text.",
            "Assessment > Notes [table 1] [row 1]": "Examples occur e.g. in text.",
        }

        violations = reviewer.review_full_report(full_report)
        messages = [violation.message for violation in violations]
        sections = [violation.section_name for violation in violations]

        self.assertIn("Avoid 'e.g.' in body text; use 'for example' instead", messages)
        self.assertIn("Assessment > Notes", sections)
        self.assertNotIn("Assessment > Notes [table 1] [row 1]", sections)


if __name__ == "__main__":
    unittest.main()
