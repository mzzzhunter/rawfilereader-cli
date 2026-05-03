# rawfilereader-cli Skill Library

Composable analysis recipes for AI agents (Claude Code, OpenAI Codex, API tool-use).
Each skill is a self-contained Python function that drives the CLI via subprocess.

---

## Shared helper

Paste this once at the top of any agent script or notebook cell.

```python
import subprocess, json, sys

def _run(raw_file: str, *args) -> dict | list:
    """Run a rawfilereader command and return parsed JSON."""
    cmd = ["rawfilereader"] + list(args) + ["--file", raw_file]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        err = json.loads(r.stderr)
        raise RuntimeError(f"[{err['type']}] {err['error']}")
    return json.loads(r.stdout)

def _stream(raw_file: str, *args) -> list[dict]:
    """Run a --stream command and return a list of NDJSON objects."""
    cmd = ["rawfilereader"] + list(args) + ["--stream", "--file", raw_file]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        err = json.loads(r.stderr)
        raise RuntimeError(f"[{err['type']}] {err['error']}")
    return [json.loads(line) for line in r.stdout.splitlines() if line.strip()]
```

---

## Skill 1 — File overview

**When to use:** Always run this first. Gives the agent the context needed to
make sensible decisions about scan ranges, retention times, and filter strings.

**Commands used:** `file info`, `file scan_range`, `analyze summary`, `file filters`

```python
def file_overview(raw_file: str) -> dict:
    """Return a compact summary of a RAW file."""
    info    = _run(raw_file, "file", "info")
    sr      = _run(raw_file, "file", "scan_range")
    summary = _run(raw_file, "analyze", "summary")
    filters = _run(raw_file, "file", "filters")["filters"]

    return {
        "name":       info["file_info"].get("name"),
        "created":    info["file_info"].get("creation_date"),
        "operator":   info["file_info"].get("operator"),
        "first_scan": sr["first_scan"],
        "last_scan":  sr["last_scan"],
        "scan_count": sr["last_scan"] - sr["first_scan"] + 1,
        "ms_orders":  summary["summary"],   # e.g. {"1": 1921, "2": 1921}
        "filters":    filters,
    }
```

**Example output**
```json
{
  "name": "sample.raw",
  "created": "2023-06-01T14:22:00",
  "operator": "jsmith",
  "first_scan": 1,
  "last_scan": 3842,
  "scan_count": 3842,
  "ms_orders": {"1": 1921, "2": 1921},
  "filters": [
    "FTMS + p NSI Full ms [200.00-2000.00]",
    "FTMS + c NSI d Full ms2 445.12@hcd28.00 [100.00-1500.00]"
  ]
}
```

---

## Skill 2 — Max-intensity m/z per filter

**When to use:** Characterise what each filter string captures — which m/z
dominates in MS1, MS2, etc.

**Commands used:** `file filters`, `search by_filter`, `scan stats`

**Performance tip:** Pass `start_scan` / `end_scan` to limit the search to a
scan window (e.g. the first 500 scans for a quick preview).

```python
def max_intensity_per_filter(
    raw_file: str,
    start_scan: int = -1,
    end_scan:   int = -1,
) -> list[dict]:
    """Return [{filter, mz, intensity, scan_number}, ...] sorted by intensity desc."""
    filters = _run(raw_file, "file", "filters")["filters"]
    results = []

    for flt in filters:
        args = ["search", "by_filter", "--filter_string", flt]
        if start_scan != -1:
            args += ["--start_scan", str(start_scan)]
        if end_scan != -1:
            args += ["--end_scan", str(end_scan)]

        scan_numbers = _run(raw_file, *args)["scan_numbers"]
        if not scan_numbers:
            continue

        best = {"mz": None, "intensity": -1, "scan_number": None}
        for sn in scan_numbers:
            stats = _run(raw_file, "scan", "stats", "--scan_number", str(sn))
            bp = stats.get("base_peak_intensity") or 0
            if bp > best["intensity"]:
                best = {
                    "mz":          stats.get("base_peak_mass"),
                    "intensity":   bp,
                    "scan_number": sn,
                }

        results.append({"filter": flt, **best})

    results.sort(key=lambda r: r["intensity"], reverse=True)
    return results
```

**Example output**
```
         m/z       intensity  scan  filter
   445.1185    9.123e+07   101  FTMS + p NSI Full ms [200.00-2000.00]
   612.3041    3.457e+06   102  FTMS + c NSI d Full ms2 445.12@hcd28.00 [100.00-1500.00]
```

---

## Skill 3 — Chromatogram peak table

**When to use:** Find elution peaks, rank them by intensity, and cross-reference
each peak back to its scan number for downstream spectrum retrieval.

**Commands used:** `file chromatogram_peaks`, `search by_rt`

```python
def chromatogram_peak_table(
    raw_file:    str,
    trace_type:  str   = "BasePeak",
    smooth_window: int = 7,
    min_height:  float = 0.0,
) -> list[dict]:
    """Return chromatogram peaks with scan numbers, sorted by intensity desc."""
    data = _run(
        raw_file,
        "file", "chromatogram_peaks",
        "--trace_type",    trace_type,
        "--smooth_window", str(smooth_window),
        "--min_height",    str(min_height),
    )

    peaks = []
    for p in data["peaks"]:
        scan = _run(
            raw_file,
            "search", "by_rt",
            "--retention_time", str(p["retention_time"]),
        )
        peaks.append({
            "retention_time":    p["retention_time"],
            "intensity":         p["intensity"],
            "smoothed_intensity": p["smoothed_intensity"],
            "scan_number":       scan["scan_number"],
        })

    return peaks   # already sorted by intensity desc
```

**Example — get the top-3 peaks and fetch their spectra**
```python
peaks = chromatogram_peak_table("run.raw", min_height=1e6)
for p in peaks[:3]:
    spec = _run("run.raw", "scan", "spectrum",
                "--scan_number", str(p["scan_number"]),
                "--max_points",  "20")
    print(f"RT {p['retention_time']:.3f} min  scan {p['scan_number']}"
          f"  top m/z {spec['masses'][0]:.4f}")
```

---

## Skill 4 — Spectrum near a target retention time

**When to use:** The agent knows an RT of interest (from literature, a peak,
or the user) and wants to pull a spectrum without knowing the scan number.

**Commands used:** `search by_rt`, `scan stats`, `scan spectrum`

```python
def spectrum_at_rt(
    raw_file:   str,
    rt_minutes: float,
    max_points: int = 0,     # 0 = all, -1 = metadata only, N = truncate
) -> dict:
    """Return the centroid spectrum for the scan closest to rt_minutes."""
    hit    = _run(raw_file, "search", "by_rt", "--retention_time", str(rt_minutes))
    sn     = hit["scan_number"]
    actual_rt = hit["retention_time"]

    # Metadata check before loading arrays
    meta = _run(raw_file, "scan", "stats", "--scan_number", str(sn))

    spec = _run(
        raw_file,
        "scan", "spectrum",
        "--scan_number", str(sn),
        "--max_points",  str(max_points),
    )
    spec["requested_rt"] = rt_minutes
    spec["actual_rt"]    = actual_rt
    spec["tic"]          = meta.get("tic")
    spec["base_peak_mass"] = meta.get("base_peak_mass")
    return spec
```

**Example**
```python
spec = spectrum_at_rt("run.raw", rt_minutes=4.5, max_points=50)
print(f"Closest scan: {spec['scan_number']}  actual RT: {spec['actual_rt']:.4f} min")
print(f"TIC: {spec['tic']:.3e}   base peak: {spec['base_peak_mass']:.4f} m/z")
```

---

## Skill 5 — MS² precursor survey

**When to use:** Proteomics / metabolomics workflows where the agent needs to
map every MS2 event — which precursor m/z was fragmented, at what RT, with
what charge state.

**Commands used:** `analyze scan_info_range --stream`, `scan trailer`

Use `--stream` here because a file can contain thousands of MS2 scans; streaming
avoids buffering the entire array in memory.

```python
def ms2_precursor_survey(raw_file: str) -> list[dict]:
    """Return [{scan_number, rt, precursor_mz, charge, filter}, ...] for all MS2 scans."""
    ms2_infos = _stream(raw_file, "analyze", "scan_info_range", "--ms_order", "2")
    rows = []
    for si in ms2_infos:
        sn = si["scan_number"]
        trailer = _run(raw_file, "scan", "trailer", "--scan_number", str(sn))
        fields  = trailer.get("fields", {})
        rows.append({
            "scan_number":   sn,
            "retention_time": si.get("retention_time"),
            "filter":         si.get("filter"),
            "charge":         fields.get("Charge State", fields.get("charge_state")),
            "precursor_mz":   fields.get("Monoisotopic M/Z",
                               fields.get("monoisotopic_mz",
                               si.get("base_peak_mass"))),
        })
    return rows
```

**Example — find the most-fragmented precursor mass**
```python
from collections import Counter

rows = ms2_precursor_survey("run.raw")
# Round to 2 dp and count occurrences
mz_counts = Counter(round(r["precursor_mz"], 2) for r in rows if r["precursor_mz"])
print("Top 5 precursor m/z by fragmentation count:")
for mz, n in mz_counts.most_common(5):
    print(f"  {mz:.2f}  ×{n}")
```

---

## Skill 6 — Averaged spectrum for a filter

**When to use:** Improve signal-to-noise by co-adding many scans of the same
type. Useful before calling a peak-picking algorithm or reporting a clean MS1.

**Commands used:** `search by_filter`, `analyze average_scans`

```python
def averaged_spectrum(
    raw_file:     str,
    filter_string: str,
    start_scan:   int = -1,
    end_scan:     int = -1,
    max_points:   int = 0,
) -> dict:
    """Return an averaged centroid spectrum for all scans matching filter_string."""
    hit = _run(
        raw_file,
        "search", "by_filter",
        "--filter_string", filter_string,
        *(["--start_scan", str(start_scan)] if start_scan != -1 else []),
        *(["--end_scan",   str(end_scan)]   if end_scan   != -1 else []),
    )
    scan_numbers = hit["scan_numbers"]
    if not scan_numbers:
        raise ValueError(f"No scans matched filter: {filter_string!r}")

    avg = _run(
        raw_file,
        "analyze", "average_scans",
        "--first_scan",    str(min(scan_numbers)),
        "--last_scan",     str(max(scan_numbers)),
        "--filter_string", filter_string,
    )

    if max_points > 0 and avg.get("masses"):
        avg["masses"]      = avg["masses"][:max_points]
        avg["intensities"] = avg["intensities"][:max_points]

    avg["scan_count"]     = len(scan_numbers)
    avg["filter_string"]  = filter_string
    return avg
```

**Example**
```python
overview = file_overview("run.raw")
ms1_filter = overview["filters"][0]   # first filter = MS1 in most DDA runs

avg = averaged_spectrum("run.raw", ms1_filter, max_points=100)
print(f"Averaged {avg['scan_count']} scans — {avg['point_count']} data points")
```

---

## Agent tips

### 1. Always orient first
Call `file_overview` (Skill 1) before anything else. Agents that skip this
often request out-of-range scan numbers or invalid retention times.

### 2. Metadata before arrays
Use `--max_points -1` to retrieve only `point_count` and `base_peak_*` before
deciding whether to load full spectrum arrays:

```python
meta = _run(raw_file, "scan", "spectrum", "--scan_number", "1", "--max_points", "-1")
print(meta["point_count"])   # how many centroids?
# now decide: load all, truncate, or skip
```

### 3. Stream large result sets
Prefer `_stream()` over `_run()` whenever iterating all scans of an MS order or
a long filter match. It avoids buffering a large JSON array:

```python
scans = _stream(raw_file, "analyze", "scan_info_range", "--ms_order", "1")
```

### 4. Narrow before iterating
When a filter has thousands of matching scans, bound the search to a scan window
before looping over `scan stats`:

```python
# Only look at scans 1–500 for a quick preview
hits = _run(raw_file, "search", "by_filter",
            "--filter_string", flt,
            "--start_scan", "1", "--end_scan", "500")
```

### 5. RT-to-scan navigation
Never guess scan numbers from retention times — always resolve via the CLI:

```python
sn = _run(raw_file, "search", "by_rt", "--retention_time", "4.5")["scan_number"]
rt = _run(raw_file, "search", "rt_for_scan", "--scan_number", str(sn))["retention_time"]
```

### 6. Error handling
All errors return a typed JSON object on stderr. Parse the `type` field to
decide whether to retry, skip, or abort:

```python
try:
    spec = _run(raw_file, "scan", "spectrum", "--scan_number", str(sn))
except RuntimeError as e:
    if "scan_not_found" in str(e):
        pass   # skip this scan
    else:
        raise
```

Error types: `raw_file_error`, `not_open_error`, `scan_not_found`,
`instrument_error`, `assembly_load_error`, `in_acquisition_error`, `unexpected_error`.

### 7. Composing skills
Skills are designed to chain:

```python
overview = file_overview("run.raw")
ms1 = overview["filters"][0]

peaks    = chromatogram_peak_table("run.raw", min_height=1e6)
top_scan = peaks[0]["scan_number"]

spec = spectrum_at_rt("run.raw", rt_minutes=peaks[0]["retention_time"])
avg  = averaged_spectrum("run.raw", ms1)
```
