import unittest

from unittest.mock import patch, MagicMock
from datetime import datetime
from app.services.smart_service import SmartEventParser
from app.model import parse_model

import sys
import types


class TestNormalize(unittest.TestCase):

    def setUp(self):
        self.parser = SmartEventParser()

    def test_single_line_unchanged(self):
        self.assertEqual(self.parser._normalize(
            "Hallo Herr Mustermann"), "Hallo Herr Mustermann")

    def test_multiline_joined(self):
        self.assertEqual(self.parser._normalize(
            "Die Schulung beginnt am 15. April 2026 und endet am 17. April 2026.\nDie täglichen Unterrichtszeiten sind von 09:00 Uhr bis 16:30 Uhr.\nOrt: Seminarzentrum, Musterstadt\nOrt: Seminarzentrum, Musterstadt\nTrainer: Max Mustermann"), "Die Schulung beginnt am 15. April 2026 und endet am 17. April 2026. Die täglichen Unterrichtszeiten sind von 09:00 Uhr bis 16:30 Uhr. Ort: Seminarzentrum, Musterstadt Ort: Seminarzentrum, Musterstadt Trainer: Max Mustermann")

    def test_blank_lines_ignored(self):
        self.assertEqual(self.parser._normalize(
            "Die Schulung beginnt am 15. April 2026 und endet am 17. April 2026.\n\n\nDie täglichen Unterrichtszeiten sind von 09:00 Uhr bis 16:30 Uhr.\n\n\nOrt: Seminarzentrum, Musterstadt\n\n\nOrt: Seminarzentrum, Musterstadt\n\n\nTrainer: Max Mustermann"), "Die Schulung beginnt am 15. April 2026 und endet am 17. April 2026. Die täglichen Unterrichtszeiten sind von 09:00 Uhr bis 16:30 Uhr. Ort: Seminarzentrum, Musterstadt Ort: Seminarzentrum, Musterstadt Trainer: Max Mustermann")

    def test_whitespace_trimmed(self):
        self.assertEqual(self.parser._normalize(
            "Hallo   \n   Herr   \n   Mustermann"), "Hallo Herr Mustermann")

    def test_empty_string(self):
        self.assertEqual(self.parser._normalize(""), "")

    def test_only_whitespace(self):
        self.assertEqual(self.parser._normalize("      \n      "), "")


class TestMonthToNumber(unittest.TestCase):

    def setUp(self):
        self.parser = SmartEventParser()

    def test_full_names(self):
        cases = {
            "januar": 1, "februar": 2, "märz": 3, "april": 4, "mai": 5, "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(self.parser._month_to_number(name), expected)

    def test_abbreviations(self):
        self.assertEqual(self.parser._month_to_number("jan"), 1)
        self.assertEqual(self.parser._month_to_number("feb"), 2)
        self.assertEqual(self.parser._month_to_number("dez"), 12)

    def test_uppercase_input(self):
        self.assertEqual(self.parser._month_to_number("MÄRZ"), 3)
        self.assertEqual(self.parser._month_to_number("APRIL"), 4)

    def test_digit_string(self):
        self.assertEqual(self.parser._month_to_number("7"), 7)
        self.assertEqual(self.parser._month_to_number("8"), 8)

    def test_maerz_alternative_spelling(self):
        self.assertEqual(self.parser._month_to_number("maerz"), 3)

class TestExtractTimeRange(unittest.TestCase):

    def setUp(self):
        self.parser = SmartEventParser()

    def test_basic_range(self):
        self.assertEqual(
            self.parser._extract_time_range("von 09:00 bis 17:00 Uhr"), ("09:00", "17:00"))

    def test_range_with_dash(self):
        self.assertEqual(
            self.parser._extract_time_range("Uhrzeit: 08:30 - 16:00"), ("08:30", "16:00"))

    def test_no_time_returns_none(self):
        self.assertIsNone(self.parser._extract_time_range("Kein Datum hier!"))

    def test_time_without_uhr_keyword(self):
        self.assertEqual(self.parser._extract_time_range("10:00 bis 12:00"), ("10:00", "12:00"))

class TestExtractLocation(unittest.TestCase):

    def setUp(self):
        self.parser = SmartEventParser()

    def test_basic_location(self):
        self.assertEqual(
            self.parser._extract_location("Ort: Berlin. Weitere Infos folgen."), "Berlin")

    def test_location_with_city_name(self):
        self.assertEqual(
            self.parser._extract_location("Schulung in München. Ort: Konferenzraum A."),
            "Konferenzraum A")

    def test_no_location_returns_empty(self):
        self.assertEqual(self.parser._extract_location("Kein Ort angegeben"), "")

    def test_location_titlecase(self):
        self.assertEqual(self.parser._extract_location("ort: frankfurt am main."),
                         "Frankfurt Am Main")

class TestExtractTrainer(unittest.TestCase):

    def setUp(self):
        self.parser = SmartEventParser()

    def test_trainer_keyword(self):
        self.assertEqual(
            self.parser._extract_trainer("Trainer: Max Mustermann."),
            "Max Mustermann")

    def test_referent_keyword_without_title(self):
        self.assertEqual(
            self.parser._extract_trainer("Referent: Anna Schmidt"),
            "Anna Schmidt")

    def test_referent_with_title_bug(self):
        self.assertEqual(
            self.parser._extract_trainer("Referent: Dr. Anna Schmidt."),
              "Dr. Anna Schmidt")

    def test_no_trainer_returns_empty(self):
        self.assertEqual(
            self.parser._extract_trainer("Keine Angabe zum Referenten"), "")

    def test_trainer_titlecase(self):
        self.assertEqual(
            self.parser._extract_trainer("trainer: thomas müller."),
            "Thomas Müller")

if __name__ == "__main__":
    unittest.main()


# Die Schulung beginnt am 15. April 2026 und endet am 17. April 2026.
# Die täglichen Unterrichtszeiten sind von 09:00 Uhr bis 16:30 Uhr.
# Ort: Seminarzentrum, Musterstadt
# Trainer: Max Mustermann
