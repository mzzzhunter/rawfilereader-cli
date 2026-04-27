import dataclasses
import sys

import click

from rawfilereader_cli.errors import handle_raw_errors
from rawfilereader_cli.serialization import emit_json, to_json

try:
    from rawfilereader import RawFileAdapter
except ImportError:
    RawFileAdapter = None


@click.group("scan")
def scan_group():
    """Per-scan data retrieval commands."""


@scan_group.command("info")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--scan_number", default=None, type=int, help="Single scan number to retrieve")
@click.option("--ms_order", default=None, type=int, help="Iterate all scans of this MS order")
@click.option("--stream", is_flag=True, default=False, help="Output newline-delimited JSON instead of array")
@click.pass_context
def info(ctx, file_path, scan_number, ms_order, stream):
    """Scan metadata. Use --scan_number for one scan, --ms_order to iterate all scans of that order."""
    if scan_number is None and ms_order is None:
        raise click.UsageError("Provide --scan_number or --ms_order.")

    indent = ctx.obj.get("indent")
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            if scan_number is not None:
                result = dataclasses.asdict(adapter.get_scan_info(scan_number))
                emit_json(result, indent=indent)
            else:
                if stream:
                    for si in adapter.iter_scan_info(ms_order=ms_order):
                        print(to_json(dataclasses.asdict(si)))
                else:
                    results = [dataclasses.asdict(si) for si in adapter.iter_scan_info(ms_order=ms_order)]
                    emit_json(results, indent=indent)


@scan_group.command("stats")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--scan_number", required=True, type=int)
@click.pass_context
def stats(ctx, file_path, scan_number):
    """Scan statistics (TIC, base peak, mass range, etc.)."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            emit_json(dataclasses.asdict(adapter.get_scan_stats(scan_number)), indent=ctx.obj.get("indent"))


def _apply_max_points(data_dict, array_keys, max_points):
    """Truncate or nullify array fields based on --max_points."""
    truncated = False
    point_count = None

    for key in array_keys:
        arr = data_dict.get(key)
        if arr is None:
            continue
        if point_count is None:
            point_count = len(arr)
        if max_points == -1:
            data_dict[key] = None
        elif max_points > 0 and len(arr) > max_points:
            data_dict[key] = arr[:max_points]
            truncated = True

    if point_count is not None:
        data_dict["point_count"] = point_count
    if max_points != -1:
        data_dict["truncated"] = truncated
    return data_dict


@scan_group.command("spectrum")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--scan_number", required=True, type=int)
@click.option("--prefer_profile", is_flag=True, default=False, help="Prefer profile data if available")
@click.option("--max_points", default=0, type=int,
              help="Max array points to return. 0=all, -1=omit arrays, N=truncate to N")
@click.pass_context
def spectrum(ctx, file_path, scan_number, prefer_profile, max_points):
    """Centroid spectrum (masses + intensities) for a scan."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            data = adapter.get_centroid_stream(scan_number, prefer_profile_data=prefer_profile)
            result = dataclasses.asdict(data)
            result["scan_number"] = scan_number
            _apply_max_points(result, ["masses", "intensities", "charges", "baselines", "noises", "resolutions"], max_points)
            emit_json(result, indent=ctx.obj.get("indent"))


@scan_group.command("profile")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--scan_number", required=True, type=int)
@click.option("--max_points", default=0, type=int,
              help="Max array points to return. 0=all, -1=omit arrays, N=truncate to N")
@click.pass_context
def profile(ctx, file_path, scan_number, max_points):
    """Profile (continuous) spectrum for a scan."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            data = adapter.get_profile_data(scan_number)
            result = dataclasses.asdict(data)
            result["scan_number"] = scan_number
            _apply_max_points(result, ["masses", "intensities"], max_points)
            emit_json(result, indent=ctx.obj.get("indent"))


@scan_group.command("filter")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--scan_number", required=True, type=int)
@click.pass_context
def scan_filter(ctx, file_path, scan_number):
    """Thermo filter string for a specific scan."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            emit_json(
                {"scan_number": scan_number, "filter": adapter.get_filter_for_scan(scan_number)},
                indent=ctx.obj.get("indent"),
            )


@scan_group.command("trailer")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--scan_number", required=True, type=int)
@click.pass_context
def trailer(ctx, file_path, scan_number):
    """Trailer (auxiliary) data for a scan."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            data = adapter.get_trailer_data(scan_number)
            emit_json(dataclasses.asdict(data), indent=ctx.obj.get("indent"))


@scan_group.command("dependents")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--scan_number", required=True, type=int)
@click.option("--depth", default=1, show_default=True, type=int,
              help="Recursion depth for dependent scan lookup")
@click.pass_context
def dependents(ctx, file_path, scan_number, depth):
    """Parent-dependent scan hierarchy for a scan."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            data = adapter.get_scan_dependents(scan_number, depth=depth)
            emit_json(dataclasses.asdict(data), indent=ctx.obj.get("indent"))
