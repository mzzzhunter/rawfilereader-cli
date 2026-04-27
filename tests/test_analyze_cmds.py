import json

import pytest
from click.testing import CliRunner

from rawfilereader_cli.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_analyze_summary(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["analyze", "summary", "--file", raw_path])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "summary" in data
    assert data["summary"]["MS1"] == 30


def test_analyze_average_scans(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, [
        "analyze", "average_scans", "--file", raw_path,
        "--first_scan", "1", "--last_scan", "5",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["first_scan"] == 1
    assert data["last_scan"] == 5
    assert "masses" in data
    assert data["point_count"] == 2


def test_analyze_average_scans_with_filter(mock_adapter, runner):
    adapter, raw_path = mock_adapter
    result = runner.invoke(cli, [
        "analyze", "average_scans", "--file", raw_path,
        "--first_scan", "1", "--last_scan", "10", "--filter_string", "Full ms",
    ])
    assert result.exit_code == 0
    adapter.average_scans_in_range.assert_called_with(1, 10, filter_string="Full ms")


def test_analyze_scan_info_range_array(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["analyze", "scan_info_range", "--file", raw_path])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "scans" in data
    assert data["count"] == 2


def test_analyze_scan_info_range_stream(mock_adapter, runner):
    adapter, raw_path = mock_adapter
    from tests.conftest import _ScanInfo
    import dataclasses
    adapter.iter_scan_info.return_value = iter([_ScanInfo(scan_number=1), _ScanInfo(scan_number=2)])
    result = runner.invoke(cli, ["analyze", "scan_info_range", "--file", raw_path, "--stream"])
    assert result.exit_code == 0
    lines = [l for l in result.output.strip().splitlines() if l]
    assert len(lines) == 2
    assert json.loads(lines[0])["scan_number"] == 1
