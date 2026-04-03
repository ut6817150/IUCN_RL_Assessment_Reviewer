"""Formatting checker for IUCN assessments (italics, bold, etc.).

This checker expects text to contain HTML formatting tags:
- <i>text</i> or <em>text</em> for italics
- <b>text</b> or <strong>text</strong> for bold
"""

import re
from typing import List, Optional, Set

from ..violation import Violation
from .base import BaseChecker


class FormattingChecker(BaseChecker):
    """Checker for formatting rules such as scientific-name italics."""

    FAMILY_SUFFIXES = {
        'aceae',
        'idae',
        'ales',
        'ineae',
        'inae',
        'eae',
        'oideae',
    }

    KNOWN_FAMILIES = {
        'Orchidaceae', 'Rubiaceae', 'Fabaceae', 'Asteraceae', 'Poaceae',
        'Rosaceae', 'Euphorbiaceae', 'Lamiaceae', 'Malvaceae', 'Solanaceae',
        'Brassicaceae', 'Apiaceae', 'Cactaceae', 'Acanthaceae', 'Araceae',
        'Felidae', 'Canidae', 'Hominidae', 'Bovidae', 'Cervidae',
        'Accipitridae', 'Columbidae', 'Psittacidae', 'Salamandridae',
        'Rosales', 'Fabales', 'Asparagales', 'Lamiales', 'Solanales',
        'Carnivora', 'Primates', 'Rodentia',
    }

    def __init__(self):
        super().__init__()
        self._collected_higher_taxonomy_names: Set[str] = set()
        self._collected_genus_name: Optional[str] = None
        self._collected_species_name: Optional[str] = None

    def begin_sweep(self) -> None:
        """Reset temporary taxonomy names before processing a full report."""
        self._collected_higher_taxonomy_names.clear()
        self._collected_genus_name = None
        self._collected_species_name = None

    def end_sweep(self) -> None:
        """Clear temporary taxonomy names after processing a full report."""
        self._collected_higher_taxonomy_names.clear()
        self._collected_genus_name = None
        self._collected_species_name = None

    def check_text(self, section_name: str, text: str) -> List[Violation]:
        """Check for formatting violations."""
        violations = []
        violations.extend(self.check_genus_and_species(section_name, text))
        violations.extend(self.check_family_name_capitalized_and_not_italicized(section_name, text))
        violations.extend(self.check_eoo_aoo_capitalization(section_name, text))
        return violations

    def check_eoo_aoo_capitalization(self, section_name: str, text: str) -> List[Violation]:
        """Check capitalization of spelled-out EOO/AOO phrases.

        This method strips simple inline style tags first:
        ``<i>``, ``<em>``, ``<b>``, ``<strong>``, ``<sup>``, and ``<sub>``.

        This method checks the full phrases:
        - ``extent of occurrence``
        - ``area of occupancy``

        It treats the fully lowercase form as the default correct form and
        flags capitalized or partially capitalized variants such as:
        - ``Extent of Occurrence``
        - ``Area of Occupancy``
        - ``Extent of occurrence``
        - ``Area of occupancy``
        - ``extent of Occurrence``

        It can catch these forms:
        - mid-sentence, for example ``the Extent of Occurrence was revised``
        - after punctuation such as ``(``, `:` and `,`
        - at the start of a text block
        - after ``?`` and ``!``

        There is one explicit exception:
        if the phrase is written with only the first word capitalized and is
        at the start of a paragraph or immediately preceded by ``. ``, ``? ``,
        or ``: ``, it is treated as an allowed sentence start.
        Examples allowed:
        - ``Extent of occurrence remained restricted.``
        - ``This was revised. Extent of occurrence remained restricted.``
        - ``Was this revised? Extent of occurrence was updated.``
        - ``Summary: Area of occupancy was recalculated.``
        - ``That was updated. Area of occupancy stayed small.``

        Examples still flagged:
        - ``The Extent of occurrence was revised.``
        - ``Summary, Area of occupancy was recalculated.``
        - ``(Extent of occurrence) was revised.``

        Examples not checked:
        - ``EOO`` and ``AOO`` abbreviations
        - misspelled forms such as ``extent of occurence``
        - reworded phrases such as ``occupied area``
        """
        violations = []
        cleaned_text, index_map = self.strip_style_markers(
            text,
            italics=True,
            bold=True,
            superscript=True,
            subscript=True,
        )
        terms = (
            'extent of occurrence',
            'area of occupancy',
        )

        def is_allowed_sentence_start(index: int) -> bool:
            if index == 0:
                return True
            if index >= 2 and cleaned_text[index - 2:index] in {'. ', '? ', ': '}:
                return True
            return False

        for correct in terms:
            phrase_pattern = re.escape(correct).replace(r'\ ', r'\s+')
            pattern = re.compile(rf'\b{phrase_pattern}\b', re.IGNORECASE)
            for match in pattern.finditer(cleaned_text):
                matched_phrase = match.group(0)
                normalized_phrase = ' '.join(matched_phrase.split())
                sentence_start_phrase = correct.capitalize()

                if normalized_phrase == correct:
                    continue
                if normalized_phrase == sentence_start_phrase and is_allowed_sentence_start(match.start()):
                    continue

                original_start = index_map[match.start()]
                original_end = index_map[match.end() - 1] + 1
                violations.append(self.create_violation(
                    section_name=section_name,
                    text=text,
                    span=(original_start, original_end),
                    message=f"Use lowercase: '{correct}' not '{matched_phrase}'",
                    suggested_fix=correct,
                ))

        return violations

    def check_family_name_capitalized_and_not_italicized(self, section_name: str, text: str) -> List[Violation]:
        """Check that family/taxonomy names are capitalized and not italicized.

        This method strips non-italic inline style tags first:
        ``<b>``, ``<strong>``, ``<sup>``, and ``<sub>``.
        It preserves ``<i>`` / ``<em>`` because italicization is part of the
        rule being checked.

        During a full-report sweep, this method first looks for taxonomy-ladder
        entries such as:
        ``PLANTAE - TRACHEOPHYTA - MAGNOLIOPSIDA - FABALES - FABACEAE - Acrocarpus - fraxinifolius``.
        When it finds one, it does not report violations for that value.
        Instead, it harvests the all-uppercase higher-order taxonomy names,
        normalizes them to title case (for example ``FABACEAE`` -> ``Fabaceae``),
        stores them temporarily, and uses them while checking the remaining
        sections in the same sweep. The temporary list is cleared when the
        sweep ends.

        Outside those harvested higher-order names, the method also looks for
        family- or higher-taxon-looking names based on the configured suffix
        list, such as ``-aceae``, ``-idae`` and ``-ales``. It then checks two
        things at once:
        - whether the name starts with a capital letter
        - whether the name is free of surrounding ``<i>...</i>`` or
          ``<em>...</em>`` markup

        A suffix-based match is treated as worth checking if the capitalized
        form is either:
        - in the ``KNOWN_FAMILIES`` set, or
        - not in ``KNOWN_FAMILIES`` but still has a stem of at least 4 letters
          before the family/rank suffix

        In practice, that means the method is willing to flag unknown-looking
        names such as ``mysteriaceae`` because ``mysteri`` is long enough to
        resemble a taxonomic stem, but it tries to avoid very short accidental
        matches where a normal word happens to end with one of the suffixes.

        Examples flagged:
        - ``orchidaceae`` -> suggests ``Orchidaceae``
        - ``felidae`` -> suggests ``Felidae``
        - ``<i>Orchidaceae</i>`` -> suggests ``Orchidaceae``
        - ``<i>felidae</i>`` -> suggests ``Felidae``
        - after harvesting taxonomy names from a ladder entry:
          ``plantae`` -> suggests ``Plantae``
        - after harvesting taxonomy names from a ladder entry:
          ``<i>Magnoliopsida</i>`` -> suggests ``Magnoliopsida``

        Examples not flagged:
        - ``Orchidaceae`` because it is capitalized and not italicized
        - ``Felidae`` because it is capitalized and not italicized
        - ``family`` because literal rank labels are outside this method's scope
        - ``<i>family</i>`` because literal rank labels are outside this method's scope
        - words that do not match one of the configured suffixes
        - short suffix-matching words that do not look taxonomic enough to pass the plausibility check
        """
        cleaned_text, index_map = self.strip_style_markers(
            text,
            italics=False,
            bold=True,
            superscript=True,
            subscript=True,
        )

        if self.collect_taxonomy_names_from_ladder(cleaned_text):
            return []

        violations = []
        seen_matches = set()

        for proper_name in sorted(self._collected_higher_taxonomy_names, key=len, reverse=True):
            for cleaned_span, message, suggested_fix in self.find_taxonomy_name_violations(cleaned_text, proper_name):
                original_span = (
                    index_map[cleaned_span[0]],
                    index_map[cleaned_span[1] - 1] + 1,
                )
                match_key = (original_span, suggested_fix)
                if match_key in seen_matches:
                    continue
                seen_matches.add(match_key)
                violations.append(self.create_violation(
                    section_name=section_name,
                    text=text,
                    span=original_span,
                    message=message,
                    suggested_fix=suggested_fix,
                ))

        suffix_pattern = '|'.join(re.escape(s) for s in self.FAMILY_SUFFIXES)
        pattern = re.compile(
            rf'(?P<markup><(?:i|em)>)?(?P<name>\b([A-Za-z][a-z]+)({suffix_pattern})\b)(?(markup)</(?:i|em)>)',
            re.IGNORECASE,
        )

        for match in pattern.finditer(cleaned_text):
            family_name = match.group('name')
            stem_match = re.match(r'([A-Za-z][a-z]+)(' + suffix_pattern + r')$', family_name, re.IGNORECASE)
            if stem_match is None:
                continue

            stem = stem_match.group(1)
            suffix = stem_match.group(2)
            proper_name = stem.capitalize() + suffix.lower()
            is_known_or_plausible = proper_name in self.KNOWN_FAMILIES or len(stem) >= 4
            if not is_known_or_plausible:
                continue

            is_capitalized = family_name == proper_name
            is_italicized = match.group('markup') is not None

            if is_capitalized and not is_italicized:
                continue

            original_span = (
                index_map[match.start()],
                index_map[match.end() - 1] + 1,
            )
            match_key = (original_span, proper_name)
            if match_key in seen_matches:
                continue
            seen_matches.add(match_key)
            violations.append(self.create_violation(
                section_name=section_name,
                text=text,
                span=original_span,
                message=f"Family/taxonomy names should be capitalized and not italicized: '{proper_name}'",
                suggested_fix=proper_name,
            ))

        return violations

    def check_genus_and_species(self, section_name: str, text: str) -> List[Violation]:
        """Check harvested genus/species names for italics and casing.

        This method strips non-italic inline style tags first:
        ``<b>``, ``<strong>``, ``<sup>``, and ``<sub>``.
        It preserves ``<i>`` / ``<em>`` because italicization is part of the
        rule being checked.

        During a full-report sweep, this method looks for taxonomy-ladder
        entries such as:
        ``PLANTAE - TRACHEOPHYTA - MAGNOLIOPSIDA - FABALES - FABACEAE - Acrocarpus - fraxinifolius``.
        From that ladder, it harvests:
        - the second-to-last segment as the genus
        - the last segment as the species

        The ladder entry itself is not checked for violations by this method.
        Instead, the harvested genus and species are stored temporarily and
        checked against the remaining sections in the same sweep.

        The applied rules are:
        - occurrences of the genus must be italicized
        - occurrences of the species must be italicized
        - the genus must start with a capital letter
        - the species must start with a lowercase letter

        Examples flagged after harvesting ``Acrocarpus`` / ``fraxinifolius``:
        - ``Acrocarpus`` -> suggests ``<i>Acrocarpus</i>``
        - ``acrocarpus`` -> suggests ``<i>Acrocarpus</i>``
        - ``fraxinifolius`` -> suggests ``<i>fraxinifolius</i>``
        - ``Fraxinifolius`` -> suggests ``<i>fraxinifolius</i>``
        - ``<i>Fraxinifolius</i>`` -> suggests ``<i>fraxinifolius</i>``

        Examples not flagged:
        - the taxonomy ladder entry that provided the genus/species names
        - ``<i>Acrocarpus</i>``
        - ``<i>fraxinifolius</i>``
        - names before any taxonomy ladder has been harvested in the current sweep
        """
        cleaned_text, index_map = self.strip_style_markers(
            text,
            italics=False,
            bold=True,
            superscript=True,
            subscript=True,
        )

        if self.collect_taxonomy_names_from_ladder(cleaned_text):
            return []

        violations = []
        name_rules = (
            (self._collected_genus_name, True),
            (self._collected_species_name, False),
        )

        for proper_name, should_be_capitalized in name_rules:
            if not proper_name:
                continue

            name_pattern = re.escape(proper_name).replace(r'\ ', r'\s+')
            pattern = re.compile(
                rf'(?P<markup><(?:i|em)>)?(?P<name>\b{name_pattern}\b)(?(markup)</(?:i|em)>)',
                re.IGNORECASE,
            )

            for match in pattern.finditer(cleaned_text):
                matched_name = match.group('name')
                normalized_name = (
                    proper_name if should_be_capitalized else proper_name.lower()
                )
                is_italicized = (
                    match.group('markup') is not None
                    or self.is_inside_italic(cleaned_text, match.start(), match.end())
                )
                has_expected_case = matched_name == normalized_name

                if is_italicized and has_expected_case:
                    continue

                message = (
                    f"Scientific names should be italicized and use correct case: "
                    f"'<i>{normalized_name}</i>'"
                )
                original_span = (
                    index_map[match.start()],
                    index_map[match.end() - 1] + 1,
                )
                violations.append(self.create_violation(
                    section_name=section_name,
                    text=text,
                    span=original_span,
                    message=message,
                    suggested_fix=f"<i>{normalized_name}</i>",
                ))

        return violations

    def collect_taxonomy_names_from_ladder(self, text: str) -> bool:
        """Harvest higher taxonomy names plus genus/species from a ladder entry."""
        segments = [segment.strip() for segment in text.split(' - ') if segment.strip()]
        if len(segments) < 6:
            return False

        uppercase_segments = [
            segment for segment in segments
            if re.fullmatch(r'[A-Z][A-Z]+', segment)
        ]
        if len(uppercase_segments) < 4:
            return False

        genus_segment = segments[-2]
        species_segment = segments[-1]
        if not re.fullmatch(r'[A-Za-z][A-Za-z-]*', genus_segment):
            return False
        if not re.fullmatch(r'[A-Za-z][A-Za-z-]*', species_segment):
            return False

        for segment in uppercase_segments:
            self._collected_higher_taxonomy_names.add(segment.title())
        self._collected_genus_name = genus_segment.capitalize()
        self._collected_species_name = species_segment.lower()
        return True

    def find_taxonomy_name_violations(self, text: str, proper_name: str) -> List[tuple]:
        """Return violations for a harvested higher-order taxonomy name."""
        violations = []
        name_pattern = re.escape(proper_name).replace(r'\ ', r'\s+')
        pattern = re.compile(
            rf'(?P<markup><(?:i|em)>)?(?P<name>\b{name_pattern}\b)(?(markup)</(?:i|em)>)',
            re.IGNORECASE,
        )

        for match in pattern.finditer(text):
            matched_name = match.group('name')
            is_italicized = match.group('markup') is not None
            if matched_name == proper_name and not is_italicized:
                continue

            violations.append((
                match.span(),
                f"Family/taxonomy names should be capitalized and not italicized: '{proper_name}'",
                proper_name,
            ))

        return violations
    def is_inside_italic(self, text: str, start: int, end: int) -> bool:
        """Check if a position is inside italic tags."""
        before = text[:start]
        after = text[end:]

        open_i = before.rfind('<i>')
        open_em = before.rfind('<em>')
        last_open = max(open_i, open_em)
        if last_open == -1:
            return False

        close_i = before.rfind('</i>')
        close_em = before.rfind('</em>')
        last_close = max(close_i, close_em)

        if last_open > last_close:
            close_after_i = after.find('</i>')
            close_after_em = after.find('</em>')
            if close_after_i != -1 or close_after_em != -1:
                return True

        return False
