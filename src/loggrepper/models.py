from dataclasses import dataclass
from datetime import datetime

@dataclass
class LogLine:
    number: int
    raw: str

@dataclass
class Incident:
    id: int
    start: datetime
    end: datetime
    lines: list[LogLine]
    matches: list[int]

