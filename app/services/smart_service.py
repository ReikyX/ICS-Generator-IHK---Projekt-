import re
from datetime import datetime
from app.model.parse_model import ParsedEvent


class SmartEventParser:
    """Parser for natural language (German)"""

    MONTHS_DE = {
        'januar': 1, 'jan': 1,
        'februar': 2,'feb': 2,
        'märz': 3, 'maerz': 3, 'mär': 3,
        'april': 4, 'apr': 4,
        'mai': 5,
        'juni': 6, 'jun': 6,
        'juli': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'oktober': 10, 'okt': 10,
        'november': 11, 'nov': 11,
        'dezember': 12, 'dez': 12,
    }

    _STOP_WORDS = r'trainer|referent|ort|uhrzeit|von|bis|beschreibung'

    def __init__(self) -> None:
        self._current_year = datetime.now().year
        self._month_re = '|'.join(self.MONTHS_DE.keys())

    def _normalize(self, text):
        lines = text.splitlines()
        return " ".join(line.strip() for line in lines if line.strip())

    def parse_smart_text(self, text) -> list[ParsedEvent]:
        """Main method for parsing a natural language"""
        normalized = self._normalize(text)
        events: list[ParsedEvent] = []

        # 1. Search by date range (multi-day)
        events.extend(self._extract_date_range(normalized))

        # 2. Search by single date 
        if not events:
            events.extend(self._extract_single_date(normalized))

        # 3. Extract common information
        self._extract_common_info(events, normalized)

        # 4. Apply common information to all events

        return events

    def _extract_date_range(self, text) -> list[ParsedEvent]:

        # --- „vom DD. bis DD. Monat [Jahr]" ---
        pattern1 = (
            r'vom\s+(\d{1,2})\.\s*bis\s+'
            r'(\d{1,2})\.\s+'
            r'(' + self._month_re + r')'
            r'(?:\s+(\d{4}))?'
        )
        events = []
        for match in re.finditer(pattern1, text.lower()):
            start_date, end_date, month_str, year_str=match.groups()
            month= self._month_to_number(month_str)
            year = int(year_str) if year_str else self._current_year
            events.append(ParsedEvent(
                start_date = datetime(year, month, int(start_date)),
                end_date = datetime(year, month, int(end_date)),
                raw = text[match.start():match.end()],
            ))

        # --- „beginnt am DD. Monat [Jahr] und endet am DD. Monat [Jahr]" ---
        pattern2 = (
            r'beginnt am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?\s*'
            r'und endet am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern2, text.lower()):
            start_day,start_month_str,start_year, end_day, end_month_str, end_year = match.groups()

            start_date = datetime(
                int(start_year) if start_year else self._current_year,
                self._month_to_number(start_month_str),
                int(start_day))
            end_date = datetime(
                int(end_year) if end_year else self._current_year, 
                self._month_to_number(end_month_str), 
                int(end_day))

            if start_date and end_date:
                events.append(ParsedEvent(
                    start_date = start_date,
                    end_date = end_date,
                    raw = text[match.start():match.end()],
                ))

        return events

    def _extract_single_date(self, text) -> list[ParsedEvent]:
        pattern = (
            r'(?:am\s+)?(\d{1,2})\.\s+'
            r'(' + self._month_re + r')'
            r'(?:\s+(\d{4}))?'
        )
        events = []

        for match in re.finditer(pattern, text.lower()):
            day, month_str, year_str = match.groups()
            date = self._make_date(day, month_str, year_str)
            if date:
                events.append(ParsedEvent(
                    start_date = date,
                    end_date = date,
                    raw = text[match.start():match.end()],
                ))

        return events

    def _extract_time_range(self, text) -> tuple[str, str] | None:
        pattern = (
            r'(?:von\s+)?(\d{1,2}:\d{2})\s*(?:uhr)?\s*'
            r'(?:bis|-)\s*(\d{1,2}:\d{2})\s*(?:uhr)?'
        )
        m =re.search(pattern, text.lower())
        return (m.group(1), m.group(2)) if m else None

    def _extract_common_info(self, events: list[ParsedEvent], text):
        title = self._extract_title(text)
        time_range = self._extract_time_range(text)
        location = self._extract_location(text)
        trainer = self._extract_trainer(text)

        for event in events:
            if title:
                event.title = title
            if time_range:
                event.start_time, event.end_time = time_range
            if location:
                event.location = location
            if trainer:
                event.trainer = trainer

    def _extract_title(self, text):
        pattern_label = r'(?:schulung|seminar|kurs|veranstaltung|betreff|titel)\s*:\s*(.+?)(?:\.|$)'

        m = re.search(pattern_label, text.lower())
        if m:
            return m.group(1).strip().title()

        pattern_befor = r'^(.+?)\s+(?:beginnt am|vom\s+\d)'
        m = re.search(pattern_befor, text.lower())
        if m:
            candidate = m.group(1).strip()

            if 4 < len(candidate) < 60:
                return candidate.title()

        return ''

    def _extract_location(self, text):
        pattern = r'ort\s*:\s*(.+?)(?:\.|' + self._STOP_WORDS + r'|)'
        m = re.search(pattern, text.lower())
        return m.group(1).strip().title() if m else ''

    def _extract_trainer(self, text):
        m = re.search(r'(?:trainer|referent)\s*:\s*(.+?)(?:\.|$)', text.lower())
        return m.group(1).strip().title() if m else ''

    def _make_date(self, day: str, month_str: str, year_str: str | None) -> datetime | None:
        try:
            return datetime(
                int(year_str) if year_str else self._current_year,
                self._month_to_number(month_str), int(day))
        except ValueError:
            return None

    def _month_to_number(self, month_name):
        month_name = month_name.lower().strip('.').strip()

        if month_name.isdigit():
            return int(month_name)

        if month_name in self.MONTHS_DE:
            return self.MONTHS_DE[month_name]

        return datetime.now().month

def parse_smart_text_to_event(text):
    pass
