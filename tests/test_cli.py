import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from loggrepper.cli import main


def _write_log(path: Path, content: str) -> None:
    path.write_text(content)


class TestBasic:
    def test_finds_match(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-05-16 14:31:58.100 INFO  antes\n")
            f.write("2026-05-16 14:32:01.123 ERROR timeout\n")
            f.write("2026-05-16 14:32:02.000 DEBUG despues\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", f.name, "-w", "3"])
        assert result.exit_code == 0
        assert "Incidente #1" in result.output
        assert "ERROR timeout" in result.output

    def test_no_match(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-05-16 14:32:01.123 INFO todo ok\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", f.name])
        assert result.exit_code == 0
        assert "Sin incidentes" in result.output

    def test_multi_pattern(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-05-16 14:31:58.100 INFO  antes\n")
            f.write("2026-05-16 14:32:01.123 ERROR timeout\n")
            f.write("2026-05-16 14:32:02.000 FATAL crash\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", "FATAL", f.name, "-w", "3"])
        assert result.exit_code == 0
        assert "timeout" in result.output
        assert "crash" in result.output

    def test_exclude(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-05-16 14:31:58.100 DEBUG heartbeat\n")
            f.write("2026-05-16 14:32:01.123 ERROR timeout\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", f.name, "-w", "3", "-e", "heartbeat"])
        assert result.exit_code == 0
        assert "timeout" in result.output

    def test_max_incidents(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-05-16 14:32:01.123 ERROR first\n")
            f.write("2026-05-16 14:32:10.123 ERROR second\n")
            f.write("2026-05-16 14:32:20.123 ERROR third\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", f.name, "-w", "1", "-n", "2"])
        assert result.exit_code == 0
        assert "Incidente #1" in result.output
        assert "Incidente #2" in result.output
        assert "Incidente #3" not in result.output


class TestOutputFormats:
    def test_json_output(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-05-16 14:32:01.123 ERROR timeout\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", f.name, "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["id"] == 1

    def test_ndjson_output(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-05-16 14:32:01.123 ERROR first\n")
            f.write("2026-05-16 14:32:10.123 ERROR second\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", f.name, "-o", "ndjson"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            data = json.loads(line)
            assert "id" in data

    def test_stats_output(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-05-16 14:32:01.123 ERROR timeout\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", f.name, "-o", "stats"])
        assert result.exit_code == 0
        assert "Incidentes encontrados" in result.output


class TestNoColor:
    def test_no_color_flag(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-05-16 14:32:01.123 ERROR timeout\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", f.name, "--no-color"])
        assert result.exit_code == 0
        assert "bold red" not in result.output
        assert ">>>" in result.output


class TestVersion:
    def test_version_flag(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "loggrepper" in result.output


class TestTimestampFormat:
    def test_syslog_format(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("May 16 14:32:01 hostname ERROR: timeout\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", f.name, "--ts-format", "syslog", "-w", "3"])
        assert result.exit_code == 0
        assert "Incidente #1" in result.output

    def test_nginx_format(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write('16/May/2026:14:32:01 +0000 GET /admin\n')
            f.flush()
            result = runner.invoke(main, ["GET", f.name, "--ts-format", "nginx", "-w", "3"])
        assert result.exit_code == 0
        assert "Incidente #1" in result.output

    def test_epoch_ms_format(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("1715872321123 ERROR timeout\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", f.name, "--ts-format", "epoch-ms", "-w", "3"])
        assert result.exit_code == 0
        assert "Incidente #1" in result.output


class TestErrors:
    def test_file_not_found(self):
        runner = CliRunner()
        result = runner.invoke(main, ["ERROR", "/nonexistent/path.log"])
        assert result.exit_code != 0

    def test_invalid_ts_format(self):
        runner = CliRunner()
        result = runner.invoke(main, ["ERROR", "/tmp/test.log", "--ts-format", "invalid_xyz"])
        assert result.exit_code != 0

    def test_stdin_auto_fails(self):
        runner = CliRunner()
        result = runner.invoke(main, ["ERROR", "-", "--ts-format", "auto"], input="")
        assert result.exit_code != 0

    def test_stdin_with_explicit_format(self):
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["ERROR", "-", "--ts-format", "iso8601", "-w", "3"],
            input="2026-05-16 14:32:01.123 ERROR timeout\n",
        )
        assert result.exit_code == 0
        assert "Incidente #1" in result.output


class TestBeforeAfter:
    def test_asymmetric_window_cli(self):
        runner = CliRunner()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("2026-05-16 14:31:55.100 INFO  muy antes\n")
            f.write("2026-05-16 14:31:59.100 INFO  justo antes\n")
            f.write("2026-05-16 14:32:01.123 ERROR timeout\n")
            f.write("2026-05-16 14:32:02.000 DEBUG justo despues\n")
            f.write("2026-05-16 14:32:05.000 DEBUG muy despues\n")
            f.flush()
            result = runner.invoke(main, ["ERROR", f.name, "-w", "5", "--before", "2"])
        assert result.exit_code == 0
        assert "Incidente #1" in result.output
        assert "justo antes" in result.output
        assert "muy antes" not in result.output
