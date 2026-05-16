from re import compile
from loggrepper.matcher import match_lines
from loggrepper.models import LogLine

def test_match_lines_finds_pattern():
    pattern = compile(r"ERROR")
    lines = iter([LogLine(1,"INFO: ok"), LogLine(2,"ERROR: timeout")])
    result = list(match_lines(lines, [pattern]))
    assert result[0] == (LogLine(1,"INFO: ok"), False)
    assert result[1] == (LogLine(2,"ERROR: timeout"), True)

def test_match_lines_no_match():
    pattern = compile(r"ERROR")
    lines = iter([LogLine(1,"todo bien"), LogLine(2, "todo ok")])
    result = list(match_lines(lines, [pattern]))
    assert all(not matched for _, matched in result)