import json
from datetime import datetime

from loggrepper.formatter import PrettyFormatter, JsonFormatter, StatsFormatter, NdjsonFormatter
from loggrepper.models import Incident, LogLine


def _make_incident():
    return Incident(
        id=1,
        start=datetime(2026, 5, 16, 14, 31, 58),
        end=datetime(2026, 5, 16, 14, 32, 4),
        lines=[
            LogLine(1, "INFO: antes"),
            LogLine(2, "ERROR: boom"),
            LogLine(3, "DEBUG: despues"),
        ],
        matches=[1],
    )


class TestPrettyFormatter:
    def test_empty(self):
        result = PrettyFormatter().format_empty()
        assert result == "Sin incidentes encontrados."

    def test_single_incident(self):
        result = PrettyFormatter().format_one(_make_incident())
        assert "Incidente #1" in result
        assert ">>>" in result
        assert "ERROR: boom" in result
        # verificar rich markup presente
        assert "bold red" in result
        assert "bold cyan" in result
        assert "dim" in result


class TestJsonFormatter:
    def test_empty(self):
        result = JsonFormatter().format_empty()
        assert result == "[]"

    def test_incident_accumulates(self):
        fmt = JsonFormatter()
        result = fmt.format_one(_make_incident())
        assert result == ""  # no output per-incident
        flushed = fmt.flush()
        data = json.loads(flushed)
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["lines"][1]["match"] is True
        assert data[0]["lines"][0]["match"] is False


class TestStatsFormatter:
    def test_empty(self):
        result = StatsFormatter().format_empty()
        assert result == "Sin incidentes encontrados."

    def test_single_incident(self):
        fmt = StatsFormatter()
        fmt.format_one(_make_incident())
        flushed = fmt.flush()
        assert "Incidentes encontrados: 1" in flushed
        assert "Lineas en incidentes:   3" in flushed
        assert "Lineas con match:       1" in flushed

    def test_multiple_incidents(self):
        fmt = StatsFormatter()
        inc1 = _make_incident()
        inc2 = Incident(
            id=2,
            start=datetime(2026, 5, 16, 15, 0, 0),
            end=datetime(2026, 5, 16, 15, 0, 5),
            lines=[LogLine(10, "ERROR: otro")],
            matches=[0],
        )
        fmt.format_one(inc1)
        fmt.format_one(inc2)
        flushed = fmt.flush()
        assert "Incidentes encontrados: 2" in flushed
        assert "Lineas en incidentes:   4" in flushed
        assert "Lineas con match:       2" in flushed


class TestPrettyFormatterNoColor:
    def test_no_rich_markup(self):
        fmt = PrettyFormatter(color=False)
        result = fmt.format_one(_make_incident())
        assert "bold red" not in result
        assert "bold cyan" not in result
        assert "dim" not in result
        assert ">>>" in result
        assert "Incidente #1" in result
        assert "ERROR: boom" in result

    def test_flush_returns_empty(self):
        fmt = PrettyFormatter(color=False)
        assert fmt.flush() == ""


class TestNdjsonFormatter:
    def test_empty(self):
        result = NdjsonFormatter().format_empty()
        assert result == ""

    def test_single_incident(self):
        fmt = NdjsonFormatter()
        result = fmt.format_one(_make_incident())
        data = json.loads(result)
        assert data["id"] == 1
        assert data["line_count"] == 3
        assert data["lines"][1]["match"] is True

    def test_flush_returns_empty(self):
        assert NdjsonFormatter().flush() == ""
