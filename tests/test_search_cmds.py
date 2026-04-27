import json

import pytest
from click.testing import CliRunner

from rawfilereader_cli.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_search_by_filter(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, [
        "search", "by_filter", "--file", raw_path, "--filter_string", "Full ms",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["filter_string"] == "Full ms"
    assert data["scan_numbers"] == [1, 5, 9]
    assert data["count"] == 3


def test_search_by_filter_with_bounds(mock_adapter, runner):
    adapter, raw_path = mock_adapter
    result = runner.invoke(cli, [
        "search", "by_filter", "--file", raw_path, "--filter_string", "Full ms",
        "--start_scan", "1", "--end_scan", "50",
    ])
    assert result.exit_code == 0
    adapter.get_filtered_scan_numbers.assert_called_with("Full ms", start_scan=1, end_scan=50)


def test_search_by_rt(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, [
        "search", "by_rt", "--file", raw_path, "--retention_time", "1.5",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["scan_number"] == 42
    assert data["retention_time"] == 1.5


def test_search_rt_for_scan(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, [
        "search", "rt_for_scan", "--file", raw_path, "--scan_number", "42",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["scan_number"] == 42
    assert data["retention_time"] == 1.23


def test_search_iterate_filter_array(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, [
        "search", "iterate_filter", "--file", raw_path, "--filter_string", "Full ms",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["scan_numbers"] == [1, 5, 9]
    assert data["count"] == 3


def test_search_iterate_filter_stream(mock_adapter, runner):
    adapter, raw_path = mock_adapter
    adapter.iterate_filtered_scans.return_value = iter([1, 5, 9])
    result = runner.invoke(cli, [
        "search", "iterate_filter", "--file", raw_path, "--filter_string", "Full ms", "--stream",
    ])
    assert result.exit_code == 0
    lines = [l for l in result.output.strip().splitlines() if l]
    assert len(lines) == 3
    assert json.loads(lines[0])["scan_number"] == 1
