import re
from datetime import datetime, timedelta
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
    WEEKDAYS_DE = {
        'montag': 0,
        'dienstag': 1,
        'mittwoch': 2,
        'donnerstag': 3,
        'freitag': 4,
        'samstag': 5,
        'sonntag': 6,
    }

    _STOP_WORDS = r'trainer(?:in)|referent(?:in)?|ort|veranstaltungsort'

    def __init__(self) -> None:
        self._current_year = datetime.now().year
        self._month_re = '|'.join(self.MONTHS_DE.keys())

    def _normalize(self, text):
        lines = text.splitlines()
        return " ".join(line.strip() for line in lines if line.strip())

    def _normalize_time(self, h, m):
        h = int(h)
        m = int(m) if m else 0
        return f"{h:02d}:{m:02d}"
    
    def _resolve_relative_weekday(self, weekday_name:str, modifier:str = '') -> datetime | None:
        weekday_name = weekday_name.lower().strip()
        if weekday_name not in self.WEEKDAYS_DE:
            return None
        
        target = self.WEEKDAYS_DE[weekday_name]
        today = datetime.now()
        days_ahead = target - today.weekday()

        next_modifier = {'kommenden', 'kommende', 'nächsten', 'nächste', 'nächster'}
        this_modifier = {'diesen', 'diesem', 'dieser', 'heutigen', 'heute'}

        if modifier.lower() in next_modifier:
            if days_ahead <= 0:
                days_ahead += 7
        elif modifier.lower() in this_modifier:
            if days_ahead < 0:
                days_ahead += 7
        else:
            if days_ahead <= 0:
                days_ahead += 7
        return (today + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)

    def _deduplicate_events(self, events):
        unique = []
        seen = set()
        for e in events:
                key = (e.start_date, e.end_date)
                if key not in seen:
                    seen.add(key)
                    unique.append(e)

        return unique

    def parse_smart_text(self, text, custom_title="") -> list[ParsedEvent]:
        """Main method for parsing a natural language"""
        normalized = self._normalize(text)
        events: list[ParsedEvent] = []

        # 1. Search by date range (multi-day)
        events.extend(self._extract_date_range(normalized))

        if not events:
            events.extend(self._extract_dated_weekday(normalized))

        # 2. Search by multi dates
        if not events:
            events.extend(self._extract_multi_dates(normalized))

        # 3. Search by relative weekday
        if not events:
            events.extend(self._extract_relative_weekday(normalized))

        # 4. Search by single date
        if not events:
            events.extend(self._extract_single_date(normalized))

        # 5. Extract common information
        global_title = custom_title if custom_title else self._extract_title(text)
        events.sort(key=lambda e: e.span[0] if e.span else 0)
        for event in events:
            event.title = global_title
            event.description = self._extract_event_description(normalized, event.span[0]) if event.span else ''
        self._assign_event_context(events, normalized)

        events = self._deduplicate_events(events)
        return events

    def _extract_dated_weekday(self, text) -> list[ParsedEvent]:
        weekday_re = '|'.join(self.WEEKDAYS_DE.keys())
        pattern = (
            r'\b(?:' + weekday_re + r')\s*,\s*'
            r'(\d{1,2})\.?\s*'
            r'(' + self._month_re + r')'
            r'(?:\s+(\d{4}))?'
        )
        events = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            day, month_str, year_str = match.groups()
            date = self._make_date(day, month_str, year_str)
            if date:
                event = ParsedEvent(start_date=date, end_date=date, raw=match.group(0))
                event.span = (match.start(), match.end())
                events.append(event)
        return events

    def _extract_date_range(self, text) -> list[ParsedEvent]:
        events = []
        # --- „start DD. Monat [Jahr] ende DD. Monat [Jahr]" ---
        pattern_start_end = (
            r'start\s+(?:wäre|ist)?\s*am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?\s*'
            r'und\s+ende\s+(?:wäre|ist)?\s*am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern_start_end, text, re.IGNORECASE):
            start_day, start_month_str, start_year_str, end_day, end_month_str, end_year_str = match.groups()
            try:
                event = ParsedEvent(
                    start_date=datetime(
                        int(start_year_str) if start_year_str else self._current_year,
                        self._month_to_number(start_month_str),
                        int(start_day)),
                    end_date=datetime(
                        int(end_year_str) if end_year_str else self._current_year,
                        self._month_to_number(end_month_str),
                        int(end_day)),
                    raw=text[match.start():match.end()],
                )
                event.span = (match.start(), match.end())
                events.append(event)
            except ValueError:
                pass

        # --- Numerischer Bereich: DD.MM.YYYY - DD.MM.YYYY (auch mit –) ---
        pattern_num_range = (
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
            r'\s*[-–]\s*'
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})'
        )
        for match in re.finditer(pattern_num_range, text, re.IGNORECASE):
            start_day, start_month_str, start_year_str, end_day, end_month_str, end_year_str = match.groups()
            try:
                event = ParsedEvent(
                    start_date=datetime(int(start_year_str), int(start_month_str), int(start_day)),
                    end_date=datetime(int(end_year_str), int(end_month_str), int(end_day)),
                    raw=text[match.start():match.end()],
                )
                event.span = (match.start(), match.end())
                events.append(event)
            except ValueError:
                pass

        # --- „vom DD. bis/-– DD. Monat [Jahr]" ---
        pattern_vom_bis = (
            r'vom\s+(\d{1,2})\.\s*(?:bis|[-–])\s+'
            r'(\d{1,2})\.\s+'
            r'(' + self._month_re + r')'
            r'(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern_vom_bis, text, re.IGNORECASE):
            start_day, end_day, month_str, year_str = match.groups()
            month = self._month_to_number(month_str)
            year = int(year_str) if year_str else self._current_year
            try:
                event = ParsedEvent(
                    start_date=datetime(year, month, int(start_day)),
                    end_date=datetime(year, month, int(end_day)),
                    raw=text[match.start():match.end()],
                )
                event.span = (match.start(), match.end())
                events.append(event)
            except ValueError:
                pass

        # --- „beginnt am DD. Monat [Jahr] und endet am DD. Monat [Jahr]" ---
        pattern_beginnt_endet = (
            r'beginnt\s+am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?\s*'
            r'.*?'
            r'und\s+endet\s+am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern_beginnt_endet, text, re.IGNORECASE):
            start_day, start_month_str, start_year_str, end_day, end_month_str, end_year_str = match.groups()
            try:
                event = ParsedEvent(
                    start_date=datetime(
                        int(start_year_str) if start_year_str else self._current_year,
                        self._month_to_number(start_month_str),
                        int(start_day)),
                    end_date=datetime(
                        int(end_year_str) if end_year_str else self._current_year,
                        self._month_to_number(end_month_str),
                        int(end_day)),
                    raw=text[match.start():match.end()],
                )
                event.span = (match.start(), match.end())
                events.append(event)
            except ValueError:
                pass

        pattern_mixed_range = (
            r'am\s+(\d{1,2})\.?\s*('+ self._month_re + r')(?:\s+(\d{4}))?'
            r'.*?'
            r'und\s+endet\s+am\s+(\d{1,2})\.?\s*('+ self._month_re + r')(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern_mixed_range, text, re.IGNORECASE):
            start_day, start_month_str, start_year_str, end_day, end_month_str, end_year_str = match.groups()
            try:
                event = ParsedEvent(
                    start_date=datetime(
                        int(start_year_str) if start_year_str else self._current_year,
                        self._month_to_number(start_month_str),
                        int(start_day)),
                    end_date=datetime(
                        int(end_year_str) if end_year_str else self._current_year,
                        self._month_to_number(end_month_str),
                        int(end_day)),
                    raw=text[match.start():match.end()],
                )
                event.span = (match.start(), match.end())
                events.append(event)
            except ValueError:
                pass

        pattern_short_range = (
            r'(\d{1,2})\.\s*[-–]\s*'       # 15. -
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})'  # 17.6.2026
        )
        for match in re.finditer(pattern_short_range, text, re.IGNORECASE):
            start_day, end_day, month, year = match.groups()
            try:
                event = ParsedEvent(
                    start_date=datetime(int(year), int(month), int(start_day)),
                    end_date=datetime(int(year), int(month), int(end_day)),
                    raw=match.group(0),
                )
                event.span = (match.start(), match.end())
                events.append(event)
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
        for match in re.finditer(pattern, text, re.IGNORECASE):
            days_raw, month_str, year_str = match.groups()
            days  = [int(d) for d in re.findall(r'\d{1,2}', days_raw)]
            if len(days) < 2:
                continue
            month = self._month_to_number(month_str)
            year  = int(year_str) if year_str else self._current_year
            for day in days:
                try:
                    date = datetime(year, month, day)
                    event = ParsedEvent(
                        start_date=date, end_date=date,
                        raw=match.group(0),
                    )
                    event.span = (match.start(), match.end())
                    events.append(event)
                except ValueError:
                    pass
        return events

    def _extract_single_date(self, text) -> list[ParsedEvent]:
        pattern = (
            r'\b(?:am\s+)?(\d{1,2})\.?\s*'
            r'(' + self._month_re + r')'
            r'(?:\s+(\d{4}))?\b'
        )
        events = []

        for match in re.finditer(pattern, text, re.IGNORECASE):
            if any(not(match.end() <= e.span[0] or match.start() >= e.span[1]) for e in events):
                continue
            day, month_str, year_str = match.groups()
            date = self._make_date(day, month_str, year_str)
            if date:
                event = ParsedEvent(
                    start_date = date,
                    end_date = date,
                    raw = text[match.start():match.end()],
                )
                event.span = (match.start(), match.end())

                events.append(event)

        return events

    def _extract_time_range(self, text) -> tuple[str, str] | None:
        pattern_standard = (
            r'(?<!\d)'
            r'(?:von\s+)?'
            r'(\d{1,2})(?::(\d{2}))?\s*(?:uhr)?\s*'
            r'(?:bis|[-–])\s*'
            r'(\d{1,2})(?::(\d{2}))?\s*(?:uhr)?'
            r'(?!\d)'
        )
        match =re.search(pattern_standard, text.lower())
        if match:
            start_h, start_m, end_h, end_m = match.groups()
            start_time = self._normalize_time(start_h, start_m)
            end_time = self._normalize_time(end_h, end_m)
            return start_time, end_time

        pattern_natural = (
            r'(?<!\d)'
            r'(?:gegen\s+)?'
            r'(\d{1,2})(?::(\d{2}))?\s*(?:uhr)?\s*'
            r'(?:anfang(?:en)|start(?:en|et)|beginn(?:t|en)?)?\s*'
            r'(?:und\s+)?'
            r'(?:bis\s+(?:etwa\s+)?)'
            r'(\d{1,2})(?::(\d{2}))?\s*(?:uhr)?'
            r'(?!\d)'
        )
        match = re.search(pattern_natural, text, re.IGNORECASE)
        if match:
            start_h, start_m, end_h, end_m = match.groups()
            start_time = self._normalize_time(start_h, start_m)
            end_time = self._normalize_time(end_h, end_m)
            return start_time, end_time

        pattern_single = r'(?<!\d)(?:um|gegen)\s+(\d{1,2})(?::(\d{2}))?\s*(?:uhr)?(?!\d)'
        match = re.search(pattern_single, text, re.IGNORECASE)
        if match:
            start_h, start_m = match.groups()
            return self._normalize_time(start_h, start_m), ''

        return None

    def _extract_relative_weekday(self, text) -> list[ParsedEvent]:
        weekday_re = '|'.join(self.WEEKDAYS_DE.keys())
        pattern= (
            r'(?:am\s+)?'
            r'(kommende(?:n)?|nächste(?:n)?|diese(?:n|m)?|heutige(?:n)?)?\s*'
            r'\b(' + weekday_re + r')\b'
        )
        events = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            modifier = (match.group(1) or '').strip()
            weekday_str = match.group(2).strip()
            date = self._resolve_relative_weekday(weekday_str, modifier)

            if date:
                event = ParsedEvent(
                    start_date=date,
                    end_date=date,
                    raw=match.group(0)
                )
                event.span = (match.start(), match.end())
                events.append(event)
        return events

    def _assign_event_context(self, events, text):
        global_location = self._extract_location(text)
        global_trainer = self._extract_trainer(text)

        for i, event in enumerate(events):
            time_start = event.span[1]
            time_end = events[i + 1].span[0] if i + 1 < len(events) else len(text)
            time_range = self._extract_time_range(text[time_start:time_end])

            if not time_range:
                time_range = self._extract_time_range(text)

            if time_range:
                event.start_time, event.end_time = time_range
            else:
                event.start_time = ''
                event.end_time = ''

            context_start = max(0, event.span[0] - 200)
            context_end = min(len(text), event.span[1] + 200)
            context = text[context_start:context_end]

            event.location = self._extract_location(context) or global_location or ''
            event.trainer = self._extract_trainer(context) or global_trainer or ''

    def _extract_title(self, text):

        for line in text.splitlines():
            line = line.strip()
            match = re.match(r'^(?:betreff|titel|subject)\s*:\s*(.+)$', line, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        pattern = r'^(.*?)(?:beginnt am|vom\s+\d{1,2}|am \d{1,2})'
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            candidate = match.group(1).strip()
            if 3 < len(candidate) < 60:
                return candidate

        return ''

    def _extract_event_description(self, text, span_start):
        look_back = text[max(0, span_start - 80):span_start]
        pattern = r'[-•*]?\s*([A-Za-zÄÖÜäöüß]+(?:\s+\d+|\s+[IVXLC]+)?)\s*:\s*$'
        match = re.search(pattern, look_back.strip())
        if match:
            return match.group(1).strip()
        return ''

    def _extract_location(self, text):
        text = self._normalize(text)
        text_lower = text.lower()

        # special case
        if "remote" in text_lower:
            return "remote"

        patterns = [
            # spezifisch zuerst
            r'(?i:ort|location)\s*(?:ist|wäre|:)?\s*(?:aktuell\s+|derzeit\s+|momentan\s+|noch\s+)?([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)(?:[.,]|$|\s)',

            r'(?i:findet\s+in)\s+([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)(?:\s+(?:statt|geplant|sein)|[.,]|$)',

            r'(?i:\bin\s+(?:(?:der|dem|die|das|unserem|ihrem|unser|ihr)\s+\w+\s+)?in\s+)([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)(?:\s+\w+|[.,]|$)',

            r'(?i:\b(?:in\s+(?:der\s+|dem\s+|die\s+|das\s+)?|im\s+|ins\s+))([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)(?:\s+(?:statt|stattfinden|geplant|sein|wird|durchführen|durchgeführt)|[.,]|$)',
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                location = match.group(1).strip()
                words = location.split()
                if location.lower().split()[0] in self.MONTHS_DE:
                    continue

                if len(words) == 2 and words[1].lower() in {"hallo", "hi", "hey", "guten morgen", "guten tag", "guten abend", "viele grüße", "vg", "lg", "mit freundlichen grüßen", "beste grüße"}:
                    continue

                location = re.sub(r'\b(statt|stattfinden|geplant|sein|wird)\b.*', '', location, flags=re.IGNORECASE).strip()

                if len(location.split()) <= 4:
                    return location
        return ''

    def _extract_trainer(self, text):
        text = self._normalize(text)

        patterns = [
            r'(?i)(?P<keyword>trainer(?:in)?|referent(?:in)?)\s*(?:ist|wird|:)\s*'
            r'(?:(?P<title>dr\.|doktor|prof\.|professor|frau|herr|fräulein)\s+)?'
            r'(?P<name>[A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)',

            r'(?i)(?P<keyword>als\s+(?:trainer(?:in)?|referent(?:in)?))\s+ist\s*'
            r'(?:(?P<title>dr\.|doktor|prof\.|professor|frau|herr|fräulein)\s+)?'
            r'(?P<name>[A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)',

            r'(?i)(?P<keyword>von|leiter(?:in)?)\s*(?:ist|:)?\s*'
            r'(?:(?P<title>dr\.|doktor|prof\.|professor|frau|herr|fräulein)\s+)?'
            r'(?P<name>[A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)'
        ]

        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if not match:
                continue

            title = (match.group("title") or "").strip().lower()
            name = (match.group("name") or "").strip()

            name = re.sub(
                r'^(wie\s+\w+\s+|noch\s+|auch\s+|bitte\s+|bereits\s+)',
                '',
                name,
                flags=re.IGNORECASE
            ).strip()

            name = re.sub(r'\bgeleitet\b', '', name, flags=re.IGNORECASE).strip()

            name = re.split(
                r'\s+(?:vorgesehen|geplant|wird|die|der|das|ist|sein)\b',
                name,
                flags=re.IGNORECASE
            )[0].strip()

            if len(name.split()) < 1:
                continue

            allowed_titles = {"dr.", "prof.", "herr", "frau"}

            if title in allowed_titles:
                return f"{title.title()} {name}".strip()

            return name

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
