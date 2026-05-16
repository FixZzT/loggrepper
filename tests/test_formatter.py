import json
from datetime import datetime

from loggrepper.formatter import PrettyFormatter, JsonFormatter
from loggrepper.models import Incident, LogLine


def test_pretty_formatter_empty():
    result = PrettyFormatter().format([])
    assert result == "Sin incidentes encontrados."


def test_pretty_formatter_single_incident():
    incident = Incident(
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
    result = PrettyFormatter().format([incident])
    assert "Incidente #1" in result
    assert ">>>" in result
    assert "ERROR: boom" in result


def test_json_formatter_empty():
    result = JsonFormatter().format([])
    data = json.loads(result)
    assert data == []


def test_json_formatter_incident():
    incident = Incident(
        id=1,
        start=datetime(2026, 5, 16, 14, 31, 58),
        end=datetime(2026, 5, 16, 14, 32, 4),
        lines=[
            LogLine(1, "INFO: antes"),
            LogLine(2, "ERROR: boom"),
        ],
        matches=[1],
    )
    result = JsonFormatter().format([incident])
    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["lines"][1]["match"] is True
    assert data[0]["lines"][0]["match"] is False
