"""Shared fixtures providing a fully mocked RawFileAdapter for unit tests."""
import dataclasses
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Minimal stub dataclasses mirroring the real adapter return types
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class _FileInfo:
    name: str = "sample.raw"
    creation_date: str = "2024-01-01"
    operator: str = "test"
    ms_orders: list = dataclasses.field(default_factory=lambda: [1, 2])


@dataclasses.dataclass
class _RunHeaderInfo:
    scan_range: tuple = (1, 100)
    time_range: tuple = (0.0, 10.0)
    mass_range: tuple = (100.0, 2000.0)
    counts: int = 100


@dataclasses.dataclass
class _InstrumentInfo:
    device_type: str = "MS"
    instance_number: int = 1
    name: str = "Orbitrap"
    model: str = "Orbitrap Fusion"
    serial_number: str = "SN-001"


@dataclasses.dataclass
class _ScanInfo:
    scan_number: int = 1
    filter: str = "FTMS + p NSI Full ms [400.00-1600.00]"
    ms_order: int = 1
    retention_time: float = 0.5
    injection_time: float = 50.0
    centroid_flag: bool = True
    detector_type: str = "FTMS"
    activation_type: str = None
    precursor_mz: float = None
    precursor_charge: int = None


@dataclasses.dataclass
class _ScanStats:
    scan_number: int = 1
    start_time: float = 0.5
    mass_range: tuple = (100.0, 2000.0)
    tic: float = 1e8
    base_peak_mass: float = 500.0
    base_peak_intensity: float = 5e7
    centroid_flag: bool = True


@dataclasses.dataclass
class _CentroidData:
    masses: list = dataclasses.field(default_factory=lambda: [400.0, 500.0, 600.0])
    intensities: list = dataclasses.field(default_factory=lambda: [1000.0, 2000.0, 1500.0])
    charges: list = dataclasses.field(default_factory=lambda: [1, 1, 1])
    baselines: list = dataclasses.field(default_factory=lambda: [10.0, 10.0, 10.0])
    noises: list = dataclasses.field(default_factory=lambda: [5.0, 5.0, 5.0])
    resolutions: list = dataclasses.field(default_factory=lambda: [60000.0, 60000.0, 60000.0])


@dataclasses.dataclass
class _ProfileData:
    masses: list = dataclasses.field(default_factory=lambda: [400.0, 401.0, 402.0])
    intensities: list = dataclasses.field(default_factory=lambda: [500.0, 800.0, 400.0])


@dataclasses.dataclass
class _TrailerData:
    scan_number: int = 1
    fields: dict = dataclasses.field(default_factory=lambda: {"Charge State": "2"})


@dataclasses.dataclass
class _ScanDependent:
    scan_number: int = 1
    dependent_scan_numbers: list = dataclasses.field(default_factory=lambda: [2, 3])


@dataclasses.dataclass
class _ChromatogramData:
    trace_type: str = "BasePeak"
    mass_range: str = ""
    times: list = dataclasses.field(default_factory=lambda: [0.1, 0.2, 0.3, 0.4, 0.5])
    intensities: list = dataclasses.field(default_factory=lambda: [100.0, 500.0, 300.0, 800.0, 200.0])


@dataclasses.dataclass
class _AveragedScan:
    first_scan: int = 1
    last_scan: int = 5
    masses: list = dataclasses.field(default_factory=lambda: [400.0, 500.0])
    intensities: list = dataclasses.field(default_factory=lambda: [1500.0, 2500.0])


# ---------------------------------------------------------------------------
# Mock adapter factory
# ---------------------------------------------------------------------------

def _make_mock_adapter():
    adapter = MagicMock()
    adapter.__enter__ = MagicMock(return_value=adapter)
    adapter.__exit__ = MagicMock(return_value=False)

    adapter.get_file_info.return_value = _FileInfo()
    adapter.get_run_header_info.return_value = _RunHeaderInfo()
    adapter.get_scan_range.return_value = (1, 100)
    adapter.get_instrument_count.return_value = 1
    adapter.get_instrument_data.return_value = _InstrumentInfo()
    adapter.get_all_instrument_names_from_method.return_value = ["MS", "LC"]
    adapter.get_instrument_method.side_effect = lambda index=0: [
        "MS method text",
        "LC method text",
    ][index]
    adapter.get_filters.return_value = ["FTMS + p NSI Full ms [400.00-1600.00]"]
    adapter.get_scan_info.return_value = _ScanInfo()
    adapter.iter_scan_info.return_value = iter([_ScanInfo(scan_number=1), _ScanInfo(scan_number=2)])
    adapter.get_scan_stats.return_value = _ScanStats()
    adapter.get_centroid_stream.return_value = _CentroidData()
    adapter.get_profile_data.return_value = _ProfileData()
    adapter.get_filter_for_scan.return_value = "FTMS + p NSI Full ms [400.00-1600.00]"
    adapter.get_trailer_data.return_value = _TrailerData()
    adapter.get_scan_dependents.return_value = _ScanDependent()
    adapter.get_chromatogram.return_value = _ChromatogramData()
    adapter.get_filtered_scan_numbers.return_value = [1, 5, 9]
    adapter.iterate_filtered_scans.return_value = iter([1, 5, 9])
    adapter.scan_number_from_retention_time.return_value = 42
    adapter.get_retention_time.return_value = 1.23
    adapter.analyze_all_scans.return_value = {"MS1": 30, "MS2": 70}
    adapter.average_scans_in_range.return_value = _AveragedScan()

    return adapter


@pytest.fixture
def mock_adapter(tmp_path):
    """A fully mocked RawFileAdapter. Patches all command modules simultaneously."""
    fake_raw = tmp_path / "fake.raw"
    fake_raw.write_bytes(b"")
    adapter = _make_mock_adapter()

    targets = [
        "rawfilereader_cli.commands.file_cmds.RawFileAdapter",
        "rawfilereader_cli.commands.scan_cmds.RawFileAdapter",
        "rawfilereader_cli.commands.search_cmds.RawFileAdapter",
        "rawfilereader_cli.commands.analyze_cmds.RawFileAdapter",
    ]
    patchers = [patch(t, return_value=adapter) for t in targets]
    for p in patchers:
        p.start()

    yield adapter, str(fake_raw)

    for p in patchers:
        p.stop()
