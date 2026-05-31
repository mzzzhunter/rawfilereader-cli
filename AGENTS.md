# Agent Instructions — rawfilereader-cli

Use these instructions when an AI agent needs to inspect Thermo Fisher `.raw` mass spectrometry files from this repository or a data directory. The project exposes a single shell command, `rawfilereader`, and every subcommand returns JSON on stdout.

## Environment

The runtime environment must provide:

- `RAWFILEREADER_LIBS`: path to the Thermo RawFileReader `.dll` assembly directory.
- `DOTNET_ROOT`: .NET 8 runtime root on Linux or Colab.
- `PATH`: should include the .NET runtime directory on Linux or Colab.

If a command fails, inspect stderr. Errors are JSON objects with `error`, `type`, and `details` fields.

## General command shape

```bash
rawfilereader [--indent N] GROUP COMMAND --file PATH [OPTIONS]
```

Global options must appear before the command group:

- `--indent N`: pretty-print JSON with an N-space indent; omit for compact JSON.
- `--version`: print the installed `rawfilereader-cli` version.
- `--help`: show Click help for any level, for example `rawfilereader scan spectrum --help`.

## Recommended first-pass orientation

Always orient on the file before selecting scan ranges, filters, or retention-time windows:

```bash
rawfilereader file info       --file run.raw
rawfilereader file scan_range --file run.raw
rawfilereader analyze summary --file run.raw
rawfilereader file filters    --file run.raw
rawfilereader file method     --file run.raw
```

## Complete command reference

### `file` — file-level metadata, methods, filters, and chromatograms

```bash
rawfilereader file COMMAND --file PATH [OPTIONS]
```

| Command | Required options | Optional options | Use when you need |
|---|---|---|---|
| `info` | `--file` | | File metadata plus run header summary. |
| `scan_range` | `--file` | | First and last scan numbers. |
| `instrument` | `--file` | | Instrument count and instrument metadata. |
| `method` | `--file` | | Instrument method strings keyed by method device name. Duplicate device names are suffixed, for example `MS (2)`. |
| `filters` | `--file` | | All unique Thermo scan filter strings. |
| `chromatogram` | `--file` | `--trace_type`, `--filter_string`, `--mass_range`, `--start_scan`, `--end_scan`, `--start_rt`, `--end_rt` | A chromatogram trace. |
| `chromatogram_peaks` | `--file` | all `chromatogram` options plus `--smooth_window`, `--min_height` | Local maxima in a chromatogram, sorted by raw intensity. |

Chromatogram options:

- `--trace_type`: chromatogram trace type. Default: `BasePeak`. Common values include `BasePeak`, `TIC`, and `SIC`.
- `--filter_string`: Thermo filter string used to narrow scan bounds.
- `--mass_range`: mass range string for SIC extraction, for example `500.0-510.0`. Default: empty string.
- `--start_scan`: first scan number. Default: `-1`, meaning adapter/file start.
- `--end_scan`: last scan number. Default: `-1`, meaning adapter/file end.
- `--start_rt`: start retention time in minutes; overrides `--start_scan`.
- `--end_rt`: end retention time in minutes; overrides `--end_scan`.
- `--smooth_window`: moving-average smoothing window for `chromatogram_peaks`. Default: `5`.
- `--min_height`: minimum raw intensity for a reported peak. Default: `0`; scientific notation such as `1e5` is accepted.

Examples:

```bash
rawfilereader --indent 2 file method --file run.raw
rawfilereader file chromatogram --file run.raw --trace_type TIC --start_rt 2.0 --end_rt 10.0
rawfilereader file chromatogram --file run.raw --trace_type SIC --mass_range 500.0-510.0
rawfilereader file chromatogram_peaks --file run.raw --smooth_window 7 --min_height 1e6
```

### `scan` — per-scan metadata and spectra

```bash
rawfilereader scan COMMAND --file PATH [OPTIONS]
```

| Command | Required options | Optional options | Use when you need |
|---|---|---|---|
| `info` | `--file` plus `--scan_number` or `--ms_order` | `--stream` with `--ms_order` | Metadata for one scan, or metadata for every scan matching an MS order. |
| `stats` | `--file`, `--scan_number` | | Scan statistics such as TIC, base peak, and mass range. |
| `spectrum` | `--file`, `--scan_number` | `--prefer_profile`, `--max_points` | Centroid masses/intensities and auxiliary arrays. |
| `profile` | `--file`, `--scan_number` | `--max_points` | Profile/continuous masses and intensities. |
| `filter` | `--file`, `--scan_number` | | Thermo filter string for one scan. |
| `trailer` | `--file`, `--scan_number` | | Trailer/auxiliary values for one scan. |
| `dependents` | `--file`, `--scan_number` | `--depth` | Parent-dependent scan hierarchy. |

Spectrum/profile point controls:

- `--max_points 0`: return all array points. This is the default.
- `--max_points -1`: omit arrays and return `point_count` only; use this before loading very large spectra.
- `--max_points N`: return at most N array points and set `truncated` when arrays are shortened.
- `--prefer_profile`: with `scan spectrum`, prefer profile data when available.
- `--depth`: recursion depth for dependent scan lookup. Default: `1`.

Examples:

```bash
rawfilereader scan info --file run.raw --scan_number 42
rawfilereader scan info --file run.raw --ms_order 2 --stream
rawfilereader scan stats --file run.raw --scan_number 42
rawfilereader scan spectrum --file run.raw --scan_number 42 --max_points 50
rawfilereader scan spectrum --file run.raw --scan_number 42 --prefer_profile --max_points -1
rawfilereader scan profile --file run.raw --scan_number 42 --max_points 100
rawfilereader scan filter --file run.raw --scan_number 42
rawfilereader scan trailer --file run.raw --scan_number 42
rawfilereader scan dependents --file run.raw --scan_number 42 --depth 2
```

### `search` — scan lookup by filter, retention time, or scan number

```bash
rawfilereader search COMMAND --file PATH [OPTIONS]
```

| Command | Required options | Optional options | Use when you need |
|---|---|---|---|
| `by_filter` | `--file`, `--filter_string` | `--start_scan`, `--end_scan` | Scan numbers whose Thermo filter string matches a value. |
| `by_rt` | `--file`, `--retention_time` | | Scan number closest to a retention time in minutes. |
| `rt_for_scan` | `--file`, `--scan_number` | | Retention time in minutes for a scan number. |
| `iterate_filter` | `--file`, `--filter_string` | `--start_time`, `--end_time`, `--stream` | Scan numbers matching a filter string inside an optional retention-time window. |

Examples:

```bash
rawfilereader search by_filter --file run.raw --filter_string "Full ms"
rawfilereader search by_filter --file run.raw --filter_string "ms2" --start_scan 100 --end_scan 500
rawfilereader search by_rt --file run.raw --retention_time 4.5
rawfilereader search rt_for_scan --file run.raw --scan_number 42
rawfilereader search iterate_filter --file run.raw --filter_string "ms2" --start_time 2.0 --end_time 5.0 --stream
```

### `analyze` — aggregate operations

```bash
rawfilereader analyze COMMAND --file PATH [OPTIONS]
```

| Command | Required options | Optional options | Use when you need |
|---|---|---|---|
| `summary` | `--file` | | Counts of scans by MS order across the file. |
| `average_scans` | `--file`, `--first_scan`, `--last_scan` | `--filter_string` | Average spectrum across a scan range, optionally restricted by filter string. |
| `scan_info_range` | `--file` | `--ms_order`, `--stream` | Scan metadata for all scans or for a single MS order. |

Examples:

```bash
rawfilereader analyze summary --file run.raw
rawfilereader analyze average_scans --file run.raw --first_scan 1 --last_scan 50
rawfilereader analyze average_scans --file run.raw --first_scan 1 --last_scan 50 --filter_string "Full ms"
rawfilereader analyze scan_info_range --file run.raw --ms_order 1 --stream
```

## Output conventions

Success output is JSON on stdout. For large iterable outputs, use `--stream` where available to emit newline-delimited JSON objects.

```json
{"first_scan": 1, "last_scan": 3842}
```

Failure output is JSON on stderr with exit code `1`.

```json
{"error": "Scan 9999 not found", "type": "scan_not_found", "details": {}}
```

Known error `type` values include `raw_file_error`, `not_open_error`, `scan_not_found`, `instrument_error`, `assembly_load_error`, `in_acquisition_error`, and `unexpected_error`.

## Practical guidance for agents

- Prefer `file scan_range`, `analyze summary`, and `file filters` before making assumptions about a run.
- Use retention times in minutes for every RT option.
- Use `--max_points -1` first for unknown or large scans; fetch arrays only when necessary.
- Use `--stream` for `scan info`, `search iterate_filter`, and `analyze scan_info_range` on large files.
- Use `SKILL.md` for reusable multi-step recipes such as file overview, chromatogram peak tables, spectra near target RTs, MS2 precursor surveys, and averaged spectra.
