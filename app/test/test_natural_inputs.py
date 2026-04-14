import unittest
from datetime import datetime, timedelta
from app.services.smart_service import SmartEventParser

class TestNaturalInputs(unittest.TestCase):

    def setUp(self) -> None:
        self.parser = SmartEventParser()

    def test_parse_natural_input(self):
        case_1 = """Betreff: Training am Dienstag

Hallo zusammen,
kurze Info zum Termin am kommenden Dienstag: Das Training findet um 18:30 Uhr in der Sporthalle Nord statt.
Trainer ist wie besprochen Herr Krüger.

Bitte 10 Minuten vorher da sein, damit wir pünktlich starten können.
Viele Grüße
Sven"""
        events = self.parser.parse_smart_text(case_1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].title, "Training am Dienstag")
        today = datetime.now()
        days_ahead = (1 - today.weekday() + 7) % 7 or 7
        expected = (today + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.assertEqual(events[0].start_date, expected)
        self.assertEqual(events[0].end_date, expected)
        self.assertEqual(events[0].start_time, "18:30")
        self.assertEqual(events[0].end_time, "")
        self.assertEqual(events[0].trainer, "Herr Krüger")
        self.assertEqual(events[0].location, "Sporthalle Nord")


if __name__ == '__main__':
    unittest.main()