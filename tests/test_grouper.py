from datetime import datetime, timedelta
from loggrepper.grouper import group_incidents
from loggrepper.models import LogLine

_BASE = datetime(2026, 5, 16, 14, 32, 0)


def _ts(offset_sec: float) -> datetime:
    return _BASE + timedelta(seconds=offset_sec)


def _line(num: int, text: str) -> LogLine:
    return LogLine(num, text)


class TestSingleMatch:
    def test_creates_window_with_context(self):
        window = timedelta(seconds=3)
        items = iter([
            (LogLine(1, "DEBUG: antes"), _ts(58), False),
            (LogLine(2, "ERROR: boom"), _ts(0), True),
            (LogLine(3, "DEBUG: despues"), _ts(2), False),
        ])
        incidents = list(group_incidents(items, window, window))
        assert len(incidents) == 1
        assert incidents[0].id == 1
        assert len(incidents[0].lines) == 3
        assert incidents[0].matches == [1]

    def test_line_outside_window_excluded(self):
        window = timedelta(seconds=2)
        items = iter([
            (LogLine(1, "ERROR: boom"), _ts(0), True),
            (LogLine(2, "DEBUG: muy lejos"), _ts(5), False),
        ])
        incidents = list(group_incidents(items, window, window))
        assert len(incidents) == 1
        assert len(incidents[0].lines) == 1


class TestWindowOverlap:
    def test_overlapping_windows_merge(self):
        """Dos matches cercanos deben fusionarse en un solo incidente."""
        window = timedelta(seconds=3)
        items = iter([
            (LogLine(1, "ERROR: primero"), _ts(0), True),
            (LogLine(2, "INFO: entremedio"), _ts(2), False),
            (LogLine(3, "ERROR: segundo"), _ts(3), True),  # dentro de ventana del primero
            (LogLine(4, "DEBUG: final"), _ts(5), False),
        ])
        incidents = list(group_incidents(items, window, window))
        assert len(incidents) == 1
        assert len(incidents[0].lines) == 4
        assert len(incidents[0].matches) == 2

    def test_non_overlapping_windows_separate(self):
        """Matches distantes deben generar incidentes separados."""
        window = timedelta(seconds=2)
        items = iter([
            (LogLine(1, "ERROR: primero"), _ts(0), True),
            (LogLine(2, "INFO: ok"), _ts(1), False),
            (LogLine(3, "ERROR: segundo"), _ts(10), True),  # fuera de ventana
            (LogLine(4, "INFO: ok2"), _ts(11), False),
        ])
        incidents = list(group_incidents(items, window, window))
        assert len(incidents) == 2
        assert incidents[0].id == 1
        assert incidents[1].id == 2


class TestPendingBuffer:
    def test_pending_lines_before_window_rescued(self):
        """Lineas pendientes dentro de la ventana se incluyen en el incidente."""
        window = timedelta(seconds=3)
        items = iter([
            (LogLine(1, "DEBUG: antes"), _ts(57), False),  # -3s del match
            (LogLine(2, "ERROR: boom"), _ts(0), True),
        ])
        incidents = list(group_incidents(items, window, window))
        assert len(incidents) == 1
        assert len(incidents[0].lines) == 2

    def test_pending_lines_before_window_discarded(self):
        """Lineas pendientes fuera de la ventana se descartan."""
        window = timedelta(seconds=2)
        # linea pendiente con timestamp muy anterior al match
        old_ts = datetime(2026, 5, 16, 14, 25, 0)  # 7 min antes
        items = iter([
            (LogLine(1, "DEBUG: muy antes"), old_ts, False),
            (LogLine(2, "ERROR: boom"), _ts(0), True),
        ])
        incidents = list(group_incidents(items, window, window))
        assert len(incidents) == 1
        assert len(incidents[0].lines) == 1
        assert incidents[0].lines[0].raw == "ERROR: boom"

    def test_pending_discarded_after_incident_close(self):
        """Lineas pendientes se descartan si estan antes del cutoff del incidente anterior."""
        window = timedelta(seconds=2)
        items = iter([
            (LogLine(1, "DEBUG: antes match1"), _ts(57), False),
            (LogLine(2, "ERROR: match1"), _ts(0), True),
            (LogLine(3, "DEBUG: fuera de ventana"), _ts(3), False),  # en end del incidente, no se incluye
            (LogLine(4, "ERROR: match2"), _ts(10), True),
        ])
        incidents = list(group_incidents(items, window, window))
        assert len(incidents) == 2


class TestAsymmetricWindows:
    def test_more_before_than_after(self):
        """before > after: mas contexto atras que adelante."""
        before = timedelta(seconds=5)
        after = timedelta(seconds=1)
        items = iter([
            (LogLine(1, "DEBUG: muy antes"), _ts(-5), False),
            (LogLine(2, "DEBUG: justo antes"), _ts(-2), False),
            (LogLine(3, "ERROR: boom"), _ts(0), True),
            (LogLine(4, "DEBUG: justo despues"), _ts(0.5), False),
            (LogLine(5, "DEBUG: muy despues"), _ts(3), False),
        ])
        incidents = list(group_incidents(items, before, after))
        assert len(incidents) == 1
        assert len(incidents[0].lines) == 4
        assert "muy antes" in incidents[0].lines[0].raw
        assert "muy despues" not in [l.raw for l in incidents[0].lines]

    def test_more_after_than_before(self):
        """after > before: mas contexto adelante que atras."""
        before = timedelta(seconds=1)
        after = timedelta(seconds=5)
        items = iter([
            (LogLine(1, "DEBUG: muy antes"), _ts(-5), False),
            (LogLine(2, "DEBUG: justo antes"), _ts(-0.5), False),
            (LogLine(3, "ERROR: boom"), _ts(0), True),
            (LogLine(4, "DEBUG: justo despues"), _ts(2), False),
            (LogLine(5, "DEBUG: muy despues"), _ts(4), False),
        ])
        incidents = list(group_incidents(items, before, after))
        assert len(incidents) == 1
        assert len(incidents[0].lines) == 4
        assert "muy antes" not in [l.raw for l in incidents[0].lines]
        assert "muy despues" in incidents[0].lines[-1].raw


class TestPendingLimit:
    def test_buffer_truncated_when_exceeded(self):
        """El buffer de pendientes se trunca al exceder _MAX_PENDING."""
        from loggrepper.grouper import _MAX_PENDING
        before = timedelta(seconds=3)
        after = timedelta(seconds=3)
        items = [(LogLine(i, f"INFO: linea {i}"), _ts(float(i)), False) for i in range(_MAX_PENDING + 100)]
        items.append((LogLine(_MAX_PENDING + 100, "ERROR: boom"), _ts(float(_MAX_PENDING + 100)), True))
        incidents = list(group_incidents(iter(items), before, after))
        assert len(incidents) == 1
        assert incidents[0].lines[0].number > 1


class TestNoMatches:
    def test_all_lines_pending_no_output(self):
        """Sin matches no se generan incidentes."""
        window = timedelta(seconds=3)
        items = iter([
            (LogLine(1, "INFO: linea1"), _ts(0), False),
            (LogLine(2, "INFO: linea2"), _ts(1), False),
            (LogLine(3, "INFO: linea3"), _ts(2), False),
        ])
        incidents = list(group_incidents(items, window, window))
        assert len(incidents) == 0
