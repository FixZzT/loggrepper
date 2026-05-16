from re import compile
from datetime import datetime
from loggrepper.timestamp import TimestampFormat, extract_timestamp, detect_format

ISO_FORMAT = TimestampFormat(
    name="iso8601",
    regex=compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}"),
    format_str="%Y-%m-%d %H:%M:%S.%f",
    position="start",
)


def test_extract_timestamp_start():
    ts = extract_timestamp("2026-05-16 14:32:01.123 ERROR: timeout", [ISO_FORMAT])
    assert ts == datetime(2026, 5, 16, 14, 32, 1, 123000)


def test_extract_timestamp_no_match():
    ts = extract_timestamp("sin timestamp aqui", [ISO_FORMAT])
    assert ts is None


def test_detect_format_iso8601():
    lines = [
        "2026-05-16 14:32:00.100 INFO  inicio",
        "2026-05-16 14:32:01.123 ERROR timeout",
        "2026-05-16 14:32:02.000 DEBUG fin",
    ]
    fmt = detect_format(lines)
    assert fmt is not None
    assert fmt.name in ("iso8601", "iso8601-t")


def test_detect_format_no_detect():
    lines = ["sin timestamp aqui", "tampoco esta linea"]
    fmt = detect_format(lines)
    assert fmt is None
