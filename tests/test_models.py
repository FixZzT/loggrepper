from loggrepper.models import LogLine,Incident
from datetime import datetime


def test_create_logline():
    linea = LogLine(number=3, raw="ERROR: algo exploto")
    assert linea.number == 3
    assert linea.raw == "ERROR: algo exploto"

def test_create_incident():
    linea = LogLine(number=5, raw="ERROR: timeout")
    incident = Incident(
        id = 1,
        start=datetime(2026, 5, 16, 14, 32, 0),
        end=datetime(2026, 5, 16, 14, 32, 5),
        lines=[linea],
        matches=[0]
    )
    assert incident.id == 1
    assert incident.lines == [linea]
    assert incident.matches == [0]