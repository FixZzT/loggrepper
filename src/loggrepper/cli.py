import bz2
import gzip
import lzma
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


def _read_stream(file: str) -> tuple[TextIO, bool]:
    """Devuelve (stream, should_close). Soporta stdin y archivos comprimidos."""
    if file == "-":
        return sys.stdin, False
    if file.endswith(".gz"):
        return gzip.open(file, "rt"), True
    if file.endswith(".bz2"):
        return bz2.open(file, "rt"), True
    if file.endswith(".xz"):
        return lzma.open(file, "rt"), True
    return open(file), True  # noqa: SIM115


def _iter_lines(
    stream: TextIO, follow: bool, idle_timeout: int | None = None
) -> Iterator[str]:
    """Generador de lineas. En modo follow espera nuevas lineas. idle_timeout sale tras N segundos sin datos."""
    last_line_at = time.monotonic()
    while True:
        line = stream.readline()
        if line:
            yield line.rstrip("\n")
            last_line_at = time.monotonic()
        elif follow:
            if idle_timeout is not None and time.monotonic() - last_line_at > idle_timeout:
                break
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
@click.version_option(version="0.3.0", package_name="loggrepper")
@click.argument("patterns", nargs=-1, required=True)
@click.argument("file", type=click.Path())
@click.option("--window", "-w", default=3, type=int, help="Ventana en segundos alrededor del match")
@click.option(
    "--before", default=None, type=int,
    help="Segundos antes del match (sobrescribe --window para la ventana izquierda)",
)
@click.option(
    "--after", default=None, type=int,
    help="Segundos despues del match (sobrescribe --window para la ventana derecha)",
)
@click.option(
    "--ts-format", default="auto",
    help="Formato de timestamp (auto, iso8601, iso8601-t, syslog, nginx, epoch-ms)",
)
@click.option(
    "--output", "-o", default="pretty",
    type=click.Choice(["pretty", "json", "ndjson", "stats"]),
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
@click.option(
    "--idle-timeout", default=None, type=int,
    help="Salir tras N segundos sin nuevos matches (solo con --follow)",
)
@click.option(
    "--no-color", "color", is_flag=True, default=True,
    help="Desactivar colores en la salida",
)
def main(
    patterns: tuple[str, ...],
    file: str,
    window: int,
    before: int | None,
    after: int | None,
    ts_format: str,
    output: str,
    exclude: str | None,
    max_incidents: int | None,
    follow: bool,
    idle_timeout: int | None,
    color: bool,
) -> None:
    """Extrae ventanas de contexto alrededor de matches en archivos de log.

    Ejemplos:

        loggrepper ERROR app.log -w 5

        loggrepper ERROR FATAL app.log -o json

        docker logs mi-app | loggrepper panic -
    """
    # ── validar archivo ──────────────────────────────────────────────
    if file != "-" and not os.path.exists(file) and not any(
        file.endswith(ext) for ext in (".gz", ".bz2", ".xz")
    ):
        if not os.path.exists(file):
            raise click.BadParameter(f"Archivo no encontrado: {file}")

    # ── formato de timestamp ─────────────────────────────────────────
    if ts_format == "auto":
        if file == "-":
            raise click.UsageError(
                "--ts-format auto no funciona con stdin. Especifica un formato."
            )
        stream, should_close = _read_stream(file)
        try:
            head = [next(stream, "").rstrip("\n") for _ in range(50)]
        finally:
            if should_close:
                stream.close()
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

    # ── ventana temporal ─────────────────────────────────────────────
    before_td = timedelta(seconds=before if before is not None else window)
    after_td = timedelta(seconds=after if after is not None else window)

    formatter = get_formatter(output, color=color)

    # ── procesar ─────────────────────────────────────────────────────
    stream, should_close = _read_stream(file)
    try:
        raw_lines = (
            LogLine(number=i, raw=line)
            for i, line in enumerate(_iter_lines(stream, follow, idle_timeout), 1)
        )
        timestamped = _timestamped_lines(raw_lines, fmt, compiled_patterns, exclude_pat)
        incidents = group_incidents(timestamped, before_td, after_td)

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

        flushed = formatter.flush()
        if flushed:
            console.print(flushed)
    finally:
        if should_close:
            stream.close()


if __name__ == "__main__":
    main()
