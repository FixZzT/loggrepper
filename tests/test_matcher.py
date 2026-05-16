from re import compile
from loggrepper.matcher import match_lines, exclude_lines
from loggrepper.models import LogLine


def test_match_lines_finds_pattern():
    pattern = compile(r"ERROR")
    lines = iter([LogLine(1, "INFO: ok"), LogLine(2, "ERROR: timeout")])
    result = list(match_lines(lines, [pattern]))
    assert result[0] == (LogLine(1, "INFO: ok"), False)
    assert result[1] == (LogLine(2, "ERROR: timeout"), True)


def test_match_lines_no_match():
    pattern = compile(r"ERROR")
    lines = iter([LogLine(1, "todo bien"), LogLine(2, "todo ok")])
    result = list(match_lines(lines, [pattern]))
    assert all(not matched for _, matched in result)


def test_match_lines_multi_pattern():
    patterns = [compile(r"ERROR"), compile(r"FATAL")]
    lines = iter([
        LogLine(1, "INFO: ok"),
        LogLine(2, "ERROR: timeout"),
        LogLine(3, "FATAL: crash"),
        LogLine(4, "DEBUG: normal"),
    ])
    result = list(match_lines(lines, patterns))
    assert result[0][1] is False
    assert result[1][1] is True
    assert result[2][1] is True
    assert result[3][1] is False


def test_exclude_lines_filters():
    exclude_pat = compile(r"DEBUG")
    items = iter([
        (LogLine(1, "DEBUG: verbose"), True),
        (LogLine(2, "ERROR: real"), True),
        (LogLine(3, "DEBUG: noisy"), False),
        (LogLine(4, "INFO: important"), False),
    ])
    result = list(exclude_lines(items, exclude_pat))
    assert len(result) == 2
    assert result[0][0].raw == "ERROR: real"
    assert result[1][0].raw == "INFO: important"
