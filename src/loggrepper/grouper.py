from datetime import datetime, timedelta
from collections.abc import Iterator

from loggrepper.models import Incident, LogLine


def group_incidents(
    items: Iterator[tuple[LogLine, datetime, bool]],
    window: timedelta,
) -> Iterator[Incident]:
    incident: Incident | None = None
    next_id = 1
    pending: list[tuple[LogLine, datetime]] = []

    for line, ts, matched in items:
        if incident is not None and ts <= incident.end:
            incident.lines.append(line)
            if matched:
                incident.matches.append(len(incident.lines) - 1)
                incident.end = max(incident.end, ts + window)
            continue

        if incident is not None and ts > incident.end:
            yield incident
            pending = _discard_before(pending, incident.end)
            incident = None
            # la linea actual se reprocesa en el siguiente if

        if incident is None:
            if matched:
                incident = _new_incident(next_id, line, ts, window, pending)
                next_id += 1
            else:
                pending.append((line, ts))

    if incident is not None:
        yield incident


def _new_incident(
    iid: int,
    match_line: LogLine,
    match_ts: datetime,
    window: timedelta,
    pending: list[tuple[LogLine, datetime]],
) -> Incident:
    """Crea incidente rescatando lineas pendientes dentro de [match_ts - window, ...]."""
    start = match_ts - window
    incident_lines: list[LogLine] = []
    incident_matches: list[int] = []

    # rescatar lineas pendientes dentro de la ventana
    survivors: list[tuple[LogLine, datetime]] = []
    for pl, pts in pending:
        if pts >= start:
            incident_lines.append(pl)
        else:
            survivors.append((pl, pts))

    pending.clear()
    pending.extend(survivors)

    incident_matches.append(len(incident_lines))
    incident_lines.append(match_line)

    return Incident(
        id=iid,
        start=start,
        end=match_ts + window,
        lines=incident_lines,
        matches=incident_matches,
    )


def _discard_before(
    pending: list[tuple[LogLine, datetime]],
    cutoff: datetime,
) -> list[tuple[LogLine, datetime]]:
    """Descarta lineas con timestamp <= cutoff."""
    return [(pl, pts) for pl, pts in pending if pts > cutoff]
