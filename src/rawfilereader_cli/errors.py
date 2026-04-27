import sys
import json
import traceback
from contextlib import contextmanager

try:
    from rawfilereader.exceptions import (
        RawFileError,
        RawFileNotOpenError,
        RawFileInAcquisitionError,
        InstrumentSelectionError,
        ScanNotFoundError,
        AssemblyLoadError,
    )
    _EXCEPTION_CLASSES = (
        RawFileError,
        RawFileNotOpenError,
        RawFileInAcquisitionError,
        InstrumentSelectionError,
        ScanNotFoundError,
        AssemblyLoadError,
    )
except ImportError:
    class RawFileError(Exception): pass
    class RawFileNotOpenError(Exception): pass
    class RawFileInAcquisitionError(Exception): pass
    class InstrumentSelectionError(Exception): pass
    class ScanNotFoundError(Exception): pass
    class AssemblyLoadError(Exception): pass
    _EXCEPTION_CLASSES = (RawFileError,)

_TYPE_MAP = {
    "RawFileNotOpenError": "not_open_error",
    "RawFileInAcquisitionError": "in_acquisition_error",
    "InstrumentSelectionError": "instrument_error",
    "ScanNotFoundError": "scan_not_found",
    "AssemblyLoadError": "assembly_load_error",
    "RawFileError": "raw_file_error",
}


def _error_type(exc):
    return _TYPE_MAP.get(type(exc).__name__, "raw_file_error")


def emit_error(exc, details=None):
    payload = {
        "error": str(exc),
        "type": _error_type(exc),
        "details": details or {},
    }
    print(json.dumps(payload), file=sys.stderr)
    sys.exit(1)


@contextmanager
def handle_raw_errors():
    try:
        yield
    except _EXCEPTION_CLASSES as exc:
        emit_error(exc)
    except SystemExit:
        raise
    except Exception as exc:
        payload = {
            "error": str(exc),
            "type": "unexpected_error",
            "details": {"traceback": traceback.format_exc()},
        }
        print(json.dumps(payload), file=sys.stderr)
        sys.exit(1)
