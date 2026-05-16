"""Formateadores de output para incidentes."""
import json
from typing import Protocol

from loggrepper.models import Incident


class Formatter(Protocol):
    """Protocolo que todo formateador debe cumplir."""
    def format(self, incidents: list[Incident]) -> str:
        ...


class PrettyFormatter:
    """Output legible para humanos, con colores y marcadores."""

    def format(self, incidents: list[Incident]) -> str:
        if not incidents:
            return "Sin incidentes encontrados."

        lines: list[str] = []
        for inc in incidents:
            lines.append(
                f"--- Incidente #{inc.id} | "
                f"{inc.start} — {inc.end} | "
                f"{len(inc.lines)} lineas ---"
            )
            for i, logline in enumerate(inc.lines):
                marker = ">>>" if i in inc.matches else "   "
                lines.append(f"{marker} {logline.raw}")
            lines.append("")
        return "\n".join(lines)


class JsonFormatter:
    """Output JSON, ideal para pipe a jq u otras herramientas."""

    def format(self, incidents: list[Incident]) -> str:
        data = [
            {
                "id": inc.id,
                "start": inc.start.isoformat(),
                "end": inc.end.isoformat(),
                "line_count": len(inc.lines),
                "match_count": len(inc.matches),
                "lines": [
                    {
                        "number": logline.number,
                        "text": logline.raw,
                        "match": i in inc.matches,
                    }
                    for i, logline in enumerate(inc.lines)
                ],
            }
            for inc in incidents
        ]
        return json.dumps(data, indent=2, ensure_ascii=False)


def get_formatter(output: str) -> Formatter:
    """Devuelve el formateador segun el formato elegido."""
    formatters: dict[str, Formatter] = {
        "pretty": PrettyFormatter(),
        "json": JsonFormatter(),
    }
    return formatters[output]
