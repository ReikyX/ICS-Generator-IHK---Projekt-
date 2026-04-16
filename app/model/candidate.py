from dataclasses import dataclass
from datetime import datetime

@dataclass
class Candidate:
    start_date: datetime
    end_date: datetime
    span: tuple[int, int]
    source: str
    raw: str
    confidence: int = 1