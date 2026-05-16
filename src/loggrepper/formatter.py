"""Formateadores de output para incidentes."""
import json
from datetime import datetime
from typing import Protocol

from rich.console import Console

from loggrepper.models import Incident

console = Console(highlight=False)


class Formatter(Protocol):
    """Protocolo que todo formateador debe cumplir."""
    def format_empty(self) -> str:
        ...
    def format_one(self, inc: Incident) -> str:
        ...


class PrettyFormatter:
    """Output legible para humanos, con colores y marcadores."""

    def format_empty(self) -> str:
        return "Sin incidentes encontrados."

    def format_one(self, inc: Incident) -> str:
        lines: list[str] = []
        header = (
            f"[bold cyan]--- Incidente #{inc.id}[/bold cyan] | "
            f"{inc.start} — {inc.end} | "
            f"{len(inc.lines)} lineas ---"
        )
        lines.append(header)
        for i, logline in enumerate(inc.lines):
            if i in inc.matches:
                marker = "[bold red]>>>[/bold red]"
                text = f"[bold red]{logline.raw}[/bold red]"
            else:
                marker = "   "
                text = f"[dim]{logline.raw}[/dim]"
            lines.append(f"{marker} {text}")
        lines.append("")
        output = "\n".join(lines)
        return output


class JsonFormatter:
    """Output JSON, ideal para pipe a jq u otras herramientas."""

    def __init__(self) -> None:
        self._incidents: list[Incident] = []

    def format_empty(self) -> str:
        return "[]"

    def format_one(self, inc: Incident) -> str:
        self._incidents.append(inc)
        return ""

    def flush(self) -> str:
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
            for inc in self._incidents
        ]
        return json.dumps(data, indent=2, ensure_ascii=False)


class StatsFormatter:
    """Resumen estadistico en vez de incidentes individuales."""

    def __init__(self) -> None:
        self.count = 0
        self.total_lines = 0
        self.total_matches = 0
        self.first_ts: datetime | None = None
        self.last_ts: datetime | None = None

    def format_empty(self) -> str:
        return "Sin incidentes encontrados."

    def format_one(self, inc: Incident) -> str:
        self.count += 1
        self.total_lines += len(inc.lines)
        self.total_matches += len(inc.matches)
        if self.first_ts is None:
            self.first_ts = inc.start
        self.last_ts = inc.end
        return ""

    def flush(self) -> str:
        if self.count == 0:
            return self.format_empty()
        lines: list[str] = []
        lines.append("[bold]Resumen de busqueda[/bold]")
        lines.append(f"  Incidentes encontrados: {self.count}")
        lines.append(f"  Lineas en incidentes:   {self.total_lines}")
        lines.append(f"  Lineas con match:       {self.total_matches}")
        lines.append(f"  Rango temporal:         {self.first_ts} — {self.last_ts}")
        return "\n".join(lines)


def get_formatter(output: str) -> Formatter:
    """Devuelve el formateador segun el formato elegido."""
    formatters: dict[str, Formatter] = {
        "pretty": PrettyFormatter(),
        "json": JsonFormatter(),
        "stats": StatsFormatter(),
    }
    return formatters[output]
