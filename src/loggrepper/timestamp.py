from datetime import datetime
from re import Pattern, compile
from typing import Literal
from dataclasses import dataclass


@dataclass
class TimestampFormat:
    """Define como extraer y parsear un timestamp de una linea."""
    name: str
    regex: Pattern[str]
    format_str: str
    position: Literal["start", "anywhere"]


def extract_timestamp(line: str, formats: list[TimestampFormat]) -> datetime | None:
    """Prueba cada formato contra la linea, devuelve el primer datetime parseado."""
    for fmt in formats:
        match = fmt.regex.match(line) if fmt.position == "start" else fmt.regex.search(line)
        if match:
            ts_str = match.group(0)
            if fmt.name == "epoch-ms":
                try:
                    return datetime.fromtimestamp(int(ts_str) / 1000)
                except (ValueError, OSError):
                    continue
            try:
                return datetime.strptime(ts_str, fmt.format_str)
            except ValueError:
                continue
    return None


def detect_format(lines: list[str]) -> TimestampFormat | None:
    """Auto-detecta el formato de timestamp analizando las primeras lineas."""
    best: tuple[TimestampFormat, int] | None = None
    for fmt in ALL_FORMATS:
        hits = sum(1 for line in lines if extract_timestamp(line, [fmt]) is not None)
        if hits > len(lines) * 0.5:
            if best is None or hits > best[1]:
                best = (fmt, hits)
    return best[0] if best else None


# ── Formatos predefinidos ────────────────────────────────────────────

ISO8601 = TimestampFormat(
    name="iso8601",
    regex=compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{3,6})?(?:[+-]\d{2}:?\d{2}|Z)?"),
    format_str="%Y-%m-%d %H:%M:%S.%f",
    position="anywhere",
)

ISO8601_T = TimestampFormat(
    name="iso8601-t",
    regex=compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3,6})?(?:[+-]\d{2}:?\d{2}|Z)?"),
    format_str="%Y-%m-%dT%H:%M:%S.%f",
    position="anywhere",
)

SYSLOG = TimestampFormat(
    name="syslog",
    regex=compile(r"[A-Z][a-z]{2} \d{1,2} \d{2}:\d{2}:\d{2}"),
    format_str="%b %d %H:%M:%S",
    position="anywhere",
)

NGINX = TimestampFormat(
    name="nginx",
    regex=compile(r"\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4}"),
    format_str="%d/%b/%Y:%H:%M:%S %z",
    position="anywhere",
)

EPOCH_MS = TimestampFormat(
    name="epoch-ms",
    regex=compile(r"\b\d{13}\b"),
    format_str="",
    position="anywhere",
)

BUILTIN_FORMATS: dict[str, TimestampFormat] = {
    "iso8601": ISO8601,
    "iso8601-t": ISO8601_T,
    "syslog": SYSLOG,
    "nginx": NGINX,
    "epoch-ms": EPOCH_MS,
}

ALL_FORMATS: list[TimestampFormat] = list(BUILTIN_FORMATS.values())
