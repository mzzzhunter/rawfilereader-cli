# Agent instructions for rawfilereader-cli

Use this file as a ready-to-copy agent instruction file. For OpenAI Codex CLI,
copy this content into `AGENTS.md` at the project or data directory root. Other
terminal agents can copy it into the instruction filename they support.

## Mass spectrometry file access — rawfilereader-cli

You have access to `rawfilereader`, a CLI that reads Thermo Fisher `.raw` mass
spectrometry files and returns structured JSON on stdout.

### Prerequisites expected in this environment

- `RAWFILEREADER_LIBS` — path to Thermo RawFileReader .NET assemblies
- `DOTNET_ROOT` — .NET 8 runtime root on Linux

If these are not set, ask the user to configure them before RAW file analysis.

### Command structure

```bash
rawfilereader [--indent N] GROUP COMMAND --file PATH [OPTIONS]
```

### Command groups and key commands

#### `file` — file-level metadata and chromatograms

```bash
rawfilereader file info              --file F
rawfilereader file scan_range        --file F
rawfilereader file filters           --file F
rawfilereader file instrument        --file F
rawfilereader file chromatogram      --file F --trace_type BasePeak|TIC \
  [--start_rt MIN] [--end_rt MIN] [--filter_string STR]
rawfilereader file chromatogram_peaks --file F [--smooth_window 5] [--min_height 1e5]
```

#### `scan` — per-scan data

```bash
rawfilereader scan info       --file F --scan_number N
rawfilereader scan stats      --file F --scan_number N
rawfilereader scan spectrum   --file F --scan_number N [--max_points N]
rawfilereader scan profile    --file F --scan_number N [--max_points N]
rawfilereader scan trailer    --file F --scan_number N
rawfilereader scan filter     --file F --scan_number N
rawfilereader scan dependents --file F --scan_number N [--depth 1]
```

#### `search` — find scans

```bash
rawfilereader search by_filter      --file F --filter_string STR [--start_scan N] [--end_scan N]
rawfilereader search by_rt          --file F --retention_time MIN
rawfilereader search rt_for_scan    --file F --scan_number N
rawfilereader search iterate_filter --file F --filter_string STR \
  [--start_time MIN] [--end_time MIN] [--stream]
```

#### `analyze` — aggregates

```bash
rawfilereader analyze summary         --file F
rawfilereader analyze average_scans   --file F --first_scan N --last_scan N [--filter_string STR]
rawfilereader analyze scan_info_range --file F [--ms_order INT] [--stream]
```

### Output format

- Success: JSON object on stdout, exit code 0
- Error: JSON on stderr, exit code 1, typically shaped like:

```json
{"error": "...", "type": "...", "details": {}}
```

Read the `type` field before retrying.

### Important flags

| Flag | Meaning |
|---|---|
| `--max_points 0` | Return all data points (default) |
| `--max_points -1` | Omit arrays; return metadata plus `point_count` only |
| `--max_points N` | Truncate arrays to first `N` points |
| `--stream` | Emit one JSON object per line (NDJSON) |
| `--indent N` | Pretty-print JSON with `N` spaces |

All retention times are in **minutes**.

### Standard workflow

1. Orient first:

   ```bash
   rawfilereader file info --file run.raw
   rawfilereader file scan_range --file run.raw
   rawfilereader analyze summary --file run.raw
   rawfilereader file filters --file run.raw
   ```

2. Use metadata before arrays:

   ```bash
   rawfilereader scan spectrum --file run.raw --scan_number 1 --max_points -1
   ```

3. Narrow searches before loops:

   ```bash
   rawfilereader search by_filter --file run.raw --filter_string "Full ms" \
     --start_scan 1 --end_scan 500
   ```

4. Stream large sets:

   ```bash
   rawfilereader analyze scan_info_range --file run.raw --ms_order 2 --stream
   ```

5. Resolve retention time to scan number with `search by_rt`; never estimate scan
   numbers arithmetically from retention time.

### Example tasks

#### Summarize a file

```bash
rawfilereader analyze summary --file sample.raw
```

Report scan counts per MS order and include relevant metadata from the initial
orientation commands.

#### Extract a TIC and pick peaks

```bash
rawfilereader file chromatogram_peaks --file sample.raw \
  --trace_type TIC --smooth_window 7
```

Summarize `peak_count` and format peak retention times and intensities in a
table if the user asks for a report.

#### Inspect a scan

```bash
rawfilereader scan spectrum --file sample.raw --scan_number 42 --max_points 10
rawfilereader scan trailer  --file sample.raw --scan_number 42
```

Use `scan stats` first if the user asks for base peak, TIC, or mass range.

### Skill recipes

If `SKILL.md` is present, read it for six ready-to-use multi-step workflows:
file overview, max-intensity m/z per filter, chromatogram peak table, spectrum
at retention time, MS2 precursor survey, and averaged spectrum.
