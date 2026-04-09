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

    _STOP_WORDS = r'trainer|referent(?:in)?|ort|veranstaltungsort'

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

        # 2. Search by multi dates
        if not events:
            events.extend(self._extract_multi_dates(normalized))

        # 3. Search by single date 
        if not events:
            events.extend(self._extract_single_date(normalized))

        # 4. Extract common information
        self._extract_common_info(events, text)

        # 4. Apply common information to all events

        return events

    def _extract_date_range(self, text) -> list[ParsedEvent]:

        events = []
        # --- „start DD. Monat [Jahr] ende DD. Monat [Jahr]" ---
        pattern_start_end = (
            r'start\s+(?:wäre|ist)?\s*am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?\s*'
            r'und\s+ende\s+(?:wäre|ist)?\s*am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern_start_end, text.lower()):
            start_day, start_month_str, start_year_str, end_day, end_month_str, end_year_str = match.groups()
            try:
                events.append(ParsedEvent(
                    start_date=datetime(
                        int(start_year_str) if start_year_str else self._current_year,
                        self._month_to_number(start_month_str),
                        int(start_day)),
                    end_date=datetime(
                        int(end_year_str) if end_year_str else self._current_year,
                        self._month_to_number(end_month_str),
                        int(end_day)),
                    raw=text[match.start():match.end()],
                ))
            except ValueError:
                pass

        # --- Numerischer Bereich: DD.MM.YYYY - DD.MM.YYYY (auch mit –) ---
        pattern_num_range = (
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
            r'\s*[-–]\s*'
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
        )
        for match in re.finditer(pattern_num_range, text.lower()):
            start_day, start_month_str, start_year_str, end_day, end_month_str, end_year_str = match.groups()
            try:
                events.append(ParsedEvent(
                    start_date=datetime(int(start_year_str), int(start_month_str), int(start_day)),
                    end_date=datetime(int(end_year_str), int(end_month_str), int(end_day)),
                    raw=text[match.start():match.end()],
                ))
            except ValueError:
                pass

        # --- „vom DD. bis/-– DD. Monat [Jahr]" ---
        pattern_vom_bis = (
            r'vom\s+(\d{1,2})\.\s*(?:bis|[-–])\s+'
            r'(\d{1,2})\.\s+'
            r'(' + self._month_re + r')'
            r'(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern_vom_bis, text.lower()):
            start_day, end_day, month_str, year_str = match.groups()
            month = self._month_to_number(month_str)
            year = int(year_str) if year_str else self._current_year
            try:
                events.append(ParsedEvent(
                    start_date=datetime(year, month, int(start_day)),
                    end_date=datetime(year, month, int(end_day)),
                    raw=text[match.start():match.end()],
                ))
            except ValueError:
                pass

        # --- „beginnt am DD. Monat [Jahr] und endet am DD. Monat [Jahr]" ---
        pattern_beginnt_endet = (
            r'beginnt am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?\s*'
            r'und endet am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern_beginnt_endet, text.lower()):
            start_day, start_month_str, start_year_str, end_day, end_month_str, end_year_str = match.groups()
            try:
                events.append(ParsedEvent(
                    start_date=datetime(
                        int(start_year_str) if start_year_str else self._current_year,
                        self._month_to_number(start_month_str),
                        int(start_day)),
                    end_date=datetime(
                        int(end_year_str) if end_year_str else self._current_year,
                        self._month_to_number(end_month_str),
                        int(end_day)),
                    raw=text[match.start():match.end()],
                ))
            except ValueError:
                pass

        return events

    def _extract_multi_dates(self, text) -> list[ParsedEvent]:
        pattern = (
            r'am\s+'
            r'(\d{1,2}\.(?:\s*,\s*\d{1,2}\.)*\s*(?:,?\s*und\s+)?\d{1,2}\.)'
            r'\s+(' + self._month_re + r')'
            r'(?:\s+(\d{4}))?'
        )
        events: list[ParsedEvent] = []
        for match in re.finditer(pattern, text.lower()):
            days_raw, month_str, year_str = match.groups()
            days  = [int(d) for d in re.findall(r'\d{1,2}', days_raw)]
            if len(days) < 2:
                continue
            month = self._month_to_number(month_str)
            year  = int(year_str) if year_str else self._current_year
            for day in days:
                try:
                    date = datetime(year, month, day)
                    events.append(ParsedEvent(
                        start_date=date, end_date=date,
                        raw=match.group(0),
                    ))
                except ValueError:
                    pass
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
        pattern_standard = (
            r'(?:von\s+)?(\d{1,2}:\d{2})\s*(?:uhr)?\s*'
            r'(?:bis|-)\s*(\d{1,2}:\d{2})\s*(?:uhr)?'
        )
        match =re.search(pattern_standard, text.lower())
        if match:
            return(match.group(1), match.group(2))

        pattern_natural = (
            r'(?:gegen\s+)?(\d{1,2}:\d{2})\s*'
            r'(?:anfangen|starten|beginnen|beginn)?\s*(?:und)?\s*'
            r'(?:bis\s+(?:etwa\s+)?)'
            r'(\d{1,2}:\d{2})'
        )
        match = re.search(pattern_natural, text.lower())
        if match:
            return (match.group(1), match.group(2))

        return None

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
        
        for line in text.splitlines():
            line = line.strip()
            match = re.match(r'^(?:betreff|titel)\s*:\s*(.+)$', line, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        pattern = r'^(.*?)(?:beginnt am|vom\s+\d{1,2}|am \d{1,2})'
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            candidate = match.group(1).strip()
            if 3 < len(candidate) < 60:
                return candidate

        return ''

    def _extract_location(self, text):
        text = self._normalize(text)
        text_lower = text.lower()

        # special case
        if "remote" in text_lower:
            return "remote"

        patterns = [
            # spezifisch zuerst
            r'(?i:ort|location)\s*(?:ist|:)?\s*(?:aktuell\s+|derzeit\s+|momentan\s+|noch\s+)?([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)(?:[.,]|$|\s)',

            r'(?i:findet\s+in)\s+([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)(?:\s+(?:statt|geplant|sein)|[.,]|$)',

            r'(?i:\bin)\s+([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)(?:\s+(?:statt|stattfinden|geplant|sein|wird)|[.,]|$)',
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                location = match.group(1).strip()

                location = re.sub(r'\b(statt|stattfinden|geplant|sein|wird)\b.*', '', location, flags=re.IGNORECASE).strip()

                if len(location.split()) <= 4:
                    return location
        return ''

    def _extract_trainer(self, text):
        text = self._normalize(text)
        patterns = [
            r'(?:trainer(?:in)?|referent(?:in)?)\s*(?:ist|wird|:)\s*'
            r'((?:dr\.|prof\.|frau|herr|fräulein)\s*)?'
            r'([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)',

            r'als\s+(?:trainer(?:in)?|referent(?:in)?)\s+ist\s+'
            r'((?:dr\.|prof\.|frau|herr|fräulein)\s*)?'
            r'([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)',

            r'(?:von|leiter(?:in)?)\s*(?:ist|:)?\s*'
            r'((?:dr\.|prof\.|frau|herr|fräulein)\s*)?'
            r'([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)'
            r'(?:\s+geleitet)'
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                title_prefix = (match.group(1) or '').strip()
                name_part = (match.group(2) or '').strip()

                name_part = re.split(r'\s+(?:vorgesehen|geplant|wird|die|der|das|ist|sein)\b', name_part, flags=re.IGNORECASE)[0].strip()
                allowed_titles = {"dr.", "prof.", "herr", "frau"}
                title_clean = title_prefix.lower().strip()

                if title_clean in allowed_titles:
                    full_name = f"{title_clean.title()} {name_part}".strip()
                else:
                    full_name = name_part

                if full_name:
                    return full_name
        return ''

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
