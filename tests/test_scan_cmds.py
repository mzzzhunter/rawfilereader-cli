import json

import pytest
from click.testing import CliRunner

from rawfilereader_cli.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_scan_info_single(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["scan", "info", "--file", raw_path, "--scan_number", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["scan_number"] == 1
    assert "filter" in data
    assert "ms_order" in data


def test_scan_info_iter_array(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["scan", "info", "--file", raw_path, "--ms_order", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 2


def test_scan_info_iter_stream(mock_adapter, runner):
    adapter, raw_path = mock_adapter
    # reset the iterator for stream call
    import dataclasses
    from tests.conftest import _ScanInfo
    adapter.iter_scan_info.return_value = iter([_ScanInfo(scan_number=1), _ScanInfo(scan_number=2)])
    result = runner.invoke(cli, ["scan", "info", "--file", raw_path, "--ms_order", "1", "--stream"])
    assert result.exit_code == 0
    lines = [l for l in result.output.strip().splitlines() if l]
    assert len(lines) == 2
    assert json.loads(lines[0])["scan_number"] == 1


def test_scan_info_requires_arg(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["scan", "info", "--file", raw_path])
    assert result.exit_code != 0


def test_scan_stats(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["scan", "stats", "--file", raw_path, "--scan_number", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "tic" in data


def test_scan_spectrum(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["scan", "spectrum", "--file", raw_path, "--scan_number", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "masses" in data
    assert "intensities" in data
    assert data["scan_number"] == 1


def test_scan_spectrum_max_points(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["scan", "spectrum", "--file", raw_path, "--scan_number", "1", "--max_points", "2"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["masses"]) == 2
    assert data["truncated"] is True
    assert data["point_count"] == 3


def test_scan_spectrum_omit_arrays(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["scan", "spectrum", "--file", raw_path, "--scan_number", "1", "--max_points", "-1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["masses"] is None
    assert data["point_count"] == 3


def test_scan_profile(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["scan", "profile", "--file", raw_path, "--scan_number", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "masses" in data
    assert "intensities" in data


def test_scan_filter(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["scan", "filter", "--file", raw_path, "--scan_number", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "filter" in data
    assert data["scan_number"] == 1


def test_scan_trailer(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["scan", "trailer", "--file", raw_path, "--scan_number", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "fields" in data


def test_scan_dependents(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["scan", "dependents", "--file", raw_path, "--scan_number", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "dependent_scan_numbers" in data
