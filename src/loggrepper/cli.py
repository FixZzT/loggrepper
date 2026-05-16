from datetime import datetime, timedelta
from re import compile

import click

from loggrepper.models import LogLine
from loggrepper.timestamp import BUILTIN_FORMATS, detect_format, extract_timestamp
from loggrepper.grouper import group_incidents
from loggrepper.formatter import get_formatter


@click.command()
@click.argument("pattern")
@click.argument("file", type=click.Path(exists=True))
@click.option("--window", "-w", default=3, help="Ventana en segundos alrededor del match")
@click.option("--ts-format", default="auto", help="Formato de timestamp (auto, iso8601, syslog, nginx, epoch-ms)")
@click.option("--output", "-o", default="pretty", type=click.Choice(["pretty", "json"]), help="Formato de salida")
def main(pattern: str, file: str, window: int, ts_format: str, output: str) -> None:
    """Extrae ventanas de contexto alrededor de matches en archivos de log.

    Ejemplo: loggrepper ERROR app.log -w 5 --output json
    """
    # ── formato de timestamp ──────────────────────────────────────
    if ts_format == "auto":
        with open(file) as f:
            head = [next(f, "").rstrip("\n") for _ in range(50)]
            head = [l for l in head if l]
        fmt = detect_format(head)
        if fmt is None:
            raise click.UsageError(
                "No se pudo detectar el formato de timestamp. "
                "Usa --ts-format para especificar uno (iso8601, syslog, nginx, epoch-ms)."
            )
        click.echo(f"Formato detectado: {fmt.name}", err=True)
    else:
        fmt = BUILTIN_FORMATS.get(ts_format)
        if fmt is None:
            valid = ", ".join(BUILTIN_FORMATS.keys())
            raise click.BadParameter(f"Formato '{ts_format}' desconocido. Opciones: {valid}")

    # ── compilar patron de busqueda ───────────────────────────────
    try:
        pat = compile(pattern)
    except Exception as e:
        raise click.BadParameter(f"Patron regex invalido: {e}")

    window_td = timedelta(seconds=window)
    formatter = get_formatter(output)

    # ── procesar archivo ──────────────────────────────────────────
    with open(file) as f:
        raw_lines = (
            LogLine(number=i, raw=line.rstrip("\n"))
            for i, line in enumerate(f, 1)
        )

        timestamped: list[tuple[LogLine, datetime, bool]] = []
        skipped = 0
        for logline in raw_lines:
            ts = extract_timestamp(logline.raw, [fmt])
            if ts is None:
                skipped += 1
                continue
            matched = pat.search(logline.raw) is not None
            timestamped.append((logline, ts, matched))

    if skipped:
        click.echo(f"Lineas sin timestamp detectado: {skipped}", err=True)

    # ── agrupar y mostrar ─────────────────────────────────────────
    incidents = list(group_incidents(iter(timestamped), window_td))

    if not incidents:
        click.echo(formatter.format([]))
        return

    click.echo(formatter.format(incidents))
