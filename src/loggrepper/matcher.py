from re import Pattern
from collections.abc import Iterator

from loggrepper.models import LogLine


def match_lines(
    lines: Iterator[LogLine],
    patterns: list[Pattern[str]],
) -> Iterator[tuple[LogLine, bool]]:
    for line in lines:
        matched = any(p.search(line.raw) for p in patterns)
        yield line, matched


def exclude_lines(
    items: Iterator[tuple[LogLine, bool]],
    exclude_pat: Pattern[str],
) -> Iterator[tuple[LogLine, bool]]:
    """Filtra lineas que coinciden con el patron de exclusion."""
    for line, matched in items:
        if not exclude_pat.search(line.raw):
            yield line, matched
