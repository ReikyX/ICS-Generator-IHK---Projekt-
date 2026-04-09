import unittest
from datetime import datetime
from app.services.smart_service import SmartEventParser

class TestParseSmartText(unittest.TestCase):
    case1_single_date = """Betreff: KI-Schulung im März

Hallo zusammen,

wir wollen im März eine Einführung in das Thema KI machen, da ja immer mehr Anfragen dazu kommen.
Geplant ist aktuell der 5. März 2026, so ungefähr von 09:00 bis 17:00 Uhr.

Das Ganze soll in München stattfinden, als Trainer ist Jörg Müller vorgesehen.

Gebt bitte kurz Bescheid, ob das für euch passt.

Viele Grüße"""
    case2_with_location = """Betreff: Workshop Planung April

Hi,

ich wollte schon mal den nächsten Workshop ankündigen. Es geht um agiles Arbeiten, Termin wäre der 12. April, vermutlich so von 10:00 bis 15:00.

Ort ist aktuell Frankfurt, Raum klären wir noch final.

Wenn jemand Themenwünsche hat, gerne melden 🙂"""
    case3_multiple_dates_same_event = """Betreff: Python Seminar Termine

Hallo,

für das Python Basics Seminar haben wir aktuell zwei mögliche Termine eingeplant, und zwar den 10. Mai 2026 sowie den 12. Mai 2026.

Die Uhrzeit wäre jeweils von 10:00 bis 15:00 Uhr, damit es für alle gut machbar ist.
Als Referent ist Max Mustermann vorgesehen.

Bitte gebt mir Rückmeldung, welcher Termin euch besser passt.

Danke!"""
    case4_date_range_with_time = """Betreff: Data Science Kurs (mehrtägig)

Hallo zusammen,

wir planen aktuell einen Data Science Kurs, der sich über mehrere Tage erstrecken soll.
Start wäre am 1. Juni 2026 und Ende am 3. Juni.

Täglich würden wir so gegen 09:30 anfangen und bis etwa 16:30 machen.
Ort ist Berlin.

Weitere Details folgen noch."""
    case5_text_with_date_range_natural_language = """Betreff: DevOps Training Infos

Hi zusammen,

anbei schon mal die Infos zum DevOps Training:
Das Training beginnt am 7. Juli und endet am 9. Juli, also insgesamt drei Tage.

Es findet in Berlin statt und richtet sich eher an Fortgeschrittene, wird also recht intensiv.

Wenn ihr teilnehmen wollt, gebt bitte kurz Bescheid."""
    case6_single_date_short_text = """Betreff: kurzer Termin im August

Hallo,

nur kurz zur Info: wir haben am 2. August noch einen kleinen Kurs eingeplant, aktuell von 08:30 bis 12:30.

Mehr Details habe ich gerade leider nicht, reiche ich aber nach.

VG"""
    case7_uppercase_and_umlauts = """Betreff: WICHTIGES Update zum Cloud-Seminar

Hallo zusammen,

wir haben nun ENDLICH einen Termin für das Cloud-Seminar gefunden:
Es findet am 15. September 2026 in München statt.

Unsere Trainerin ist FRÄULEIN Anna Schmitt, die Expertise in Cloud-Computing, KI-Tools und Ökosysteme mitbringt.

Agenda und weitere Infos schicke ich separat rum. Bitte meldet Euch frühzeitig zurück.

Vielen Dank und bis bald,
Euer Team"""
    case8_invalid_date_should_fail = """Betreff: Termin (unsicher)

Hi,

ich habe hier noch eine etwas komische Angabe bekommen: angeblich soll ein Event am 32. Januar stattfinden, was ja offensichtlich nicht stimmen kann.

Ort wäre Köln gewesen, aber ich kläre das nochmal.

Ich melde mich, sobald ich korrekte Infos habe."""
    case9_multiple_events_in_text = """Betreff: mehrere Workshops im Oktober

Hallo,

im Oktober stehen gleich zwei Veranstaltungen an.
Zum einen ein Scrum Kurs am 3. Oktober, geplant von 09:00 bis 13:00 Uhr.

Zusätzlich gibt es noch einen Kanban Workshop am 5. Oktober, der eher ganztägig ist, aktuell 10:00 bis 16:00.

Beides wird remote stattfinden.

Gebt bitte Bescheid, wer woran teilnehmen möchte."""
    case10_date_range_with_missing_location = """Betreff: Führungskräfte Training

Hallo Team,

bitte merkt euch schon mal das Führungskräfte-Training vor.
Das Ganze ist aktuell vom 20. bis 22. November 2026 geplant.

Uhrzeiten werden wahrscheinlich jeweils so gegen 9:00 bis 17:00 liegen.
Trainer wird Dr. Weber sein.

Beim Ort sind wir noch nicht final, das reiche ich nach.

Danke euch!"""
    case11_no_reference = """Hallo,

wir haben nächste Woche eine Schulung geplant, genauer gesagt am 8. April 2026 von 09:00 bis 16:00 Uhr.
Das Ganze findet in Stuttgart statt, Trainer ist Michael Braun."""
    case12_no_date = """Betreff: Workshop ohne Datum

Hi,

wir wollen einen Workshop zum Thema Kommunikation machen, wahrscheinlich von 10:00 bis 15:00 Uhr.
Ort wäre Berlin und als Trainerin ist Frau Keller vorgesehen.

Den genauen Termin liefere ich noch nach."""
    case13_no_time = """Betreff: Scrum Training

Hallo zusammen,

das Scrum Training ist für den 14. Juni 2026 geplant.
Es wird in Hamburg stattfinden und von Thomas Richter geleitet.

Uhrzeit steht noch nicht fest."""
    case14_no_location = """Betreff: DevOps Kurs

Hi,

wir haben einen DevOps Kurs am 3. Juli 2026 von 09:00 bis 17:00 Uhr eingeplant.
Trainer ist Stefan Koch.

Ort klären wir noch."""
    case15_no_trainer = """Betreff: Data Analytics

Hallo,

der Data Analytics Workshop findet am 21. August 2026 statt, von 10:00 bis 16:00 Uhr in München.

Wer den Workshop leitet, ist noch offen."""
    case16_no_title = """Betreff: Termin Info

Hallo,

am 11. September 2026 haben wir von 09:30 bis 15:30 Uhr eine Veranstaltung in Köln.
Trainer ist Julia Meier.

Details folgen."""
    case17_no_date_range = """Betreff: Mehrtägige Schulung

Hi,

die Schulung beginnt am 5. Oktober 2026 und geht über mehrere Tage, genaues Enddatum ist noch unklar.
Geplant ist täglich von 09:00 bis 17:00 Uhr in Berlin.

Trainer: Markus Weber"""
    case18_no_time_and_trainer = """Betreff: UX Workshop

Hallo zusammen,

der UX Workshop ist aktuell für den 18. November 2026 in Frankfurt geplant.

Weitere Infos folgen noch."""
    case19_no_date_and_trainer = """Betreff: kurzer Slot

Hi,

wir haben noch einen Termin von 13:00 bis 15:00 Uhr für ein internes Training reserviert.
Ort ist remote.

Datum fehlt mir gerade, kommt noch."""
    case20_no_declaration = """Betreff: Re: irgendwas mit Schulung

Hallo,

wegen der Sache von letzter Woche: das Training soll wohl im Dezember stattfinden, vermutlich in Berlin.

Mehr habe ich aktuell leider auch nicht."""
    def setUp(self):
        self.parser = SmartEventParser()

    def test_parse_smart_text(self):
        test_cases = [
            (self.case1_single_date, 1),
            (self.case2_with_location, 1),
            (self.case3_multiple_dates_same_event, 2),
            (self.case4_date_range_with_time, 1),
            (self.case5_text_with_date_range_natural_language, 1),
            (self.case6_single_date_short_text, 1),
            (self.case7_uppercase_and_umlauts, 1),
            (self.case8_invalid_date_should_fail, 0),
            (self.case9_multiple_events_in_text, 2),
            (self.case10_date_range_with_missing_location, 1),
            (self.case11_no_reference, 1),
            (self.case12_no_date, 0),
            (self.case13_no_time, 1),
            (self.case14_no_location, 1),
            (self.case15_no_trainer, 1),
            (self.case16_no_title, 1),
            (self.case17_no_date_range, 1),
            (self.case18_no_time_and_trainer, 1),
            (self.case19_no_date_and_trainer, 0),
            (self.case20_no_declaration, 0),
        ]
        for text, expected_count in test_cases:
            with self.subTest(text=text):
                events = self.parser.parse_smart_text(text)
                self.assertEqual(len(events), expected_count)

class TestSingleDateCase1(unittest.TestCase):
    def setUp(self):
        self.parser = SmartEventParser()

    def test_single_date(self):
        case1_single_date = """Betreff: KI-Schulung im März

Hallo zusammen,

wir wollen im März eine Einführung in das Thema KI machen, da ja immer mehr Anfragen dazu kommen.
Geplant ist aktuell der 5. März 2026, so ungefähr von 09:00 bis 17:00 Uhr.

Das Ganze soll in München stattfinden, als Trainer ist Jörg Müller vorgesehen.

Gebt bitte kurz Bescheid, ob das für euch passt.

Viele Grüße"""
        events = self.parser.parse_smart_text(case1_single_date)
        self.assertEqual(events[0].title, "KI-Schulung im März")
        self.assertEqual(events[0].start_date, datetime(2026, 3, 5))
        self.assertEqual(events[0].end_date, datetime(2026, 3, 5))
        self.assertEqual(events[0].start_time, "09:00")
        self.assertEqual(events[0].end_time, "17:00")
        self.assertEqual(events[0].location, "München")
        self.assertEqual(events[0].trainer, "Jörg Müller")

class TestSingleDateCase2(unittest.TestCase):
    def setUp(self):
        self.parser = SmartEventParser()

    def test_single_date(self):
        case2_with_location = """Betreff: Workshop Planung April

Hi,

ich wollte schon mal den nächsten Workshop ankündigen. Es geht um agiles Arbeiten, Termin wäre der 12. April, vermutlich so von 10:00 bis 15:00.

Ort ist aktuell Frankfurt, Raum klären wir noch final.

Wenn jemand Themenwünsche hat, gerne melden 🙂"""
        events = self.parser.parse_smart_text(case2_with_location)
        self.assertEqual(events[0].title, "Workshop Planung April")
        self.assertEqual(events[0].start_date, datetime(2026, 4, 12))
        self.assertEqual(events[0].end_date, datetime(2026, 4, 12))
        self.assertEqual(events[0].start_time, "10:00")
        self.assertEqual(events[0].end_time, "15:00")
        self.assertEqual(events[0].trainer, "")
        self.assertEqual(events[0].location, "Frankfurt")

class MultipleDatesCase3(unittest.TestCase):

    def setUp(self):
        self.parser = SmartEventParser()

    def test_multi_dates(self):
        case3_multiple_dates_same_event = """Betreff: Python Seminar Termine

Hallo,

für das Python Basics Seminar haben wir aktuell zwei mögliche Termine eingeplant, und zwar den 10. Mai 2026 sowie den 12. Mai 2026.

Die Uhrzeit wäre jeweils von 10:00 bis 15:00 Uhr, damit es für alle gut machbar ist.
Als Referent ist Max Mustermann vorgesehen.

Bitte gebt mir Rückmeldung, welcher Termin euch besser passt.

Danke!"""
        events = self.parser.parse_smart_text(case3_multiple_dates_same_event)
        self.assertEqual(events[0].title, "Python Seminar Termine")
        self.assertEqual(events[0].start_date, datetime(2026, 5, 10))
        self.assertEqual(events[0].start_time, "10:00")
        self.assertEqual(events[1].start_date, datetime(2026, 5, 12))
        self.assertEqual(events[1].start_time, "10:00")
        self.assertEqual(events[0].end_time, "15:00")
        self.assertEqual(events[0].trainer, "Max Mustermann")
        self.assertEqual(events[0].location, "")

class TestDateRangeCase4(unittest.TestCase):

    def setUp(self):
        self.parser = SmartEventParser()

    def test_date_range(self):
        case4_date_range_with_time = """Betreff: Data Science Kurs (mehrtägig)

Hallo zusammen,

wir planen aktuell einen Data Science Kurs, der sich über mehrere Tage erstrecken soll.
Start wäre am 1. Juni 2026 und Ende am 3. Juni.

Täglich würden wir so gegen 09:30 anfangen und bis etwa 16:30 machen.
Ort ist Berlin.

Weitere Details folgen noch."""

        events = self.parser.parse_smart_text(case4_date_range_with_time)
        self.assertEqual(
            events[0].title, "Data Science Kurs (mehrtägig)")
        self.assertEqual(events[0].start_date, datetime(2026, 6, 1))
        self.assertEqual(events[0].end_date, datetime(2026, 6, 3))
        self.assertEqual(events[0].start_time, "09:30")
        self.assertEqual(events[0].end_time, "16:30")
        self.assertEqual(events[0].trainer, "")
        self.assertEqual(events[0].location, "Berlin")

class TestDateRangeCase5(unittest.TestCase):

    def setUp(self):
        self.parser = SmartEventParser()

    def test_date_range_natural_language(self):
        case5_text_with_date_range_natural_language = """Betreff: DevOps Training Infos

Hi zusammen,

anbei schon mal die Infos zum DevOps Training:
Das Training beginnt am 7. Juli und endet am 9. Juli, also insgesamt drei Tage.

Es findet in Berlin statt und richtet sich eher an Fortgeschrittene, wird also recht intensiv.

Wenn ihr teilnehmen wollt, gebt bitte kurz Bescheid."""

        events = self.parser.parse_smart_text(case5_text_with_date_range_natural_language)
        self.assertEqual(
            events[0].title, "DevOps Training Infos")
        self.assertEqual(events[0].start_date, datetime(2026, 7, 7))
        self.assertEqual(events[0].end_date, datetime(2026, 7, 9))
        self.assertEqual(events[0].start_time, "")
        self.assertEqual(events[0].end_time, "")
        self.assertEqual(events[0].trainer, "")
        self.assertEqual(events[0].location, "Berlin")

class SingleDateCase6(unittest.TestCase):

    def setUp(self):
        self.parser = SmartEventParser()

    def test_single_date_short(self):
        case6_single_date_short_text = """Betreff: kurzer Termin im August

Hallo,

nur kurz zur Info: wir haben am 2. August noch einen kleinen Kurs eingeplant, aktuell von 08:30 bis 12:30.

Mehr Details habe ich gerade leider nicht, reiche ich aber nach.

VG"""

        events = self.parser.parse_smart_text(
            case6_single_date_short_text)
        self.assertEqual(
            events[0].title, "kurzer Termin im August")
        self.assertEqual(events[0].start_date, datetime(2026, 8, 2))
        self.assertEqual(events[0].end_date, datetime(2026, 8, 2))
        self.assertEqual(events[0].start_time, "08:30")
        self.assertEqual(events[0].end_time, "12:30")
        self.assertEqual(events[0].trainer, "")
        self.assertEqual(events[0].location, "")

class SingleDateCase7(unittest.TestCase):

    def setUp(self):
        self.parser = SmartEventParser()

    def test_single_date_uppercase_and_umlauts(self):
        case7_uppercase_and_umlauts = """Betreff: WICHTIGES Update zum Cloud-Seminar

Hallo zusammen,

wir haben nun ENDLICH einen Termin für das Cloud-Seminar gefunden:
Es findet am 15. September 2026 in München statt.

Unsere Trainerin ist FRÄULEIN Anna Schmitt, die Expertise in Cloud-Computing, KI-Tools und Ökosysteme mitbringt.

Agenda und weitere Infos schicke ich separat rum. Bitte meldet Euch frühzeitig zurück.

Vielen Dank und bis bald,
Euer Team"""

        events = self.parser.parse_smart_text(
            case7_uppercase_and_umlauts)
        self.assertEqual(
            events[0].title, "WICHTIGES Update zum Cloud-Seminar")
        self.assertEqual(events[0].start_date, datetime(2026, 9, 15))
        self.assertEqual(events[0].end_date, datetime(2026, 9, 15))
        self.assertEqual(events[0].start_time, "")
        self.assertEqual(events[0].end_time, "")
        self.assertEqual(events[0].trainer, "Anna Schmitt")
        self.assertEqual(events[0].location, "München")

if __name__ == "__main__":
    unittest.main()