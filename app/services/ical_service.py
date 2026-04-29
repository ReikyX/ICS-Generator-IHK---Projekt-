from icalendar import Calendar, Event
from datetime import datetime, timedelta, timezone
from typing import List
from app.model.parse_model import ParsedEvent

class ICalService:

    def create_icalendar(self, events: List[ParsedEvent]) -> bytes:
        cal = Calendar()
        cal.add('prodid', "ICS Generator IHK Projekt")
        cal.add('version', '2.0')

        for e in events:
            event = Event()
            event.add('summary', e.title or "Event")

            is_multi_day = e.end_date.date() != e.start_date.date()
            has_time = bool(e.start_time)

            if not has_time and is_multi_day:
                # Ganztagesevent — DATE ohne Uhrzeit
                event.add('dtstart', e.start_date.date())
                # exklusiv
                event.add('dtend', (e.end_date + timedelta(days=1)).date())
            else:
                start = self.combine(e.start_date, e.start_time)
                if not has_time:
                    start = start.replace(hour=8, minute=0)
                end = self.combine(e.end_date, e.end_time)
                if not e.end_time:
                    end = start + timedelta(hours=1)
                event.add('dtstart', start)
                event.add('dtend', end)

            if e.location:
                event.add('location', e.location)

            parts = []
            if e.description:
                parts.append(e.description)
            if e.raw:
                parts.append(e.raw)
            if e.trainer:
                parts.append(f"Trainer: {e.trainer}")
            event.add('description', "\n".join(parts))

            event.add('dtstamp', datetime.now(timezone.utc))
            cal.add_component(event)

        return cal.to_ical()
    
    def combine(self,dt: datetime, time_str: str) -> datetime:
        if not time_str:
            return dt
        try:
            time_parts = [int(part) for part in time_str.split(":")]
            if len(time_parts) == 2:
                return dt.replace(hour=time_parts[0], minute=time_parts[1])
        except ValueError:
            pass
        return dt