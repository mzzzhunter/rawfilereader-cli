import json

import pytest
from click.testing import CliRunner

from rawfilereader_cli.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_file_info(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["file", "info", "--file", raw_path])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "file_info" in data
    assert "run_header" in data
    assert data["file_info"]["name"] == "sample.raw"


def test_file_scan_range(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["file", "scan_range", "--file", raw_path])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["first_scan"] == 1
    assert data["last_scan"] == 100


def test_file_instrument(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["file", "instrument", "--file", raw_path])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["count"] == 1
    assert "instrument_info" in data


def test_file_filters(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["file", "filters", "--file", raw_path])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data["filters"], list)
    assert len(data["filters"]) == 1


def test_file_method(mock_adapter, runner):
    adapter, raw_path = mock_adapter
    result = runner.invoke(cli, ["file", "method", "--file", raw_path])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == {
        "MS": "MS method text",
        "LC": "LC method text",
    }
    adapter.get_all_instrument_names_from_method.assert_called_once_with()
    assert adapter.get_instrument_method.call_count == 2
    adapter.get_instrument_method.assert_any_call(index=0)
    adapter.get_instrument_method.assert_any_call(index=1)


def test_file_method_deduplicates_device_names(mock_adapter, runner):
    adapter, raw_path = mock_adapter
    adapter.get_all_instrument_names_from_method.return_value = ["MS", "MS"]
    adapter.get_instrument_method.side_effect = lambda index=0: [
        "first MS method",
        "second MS method",
    ][index]

    result = runner.invoke(cli, ["file", "method", "--file", raw_path])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == {
        "MS": "first MS method",
        "MS (2)": "second MS method",
    }


def test_file_chromatogram(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["file", "chromatogram", "--file", raw_path, "--trace_type", "BasePeak"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "times" in data
    assert "intensities" in data


def test_file_chromatogram_with_rt(mock_adapter, runner):
    adapter, raw_path = mock_adapter
    result = runner.invoke(cli, [
        "file", "chromatogram", "--file", raw_path,
        "--start_rt", "1.0", "--end_rt", "5.0",
    ])
    assert result.exit_code == 0
    adapter.scan_number_from_retention_time.assert_called()


def test_file_chromatogram_peaks(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["file", "chromatogram_peaks", "--file", raw_path, "--smooth_window", "3"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "peaks" in data
    assert "peak_count" in data
    assert "times" in data
    assert "smoothed_intensities" in data
    assert data["smooth_window"] == 3
    assert data["min_height"] == 0.0
    # peaks should be sorted by intensity descending
    intensities = [p["intensity"] for p in data["peaks"]]
    assert intensities == sorted(intensities, reverse=True)


def test_file_chromatogram_peaks_min_height(mock_adapter, runner):
    _, raw_path = mock_adapter
    # use a very high threshold — should produce zero peaks
    result = runner.invoke(cli, [
        "file", "chromatogram_peaks", "--file", raw_path,
        "--smooth_window", "3", "--min_height", "1e99",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["peak_count"] == 0
    assert data["peaks"] == []
    assert data["min_height"] == 1e99


def test_indent_option(mock_adapter, runner):
    _, raw_path = mock_adapter
    result = runner.invoke(cli, ["--indent", "2", "file", "scan_range", "--file", raw_path])
    assert result.exit_code == 0
    assert "\n" in result.output
