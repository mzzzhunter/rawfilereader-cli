import dataclasses

import click
import numpy as np

from rawfilereader_cli.errors import handle_raw_errors
from rawfilereader_cli.serialization import emit_json

try:
    from rawfilereader import RawFileAdapter
except ImportError:
    RawFileAdapter = None


@click.group("file")
def file_group():
    """File-level metadata and chromatogram commands."""


@file_group.command("info")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.pass_context
def info(ctx, file_path):
    """File metadata and run header summary."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            result = {
                "file_info": dataclasses.asdict(adapter.get_file_info()),
                "run_header": dataclasses.asdict(adapter.get_run_header_info()),
            }
            emit_json(result, indent=ctx.obj.get("indent"))


@file_group.command("scan_range")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.pass_context
def scan_range(ctx, file_path):
    """First and last scan number in the file."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            first, last = adapter.get_scan_range()
            emit_json({"first_scan": first, "last_scan": last}, indent=ctx.obj.get("indent"))


@file_group.command("instrument")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.pass_context
def instrument(ctx, file_path):
    """Instrument count and metadata."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            result = {
                "count": adapter.get_instrument_count(),
                "instrument_info": dataclasses.asdict(adapter.get_instrument_data()),
            }
            emit_json(result, indent=ctx.obj.get("indent"))


def _unique_method_device_key(name, index, seen):
    """Return a stable JSON object key for a method device name."""
    base = str(name) if name else f"device_{index}"
    count = seen.get(base, 0)
    seen[base] = count + 1
    if count == 0:
        return base
    return f"{base} ({count + 1})"


@file_group.command("method")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.pass_context
def method(ctx, file_path):
    """Instrument method strings keyed by device name."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            device_names = adapter.get_all_instrument_names_from_method()
            seen = {}
            result = {}
            for index, device_name in enumerate(device_names):
                key = _unique_method_device_key(device_name, index, seen)
                result[key] = adapter.get_instrument_method(index=index)
            emit_json(result, indent=ctx.obj.get("indent"))


@file_group.command("filters")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.pass_context
def filters(ctx, file_path):
    """All unique scan filter strings in the file."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            emit_json({"filters": adapter.get_filters()}, indent=ctx.obj.get("indent"))


def _resolve_scan_bounds(adapter, start_scan, end_scan, start_rt, end_rt, filter_string):
    """Resolve scan bounds from RT, filter_string, or direct scan number inputs."""
    if filter_string:
        scan_nums = adapter.get_filtered_scan_numbers(filter_string)
        if scan_nums:
            if start_scan == -1:
                start_scan = min(scan_nums)
            if end_scan == -1:
                end_scan = max(scan_nums)

    if start_rt is not None:
        start_scan = adapter.scan_number_from_retention_time(start_rt)
    if end_rt is not None:
        end_scan = adapter.scan_number_from_retention_time(end_rt)

    return start_scan, end_scan


def _chromatogram_options(f):
    f = click.option("--trace_type", default="BasePeak", show_default=True,
                     help="Chromatogram trace type (BasePeak, TIC, SIC, ...)")(f)
    f = click.option("--filter_string", default=None,
                     help="Thermo filter string to narrow scan range")(f)
    f = click.option("--mass_range", default="", show_default=True,
                     help="Mass range string for SIC (e.g. '500.0-510.0')")(f)
    f = click.option("--start_scan", default=-1, show_default=True, type=int,
                     help="First scan number (-1 = file start)")(f)
    f = click.option("--end_scan", default=-1, show_default=True, type=int,
                     help="Last scan number (-1 = file end)")(f)
    f = click.option("--start_rt", default=None, type=float,
                     help="Start retention time in minutes (overrides --start_scan)")(f)
    f = click.option("--end_rt", default=None, type=float,
                     help="End retention time in minutes (overrides --end_scan)")(f)
    return f


@file_group.command("chromatogram")
@_chromatogram_options
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.pass_context
def chromatogram(ctx, file_path, trace_type, filter_string, mass_range,
                 start_scan, end_scan, start_rt, end_rt):
    """Extract a chromatogram trace."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            start_scan, end_scan = _resolve_scan_bounds(
                adapter, start_scan, end_scan, start_rt, end_rt, filter_string
            )
            data = adapter.get_chromatogram(
                trace_type=trace_type,
                mass_range=mass_range,
                start_scan=start_scan,
                end_scan=end_scan,
            )
            result = dataclasses.asdict(data)
            emit_json(result, indent=ctx.obj.get("indent"))


@file_group.command("chromatogram_peaks")
@_chromatogram_options
@click.option("--smooth_window", default=5, show_default=True, type=int,
              help="Moving average smoothing window size")
@click.option("--min_height", default=0.0, show_default=True, type=float,
              help="Minimum peak intensity to include (e.g. 1e5). 0 = no filter.")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.pass_context
def chromatogram_peaks(ctx, file_path, trace_type, filter_string, mass_range,
                       start_scan, end_scan, start_rt, end_rt, smooth_window, min_height):
    """Extract chromatogram and detect peaks using moving average smoothing."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            start_scan, end_scan = _resolve_scan_bounds(
                adapter, start_scan, end_scan, start_rt, end_rt, filter_string
            )
            data = adapter.get_chromatogram(
                trace_type=trace_type,
                mass_range=mass_range,
                start_scan=start_scan,
                end_scan=end_scan,
            )

            times = np.asarray(data.times, dtype=float)
            intensities = np.asarray(data.intensities, dtype=float)

            if smooth_window > 1 and len(intensities) >= smooth_window:
                kernel = np.ones(smooth_window) / smooth_window
                smoothed = np.convolve(intensities, kernel, mode="same")
            else:
                smoothed = intensities.copy()

            peaks = []
            for i in range(1, len(smoothed) - 1):
                if smoothed[i] > smoothed[i - 1] and smoothed[i] > smoothed[i + 1]:
                    if intensities[i] >= min_height:
                        peaks.append({
                            "index": i,
                            "retention_time": float(times[i]),
                            "intensity": float(intensities[i]),
                            "smoothed_intensity": float(smoothed[i]),
                        })

            peaks.sort(key=lambda p: p["intensity"], reverse=True)

            emit_json(
                {
                    "trace_type": trace_type,
                    "smooth_window": smooth_window,
                    "min_height": min_height,
                    "times": times.tolist(),
                    "smoothed_intensities": smoothed.tolist(),
                    "peaks": peaks,
                    "peak_count": len(peaks),
                },
                indent=ctx.obj.get("indent"),
            )
