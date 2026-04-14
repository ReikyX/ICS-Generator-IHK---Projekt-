from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Tuple

@dataclass
class ParsedEvent:
    start_date: datetime
    end_date: datetime
    raw: str
    title: str = ""
    start_time: str = ""
    end_time: str = ""
    location: str = ""
    trainer: str = ""
    span: Optional[Tuple[int, int]] = None

    def to_dict(self) -> dict:
        return{
            "title": self.title,
            "start_date": self.start_date.strftime("%d.%m.%Y"),
            "end_date": self.end_date.strftime("%d.%m.%Y"),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "location": self.location,
            "trainer": self.trainer,
            "raw": self.raw
        }