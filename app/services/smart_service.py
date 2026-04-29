import re
from datetime import datetime, timedelta
from app.model.parse_model import ParsedEvent
from app.model.candidate import Candidate


class SmartEventParser:
    """Parser for natural language (German)"""

    MONTHS_DE = {
        'januar': 1, 'jan': 1,
        'februar': 2, 'feb': 2,
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

    # -------------------------------------------------------------------------
    # PUBLIC
    # -------------------------------------------------------------------------

    def parse_smart_text(self, text, custom_title="") -> list[ParsedEvent]:
        """Main method for parsing natural language (German)."""
        normalized = self._normalize(text)

        # 1. Extractor Phase → nur Kandidaten sammeln
        candidates: list[Candidate] = []
        candidates.extend(self._extract_date_range(normalized))
        candidates.extend(self._extract_dated_weekday(normalized))
        candidates.extend(self._extract_multi_dates(normalized))
        candidates.extend(self._extract_numeric_single_date(normalized))
        candidates.extend(self._extract_single_date(normalized))

        # Relative Wochentage nur als Fallback, wenn keine konkreten Daten
        has_concrete = any(
            c.source in ('date_range', 'dated_weekday', 'multi_date',
                         'numeric_single', 'single_date')
            for c in candidates
        )
        if not has_concrete:
            candidates.extend(self._extract_relative_weekday(normalized))

        # 2. Resolve Phase → Überlappungen auflösen, Events erzeugen
        events = self._resolve_candidates(candidates)

        # 3. Meta
        global_title = custom_title if custom_title else self._extract_title(text)
        events.sort(key=lambda e: e.span[0] if e.span else 0)

        for event in events:
            event.title = global_title
            event.description = (
                self._extract_event_description(normalized, event.span[0])
                if event.span else ''
            )

        self._assign_event_context(events, normalized)
        return events

    # -------------------------------------------------------------------------
    # RESOLVE
    # -------------------------------------------------------------------------

    def _resolve_candidates(self, candidates: list[Candidate]) -> list[ParsedEvent]:
        """
        Sortiert nach Position, löst Überlappungen auf (höhere confidence gewinnt),
        entfernt Duplikate (gleiche start_date + end_date) und erzeugt ParsedEvents.
        """
        # Bei Überlappung: höhere confidence bevorzugen, dann längerer Span
        candidates.sort(key=lambda c: (c.span[0], -c.confidence, -(c.span[1] - c.span[0])))

        accepted: list[Candidate] = []
        occupied: list[tuple[int, int]] = []

        for c in candidates:
            if self._overlaps(c.span, occupied):
                continue
            accepted.append(c)
            occupied.append(c.span)

        # Duplikate (gleiche Daten) entfernen
        seen: set[tuple] = set()
        events: list[ParsedEvent] = []

        for c in accepted:
            key = (c.start_date, c.end_date)
            if key in seen:
                continue
            seen.add(key)

            event = ParsedEvent(
                start_date=c.start_date,
                end_date=c.end_date,
                raw=c.raw,
            )
            event.span = c.span
            events.append(event)

        return events

    def _overlaps(self, span: tuple[int, int], occupied: list[tuple[int, int]]) -> bool:
        s1, e1 = span
        for s2, e2 in occupied:
            if not (e1 <= s2 or s1 >= e2):
                return True
        return False

    # -------------------------------------------------------------------------
    # EXTRACTORS → geben Candidate-Listen zurück
    # -------------------------------------------------------------------------

    def _extract_date_range(self, text) -> list[Candidate]:
        candidates = []

        # --- „start wäre am DD. Monat – ende wäre am DD. Monat" ---
        pattern_start_end = (
            r'start\s+(?:wäre|ist)?\s*am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?\s*'
            r'und\s+ende\s+(?:wäre|ist)?\s*am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern_start_end, text, re.IGNORECASE):
            sd, sm, sy, ed, em, ey = match.groups()
            try:
                candidates.append(Candidate(
                    start_date=datetime(int(sy) if sy else self._current_year, self._month_to_number(sm), int(sd)),
                    end_date=datetime(int(ey) if ey else self._current_year, self._month_to_number(em), int(ed)),
                    span=(match.start(), match.end()), raw=match.group(0),
                    source='date_range', confidence=5,
                ))
            except ValueError:
                pass

        # --- DD.MM.YYYY – DD.MM.YYYY ---
        pattern_num_range = (
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})\s*[-–]\s*(\d{1,2})\.(\d{1,2})\.(\d{4})'
        )
        for match in re.finditer(pattern_num_range, text):
            sd, sm, sy, ed, em, ey = match.groups()
            try:
                candidates.append(Candidate(
                    start_date=datetime(int(sy), int(sm), int(sd)),
                    end_date=datetime(int(ey), int(em), int(ed)),
                    span=(match.start(), match.end()), raw=match.group(0),
                    source='date_range', confidence=5,
                ))
            except ValueError:
                pass

       # --- DD.MM. – DD.MM.YYYY (Cross-Month, z. B. "30.9. - 2.10.2026") ---
        pattern_cross_month = r'(\d{1,2})\.(\d{1,2})\.\s*[-–]\s*(\d{1,2})\.(\d{1,2})\.(\d{4})'
        for match in re.finditer(pattern_cross_month, text):
            sd, sm, ed, em, year = match.groups()
            try:
                candidates.append(Candidate(
                    start_date=datetime(int(year), int(sm), int(sd)),
                    end_date=datetime(int(year), int(em), int(ed)),
                    span=(match.start(), match.end()), raw=match.group(0),
                    source='date_range', confidence=5,
                ))
            except ValueError:
                pass

        # --- DD. – DD.MM.YYYY (Same-Month, z. B. "7. - 9.10.2025") ---
        pattern_short_range = r'(?<!\d\.)(\d{1,2})\.\s*[-–]\s*(\d{1,2})\.(\d{1,2})\.(\d{4})'
        for match in re.finditer(pattern_short_range, text):
            sd, ed, month, year = match.groups()
            try:
                candidates.append(Candidate(
                    start_date=datetime(int(year), int(month), int(sd)),
                    end_date=datetime(int(year), int(month), int(ed)),
                    span=(match.start(), match.end()), raw=match.group(0),
                    source='date_range', confidence=5,
                ))
            except ValueError:
                pass

        # --- vom DD. bis DD. Monat [Jahr] ---
        pattern_vom_bis = (
            r'vom\s+(\d{1,2})\.\s*(?:bis|[-–])\s+'
            r'(\d{1,2})\.\s+(' + self._month_re + r')(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern_vom_bis, text, re.IGNORECASE):
            sd, ed, month_str, year_str = match.groups()
            month = self._month_to_number(month_str)
            year = int(year_str) if year_str else self._current_year
            try:
                candidates.append(Candidate(
                    start_date=datetime(year, month, int(sd)),
                    end_date=datetime(year, month, int(ed)),
                    span=(match.start(), match.end()), raw=match.group(0),
                    source='date_range', confidence=5,
                ))
            except ValueError:
                pass

        # --- beginnt am … und endet am … ---
        pattern_beginnt_endet = (
            r'beginnt\s+am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?\s*.*?'
            r'und\s+endet\s+am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern_beginnt_endet, text, re.IGNORECASE):
            sd, sm, sy, ed, em, ey = match.groups()
            try:
                candidates.append(Candidate(
                    start_date=datetime(int(sy) if sy else self._current_year, self._month_to_number(sm), int(sd)),
                    end_date=datetime(int(ey) if ey else self._current_year, self._month_to_number(em), int(ed)),
                    span=(match.start(), match.end()), raw=match.group(0),
                    source='date_range', confidence=5,
                ))
            except ValueError:
                pass

        # --- am … und endet am … ---
        pattern_mixed = (
            r'am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?.*?'
            r'und\s+endet\s+am\s+(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?'
        )
        for match in re.finditer(pattern_mixed, text, re.IGNORECASE):
            sd, sm, sy, ed, em, ey = match.groups()
            try:
                candidates.append(Candidate(
                    start_date=datetime(int(sy) if sy else self._current_year, self._month_to_number(sm), int(sd)),
                    end_date=datetime(int(ey) if ey else self._current_year, self._month_to_number(em), int(ed)),
                    span=(match.start(), match.end()), raw=match.group(0),
                    source='date_range', confidence=5,
                ))
            except ValueError:
                pass

        return candidates

    def _extract_dated_weekday(self, text) -> list[Candidate]:
        """Wochentag, DD. Monat [Jahr]  →  confidence 4"""
        weekday_re = '|'.join(self.WEEKDAYS_DE.keys())
        pattern = (
            r'\b(?:' + weekday_re + r')\s*,\s*'
            r'(\d{1,2})\.?\s*(' + self._month_re + r')(?:\s+(\d{4}))?'
        )
        candidates = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            day, month_str, year_str = match.groups()
            date = self._make_date(day, month_str, year_str)
            if date:
                candidates.append(Candidate(
                    start_date=date, end_date=date,
                    span=(match.start(), match.end()), raw=match.group(0),
                    source='dated_weekday', confidence=4,
                ))
        return candidates

    def _extract_multi_dates(self, text) -> list[Candidate]:
        """am 5., 12., und 19. März  →  confidence 3"""
        pattern = (
            r'am\s+'
            r'(\d{1,2}\.(?:\s*,\s*\d{1,2}\.)*\s*(?:,?\s*und\s+)?\d{1,2}\.)'
            r'\s+(' + self._month_re + r')(?:\s+(\d{4}))?'
        )
        candidates = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            days_raw, month_str, year_str = match.groups()
            days = [int(d) for d in re.findall(r'\d{1,2}', days_raw)]
            if len(days) < 2:
                continue
            month = self._month_to_number(month_str)
            year = int(year_str) if year_str else self._current_year
            for day in days:
                try:
                    date = datetime(year, month, day)
                    candidates.append(Candidate(
                        start_date=date, end_date=date,
                        span=(match.start(), match.end()), raw=match.group(0),
                        source='multi_date', confidence=3,
                    ))
                except ValueError:
                    pass
        return candidates

    def _extract_numeric_single_date(self, text) -> list[Candidate]:
        """DD.MM.YYYY  →  confidence 3"""
        pattern = r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b'
        candidates = []
        for match in re.finditer(pattern, text):
            day, month, year = match.groups()
            try:
                date = datetime(int(year), int(month), int(day))
                candidates.append(Candidate(
                    start_date=date, end_date=date,
                    span=(match.start(), match.end()), raw=match.group(0),
                    source='numeric_single', confidence=3,
                ))
            except ValueError:
                pass
        return candidates

    def _extract_single_date(self, text) -> list[Candidate]:
        """DD. Monat [Jahr]  →  confidence 2"""
        pattern = (
            r'(?<![-–]\s)(?<!\d\.\s)'
            r'\b(?:am\s+)?(\d{1,2})\.?\s*'
            r'(' + self._month_re + r')(?:\s+(\d{4}))?\b'
        )
        candidates = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            day, month_str, year_str = match.groups()
            date = self._make_date(day, month_str, year_str)
            if date:
                candidates.append(Candidate(
                    start_date=date, end_date=date,
                    span=(match.start(), match.end()), raw=match.group(0),
                    source='single_date', confidence=2,
                ))
        return candidates

    def _extract_relative_weekday(self, text) -> list[Candidate]:
        """nächsten Montag  →  confidence 1 (nur als Fallback)"""
        weekday_re = '|'.join(self.WEEKDAYS_DE.keys())
        pattern = (
            r'(?:am\s+)?'
            r'(kommende(?:n)?|nächste(?:n)?|diese(?:n|m)?|heutige(?:n)?)?\s*'
            r'\b(' + weekday_re + r')\b'
        )
        candidates = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            modifier = (match.group(1) or '').strip()
            weekday_str = match.group(2).strip()
            date = self._resolve_relative_weekday(weekday_str, modifier)
            if date:
                candidates.append(Candidate(
                    start_date=date, end_date=date,
                    span=(match.start(), match.end()), raw=match.group(0),
                    source='relative_weekday', confidence=1,
                ))
        return candidates

    # -------------------------------------------------------------------------
    # HELPER
    # -------------------------------------------------------------------------

    def _normalize(self, text):
        return " ".join(line.strip() for line in text.splitlines() if line.strip())

    def _normalize_time(self, h, m):
        return f"{int(h):02d}:{int(m) if m else 0:02d}"

    def _resolve_relative_weekday(self, weekday_name: str, modifier: str = '') -> datetime | None:
        weekday_name = weekday_name.lower().strip()
        if weekday_name not in self.WEEKDAYS_DE:
            return None
        target = self.WEEKDAYS_DE[weekday_name]
        today = datetime.now()
        days_ahead = target - today.weekday()
        next_mod = {'kommenden', 'kommende', 'nächsten', 'nächste', 'nächster'}
        this_mod = {'diesen', 'diesem', 'dieser', 'heutigen', 'heute'}
        if modifier.lower() in next_mod:
            if days_ahead <= 0:
                days_ahead += 7
        elif modifier.lower() in this_mod:
            if days_ahead < 0:
                days_ahead += 7
        else:
            if days_ahead <= 0:
                days_ahead += 7
        return (today + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)

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
                return match.group(1).strip().rstrip(':').strip()

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

    def _extract_time_range(self, text) -> tuple[str, str] | None:
        if not re.search(r'\b(uhr|:)\b', text, re.IGNORECASE):
            return None

        pattern_standard = (
            r'(?<![\d.])'
            r'(?:von\s+)?(\d{1,2})(?::(\d{2}))?\s*(?:uhr)?\s*'
            r'(?:bis|[-–])\s*(\d{1,2})(?::(\d{2}))?\s*(?:uhr)?'
            r'(?!\d.)'
        )
        match = re.search(pattern_standard, text.lower())
        if match:
            sh, sm, eh, em = match.groups()
            return self._normalize_time(sh, sm), self._normalize_time(eh, em)

        pattern_natural = (
            r'(?<!\d)(?:gegen\s+)?(\d{1,2})(?::(\d{2}))?\s*(?:uhr)?\s*'
            r'(?:anfang(?:en)|start(?:en|et)|beginn(?:t|en)?)?\s*(?:und\s+)?'
            r'(?:bis\s+(?:etwa\s+)?)(\d{1,2})(?::(\d{2}))?\s*(?:uhr)?(?!\d)'
        )
        match = re.search(pattern_natural, text, re.IGNORECASE)
        if match:
            sh, sm, eh, em = match.groups()
            return self._normalize_time(sh, sm), self._normalize_time(eh, em)

        pattern_single = r'(?<!\d)(?:um|gegen)\s+(\d{1,2})(?::(\d{2}))?\s*(?:uhr)?(?!\d)'
        match = re.search(pattern_single, text, re.IGNORECASE)
        if match:
            sh, sm = match.groups()
            return self._normalize_time(sh, sm), ''

        return None

    def _extract_location(self, text):
        text = self._normalize(text)
        if "remote" in text.lower():
            return "remote"

        patterns = [
            r'(?i:ort|location)\s*(?:ist|wäre|:)?\s*(?:aktuell\s+|derzeit\s+|momentan\s+|noch\s+)?([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)(?:[.,]|$|\s)',
            r'(?i:findet\s+in)\s+([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)(?:\s+(?:statt|geplant|sein)|[.,]|$)',
            r'(?i:\bin\s+(?:(?:der|dem|die|das|unserem|ihrem|unser|ihr)\s+\w+\s+)?in\s+)([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)(?:\s+\w+|[.,]|$)',
            r'(?i:\b(?:in\s+(?:der\s+|dem\s+|die\s+|das\s+)?|im\s+|ins\s+))([A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)(?:\s+(?:statt|stattfinden|geplant|sein|wird|durchführen|durchgeführt)|[.,]|$)',
        ]
        greetings = {"hallo", "hi", "hey", "guten morgen", "guten tag", "guten abend",
                     "viele grüße", "vg", "lg", "mit freundlichen grüßen", "beste grüße"}

        for pat in patterns:
            match = re.search(pat, text)
            if not match:
                continue
            location = match.group(1).strip()
            words = location.split()
            if location.lower().split()[0] in self.MONTHS_DE:
                continue
            if len(words) == 2 and words[1].lower() in greetings:
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
            r'(?P<name>[A-ZÄÖÜ][a-zäöüß\-]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+)*)',
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if not match:
                continue
            title = (match.group("title") or "").strip().lower()
            name = (match.group("name") or "").strip()
            name = re.sub(r'^(wie\s+\w+\s+|noch\s+|auch\s+|bitte\s+|bereits\s+)', '', name, flags=re.IGNORECASE).strip()
            name = re.sub(r'\bgeleitet\b', '', name, flags=re.IGNORECASE).strip()
            name = re.split(r'\s+(?:vorgesehen|geplant|wird|die|der|das|ist|sein)\b', name, flags=re.IGNORECASE)[0].strip()
            if not name:
                continue
            if title in {"dr.", "prof.", "herr", "frau"}:
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
        return self.MONTHS_DE.get(month_name, datetime.now().month)