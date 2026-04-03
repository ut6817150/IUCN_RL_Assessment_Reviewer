"""Regression tests for reference-formatting behavior."""

import unittest

from iucn_rules_checker.checkers.references import ReferenceChecker


class ReferenceCheckerTests(unittest.TestCase):
    """Check the current reference rules."""

    def test_ampersand_usage_only_runs_in_bibliography_sections(self) -> None:
        checker = ReferenceChecker()

        bibliography_violations = checker.check((
            "Assessment > Bibliography [paragraph 1]",
            "Smith & Jones 2020. Example reference."
        ))
        body_violations = checker.check((
            "Assessment > Rationale [paragraph 1]",
            "Smith & Jones 2020 discussed the species."
        ))

        ampersand_messages = [
            violation.message for violation in bibliography_violations
            if "Use 'and' not '&'" in violation.message
        ]
        body_ampersand_messages = [
            violation.message for violation in body_violations
            if "Use 'and' not '&'" in violation.message
        ]

        self.assertEqual(len(ampersand_messages), 1)
        self.assertEqual(body_ampersand_messages, [])

    def test_ampersand_usage_flags_all_ampersands_in_bibliography(self) -> None:
        checker = ReferenceChecker()

        violations = checker.check((
            "Assessment > Bibliography [paragraph 1]",
            "<i>Smith</i> <b>&</b> <i>Jones</i> 2020 & Brown 2021."
        ))

        ampersand_violations = [
            violation for violation in violations
            if "Use 'and' not '&'" in violation.message
        ]

        self.assertEqual(len(ampersand_violations), 2)
        self.assertTrue(all(v.suggested_fix == "and" for v in ampersand_violations))

    def test_citation_comma_flags_bracketed_citations_with_final_comma_before_year(self) -> None:
        checker = ReferenceChecker()
        violations = checker.check((
            "Assessment > Rationale [paragraph 1]",
            "Examples include (Smith, 2020) and (Mishra et al., 2015)."
        ))

        citation_violations = [
            violation for violation in violations
            if "No comma between author and date" in violation.message
        ]

        self.assertEqual(len(citation_violations), 2)
        self.assertEqual(
            [violation.suggested_fix for violation in citation_violations],
            ["(Smith 2020)", "(Mishra et al. 2015)"],
        )

    def test_citation_comma_strips_style_markers_before_matching(self) -> None:
        checker = ReferenceChecker()
        violations = checker.check((
            "Assessment > Rationale [paragraph 1]",
            "Examples include (<i>Smith</i>, <b>2020</b>) and "
            "(<sup>Mishra et al.</sup>, <sub>2015</sub>)."
        ))

        citation_violations = [
            violation for violation in violations
            if "No comma between author and date" in violation.message
        ]

        self.assertEqual(len(citation_violations), 2)
        self.assertEqual(
            [violation.suggested_fix for violation in citation_violations],
            ["(Smith 2020)", "(Mishra et al. 2015)"],
        )

    def test_citation_comma_skips_square_brackets_unbracketed_and_already_correct_forms(self) -> None:
        checker = ReferenceChecker()
        violations = checker.check((
            "Assessment > Rationale [paragraph 1]",
            "Examples include (Smith 2020), [GBIF.org, 2021], and Smith, 2020."
        ))

        citation_violations = [
            violation for violation in violations
            if "No comma between author and date" in violation.message
        ]

        self.assertEqual(citation_violations, [])


if __name__ == "__main__":
    unittest.main()
