"""Geographic naming checker for IUCN assessments."""

import re
from typing import List

from checkers.base import BaseChecker
from models import Violation, Severity


class GeographyChecker(BaseChecker):
    """Checker for geographic naming conventions (ISO 3166)."""

    # Common incorrect country names -> correct (ISO 3166) names
    COUNTRY_CORRECTIONS = {
        "vietnam": "Viet Nam",
        "laos": "Lao PDR",
        "ivory coast": "Cote d'Ivoire",
        "burma": "Myanmar",
        "kazakstan": "Kazakhstan",
        "zaire": "DRC",
        "democratic republic of congo": "DRC",
        "democratic republic of the congo": "DRC",
        "congo-kinshasa": "DRC",
        "congo, democratic republic": "DRC",
        "republic of congo": "Republic of the Congo",
        "congo-brazzaville": "Republic of the Congo",
        "great britain": "United Kingdom",
        "holland": "Netherlands",
        "czech republic": "Czechia",
        "swaziland": "Eswatini",
        "cape verde": "Cabo Verde",
        "ivory coast": "Cote d'Ivoire",
        "cote d'ivoire": "Cote d'Ivoire",  # Correct but check apostrophe
    }

    def __init__(self):
        super().__init__(
            rule_id="geography_names",
            rule_name="Geographic naming conventions",
            category="Geography",
            severity=Severity.WARNING,
            assessment_section="Geographic Range"
        )

    def check(self, text: str) -> List[Violation]:
        """Check for geographic naming violations."""
        violations = []

        # Check country name corrections
        violations.extend(self._check_country_names(text))

        # Check directional capitalization
        violations.extend(self._check_directional_capitalization(text))

        return violations

    def _check_country_names(self, text: str) -> List[Violation]:
        """Check for incorrect country names."""
        violations = []

        for incorrect, correct in self.COUNTRY_CORRECTIONS.items():
            pattern = re.compile(rf'\b{re.escape(incorrect)}\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                # Don't flag if already correct
                if match.group(0) == correct:
                    continue

                violations.append(self._create_violation(
                    text=text,
                    matched_text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    message=f"Use ISO 3166 country name: '{correct}' not '{match.group(0)}'",
                    suggested_fix=correct
                ))

        return violations

    def _check_directional_capitalization(self, text: str) -> List[Violation]:
        """Check capitalization of directions (should be lowercase unless part of proper name)."""
        violations = []

        # Directions should generally be lowercase when describing parts of countries
        # e.g., "east Japan" not "East Japan" (but "East Africa" is a proper name)
        directions = ['North', 'South', 'East', 'West', 'Northern', 'Southern', 'Eastern', 'Western']

        for direction in directions:
            # Pattern: Direction + country name (not at sentence start)
            pattern = re.compile(rf'(?<=[a-z]\s){direction}\s+([A-Z][a-z]+)\b')
            for match in pattern.finditer(text):
                country = match.group(1)
                # Check if this is a proper region name (like "East Africa", "North America")
                proper_regions = ['Africa', 'America', 'Asia', 'Europe', 'Pacific', 'Atlantic',
                                 'Indies', 'Ireland', 'Korea', 'Carolina', 'Dakota', 'Virginia']
                if country in proper_regions:
                    continue

                lower_direction = direction.lower()
                fix = f"{lower_direction} {country}"
                violations.append(self._create_violation(
                    text=text,
                    matched_text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    message=f"Use lowercase direction for parts of countries: '{fix}'",
                    suggested_fix=fix
                ))

        return violations
