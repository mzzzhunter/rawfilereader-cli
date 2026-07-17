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
        RawFileInAc