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


class TestNaturalInputsMultiple(unittest.TestCase):

    def setUp(self) -> None:
        self.parser = SmartEventParser()

    def test_parse_multiple_events(self):
        case_2 = """Subject: Terminvorschläge für unsere Seminarreihe

Guten Tag Herr Bellmann,

vielen Dank für Ihr Angebot. Wir würden gerne mit der Seminarreihe starten und haben intern folgende Wunscht termine abgestimmt:

- Modul 1: Dienstag, 12. Mai 2026
- Modul 2: Dienstag, 26. Mai 2026
- Modul 3: Dienstag, 9. Juni 2026
- Modul 4: Dienstag, 23. Juni 2026
- Modul 5: Dienstag, 7. Juli 2026

Wir würden die Seminare gerne in unserem Haus in München durchführen. Bitte bestätigen Sie uns, ob diese Termine für Sie realisierbar sind, oder ob es Engpässe gibt.

Für Rückfragen stehe ich jederzeit zur Verfügung.

Mit freundlichen Grüßen
Sandra Hoffmann
Personalentwicklung
Mustermann AG
+49 89 987654-32"""
        events = self.parser.parse_smart_text(case_2)
        self.assertEqual(len(events), 5)
        expected_dates = [
            datetime(2026, 5, 12),
            datetime(2026, 5, 26),
            datetime(2026, 6, 9),
            datetime(2026, 6, 23),
            datetime(2026, 7, 7)
        ]
        for i in range(5):
            self.assertEqual(events[i].title, "Terminvorschläge für unsere Seminarreihe")
            self.assertEqual(events[i].start_date, expected_dates[i])
            self.assertEqual(events[i].end_date, expected_dates[i])
            self.assertEqual(events[i].start_time, "")
            self.assertEqual(events[i].end_time, "")
            self.assertEqual(events[i].trainer, "")
            self.assertEqual(events[i].location, "München")

if __name__ == '__main__':
    unittest.main()