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


@click.group("search")
def search_group():
    """Scan number lookup and filtering commands."""


@search_group.command("by_filter")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--filter_string", required=True, help="Thermo scan filter string to match")
@click.option("--start_scan", default=None, type=int, help="First scan to search (default: file start)")
@click.option("--end_scan", default=None, type=int, help="Last scan to search (default: file end)")
@click.pass_context
def by_filter(ctx, file_path, filter_string, start_scan, end_scan):
    """Return all scan numbers matching a filter string."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            scan_numbers = adapter.get_filtered_scan_numbers(filter_string, start_scan=start_scan, end_scan=end_scan)
            emit_json({"filter_string": filter_string, "scan_numbers": scan_numbers, "count": len(scan_numbers)}, indent=ctx.obj.get("indent"))


@search_group.command("by_rt")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--retention_time", required=True, type=float, help="Retention time in minutes")
@click.pass_context
def by_rt(ctx, file_path, retention_time):
    """Find the scan number closest to a given retention time (minutes)."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            scan_number = adapter.scan_number_from_retention_time(retention_time)
            emit_json({"retention_time": retention_time, "scan_number": scan_number}, indent=ctx.obj.get("indent"))


@search_group.command("rt_for_scan")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--scan_number", required=True, type=int)
@click.pass_context
def rt_for_scan(ctx, file_path, scan_number):
    """Return the retention time (minutes) for a given scan number."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            rt = adapter.get_retention_time(scan_number)
            emit_json({"scan_number": scan_number, "retention_time": rt}, indent=ctx.obj.get("indent"))


@search_group.command("iterate_filter")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option("--filter_string", required=True, help="Thermo scan filter string to match")
@click.option("--start_time", default=None, type=float, help="Start retention time in minutes")
@click.option("--end_time", default=None, type=float, help="End retention time in minutes")
@click.option("--stream", is_flag=True, default=False, help="Output one JSON object per line")
@click.pass_context
def iterate_filter(ctx, file_path, filter_string, start_time, end_time, stream):
    """Iterate scan numbers matching a filter string within an optional time window."""
    with handle_raw_errors():
        with RawFileAdapter(file_path) as adapter:
            scan_iter = adapter.iterate_filtered_scans(filter_string, start_time=start_time, end_time=end_time)
            if stream:
                for sn in scan_iter:
                    print(to_json({"scan_number": sn}))
            else:
                scan_numbers = list(scan_iter)
                emit_json({"filter_string": filter_string, "scan_numbers": scan_numbers, "count": len(scan_numbers)}, indent=ctx.obj.get("indent"))
