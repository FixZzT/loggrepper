from re import Pattern
from collections.abc import Iterator

from loggrepper.models import LogLine

def match_lines(lines: Iterator[LogLine], patterns: list[Pattern]) -> Iterator[tuple[LogLine, bool]]:
    for line in lines:
        matched = any(p.search(line.raw) for p in patterns)
        yield line, matched 