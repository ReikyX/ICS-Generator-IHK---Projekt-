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

            start = self.combine(e.start_date, e.start_time)
            if not e.start_time:
                start = start.replace(hour=8, minute=0)
            event.add('dtstart', start)
            end = self.combine(e.end_date, e.end_time)
            if not e.end_time:
                end = start + timedelta(hours=1)
            event.add('dtend', end)
            
            if e.location:
                event.add('location', e.location)

            description = e.raw or ""
            if e.trainer:
                description += f"\nTrainer: {e.trainer}"
            event.add('description', description)

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