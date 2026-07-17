import dataclasses

import click

from rawfilereader_cli.errors import AssemblyLoadError, handle_raw_errors
from rawfilereader_cli.serialization import emit_json, to_json

try:
    from rawfilereader import RawFileAdapter
except ImportError as exc:
    _ADAPTER_IMPORT_ERROR = exc

    class RawFileAdapter:
        def __init__(self, *args, **kwargs):
            raise AssemblyLoadError(
                f"Unable to import rawfilereader/RawFileAdapter: {_ADAPTER_IMPORT_ERROR}"
            )


@click.group("analyze")
def analyze_group():
    """Aggregate analysis commands."""


@analyze_group.command("summary")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.pass_context
def summary(ctx, file_path):
    """Count scans by MS order across the entire file."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            emit_json({"summary": adapter.analyze_all_scans()}, indent=ctx.obj.get("indent"))


@analyze_group.command("average_scans")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--first_scan", required=True, type=int)
@click.option("--last_scan", required=True, type=int)
@click.option("--filter_string", default=None, help="Optional filter to restrict which scans are averaged")
@click.pass_context
def average_scans(ctx, file_path, first_scan, last_scan, filter_string):
    """Average spectra over a scan range, optionally filtered."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            data = adapter.average_scans_in_range(first_scan, last_scan, filter_string=filter_string)
            result = dataclasses.asdict(data)
            if "masses" in result and result["masses"] is not None:
                result["point_count"] = len(result["masses"])
            emit_json(result, indent=ctx.obj.get("indent"))


@analyze_group.command("scan_info_range")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--ms_order", default=None, type=int, help="Restrict to this MS order (default: all)")
@click.option("--stream", is_flag=True, default=False, help="Output one JSON object per line")
@click.pass_context
def scan_info_range(ctx, file_path, ms_order, stream):
    """Iterate scan info for all (or MS-order-filtered) scans in the file."""
    indent = ctx.obj.get("indent")
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            if stream:
                for si in adapter.iter_scan_info(ms_order=ms_order):
                    print(to_json(dataclasses.asdict(si)))
            else:
                scans = [dataclasses.asdict(si) for si in adapter.iter_scan_info(ms_order=ms_order)]
                emit_json({"scans": scans, "count": len(scans)}, indent=indent)
