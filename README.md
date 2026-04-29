# rawfilereader-cli

A command-line interface that wraps [RawFileReaderPyAdapter](https://github.com/mzzzhunter/RawFileReaderPyAdapter) so AI agents and shell scripts can read Thermo Fisher `.raw` mass spectrometry files via subprocess calls. Every command outputs JSON to stdout.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mzzzhunter/rawfilereader-cli/blob/claude/cli-file-access-agent-xsdMh/notebooks/rawfilereader_cli_colab.ipynb)

---

## Requirements

- Python ≥ 3.8
- .NET 8 runtime (required by Thermo's RawFileReader library)
- Windows or Linux (with .NET installed)

### Install .NET 8

**Windows:** Download from [dotnet.microsoft.com](https://dotnet.microsoft.com/download/dotnet/8.0).

**Linux / Colab:**
```bash
wget -q https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
bash dotnet-install.sh --channel 8.0 --runtime dotnet
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$HOME/.dotnet:$HOME/.dotnet/tools:$PATH"
```

### Download Thermo RawFileReader DLLs

The adapter requires Thermo's RawFileReader `.NET` assemblies. Download them from the official repository:

```
https://github.com/thermofisherlsms/RawFileReader/tree/main/Libs/NetCore/Net8/Assemblies
```

Click **"Download raw file"** for each `.dll` file, or use a sparse Git clone to grab the whole folder at once:

```bash
git clone --filter=blob:none --no-checkout --sparse \
    https://github.com/thermofisherlsms/RawFileReader.git thermo-libs
cd thermo-libs
git sparse-checkout set Libs/NetCore/Net8/Assemblies
git checkout
```

The assemblies will be in `thermo-libs/Libs/NetCore/Net8/Assemblies/`.

Then point the adapter at the directory:

```bash
export RAWFILEREADER_LIBS="/path/to/thermo-libs/Libs/NetCore/Net8/Assemblies"
```

Add this export to your shell profile (`.bashrc`, `.zshrc`, etc.) to make it permanent.

---

## Installation

```bash
pip install git+https://github.com/mzzzhunter/rawfilereader-cli.git
```

Or clone and install in editable mode:
```bash
git clone https://github.com/mzzzhunter/rawfilereader-cli.git
cd rawfilereader-cli
pip install -e .
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `RAWFILEREADER_LIBS` | **Yes** | Path to the folder containing the Thermo RawFileReader `.dll` assemblies (see [Download Thermo RawFileReader DLLs](#download-thermo-rawfilereader-dlls)) |
| `DOTNET_ROOT` | Linux/Colab | Path to the .NET runtime root (e.g. `$HOME/.dotnet`) |

```bash
export RAWFILEREADER_LIBS="/path/to/thermo-libs/Libs/NetCore/Net8/Assemblies"
export DOTNET_ROOT="$HOME/.dotnet"
export PATH="$HOME/.dotnet:$HOME/.dotnet/tools:$PATH"
```

---

## Quick Start

```bash
# File overview
rawfilereader file info       --file run.raw
rawfilereader file scan_range --file run.raw

# Extract the Base Peak Chromatogram
rawfilereader file chromatogram --file run.raw --trace_type BasePeak

# Get a centroid spectrum for scan 1
rawfilereader scan spectrum --file run.raw --scan_number 1

# Find all MS1 scans
rawfilereader search by_filter --file run.raw --filter_string "Full ms"

# Scan count by MS order
rawfilereader analyze summary --file run.raw
```

All output is compact JSON by default. Pass `--indent 2` for pretty-printed output:
```bash
rawfilereader --indent 2 file info --file run.raw
```

---

## Command Reference

### Global options

| Option | Default | Description |
|---|---|---|
| `--indent N` | compact | JSON indent level |
| `--version` | | Print version and exit |

---

### `file` — file-level metadata and chromatograms

```
rawfilereader file COMMAND --file PATH [OPTIONS]
```

| Command | Key options | Description |
|---|---|---|
| `info` | | File metadata and run header |
| `scan_range` | | First and last scan number |
| `instrument` | | Instrument count and metadata |
| `filters` | | All unique scan filter strings |
| `chromatogram` | `--trace_type`, `--filter_string`, `--mass_range`, `--start_scan`, `--end_scan`, `--start_rt`, `--end_rt` | Extract a chromatogram trace |
| `chromatogram_peaks` | same as above + `--smooth_window` | Detect peaks in a chromatogram |

**Chromatogram options:**

| Option | Default | Description |
|---|---|---|
| `--trace_type` | `BasePeak` | `BasePeak`, `TIC`, `SIC`, … |
| `--filter_string` | | Thermo filter to narrow scan range |
| `--mass_range` | `""` | Mass range string for SIC (e.g. `500.0-510.0`) |
| `--start_scan` | `-1` | First scan (adapter default = file start) |
| `--end_scan` | `-1` | Last scan (adapter default = file end) |
| `--start_rt` | | Start RT in **minutes** (overrides `--start_scan`) |
| `--end_rt` | | End RT in **minutes** (overrides `--end_scan`) |
| `--smooth_window` *(peaks only)* | `5` | Moving-average smoothing window |

---

### `scan` — per-scan data

```
rawfilereader scan COMMAND --file PATH --scan_number N [OPTIONS]
```

| Command | Key options | Description |
|---|---|---|
| `info` | `--scan_number` or `--ms_order`, `--stream` | Scan metadata |
| `stats` | `--scan_number` | TIC, base peak mass/intensity |
| `spectrum` | `--scan_number`, `--prefer_profile`, `--max_points` | Centroid m/z + intensity arrays |
| `profile` | `--scan_number`, `--max_points` | Profile (continuous) spectrum |
| `filter` | `--scan_number` | Thermo filter string for a scan |
| `trailer` | `--scan_number` | Auxiliary / trailer values |
| `dependents` | `--scan_number`, `--depth` | Parent–dependent scan hierarchy |

`--max_points`: `0` = return all points, `-1` = omit arrays (return `point_count` only), `N > 0` = truncate to N points.

---

### `search` — scan number lookup

```
rawfilereader search COMMAND --file PATH [OPTIONS]
```

| Command | Key options | Description |
|---|---|---|
| `by_filter` | `--filter_string`, `--start_scan`, `--end_scan` | Scan numbers matching a filter string |
| `by_rt` | `--retention_time` (minutes) | Scan number closest to an RT |
| `rt_for_scan` | `--scan_number` | RT (minutes) for a given scan |
| `iterate_filter` | `--filter_string`, `--start_time`, `--end_time`, `--stream` | Scan numbers in an RT window |

---

### `analyze` — aggregate operations

```
rawfilereader analyze COMMAND --file PATH [OPTIONS]
```

| Command | Key options | Description |
|---|---|---|
| `summary` | | Scan count by MS order |
| `average_scans` | `--first_scan`, `--last_scan`, `--filter_string` | Average spectra over a scan range |
| `scan_info_range` | `--ms_order`, `--stream` | Iterate scan metadata for all scans |

---

## Output format

### Success — stdout JSON

```json
{"first_scan": 1, "last_scan": 3842}
```

### Error — stderr JSON, exit code 1

```json
{"error": "Scan 9999 not found", "type": "scan_not_found", "details": {}}
```

Error types: `raw_file_error`, `not_open_error`, `scan_not_found`, `instrument_error`, `assembly_load_error`, `in_acquisition_error`, `unexpected_error`.

### Streaming output (`--stream`)

Commands that return arrays support `--stream` to emit one JSON object per line (NDJSON), useful for large files:

```bash
rawfilereader analyze scan_info_range --ms_order 1 --stream --file run.raw \
  | python -c "import sys,json; [print(json.loads(l)['retention_time']) for l in sys.stdin]"
```

---

## Examples

```bash
# Pretty-print all file metadata
rawfilereader --indent 2 file info --file run.raw

# TIC chromatogram for the first 5 minutes
rawfilereader file chromatogram \
  --trace_type TIC \
  --end_rt 5.0 \
  --file run.raw

# Detect chromatogram peaks (smoothing window = 9)
rawfilereader file chromatogram_peaks --smooth_window 9 --file run.raw

# Centroid spectrum for scan 42, top 50 peaks only
rawfilereader scan spectrum --scan_number 42 --max_points 50 --file run.raw

# All MS2 scan numbers between 2 and 5 minutes
rawfilereader search iterate_filter \
  --filter_string "ms2" \
  --start_time 2.0 \
  --end_time 5.0 \
  --file run.raw

# Average the first 10 MS1 scans
rawfilereader analyze average_scans \
  --first_scan 1 --last_scan 10 \
  --filter_string "Full ms" \
  --file run.raw
```

---

## Using from Python

```python
import subprocess, json

def rawfilereader(*args, file):
    cmd = ["rawfilereader"] + list(args) + ["--file", file]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(r.stdout)

sr = rawfilereader("file", "scan_range", file="run.raw")
print(sr["first_scan"], "–", sr["last_scan"])
```

---

## Interactive notebook

The Colab notebook walks through every command with live plots:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mzzzhunter/rawfilereader-cli/blob/claude/cli-file-access-agent-xsdMh/notebooks/rawfilereader_cli_colab.ipynb)

Source: [`notebooks/rawfilereader_cli_colab.ipynb`](notebooks/rawfilereader_cli_colab.ipynb)

---

## Running tests

Unit tests use a fully mocked adapter — no `.raw` file or .NET runtime required:

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## License

MIT
