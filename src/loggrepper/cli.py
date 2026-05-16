import os
import sys
import time
from collections.abc import Iterator
from datetime import datetime, timedelta
from re import Pattern, compile
from typing import TextIO

import click
from rich.console import Console

from loggrepper.formatter import get_formatter
from loggrepper.grouper import group_incidents
from loggrepper.models import LogLine
from loggrepper.timestamp import BUILTIN_FORMATS, TimestampFormat, detect_format, extract_timestamp

console = Console(highlight=False)


def _read_stream(file: str, follow: bool) -> TextIO:
    """Devuelve el stream de entrada. Soporta '-' para stdin."""
    if file == "-":
        return sys.stdin
    return open(file)  # noqa: SIM115 — se cierra al salir del proceso


def _iter_lines(stream: TextIO, follow: bool) -> Iterator[str]:
    """Generador de lineas. En modo follow espera nuevas lineas indefinidamente."""
    while True:
        line = stream.readline()
        if line:
            yield line.rstrip("\n")
        elif follow:
            time.sleep(0.1)
        else:
            break


def _timestamped_lines(
    raw_lines: Iterator[LogLine],
    fmt: TimestampFormat,
    patterns: list[Pattern[str]],
    exclude_pat: Pattern[str] | None,
) -> Iterator[tuple[LogLine, datetime, bool]]:
    """Convierte lineas raw en tuplas (LogLine, datetime, matched) aplicando filtros."""
    skipped = 0
    for logline in raw_lines:
        ts = extract_timestamp(logline.raw, [fmt])
        if ts is None:
            skipped += 1
            continue
        if exclude_pat is not None and exclude_pat.search(logline.raw):
            continue
        matched = any(p.search(logline.raw) for p in patterns)
        yield logline, ts, matched
    if skipped:
        click.echo(f"Lineas sin timestamp detectado: {skipped}", err=True)


@click.command()
@click.argument("patterns", nargs=-1, required=True)
@click.argument("file", type=click.Path())
@click.option("--window", "-w", default=3, help="Ventana en segundos alrededor del match")
@click.option(
    "--ts-format", default="auto",
    help="Formato de timestamp (auto, iso8601, iso8601-t, syslog, nginx, epoch-ms)",
)
@click.option(
    "--output", "-o", default="pretty",
    type=click.Choice(["pretty", "json", "stats"]),
    help="Formato de salida",
)
@click.option("--exclude", "-e", default=None, help="Patron regex para excluir lineas")
@click.option(
    "--max-incidents", "-n", default=None, type=int,
    help="Maximo de incidentes a mostrar",
)
@click.option(
    "--follow", "-f", is_flag=True, default=False,
    help="Seguir leyendo nuevas lineas (como tail -f)",
)
def main(
    patterns: tuple[str, ...],
    file: str,
    window: int,
    ts_format: str,
    output: str,
    exclude: str | None,
    max_incidents: int | None,
    follow: bool,
) -> None:
    """Extrae ventanas de contexto alrededor de matches en archivos de log.

    Ejemplos:

        loggrepper ERROR app.log -w 5

        loggrepper ERROR FATAL app.log -o json

        docker logs mi-app | loggrepper panic -
    """
    # ── validar archivo ──────────────────────────────────────────────
    if file != "-" and not os.path.exists(file):
        raise click.BadParameter(f"Archivo no encontrado: {file}")

    # ── formato de timestamp ─────────────────────────────────────────
    if ts_format == "auto":
        if file == "-":
            raise click.UsageError(
                "--ts-format auto no funciona con stdin. Especifica un formato."
            )
        with open(file) as f:
            head = [next(f, "").rstrip("\n") for _ in range(50)]
            head = [line for line in head if line]
        fmt = detect_format(head)
        if fmt is None:
            raise click.UsageError(
                "No se pudo detectar el formato de timestamp. "
                "Usa --ts-format para especificar uno."
            )
        click.echo(f"Formato detectado: {fmt.name}", err=True)
    else:
        fmt = BUILTIN_FORMATS.get(ts_format)
        if fmt is None:
            valid = ", ".join(BUILTIN_FORMATS.keys())
            raise click.BadParameter(f"Formato '{ts_format}' desconocido. Opciones: {valid}")

    # ── compilar patrones ────────────────────────────────────────────
    try:
        compiled_patterns = [compile(p) for p in patterns]
    except Exception as e:
        raise click.BadParameter(f"Patron regex invalido: {e}")

    exclude_pat = None
    if exclude is not None:
        try:
            exclude_pat = compile(exclude)
        except Exception as e:
            raise click.BadParameter(f"Patron exclude regex invalido: {e}")

    window_td = timedelta(seconds=window)
    formatter = get_formatter(output)

    # ── procesar ─────────────────────────────────────────────────────
    stream = _read_stream(file, follow)
    raw_lines = (
        LogLine(number=i, raw=line)
        for i, line in enumerate(_iter_lines(stream, follow), 1)
    )
    timestamped = _timestamped_lines(raw_lines, fmt, compiled_patterns, exclude_pat)
    incidents = group_incidents(timestamped, window_td)

    shown = 0
    for inc in incidents:
        if max_incidents is not None and shown >= max_incidents:
            break
        output_str = formatter.format_one(inc)
        if output_str:
            console.print(output_str)
        shown += 1

    if shown == 0:
        msg = formatter.format_empty()
        if msg:
            console.print(msg)

    # flush para formatos que acumulan (json, stats)
    flush_fn = getattr(formatter, "flush", None)
    if flush_fn is not None:
        flushed = flush_fn()
        if flushed:
            console.print(flushed)


if __name__ == "__main__":
    main()
