from datetime import datetime, timedelta
from loggrepper.grouper import group_incidents
from loggrepper.models import LogLine


def test_single_match_creates_window():
    window = timedelta(seconds=3)
    ts = datetime(2026, 5, 16, 14, 32, 0)
    items = iter([
        (LogLine(1, "DEBUG: antes"), ts - timedelta(seconds=2), False),
        (LogLine(2, "ERROR: boom"), ts, True),
        (LogLine(3, "DEBUG: despues"), ts + timedelta(seconds=2), False),
    ])
    incidents = list(group_incidents(items, window))
    assert len(incidents) == 1
    assert incidents[0].id == 1
    assert len(incidents[0].lines) == 3
    assert incidents[0].matches == [1]


def test_line_outside_window_excluded():
    window = timedelta(seconds=2)
    ts = datetime(2026, 5, 16, 14, 32, 0)
    items = iter([
        (LogLine(1, "ERROR: boom"), ts, True),
        (LogLine(2, "DEBUG: muy lejos"), ts + timedelta(seconds=5), False),
    ])
    incidents = list(group_incidents(items, window))
    assert len(incidents) == 1
    assert len(incidents[0].lines) == 1
    assert incidents[0].lines[0].raw == "ERROR: boom"