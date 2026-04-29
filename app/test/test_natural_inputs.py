import unittest
from datetime import datetime, timedelta
from app.services.smart_service import SmartEventParser


class BaseParserTest(unittest.TestCase):
    """Gemeinsame Basis — setUp nur einmal."""

    def setUp(self) -> None:
        self.parser = SmartEventParser()


class TestRelativeWeekdayWithContext(BaseParserTest):

    def test_next_tuesday_with_time_trainer_location(self):
        text = """Betreff: Training am Dienstag

Hallo zusammen,
kurze Info zum Termin am kommenden Dienstag: Das Training findet um 18:30 Uhr in der Sporthalle Nord statt.
Trainer ist wie besprochen Herr Krüger.

Bitte 10 Minuten vorher da sein, damit wir pünktlich starten können.
Viele Grüße
Sven"""
        events = self.parser.parse_smart_text(text)

        self.assertEqual(len(events), 1)
        event = events[0]

        # Datum
        today = datetime.now()
        days_ahead = (1 - today.weekday() + 7) % 7 or 7
        expected_date = (today + timedelta(days=days_ahead)).replace(
            hour=0, minute=0, second=0, microsecond=0)

        self.assertEqual(event.title, "Training am Dienstag")
        self.assertEqual(event.start_date, expected_date)
        self.assertEqual(event.end_date, expected_date)
        self.assertEqual(event.start_time, "18:30")
        self.assertEqual(event.end_time, "")
        self.assertEqual(event.trainer, "Herr Krüger")
        self.assertEqual(event.location, "Sporthalle Nord")


class TestSeminarSeriesWithModules(BaseParserTest):

    TEXT = """Subject: Terminvorschläge für unsere Seminarreihe

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

    EXPECTED = [
        (datetime(2026, 5, 12), "Modul 1"),
        (datetime(2026, 5, 26), "Modul 2"),
        (datetime(2026, 6,  9), "Modul 3"),
        (datetime(2026, 6, 23), "Modul 4"),
        (datetime(2026, 7,  7), "Modul 5"),
    ]

    def test_event_count(self):
        events = self.parser.parse_smart_text(self.TEXT)
        self.assertEqual(len(events), 5)

    def test_dates_and_descriptions(self):
        events = self.parser.parse_smart_text(self.TEXT)
        for i, (exp_date, exp_desc) in enumerate(self.EXPECTED):
            with self.subTest(modul=exp_desc):
                self.assertEqual(events[i].start_date, exp_date)
                self.assertEqual(events[i].end_date, exp_date)
                self.assertEqual(events[i].description, exp_desc)  # ← neu

    def test_shared_metadata(self):
        events = self.parser.parse_smart_text(self.TEXT)
        for event in events:
            with self.subTest(date=event.start_date):
                self.assertEqual(
                    event.title, "Terminvorschläge für unsere Seminarreihe")
                self.assertEqual(event.start_time, "")
                self.assertEqual(event.end_time, "")
                self.assertEqual(event.trainer, "")
                self.assertEqual(event.location, "München")


class TestCrossMonthRanges(BaseParserTest):

    TEXT = """Titel: Data Science Foundation (Conti)?:

30.9. - 2.10.2026 (3 Tage)
 7. - 9.10.2025 (3 Tage)
 29. - 30.10.2026 (2 Tage)
 9. - 11.11.2026 (3 Tage)
 16. - 18.11.2026 (3 Tage)
 3. - 4.12.2026 (2 Tage)
 10. - 11.12.2026 (2 Tage)"""

    EXPECTED = [
        (datetime(2026,  9, 30), datetime(2026, 10,  2)),  # Cross-Month
        (datetime(2025, 10,  7), datetime(2025, 10,  9)),  # anderes Jahr
        (datetime(2026, 10, 29), datetime(2026, 10, 30)),
        (datetime(2026, 11,  9), datetime(2026, 11, 11)),
        (datetime(2026, 11, 16), datetime(2026, 11, 18)),
        (datetime(2026, 12,  3), datetime(2026, 12,  4)),
        (datetime(2026, 12, 10), datetime(2026, 12, 11)),
    ]

    def test_event_count(self):
        events = self.parser.parse_smart_text(self.TEXT)
        self.assertEqual(len(events), 7)

    def test_date_ranges(self):
        events = self.parser.parse_smart_text(self.TEXT)
        for i, (exp_start, exp_end) in enumerate(self.EXPECTED):
            with self.subTest(i=i, exp_start=exp_start):
                self.assertEqual(events[i].start_date, exp_start)
                self.assertEqual(events[i].end_date, exp_end)

    def test_title_from_titel_prefix(self):
        events = self.parser.parse_smart_text(self.TEXT)
        for event in events:
            self.assertEqual(event.title, "Data Science Foundation (Conti)?")

    def test_custom_title_overrides(self):
        events = self.parser.parse_smart_text(
            self.TEXT, custom_title="Mein Titel")
        self.assertEqual(events[0].title, "Mein Titel")

    # Isolierte Pattern-Tests
    def test_cross_month_pattern_isolated(self):
        events = self.parser.parse_smart_text("30.9. - 2.10.2026")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].start_date, datetime(2026, 9, 30))
        self.assertEqual(events[0].end_date,   datetime(2026, 10, 2))

    def test_same_month_pattern_isolated(self):
        events = self.parser.parse_smart_text("7. - 9.10.2025")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].start_date, datetime(2025, 10, 7))
        self.assertEqual(events[0].end_date,   datetime(2025, 10, 9))


if __name__ == '__main__':
    unittest.main()
