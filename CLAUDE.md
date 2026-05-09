# Claude Code instructions for rawfilereader-cli

Use this file as a ready-to-copy `CLAUDE.md` in any project or data directory
where Claude Code should inspect Thermo Fisher `.raw` mass spectrometry files
with `rawfilereader-cli`.

## Mass spectrometry file access — rawfilereader-cli

You have access to `rawfilereader`, a CLI that reads Thermo Fisher `.raw` files
and returns JSON. Use it via the Bash tool.

### Environment expected in this shell

- `RAWFILEREADER_LIBS` — path to Thermo RawFileReader .NET assemblies
- `DOTNET_ROOT` — .NET 8 runtime root on Linux

If either variable is missing, ask the user to set it before attempting RAW file
analysis.

### General usage pattern

```bash
rawfilereader [--indent N] GROUP COMMAND --file PATH [OPTIONS]
```

All successful output is JSON on stdout. Errors are JSON on stderr with exit
code 1.

### Command groups

- `file` — file metadata, scan range, instrument info, filters, chromatograms
- `scan` — per-scan data: info, stats, spectrum, profile, trailer, dependents
- `search` — find scans by filter string, retention time, or scan number
- `analyze` — aggregate operations: summary, average spectra, bulk scan info

### Orient first

Always run these before deeper analysis so scan ranges, MS orders, filters, and
metadata are known:

```bash
rawfilereader file info       --file run.raw
rawfilereader file scan_range --file run.raw
rawfilereader analyze summary --file run.raw
rawfilereader file filters    --file run.raw
```

### Common commands

```bash
rawfilereader scan stats            --file run.raw --scan_number 1
rawfilereader scan spectrum         --file run.raw --scan_number 1 --max_points 20
rawfilereader scan trailer          --file run.raw --scan_number 1
rawfilereader search by_filter      --file run.raw --filter_string "Full ms"
rawfilereader search by_rt          --file run.raw --retention_time 4.5
rawfilereader search rt_for_scan    --file run.raw --scan_number 1
rawfilereader analyze average_scans --file run.raw --first_scan 1 --last_scan 50
rawfilereader analyze scan_info_range --file run.raw --ms_order 2 --stream
rawfilereader file chromatogram_peaks --file run.raw --min_height 1e5
```

### Output handling

- Pass `--indent 2` for readable output during manual inspection.
- Use `--max_points -1` to return metadata only, without arrays, and check
  `point_count` before fetching full spectrum/profile data.
- Use `--stream` on iterative commands for newline-delimited JSON (NDJSON), one
  JSON object per line.
- All retention times are in **minutes**.
- On failure, inspect the JSON `type` field in stderr before retrying.

### Recommended workflows

#### File overview

```bash
rawfilereader file info --file run.raw
rawfilereader file scan_range --file run.raw
rawfilereader analyze summary --file run.raw
rawfilereader file filters --file run.raw
```

Report the file metadata, total scan count, scan range, MS-order counts, and
unique filter strings.

#### Base-peak chromatogram over an RT window

```bash
rawfilereader file chromatogram --file run.raw \
  --trace_type BasePeak --start_rt 2.0 --end_rt 10.0
```

Return or summarize the `times` and `intensities` arrays. Use
`file chromatogram_peaks` when the user asks for peak picking.

#### Spectrum at retention time

```bash
rawfilereader search by_rt --file run.raw --retention_time 4.5
rawfilereader scan stats --file run.raw --scan_number SCAN
rawfilereader scan spectrum --file run.raw --scan_number SCAN --max_points 50
```

Resolve retention time to scan number with `search by_rt`; do not guess scan
numbers from retention times.

#### MS2 precursor survey

```bash
rawfilereader analyze scan_info_range --file run.raw --ms_order 2 --stream
rawfilereader scan trailer --file run.raw --scan_number SCAN
```

Stream MS2 scan metadata, then inspect trailer data for precursor and charge
state fields when needed.

### Skill recipes

If the repository or copied directory includes `SKILL.md`, read it for six
ready-to-run multi-step recipes:

1. File overview
2. Max-intensity m/z per filter
3. Chromatogram peak table
4. Spectrum at retention time
5. MS2 precursor survey
6. Averaged spectrum
