import unittest

from unittest.mock import patch, MagicMock
from datetime import datetime
from app.services.smart_service import SmartEventParser
from app.model import parse_model

import sys, types

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

if __name__ == "__main__":
    unittest.main()


# Die Schulung beginnt am 15. April 2026 und endet am 17. April 2026.
# Die täglichen Unterrichtszeiten sind von 09:00 Uhr bis 16:30 Uhr.
# Ort: Seminarzentrum, Musterstadt
# Trainer: Max Mustermann
